"""
moel_expc AI 매핑 엔진 (9단계)

Step 1 : 입력 데이터셋 준비  — law_moel_expc.json + XML 상세 본문 수집
Step 2 : AI 출력 스키마 정의 — hazard/work_type/equipment 후보 + confidence + evidence
Step 3 : taxonomy 코드 목록 로드
Step 4 : OpenAI 분류기 구현  — structured JSON output
Step 5 : 샘플 100건 실행
Step 6 : 결과 저장 (mappings/*.json)
Step 7 : 검증
Step 8 : 법적 의무 항목 분리
Step 9 : 보고

실행:
  python -m scripts.mapping.ai_mapper_moel_expc [--limit N] [--offset O]
  기본값: --limit 100 (샘플 검증)

환경변수:
  OPENAI_API_KEY   (backend/.env)
  OPENAI_MODEL     (기본 gpt-4o-mini)
"""
import argparse
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

# ─── 경로 ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent.parent
BACKEND_ENV = ROOT / "backend" / ".env"
NORM_JSON   = ROOT / "data" / "risk_db" / "laws"   / "law_moel_expc.json"
MAP_DIR     = ROOT / "data" / "risk_db" / "mappings"
OUT_HAZARD  = MAP_DIR / "law_hazard_map_ai.json"
OUT_WTYPE   = MAP_DIR / "law_worktype_map_ai.json"
OUT_EQUIP   = MAP_DIR / "law_equipment_map_ai.json"

HAZARDS_F   = ROOT / "data" / "risk_db" / "hazard_action"  / "hazards.json"
WTYPES_F    = ROOT / "data" / "risk_db" / "work_taxonomy"   / "work_types.json"
EQUIP_F     = ROOT / "data" / "risk_db" / "equipment"       / "equipment_master.json"

load_dotenv(BACKEND_ENV)
load_dotenv(ROOT / ".env", override=False)

DETAIL_URL  = "https://www.law.go.kr/DRF/lawService.do"
DETAIL_TAGS = ["질의요지", "회답", "이유", "관련법령"]
REQUEST_DELAY = 0.5


# ─── Step 3: taxonomy 로드 ────────────────────────────────────────────────────

def _load_taxonomy() -> tuple[list, list, list]:
    def _load(path, key):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        items = d.get(key, d) if isinstance(d, dict) else d
        return items if isinstance(items, list) else list(items.values())

    hazards = _load(HAZARDS_F, "hazards")
    wtypes  = _load(WTYPES_F,  "work_types")
    equips  = _load(EQUIP_F,   "equipment")
    return hazards, wtypes, equips


def _taxonomy_prompt_block(hazards, wtypes, equips) -> str:
    h_lines = "\n".join(f"  {h['code']}: {h['name_ko']}" for h in hazards)
    w_lines = "\n".join(f"  {w['code']}: {w['name_ko']}" for w in wtypes)
    e_lines = "\n".join(f"  {e['code']}: {e['name_ko']}" for e in equips)
    return f"[위험요인 코드]\n{h_lines}\n\n[작업유형 코드]\n{w_lines}\n\n[장비 코드]\n{e_lines}"


# ─── Step 1: 입력 데이터 준비 ─────────────────────────────────────────────────

def _fetch_detail(serial_no: str) -> dict:
    """law.go.kr XML API에서 상세 본문 수집."""
    try:
        r = requests.get(
            DETAIL_URL,
            params={"OC": "data", "target": "moelCgmExpc",
                    "ID": serial_no, "type": "XML"},
            timeout=15,
        )
        r.raise_for_status()
        root = ET.fromstring(r.content)
        result = {}
        for tag in DETAIL_TAGS:
            elem = root.find(tag)
            result[tag] = (elem.text or "").strip() if elem is not None else ""
        return result
    except Exception as e:
        return {tag: "" for tag in DETAIL_TAGS}


def _build_text(item: dict, detail: dict) -> str:
    """분류에 사용할 텍스트 조합."""
    parts = []
    if item.get("title"):
        parts.append(f"안건명: {item['title']}")
    if detail.get("질의요지"):
        parts.append(f"질의요지: {detail['질의요지'][:400]}")
    if detail.get("회답"):
        parts.append(f"회신: {detail['회답'][:400]}")
    if detail.get("이유"):
        parts.append(f"이유: {detail['이유'][:300]}")
    if detail.get("관련법령"):
        parts.append(f"관련법령: {detail['관련법령'][:200]}")
    return "\n".join(parts)


# ─── Step 4: AI 분류기 ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """당신은 산업안전보건 법령해석 분류 전문가입니다.
주어진 고용노동부 법령해석 본문을 읽고, 아래 taxonomy에서 관련 코드를 추천하세요.

규칙:
1. 본문에 명확한 근거가 있을 때만 코드를 추천하세요.
2. 불확실하면 빈 배열을 반환하고 needs_review=true로 표시하세요.
3. 법적 의무 확정은 하지 마세요. 분류/추천만 수행하세요.
4. confidence: 0.0(확신 없음) ~ 1.0(확실), 0.5 미만이면 needs_review=true.
5. evidence_spans: 판단 근거가 된 원문 구절(최대 2개, 각 80자 이내).
6. 반드시 JSON만 반환하세요."""

USER_TEMPLATE = """{taxonomy}

---
[분류 대상]
{text}

---
다음 JSON 형식으로만 답변하세요:
{{
  "hazard_candidates": ["코드1", "코드2"],
  "work_type_candidates": ["코드1"],
  "equipment_candidates": ["코드1"],
  "confidence": 0.85,
  "evidence_spans": ["근거 문장1", "근거 문장2"],
  "needs_review": false
}}"""


def _classify_one(
    client: OpenAI,
    model: str,
    item: dict,
    detail: dict,
    taxonomy_block: str,
) -> dict:
    text = _build_text(item, detail)
    if not text.strip():
        return {
            "hazard_candidates": [], "work_type_candidates": [],
            "equipment_candidates": [], "confidence": 0.0,
            "evidence_spans": [], "needs_review": True,
            "_reason": "no_text",
        }

    prompt = USER_TEMPLATE.format(taxonomy=taxonomy_block, text=text)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=512,
        )
        raw = resp.choices[0].message.content or "{}"
        parsed = json.loads(raw)

        # 필드 보정
        conf = float(parsed.get("confidence", 0.0))
        result = {
            "hazard_candidates":    parsed.get("hazard_candidates",    []),
            "work_type_candidates": parsed.get("work_type_candidates", []),
            "equipment_candidates": parsed.get("equipment_candidates", []),
            "confidence":           conf,
            "evidence_spans":       parsed.get("evidence_spans", [])[:2],
            "needs_review":         parsed.get("needs_review", conf < 0.5),
        }
        if conf < 0.5:
            result["needs_review"] = True
        return result

    except Exception as e:
        return {
            "hazard_candidates": [], "work_type_candidates": [],
            "equipment_candidates": [], "confidence": 0.0,
            "evidence_spans": [], "needs_review": True,
            "_error": str(e),
        }


# ─── Step 5: 샘플 실행 ───────────────────────────────────────────────────────

def run(limit: int = 100, offset: int = 0) -> None:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("[FAIL] OPENAI_API_KEY 미설정. backend/.env 확인 필요.")
        sys.exit(1)

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    # Step 3: taxonomy
    hazards, wtypes, equips = _load_taxonomy()
    taxonomy_block = _taxonomy_prompt_block(hazards, wtypes, equips)
    valid_h = {h["code"] for h in hazards}
    valid_w = {w["code"] for w in wtypes}
    valid_e = {e["code"] for e in equips}
    print(f"[Step 3] taxonomy 로드: hazard {len(hazards)}종 / work_type {len(wtypes)}종 / equipment {len(equips)}종")

    # Step 1: 입력 데이터 — 안전보건 관련 키워드 필터링
    SAFETY_KEYWORDS = [
        "안전", "보건", "재해", "위험", "사고", "추락", "감전", "폭발", "화재",
        "밀폐", "질식", "화학", "유해", "MSDS", "방호", "안전관리",
        "산업안전보건", "중대재해", "작업환경", "보호구", "안전검사",
    ]
    with open(NORM_JSON, encoding="utf-8") as f:
        norm = json.load(f)
    all_items = norm["items"]
    safety_items = [
        i for i in all_items
        if any(kw in (i.get("title") or "") for kw in SAFETY_KEYWORDS)
    ]
    sample = safety_items[offset: offset + limit]
    print(f"[Step 1] 전체 {len(all_items)}건 중 안전보건 관련: {len(safety_items)}건")
    print(f"         offset={offset}, limit={limit} → 샘플 {len(sample)}건")
    print(f"[Step 4] 모델: {model}")

    # Step 5: 분류 실행
    results = []
    for idx, item in enumerate(sample, 1):
        serial = item["law_id"].replace("moel_expc:", "")

        # 상세 본문 수집
        detail = _fetch_detail(serial)
        time.sleep(REQUEST_DELAY)

        # AI 분류
        mapped = _classify_one(client, model, item, detail, taxonomy_block)

        # 유효하지 않은 코드 필터링
        mapped["hazard_candidates"]    = [c for c in mapped["hazard_candidates"]    if c in valid_h]
        mapped["work_type_candidates"] = [c for c in mapped["work_type_candidates"] if c in valid_w]
        mapped["equipment_candidates"] = [c for c in mapped["equipment_candidates"] if c in valid_e]

        record = {
            "law_id":               item["law_id"],
            "title":                item.get("title", ""),
            "issued_at":            item.get("issued_at", ""),
            "hazard_candidates":    mapped["hazard_candidates"],
            "work_type_candidates": mapped["work_type_candidates"],
            "equipment_candidates": mapped["equipment_candidates"],
            "confidence":           mapped["confidence"],
            "evidence_spans":       mapped["evidence_spans"],
            "needs_review":         mapped["needs_review"],
            "ai_model":             model,
            "classified_at":        datetime.now(timezone.utc).isoformat(),
            "source":               "ai_classifier_v1",
        }
        if "_error" in mapped:
            record["_error"] = mapped["_error"]
        if "_reason" in mapped:
            record["_reason"] = mapped["_reason"]

        results.append(record)

        status = "OK" if not mapped["needs_review"] else "? "
        h_cnt = len(mapped["hazard_candidates"])
        w_cnt = len(mapped["work_type_candidates"])
        e_cnt = len(mapped["equipment_candidates"])
        print(f"  [{idx:3d}/{len(sample)}] {status} conf={mapped['confidence']:.2f} "
              f"H:{h_cnt} W:{w_cnt} E:{e_cnt}  {item.get('title','')[:40]}")

    # Step 6: 저장
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    _save_maps(results, model, limit, offset)

    # Step 7·8: 검증 및 보고
    _validate_and_report(results, all_items, limit, safety_items)


def _save_maps(results: list[dict], model: str, limit: int, offset: int) -> None:
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ai_model":     model,
        "sample_limit": limit,
        "offset":       offset,
        "total":        len(results),
        "note":         "AI 분류 보조 결과. 법적 의무 확정은 rule_db가 담당.",
    }

    # hazard
    hazard_items = [
        {k: r[k] for k in ["law_id", "title", "issued_at", "hazard_candidates",
                            "confidence", "evidence_spans", "needs_review",
                            "ai_model", "classified_at"]}
        for r in results
    ]
    _write(OUT_HAZARD,  {**meta, "mappings": hazard_items})

    # work_type
    wtype_items = [
        {k: r[k] for k in ["law_id", "title", "issued_at", "work_type_candidates",
                            "confidence", "evidence_spans", "needs_review",
                            "ai_model", "classified_at"]}
        for r in results
    ]
    _write(OUT_WTYPE,   {**meta, "mappings": wtype_items})

    # equipment
    equip_items = [
        {k: r[k] for k in ["law_id", "title", "issued_at", "equipment_candidates",
                            "confidence", "evidence_spans", "needs_review",
                            "ai_model", "classified_at"]}
        for r in results
    ]
    _write(OUT_EQUIP,   {**meta, "mappings": equip_items})

    print(f"\n[Step 6] 저장 완료:")
    print(f"  {OUT_HAZARD}")
    print(f"  {OUT_WTYPE}")
    print(f"  {OUT_EQUIP}")


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ─── Step 7·8·9: 검증·분리·보고 ──────────────────────────────────────────────

def _validate_and_report(results: list[dict], all_items: list[dict], limit: int,
                         safety_items: list[dict] | None = None) -> None:
    if safety_items is None:
        safety_items = all_items
    total = len(results)
    if total == 0:
        print("[FAIL] 결과 없음")
        return

    has_hazard  = sum(1 for r in results if r["hazard_candidates"])
    has_wtype   = sum(1 for r in results if r["work_type_candidates"])
    has_equip   = sum(1 for r in results if r["equipment_candidates"])
    needs_rev   = sum(1 for r in results if r["needs_review"])
    high_conf   = sum(1 for r in results if r["confidence"] >= 0.7)
    errors      = sum(1 for r in results if "_error" in r)

    # 기존 키워드 방식 vs AI 방식 개선율 (안전 필터 후 동일 샘플 기준)
    prev_kw_mapped = sum(1 for i in safety_items[:limit] if i.get("hazard_codes"))
    prev_kw_rate   = prev_kw_mapped / limit * 100 if limit else 0
    ai_rate        = has_hazard / total * 100

    # Step 8: 법적 의무 분리 확인 (source="ai_classifier_v1" 태깅으로 분리)
    legal_obligation_note = (
        "법적 의무 항목은 rule_db(safety_rules.json)가 단독 확정. "
        "AI 결과(source=ai_classifier_v1)는 추천 보조 역할만 수행."
    )

    # 판정
    if errors > total * 0.1:
        verdict = "FAIL"
    elif needs_rev > total * 0.6 or has_hazard < total * 0.3:
        verdict = "WARN"
    else:
        verdict = "PASS"

    conf_vals = [r["confidence"] for r in results]
    conf_avg  = sum(conf_vals) / len(conf_vals) if conf_vals else 0

    print()
    print("=" * 62)
    print("[Step 9] 최종 보고")
    print("=" * 62)
    print(f"  생성/수정 파일:")
    print(f"    {OUT_HAZARD.name}")
    print(f"    {OUT_WTYPE.name}")
    print(f"    {OUT_EQUIP.name}")
    print(f"  샘플 대상 수      : {total}건")
    print(f"  hazard 매핑 성공  : {has_hazard}건 ({ai_rate:.1f}%)")
    print(f"  work_type 매핑    : {has_wtype}건 ({has_wtype/total*100:.1f}%)")
    print(f"  equipment 매핑    : {has_equip}건 ({has_equip/total*100:.1f}%)")
    print(f"  고신뢰(>=0.7)     : {high_conf}건 ({high_conf/total*100:.1f}%)")
    print(f"  평균 confidence   : {conf_avg:.3f}")
    print(f"  needs_review      : {needs_rev}건 ({needs_rev/total*100:.1f}%)")
    print(f"  API 오류          : {errors}건")
    print(f"  키워드 방식 대비  : {prev_kw_rate:.1f}% → {ai_rate:.1f}% "
          f"(+{ai_rate - prev_kw_rate:.1f}%p)")
    print(f"  [Step 8] {legal_obligation_note}")
    print(f"\n  결과: [{verdict}]")
    print("=" * 62)


# ─── 진입점 ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",  type=int, default=100, help="처리 건수 (기본 100)")
    parser.add_argument("--offset", type=int, default=0,   help="시작 위치 (기본 0)")
    args = parser.parse_args()
    run(limit=args.limit, offset=args.offset)

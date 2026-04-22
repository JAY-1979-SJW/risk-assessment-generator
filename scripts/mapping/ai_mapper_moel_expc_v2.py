"""
moel_expc AI 매핑 엔진 v2 — 3단계 relevance 분류 + 강화 confidence 산정

v1 대비 개선:
  - 물리적 위험 positive / 행정절차 negative 키워드 사전 강화
  - 3-stage pre-filter: physical_safety / non_physical / uncertain
  - physical_safety_relevant 레코드에만 전체 AI 분류 실행
  - uncertain 레코드는 경량 relevance check 선행
  - evidence span 수 · 카테고리 동시 검출 · 키워드 밀도 기반 confidence 조정
  - high confidence >= 20% 달성 시 전량 실행 gate

실행:
  python -m scripts.mapping.ai_mapper_moel_expc_v2 [--limit N] [--offset O] [--full-run]
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
NORM_JSON   = ROOT / "data" / "risk_db" / "laws"    / "law_moel_expc.json"
MAP_DIR     = ROOT / "data" / "risk_db" / "mappings"
OUT_HAZARD  = MAP_DIR / "law_hazard_map_ai.json"
OUT_WTYPE   = MAP_DIR / "law_worktype_map_ai.json"
OUT_EQUIP   = MAP_DIR / "law_equipment_map_ai.json"
HAZARDS_F   = ROOT / "data" / "risk_db" / "hazard_action"  / "hazards.json"
WTYPES_F    = ROOT / "data" / "risk_db" / "work_taxonomy"   / "work_types.json"
EQUIP_F     = ROOT / "data" / "risk_db" / "equipment"       / "equipment_master.json"

load_dotenv(BACKEND_ENV)
load_dotenv(ROOT / ".env", override=False)

DETAIL_URL    = "https://www.law.go.kr/DRF/lawService.do"
DETAIL_TAGS   = ["질의요지", "회답", "이유", "관련법령"]
REQUEST_DELAY = 0.5
LAW_OC        = os.getenv("LAW_GO_KR_OC", "data")

# ─── Step 3: 키워드 사전 ─────────────────────────────────────────────────────

# 물리적 현장 위험 → physical_safety_relevant 강신호
PHYSICAL_POSITIVE = [
    # 추락/낙하
    "추락", "낙하물", "낙하", "추락방지", "추락위험", "안전난간", "개구부",
    "작업발판", "달비계", "달줄", "달기구",
    # 전기/감전
    "감전", "누전", "충전부", "전기재해", "활선작업", "정전작업",
    # 화재/폭발
    "화재", "폭발", "인화성", "폭발위험", "화기작업", "위험물",
    # 밀폐공간
    "밀폐공간", "질식", "유해가스", "산소결핍", "이산화탄소", "황화수소",
    # 화학물질
    "화학물질", "유해물질", "위험물질", "MSDS", "발암물질", "유기용제",
    "석면", "납", "수은", "허용기준", "노출기준",
    # 분진/소음/진동
    "분진", "소음", "진동", "이상기압", "방사선",
    # 보호구
    "보호구", "안전모", "안전대", "안전화", "방진마스크", "방독마스크",
    "귀마개", "보안경", "보안면", "방열복",
    # 건설 장비/설비
    "비계", "거푸집", "굴착", "굴착면", "흙막이", "터널", "가설구조물",
    "크레인", "타워크레인", "이동식크레인", "지게차", "리프트",
    "고소작업대", "달비계", "이동식비계", "컨베이어", "프레스",
    "로울러", "압력용기", "보일러", "용접", "절단", "연삭", "천공",
    "항타기", "말뚝", "아스팔트", "콘크리트펌프", "믹서",
    # 방호장치
    "방호장치", "방호울", "과부하방지장치", "안전블록", "방호망",
    "추락방호망", "수직형추락방망",
    # 특정 위험 작업
    "고압작업", "발파작업", "잠수작업", "고온작업", "야간작업",
    # 재해/검사
    "산업재해", "중대재해", "중대산업사고", "업무상재해",
    "안전검사", "자율안전확인", "안전인증", "위험기계기구",
    # 작업환경
    "작업환경측정", "특수건강진단", "건강장해",
]

# 행정/조직/절차 → non_physical 신호 (물리 positive 없을 때만 적용)
ADMIN_SIGNALS = [
    "안전보건위원회", "위원 선출", "위원 임기", "위원 보수",
    "근로자대표", "안전관리자 선임", "보건관리자 선임",
    "안전보건관리책임자 선임", "총괄안전보건관리책임자",
    "안전관리비 계상", "산업안전보건관리비 계상", "안전관리비 사용기준",
    "안전관리비 사용가능", "안전관리비를",
    "과태료", "행정처분", "고용허가", "파견근로자",
    "특수형태근로종사자", "근로계약", "취업규칙",
    "이수시간", "자격증명", "등록기준", "허가기준",
    "이의신청", "불복", "심사청구", "재심사",
]

HIGH_CONFIDENCE_GATE = 0.20   # 20% 이상이면 전량 실행


# ─── Step 3: taxonomy 로드 ────────────────────────────────────────────────────

def _load_taxonomy():
    def _load(path, key):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        items = d.get(key, d) if isinstance(d, dict) else d
        return items if isinstance(items, list) else list(items.values())

    return _load(HAZARDS_F, "hazards"), _load(WTYPES_F, "work_types"), _load(EQUIP_F, "equipment")


def _taxonomy_block(hazards, wtypes, equips) -> str:
    h = "\n".join(f"  {h['code']}: {h['name_ko']}" for h in hazards)
    w = "\n".join(f"  {w['code']}: {w['name_ko']}" for w in wtypes)
    e = "\n".join(f"  {e['code']}: {e['name_ko']}" for e in equips)
    return f"[위험요인 코드]\n{h}\n\n[작업유형 코드]\n{w}\n\n[장비 코드]\n{e}"


# ─── Step 1: 3단계 relevance pre-filter ──────────────────────────────────────

def _relevance_prefilter(title: str, detail: dict) -> str:
    """
    Returns: 'physical_safety' | 'uncertain' | 'non_physical'
    """
    full_text = title + " " + " ".join(detail.get(t, "") for t in DETAIL_TAGS)

    physical_hits = sum(1 for kw in PHYSICAL_POSITIVE if kw in full_text)
    admin_hits    = sum(1 for kw in ADMIN_SIGNALS    if kw in full_text)

    if physical_hits >= 2:
        return "physical_safety"
    if physical_hits == 1 and admin_hits == 0:
        return "physical_safety"
    if physical_hits == 0 and admin_hits >= 1:
        return "non_physical"
    return "uncertain"


# ─── Step 4: AI 분류기 ────────────────────────────────────────────────────────

SYSTEM_CLASSIFY = """당신은 산업안전보건 법령해석 분류 전문가입니다.
다음 고용노동부 법령해석 본문을 읽고, 물리적 현장 위험(추락·감전·화학물질·장비 등)과 직접 관련된 경우에만 taxonomy 코드를 추천하세요.

규칙:
1. 물리적 위험, 장비, 작업유형이 본문에 명확히 언급될 때만 추천.
2. 조직구성·행정절차·자격요건만 다루는 경우 모든 배열을 비워두세요.
3. confidence: 근거 문장 명확 → 0.8+, 간접 언급 → 0.5~0.7, 불확실 → 0.3 이하.
4. evidence_spans: 판단 근거 원문 구절(최대 2개, 각 80자 이내).
5. needs_review: confidence < 0.6이면 true.
6. 반드시 JSON만 반환하세요."""

SYSTEM_RELEVANCE = """당신은 산업안전보건 문서 분류기입니다.
주어진 법령해석이 물리적 현장 위험(추락, 감전, 화학물질, 장비사고 등)과 직접 관련이 있는지 판별하세요.
반드시 JSON만 반환하세요."""

USER_CLASSIFY = """{taxonomy}

---
[분류 대상]
{text}

---
JSON 형식:
{{
  "hazard_candidates": ["코드"],
  "work_type_candidates": ["코드"],
  "equipment_candidates": ["코드"],
  "confidence": 0.85,
  "evidence_spans": ["근거1", "근거2"],
  "needs_review": false
}}"""

USER_RELEVANCE = """다음 법령해석이 물리적 현장 위험과 직접 관련이 있는지 판별하세요.
물리적 현장 위험 예: 추락, 감전, 화재폭발, 화학물질, 건설장비, 보호구 착용의무

[법령해석]
{text}

JSON 형식:
{{"relevant": true/false, "reason": "한 줄 이유"}}"""


def _call_classify(client, model, text, taxonomy_block) -> dict:
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_CLASSIFY},
                {"role": "user",   "content": USER_CLASSIFY.format(taxonomy=taxonomy_block, text=text)},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=512,
        )
        return json.loads(resp.choices[0].message.content or "{}")
    except Exception as e:
        return {"_error": str(e)}


def _call_relevance(client, model, text) -> bool:
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_RELEVANCE},
                {"role": "user",   "content": USER_RELEVANCE.format(text=text[:800])},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=80,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        return bool(data.get("relevant", False))
    except Exception:
        return False


# ─── Step 4: confidence 재산정 ────────────────────────────────────────────────

def _adjust_confidence(raw: dict, relevance: str) -> float:
    """
    base confidence에 evidence·카테고리 수·relevance 보정 적용.
    """
    conf = float(raw.get("confidence", 0.0))
    spans = raw.get("evidence_spans", [])
    h     = raw.get("hazard_candidates",    [])
    w     = raw.get("work_type_candidates", [])
    e     = raw.get("equipment_candidates", [])
    cats  = sum(1 for lst in [h, w, e] if lst)

    # evidence 없는데 후보 있으면 신뢰도 낮춤
    if not spans and (h or w or e):
        conf = min(conf, 0.55)

    # evidence 2개 이상 + 카테고리 2개 이상 → 보너스
    if len(spans) >= 2 and cats >= 2:
        conf = min(conf + 0.10, 1.0)
    elif len(spans) >= 1 and cats >= 1:
        conf = min(conf + 0.05, 1.0)

    # relevance=physical_safety면 소폭 부스트
    if relevance == "physical_safety" and conf >= 0.5:
        conf = min(conf + 0.05, 1.0)

    # 후보가 없으면 최대 0.5
    if not h and not w and not e:
        conf = min(conf, 0.50)

    return round(conf, 3)


# ─── 상세 본문 수집 ───────────────────────────────────────────────────────────

def _fetch_detail(serial_no: str) -> dict:
    try:
        r = requests.get(
            DETAIL_URL,
            params={"OC": LAW_OC, "target": "moelCgmExpc",
                    "ID": serial_no, "type": "XML"},
            timeout=15,
        )
        r.raise_for_status()
        root = ET.fromstring(r.content)
        return {tag: (root.find(tag) and root.find(tag).text or "").strip()
                for tag in DETAIL_TAGS}
    except Exception:
        return {tag: "" for tag in DETAIL_TAGS}


def _build_text(item: dict, detail: dict) -> str:
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


# ─── 메인 실행 ───────────────────────────────────────────────────────────────

def run(limit: int = 100, offset: int = 0, full_run: bool = False, physical_only: bool = False) -> None:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("[FAIL] OPENAI_API_KEY 미설정.")
        sys.exit(1)

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    hazards, wtypes, equips = _load_taxonomy()
    tax_block = _taxonomy_block(hazards, wtypes, equips)
    valid_h = {h["code"] for h in hazards}
    valid_w = {w["code"] for w in wtypes}
    valid_e = {e["code"] for e in equips}
    print(f"[Step 3] taxonomy: hazard {len(hazards)} / work_type {len(wtypes)} / equipment {len(equips)}")

    with open(NORM_JSON, encoding="utf-8") as f:
        norm = json.load(f)
    all_items = norm["items"]

    # v1 안전보건 키워드 필터
    SAFETY_KW = ["안전", "보건", "재해", "위험", "사고", "추락", "감전",
                 "폭발", "화재", "밀폐", "질식", "화학", "유해", "MSDS",
                 "방호", "안전관리", "산업안전보건", "중대재해", "작업환경",
                 "보호구", "안전검사"]
    safety_pool = [i for i in all_items if any(k in (i.get("title") or "") for k in SAFETY_KW)]

    # 타이틀 수준 물리적 위험 필터 (physical_only 모드용)
    physical_pool = [
        i for i in safety_pool
        if any(k in (i.get("title") or "") for k in PHYSICAL_POSITIVE)
    ]

    if physical_only:
        target_pool = physical_pool
        pool_label  = f"물리적위험 타이틀 {len(physical_pool)}건"
    elif full_run:
        target_pool = all_items
        pool_label  = f"전체 {len(all_items)}건"
    else:
        target_pool = safety_pool
        pool_label  = f"안전보건 풀 {len(safety_pool)}건"

    sample = target_pool[offset: offset + limit]

    print(f"[Step 1] 전체 {len(all_items)}건 / 안전보건: {len(safety_pool)}건 / 물리적 타이틀: {len(physical_pool)}건")
    print(f"         대상: {pool_label} -> 샘플 {len(sample)}건 (offset={offset})")
    print(f"[Step 4] 모델: {model}")
    print()

    results = []
    bucket_count = {"physical_safety": 0, "uncertain": 0, "non_physical": 0}
    ai_call_count = 0

    for idx, item in enumerate(sample, 1):
        serial = item["law_id"].replace("moel_expc:", "")
        detail = _fetch_detail(serial)
        time.sleep(REQUEST_DELAY)

        # Step 1: 3단계 pre-filter
        relevance = _relevance_prefilter(item.get("title", ""), detail)
        bucket_count[relevance] += 1

        # Step 2: non_physical은 skip
        if relevance == "non_physical":
            result = _make_empty(item, relevance, "non_physical_skip")
            results.append(result)
            print(f"  [{idx:3d}/{len(sample)}] SKIP  non_physical  {item.get('title','')[:50]}")
            continue

        text = _build_text(item, detail)

        # uncertain → 전체 분류 실행 (이진 거부 제거, confidence로 자연 필터링)
        # Step 2: 전체 분류
        raw = _call_classify(client, model, text, tax_block)
        ai_call_count += 1

        if "_error" in raw:
            result = _make_empty(item, relevance, "api_error")
            result["_error"] = raw["_error"]
            results.append(result)
            print(f"  [{idx:3d}/{len(sample)}] ERR   {item.get('title','')[:50]}")
            continue

        # Step 4: confidence 재산정 (uncertain은 최대 0.75)
        conf = _adjust_confidence(raw, relevance)
        if relevance == "uncertain":
            conf = min(conf, 0.75)

        result = {
            "law_id":               item["law_id"],
            "title":                item.get("title", ""),
            "issued_at":            item.get("issued_at", ""),
            "relevance":            relevance,
            "hazard_candidates":    [c for c in raw.get("hazard_candidates",    []) if c in valid_h],
            "work_type_candidates": [c for c in raw.get("work_type_candidates", []) if c in valid_w],
            "equipment_candidates": [c for c in raw.get("equipment_candidates", []) if c in valid_e],
            "confidence":           conf,
            "evidence_spans":       (raw.get("evidence_spans") or [])[:2],
            "needs_review":         conf < 0.6,
            "ai_model":             model,
            "classified_at":        _now(),
            "source":               "ai_classifier_v2",
        }
        results.append(result)

        h_n = len(result["hazard_candidates"])
        w_n = len(result["work_type_candidates"])
        e_n = len(result["equipment_candidates"])
        tag = "OK  " if not result["needs_review"] else "?   "
        print(f"  [{idx:3d}/{len(sample)}] {tag} conf={conf:.2f} H:{h_n} W:{w_n} E:{e_n}  {item.get('title','')[:40]}")

    # Step 6 저장
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    _save_maps(results, model, limit, offset)

    # Step 6·7 보고 + gate
    _report(results, safety_pool, limit, offset, bucket_count, ai_call_count, full_run, physical_only)


def _make_empty(item, relevance, reason) -> dict:
    return {
        "law_id":               item["law_id"],
        "title":                item.get("title", ""),
        "issued_at":            item.get("issued_at", ""),
        "relevance":            relevance,
        "hazard_candidates":    [],
        "work_type_candidates": [],
        "equipment_candidates": [],
        "confidence":           0.0,
        "evidence_spans":       [],
        "needs_review":         True,
        "ai_model":             "",
        "classified_at":        _now(),
        "source":               "ai_classifier_v2",
        "_reason":              reason,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _save_maps(results, model, limit, offset):
    meta = {
        "generated_at": _now(), "ai_model": model,
        "version":      "v2",   "sample_limit": limit, "offset": offset,
        "total":        len(results),
        "note":         "AI 분류 보조. 법적 의무 확정은 rule_db 담당.",
    }
    fields_h = ["law_id", "title", "issued_at", "relevance", "hazard_candidates",
                "confidence", "evidence_spans", "needs_review", "ai_model", "classified_at"]
    fields_w = ["law_id", "title", "issued_at", "relevance", "work_type_candidates",
                "confidence", "evidence_spans", "needs_review", "ai_model", "classified_at"]
    fields_e = ["law_id", "title", "issued_at", "relevance", "equipment_candidates",
                "confidence", "evidence_spans", "needs_review", "ai_model", "classified_at"]

    def _pick(r, keys): return {k: r.get(k) for k in keys}

    _write(OUT_HAZARD, {**meta, "mappings": [_pick(r, fields_h) for r in results]})
    _write(OUT_WTYPE,  {**meta, "mappings": [_pick(r, fields_w) for r in results]})
    _write(OUT_EQUIP,  {**meta, "mappings": [_pick(r, fields_e) for r in results]})
    print(f"\n[Step 6] 저장 완료: {OUT_HAZARD.parent}/")


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _report(results, safety_pool, limit, offset, bucket_count, ai_calls, full_run, physical_only=False):
    total = len(results)
    if total == 0:
        print("[FAIL] 결과 없음")
        return

    classified = [r for r in results if r.get("relevance") == "physical_safety"]
    skipped    = [r for r in results if r.get("_reason") in ("non_physical_skip", "uncertain_rejected")]

    has_h = sum(1 for r in results if r["hazard_candidates"])
    has_w = sum(1 for r in results if r["work_type_candidates"])
    has_e = sum(1 for r in results if r["equipment_candidates"])
    needs = sum(1 for r in results if r["needs_review"])
    high  = sum(1 for r in results if r["confidence"] >= 0.7)
    errors = sum(1 for r in results if "_error" in r)

    conf_vals = [r["confidence"] for r in results]
    conf_avg  = sum(conf_vals) / len(conf_vals) if conf_vals else 0
    high_rate = high / total if total else 0

    # v1 기준치 (키워드 방식)
    prev_h = sum(1 for i in safety_pool[:limit] if i.get("hazard_codes"))
    prev_r = prev_h / limit * 100 if limit else 0
    ai_r   = has_h / total * 100

    # Step 8: 법적의무 분리 확인
    legal_note = "법적 의무 항목은 rule_db 단독 확정. AI(v2)는 추천 보조 전용."

    print()
    print("=" * 65)
    print("[Step 6] 비교 보고 (v1 vs v2)")
    print("=" * 65)
    print(f"  [relevance 판정]")
    print(f"    physical_safety  : {bucket_count['physical_safety']}건")
    print(f"    uncertain        : {bucket_count['uncertain']}건")
    print(f"    non_physical     : {bucket_count['non_physical']}건 (skip)")
    print(f"    AI 호출 수       : {ai_calls}건")
    print()
    print(f"  [매핑 결과]")
    print(f"    hazard 매핑률    : {ai_r:.1f}%  (v1 {prev_r:.1f}%  +{ai_r-prev_r:.1f}%p)")
    print(f"    work_type 매핑률 : {has_w/total*100:.1f}%")
    print(f"    equipment 매핑률 : {has_e/total*100:.1f}%")
    print()
    print(f"  [confidence]")
    print(f"    평균             : {conf_avg:.3f}")
    print(f"    high (>=0.7)     : {high}건 ({high_rate*100:.1f}%)")
    print(f"    needs_review     : {needs}건 ({needs/total*100:.1f}%)")
    print(f"    API 오류         : {errors}건")
    print()
    print(f"  [Step 8] {legal_note}")

    # Step 7: gate
    print()
    print("=" * 65)
    print("[Step 7] 전량 실행 gate")
    if full_run:
        print(f"  전량 실행 완료: {total}건 처리")
        verdict = "PASS" if errors < total * 0.05 else "WARN"
    elif high_rate >= HIGH_CONFIDENCE_GATE:
        verdict = "PASS"
        print(f"  고신뢰 비율 {high_rate*100:.1f}% >= {HIGH_CONFIDENCE_GATE*100:.0f}% 기준 충족"  )
        print(f"  전량 실행 권장: python -m scripts.mapping.ai_mapper_moel_expc_v2 --limit 9573 --full-run")
    else:
        verdict = "WARN"
        print(f"  고신뢰 비율 {high_rate*100:.1f}% < {HIGH_CONFIDENCE_GATE*100:.0f}% - 전량 실행 보류")
        print(f"  프롬프트 또는 taxonomy 추가 보강 후 재시도 권장")

    print(f"\n  결과: [{verdict}]")
    print("=" * 65)


# ─── 진입점 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",    type=int,  default=100, help="처리 건수")
    parser.add_argument("--offset",   type=int,  default=0,   help="시작 위치")
    parser.add_argument("--full-run",      action="store_true", help="전량 실행 (gate 통과 시)")
    parser.add_argument("--physical-only", action="store_true", help="물리적 위험 타이틀 필터 풀만 대상")
    args = parser.parse_args()
    run(limit=args.limit, offset=args.offset, full_run=args.full_run, physical_only=args.physical_only)

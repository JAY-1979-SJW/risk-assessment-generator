"""
moel_expc AI 매핑 엔진 v3 — OC 기반 상세 본문 활용 + v2 대비 정확도 비교

v2 대비 개선:
  - OC=haehan2026 (등록키) 사용으로 질의요지/회답/이유/관련법령 완전 수집
  - 텍스트 입력 한도 확장: 질의요지·회답 800→1200자, 이유 300→600자, 관련법령 200→400자
  - 결과에 question_summary / answer / reason / related_laws 저장 (수동 검증용)
  - 출력: law_hazard_map_ai_v3.json / law_worktype_map_ai_v3.json / law_equipment_map_ai_v3.json
  - 최종 보고: v2 vs v3 지표 자동 비교 (6단계)

실행:
  python -m scripts.mapping.ai_mapper_moel_expc_v3 --physical-only --limit 374
  python -m scripts.mapping.ai_mapper_moel_expc_v3 --physical-only --limit 20 --verify
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
OUT_HAZARD  = MAP_DIR / "law_hazard_map_ai_v3.json"
OUT_WTYPE   = MAP_DIR / "law_worktype_map_ai_v3.json"
OUT_EQUIP   = MAP_DIR / "law_equipment_map_ai_v3.json"
# v2 기준 파일 (비교용)
V2_HAZARD   = MAP_DIR / "law_hazard_map_ai.json"
V2_WTYPE    = MAP_DIR / "law_worktype_map_ai.json"
V2_EQUIP    = MAP_DIR / "law_equipment_map_ai.json"
HAZARDS_F   = ROOT / "data" / "risk_db" / "hazard_action"  / "hazards.json"
WTYPES_F    = ROOT / "data" / "risk_db" / "work_taxonomy"   / "work_types.json"
EQUIP_F     = ROOT / "data" / "risk_db" / "equipment"       / "equipment_master.json"

load_dotenv(BACKEND_ENV)
load_dotenv(ROOT / ".env", override=False)

DETAIL_URL    = "https://www.law.go.kr/DRF/lawService.do"
DETAIL_TAGS   = ["질의요지", "회답", "이유", "관련법령"]
REQUEST_DELAY = 0.5
LAW_OC        = os.getenv("LAW_GO_KR_OC", "data")

# ─── 물리적 위험 키워드 사전 ──────────────────────────────────────────────────

PHYSICAL_POSITIVE = [
    "추락", "낙하물", "낙하", "추락방지", "추락위험", "안전난간", "개구부",
    "작업발판", "달비계", "달줄", "달기구",
    "감전", "누전", "충전부", "전기재해", "활선작업", "정전작업",
    "화재", "폭발", "인화성", "폭발위험", "화기작업", "위험물",
    "밀폐공간", "질식", "유해가스", "산소결핍", "이산화탄소", "황화수소",
    "화학물질", "유해물질", "위험물질", "MSDS", "발암물질", "유기용제",
    "석면", "납", "수은", "허용기준", "노출기준",
    "분진", "소음", "진동", "이상기압", "방사선",
    "보호구", "안전모", "안전대", "안전화", "방진마스크", "방독마스크",
    "귀마개", "보안경", "보안면", "방열복",
    "비계", "거푸집", "굴착", "굴착면", "흙막이", "터널", "가설구조물",
    "크레인", "타워크레인", "이동식크레인", "지게차", "리프트",
    "고소작업대", "달비계", "이동식비계", "컨베이어", "프레스",
    "로울러", "압력용기", "보일러", "용접", "절단", "연삭", "천공",
    "항타기", "말뚝", "아스팔트", "콘크리트펌프", "믹서",
    "방호장치", "방호울", "과부하방지장치", "안전블록", "방호망",
    "추락방호망", "수직형추락방망",
    "고압작업", "발파작업", "잠수작업", "고온작업", "야간작업",
    "산업재해", "중대재해", "중대산업사고", "업무상재해",
    "안전검사", "자율안전확인", "안전인증", "위험기계기구",
    "작업환경측정", "특수건강진단", "건강장해",
]

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

HIGH_CONFIDENCE_GATE = 0.20


# ─── taxonomy 로드 ────────────────────────────────────────────────────────────

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


# ─── 3단계 relevance pre-filter ──────────────────────────────────────────────

def _relevance_prefilter(title: str, detail: dict) -> str:
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


# ─── 프롬프트 ─────────────────────────────────────────────────────────────────

SYSTEM_CLASSIFY = """당신은 산업안전보건 법령해석 분류 전문가입니다.
다음 고용노동부 법령해석 본문을 읽고, 물리적 현장 위험(추락·감전·화학물질·장비 등)과 직접 관련된 경우에만 taxonomy 코드를 추천하세요.

규칙:
1. 물리적 위험, 장비, 작업유형이 본문에 명확히 언급될 때만 추천.
2. 조직구성·행정절차·자격요건만 다루는 경우 모든 배열을 비워두세요.
3. confidence: 근거 문장 명확 → 0.8+, 간접 언급 → 0.5~0.7, 불확실 → 0.3 이하.
4. evidence_spans: 판단 근거 원문 구절(최대 2개, 각 80자 이내).
5. needs_review: confidence < 0.6이면 true.
6. 반드시 JSON만 반환하세요."""

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


# ─── confidence 재산정 ────────────────────────────────────────────────────────

def _adjust_confidence(raw: dict, relevance: str) -> float:
    conf  = float(raw.get("confidence", 0.0))
    spans = raw.get("evidence_spans", [])
    h     = raw.get("hazard_candidates",    [])
    w     = raw.get("work_type_candidates", [])
    e     = raw.get("equipment_candidates", [])
    cats  = sum(1 for lst in [h, w, e] if lst)

    if not spans and (h or w or e):
        conf = min(conf, 0.55)

    if len(spans) >= 2 and cats >= 2:
        conf = min(conf + 0.10, 1.0)
    elif len(spans) >= 1 and cats >= 1:
        conf = min(conf + 0.05, 1.0)

    if relevance == "physical_safety" and conf >= 0.5:
        conf = min(conf + 0.05, 1.0)

    if not h and not w and not e:
        conf = min(conf, 0.50)

    return round(conf, 3)


# ─── 상세 본문 수집 (v3: 텍스트 한도 확장) ───────────────────────────────────

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
    """v3: 텍스트 입력 한도 확장 (질의요지·회답 1200자, 이유 600자, 관련법령 400자)"""
    parts = []
    if item.get("title"):
        parts.append(f"안건명: {item['title']}")
    if detail.get("질의요지"):
        parts.append(f"질의요지: {detail['질의요지'][:1200]}")
    if detail.get("회답"):
        parts.append(f"회신: {detail['회답'][:1200]}")
    if detail.get("이유"):
        parts.append(f"이유: {detail['이유'][:600]}")
    if detail.get("관련법령"):
        parts.append(f"관련법령: {detail['관련법령'][:400]}")
    return "\n".join(parts)


# ─── 유틸 ────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_empty(item, detail, relevance, reason) -> dict:
    return {
        "law_id":               item["law_id"],
        "title":                item.get("title", ""),
        "issued_at":            item.get("issued_at", ""),
        "question_summary":     detail.get("질의요지", "")[:200],
        "answer":               detail.get("회답", "")[:200],
        "reason":               detail.get("이유", "")[:200],
        "related_laws":         detail.get("관련법령", "")[:200],
        "relevance":            relevance,
        "hazard_candidates":    [],
        "work_type_candidates": [],
        "equipment_candidates": [],
        "confidence":           0.0,
        "evidence_spans":       [],
        "needs_review":         True,
        "ai_model":             "",
        "classified_at":        _now(),
        "source":               "ai_classifier_v3",
        "_reason":              reason,
    }


# ─── 저장 ────────────────────────────────────────────────────────────────────

def _save_maps(results, model, limit, offset):
    meta = {
        "generated_at": _now(), "ai_model": model,
        "version":      "v3",   "sample_limit": limit, "offset": offset,
        "total":        len(results),
        "oc_key":       LAW_OC,
        "note":         "AI 분류 보조. 법적 의무 확정은 rule_db 담당.",
    }
    # v3: question_summary / answer / reason / related_laws 포함
    fields_h = ["law_id", "title", "question_summary", "answer", "reason", "related_laws",
                "issued_at", "relevance", "hazard_candidates",
                "confidence", "evidence_spans", "needs_review", "ai_model", "classified_at"]
    fields_w = ["law_id", "title", "question_summary", "answer", "reason", "related_laws",
                "issued_at", "relevance", "work_type_candidates",
                "confidence", "evidence_spans", "needs_review", "ai_model", "classified_at"]
    fields_e = ["law_id", "title", "question_summary", "answer", "reason", "related_laws",
                "issued_at", "relevance", "equipment_candidates",
                "confidence", "evidence_spans", "needs_review", "ai_model", "classified_at"]

    def _pick(r, keys): return {k: r.get(k) for k in keys}

    _write(OUT_HAZARD, {**meta, "mappings": [_pick(r, fields_h) for r in results]})
    _write(OUT_WTYPE,  {**meta, "mappings": [_pick(r, fields_w) for r in results]})
    _write(OUT_EQUIP,  {**meta, "mappings": [_pick(r, fields_e) for r in results]})
    print(f"\n[Step 3] 저장 완료: {OUT_HAZARD.parent}/")
    print(f"  {OUT_HAZARD.name}")
    print(f"  {OUT_WTYPE.name}")
    print(f"  {OUT_EQUIP.name}")


# ─── v2 통계 로드 ────────────────────────────────────────────────────────────

def _load_v2_stats() -> dict | None:
    if not V2_HAZARD.exists():
        return None
    try:
        with open(V2_HAZARD, encoding="utf-8") as f:
            v2h = json.load(f)
        with open(V2_WTYPE,  encoding="utf-8") as f:
            v2w = json.load(f)
        with open(V2_EQUIP,  encoding="utf-8") as f:
            v2e = json.load(f)

        maps = v2h.get("mappings", [])
        total = len(maps)
        if total == 0:
            return None

        has_h = sum(1 for r in maps if r.get("hazard_candidates"))
        has_w = sum(1 for r in v2w.get("mappings", []) if r.get("work_type_candidates"))
        has_e = sum(1 for r in v2e.get("mappings", []) if r.get("equipment_candidates"))
        high  = sum(1 for r in maps if (r.get("confidence") or 0) >= 0.7)
        needs = sum(1 for r in maps if r.get("needs_review"))
        confs = [r.get("confidence") or 0 for r in maps]
        avg_c = sum(confs) / len(confs) if confs else 0

        return {
            "total":          total,
            "hazard_rate":    has_h / total * 100,
            "worktype_rate":  has_w / total * 100,
            "equip_rate":     has_e / total * 100,
            "high_conf_rate": high  / total * 100,
            "avg_conf":       avg_c,
            "needs_review":   needs / total * 100,
        }
    except Exception:
        return None


# ─── 보고 ────────────────────────────────────────────────────────────────────

def _report(results, bucket_count, ai_calls, full_run, physical_only, verify_mode):
    total = len(results)
    if total == 0:
        print("[FAIL] 결과 없음")
        return

    has_h  = sum(1 for r in results if r.get("hazard_candidates"))
    has_w  = sum(1 for r in results if r.get("work_type_candidates"))
    has_e  = sum(1 for r in results if r.get("equipment_candidates"))
    needs  = sum(1 for r in results if r.get("needs_review"))
    high   = sum(1 for r in results if (r.get("confidence") or 0) >= 0.7)
    errors = sum(1 for r in results if "_error" in r)
    confs  = [r.get("confidence") or 0 for r in results]
    avg_c  = sum(confs) / len(confs) if confs else 0
    high_rate = high / total if total else 0

    v3 = {
        "total":          total,
        "hazard_rate":    has_h / total * 100,
        "worktype_rate":  has_w / total * 100,
        "equip_rate":     has_e / total * 100,
        "high_conf_rate": high_rate * 100,
        "avg_conf":       avg_c,
        "needs_review":   needs / total * 100,
    }
    v2 = _load_v2_stats()

    print()
    print("=" * 70)
    print("[Step 6] v2 vs v3 비교 보고")
    print("=" * 70)
    print(f"  대상: {'물리적위험 타이틀 필터' if physical_only else '전체'} {total}건")
    print(f"  OC키: {LAW_OC}")
    print()
    print(f"  [relevance 판정]")
    print(f"    physical_safety : {bucket_count['physical_safety']}건")
    print(f"    uncertain       : {bucket_count['uncertain']}건")
    print(f"    non_physical    : {bucket_count['non_physical']}건 (skip)")
    print(f"    AI 호출 수      : {ai_calls}건")
    print()

    def _row(label, v2_val, v3_val, fmt=".1f", unit="%"):
        if v2_val is None:
            print(f"  {label:<22} v3={v3_val:{fmt}}{unit}  (v2 없음)")
        else:
            delta = v3_val - v2_val
            sign  = "+" if delta >= 0 else ""
            print(f"  {label:<22} v2={v2_val:{fmt}}{unit}  v3={v3_val:{fmt}}{unit}  ({sign}{delta:{fmt}}{unit})")

    print(f"  [4단계: 지표 비교]")
    v2h = v2["hazard_rate"]   if v2 else None
    v2w = v2["worktype_rate"] if v2 else None
    v2e = v2["equip_rate"]    if v2 else None
    v2hc = v2["high_conf_rate"] if v2 else None
    v2ac = v2["avg_conf"]       if v2 else None
    v2nr = v2["needs_review"]   if v2 else None

    _row("hazard 매핑률",    v2h,  v3["hazard_rate"])
    _row("work_type 매핑률", v2w,  v3["worktype_rate"])
    _row("equipment 매핑률", v2e,  v3["equip_rate"])
    _row("high conf (>=0.7)", v2hc, v3["high_conf_rate"])
    _row("평균 confidence",  v2ac, v3["avg_conf"], fmt=".3f", unit="")
    _row("needs_review",     v2nr, v3["needs_review"])
    print(f"  {'API 오류':<22} {errors}건")

    # 5단계: 샘플 수동 검증
    if verify_mode:
        print()
        print("=" * 70)
        print("[Step 5] 샘플 20건 수동 검증")
        print("=" * 70)
        sample = [r for r in results if not r.get("_reason")][:20]
        for i, r in enumerate(sample, 1):
            h = ", ".join(r.get("hazard_candidates") or []) or "-"
            w = ", ".join(r.get("work_type_candidates") or []) or "-"
            e = ", ".join(r.get("equipment_candidates") or []) or "-"
            conf = r.get("confidence", 0)
            ev = " | ".join((r.get("evidence_spans") or [])[:2]) or "-"
            nr = "Y" if r.get("needs_review") else "N"
            print(f"\n  [{i:02d}] {r.get('title','')[:55]}")
            print(f"       Q: {(r.get('question_summary') or '')[:80]}")
            print(f"       H:{h}  W:{w}  E:{e}")
            print(f"       conf={conf:.2f}  NR={nr}  근거: {ev[:60]}")

    # 6단계: 최종 판정
    print()
    print("=" * 70)
    print("[Step 6] 최종 판정")
    print("=" * 70)
    print(f"  총 대상 수      : {total}건")
    print(f"  hazard 매핑률   : {v3['hazard_rate']:.1f}%")
    print(f"  work_type 매핑률: {v3['worktype_rate']:.1f}%")
    print(f"  equipment 매핑률: {v3['equip_rate']:.1f}%")
    print(f"  high conf 비율  : {v3['high_conf_rate']:.1f}%")
    print(f"  평균 confidence : {v3['avg_conf']:.3f}")
    print(f"  needs_review    : {v3['needs_review']:.1f}%")

    if v2:
        print()
        print(f"  [개선폭 (v2 -> v3)]")
        print(f"    hazard        : {v3['hazard_rate'] - v2['hazard_rate']:+.1f}%p")
        print(f"    work_type     : {v3['worktype_rate'] - v2['worktype_rate']:+.1f}%p")
        print(f"    equipment     : {v3['equip_rate'] - v2['equip_rate']:+.1f}%p")
        print(f"    high conf     : {v3['high_conf_rate'] - v2['high_conf_rate']:+.1f}%p")
        print(f"    avg conf      : {v3['avg_conf'] - v2['avg_conf']:+.3f}")
        print(f"    needs_review  : {v3['needs_review'] - v2['needs_review']:+.1f}%p")

    if errors > total * 0.05:
        verdict = "FAIL"
    elif high_rate >= HIGH_CONFIDENCE_GATE:
        verdict = "PASS"
    else:
        verdict = "WARN"

    print(f"\n  결과: [{verdict}]")
    print("=" * 70)


# ─── 메인 ────────────────────────────────────────────────────────────────────

def run(limit: int = 100, offset: int = 0, physical_only: bool = False,
        full_run: bool = False, verify: bool = False) -> None:
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
    print(f"         OC키: {LAW_OC}")

    with open(NORM_JSON, encoding="utf-8") as f:
        norm = json.load(f)
    all_items = norm["items"]

    SAFETY_KW = ["안전", "보건", "재해", "위험", "사고", "추락", "감전",
                 "폭발", "화재", "밀폐", "질식", "화학", "유해", "MSDS",
                 "방호", "안전관리", "산업안전보건", "중대재해", "작업환경",
                 "보호구", "안전검사"]
    safety_pool  = [i for i in all_items if any(k in (i.get("title") or "") for k in SAFETY_KW)]
    physical_pool = [i for i in safety_pool if any(k in (i.get("title") or "") for k in PHYSICAL_POSITIVE)]

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

    print(f"[Step 1] 전체 {len(all_items)}건 / 안전보건: {len(safety_pool)}건 / 물리적타이틀: {len(physical_pool)}건")
    print(f"         대상: {pool_label} -> 처리 {len(sample)}건 (offset={offset})")
    print(f"[Step 4] 모델: {model}")
    print()

    results = []
    bucket_count = {"physical_safety": 0, "uncertain": 0, "non_physical": 0}
    ai_call_count = 0

    for idx, item in enumerate(sample, 1):
        serial = item["law_id"].replace("moel_expc:", "")
        detail = _fetch_detail(serial)
        time.sleep(REQUEST_DELAY)

        relevance = _relevance_prefilter(item.get("title", ""), detail)
        bucket_count[relevance] += 1

        if relevance == "non_physical":
            result = _make_empty(item, detail, relevance, "non_physical_skip")
            results.append(result)
            print(f"  [{idx:3d}/{len(sample)}] SKIP  {item.get('title','')[:50]}")
            continue

        text = _build_text(item, detail)
        raw  = _call_classify(client, model, text, tax_block)
        ai_call_count += 1

        if "_error" in raw:
            result = _make_empty(item, detail, relevance, "api_error")
            result["_error"] = raw["_error"]
            results.append(result)
            print(f"  [{idx:3d}/{len(sample)}] ERR   {item.get('title','')[:50]}")
            continue

        conf = _adjust_confidence(raw, relevance)
        if relevance == "uncertain":
            conf = min(conf, 0.75)

        result = {
            "law_id":               item["law_id"],
            "title":                item.get("title", ""),
            "issued_at":            item.get("issued_at", ""),
            # v3 추가 필드 (수동 검증용)
            "question_summary":     detail.get("질의요지", "")[:200],
            "answer":               detail.get("회답", "")[:200],
            "reason":               detail.get("이유", "")[:200],
            "related_laws":         detail.get("관련법령", "")[:200],
            "relevance":            relevance,
            "hazard_candidates":    [c for c in raw.get("hazard_candidates",    []) if c in valid_h],
            "work_type_candidates": [c for c in raw.get("work_type_candidates", []) if c in valid_w],
            "equipment_candidates": [c for c in raw.get("equipment_candidates", []) if c in valid_e],
            "confidence":           conf,
            "evidence_spans":       (raw.get("evidence_spans") or [])[:2],
            "needs_review":         conf < 0.6,
            "ai_model":             model,
            "classified_at":        _now(),
            "source":               "ai_classifier_v3",
        }
        results.append(result)

        h_n = len(result["hazard_candidates"])
        w_n = len(result["work_type_candidates"])
        e_n = len(result["equipment_candidates"])
        tag = "OK  " if not result["needs_review"] else "?   "
        print(f"  [{idx:3d}/{len(sample)}] {tag} conf={conf:.2f} H:{h_n} W:{w_n} E:{e_n}  {item.get('title','')[:40]}")

    _save_maps(results, model, limit, offset)
    _report(results, bucket_count, ai_call_count, full_run, physical_only, verify)


# ─── 진입점 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",         type=int,  default=100, help="처리 건수")
    parser.add_argument("--offset",        type=int,  default=0,   help="시작 위치")
    parser.add_argument("--physical-only", action="store_true",    help="물리적 위험 타이틀 필터 풀")
    parser.add_argument("--full-run",      action="store_true",    help="전량 실행")
    parser.add_argument("--verify",        action="store_true",    help="샘플 20건 수동 검증 출력")
    args = parser.parse_args()
    run(
        limit=args.limit,
        offset=args.offset,
        physical_only=args.physical_only,
        full_run=args.full_run,
        verify=args.verify,
    )

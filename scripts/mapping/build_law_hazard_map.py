"""
build_law_hazard_map.py
위험요인 코드(hazards.json) ↔ 정규화 법령(safety_laws_normalized.json) 초안 매핑 생성.

출력:
  data/risk_db/law_mapping/law_hazard_map.json               (score >= 60, draft)
  data/risk_db/law_mapping/law_hazard_map_review_needed.json (score < 60 또는 검토 필요)

실행:
  python scripts/mapping/build_law_hazard_map.py
"""

import json
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HAZARD_FILE = os.path.join(BASE_DIR, "data/risk_db/hazard_action/hazards.json")
LAW_FILE    = os.path.join(BASE_DIR, "data/risk_db/law_normalized/safety_laws_normalized.json")
OUT_DIR     = os.path.join(BASE_DIR, "data/risk_db/law_mapping")
OUT_DRAFT   = os.path.join(OUT_DIR, "law_hazard_map.json")
OUT_REVIEW  = os.path.join(OUT_DIR, "law_hazard_map_review_needed.json")

# ---------------------------------------------------------------------------
# source 우선순위
# ---------------------------------------------------------------------------
SOURCE_RANK = {"statute": 1, "admin_rule": 2, "licbyl": 3, "interpretation": 4}

DRAFT_SCORE_THRESHOLD = 60
MAX_DRAFT_PER_HAZARD  = 5

# ---------------------------------------------------------------------------
# 고정 seed 매핑  (§11 최소 시드 규칙)
# raw_id → (score, match_type, keywords)
# 근거: hazards.json의 source 필드에 명시된 법령 조문 번호
# ---------------------------------------------------------------------------
SEED_MAP: dict[str, dict[str, tuple[int, str, list[str]]]] = {
    # hazard_code: { raw_id: (score, match_type, keywords) }

    # 산업안전보건기준에 관한 규칙 (273603) — 거의 모든 위험요인의 직접 규정 근거
    # (약칭 안전보건규칙, 고용노동부령)
    "FALL":     {"273603": (95, "manual_seed", ["추락방지", "안전난간", "작업발판"])},
    "DROP":     {"273603": (92, "manual_seed", ["낙하물", "낙하물 방지망"])},
    "ELEC":     {"273603": (95, "manual_seed", ["전기", "전로", "충전", "접지"])},
    "ASPHYX":   {"273603": (95, "manual_seed", ["산소결핍", "밀폐공간", "유해가스"])},
    "FIRE":     {"273603": (92, "manual_seed", ["인화성", "화기", "가연물"])},
    "EXPLO":    {"273603": (92, "manual_seed", ["폭발", "가연성 가스", "압력"])},
    "COLLIDE":  {"273603": (90, "manual_seed", ["충돌", "차량계 건설기계"])},
    "COLLAPSE": {"273603": (92, "manual_seed", ["붕괴", "흙막이", "동바리"])},
    "ENTRAP":   {"273603": (93, "manual_seed", ["협착", "끼임", "회전체"])},
    "CUT":      {"273603": (85, "manual_seed", ["절단", "회전날"])},
    "POISON":   {"273603": (85, "manual_seed", ["화학물질", "흡입"])},
    "DUST":     {"273603": (92, "manual_seed", ["분진", "용접흄", "석면"])},
    "NOISE":    {"273603": (92, "manual_seed", ["소음"])},
    "CHEM":     {"273603": (88, "manual_seed", ["화학물질", "누출"])},
    "TRIP":     {"273603": (85, "manual_seed", ["전도", "미끄러짐"])},
    "BURN":     {"273603": (88, "manual_seed", ["화상", "화기취급", "고온"])},
    "FLYBY":    {"273603": (88, "manual_seed", ["비래", "파편"])},
}

# 산업안전보건법 (276853) — 모든 위험요인의 상위 의무 규정 (rule_based_inference)
STATUTE_PARENT_RAW_ID = "276853"
STATUTE_PARENT_SCORE  = 80

# 건설업 산업안전보건관리비 계상 및 사용기준 (2100000254546)
# 건설 작업 위험요인에만 보조 적용
CONSTRUCTION_ADMIN_RULE_ID = "2100000254546"
CONSTRUCTION_HAZARDS = {"FALL", "DROP", "COLLAPSE", "COLLIDE"}
CONSTRUCTION_ADMIN_SCORE = 65

# ---------------------------------------------------------------------------
# 키워드 검색 대상: 해석례(interpretation) 제목에서만 keyword 검색
# 이유: statute/licbyl 제목은 일반 명칭 → 위험요인 특정 불가
# ---------------------------------------------------------------------------
HAZARD_SEARCH_KEYWORDS: dict[str, list[str]] = {
    "FALL":     ["추락", "안전난간"],
    "DROP":     ["낙하"],
    "ELEC":     ["감전", "전기"],
    "ASPHYX":   ["질식", "산소결핍", "밀폐공간"],
    "FIRE":     ["화재"],
    "EXPLO":    ["폭발"],
    "COLLIDE":  ["충돌"],
    "COLLAPSE": ["붕괴"],
    "ENTRAP":   ["협착", "끼임"],
    "CUT":      ["절단"],
    "POISON":   ["중독"],
    "DUST":     ["분진", "석면", "용접흄"],
    "NOISE":    ["소음"],
    "CHEM":     ["화학물질", "유해물질"],
    "TRIP":     ["전도", "미끄러짐"],
    "BURN":     ["화상"],
    "FLYBY":    ["비래", "파편"],
}


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_law_id(law: dict) -> str:
    return f"{law['category']}:{law['raw_id']}"


def score_law_for_hazard(hazard_code: str, law: dict) -> tuple[int, str, list[str]]:
    """(score, match_type, matched_keywords) 반환. score 0 = 매핑 없음."""
    raw_id   = law.get("raw_id", "")
    category = law.get("category", "")
    title    = law.get("title_ko", "")

    # 1. seed 매핑 — 코드 기반, 최우선
    seed = SEED_MAP.get(hazard_code, {})
    if raw_id in seed:
        sc, mt, kws = seed[raw_id]
        return sc, mt, kws

    # 2. 산업안전보건법(부모법) — 모든 hazard에 rule_based_inference
    if raw_id == STATUTE_PARENT_RAW_ID and category == "statute":
        return STATUTE_PARENT_SCORE, "rule_based_inference", []

    # 3. 건설업 관리비 고시 — 건설 위험요인만
    if raw_id == CONSTRUCTION_ADMIN_RULE_ID and hazard_code in CONSTRUCTION_HAZARDS:
        return CONSTRUCTION_ADMIN_SCORE, "rule_based_inference", []

    # 4. interpretation(해석례) — 제목 키워드 검색
    if category == "interpretation":
        kws = HAZARD_SEARCH_KEYWORDS.get(hazard_code, [])
        matched = [kw for kw in kws if kw in title]
        if len(matched) >= 2:
            return 82, "exact_keyword", matched
        if len(matched) == 1:
            return 68, "partial_keyword", matched

    return 0, "", []


def main():
    hazard_db = load_json(HAZARD_FILE)
    law_db    = load_json(LAW_FILE)

    hazards = hazard_db["hazards"]
    laws    = law_db["items"]
    now     = datetime.now(timezone.utc).isoformat()

    draft_items: list[dict] = []
    review_items: list[dict] = []

    for hazard in hazards:
        hcode = hazard["code"]
        hname = hazard["name_ko"]

        scored: list[tuple[int, dict, str, list]] = []

        for law in laws:
            score, match_type, matched_kws = score_law_for_hazard(hcode, law)
            if score == 0:
                continue
            scored.append((score, law, match_type, matched_kws))

        # 정렬: score 내림차순 → source 우선순위
        scored.sort(key=lambda x: (-x[0], SOURCE_RANK.get(x[1]["category"], 9)))

        per_draft  = []
        per_review = []

        for score, law, match_type, matched_kws in scored:
            law_id = build_law_id(law)
            item_full = {
                "hazard_code": hcode,
                "hazard_name": hname,
                "law_id": law_id,
                "law_title": law["title_ko"],
                "law_category": law["category"],
                "law_document_type": law["document_type"],
                "law_source_target": law.get("source_target", ""),
                "match_type": match_type,
                "match_score": score,
                "match_keywords": matched_kws,
                "reason_summary": _reason(hcode, law, score, matched_kws),
                "detail_link": law.get("detail_link", ""),
                "reference_no": law.get("reference_no", ""),
                "ministry_name": law.get("ministry_name", ""),
                "review_status": "draft",
                "created_at": now,
                "source": "law_hazard_map_builder",
            }
            candidate = {
                "hazard_code": hcode,
                "hazard_name": hname,
                "candidate_law_id": law_id,
                "candidate_law_title": law["title_ko"],
                "candidate_category": law["category"],
                "candidate_score": score,
                "reason": item_full["reason_summary"],
                "match_keywords": matched_kws,
                "detail_link": law.get("detail_link", ""),
            }

            if score < DRAFT_SCORE_THRESHOLD:
                per_review.append(candidate)
            elif len(per_draft) < MAX_DRAFT_PER_HAZARD:
                per_draft.append(item_full)
            else:
                candidate["reason"] = "draft 초과(5건 제한) → review_needed"
                per_review.append(candidate)

        draft_items.extend(per_draft)
        review_items.extend(per_review)

    os.makedirs(OUT_DIR, exist_ok=True)

    draft_out = {
        "generated_at": now,
        "source_law_file": "data/risk_db/law_normalized/safety_laws_normalized.json",
        "source_hazard_file": "data/risk_db/hazard_action/hazards.json",
        "item_count": len(draft_items),
        "items": draft_items,
    }
    review_out = {
        "generated_at": now,
        "item_count": len(review_items),
        "items": review_items,
    }

    with open(OUT_DRAFT, "w", encoding="utf-8") as f:
        json.dump(draft_out, f, ensure_ascii=False, indent=2)
    with open(OUT_REVIEW, "w", encoding="utf-8") as f:
        json.dump(review_out, f, ensure_ascii=False, indent=2)

    print(f"[완료] draft={len(draft_items)}건, review_needed={len(review_items)}건")
    _print_stats(draft_items)


def _reason(hcode: str, law: dict, score: int, matched_kws: list) -> str:
    cat_map = {
        "statute":        "법률/명령",
        "admin_rule":     "고시",
        "licbyl":         "별표·서식",
        "interpretation": "해석례",
    }
    cat = cat_map.get(law["category"], law["category"])
    if matched_kws:
        return (
            f"{cat} '{law['title_ko']}' — "
            f"키워드 포함: {', '.join(matched_kws[:3])}"
        )
    if score >= 90:
        return f"{cat} '{law['title_ko']}' — {hcode} 위험요인 직접 규정 (seed)"
    return f"{cat} '{law['title_ko']}' — {hcode} 위험요인 상위/보조 법규"


def _print_stats(items: list[dict]):
    from collections import Counter
    cat_dist   = Counter(i["law_category"] for i in items)
    score_dist = {"90-100": 0, "75-89": 0, "60-74": 0}
    for i in items:
        s = i["match_score"]
        if s >= 90:
            score_dist["90-100"] += 1
        elif s >= 75:
            score_dist["75-89"] += 1
        else:
            score_dist["60-74"] += 1
    print(f"  source 분포: {dict(cat_dist)}")
    print(f"  score 분포:  {score_dist}")


if __name__ == "__main__":
    main()

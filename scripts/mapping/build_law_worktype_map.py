"""
build_law_worktype_map.py
작업유형(work_types.json) ↔ 정규화 법령(safety_laws_normalized.json) 초안 매핑 생성.

매핑 단위: work_type (132개)
sub_type(85개)은 score/keywords 보정에만 참조 — 필드에 빈값 허용(지시문 §3)

출력:
  data/risk_db/law_mapping/law_worktype_map.json          (score >= 60, draft)
  data/risk_db/law_mapping/law_worktype_map_review_needed.json

실행:
  python scripts/mapping/build_law_worktype_map.py
"""

import json
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WORKTYPE_FILE    = os.path.join(BASE_DIR, "data/risk_db/work_taxonomy/work_types.json")
WORKSUB_FILE     = os.path.join(BASE_DIR, "data/risk_db/work_taxonomy/work_sub_types.json")
LAW_FILE         = os.path.join(BASE_DIR, "data/risk_db/law_normalized/safety_laws_normalized.json")
OUT_DIR          = os.path.join(BASE_DIR, "data/risk_db/law_mapping")
OUT_DRAFT        = os.path.join(OUT_DIR, "law_worktype_map.json")
OUT_REVIEW       = os.path.join(OUT_DIR, "law_worktype_map_review_needed.json")

# ---------------------------------------------------------------------------
# source 우선순위
# ---------------------------------------------------------------------------
SOURCE_RANK = {"statute": 1, "admin_rule": 2, "licbyl": 3, "interpretation": 4}

DRAFT_SCORE_THRESHOLD = 60
MAX_DRAFT_PER_WORKTYPE = 5

# ---------------------------------------------------------------------------
# 산업안전보건기준에 관한 규칙 (raw_id: 273603) — 거의 모든 건설 작업의 직접 기준
# 산업안전보건법             (raw_id: 276853) — 상위 의무 규정
# 건설업 산업안전보건관리비   (raw_id: 2100000254546) — 건설업 전용 보조
# ---------------------------------------------------------------------------
SAFETYCODE_ID      = "273603"
PARENT_LAW_ID      = "276853"
CONST_ADMIN_ID     = "2100000254546"
RISK_ASSESS_ID     = "2100000251014"

# ---------------------------------------------------------------------------
# trade_code → [(raw_id, score_at_risk3, match_type, keywords)]
# score_at_risk3: risk_level=3 기준 score.
# risk_level=2이면 -5, risk_level=1이면 -15 적용.
# ---------------------------------------------------------------------------
TRADE_SEED_MAP: dict[str, list[tuple]] = {
    # 토공
    "CIVIL":      [(SAFETYCODE_ID, 90, "manual_seed", ["굴착", "흙막이", "사면"])],
    # 기초
    "FOUND":      [(SAFETYCODE_ID, 85, "manual_seed", ["항타기", "천공", "말뚝"])],
    # RC공
    "RC":         [(SAFETYCODE_ID, 88, "manual_seed", ["거푸집", "동바리", "콘크리트"])],
    # 철골
    "STEEL":      [(SAFETYCODE_ID, 90, "manual_seed", ["철골", "양중", "고소"])],
    # 가설
    "TEMP":       [(SAFETYCODE_ID, 93, "manual_seed", ["비계", "작업발판", "사다리", "개구부"])],
    # 전기
    "ELEC":       [(SAFETYCODE_ID, 93, "manual_seed", ["전기", "전로", "감전"])],
    # 용접·절단
    "WELD":       [(SAFETYCODE_ID, 90, "manual_seed", ["용접", "화기", "절단", "가스"])],
    # 배관
    "PIPE":       [(SAFETYCODE_ID, 82, "manual_seed", ["배관", "용접", "압력"])],
    # 도장
    "PAINT":      [(SAFETYCODE_ID, 85, "manual_seed", ["유기화합물", "도장", "뿜칠"])],
    # 해체·철거
    "DEMO":       [(SAFETYCODE_ID, 88, "manual_seed", ["해체", "철거", "낙하"])],
    # 상하수도
    "WATER":      [(SAFETYCODE_ID, 92, "manual_seed", ["밀폐공간", "산소결핍", "맨홀"])],
    # 기계·중장비
    "MECH":       [(SAFETYCODE_ID, 90, "manual_seed", ["크레인", "양중", "지게차"])],
    # 방수
    "WATERP":     [(SAFETYCODE_ID, 80, "manual_seed", ["고소", "추락"])],
    # 지붕
    "ROOFING":    [(SAFETYCODE_ID, 85, "manual_seed", ["지붕", "고소", "추락"])],
    # 기계설비
    "HVAC":       [(SAFETYCODE_ID, 78, "manual_seed", ["보일러", "고압"])],
    # 터널
    "TUNNEL":     [(SAFETYCODE_ID, 90, "manual_seed", ["굴착", "밀폐공간", "발파"])],
    # 도로포장
    "ROAD":       [(SAFETYCODE_ID, 75, "manual_seed", ["차량계", "아스팔트"])],
    # 조적
    "MASON":      [(SAFETYCODE_ID, 75, "manual_seed", ["외벽", "고소"])],
    # 목공
    "CARPENTRY":  [(SAFETYCODE_ID, 80, "manual_seed", ["거푸집", "고소"])],
    # 창호
    "WINDOW":     [(SAFETYCODE_ID, 78, "manual_seed", ["고소", "유리"])],
    # 교량
    "BRIDGE":     [(SAFETYCODE_ID, 88, "manual_seed", ["고소", "양중", "교량"])],
    # 소방
    "FIRE":       [(SAFETYCODE_ID, 70, "manual_seed", ["소방"])],
    # 통신
    "COMM":       [(SAFETYCODE_ID, 70, "manual_seed", ["안테나", "고소"])],
    # 조경
    "LANDSCAPE":  [(SAFETYCODE_ID, 65, "manual_seed", [])],
    # 보온단열
    "INSUL":      [(SAFETYCODE_ID, 70, "manual_seed", ["보온", "단열"])],
    # 바닥마감
    "FLOOR":      [(SAFETYCODE_ID, 65, "manual_seed", [])],
    # 양중
    "LIFT":       [(SAFETYCODE_ID, 92, "manual_seed", ["양중", "크레인", "줄걸이"])],
    # 프리스트레스
    "PRESTRESS":  [(SAFETYCODE_ID, 85, "manual_seed", ["양중", "긴장"])],
    # 환경관리
    "ENVIRON":    [(SAFETYCODE_ID, 85, "manual_seed", ["석면", "분진"]),
                   (PARENT_LAW_ID, 88, "manual_seed", ["석면"])],
}

# ---------------------------------------------------------------------------
# 작업유형 개별 override (trade seed 대신 또는 추가 적용)
# work_type_code → [(raw_id, score, match_type, keywords)]
# ---------------------------------------------------------------------------
WORKTYPE_OVERRIDE: dict[str, list[tuple]] = {
    # 석면 직접 규정: 산안법 제122조
    "DEMO_ASBESTOS": [(PARENT_LAW_ID, 92, "manual_seed", ["석면해체", "제거"])],
    "ENV_ASBESTOS":  [(PARENT_LAW_ID, 92, "manual_seed", ["석면해체", "제거"])],
    # 활선: 산안규칙 제301조 + 전기설비기술기준 + 위험성평가지침
    "ELEC_LIVE":     [
        (SAFETYCODE_ID,       95, "manual_seed", ["활선", "전로", "충전"]),
        ("2100000267908",     90, "manual_seed", ["전기설비", "전기안전"]),  # 전기설비기술기준
        (RISK_ASSESS_ID,      88, "manual_seed", ["위험성평가"]),
    ],
    # 맨홀(밀폐공간): 산안규칙 제619조 + 산안법 + 위험성평가지침
    "WATER_MANHOLE": [
        (SAFETYCODE_ID,       95, "manual_seed", ["밀폐공간", "산소결핍", "맨홀"]),
        (PARENT_LAW_ID,       90, "manual_seed", ["밀폐공간", "산소결핍"]),
        (RISK_ASSESS_ID,      88, "manual_seed", ["위험성평가"]),
    ],
    # 타워크레인·이동식 크레인: 산안규칙 제140~149조
    "MECH_CRANE":    [(SAFETYCODE_ID, 93, "manual_seed", ["크레인", "타워크레인", "양중"])],
    # 지게차: 산안규칙 제177조
    "MECH_FORKLIFT": [(SAFETYCODE_ID, 90, "manual_seed", ["지게차", "협착"])],
    # 가스 용접: 산안규칙 제232조 (폭발 위험)
    "WELD_GAS":      [(SAFETYCODE_ID, 92, "manual_seed", ["가스용접", "폭발", "아세틸렌"])],
    "WELD_GAS_CUT":  [(SAFETYCODE_ID, 90, "manual_seed", ["가스절단", "화기"])],
    # 밀폐공간 아크 용접: 산안규칙 제619조 + 제241조
    "WELD_ARC":      [(SAFETYCODE_ID, 90, "manual_seed", ["용접", "밀폐공간", "화기"])],
    # 철골 인양: 산안규칙 제153조
    "STEEL_LIFT":    [(SAFETYCODE_ID, 92, "manual_seed", ["철골", "크레인", "인양"])],
    # 리깅·줄걸이: 산안규칙 제153조 + 산안법 + 위험성평가지침
    "LIFT_RIGGING":  [
        (SAFETYCODE_ID,       93, "manual_seed", ["줄걸이", "인양", "달기"]),
        (PARENT_LAW_ID,       90, "manual_seed", ["크레인", "양중", "인양"]),
        (RISK_ASSESS_ID,      88, "manual_seed", ["위험성평가"]),
    ],
    "LIFT_CRANE_OP": [(SAFETYCODE_ID, 92, "manual_seed", ["크레인", "인양", "양중"])],
    # 분전반: 산안규칙 제303조
    "ELEC_PANEL":    [(SAFETYCODE_ID, 92, "manual_seed", ["분전반", "전기", "감전"])],
    # 비계: 산안규칙 제59조, 제68조 + 산안법 + 건설업관리비 고시
    "TEMP_SCAFF":    [
        (SAFETYCODE_ID,       93, "manual_seed", ["비계", "발판", "추락"]),
        (PARENT_LAW_ID,       88, "manual_seed", ["추락", "비계"]),
        (CONST_ADMIN_ID,      88, "manual_seed", ["건설안전", "추락재해"]),
    ],
    "TEMP_SCAFF_DM": [(SAFETYCODE_ID, 93, "manual_seed", ["비계해체", "추락"])],
    # 개구부: 산안규칙 제42조
    "TEMP_OPEN":     [(SAFETYCODE_ID, 93, "manual_seed", ["개구부", "추락"])],
    # 유기용제 도장: 산안규칙 제616조
    "PAINT_SPRAY":   [(SAFETYCODE_ID, 88, "manual_seed", ["유기화합물", "도장", "폭발"])],
    "PAINT_ANTICORR":[(SAFETYCODE_ID, 85, "manual_seed", ["방청", "도장", "유기화합물"])],
    # 터널 발파: 화약류관리법(DB 미수록) → 산안규칙 밀폐공간 규정
    "TUNNEL_DRILL":  [(SAFETYCODE_ID, 92, "manual_seed", ["굴착", "밀폐공간", "분진"])],
    "TUNNEL_SHOT":   [(SAFETYCODE_ID, 88, "manual_seed", ["숏크리트", "밀폐공간", "분진"])],
}

# ---------------------------------------------------------------------------
# 해석례(interpretation) 제목 키워드 검색
# work_type_code → [키워드]
# ---------------------------------------------------------------------------
INTERP_KEYWORDS: dict[str, list[str]] = {
    "TEMP_SCAFF":    ["추락", "안전난간"],
    "TEMP_SCAFF_DM": ["추락", "안전난간"],
    "TEMP_OPEN":     ["추락", "안전난간"],
    "TEMP_AWP":      ["추락", "안전난간"],
    "TEMP_LADDER":   ["추락"],
    "STEEL_ASSEM":   ["추락", "안전난간"],
    "STEEL_BOLT":    ["추락"],
    "BRDG_DECK":     ["추락"],
    "DEMO_ASBESTOS": ["석면"],
    "ENV_ASBESTOS":  ["석면"],
    "DEMO_STRUCT":   ["석면"],
}

# 건설업관리비 고시 적용 trade 목록 (건설 직종)
CONST_TRADES = {
    "CIVIL","FOUND","RC","STEEL","TEMP","WELD","PIPE","PAINT","DEMO",
    "WATER","MECH","WATERP","ROOFING","HVAC","TUNNEL","ROAD","MASON",
    "CARPENTRY","WINDOW","BRIDGE","FIRE","COMM","LANDSCAPE","INSUL",
    "FLOOR","LIFT","PRESTRESS","ENVIRON",
}


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_law_id(law: dict) -> str:
    return f"{law['category']}:{law['raw_id']}"


def get_law_by_raw_id(laws: list[dict], raw_id: str) -> dict | None:
    for law in laws:
        if law.get("raw_id") == raw_id:
            return law
    return None


def score_for_worktype(
    wt_code: str,
    wt_trade: str,
    wt_risk: int,
    law: dict,
    laws_index: dict[str, dict],
) -> tuple[int, str, list[str]]:
    """
    (score, match_type, matched_keywords) 반환. score 0 = 매핑 없음.
    우선순위: WORKTYPE_OVERRIDE > TRADE_SEED_MAP > 건설업관리비 > 해석례 키워드
    """
    raw_id   = law.get("raw_id", "")
    category = law.get("category", "")
    title    = law.get("title_ko", "")

    risk_penalty = {3: 0, 2: -5, 1: -15}.get(wt_risk, -15)

    # 1. 작업유형 개별 override
    if wt_code in WORKTYPE_OVERRIDE:
        for oid, base_score, mtype, kws in WORKTYPE_OVERRIDE[wt_code]:
            if raw_id == oid:
                score = max(DRAFT_SCORE_THRESHOLD, base_score + risk_penalty)
                return score, mtype, kws
        # override 있는 작업유형은 trade seed를 skip하고 override만 사용
        # (단, 추가 법령들은 아래에서 처리)

    # 2. trade seed map
    seeds = TRADE_SEED_MAP.get(wt_trade, [])
    for oid, base_score, mtype, kws in seeds:
        if raw_id == oid:
            # override가 같은 law를 이미 처리했으면 중복 방지
            if wt_code in WORKTYPE_OVERRIDE:
                for oid2, _, _, _ in WORKTYPE_OVERRIDE[wt_code]:
                    if raw_id == oid2:
                        return 0, "", []  # override가 이미 처리
            score = base_score + risk_penalty
            if score < DRAFT_SCORE_THRESHOLD:
                return score, mtype, kws  # review_needed 후보
            return score, mtype, kws

    # 3. 산업안전보건법(부모법) — risk_level=3 고위험 작업에만 보조 연결
    if raw_id == PARENT_LAW_ID and category == "statute":
        # ENVIRON는 이미 trade seed에 포함됨
        if wt_trade != "ENVIRON":
            if wt_risk == 3:
                return 78, "rule_based_inference", []
            else:
                return 52, "rule_based_inference", []  # review_needed

    # 4. 건설업 산업안전보건관리비 — 건설 직종 risk_level=3 작업만
    if raw_id == CONST_ADMIN_ID:
        if wt_trade in CONST_TRADES and wt_risk == 3:
            return 63, "rule_based_inference", []

    # 5. 해석례 keyword search
    if category == "interpretation":
        kws_target = INTERP_KEYWORDS.get(wt_code, [])
        if kws_target:
            matched = [kw for kw in kws_target if kw in title]
            if len(matched) >= 2:
                return 80, "exact_keyword", matched
            if len(matched) == 1:
                return 65, "partial_keyword", matched

    return 0, "", []


def main():
    wt_db  = load_json(WORKTYPE_FILE)
    law_db = load_json(LAW_FILE)

    work_types = wt_db["work_types"]
    laws       = law_db["items"]
    now        = datetime.now(timezone.utc).isoformat()

    # law lookup by raw_id
    laws_index = {law["raw_id"]: law for law in laws}

    draft_items:  list[dict] = []
    review_items: list[dict] = []

    for wt in work_types:
        wt_code  = wt["code"]
        wt_name  = wt["name_ko"]
        wt_trade = wt.get("trade_code", "")
        wt_risk  = wt.get("risk_level", 2)

        scored: list[tuple[int, dict, str, list]] = []

        for law in laws:
            score, match_type, matched_kws = score_for_worktype(
                wt_code, wt_trade, wt_risk, law, laws_index
            )
            if score == 0:
                continue
            scored.append((score, law, match_type, matched_kws))

        # 정렬: score 내림차순 → source 우선순위
        scored.sort(
            key=lambda x: (-x[0], SOURCE_RANK.get(x[1]["category"], 9))
        )

        per_draft:  list[dict] = []
        per_review: list[dict] = []

        for score, law, match_type, matched_kws in scored:
            law_id    = build_law_id(law)
            item_full = {
                "work_type_code":     wt_code,
                "work_type_name":     wt_name,
                "work_sub_type_code": "",
                "work_sub_type_name": "",
                "law_id":             law_id,
                "law_title":          law["title_ko"],
                "law_category":       law["category"],
                "law_document_type":  law["document_type"],
                "law_source_target":  law.get("source_target", ""),
                "match_type":         match_type,
                "match_score":        score,
                "match_keywords":     matched_kws,
                "reason_summary":     _reason(wt_code, wt_name, law, score, matched_kws),
                "detail_link":        law.get("detail_link", ""),
                "reference_no":       law.get("reference_no", ""),
                "ministry_name":      law.get("ministry_name", ""),
                "review_status":      "draft",
                "created_at":         now,
                "source":             "law_worktype_map_builder",
            }
            candidate = {
                "work_type_code":      wt_code,
                "work_type_name":      wt_name,
                "work_sub_type_code":  "",
                "work_sub_type_name":  "",
                "candidate_law_id":    law_id,
                "candidate_law_title": law["title_ko"],
                "candidate_category":  law["category"],
                "candidate_score":     score,
                "reason":              item_full["reason_summary"],
                "match_keywords":      matched_kws,
                "detail_link":         law.get("detail_link", ""),
            }

            if score < DRAFT_SCORE_THRESHOLD:
                per_review.append(candidate)
            elif len(per_draft) < MAX_DRAFT_PER_WORKTYPE:
                per_draft.append(item_full)
            else:
                candidate["reason"] = "draft 초과(5건 제한) → review_needed"
                per_review.append(candidate)

        draft_items.extend(per_draft)
        review_items.extend(per_review)

    os.makedirs(OUT_DIR, exist_ok=True)

    draft_out = {
        "generated_at":        now,
        "source_law_file":     "data/risk_db/law_normalized/safety_laws_normalized.json",
        "source_worktype_file":"data/risk_db/work_taxonomy/work_types.json",
        "item_count":          len(draft_items),
        "items":               draft_items,
    }
    review_out = {
        "generated_at": now,
        "item_count":   len(review_items),
        "items":        review_items,
    }

    with open(OUT_DRAFT, "w", encoding="utf-8") as f:
        json.dump(draft_out, f, ensure_ascii=False, indent=2)
    with open(OUT_REVIEW, "w", encoding="utf-8") as f:
        json.dump(review_out, f, ensure_ascii=False, indent=2)

    print(f"[완료] draft={len(draft_items)}건, review_needed={len(review_items)}건")
    _print_stats(draft_items, len(work_types))


def _reason(wt_code: str, wt_name: str, law: dict, score: int, matched_kws: list) -> str:
    cat_map = {
        "statute":        "법률/명령",
        "admin_rule":     "고시",
        "licbyl":         "별표·서식",
        "interpretation": "해석례",
    }
    cat = cat_map.get(law["category"], law["category"])
    if matched_kws:
        return (
            f"[{wt_name}] {cat} '{law['title_ko']}' — "
            f"키워드: {', '.join(matched_kws[:3])}"
        )
    if score >= 88:
        return f"[{wt_name}] {cat} '{law['title_ko']}' — 직접 규정 (seed)"
    return f"[{wt_name}] {cat} '{law['title_ko']}' — 상위/보조 법규"


def _print_stats(items: list[dict], total_wt: int):
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

    wt_counts = Counter(i["work_type_code"] for i in items)
    avg = len(items) / total_wt if total_wt else 0
    print(f"  총 work_type: {total_wt}")
    print(f"  draft 평균:   {avg:.2f}건/work_type")
    print(f"  source 분포:  {dict(cat_dist)}")
    print(f"  score 분포:   {score_dist}")


if __name__ == "__main__":
    main()

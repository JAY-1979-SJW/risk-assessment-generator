"""
6단계 — law_control_map 초안 생성
입력: controls_normalized.json, safety_laws_normalized.json
출력: law_control_map.json, law_control_map_review_needed.json
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "risk_db"

INPUT_CONTROLS = DATA / "hazard_action_normalized" / "controls_normalized.json"
INPUT_LAWS     = DATA / "law_normalized" / "safety_laws_normalized.json"
REF_HAZARD_MAP = DATA / "law_mapping" / "law_hazard_map.json"

OUT_DRAFT      = DATA / "law_mapping" / "law_control_map.json"
OUT_REVIEW     = DATA / "law_mapping" / "law_control_map_review_needed.json"

SAFETYCODE_ID  = "statute:273603"
PARENTLAW_ID   = "statute:276853"

# 안전난간 관련 해석례 (FALL 보조 secondary)
FALL_GUARDRAIL_INTERP = "interpretation:313846"
FALL_GUARDRAIL_KEYWORDS = ["안전난간", "추락방지"]

# secondary 연결 허용 control_code (안전난간 관련 FALL 2건)
SECONDARY_MAP: dict[str, list[tuple]] = {
    "FALL_C01": [(FALL_GUARDRAIL_INTERP, 72, "related_law_match",
                  ["안전난간", "추락"],
                  "추락 위험 방지 안전난간 설치작업 지휘 관련 해석례 보조 근거")],
    "FALL_C11": [(FALL_GUARDRAIL_INTERP, 72, "related_law_match",
                  ["안전난간", "개구부"],
                  "개구부 안전난간 설치 관련 해석례 보조 근거")],
}

# ──────────────────────────────────────────────
# 법령 인덱스 로드
# ──────────────────────────────────────────────

def load_law_index(path: Path) -> dict[str, dict]:
    """law_id → 법령 상세 메타데이터"""
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    index: dict[str, dict] = {}
    for item in data.get("items", []):
        cat    = item.get("category", "")
        raw_id = str(item.get("raw_id", ""))
        law_id = f"{cat}:{raw_id}"
        index[law_id] = {
            "law_id":          law_id,
            "law_title":       item.get("title_ko", ""),
            "law_category":    cat,
            "law_document_type": item.get("document_type", ""),
            "law_source_target": item.get("source_target", ""),
            "detail_link":     item.get("detail_link", ""),
            "reference_no":    item.get("reference_no", ""),
            "ministry_name":   item.get("ministry_name", ""),
        }
    return index


# ──────────────────────────────────────────────
# score 계산
# ──────────────────────────────────────────────

# base score: (control_type, priority) → score (for statute:273603 only)
SCORE_BASE: dict[tuple, int] = {
    ("engineering", 1): 92,
    ("admin",       1): 88,
    ("ppe",         1): 85,
    ("engineering", 2): 82,
    ("admin",       2): 80,
    ("ppe",         2): 80,
}

DRAFT_THRESHOLD   = 60
MAX_DRAFT_PER_CTL = 3


def calc_score(law_id: str, ctrl_type: str, priority: int, law_ref_raw: str) -> int:
    if law_id == PARENTLAW_ID:
        # 부모법: 직접 근거 명확하나 구체성 낮음
        return 80
    # statute:273603 기본 점수
    base = SCORE_BASE.get((ctrl_type, priority), 78)
    # 절(section) 수준 참조이면 -4 (조문 수준보다 덜 구체적)
    is_section_only = ("절" in law_ref_raw and "조" not in law_ref_raw)
    if is_section_only:
        base -= 4
    return base


def law_ref_article(law_ref_raw: str) -> str:
    """law_ref_raw에서 조문 번호 추출 (보조)"""
    import re
    m = re.search(r"제\d+[a-zA-Z가-힣]*[절조]", law_ref_raw)
    return m.group(0) if m else ""


# ──────────────────────────────────────────────
# 매핑 항목 생성
# ──────────────────────────────────────────────

def make_item(ctrl: dict, law_id: str, law_meta: dict,
              match_type: str, score: int,
              keywords: list[str], reason: str, now: str) -> dict:
    law_ref_raw = ctrl["law_ref_raw"][0] if ctrl["law_ref_raw"] else ""
    return {
        "control_code":      ctrl["control_code"],
        "control_name":      ctrl["control_text"],
        "hazard_code":       ctrl["hazard_code"],
        "hazard_name":       ctrl["hazard_name"],
        "law_id":            law_id,
        "law_title":         law_meta.get("law_title", ""),
        "law_category":      law_meta.get("law_category", ""),
        "law_document_type": law_meta.get("law_document_type", ""),
        "law_source_target": law_meta.get("law_source_target", ""),
        "match_type":        match_type,
        "match_score":       score,
        "match_keywords":    keywords,
        "reason_summary":    reason,
        "detail_link":       law_meta.get("detail_link", ""),
        "reference_no":      law_meta.get("reference_no", ""),
        "ministry_name":     law_meta.get("ministry_name", ""),
        "law_ref_article":   law_ref_article(law_ref_raw),
        "review_status":     "draft",
        "created_at":        now,
        "source":            "law_control_map_builder",
    }


def make_review_item(ctrl: dict, law_id: str, law_meta: dict,
                     score: int, reason: str, keywords: list[str]) -> dict:
    return {
        "control_code":       ctrl["control_code"],
        "control_name":       ctrl["control_text"],
        "hazard_code":        ctrl["hazard_code"],
        "candidate_law_id":   law_id,
        "candidate_law_title": law_meta.get("law_title", ""),
        "candidate_category": law_meta.get("law_category", ""),
        "candidate_score":    score,
        "reason":             reason,
        "match_keywords":     keywords,
        "detail_link":        law_meta.get("detail_link", ""),
    }


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────

def main():
    law_index = load_law_index(INPUT_LAWS)

    with INPUT_CONTROLS.open(encoding="utf-8") as f:
        cn_data = json.load(f)
    controls = cn_data["items"]

    now = datetime.now(timezone.utc).isoformat()
    draft_items:  list[dict] = []
    review_items: list[dict] = []

    # control당 draft 건수 추적
    draft_per_ctrl: dict[str, int] = defaultdict(int)

    for ctrl in controls:
        code     = ctrl["control_code"]
        ctype    = ctrl["control_type"]
        priority = int(ctrl["priority"])
        law_ref  = ctrl["law_ref_raw"][0] if ctrl["law_ref_raw"] else ""

        # 1순위: prelinked_law_ids 처리
        for law_id in ctrl["law_ids"]:
            law_meta = law_index.get(law_id, {})
            score    = calc_score(law_id, ctype, priority, law_ref)
            reason   = f"5.5단계 정규화 law_id ({law_ref})"
            keywords = [kw for kw in ["안전보건기준", "산업안전보건법"]
                        if kw in law_meta.get("law_title", "")]

            if score < DRAFT_THRESHOLD:
                review_items.append(make_review_item(
                    ctrl, law_id, law_meta, score,
                    f"score {score} < {DRAFT_THRESHOLD}: {reason}", keywords))
            elif draft_per_ctrl[code] >= MAX_DRAFT_PER_CTL:
                review_items.append(make_review_item(
                    ctrl, law_id, law_meta, score,
                    f"MAX_DRAFT_PER_CTL({MAX_DRAFT_PER_CTL}) 초과", keywords))
            else:
                draft_items.append(make_item(
                    ctrl, law_id, law_meta,
                    "prelinked_law_id", score, keywords, reason, now))
                draft_per_ctrl[code] += 1

        # 2순위: secondary 연결 (FALL 안전난간 해석례)
        if code in SECONDARY_MAP and draft_per_ctrl[code] < MAX_DRAFT_PER_CTL:
            for (sec_law_id, sec_score, sec_match, sec_kw, sec_reason) in SECONDARY_MAP[code]:
                law_meta = law_index.get(sec_law_id, {})
                if law_meta and sec_score >= DRAFT_THRESHOLD:
                    draft_items.append(make_item(
                        ctrl, sec_law_id, law_meta,
                        sec_match, sec_score, sec_kw, sec_reason, now))
                    draft_per_ctrl[code] += 1
                else:
                    review_items.append(make_review_item(
                        ctrl, sec_law_id, law_meta,
                        sec_score, f"secondary score={sec_score} 또는 미매칭", sec_kw))

    # 결과 저장
    with OUT_DRAFT.open("w", encoding="utf-8") as f:
        json.dump({
            "generated_at":       now,
            "source_control_file": str(INPUT_CONTROLS.relative_to(ROOT)),
            "source_law_file":     str(INPUT_LAWS.relative_to(ROOT)),
            "item_count":          len(draft_items),
            "items":               draft_items,
        }, f, ensure_ascii=False, indent=2)

    with OUT_REVIEW.open("w", encoding="utf-8") as f:
        json.dump({
            "generated_at": now,
            "item_count":   len(review_items),
            "items":        review_items,
        }, f, ensure_ascii=False, indent=2)

    # 보고
    from collections import Counter

    source_dist  = Counter(i["law_category"] for i in draft_items)
    match_dist   = Counter(i["match_type"]   for i in draft_items)
    score_bands  = Counter(
        "90-100" if i["match_score"] >= 90 else
        "75-89"  if i["match_score"] >= 75 else
        "60-74"
        for i in draft_items
    )

    total_ctrls  = len(set(i["control_code"] for i in draft_items))
    avg_per_ctrl = len(draft_items) / max(total_ctrls, 1)

    print(f"[완료] {OUT_DRAFT.name}   : {len(draft_items)}건")
    print(f"[완료] {OUT_REVIEW.name}  : {len(review_items)}건")
    print()
    print("=== 총 통계 ===")
    print(f"  총 control 수   : 90")
    print(f"  총 law 수       : 52")
    print(f"  draft 매핑      : {len(draft_items)}건")
    print(f"  review_needed   : {len(review_items)}건")
    print(f"  control당 평균  : {avg_per_ctrl:.2f}건")
    print()
    print("=== source(category) 분포 ===")
    for k, v in sorted(source_dist.items()):
        print(f"  {k}: {v}")
    print()
    print("=== match_type 분포 ===")
    for k, v in sorted(match_dist.items()):
        print(f"  {k}: {v}")
    print()
    print("=== score 분포 ===")
    for k in ["90-100", "75-89", "60-74"]:
        print(f"  {k}: {score_bands.get(k, 0)}")
    print()
    print("=== 대표 예시 5건 ===")
    shown = set()
    cnt = 0
    for item in draft_items:
        if cnt >= 5:
            break
        code = item["control_code"]
        if code not in shown:
            print(f"  {code} | {item['control_name'][:35]} | {item['law_id']} | score={item['match_score']}")
            shown.add(code)
            cnt += 1


if __name__ == "__main__":
    main()

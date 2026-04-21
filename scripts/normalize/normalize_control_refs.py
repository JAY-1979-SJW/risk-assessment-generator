"""
5.5단계 — control_code 기준 확정 및 law_ref → law_id 정규화
입력: hazard_controls.json, hazards.json, safety_laws_normalized.json
출력: controls_normalized.json, controls_review_needed.json,
       control_law_ref_candidates.json
"""

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "risk_db"

INPUT_CONTROLS  = DATA / "hazard_action" / "hazard_controls.json"
INPUT_HAZARDS   = DATA / "hazard_action" / "hazards.json"
INPUT_LAWS      = DATA / "law_normalized" / "safety_laws_normalized.json"

OUT_DIR         = DATA / "hazard_action_normalized"
OUT_NORM        = OUT_DIR / "controls_normalized.json"
OUT_REVIEW      = OUT_DIR / "controls_review_needed.json"
OUT_CANDIDATES  = DATA / "law_mapping" / "control_law_ref_candidates.json"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# 법령 기준 로드
# ──────────────────────────────────────────────

def load_laws(path: Path) -> dict[str, dict]:
    """raw_id → {law_id, title_ko, category} 인덱스"""
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", [])
    index: dict[str, dict] = {}
    for item in items:
        raw_id = str(item.get("raw_id", ""))
        cat    = item.get("category", "statute")
        law_id = f"{cat}:{raw_id}"
        index[raw_id] = {
            "law_id":    law_id,
            "title_ko":  item.get("title_ko", ""),
            "category":  cat,
        }
    return index


def load_hazards(path: Path) -> dict[str, str]:
    """hazard_code → name_ko"""
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("hazards", [])
    return {h["code"]: h.get("name_ko", h["code"]) for h in items}


# ──────────────────────────────────────────────
# law_ref → law_id 변환 규칙
# ──────────────────────────────────────────────

SAFETYCODE_RAW  = "273603"   # 산업안전보건기준에 관한 규칙
PARENTLAW_RAW   = "276853"   # 산업안전보건법

def resolve_law_ref(law_ref: str, law_index: dict[str, dict]) -> list[str]:
    """
    law_ref 자유 텍스트 → 후보 law_id 목록 반환.
    - "산업안전보건기준에 관한 규칙" 또는 "안전보건규칙" → statute:273603
    - "산업안전보건법" (기준/규칙 미포함) → statute:276853
    - 미매칭 → []
    """
    if not law_ref:
        return []
    ref = law_ref.strip()
    # 안전보건규칙 패턴 (기준에 관한 규칙 포함)
    if "기준에 관한 규칙" in ref or "안전보건기준" in ref:
        return [law_index[SAFETYCODE_RAW]["law_id"]]
    # 산업안전보건법 (순수 부모법만)
    if "산업안전보건법" in ref and "기준" not in ref and "규칙" not in ref:
        return [law_index[PARENTLAW_RAW]["law_id"]]
    return []


def confidence_score(candidates: list[str]) -> int:
    if len(candidates) == 1:
        return 95
    if len(candidates) > 1:
        return 70
    return 0


def match_status(candidates: list[str], law_ref: str) -> str:
    if not law_ref:
        return "no_match"
    if len(candidates) == 1:
        return "matched"
    if len(candidates) > 1:
        return "multiple_candidates"
    return "no_match"


# ──────────────────────────────────────────────
# control_code 파생 (방식 B: {hazard_code}_C{nn:02d})
# ──────────────────────────────────────────────

def build_control_codes(controls: list[dict]) -> list[str]:
    """hazard_code별 순번을 붙여 control_code 생성. 입력 순서 기준."""
    seq_counter: dict[str, int] = defaultdict(int)
    codes = []
    for c in controls:
        hz = c["hazard_code"]
        seq_counter[hz] += 1
        codes.append(f"{hz}_C{seq_counter[hz]:02d}")
    return codes


# ──────────────────────────────────────────────
# 정규화 상태 결정
# ──────────────────────────────────────────────

def normalization_status(law_ids: list[str], law_ref: str) -> str:
    if law_ids:
        return "normalized"
    if not law_ref:
        return "normalized_without_law"
    return "review_needed"


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────

def main():
    law_index  = load_laws(INPUT_LAWS)
    hz_names   = load_hazards(INPUT_HAZARDS)

    with INPUT_CONTROLS.open(encoding="utf-8") as f:
        hc_data = json.load(f)
    controls: list[dict] = hc_data["hazard_controls"]

    codes = build_control_codes(controls)
    now   = datetime.now(timezone.utc).isoformat()

    normalized_items  = []
    review_items      = []
    candidate_items   = []

    for code, raw in zip(codes, controls):
        hz_code  = raw["hazard_code"]
        hz_name  = hz_names.get(hz_code, hz_code)
        law_ref  = raw.get("law_ref", "")

        candidates = resolve_law_ref(law_ref, law_index)
        law_titles = [law_index[SAFETYCODE_RAW if "273603" in lid else PARENTLAW_RAW]["title_ko"]
                      for lid in candidates]

        status = normalization_status(candidates, law_ref)

        item = {
            "control_code":          code,
            "control_name":          raw.get("control_text", "")[:60],
            "control_text":          raw.get("control_text", ""),
            "hazard_code":           hz_code,
            "hazard_name":           hz_name,
            "control_group":         hz_code,
            "control_type":          raw.get("control_type", ""),
            "priority":              raw.get("priority", ""),
            "law_ids":               candidates,
            "law_titles":            law_titles,
            "law_ref_raw":           [law_ref] if law_ref else [],
            "normalization_status":  status,
            "created_at":            now,
            "updated_at":            now,
        }

        if status == "review_needed":
            review_items.append({
                "issue_type":       "no_law_id_match",
                "control_name":     item["control_text"],
                "hazard_code":      hz_code,
                "raw_control":      raw,
                "note":             f"law_ref '{law_ref}'에 대응하는 law_id 미확정",
                "candidate_law_ids": candidates,
            })
        else:
            normalized_items.append(item)

        # 후보 매칭 기록 (law_ref 있는 모든 항목)
        if law_ref:
            candidate_items.append({
                "control_code":      code,
                "control_name":      raw.get("control_text", ""),
                "hazard_code":       hz_code,
                "law_ref_raw":       law_ref,
                "candidate_law_ids": candidates,
                "candidate_titles":  law_titles,
                "selected_law_ids":  candidates if status in ("normalized",) else [],
                "match_type":        "text_pattern",
                "confidence":        confidence_score(candidates),
                "status":            match_status(candidates, law_ref),
            })

    # 결과 저장
    with OUT_NORM.open("w", encoding="utf-8") as f:
        json.dump({
            "generated_at":           now,
            "control_code_method":    "B — {hazard_code}_C{nn:02d}",
            "item_count":             len(normalized_items),
            "items":                  normalized_items,
        }, f, ensure_ascii=False, indent=2)

    with OUT_REVIEW.open("w", encoding="utf-8") as f:
        json.dump({
            "generated_at":  now,
            "review_count":  len(review_items),
            "items":         review_items,
        }, f, ensure_ascii=False, indent=2)

    with OUT_CANDIDATES.open("w", encoding="utf-8") as f:
        json.dump({
            "generated_at": now,
            "item_count":   len(candidate_items),
            "items":        candidate_items,
        }, f, ensure_ascii=False, indent=2)

    # 보고
    from collections import Counter
    statuses = Counter(i["normalization_status"] for i in normalized_items)
    match_statuses = Counter(c["status"] for c in candidate_items)

    print(f"[완료] {OUT_NORM.name} : {len(normalized_items)}건")
    print(f"[완료] {OUT_REVIEW.name} : {len(review_items)}건")
    print(f"[완료] {OUT_CANDIDATES.name} : {len(candidate_items)}건")
    print()
    print("=== 정규화 상태 분포 ===")
    for k, v in statuses.items():
        print(f"  {k}: {v}")
    print(f"  review_needed: {len(review_items)}")
    print()
    print("=== 후보 매칭 결과 ===")
    for k, v in match_statuses.items():
        print(f"  {k}: {v}")
    print()
    print("=== 대표 예시 5건 ===")
    for item in normalized_items[:5]:
        print(f"  {item['control_code']} | {item['control_text'][:40]} | {item['law_ids']}")


if __name__ == "__main__":
    main()

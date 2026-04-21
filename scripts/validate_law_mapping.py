"""
법령 매핑 품질 검증 스크립트

대상 worktype 4개: ELEC_LIVE, WATER_MANHOLE, TEMP_SCAFF, LIFT_RIGGING
확인 항목:
  - worktype별 연결된 law 수
  - hazard별 law 수
  - control별 law 수
  - 명백히 맞는 law 3건 이상 존재 여부

실행:
  python scripts/validate_law_mapping.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "risk_db"

# ── 파일 경로 ──────────────────────────────────────────────────────────────────
WORKTYPE_MAP  = DATA / "law_mapping" / "law_worktype_map.json"
HAZARD_MAP    = DATA / "law_mapping" / "law_hazard_map.json"
CONTROL_MAP   = DATA / "law_mapping" / "law_control_map.json"
WORK_HZ_MAP   = DATA / "work_taxonomy" / "work_hazards_map.json"
NORMALIZED    = DATA / "law_normalized" / "safety_laws_normalized.json"

TARGET_WORKTYPES = ["ELEC_LIVE", "WATER_MANHOLE", "TEMP_SCAFF", "LIFT_RIGGING"]

# worktype별 기대 hazard 코드
EXPECTED_HAZARDS: dict[str, list[str]] = {
    "ELEC_LIVE":     ["ELEC"],
    "WATER_MANHOLE": ["ASPHYX", "FALL", "DROP"],
    "TEMP_SCAFF":    ["FALL", "DROP", "COLLAPSE"],
    "LIFT_RIGGING":  ["DROP", "FALL", "COLLIDE"],
}

# 명백히 맞는 법령 기준 (score >= 85 AND match_type in manual_seed/exact_keyword/prelinked_law_id)
HIGH_CONFIDENCE_SCORE = 85
HIGH_CONFIDENCE_TYPES = {"manual_seed", "exact_keyword", "prelinked_law_id"}


def load(path: Path) -> dict:
    if not path.exists():
        print(f"[MISSING] {path}")
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _index_by(items: list[dict], key: str) -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        idx[item.get(key, "")].append(item)
    return idx


def validate_worktype(
    wt_code: str,
    wt_items: list[dict],
    hz_items_by_code: dict[str, list[dict]],
    ctrl_items_by_code: dict[str, list[dict]],
    work_hazards: dict[str, list[str]],
) -> dict:
    """단일 worktype 검증 결과 반환."""
    result = {
        "work_type_code":   wt_code,
        "law_count":        len(wt_items),
        "high_conf_laws":   [],
        "hazard_coverage":  {},
        "control_coverage": {},
        "warnings":         [],
        "verdict":          "PASS",
    }

    # 명백히 맞는 law 확인
    for item in wt_items:
        if (item.get("match_score", 0) >= HIGH_CONFIDENCE_SCORE
                and item.get("match_type") in HIGH_CONFIDENCE_TYPES):
            result["high_conf_laws"].append({
                "law_id":    item.get("law_id"),
                "title":     item.get("law_title"),
                "score":     item.get("match_score"),
                "match":     item.get("match_type"),
                "keywords":  item.get("match_keywords"),
            })

    if len(result["high_conf_laws"]) < 3:
        result["warnings"].append(
            f"고신뢰 법령 {len(result['high_conf_laws'])}건 < 3건 기준 미달"
        )
        result["verdict"] = "WARN"

    # hazard별 law 수
    expected_hz = EXPECTED_HAZARDS.get(wt_code, [])
    for hz_code in expected_hz:
        hz_laws = hz_items_by_code.get(hz_code, [])
        result["hazard_coverage"][hz_code] = len(hz_laws)
        if len(hz_laws) == 0:
            result["warnings"].append(f"hazard {hz_code}: law 0건")
            result["verdict"] = "FAIL"
        elif len(hz_laws) < 2:
            result["warnings"].append(f"hazard {hz_code}: law {len(hz_laws)}건 (2건 미만 주의)")

    # worktype 소속 hazard에서 control별 law 수
    wt_hazard_codes = set(work_hazards.get(wt_code, EXPECTED_HAZARDS.get(wt_code, [])))
    ctrl_total = 0
    for ctrl_code, ctrl_laws in ctrl_items_by_code.items():
        hz = ctrl_laws[0].get("hazard_code", "") if ctrl_laws else ""
        if hz in wt_hazard_codes:
            result["control_coverage"][ctrl_code] = len(ctrl_laws)
            ctrl_total += 1

    if ctrl_total == 0:
        result["warnings"].append("연결된 control에 법령 없음")
        result["verdict"] = "FAIL"

    return result


def main() -> int:
    wt_map   = load(WORKTYPE_MAP)
    hz_map   = load(HAZARD_MAP)
    ctrl_map = load(CONTROL_MAP)
    wh_map   = load(WORK_HZ_MAP)
    norm     = load(NORMALIZED)

    if not wt_map or not hz_map or not ctrl_map:
        print("[ERROR] 필수 매핑 파일 없음")
        return 1

    wt_items_by_code   = _index_by(wt_map.get("items", []),   "work_type_code")
    hz_items_by_code   = _index_by(hz_map.get("items", []),   "hazard_code")
    ctrl_items_by_code = _index_by(ctrl_map.get("items", []), "control_code")

    # work_hazards_map: work_type_code → [hazard_code]
    work_hazards: dict[str, list[str]] = {}
    for entry in wh_map.get("items", wh_map.get("mappings", [])):
        wc = entry.get("work_type_code", "")
        hc = entry.get("hazard_code", "")
        if wc and hc:
            work_hazards.setdefault(wc, []).append(hc)

    print("=" * 60)
    print("법령 매핑 품질 검증")
    print(f"  normalized law 수: {norm.get('item_count', len(norm.get('items', [])))}")
    print(f"  worktype 매핑 수:  {wt_map.get('item_count', len(wt_map.get('items', [])))}")
    print(f"  hazard 매핑 수:    {hz_map.get('item_count', len(hz_map.get('items', [])))}")
    print(f"  control 매핑 수:   {ctrl_map.get('item_count', len(ctrl_map.get('items', [])))}")
    print("=" * 60)

    all_pass = True
    results = []

    for wt_code in TARGET_WORKTYPES:
        wt_items = wt_items_by_code.get(wt_code, [])
        r = validate_worktype(
            wt_code, wt_items, hz_items_by_code, ctrl_items_by_code, work_hazards
        )
        results.append(r)

        verdict = r["verdict"]
        mark    = "OK" if verdict == "PASS" else ("^" if verdict == "WARN" else "NG")
        if verdict == "FAIL":
            all_pass = False

        print(f"\n[{mark} {verdict}] {wt_code}")
        print(f"  worktype law 수     : {r['law_count']}")
        print(f"  고신뢰 law (≥{HIGH_CONFIDENCE_SCORE}) : {len(r['high_conf_laws'])}건")
        for lw in r["high_conf_laws"][:3]:
            print(f"    - [{lw['score']}] {lw['title']} ({lw['match']})")

        print(f"  hazard별 law 수:")
        for hz, cnt in r["hazard_coverage"].items():
            ok_mark = "OK" if cnt >= 1 else "NG"
            print(f"    [{ok_mark}] {hz}: {cnt}건")

        print(f"  control 연결 수: {len(r['control_coverage'])}개 코드")
        if r["warnings"]:
            for w in r["warnings"]:
                print(f"  WARN: {w}")

    print("\n" + "=" * 60)
    final = "PASS" if all_pass else "WARN"
    # FAIL이 하나라도 있으면 전체 FAIL
    if any(r["verdict"] == "FAIL" for r in results):
        final = "FAIL"
    print(f"최종 판정: {final}")
    print("=" * 60)

    return 0 if final in ("PASS", "WARN") else 1


if __name__ == "__main__":
    sys.exit(main())

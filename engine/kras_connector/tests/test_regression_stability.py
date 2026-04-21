"""
Regression stability tests for recommend / recalculate output.
Run: pytest engine/kras_connector/tests/test_regression_stability.py -v

Validates:
- Deterministic ordering across repeated calls
- recommend / recalculate law-order alignment
- generic-law (worktype-only) pushed to end of list
- control-specific law priority over hazard-only law
- fallback behaviour when specific laws are absent
"""

import sys
import os

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest
from backend.services.risk_assessment_engine import recommend, recalculate

# ── helpers ────────────────────────────────────────────────────────────────────

def _law_order(result: dict) -> list[tuple[str, list[str]]]:
    """[(hazard_code, [law_id, ...]), ...]"""
    return [(row["hazard"]["hazard_code"], [l["law_id"] for l in row["laws"]]) for row in result["rows"]]


def _rec(work_type_code: str, flags: list[str] | None = None, max_laws: int = 3) -> dict:
    return recommend(work_type_code, "", "", flags or [], 5, 3, max_laws, True, True, [], [], [])


def _recalc(result: dict, work_type_code: str, flags: list[str] | None = None, max_laws: int = 3) -> dict:
    rows_in = [
        {
            "row_id": row["row_id"],
            "hazard_code": row["hazard"]["hazard_code"],
            "selected_control_codes": [c["control_code"] for c in row["controls"]],
            "custom_control_texts": [],
            "excluded_law_ids": [],
            "memo": "",
        }
        for row in result["rows"]
    ]
    return recalculate(work_type_code, "", flags or [], rows_in, True, True, max_laws)


def _ev_priority(paths: list[str]) -> int:
    if "control_law" in paths:
        return 0
    if "hazard_law" in paths:
        return 1
    return 2


# ── A. 반복 호출 일관성 테스트 ──────────────────────────────────────────────────

@pytest.mark.parametrize("work_type_code,flags", [
    ("ELEC_LIVE",   ["live_electric"]),
    ("TEMP_SCAFF",  []),
    ("LIFT_RIGGING",[]),
    ("WELD_ARC",    []),
])
def test_repeat_calls_deterministic(work_type_code, flags):
    """동일 입력 3회 반복 호출 시 law 순서 동일."""
    r1 = _rec(work_type_code, flags)
    r2 = _rec(work_type_code, flags)
    r3 = _rec(work_type_code, flags)
    lo1, lo2, lo3 = _law_order(r1), _law_order(r2), _law_order(r3)
    assert lo1 == lo2 == lo3, f"{work_type_code}: law order changed across calls"


# ── B. recommend / recalculate 정렬 일치 ──────────────────────────────────────

@pytest.mark.parametrize("work_type_code,flags", [
    ("ELEC_LIVE",   ["live_electric"]),
    ("TEMP_SCAFF",  []),
    ("LIFT_RIGGING",[]),
])
def test_recommend_recalculate_law_alignment(work_type_code, flags):
    """recommend와 recalculate의 law 목록 및 순서가 동일."""
    rec_result = _rec(work_type_code, flags)
    recalc_result = _recalc(rec_result, work_type_code, flags)
    rec_order = _law_order(rec_result)
    recalc_order = _law_order(recalc_result)
    assert rec_order == recalc_order, (
        f"{work_type_code}: recommend vs recalculate law order differs\n"
        f"recommend:   {rec_order}\n"
        f"recalculate: {recalc_order}"
    )


# ── C. generic-law 후순위 고정 ─────────────────────────────────────────────────

@pytest.mark.parametrize("work_type_code,flags", [
    ("ELEC_LIVE",   ["live_electric"]),
    ("TEMP_SCAFF",  []),
    ("LIFT_RIGGING",[]),
])
def test_generic_law_not_top1(work_type_code, flags):
    """specific law 존재 시 top-1 law가 worktype-only generic이 아님."""
    result = _rec(work_type_code, flags, max_laws=5)
    for row in result["rows"]:
        laws = row["laws"]
        if len(laws) < 2:
            continue
        top_paths = laws[0]["evidence_paths"]
        has_specific = any(
            _ev_priority(l["evidence_paths"]) < 2 for l in laws
        )
        if has_specific:
            assert _ev_priority(top_paths) < 2, (
                f"{work_type_code}/{row['hazard']['hazard_code']}: "
                f"generic-law at top1 even though specific laws exist. "
                f"top paths={top_paths}"
            )


def test_generic_law_cap_with_specific():
    """specific law 있을 때 generic (worktype-only) law는 최대 1개."""
    result = _rec("TEMP_SCAFF", [], max_laws=5)
    for row in result["rows"]:
        laws = row["laws"]
        specific = [l for l in laws if _ev_priority(l["evidence_paths"]) < 2]
        generic = [l for l in laws if _ev_priority(l["evidence_paths"]) == 2]
        if specific:
            assert len(generic) <= 1, (
                f"TEMP_SCAFF/{row['hazard']['hazard_code']}: "
                f"{len(generic)} generic laws when specific exist (cap=1)"
            )


# ── D. control-specific law 우선 ───────────────────────────────────────────────

@pytest.mark.parametrize("work_type_code,flags", [
    ("ELEC_LIVE", ["live_electric"]),
    ("TEMP_SCAFF", []),
])
def test_control_specific_law_before_hazard_only(work_type_code, flags):
    """control_law path를 포함한 law가 hazard-only law보다 앞."""
    result = _rec(work_type_code, flags, max_laws=5)
    for row in result["rows"]:
        laws = row["laws"]
        for i, law in enumerate(laws[:-1]):
            next_law = laws[i + 1]
            cur_pri = _ev_priority(law["evidence_paths"])
            nxt_pri = _ev_priority(next_law["evidence_paths"])
            # Higher-priority (lower number) law must not come after lower-priority
            assert cur_pri <= nxt_pri, (
                f"{work_type_code}/{row['hazard']['hazard_code']}: "
                f"law order violation at position {i}: "
                f"{law['law_id']}(ev_pri={cur_pri}) before "
                f"{next_law['law_id']}(ev_pri={nxt_pri})"
            )


# ── E. row당 law 수 기준 ───────────────────────────────────────────────────────

@pytest.mark.parametrize("work_type_code,max_laws", [
    ("ELEC_LIVE",   3),
    ("TEMP_SCAFF",  5),
    ("LIFT_RIGGING",3),
])
def test_law_count_cap_respected(work_type_code, max_laws):
    """row당 law 수가 max_laws_per_row 초과하지 않음."""
    result = _rec(work_type_code, [], max_laws=max_laws)
    for row in result["rows"]:
        assert len(row["laws"]) <= max_laws, (
            f"{work_type_code}/{row['hazard']['hazard_code']}: "
            f"{len(row['laws'])} laws > max {max_laws}"
        )


# ── F. 경계 조건 — specific law 없는 경우 fallback ────────────────────────────

def test_fallback_generic_when_no_specific():
    """specific law 없으면 generic (worktype-only) law를 최대 2개 허용."""
    result = _rec("CIVIL_EXCAV", [], max_laws=5)
    for row in result["rows"]:
        laws = row["laws"]
        specific = [l for l in laws if _ev_priority(l["evidence_paths"]) < 2]
        generic = [l for l in laws if _ev_priority(l["evidence_paths"]) == 2]
        if not specific and generic:
            assert len(generic) <= 2, (
                f"CIVIL_EXCAV/{row['hazard']['hazard_code']}: "
                f"{len(generic)} generic fallback laws (cap=2)"
            )


# ── G. recalculate max_laws_per_row 전달 ──────────────────────────────────────

def test_recalculate_max_laws_per_row():
    """recalculate가 max_laws_per_row를 존중."""
    rec_result = _rec("TEMP_SCAFF", [], max_laws=3)
    rows_in = [
        {
            "row_id": row["row_id"],
            "hazard_code": row["hazard"]["hazard_code"],
            "selected_control_codes": [c["control_code"] for c in row["controls"]],
            "custom_control_texts": [],
            "excluded_law_ids": [],
            "memo": "",
        }
        for row in rec_result["rows"]
    ]
    rc = recalculate("TEMP_SCAFF", "", [], rows_in, True, True, max_laws_per_row=2)
    for row in rc["rows"]:
        assert len(row["laws"]) <= 2, (
            f"TEMP_SCAFF recalculate: {len(row['laws'])} laws > max 2"
        )


# ── H. hazard row 생성 확인 ────────────────────────────────────────────────────

@pytest.mark.parametrize("work_type_code,min_rows", [
    ("ELEC_LIVE",   1),
    ("TEMP_SCAFF",  2),
    ("LIFT_RIGGING",2),
    ("WELD_ARC",    1),
])
def test_hazard_rows_generated(work_type_code, min_rows):
    """각 worktype에서 hazard row가 최소 min_rows 이상 생성됨."""
    result = _rec(work_type_code)
    assert len(result["rows"]) >= min_rows, (
        f"{work_type_code}: only {len(result['rows'])} rows, expected >= {min_rows}"
    )

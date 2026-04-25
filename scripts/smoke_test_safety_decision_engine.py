"""
Safety Decision Engine 스모크 테스트.
결과는 PASS / WARN / FAIL 요약만 출력한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.safety_decision import build_decision_summary

# ── 결과 수집 ─────────────────────────────────────────────────────────

_results: list[tuple[str, str, str]] = []


def ok(case: str, msg: str) -> None:
    _results.append(("PASS", case, msg))


def warn(case: str, msg: str) -> None:
    _results.append(("WARN", case, msg))


def fail(case: str, msg: str) -> None:
    _results.append(("FAIL", case, msg))


# ── 공통 검증 로직 ──────────────────────────────────────────────────────

def _check_summary(input_type: str, input_id: str) -> None:
    case = f"{input_type}:{input_id}"
    try:
        result = build_decision_summary(input_type, input_id)
    except Exception as e:
        fail(case, f"예외 발생: {e}")
        return

    # input 인식
    if result.get("input", {}).get("id") == input_id:
        ok(case, f"input 인식 — name: {result['input'].get('name','?')}")
    else:
        fail(case, "input id 불일치")

    # required_documents ≥ 1
    docs = result.get("required_documents", [])
    if len(docs) >= 1:
        ok(case, f"required_documents {len(docs)}건")
    else:
        fail(case, "required_documents 0건")

    # doc_id가 catalog에 존재하고 name이 있음
    for doc in docs:
        if doc.get("name") and doc["name"] != doc["id"]:
            ok(case, f"  문서 조회: {doc['id']} ({doc['name']})")
        else:
            warn(case, f"  문서 이름 미확인: {doc['id']}")

    # DONE 문서는 form_type이 있어야 함
    for doc in docs:
        if doc.get("implementation_status") == "DONE":
            if doc.get("form_type"):
                ok(case, f"  DONE form_type 존재: {doc['id']} → {doc['form_type']}")
            else:
                fail(case, f"  DONE 문서 form_type 없음: {doc['id']}")

    # compliance_basis 또는 warnings 반환
    has_basis = bool(result.get("compliance_basis"))
    has_warnings = bool(result.get("warnings"))
    if has_basis:
        ok(case, f"compliance_basis {len(result['compliance_basis'])}건")
    elif has_warnings:
        warn(case, f"compliance_basis 없음 — warnings {len(result['warnings'])}건")
    else:
        warn(case, "compliance_basis 없음 (warnings도 없음)")

    # basis_missing warnings 내용 확인
    for w in result.get("warnings", []):
        if w.get("type") == "basis_missing":
            warn(case, f"  basis_missing: {w.get('target_id')}")

    # required_training 반환 여부 (0건도 허용)
    train_count = len(result.get("required_training", []))
    ok(case, f"required_training {train_count}건")

    # required_inspections 반환 여부 (장비 입력 시에만 확인)
    if input_type == "equipment":
        inspections = result.get("required_inspections", [])
        insp_count = len(inspections)
        ok(case, f"required_inspections {insp_count}건")
        for insp in inspections:
            iname = insp.get("name", "?")
            has_basis = bool(insp.get("basis"))
            if has_basis:
                ok(case, f"  점검 조회(basis 확인): {insp['id']} ({iname})")
            else:
                warn(case, f"  점검 조회(basis 없음): {insp['id']} ({iname})")
        # inspection_basis_missing warnings 확인
        for w in result.get("warnings", []):
            if w.get("type") == "inspection_basis_missing":
                warn(case, f"  inspection_basis_missing: {w.get('target_id')}")


# ── 에러 케이스 ──────────────────────────────────────────────────────────

def _check_invalid_input() -> None:
    for bad_type, bad_id in [("equipment", "EQ_UNKNOWN"), ("work", "WT_UNKNOWN")]:
        try:
            build_decision_summary(bad_type, bad_id)
            fail(f"invalid:{bad_id}", "ValueError가 발생하지 않음")
        except ValueError:
            ok(f"invalid:{bad_id}", "미등록 ID → ValueError 정상 발생")
        except Exception as e:
            fail(f"invalid:{bad_id}", f"예상치 않은 예외: {e}")

    try:
        build_decision_summary("unknown_type", "anything")
        fail("invalid:input_type", "ValueError가 발생하지 않음")
    except ValueError:
        ok("invalid:input_type", "미지원 input_type → ValueError 정상 발생")


# ── inspection 커버리지 검증 ──────────────────────────────────────────────

def _check_inspection_coverage() -> None:
    """주요 장비 inspection ≥ 1 검증."""
    must_have_inspection = ["EQ_CRANE_TOWER", "EQ_FORKLIFT", "EQ_EXCAV", "EQ_MANHOLE_BLOWER"]
    for eq_id in must_have_inspection:
        case = f"insp_coverage:{eq_id}"
        try:
            result = build_decision_summary("equipment", eq_id)
            inspections = result.get("required_inspections", [])
            if len(inspections) >= 1:
                ok(case, f"required_inspections {len(inspections)}건 확인")
            else:
                fail(case, "required_inspections 0건 — 점검 매핑 누락")
        except Exception as e:
            fail(case, f"예외: {e}")


# ── 메인 ─────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 60)
    print("Safety Decision Engine 스모크 테스트")
    print("=" * 60)

    test_cases = [
        ("equipment", "EQ_CRANE_TOWER"),
        ("equipment", "EQ_CRANE_MOB"),
        ("equipment", "EQ_FORKLIFT"),
        ("equipment", "EQ_EXCAV"),
        ("work", "WT_CONFINED_SPACE"),
        ("work", "WT_CRANE_LIFTING"),
        ("work", "WT_EXCAVATION"),
    ]

    for input_type, input_id in test_cases:
        _check_summary(input_type, input_id)

    _check_invalid_input()
    _check_inspection_coverage()

    # ── 결과 출력 ──
    passes = [r for r in _results if r[0] == "PASS"]
    warns  = [r for r in _results if r[0] == "WARN"]
    fails  = [r for r in _results if r[0] == "FAIL"]

    print()
    for status, case, msg in _results:
        icon = {"PASS": "✓", "WARN": "△", "FAIL": "✗"}[status]
        print(f"  [{status}] {icon} [{case}] {msg}")

    print()
    print(f"  PASS: {len(passes)}  WARN: {len(warns)}  FAIL: {len(fails)}")
    print()

    if fails:
        print("최종 판정: FAIL")
        return 1
    if warns:
        print("최종 판정: WARN")
        return 0
    print("최종 판정: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

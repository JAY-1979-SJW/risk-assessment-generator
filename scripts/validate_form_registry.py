"""
Form Registry 검증 스크립트.

검증 항목:
  1. supported_types() 가 2개 form_type 반환
  2. get_spec() 각 form_type별 FormSpec 반환 확인
  3. build('education_log', ...) → bytes
  4. build('excavation_workplan', ...) → bytes
  5. 미지원 form_type → UnsupportedFormTypeError
  6. 각 spec: required_fields 비어있지 않음
  7. 각 spec: max_repeat_rows > 0
  8. 각 spec: builder 결과 bytes 크기 > 0

실행:
  python scripts/validate_form_registry.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.output.form_registry import (
    UnsupportedFormTypeError,
    build,
    get_spec,
    supported_types,
)

# ---------------------------------------------------------------------------
# 최소 샘플 데이터 (builder 정상 동작 확인 목적만)
# ---------------------------------------------------------------------------
_EDUCATION_LOG_SAMPLE = {
    "site_name": "검증용 사업장",
    "education_type": "정기교육",
    "education_date": "2026-04-24",
    "education_location": "본사 교육실",
    "education_duration_hours": "2",
    "education_target_job": "전 직원",
    "instructor_name": "검증자",
    "instructor_qualification": "산업안전지도사",
    "confirmer_name": "검증확인자",
    "confirmer_role": "안전보건관리책임자",
}

_EXCAVATION_WORKPLAN_SAMPLE = {
    "site_name": "검증용 현장",
    "excavation_method": "개착식",
    "earth_retaining": "H-Pile + 토류판",
    "excavation_machine": "백호우 0.8m³",
    "soil_disposal": "현장 외 반출",
    "water_disposal": "웰포인트 공법",
    "work_method": "단계별 굴착",
    "emergency_measure": "즉시 작업중단 및 대피",
}

_SAMPLES: dict[str, dict] = {
    "education_log": _EDUCATION_LOG_SAMPLE,
    "excavation_workplan": _EXCAVATION_WORKPLAN_SAMPLE,
}

_EXPECTED_TYPES = {"education_log", "excavation_workplan"}


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _check(condition: bool, name: str, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition


# ---------------------------------------------------------------------------
# 검증 함수
# ---------------------------------------------------------------------------

def validate_registry_meta() -> list[bool]:
    results: list[bool] = []
    print("\n=== Registry 메타 검증 ===")

    # 1. supported_types
    types = supported_types()
    results.append(_check(
        set(types) == _EXPECTED_TYPES,
        f"supported_types() == {sorted(_EXPECTED_TYPES)}",
        str(sorted(types)),
    ))

    # 2. get_spec 각 form_type
    for ft in _EXPECTED_TYPES:
        try:
            spec = get_spec(ft)
            results.append(_check(True, f"get_spec('{ft}') 반환 성공",
                                  f"display_name={spec.display_name!r}"))
        except Exception as e:
            results.append(_check(False, f"get_spec('{ft}')", str(e)))
            continue

        # 3. required_fields 비어있지 않음
        results.append(_check(
            len(spec.required_fields) > 0,
            f"  {ft}: required_fields 비어있지 않음",
            str(spec.required_fields),
        ))

        # 4. max_repeat_rows > 0
        results.append(_check(
            isinstance(spec.max_repeat_rows, int) and spec.max_repeat_rows > 0,
            f"  {ft}: max_repeat_rows > 0",
            str(spec.max_repeat_rows),
        ))

        # 5. version 문자열
        results.append(_check(
            isinstance(spec.version, str) and len(spec.version) > 0,
            f"  {ft}: version 문자열",
            repr(spec.version),
        ))

    return results


def validate_build_calls() -> list[bool]:
    results: list[bool] = []
    print("\n=== build() 호출 검증 ===")

    for ft, sample in _SAMPLES.items():
        try:
            result = build(ft, sample)
            ok_bytes = isinstance(result, bytes) and len(result) > 0
            results.append(_check(
                ok_bytes,
                f"build('{ft}', ...) → bytes",
                f"{len(result):,} bytes" if isinstance(result, bytes) else repr(type(result)),
            ))
        except Exception as e:
            results.append(_check(False, f"build('{ft}', ...)", str(e)))

    return results


def validate_unsupported() -> list[bool]:
    results: list[bool] = []
    print("\n=== 미지원 form_type 오류 검증 ===")

    for bad_type in ["unknown_form", "", "vehicle_workplan"]:
        try:
            build(bad_type, {})
            results.append(_check(False, f"build('{bad_type}') → 예외 미발생 (오류)"))
        except UnsupportedFormTypeError as e:
            results.append(_check(True, f"build('{bad_type}') → UnsupportedFormTypeError",
                                  str(e)[:60]))
        except Exception as e:
            results.append(_check(False, f"build('{bad_type}') → 잘못된 예외 타입: {type(e).__name__}",
                                  str(e)[:60]))

    return results


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main() -> int:
    print("Form Registry 검증 시작")
    print("=" * 50)

    all_results: list[bool] = []
    all_results += validate_registry_meta()
    all_results += validate_build_calls()
    all_results += validate_unsupported()

    total  = len(all_results)
    passed = sum(all_results)
    failed = total - passed

    print("\n" + "=" * 50)
    print(f"결과: {passed}/{total} PASS, {failed} FAIL")
    if failed == 0:
        print("최종 판정: PASS")
        return 0
    else:
        print("최종 판정: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())

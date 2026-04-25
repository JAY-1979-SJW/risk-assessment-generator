"""
Form Registry 검증 스크립트.

검증 범위:
  - "현재 구현 완료된 form builder 등록 상태"를 검증한다.
  - 전체 90종 카탈로그 완성 여부를 검증하는 스크립트가 아니다.
  - 전체 카탈로그/매핑 검증은 validate_safety_platform_skeleton.py 에서 수행한다.

검증 항목:
  1. list_supported_forms() — REQUIRED_FORM_TYPES 전체 포함 확인 (동적 기준)
  2. registry key 중복 없음
  3. get_form_spec() — education_log / excavation_workplan: 필드 구조 검증
  4. risk_assessment 전용 spec 검증 (required_fields=[], max_repeat_rows=None 허용)
  5. build_form_excel() → bytes (샘플 3종 + 공란 생성)
  6. 미지원 form_type → ValueError (UnsupportedFormTypeError)

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
    build_form_excel,
    get_form_spec,
    list_supported_forms,
)

# 현재 구현 완료된 서식 — registry에 반드시 존재해야 함
REQUIRED_FORM_TYPES: set[str] = {
    "excavation_workplan",
    "vehicle_construction_workplan",
    "material_handling_workplan",
    "risk_assessment",
    "education_log",
    "tower_crane_workplan",
    "mobile_crane_workplan",
    "confined_space_workplan",
    "tbm_log",
    "confined_space_permit",
    "confined_space_checklist",
}

# required_fields 비어있지 않음 / max_repeat_rows > 0 조건 적용 대상
_STRICT_TYPED = {"education_log", "excavation_workplan"}

_SAMPLES: dict[str, dict] = {
    "risk_assessment": {
        "company_name": "검증용 회사",
        "industry": "건설업",
        "site_name": "검증용 현장",
        "assessment_type": "최초평가",
        "assessment_date": "2026-04-24",
        "work_type": "굴착공사",
        "rows": [
            {
                "no": "1",
                "process": "굴착",
                "sub_work": "지반 굴착",
                "hazard_category_major": "기계적",
                "hazard_category_minor": "전도",
                "hazard": "굴착기 전도",
                "legal_basis": "기준 규칙 제82조",
                "current_measures": "안전대 착용",
                "risk_scale": "3×3",
                "probability": "2",
                "severity": "3",
                "risk_level": "6",
                "control_measures": "유도자 배치",
                "residual_risk_level": "3",
                "target_date": "2026-05-01",
                "completion_date": None,
                "responsible_person": "김안전",
            },
        ],
    },
    "education_log": {
        "site_name": "검증용 사업장",
        "education_type": "정기교육",
        "education_date": "2026-04-24",
        "education_location": "본사 교육실",
        "education_duration_hours": "2",
        "education_target_job": "전 직원",
        "instructor_name": "검증강사",
        "instructor_qualification": "산업안전지도사",
        "confirmer_name": "검증확인자",
        "confirmer_role": "안전보건관리책임자",
        "attendees": [
            {"attendee_name": "홍길동", "attendee_job_type": "생산직"},
        ],
    },
    "excavation_workplan": {
        "site_name": "검증용 현장",
        "excavation_method": "개착식",
        "earth_retaining": "H-Pile + 토류판",
        "excavation_machine": "백호우 0.8m³",
        "soil_disposal": "현장 외 반출",
        "water_disposal": "웰포인트 공법",
        "work_method": "단계별 굴착",
        "emergency_measure": "즉시 작업중단 및 대피",
        "guide_worker_required": "필요 (굴착기 진입 시 1명 배치)",
        "access_control": "작업구역 울타리 설치, 안전표지판 부착",
        "emergency_contact": "현장소장 010-0000-0000 / 119",
        "safety_steps": [
            {"task_step": "지하매설물 확인", "hazard": "파손", "safety_measure": "시험굴착"},
        ],
    },
}


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
# 검증 섹션
# ---------------------------------------------------------------------------

def validate_list_supported_forms() -> list[bool]:
    results: list[bool] = []
    print("\n=== list_supported_forms() 검증 ===")

    forms = list_supported_forms()
    form_type_list = [f["form_type"] for f in forms]
    form_types = set(form_type_list)

    # REQUIRED_FORM_TYPES가 모두 registry에 포함되는지 확인
    missing = REQUIRED_FORM_TYPES - form_types
    results.append(_check(
        len(missing) == 0,
        f"REQUIRED_FORM_TYPES {len(REQUIRED_FORM_TYPES)}종 모두 등록됨",
        f"누락: {sorted(missing)}" if missing else f"등록 총 {len(forms)}종",
    ))
    # registry key 중복 없음
    results.append(_check(
        len(form_type_list) == len(form_types),
        "registry key 중복 없음",
        f"총 {len(form_type_list)}건 중 고유 {len(form_types)}건",
    ))
    # builder 참조가 dict에 노출되지 않는지 확인
    results.append(_check(
        all("builder" not in f for f in forms),
        "builder 참조 미노출 (공개 dict에 builder 키 없음)",
    ))
    return results


def validate_get_form_spec() -> list[bool]:
    results: list[bool] = []
    print("\n=== get_form_spec() 검증 — education_log / excavation_workplan ===")

    for ft in _STRICT_TYPED:
        try:
            spec = get_form_spec(ft)
        except Exception as e:
            results.append(_check(False, f"get_form_spec('{ft}') 반환 성공", str(e)))
            continue

        results.append(_check(
            isinstance(spec, dict),
            f"get_form_spec('{ft}') → dict",
            str(type(spec).__name__),
        ))
        results.append(_check(
            isinstance(spec.get("required_fields"), list) and len(spec["required_fields"]) > 0,
            f"  {ft}: required_fields 비어있지 않음",
            str(spec.get("required_fields", [])[:2]) + "...",
        ))
        results.append(_check(
            isinstance(spec.get("optional_fields"), list),
            f"  {ft}: optional_fields 존재",
        ))
        results.append(_check(
            spec.get("repeat_field") is not None and len(spec["repeat_field"]) > 0,
            f"  {ft}: repeat_field 값 존재",
            repr(spec.get("repeat_field")),
        ))
        results.append(_check(
            isinstance(spec.get("max_repeat_rows"), int) and spec["max_repeat_rows"] > 0,
            f"  {ft}: max_repeat_rows > 0",
            str(spec.get("max_repeat_rows")),
        ))
        results.append(_check(
            isinstance(spec.get("version"), str) and len(spec["version"]) > 0,
            f"  {ft}: version 존재",
            repr(spec.get("version")),
        ))

    return results


def validate_risk_assessment_spec() -> list[bool]:
    results: list[bool] = []
    print("\n=== get_form_spec('risk_assessment') 검증 ===")

    try:
        spec = get_form_spec("risk_assessment")
    except Exception as e:
        results.append(_check(False, "get_form_spec('risk_assessment') 반환 성공", str(e)))
        return results

    results.append(_check(isinstance(spec, dict),
                          "get_form_spec('risk_assessment') → dict"))
    results.append(_check(spec.get("form_type") == "risk_assessment",
                          "form_type == 'risk_assessment'"))
    results.append(_check(spec.get("display_name") == "위험성평가표",
                          "display_name == '위험성평가표'",
                          repr(spec.get("display_name"))))
    results.append(_check(isinstance(spec.get("required_fields"), list),
                          "required_fields → list (빈 리스트 허용)",
                          str(spec.get("required_fields"))))
    results.append(_check(isinstance(spec.get("optional_fields"), list),
                          "optional_fields → list"))
    results.append(_check(spec.get("repeat_field") == "rows",
                          "repeat_field == 'rows'",
                          repr(spec.get("repeat_field"))))
    results.append(_check(spec.get("max_repeat_rows") is None,
                          "max_repeat_rows is None (제한 없음)"))
    results.append(_check("builder" not in spec,
                          "builder 참조 미노출"))
    results.append(_check(isinstance(spec.get("version"), str) and spec["version"] == "1.0",
                          "version == '1.0'",
                          repr(spec.get("version"))))

    return results


def validate_build_form_excel() -> list[bool]:
    results: list[bool] = []
    print("\n=== build_form_excel() 검증 ===")

    for ft, sample in _SAMPLES.items():
        try:
            result = build_form_excel(ft, sample)
            results.append(_check(
                isinstance(result, bytes) and len(result) > 0,
                f"build_form_excel('{ft}', sample) → bytes",
                f"{len(result):,} bytes",
            ))
        except Exception as e:
            results.append(_check(False, f"build_form_excel('{ft}', sample)", str(e)))

    # 빈 form_data → 공란 xlsx (오류 없이 생성, 샘플 보유 3종)
    for ft in _SAMPLES:
        try:
            result = build_form_excel(ft, {})
            results.append(_check(
                isinstance(result, bytes) and len(result) > 0,
                f"build_form_excel('{ft}', {{}}) → bytes (공란)",
                f"{len(result):,} bytes",
            ))
        except Exception as e:
            results.append(_check(False, f"build_form_excel('{ft}', {{}})", str(e)))

    return results


def validate_unsupported_type() -> list[bool]:
    results: list[bool] = []
    print("\n=== 미지원 form_type 오류 검증 ===")

    bad_types = ["vehicle_workplan", "tunnel_workplan", "", "EDUCATION_LOG"]
    for bad in bad_types:
        # build_form_excel
        try:
            build_form_excel(bad, {})
            results.append(_check(False, f"build_form_excel('{bad}') → 예외 미발생 (오류)"))
        except UnsupportedFormTypeError as e:
            results.append(_check(
                True,
                f"build_form_excel('{bad}') → UnsupportedFormTypeError(ValueError)",
                str(e)[:70],
            ))
        except Exception as e:
            results.append(_check(
                False,
                f"build_form_excel('{bad}') → 잘못된 예외: {type(e).__name__}",
                str(e)[:60],
            ))

        # get_form_spec
        try:
            get_form_spec(bad)
            results.append(_check(False, f"get_form_spec('{bad}') → 예외 미발생 (오류)"))
        except UnsupportedFormTypeError:
            results.append(_check(True, f"get_form_spec('{bad}') → UnsupportedFormTypeError"))
        except Exception as e:
            results.append(_check(
                False,
                f"get_form_spec('{bad}') → 잘못된 예외: {type(e).__name__}",
            ))

    return results


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main() -> int:
    print("Form Registry 검증 시작")
    print("=" * 50)

    all_results: list[bool] = []
    all_results += validate_list_supported_forms()
    all_results += validate_get_form_spec()
    all_results += validate_risk_assessment_spec()
    all_results += validate_build_form_excel()
    all_results += validate_unsupported_type()

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

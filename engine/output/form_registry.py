"""
Form Builder Registry.

form_type 문자열로 builder 함수를 선택하고 호출하는 최소 디스패처.
export API 연결 전 단계 — builder 호출 인터페이스만 제공.

지원 form_type:
    education_log        — 안전보건교육일지 (v1.1)
    excavation_workplan  — 굴착 작업계획서 (v1.0)

사용법:
    from engine.output.form_registry import build, get_spec, supported_types

    xlsx_bytes = build("education_log", form_data)
    spec = get_spec("excavation_workplan")
    print(spec.required_fields)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple

from engine.output.education_log_builder import build_education_log_excel
from engine.output.workplan_builder import build_excavation_workplan_excel


# ---------------------------------------------------------------------------
# 예외
# ---------------------------------------------------------------------------

class UnsupportedFormTypeError(ValueError):
    """등록되지 않은 form_type 요청 시."""
    def __init__(self, form_type: str) -> None:
        super().__init__(
            f"지원하지 않는 form_type: '{form_type}'. "
            f"지원 목록: {supported_types()}"
        )
        self.form_type = form_type


# ---------------------------------------------------------------------------
# FormSpec
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FormSpec:
    """단일 form_type에 대한 메타데이터 + builder 참조."""

    display_name: str
    builder: Callable[[dict], bytes]
    required_fields: Tuple[str, ...]
    optional_fields: Tuple[str, ...]
    max_repeat_rows: int | None
    version: str


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, FormSpec] = {
    "education_log": FormSpec(
        display_name="안전보건교육일지",
        builder=build_education_log_excel,
        required_fields=(
            # 시행규칙 제32조 법정 필수
            "education_type",
            "education_date",
            "education_location",
            "education_duration_hours",
            "education_target_job",
            "instructor_name",
            "instructor_qualification",
            "confirmer_name",
            "confirmer_role",
        ),
        optional_fields=(
            "site_name",
            "site_address",
            "subjects",       # list[dict]: subject_name, subject_content, subject_hours
            "attendees",      # list[dict]: attendee_name, attendee_job_type
            "confirm_date",
        ),
        max_repeat_rows=30,   # MAX_ATTENDEES
        version="1.1",
    ),
    "excavation_workplan": FormSpec(
        display_name="굴착 작업계획서",
        builder=build_excavation_workplan_excel,
        required_fields=(
            # 산업안전보건기준에 관한 규칙 제82조 제1항 + 제38조 법정 필수
            "excavation_method",
            "earth_retaining",
            "excavation_machine",
            "soil_disposal",
            "water_disposal",
            "work_method",
            "emergency_measure",
        ),
        optional_fields=(
            "site_name",
            "project_name",
            "work_location",
            "work_date",
            "supervisor",
            "contractor",
            "safety_steps",   # list[dict]: task_step, hazard, safety_measure
            "sign_date",
        ),
        max_repeat_rows=10,   # MAX_STEPS
        version="1.0",
    ),
}


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def supported_types() -> list[str]:
    """등록된 form_type 목록 반환."""
    return list(_REGISTRY.keys())


def get_spec(form_type: str) -> FormSpec:
    """
    form_type에 대한 FormSpec 반환.

    Raises:
        UnsupportedFormTypeError: 등록되지 않은 form_type.
    """
    try:
        return _REGISTRY[form_type]
    except KeyError:
        raise UnsupportedFormTypeError(form_type)


def build(form_type: str, form_data: dict) -> bytes:
    """
    form_type에 맞는 builder를 호출해 xlsx bytes 반환.

    Args:
        form_type: 'education_log' | 'excavation_workplan'
        form_data: builder 입력 dict (각 builder 스키마 준수).

    Returns:
        xlsx 파일 bytes.

    Raises:
        UnsupportedFormTypeError: 등록되지 않은 form_type.
    """
    spec = get_spec(form_type)
    return spec.builder(form_data)

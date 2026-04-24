"""
Form Builder Registry.

form_type 문자열로 builder 함수를 선택하고 호출하는 최소 디스패처.
export API 연결 전 단계 — builder 호출 인터페이스만 제공.

지원 form_type:
    education_log        — 안전보건교육일지 (v1.1)
    excavation_workplan  — 굴착 작업계획서 (v1.0)

사용법:
    from engine.output.form_registry import (
        list_supported_forms, get_form_spec, build_form_excel
    )

    forms = list_supported_forms()          # list[dict]
    spec  = get_form_spec("education_log")  # dict
    xlsx  = build_form_excel("excavation_workplan", form_data)  # bytes
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Tuple

from engine.output.education_log_builder import build_education_log_excel
from engine.output.form_excel_builder import build_form_excel as _build_risk_assessment_excel_raw
from engine.output.workplan_builder import build_excavation_workplan_excel


# ---------------------------------------------------------------------------
# 예외
# ---------------------------------------------------------------------------

class UnsupportedFormTypeError(ValueError):
    """등록되지 않은 form_type 요청 시."""
    def __init__(self, form_type: str, supported: list[str]) -> None:
        super().__init__(
            f"지원하지 않는 form_type: '{form_type}'. "
            f"지원 목록: {supported}"
        )
        self.form_type = form_type


# ---------------------------------------------------------------------------
# FormSpec
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FormSpec:
    """단일 form_type의 메타데이터 + builder 참조."""

    form_type: str
    display_name: str
    version: str
    builder: Callable[[dict], bytes]
    required_fields: Tuple[str, ...]
    optional_fields: Tuple[str, ...]
    repeat_field: str | None        # 반복행 list 필드명 (없으면 None)
    max_repeat_rows: int | None     # 최대 반복행 수 (없으면 None)

    def to_dict(self) -> dict[str, Any]:
        """builder 제외 공개 메타데이터 dict 반환."""
        return {
            "form_type":       self.form_type,
            "display_name":    self.display_name,
            "version":         self.version,
            "required_fields": list(self.required_fields),
            "optional_fields": list(self.optional_fields),
            "repeat_field":    self.repeat_field,
            "max_repeat_rows": self.max_repeat_rows,
        }


# ---------------------------------------------------------------------------
# 위험성평가표 어댑터
# ---------------------------------------------------------------------------
# form_excel_builder는 {"header": {...}, "rows": [...]} 구조를 기대하지만
# registry API는 flat dict를 form_data로 수신한다.
# 이 어댑터가 flat → nested 변환만 수행하며, Excel 렌더링은 기존 builder에 위임.

_RISK_ASSESSMENT_HEADER_KEYS: frozenset[str] = frozenset((
    "company_name", "industry", "site_name", "representative",
    "assessment_type", "assessment_date", "work_type",
))


def _risk_assessment_builder(form_data: dict) -> bytes:
    header = {k: form_data.get(k) for k in _RISK_ASSESSMENT_HEADER_KEYS}
    rows   = form_data.get("rows") or []
    return _build_risk_assessment_excel_raw({"header": header, "rows": rows})


# ---------------------------------------------------------------------------
# Registry 등록 테이블
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, FormSpec] = {
    "education_log": FormSpec(
        form_type="education_log",
        display_name="안전보건교육일지",
        version="1.1",
        builder=build_education_log_excel,
        required_fields=(
            # 산업안전보건법 시행규칙 제32조 법정 필수
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
            "subjects",      # list[dict]: subject_name, subject_content, subject_hours
            "attendees",     # list[dict]: attendee_name, attendee_job_type
            "confirm_date",
        ),
        repeat_field="attendees",
        max_repeat_rows=30,  # MAX_ATTENDEES
    ),
    "risk_assessment": FormSpec(
        form_type="risk_assessment",
        display_name="위험성평가표",
        version="1.0",
        builder=_risk_assessment_builder,
        required_fields=(),          # builder에 필수 필드 없음 (모두 optional 처리)
        optional_fields=tuple(_RISK_ASSESSMENT_HEADER_KEYS),
        repeat_field="rows",         # 위험성평가 행 목록
        max_repeat_rows=None,        # builder에 행 수 제한 없음
    ),
    "excavation_workplan": FormSpec(
        form_type="excavation_workplan",
        display_name="굴착 작업계획서",
        version="1.0",
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
            "safety_steps",  # list[dict]: task_step, hazard, safety_measure
            "sign_date",
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,  # MAX_STEPS
    ),
}


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def list_supported_forms() -> list[dict[str, Any]]:
    """
    등록된 모든 form_type의 메타데이터 목록 반환.

    Returns:
        각 form_type의 공개 메타데이터 dict 목록.
        builder 참조는 포함하지 않음.
    """
    return [spec.to_dict() for spec in _REGISTRY.values()]


def get_form_spec(form_type: str) -> dict[str, Any]:
    """
    form_type에 대한 메타데이터 dict 반환.

    Args:
        form_type: 등록된 form_type 문자열.

    Returns:
        공개 메타데이터 dict (builder 참조 미포함).

    Raises:
        UnsupportedFormTypeError(ValueError): 등록되지 않은 form_type.
    """
    if form_type not in _REGISTRY:
        raise UnsupportedFormTypeError(form_type, list(_REGISTRY.keys()))
    return _REGISTRY[form_type].to_dict()


def build_form_excel(form_type: str, form_data: dict) -> bytes:
    """
    form_type에 맞는 builder를 호출해 xlsx bytes 반환.

    Args:
        form_type: 등록된 form_type 문자열.
        form_data: builder 입력 dict (각 builder 스키마 준수).
            safety_steps / attendees > max_repeat_rows 시 builder가 초과분 무시.

    Returns:
        xlsx 파일 bytes.

    Raises:
        UnsupportedFormTypeError(ValueError): 등록되지 않은 form_type.
        TypeError: builder가 bytes 이외 타입을 반환한 경우 (내부 오류).
    """
    if form_type not in _REGISTRY:
        raise UnsupportedFormTypeError(form_type, list(_REGISTRY.keys()))
    result = _REGISTRY[form_type].builder(form_data)
    if not isinstance(result, bytes):
        raise TypeError(
            f"builder '{form_type}' 반환 타입 오류: "
            f"bytes 예상, {type(result).__name__} 수신"
        )
    return result

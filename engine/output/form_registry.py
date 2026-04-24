"""
Form Builder Registry.

form_type 문자열로 builder 함수를 선택하고 호출하는 최소 디스패처.
export API 연결 전 단계 — builder 호출 인터페이스만 제공.

지원 form_type:
    education_log                  — 안전보건교육일지 (v1.1)
    risk_assessment                — 위험성평가표 (v1.0)
    excavation_workplan            — 굴착 작업계획서 (v1.0)
    vehicle_construction_workplan  — 차량계 건설기계 작업계획서 (v1.0)
    material_handling_workplan     — 차량계 하역운반기계 작업계획서 (v1.0)
    tower_crane_workplan           — 타워크레인 작업계획서 (v1.0)       [WP-006]
    mobile_crane_workplan          — 이동식 크레인 작업계획서 (v1.0)    [WP-007]
    confined_space_workplan        — 밀폐공간 작업계획서 (v1.0)         [WP-014]
    tbm_log                        — TBM 안전점검 일지 (v1.0)           [RA-004]
    confined_space_permit          — 밀폐공간 작업허가서 (v1.0)         [PTW-001]
    confined_space_checklist       — 밀폐공간 사전 안전점검표 (v1.0)    [CL-010]

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

from engine.output.confined_space_checklist_builder import build_confined_space_checklist_excel
from engine.output.confined_space_permit_builder import build_confined_space_permit_excel
from engine.output.confined_space_workplan_builder import build_confined_space_workplan_excel
from engine.output.education_log_builder import build_education_log_excel
from engine.output.form_excel_builder import build_form_excel as _build_risk_assessment_excel_raw
from engine.output.material_handling_workplan_builder import build_material_handling_workplan_excel
from engine.output.mobile_crane_workplan_builder import build_mobile_crane_workplan_excel
from engine.output.tbm_log_builder import build_tbm_log_excel
from engine.output.tower_crane_workplan_builder import build_tower_crane_workplan_excel
from engine.output.vehicle_workplan_builder import build_vehicle_workplan_excel
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
    repeat_field: str | None          # 주 반복행 list 필드명 (없으면 None)
    max_repeat_rows: int | None       # 주 반복행 최대 행 수 (없으면 None)
    extra_list_fields: Tuple[str, ...] = ()  # 2번째 이상 list 필드명 (validator 타입 체크 제외)

    def to_dict(self) -> dict[str, Any]:
        """builder 제외 공개 메타데이터 dict 반환."""
        return {
            "form_type":         self.form_type,
            "display_name":      self.display_name,
            "version":           self.version,
            "required_fields":   list(self.required_fields),
            "optional_fields":   list(self.optional_fields),
            "repeat_field":      self.repeat_field,
            "max_repeat_rows":   self.max_repeat_rows,
            "extra_list_fields": list(self.extra_list_fields),
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
            "guide_worker_required",
            "access_control",
            "emergency_contact",
            "safety_steps",  # list[dict]: task_step, hazard, safety_measure
            "sign_date",
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,  # MAX_STEPS
    ),
    "vehicle_construction_workplan": FormSpec(
        form_type="vehicle_construction_workplan",
        display_name="차량계 건설기계 작업계획서",
        version="1.0",
        builder=build_vehicle_workplan_excel,
        required_fields=(
            # 산업안전보건기준에 관한 규칙 제38조 제1항 제3호 + 제170조 법정 필수
            "machine_type",       # 기계의 종류 [제170조 제1호]
            "machine_capacity",   # 기계의 성능·최대작업능력 [제170조 제1호]
            "work_method",        # 작업방법 [제170조 제3호]
            "travel_route_text",  # 운행경로 [제170조 제2호]
        ),
        optional_fields=(
            "site_name",
            "project_name",
            "work_location",
            "work_date",
            "supervisor",
            "contractor",
            "prepared_by",
            "operator_name",
            "operator_license",
            "guide_worker_required",
            "speed_limit",
            "work_radius",
            "ground_survey",
            "travel_route_sketch_note",
            "access_control",
            "emergency_contact",   # 비상연락처
            "emergency_measure",   # 비상조치 방법
            "sign_date",
        ),
        repeat_field="hazard_items",      # list[dict]: hazard, safety_measure
        max_repeat_rows=10,               # MAX_HAZARD
        extra_list_fields=("pre_check_items",),  # list[dict]: check_item, result, note
    ),
    "material_handling_workplan": FormSpec(
        form_type="material_handling_workplan",
        display_name="차량계 하역운반기계 작업계획서",
        version="1.0",
        builder=build_material_handling_workplan_excel,
        required_fields=(
            # 산업안전보건기준에 관한 규칙 제38조 제1항 제2호 + 제38조 제2항 법정 필수
            "machine_type",       # 기계의 종류 [제38조 제2항]
            "machine_max_load",   # 기계의 최대 하중 [제38조 제2항] — machine_capacity와 다름
            "work_method",        # 작업방법 [제38조 제2항]
            "travel_route_text",  # 운행경로 [제38조 제2항]
            "emergency_measure",  # 비상조치 방법 [제38조 제2항]
        ),
        optional_fields=(
            "site_name",
            "project_name",
            "work_location",
            "work_date",
            "supervisor",
            "contractor",
            "prepared_by",
            "machine_count",
            "operator_name",
            "operator_license",
            "guide_worker_required",
            "speed_limit",
            "ground_survey",
            "travel_route_sketch_note",
            "access_control",
            "emergency_contact",        # 비상연락처 (emergency_measure와 별도 필드)
            "pedestrian_separation",    # 보행자 동선 분리 (하역운반기계 전용)
            "sign_date",
        ),
        repeat_field="hazard_items",      # list[dict]: hazard, safety_measure
        max_repeat_rows=10,               # MAX_HAZARD
        extra_list_fields=("pre_check_items",),  # list[dict]: check_item, result, note (미제공 시 제179조 기본값 자동 적용)
    ),
    # ------------------------------------------------------------------
    # P0 신규 등록 (2026-04-24)
    # ------------------------------------------------------------------
    "tower_crane_workplan": FormSpec(
        form_type="tower_crane_workplan",
        display_name="타워크레인 작업계획서",
        version="1.0",
        builder=build_tower_crane_workplan_excel,
        required_fields=(
            "crane_type",       # 기계의 종류 [법정] 제38조
            "crane_capacity",   # 정격하중   [법정] 제142조
            "work_method",      # 작업방법   [법정] 제38조
            "emergency_measure",# 비상조치   [법정] 제38조
        ),
        optional_fields=(
            "site_name", "project_name", "work_location", "work_date",
            "supervisor", "contractor", "prepared_by",
            "crane_reg_no", "installation_location", "work_radius",
            "load_info", "signal_worker", "work_sequence",
            "anti_fall_measures", "sign_date",
        ),
        repeat_field="safety_steps",   # list[dict]: task_step, hazard, safety_measure
        max_repeat_rows=10,
    ),
    "mobile_crane_workplan": FormSpec(
        form_type="mobile_crane_workplan",
        display_name="이동식 크레인 작업계획서",
        version="1.0",
        builder=build_mobile_crane_workplan_excel,
        required_fields=(
            "crane_type",        # 기계의 종류 [법정] 제38조
            "crane_capacity",    # 정격하중   [법정] 제134조
            "work_method",       # 작업방법   [법정] 제38조
            "emergency_measure", # 비상조치   [법정] 제38조
        ),
        optional_fields=(
            "site_name", "project_name", "work_location", "work_date",
            "supervisor", "contractor", "prepared_by",
            "vehicle_no", "outrigger_setup", "ground_condition",
            "load_weight", "work_radius", "rigging_method", "signal_worker",
            "travel_route_text", "travel_route_sketch_note",
            "anti_topple_measures", "sign_date",
        ),
        repeat_field="safety_steps",   # list[dict]: task_step, hazard, safety_measure
        max_repeat_rows=10,
    ),
    "confined_space_workplan": FormSpec(
        form_type="confined_space_workplan",
        display_name="밀폐공간 작업계획서",
        version="1.0",
        builder=build_confined_space_workplan_excel,
        required_fields=(
            "confined_space_location",  # 밀폐공간 위치   [법정] 제619조
            "gas_measurement_plan",     # 측정계획        [법정] 제619조
            "ventilation_plan",         # 환기계획        [법정] 제619조
            "emergency_measure",        # 비상조치        [법정] 제619조
        ),
        optional_fields=(
            "site_name", "project_name", "work_date",
            "supervisor", "contractor", "prepared_by",
            "work_content", "worker_count", "confined_space_type",
            "monitor_placement", "rescue_equipment", "emergency_contact",
            "access_control", "work_before_check", "work_during_check",
            "work_after_check", "sign_date",
        ),
        repeat_field=None,
        max_repeat_rows=None,
    ),
    "tbm_log": FormSpec(
        form_type="tbm_log",
        display_name="TBM 안전점검 일지",
        version="1.0",
        builder=build_tbm_log_excel,
        required_fields=(
            "tbm_date",            # 실시 일시 [실무 권장]
            "today_work",          # 작업 내용 [실무 권장]
            "hazard_points",       # 위험요인  [실무 권장]
            "safety_instructions", # 안전수칙  [실무 권장]
        ),
        optional_fields=(
            "site_name", "project_name", "tbm_location",
            "ppe_check", "worker_opinion", "action_items",
        ),
        repeat_field="attendees",   # list[dict]: name, job_type
        max_repeat_rows=20,
    ),
    "confined_space_permit": FormSpec(
        form_type="confined_space_permit",
        display_name="밀폐공간 작업허가서",
        version="1.0",
        builder=build_confined_space_permit_excel,
        required_fields=(
            "permit_no",     # 허가 번호     [실무 권장]
            "work_location", # 작업 장소     [법정] 제619조
            "work_content",  # 작업 내용     [법정] 제619조
            "monitor_name",  # 감시인 성명   [법정] 제625조
            "oxygen_level",  # 산소농도 측정값 [법정] 제622조
            "permit_issuer", # 허가자        [실무 권장]
        ),
        optional_fields=(
            "site_name", "project_name",
            "permit_datetime", "validity_period",
            "gas_h2s_level", "gas_co_level", "gas_other",
            "ventilation_status", "rescue_equipment_check",
            "work_end_time", "completion_confirm",
        ),
        repeat_field="workers",   # list[dict]: name, role
        max_repeat_rows=10,
    ),
    "confined_space_checklist": FormSpec(
        form_type="confined_space_checklist",
        display_name="밀폐공간 사전 안전점검표",
        version="1.0",
        builder=build_confined_space_checklist_excel,
        required_fields=(
            "check_date",    # 점검 일자   [실무 권장]
            "work_location", # 작업 장소   [법정] 제619조
            "checker_name",  # 점검자 성명 [실무 권장]
        ),
        optional_fields=(
            "site_name", "project_name", "work_content",
        ),
        repeat_field=None,
        max_repeat_rows=None,
        extra_list_fields=("check_items",),  # list[dict]: item, result, note (미제공 시 기본 10개 자동 적용)
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

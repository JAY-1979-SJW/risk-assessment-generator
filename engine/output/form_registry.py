"""
Form Builder Registry.

form_type 문자열로 builder 함수를 선택하고 호출하는 최소 디스패처.
export API 연결 전 단계 — builder 호출 인터페이스만 제공.

지원 form_type:
    education_log                       — 안전보건교육일지 (v1.1)
    special_education_log               — 특별 안전보건교육 교육일지 (v1.0)  [ED-003]
    manager_job_training_record         — 안전보건관리자 직무교육 이수 확인서 (v1.0) [ED-004]
    risk_assessment                     — 위험성평가표 (v1.0)
    risk_assessment_register            — 위험성평가 관리 등록부 (v1.0)   [RA-002]
    risk_assessment_meeting_minutes     — 위험성평가 참여 회의록 (v1.0)    [RA-003]
    excavation_workplan                 — 굴착 작업계획서 (v1.0)
    vehicle_construction_workplan       — 차량계 건설기계 작업계획서 (v1.0)
    material_handling_workplan          — 차량계 하역운반기계 작업계획서 (v1.0)
    tower_crane_workplan                — 타워크레인 작업계획서 (v1.0)       [WP-006]
    mobile_crane_workplan               — 이동식 크레인 작업계획서 (v1.0)    [WP-007]
    confined_space_workplan             — 밀폐공간 작업계획서 (v1.0)         [WP-014]
    tbm_log                             — TBM 안전점검 일지 (v1.0)           [RA-004]
    confined_space_permit               — 밀폐공간 작업허가서 (v1.0)         [PTW-001]
    hot_work_permit                     — 화기작업 허가서 (v1.0)             [PTW-002]
    work_at_height_permit               — 고소작업 허가서 (v1.0)             [PTW-003]
    excavation_work_permit              — 굴착 작업 허가서 (v1.0)            [PTW-005]
    heavy_lifting_workplan              — 중량물 취급 작업계획서 (v1.0)            [WP-005]
    lifting_work_permit                 — 중량물 인양·중장비사용 작업 허가서 (v1.0) [PTW-007]
    confined_space_checklist            — 밀폐공간 사전 안전점검표 (v1.0)    [CL-010]
    work_environment_measurement        — 작업환경측정 실시 및 결과 관리대장 (v1.0) [HM-001]
    special_health_examination          — 특수건강진단 대상자 및 결과 관리대장 (v1.0) [HM-002]
    formwork_shoring_workplan           — 거푸집·동바리 작업계획서 (v1.0)            [WP-015]
    scaffold_installation_checklist     — 비계 설치 점검표 (v1.0)                    [CL-001]
    tower_crane_self_inspection_checklist — 타워크레인 자체 점검표 (v1.0)            [CL-006]
    construction_equipment_daily_checklist — 건설장비 일일 사전점검표 (v1.0)        [CL-003]
    formwork_shoring_installation_checklist — 거푸집 및 동바리 설치 점검표 (v1.0)  [CL-002]
    fall_protection_checklist             — 추락 방호 설비 점검표 (v1.0)                [CL-007]
    electrical_workplan                   — 전기 작업계획서 (v1.0)                       [WP-011]
    electrical_work_permit                — 전기작업 허가서 / LOTO (v1.0)                [PTW-004]
    electrical_facility_checklist         — 전기설비 정기 점검표 (v1.0)                   [CL-004]
    fire_prevention_checklist             — 화재 예방 점검표 (v1.0)                        [CL-005]
    work_safety_checklist                 — 작업 전 안전 확인서 (v1.0)                    [DL-005]
    hot_work_workplan                     — 용접·용단·화기작업 계획서 (v1.0)              [EQ-014]
    piling_workplan                       — 항타기·항발기·천공기 사용계획서 (v1.0)        [EQ-009]
    piling_use_workplan                   — 항타기·항발기 사용 작업계획서 (v1.0)          [WP-010]
    tunnel_excavation_workplan            — 터널 굴착 작업계획서 (v1.0)                    [WP-002]
    construction_equipment_entry_request  — 건설 장비 반입 신청서 (v1.0)                   [PPE-002]
    temp_electrical_installation_permit   — 임시전기 설치·연결 허가서 (v1.0)               [PTW-008]

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
from engine.output.excavation_work_permit_builder import build_excavation_work_permit_excel
from engine.output.hot_work_permit_builder import build_hot_work_permit_excel
from engine.output.work_at_height_permit_builder import build_work_at_height_permit_excel
from engine.output.lifting_work_permit_builder import build_lifting_work_permit_excel
from engine.output.confined_space_workplan_builder import build_confined_space_workplan_excel
from engine.output.education_log_builder import build_education_log_excel
from engine.output.form_excel_builder import build_form_excel as _build_risk_assessment_excel_raw
from engine.output.formwork_shoring_workplan_builder import build_formwork_shoring_workplan_excel
from engine.output.construction_equipment_daily_checklist_builder import build_construction_equipment_daily_checklist_excel
from engine.output.formwork_shoring_installation_checklist_builder import build_formwork_shoring_installation_checklist_excel
from engine.output.scaffold_installation_checklist_builder import build_scaffold_installation_checklist_excel
from engine.output.tower_crane_self_inspection_checklist_builder import build_tower_crane_self_inspection_checklist_excel
from engine.output.manager_job_training_record_builder import build_manager_job_training_record_excel
from engine.output.material_handling_workplan_builder import build_material_handling_workplan_excel
from engine.output.mobile_crane_workplan_builder import build_mobile_crane_workplan_excel
from engine.output.special_education_log_builder import build_special_education_log_excel
from engine.output.special_health_examination_builder import build_special_health_examination_excel
from engine.output.tbm_log_builder import build_tbm_log_excel
from engine.output.risk_assessment_register_builder import build_risk_assessment_register_excel
from engine.output.risk_assessment_meeting_minutes_builder import build_risk_assessment_meeting_minutes_excel
from engine.output.risk_assessment_procedure_builder import build_risk_assessment_procedure
from engine.output.risk_assessment_result_notice_builder import build_risk_assessment_result_notice
from engine.output.tower_crane_workplan_builder import build_tower_crane_workplan_excel
from engine.output.vehicle_workplan_builder import build_vehicle_workplan_excel
from engine.output.work_environment_measurement_builder import build_work_environment_measurement_excel
from engine.output.safety_management_log_builder import build_safety_management_log
from engine.output.supervisor_safety_log_builder import build_supervisor_safety_log
from engine.output.safety_patrol_inspection_log_builder import build_safety_patrol_inspection_log
from engine.output.weather_condition_log_builder import build_weather_condition_log
from engine.output.pre_work_safety_check_builder import build_pre_work_safety_check
from engine.output.work_safety_checklist_builder import build_work_safety_checklist
from engine.output.heavy_lifting_workplan_builder import build_heavy_lifting_workplan_excel
from engine.output.workplan_builder import build_excavation_workplan_excel
from engine.output.fall_protection_checklist_builder import build_fall_protection_checklist_excel
from engine.output.electrical_workplan_builder import build_electrical_workplan_excel
from engine.output.electrical_work_permit_builder import build_electrical_work_permit_excel
from engine.output.electrical_facility_checklist_builder import build_electrical_facility_checklist_excel
from engine.output.fire_prevention_checklist_builder import build_fire_prevention_checklist_excel
from engine.output.protective_equipment_checklist_builder import build_protective_equipment_checklist
from engine.output.ppe_management_checklist_builder import build_ppe_management_checklist
from engine.output.hazardous_chemical_checklist_builder import build_hazardous_chemical_checklist
from engine.output.hot_work_workplan_builder import build_hot_work_workplan_excel
from engine.output.piling_workplan_builder import build_piling_workplan_excel
from engine.output.piling_use_workplan_builder import build_piling_use_workplan_excel
from engine.output.tunnel_excavation_workplan_builder import build_tunnel_excavation_workplan_excel
from engine.output.building_demolition_workplan_builder import build_building_demolition_workplan_excel
from engine.output.aerial_work_platform_use_plan_builder import build_aerial_work_platform_use_plan_excel
from engine.output.bridge_work_workplan_builder import build_bridge_work_workplan_excel
from engine.output.earthwork_equipment_use_plan_builder import build_earthwork_equipment_use_plan_excel
from engine.output.lifting_equipment_workplan_builder import build_lifting_equipment_workplan_excel
from engine.output.track_maintenance_workplan_builder import build_track_maintenance_workplan
from engine.output.contractor_safety_consultation_builder import build_contractor_safety_consultation_excel
from engine.output.safety_committee_minutes_builder import build_safety_committee_minutes_excel
from engine.output.industrial_accident_report_builder import build_industrial_accident_report_excel
from engine.output.emergency_contact_evacuation_plan_builder import build_emergency_contact_evacuation_plan_excel
from engine.output.emergency_first_aid_record_builder import build_emergency_first_aid_record_excel
from engine.output.accident_root_cause_prevention_report_builder import build_accident_root_cause_prevention_report_excel
from engine.output.ppe_issuance_ledger_builder import build_ppe_issuance_ledger_excel
from engine.output.ppe_issue_register_builder import build_ppe_issue_register
from engine.output.chemical_equipment_workplan_builder import build_chemical_equipment_workplan_excel
from engine.output.asbestos_removal_workplan_builder import build_asbestos_removal_workplan_excel
from engine.output.contractor_safety_document_checklist_builder import build_contractor_safety_document_checklist_excel
from engine.output.annual_safety_education_plan_builder import build_annual_safety_education_plan_excel
from engine.output.near_miss_report_builder import build_near_miss_report_excel
from engine.output.lift_gondola_use_plan_builder import build_lift_gondola_use_plan_excel
from engine.output.temp_power_generator_use_plan_builder import build_temp_power_generator_use_plan_excel
from engine.output.ladder_stepladder_workboard_use_plan_builder import build_ladder_stepladder_workboard_use_plan_excel
from engine.output.construction_equipment_entry_request_builder import build_construction_equipment_entry_request_excel
from engine.output.equipment_entry_application_builder import build_equipment_entry_application
from engine.output.equipment_insurance_inspection_check_builder import build_equipment_insurance_inspection_check
from engine.output.msds_posting_education_check_builder import build_msds_posting_education_check
from engine.output.temp_electrical_installation_permit_builder import build_temp_electrical_installation_permit_excel
from engine.output.safety_cost_use_plan_builder import build_safety_cost_use_plan_excel
from engine.output.health_exam_result_builder import build_health_exam_result_excel
from engine.output.new_worker_safety_pledge_builder import build_new_worker_safety_pledge_excel
from engine.output.foreign_worker_safety_edu_builder import build_foreign_worker_safety_edu_excel
from engine.output.serious_accident_immediate_report_builder import build_serious_accident_immediate_report_excel
from engine.output.safety_manager_appointment_report_builder import build_safety_manager_appointment_report_excel
from engine.output.industrial_accident_status_ledger_builder import build_industrial_accident_status_ledger
from engine.output.radiography_work_permit_builder import build_radiography_work_permit


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
    # ------------------------------------------------------------------
    # P1 — ED-003 (2026-04-25)
    # 법적 근거: 산안법 제29조 제3항, 시행규칙 제26조, 별표 4, 별표 5
    # evidence_status: NEEDS_VERIFICATION (별표 4/5 원문 evidence 미수집)
    # ------------------------------------------------------------------
    "special_education_log": FormSpec(
        form_type="special_education_log",
        display_name="특별 안전보건교육 교육일지",
        version="1.0",
        builder=build_special_education_log_excel,
        required_fields=(
            # 산업안전보건법 제29조 제3항 / 시행규칙 제26조 법정 필수
            "education_date",           # 교육 일자
            "education_location",       # 교육 장소
            "education_target_work",    # 교육 대상 작업명 (별표 5 기준)
            "instructor_name",          # 강사 성명
            "confirmer_name",           # 교육담당자 성명
            "confirmer_role",           # 교육담당자 직위
        ),
        optional_fields=(
            "site_name",
            "site_address",
            "education_name",
            "target_work_free_input",   # 별표 5 미수집 시 자유입력
            "related_education",
            "duration_category",        # 교육시간 구분 (별표 4 기준)
            "actual_duration_hours",
            "remaining_hours",
            "subjects",                 # list[dict]: subject_name, subject_content, subject_hours
            "instructor_org",
            "instructor_role",
            "instructor_qualification",
            "attendees",                # list[dict]: attendee_name, attendee_org, attendee_job_type, attendee_birth_year, attendee_completed
            "comprehension_verbal",
            "comprehension_checklist",
            "comprehension_practice",
            "retraining_targets",
            "attachments",
            "supervisor_name",
            "site_manager_name",
            "confirm_date",
        ),
        repeat_field="attendees",
        max_repeat_rows=30,  # MAX_ATTENDEES
        extra_list_fields=("subjects",),
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
            "trade_name",          # 작업 공종명 (공종별 프리셋 연동 시 자동 입력)
            "pre_work_checks",     # 작업 전 확인사항 (서류·보호구·장비 체크리스트)
            "permit_check",        # 작업허가서 확인 (허가서 번호/종류)
            "ppe_check", "worker_opinion", "action_items",
        ),
        repeat_field="attendees",   # list[dict]: name, job_type
        max_repeat_rows=20,
    ),
    # ------------------------------------------------------------------
    # RA-003 — 위험성평가 참여 회의록 (2026-04-26)
    # 법적 근거: 산업안전보건법 제36조 제3항 (근로자 참여 보장)
    # evidence_status: RA-001 공유 (동일 산안법 제36조 근거)
    "risk_assessment_meeting_minutes": FormSpec(
        form_type="risk_assessment_meeting_minutes",
        display_name="위험성평가 참여 회의록",
        version="1.0",
        builder=build_risk_assessment_meeting_minutes_excel,
        required_fields=(),
        optional_fields=(
            "site_name", "project_name", "representative", "safety_manager",
            "meeting_date", "meeting_place", "work_type", "meeting_purpose",
            "discussion_items", "worker_opinions", "meeting_summary",
            "prepared_by", "reviewed_by", "approved_by",
            "prepared_date", "reviewed_date", "approved_date",
        ),
        repeat_field="attendees",
        max_repeat_rows=15,
    ),
    # ------------------------------------------------------------------
    # P3 — RA-005 (2026-04-29)
    # 법적 근거: 산업안전보건법 제36조, 시행규칙 제37조,
    #           고용노동부고시 제2023-19호 제9조 (실시규정 작성 권고)
    # evidence_status: PRACTICAL — 법정 별지 서식 없음, 고시 제9조 권고 이행용
    # 역할: 사업장 위험성평가 운영 체계 규정서.
    #       RA-001(평가표)/RA-002(등록부)/RA-003(회의록)/RA-006(공지문)과 역할 분리.
    # ------------------------------------------------------------------
    "risk_assessment_procedure": FormSpec(
        form_type="risk_assessment_procedure",
        display_name="위험성평가 실시 규정",
        version="1.0",
        builder=build_risk_assessment_procedure,
        required_fields=(
            "company_name",    # 사업장명
            "established_by",  # 작성/제정자
            "issue_date",      # 제정일
        ),
        optional_fields=(
            "doc_no", "revision", "revision_date",
            "approver", "reviewer", "applicable_site",
            "purpose", "scope",
            "timing_initial", "timing_regular",
            "timing_occasional", "timing_tbm",
            "risk_matrix_desc",
            "risk_level_high", "risk_level_medium", "risk_level_low",
            "acceptable_level",
            "measure_priority", "measure_tracking", "measure_verify",
            "participation_method", "education_timing", "education_content",
            "disclosure_method",
            "review_cycle", "review_trigger", "revision_procedure",
        ),
        repeat_field="step_items",
        max_repeat_rows=10,
        extra_list_fields=("term_items", "role_items", "record_items", "revision_history"),
    ),
    # ------------------------------------------------------------------
    # P3 — RA-006 (2026-04-29)
    # 법적 근거: 산업안전보건법 제36조 제3항(위험성평가 결과 주지),
    #           고용노동부고시 제2023-19호 제21조(게시·공지 권고), 제3조(근로자 참여)
    # evidence_status: PRACTICAL — 법정 별지 서식 없음, 고시 권고 이행용 현장 게시용
    # 역할: 위험성평가 결과 근로자 공지·증빙. RA-001(원본)/RA-005(규정)와 역할 분리.
    # ------------------------------------------------------------------
    "risk_assessment_result_notice": FormSpec(
        form_type="risk_assessment_result_notice",
        display_name="위험성평가 결과 근로자 공지문",
        version="1.0",
        builder=build_risk_assessment_result_notice,
        required_fields=(
            "site_name",    # 사업장명
            "notice_date",  # 공지 일자
            "supervisor",   # 관리감독자
        ),
        optional_fields=(
            "project_name", "company_name", "safety_manager",
            "ra_ref_no", "ra_date",
            "work_type", "work_location", "work_period", "target_workers",
            "ra_summary", "ra_participants", "ra_method",
            "total_hazards", "high_risk_count", "medium_risk_count", "low_risk_count",
            "ppe_required", "restricted_zone", "access_condition",
            "post_start_date", "post_end_date",
            "post_location_1", "post_location_2",
            "confirm_date", "approver",
        ),
        repeat_field="hazard_items",
        max_repeat_rows=12,
        extra_list_fields=("precaution_items", "worker_sign_items"),
    ),
    # ------------------------------------------------------------------
    # RA-002 — 위험성평가 관리 등록부 (2026-04-26)
    # 법적 근거: 산업안전보건법 시행규칙 제37조 (기록·보존 3년)
    # evidence_status: RA-001 공유 (동일 산안법 제36조·시행규칙 제37조 근거)
    "risk_assessment_register": FormSpec(
        form_type="risk_assessment_register",
        display_name="위험성평가 관리 등록부",
        version="1.0",
        builder=build_risk_assessment_register_excel,
        required_fields=(),
        optional_fields=(
            "site_name", "project_name", "representative", "safety_manager",
            "prepared_by", "reviewed_by", "approved_by",
            "prepared_date", "reviewed_date", "approved_date",
        ),
        repeat_field="entries",
        max_repeat_rows=30,
    ),
    # ------------------------------------------------------------------
    # P1 — PTW-002 (2026-04-25)
    # 법적 근거: 산안규칙 제236조, 제240조, 제241조, 제241조의2, 제243조, 제244조
    # evidence_status: PARTIAL_VERIFIED (조항 확인, 원문 API 미수집. KOSHA NEEDS_VERIFICATION)
    # 주의: 법정 별지 서식 없음. KOSHA P-94-2021 별지 양식1 참고. 자체 표준 서식.
    #       화재감시자 배치는 조건부 판단 — 모든 화기작업 무조건 필수 아님.
    #       법정 안전보건교육 수료증 대체 불가.
    # ------------------------------------------------------------------
    "hot_work_permit": FormSpec(
        form_type="hot_work_permit",
        display_name="화기작업 허가서",
        version="1.0",
        builder=build_hot_work_permit_excel,
        required_fields=(
            # 산안규칙 제241조 제4항 — 서면 게시 의무 이행 필수 정보
            "site_name",       # 현장명
            "work_date",       # 작업일자
            "work_time",       # 작업시간
            "work_location",   # 작업장소
            "trade_name",      # 작업공종
            "work_content",    # 작업내용
            "contractor",      # 작업업체
            "work_supervisor", # 작업책임자
        ),
        optional_fields=(
            "project_name", "permit_no",
            "equipment_list",
            "combustibles_present", "combustibles_removed",
            "hazmat_storage", "flammable_vapor",
            "spark_prevention", "fire_blanket_used",
            "extinguisher_placed", "ventilation_status",
            "fire_watch_required", "fire_watch_name", "fire_watch_equipment",
            "permit_issuer", "supervisor_name", "validity_period",
            "during_work_issues",
            "work_end_time", "post_work_confirmer",
            "final_sign", "safety_manager_sign",
            "photo_file_list",
            # list fields
            "work_types",          # list[str]: 화기작업 종류 선택
            "pre_work_checks",     # list[str]: 이행된 안전조치 항목명
            "fire_ext_checks",     # list[str]: 이행된 소화설비 항목명
            "fire_watch_conditions", # list[str]: 해당 화재감시자 판단 조건
            "ppe_checks",          # list[str]: 지급된 보호구 항목명
            "post_work_checks",    # list[str]: 이행된 작업 종료 확인 항목명
            "photo_items",         # list[str]: 촬영된 사진 항목명
            "workers",             # list[dict]: name, job_type
        ),
        repeat_field="workers",
        max_repeat_rows=10,
        extra_list_fields=(
            "work_types", "pre_work_checks", "fire_ext_checks",
            "fire_watch_conditions", "ppe_checks", "post_work_checks",
            "photo_items",
        ),
    ),
    # ------------------------------------------------------------------
    # P1 — PTW-003 (2026-04-25)
    # 법적 근거: 산안규칙 제37조, 제42조~제45조, 제57조~제58조, 제186조
    # evidence_status: PARTIAL_VERIFIED (L1~L4 법령 원문 확인. K1~K3 KOSHA PDF 미수집)
    # 주의: 법정 별지 서식 없음. 자체 표준서식.
    #       법정 안전보건교육 수료증 대체 불가.
    #       비계 작업 → CL-001 병행 확인. 고소작업대 → CL-003 병행 확인.
    # ------------------------------------------------------------------
    "work_at_height_permit": FormSpec(
        form_type="work_at_height_permit",
        display_name="고소작업 허가서",
        version="1.0",
        builder=build_work_at_height_permit_excel,
        required_fields=(
            # 산안규칙 제42조 안전조치 이행 확인 필수 정보
            "site_name",       # 현장명
            "work_date",       # 작업일자
            "work_time",       # 작업시간
            "work_location",   # 작업장소
            "trade_name",      # 작업공종
            "work_content",    # 작업내용
            "contractor",      # 작업업체
            "work_supervisor", # 작업책임자
        ),
        optional_fields=(
            "project_name", "permit_no",
            "work_height",
            "equipment_list", "equipment_type",
            "fall_risk_present", "opening_present",
            "workboard_installed", "railing_installed",
            "lanyard_worn", "anchor_confirmed",
            "falling_zone_set", "access_control", "weather_confirmed",
            "permit_issuer", "supervisor_name", "safety_manager_sign",
            "work_end_confirmer", "final_sign", "validity_period",
            "during_work_issues",
            "work_end_time", "photo_file_list",
            # list fields
            "work_types",         # list[str]: 고소작업 유형 선택
            "pre_work_checks",    # list[str]: 작업 전 안전조치 항목
            "workboard_checks",   # list[str]: 작업발판·비계·사다리 확인 항목
            "aerial_checks",      # list[str]: 고소작업대 확인 항목
            "harness_checks",     # list[str]: 안전대·추락방지설비 확인 항목
            "falling_checks",     # list[str]: 낙하물 방지 확인 항목
            "post_work_checks",   # list[str]: 작업 종료 후 확인 항목
            "photo_items",        # list[str]: 사진 증빙 항목
            "workers",            # list[dict]: name, job_type
        ),
        repeat_field="workers",
        max_repeat_rows=10,
        extra_list_fields=(
            "work_types", "pre_work_checks", "workboard_checks",
            "aerial_checks", "harness_checks", "falling_checks",
            "post_work_checks", "photo_items",
        ),
    ),
    # ------------------------------------------------------------------
    # P1 — WP-005 (2026-04-25)
    # 법적 근거: 산안규칙 제38조 제1항 제11호 + 별표4, 제39조, 제40조,
    #            제132조, 제133조, 제163조~제170조, 제385조
    # evidence_status: NEEDS_VERIFICATION (조항 원문 API 미수집)
    # 주의: 법정 별지 서식 없음. 자체 표준서식.
    #       PTW-007 중량물 인양 허가서 발급 전 이 서식(WP-005) 선행 작성 필수.
    # ------------------------------------------------------------------
    "heavy_lifting_workplan": FormSpec(
        form_type="heavy_lifting_workplan",
        display_name="중량물 취급 작업계획서",
        version="1.0",
        builder=build_heavy_lifting_workplan_excel,
        required_fields=(
            # 산안규칙 제38조+별표4 법정 필수 — 중량물 취급 작업계획서
            "object_name",      # 중량물 명칭   [법정] 별표4
            "object_weight",    # 중량물 중량   [법정] 별표4
            "work_method",      # 작업방법      [법정] 제38조
            "emergency_measure",# 비상조치      [법정] 제38조+별표4
        ),
        optional_fields=(
            "site_name", "project_name", "work_location", "work_date",
            "supervisor", "contractor", "prepared_by",
            "object_size", "object_shape", "weight_basis", "center_of_gravity",
            "transport_route", "route_sketch_note",
            "work_site_condition", "ground_condition", "access_control",
            "equipment_name", "equipment_capacity", "auxiliary_equipment",
            "rigging_method", "rigging_angle", "rigging_gear", "rigging_safety_coeff",
            "work_commander", "signal_worker", "worker_roles",
            "fall_prevention", "drop_prevention", "tipping_prevention",
            "pinch_prevention", "collapse_prevention",
            "pre_work_check_items", "photo_items",
            "sign_date",
        ),
        repeat_field="safety_steps",   # list[dict]: task_step, hazard, safety_measure
        max_repeat_rows=10,
    ),
    # ------------------------------------------------------------------
    # P1 — PTW-007 (2026-04-25)
    # 법적 근거: 산안규칙 제38조+별표4, 제39조, 제40조, 제132조, 제133조, 제135조,
    #            제138조, 제146조④⑤, 제163조~제170조, 제221조의5, 제385조
    # evidence_status: NEEDS_VERIFICATION (조항 원문 API 미수집, KOSHA PDF 미수집)
    # 주의: 법정 별지 서식 없음. 자체 표준서식.
    #       법정 안전보건교육 수료증 대체 불가.
    #       WP-005 작업계획서 대체 불가 — 허가 전 WP-005 선행 작성 필수.
    #       이동식크레인 사용 시 CL-003 장비점검표 병행 확인 필요.
    #       사진 증빙 OPTIONAL.
    # ------------------------------------------------------------------
    "lifting_work_permit": FormSpec(
        form_type="lifting_work_permit",
        display_name="중량물 인양·중장비사용 작업 허가서",
        version="1.0",
        builder=build_lifting_work_permit_excel,
        required_fields=(
            # 산안규칙 제40조(신호방법), 제133조(정격하중), 제146조(출입통제) 이행 확인 필수
            "site_name",       # 현장명
            "work_date",       # 작업일자
            "work_time",       # 작업시간
            "work_location",   # 작업장소
            "trade_name",      # 작업공종
            "work_content",    # 작업내용
            "contractor",      # 작업업체
            "work_supervisor", # 작업책임자
        ),
        optional_fields=(
            "project_name", "permit_no",
            "lifting_object_name", "lifting_weight",
            "lifting_size", "lifting_height", "lifting_distance", "lifting_route",
            "equipment_name", "equipment_rated_load",
            "work_radius", "outrigger_installed", "ground_condition",
            "rigging_method", "rigging_gear",
            "signal_worker_name",
            "permit_issuer", "supervisor_name", "safety_manager_sign",
            "work_end_confirmer", "final_sign",
            "during_work_issues", "work_end_time", "photo_file_list", "validity_period",
            # list fields
            "lifting_types",        # list[str]: 인양작업 유형 선택
            "workplan_checks",      # list[str]: 작업계획서 확인 항목
            "equipment_checks",     # list[str]: 장비 및 정격하중 확인 항목
            "rigging_checks",       # list[str]: 달기구·줄걸이 확인 항목
            "signal_checks",        # list[str]: 신호수·통제 확인 항목
            "pre_work_checks",      # list[str]: 작업 전 안전조치 항목
            "post_work_checks",     # list[str]: 작업 종료 후 확인 항목
            "photo_items",          # list[str]: 사진 증빙 항목
            "workers",              # list[dict]: name, job_type
        ),
        repeat_field="workers",
        max_repeat_rows=10,
        extra_list_fields=(
            "lifting_types", "workplan_checks", "equipment_checks",
            "rigging_checks", "signal_checks", "pre_work_checks",
            "post_work_checks", "photo_items",
        ),
    ),
    # P2 — PTW-005 (2026-04-26)
    # 법적 근거: 산안규칙 제38조, 제82조~제88조 (굴착작업 안전조치)
    # evidence_status: NEEDS_VERIFICATION
    # 주의: 법정 별지 서식 없음. 자체 표준서식.
    #       WP-001 굴착 작업계획서 선행 작성 필수.
    # ------------------------------------------------------------------
    "excavation_work_permit": FormSpec(
        form_type="excavation_work_permit",
        display_name="굴착 작업 허가서",
        version="1.0",
        builder=build_excavation_work_permit_excel,
        required_fields=(
            "site_name",
            "work_date",
            "work_time",
            "work_location",
            "trade_name",
            "work_content",
            "contractor",
            "work_supervisor",
        ),
        optional_fields=(
            "project_name", "permit_no",
            "excavation_depth", "excavation_area",
            "validity_period",
            "permit_issuer", "supervisor_name", "safety_manager_sign",
            "work_end_confirmer", "final_sign",
            "during_work_issues", "work_end_time", "photo_file_list",
            # list fields
            "pre_check_items",
            "risk_factor_items",
            "safety_measure_items",
            "ppe_items",
            "approval_conditions",
            "stop_conditions",
            "workers",
        ),
        repeat_field="workers",
        max_repeat_rows=10,
        extra_list_fields=(
            "pre_check_items", "risk_factor_items", "safety_measure_items",
            "ppe_items", "approval_conditions", "stop_conditions",
        ),
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
    # ------------------------------------------------------------------
    # P1 — ED-004 (2026-04-25)
    # 법적 근거: 산안법 제32조, 제15조, 제17조, 제18조
    # evidence_status: PARTIAL_VERIFIED (법 제32조 확인, 시행규칙 조항번호 NEEDS_VERIFICATION)
    # 주의: 공식 수료증 대체 아님. 수료증 원본 별도 보관 필요.
    # ------------------------------------------------------------------
    "manager_job_training_record": FormSpec(
        form_type="manager_job_training_record",
        display_name="안전보건관리자 직무교육 이수 확인서",
        version="1.0",
        builder=build_manager_job_training_record_excel,
        required_fields=(
            # 산안법 제32조 법정 필수 — 역할 선택 통합 관리
            "role_type",        # 역할 구분 (안전보건관리책임자/안전관리자/보건관리자)
            "training_category", # 신규교육/보수교육 구분
        ),
        optional_fields=(
            "site_name", "field_name", "employer_name", "write_date", "department",
            "person_name", "person_org", "person_title", "appointment_date",
            "is_training_target",
            "legal_basis_text", "new_training_deadline", "refresher_cycle",
            "doctor_special_case", "training_exemption",
            "training_org", "training_course",
            "training_start_date", "training_end_date",
            "training_hours", "completion_no", "certificate_date", "completion_status",
            "cert_attached", "agency_confirm_attached",
            "appointment_doc_attached", "refresher_basis_attached",
            "not_completed", "not_completed_reason",
            "action_plan", "scheduled_training_date", "manager_name",
            "writer_name", "safety_manager_sign", "supervisor_sign",
            "site_manager_sign", "sign_date",
        ),
        repeat_field=None,
        max_repeat_rows=None,
    ),
    # ------------------------------------------------------------------
    # P1 — WP-015 (2026-04-25)
    # 법적 근거: 산안규칙 제38조·제39조·제331조, 제328조~제337조
    # evidence_status: PARTIAL_VERIFIED (제38조 별표4 포함 여부 미확인)
    # 주의: 구조계산·조립도 자체 생성 없음. 첨부·보관 확인 필드로만 구현.
    # ------------------------------------------------------------------
    "formwork_shoring_workplan": FormSpec(
        form_type="formwork_shoring_workplan",
        display_name="거푸집·동바리 작업계획서",
        version="1.0",
        builder=build_formwork_shoring_workplan_excel,
        required_fields=(
            # 산안규칙 제331조 법정 필수 — 구조검토 및 조립도 작성
            "structural_review_done",    # 구조검토 실시 여부 [제331조 제1항]
            "assembly_drawing_done",     # 조립도 작성 여부   [제331조 제1항]
            "work_location",             # 작업 위치          [제38조]
        ),
        optional_fields=(
            "site_name", "project_name", "work_date", "work_period",
            "contractor", "prepared_by", "reviewer", "approver",
            "work_scope", "formwork_type", "shoring_type",
            "floor_section", "work_phases",
            "survey_ground", "survey_substructure", "survey_opening",
            "survey_material_place", "survey_equipment_route",
            "survey_weather", "survey_lighting",
            "structural_reviewer", "member_spec", "install_interval",
            "joint_method", "brace_plan", "base_plate_plan",
            "structural_doc_attached", "assembly_drawing_attached",
            "work_sequence", "safety_measures_text",
            "work_commander_name", "work_commander_org",
            "work_commander_contact", "work_commander_duties",
            "work_commander_educated",
            "education_done", "tbm_done", "sign_date",
        ),
        repeat_field="hazard_items",      # list[dict]: hazard, safety_measure
        max_repeat_rows=10,               # MAX_HAZARD
        extra_list_fields=("pre_check_items",),  # list[dict]: check_item, result, note
    ),
    # ------------------------------------------------------------------
    # HM — 보건관리 서류 (2026-04-25)
    # 외부 전문기관 발급 원본 결과서를 대체하지 않는 사업장 자체 관리대장
    # ------------------------------------------------------------------
    "work_environment_measurement": FormSpec(
        form_type="work_environment_measurement",
        display_name="작업환경측정 실시 및 결과 관리대장",
        version="1.0",
        builder=build_work_environment_measurement_excel,
        required_fields=(
            "target_process",       # 측정 대상 공정/장소  [법정] 산안법 제125조
            "measurement_agency",   # 측정기관명           [법정] 산안법 제125조
            "measurement_date",     # 측정 실시일          [법정] 산안법 제125조
            "hazardous_agents",     # 유해인자 목록        [법정] 산안법 제125조
        ),
        optional_fields=(
            "site_name", "project_name", "work_location",
            "measurement_period", "supervisor", "contractor", "prepared_by",
            "agency_contact", "result_received_date",
            "result_summary", "exceedance_status", "exceedance_detail",
            "improvement_plan", "improvement_deadline", "improvement_done",
            "worker_notification", "original_attached",
            "confirmer_name", "confirmer_role", "sign_date",
        ),
        repeat_field="measurement_rows",   # list[dict]: target_location, hazardous_agent, measured_value, exposure_limit, exceedance
        max_repeat_rows=10,
    ),
    "special_health_examination": FormSpec(
        form_type="special_health_examination",
        display_name="특수건강진단 대상자 및 결과 관리대장",
        version="1.0",
        builder=build_special_health_examination_excel,
        required_fields=(
            "exam_agency",          # 검진기관명     [법정] 산안법 제130조
            "exam_date",            # 검진 실시일    [법정] 산안법 제130조
            "exam_type",            # 검진 구분      [법정] 산안법 제130조
            "hazardous_agents",     # 해당 유해인자  [법정] 산안법 제130조
        ),
        optional_fields=(
            "site_name", "project_name", "exam_target_work",
            "exam_period", "supervisor", "contractor", "prepared_by",
            "agency_contact", "result_received_date",
            "judgment_summary", "followup_plan",
            "non_exam_count", "non_exam_reason", "non_exam_action",
            "original_stored", "privacy_confirmed",
            "confirmer_name", "confirmer_role", "sign_date",
        ),
        repeat_field="worker_rows",   # list[dict]: employee_no, name, birth_year, job_type, exam_done, judgment, followup_needed
        max_repeat_rows=15,
    ),
    # ------------------------------------------------------------------
    # P1 — CL-001 (2026-04-25)
    # 법적 근거: 산안규칙 제57조 (비계 조립·해체·변경)
    # evidence_status: PARTIAL_VERIFIED (제57조 확인, 세부 조항 NEEDS_VERIFICATION)
    # 주의: 비계 전용. 거푸집동바리는 CL-002 별도 서식으로 관리.
    # ------------------------------------------------------------------
    "scaffold_installation_checklist": FormSpec(
        form_type="scaffold_installation_checklist",
        display_name="비계 설치 점검표",
        version="1.0",
        builder=build_scaffold_installation_checklist_excel,
        required_fields=(
            # 산안규칙 제57조 이하 기반 — 점검 기본정보
            "check_date",    # 점검 일자
            "work_location", # 작업 장소
            "checker_name",  # 점검자 성명
        ),
        optional_fields=(
            "site_name", "project_name", "work_date", "supervisor_name",
            "scaffold_type", "scaffold_height", "scaffold_length",
            "scaffold_location", "scaffold_work_type",
            "pre_install_items",   # list[dict]: item, result, note
            "structure_items",     # list[dict]: item, result, note
            "workboard_items",     # list[dict]: item, result, note
            "railing_items",       # list[dict]: item, result, note
            "assembly_items",      # list[dict]: item, result, note
            "usage_items",         # list[dict]: item, result, note
            "nonconformance_items", # list[dict]: content, location, action, deadline, completed
            "inspector_sign", "supervisor_sign", "manager_sign", "sign_date",
        ),
        repeat_field=None,
        max_repeat_rows=None,
        extra_list_fields=(
            "pre_install_items", "structure_items", "workboard_items",
            "railing_items", "assembly_items", "usage_items",
            "nonconformance_items",
        ),
    ),
    # ------------------------------------------------------------------
    # P2 → P1 — CL-002 (2026-04-25)
    # 법적 근거: 산안규칙 제328조~제337조 (거푸집·동바리 재료·조립도·타설·해체)
    # evidence_status: PARTIAL_VERIFIED (WP-015 evidence 연계, 세부 조항 NEEDS_VERIFICATION 포함)
    # 주의: 거푸집·동바리 설치 점검 전용. 비계(CL-001) 대체 불가.
    #       WP-015 작업계획서 및 구조검토서·조립도 원본 대체 불가.
    #       제338조 이후 굴착작업 계열 조항은 본 서식 근거로 사용하지 않음.
    # ------------------------------------------------------------------
    "formwork_shoring_installation_checklist": FormSpec(
        form_type="formwork_shoring_installation_checklist",
        display_name="거푸집 및 동바리 설치 점검표",
        version="1.0",
        builder=build_formwork_shoring_installation_checklist_excel,
        required_fields=(
            "check_date",    # 점검 일자
            "work_location", # 작업 장소
            "checker_name",  # 점검자 성명
        ),
        optional_fields=(
            "site_name", "project_name", "work_date", "supervisor_name",
            "structure_type", "floor_level", "work_area",
            "formwork_type", "shoring_type",
            "inspector_sign", "supervisor_sign", "work_commander_sign",
            "manager_sign", "sign_date",
        ),
        repeat_field=None,
        max_repeat_rows=None,
        extra_list_fields=(
            "drawing_items", "material_items", "shoring_items",
            "formwork_items", "stability_items", "platform_items",
            "pre_pour_items", "during_pour_items", "removal_items",
            "nonconformance_items",
        ),
    ),
    # ------------------------------------------------------------------
    # P1 — CL-003 (2026-04-25)
    # 법적 근거: 산안규칙 제196조~제199조(차량계 건설기계 NEEDS_VERIFICATION),
    #            제171조~제178조(하역운반기계등 PARTIAL_VERIFIED),
    #            제179조~제183조(지게차 세부 PARTIAL_VERIFIED)
    # evidence_status: PARTIAL_VERIFIED (차량계 건설기계 조항 NEEDS_VERIFICATION 포함)
    # 주의: 일일 사전점검 전용. 작업계획서/장비사용계획서 대체 불가.
    #       타워크레인·이동식 크레인·비계·거푸집동바리 전용 점검 제외.
    # ------------------------------------------------------------------
    "construction_equipment_daily_checklist": FormSpec(
        form_type="construction_equipment_daily_checklist",
        display_name="건설장비 일일 사전점검표",
        version="1.0",
        builder=build_construction_equipment_daily_checklist_excel,
        required_fields=(
            "check_date",    # 점검 일자
            "work_location", # 작업 장소
            "checker_name",  # 점검자 성명
        ),
        optional_fields=(
            "site_name", "project_name",
            "equipment_type", "equipment_model", "equipment_reg_no", "equipment_capacity",
            "operator_name", "operator_license_no",
            "guide_worker_name", "work_commander_name",
            "sign_date",
            "operator_sign", "guide_worker_sign", "work_commander_sign",
            "supervisor_sign", "manager_sign",
        ),
        repeat_field=None,
        max_repeat_rows=None,
        extra_list_fields=(
            "doc_check_items", "appearance_items", "light_items",
            "brake_items", "stability_items", "contact_items",
            "load_items", "additional_items", "nonconformance_items",
        ),
    ),
    # ------------------------------------------------------------------
    # P1 — CL-006 (2026-04-25)
    # 법적 근거: 산안규칙 제142조~제146조 (타워크레인 설치·지지·작업 관련)
    # evidence_status: PARTIAL_VERIFIED (제142조~제146조 확인, 세부 조항 NEEDS_VERIFICATION)
    # 주의: 타워크레인 전용. 제147조·제148조(이동식 크레인) 미적용.
    # ------------------------------------------------------------------
    "tower_crane_self_inspection_checklist": FormSpec(
        form_type="tower_crane_self_inspection_checklist",
        display_name="타워크레인 자체 점검표",
        version="1.0",
        builder=build_tower_crane_self_inspection_checklist_excel,
        required_fields=(
            # 산안규칙 제142조 이하 기반 — 점검 기본정보
            "check_date",    # 점검 일자
            "work_location", # 타워크레인 설치 위치
            "checker_name",  # 점검자 성명
        ),
        optional_fields=(
            "site_name", "project_name", "work_date", "supervisor_name",
            "crane_model", "crane_reg_no", "crane_capacity",
            "crane_height", "crane_work_radius",
            "installation_date", "next_inspection_date",
            "operator_name", "operator_license_no",
            "doc_check_items",       # list[dict]: item, result, note
            "install_check_items",   # list[dict]: item, result, note
            "structure_check_items", # list[dict]: item, result, note
            "rope_check_items",      # list[dict]: item, result, note
            "brake_check_items",     # list[dict]: item, result, note
            "electric_check_items",  # list[dict]: item, result, note
            "radius_check_items",    # list[dict]: item, result, note
            "signal_check_items",    # list[dict]: item, result, note
            "nonconformance_items",  # list[dict]: content, location, action, deadline, completed
            "daily_inspector_sign", "operator_sign",
            "supervisor_sign", "manager_sign", "sign_date",
        ),
        repeat_field=None,
        max_repeat_rows=None,
        extra_list_fields=(
            "doc_check_items", "install_check_items", "structure_check_items",
            "rope_check_items", "brake_check_items", "electric_check_items",
            "radius_check_items", "signal_check_items", "nonconformance_items",
        ),
    ),
    # ------------------------------------------------------------------
    # P2 → P1 — CL-007 (2026-04-25)
    # 법적 근거: 산안규칙 제42조~제45조 (추락방지/개구부방호/안전대부착설비/지붕위험)
    # evidence_status: PARTIAL_VERIFIED (제42~45조 원문 API 수집, 제13조 NEEDS_VERIFICATION)
    # 연계: PTW-003(고소작업허가), CL-001(비계점검), RA-001(위험성평가), RA-004(TBM)
    # 주의: 법정 별지 서식 아님. 실무 점검표. 비계 전용 점검은 CL-001 별도 사용.
    # ------------------------------------------------------------------
    "fall_protection_checklist": FormSpec(
        form_type="fall_protection_checklist",
        display_name="추락 방호 설비 점검표",
        version="1.0",
        builder=build_fall_protection_checklist_excel,
        required_fields=(
            "check_date",    # 점검 일자
            "work_location", # 작업 장소
            "checker_name",  # 점검자 성명
        ),
        optional_fields=(
            "site_name", "project_name", "work_name", "work_height",
            "work_period", "ptw_no", "supervisor_name",
            "hazard_zone_items",   # list[dict]: item, result, note
            "platform_items",      # list[dict]: item, result, note
            "railing_items",       # list[dict]: item, result, note
            "opening_items",       # list[dict]: item, result, note
            "harness_items",       # list[dict]: item, result, note
            "net_items",           # list[dict]: item, result, note
            "special_equip_items", # list[dict]: item, result, note
            "nonconformance_items", # list[dict]: content, location, action, deadline, completed
            "work_verdict",        # 적합/조건부 적합/작업중지
            "verdict_condition",   # 조건부 적합 조건
            "inspector_sign", "supervisor_sign", "manager_sign", "sign_date",
        ),
        repeat_field=None,
        max_repeat_rows=None,
        extra_list_fields=(
            "hazard_zone_items", "platform_items", "railing_items",
            "opening_items", "harness_items", "net_items",
            "special_equip_items", "nonconformance_items",
        ),
    ),
    # ------------------------------------------------------------------
    # P1 — WP-011 (2026-04-25)
    # 법적 근거: 산안규칙 제38조 제1항(별표4 제5호 — 전기작업), 제301조 이하
    # evidence_status: PARTIAL_VERIFIED (제38조 별표4 간접 확인, 제301조 NEEDS_VERIFICATION)
    # 주의: 법정 별지 서식 없음 — 실무 표준서식.
    #       PTW-004 전기작업 허가서·LOTO를 대체하지 않음.
    # ------------------------------------------------------------------
    "electrical_workplan": FormSpec(
        form_type="electrical_workplan",
        display_name="전기 작업계획서",
        version="1.0",
        builder=build_electrical_workplan_excel,
        required_fields=(
            # 산안규칙 제38조 제1항 기반 — 전기작업 필수 기재사항
            "work_location",     # 작업 위치
            "work_supervisor",   # 작업책임자
        ),
        optional_fields=(
            "site_name", "project_name", "work_date", "work_period",
            "contractor", "prepared_by", "reviewer",
            "work_name", "work_datetime", "voltage", "work_category",
            "type_outage", "type_live", "type_near", "type_temp_elec",
            "type_panel", "type_cable", "type_power_tool", "type_test_measure",
            "hazard_electric_shock", "hazard_arc", "hazard_short_circuit",
            "hazard_leakage", "hazard_fire", "hazard_explosion",
            "hazard_fall", "hazard_pinch",
            "prereq_ra001", "prereq_ra004", "prereq_ptw004",
            "prereq_cl004", "prereq_ppe001",
            "loto_scope", "loto_breaker_location",
            "loto_lock_installed", "loto_sign_attached",
            "loto_residual_voltage", "loto_re_energize",
            "live_approach_limit", "live_insulation_ppe", "live_insulation_tools",
            "live_monitor", "live_energized_protect",
            "temp_elcb", "temp_grounding", "temp_wire_protect",
            "temp_waterproof", "temp_overload", "temp_panel_lock",
            "tool_body_damage", "tool_wire_insulation", "tool_plug",
            "tool_ground_wire", "tool_elcb",
            "ppe_insulated_gloves", "ppe_insulated_shoes", "ppe_face_shield",
            "ppe_insulation_mat", "equip_voltage_tester", "equip_insulation_meter",
            "mgmt_zone_control", "mgmt_monitor", "mgmt_emergency_stop",
            "mgmt_fire_response", "mgmt_reenergize_proc",
            "work_verdict", "verdict_condition", "sign_date",
        ),
        repeat_field="nonconformance_items",  # list[dict]: content, action, deadline, completed
        max_repeat_rows=5,                    # MAX_NC
    ),
    # ------------------------------------------------------------------
    # P2 → P1 — CL-004 (2026-04-25)
    # 법적 근거: 산안규칙 제302조~제305조(접지/누전차단기),
    #           제301조·제309조·제313조(전기기계기구/이동전선),
    #           제319조·제323조(정전작업/절연PPE)
    # evidence_status: PARTIAL_VERIFIED (ELEC-001 pack L2/L4/L5/L6 재사용)
    # 주의: 법정 별지 서식 없음. 실무 표준서식.
    #       ELEC-001 공통 evidence pack 재사용. WP-011·PTW-004와 연계.
    # ------------------------------------------------------------------
    "electrical_facility_checklist": FormSpec(
        form_type="electrical_facility_checklist",
        display_name="전기설비 정기 점검표",
        version="1.0",
        builder=build_electrical_facility_checklist_excel,
        required_fields=(
            "site_name",       # 현장명
            "inspection_date", # 점검일
            "inspector",       # 점검자
        ),
        optional_fields=(
            "project_name", "inspection_no",
            "equipment_name", "voltage",
            "inspection_location", "responsible_person",
            "related_wp_no", "related_ptw_no",
            "verdict", "verdict_condition",
            "inspector_sign", "supervisor_sign", "safety_manager_sign",
        ),
        repeat_field="nonconformance_items",
        max_repeat_rows=5,
        extra_list_fields=(
            "panel_checks", "grounding_checks", "wiring_checks",
            "equipment_checks", "temporary_checks", "hazard_checks",
            "ppe_checks",
        ),
    ),
    # ------------------------------------------------------------------
    # P1 — CL-005 (2026-04-25)
    # 법적 근거: 산안규칙 제236조(화재위험 작업 장소·가연물 제거),
    #           제241조(화기작업 안전조치·불티비산방지),
    #           제241조의2(화재감시자 배치),
    #           제243조·제244조(소화설비·잔불감시)
    # evidence_status: PARTIAL_VERIFIED (PTW-002 evidence L1~L4 재사용)
    # 주의: 법정 별지 서식 없음. 실무 표준서식.
    #       PTW-002 화기작업 허가서와 연계 사용.
    # ------------------------------------------------------------------
    "fire_prevention_checklist": FormSpec(
        form_type="fire_prevention_checklist",
        display_name="화재 예방 점검표",
        version="1.0",
        builder=build_fire_prevention_checklist_excel,
        required_fields=(
            "site_name",       # 현장명
            "inspection_date", # 점검일
            "inspector",       # 점검자
        ),
        optional_fields=(
            "project_name", "inspection_no",
            "work_name", "work_location", "work_datetime",
            "work_category", "related_ptw_no", "work_supervisor",
            "verdict", "verdict_condition",
            "inspector_sign", "fire_watch_sign",
            "supervisor_sign", "safety_manager_sign",
        ),
        repeat_field="nonconformance_items",
        max_repeat_rows=5,
        extra_list_fields=(
            "fire_work_types",
            "combustible_checks", "spark_checks",
            "extinguisher_checks", "fire_watch_checks",
            "gas_equip_checks", "elec_fire_checks",
            "post_work_checks",
        ),
    ),
    # ------------------------------------------------------------------
    # P3 — DL-005 (2026-04-26)
    # 법적 근거: 중대재해처벌법 시행령 제4조 (안전보건관리체계 구축 의무)
    # evidence_status: NEEDS_VERIFICATION
    # 주의: 법정 별지 서식 없음. 실무 자체 표준서식.
    #       근로자 개인 작업 개시 전 자가 점검 기록용.
    # ------------------------------------------------------------------
    "safety_management_log": FormSpec(
        form_type="safety_management_log",
        display_name="안전관리 일지",
        version="2.0",
        builder=build_safety_management_log,
        required_fields=(
            "site_name",
            "log_date",
            "writer_name",
            "weather",
            "work_summary",
        ),
        optional_fields=(
            "project_name",
            "log_day_of_week",
            "temperature",
            "work_start_time",
            "work_end_time",
            "reviewer_name",
            "approver_name",
            "work_type",
            "work_zone",
            "worker_count",
            "subcontractor_name",
            "main_equipment",
            "high_risk_work",
            "night_work",
            "work_remarks",
            "tbm_done",
            "risk_assessment_shared",
            "work_plan_checked",
            "permit_required",
            "permit_issued",
            "ppe_check_done",
            "passage_opening_checked",
            "fall_protection_checked",
            "falling_object_checked",
            "electrical_fire_checked",
            "equipment_check_done",
            "emergency_contact_checked",
            "hazard_items",
            "patrol_items",
            "tbm_time",
            "education_topic",
            "attendees_count",
            "absent_count",
            "education_note",
            "foreign_worker_notified",
            "new_worker_educated",
            "sign_sheet_attached",
            "equipment_status",
            "equipment_log_prepared",
            "incoming_equipment_ok",
            "material_storage_ok",
            "ppe_supply_ok",
            "ppe_wearing_ok",
            "defective_ppe_replaced",
            "accident_occurred",
            "near_miss_occurred",
            "first_aid_occurred",
            "em002_linked",
            "em006_linked",
            "serious_accident_report",
            "incident_followup",
            "next_day_work",
            "next_day_hazard",
            "preparation_needed",
            "subcontractor_note",
            "pending_actions",
            "handover_person",
            "receiver_person",
            "safety_manager_name",
            "supervisor_name",
            "site_manager_name",
            "contractor_rep_name",
            "confirm_date",
        ),
        repeat_field="hazard_items",
        max_repeat_rows=5,
    ),
    # ------------------------------------------------------------------
    # DL-002 — 관리감독자 안전보건 업무 일지 (2026-04-27)
    # 법적 근거: 산업안전보건법 제16조 (관리감독자의 안전보건 업무 의무)
    # evidence_status: NEEDS_VERIFICATION
    # 주의: 법정 별지 서식 없음. 실무 자체 표준서식.
    #       관리감독자 당일 안전보건 업무 수행 기록용.
    # ------------------------------------------------------------------
    "supervisor_safety_log": FormSpec(
        form_type="supervisor_safety_log",
        display_name="관리감독자 안전보건 업무 일지",
        version="2.0",
        builder=build_supervisor_safety_log,
        required_fields=(
            "site_name",
            "log_date",
            "supervisor_name",
            "department",
        ),
        optional_fields=(
            "project_name",
            "day_of_week",
            "work_area",
            "position",
            "contact",
            "writer_name",
            "reviewer_name",
            "approver_name",
            "work_items",
            "equipment_checks",
            "ppe_wear_checked",
            "ppe_condition_checked",
            "guard_installed_checked",
            "guard_working_checked",
            "ppe_violation_guidance",
            "edu_guidance_content",
            "improvement_needed",
            "passage_status",
            "material_storage_status",
            "opening_area_status",
            "fall_risk_zone_status",
            "lighting_status",
            "emergency_exit_secured",
            "housekeeping_order",
            "housekeeping_done",
            "pretask_applicable",
            "pretask_conducted",
            "pretask_check_items",
            "work_start_approved",
            "work_stopped",
            "tbm_conducted",
            "work_method_guidance",
            "risk_factor_communicated",
            "new_worker_guidance",
            "foreign_worker_communicated",
            "unsafe_behavior_guidance",
            "edu_material_distributed",
            "signature_sheet_attached",
            "accident_occurred",
            "near_miss_occurred",
            "first_aid_needed",
            "reported",
            "first_aid_content",
            "em002_linked",
            "em006_linked",
            "followup_action",
            "improvement_actions",
            "confirm_supervisor",
            "confirm_safety_manager",
            "confirm_site_manager",
            "confirm_contractor",
            "confirm_date",
        ),
        repeat_field="improvement_actions",
        max_repeat_rows=8,
    ),
    # ------------------------------------------------------------------
    # DL-003 — 안전순찰 점검 일지 (2026-04-27)
    # 법적 근거: 산업안전보건법 제17조 (안전관리자 직무)
    # evidence_status: NEEDS_VERIFICATION
    # 주의: 법정 별지 서식 없음. 실무 자체 표준서식. 현장 순찰 결과 기록용.
    # ------------------------------------------------------------------
    "safety_patrol_inspection_log": FormSpec(
        form_type="safety_patrol_inspection_log",
        display_name="안전순찰 점검 일지",
        version="2.0",
        builder=build_safety_patrol_inspection_log,
        required_fields=(
            "site_name",
            "patrol_date",
            "patrol_officer",
        ),
        optional_fields=(
            "project_name",
            "patrol_time_start",
            "patrol_time_end",
            "patrol_route",
            "department",
            "position",
            "contact",
            "writer_name",
            "reviewer_name",
            "approver_name",
            "weather",
            "temperature",
            "total_workers",
            "high_risk_work_today",
            "patrol_results",
            "fall_protection",
            "electrical_safety",
            "fire_prevention",
            "equipment_safety",
            "chemical_safety",
            "health_hazard",
            "traffic_safety",
            "others_risk",
            "immediate_actions",
            "improvement_actions",
            "repeat_issues",
            "repeat_risk_level",
            "ra_reflected",
            "tbm_reflected",
            "root_cause",
            "prevention_measures",
            "accident_occurred",
            "near_miss_occurred",
            "em_form_linked",
            "em_form_type",
            "followup_needed",
            "followup_content",
            "overall_opinion",
            "handover_items",
            "next_patrol_focus",
        ),
        repeat_field="improvement_actions",
        max_repeat_rows=8,
    ),
    # ------------------------------------------------------------------
    # DL-004 — 기상 조건 기록 일지 (2026-04-28)
    # 법적 근거: 산업안전보건기준에 관한 규칙 제37조 (악천후 및 강풍 시 작업 중지)
    # evidence_status: NEEDS_VERIFICATION
    # 주의: 법정 별지 서식 없음. 실무 자체 표준서식. 기상 위험 및 작업중지 판단 기록용.
    # ------------------------------------------------------------------
    "weather_condition_log": FormSpec(
        form_type="weather_condition_log",
        display_name="기상 조건 기록 일지",
        version="1.0",
        builder=build_weather_condition_log,
        required_fields=(
            "site_name",
            "record_date",
            "recorder",
        ),
        optional_fields=(
            "project_name",
            "department",
            "position",
            "total_workers",
            "obs_time_am",
            "obs_time_pm",
            "temperature_am",
            "temperature_pm",
            "humidity_am",
            "humidity_pm",
            "wind_speed_am",
            "wind_speed_pm",
            "wind_gust_am",
            "wind_gust_pm",
            "wind_direction",
            "precipitation",
            "precipitation_type",
            "snow_depth",
            "visibility",
            "weather_forecast",
            "weather_source",
            "risk_level",
            "affected_work_types",
            "high_risk_equipment",
            "risk_assessment_summary",
            "work_stop_decided",
            "work_stop_time",
            "work_stop_scope",
            "work_stop_reason",
            "work_stop_decision_by",
            "workers_evacuated",
            "evacuation_location",
            "heat_index",
            "heat_alert_level",
            "cooling_measures",
            "work_hour_adjustment",
            "rest_time_provided",
            "water_supply",
            "heat_illness_symptoms",
            "cold_alert_level",
            "cold_prevention_measures",
            "crane_work_suspended",
            "crane_wind_criterion",
            "scaffold_checked",
            "drainage_measures",
            "slope_stability_checked",
            "snow_removal_done",
            "slippery_prevention",
            "resume_decided",
            "resume_time",
            "resume_check_weather",
            "resume_site_inspection",
            "resume_decision_by",
            "resume_conditions",
            "actions",
            "handover_items",
            "next_watch_focus",
            "writer_name",
            "reviewer_name",
            "approver_name",
        ),
        repeat_field="actions",
        max_repeat_rows=8,
    ),
    # ------------------------------------------------------------------
    # DL-005 — 작업 전 안전 확인서 v2 (2026-04-28)
    # 법적 근거: 산업안전보건법 제38조 (안전조치), 제36조 (위험성평가 및 조치사항)
    #           산업안전보건기준에 관한 규칙 별표 3 (작업시작 전 점검사항)
    # evidence_status: NEEDS_VERIFICATION
    # 주의: 법정 별지 서식 없음. 실무 자체 표준서식. 작업 시작 직전 작업개시 가능 여부 확인용.
    #       work_safety_checklist(개인 자가 점검)와 별도 운영.
    # ------------------------------------------------------------------
    "pre_work_safety_check": FormSpec(
        form_type="pre_work_safety_check",
        display_name="작업 전 안전 확인서",
        version="2.0",
        builder=build_pre_work_safety_check,
        required_fields=(
            "site_name",
            "work_date",
            "confirmer",
        ),
        optional_fields=(
            "project_name",
            "work_day",
            "work_start_time",
            "work_zone",
            "writer_name",
            "reviewer_name",
            "approver_name",
            "work_name",
            "work_type",
            "work_content",
            "work_location",
            "worker_count",
            "subcontractor",
            "equipment_used",
            "materials_used",
            "high_risk_work",
            "special_notes",
            "workplan_required",
            "workplan_approved",
            "permit_required",
            "permit_issued",
            "hazardous_work_type",
            "permit_conditions_ok",
            "related_form_number",
            "stop_if_unmet",
            "ra_conducted",
            "ra_shared",
            "residual_risk_checked",
            "tbm_conducted",
            "tbm_attendees",
            "tbm_absentee_action",
            "new_worker_informed",
            "foreign_worker_informed",
            "passage_secured",
            "opening_protected",
            "fall_prevented",
            "falling_object_prevented",
            "lighting_ok",
            "ventilation_ok",
            "housekeeping_ok",
            "temp_power_ok",
            "combustibles_removed",
            "escape_route_secured",
            "equipment_inspected",
            "tools_ok",
            "elcb_checked",
            "safety_device_ok",
            "ppe_issued",
            "ppe_worn",
            "safety_harness_attached",
            "defective_ppe_replaced",
            "weather_checked",
            "weather_risk",
            "work_stop_criteria",
            "dl004_linked",
            "gas_measurement_needed",
            "hazardous_env_risk",
            "emergency_contact_ok",
            "first_aid_location",
            "extinguisher_location",
            "aed_location",
            "fire_report_ok",
            "evacuation_route_ok",
            "assembly_point_ok",
            "first_aid_person",
            "work_start_approved",
            "conditional_approval",
            "conditional_conditions",
            "work_stop_reason",
            "remedial_action",
            "remedial_person",
            "remedial_eta",
            "reconfirmer",
            "final_approver",
            "foreman_name",
            "supervisor_name",
            "safety_manager_name",
            "site_manager_name",
            "subcontractor_manager",
            "confirm_date",
        ),
        repeat_field=None,
        max_repeat_rows=None,
    ),
    # ------------------------------------------------------------------
    # DL-005 (v1 레거시) — 작업자 개인 자가 점검서 (2026-04-26)
    # 법적 근거: 중대재해처벌법 시행령 제4조 (안전보건관리체계 구축 의무)
    # evidence_status: VERIFIED (DL-001과 공유)
    # 주의: 개인 자가 점검서. DL-005 v2(pre_work_safety_check)와 별도 운영.
    "work_safety_checklist": FormSpec(
        form_type="work_safety_checklist",
        display_name="작업 전 안전 확인서",
        version="1.0",
        builder=build_work_safety_checklist,
        required_fields=(
            "site_name",
            "check_date",
            "worker_name",
        ),
        optional_fields=(
            "project_name",
            "department", "position",
            "work_type", "work_location", "work_time",
            "supervisor_name", "work_content",
            "hazard_found", "hazard_description",
            "action_taken", "action_taken_by", "action_completed",
            "work_approval", "work_approval_reason",
            "checker_name", "manager_sign", "check_datetime",
        ),
        repeat_field=None,
        max_repeat_rows=None,
    ),
    # ------------------------------------------------------------------
    # P3 — CL-008 (2026-04-26)
    # 법적 근거: 산안규칙 제5조, 제115조~제118조 (보호구 지급·관리)
    # evidence_status: NEEDS_VERIFICATION
    # 주의: 법정 별지 서식 없음. 실무 자체 표준서식.
    #       보호구 지급 및 착용 관리 점검 기록용.
    # ------------------------------------------------------------------
    "protective_equipment_checklist": FormSpec(
        form_type="protective_equipment_checklist",
        display_name="보호구 지급 및 관리 점검표",
        version="1.0",
        builder=build_protective_equipment_checklist,
        required_fields=(
            "site_name",
            "check_date",
            "inspector_name",
        ),
        optional_fields=(
            "project_name",
            "department", "position",
            "work_trade", "work_location", "work_description",
            "worker_count", "supervisor_name",
            "helmet_status", "safety_shoes_status", "safety_belt_status",
            "safety_glasses_status", "dust_mask_status", "gas_mask_status",
            "ear_protection_status", "safety_gloves_status", "face_shield_status",
            "protective_clothing_status", "overall_result", "remarks",
        ),
        repeat_field=None,
        max_repeat_rows=None,
    ),
    # ------------------------------------------------------------------
    # P3 — CL-008 v2 (2026-04-28)
    # 법적 근거: 산안규칙 제32조 보호구 지급, 제33조 보호구 관리, 제34조 전용 보호구
    # evidence_status: PRACTICAL — 법정 별지 서식 없음
    # 주의: 공식 별지 제출서식 아님. 보호구 지급·착용·손상·보관·재고·관리상태 점검 보조서식.
    #       PPE-001(지급 이력), DL-005(작업개시 확인)와 역할 분리.
    # ------------------------------------------------------------------
    "ppe_management_checklist": FormSpec(
        form_type="ppe_management_checklist",
        display_name="보호구 지급 및 관리 점검표 (v2)",
        version="2.0",
        builder=build_ppe_management_checklist,
        required_fields=(
            "site_name",    # 현장명
            "check_date",   # 점검일
            "inspector",    # 점검자
        ),
        optional_fields=(
            "project_name", "check_zone", "manager", "writer", "reviewer", "approver",
            "helmet_issued", "safety_belt_issued", "safety_shoes_issued",
            "safety_glasses_issued", "face_shield_issued", "dust_mask_issued",
            "respirator_issued", "ear_protection_issued", "gloves_issued",
            "protective_clothing_issued", "ppe_fit_for_work",
            "target_work", "target_workers", "actual_wearers", "non_wearers",
            "improper_wearing", "non_wearing_reason", "immediate_guidance",
            "work_stopped", "recheck_result",
            "damaged_ppe_type", "damaged_qty", "damage_content",
            "expired_ppe", "certification_ok", "disposal_needed",
            "replacement_needed", "action_person", "action_completed",
            "individual_ppe_required", "infection_risk_ppe", "shared_use",
            "id_marking", "cleaning_status", "storage_personal",
            "no_individual_reason", "individual_action_plan",
            "storage_location", "storage_status", "contamination_exposure",
            "stock_qty", "shortage_qty", "purchase_needed",
            "disposal_scheduled_qty", "next_inspection_date",
            "wearing_edu_done", "usage_guide_done", "new_worker_edu",
            "foreign_worker_guide", "edu_material_distributed",
            "signature_confirmed", "no_edu_action",
            "ppe001_reflected", "nonissue_supplemented", "dl005_linked",
            "pre_work_recheck_needed", "related_form_no", "follow_up",
            "inspector_sign", "safety_manager_name", "supervisor_name",
            "site_manager_name", "subcon_manager_name", "confirm_date",
            "deficiency_records",  # list[dict]: content, risk_grade, action, person, due_date, completed_date, status, evidence, confirmer
        ),
        repeat_field="deficiency_records",
        max_repeat_rows=10,
    ),
    # ------------------------------------------------------------------
    # P3 — CL-009 (2026-04-27)
    # 법적 근거: 산안규칙 제441조 이하 (유해화학물질 취급)
    # evidence_status: NEEDS_VERIFICATION
    # 주의: 법정 별지 서식 없음. 실무 자체 표준서식.
    #       유해화학물질 취급 작업 현장에서 MSDS, 라벨, 보관, 환기 등을 점검.
    # ------------------------------------------------------------------
    "hazardous_chemical_checklist": FormSpec(
        form_type="hazardous_chemical_checklist",
        display_name="유해화학물질 취급 점검표",
        version="1.0",
        builder=build_hazardous_chemical_checklist,
        required_fields=(
            "site_name",
            "check_date",
            "inspector_name",
        ),
        optional_fields=(
            "project_name",
            "department", "position",
            "work_location", "work_description",
            "chemical_name", "cas_no",
            "chemical_purpose", "taking_amount", "taking_method",
            "storage_chemical_name",
            "msds_available", "msds_understanding",
            "container_label", "label_legible",
            "storage_condition", "storage_location",
            "incompatible_separated", "spill_kit_available",
            "ventilation_status", "fire_extinguisher_available",
            "emergency_response_plan",
            "ppe_required",
            "judgment", "judgment_reason", "remarks",
            "preparer_name", "reviewer_sign", "approval_sign",
        ),
        repeat_field="nonconformance_items",
        max_repeat_rows=8,
    ),
    # ------------------------------------------------------------------
    # P2 → P1 — PTW-004 (2026-04-25)
    # 법적 근거: 산안규칙 제319조~제320조(정전/LOTO), 제321조~제322조(활선/근접),
    #           제323조(절연PPE), 제302조~제305조(접지/누전차단기)
    # evidence_status: PARTIAL_VERIFIED (ELEC-001 pack L2/L3/L5 재사용)
    # 주의: 법정 별지 서식 없음. 실무 표준서식.
    #       ELEC-001 공통 evidence pack 재사용. WP-011과 연계.
    #       CL-004 전기설비 정기점검표 builder v1.0 구현 완료(2026-04-25).
    # ------------------------------------------------------------------
    "electrical_work_permit": FormSpec(
        form_type="electrical_work_permit",
        display_name="전기작업 허가서 / LOTO",
        version="1.0",
        builder=build_electrical_work_permit_excel,
        required_fields=(
            "site_name",       # 현장명
            "work_date",       # 작업일자
            "work_location",   # 작업 위치
            "work_supervisor", # 작업책임자
        ),
        optional_fields=(
            "project_name", "permit_no", "work_time", "voltage",
            "work_category", "contractor", "work_name",
            "permit_issuer", "supervisor_name", "safety_manager",
            "validity_period",
            "loto_scope", "loto_breaker_location", "loto_key_holder",
            "voltage_tester_used", "voltage_zero_confirmed",
            "residual_voltage_result", "ground_confirmed",
            "voltage_measurer_sign",
            "reenergize_approver", "work_end_time", "work_end_confirmer",
            "during_work_issues", "final_sign",
        ),
        repeat_field="nonconformance_items",  # list[dict]: content, action, deadline, completed
        max_repeat_rows=5,
        extra_list_fields=(
            "work_types", "prereq_checks", "loto_checks",
            "voltage_zero_checks", "live_work_checks", "ppe_checks",
            "zone_control_checks", "stop_conditions", "completion_checks",
            "workers",
        ),
    ),
    # ------------------------------------------------------------------
    # P1 — EQ-014 (2026-04-27)
    # 법적 근거: 산안규칙 제241조~제252조 (화재위험작업 준수사항, 화재감시자, 소화설비)
    # evidence_status: PARTIAL_VERIFIED (원문 API 미수집, lbox.kr 확인)
    # 주의: 법정 별지 서식 없음. 실무 표준서식.
    #       PTW-002 화기작업 허가서(허가/승인 절차)와 구분되는 사전 계획 문서.
    #       허가자·승인자·permit_no 등 허가 필드 미포함.
    # ------------------------------------------------------------------
    "hot_work_workplan": FormSpec(
        form_type="hot_work_workplan",
        display_name="용접·용단·화기작업 계획서",
        version="1.0",
        builder=build_hot_work_workplan_excel,
        required_fields=(
            # 산안규칙 제241조 제2항 — 사전 계획 필수 정보
            "site_name",        # 현장명
            "work_date",        # 작업일자/기간
            "work_location",    # 작업장소
            "work_content",     # 화기작업 내용 설명
            "work_types",       # 화기작업 종류 (list[str])
            "safety_measures",  # 안전조치 계획 (종합)
        ),
        optional_fields=(
            "project_name", "trade_name", "contractor",
            "supervisor", "prepared_by", "sign_date",
            "equipment_list", "work_period",
            "combustibles_removed", "spark_prevention",
            "fire_blanket_plan", "extinguisher_plan",
            "ventilation_plan",
            "fire_watch_required", "fire_watch_plan",
            "post_work_plan",
            "emergency_measure", "emergency_contact",
            "overall_opinion",
        ),
        repeat_field="hazard_items",
        max_repeat_rows=10,
        extra_list_fields=("work_types",),
    ),
    "piling_workplan": FormSpec(
        form_type="piling_workplan",
        display_name="항타기·항발기·천공기 사용계획서",
        version="1.0",
        builder=build_piling_workplan_excel,
        required_fields=(
            # 산업안전보건기준에 관한 규칙 제38조 제1항 제12호 법정 필수
            "machine_type",      # 기계의 종류
            "machine_capacity",  # 기계의 성능·최대작업능력
            "work_method",       # 작업방법
        ),
        optional_fields=(
            "site_name",
            "project_name",
            "work_location",
            "work_date",
            "contractor",
            "supervisor",
            "prepared_by",
            "sign_date",
            "machine_model",
            "machine_capacity_kn",
            "pile_type",
            "pile_length",
            "pile_count",
            "ground_survey",
            "underground_facilities",
            "adjacent_structures",
            "noise_vibration_measure",
            "dust_measure",
            "emergency_measure",
            "emergency_contact",
        ),
        repeat_field="hazard_items",
        max_repeat_rows=10,
    ),
    "piling_use_workplan": FormSpec(
        form_type="piling_use_workplan",
        display_name="항타기·항발기 사용 작업계획서",
        version="1.0",
        builder=build_piling_use_workplan_excel,
        required_fields=(
            # 산업안전보건기준에 관한 규칙 제38조 제1항 제12호, 제186조 법정 필수
            "machine_type",     # 기계 종류
            "work_method",      # 작업방법
            "operator_name",    # 조종사 성명
        ),
        optional_fields=(
            "site_name",
            "project_name",
            "work_location",
            "work_date",
            "contractor",
            "supervisor",
            "prepared_by",
            "sign_date",
            "machine_capacity",
            "operator_license",
            "guide_worker",
            "speed_limit",
            "travel_route",
            "work_radius",
            "signal_method",
            "ground_condition",
            "adjacent_risk",
            "emergency_measure",
            "emergency_contact",
            "approver",
        ),
        repeat_field="work_steps",
        max_repeat_rows=8,
        extra_list_fields=("hazard_items",),
    ),
    # ------------------------------------------------------------------
    # P1 — WP-002 (2026-04-28)
    # 법적 근거: 산안규칙 제38조 제1항 제7호, 제46조 이하 (터널공사 안전조치)
    # evidence_status: NEEDS_VERIFICATION (조항 원문 API 미수집)
    # 주의: 법정 별지 서식 없음. 실무 표준서식. 터널공사 한정.
    #       발파 포함 시 화약류 관련 별도 법령(총포도검법 등) 추가 검토 필요.
    # ------------------------------------------------------------------
    "tunnel_excavation_workplan": FormSpec(
        form_type="tunnel_excavation_workplan",
        display_name="터널 굴착 작업계획서",
        version="1.0",
        builder=build_tunnel_excavation_workplan_excel,
        required_fields=(
            # 산안규칙 제38조 제1항 제7호 + 제46조 이하 법정 필수
            "excavation_method",  # 굴착 공법
            "ventilation_plan",   # 환기 계획 [제46조 이하]
            "support_measure",    # 낙반·붕괴 방지 조치 [제46조 이하]
            "emergency_measure",  # 비상조치 방법 [제38조]
        ),
        optional_fields=(
            "site_name", "project_name", "work_location", "work_date",
            "contractor", "supervisor", "prepared_by",
            "tunnel_type", "tunnel_section", "ground_condition",
            "blasting_plan", "lighting_plan", "access_control",
            "emergency_contacts",   # list[dict]: role, name, phone
            "safety_steps",         # list[dict]: task_step, hazard, safety_measure, responsible
            "sign_date",
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("emergency_contacts",),
    ),
    # ------------------------------------------------------------------
    # WP-003 건축물 해체 작업계획서
    # 법적 근거: 산안규칙 제38조 제1항 제9호, 제52조~제55조
    # ------------------------------------------------------------------
    "building_demolition_workplan": FormSpec(
        form_type="building_demolition_workplan",
        display_name="건축물 해체 작업계획서",
        version="1.0",
        builder=build_building_demolition_workplan_excel,
        required_fields=(
            # 산안규칙 제38조 제1항 제9호 법정 필수
            "demolition_method",    # 해체 공법
            "demolition_sequence",  # 해체 순서·절차
            "emergency_measure",    # 비상조치 방법 [제38조]
        ),
        optional_fields=(
            "site_name", "project_name", "work_location", "work_date",
            "contractor", "supervisor", "prepared_by",
            "building_info",
            "temporary_structure", "preliminary_survey",
            "hazmat_removal", "underground_facilities",
            "adjacent_protection", "work_zone",
            "emergency_contacts",   # list[dict]: role, name, phone
            "safety_steps",         # list[dict]: task_step, hazard, safety_measure, responsible
            "sign_date",
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("emergency_contacts",),
    ),
    # ------------------------------------------------------------------
    # EQ-005 고소작업대 사용계획서
    # 법적 근거: 산안규칙 제86조 이하
    # ------------------------------------------------------------------
    "aerial_work_platform_use_plan": FormSpec(
        form_type="aerial_work_platform_use_plan",
        display_name="고소작업대 사용계획서",
        version="1.0",
        builder=build_aerial_work_platform_use_plan_excel,
        required_fields=(
            # 산안규칙 제86조 이하 법정 필수
            "equipment_type",     # 장비 종류
            "emergency_measure",  # 비상조치 방법
        ),
        optional_fields=(
            "site_name", "project_name", "work_location", "work_date",
            "contractor", "supervisor", "prepared_by",
            "work_summary",
            "equipment_model", "max_height", "max_load",
            "operator_qualification", "work_radius",
            "ground_condition", "outrigger_plan",
            "emergency_contacts",   # list[dict]: role, name, phone
            "safety_steps",         # list[dict]: task_step, hazard, safety_measure, responsible
            "sign_date",
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("emergency_contacts",),
    ),
    "earthwork_equipment_use_plan": FormSpec(
        form_type="earthwork_equipment_use_plan",
        display_name="덤프·롤러·불도저 사용계획서",
        version="1.0",
        builder=build_earthwork_equipment_use_plan_excel,
        required_fields=(
            "equipment_type",     # 장비 종류
            "emergency_measure",  # 비상조치 방법
        ),
        optional_fields=(
            "site_name", "project_name", "work_location", "work_date",
            "contractor", "supervisor", "prepared_by", "approver",
            "work_summary", "work_detail",
            "equipment_model", "equipment_capacity", "operator_qualification",
            "work_zone", "ground_condition", "max_speed", "guide_worker",
            "safety_steps",       # list[dict]: task_step, hazard, safety_measure, responsible
            "emergency_contacts", # list[dict]: role, name, phone
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("emergency_contacts",),
    ),
    "bridge_work_workplan": FormSpec(
        form_type="bridge_work_workplan",
        display_name="교량 설치·해체·변경 작업계획서",
        version="1.0",
        builder=build_bridge_work_workplan_excel,
        required_fields=(
            "work_type",          # 작업 구분 (설치·해체·변경)
            "emergency_measure",  # 비상조치 방법
        ),
        optional_fields=(
            "site_name", "project_name", "work_location", "work_date",
            "contractor", "supervisor", "prepared_by", "approver",
            "work_summary", "work_detail",
            "bridge_name", "bridge_type", "span_length", "max_height",
            "equipment", "ground_condition", "support_method",
            "safety_steps",       # list[dict]: task_step, hazard, safety_measure, responsible
            "emergency_contacts", # list[dict]: role, name, phone
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("emergency_contacts",),
    ),
    "lifting_equipment_workplan": FormSpec(
        form_type="lifting_equipment_workplan",
        display_name="양중기·호이스트·윈치 작업계획서",
        version="1.0",
        builder=build_lifting_equipment_workplan_excel,
        required_fields=(
            "equipment_type",     # 장비 종류
            "emergency_measure",  # 비상조치 방법
        ),
        optional_fields=(
            "site_name", "project_name", "work_location", "work_date",
            "contractor", "supervisor", "prepared_by", "approver",
            "work_summary",
            "equipment_model", "rated_load", "max_lift_height",
            "work_radius", "operator_qualification", "inspection_expiry",
            "ground_condition", "load_description", "auxiliary_equipment",
            "safety_steps",         # list[dict]: task_step, hazard, safety_measure, responsible
            "emergency_contacts",   # list[dict]: role, name, phone
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("emergency_contacts",),
    ),
    # ------------------------------------------------------------------
    # P3 — WP-012 (2026-04-29)
    # 법적 근거: 산안규칙 제38조 제1항 제12호(궤도 보수·점검 작업계획서),
    #           제38조 제2항(근로자 주지), 제38조 제4항(궤도작업차량 열차운행관계자 협의),
    #           별표4(사전조사 및 작업계획서 내용)
    # evidence_status: NEEDS_VERIFICATION — 제12호/제11호 조항 번호 교차검증 필요
    #   (catalog 기존 기재: 제11호 / 작업 명세서: 제12호)
    # 역할: 궤도·철도 현장 한정 법정 작업계획서
    # ------------------------------------------------------------------
    "track_maintenance_workplan": FormSpec(
        form_type="track_maintenance_workplan",
        display_name="궤도 작업계획서",
        version="1.0",
        builder=build_track_maintenance_workplan,
        required_fields=(
            "site_name",   # 사업장명
            "work_date",   # 작업 예정일
            "supervisor",  # 작업지휘자
        ),
        optional_fields=(
            "project_name", "contractor", "subcontractor",
            "prepared_by", "approved_by", "prepare_date",
            "track_line", "track_section_start", "track_section_end",
            "track_type", "work_type", "work_scope",
            "work_start_time", "work_end_time", "track_possession",
            "track_condition", "hazard_structures", "train_schedule",
            "weather_condition", "underground_facilities",
            "survey_conducted_by", "survey_date",
            "worker_count", "supervisor_name", "supervisor_cert",
            "safety_manager", "watchman_name", "worker_list",
            "rail_vehicle_used", "rail_vehicle_type", "rail_vehicle_operator",
            "rail_operator_name", "consultation_date", "consultation_person",
            "consultation_content", "work_window_granted",
            "train_halt_required", "train_halt_time",
            "signal_method", "communication_device",
            "watchman_position", "alarm_method", "evacuation_signal",
            "ppe_required", "access_prohibition",
            "work_sequence", "entry_control_method",
            "barrier_type", "restricted_zone",
            "emergency_contact_119", "emergency_contact_rail",
            "emergency_contact_site", "evacuation_route", "first_aid_location",
            "worker_briefing_done", "briefing_date",
            "briefing_method", "worker_signatures",
        ),
        repeat_field="hazard_items",
        max_repeat_rows=8,
        extra_list_fields=("equipment_items",),
    ),
    "contractor_safety_consultation": FormSpec(
        form_type="contractor_safety_consultation",
        display_name="도급·용역 안전보건 협의서",
        version="1.0",
        builder=build_contractor_safety_consultation_excel,
        required_fields=(
            "principal_contractor",  # 도급인
            "subcontractor",         # 수급인
        ),
        optional_fields=(
            "site_name", "project_name", "work_period", "meeting_date",
            "meeting_location", "work_type",
            "principal_rep", "subcontractor_rep",
            "participants",      # list[dict]: role, name, position
            "agenda_items",      # list[dict]: topic, content, decision, remarks
            "safety_measures",   # list[dict]: hazard_work, safety_action, deadline, responsible
        ),
        repeat_field="agenda_items",
        max_repeat_rows=10,
        extra_list_fields=("participants", "safety_measures"),
    ),
    "safety_committee_minutes": FormSpec(
        form_type="safety_committee_minutes",
        display_name="안전보건협의체 회의록",
        version="1.0",
        builder=build_safety_committee_minutes_excel,
        required_fields=(
            "workplace_name",   # 사업장명
            "meeting_date",     # 회의 일시
        ),
        optional_fields=(
            "meeting_location", "meeting_number", "chairperson", "secretary",
            "special_notes", "next_meeting_date",
            "attendees",      # list[dict]: organization, name, position, role
            "agenda_items",   # list[dict]: agenda, discussion, decision, deadline, responsible
        ),
        repeat_field="agenda_items",
        max_repeat_rows=10,
        extra_list_fields=("attendees",),
    ),
    "industrial_accident_report": FormSpec(
        form_type="industrial_accident_report",
        display_name="산업재해조사표",
        version="1.0",
        builder=build_industrial_accident_report_excel,
        required_fields=(
            "workplace_name",      # 사업장명
            "accident_datetime",   # 재해 발생일시
        ),
        optional_fields=(
            "business_reg_no", "workplace_address", "industry_type",
            "worker_count", "representative",
            "industrial_accident_no", "contractor_type",
            "prime_contractor_name", "client_type",
            "construction_site", "construction_type",
            "construction_progress", "construction_amount",
            "victim_name", "victim_gender", "victim_birth", "victim_nationality",
            "employment_type", "work_type", "occupation", "entry_date", "tenure",
            "is_fatal", "injury_part", "injury_type", "disease_name", "sick_leave_days",
            "accident_location", "accident_type", "causative_object",
            "work_content", "accident_description", "witness",
            "direct_cause", "indirect_cause", "immediate_action",
            "cause_items",   # list[dict]: cause_category, cause_detail, prevention, deadline, responsible
            "checker", "check_date",
            "report_date", "submit_to", "submit_method", "safety_manager",
            "worker_rep_confirmed", "worker_rep_opinion",
        ),
        repeat_field="cause_items",
        max_repeat_rows=6,
        extra_list_fields=(),
    ),
    "emergency_contact_evacuation_plan": FormSpec(
        form_type="emergency_contact_evacuation_plan",
        display_name="비상 연락망 및 대피 계획서",
        version="1.0",
        builder=build_emergency_contact_evacuation_plan_excel,
        required_fields=(
            "site_name",        # 현장명
            "safety_manager",   # 안전관리자
        ),
        optional_fields=(
            "project_name", "site_address", "prepared_date", "site_director",
            "labor_office_phone",
            "emergency_contacts",   # list[dict]: role, name, organization, phone, remarks
            "external_contacts",    # list[dict]: agency, phone, remarks
            "evacuation_routes",    # list[dict]: zone, route_description, exit_location, assembly_point, responsible
            "assembly_points",      # list[dict]: point_name, location, capacity, responsible
        ),
        repeat_field="emergency_contacts",
        max_repeat_rows=12,
        extra_list_fields=("external_contacts", "evacuation_routes", "assembly_points"),
    ),
    "accident_root_cause_prevention_report": FormSpec(
        form_type="accident_root_cause_prevention_report",
        display_name="재해 원인 분석 및 재발 방지 보고서",
        version="1.0",
        builder=build_accident_root_cause_prevention_report_excel,
        required_fields=(
            "accident_datetime",   # 재해 발생일시
            "direct_cause",        # 직접 원인
        ),
        optional_fields=(
            "project_name", "site_name", "prepared_date", "accident_no",
            "em001_submitted", "em004_reported",
            "author", "reviewer", "approver",
            "accident_location", "work_type", "work_content", "accident_type",
            "victim_count", "is_fatal", "sick_leave_days",
            "property_damage", "agency_notified",
            "pre_accident_situation", "accident_sequence", "immediate_action",
            "work_stopped", "scene_preserved", "witness_summary", "evidence_media",
            "indirect_cause", "human_factor", "equipment_factor", "method_factor",
            "supervision_factor", "training_factor", "environment_factor",
            "contractor_factor", "ra_reflected", "workplan_reflected",
            "five_why_items",      # list[dict]: answer, evidence
            "root_cause", "root_cause_basis",
            "prevention_items",    # list[dict]: category, description, responsible, deadline, remarks
            "action_items",        # list[dict]: improvement, responsible, deadline, completed_date, status, checker
            "safety_manager", "supervisor", "site_director",
            "subcon_manager", "worker_rep_opinion", "final_approved_date",
        ),
        repeat_field="prevention_items",
        max_repeat_rows=10,
        extra_list_fields=("five_why_items", "action_items"),
    ),
    # ------------------------------------------------------------------
    # P3 — CM-007 (2026-04-29)
    # 법적 근거: 산업안전보건법 제57조(산업재해 기록·보존), 시행규칙 제73조
    # evidence_status: PRACTICAL — 법정 별지 서식 없음
    # 역할: 현장 재해 발생 현황 집계·관리 대장.
    #       EM-001(법정 조사표 제출), EM-005(원인 분석 심화)와 역할 분리.
    # ------------------------------------------------------------------
    "industrial_accident_status_ledger": FormSpec(
        form_type="industrial_accident_status_ledger",
        display_name="산업재해 발생 현황 관리 대장",
        version="1.0",
        builder=build_industrial_accident_status_ledger,
        required_fields=(
            "site_name",  # 사업장명
            "manager",    # 관리책임자
        ),
        optional_fields=(
            "project_name", "company_name", "period",
            "safety_manager", "prepared_date", "approver",
            "total_accidents", "total_workers", "total_fatality",
            "total_sick_leave", "total_no_leave", "summary_remarks",
            "supervisor_name", "confirm_date",
        ),
        repeat_field="accident_records",
        max_repeat_rows=20,
    ),
    "ppe_issuance_ledger": FormSpec(
        form_type="ppe_issuance_ledger",
        display_name="보호구 지급 대장",
        version="1.0",
        builder=build_ppe_issuance_ledger_excel,
        required_fields=(
            "site_name",   # 현장명
            "manager",     # 관리책임자
        ),
        optional_fields=(
            "project_name", "company_name", "period", "prepared_date", "approver",
            "issue_records",  # list[dict]: worker_name, occupation, ppe_type, issue_date, receipt_confirm, return_date
            "stock_items",    # list[dict]: ppe_type, spec, stock_qty, issued_qty, remain_qty, remarks
        ),
        repeat_field="issue_records",
        max_repeat_rows=20,
        extra_list_fields=("stock_items",),
    ),
    "ppe_issue_register": FormSpec(
        form_type="ppe_issue_register",
        display_name="보호구 지급 대장 (v2)",
        version="2.0",
        builder=build_ppe_issue_register,
        required_fields=(
            "site_name",   # 현장명
            "manager",     # 관리책임자
        ),
        optional_fields=(
            "project_name", "company_name", "period", "prepared_date", "approver",
            "worker_name", "worker_id", "occupation", "subcontractor", "work_location",
            "ppe_standard_checked", "qty_sufficient", "individual_ppe_needed", "ppe_condition_ok",
            "edu_conducted", "edu_date", "edu_instructor", "edu_attendees",
            "inspection_date", "inspector", "inspection_result",
            "supervisor_name", "safety_manager_name", "site_manager_name", "confirm_date",
            "issue_records",        # list[dict]: worker_name, ppe_type, spec, issue_date, qty, receipt_confirm
            "ppe_type_records",     # list[dict]: ppe_type, standard, qty_required, qty_issued, qty_remain, remarks
            "signature_records",    # list[dict]: worker_name, date, signature_confirm
            "replace_records",      # list[dict]: worker_name, ppe_type, action, date, reason, handler
            "nonissue_records",     # list[dict]: worker_name, ppe_type, reason, action, action_date
            "nonwear_records",      # list[dict]: worker_name, ppe_type, date, action
            "stock_records",        # list[dict]: ppe_type, spec, stock_qty, issued_qty, remain_qty, status
        ),
        repeat_field="issue_records",
        max_repeat_rows=20,
        extra_list_fields=(
            "ppe_type_records", "signature_records", "replace_records",
            "nonissue_records", "nonwear_records", "stock_records",
        ),
    ),
    "chemical_equipment_workplan": FormSpec(
        form_type="chemical_equipment_workplan",
        display_name="화학설비·부속설비 작업계획서",
        version="1.0",
        builder=build_chemical_equipment_workplan_excel,
        required_fields=(
            "equipment_name",    # 설비명
            "emergency_measure", # 비상조치 방법
        ),
        optional_fields=(
            "site_name", "project_name", "contractor", "work_date",
            "work_location", "supervisor", "prepared_by", "approver",
            "equipment_type", "chemical_name", "chemical_state",
            "is_hazardous", "max_pressure", "max_temperature", "capacity",
            "work_summary",
            "safety_steps",       # list[dict]: task_step, hazard, safety_measure, responsible
            "chemical_hazards",   # list[dict]: hazard_type, description, response, ppe_required
            "emergency_contacts", # list[dict]: role, name, phone
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("chemical_hazards", "emergency_contacts"),
    ),
    "asbestos_removal_workplan": FormSpec(
        form_type="asbestos_removal_workplan",
        display_name="석면 해체·제거 작업 계획서",
        version="1.0",
        builder=build_asbestos_removal_workplan_excel,
        required_fields=(
            "site_name",       # 현장명
            "removal_method",  # 해체 방법
        ),
        optional_fields=(
            "building_name", "contractor", "work_period", "work_location",
            "supervisor", "survey_agency", "survey_date",
            "asbestos_type", "material_name", "content_ratio", "estimated_qty",
            "material_location",
            "safety_steps",    # list[dict]: task_step, hazard, safety_measure, responsible
            "workers",         # list[dict]: name, occupation, health_exam, ppe, remarks
            "waste_contractor", "disposal_method", "storage_location", "emergency_measure",
            "prepared_by", "approver",
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("workers",),
    ),
    "contractor_safety_document_checklist": FormSpec(
        form_type="contractor_safety_document_checklist",
        display_name="협력업체 안전보건 관련 서류 확인서",
        version="1.0",
        builder=build_contractor_safety_document_checklist_excel,
        required_fields=(
            "principal_contractor", # 원청업체명
            "subcontractor",        # 협력업체명
        ),
        optional_fields=(
            "site_name", "project_name", "check_date", "checker", "approver",
            "doc_items",      # list[dict]: doc_name, submitted, submit_date, expiry_date, remarks
            "required_docs",  # list[dict]: doc_name, legal_basis, remarks
        ),
        repeat_field="doc_items",
        max_repeat_rows=20,
        extra_list_fields=("required_docs",),
    ),
    "annual_safety_education_plan": FormSpec(
        form_type="annual_safety_education_plan",
        display_name="연간 안전보건교육 계획서",
        version="1.0",
        builder=build_annual_safety_education_plan_excel,
        required_fields=(
            "workplace_name", # 사업장명
            "plan_year",      # 계획 연도
        ),
        optional_fields=(
            "company_name", "safety_manager", "total_workers", "prepared_date",
            "prepared_by", "approver",
            "education_plan",  # list[dict]: course_name, target, month, hours, method, instructor
            "education_types", # list[dict]: edu_type, target, legal_hours, planned_hours, remarks
        ),
        repeat_field="education_plan",
        max_repeat_rows=24,
        extra_list_fields=("education_types",),
    ),
    "near_miss_report": FormSpec(
        form_type="near_miss_report",
        display_name="아차사고 보고서",
        version="2.0",
        builder=build_near_miss_report_excel,
        required_fields=(
            "site_name",          # 현장명
            "incident_datetime",  # 발생 일시
        ),
        optional_fields=(
            "project_name", "written_date", "near_miss_no",
            "discoverer", "author", "reviewer", "approver",
            "incident_location", "work_type", "work_content",
            "related_equipment", "related_company",
            "near_miss_type", "actual_accident",
            "no_human_damage", "no_property_damage", "work_stopped",
            "situation_description", "potential_sequence",
            "expected_accident_type", "expected_severity",
            "direct_hazard", "indirect_hazard", "work_conditions",
            "evidence_media", "witness",
            "haz_fall", "haz_falling_obj", "haz_entanglement", "haz_electric",
            "haz_collapse", "haz_overturn", "haz_fire", "haz_explosion",
            "haz_asphyxia", "haz_chemical", "haz_collision", "haz_heavy_obj", "haz_other",
            "imm_work_stop", "imm_zone_control", "imm_equip_stop",
            "imm_power_cut", "imm_gas_cut", "imm_temp_guard",
            "imm_evacuation", "imm_reported", "imm_sub_notified", "imm_other",
            "ca_unsafe_condition", "ca_unsafe_act", "ca_procedure_violation",
            "ca_lack_of_training", "ca_poor_supervision", "ca_equipment_defect",
            "ca_no_ppe", "ca_work_environment", "ca_contractor_mgmt", "ca_ra_missed",
            "prev_immediate", "prev_short_term", "prev_long_term",
            "prev_procedure_update", "prev_ra_review", "prev_tbm",
            "prev_sub_edu", "prev_ppe_update", "prev_guard_update", "prev_lateral_spread",
            "action_items",  # list[dict]: improvement, responsible, due_date, completed_date, status, evidence, checker, incomplete_reason
            "sig_author", "sig_safety_mgr", "sig_supervisor",
            "sig_site_director", "sig_sub_manager",
            "worker_rep_opinion", "sig_confirmed_date",
        ),
        repeat_field="action_items",
        max_repeat_rows=8,
        extra_list_fields=(),
    ),
    "lift_gondola_use_plan": FormSpec(
        form_type="lift_gondola_use_plan",
        display_name="리프트·곤돌라 사용계획서",
        version="1.0",
        builder=build_lift_gondola_use_plan_excel,
        required_fields=(
            "site_name",       # 현장명
            "equipment_type",  # 장비 종류
        ),
        optional_fields=(
            "project_name", "contractor", "work_date", "work_location",
            "supervisor", "equipment_model", "max_load", "max_height",
            "install_location", "use_period", "operator_license", "operator_name",
            "work_summary", "prepared_by", "approver",
            "safety_steps",      # list[dict]: task_step, hazard, safety_measure, responsible
            "inspection_items",  # list[dict]: check_item, ok, ng, action
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("inspection_items",),
    ),
    "temp_power_generator_use_plan": FormSpec(
        form_type="temp_power_generator_use_plan",
        display_name="임시전기·발전기 사용계획서",
        version="1.0",
        builder=build_temp_power_generator_use_plan_excel,
        required_fields=(
            "site_name",       # 현장명
            "equipment_type",  # 설비 종류
        ),
        optional_fields=(
            "project_name", "contractor", "work_date", "install_location",
            "supervisor", "equipment_model", "capacity", "voltage",
            "use_period", "operator_name", "electrical_license",
            "grounding_method", "use_purpose", "prepared_by", "approver",
            "safety_steps",      # list[dict]: task_step, hazard, safety_measure, responsible
            "inspection_items",  # list[dict]: check_item, ok, ng, action
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("inspection_items",),
    ),
    "ladder_stepladder_workboard_use_plan": FormSpec(
        form_type="ladder_stepladder_workboard_use_plan",
        display_name="사다리·말비계·작업발판 사용계획서",
        version="1.0",
        builder=build_ladder_stepladder_workboard_use_plan_excel,
        required_fields=(
            "site_name",       # 현장명
            "equipment_type",  # 장비 종류
        ),
        optional_fields=(
            "project_name", "contractor", "work_date", "install_location",
            "supervisor", "equipment_count", "equipment_spec", "max_height",
            "use_period", "use_purpose", "prepared_by", "approver",
            "safety_steps",      # list[dict]: task_step, hazard, safety_measure, responsible
            "inspection_items",  # list[dict]: check_item, ok, ng, action
        ),
        repeat_field="safety_steps",
        max_repeat_rows=10,
        extra_list_fields=("inspection_items",),
    ),
    "construction_equipment_entry_request": FormSpec(
        form_type="construction_equipment_entry_request",
        display_name="건설 장비 반입 신청서",
        version="1.0",
        builder=build_construction_equipment_entry_request_excel,
        required_fields=(
            "site_name",        # 현장명
            "company_name",     # 신청 업체
            "request_date",     # 신청일자
        ),
        optional_fields=(
            "project_name", "entry_date", "work_location",
            "supervisor", "contact", "applicant", "approver",
            "equipment_items",   # list[dict]: equipment_type, vehicle_number, manufacturer, manufacture_year, insurance_expiry, remarks
            "inspection_items",  # list[dict]: check_item, result, remarks
        ),
        repeat_field="equipment_items",
        max_repeat_rows=10,
        extra_list_fields=("inspection_items",),
    ),
    # ------------------------------------------------------------------
    # P2 — PPE-002 v2 (2026-04-28)
    # 법정 근거: 없음 — 원청 안전 관리 규정 기반 실무 보조서식
    # 역할: 장비 반입 신청·서류 확인·반입 승인 (PPE-003 검사증, CL-003 일일점검과 분리)
    # ------------------------------------------------------------------
    "equipment_entry_application": FormSpec(
        form_type="equipment_entry_application",
        display_name="건설 장비 반입 신청서 (v2)",
        version="2.0",
        builder=build_equipment_entry_application,
        required_fields=(
            "site_name",       # 현장명
            "equipment_name",  # 장비명
            "apply_date",      # 신청일
        ),
        optional_fields=(
            "project_name", "contractor", "subcontractor",
            "applicant", "applicant_position", "manager", "prepared_date",
            "equipment_type", "equipment_model", "equipment_reg_no",
            "manufacturer", "manufacture_year", "equipment_capacity",
            "equipment_weight", "owner_name",
            "work_purpose", "work_content", "work_location",
            "planned_entry_date", "planned_exit_date", "work_duration",
            "workplan_required", "workplan_no",
            "insurance_valid", "insurance_expiry",
            "inspection_valid", "inspection_expiry",
            "operator_license_ok", "operator_license_type",
            "safety_inspection_ok", "safety_cert_no",
            "operator_name", "operator_license_no", "operator_experience",
            "signal_worker_name", "signal_worker_assigned",
            "banksman_name", "worker_safety_edu",
            "access_route_ok", "ground_bearing_ok", "overhead_hazard_ok",
            "underground_hazard_ok", "neighboring_safety_ok",
            "exclusion_zone_ok", "signal_system_ok", "ppe_check_ok",
            "entry_time_from", "entry_time_to", "entry_route",
            "parking_location", "night_work_allowed", "weather_condition",
            "load_limit", "speed_limit",
            "approval_status", "approval_conditions", "supplementary_items",
            "supplement_deadline", "rejection_reason",
            "cl003_linked", "eq_plan_linked", "ppp003_linked",
            "daily_inspection_due", "related_form_nos", "follow_up_action",
            "applicant_sign", "safety_manager_name", "supervisor_name",
            "site_manager_name", "confirm_date",
        ),
        repeat_field=None,
        max_repeat_rows=None,
    ),
    # ------------------------------------------------------------------
    # P3 — PPE-003 (2026-04-29)
    # 법적 근거: 건설기계관리법 제13조, 자동차손해배상보장법, 산업안전보건법 제80조·제93조
    # evidence_status: PRACTICAL — 법정 별지 서식 없음
    # 역할: 장비 보험·정기검사증·등록증·자격증 등 증빙서류 상세 확인 (PPE-002 반입 신청과 분리)
    # ------------------------------------------------------------------
    "equipment_insurance_inspection_check": FormSpec(
        form_type="equipment_insurance_inspection_check",
        display_name="건설 장비 보험·정기검사증 확인서",
        version="1.0",
        builder=build_equipment_insurance_inspection_check,
        required_fields=(
            "site_name",       # 현장명
            "check_date",      # 확인일
            "equipment_name",  # 장비명
        ),
        optional_fields=(
            "project_name", "entry_request_no", "check_period",
            "checker", "writer", "reviewer", "approver",
            "equipment_type", "manufacturer", "equipment_model",
            "serial_no", "reg_no", "equipment_capacity",
            "owner_name", "rental_company", "planned_work",
            "reg_cert_submitted", "reg_cert_no", "owner_match",
            "equip_name_match", "serial_match", "reg_cert_valid", "reg_cert_supplement",
            "insurance_type", "insurance_company", "policy_no", "policy_holder",
            "insured_equipment", "insurance_start", "insurance_end",
            "liability_covered", "coverage_includes_period",
            "insurance_expiry_near", "insurance_supplement",
            "periodic_insp_required", "insp_agency", "insp_date", "insp_expiry",
            "insp_result", "insp_nonconformance", "reinspection_needed",
            "insp_expiry_near", "insp_supplement",
            "safety_insp_required", "safety_cert_submitted", "safety_insp_agency",
            "safety_insp_date", "safety_insp_expiry", "safety_insp_passed",
            "safety_insp_conditions", "safety_insp_supplement",
            "operator_name", "operator_affiliation", "license_type", "license_no",
            "license_valid", "operable_scope", "safety_edu_done",
            "safety_edu_date", "operator_supplement",
            "original_verified", "copy_stored", "electronic_stored",
            "expiry_ledger_updated", "expiry_alert_needed",
            "pii_masked", "storage_location",
            "entry_allowed", "use_allowed", "conditional_approval",
            "approval_conditions", "missing_documents", "action_person",
            "completion_due", "recheck_date", "final_confirmer",
            "ppe002_linked", "cl003_linked", "eq_plan_linked", "dl001_linked",
            "applicant_company", "safety_manager_name", "supervisor_name",
            "site_manager_name", "confirm_date",
        ),
        repeat_field=None,
        max_repeat_rows=None,
    ),
    # ------------------------------------------------------------------
    # P3 — PPE-004 (2026-04-29)
    # 법적 근거: 산업안전보건법 제112조(MSDS 게시 및 교육), 제114조(경고표지),
    #           제115조(MSDS 교육 의무)
    # evidence_status: PRACTICAL — 법정 별지 서식 없음
    # 역할: MSDS 비치 위치·경고표지·취급 근로자 교육 실시 여부 확인 (CL-009 유해화학물질 취급 점검과 분리)
    # ------------------------------------------------------------------
    "msds_posting_education_check": FormSpec(
        form_type="msds_posting_education_check",
        display_name="MSDS 비치 및 교육 확인서",
        version="1.0",
        builder=build_msds_posting_education_check,
        required_fields=(
            "site_name",   # 현장명
            "check_date",  # 확인일자
            "checker",     # 확인자
        ),
        optional_fields=(
            "project_name", "department", "position",
            "work_location", "work_type",
            "chemical_name", "cas_no", "manufacturer",
            "purpose", "daily_amount", "unit",
            "msds_available", "msds_location", "msds_accessible",
            "msds_language", "msds_version_current", "msds_remarks",
            "label_attached", "label_location", "label_legible",
            "label_ghs_compliant", "label_remarks",
            "edu_conducted", "edu_date", "edu_method", "edu_duration",
            "edu_instructor", "edu_content",
            "edu_participants", "edu_actual", "edu_record_kept", "edu_remarks",
            "ppe_specified", "ppe_provided", "ppe_types",
            "first_aid_known", "first_aid_kit_available",
            "storage_proper", "storage_labeled", "incompatible_separated",
            "ventilation_adequate", "open_flame_controlled",
            "spill_kit_available", "fire_extinguisher_available",
            "emergency_contact_posted", "emergency_procedure_known",
            "overall_result", "overall_remarks",
            "preparer_name", "supervisor_name",
            "safety_manager_name", "site_manager_name", "confirm_date",
        ),
        repeat_field="deficiency_items",
        max_repeat_rows=8,
    ),
    "temp_electrical_installation_permit": FormSpec(
        form_type="temp_electrical_installation_permit",
        display_name="임시전기 설치·연결 허가서",
        version="1.0",
        builder=build_temp_electrical_installation_permit_excel,
        required_fields=(
            "site_name",        # 현장명
            "work_date",        # 작업일자
            "work_location",    # 작업 위치
            "work_supervisor",  # 작업책임자
        ),
        optional_fields=(
            "project_name", "company_name", "permit_no", "validity_period",
            "work_name", "voltage", "power_source", "distribution_panel",
            "work_description", "permit_issuer",
            "check_items",   # list[dict]: check_item, result, remarks
            "workers",       # list[dict]: name, job_type, remarks
        ),
        repeat_field="workers",
        max_repeat_rows=10,
        extra_list_fields=("check_items",),
    ),
    "safety_cost_use_plan": FormSpec(
        form_type="safety_cost_use_plan",
        display_name="산업안전보건관리비 사용계획서",
        version="1.0",
        builder=build_safety_cost_use_plan_excel,
        required_fields=(
            "site_name",             # 현장(공사)명
            "company_name",          # 원수급인
            "safety_cost_amount",    # 안전보건관리비 계상액
        ),
        optional_fields=(
            "project_name", "contractor", "plan_year",
            "work_start_date", "work_end_date",
            "total_contract_amount", "safety_cost_rate",
            "supervisor", "approver", "sign_date",
            "cost_items",   # list[dict]: category, planned_amount, remarks
        ),
        repeat_field="cost_items",
        max_repeat_rows=15,
        extra_list_fields=(),
    ),
    "health_exam_result": FormSpec(
        form_type="health_exam_result",
        display_name="근로자 건강진단 결과 확인서",
        version="1.0",
        builder=build_health_exam_result_excel,
        required_fields=(
            "site_name",     # 현장(사업장)명
            "company_name",  # 업체명
            "exam_type",     # 건강진단 종류
        ),
        optional_fields=(
            "exam_year", "exam_period", "exam_agency", "exam_agency_contact",
            "total_workers", "supervisor", "approver", "sign_date",
            "worker_rows",  # list[dict]: name, job_type, exam_type, result, followup, remarks
        ),
        repeat_field="worker_rows",
        max_repeat_rows=20,
        extra_list_fields=(),
    ),
    "new_worker_safety_pledge": FormSpec(
        form_type="new_worker_safety_pledge",
        display_name="신규 근로자 안전보건 서약서",
        version="1.0",
        builder=build_new_worker_safety_pledge_excel,
        required_fields=(
            "site_name",    # 현장명
            "company_name", # 업체명
            "worker_name",  # 근로자 성명
        ),
        optional_fields=(
            "department", "job_title", "sign_date", "supervisor",
            "pledge_items",       # list[str]: 서약 항목 (기본값 내장)
            "extra_pledge_items", # list[str]: 추가 서약 항목
        ),
        repeat_field=None,
        max_repeat_rows=0,
        extra_list_fields=("pledge_items", "extra_pledge_items"),
    ),
    "foreign_worker_safety_edu": FormSpec(
        form_type="foreign_worker_safety_edu",
        display_name="외국인 근로자 안전보건 교육 확인서",
        version="1.0",
        builder=build_foreign_worker_safety_edu_excel,
        required_fields=(
            "site_name",    # 현장명
            "company_name", # 업체명
            "edu_date",     # 교육일자
        ),
        optional_fields=(
            "edu_duration", "edu_course", "edu_location",
            "edu_language", "instructor", "supervisor",
            "edu_items",    # list[str|dict]: 교육 항목
            "worker_rows",  # list[dict]: name, nation, team, job, remarks
        ),
        repeat_field="worker_rows",
        max_repeat_rows=20,
        extra_list_fields=("edu_items",),
    ),
    "serious_accident_immediate_report": FormSpec(
        form_type="serious_accident_immediate_report",
        display_name="중대재해 발생 즉시 보고서",
        version="1.0",
        builder=build_serious_accident_immediate_report_excel,
        required_fields=(
            "site_name",          # 현장명
            "company_name",       # 업체명
            "accident_datetime",  # 발생 일시
            "accident_location",  # 발생 장소
        ),
        optional_fields=(
            "project_name", "owner_name", "site_manager", "contact",
            "accident_type", "work_type", "accident_summary",
            "death_count", "injury_count",
            "casualty_rows",              # list[dict]: role, injury_type, status, remarks
            "work_stopped", "access_controlled",
            "agency_reports",             # list[dict]: agency, datetime, method, receiver, remarks
            "additional_risks", "temporary_countermeasures",
            "report_datetime", "reporter",
        ),
        repeat_field="casualty_rows",
        max_repeat_rows=10,
        extra_list_fields=("agency_reports",),
    ),
    "safety_manager_appointment_report": FormSpec(
        form_type="safety_manager_appointment_report",
        display_name="안전관리자ㆍ보건관리자ㆍ산업보건의 선임 등 보고서(건설업)",
        version="1.0",
        builder=build_safety_manager_appointment_report_excel,
        required_fields=(
            "company_name",  # 사업장명
            "site_name",     # 현장명
        ),
        optional_fields=(
            "biz_reg_no", "ceo_name", "company_address",
            "biz_start_no", "general_contractor", "construction_period",
            "contract_amount", "worker_count",
            "hazard_plan_yn", "hazard_plan_targets",  # list[str]
            "client_name", "client_type", "client_address", "client_contact",
            "safety_managers",            # list[dict]: name, birth_date, license_no, appointed_date, duty_type, contact
            "health_managers",            # list[dict]: 동일 구조
            "occupational_physicians",    # list[dict]: 동일 구조
            "report_date", "reporter",
        ),
        repeat_field=None,
        max_repeat_rows=0,
        extra_list_fields=("safety_managers", "health_managers",
                           "occupational_physicians", "hazard_plan_targets"),
    ),
    "emergency_first_aid_record": FormSpec(
        form_type="emergency_first_aid_record",
        display_name="응급조치 실시 기록서",
        version="1.0",
        builder=build_emergency_first_aid_record_excel,
        required_fields=(
            "site_name",        # 현장명
            "incident_datetime", # 발생일시
        ),
        optional_fields=(
            "project_name", "written_date", "accident_no",
            "em004_reported", "em001_prepared",
            "author", "reviewer", "approver",
            "incident_location", "work_type", "work_content",
            "emergency_type", "victim_count",
            "conscious", "breathing", "bleeding", "fracture_suspected",
            "burn", "asphyxia_suspected", "electric_shock", "other_symptoms",
            "victim_name", "victim_company", "victim_job",
            "victim_contact", "victim_birthdate", "guardian_contacted",
            "aid_start_time", "aid_end_time", "first_aider", "aider_qualified",
            "aid_hemostasis", "aid_cpr", "aid_aed", "aid_splint",
            "aid_burn_care", "aid_oxygen", "aid_asphyxia", "aid_power_cut",
            "aid_temperature", "aid_other",
            "eq_kit", "eq_bandage", "eq_tourniquet", "eq_splint",
            "eq_stretcher", "eq_aed", "eq_oxygen", "eq_air_supply",
            "eq_gas_meter", "eq_replenish", "eq_manager",
            "call_119_time", "ems_arrive_time", "hospital_time", "hospital_name",
            "transport_means", "escort", "guardian_time", "authority_notified",
            "handover_from", "handover_to",
            "ctrl_work_stop", "ctrl_zone", "ctrl_power", "ctrl_gas",
            "ctrl_equipment", "ctrl_evacuated", "ctrl_preserved", "ctrl_recorded",
            "fu_kit_replenish", "fu_training_needed", "fu_contact_update",
            "fu_evac_update", "fu_risk_review", "fu_em005_linked",
            "fu_responsible", "fu_due_date",
            "sig_first_aider", "sig_safety_mgr", "sig_supervisor",
            "sig_site_director", "sig_sub_manager", "sig_confirmed_date",
        ),
        repeat_field=None,
        max_repeat_rows=0,
        extra_list_fields=(),
    ),
    # ------------------------------------------------------------------
    # P3 — PTW-006 (2026-04-29)
    # 법적 근거: 산업안전보건기준에 관한 규칙 제574조(방사선관리구역 설정),
    #           제575조(관계자외 출입금지), 제578조(차폐), 제579조(개인선량계),
    #           원자력안전법 제53조(방사선작업종사자 선량한도),
    #           비파괴검사기술의 진흥 및 관리에 관한 법률 제2조(방사선 비파괴검사)
    # evidence_status: PRACTICAL — 법정 별지 서식 없음.
    #                  산안규칙 의무 항목 기반 실무 서식 (방사선 투과검사 RT 한정)
    # 역할: RT 작업 전 안전통제·허가 기록. 방사선관리구역·출입통제·차폐·개인선량계·비상조치 포함.
    # ------------------------------------------------------------------
    "radiography_work_permit": FormSpec(
        form_type="radiography_work_permit",
        display_name="방사선 투과검사 작업 허가서",
        version="1.0",
        builder=build_radiography_work_permit,
        required_fields=(
            "site_name",        # 현장명
            "permit_date",      # 허가일자
            "work_location",    # 작업장소
            "work_supervisor",  # 작업책임자
        ),
        optional_fields=(
            "project_name", "permit_no", "permit_time_start", "permit_time_end",
            "inspection_object", "inspection_method", "inspection_area",
            "radiation_source_type", "source_activity", "source_serial_no",
            "equipment_model", "source_inspector",
            "radiation_safety_officer", "rt_supervisor",
            "rt_operator", "rt_operator_cert_no",
            "control_zone_radius", "control_zone_method", "control_zone_confirmed",
            "shielding_material", "shielding_confirmed",
            "warning_sign_placed", "watchman_name", "watchman_post",
            "dosimeter_supervisor", "dosimeter_type", "ppe_confirmed",
            "evacuation_scope", "evacuation_route", "emergency_contact",
            "emergency_procedure", "stop_work_criteria",
            "post_work_source_check", "post_work_zone_release",
            "site_manager_sign",
        ),
        repeat_field="workers",
        max_repeat_rows=6,
        extra_list_fields=("pre_work_checks", "during_work_checks", "post_work_checks"),
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

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
from engine.output.tower_crane_workplan_builder import build_tower_crane_workplan_excel
from engine.output.vehicle_workplan_builder import build_vehicle_workplan_excel
from engine.output.work_environment_measurement_builder import build_work_environment_measurement_excel
from engine.output.safety_management_log_builder import build_safety_management_log
from engine.output.supervisor_safety_log_builder import build_supervisor_safety_log
from engine.output.safety_patrol_inspection_log_builder import build_safety_patrol_inspection_log
from engine.output.work_safety_checklist_builder import build_work_safety_checklist
from engine.output.heavy_lifting_workplan_builder import build_heavy_lifting_workplan_excel
from engine.output.workplan_builder import build_excavation_workplan_excel
from engine.output.fall_protection_checklist_builder import build_fall_protection_checklist_excel
from engine.output.electrical_workplan_builder import build_electrical_workplan_excel
from engine.output.electrical_work_permit_builder import build_electrical_work_permit_excel
from engine.output.electrical_facility_checklist_builder import build_electrical_facility_checklist_excel
from engine.output.fire_prevention_checklist_builder import build_fire_prevention_checklist_excel
from engine.output.protective_equipment_checklist_builder import build_protective_equipment_checklist
from engine.output.hazardous_chemical_checklist_builder import build_hazardous_chemical_checklist
from engine.output.hot_work_workplan_builder import build_hot_work_workplan_excel
from engine.output.piling_workplan_builder import build_piling_workplan_excel
from engine.output.piling_use_workplan_builder import build_piling_use_workplan_excel


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
        version="1.0",
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
            "department",
            "position",
            "work_location",
            "work_start_time",
            "work_end_time",
            "worker_count",
            "subcontractor_count",
            "visitor_count",
            "main_work",
            "high_risk_work",
            "safety_meeting_done",
            "tbm_done",
            "risk_assessment_checked",
            "equipment_check_done",
            "ppe_check_done",
            "site_patrol_done",
            "nonconformance_found",
            "corrective_action",
            "accident_or_near_miss",
            "weather_condition",
            "heat_cold_risk",
            "emergency_contact_checked",
            "remarks",
            "reviewer_name",
            "approver_name",
            "equipment_status",
            "housekeeping_status",
            "management_notes",
            "accident_detail",
            "corrective_action_completed",
            "follow_up_items",
            "nonconformance_items",
        ),
        repeat_field="nonconformance_items",
        max_repeat_rows=10,
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
        version="1.0",
        builder=build_supervisor_safety_log,
        required_fields=(
            "site_name",
            "log_date",
            "supervisor_name",
            "department",
            "work_summary",
        ),
        optional_fields=(
            "project_name",
            "position",
            "work_location",
            "work_start_time",
            "work_end_time",
            "worker_count",
            "subcontractor_count",
            "assigned_work",
            "high_risk_work",
            "worker_instruction_done",
            "safety_training_done",
            "tbm_participation",
            "risk_assessment_reviewed",
            "work_method_checked",
            "ppe_checked",
            "machine_guard_checked",
            "work_environment_checked",
            "housekeeping_checked",
            "emergency_contact_checked",
            "unsafe_behavior_found",
            "unsafe_condition_found",
            "corrective_instruction",
            "corrective_action_result",
            "accident_or_near_miss",
            "accident_detail",
            "health_condition_checked",
            "weather",
            "heat_cold_risk",
            "remarks",
            "reviewer_name",
            "approver_name",
            "instruction_items",
        ),
        repeat_field="instruction_items",
        max_repeat_rows=10,
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
        version="1.0",
        builder=build_safety_patrol_inspection_log,
        required_fields=(
            "site_name",
            "patrol_date",
            "patrol_time",
            "patrol_route",
            "patrol_officer",
            "writer_name",
        ),
        optional_fields=(
            "project_name",
            "department",
            "position",
            "weather",
            "total_workers",
            "hazard_summary",
            "corrective_summary",
            "carryover_items",
            "remarks",
            "reviewer_name",
            "approver_name",
            "patrol_items",
        ),
        repeat_field="patrol_items",
        max_repeat_rows=15,
    ),
    # ------------------------------------------------------------------
    # DL-005 — 작업 전 안전 확인서 (2026-04-26)
    # 법적 근거: 중대재해처벌법 시행령 제4조 (안전보건관리체계 구축 의무)
    # evidence_status: VERIFIED (DL-001과 공유)
    # 주의: 개인 자가 점검서. 현장 관리 일지(DL-001)와 다름.
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

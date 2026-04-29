"""
부대서류 전용 Registry.

핵심 안전서류(form_registry.py 90종)에서 파생 생성되는 부대서류를 관리한다.
document_catalog.yml에 추가하지 않으며, form_registry.py와 별개로 운영된다.

부대서류 정의:
    핵심서류 작성·제출 시 함께 생성되어야 하는 파생 출력물.
    법정 서류가 아닌 실무 보조 첨부물 중심.

SupplementalSpec 항목:
    supplemental_type  str   고유 식별자
    display_name       str   표시명
    category           str   분류 (education | ptw | equipment | ra_tbm | accident | common)
    parent_form_types  tuple 연동 가능한 핵심 form_type 목록
    trigger_condition  str   생성 조건 설명
    output_builder     callable | None  실제 builder 함수 (TODO는 None)
    required_fields    tuple 필수 입력 필드
    optional_fields    tuple 선택 입력 필드
    repeat_field       str | None  반복 행 필드명
    max_repeat_rows    int   반복 행 최대 수
    priority           str   P1 / P2 / P3

사용법:
    from engine.output.supplementary_registry import (
        list_supplemental_types,
        get_supplemental_spec,
        build_supplemental_excel,
        get_supplemental_types_for,
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# 실제 구현된 builder import
from engine.output.attendance_roster_builder import build_attendance_roster
from engine.output.photo_attachment_sheet_builder import build_photo_attachment_sheet
from engine.output.document_attachment_list_builder import build_document_attachment_list
from engine.output.confined_space_gas_measurement_builder import build_confined_space_gas_measurement
from engine.output.work_completion_confirmation_builder import build_work_completion_confirmation
from engine.output.improvement_completion_check_builder import build_improvement_completion_check
from engine.output.equipment_operator_qualification_check_builder import build_equipment_operator_qualification_check
from engine.output.watchman_assignment_confirmation_builder import build_watchman_assignment_confirmation

# ---------------------------------------------------------------------------
# SupplementalSpec
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SupplementalSpec:
    supplemental_type: str
    display_name: str
    category: str
    parent_form_types: Tuple[str, ...]
    trigger_condition: str
    output_builder: Optional[Callable[[Dict[str, Any]], bytes]]
    required_fields: Tuple[str, ...]
    optional_fields: Tuple[str, ...]
    repeat_field: Optional[str] = None
    max_repeat_rows: int = 30
    priority: str = "P2"


# ---------------------------------------------------------------------------
# 내부 TODO placeholder builder
# ---------------------------------------------------------------------------

def _todo_builder(form_data: Dict[str, Any]) -> bytes:
    """미구현 부대서류 builder — NotImplementedError 발생."""
    raise NotImplementedError("이 부대서류 builder는 아직 구현되지 않았습니다.")


# ---------------------------------------------------------------------------
# _SUPPLEMENTARY_REGISTRY
# ---------------------------------------------------------------------------

_SUPPLEMENTARY_REGISTRY: Dict[str, SupplementalSpec] = {

    # ── 1. attendance_roster ─────────────────────────────────────────────
    "attendance_roster": SupplementalSpec(
        supplemental_type="attendance_roster",
        display_name="참석자 명부",
        category="common",
        parent_form_types=(
            "education_log", "special_education_log",
            "risk_assessment_meeting_minutes", "tbm_log",
            "safety_committee_minutes",
            "confined_space_permit", "hot_work_permit",
            "work_at_height_permit", "electrical_work_permit",
            "excavation_work_permit", "radiography_work_permit",
            "lifting_work_permit", "temp_electrical_installation_permit",
            "risk_assessment", "new_worker_safety_pledge",
            "msds_posting_education_check",
            "emergency_contact_evacuation_plan",
        ),
        trigger_condition="핵심서류 작성 시 참석자 ≥ 1명",
        output_builder=build_attendance_roster,
        required_fields=(
            "site_name",   # 현장명
            "event_date",  # 행사/교육/회의 일자
            "event_title", # 제목/교육명/회의명
        ),
        optional_fields=(
            "parent_doc_id", "parent_doc_name",
            "event_location", "event_type",
            "event_duration", "instructor", "chairperson",
            "total_attendees", "absent_count",
            "absent_reason", "confirmer", "confirm_date",
        ),
        repeat_field="attendees",
        max_repeat_rows=40,
        priority="P1",
    ),

    # ── 2. photo_attachment_sheet ─────────────────────────────────────────
    "photo_attachment_sheet": SupplementalSpec(
        supplemental_type="photo_attachment_sheet",
        display_name="사진대지",
        category="common",
        parent_form_types=(
            "education_log", "special_education_log",
            "industrial_accident_report", "near_miss_report",
            "accident_root_cause_prevention_report",
            "safety_culture_activity_log",
            "risk_assessment_best_practice_report",
            "emergency_contact_evacuation_plan",
        ),
        trigger_condition="사진 첨부 필요 시 선택 생성",
        output_builder=build_photo_attachment_sheet,
        required_fields=("site_name", "doc_date", "parent_doc_id"),
        optional_fields=("parent_doc_name", "photo_mode", "photographer", "remarks"),
        repeat_field="photo_items",
        max_repeat_rows=12,
        priority="P1",
    ),

    # ── 3. document_attachment_list ───────────────────────────────────────
    "document_attachment_list": SupplementalSpec(
        supplemental_type="document_attachment_list",
        display_name="첨부서류 목록표",
        category="common",
        parent_form_types=(
            "equipment_entry_application", "equipment_insurance_inspection_check",
            "industrial_accident_report", "serious_accident_immediate_report",
            "contractor_safety_document_checklist",
        ),
        trigger_condition="제출 패키지 구성 시 부대서류 2개 이상",
        output_builder=build_document_attachment_list,
        required_fields=("site_name", "doc_date", "parent_doc_id"),
        optional_fields=("parent_doc_name", "submitted_by", "received_by", "remarks"),
        repeat_field="attachment_items",
        max_repeat_rows=20,
        priority="P1",
    ),

    # ── 4. confined_space_gas_measurement ─────────────────────────────────
    "confined_space_gas_measurement": SupplementalSpec(
        supplemental_type="confined_space_gas_measurement",
        display_name="산소·가스농도 측정기록표",
        category="ptw",
        parent_form_types=(
            "confined_space_permit", "confined_space_checklist",
            "confined_space_workplan",
        ),
        trigger_condition="밀폐공간 작업 허가서 발급 시 자동 연동",
        output_builder=build_confined_space_gas_measurement,
        required_fields=("site_name", "work_date", "work_location"),
        optional_fields=("permit_no", "measurer", "equipment_type", "equipment_cert_no"),
        repeat_field="measure_records",
        max_repeat_rows=20,
        priority="P1",
    ),

    # ── 5. work_completion_confirmation ───────────────────────────────────
    "work_completion_confirmation": SupplementalSpec(
        supplemental_type="work_completion_confirmation",
        display_name="작업 종료 확인서",
        category="ptw",
        parent_form_types=(
            "confined_space_permit", "hot_work_permit",
            "work_at_height_permit", "electrical_work_permit",
            "excavation_work_permit", "radiography_work_permit",
            "lifting_work_permit", "temp_electrical_installation_permit",
        ),
        trigger_condition="작업허가서 발급 시 자동 연동, 작업 종료 후 서명",
        output_builder=build_work_completion_confirmation,
        required_fields=(
            "site_name", "permit_date", "work_location", "work_type",
        ),
        optional_fields=(
            "permit_no", "completion_time",
            "fire_watch_duration", "final_check_items",
            "completed_by", "supervisor_confirm",
        ),
        repeat_field=None,
        max_repeat_rows=0,
        priority="P1",
    ),

    # ── 6. improvement_completion_check ───────────────────────────────────
    "improvement_completion_check": SupplementalSpec(
        supplemental_type="improvement_completion_check",
        display_name="개선조치 완료 확인서",
        category="ra_tbm",
        parent_form_types=(
            "risk_assessment", "risk_assessment_register",
            "near_miss_report", "accident_root_cause_prevention_report",
        ),
        trigger_condition="위험성평가 결과 개선 필요 항목 ≥ 1개",
        output_builder=build_improvement_completion_check,
        required_fields=("site_name", "assessment_date"),
        optional_fields=(
            "work_name", "assessor",
            "confirmer", "confirm_date",
        ),
        repeat_field="improvement_items",
        max_repeat_rows=15,
        priority="P1",
    ),

    # ── 7. equipment_operator_qualification_check ─────────────────────────
    "equipment_operator_qualification_check": SupplementalSpec(
        supplemental_type="equipment_operator_qualification_check",
        display_name="운전원 자격 확인표",
        category="equipment",
        parent_form_types=(
            "equipment_entry_application", "tower_crane_workplan",
            "mobile_crane_workplan", "heavy_lifting_workplan",
            "piling_workplan", "piling_use_workplan",
            "lift_gondola_use_plan", "aerial_work_platform_use_plan",
        ),
        trigger_condition="유자격 장비 반입 신청 시 선택 생성",
        output_builder=build_equipment_operator_qualification_check,
        required_fields=("site_name", "check_date", "equipment_type"),
        optional_fields=("equipment_model", "equipment_no", "checker"),
        repeat_field="operators",
        max_repeat_rows=10,
        priority="P1",
    ),

    # ── 8. watchman_assignment_confirmation ───────────────────────────────
    "watchman_assignment_confirmation": SupplementalSpec(
        supplemental_type="watchman_assignment_confirmation",
        display_name="감시인 배치 확인서",
        category="ptw",
        parent_form_types=(
            "confined_space_permit", "hot_work_permit",
            "radiography_work_permit",
        ),
        trigger_condition="감시인 지정이 필요한 작업허가서 발급 시",
        output_builder=build_watchman_assignment_confirmation,
        required_fields=("site_name", "permit_date", "work_location"),
        optional_fields=(
            "permit_no", "work_type",
            "watchman_name", "watchman_position", "watchman_contact",
            "duty_desc", "duty_start", "duty_end",
            "supervisor", "sign_date",
        ),
        repeat_field=None,
        max_repeat_rows=0,
        priority="P2",
    ),

    # ── 9. education_makeup_confirmation ──────────────────────────────────
    "education_makeup_confirmation": SupplementalSpec(
        supplemental_type="education_makeup_confirmation",
        display_name="미참석자 추가교육 확인서",
        category="education",
        parent_form_types=(
            "education_log", "special_education_log",
        ),
        trigger_condition="교육 미참석자 ≥ 1명이고 보완 교육 실시 시",
        output_builder=_todo_builder,  # TODO: education_makeup_confirmation_builder.py
        required_fields=(
            "site_name", "original_edu_date", "edu_subject",
            "makeup_date",
        ),
        optional_fields=(
            "makeup_location", "makeup_instructor",
            "total_absent", "makeup_duration",
            "confirmer",
        ),
        repeat_field="absent_list",
        max_repeat_rows=20,
        priority="P2",
    ),

    # ── 10. ppe_receipt_confirmation ──────────────────────────────────────
    "ppe_receipt_confirmation": SupplementalSpec(
        supplemental_type="ppe_receipt_confirmation",
        display_name="보호구 수령 확인서",
        category="equipment",
        parent_form_types=(
            "ppe_issue_register", "ppe_management_checklist",
        ),
        trigger_condition="보호구 지급 후 수령자 서명 확인 시",
        output_builder=_todo_builder,  # TODO: ppe_receipt_confirmation_builder.py
        required_fields=("site_name", "issue_date"),
        optional_fields=("issuer", "approver", "remarks"),
        repeat_field="ppe_items",
        max_repeat_rows=20,
        priority="P2",
    ),
}

# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def list_supplemental_types() -> List[Dict[str, Any]]:
    """등록된 모든 supplemental_type 메타데이터 목록 반환."""
    result = []
    for spec in _SUPPLEMENTARY_REGISTRY.values():
        result.append({
            "supplemental_type": spec.supplemental_type,
            "display_name":      spec.display_name,
            "category":          spec.category,
            "parent_form_types": list(spec.parent_form_types),
            "trigger_condition": spec.trigger_condition,
            "has_builder":       spec.output_builder is not _todo_builder,
            "required_fields":   list(spec.required_fields),
            "optional_fields":   list(spec.optional_fields),
            "repeat_field":      spec.repeat_field,
            "max_repeat_rows":   spec.max_repeat_rows,
            "priority":          spec.priority,
        })
    return result


def get_supplemental_spec(supplemental_type: str) -> Dict[str, Any]:
    """supplemental_type으로 spec dict 반환. 없으면 KeyError."""
    if supplemental_type not in _SUPPLEMENTARY_REGISTRY:
        supported = ", ".join(_SUPPLEMENTARY_REGISTRY.keys())
        raise KeyError(
            f"지원하지 않는 supplemental_type: '{supplemental_type}'. "
            f"지원 목록: {supported}"
        )
    spec = _SUPPLEMENTARY_REGISTRY[supplemental_type]
    return {
        "supplemental_type": spec.supplemental_type,
        "display_name":      spec.display_name,
        "category":          spec.category,
        "parent_form_types": list(spec.parent_form_types),
        "trigger_condition": spec.trigger_condition,
        "has_builder":       spec.output_builder is not _todo_builder,
        "required_fields":   list(spec.required_fields),
        "optional_fields":   list(spec.optional_fields),
        "repeat_field":      spec.repeat_field,
        "max_repeat_rows":   spec.max_repeat_rows,
        "priority":          spec.priority,
    }


def get_supplemental_types_for(parent_form_type: str) -> List[Dict[str, Any]]:
    """핵심 form_type에 연동 가능한 부대서류 목록 반환."""
    result = []
    for spec in _SUPPLEMENTARY_REGISTRY.values():
        if parent_form_type in spec.parent_form_types:
            result.append(get_supplemental_spec(spec.supplemental_type))
    return result


def build_supplemental_excel(
    supplemental_type: str,
    form_data: Dict[str, Any],
) -> bytes:
    """
    부대서류 Excel bytes 반환.

    Args:
        supplemental_type: 부대서류 타입 식별자
        form_data:         입력 데이터 dict

    Returns:
        xlsx bytes

    Raises:
        KeyError:           미등록 supplemental_type
        NotImplementedError: builder 미구현 (TODO 상태)
    """
    if supplemental_type not in _SUPPLEMENTARY_REGISTRY:
        supported = ", ".join(_SUPPLEMENTARY_REGISTRY.keys())
        raise KeyError(
            f"지원하지 않는 supplemental_type: '{supplemental_type}'. "
            f"지원 목록: {supported}"
        )
    spec = _SUPPLEMENTARY_REGISTRY[supplemental_type]
    if spec.output_builder is None or spec.output_builder is _todo_builder:
        raise NotImplementedError(
            f"'{supplemental_type}' builder는 아직 구현되지 않았습니다. "
            f"현재 구현된 부대서류: "
            + ", ".join(
                k for k, v in _SUPPLEMENTARY_REGISTRY.items()
                if v.output_builder is not _todo_builder and v.output_builder is not None
            )
        )
    return spec.output_builder(form_data)

"""
Safety Decision Engine — 안전의무 자동판정 엔진 (read-only)

공개 API:
    resolve_by_equipment(equipment_type_id) -> dict
    resolve_by_work_type(work_type_code) -> dict
    resolve_compliance_basis(target_type, target_id) -> list[dict]
    build_decision_summary(input_type, input_id) -> dict
"""
from .decision_engine import (
    resolve_by_equipment,
    resolve_by_work_type,
    resolve_compliance_basis,
    build_decision_summary,
)

__all__ = [
    "resolve_by_equipment",
    "resolve_by_work_type",
    "resolve_compliance_basis",
    "build_decision_summary",
]

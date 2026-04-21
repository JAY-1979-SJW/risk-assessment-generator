"""
Maps a project_assessments DB row to a RagInput dict for the RAG engine.

Mapping rules:
- All text fields are stripped and None-coalesced
- risk_situation blank → raises ValueError (execution blocked)
- process/sub_work blank → raises ValueError
- v1 optional fields (risk_category, risk_detail, current_measures, legal_basis)
  passed through as-is (may be None or empty string)
- v2 fields: included only when present in row (하위 호환 유지)
  Boolean DB values: passed as-is (PostgreSQL returns Python bool)
  Enum DB values: validated against allowed sets; invalid → None with warning
"""

import logging
import unicodedata
from typing import Any, Dict, Optional

from engine.rag_risk_engine.schema import (
    WORK_ENVIRONMENT_VALUES,
    SURFACE_CONDITION_VALUES,
    WEATHER_VALUES,
    _validate_enum,
    _coerce_bool,
    _coerce_numeric,
)

logger = logging.getLogger(__name__)

# v2 boolean column names in project_assessments
_V2_BOOL_FIELDS = (
    'night_work', 'confined_space', 'hot_work', 'electrical_work',
    'heavy_equipment', 'work_at_height', 'simultaneous_work',
)


def _clean(value: Any) -> Optional[str]:
    """Strip, normalize NFC, return None if empty."""
    if value is None:
        return None
    s = unicodedata.normalize('NFC', str(value)).strip()
    return s if s else None


def map_row_to_input(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a project_assessments row dict → engine RagInput dict.

    v1 fields always mapped; v2 fields included only when present (하위 호환).

    Raises:
        ValueError: if required fields (process, sub_work, risk_situation) are blank.
    """
    process = _clean(row.get('process'))
    sub_work = _clean(row.get('sub_work'))
    risk_situation = _clean(row.get('risk_situation'))

    errors = []
    if not process:
        errors.append("'process' 필드가 비어 있습니다")
    if not sub_work:
        errors.append("'sub_work' 필드가 비어 있습니다")
    if not risk_situation:
        errors.append("'risk_situation' 필드가 비어 있습니다 — 엔진 실행 금지")

    if errors:
        raise ValueError('; '.join(errors))

    result: Dict[str, Any] = {
        'process': process,
        'sub_work': sub_work,
        'risk_situation': risk_situation,
        'risk_category': _clean(row.get('risk_category')),
        'risk_detail': _clean(row.get('risk_detail')),
        'current_measures': _clean(row.get('current_measures')),
        'legal_basis_hint': _clean(row.get('legal_basis')),
        'top_k': 10,
    }

    # ── v2 fields — only if column exists in row ──────────────────────────
    if 'height_m' in row and row['height_m'] is not None:
        result['height_m'] = _coerce_numeric(row['height_m'], 'height_m', float, 0)

    if 'worker_count' in row and row['worker_count'] is not None:
        result['worker_count'] = _coerce_numeric(row['worker_count'], 'worker_count', int, 1)

    if 'work_environment' in row:
        result['work_environment'] = _validate_enum(
            row.get('work_environment'), WORK_ENVIRONMENT_VALUES, 'work_environment')

    if 'surface_condition' in row:
        result['surface_condition'] = _validate_enum(
            row.get('surface_condition'), SURFACE_CONDITION_VALUES, 'surface_condition')

    if 'weather' in row:
        result['weather'] = _validate_enum(
            row.get('weather'), WEATHER_VALUES, 'weather')

    for bool_field in _V2_BOOL_FIELDS:
        if bool_field in row:
            result[bool_field] = _coerce_bool(row[bool_field], bool_field)

    hint = _clean(row.get('hazard_priority_hint'))
    if hint:
        result['hazard_priority_hint'] = hint

    return result

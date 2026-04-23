"""
KRAS engine mapper.

Functions:
  map_row_to_input  — project_assessments row → RagInput dict (RAG engine)
  build_risk_assessment — work_type string → risk assessment dict (risk_mapping_core)

map_row_to_input rules:
- All text fields are stripped and None-coalesced
- risk_situation blank → raises ValueError (execution blocked)
- process/sub_work blank → raises ValueError
- v1 optional fields (risk_category, risk_detail, current_measures, legal_basis)
  passed through as-is (may be None or empty string)
- v2 fields: included only when present in row (하위 호환 유지)
  Boolean DB values: passed as-is (PostgreSQL returns Python bool)
  Enum DB values: validated against allowed sets; invalid → None with warning
"""

import json
import logging
import unicodedata
from typing import Any, Dict, List, Optional

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


# ── risk_mapping_core 매핑 ────────────────────────────────────────────────

_RISK_MAPPING_QUERY = """
SELECT
    id,
    work_type,
    hazard,
    related_law_ids,
    related_moel_expc_ids,
    related_kosha_ids,
    control_measures,
    confidence_score,
    evidence_summary
FROM risk_mapping_core
WHERE work_type = %(work_type)s
  AND hazard IS NOT NULL
  AND evidence_summary IS NOT NULL
  AND control_measures IS NOT NULL
ORDER BY confidence_score DESC
"""


def _parse_control_measures(raw: Any) -> List[str]:
    """Extract measures list from control_measures JSONB field."""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            logger.warning('control_measures JSON 파싱 실패: %r', raw)
            return []
    if isinstance(raw, dict):
        measures = raw.get('measures', [])
        if isinstance(measures, list):
            return [str(m) for m in measures if m]
        logger.warning('control_measures.measures 가 리스트가 아님: %r', measures)
        return []
    logger.warning('control_measures 구조 미인식: %r', type(raw))
    return []


def _parse_id_list(raw: Any, field: str) -> List[int]:
    """Extract integer ID list from JSONB array field."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [int(v) for v in raw if v is not None]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return [int(v) for v in parsed if v is not None]
        except (json.JSONDecodeError, ValueError):
            logger.warning('%s JSON 파싱 실패: %r', field, raw)
            return []
    logger.warning('%s 타입 미인식: %r', field, type(raw))
    return []


def _row_to_hazard(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert a single risk_mapping_core row to a hazard dict."""
    hazard = _clean(row.get('hazard'))
    if not hazard:
        logger.warning('hazard 값 없음 — row id=%s 건너뜀', row.get('id'))
        return None

    controls = _parse_control_measures(row.get('control_measures'))
    if not controls:
        logger.warning('controls 비어 있음 — work_type=%s hazard=%s',
                       row.get('work_type'), hazard)

    law_ids = _parse_id_list(row.get('related_law_ids'), 'related_law_ids')
    moel_expc_ids = _parse_id_list(row.get('related_moel_expc_ids'), 'related_moel_expc_ids')
    kosha_ids = _parse_id_list(row.get('related_kosha_ids'), 'related_kosha_ids')

    if not law_ids:
        logger.warning('related_law_ids 비어 있음 — work_type=%s hazard=%s',
                       row.get('work_type'), hazard)
    if not moel_expc_ids:
        logger.warning('related_moel_expc_ids 비어 있음 — work_type=%s hazard=%s',
                       row.get('work_type'), hazard)
    if not kosha_ids:
        logger.warning('related_kosha_ids 비어 있음 — work_type=%s hazard=%s',
                       row.get('work_type'), hazard)

    score_raw = row.get('confidence_score')
    try:
        confidence_score = float(score_raw) if score_raw is not None else 0.0
    except (TypeError, ValueError):
        logger.warning('confidence_score 변환 실패: %r', score_raw)
        confidence_score = 0.0

    evidence_summary = _clean(row.get('evidence_summary')) or ''
    if len(evidence_summary) < 100:
        logger.warning('evidence_summary 100자 미만 (%d자) — work_type=%s hazard=%s',
                       len(evidence_summary), row.get('work_type'), hazard)

    return {
        'hazard': hazard,
        'controls': controls,
        'references': {
            'law_ids': law_ids,
            'moel_expc_ids': moel_expc_ids,
            'kosha_ids': kosha_ids,
        },
        'confidence_score': confidence_score,
        'evidence_summary': evidence_summary,
    }


def build_risk_assessment(work_type: str) -> Dict[str, Any]:
    """
    Query risk_mapping_core by work_type and return a structured risk assessment dict.

    Returns:
        {
            "work_type": str,
            "hazards": [
                {
                    "hazard": str,
                    "controls": list[str],
                    "references": {
                        "law_ids": list[int],
                        "moel_expc_ids": list[int],
                        "kosha_ids": list[int],
                    },
                    "confidence_score": float,
                    "evidence_summary": str,
                }
            ]
        }

    Raises:
        RuntimeError: DB 연결 실패 시
    """
    from engine.kras_connector.db import fetchall  # 지연 import — 순환 방지

    wt = _clean(work_type)
    if not wt:
        logger.warning('build_risk_assessment: work_type 이 비어 있음')
        return {'work_type': work_type or '', 'hazards': []}

    rows = fetchall(_RISK_MAPPING_QUERY, {'work_type': wt})

    if not rows:
        logger.warning('build_risk_assessment: work_type=%r — 조회 결과 없음', wt)
        return {'work_type': wt, 'hazards': []}

    seen_hazards: set = set()
    hazards: List[Dict[str, Any]] = []

    for row in rows:
        hazard_entry = _row_to_hazard(row)
        if hazard_entry is None:
            continue
        hazard_key = hazard_entry['hazard']
        if hazard_key in seen_hazards:
            logger.warning('중복 hazard 건너뜀: work_type=%s hazard=%s', wt, hazard_key)
            continue
        seen_hazards.add(hazard_key)
        hazards.append(hazard_entry)

    return {'work_type': wt, 'hazards': hazards}

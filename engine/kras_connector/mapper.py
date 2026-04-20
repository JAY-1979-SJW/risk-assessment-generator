"""
Maps a project_assessments DB row to a RagInput dict for the RAG engine.

Mapping rules:
- All text fields are stripped and None-coalesced
- risk_situation blank → raises ValueError (execution blocked)
- process/sub_work blank → raises ValueError
- Optional fields (risk_category, risk_detail, current_measures, legal_basis)
  passed through as-is (may be None or empty string)
"""

import unicodedata
from typing import Any, Dict, Optional


def _clean(value: Any) -> Optional[str]:
    """Strip, normalize NFC, return None if empty."""
    if value is None:
        return None
    s = unicodedata.normalize('NFC', str(value)).strip()
    return s if s else None


def map_row_to_input(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a project_assessments row dict → engine RagInput dict.

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

    return {
        'process': process,
        'sub_work': sub_work,
        'risk_situation': risk_situation,
        'risk_category': _clean(row.get('risk_category')),
        'risk_detail': _clean(row.get('risk_detail')),
        'current_measures': _clean(row.get('current_measures')),
        'legal_basis_hint': _clean(row.get('legal_basis')),
        'top_k': 10,
    }

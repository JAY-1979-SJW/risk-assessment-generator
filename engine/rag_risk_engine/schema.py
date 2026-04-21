import logging
from typing import TypedDict, Dict, List, Optional, Literal

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ('process', 'sub_work', 'risk_situation')
DEFAULT_TOP_K = 10

# v2 enum allowed values
WORK_ENVIRONMENT_VALUES = frozenset({'indoor', 'outdoor', 'mixed'})
SURFACE_CONDITION_VALUES = frozenset({'normal', 'wet', 'slippery', 'uneven'})
WEATHER_VALUES = frozenset({'clear', 'rain', 'snow', 'wind', 'extreme'})


class RagInput(TypedDict, total=False):
    # ── v1 fields (required) ──────────────────────────────────────────────
    process: str            # required  — 공정명
    sub_work: str           # required  — 세부작업명
    risk_situation: str     # required  — 위험상황 (core input)
    # ── v1 fields (optional) ─────────────────────────────────────────────
    risk_category: str      # optional  — 위험분류
    risk_detail: str        # optional  — 위험세부분류
    current_measures: str   # optional  — 현재조치
    legal_basis_hint: str   # optional  — 법령 힌트
    top_k: int              # optional  — default 10, range 1-50
    # ── v2 core fields (optional → 점진적 필수화) ─────────────────────────
    height_m: float         # optional  — 작업 높이(m), >= 0
    worker_count: int       # optional  — 작업 인원, >= 1
    work_environment: str   # optional  — indoor/outdoor/mixed
    night_work: bool        # optional  — 야간작업 여부
    confined_space: bool    # optional  — 밀폐공간 여부
    hot_work: bool          # optional  — 화기작업 여부
    electrical_work: bool   # optional  — 전기작업 여부
    heavy_equipment: bool   # optional  — 중장비 사용 여부
    work_at_height: bool    # optional  — 고소작업 여부
    # ── v2 auxiliary fields ───────────────────────────────────────────────
    surface_condition: str  # optional  — normal/wet/slippery/uneven
    weather: str            # optional  — clear/rain/snow/wind/extreme
    simultaneous_work: bool # optional  — 동시작업 여부
    hazard_priority_hint: str  # optional  — 위험 우선순위 힌트 (자유 텍스트)


class MatchedChunk(TypedDict):
    chunk_id: int
    score: float
    text_preview: str
    work_type: Optional[str]
    hazard_type: Optional[str]
    control_measure: Optional[str]
    ppe: Optional[str]
    law_ref: Optional[str]
    has_tags: bool


class LegalBasisItem(TypedDict):
    law_code: str
    law_name: str
    article_no: str
    title: str
    relation_type: str          # required / recommended / reference
    matched_by: List[str]       # hazard / work_type / control


class RagOutput(TypedDict):
    # ── v1 core output fields ─────────────────────────────────────────────────
    query_summary: str
    matched_chunks: List[MatchedChunk]
    primary_hazards: List[str]
    recommended_actions: List[str]
    required_ppe: List[str]
    legal_basis_candidates: List[str]
    source_chunk_ids: List[int]
    confidence: Literal['low', 'medium', 'high']
    warnings: List[str]
    reasoning_notes: List[str]
    # ── v2 traceability fields (고도화 1차) ───────────────────────────────────
    evidence_sources: Dict[str, List[str]]   # retrieval vs DB 결과 분리
    boosted_by_conditions: List[str]          # 매칭된 condition_scenario IDs
    boosted_by_taxonomy: List[str]            # 적용된 work_type codes
    source_db_refs: List[str]                 # 참조된 risk_db 레코드 IDs
    # ── v2 legal enrichment fields (고도화 2단계) ─────────────────────────────
    legal_basis: List[LegalBasisItem]         # 법령 근거 요약 (사용자 표시용)
    law_refs: Dict[str, List[str]]            # source별 law_code 목록 (추적용)
    legal_warnings: List[str]                 # 법령 기반 경고


def _coerce_bool(value, field: str) -> Optional[bool]:
    """Coerce truthy/falsy values to bool. Returns None if absent."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ('true', '1', 'yes'):
            return True
        if v in ('false', '0', 'no', ''):
            return False
    logger.warning("v2 boolean coercion fallback for '%s': %r → False", field, value)
    return False


def _validate_enum(value: Optional[str], allowed: frozenset, field: str) -> Optional[str]:
    """Return value if in allowed set, else None with a warning."""
    if value is None:
        return None
    if value in allowed:
        return value
    logger.warning("v2 enum 검증 실패 — '%s': %r (허용값: %s) → None 처리", field, value, sorted(allowed))
    return None


def _coerce_numeric(value, field: str, target_type, min_val):
    """Cast value to target_type; return None if out of range or unconvertible."""
    if value is None:
        return None
    try:
        v = target_type(value)
        if v < min_val:
            logger.warning("v2 %s 비정상 값 %r → None 처리", field, v)
            return None
        return v
    except (TypeError, ValueError):
        logger.warning("v2 %s 타입 오류 %r → None 처리", field, value)
        return None


def validate_input(raw: dict) -> RagInput:
    """Validate and normalize engine input. Raises ValueError on invalid input."""
    # ── required fields ───────────────────────────────────────────────────
    errors = []
    for field in REQUIRED_FIELDS:
        val = raw.get(field)
        if not val or not isinstance(val, str) or not val.strip():
            errors.append(f"필수 입력 누락 또는 빈 값: '{field}'")

    if errors:
        raise ValueError('; '.join(errors))

    top_k = raw.get('top_k', DEFAULT_TOP_K)
    if not isinstance(top_k, int) or not (1 <= top_k <= 50):
        raise ValueError(f"top_k는 1~50 사이 정수여야 합니다 (입력값: {top_k!r})")

    # ── v1 optional fields ────────────────────────────────────────────────
    result: dict = {
        'process': raw['process'].strip(),
        'sub_work': raw['sub_work'].strip(),
        'risk_situation': raw['risk_situation'].strip(),
        'risk_category': (raw.get('risk_category') or '').strip() or None,
        'risk_detail': (raw.get('risk_detail') or '').strip() or None,
        'current_measures': (raw.get('current_measures') or '').strip() or None,
        'legal_basis_hint': (raw.get('legal_basis_hint') or '').strip() or None,
        'top_k': top_k,
    }

    # ── v2 fields — include only when provided (하위 호환) ────────────────
    if raw.get('height_m') is not None:
        result['height_m'] = _coerce_numeric(raw['height_m'], 'height_m', float, 0)

    if raw.get('worker_count') is not None:
        result['worker_count'] = _coerce_numeric(raw['worker_count'], 'worker_count', int, 1)

    # enum fields
    if raw.get('work_environment') is not None:
        result['work_environment'] = _validate_enum(
            raw.get('work_environment'), WORK_ENVIRONMENT_VALUES, 'work_environment')
    if raw.get('surface_condition') is not None:
        result['surface_condition'] = _validate_enum(
            raw.get('surface_condition'), SURFACE_CONDITION_VALUES, 'surface_condition')
    if raw.get('weather') is not None:
        result['weather'] = _validate_enum(
            raw.get('weather'), WEATHER_VALUES, 'weather')

    # boolean fields
    for bool_field in (
        'night_work', 'confined_space', 'hot_work', 'electrical_work',
        'heavy_equipment', 'work_at_height', 'simultaneous_work',
    ):
        raw_val = raw.get(bool_field)
        if raw_val is not None:
            result[bool_field] = _coerce_bool(raw_val, bool_field)

    # hazard_priority_hint
    hint = (raw.get('hazard_priority_hint') or '').strip()
    if hint:
        result['hazard_priority_hint'] = hint

    return result

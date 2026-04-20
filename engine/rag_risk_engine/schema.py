from typing import TypedDict, List, Optional, Literal

REQUIRED_FIELDS = ('process', 'sub_work', 'risk_situation')
DEFAULT_TOP_K = 10


class RagInput(TypedDict, total=False):
    process: str            # required  — 공정명
    sub_work: str           # required  — 세부작업명
    risk_situation: str     # required  — 위험상황 (core input)
    risk_category: str      # optional  — 위험분류
    risk_detail: str        # optional  — 위험세부분류
    current_measures: str   # optional  — 현재조치
    legal_basis_hint: str   # optional  — 법령 힌트
    top_k: int              # optional  — default 10, range 1-50


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


class RagOutput(TypedDict):
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


def validate_input(raw: dict) -> RagInput:
    """Validate and normalize engine input. Raises ValueError on invalid input."""
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

    return {
        'process': raw['process'].strip(),
        'sub_work': raw['sub_work'].strip(),
        'risk_situation': raw['risk_situation'].strip(),
        'risk_category': (raw.get('risk_category') or '').strip() or None,
        'risk_detail': (raw.get('risk_detail') or '').strip() or None,
        'current_measures': (raw.get('current_measures') or '').strip() or None,
        'legal_basis_hint': (raw.get('legal_basis_hint') or '').strip() or None,
        'top_k': top_k,
    }

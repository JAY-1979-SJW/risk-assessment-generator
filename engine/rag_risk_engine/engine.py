"""
RAG Risk Engine v1 — orchestrates retrieval, dedup, and assembly.
Deterministic, local, no external API/LLM calls.
"""

from typing import Any, Dict, List, Optional

from .schema import RagInput, RagOutput, validate_input
from .retrieval import BM25Index, normalize_text
from .assembler import (
    assemble_hazards,
    assemble_actions,
    assemble_ppe,
    assemble_legal,
    calculate_confidence,
    build_warnings,
    build_reasoning_notes,
)


def _build_query(inp: RagInput) -> str:
    """Combine input fields into a single search query, risk_situation weighted first."""
    parts = [
        inp['risk_situation'],     # core
        inp['sub_work'],
        inp.get('risk_category') or '',
        inp.get('risk_detail') or '',
        inp.get('legal_basis_hint') or '',
    ]
    return ' '.join(p for p in parts if p)


def _dedup_chunks(
    chunks: List[Dict[str, Any]],
    scores: List[float],
) -> tuple[List[Dict[str, Any]], List[float]]:
    """
    Remove chunks with near-duplicate normalized_text.
    Keeps the higher-scored version when duplicates are found.
    Uses normalized text comparison (exact match after normalization).
    """
    seen: Dict[str, int] = {}  # normalized_text → index in result
    result_chunks = []
    result_scores = []

    for chunk, score in zip(chunks, scores):
        text = normalize_text(
            chunk.get('normalized_text') or chunk.get('raw_text') or ''
        ).lower()
        # Truncate to first 80 chars as fingerprint
        fp = text[:80]
        if fp in seen:
            existing_idx = seen[fp]
            if score > result_scores[existing_idx]:
                result_chunks[existing_idx] = chunk
                result_scores[existing_idx] = score
        else:
            seen[fp] = len(result_chunks)
            result_chunks.append(chunk)
            result_scores.append(score)

    return result_chunks, result_scores


def run_engine(
    raw_input: dict,
    chunks: List[Dict[str, Any]],
) -> RagOutput:
    """
    Main entry point.
    Args:
        raw_input: dict matching RagInput schema (validated internally)
        chunks:    list of KOSHA chunk dicts from loader
    Returns:
        RagOutput dict (JSON-serializable)
    Raises:
        ValueError: on invalid input
        ValueError: if chunks list is empty
    """
    inp = validate_input(raw_input)

    if not chunks:
        raise ValueError('청크 데이터가 비어 있습니다. 데이터 소스를 확인하세요.')

    top_k = inp.get('top_k', 10)
    query = _build_query(inp)
    query_summary = f"{inp['process']} / {inp['sub_work']}: {inp['risk_situation']}"

    # Build BM25 index and search
    index = BM25Index(chunks)
    raw_results = index.search(query, top_k=top_k)

    if not raw_results:
        return _empty_result(query_summary)

    # Extract and dedup chunks
    result_chunks = [chunks[i] for i, _ in raw_results]
    result_scores = [s for _, s in raw_results]
    result_chunks, result_scores = _dedup_chunks(result_chunks, result_scores)

    # Build matched_chunk summaries for output
    matched = []
    for chunk, score in zip(result_chunks, result_scores):
        text = chunk.get('normalized_text') or chunk.get('raw_text') or ''
        matched.append({
            'chunk_id': int(chunk.get('id', 0)),
            'score': round(score, 4),
            'text_preview': text[:120],
            'work_type': chunk.get('work_type') or None,
            'hazard_type': chunk.get('hazard_type') or None,
            'control_measure': chunk.get('control_measure') or None,
            'ppe': chunk.get('ppe') or None,
            'law_ref': chunk.get('law_ref') or None,
            'has_tags': bool(chunk.get('work_type') or chunk.get('hazard_type')),
        })

    # Assemble result fields
    hazards = assemble_hazards(result_chunks)
    actions = assemble_actions(result_chunks)
    ppe = assemble_ppe(result_chunks)
    legal = assemble_legal(result_chunks)
    confidence = calculate_confidence(result_chunks, result_scores)
    warnings = build_warnings(result_chunks, legal, confidence)
    notes = build_reasoning_notes(query_summary, result_chunks, result_scores, hazards, confidence)

    return {
        'query_summary': query_summary,
        'matched_chunks': matched,
        'primary_hazards': hazards,
        'recommended_actions': actions,
        'required_ppe': ppe,
        'legal_basis_candidates': legal,
        'source_chunk_ids': [int(c.get('id', 0)) for c in result_chunks],
        'confidence': confidence,
        'warnings': warnings,
        'reasoning_notes': notes,
    }


def _empty_result(query_summary: str) -> RagOutput:
    return {
        'query_summary': query_summary,
        'matched_chunks': [],
        'primary_hazards': [],
        'recommended_actions': [],
        'required_ppe': [],
        'legal_basis_candidates': [],
        'source_chunk_ids': [],
        'confidence': 'low',
        'warnings': ['검색 결과 없음: 입력 텍스트와 매칭되는 KOSHA 청크가 없습니다.'],
        'reasoning_notes': [f'쿼리 요약: {query_summary}', '검색 결과 없음'],
    }

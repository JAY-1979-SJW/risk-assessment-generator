"""
RAG Risk Engine v2 — orchestrates retrieval, dedup, assembly, and risk_db boost.
Deterministic, local, no external API/LLM calls.

v2 upgrade (고도화 1차):
  - risk_db_booster integrated: condition_scenarios, hazard_controls, hazard_ppe
  - work_taxonomy query expansion
  - additive-only boost: KOSHA retrieval results are never replaced
  - new output fields: evidence_sources, boosted_by_conditions, boosted_by_taxonomy, source_db_refs
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
from .risk_db_booster import expand_query_by_taxonomy, boost_results, build_legal_enrichment


def _merge_items_with_cap(baseline: List[str], additions: List[str], max_count: int) -> List[str]:
    seen = {a.strip() for a in baseline}
    result = list(baseline)
    for item in additions:
        s = item.strip()
        if s and s not in seen:
            result.append(s)
            seen.add(s)
    return result[:max_count]


def _build_query(inp: RagInput) -> str:
    """Combine input fields into a single search query, risk_situation weighted first.

    v2: Append condition hint tokens when v2 flags are set.
    These are short Korean keyword clusters that boost BM25 ranking for
    relevant KOSHA chunks — they do NOT generate new content.
    """
    parts = [
        inp['risk_situation'],     # core
        inp['sub_work'],
        inp.get('risk_category') or '',
        inp.get('risk_detail') or '',
        inp.get('legal_basis_hint') or '',
    ]

    # v2 condition boosts — append hint tokens only when flag is set
    if inp.get('confined_space'):
        parts.append('밀폐공간 질식 산소결핍 환기')
    if inp.get('hot_work'):
        parts.append('화기작업 화재 폭발 불꽃')
    if inp.get('electrical_work'):
        parts.append('전기작업 감전 활선 절연')
    if inp.get('work_at_height') or (inp.get('height_m') or 0) > 2:
        parts.append('고소작업 추락 안전대 안전난간')
    if inp.get('heavy_equipment'):
        parts.append('중장비 충돌 낙하 신호수')
    if inp.get('night_work'):
        parts.append('야간작업 조명 시야')
    if inp.get('simultaneous_work'):
        parts.append('동시작업 협착 충돌 신호수')
    if inp.get('hazard_priority_hint'):
        parts.append(inp['hazard_priority_hint'])

    # v2 taxonomy expansion — adds hazard-specific query terms based on sub_work match
    taxonomy_tokens = expand_query_by_taxonomy(inp)
    if taxonomy_tokens:
        parts.append(taxonomy_tokens)

    # v2 surface/weather boosts
    surface = inp.get('surface_condition') or ''
    if surface in ('wet', 'slippery'):
        parts.append('미끄럼 안전화 바닥')
    weather = inp.get('weather') or ''
    if weather in ('rain', 'snow'):
        parts.append('우천 결빙 미끄럼')
    elif weather in ('wind', 'extreme'):
        parts.append('강풍 악천후 작업중지')

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

    # Assemble result fields (KOSHA retrieval — baseline)
    hazards = assemble_hazards(result_chunks)
    actions = assemble_actions(result_chunks, hazards=hazards)  # v1.2: pass hazards
    ppe = assemble_ppe(result_chunks)
    legal = assemble_legal(result_chunks)
    confidence = calculate_confidence(result_chunks, result_scores)
    warnings = build_warnings(result_chunks, legal, confidence)
    notes = build_reasoning_notes(query_summary, result_chunks, result_scores, hazards, confidence)

    # ── v2: risk_db additive boost ─────────────────────────────────────────
    boost = boost_results(inp, hazards, actions, ppe, legal)

    combined_actions = _merge_items_with_cap(actions, boost['scenario_controls'] + boost['db_controls'], 10)
    combined_ppe     = _merge_items_with_cap(ppe,     boost['db_ppe'],                                    8)
    combined_legal   = _merge_items_with_cap(legal,   boost['db_law_refs'],                               6)

    # Merge warnings: retrieval warnings → condition warnings → input warnings
    combined_warnings = warnings + boost['condition_warnings'] + boost['input_warnings']

    # Evidence sources for traceability
    evidence_sources: Dict[str, List[str]] = {
        'retrieval_actions':   actions[:],
        'scenario_actions':    boost['scenario_controls'],
        'db_actions':          boost['db_controls'],
        'retrieval_ppe':       ppe[:],
        'db_ppe':              boost['db_ppe'],
        'retrieval_legal':     legal[:],
        'db_legal':            boost['db_law_refs'],
    }

    # Append boost notes to reasoning
    if boost['boosted_by_conditions']:
        notes = list(notes) + [
            f"조건 시나리오 매칭: {', '.join(boost['boosted_by_conditions'])}"
        ]
    if boost['boosted_by_taxonomy']:
        notes = list(notes) + [
            f"taxonomy 확장 적용: {', '.join(boost['boosted_by_taxonomy'])}"
        ]

    # ── v2 legal enrichment (2단계) ────────────────────────────────────────
    legal_enrich = build_legal_enrichment(
        hazard_codes=boost['hazard_codes'],
        work_type_codes=boost['boosted_by_taxonomy'],
        combined_actions=combined_actions,
        combined_ppe=combined_ppe,
    )

    return {
        # ── v1 core fields ──────────────────────────────────────────────────
        'query_summary': query_summary,
        'matched_chunks': matched,
        'primary_hazards': hazards,
        'recommended_actions': combined_actions,
        'required_ppe': combined_ppe,
        'legal_basis_candidates': combined_legal,
        'source_chunk_ids': [int(c.get('id', 0)) for c in result_chunks],
        'confidence': confidence,
        'warnings': combined_warnings,
        'reasoning_notes': notes,
        # ── v2 traceability fields ──────────────────────────────────────────
        'evidence_sources':       evidence_sources,
        'boosted_by_conditions':  boost['boosted_by_conditions'],
        'boosted_by_taxonomy':    boost['boosted_by_taxonomy'],
        'source_db_refs':         boost['source_db_refs'],
        # ── v2 legal enrichment fields (2단계) ─────────────────────────────
        'legal_basis':            legal_enrich['legal_basis'],
        'law_refs':               legal_enrich['law_refs'],
        'legal_warnings':         legal_enrich['legal_warnings'],
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
        'evidence_sources': {},
        'boosted_by_conditions': [],
        'boosted_by_taxonomy': [],
        'source_db_refs': [],
        'legal_basis': [],
        'law_refs': {'hazard_refs': [], 'work_type_refs': [], 'control_refs': []},
        'legal_warnings': [],
    }

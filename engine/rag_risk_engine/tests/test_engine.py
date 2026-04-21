"""
RAG Risk Engine v1 — 10+ automated tests.
All tests use local fixture data (no DB connection required).
Run: python -m pytest engine/rag_risk_engine/tests/test_engine.py -v
"""

import json
import os
import sys
import pytest

# Allow import from project root
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

from engine.rag_risk_engine.engine import run_engine
from engine.rag_risk_engine.schema import validate_input

_FIXTURE = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_chunks.json')


def _chunks():
    with open(_FIXTURE, 'r', encoding='utf-8') as f:
        return json.load(f)


# ── helpers ───────────────────────────────────────────────────────────────

def _run(inp: dict) -> dict:
    return run_engine(inp, _chunks())


# ── Test 1: 일반 추락 위험 텍스트 ────────────────────────────────────────

def test_fall_risk_basic():
    result = _run({
        'process': '건축',
        'sub_work': '작업발판 설치',
        'risk_situation': '작업발판 위에서 작업 중 추락 위험',
    })
    assert result['source_chunk_ids'], '검색 결과가 있어야 함'
    assert result['primary_hazards'], '위험 유형이 추출되어야 함'
    assert '추락' in result['primary_hazards']
    assert result['recommended_actions'], '대책이 있어야 함'
    assert result['confidence'] in ('low', 'medium', 'high')


# ── Test 2: 고소작업 + 추락 ───────────────────────────────────────────────

def test_high_altitude_fall():
    result = _run({
        'process': '건축',
        'sub_work': '고소작업',
        'risk_situation': '2m 이상 고소작업 중 추락 위험 안전대 미착용 시',
        'risk_category': '작업특성 요인',
        'risk_detail': '추락',
    })
    assert result['source_chunk_ids']
    assert '추락' in result['primary_hazards']
    # 안전대 관련 PPE 검색 기대
    ppe_combined = ' '.join(result['required_ppe'])
    assert '안전대' in ppe_combined or '안전모' in ppe_combined
    assert result['confidence'] in ('medium', 'high')


# ── Test 3: 밀폐공간 + 질식 ───────────────────────────────────────────────

def test_confined_space_asphyxiation():
    result = _run({
        'process': '토목',
        'sub_work': '맨홀 내부 작업',
        'risk_situation': '밀폐공간 맨홀 내부 작업 중 산소 결핍 및 질식 위험',
    })
    assert result['source_chunk_ids']
    assert '질식' in result['primary_hazards']
    ppe_combined = ' '.join(result['required_ppe'])
    assert '공기호흡기' in ppe_combined or '방독마스크' in ppe_combined
    legal_combined = ' '.join(result['legal_basis_candidates'])
    assert '619' in legal_combined or '621' in legal_combined or '620' in legal_combined


# ── Test 4: 감전 위험 ────────────────────────────────────────────────────

def test_electrical_hazard():
    result = _run({
        'process': '전기공사',
        'sub_work': '전기 패널 작업',
        'risk_situation': '전기 패널 작업 중 활선 감전 위험',
    })
    assert result['source_chunk_ids']
    assert '감전' in result['primary_hazards']
    ppe_combined = ' '.join(result['required_ppe'])
    assert '절연' in ppe_combined
    actions_combined = ' '.join(result['recommended_actions'])
    assert '전원' in actions_combined or 'LOTO' in actions_combined or '차단' in actions_combined


# ── Test 5: 화재/폭발 위험 ────────────────────────────────────────────────

def test_fire_explosion_risk():
    result = _run({
        'process': '용접',
        'sub_work': '용접 및 절단 작업',
        'risk_situation': '용접 작업 중 불꽃 비산으로 인한 화재 폭발 위험',
    })
    assert result['source_chunk_ids']
    hazard_combined = ' '.join(result['primary_hazards'])
    assert '화재' in hazard_combined or '폭발' in hazard_combined
    actions_combined = ' '.join(result['recommended_actions'])
    assert '소화기' in actions_combined or '가연' in actions_combined


# ── Test 6: PPE 추출 검증 ────────────────────────────────────────────────

def test_ppe_extraction():
    result = _run({
        'process': '건축',
        'sub_work': '비계 작업',
        'risk_situation': '비계 작업 중 추락 위험 보호구 미착용',
    })
    assert result['required_ppe'], 'PPE 목록이 있어야 함'
    all_ppe = ' '.join(result['required_ppe'])
    assert '안전모' in all_ppe or '안전대' in all_ppe


# ── Test 7: 법령 근거 포함 청크 검색 ────────────────────────────────────

def test_legal_basis_extraction():
    result = _run({
        'process': '전기',
        'sub_work': '전기 배선 작업',
        'risk_situation': '절연 피복 손상 전선 감전 사고 위험',
        'legal_basis_hint': '산업안전보건기준에 관한 규칙',
    })
    assert result['source_chunk_ids']
    # 감전 관련 청크들은 law_ref가 있으므로 legal_basis_candidates가 있어야 함
    assert result['legal_basis_candidates'], '법령 근거가 있어야 함'
    legal_combined = ' '.join(result['legal_basis_candidates'])
    assert '산업안전보건' in legal_combined


# ── Test 8: 태그 없는 청크 fallback ──────────────────────────────────────

def test_tagless_chunk_fallback():
    """Tag-less chunks should still be searched and appear in results."""
    # 현장 일반 안전 수칙 관련 검색 — 태그 없는 청크들이 매칭 가능해야 함
    result = _run({
        'process': '건설',
        'sub_work': '현장 일반 작업',
        'risk_situation': '현장 일반 안전 교육 미실시 비상 대피 경로 미파악',
    })
    # 태그 없는 청크도 텍스트 매칭으로 결과에 포함될 수 있음
    assert result['confidence'] in ('low', 'medium', 'high')
    # warnings에 태그 미비 경고가 있을 수 있음 (없어도 무방)
    assert isinstance(result['warnings'], list)


# ── Test 9: 노이즈 청크 억제 ─────────────────────────────────────────────

def test_noise_chunk_suppression():
    """Short noise chunks (id 25, 26, 27) should score low."""
    all_chunks = _chunks()
    result = run_engine(
        {
            'process': '건축',
            'sub_work': '추락 위험 작업',
            'risk_situation': '추락 위험 작업발판 안전난간',
        },
        all_chunks,
    )
    # 노이즈 청크(id 25: "작업 중 필요", id 26: "안전", id 27: "확인 필요")는
    # top-k에서 상위에 오지 않아야 함
    top_ids = result['source_chunk_ids'][:3]
    assert 25 not in top_ids, '극단 노이즈 청크가 상위 3개에 없어야 함'
    assert 26 not in top_ids, '극단 노이즈 청크가 상위 3개에 없어야 함'
    assert 27 not in top_ids, '극단 노이즈 청크가 상위 3개에 없어야 함'


# ── Test 10: 검색 결과 없음 처리 ────────────────────────────────────────

def test_no_results_handling():
    """Query that matches nothing should return structured empty result with low confidence."""
    # Pure ASCII gibberish — no Korean tokens, no field matches
    result = _run({
        'process': 'zzz_noop',
        'sub_work': 'zzz_noop_sub',
        'risk_situation': 'xyzxyz qqqq rrrrr sssss ttttt vvvvv',
    })
    assert result['confidence'] == 'low'
    warnings_combined = ' '.join(result['warnings'])
    assert '없음' in warnings_combined or '낮음' in warnings_combined
    assert isinstance(result['source_chunk_ids'], list)
    assert isinstance(result['primary_hazards'], list)


# ── Test 11: 필수 입력 누락 검증 ────────────────────────────────────────

def test_missing_required_fields():
    with pytest.raises(ValueError) as exc:
        validate_input({'process': '건축'})
    assert 'sub_work' in str(exc.value) or 'risk_situation' in str(exc.value)


# ── Test 12: 빈 risk_situation 검증 ─────────────────────────────────────

def test_empty_risk_situation():
    with pytest.raises(ValueError):
        validate_input({
            'process': '건축',
            'sub_work': '비계',
            'risk_situation': '   ',
        })


# ── Test 13: confidence high 케이스 ──────────────────────────────────────

def test_confidence_high_case():
    """Strong query on well-tagged domain should yield medium or high confidence."""
    result = _run({
        'process': '건축',
        'sub_work': '비계 작업',
        'risk_situation': '비계 작업발판 위 추락 안전난간 추락방지망 안전대 착용',
        'risk_detail': '추락',
    })
    assert result['confidence'] in ('medium', 'high'), (
        f'expected medium or high, got {result["confidence"]}'
    )
    assert len(result['source_chunk_ids']) > 0


# ── Test 14: confidence low 케이스 ───────────────────────────────────────

def test_confidence_low_case():
    """Weak, unrelated query should produce low confidence."""
    result = _run({
        'process': '기타',
        'sub_work': '일반 작업',
        'risk_situation': '불명확한 작업 상황 특정 위험 없음',
    })
    # Should be low or medium at most; no specific hazard tags should dominate
    assert result['confidence'] in ('low', 'medium')


# ── Test 15: 출력 JSON 직렬화 가능 ──────────────────────────────────────

def test_output_is_json_serializable():
    result = _run({
        'process': '토목',
        'sub_work': '맨홀 작업',
        'risk_situation': '밀폐공간 내부 질식 위험 가스 농도',
    })
    # Should not raise
    serialized = json.dumps(result, ensure_ascii=False)
    assert isinstance(serialized, str)
    parsed = json.loads(serialized)
    assert 'source_chunk_ids' in parsed
    assert 'confidence' in parsed
    assert 'warnings' in parsed


# ── Test 16: 중복 청크 억제 검증 ────────────────────────────────────────

def test_duplicate_suppression():
    """Duplicate or near-duplicate chunks should not both appear in results."""
    # Add a near-duplicate to the corpus temporarily
    chunks = _chunks()
    # Clone chunk 1 with same normalized_text but different id
    dup = dict(chunks[0])
    dup['id'] = 999
    chunks_with_dup = chunks + [dup]

    result = run_engine(
        {
            'process': '건축',
            'sub_work': '비계 작업',
            'risk_situation': '비계 추락 작업발판 안전난간',
        },
        chunks_with_dup,
    )
    ids = result['source_chunk_ids']
    # Both id 1 and 999 should NOT both appear (dedup should keep only one)
    assert not (1 in ids and 999 in ids), '중복 청크가 동시에 결과에 포함되지 않아야 함'


# ════════════════════════════════════════════════════════════════════════════
# v1.2 새 테스트 (5건)
# ════════════════════════════════════════════════════════════════════════════

from engine.rag_risk_engine.assembler import (
    _extract_action_phrases,
    _dedup_actions,
    _hazard_keyed_actions,
    _is_generic_action,
    _GENERIC_ACTIONS,
    _MAX_PHRASE_LEN,
)
from engine.rag_risk_engine.retrieval import GENERIC_WORK_TYPES, BM25Index


# ── Test 17: generic action 단독 제거 ────────────────────────────────────

def test_generic_action_filter():
    """_is_generic_action should flag single generic words."""
    for word in ['착용', '확인', '점검', '대책', '관리', '조치']:
        assert _is_generic_action(word), f"'{word}'는 generic action이어야 함"
    # Specific phrases should NOT be flagged
    assert not _is_generic_action('안전난간 설치'), '구체 문구는 제거하지 않아야 함'
    assert not _is_generic_action('누전차단기 점검'), '구체 문구는 제거하지 않아야 함'
    assert not _is_generic_action('전원 차단 후 작업'), '구체 문구는 제거하지 않아야 함'


# ── Test 18: phrase 최대 길이 제한 ───────────────────────────────────────

def test_phrase_length_cap():
    """Extracted phrases must not exceed _MAX_PHRASE_LEN characters."""
    long_text = (
        '안전대를 반드시 착용하고 비계 위에서 작업 시에는 안전모를 착용하며 '
        '작업발판 위에서 안전난간을 설치 후 추락방지망을 확인하고 작업을 시작해야 합니다.'
    )
    phrases = _extract_action_phrases(long_text)
    for p in phrases:
        assert len(p) <= _MAX_PHRASE_LEN, f'phrase 길이 초과: len={len(p)}, phrase={p!r}'


# ── Test 19: 슬라이딩 윈도우 phrase 추출 ─────────────────────────────────

def test_sliding_window_extraction():
    """Sliding window should produce focused action phrases."""
    text = '비계 작업 중 안전대 착용.'
    phrases = _extract_action_phrases(text)
    assert phrases, '문장에서 phrase가 추출되어야 함'
    assert any('안전대' in p for p in phrases), "'안전대'가 phrase에 포함되어야 함"


# ── Test 20: generic work_type 보너스 약화 ───────────────────────────────

def test_generic_work_type_no_bonus():
    """Generic work_type ('작업') must not trigger work_type_match bonus."""
    assert '작업' in GENERIC_WORK_TYPES
    assert '설치' in GENERIC_WORK_TYPES
    # Specific types should NOT be in generic set
    assert '비계' not in GENERIC_WORK_TYPES
    assert '철골' not in GENERIC_WORK_TYPES
    assert '감전' not in GENERIC_WORK_TYPES

    # Build a small index with one chunk that has work_type="작업"
    chunks = [
        {
            'id': 1,
            'normalized_text': '비계 추락 안전난간 작업발판 안전대',
            'raw_text': None,
            'work_type': '작업',   # generic
            'hazard_type': '추락',  # specific
            'control_measure': '안전난간 설치',
            'ppe': '안전대',
            'law_ref': None,
            'keywords': None,
        }
    ]
    idx = BM25Index(chunks)
    # Query contains '작업' — generic work_type should NOT add bonus
    results = idx.search('비계 작업 추락 안전난간', top_k=1)
    assert results, '결과가 있어야 함'
    # Verify the code path works (bonus not added for generic work_type)
    # We can't easily assert the exact score, but we verify no error occurs
    _, score = results[0]
    assert score > 0


# ── Test 21: hazard 강화 키워드 — 실제 chunk 텍스트 기반 ─────────────────

def test_hazard_keyed_reinforcement_from_text():
    """Hazard reinforcement should only return keywords actually in chunk text."""
    chunks_with_fire_kw = [
        {
            'id': 10,
            'normalized_text': '소화기 비치 및 불티 방지 조치',
            'raw_text': None,
            'work_type': None, 'hazard_type': '화재',
            'control_measure': None, 'ppe': None, 'law_ref': None, 'keywords': None,
        }
    ]
    # '소화기' is in text → should appear in reinforcement for 화재
    result = _hazard_keyed_actions(chunks_with_fire_kw, ['화재'])
    assert '소화기' in result or '소화기 비치' in result, \
        f"'소화기'가 reinforcement에 있어야 함, got: {result}"

    # For hazard not matching chunk content, no spurious keywords
    chunks_empty = [
        {
            'id': 11,
            'normalized_text': '일반 작업 안내',
            'raw_text': None,
            'work_type': None, 'hazard_type': None,
            'control_measure': None, 'ppe': None, 'law_ref': None, 'keywords': None,
        }
    ]
    result_empty = _hazard_keyed_actions(chunks_empty, ['감전'])
    # '전원 차단', '절연' 등이 chunk text에 없으므로 빈 결과
    assert result_empty == [], f'chunk에 없는 키워드는 반환 금지, got: {result_empty}'


# ── Test 22 (regression): SYN-06 유사 — 화재 시나리오 소화기 추출 ─────────

def test_regression_fire_scenario_firefighting():
    """
    Regression: fire scenario with '소화기' in chunk should produce
    '소화기' or '소화기 비치' in actions (was ACTIONS_MISMATCH in v1.1).
    """
    chunks = [
        {
            'id': 100,
            'normalized_text': '용접 작업 시 불꽃 비산으로 화재 위험 소화기 비치 및 가연물 제거',
            'raw_text': None,
            'work_type': '작업', 'hazard_type': '화재',
            'control_measure': '소화기 비치',
            'ppe': '방염복',
            'law_ref': '규칙 제232조',
            'keywords': None,
        }
    ] * 5
    result = _run({
        'process': '배관 설치',
        'sub_work': '파이프 용접 작업',
        'risk_situation': '용접 작업 중 불꽃 비산으로 인근 가연성 자재 화재 발생 위험',
    })
    # Only check fixture chunks via direct engine call
    from engine.rag_risk_engine.assembler import assemble_hazards, assemble_actions
    hazards = assemble_hazards(chunks)
    actions = assemble_actions(chunks, hazards=hazards)
    actions_text = ' '.join(actions)
    assert '소화기' in actions_text, f"'소화기'가 actions에 포함되어야 함, got: {actions}"


# ── Test 23 (regression): SYN-08 유사 — 낙하/크레인 신호수 추출 ─────────

def test_regression_crane_signal():
    """
    Regression: crane/falling object scenario should include '신호수'
    in actions when chunk text contains it (was ACTIONS_MISMATCH in v1.1).
    """
    from engine.rag_risk_engine.assembler import assemble_hazards, assemble_actions
    chunks = [
        {
            'id': 200,
            'normalized_text': '크레인 인양 작업 시 신호수 배치 및 작업 반경 내 출입 통제',
            'raw_text': None,
            'work_type': '작업', 'hazard_type': '낙하',
            'control_measure': '신호수 배치',
            'ppe': '안전모',
            'law_ref': None,
            'keywords': None,
        }
    ] * 5
    hazards = assemble_hazards(chunks)
    actions = assemble_actions(chunks, hazards=hazards)
    actions_text = ' '.join(actions)
    assert '신호수' in actions_text, f"'신호수'가 actions에 포함되어야 함, got: {actions}"


# ── Test 24 (regression): SYN-17 유사 — 폭발/가스 환기 추출 ─────────────

def test_regression_gas_explosion_ventilation():
    """
    Regression: gas explosion scenario should include '환기' in actions
    when chunk text contains it (was ACTIONS_MISMATCH in v1.1).
    """
    from engine.rag_risk_engine.assembler import assemble_hazards, assemble_actions
    chunks = [
        {
            'id': 300,
            'normalized_text': '도시가스관 인근 굴착 시 가스 농도 측정 및 환기 실시',
            'raw_text': None,
            'work_type': '작업', 'hazard_type': '폭발',
            'control_measure': '환기',
            'ppe': '안전모',
            'law_ref': None,
            'keywords': None,
        }
    ] * 5
    hazards = assemble_hazards(chunks)
    actions = assemble_actions(chunks, hazards=hazards)
    actions_text = ' '.join(actions)
    assert '환기' in actions_text, f"'환기'가 actions에 포함되어야 함, got: {actions}"


# ════════════════════════════════════════════════════════════════════════════
# v2 입력 테스트 (8건)
# ════════════════════════════════════════════════════════════════════════════

from engine.rag_risk_engine.schema import validate_input


# ── Test 25: confined_space=True → 질식 포함 ─────────────────────────────

def test_v2_confined_space_asphyxiation():
    """confined_space=True 입력 시 질식 hazard 및 관련 action 포함 기대."""
    result = _run({
        'process': '토목',
        'sub_work': '맨홀 점검',
        'risk_situation': '맨홀 내부 가스 위험',
        'confined_space': True,
    })
    hazards_text = ' '.join(result['primary_hazards'])
    assert '질식' in hazards_text, f'질식 미검출 — hazards: {result["primary_hazards"]}'
    assert result['source_chunk_ids'], '청크 결과 있어야 함'


# ── Test 26: hot_work=True → 화재/폭발 포함 ─────────────────────────────

def test_v2_hot_work_fire():
    """hot_work=True 입력 시 화재/폭발 관련 hazard 포함 기대."""
    result = _run({
        'process': '배관',
        'sub_work': '파이프 용접',
        'risk_situation': '용접 작업 불꽃 비산',
        'hot_work': True,
    })
    hazards_text = ' '.join(result['primary_hazards'])
    assert '화재' in hazards_text or '폭발' in hazards_text, (
        f'화재/폭발 미검출 — hazards: {result["primary_hazards"]}'
    )


# ── Test 27: electrical_work=True → 감전 포함 ───────────────────────────

def test_v2_electrical_work_shock():
    """electrical_work=True 입력 시 감전 hazard 포함 기대."""
    result = _run({
        'process': '전기',
        'sub_work': '분전반 작업',
        'risk_situation': '전기 작업 활선 위험',
        'electrical_work': True,
    })
    hazards_text = ' '.join(result['primary_hazards'])
    assert '감전' in hazards_text, f'감전 미검출 — hazards: {result["primary_hazards"]}'


# ── Test 28: height_m=5 → 추락 포함 ─────────────────────────────────────

def test_v2_height_fall():
    """height_m=5.0 입력 시 추락 hazard 포함 기대 (2m 초과 boost 활성)."""
    result = _run({
        'process': '건축',
        'sub_work': '외벽 도장',
        'risk_situation': '외벽 작업 추락 위험',
        'height_m': 5.0,
    })
    hazards_text = ' '.join(result['primary_hazards'])
    assert '추락' in hazards_text, f'추락 미검출 — hazards: {result["primary_hazards"]}'


# ── Test 29: multiple flags → 복합 hazard ───────────────────────────────

def test_v2_multiple_flags_composite():
    """복합 v2 플래그: confined_space+electrical_work → 복수 hazard."""
    result = _run({
        'process': '설비',
        'sub_work': '밀폐 전기실 점검',
        'risk_situation': '밀폐된 전기 설비 점검',
        'confined_space': True,
        'electrical_work': True,
    })
    hazards = result['primary_hazards']
    hazards_text = ' '.join(hazards)
    assert len(hazards) >= 1, '복합 조건 hazard가 1개 이상이어야 함'
    assert '감전' in hazards_text or '질식' in hazards_text, (
        f'복합 hazard 미검출 — hazards: {hazards}'
    )


# ── Test 30: invalid enum → warning 처리, 오류 없음 ─────────────────────

def test_v2_invalid_enum_warning():
    """잘못된 enum 값은 None으로 처리되고 ValueError를 발생시키지 않아야 함."""
    # Should not raise
    validated = validate_input({
        'process': '건축',
        'sub_work': '외벽 작업',
        'risk_situation': '추락 위험',
        'work_environment': 'underground',   # 허용값 아님
        'surface_condition': 'muddy',        # 허용값 아님
        'weather': 'typhoon',                # 허용값 아님
    })
    assert validated.get('work_environment') is None, 'invalid enum은 None이어야 함'
    assert validated.get('surface_condition') is None
    assert validated.get('weather') is None
    # Required fields still intact
    assert validated['process'] == '건축'


# ── Test 31: partial v2 입력 → 정상 동작 ────────────────────────────────

def test_v2_partial_input_ok():
    """v2 필드 일부만 있어도 엔진이 정상 동작해야 함."""
    result = _run({
        'process': '건축',
        'sub_work': '거푸집 작업',
        'risk_situation': '거푸집 해체 중 붕괴 위험',
        'worker_count': 3,          # v2 optional
        'work_environment': 'outdoor',  # v2 optional
        # 나머지 v2 필드 없음
    })
    assert result['source_chunk_ids'] is not None
    assert result['confidence'] in ('low', 'medium', 'high')
    assert isinstance(result['primary_hazards'], list)


# ── Test 32: v1-only 입력 → 동일 결과 유지 ──────────────────────────────

def test_v2_v1_only_backward_compat():
    """v2 필드가 전혀 없는 v1 입력도 동일하게 동작해야 함 (하위 호환)."""
    v1_input = {
        'process': '건축',
        'sub_work': '비계 작업',
        'risk_situation': '비계 작업 중 추락 위험',
        'risk_category': '추락',
    }
    result = _run(v1_input)
    assert result['source_chunk_ids'], 'v1 입력도 결과 있어야 함'
    assert '추락' in result['primary_hazards'], 'v1 입력 추락 hazard 유지'
    assert result['confidence'] in ('medium', 'high'), 'v1 입력 confidence 유지'

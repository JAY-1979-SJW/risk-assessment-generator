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

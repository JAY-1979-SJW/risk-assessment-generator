"""
Service & mapper integration tests for the KRAS connector layer.
Run: pytest engine/kras_connector/tests/test_service.py -v

DB not required for mapper tests. DB required for integration tests
(mark with @pytest.mark.integration and set KRAS_DB_URL).
"""

import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

from engine.kras_connector.mapper import map_row_to_input


# ── 1. 정상 입력 매핑 ─────────────────────────────────────────────────────

class TestMapper(unittest.TestCase):

    def _good_row(self, **overrides):
        base = {
            'id': 1,
            'project_id': 1,
            'process': '고소작업',
            'sub_work': '천장 배관 설치',
            'risk_category': '추락',
            'risk_detail': '이동식비계',
            'risk_situation': '이동식 비계에서 천장 배관 설치 작업 중 추락 위험',
            'legal_basis': '산업안전보건법 제38조',
            'current_measures': '안전난간 설치',
        }
        base.update(overrides)
        return base

    def test_normal_mapping(self):
        inp = map_row_to_input(self._good_row())
        self.assertEqual(inp['process'], '고소작업')
        self.assertEqual(inp['sub_work'], '천장 배관 설치')
        self.assertEqual(inp['risk_situation'], '이동식 비계에서 천장 배관 설치 작업 중 추락 위험')
        self.assertEqual(inp['risk_category'], '추락')
        self.assertEqual(inp['risk_detail'], '이동식비계')
        self.assertEqual(inp['current_measures'], '안전난간 설치')
        self.assertEqual(inp['legal_basis_hint'], '산업안전보건법 제38조')
        self.assertEqual(inp['top_k'], 10)

    def test_optional_fields_none(self):
        row = self._good_row(risk_category=None, risk_detail='', legal_basis=None)
        inp = map_row_to_input(row)
        self.assertIsNone(inp['risk_category'])
        self.assertIsNone(inp['risk_detail'])
        self.assertIsNone(inp['legal_basis_hint'])

    # ── 2. blank risk_situation 차단 ─────────────────────────────────────

    def test_blank_risk_situation_raises(self):
        with self.assertRaises(ValueError) as ctx:
            map_row_to_input(self._good_row(risk_situation=''))
        self.assertIn('risk_situation', str(ctx.exception))

    def test_whitespace_risk_situation_raises(self):
        with self.assertRaises(ValueError):
            map_row_to_input(self._good_row(risk_situation='   '))

    def test_none_risk_situation_raises(self):
        with self.assertRaises(ValueError):
            map_row_to_input(self._good_row(risk_situation=None))

    def test_blank_process_raises(self):
        with self.assertRaises(ValueError):
            map_row_to_input(self._good_row(process=''))

    def test_blank_sub_work_raises(self):
        with self.assertRaises(ValueError):
            map_row_to_input(self._good_row(sub_work=None))


# ── 3. 서비스 success 저장 ────────────────────────────────────────────────

class TestServiceSuccess(unittest.TestCase):

    def _make_chunks(self):
        return [{
            'id': 1,
            'normalized_text': '이동식 비계 추락 방지 안전난간 설치 안전모 착용',
            'raw_text': None,
            'work_type': '건축',
            'hazard_type': '추락',
            'control_measure': '안전난간 설치',
            'ppe': '안전모',
            'law_ref': None,
            'keywords': None,
            'trade_type': None,
            'tag_confidence': None,
        }] * 10

    @patch('engine.kras_connector.service.fetchone')
    @patch('engine.kras_connector.service._save_result')
    def test_success_flow(self, mock_save, mock_fetchone):
        mock_fetchone.return_value = {
            'id': 1, 'project_id': 1,
            'process': '고소작업', 'sub_work': '천장 배관 설치',
            'risk_situation': '이동식 비계에서 추락 위험',
            'risk_category': '추락', 'risk_detail': None,
            'current_measures': '', 'legal_basis': '',
        }
        mock_save.return_value = 42

        from engine.kras_connector.service import run_for_assessment
        result = run_for_assessment(
            assessment_id=1,
            chunks=self._make_chunks(),
            chunk_count_loaded=10,
            save=True,
        )
        self.assertEqual(result['status'], 'success')
        self.assertIsNotNone(result.get('confidence'))
        self.assertGreater(result.get('hazard_count', 0), 0)
        mock_save.assert_called_once()

    # ── 4. assessment not found ───────────────────────────────────────────

    @patch('engine.kras_connector.service.fetchone', return_value=None)
    def test_not_found(self, _):
        from engine.kras_connector.service import run_for_assessment
        result = run_for_assessment(assessment_id=9999, chunks=[], save=False)
        self.assertEqual(result['status'], 'not_found')

    # ── 5. storage failure ────────────────────────────────────────────────

    @patch('engine.kras_connector.service.fetchone')
    @patch('engine.kras_connector.service._save_result', side_effect=Exception('DB down'))
    def test_storage_failure(self, mock_save, mock_fetchone):
        mock_fetchone.return_value = {
            'id': 1, 'project_id': 1,
            'process': '고소작업', 'sub_work': '천장 배관 설치',
            'risk_situation': '이동식 비계에서 추락 위험',
            'risk_category': None, 'risk_detail': None,
            'current_measures': None, 'legal_basis': None,
        }
        from engine.kras_connector.service import run_for_assessment
        result = run_for_assessment(
            assessment_id=1,
            chunks=self._make_chunks(),
            chunk_count_loaded=10,
            save=True,
        )
        self.assertEqual(result['status'], 'storage_error')
        self.assertIn('DB down', result['error'])


# ── 6. latest result 조회 (DB 불필요, SQL 검증만) ────────────────────────

class TestQueryFunctions(unittest.TestCase):

    @patch('engine.kras_connector.service.fetchone', return_value={'id': 5, 'status': 'success'})
    def test_get_latest_result(self, mock_fetch):
        from engine.kras_connector.service import get_latest_result
        row = get_latest_result(1)
        self.assertEqual(row['status'], 'success')
        call_args = mock_fetch.call_args[0]
        self.assertIn('ORDER BY executed_at DESC', call_args[0])
        self.assertIn('LIMIT 1', call_args[0])

    @patch('engine.kras_connector.service.fetchall', return_value=[
        {'id': 2, 'status': 'success'},
        {'id': 1, 'status': 'invalid_input'},
    ])
    def test_get_result_history(self, mock_fetch):
        from engine.kras_connector.service import get_result_history
        rows = get_result_history(1)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['status'], 'success')


# ════════════════════════════════════════════════════════════════════════════
# v2 mapper 테스트
# ════════════════════════════════════════════════════════════════════════════

class TestMapperV2(unittest.TestCase):

    def _base_row(self):
        return {
            'id': 1, 'project_id': 1,
            'process': '건축', 'sub_work': '외벽 작업',
            'risk_situation': '고소 외벽 작업 중 추락 위험',
            'legal_basis': None, 'current_measures': None,
            'risk_category': None, 'risk_detail': None,
        }

    def test_v2_bool_fields_true(self):
        row = {**self._base_row(), 'confined_space': True, 'hot_work': True}
        inp = map_row_to_input(row)
        self.assertTrue(inp['confined_space'])
        self.assertTrue(inp['hot_work'])

    def test_v2_bool_fields_false(self):
        row = {**self._base_row(), 'electrical_work': False}
        inp = map_row_to_input(row)
        self.assertFalse(inp['electrical_work'])

    def test_v2_height_m_valid(self):
        row = {**self._base_row(), 'height_m': 3.5}
        inp = map_row_to_input(row)
        self.assertAlmostEqual(inp['height_m'], 3.5)

    def test_v2_height_m_negative_dropped(self):
        row = {**self._base_row(), 'height_m': -1.0}
        inp = map_row_to_input(row)
        self.assertIsNone(inp.get('height_m'))

    def test_v2_worker_count_valid(self):
        row = {**self._base_row(), 'worker_count': 5}
        inp = map_row_to_input(row)
        self.assertEqual(inp['worker_count'], 5)

    def test_v2_work_environment_valid(self):
        row = {**self._base_row(), 'work_environment': 'outdoor'}
        inp = map_row_to_input(row)
        self.assertEqual(inp['work_environment'], 'outdoor')

    def test_v2_invalid_enum_becomes_none(self):
        row = {**self._base_row(), 'work_environment': 'underground'}
        inp = map_row_to_input(row)
        self.assertIsNone(inp.get('work_environment'))

    def test_v2_no_v2_fields_backward_compat(self):
        """v2 컬럼 없는 row는 v1 결과와 동일해야 함."""
        row = self._base_row()
        inp = map_row_to_input(row)
        self.assertIn('process', inp)
        self.assertIn('risk_situation', inp)
        self.assertNotIn('confined_space', inp)
        self.assertNotIn('height_m', inp)


if __name__ == '__main__':
    unittest.main(verbosity=2)

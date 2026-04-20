"""
KRAS Assessment Engine Service.

Full flow:
  assessment_id → DB row → mapper → validator → KOSHA loader → engine → save → status
"""

import json
import logging
import traceback
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from engine.kras_connector.db import fetchone, fetchall, execute
from engine.kras_connector.mapper import map_row_to_input
from engine.kras_connector.kosha_loader import load_kosha_chunks
from engine.rag_risk_engine.engine import run_engine

logger = logging.getLogger(__name__)

ENGINE_VERSION = 'v1.1'


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f'Object of type {type(obj).__name__} is not JSON serializable')


def _to_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=_json_default)

STATUS_SUCCESS = 'success'
STATUS_INVALID_INPUT = 'invalid_input'
STATUS_ENGINE_ERROR = 'engine_error'
STATUS_STORAGE_ERROR = 'storage_error'
STATUS_NOT_FOUND = 'not_found'


def run_for_assessment(
    assessment_id: int,
    chunks: Optional[List[Dict[str, Any]]] = None,
    chunk_count_loaded: Optional[int] = None,
    save: bool = True,
) -> Dict[str, Any]:
    """
    Execute the RAG engine for a single project_assessments row.

    Returns:
        {assessment_id, status, confidence, hazard_count, action_count,
         source_chunk_ids, output_json, error, result_id}
    """
    result_base = {'assessment_id': assessment_id, 'result_id': None, 'error': None}

    # 1. assessment 조회
    row = fetchone('SELECT * FROM project_assessments WHERE id = %s', (assessment_id,))
    if row is None:
        return {**result_base, 'status': STATUS_NOT_FOUND,
                'error': f'assessment_id={assessment_id} 를 찾을 수 없습니다'}

    # 2. 입력 매핑 + 유효성 검사
    try:
        engine_input = map_row_to_input(row)
    except ValueError as exc:
        err_msg = str(exc)
        if save:
            _save_result(assessment_id, dict(row), None,
                         STATUS_INVALID_INPUT, err_msg, chunk_count_loaded)
        return {**result_base, 'status': STATUS_INVALID_INPUT, 'error': err_msg}

    # 3. KOSHA 청크 로드 (사전 로드 없으면 여기서 로드)
    if chunks is None:
        try:
            chunks, chunk_count_loaded = load_kosha_chunks()
        except Exception as exc:
            err_msg = f'KOSHA 청크 로드 실패: {exc}'
            logger.error(err_msg)
            if save:
                _save_result(assessment_id, engine_input, None,
                             STATUS_ENGINE_ERROR, err_msg, chunk_count_loaded)
            return {**result_base, 'status': STATUS_ENGINE_ERROR, 'error': err_msg}

    if not chunks:
        err_msg = 'KOSHA 청크가 비어 있습니다'
        if save:
            _save_result(assessment_id, engine_input, None,
                         STATUS_ENGINE_ERROR, err_msg, chunk_count_loaded)
        return {**result_base, 'status': STATUS_ENGINE_ERROR, 'error': err_msg}

    # 4. 엔진 실행
    try:
        output = run_engine(engine_input, chunks)
    except Exception as exc:
        err_msg = f'엔진 실행 오류: {exc}'
        logger.error('%s\n%s', err_msg, traceback.format_exc())
        if save:
            _save_result(assessment_id, engine_input, None,
                         STATUS_ENGINE_ERROR, err_msg, chunk_count_loaded)
        return {**result_base, 'status': STATUS_ENGINE_ERROR, 'error': err_msg}

    # 5. 결과 저장
    result_id = None
    if save:
        try:
            result_id = _save_result(
                assessment_id, engine_input, output,
                STATUS_SUCCESS, None, chunk_count_loaded
            )
        except Exception as exc:
            err_msg = f'결과 저장 실패: {exc}'
            logger.error(err_msg)
            return {
                **result_base,
                'status': STATUS_STORAGE_ERROR,
                'error': err_msg,
                'output_json': output,
                'confidence': output.get('confidence'),
                'hazard_count': len(output.get('primary_hazards', [])),
                'action_count': len(output.get('recommended_actions', [])),
                'source_chunk_ids': output.get('source_chunk_ids', []),
            }

    return {
        'assessment_id': assessment_id,
        'status': STATUS_SUCCESS,
        'confidence': output.get('confidence'),
        'hazard_count': len(output.get('primary_hazards', [])),
        'action_count': len(output.get('recommended_actions', [])),
        'source_chunk_ids': output.get('source_chunk_ids', []),
        'output_json': output,
        'error': None,
        'result_id': result_id,
    }


def _save_result(
    assessment_id: int,
    input_snapshot: dict,
    output: Optional[dict],
    status: str,
    error_message: Optional[str],
    chunk_count: Optional[int],
) -> int:
    source_chunk_ids = output.get('source_chunk_ids', []) if output else []
    confidence = output.get('confidence') if output else None
    warnings = output.get('warnings', []) if output else []

    return execute(
        """
        INSERT INTO assessment_engine_results
          (assessment_id, engine_version, input_snapshot, output_json,
           source_chunk_ids, confidence, warnings,
           chunk_count_loaded, status, error_message)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            assessment_id,
            ENGINE_VERSION,
            _to_json(input_snapshot),
            _to_json(output) if output else None,
            source_chunk_ids,
            confidence,
            warnings,
            chunk_count,
            status,
            error_message,
        )
    )


# ── 조회 함수 ─────────────────────────────────────────────────────────────

def get_latest_result(assessment_id: int) -> Optional[Dict[str, Any]]:
    """assessment_id 기준 가장 최신 결과 1건 조회."""
    return fetchone(
        """
        SELECT * FROM assessment_engine_results
        WHERE assessment_id = %s
        ORDER BY executed_at DESC
        LIMIT 1
        """,
        (assessment_id,)
    )


def get_result_history(assessment_id: int) -> List[Dict[str, Any]]:
    """assessment_id 기준 전체 실행 이력 조회 (최신순)."""
    return fetchall(
        """
        SELECT id, assessment_id, engine_version, confidence, status,
               source_chunk_ids, warnings, chunk_count_loaded, executed_at, error_message
        FROM assessment_engine_results
        WHERE assessment_id = %s
        ORDER BY executed_at DESC
        """,
        (assessment_id,)
    )

"""
Engine result read-only endpoints.

GET /api/assessments/{aid}/engine/latest  → 최신 엔진 실행 결과 1건
GET /api/assessments/{aid}/engine/history → 전체 실행 이력 (요약 리스트)

설계 원칙:
- 엔진 재실행 없음 — assessment_engine_results 테이블에서 읽기만 함
- assessment_id 존재 여부는 별도 검증 안 함 (결과 없으면 404로 충분)
"""

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from db import fetchall, fetchone

router = APIRouter(prefix="/assessments", tags=["engine-results"])


def _parse_json_field(val: Any) -> Any:
    """JSONB 컬럼은 psycopg2가 이미 dict로 반환하지만, str인 경우 파싱."""
    if val is None:
        return None
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, ValueError):
            return val
    return val


@router.get("/{aid}/engine/latest")
def get_engine_latest(aid: int):
    """
    assessment_id 기준 가장 최신 엔진 실행 결과 1건 반환.

    Returns:
        200: 결과 있음 (status 필드 포함)
        404: 실행 이력 없음
    """
    row = fetchone(
        """
        SELECT id, assessment_id, engine_version,
               input_snapshot, output_json,
               source_chunk_ids, confidence, warnings,
               chunk_count_loaded, executed_at, status, error_message
        FROM assessment_engine_results
        WHERE assessment_id = %s
        ORDER BY executed_at DESC
        LIMIT 1
        """,
        (aid,),
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"assessment_id={aid} 에 대한 엔진 실행 결과가 없습니다.",
        )

    return _format_result_row(row)


@router.get("/{aid}/engine/history")
def get_engine_history(aid: int):
    """
    assessment_id 기준 전체 실행 이력 리스트 (최신순).
    output_json은 포함하지 않음 (용량 절감).

    Returns:
        {assessment_id, count, history: [{id, executed_at, confidence, status, ...}]}
    """
    rows = fetchall(
        """
        SELECT id, assessment_id, engine_version,
               confidence, status, error_message,
               source_chunk_ids, warnings, chunk_count_loaded, executed_at
        FROM assessment_engine_results
        WHERE assessment_id = %s
        ORDER BY executed_at DESC
        """,
        (aid,),
    )

    history = []
    for row in rows:
        history.append({
            "result_id":          row["id"],
            "assessment_id":      row["assessment_id"],
            "engine_version":     row["engine_version"],
            "status":             row["status"],
            "confidence":         row["confidence"],
            "error_message":      row["error_message"],
            "source_chunk_count": len(row["source_chunk_ids"] or []),
            "chunk_count_loaded": row["chunk_count_loaded"],
            "warnings":           list(row["warnings"] or []),
            "executed_at":        row["executed_at"].isoformat() if row["executed_at"] else None,
        })

    return {
        "assessment_id": aid,
        "count": len(history),
        "history": history,
    }


def _format_result_row(row: Dict[str, Any]) -> Dict[str, Any]:
    output = _parse_json_field(row.get("output_json"))
    input_snap = _parse_json_field(row.get("input_snapshot"))

    base = {
        "result_id":          row["id"],
        "assessment_id":      row["assessment_id"],
        "engine_version":     row["engine_version"],
        "status":             row["status"],
        "confidence":         row["confidence"],
        "error_message":      row["error_message"],
        "source_chunk_ids":   list(row["source_chunk_ids"] or []),
        "chunk_count_loaded": row["chunk_count_loaded"],
        "warnings":           list(row["warnings"] or []),
        "executed_at":        row["executed_at"].isoformat() if row["executed_at"] else None,
        "input_snapshot":     input_snap,
        "output":             output,
    }

    # output_json에서 핵심 필드를 최상위로 노출 (편의용)
    if output and isinstance(output, dict):
        base["primary_hazards"]      = output.get("primary_hazards", [])
        base["recommended_actions"]  = output.get("recommended_actions", [])
        base["required_ppe"]         = output.get("required_ppe", [])
        base["legal_basis_candidates"] = output.get("legal_basis_candidates", [])

    return base

"""
Chunk loader: DB (PostgreSQL via SSH tunnel) or local JSON file.
Engine is source-agnostic; loader returns List[dict] of chunk records.
"""

import json
import os
from typing import Any, Dict, List, Optional


# ── Local JSON loader ──────────────────────────────────────────────────────

def load_from_json(path: str) -> List[Dict[str, Any]]:
    """Load chunks from a JSON file (array of chunk dicts)."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f'청크 파일을 찾을 수 없습니다: {path}')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError('청크 파일은 JSON 배열이어야 합니다.')
    return data


# ── DB loader ─────────────────────────────────────────────────────────────

def load_from_db(limit: int = 5000) -> List[Dict[str, Any]]:
    """
    Load chunks from PostgreSQL (common_data DB via SSH tunnel on port 5435).
    Requires the SSH tunnel to be active.
    Falls back to empty list on connection failure so engine can still
    operate in local-only mode.
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        raise RuntimeError('psycopg2가 설치되어 있지 않습니다.')

    db_host = os.getenv('KOSHA_DB_HOST', '127.0.0.1')
    db_port = int(os.getenv('KOSHA_DB_PORT', '5435'))
    db_name = os.getenv('KOSHA_DB_NAME', 'common_data')
    db_user = os.getenv('KOSHA_DB_USER', 'common_admin')
    db_pass = os.getenv('KOSHA_DB_PASS', '')

    conn = psycopg2.connect(
        host=db_host, port=db_port,
        dbname=db_name, user=db_user, password=db_pass,
        connect_timeout=5,
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    kmc.id,
                    kmc.normalized_text,
                    kmc.raw_text,
                    kmc.work_type,
                    kmc.hazard_type,
                    kmc.control_measure,
                    kmc.ppe,
                    kmc.law_ref,
                    kmc.keywords,
                    kct.trade_type,
                    kct.confidence AS tag_confidence
                FROM kosha_material_chunks kmc
                LEFT JOIN kosha_chunk_tags kct ON kct.chunk_id = kmc.id
                WHERE kmc.normalized_text IS NOT NULL
                   OR kmc.raw_text IS NOT NULL
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Auto loader ───────────────────────────────────────────────────────────

_DEFAULT_CACHE = os.path.join(os.path.dirname(__file__), 'data', 'chunks_cache.json')


def load_chunks(
    source: Optional[str] = None,
    use_db: bool = False,
) -> List[Dict[str, Any]]:
    """
    Load chunks from the best available source.
    Priority:
      1. Explicit file path (source param)
      2. DB (if use_db=True)
      3. Local cache file (engine/rag_risk_engine/data/chunks_cache.json)

    Raises RuntimeError if no source is available.
    """
    if source:
        return load_from_json(source)

    if use_db:
        return load_from_db()

    if os.path.isfile(_DEFAULT_CACHE):
        return load_from_json(_DEFAULT_CACHE)

    raise RuntimeError(
        '청크 데이터 소스를 찾을 수 없습니다. '
        '--chunks 옵션으로 JSON 파일을 지정하거나 '
        '--use-db 옵션으로 DB 연결을 사용하세요.'
    )

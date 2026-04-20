"""
KRAS PostgreSQL connection for the engine connector layer.
Uses KRAS_DB_URL env var, falls back to DATABASE_URL.
"""

import os
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras


def _get_url() -> str:
    url = os.getenv('KRAS_DB_URL') or os.getenv('DATABASE_URL')
    if not url:
        raise RuntimeError(
            'KRAS DB URL이 설정되지 않았습니다. '
            'KRAS_DB_URL 또는 DATABASE_URL 환경변수를 설정하세요.'
        )
    return url


def get_conn():
    return psycopg2.connect(_get_url(), connect_timeout=5)


def fetchone(sql: str, params=()) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None


def fetchall(sql: str, params=()) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def execute(sql: str, params=()) -> Any:
    """INSERT RETURNING id → returns id; otherwise returns rowcount."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            try:
                row = cur.fetchone()
                return row[0] if row else cur.rowcount
            except Exception:
                return cur.rowcount

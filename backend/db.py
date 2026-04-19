import os
import psycopg2
import psycopg2.extras
from fastapi import HTTPException

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")
    return psycopg2.connect(DATABASE_URL)


def fetchone(sql: str, params=()) -> dict | None:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None


def fetchall(sql: str, params=()) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def execute(sql: str, params=()) -> int:
    """INSERT/UPDATE/DELETE. INSERT RETURNING id → returns id."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            try:
                row = cur.fetchone()
                return row[0] if row else cur.rowcount
            except Exception:
                return cur.rowcount


def risk_level(score: int) -> str:
    if score >= 6:
        return "높음"
    if score >= 3:
        return "보통"
    return "낮음"

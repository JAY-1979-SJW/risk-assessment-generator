"""
운영 DB 에 documents.hwpx_path 컬럼을 최소 추가.

안전:
    - ADD COLUMN IF NOT EXISTS 사용 (PostgreSQL 9.6+)
    - NULLable TEXT, 기본값 NULL, 기존 row 무영향
    - 인덱스는 보류 (사용 패턴 확정 후 별도)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for p in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if p.exists():
            load_dotenv(p, override=False)


def get_conn():
    import psycopg2
    _load_dotenv()
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    db = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    pw = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    if not (host and db and user):
        raise RuntimeError("DB 접속 정보 누락")
    return psycopg2.connect(host=host, port=int(port), dbname=db, user=user, password=pw or "")


DDL = """
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS hwpx_path TEXT;
"""


def main() -> int:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_name='documents' AND column_name='hwpx_path'"
        )
        row = cur.fetchone()
    conn.close()
    if not row:
        print("[FAIL] hwpx_path 컬럼 확인 실패", file=sys.stderr)
        return 3
    print(f"[OK] documents.hwpx_path {row[1]} NULLABLE={row[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

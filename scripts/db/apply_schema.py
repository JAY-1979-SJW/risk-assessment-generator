"""
위험성평가표 운영 DB 스키마 적용기.

입력 : data/risk_db/schema/risk_assessment_db_schema.sql
기능 : 지정된 SQL 파일을 PostgreSQL 에 그대로 실행한다.
안전 : CREATE ... IF NOT EXISTS 기반 DDL 만 적용하며,
       DROP/TRUNCATE/DELETE 등 파괴적 구문은 실행하지 않는다(사전 차단).

실행 예:
    DATABASE_URL=postgresql://user:pw@host:5432/db python scripts/db/apply_schema.py

접속 우선순위:
    1) 환경변수 DATABASE_URL
    2) 환경변수 PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD
    3) 프로젝트 루트의 .env 및 infra/.env 에 기록된 위 값들 (python-dotenv)
    4) (관리 계정) ADMIN_DB_* 환경변수는 DDL 용으로만 보조 사용 가능
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_FILE = PROJECT_ROOT / "data" / "risk_db" / "schema" / "risk_assessment_db_schema.sql"

EXPECTED_TABLES = [
    "documents",
    "hazards",
    "work_types",
    "equipment",
    "document_hazard_map",
    "document_work_type_map",
    "document_equipment_map",
    "kosha_meta",
    "law_meta",
    "expc_meta",
    "risk_assessment_results",
    "collection_runs",
    "normalization_runs",
]

EXPECTED_INDEXES = [
    "ix_documents_source_type",
    "ix_documents_doc_category",
    "ix_documents_status",
    "ix_documents_collected_at",
    "ix_documents_published_at",
    "ix_documents_file_sha256",
    "ix_dhm_hazard_code",
    "ix_dwtm_work_type_code",
    "ix_dem_equipment_code",
    "ix_law_meta_law_name",
    "ix_law_meta_article_no",
    "ix_expc_meta_agenda_no",
    "ix_collection_runs_src_date",
    "ix_normalization_runs_src_date",
]

FORBIDDEN_TOKENS = ("DROP TABLE", "DROP INDEX", "TRUNCATE", "DELETE FROM")


def _load_dotenv_files() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for env_path in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


def _build_dsn() -> tuple[str, dict]:
    """Return (label, connect_kwargs). Never hardcode credentials here."""
    _load_dotenv_files()

    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return ("DATABASE_URL", {"dsn": dsn})

    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    database = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")

    if not (host and database and user):
        missing = [k for k, v in [
            ("host", host), ("database", database), ("user", user)
        ] if not v]
        raise RuntimeError(
            "DB 접속 정보를 찾을 수 없다. "
            "DATABASE_URL 또는 PGHOST/PGDATABASE/PGUSER(/PGPASSWORD) 를 설정하라. "
            f"누락: {missing}"
        )

    return (
        f"{user}@{host}:{port}/{database}",
        dict(host=host, port=int(port), dbname=database, user=user, password=password or ""),
    )


def _read_sql(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"스키마 파일을 찾을 수 없다: {path}")
    text = path.read_text(encoding="utf-8")
    upper = text.upper()
    for token in FORBIDDEN_TOKENS:
        if token in upper:
            raise RuntimeError(f"파괴적 구문이 SQL 에 포함되어 있다: {token}")
    return text


def _connect(label: str, kw: dict):
    import psycopg2
    print(f"[DB] 접속 시도: {label}", flush=True)
    if "dsn" in kw:
        return psycopg2.connect(kw["dsn"])
    return psycopg2.connect(**kw)


def _apply_sql(conn, sql_text: str) -> None:
    with conn.cursor() as cur:
        cur.execute(sql_text)
    conn.commit()


def _count_existing(conn, schema: str, names: list[str], kind: str) -> tuple[int, list[str]]:
    """kind: 'table' | 'index'. Return (count, missing)."""
    if kind == "table":
        sql = """
            SELECT tablename FROM pg_tables
            WHERE schemaname = %s AND tablename = ANY(%s)
        """
    elif kind == "index":
        sql = """
            SELECT indexname FROM pg_indexes
            WHERE schemaname = %s AND indexname = ANY(%s)
        """
    else:
        raise ValueError(kind)

    with conn.cursor() as cur:
        cur.execute(sql, (schema, names))
        found = {r[0] for r in cur.fetchall()}
    missing = [n for n in names if n not in found]
    return len(found), missing


def _count_foreign_keys(conn, schema: str, expected_tables: list[str]) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE table_schema = %s
              AND constraint_type = 'FOREIGN KEY'
              AND table_name = ANY(%s)
            """,
            (schema, expected_tables),
        )
        return int(cur.fetchone()[0])


def main() -> int:
    print(f"[SCHEMA] 파일: {SCHEMA_FILE}")
    sql_text = _read_sql(SCHEMA_FILE)

    try:
        label, kw = _build_dsn()
        conn = _connect(label, kw)
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 2

    schema = os.getenv("PGSCHEMA", "public")
    try:
        _apply_sql(conn, sql_text)
        tbl_ok, tbl_missing = _count_existing(conn, schema, EXPECTED_TABLES, "table")
        idx_ok, idx_missing = _count_existing(conn, schema, EXPECTED_INDEXES, "index")
        fk_cnt = _count_foreign_keys(conn, schema, EXPECTED_TABLES)
    except Exception as exc:
        conn.rollback()
        print(f"[FAIL] SQL 적용 중 오류: {exc!r}", file=sys.stderr)
        return 3
    finally:
        conn.close()

    print(f"[SCHEMA] 테이블 확인: {tbl_ok}/{len(EXPECTED_TABLES)}")
    if tbl_missing:
        print(f"        누락 테이블: {tbl_missing}")
    print(f"[SCHEMA] 인덱스 확인: {idx_ok}/{len(EXPECTED_INDEXES)}")
    if idx_missing:
        print(f"        누락 인덱스: {idx_missing}")
    print(f"[SCHEMA] FK 개수 : {fk_cnt}")

    ok = (tbl_ok == len(EXPECTED_TABLES) and idx_ok == len(EXPECTED_INDEXES))
    print("[RESULT]", "PASS" if ok else "WARN")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

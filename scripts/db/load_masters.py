"""
표준 마스터 테이블(hazards / work_types / equipment) 적재기.

입력 :
    data/risk_db/mapping/hazard_keywords.json
    data/risk_db/mapping/work_type_keywords.json
    data/risk_db/mapping/equipment_keywords.json

동작 :
    - 각 JSON 의 항목 순서를 sort_order 로 변환(10,20,30…)
    - is_active = TRUE
    - PK 충돌 시 이름·sort_order·is_active 만 갱신 (UPSERT)
    - 재실행 시 건수가 유지되어야 한다.

실행 :
    python scripts/db/load_masters.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAPPING_DIR = PROJECT_ROOT / "data" / "risk_db" / "mapping"

HAZARD_FILE = MAPPING_DIR / "hazard_keywords.json"
WORK_TYPE_FILE = MAPPING_DIR / "work_type_keywords.json"
EQUIPMENT_FILE = MAPPING_DIR / "equipment_keywords.json"


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------

def _load_dotenv_files() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for env_path in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


def get_db_connection():
    """Return a new psycopg2 connection using the project's DB settings."""
    import psycopg2
    _load_dotenv_files()

    dsn = os.getenv("DATABASE_URL")
    if dsn:
        print(f"[DB] 접속: DATABASE_URL")
        return psycopg2.connect(dsn)

    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    database = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")

    if not (host and database and user):
        missing = [k for k, v in [("host", host), ("database", database), ("user", user)] if not v]
        raise RuntimeError(
            "DB 접속 정보를 찾을 수 없다. DATABASE_URL 또는 PGHOST/PGDATABASE/PGUSER 설정 필요. "
            f"누락: {missing}"
        )
    print(f"[DB] 접속: {user}@{host}:{port}/{database}")
    return psycopg2.connect(host=host, port=int(port), dbname=database, user=user, password=password or "")


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"매핑 파일을 찾을 수 없다: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 업서트
# ---------------------------------------------------------------------------

def _prepare(items: list[dict], code_key: str, name_key: str) -> list[tuple[str, str, int]]:
    seen: set[str] = set()
    rows: list[tuple[str, str, int]] = []
    for idx, it in enumerate(items, start=1):
        code = str(it.get(code_key, "")).strip()
        name = str(it.get(name_key, "")).strip()
        if not code or not name:
            continue
        if code in seen:
            continue
        seen.add(code)
        rows.append((code, name, idx * 10))
    return rows


def upsert_hazards(conn, items: list[dict]) -> int:
    rows = _prepare(items, "hazard_code", "hazard_name")
    sql = """
        INSERT INTO hazards (hazard_code, hazard_name, sort_order, is_active)
        VALUES (%s, %s, %s, TRUE)
        ON CONFLICT (hazard_code) DO UPDATE
           SET hazard_name = EXCLUDED.hazard_name,
               sort_order  = EXCLUDED.sort_order,
               is_active   = EXCLUDED.is_active
    """
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    return len(rows)


def upsert_work_types(conn, items: list[dict]) -> int:
    rows = _prepare(items, "work_type_code", "work_type_name")
    sql = """
        INSERT INTO work_types (work_type_code, work_type_name, sort_order, is_active)
        VALUES (%s, %s, %s, TRUE)
        ON CONFLICT (work_type_code) DO UPDATE
           SET work_type_name = EXCLUDED.work_type_name,
               sort_order     = EXCLUDED.sort_order,
               is_active      = EXCLUDED.is_active
    """
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    return len(rows)


def upsert_equipment(conn, items: list[dict]) -> int:
    rows = _prepare(items, "equipment_code", "equipment_name")
    sql = """
        INSERT INTO equipment (equipment_code, equipment_name, sort_order, is_active)
        VALUES (%s, %s, %s, TRUE)
        ON CONFLICT (equipment_code) DO UPDATE
           SET equipment_name = EXCLUDED.equipment_name,
               sort_order     = EXCLUDED.sort_order,
               is_active      = EXCLUDED.is_active
    """
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    return len(rows)


# ---------------------------------------------------------------------------
# 검증
# ---------------------------------------------------------------------------

def _count(conn, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return int(cur.fetchone()[0])


def _has_duplicates(conn, table: str, code_col: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) FROM (SELECT {code_col} FROM {table} GROUP BY {code_col} HAVING COUNT(*) > 1) d"
        )
        return int(cur.fetchone()[0])


def _sample(conn, table: str, code_col: str, name_col: str, n: int = 3) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {code_col}, {name_col}, sort_order, is_active "
            f"FROM {table} ORDER BY sort_order ASC LIMIT %s",
            (n,),
        )
        return list(cur.fetchall())


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------

def run() -> int:
    try:
        hazard_doc = load_json(HAZARD_FILE)
        work_doc = load_json(WORK_TYPE_FILE)
        equip_doc = load_json(EQUIPMENT_FILE)
    except Exception as exc:
        print(f"[FAIL] 매핑 파일 로드 실패: {exc!r}", file=sys.stderr)
        return 2

    hazards = hazard_doc.get("hazards", [])
    work_types = work_doc.get("work_types", [])
    equipment = equip_doc.get("equipment", [])

    print(f"[LOAD] hazards 원천 : {len(hazards)}")
    print(f"[LOAD] work_types 원천: {len(work_types)}")
    print(f"[LOAD] equipment 원천 : {len(equipment)}")

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 3

    try:
        n_h = upsert_hazards(conn, hazards)
        n_w = upsert_work_types(conn, work_types)
        n_e = upsert_equipment(conn, equipment)

        print(f"[UPSERT] hazards   : {n_h} 건")
        print(f"[UPSERT] work_types: {n_w} 건")
        print(f"[UPSERT] equipment : {n_e} 건")

        cnt_h = _count(conn, "hazards")
        cnt_w = _count(conn, "work_types")
        cnt_e = _count(conn, "equipment")
        print(f"[COUNT] hazards   : {cnt_h}")
        print(f"[COUNT] work_types: {cnt_w}")
        print(f"[COUNT] equipment : {cnt_e}")

        dup_h = _has_duplicates(conn, "hazards", "hazard_code")
        dup_w = _has_duplicates(conn, "work_types", "work_type_code")
        dup_e = _has_duplicates(conn, "equipment", "equipment_code")
        print(f"[DUP] hazards={dup_h} work_types={dup_w} equipment={dup_e}")

        print("[SAMPLE] hazards (top 3):")
        for r in _sample(conn, "hazards", "hazard_code", "hazard_name"):
            print("   ", r)
        print("[SAMPLE] work_types (top 3):")
        for r in _sample(conn, "work_types", "work_type_code", "work_type_name"):
            print("   ", r)
        print("[SAMPLE] equipment (top 3):")
        for r in _sample(conn, "equipment", "equipment_code", "equipment_name"):
            print("   ", r)

        ok = (cnt_h == n_h and cnt_w == n_w and cnt_e == n_e
              and dup_h == 0 and dup_w == 0 and dup_e == 0)
        print("[RESULT]", "PASS" if ok else "WARN")
        return 0 if ok else 1
    except Exception as exc:
        conn.rollback()
        print(f"[FAIL] 적재 중 오류: {exc!r}", file=sys.stderr)
        return 4
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(run())

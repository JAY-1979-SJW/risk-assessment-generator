"""
법령 + KOSHA 수집 현황 진단기 (read-only).

조회 대상 : documents, law_meta, expc_meta
조회 항목 :
    - documents 전체 건수
    - source_type 별 건수 (law / admrul / expc / kosha 포함)
    - law_meta / expc_meta 건수
    - source_type 별 MAX(created_at)
판정     : OK / PARTIAL / FAIL (하단 기준)

실행 :
    python scripts/db/audit_collection_status.py

절대 규칙 : SELECT 외 쿼리 수행 금지.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()

CORE_SOURCES = ("law", "admrul", "expc", "kosha")

# OK 판정 기준
THRESHOLDS = {
    "law":    1000,
    "admrul": 1000,
    "expc":    500,
    "kosha":   100,
}


# ---------------------------------------------------------------------------
# DB
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
    import psycopg2
    _load_dotenv_files()

    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)

    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    database = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")

    if not (host and database and user):
        missing = [k for k, v in [("host", host), ("database", database), ("user", user)] if not v]
        raise RuntimeError(f"DB 접속 정보 누락: {missing}")

    return psycopg2.connect(
        host=host, port=int(port), dbname=database, user=user, password=password or ""
    )


# ---------------------------------------------------------------------------
# 조회
# ---------------------------------------------------------------------------

def fetch_counts(conn) -> dict:
    """documents 전체 건수 + source_type 별 건수."""
    out: dict = {"total": 0, "by_source": {}}
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM documents")
        out["total"] = int(cur.fetchone()[0])

        cur.execute(
            "SELECT source_type, COUNT(*) FROM documents "
            "GROUP BY source_type ORDER BY source_type"
        )
        for st, cnt in cur.fetchall():
            out["by_source"][str(st)] = int(cnt)
    return out


def fetch_meta_counts(conn) -> dict:
    """law_meta / expc_meta 건수."""
    result = {"law_meta": None, "expc_meta": None}
    with conn.cursor() as cur:
        for tbl in result.keys():
            cur.execute(
                "SELECT to_regclass(%s)", (f"public.{tbl}",)
            )
            exists = cur.fetchone()[0] is not None
            if not exists:
                result[tbl] = None
                continue
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            result[tbl] = int(cur.fetchone()[0])
    return result


def fetch_latest_dates(conn) -> dict:
    """source_type 별 MAX(created_at)."""
    out: dict = {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source_type, MAX(created_at) FROM documents GROUP BY source_type"
        )
        for st, ts in cur.fetchall():
            out[str(st)] = ts.strftime("%Y-%m-%d") if ts else None
    return out


# ---------------------------------------------------------------------------
# 판정
# ---------------------------------------------------------------------------

def evaluate_status(data: dict) -> dict:
    """
    data : {total, by_source, latest, meta}
    return : {status, missing[], shortage[], notes[]}
    """
    by_src = data.get("by_source", {})
    total = data.get("total", 0)

    missing = [s for s in CORE_SOURCES if by_src.get(s, 0) <= 0]
    shortage = [
        s for s in CORE_SOURCES
        if by_src.get(s, 0) > 0 and by_src.get(s, 0) < THRESHOLDS[s]
    ]

    if total <= 0 or len(missing) == len(CORE_SOURCES):
        status = "FAIL"
    elif not missing and not shortage:
        status = "OK"
    else:
        status = "PARTIAL"

    notes: list[str] = []
    if total <= 0:
        notes.append("documents 테이블이 비어 있음.")
    if missing:
        notes.append("누락 source: " + ", ".join(missing))
    if shortage:
        notes.append(
            "건수 부족: "
            + ", ".join(f"{s}({by_src.get(s,0)}<{THRESHOLDS[s]})" for s in shortage)
        )

    return {"status": status, "missing": missing, "shortage": shortage, "notes": notes}


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------

def _fmt_count(v) -> str:
    return "-" if v is None else f"{v:,}"


def _print_report(data: dict, verdict: dict) -> None:
    by_src = data["by_source"]
    meta = data["meta"]
    latest = data["latest"]

    print("[수집 현황]")
    print()
    print(f"총 건수: {_fmt_count(data['total'])}")
    print()
    print("source_type별:")
    for s in CORE_SOURCES:
        print(f"- {s}: {_fmt_count(by_src.get(s, 0))}")
    extras = [k for k in by_src.keys() if k not in CORE_SOURCES]
    for s in sorted(extras):
        print(f"- {s} (기타): {_fmt_count(by_src[s])}")
    print()
    print("[메타]")
    print(f"- law_meta : {_fmt_count(meta.get('law_meta'))}")
    print(f"- expc_meta: {_fmt_count(meta.get('expc_meta'))}")
    print()
    print("[최신 수집]")
    for s in CORE_SOURCES:
        print(f"- {s}: {latest.get(s) or '-'}")
    print()
    print("[판정]")
    print(verdict["status"])
    print()
    print("[분석]")
    if verdict["notes"]:
        for n in verdict["notes"]:
            print(f"- {n}")
    else:
        print("- 이상 없음")


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------

def run() -> int:
    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 2

    try:
        # read-only 트랜잭션으로 안전장치
        conn.set_session(readonly=True)
        counts = fetch_counts(conn)
        meta = fetch_meta_counts(conn)
        latest = fetch_latest_dates(conn)
    except Exception as exc:
        print(f"[FAIL] 조회 중 오류: {exc!r}", file=sys.stderr)
        return 3
    finally:
        conn.close()

    data = {
        "total": counts["total"],
        "by_source": counts["by_source"],
        "meta": meta,
        "latest": latest,
    }
    verdict = evaluate_status(data)
    _print_report(data, verdict)
    return 0


if __name__ == "__main__":
    sys.exit(run())

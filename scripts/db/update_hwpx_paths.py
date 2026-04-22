"""
서버 파일시스템의 HWPX → documents.hwpx_path 매핑 UPDATE.

규칙:
    - /data/raw/law_api/licbyl/files/<source_id>/*.hwpx
        → source_type='licbyl', source_id=<폴더명>
    - /data/raw/moel_forms/policy_data/files/<source_id>/*.hwpx
        → source_type='moel_form', source_id=<폴더명>
    - 폴더에 HWPX 가 여러 개면 가장 큰 파일(본체 추정)을 채택.
    - 상대 경로(PROJECT_ROOT 기준) 를 hwpx_path 에 기록.

idempotent:
    - 동일 경로 재실행 시 NO-OP. 다른 파일이면 UPDATE.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCES = [
    ("licbyl",   PROJECT_ROOT / "data" / "raw" / "law_api" / "licbyl" / "files"),
    ("moel_form", PROJECT_ROOT / "data" / "raw" / "moel_forms" / "policy_data" / "files"),
]


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


def pick_hwpx(folder: Path) -> Path | None:
    candidates = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".hwpx"]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_size)


def main() -> int:
    conn = get_conn()
    totals = {
        "seen": 0, "matched": 0, "updated": 0, "same": 0, "no_row": 0,
    }
    per_source: dict[str, dict] = {}

    with conn.cursor() as cur:
        for src_type, base in SOURCES:
            st = {"seen": 0, "matched": 0, "updated": 0, "same": 0, "no_row": 0}
            if not base.exists():
                print(f"[SKIP] {src_type}: 경로 없음 {base}")
                per_source[src_type] = st
                continue
            for folder in sorted(base.iterdir()):
                if not folder.is_dir():
                    continue
                st["seen"] += 1
                hx = pick_hwpx(folder)
                if not hx:
                    continue
                rel = str(hx.resolve().relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
                source_id = folder.name
                st["matched"] += 1

                cur.execute(
                    "SELECT hwpx_path FROM documents "
                    "WHERE source_type=%s AND source_id=%s",
                    (src_type, source_id),
                )
                row = cur.fetchone()
                if row is None:
                    st["no_row"] += 1
                    continue
                if row[0] == rel:
                    st["same"] += 1
                    continue
                cur.execute(
                    "UPDATE documents SET hwpx_path = %s, updated_at = NOW() "
                    "WHERE source_type = %s AND source_id = %s",
                    (rel, src_type, source_id),
                )
                st["updated"] += cur.rowcount

            per_source[src_type] = st
            for k, v in st.items():
                totals[k] = totals.get(k, 0) + v
    conn.commit()

    print("[요약]")
    for src_type, st in per_source.items():
        print(f"  {src_type:<10} seen={st['seen']:>4} matched={st['matched']:>4} "
              f"updated={st['updated']:>4} same={st['same']:>4} no_row={st['no_row']:>4}")
    print(f"  {'TOTAL':<10} seen={totals['seen']:>4} matched={totals['matched']:>4} "
          f"updated={totals['updated']:>4} same={totals['same']:>4} no_row={totals['no_row']:>4}")

    # 검증: source_type별 hwpx_path 커버리지
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source_type, "
            "COUNT(*) AS total, "
            "COUNT(hwpx_path) AS with_hwpx "
            "FROM documents WHERE source_type IN ('licbyl', 'moel_form') "
            "GROUP BY source_type ORDER BY source_type"
        )
        print("[커버리지]")
        for st, total, with_hwpx in cur.fetchall():
            print(f"  {st:<10} total={total:>4}  hwpx_path 있음={with_hwpx:>4}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

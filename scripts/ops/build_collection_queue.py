"""
백그라운드 수집 큐 빌더.

원칙
- DB 현재 상태 기준으로 "실행 가능한 작업" 만 큐에 넣는다.
- 외부 자격증명/로컬전용 도구가 필요한 대상은 큐에서 제외하고 `excluded_summary` 로만 보고한다.
- 기존 큐가 있으면: 이미 `done` 인 job 은 그대로 두고, 신규 대상만 추가.

출력 큐 항목의 action 종류
    relink_articles      — 본문 "[법령명] 제N조" 추출 → document_law_map(match_type='article')
    refresh_hwpx_path    — documents.hwpx_path NULL 인 문서의 data/raw 경로 재스캔

제외 (excluded_summary 에만 보고)
    kosha_redownload     — kosha status='draft' : 크레덴셜(KOSHA_ID/PW) 필요
    hwp_to_hwpx          — moel_form 의 원본 HWP→HWPX 변환 : 로컬 한컴 필요 (MCP)
    image_only           — kosha status='excluded' : 픽토그램·포스터·VR 등

CLI
    python scripts/ops/build_collection_queue.py [--reset] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()

sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ops._queue import (  # noqa: E402
    make_job, read_all, write_all, counts, master_path,
)


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    for env in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env.exists():
            load_dotenv(env, override=False)


def get_db_connection():
    import psycopg2  # type: ignore
    _load_dotenv()
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    database = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    if not (host and database and user):
        raise RuntimeError("DB 접속 정보 누락")
    return psycopg2.connect(
        host=host, port=int(port), dbname=database, user=user, password=password or ""
    )


FORM_SOURCES = ("kosha_form", "moel_form", "licbyl")


# ---------------------------------------------------------------------------
# 대상 쿼리
# ---------------------------------------------------------------------------

SQL_RELINK_ARTICLES = """
    -- 형태서식 중 현재 article 매핑이 없거나(=law_name 레벨만 존재), 아예 매핑이 없는 것
    SELECT d.source_type, d.source_id
      FROM documents d
     WHERE d.source_type = ANY(%(sources)s)
       AND (d.body_text IS NOT NULL AND LENGTH(d.body_text) >= 40)
       AND NOT EXISTS (
           SELECT 1 FROM document_law_map dlm
            WHERE dlm.document_id = d.id AND dlm.match_type = 'article'
       )
     ORDER BY d.id
"""


SQL_REFRESH_HWPX = """
    -- hwpx_path NULL 이고, 잠재적으로 data/raw 에 HWPX 가 있을 수 있는 form
    SELECT d.source_type, d.source_id
      FROM documents d
     WHERE d.source_type = ANY(%(sources)s)
       AND d.hwpx_path IS NULL
       AND d.file_url IS NOT NULL
     ORDER BY d.id
"""


SQL_EXCLUDED_KOSHA_DRAFT = """
    SELECT COUNT(*) FROM documents
     WHERE source_type='kosha' AND status='draft'
"""

SQL_EXCLUDED_IMAGE_ONLY = """
    SELECT COUNT(*) FROM documents
     WHERE source_type='kosha' AND status='excluded'
"""

SQL_EXCLUDED_MOEL_HWP = """
    SELECT COUNT(*) FROM documents
     WHERE source_type='moel_form' AND hwpx_path IS NULL
"""


# ---------------------------------------------------------------------------
# 빌드
# ---------------------------------------------------------------------------

def _fetch_targets(conn, sql: str, params: dict) -> list[tuple[str, str]]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return [(r[0], r[1]) for r in cur.fetchall()]


def build(reset: bool, dry_run: bool) -> dict:
    conn = get_db_connection()
    try:
        relink = _fetch_targets(conn, SQL_RELINK_ARTICLES, {"sources": list(FORM_SOURCES)})
        hwpx   = _fetch_targets(conn, SQL_REFRESH_HWPX,    {"sources": list(FORM_SOURCES)})
        with conn.cursor() as cur:
            cur.execute(SQL_EXCLUDED_KOSHA_DRAFT); excl_draft = cur.fetchone()[0]
            cur.execute(SQL_EXCLUDED_IMAGE_ONLY);  excl_image = cur.fetchone()[0]
            cur.execute(SQL_EXCLUDED_MOEL_HWP);    excl_moelhwp = cur.fetchone()[0]
    finally:
        conn.close()

    existing = [] if reset else read_all()
    by_id: dict[str, dict] = {j["job_id"]: j for j in existing}

    def _enqueue(items: Iterable[tuple[str, str]], action: str, priority: int, note: str | None = None) -> int:
        added = 0
        for st, sid in items:
            job = make_job(action=action, source_type=st, source_id=sid, priority=priority, note=note)
            if job["job_id"] not in by_id:
                by_id[job["job_id"]] = job
                added += 1
        return added

    added_relink = _enqueue(relink, "relink_articles",   priority=3, note="법령 article 재매칭")
    added_hwpx   = _enqueue(hwpx,   "refresh_hwpx_path", priority=5, note="hwpx_path NULL 재스캔")

    jobs = list(by_id.values())

    if not dry_run:
        write_all(jobs)

    excluded = {
        "kosha_redownload": {"count": int(excl_draft),
                             "reason": "KOSHA_ID/KOSHA_PW 크레덴셜 미탑재"},
        "hwp_to_hwpx":      {"count": int(excl_moelhwp),
                             "reason": "로컬 한컴(Windows) 필요 — MCP convert_moel 참고"},
        "image_only":       {"count": int(excl_image),
                             "reason": "픽토그램·포스터·VR 등 제외 대상"},
    }

    return {
        "queue_path": str(master_path()),
        "added": {"relink_articles": added_relink, "refresh_hwpx_path": added_hwpx},
        "queue_counts": counts(jobs),
        "excluded_summary": excluded,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="기존 큐 무시하고 새로 빌드")
    ap.add_argument("--dry-run", action="store_true", help="큐 파일을 쓰지 않음")
    args = ap.parse_args()

    try:
        r = build(reset=args.reset, dry_run=args.dry_run)
    except Exception as exc:
        print(f"[FAIL] {exc!r}", file=sys.stderr)
        return 3

    print(f"[QUEUE] {r['queue_path']}")
    print(f"[ADDED] {r['added']}")
    print(f"[COUNTS] {r['queue_counts']}")
    print("[EXCLUDED]")
    for k, v in r["excluded_summary"].items():
        print(f"  {k:<18} count={v['count']:<6}  reason={v['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

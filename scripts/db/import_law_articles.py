"""
법령 조문 단위(article) 운영 DB 이관기.

목적
    - 서버의 `normalized/law/*.json` (9,137 조문)을 운영 DB에 적재한다.
    - 기존 `scripts/db/import_documents.py` 는 법령 수준 요약본만 다루므로
      조문 본문 이관 경로가 없다. 이 스크립트가 그 공백을 채운다.

입력
    <data_root>/normalized/law/*.json
    (data_root 우선순위: 환경변수 KRAS_DATA_ROOT → PROJECT_ROOT/data → PROJECT_ROOT/../data)

적재 대상
    documents
        source_type   : 'law'
        source_id     : 파일의 source_id (예: 'law_228817_0001')
        doc_category  : 'law_article'     ← 법령 수준 'law_statute' 와 분리
        title, title_normalized, body_text, has_text, content_length
        language='ko', status='active', collected_at

    law_meta (document_id 1:1)
        law_name, law_id, article_no, promulgation_date, effective_date, ministry
        extra = {"source_file": basename}

옵션
    --dry-run      실제 커밋하지 않고 예상 insert/update 수만 출력 (트랜잭션 ROLLBACK)
    --limit N      테스트용 파일 상한 (기본 0 = 전수)
    --batch N      INSERT 배치 크기 (기본 500)
    --data-root P  data 루트 직접 지정 (환경변수보다 우선)

실행
    # 서버
    DATABASE_URL=postgresql://kras:kras_secure_2026@<db_ip>:5432/kras \\
      python3 scripts/db/import_law_articles.py --dry-run

    # 실적재
    DATABASE_URL=... python3 scripts/db/import_law_articles.py

원칙
    - ON CONFLICT (source_type, source_id) DO UPDATE → idempotent
    - 파일 파싱 실패는 집계만 하고 계속
    - 본 스크립트는 documents / law_meta 에만 쓴다. 분류 매핑은 손대지 않는다.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()


# ---------------------------------------------------------------------------
# 경로 / 환경
# ---------------------------------------------------------------------------

def _data_root_candidates(override: str | None) -> list[Path]:
    roots: list[Path] = []
    if override:
        roots.append(Path(override))
    env = os.environ.get("KRAS_DATA_ROOT")
    if env:
        roots.append(Path(env))
    roots.append(PROJECT_ROOT / "data")
    roots.append(PROJECT_ROOT.parent / "data")
    return [r for r in roots if r.exists()]


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
        missing = [k for k, v in [("host", host), ("database", database), ("user", user)] if not v]
        raise RuntimeError(f"DB 접속 정보 누락: {missing}")
    return psycopg2.connect(
        host=host, port=int(port), dbname=database, user=user, password=password or ""
    )


# ---------------------------------------------------------------------------
# 파싱
# ---------------------------------------------------------------------------

def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y%m%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_collected_at(value: Any) -> datetime | None:
    if not value:
        return None
    s = str(value)
    # ISO 'YYYY-MM-DDTHH:MM:SS(+TZ)'
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _load_article(fp: Path) -> dict | None:
    try:
        with fp.open(encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    source_id = d.get("source_id")
    if not source_id:
        return None

    extra = d.get("extra") or {}

    body = d.get("body_text") or ""
    title = d.get("title") or ""
    content_length = int(d.get("content_length") or len(body))

    return {
        "source_id": source_id,
        "title": title,
        "title_normalized": d.get("title_normalized") or title,
        "body_text": body,
        "has_text": bool(d.get("has_text")) and bool(body),
        "content_length": content_length,
        "collected_at": _parse_collected_at(d.get("collected_at")),
        "law_id": extra.get("law_id") or "",
        "law_name": extra.get("law_name") or "",
        "article_no": extra.get("article_no") or "",
        "promulgation_date": _parse_date(extra.get("promulgation_date")),
        "effective_date": _parse_date(extra.get("effective_date")),
        "ministry": extra.get("ministry") or "",
        "source_file": fp.name,
    }


# ---------------------------------------------------------------------------
# 적재
# ---------------------------------------------------------------------------

UPSERT_DOCUMENT_SQL = """
INSERT INTO documents (
    source_type, source_id, doc_category,
    title, title_normalized, body_text,
    has_text, content_length,
    language, status, collected_at
) VALUES (
    'law', %(source_id)s, 'law_article',
    %(title)s, %(title_normalized)s, %(body_text)s,
    %(has_text)s, %(content_length)s,
    'ko', 'active', %(collected_at)s
)
ON CONFLICT (source_type, source_id) DO UPDATE SET
    doc_category     = EXCLUDED.doc_category,
    title            = EXCLUDED.title,
    title_normalized = EXCLUDED.title_normalized,
    body_text        = EXCLUDED.body_text,
    has_text         = EXCLUDED.has_text,
    content_length   = EXCLUDED.content_length,
    collected_at     = EXCLUDED.collected_at,
    updated_at       = now()
RETURNING id
"""

UPSERT_LAW_META_SQL = """
INSERT INTO law_meta (
    document_id, law_name, law_id, article_no,
    promulgation_date, effective_date, ministry, extra
) VALUES (
    %(document_id)s, %(law_name)s, %(law_id)s, %(article_no)s,
    %(promulgation_date)s, %(effective_date)s, %(ministry)s, %(extra)s
)
ON CONFLICT (document_id) DO UPDATE SET
    law_name          = EXCLUDED.law_name,
    law_id            = EXCLUDED.law_id,
    article_no        = EXCLUDED.article_no,
    promulgation_date = EXCLUDED.promulgation_date,
    effective_date    = EXCLUDED.effective_date,
    ministry          = EXCLUDED.ministry,
    extra             = EXCLUDED.extra
"""


def run_import(
    conn,
    articles_dir: Path,
    dry_run: bool,
    limit: int,
    batch: int,
) -> dict:
    from psycopg2.extras import Json  # type: ignore

    stats = {
        "files_seen": 0,
        "parsed": 0,
        "parse_failed": 0,
        "inserted_or_updated": 0,
        "law_meta_written": 0,
        "skipped_empty": 0,
    }

    files = sorted(articles_dir.glob("*.json"))
    if limit > 0:
        files = files[:limit]
    stats["files_seen"] = len(files)
    if not files:
        return stats

    # idempotent 보장을 위해 savepoint 없이 전체 트랜잭션. dry-run 은 ROLLBACK.
    with conn.cursor() as cur:
        for i, fp in enumerate(files, 1):
            art = _load_article(fp)
            if art is None:
                stats["parse_failed"] += 1
                continue
            stats["parsed"] += 1
            if not art["title"]:
                stats["skipped_empty"] += 1
                continue

            cur.execute(UPSERT_DOCUMENT_SQL, art)
            doc_id_row = cur.fetchone()
            if not doc_id_row:
                continue
            doc_id = doc_id_row[0]
            stats["inserted_or_updated"] += 1

            meta_params = {
                "document_id": doc_id,
                "law_name": art["law_name"],
                "law_id": art["law_id"],
                "article_no": art["article_no"],
                "promulgation_date": art["promulgation_date"],
                "effective_date": art["effective_date"],
                "ministry": art["ministry"],
                "extra": Json({"source_file": art["source_file"]}),
            }
            cur.execute(UPSERT_LAW_META_SQL, meta_params)
            stats["law_meta_written"] += 1

            if i % batch == 0:
                print(f"  [progress] {i:>6,}/{len(files):,}  upserted={stats['inserted_or_updated']:,}", flush=True)

    if dry_run:
        conn.rollback()
        print("[DRY-RUN] 변경 롤백됨")
    else:
        conn.commit()
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", type=int, default=500)
    ap.add_argument("--data-root", type=str, default=None)
    args = ap.parse_args()

    roots = _data_root_candidates(args.data_root)
    if not roots:
        print("[FAIL] data_root 를 찾을 수 없다.", file=sys.stderr)
        return 2
    root = roots[0]
    articles_dir = root / "normalized" / "law"
    if not articles_dir.exists():
        print(f"[FAIL] {articles_dir} 가 존재하지 않음.", file=sys.stderr)
        return 2

    print(f"[FS]  articles_dir = {articles_dir}")
    print(f"[OPT] dry_run={args.dry_run}  limit={args.limit}  batch={args.batch}")

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 3

    try:
        stats = run_import(conn, articles_dir, args.dry_run, args.limit, args.batch)
    except Exception as exc:
        conn.rollback()
        print(f"[FAIL] 적재 중 오류: {exc!r}", file=sys.stderr)
        return 4
    finally:
        conn.close()

    print()
    print("[RESULT]")
    for k in ("files_seen", "parsed", "parse_failed", "skipped_empty", "inserted_or_updated", "law_meta_written"):
        print(f"  {k:<22}: {stats[k]:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

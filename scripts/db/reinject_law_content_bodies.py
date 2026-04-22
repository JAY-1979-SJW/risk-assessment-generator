"""
expc / admrul 본문 재주입기.

배경
    법령 해석례(expc)·행정규칙(admrul) 문서는 이미 DB 에 메타만 적재되어
    `body_text` 가 null 이다. 원천 raw/law_content/{source}/YYYY-MM-DD/*_content.jsonl
    에 full text 가 있으므로 그 내용만 body_text 컬럼에 UPDATE 한다.

원칙
    - title / source_id / source_type / url 등 기존 값은 건드리지 않는다.
    - body 가 실제로 있는 jsonl 줄만 UPDATE 대상.
    - 매칭 규칙: jsonl doc_id 에서 '{source_type}_' prefix 제거 → DB source_id
    - 본문에서 제어문자(\\x00 등) 제거.
    - 본문 있는 줄만 UPDATE, 없는 줄은 skipped.

옵션
    --source {expc,admrul,all}   기본 all
    --dry-run
    --data-root P
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    for env in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env.exists():
            load_dotenv(env, override=False)


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


# ---------------------------------------------------------------------------

# 제어문자 제거 (NUL, BEL 등). 개행/탭은 유지.
_CTRL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def _clean(text: str) -> str:
    if not text:
        return ""
    return _CTRL_RE.sub("", text)


def _find_latest_jsonl(root: Path, source_type: str) -> Path | None:
    base = root / "raw" / "law_content" / source_type
    if not base.exists():
        return None
    date_dirs = sorted([d for d in base.iterdir() if d.is_dir()], reverse=True)
    for dd in date_dirs:
        for p in dd.glob(f"{source_type}_content.jsonl"):
            return p
    return None


def _iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def reinject(conn, source_type: str, jsonl: Path, dry_run: bool) -> dict:
    stats = {
        "source_type": source_type,
        "jsonl": str(jsonl),
        "rows": 0,
        "candidates": 0,
        "updated": 0,
        "skipped_empty_body": 0,
        "skipped_no_db_row": 0,
    }
    prefix = f"{source_type}_"

    with conn.cursor() as cur:
        for rec in _iter_jsonl(jsonl):
            stats["rows"] += 1
            doc_id = rec.get("doc_id") or ""
            body = _clean(rec.get("content_raw") or rec.get("body_text") or "")
            if not doc_id.startswith(prefix):
                continue
            source_id = doc_id[len(prefix):]
            if not body.strip():
                stats["skipped_empty_body"] += 1
                continue
            stats["candidates"] += 1
            cur.execute(
                """
                UPDATE documents
                   SET body_text      = %s,
                       has_text       = TRUE,
                       content_length = %s,
                       updated_at     = now()
                 WHERE source_type = %s
                   AND source_id   = %s
                   AND COALESCE(body_text, '') = ''
                """,
                (body, len(body), source_type, source_id),
            )
            if cur.rowcount > 0:
                stats["updated"] += cur.rowcount
            else:
                stats["skipped_no_db_row"] += 1

    if dry_run:
        conn.rollback()
    else:
        conn.commit()
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=("expc", "admrul", "all"), default="all")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--data-root", type=str, default=None)
    args = ap.parse_args()

    roots = _data_root_candidates(args.data_root)
    if not roots:
        print("[FAIL] data_root 없음", file=sys.stderr)
        return 2
    root = roots[0]
    print(f"[FS] data_root = {root}")

    sources = ("expc", "admrul") if args.source == "all" else (args.source,)
    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 3

    try:
        for src in sources:
            jsonl = _find_latest_jsonl(root, src)
            if jsonl is None:
                print(f"[WARN] {src}: jsonl 없음")
                continue
            stats = reinject(conn, src, jsonl, args.dry_run)
            print(
                f"[{src}] jsonl={jsonl.name}  rows={stats['rows']}  "
                f"cand={stats['candidates']}  updated={stats['updated']}  "
                f"skip_empty={stats['skipped_empty_body']}  skip_nodb={stats['skipped_no_db_row']}"
            )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

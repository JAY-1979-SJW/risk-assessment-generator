"""
KOSHA null_body 문서 상태 분리기.

배경
    DB 의 kosha 본문 null 1,415 건을 아래 3 상태로 명확히 분리한다.
        image_only       : 원본 PDF 는 있으나 텍스트가 실제로 없음 (excluded)
        parse_failed     : PDF 에 텍스트가 있으나 과거 파싱 실패 (draft, reparsable)
        missing_source   : 원본 파일 자체가 없음 (draft, 복구 불가)

원칙
    - 대량 복구보다 정확한 상태 마킹이 우선.
    - OCR 도입 금지. pdfminer 로 텍스트 추출이 되면 parse_failed 로 분류하고
      body_text 도 함께 채운다 (부수효과). 추출 안 되면 image_only 로 마킹.
    - pdf_path 가 없는 행은 missing_source 로 일괄 마킹.
    - 스키마 최소 수정: 기존 `status` + `doc_category` 만 활용.

적재 대상 (문서 단위 UPDATE)
    image_only     : status='excluded', doc_category='kosha_opl_image_only'
    parse_failed   : status='active',   doc_category='kosha_opl_parse_recovered',
                     body_text=추출텍스트
    missing_source : status='draft',    doc_category='kosha_opl_missing_source'

옵션
    --dry-run
    --limit N        테스트용 상한
    --min-text-len N parse_failed 판정 임계(기본 20)
"""
from __future__ import annotations

import argparse
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


_CTRL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def _extract_pdf_text(path: Path) -> str:
    try:
        from pdfminer.high_level import extract_text  # type: ignore
    except ImportError:
        return ""
    try:
        txt = extract_text(str(path)) or ""
    except Exception:
        return ""
    return _CTRL_RE.sub("", txt).strip()


IMAGE_ONLY_DOC_CATEGORY = "kosha_opl_image_only"
RECOVERED_DOC_CATEGORY = "kosha_opl_parse_recovered"
MISSING_DOC_CATEGORY = "kosha_opl_missing_source"


def run(conn, dry_run: bool, limit: int, min_text_len: int) -> dict:
    stats = {
        "candidates": 0,
        "image_only": 0,
        "parse_recovered": 0,
        "missing_source": 0,
        "pdf_read_error": 0,
    }
    with conn.cursor() as rcur, conn.cursor() as wcur:
        q = """
            SELECT id, source_id, pdf_path
              FROM documents
             WHERE source_type='kosha'
               AND COALESCE(body_text,'')=''
             ORDER BY id
        """
        if limit > 0:
            q += f" LIMIT {int(limit)}"
        rcur.execute(q)
        rows = rcur.fetchall()
        stats["candidates"] = len(rows)

        for doc_id, source_id, pdf_path in rows:
            if not pdf_path:
                wcur.execute(
                    """
                    UPDATE documents
                       SET status       = 'draft',
                           doc_category = %s,
                           updated_at   = now()
                     WHERE id = %s
                    """,
                    (MISSING_DOC_CATEGORY, doc_id),
                )
                stats["missing_source"] += 1
                continue

            p = Path(pdf_path)
            if not p.exists():
                # PDF 경로는 있지만 파일 없음 → missing
                wcur.execute(
                    """
                    UPDATE documents
                       SET status       = 'draft',
                           doc_category = %s,
                           updated_at   = now()
                     WHERE id = %s
                    """,
                    (MISSING_DOC_CATEGORY, doc_id),
                )
                stats["missing_source"] += 1
                continue

            text = _extract_pdf_text(p)
            if len(text) >= min_text_len:
                wcur.execute(
                    """
                    UPDATE documents
                       SET status         = 'active',
                           doc_category   = %s,
                           body_text      = %s,
                           has_text       = TRUE,
                           content_length = %s,
                           updated_at     = now()
                     WHERE id = %s
                    """,
                    (RECOVERED_DOC_CATEGORY, text, len(text), doc_id),
                )
                stats["parse_recovered"] += 1
            else:
                wcur.execute(
                    """
                    UPDATE documents
                       SET status       = 'excluded',
                           doc_category = %s,
                           updated_at   = now()
                     WHERE id = %s
                    """,
                    (IMAGE_ONLY_DOC_CATEGORY, doc_id),
                )
                stats["image_only"] += 1

    if dry_run:
        conn.rollback()
    else:
        conn.commit()
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--min-text-len", type=int, default=20)
    args = ap.parse_args()

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 3

    try:
        stats = run(conn, args.dry_run, args.limit, args.min_text_len)
    finally:
        conn.close()

    print("[RESULT]")
    for k in ("candidates", "image_only", "parse_recovered", "missing_source", "pdf_read_error"):
        print(f"  {k:<18}: {stats[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

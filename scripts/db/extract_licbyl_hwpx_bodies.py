"""
licbyl HWPX → documents.body_text 추출기.

배경
    licbyl(법령 별표·별지서식) 17건은 DB 에 hwpx_path 는 있으나 body 가 null.
    raw/law_api/licbyl/files/<source_id>/*.hwpx 를 unzip 하여
    Contents/section*.xml 의 <hp:t> 텍스트를 이어 붙여 body_text 로 UPDATE.

원칙
    - source_id 디렉토리 기준으로 hwpx 파일을 찾는다 (파일명 mojibake 안전).
    - body_text 는 현재 null 인 행만 UPDATE.
    - 실패 파일은 failed 목록에 기록.
    - 새로운 문서 INSERT 없음.

옵션
    --dry-run
    --data-root P
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
import zipfile
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
# HWPX 파싱
# ---------------------------------------------------------------------------

_HP_T_RE = re.compile(r"<hp:t[^>]*>([^<]*)</hp:t>")
_CTRL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def _extract_text_from_section(xml_bytes: bytes) -> str:
    text = xml_bytes.decode("utf-8", errors="ignore")
    fragments = _HP_T_RE.findall(text)
    joined = " ".join(fragments)
    return _CTRL_RE.sub("", html.unescape(joined)).strip()


def _extract_hwpx_body(hwpx_path: Path) -> tuple[str, int]:
    """(body_text, section_count)."""
    with zipfile.ZipFile(hwpx_path) as zf:
        section_names = sorted(
            n for n in zf.namelist()
            if n.startswith("Contents/section") and n.endswith(".xml")
        )
        parts: list[str] = []
        for name in section_names:
            with zf.open(name) as fp:
                parts.append(_extract_text_from_section(fp.read()))
    return "\n\n".join(p for p in parts if p), len(section_names)


def _find_hwpx_for_source_id(licbyl_root: Path, source_id: str) -> Path | None:
    dd = licbyl_root / str(source_id)
    if not dd.exists():
        return None
    for p in dd.glob("*.hwpx"):
        return p
    return None


# ---------------------------------------------------------------------------

def run(conn, data_root: Path, dry_run: bool) -> dict:
    licbyl_root = data_root / "raw" / "law_api" / "licbyl" / "files"
    stats: dict = {
        "candidates": 0,
        "file_found": 0,
        "file_missing": 0,
        "parsed_ok": 0,
        "parsed_empty": 0,
        "parsed_failed": 0,
        "updated": 0,
        "failed_ids": [],
    }

    with conn.cursor() as rcur, conn.cursor() as wcur:
        rcur.execute(
            "SELECT id, source_id, title FROM documents "
            "WHERE source_type='licbyl' AND COALESCE(body_text,'')='' "
            "ORDER BY id"
        )
        rows = rcur.fetchall()
        stats["candidates"] = len(rows)

        for doc_id, source_id, title in rows:
            hwpx = _find_hwpx_for_source_id(licbyl_root, source_id)
            if hwpx is None:
                stats["file_missing"] += 1
                stats["failed_ids"].append((doc_id, source_id, "hwpx_not_found"))
                continue
            stats["file_found"] += 1
            try:
                body, _sec_n = _extract_hwpx_body(hwpx)
            except Exception as exc:
                stats["parsed_failed"] += 1
                stats["failed_ids"].append((doc_id, source_id, f"parse_err:{exc!r}"))
                continue

            if not body.strip():
                stats["parsed_empty"] += 1
                stats["failed_ids"].append((doc_id, source_id, "empty_body"))
                continue
            stats["parsed_ok"] += 1

            wcur.execute(
                """
                UPDATE documents
                   SET body_text      = %s,
                       has_text       = TRUE,
                       content_length = %s,
                       updated_at     = now()
                 WHERE id = %s AND COALESCE(body_text,'') = ''
                """,
                (body, len(body), doc_id),
            )
            if wcur.rowcount > 0:
                stats["updated"] += wcur.rowcount

    if dry_run:
        conn.rollback()
    else:
        conn.commit()
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--data-root", type=str, default=None)
    args = ap.parse_args()

    roots = _data_root_candidates(args.data_root)
    if not roots:
        print("[FAIL] data_root 없음", file=sys.stderr)
        return 2
    root = roots[0]
    print(f"[FS] data_root = {root}")

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 3

    try:
        stats = run(conn, root, args.dry_run)
    finally:
        conn.close()

    print("[RESULT]")
    for k in ("candidates", "file_found", "file_missing",
              "parsed_ok", "parsed_empty", "parsed_failed", "updated"):
        print(f"  {k:<18}: {stats[k]}")
    if stats["failed_ids"]:
        print("  failed:")
        for doc_id, source_id, reason in stats["failed_ids"]:
            print(f"    - id={doc_id} source_id={source_id}  reason={reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

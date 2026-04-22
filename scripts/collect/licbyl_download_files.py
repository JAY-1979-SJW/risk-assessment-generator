"""
law.go.kr 법령 별표서식(licbyl) HWP/PDF 파일 다운로드 + 운영 DB 메타 갱신.

입력:
    data/raw/law_api/licbyl/YYYY-MM-DD/licbyl_index.json 의 items

동작:
    - 각 item 의 별표서식파일링크 (HWP) / 별표서식PDF파일링크 (PDF) 를
      https://www.law.go.kr 를 base 로 전체 URL 로 조립하여 requests.get.
    - data/raw/law_api/licbyl/files/{별표일련번호}/ 하위에 저장.
    - 파일 이름은 Content-Disposition 헤더에서 추출 (실패 시 fallback).
    - 기존 파일이 같은 size 로 있으면 skip (idempotent).
    - 완료 후 manifest.json 생성.
    - DB 에 연결 가능하면 documents(source_type='licbyl', source_id=별표일련번호)
      의 file_url, pdf_path, file_sha256 를 UPDATE.

옵션:
    --dry-run       : 다운로드·DB update 수행하지 않고 계획만 출력.
    --limit N       : 상한.
    --no-db         : DB update 생략.
    --overwrite     : 기존 파일도 다시 받음.

재실행 안전:
    같은 URL 에서 동일 파일을 받으면 skip. DB update 는 WHERE 절 기반 idempotent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 실제 index 파일 위치는 환경에 따라 다름.
#   1) data/raw/law_api/licbyl/YYYY-MM-DD/licbyl_index.json  (dated archive)
#   2) data/raw/law_api/licbyl/licbyl_index.json             (flat)
#   3) data/risk_db/law_raw/licbyl_index.json                (법령 수집기 기본 저장 경로)
INDEX_CANDIDATES_FLAT = [
    PROJECT_ROOT / "data" / "raw" / "law_api" / "licbyl" / "licbyl_index.json",
    PROJECT_ROOT / "data" / "risk_db" / "law_raw" / "licbyl_index.json",
]
INDEX_DATED_BASE = PROJECT_ROOT / "data" / "raw" / "law_api" / "licbyl"

# 다운로드 저장 루트: dated-raw 트리 밖 files/ 서브디렉토리
FILES_ROOT = PROJECT_ROOT / "data" / "raw" / "law_api" / "licbyl" / "files"
MANIFEST_PATH = PROJECT_ROOT / "data" / "raw" / "law_api" / "licbyl" / "files_manifest.json"
LAWGO_BASE = "https://www.law.go.kr"

DL_TIMEOUT = 30
RETRY = 3
SLEEP_BETWEEN = 0.8


# ---------------------------------------------------------------------------
# 입력
# ---------------------------------------------------------------------------

def find_latest_index() -> Path | None:
    # 1) 날짜 디렉토리 (최신순)
    if INDEX_DATED_BASE.exists():
        dated = sorted(
            [d for d in INDEX_DATED_BASE.iterdir()
             if d.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}", d.name)],
            reverse=True,
        )
        for d in dated:
            idx = d / "licbyl_index.json"
            if idx.exists():
                return idx
    # 2) flat / 기본 수집기 저장 경로
    for p in INDEX_CANDIDATES_FLAT:
        if p.exists():
            return p
    return None


def load_items(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items") or []
    return items if isinstance(items, list) else []


# ---------------------------------------------------------------------------
# 파일명 추출
# ---------------------------------------------------------------------------

_FILENAME_STAR_RE = re.compile(r"filename\*=(?:UTF-8|utf-8)''([^;]+)", re.IGNORECASE)
_FILENAME_RE      = re.compile(r'filename="?([^";]+)"?', re.IGNORECASE)


def filename_from_headers(headers: dict, fallback: str) -> str:
    cd = headers.get("Content-Disposition") or headers.get("content-disposition") or ""
    if cd:
        m = _FILENAME_STAR_RE.search(cd)
        if m:
            try:
                return unquote(m.group(1))
            except Exception:
                pass
        m = _FILENAME_RE.search(cd)
        if m:
            try:
                # 일부 서버가 euc-kr / cp949 로 인코딩하는 경우가 있어 정규화
                raw = m.group(1)
                try:
                    return raw.encode("latin1").decode("utf-8")
                except Exception:
                    pass
                return raw
            except Exception:
                pass
    return fallback


def sanitize(name: str) -> str:
    return re.sub(r"[\\/:*?\"<>|]", "_", name).strip() or "file"


# ---------------------------------------------------------------------------
# 다운로드
# ---------------------------------------------------------------------------

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_one(url: str, out_dir: Path, fallback_name: str, *,
                 overwrite: bool) -> dict:
    """
    Return dict:
      {"ok": bool, "path": str|None, "url": str, "size": int, "sha256": str,
       "content_type": str, "skipped": bool, "error": str|None}
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    err = None
    for attempt in range(1, RETRY + 1):
        try:
            r = requests.get(url, timeout=DL_TIMEOUT, verify=False, stream=True)
            if r.status_code != 200:
                err = f"HTTP {r.status_code}"
                time.sleep(attempt * 1.0)
                continue
            ctype = r.headers.get("Content-Type", "")
            # HTML 페이지가 내려오면 다운로드 실패로 간주 (리다이렉트/에러 페이지)
            if "text/html" in ctype.lower() and "octet" not in ctype.lower():
                err = f"got HTML (not file): {ctype}"
                return {"ok": False, "path": None, "url": url, "size": 0, "sha256": "",
                        "content_type": ctype, "skipped": False, "error": err}

            name = filename_from_headers(r.headers, fallback_name)
            name = sanitize(name)
            out_path = out_dir / name

            if out_path.exists() and not overwrite:
                size = out_path.stat().st_size
                return {"ok": True, "path": str(out_path), "url": url, "size": size,
                        "sha256": sha256_of(out_path), "content_type": ctype,
                        "skipped": True, "error": None}

            total = 0
            h = hashlib.sha256()
            with out_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    f.write(chunk)
                    h.update(chunk)
                    total += len(chunk)
            return {"ok": True, "path": str(out_path), "url": url, "size": total,
                    "sha256": h.hexdigest(), "content_type": ctype,
                    "skipped": False, "error": None}
        except Exception as exc:
            err = repr(exc)
            time.sleep(attempt * 1.0)
    return {"ok": False, "path": None, "url": url, "size": 0, "sha256": "",
            "content_type": "", "skipped": False, "error": err}


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for env_path in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


def get_db_connection():
    import psycopg2
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
    return psycopg2.connect(host=host, port=int(port), dbname=database, user=user, password=password or "")


def update_db_row(cur, *, source_id: str, file_url: str | None,
                  pdf_path: str | None, file_sha256: str | None) -> int:
    """documents(source_type='licbyl', source_id=...) 한 행을 UPDATE. 변경 행 수 반환."""
    cur.execute(
        """
        UPDATE documents
           SET file_url    = COALESCE(%s, file_url),
               pdf_path    = COALESCE(%s, pdf_path),
               file_sha256 = COALESCE(%s, file_sha256),
               updated_at  = NOW()
         WHERE source_type = 'licbyl' AND source_id = %s
        """,
        (file_url, pdf_path, file_sha256, source_id),
    )
    return cur.rowcount


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def pick_url(raw_link: str) -> str:
    if not raw_link:
        return ""
    raw_link = raw_link.strip()
    if raw_link.startswith("http"):
        return raw_link
    if raw_link.startswith("/"):
        return LAWGO_BASE + raw_link
    return LAWGO_BASE + "/" + raw_link


def run(args) -> int:
    idx_path = find_latest_index()
    if idx_path is None:
        print("[FAIL] licbyl_index.json 를 찾을 수 없음. data/raw/law_api/licbyl/ 하위 확인.",
              file=sys.stderr)
        return 2
    print(f"[INDEX] {idx_path}")

    items = load_items(idx_path)
    print(f"[INDEX] items={len(items)}")
    if args.limit > 0:
        items = items[: args.limit]

    conn = None
    if not args.no_db and not args.dry_run:
        try:
            conn = get_db_connection()
        except Exception as exc:
            print(f"[WARN] DB 접속 실패, DB update 생략: {exc!r}")
            conn = None

    stats = {
        "total": 0,
        "hwp_ok": 0, "hwp_skip": 0, "hwp_fail": 0,
        "pdf_ok": 0, "pdf_skip": 0, "pdf_fail": 0,
        "db_updated": 0, "db_missing": 0, "no_urls": 0,
    }
    manifest: list[dict] = []

    for idx, it in enumerate(items, start=1):
        source_id = str(it.get("별표일련번호") or "").strip()
        title = (it.get("별표명") or "").strip()
        law_name = (it.get("관련법령명") or "").strip()
        hwp_link = (it.get("별표서식파일링크") or "").strip()
        pdf_link = (it.get("별표서식PDF파일링크") or "").strip()
        hwp_url = pick_url(hwp_link)
        pdf_url = pick_url(pdf_link)

        if not source_id:
            continue
        stats["total"] += 1

        if not hwp_url and not pdf_url:
            stats["no_urls"] += 1
            manifest.append({"source_id": source_id, "title": title, "error": "no urls"})
            continue

        out_dir = FILES_ROOT / source_id
        entry: dict = {"source_id": source_id, "title": title, "law_name": law_name,
                       "hwp": None, "pdf": None}

        if args.dry_run:
            print(f"  [{idx}] {source_id} — dry-run  hwp={hwp_url!r}  pdf={pdf_url!r}")
            manifest.append(entry)
            continue

        if hwp_url:
            res = download_one(hwp_url, out_dir, fallback_name=f"{source_id}.hwp",
                               overwrite=args.overwrite)
            entry["hwp"] = res
            if res["ok"]:
                stats["hwp_skip"] += 1 if res["skipped"] else 0
                stats["hwp_ok"]   += 0 if res["skipped"] else 1
            else:
                stats["hwp_fail"] += 1
            time.sleep(SLEEP_BETWEEN)

        if pdf_url:
            res = download_one(pdf_url, out_dir, fallback_name=f"{source_id}.pdf",
                               overwrite=args.overwrite)
            entry["pdf"] = res
            if res["ok"]:
                stats["pdf_skip"] += 1 if res["skipped"] else 0
                stats["pdf_ok"]   += 0 if res["skipped"] else 1
            else:
                stats["pdf_fail"] += 1
            time.sleep(SLEEP_BETWEEN)

        manifest.append(entry)

        # DB update: pdf 우선, 없으면 hwp
        if conn is not None:
            file_url = pdf_url or hwp_url or None
            chosen = entry["pdf"] if entry["pdf"] and entry["pdf"]["ok"] else entry["hwp"]
            pdf_path_rel = None
            file_sha = None
            if chosen and chosen["ok"] and chosen.get("path"):
                pdf_path_rel = str(Path(chosen["path"]).relative_to(PROJECT_ROOT)).replace("\\", "/")
                file_sha = chosen.get("sha256") or None
            try:
                with conn.cursor() as cur:
                    rc = update_db_row(cur, source_id=source_id,
                                       file_url=file_url, pdf_path=pdf_path_rel,
                                       file_sha256=file_sha)
                conn.commit()
                if rc > 0:
                    stats["db_updated"] += 1
                else:
                    stats["db_missing"] += 1
            except Exception as exc:
                conn.rollback()
                print(f"    [WARN] DB update 실패 sid={source_id}: {exc!r}")

    # manifest 저장
    if not args.dry_run:
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with MANIFEST_PATH.open("w", encoding="utf-8") as f:
            json.dump({"generated_at_items": len(items), "stats": stats, "entries": manifest},
                      f, ensure_ascii=False, indent=2)
        print(f"[MANIFEST] {MANIFEST_PATH}")

    if conn is not None:
        conn.close()

    print()
    print("[요약]")
    for k, v in stats.items():
        print(f"  - {k:<14} {v}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-db", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    return run(ap.parse_args())


if __name__ == "__main__":
    sys.exit(main())

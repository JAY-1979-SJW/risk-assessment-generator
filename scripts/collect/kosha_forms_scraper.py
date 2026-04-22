"""
portal.kosha.or.kr 기술지원규정(KOSHA Guide) 및 기타 서식성 문서 수집기.

구현:
    SPA 내부 XHR 엔드포인트를 requests 로 재현 (playwright 불필요).

엔드포인트 (2026-04-22 확인):
    POST /api/portal24/bizV/p/VCPDG08009/selectList
        body {techGdlnCtgryCd, techGdlnSttsSeCdIng, techGdlnSttsSeCdDel,
              page, rowsPerPage, searchType, searchVal, startDt, endDt}
        payload.list[].techGdlnOrgnlAtcflNo  → fileId
        payload.totalCount

    POST /api/portal24/bizA/p/files/getFileList
        body {fileId, fileUploadType:"02", atcflTaskColNm:"onlyPDF",
              atcflSeTaskComCdNm:"Y"}
        payload[].atcflNo, atcflSeq, orgnlAtchFileNm, mimeType, atcflSz

    GET  /api/portal24/bizA/p/files/downloadAtchFile?atcflNo=<>&atcflSeq=<>
        → 바이너리 PDF

결과물:
    data/raw/kosha_forms/{category}/index.json        (수집된 목록)
    data/raw/kosha_forms/{category}/files/<techGdlnNo>/<file.pdf>
    data/raw/kosha_forms/{category}/manifest.json

DB 이관:
    source_type = kosha_form
    doc_category = kosha_guide | kosha_form_* (향후 확장)
    source_id = techGdlnNo (예: C-C-11-2026)
    UNIQUE (source_type, source_id) 기반 idempotent upsert
    sha256 으로 동일 파일 재다운로드 방지

옵션:
    --category {all|CC|...}     techGdlnCtgryCd 필터 (all 은 공란)
    --rows N                    page 당 rows (기본 100)
    --max-pages N               상한 (기본 999 즉 전량)
    --limit N                   전체 아이템 상한 (선택)
    --no-download               파일 메타/리스트만 갱신
    --no-db                     DB upsert 생략
    --dry-run                   DB/파일 쓰지 않고 계획만 출력
    --rate SECONDS              API 호출 간격 (기본 0.6초)
"""
from __future__ import annotations

import argparse
import hashlib
import html
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
RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "kosha_forms"
RAW_ROOT.mkdir(parents=True, exist_ok=True)

PORTAL = "https://portal.kosha.or.kr"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "Chrome/120.0.0.0 Safari/537.36")

# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------

def sanitize(name: str, *, max_bytes: int = 200) -> str:
    name = re.sub(r"[\\/:*?\"<>|\n\r\t]", "_", name).strip() or "file"
    enc = name.encode("utf-8", errors="ignore")
    if len(enc) <= max_bytes:
        return name
    if "." in name:
        base, ext = name.rsplit(".", 1)
        ext = "." + ext
    else:
        base, ext = name, ""
    ext_b = ext.encode("utf-8", errors="ignore")
    budget = max(1, max_bytes - len(ext_b))
    base = base.encode("utf-8", errors="ignore")[:budget].decode("utf-8", errors="ignore").rstrip()
    return (base + ext) or "file"


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

def strip_html(s: str) -> str:
    if not s:
        return ""
    s = _TAG_RE.sub(" ", s)
    s = html.unescape(s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def parse_ymd(s: str | None) -> str | None:
    """20260130 → 2026-01-30"""
    if not s:
        return None
    s = str(s).strip()
    m = re.match(r"^(\d{4})[-.]?(\d{2})[-.]?(\d{2})$", s)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def status_from_kosha(code_st: str | None) -> str:
    """techGdlnSttsSeCdSt 값(현행/개정/폐지)을 documents.status 허용값에 매핑."""
    if not code_st:
        return "active"
    s = str(code_st).strip()
    if s in ("폐지",):
        return "archived"
    return "active"


# ---------------------------------------------------------------------------
# API 클라이언트
# ---------------------------------------------------------------------------

class KoshaPortalClient:
    def __init__(self, rate: float = 0.6) -> None:
        self.s = requests.Session()
        self.s.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": UA,
            "Origin": PORTAL,
            "Referer": PORTAL + "/archive/resources/tech-support/search/all",
        })
        self.rate = rate

    def _post(self, path: str, body: dict) -> dict:
        url = PORTAL + path
        last_err = ""
        for attempt in range(1, 4):
            try:
                r = self.s.post(url, json=body, verify=False, timeout=20)
                if r.status_code != 200:
                    last_err = f"HTTP {r.status_code}"
                    time.sleep(attempt)
                    continue
                return r.json()
            except Exception as e:
                last_err = repr(e)
                time.sleep(attempt)
        raise RuntimeError(f"POST {path} 실패: {last_err}")

    def tech_guide_list(self, page: int, rows: int, *,
                        category_cd: str = "",
                        search_val: str | None = None) -> dict:
        body = {
            "techGdlnCtgryCd": category_cd or "",
            "techGdlnSttsSeCdIng": "1",
            "techGdlnSttsSeCdDel": "0",
            "startDt": None, "endDt": None,
            "searchType": "all", "searchVal": search_val,
            "page": page, "rowsPerPage": rows,
        }
        time.sleep(self.rate)
        return self._post("/api/portal24/bizV/p/VCPDG08009/selectList", body)

    def file_list(self, file_id: str, *, only_pdf: bool = False) -> list[dict]:
        # only_pdf=True 면 portal 기본 동작(onlyPDF 필터) 재현.
        # False 면 HWP/PDF 모두 반환 시도 (서버 동작에 따름).
        body: dict = {"fileId": file_id, "fileUploadType": "02"}
        if only_pdf:
            body["atcflTaskColNm"] = "onlyPDF"
            body["atcflSeTaskComCdNm"] = "Y"
        time.sleep(self.rate)
        resp = self._post("/api/portal24/bizA/p/files/getFileList", body)
        payload = resp.get("payload") or []
        return payload if isinstance(payload, list) else []

    def download(self, atcfl_no: str, atcfl_seq: int, out_path: Path) -> dict:
        url = f"{PORTAL}/api/portal24/bizA/p/files/downloadAtchFile"
        params = {"atcflNo": atcfl_no, "atcflSeq": atcfl_seq}
        time.sleep(self.rate)
        try:
            r = self.s.get(url, params=params, verify=False, timeout=60, stream=True)
            if r.status_code != 200:
                return {"ok": False, "error": f"HTTP {r.status_code}"}
            ctype = r.headers.get("Content-Type", "")
            if "text/html" in ctype.lower():
                return {"ok": False, "error": f"got HTML: {ctype}"}
            out_path.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256()
            total = 0
            with out_path.open("wb") as f:
                for chunk in r.iter_content(65536):
                    if not chunk:
                        continue
                    f.write(chunk)
                    h.update(chunk)
                    total += len(chunk)
            return {"ok": True, "size": total, "sha256": h.hexdigest(),
                    "content_type": ctype, "path": str(out_path)}
        except Exception as e:
            return {"ok": False, "error": repr(e)}


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for p in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if p.exists():
            load_dotenv(p, override=False)


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


DOC_UPSERT_SQL = """
INSERT INTO documents (
    source_type, source_id, doc_category,
    title, title_normalized, body_text, has_text, content_length,
    url, file_url, pdf_path, file_sha256,
    language, status, published_at, collected_at,
    created_at, updated_at
) VALUES (
    %(source_type)s, %(source_id)s, %(doc_category)s,
    %(title)s, %(title_normalized)s, %(body_text)s, %(has_text)s, %(content_length)s,
    %(url)s, %(file_url)s, %(pdf_path)s, %(file_sha256)s,
    %(language)s, %(status)s, %(published_at)s, %(collected_at)s,
    NOW(), NOW()
)
ON CONFLICT (source_type, source_id) DO UPDATE SET
    doc_category     = EXCLUDED.doc_category,
    title            = EXCLUDED.title,
    title_normalized = EXCLUDED.title_normalized,
    body_text        = EXCLUDED.body_text,
    has_text         = EXCLUDED.has_text,
    content_length   = EXCLUDED.content_length,
    url              = EXCLUDED.url,
    file_url         = EXCLUDED.file_url,
    pdf_path         = EXCLUDED.pdf_path,
    file_sha256      = COALESCE(EXCLUDED.file_sha256, documents.file_sha256),
    language         = EXCLUDED.language,
    status           = EXCLUDED.status,
    published_at     = EXCLUDED.published_at,
    collected_at     = EXCLUDED.collected_at,
    updated_at       = NOW()
RETURNING id, (xmax = 0) AS inserted;
"""


def upsert_document(cur, row: dict) -> tuple[int, bool]:
    cur.execute(DOC_UPSERT_SQL, row)
    rec = cur.fetchone()
    return int(rec[0]), bool(rec[1])


# ---------------------------------------------------------------------------
# 메인 (KOSHA Guide)
# ---------------------------------------------------------------------------

def build_guide_row(item: dict, *, file_url: str | None, pdf_path: str | None,
                    file_sha256: str | None) -> dict:
    source_id = str(item.get("techGdlnNo") or "").strip()
    title = str(item.get("techGdlnNm") or "").strip()
    body = strip_html(item.get("techGdlnMtxtCn") or "")
    body = body if body else None
    return dict(
        source_type="kosha_form",
        source_id=source_id,
        doc_category="kosha_guide",
        title=title,
        title_normalized=title,
        body_text=body,
        has_text=bool(body),
        content_length=len(body) if body else 0,
        url=f"{PORTAL}/archive/resources/tech-support/search/all",
        file_url=file_url,
        pdf_path=pdf_path,
        file_sha256=file_sha256,
        language="ko",
        status=status_from_kosha(item.get("techGdlnSttsSeCdSt")),
        published_at=parse_ymd(item.get("techGdlnOfancYmd")),
        collected_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def collect_tech_guide(args) -> int:
    cat_dir = RAW_ROOT / "tech_guide"
    files_dir = cat_dir / "files"
    cat_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cat_dir / "manifest.json"
    index_path = cat_dir / "index.json"

    client = KoshaPortalClient(rate=args.rate)

    # 1단계: 전체 목록 수집
    print(f"[LIST] fetching KOSHA Guide list (rows={args.rows}, max_pages={args.max_pages})")
    all_items: list[dict] = []
    page = 1
    total_count = None
    while page <= args.max_pages:
        try:
            resp = client.tech_guide_list(page=page, rows=args.rows,
                                          category_cd=args.category if args.category != "all" else "")
        except Exception as e:
            print(f"  [ERR] list page={page}: {e!r}")
            break
        payload = resp.get("payload") or {}
        items = payload.get("list") or []
        if not items:
            break
        if total_count is None:
            total_count = items[0].get("totalCount")
        all_items.extend(items)
        print(f"  page={page}: +{len(items)} (누적 {len(all_items)}/{total_count})")
        if total_count and len(all_items) >= int(total_count):
            break
        page += 1

    # 인덱스 저장
    if not args.dry_run:
        with index_path.open("w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "total_count": total_count, "items": all_items},
                      f, ensure_ascii=False, indent=2)
        print(f"[INDEX] saved: {index_path}")

    if args.limit > 0:
        all_items = all_items[: args.limit]
    print(f"[PLAN] 처리 대상: {len(all_items)} items")

    # DB
    conn = None
    if not args.dry_run and not args.no_db:
        try:
            conn = get_db_connection()
        except Exception as e:
            print(f"[WARN] DB 접속 실패, DB upsert 생략: {e!r}")
            conn = None

    # 2-3단계: 파일 목록 + 다운로드 + DB
    stats = dict(total=len(all_items), file_ok=0, file_skip=0, file_fail=0,
                 no_file=0, db_inserted=0, db_updated=0, db_failed=0)
    manifest_entries: list[dict] = []

    for idx, it in enumerate(all_items, start=1):
        source_id = str(it.get("techGdlnNo") or "").strip()
        file_id = str(it.get("techGdlnOrgnlAtcflNo") or "").strip()
        title = str(it.get("techGdlnNm") or "").strip()
        entry = {"source_id": source_id, "title": title, "fileId": file_id,
                 "files": []}

        file_url = None
        pdf_path_rel = None
        file_sha256 = None

        if args.dry_run:
            print(f"  [{idx}/{len(all_items)}] {source_id} — dry-run  fileId={file_id!r}")
        elif not file_id:
            stats["no_file"] += 1
        else:
            try:
                attachments = client.file_list(file_id, only_pdf=True)
            except Exception as e:
                attachments = []
                entry["file_list_error"] = repr(e)

            if not attachments:
                stats["no_file"] += 1
            else:
                # 첫 PDF 다운로드
                att = attachments[0]
                atcfl_no = str(att.get("atcflNo") or "")
                atcfl_seq = int(att.get("atcflSeq") or 1)
                orig_name = att.get("orgnlAtchFileNm") or f"{source_id}.pdf"
                fname = sanitize(orig_name)
                out_dir = files_dir / source_id
                out_path = out_dir / fname

                if out_path.exists() and not args.no_download:
                    # 동일 파일 skip (size 기반)
                    prev_size = out_path.stat().st_size
                    expected = int(att.get("atcflSz") or 0)
                    if expected and prev_size == expected:
                        # 해시 재계산
                        h = hashlib.sha256()
                        with out_path.open("rb") as f:
                            for chunk in iter(lambda: f.read(65536), b""):
                                h.update(chunk)
                        file_sha256 = h.hexdigest()
                        stats["file_skip"] += 1
                        entry["files"].append({"ok": True, "skipped": True,
                                               "path": str(out_path),
                                               "size": prev_size, "sha256": file_sha256})
                    else:
                        out_path.unlink(missing_ok=True)

                if not out_path.exists() and not args.no_download:
                    res = client.download(atcfl_no, atcfl_seq, out_path)
                    entry["files"].append(res)
                    if res.get("ok"):
                        stats["file_ok"] += 1
                        file_sha256 = res.get("sha256")
                    else:
                        stats["file_fail"] += 1

                file_url = (f"{PORTAL}/api/portal24/bizA/p/files/downloadAtchFile"
                            f"?atcflNo={atcfl_no}&atcflSeq={atcfl_seq}")
                if out_path.exists():
                    pdf_path_rel = str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/")

        manifest_entries.append(entry)

        # DB upsert
        if conn is not None and source_id and title:
            row = build_guide_row(it, file_url=file_url, pdf_path=pdf_path_rel,
                                  file_sha256=file_sha256)
            try:
                with conn.cursor() as cur:
                    doc_id, inserted = upsert_document(cur, row)
                conn.commit()
                if inserted:
                    stats["db_inserted"] += 1
                else:
                    stats["db_updated"] += 1
            except Exception as e:
                conn.rollback()
                stats["db_failed"] += 1
                entry["db_error"] = repr(e)

        if idx % 20 == 0:
            print(f"  진행: {idx}/{len(all_items)}  {stats}")

    if not args.dry_run:
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "stats": stats, "entries": manifest_entries},
                      f, ensure_ascii=False, indent=2)
        print(f"[MANIFEST] {manifest_path}")

    if conn is not None:
        conn.close()

    print()
    print("[요약] KOSHA Guide")
    for k, v in stats.items():
        print(f"  - {k:<12} {v}")
    return 0


# ---------------------------------------------------------------------------
# 엔트리
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="all",
                    help="techGdlnCtgryCd: all | A | B | C | D | E")
    ap.add_argument("--rows", type=int, default=100)
    ap.add_argument("--max-pages", type=int, default=999)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-download", action="store_true")
    ap.add_argument("--no-db", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rate", type=float, default=0.6)
    args = ap.parse_args()
    return collect_tech_guide(args)


if __name__ == "__main__":
    sys.exit(main())

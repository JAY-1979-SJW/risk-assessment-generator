"""
고용노동부 정책자료실(https://www.moel.go.kr/policy/policydata/) 안전보건·서식 수집기.

구현:
    HTML 스크래핑 기반 (requests + 정규식). SPA 아님.

흐름:
    1) LIST:   /policy/policydata/list.do?bbsCd=OMP_BBS_2&pageIndex=N
       → <tbody> 내 tr 파싱, bbs_seq 와 title 수집.
    2) 필터:   안전/보건 관련 키워드로 제목 필터링 (위험성평가/TBM/점검표/서식 등).
    3) DETAIL: /policy/policydata/view.do?bbs_seq=<seq>
       → 첨부파일 영역의 /common/downloadFile.do?file_seq=...&bbs_seq=...&file_ext=... 추출.
    4) DOWNLOAD: /common/downloadFile.do?file_seq=...&bbs_seq=...&bbs_id=29&file_ext=<ext>
    5) DB UPSERT: documents(source_type='moel_form', doc_category='moel_policy_data',
                             source_id=bbs_seq).

idempotent:
    - 동일 파일 skip (size + sha256)
    - ON CONFLICT (source_type, source_id) DO UPDATE

옵션:
    --bbs-cd BOARD           기본 OMP_BBS_2 (정책자료)
    --max-pages N            목록 페이지 상한 (기본 999)
    --keywords "a,b,c"       추가 키워드(OR). 제공 시 기본 safety 키워드와 병합
    --collect-all            키워드 필터 비활성 (전량 수집 — 경고)
    --limit N                필터 후 최대 처리 건수
    --no-download / --no-db / --dry-run
    --rate SECONDS           호출 간격 (기본 0.5)
"""
from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "moel_forms"
RAW_ROOT.mkdir(parents=True, exist_ok=True)

BASE = "https://www.moel.go.kr"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "Chrome/120.0.0.0 Safari/537.36")

# 직접 통과 — 안전·보건 도메인이 확실한 핵심 키워드
STRONG_KEYWORDS = [
    "위험성평가", "위험성 평가",
    "산업안전보건", "산업안전", "산업보건", "안전보건",
    "산업재해", "중대재해", "재해예방",
    "유해위험", "유해·위험", "유해위험방지", "밀폐공간",
    "작업환경개선", "인간공학",
    "안전보건길잡이", "안전보건 길잡이",
    "안전보건지침", "안전보건 지침",
    "TBM", "작업전 안전점검", "작업 전 안전점검",
    "표준작업절차",
    "위험성평가표",
]

# 서식·지침·체크리스트 — 단독으로는 부족, 안전도메인 컨텍스트와 함께 있을 때만 통과
FORM_KEYWORDS = [
    "서식", "양식", "점검표", "체크리스트", "교육일지",
    "지침", "매뉴얼", "가이드", "길잡이", "안내서",
    "제출서", "신청서", "보고서식",
]

# 서식/지침 키워드 옆에 붙었을 때 안전 컨텍스트 인정
DOMAIN_TAG_RE = r"(안전|보건|위험|재해|유해|밀폐|석면|소음|진동|산재|밀폐공간|추락 방지|추락방지|근골격|유해화학)"

# 비안전 제외 키워드 — 서식이더라도 이 키워드 포함시 스킵
EXCLUDE_PATTERNS = [
    # 사고·통계·사례 (form 아님)
    "추락사고", "사망사고 발생", "사망사고 현황", "추락으로 1명",
    "재해현황", "산업재해 현황", "부가통계", "사이렌", "재해조사",
    "사망재해", "재해발생",
    # 비안전 노무·복지·인사
    "인센티브", "일손부족", "채용", "일자리",
    "최저임금", "근로시간단축", "근로시간 단축",
    "여성", "청년", "고령", "직장내성희롱",
    "직업훈련", "고용장려금", "고용보험", "경력지원",
    "중장년", "동행", "임금채권", "근로복지", "공무원",
    "장애인공무원", "우선고용", "사내근로복지기금",
    "근로기준법", "시행규칙서식",
    "취직인허증",
]

# ---------------------------------------------------------------------------
# 유틸
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

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = _TAG_RE.sub(" ", s)
    s = html_lib.unescape(s)
    return _WS_RE.sub(" ", s).strip()


# ---------------------------------------------------------------------------
# 클라이언트
# ---------------------------------------------------------------------------

class MoelClient:
    def __init__(self, rate: float = 0.5) -> None:
        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml",
        })
        self.rate = rate

    def _get(self, path: str, params: dict | None = None, *, stream: bool = False):
        url = BASE + path
        for attempt in range(1, 4):
            try:
                r = self.s.get(url, params=params, verify=False, timeout=30, stream=stream)
                if r.status_code == 200:
                    return r
                time.sleep(attempt)
            except Exception:
                time.sleep(attempt)
        raise RuntimeError(f"GET {path} 실패")

    def list_page(self, bbs_cd: str, page: int) -> str:
        time.sleep(self.rate)
        return self._get("/policy/policydata/list.do",
                         {"bbsCd": bbs_cd, "pageIndex": page, "_": 1}).text

    def detail(self, bbs_seq: str) -> str:
        time.sleep(self.rate)
        return self._get("/policy/policydata/view.do",
                         {"bbs_seq": bbs_seq}).text

    def download(self, file_seq: str, bbs_seq: str, bbs_id: str, file_ext: str,
                 out_path: Path) -> dict:
        params = {"file_seq": file_seq, "bbs_seq": bbs_seq,
                  "bbs_id": bbs_id, "file_ext": file_ext}
        time.sleep(self.rate)
        try:
            r = self._get("/common/downloadFile.do", params, stream=True)
            ctype = r.headers.get("Content-Type", "")
            # HTML 응답 = 세션/WAF 실패
            if "text/html" in ctype.lower() and "application" not in ctype.lower():
                return {"ok": False, "error": f"got HTML: {ctype}"}
            out_path.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256()
            total = 0
            with out_path.open("wb") as f:
                for chunk in r.iter_content(65536):
                    if not chunk:
                        continue
                    f.write(chunk); h.update(chunk); total += len(chunk)
            return {"ok": True, "size": total, "sha256": h.hexdigest(),
                    "content_type": ctype, "path": str(out_path)}
        except Exception as e:
            return {"ok": False, "error": repr(e)}


# ---------------------------------------------------------------------------
# 파서
# ---------------------------------------------------------------------------

_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
_BBS_RE = re.compile(r"bbs_seq=(\d+)")

def parse_list_html(html: str) -> list[dict]:
    items: list[dict] = []
    tbody = re.search(r"<tbody[^>]*>(.*?)</tbody>", html, re.DOTALL)
    body = tbody.group(1) if tbody else html
    for tr in _TR_RE.findall(body):
        tds = _TD_RE.findall(tr)
        if not tds:
            continue
        m = _BBS_RE.search(tr)
        if not m:
            continue
        bbs_seq = m.group(1)
        # 제목 텍스트는 대개 두번째 td 의 <a> 내부
        title = ""
        dept = ""
        date = ""
        for td in tds:
            text = clean_text(td)
            if not title and len(text) > 5 and not text.isdigit():
                # 제목 후보
                if bbs_seq in tr:
                    title = text[:500]
                    break
        # 제목을 못 찾으면 td 전체 중 긴 것 선택
        if not title:
            texts = [clean_text(td) for td in tds]
            texts = [t for t in texts if len(t) > 5]
            title = texts[0] if texts else ""
        # 담당부서 / 날짜는 각 td에서 추정
        plain_tds = [clean_text(td) for td in tds]
        for t in plain_tds:
            if re.match(r"^\d{4}[./-]\d{2}[./-]\d{2}$", t):
                date = t
        items.append({
            "bbs_seq": bbs_seq,
            "title": title,
            "row_dates": [t for t in plain_tds if re.match(r"\d{4}", t)],
            "raw_date": date,
        })
    return items


_ATTACH_A_RE = re.compile(
    r'href="(/common/downloadFile\.do\?[^"]+)"[^>]*title="([^"]+)"'
)

def parse_detail_html(html: str) -> dict:
    """detail 페이지에서 제목/본문/첨부파일 목록 추출."""
    out: dict = {"title": None, "body_text": None, "attachments": []}

    # 첨부파일
    for m in _ATTACH_A_RE.finditer(html):
        href = html_lib.unescape(m.group(1))
        filename_title = html_lib.unescape(m.group(2)).strip()
        q = re.search(r"file_seq=(\d+)", href)
        b = re.search(r"bbs_seq=(\d+)", href)
        i = re.search(r"bbs_id=(\d+)", href)
        e = re.search(r"file_ext=(\w+)", href)
        # 같은 파일이 다운로드/바로보기 2개 href로 나오는 경우 중복 제거
        key = (q.group(1) if q else "", e.group(1) if e else "")
        if any((a.get("file_seq"), a.get("file_ext")) == key for a in out["attachments"]):
            continue
        out["attachments"].append({
            "file_seq": q.group(1) if q else None,
            "bbs_seq": b.group(1) if b else None,
            "bbs_id": i.group(1) if i else "29",
            "file_ext": e.group(1).lower() if e else "",
            "orig_name": re.sub(r"\s+다운로드$", "", filename_title).strip(),
            "href": href,
        })

    # 제목
    m = re.search(r'class="subject"[^>]*>([^<]+)</', html)
    if m:
        out["title"] = clean_text(m.group(1))
    if not out["title"]:
        m = re.search(r"<title>([^<]+)</title>", html)
        if m:
            out["title"] = clean_text(m.group(1)).replace("| 고용노동부", "").strip()

    # 본문 (view_cont 또는 bbs_content)
    for cls in ("view_cont", "bbs_content", "view_content", "board_view"):
        m = re.search(rf'class="{cls}[^"]*"[^>]*>(.*?)</div>\s*<', html, re.DOTALL)
        if m:
            text = clean_text(m.group(1))
            if text and len(text) > 30:
                out["body_text"] = text[:8000]
                break
    return out


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


UPSERT_SQL = """
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
) ON CONFLICT (source_type, source_id) DO UPDATE SET
    doc_category     = EXCLUDED.doc_category,
    title            = EXCLUDED.title,
    title_normalized = EXCLUDED.title_normalized,
    body_text        = COALESCE(EXCLUDED.body_text, documents.body_text),
    has_text         = EXCLUDED.has_text OR documents.has_text,
    content_length   = GREATEST(EXCLUDED.content_length, documents.content_length),
    url              = EXCLUDED.url,
    file_url         = COALESCE(EXCLUDED.file_url, documents.file_url),
    pdf_path         = COALESCE(EXCLUDED.pdf_path, documents.pdf_path),
    file_sha256      = COALESCE(EXCLUDED.file_sha256, documents.file_sha256),
    language         = EXCLUDED.language,
    status           = EXCLUDED.status,
    published_at     = COALESCE(EXCLUDED.published_at, documents.published_at),
    collected_at     = EXCLUDED.collected_at,
    updated_at       = NOW()
RETURNING id, (xmax = 0) AS inserted;
"""


def upsert_doc(cur, row: dict) -> tuple[int, bool]:
    cur.execute(UPSERT_SQL, row)
    rec = cur.fetchone()
    return int(rec[0]), bool(rec[1])


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def build_row(item_list: dict, detail: dict, *, file_url: str | None,
              pdf_path: str | None, file_sha256: str | None) -> dict:
    bbs_seq = item_list["bbs_seq"]
    title = detail.get("title") or item_list.get("title") or ""
    body = detail.get("body_text")
    raw_date = (item_list.get("raw_date") or "").replace(".", "-").replace("/", "-")
    pub = None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw_date)
    if m:
        pub = raw_date
    return dict(
        source_type="moel_form",
        source_id=bbs_seq,
        doc_category="moel_policy_data",
        title=title,
        title_normalized=title,
        body_text=body,
        has_text=bool(body),
        content_length=len(body) if body else 0,
        url=f"{BASE}/policy/policydata/view.do?bbs_seq={bbs_seq}",
        file_url=file_url,
        pdf_path=pdf_path,
        file_sha256=file_sha256,
        language="ko",
        status="active",
        published_at=pub,
        collected_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def run(args) -> int:
    client = MoelClient(rate=args.rate)

    # 1) 키워드 컴파일
    strong = list(STRONG_KEYWORDS)
    form_kw = list(FORM_KEYWORDS)
    if args.keywords:
        strong += [k.strip() for k in args.keywords.split(",") if k.strip()]
    strong_re = re.compile("|".join(re.escape(k) for k in set(strong)))
    form_re = re.compile("|".join(re.escape(k) for k in set(form_kw)))
    domain_re = re.compile(DOMAIN_TAG_RE)

    def title_match(title: str) -> bool:
        if not title:
            return False
        if strong_re.search(title):
            return True
        # 서식/지침 키워드는 안전 컨텍스트가 있을 때만 통과
        if form_re.search(title) and domain_re.search(title):
            return True
        return False

    out_cat = RAW_ROOT / "policy_data"
    out_cat.mkdir(parents=True, exist_ok=True)
    files_dir = out_cat / "files"

    all_items: list[dict] = []
    for page in range(1, args.max_pages + 1):
        try:
            html = client.list_page(args.bbs_cd, page)
        except Exception as e:
            print(f"  [ERR] list p{page}: {e!r}")
            break
        items = parse_list_html(html)
        if not items:
            print(f"  p{page}: 0건 — 종료")
            break
        all_items.extend(items)
        if page % 20 == 0 or page == 1:
            print(f"  list p{page}: +{len(items)} (누적 {len(all_items)})")
        if len(items) < 10:
            # 마지막 페이지 추정
            break
    print(f"[LIST] 전체 {len(all_items)}건 수집")

    # 2) 키워드 필터 (STRONG 단독 / FORM+도메인 컨텍스트 / 제외 키워드 차단)
    excl_re = re.compile("|".join(re.escape(e) for e in EXCLUDE_PATTERNS))
    if args.collect_all:
        filtered = all_items
    else:
        filtered = [
            it for it in all_items
            if title_match(it.get("title") or "")
            and not excl_re.search(it.get("title") or "")
        ]
    print(f"[FILTER] 안전/보건 키워드 매칭: {len(filtered)}건 (전체 {len(all_items)})")
    if args.limit > 0:
        filtered = filtered[: args.limit]

    # 전체 목록 JSON 저장
    if not args.dry_run:
        with (out_cat / "list_all.json").open("w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "bbs_cd": args.bbs_cd, "total": len(all_items),
                       "filtered_count": len(filtered), "filtered": filtered},
                      f, ensure_ascii=False, indent=2)

    conn = None
    if not args.dry_run and not args.no_db:
        try:
            conn = get_db_connection()
        except Exception as e:
            print(f"[WARN] DB 접속 실패: {e!r}")
            conn = None

    stats = dict(total=len(filtered), detail_ok=0, detail_fail=0,
                 no_attach=0, file_ok=0, file_skip=0, file_fail=0,
                 db_inserted=0, db_updated=0, db_failed=0)
    manifest: list[dict] = []

    for idx, it in enumerate(filtered, start=1):
        bbs_seq = it["bbs_seq"]
        entry = {"bbs_seq": bbs_seq, "title": it.get("title"), "attachments": []}

        if args.dry_run:
            print(f"  [{idx}] {bbs_seq} — dry-run  title={it.get('title','')[:40]}")
            manifest.append(entry)
            continue

        # detail
        try:
            detail_html = client.detail(bbs_seq)
            detail = parse_detail_html(detail_html)
            stats["detail_ok"] += 1
        except Exception as e:
            detail = {"title": it.get("title"), "body_text": None, "attachments": []}
            stats["detail_fail"] += 1
            entry["detail_error"] = repr(e)

        attachments = detail.get("attachments") or []
        if not attachments:
            stats["no_attach"] += 1

        # 첫 번째 첨부(선호 pdf > hwp > 나머지) 다운로드
        first_attach_file_url = None
        first_pdf_path = None
        first_sha = None
        sorted_atts = sorted(attachments,
                             key=lambda a: {"pdf": 0, "hwp": 1, "hwpx": 1}.get(a.get("file_ext", ""), 3))
        if not args.no_download and sorted_atts:
            for att in sorted_atts:
                file_seq = att.get("file_seq")
                file_ext = att.get("file_ext") or "bin"
                if not file_seq:
                    continue
                orig = att.get("orig_name") or f"{bbs_seq}.{file_ext}"
                fname = sanitize(orig)
                out_dir = files_dir / bbs_seq
                out_path = out_dir / fname
                if out_path.exists():
                    h = hashlib.sha256()
                    with out_path.open("rb") as f:
                        for chunk in iter(lambda: f.read(65536), b""):
                            h.update(chunk)
                    res = {"ok": True, "skipped": True, "path": str(out_path),
                           "size": out_path.stat().st_size, "sha256": h.hexdigest()}
                    stats["file_skip"] += 1
                else:
                    res = client.download(file_seq, att.get("bbs_seq") or bbs_seq,
                                          att.get("bbs_id") or "29", file_ext, out_path)
                    if res.get("ok"):
                        stats["file_ok"] += 1
                    else:
                        stats["file_fail"] += 1
                entry["attachments"].append({**att, **res})
                if res.get("ok") and first_attach_file_url is None:
                    first_attach_file_url = BASE + att["href"]
                    first_pdf_path = str(Path(res["path"]).relative_to(PROJECT_ROOT)).replace("\\", "/")
                    first_sha = res.get("sha256")

        # DB upsert
        if conn is not None:
            row = build_row(it, detail, file_url=first_attach_file_url,
                            pdf_path=first_pdf_path, file_sha256=first_sha)
            if row["title"]:
                try:
                    with conn.cursor() as cur:
                        doc_id, inserted = upsert_doc(cur, row)
                    conn.commit()
                    if inserted:
                        stats["db_inserted"] += 1
                    else:
                        stats["db_updated"] += 1
                except Exception as e:
                    conn.rollback()
                    stats["db_failed"] += 1
                    entry["db_error"] = repr(e)

        manifest.append(entry)

        if idx % 20 == 0:
            print(f"  진행: {idx}/{len(filtered)}  {stats}")

    if not args.dry_run:
        with (out_cat / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "stats": stats, "entries": manifest},
                      f, ensure_ascii=False, indent=2)

    if conn is not None:
        conn.close()

    print("\n[요약] MOEL policy data")
    for k, v in stats.items():
        print(f"  - {k:<12} {v}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbs-cd", default="OMP_BBS_2")
    ap.add_argument("--max-pages", type=int, default=999)
    ap.add_argument("--keywords", default="")
    ap.add_argument("--collect-all", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-download", action="store_true")
    ap.add_argument("--no-db", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rate", type=float, default=0.5)
    args = ap.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())

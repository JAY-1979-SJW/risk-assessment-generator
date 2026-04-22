"""
KOSHA 안전보건자료 수집기 (OPS + 기타 목록 기준)

수집 흐름:
1. Playwright 로그인 → 세션 쿠키 + shpCd 파라미터 확보
2. requests + 쿠키 → selectMediaList API 페이지네이션
3. contsAtcflNo → PDF 다운로드 → PyMuPDF/pdfminer 텍스트 추출
4. data/raw/kosha/kosha_{category}_{id}.json 저장

환경변수:
  KOSHA_ID  (없으면 dry-run)
  KOSHA_PW  (없으면 dry-run)

CLAUDE.md 수집 범위:
  대상 list_type: OPS(1), 기타(5)
  제외 list_type: 동영상(2), 외국어교재(3), 외국어교안(4)
"""
import hashlib
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from ._base import get_logger, save_json, write_status, now_iso, ROOT, get_env

log = get_logger("kosha_collector")

BASE       = "https://portal.kosha.or.kr"
LIST_API   = f"{BASE}/api/portal24/bizV/p/VCPDG01007/selectMediaList"
DL_BASE    = f"{BASE}/api/portal24/bizA/p/files/downloadAtchFile"
OUT_DIR    = ROOT / "data" / "raw" / "kosha"
DELAY      = 1.0
TEXT_MIN   = 500  # has_text 판정 기준 글자 수

INDUSTRIES = {1: "제조업", 2: "건설업", 3: "서비스업", 4: "조선업", 5: "기타산업"}
LIST_TYPES = {1: "OPS", 5: "기타"}  # 수집 대상만

CATEGORY_MAP = {
    "OPS": "kosha_opl",
    "기타": "kosha_edu",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


class KoshaCollector:
    def __init__(self):
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        self._seen: set[str] = self._load_seen()
        self._kosha_id = get_env("KOSHA_ID")
        self._kosha_pw = get_env("KOSHA_PW")

    def _load_seen(self) -> set[str]:
        seen = set()
        for f in OUT_DIR.glob("kosha_*.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                uid = d.get("item_id", "")
                if uid:
                    seen.add(uid)
            except Exception:
                pass
        return seen

    # ── Playwright 로그인 + shpCd 캡처 ──────────────────────────────────────

    def _playwright_setup(self) -> tuple[dict, dict]:
        """Playwright로 로그인 → (cookies dict, section_params dict) 반환."""
        from playwright.sync_api import sync_playwright

        section_params = {}  # {(ind, lst_type_key): {'shpCd', 'menuMode', 'menuCode'}}
        cookies_dict = {}

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})

            # 요청 인터셉트 — selectMediaList 파라미터 캡처
            last_body: dict = {}

            def on_request(req):
                if "selectMediaList" in req.url and req.post_data:
                    try:
                        body = json.loads(req.post_data)
                        if body.get("page", 0) == 1:
                            last_body.clear()
                            last_body.update(body)
                    except Exception:
                        pass

            page.on("request", on_request)

            # 로그인
            log.info("Playwright 로그인 시작")
            page.goto(f"{BASE}/", timeout=60000)
            page.wait_for_load_state("networkidle")
            page.locator("a:has-text('로그인')").first.click()
            page.wait_for_timeout(2000)
            for _ in range(10):
                if page.evaluate("!!document.querySelector('.popup')"):
                    break
                page.wait_for_timeout(500)
            page.evaluate("const p=document.querySelector('.popup'); if(p) p.style.display='block'")
            page.eval_on_selector(
                ".inputGroup input[type=text]",
                f"el=>{{el.value='{self._kosha_id}';el.dispatchEvent(new Event('input',{{bubbles:true}}))}}"
            )
            page.eval_on_selector(
                ".password input[type=password]",
                f"el=>{{el.value='{self._kosha_pw}';el.dispatchEvent(new Event('input',{{bubbles:true}}))}}"
            )
            page.eval_on_selector(
                "section.login",
                "el=>{const btn=el.querySelector('button[type=button]');if(btn)btn.click()}"
            )
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            logged_in = page.locator("button:has-text('로그아웃')").count() > 0
            if not logged_in:
                log.error("KOSHA 로그인 실패")
                browser.close()
                return {}, {}
            log.info("로그인 성공")

            # 각 섹션 방문 → shpCd 캡처
            for ind in range(1, 6):
                for lst in (1, 5):  # OPS, 기타
                    last_body.clear()
                    url = (
                        f"{BASE}/archive/cent-archive/indust-arch"
                        f"/indust-page{ind}/indust-page{ind}-list{lst}"
                        f"?page=1&rowsPerPage=12"
                    )
                    page.goto(url, timeout=60000)
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(1000)
                    if last_body.get("shpCd"):
                        section_params[(ind, lst)] = {
                            "shpCd":    last_body["shpCd"],
                            "menuMode": last_body.get("menuMode", "1"),
                            "menuCode": last_body.get("menuCode", ""),
                        }
                        log.info(
                            f"  [{INDUSTRIES[ind]}-{LIST_TYPES[lst]}] "
                            f"shpCd={last_body['shpCd']}"
                        )
                    else:
                        log.warning(f"  [{INDUSTRIES[ind]}-{LIST_TYPES[lst]}] shpCd 없음")

            # 쿠키 추출
            cookies_dict = {c["name"]: c["value"] for c in page.context.cookies()}
            browser.close()

        log.info(f"섹션 파라미터 확보: {len(section_params)}/10")
        return cookies_dict, section_params

    # ── requests로 목록 수집 ─────────────────────────────────────────────────

    def _fetch_section_list(
        self,
        session: requests.Session,
        params: dict,
        industry: str,
        list_type: str,
    ) -> list[dict]:
        category = CATEGORY_MAP.get(list_type, "kosha_etc")
        items_all = []
        page_num, total_pages = 1, 1

        while page_num <= total_pages:
            payload = {
                "shpCd":           params["shpCd"],
                "menuMode":        params["menuMode"],
                "menuCode":        params["menuCode"],
                "searchCondition": "all",
                "searchValue":     None,
                "page":            page_num,
                "rowsPerPage":     100,
                "ascDesc":         "desc",
            }
            try:
                r = session.post(
                    LIST_API,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=20,
                )
                r.raise_for_status()
                result = r.json()
            except Exception as e:
                log.warning(f"목록 API 실패 [{industry}-{list_type} p{page_num}]: {e}")
                break

            items = result.get("payload", {}).get("list", [])
            if page_num == 1:
                total = items[0].get("totalCount", 0) if items else 0
                total_pages = max(1, (total + 99) // 100)
                log.info(f"  [{industry}-{list_type}] 총 {total}건 / {total_pages}p")

            for item in items:
                atcfl_no = item.get("contsAtcflNo", "")
                items_all.append({
                    "item_id":    str(item.get("medSeq", "")),
                    "title":      item.get("medName", "").strip(),
                    "category":   category,
                    "industry":   industry,
                    "list_type":  list_type,
                    "atcfl_no":   atcfl_no,
                    "download_url": (
                        f"{DL_BASE}?atcflNo={atcfl_no}&atcflSeq=1" if atcfl_no else ""
                    ),
                    "reg_date":   item.get("contsRegYmd", ""),
                    "keyword":    item.get("medKeyword", ""),
                })

            log.info(f"    p{page_num}/{total_pages}: {len(items)}건 | 누적 {len(items_all)}")
            page_num += 1
            time.sleep(DELAY)

        return items_all

    # ── PDF 다운로드 + 텍스트 추출 ──────────────────────────────────────────

    def _parse_pdf(self, session: requests.Session, dl_url: str) -> tuple[str, bool]:
        if not dl_url:
            return "", False
        try:
            r = session.get(dl_url, timeout=(10, 60), stream=False)
            r.raise_for_status()
            content = r.content
            if not content or not content.startswith(b"%PDF"):
                return "", False
            return self._extract_text(content)
        except Exception as e:
            log.debug(f"PDF 다운로드 실패 [{dl_url}]: {e}")
            return "", False

    def _extract_text(self, content: bytes) -> tuple[str, bool]:
        try:
            import fitz
            doc = fitz.open(stream=io.BytesIO(content), filetype="pdf")
            text = "\n".join(p.get_text() for p in doc)
            doc.close()
            t = text.strip()
            return t[:8000], len(t) >= TEXT_MIN
        except ImportError:
            pass
        except Exception as e:
            log.debug(f"PyMuPDF 오류: {e}")
        try:
            from pdfminer.high_level import extract_text_to_fp
            from pdfminer.layout import LAParams
            buf = io.BytesIO()
            extract_text_to_fp(io.BytesIO(content), buf, laparams=LAParams())
            t = buf.getvalue().decode("utf-8", errors="ignore").strip()
            return t[:8000], len(t) >= TEXT_MIN
        except Exception as e:
            log.debug(f"pdfminer 오류: {e}")
        return "", False

    # ── 저장 ─────────────────────────────────────────────────────────────────

    def _save(self, record: dict) -> None:
        uid = record["item_id"] or hashlib.md5(record["title"].encode()).hexdigest()[:12]
        path = OUT_DIR / f"kosha_{record['category']}_{uid}.json"
        save_json(path, record)

    # ── 메인 ─────────────────────────────────────────────────────────────────

    def run(self) -> bool:
        if not self._kosha_id:
            log.warning("KOSHA_ID 미설정 — dry-run")
            self._report(0, 0, 0, dry_run=True)
            write_status("kosha_guides", "DRY_RUN", 0, 0)
            return False

        # 1. Playwright 인증 + shpCd 확보
        cookies, section_params = self._playwright_setup()
        if not cookies:
            log.error("인증 실패 — 중단")
            write_status("kosha_guides", "FAIL", 0, 1)
            return False

        # 2. requests 세션 구성
        session = requests.Session()
        session.headers.update(HEADERS)
        session.cookies.update(cookies)

        # 3. 섹션별 수집
        total, has_text_cnt, fail_cnt = 0, 0, 0

        for (ind, lst), params in sorted(section_params.items()):
            industry  = INDUSTRIES[ind]
            list_type = LIST_TYPES[lst]
            items = self._fetch_section_list(session, params, industry, list_type)

            for item in items:
                uid = item["item_id"]
                if uid in self._seen:
                    continue
                self._seen.add(uid)

                content, has_text = "", False
                if item["download_url"]:
                    content, has_text = self._parse_pdf(session, item["download_url"])
                    if item["download_url"] and not has_text and not content:
                        fail_cnt += 1
                    time.sleep(DELAY)

                record = {
                    **item,
                    "source":       "kosha",
                    "url":          item["download_url"],
                    "file_url":     item["download_url"],
                    "content":      content,
                    "has_text":     has_text,
                    "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                }
                self._save(record)
                total += 1
                if has_text:
                    has_text_cnt += 1

        self._report(total, has_text_cnt, fail_cnt)
        status = "SUCCESS" if total >= 100 else ("PARTIAL" if total > 0 else "FAIL")
        write_status("kosha_guides", status, total, fail_cnt)
        return total > 0

    def _report(self, total: int, has_text: int, fail: int, dry_run: bool = False) -> None:
        ratio = has_text / total * 100 if total else 0
        if dry_run:
            verdict = "SKIP (KOSHA_ID 미설정)"
        else:
            verdict = "PASS" if total >= 100 and ratio >= 70 else ("WARN" if total >= 10 else "FAIL")

        log.info("=" * 52)
        log.info(f"총 수집 건수  : {total}")
        log.info(f"has_text 비율 : {has_text}/{total} ({ratio:.1f}%)")
        log.info(f"실패 건수     : {fail}")
        log.info(f"검증 결과     : {verdict}")
        log.info(f"저장 경로     : {OUT_DIR}")
        log.info("=" * 52)
        print(f"\n{'='*52}")
        print(f"총 수집 건수  : {total}")
        print(f"has_text 비율 : {has_text}/{total} ({ratio:.1f}%)")
        print(f"실패 건수     : {fail}")
        print(f"검증 결과     : {verdict}")
        print(f"{'='*52}\n")


def run() -> bool:
    return KoshaCollector().run()


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

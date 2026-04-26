"""
kosha_sif_scraper.py — KOSHA 포털 산업재해 사고사례 수집 (Playwright)
출처: https://portal.kosha.or.kr/archive/disaster-case/accident-case
수집: stdtboard 렌더링 HTML 파싱 → No, 제목, 작성자, 등록일, 조회수
출력: data/raw/kosha_external/kosha_sif_cases.jsonl

환경변수: KOSHA_ID, KOSHA_PW  (scraper/.env)

bbsId 목록 (portal24 stdtboard)
  B2025022104001  중대재해 사고백서 (3건, PDF)
  B2025022104002  제조업 사고사례 (1,427건) ← 메인 수집 대상

API (POST): /api/compn24/auth/stdtboard/process.do
  - serviceId=getBbsDefaultInfo: 게시판 컬럼 정의
  - serviceId=basicAccess: 목록 조회 (페이지 파라미터: curPageCo, rowsPerPage)
  목록에서 artclValueGrid는 조회수(D020100004)만 반환;
  제목·등록일은 Playwright로 렌더링된 HTML에서 파싱
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from scripts.collect._base import get_logger, ROOT

# ── 설정 ──────────────────────────────────────────────────────────────────────
load_dotenv(ROOT / "scraper" / ".env")

BASE_URL = "https://portal.kosha.or.kr"
LIST_URL = f"{BASE_URL}/archive/disaster-case/accident-case"

OUT_DIR = ROOT / "data" / "raw" / "kosha_external"
OUT_FILE = OUT_DIR / "kosha_sif_cases.jsonl"
META_FILE = OUT_DIR / "kosha_sif_cases_meta.json"

PAGE_LOAD_WAIT = 5000   # 페이지 로드 대기 ms
DELAY = 0.5              # 페이지 간 지연 초


def _parse_tboard(html: str) -> list[dict]:
    """렌더링된 stdtboard 커스텀 div 구조 파싱
    각 행: div.tboard_list_row > div[data-tboard-artcl-no=...] 셀들
    컬럼코드: D020100001=No, D010100001=제목, D010100003=작성자,
              D030100001=등록일, D020100004=조회수
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(".tboard_list_row")
    items = []
    for row in rows:
        cells = {
            cell.get("data-tboard-artcl-no", ""): cell
            for cell in row.find_all("div", attrs={"data-tboard-artcl-no": True})
        }
        title_el = cells.get("D010100001")
        title = ""
        if title_el:
            a = title_el.find("a", class_="tboard_list_subject")
            title = (a.get_text(strip=True) if a else title_el.get_text(strip=True))
        if not title:
            continue
        def _cell_val(el):
            if not el:
                return ""
            # tboard_list_item_title(헤더) 제거 후 텍스트
            for h in el.find_all(class_="tboard_list_item_title"):
                h.decompose()
            return el.get_text(strip=True)

        no_el = cells.get("D020100001")
        author_el = cells.get("D010100003")
        date_el = cells.get("D030100003") or cells.get("D030100001")
        view_el = cells.get("D020100004")
        items.append({
            "no": _cell_val(no_el),
            "title": title,
            "author": _cell_val(author_el),
            "reg_date": _cell_val(date_el),
            "view_count": _cell_val(view_el),
        })
    return items


def run(
    max_pages: int | None = None,
    kosha_id: str | None = None,
    kosha_pw: str | None = None,
) -> int:
    from playwright.sync_api import sync_playwright

    log = get_logger("kosha_sif_scraper")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    kosha_id = kosha_id or os.getenv("KOSHA_ID", "")
    kosha_pw = kosha_pw or os.getenv("KOSHA_PW", "")

    success = fail = total_pages_visited = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
        )
        page = ctx.new_page()

        # 로그인 시도
        if kosha_id and kosha_pw:
            try:
                page.goto(f"{BASE_URL}/com/user/login", timeout=30000, wait_until="networkidle")
                page.wait_for_timeout(2000)
                page.evaluate(f"""
                    var idEl = document.querySelector('#id') || document.querySelector('input[type=text]');
                    var pwEl = document.querySelector('input[type=password]');
                    if(idEl){{ idEl.value = '{kosha_id}'; idEl.dispatchEvent(new Event('input')); }}
                    if(pwEl){{ pwEl.value = '{kosha_pw}'; pwEl.dispatchEvent(new Event('input')); }}
                """)
                page.wait_for_timeout(300)
                page.click("button[type='submit']", timeout=3000)
                page.wait_for_timeout(2000)
                if "login" not in page.url:
                    log.info("KOSHA 로그인 성공")
                else:
                    log.warning("KOSHA 로그인 실패 — 비로그인으로 진행")
            except Exception as e:
                log.warning(f"로그인 오류: {e} — 비로그인으로 진행")

        # 1페이지 로드 → 총 건수 파악
        log.info(f"SIF 목록 수집 시작: {LIST_URL}")
        page.goto(LIST_URL, timeout=30000, wait_until="networkidle")
        page.wait_for_timeout(PAGE_LOAD_WAIT)

        # 총 건수 파악
        import re
        body_text = page.inner_text("body")
        m = re.search(r"총\s*([\d,]+)\s*건", body_text)
        total = int(m.group(1).replace(",", "")) if m else 0
        total_pages = (total + 9) // 10  # stdtboard 기본 10건/페이지
        if max_pages:
            total_pages = min(total_pages, max_pages)
        log.info(f"총 {total}건 / {total_pages}페이지 수집 예정")

        with OUT_FILE.open("w", encoding="utf-8") as fout:
            # 1페이지 파싱
            html = page.inner_html("body")
            items = _parse_tboard(html)
            for item in items:
                fout.write(json.dumps(item, ensure_ascii=False) + "\n")
                success += 1
            log.info(f"  page 1/{total_pages}: {len(items)}건")
            total_pages_visited += 1

            # 2페이지 이후: goPage(n) JS 함수 호출
            for pg in range(2, total_pages + 1):
                try:
                    page.evaluate(f"window.goPage && window.goPage('{pg}')")
                    page.wait_for_timeout(int(PAGE_LOAD_WAIT * 0.8))
                    html = page.inner_html("body")
                    items = _parse_tboard(html)
                    for item in items:
                        fout.write(json.dumps(item, ensure_ascii=False) + "\n")
                        success += 1
                    log.info(f"  page {pg}/{total_pages}: {len(items)}건")
                    total_pages_visited += 1
                    time.sleep(DELAY)
                except Exception as e:
                    log.error(f"page {pg} 실패: {e}")
                    fail += 1

        browser.close()

    meta = {
        "source": "KOSHA 포털 산업재해 사고사례 (제조업)",
        "url": LIST_URL,
        "api_url": f"{BASE_URL}/api/compn24/auth/stdtboard/process.do",
        "bbs_id": "B2025022104002",
        "total_count": total,
        "collected_records": success,
        "failed_pages": fail,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"완료: {success}건 수집, {fail}페이지 실패 → {OUT_FILE}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    max_p = None
    for a in sys.argv[1:]:
        if a.startswith("--max-pages="):
            max_p = int(a.split("=")[1])
    sys.exit(run(max_pages=max_p))

"""
KOSHA 포털 업종별·분야별 안전보건 자료 수집기
대상: https://portal.kosha.or.kr/archive/cent-archive/indust-arch
수집: 제조업/건설업/서비스업/조선업/기타 탭별 자료 목록 + 다운로드 링크
"""
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

load_dotenv(Path(__file__).parent / ".env")

ID = os.getenv("KOSHA_ID")
PW = os.getenv("KOSHA_PW")
BASE = "https://portal.kosha.or.kr"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INDUSTRY_TABS = [
    ("제조업", f"{BASE}/archive/cent-archive/indust-arch/indust-page1"),
    ("건설업", f"{BASE}/archive/cent-archive/indust-arch/indust-page2"),
    ("서비스업", f"{BASE}/archive/cent-archive/indust-arch/indust-page3"),
    ("조선업", f"{BASE}/archive/cent-archive/indust-arch/indust-page4"),
    ("기타산업", f"{BASE}/archive/cent-archive/indust-arch/indust-page5"),
]

GUIDE_URL = f"{BASE}/archive/cent-archive/field-arch"


def login(page):
    """검증된 로그인 방식 — popup 강제 표시 + eval_on_selector"""
    page.goto(f"{BASE}/", timeout=30000)
    page.wait_for_load_state("networkidle")
    page.click("a:has-text('로그인')")
    page.wait_for_timeout(2000)
    page.evaluate("document.querySelector('.popup').style.display='block'")
    page.wait_for_timeout(500)
    page.eval_on_selector(
        ".inputGroup input[type=text]",
        f"el=>{{el.value='{ID}';el.dispatchEvent(new Event('input',{{bubbles:true}}))}}"
    )
    page.eval_on_selector(
        ".password input[type=password]",
        f"el=>{{el.value='{PW}';el.dispatchEvent(new Event('input',{{bubbles:true}}))}}"
    )
    page.wait_for_timeout(300)
    page.eval_on_selector(
        "section.login",
        "el=>{const btn=el.querySelector('button[type=button]');if(btn)btn.click()}"
    )
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    ok = page.locator("button:has-text('로그아웃')").count() > 0
    print(f"[login] {'성공' if ok else '실패'} | URL: {page.url}")
    return ok


def close_popup(page):
    try:
        page.click("button:has-text('확인')", timeout=2000)
    except PlaywrightTimeout:
        pass
    try:
        page.click("button:has-text('닫기')", timeout=1000)
    except PlaywrightTimeout:
        pass


def collect_industry_data(page, name, url):
    """업종 탭별 자료 수집 — 페이지네이션 포함"""
    print(f"\n[{name}] 수집 시작: {url}")
    all_items = []

    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    close_popup(page)

    # 전체 건수 파악
    total_text = ""
    try:
        total_text = page.locator(".total, .count, [class*=total]").first.inner_text()
    except Exception:
        pass

    page_num = 1
    while True:
        # 현재 페이지 자료 수집
        items = page.eval_on_selector_all(
            ".card, article, .list-wrap li, .item-wrap .item",
            """els => els.map(e => {
                const title = e.querySelector('.title, h3, h4, .name, strong');
                const link = e.querySelector('a[href]');
                const date = e.querySelector('.date, time, [class*=date]');
                const dl = e.querySelector('a[download], .download, [class*=down]');
                return {
                    title: title ? title.innerText.trim() : e.innerText.trim().substring(0,80),
                    href: link ? link.href : '',
                    date: date ? date.innerText.trim() : '',
                    download: dl ? dl.href : ''
                };
            }).filter(i => i.title.length > 2)"""
        )

        if not items:
            # 대체 선택자
            items = page.eval_on_selector_all(
                "li, tr",
                """els => els.map(e => {
                    const a = e.querySelector('a');
                    return {title: e.innerText.trim().substring(0,100), href: a ? a.href : ''};
                }).filter(i => i.title.length > 5 && i.href)"""
            )

        all_items.extend(items)
        print(f"  페이지 {page_num}: {len(items)}개 | 누적 {len(all_items)}개")

        # 더보기 / 다음 페이지
        try:
            next_btn = page.locator("button:has-text('더보기'), a:has-text('다음'), .next, [aria-label='다음']").first
            if next_btn.is_visible():
                next_btn.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(1500)
                page_num += 1
                if page_num > 10:  # 최대 10페이지
                    break
            else:
                break
        except Exception:
            break

    result = {"name": name, "url": url, "total_text": total_text, "count": len(all_items), "items": all_items}
    print(f"  [{name}] 총 {len(all_items)}개 수집 완료")
    return result


def save(data, filename):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[save] {path} ({path.stat().st_size // 1024}KB)")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        )

        print("=== 1단계: 로그인 ===")
        login(page)

        all_results = {}

        print("\n=== 2단계: 업종별 자료 수집 ===")
        for name, url in INDUSTRY_TABS:
            result = collect_industry_data(page, name, url)
            all_results[name] = result
            save(result, f"industry_{name}.json")
            time.sleep(1)

        save(all_results, "all_industry_data.json")
        browser.close()
        print("\n=== 완료 ===")


if __name__ == "__main__":
    main()

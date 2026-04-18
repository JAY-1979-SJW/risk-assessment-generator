"""
KOSHA 포털 공종별 위험성평가 데이터 수집기
수집 대상:
  1. /kras/implement/real  - 위험성평가 실시 (공종별 체크리스트)
  2. /archive/cent-archive/indust-arch - 업종별 자료
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
BASE_URL = "https://portal.kosha.or.kr"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def login(page):
    page.goto(f"{BASE_URL}/", timeout=30000)
    page.wait_for_load_state("networkidle")
    page.click("a:has-text('로그인')")
    page.wait_for_timeout(2000)
    page.wait_for_load_state("networkidle")
    page.evaluate(f"document.getElementById('id').value = '{ID}'")
    page.evaluate(f"document.getElementById('pw').value = '{PW}'")
    try:
        page.click("button[type='submit'], .btn-login, button:has-text('로그인')", timeout=3000)
    except PlaywrightTimeout:
        page.keyboard.press("Enter")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    print(f"[login] {page.url}")


def explore_page(page, url, label):
    """페이지 구조 탐색 — 업종/공종 목록 수집"""
    print(f"\n[{label}] {url}")
    page.goto(url, timeout=30000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)

    # 페이지 전체 텍스트 및 링크 수집
    text = page.inner_text("body")
    links = page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => ({text: e.innerText.trim(), href: e.href})).filter(l => l.text.length > 1)"
    )

    # select/option 요소 (업종·공종 드롭다운)
    selects = page.eval_on_selector_all(
        "select option",
        "els => els.map(e => ({value: e.value, text: e.innerText.trim()}))"
    )

    # 버튼 목록
    buttons = page.eval_on_selector_all(
        "button, .btn",
        "els => els.map(e => e.innerText.trim()).filter(t => t.length > 1)"
    )

    result = {
        "url": url,
        "title": page.title(),
        "links_count": len(links),
        "select_options": selects,
        "buttons": buttons[:30],
        "links": [l for l in links if BASE_URL in l["href"]][:50],
        "text_preview": text[:500]
    }

    print(f"  링크: {len(links)}개 | select옵션: {len(selects)}개 | 버튼: {len(buttons)}개")
    if selects:
        print(f"  드롭다운 항목 (최대20):")
        for s in selects[:20]:
            print(f"    [{s['value']}] {s['text']}")

    return result


def save(data, filename):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[save] {path}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        ).new_page()

        print("=== 로그인 ===")
        login(page)

        results = {}

        print("\n=== 위험성평가 실시 페이지 탐색 ===")
        results["implement"] = explore_page(page, f"{BASE_URL}/kras/implement/real", "implement")

        print("\n=== 업종별 자료 페이지 탐색 ===")
        results["archive"] = explore_page(page, f"{BASE_URL}/archive/cent-archive/indust-arch", "archive")

        save(results, "page_structure.json")
        browser.close()
        print("\n=== 탐색 완료 ===")


if __name__ == "__main__":
    main()

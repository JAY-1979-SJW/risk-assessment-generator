"""
KOSHA 포털 위험성평가 공종별 자료 수집기
대상: https://portal.kosha.or.kr/
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
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

PORTAL_URL = "https://portal.kosha.or.kr/"
KRAS_URL = "https://kras.kosha.or.kr/"


def login(page):
    page.goto(PORTAL_URL, timeout=30000)
    page.wait_for_load_state("networkidle")

    # 로그인 버튼 클릭 → ssoLogin 페이지로 이동
    page.click("a:has-text('로그인')")
    page.wait_for_timeout(2000)
    page.wait_for_load_state("networkidle")
    print(f"[login] 로그인 URL: {page.url}")

    # id/pw 필드가 hidden 상태이므로 JS로 직접 값 설정 후 Enter
    page.evaluate("document.getElementById('id').value = arguments[0]", ID)
    page.evaluate("document.getElementById('pw').value = arguments[0]", PW)

    # 로그인 버튼 클릭 또는 Enter
    try:
        page.click("button[type='submit'], input[type='submit'], .btn-login, button:has-text('로그인')", timeout=3000)
    except PlaywrightTimeout:
        page.keyboard.press("Enter")

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    print(f"[login] 로그인 후 URL: {page.url}")


def explore_kras(page):
    """KRAS 시스템 공종별 체크리스트 구조 파악"""
    page.goto(KRAS_URL, timeout=30000)
    page.wait_for_load_state("networkidle")
    print(f"[kras] URL: {page.url}")
    print(f"[kras] title: {page.title()}")

    # 페이지 내 모든 링크 수집
    links = page.eval_on_selector_all("a[href]", """
        els => els.map(e => ({text: e.innerText.trim(), href: e.href}))
            .filter(l => l.text && l.text.length > 1)
    """)

    keywords = ["체크리스트", "공종", "위험성", "평가", "업종", "작업"]
    filtered = [l for l in links if any(k in l["text"] for k in keywords)]
    print(f"[kras] 관련 링크 {len(filtered)}개 발견")
    for l in filtered[:20]:
        print(f"  {l['text'][:40]:<40} {l['href']}")

    return filtered


def collect_checklist_list(page):
    """공종별 체크리스트 목록 수집"""
    targets = [
        ("체크리스트", f"{KRAS_URL}checklist"),
        ("자료실", f"{KRAS_URL}board/index/1"),
    ]
    results = {}

    for name, url in targets:
        try:
            page.goto(url, timeout=15000)
            page.wait_for_load_state("networkidle")
            items = page.eval_on_selector_all("tr, li, .item, .list-item", """
                els => els.map(e => e.innerText.trim()).filter(t => t.length > 2)
            """)
            results[name] = {"url": url, "count": len(items), "items": items[:50]}
            print(f"[{name}] {len(items)}개 항목")
        except Exception as e:
            print(f"[{name}] 접근 실패: {e}")
            results[name] = {"url": url, "error": str(e)}

    return results


def save(data, filename):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[save] {path}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        )
        page = context.new_page()

        print("=== 1단계: 로그인 ===")
        login(page)

        print("\n=== 2단계: KRAS 구조 파악 ===")
        links = explore_kras(page)
        save(links, "kras_links.json")

        print("\n=== 3단계: 체크리스트 목록 수집 ===")
        data = collect_checklist_list(page)
        save(data, "checklist_structure.json")

        browser.close()
        print("\n=== 완료 ===")


if __name__ == "__main__":
    main()

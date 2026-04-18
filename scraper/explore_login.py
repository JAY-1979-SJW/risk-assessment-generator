"""포털 로그인 구조 파악용 임시 스크립트"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://portal.kosha.or.kr/", timeout=30000)
    page.wait_for_load_state("networkidle")

    links = page.eval_on_selector_all(
        "a",
        "els => els.map(e => ({text: e.innerText.trim(), href: e.href})).filter(l => l.text)"
    )
    print("=== 로그인 관련 링크 ===")
    for l in links:
        if "로그인" in l["text"] or "login" in l["href"].lower() or "Login" in l["href"]:
            print(f"  text={l['text']!r}  href={l['href']}")

    inputs = page.eval_on_selector_all(
        "input",
        "els => els.map(e => ({type: e.type, name: e.name, id: e.id, class: e.className, visible: e.offsetParent !== null}))"
    )
    print("\n=== input 요소 ===")
    for i in inputs:
        print(f"  {i}")

    print(f"\n=== 현재 URL ===\n  {page.url}")
    browser.close()

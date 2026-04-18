"""포털 로그인 구조 파악용 임시 스크립트"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://portal.kosha.or.kr/", timeout=30000)
    page.wait_for_load_state("networkidle")

    # 로그인 링크 클릭 후 URL 추적
    print("=== 로그인 링크 클릭 시도 ===")
    with page.expect_navigation(timeout=15000):
        page.click("a:has-text('로그인')")
    page.wait_for_load_state("networkidle")
    print(f"  클릭 후 URL: {page.url}")

    # 현재 페이지 input 요소 재확인
    inputs = page.eval_on_selector_all(
        "input",
        "els => els.map(e => ({type: e.type, name: e.name, id: e.id, visible: e.offsetParent !== null}))"
    )
    print("\n=== 로그인 페이지 input 요소 ===")
    for i in inputs:
        if i["visible"] or i["type"] not in ("hidden",):
            print(f"  {i}")

    # iframe 확인
    frames = page.frames
    print(f"\n=== iframe 수: {len(frames)} ===")
    for f in frames:
        print(f"  {f.url}")
        f_inputs = f.eval_on_selector_all(
            "input",
            "els => els.map(e => ({type: e.type, name: e.name, id: e.id, visible: e.offsetParent !== null}))"
        )
        for i in f_inputs:
            if i["type"] in ("text", "password", "email"):
                print(f"    INPUT: {i}")

    browser.close()

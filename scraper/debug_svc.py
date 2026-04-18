"""서비스업 API 파라미터 직접 캡처"""
from dotenv import load_dotenv
from pathlib import Path
import os, json
load_dotenv(Path(__file__).parent / ".env")
ID = os.getenv("KOSHA_ID")
PW = os.getenv("KOSHA_PW")
BASE = "https://portal.kosha.or.kr"

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    calls = []
    def on_req(req):
        if "selectMediaList" in req.url:
            calls.append({"url": req.url, "body": req.post_data})
    def on_resp(resp):
        if "selectMediaList" in resp.url:
            try:
                d = resp.json()
                items = d.get("payload", {}).get("list", [])
                total = items[0].get("totalCount", 0) if items else 0
                for c in calls:
                    if c.get("_total") is None:
                        c["_total"] = total
                        c["_count"] = len(items)
                        break
            except Exception:
                pass

    page.on("request", on_req)
    page.on("response", on_resp)

    # 로그인
    page.goto(f"{BASE}/", timeout=60000)
    page.wait_for_load_state("networkidle")
    page.locator("a:has-text('로그인')").first.click()
    page.wait_for_timeout(2000)
    for _ in range(10):
        if page.evaluate("!!document.querySelector('.popup')"):
            break
        page.wait_for_timeout(500)
    page.evaluate("const p=document.querySelector('.popup'); if(p) p.style.display='block'")
    page.eval_on_selector(".inputGroup input[type=text]",
        f"el=>{{el.value='{ID}';el.dispatchEvent(new Event('input',{{bubbles:true}}))}}")
    page.eval_on_selector(".password input[type=password]",
        f"el=>{{el.value='{PW}';el.dispatchEvent(new Event('input',{{bubbles:true}}))}}")
    page.eval_on_selector("section.login",
        "el=>{const btn=el.querySelector('button[type=button]');if(btn)btn.click()}")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # 서비스업 5개 섹션 순회
    svc_urls = [
        ("svc-OPS",  "indust-page3/indust-page3-list1"),
        ("svc-동영상", "indust-page3/indust-page3-list2"),
        ("svc-교재",  "indust-page3/indust-page3-list3"),
        ("svc-교안",  "indust-page3/indust-page3-list4"),
        ("svc-기타",  "indust-page3/indust-page3-list5"),
    ]
    for label, path in svc_urls:
        calls.clear()
        page.goto(f"{BASE}/archive/cent-archive/indust-arch/{path}?page=1&rowsPerPage=12", timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        print(f"\n=== {label} ===")
        for c in calls:
            print(f"  body: {c['body']}")
            print(f"  total: {c.get('_total')}, count: {c.get('_count')}")

    browser.close()

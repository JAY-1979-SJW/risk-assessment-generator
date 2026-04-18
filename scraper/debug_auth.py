"""requests 쿠키 vs in-browser fetch 인증 비교"""
from dotenv import load_dotenv
from pathlib import Path
import os, json, requests
load_dotenv(Path(__file__).parent / ".env")
ID = os.getenv("KOSHA_ID")
PW = os.getenv("KOSHA_PW")
BASE = "https://portal.kosha.or.kr"
API = f"{BASE}/api/portal24/bizV/p/VCPDG01007/selectMediaList"

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

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

    # 서비스업 OPS 페이지 이동
    page.goto(f"{BASE}/archive/cent-archive/indust-arch/indust-page3/indust-page3-list1?page=1&rowsPerPage=12", timeout=60000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)

    # 1. 브라우저 내부 fetch (인증 자동)
    result = page.evaluate("""
        async () => {
            const r = await fetch("/api/portal24/bizV/p/VCPDG01007/selectMediaList", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({shpCd:"12", menuMode:"3", menuCode:"01", page:1, rowsPerPage:5, ascDesc:"desc", searchCondition:"all", searchValue:null})
            });
            return await r.json();
        }
    """)
    items = result.get("payload", {}).get("list", [])
    total = items[0].get("totalCount") if items else 0
    print(f"[in-browser] 서비스업-OPS: 총 {total}건, 수신 {len(items)}건")

    # auth 요청 헤더 캡처
    auth_headers = {}
    def capture_auth(req):
        if "selectMediaList" in req.url:
            h = req.headers
            for k in ["authorization", "x-access-token", "x-auth-token"]:
                if k in h:
                    auth_headers[k] = h[k]
    page.on("request", capture_auth)
    # 재로드해서 헤더 캡처
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    print(f"[auth headers] {auth_headers}")

    # 2. requests + 쿠키
    cookies = {c["name"]: c["value"] for c in page.context.cookies()}
    headers = {"Content-Type": "application/json", "Referer": BASE, "Origin": BASE}
    headers.update(auth_headers)
    resp = requests.post(API,
        json={"shpCd":"12", "menuMode":"3", "menuCode":"01", "page":1, "rowsPerPage":5, "ascDesc":"desc", "searchCondition":"all", "searchValue":None},
        cookies=cookies, headers=headers, timeout=30)
    data = resp.json()
    items2 = data.get("payload", {}).get("list", [])
    total2 = items2[0].get("totalCount") if items2 else 0
    print(f"[requests+cookies] 서비스업-OPS: 총 {total2}건, 수신 {len(items2)}건")
    print(f"[requests status] {resp.status_code}")
    print(f"[cookies count] {len(cookies)}")

    browser.close()

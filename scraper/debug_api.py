"""API 엔드포인트 및 다운로드 URL 구조 파악"""
from dotenv import load_dotenv
from pathlib import Path
import os, json
load_dotenv(Path(__file__).parent / '.env')
ID = os.getenv('KOSHA_ID')
PW = os.getenv('KOSHA_PW')
BASE = 'https://portal.kosha.or.kr'

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 900})

    req_log = []
    resp_log = []

    def on_request(req):
        url = req.url
        if any(x in url for x in ['selectMediaList', 'selectAtchList', 'download', 'fileDown', 'getFileList']):
            req_log.append({'url': url, 'body': req.post_data})

    def on_response(resp):
        url = resp.url
        if any(x in url for x in ['selectMediaList', 'selectAtchList']):
            try:
                resp_log.append({'url': url, 'json': resp.json()})
            except Exception:
                pass

    page.on('request', on_request)
    page.on('response', on_response)

    # 로그인
    page.goto(f'{BASE}/', timeout=60000)
    page.wait_for_load_state('networkidle')
    page.locator("a:has-text('로그인')").first.click()
    page.wait_for_timeout(2000)
    for _ in range(10):
        if page.evaluate("!!document.querySelector('.popup')"):
            break
        page.wait_for_timeout(500)
    page.evaluate("const p=document.querySelector('.popup'); if(p) p.style.display='block'")
    page.eval_on_selector('.inputGroup input[type=text]',
        f"el=>{{el.value='{ID}';el.dispatchEvent(new Event('input',{{bubbles:true}}))}}")
    page.eval_on_selector('.password input[type=password]',
        f"el=>{{el.value='{PW}';el.dispatchEvent(new Event('input',{{bubbles:true}}))}}")
    page.eval_on_selector('section.login',
        "el=>{const btn=el.querySelector('button[type=button]');if(btn)btn.click()}")
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    print('[login]', page.locator("button:has-text('로그아웃')").count() > 0)

    # 목록 → 상세 페이지
    page.goto(f'{BASE}/archive/cent-archive/indust-arch/indust-page1/indust-page1-list1?page=1&rowsPerPage=12', timeout=60000)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1500)
    page.locator('ul.thumbList > li:first-child a.subject').click()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(3000)

    print('\n=== 요청 body ===')
    for r in req_log:
        print('URL:', r['url'])
        print('BODY:', r['body'])
        print('---')

    print('\n=== selectAtchList 응답 ===')
    for r in resp_log:
        if 'selectAtchList' in r['url']:
            print(json.dumps(r['json'], ensure_ascii=False, indent=2)[:1000])

    print('\n=== selectMediaList 응답 (첫 항목만) ===')
    for r in resp_log:
        if 'selectMediaList' in r['url']:
            items = r['json'].get('payload', {}).get('list', [])
            if items:
                print(json.dumps(items[0], ensure_ascii=False, indent=2))
            break

    # 다운로드 버튼 클릭 → 실제 요청 URL 캡처
    download_reqs = []
    page.on('request', lambda req: download_reqs.append({'url': req.url, 'body': req.post_data})
            if req.url != 'about:blank' else None)

    dl_btn = page.locator('button.download').first
    print('\ndl_btn count:', dl_btn.count())
    if dl_btn.count() > 0:
        try:
            with page.expect_download(timeout=5000) as dl_info:
                dl_btn.click()
            d = dl_info.value
            print('Download URL:', d.url)
        except Exception as e:
            print('No file download triggered:', e)
        page.wait_for_timeout(2000)

    print('\n=== 다운로드 버튼 클릭 후 요청 ===')
    for r in download_reqs[-10:]:
        print(r)

    browser.close()

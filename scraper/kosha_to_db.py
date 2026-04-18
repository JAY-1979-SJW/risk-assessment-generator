"""
KOSHA selectMediaList API → PostgreSQL(common-db) kosha_materials 테이블 적재
단계:
  1. Playwright 로그인 → 세션 쿠키 추출
  2. 25개 섹션 URL 순회 → API 인터셉트로 shpCd 확보 + 1페이지 데이터
  3. 전체 페이지를 requests로 직접 호출 (rowsPerPage=100)
  4. contsAtcflNo → download_url 생성
  5. PostgreSQL upsert (contsAtcflNo 중복 방지)
"""
import os, json, time, requests, psycopg2
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv(Path(__file__).parent / '.env')
ID  = os.getenv('KOSHA_ID')
PW  = os.getenv('KOSHA_PW')
BASE = 'https://portal.kosha.or.kr'
API  = f'{BASE}/api/portal24/bizV/p/VCPDG01007/selectMediaList'
DL_BASE = f'{BASE}/api/portal24/bizA/p/files/downloadAtchFile'

INDUSTRIES = {1: '제조업', 2: '건설업', 3: '서비스업', 4: '조선업', 5: '기타산업'}
LIST_TYPES  = {1: 'OPS', 2: '동영상', 3: '외국어교재', 4: '외국어교안', 5: '기타'}
MENU_CODES  = {1: '01', 2: '02', 3: '03', 4: '04', 5: '05'}

DB_HOST = '127.0.0.1'
DB_PORT = 5435
DB_NAME = 'common_data'
DB_USER = 'common_admin'
DB_PASS = 'XenZ5xmKw5jEf1bWQuU2LxWRZMlJ'

# ── 1. Playwright 로그인 + 쿠키 + shpCd 수집 ──────────────────────────────
section_meta = {}   # {(ind_num, list_num): shpCd}

def login_page(page):
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
    ok = page.locator("button:has-text('로그아웃')").count() > 0
    print(f'[login] {"성공" if ok else "실패"}')
    return ok


def run_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 900})

        # REQUEST 인터셉트: 실제 API 파라미터(shpCd, menuMode, menuCode) 캡처
        # {(ind, lst): {'shpCd': ..., 'menuMode': ..., 'menuCode': ...}}
        last_req = {}

        def on_request(req):
            if 'selectMediaList' in req.url and req.post_data:
                try:
                    body = json.loads(req.post_data)
                    # page_num=1 인 첫 요청만 캡처 (목록 파라미터)
                    if body.get('page', 0) == 1:
                        last_req['params'] = body
                except Exception:
                    pass

        page.on('request', on_request)

        if not login_page(page):
            browser.close()
            return None, {}

        # 25개 섹션 순회 → 실제 API 파라미터 캡처
        meta = {}
        for ind in range(1, 6):
            for lst in range(1, 6):
                last_req.clear()
                url = (f'{BASE}/archive/cent-archive/indust-arch'
                       f'/indust-page{ind}/indust-page{ind}-list{lst}'
                       f'?page=1&rowsPerPage=12')
                page.goto(url, timeout=60000)
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(800)
                params = last_req.get('params', {})
                meta[(ind, lst)] = {
                    'shpCd':    params.get('shpCd', ''),
                    'menuMode': params.get('menuMode', '1'),
                    'menuCode': params.get('menuCode', ''),
                }
                shp = meta[(ind, lst)]['shpCd']
                mc  = meta[(ind, lst)]['menuCode']
                print(f'  [{INDUSTRIES[ind]}-{LIST_TYPES[lst]}] menuCode={mc} shpCd={repr(shp)}')

        print(f'  파라미터 확보: {len(meta)}/25 섹션')
        browser.close()
        return meta

# ── 2. requests로 전체 데이터 수집 ──────────────────────────────────────────
def fetch_all(cookies, section_meta):
    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update({
        'Content-Type': 'application/json',
        'Referer': BASE,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    })

    all_items = []

    for (ind, lst), shp_cd in section_meta.items():
        industry = INDUSTRIES[ind]
        list_type = LIST_TYPES[lst]
        menu_code = MENU_CODES[lst]
        page_num = 1
        total_pages = 1

        while page_num <= total_pages:
            payload = {
                'shpCd': shp_cd,
                'searchCondition': 'all',
                'searchValue': None,
                'page': page_num,
                'rowsPerPage': 100,
                'ascDesc': 'desc',
                'menuMode': str(ind),
                'menuCode': menu_code
            }
            try:
                resp = session.post(API, json=payload, timeout=30)
                data = resp.json()
                items = data.get('payload', {}).get('list', [])
                if page_num == 1:
                    total = items[0].get('totalCount', 0) if items else 0
                    total_pages = max(1, (total + 99) // 100)
                    print(f'  [{industry}-{list_type}] 총 {total}건 / {total_pages}페이지')

                for item in items:
                    atcfl_no = item.get('contsAtcflNo', '')
                    all_items.append({
                        'title': item.get('medName', '').strip(),
                        'category': f'{industry}_{list_type}',
                        'industry': industry,
                        'list_type': list_type,
                        'med_seq': item.get('medSeq'),
                        'contsAtcflNo': atcfl_no,
                        'download_url': f'{DL_BASE}?atcflNo={atcfl_no}&atcflSeq=1' if atcfl_no else '',
                        'reg_date': item.get('contsRegYmd', ''),
                        'keyword': item.get('medKeyword', ''),
                        'note': item.get('medNote', ''),
                        'source': 'kosha'
                    })

                print(f'    페이지 {page_num}/{total_pages}: {len(items)}개 | 누적 {len(all_items)}개')
                page_num += 1
                time.sleep(0.2)

            except Exception as e:
                print(f'    [error] {e}')
                break

    return all_items

# ── 3. PostgreSQL 테이블 생성 + upsert ──────────────────────────────────────
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS kosha_materials (
    id              SERIAL PRIMARY KEY,
    title           TEXT,
    category        VARCHAR(50),
    industry        VARCHAR(20),
    list_type       VARCHAR(20),
    med_seq         INTEGER,
    conts_atcfl_no  VARCHAR(50) UNIQUE,
    download_url    TEXT,
    reg_date        VARCHAR(10),
    keyword         TEXT,
    note            TEXT,
    source          VARCHAR(20) DEFAULT 'kosha',
    created_at      TIMESTAMP DEFAULT NOW()
);
"""

UPSERT_SQL = """
INSERT INTO kosha_materials
    (title, category, industry, list_type, med_seq, conts_atcfl_no,
     download_url, reg_date, keyword, note, source)
VALUES
    (%(title)s, %(category)s, %(industry)s, %(list_type)s, %(med_seq)s,
     %(contsAtcflNo)s, %(download_url)s, %(reg_date)s, %(keyword)s, %(note)s, %(source)s)
ON CONFLICT (conts_atcfl_no) DO UPDATE SET
    title        = EXCLUDED.title,
    download_url = EXCLUDED.download_url,
    reg_date     = EXCLUDED.reg_date;
"""

def load_to_db(items):
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()
    cur.execute(CREATE_SQL)
    conn.commit()

    inserted = 0
    for item in items:
        if not item['contsAtcflNo']:
            continue
        cur.execute(UPSERT_SQL, item)
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    return inserted

# ── 4. category별 분포 출력 ──────────────────────────────────────────────────
def print_stats():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()
    cur.execute("SELECT category, COUNT(*) FROM kosha_materials GROUP BY category ORDER BY category")
    rows = cur.fetchall()
    total = sum(r[1] for r in rows)
    print('\n=== category별 분포 ===')
    for cat, cnt in rows:
        print(f'  {cat}: {cnt}건')
    print(f'  합계: {total}건')

    cur.execute("SELECT COUNT(*) FROM kosha_materials WHERE download_url != ''")
    dl_cnt = cur.fetchone()[0]
    print(f'  download_url 보유: {dl_cnt}건')
    cur.close()
    conn.close()

# ── main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('=== STEP 1: 로그인 + shpCd 수집 ===')
    cookies, meta = run_playwright()
    if not cookies:
        print('로그인 실패, 종료')
        exit(1)
    print(f'  shpCd 확보: {len(meta)}/25 섹션')

    print('\n=== STEP 2: API 전체 수집 ===')
    items = fetch_all(cookies, meta)
    print(f'  수집 완료: {len(items)}건')

    print('\n=== STEP 3: DB 적재 ===')
    inserted = load_to_db(items)
    print(f'  insert/update: {inserted}건')

    print_stats()
    print('\n=== 완료 ===')

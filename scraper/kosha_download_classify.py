"""
KOSHA 파일 다운로드 + 즉시 매직바이트 분류 + 즉시 파싱
1. Playwright 로그인 → 쿠키 확보
2. text_pdf / hwp / zip 대상만 다운로드 (이미 받은 것 제외)
3. 다운로드 직후 매직바이트로 실제 파일 형식 분류 → doc_type 갱신
4. 파싱 가능 파일(pdf/hwp/zip) 즉시 텍스트 추출 → 청크 저장
5. 50건마다 진행 로그 출력
"""
import os, re, sys, time, hashlib, requests, psycopg2, psycopg2.extras
import functools
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from logger import get_logger, get_run_logger, get_pipeline_logger, mask
from kosha_parser import extract_text, build_chunks, save_chunks, update_file_parse

print = functools.partial(print, flush=True)
log  = get_logger('kosha.download')
rlog = get_run_logger('download')
plog = get_pipeline_logger()

from config import get_conn, FILES_BASE, KOSHA_ID as ID, KOSHA_PW as PW, KOSHA_BASE as BASE

# 다운로드 대상 doc_type
TARGET_TYPES = ('text_pdf', 'hwp', 'image_pdf', 'zip')


# ── 매직바이트 분류 ──────────────────────────────────────────────────────────

def detect_magic(data: bytes) -> tuple[str, str]:
    """(magic, doc_type) 반환"""
    if not data or len(data) < 4:
        return 'empty', 'no_file'
    if data[:4] == b'%PDF':
        return 'pdf', 'text_pdf'       # 텍스트 레이어는 파싱 시 확인
    if data[:3] == b'\xff\xd8\xff':
        return 'jpg', 'image_jpg'
    if data[:4] == b'\x89PNG':
        return 'png', 'image_png'
    if data[:4] == b'PK\x03\x04':
        return 'zip', 'zip'
    if data[:4] in (b'\xd0\xcf\x11\xe0',):
        return 'hwp', 'hwp'
    if b'ftyp' in data[4:12]:
        return 'mp4', 'video'
    if data[:4] == b'RIFF':
        return 'avi', 'video'
    return 'unknown', 'unknown'


# ── 파일 저장 경로 ───────────────────────────────────────────────────────────

def _safe(s): return re.sub(r'[\\/:*?"<>|]', '_', s or '').strip()

def file_dir(industry, list_type, reg_date):
    date = re.sub(r'[^0-9]', '', reg_date or '')[:8] or datetime.now().strftime('%Y%m%d')
    d = FILES_BASE / _safe(industry) / _safe(list_type) / date
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Playwright 로그인 ────────────────────────────────────────────────────────

def get_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
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
        print(f'[로그인] {"성공" if ok else "실패"}')
        cookies = {c['name']: c['value'] for c in page.context.cookies()}
        browser.close()
        return cookies if ok else None


# ── 실패 로그 기록 ───────────────────────────────────────────────────────────

FAIL_LOG = Path(__file__).parent / 'kosha_fail.log'

def _log_fail(mid, url, reason, detail):
    with open(FAIL_LOG, 'a') as f:
        f.write(str(mid) + '|' + reason + '|' + str(detail)[:80] + '|' + str(url) + chr(10))


# ── 단일 파일 다운로드 + 분류 ────────────────────────────────────────────────

def download_and_classify(mat: dict, session: requests.Session) -> dict:
    mid  = mat['id']
    url  = mat['download_url']
    no   = mat['conts_atcfl_no']
    ind  = mat.get('industry', '')
    lt   = mat.get('list_type', '')
    rd   = mat.get('reg_date', '')

    result = {'material_id': mid, 'status': 'failed', 'magic': None,
              'doc_type': None, 'file_path': None, 'file_size': 0}
    if not url:
        result['status'] = 'no_url'
        return result

    try:
        resp = session.get(url, timeout=10, stream=False)
        resp.raise_for_status()
    except Exception as e:
        err = str(e)[:80]
        result['status'] = f'download_error:{err[:60]}'
        log.error('다운로드 오류 id=%s atcfl=%s err=%s', mid, no, err)
        _log_fail(mid, url, 'download_error', err)
        return result

    content = resp.content
    if not content:
        result['status'] = 'empty_response'
        log.warning('빈 응답 id=%s atcfl=%s (url_expired)', mid, no)
        _log_fail(mid, url, 'empty_response', '')
        return result

    magic, doc_type = detect_magic(content)
    file_hash = hashlib.sha256(content).hexdigest()

    # 확장자 결정
    ext_map = {'pdf': 'pdf', 'jpg': 'jpg', 'png': 'png',
               'zip': 'zip', 'hwp': 'hwp', 'mp4': 'mp4', 'avi': 'avi'}
    ext = ext_map.get(magic, 'bin')

    fpath = file_dir(ind, lt, rd) / f'{mid}_{no}.{ext}'
    fpath.write_bytes(content)

    result.update({
        'status':    'downloaded',
        'magic':     magic,
        'doc_type':  doc_type,
        'file_path': str(fpath),
        'file_size': len(content),
        'file_hash': file_hash,
        'file_type': ext,
    })
    return result


# ── DB 저장 ──────────────────────────────────────────────────────────────────

def ensure_columns():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("ALTER TABLE kosha_materials ADD COLUMN IF NOT EXISTS actual_magic VARCHAR(20)")
    conn.commit(); cur.close(); conn.close()


def save_file_record(result: dict) -> int | None:
    if result['status'] != 'downloaded':
        return None
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO kosha_material_files
            (material_id, file_path, file_type, file_hash, file_size,
             download_status, parse_status)
        VALUES (%s,%s,%s,%s,%s,'downloaded','pending')
        ON CONFLICT DO NOTHING
        RETURNING id
    """, (result['material_id'], result['file_path'], result['file_type'],
          result.get('file_hash'), result['file_size']))
    row = cur.fetchone()
    conn.commit(); cur.close(); conn.close()
    return row[0] if row else None


def update_doc_type(updates: list[tuple]):
    """[(doc_type, actual_magic, material_id), ...]"""
    conn = get_conn(); cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """
        UPDATE kosha_materials SET doc_type=%s, actual_magic=%s WHERE id=%s
    """, updates)
    conn.commit(); cur.close(); conn.close()


# ── 메인 ─────────────────────────────────────────────────────────────────────

def run(batch_size: int = 50):
    ensure_columns()

    # 대상 자료 조회 (이미 다운로드된 것 제외)
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT km.id, km.title, km.conts_atcfl_no, km.download_url,
               km.industry, km.list_type, km.reg_date, km.doc_type
        FROM kosha_materials km
        WHERE km.doc_type IN %s
          AND km.download_url IS NOT NULL AND km.download_url != ''
          AND NOT EXISTS (
              SELECT 1 FROM kosha_material_files f WHERE f.material_id = km.id
          )
        ORDER BY km.industry, km.list_type, km.id
    """, (TARGET_TYPES,))
    materials = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()

    total = len(materials)
    rlog.info('=== 다운로드 시작 === 대상:%d건 유형:%s', total, list(TARGET_TYPES))
    print(f'[다운로드] 대상: {total:,}건 (이미 완료된 것 제외)')
    print(f'[대상 유형] {", ".join(TARGET_TYPES)}')

    if total == 0:
        rlog.info('다운로드 대상 없음 — 종료')
        print('다운로드할 자료 없음')
        return

    # Playwright 로그인
    print('[1단계] KOSHA 로그인...')
    cookies = get_cookies()
    if not cookies:
        log.error('KOSHA 로그인 실패')
        print('로그인 실패 — 종료')
        return

    def _make_session(ck):
        s = requests.Session()
        s.cookies.update(ck)
        s.headers.update({'User-Agent': 'Mozilla/5.0'})
        return s

    session = _make_session(cookies)
    log.info('KOSHA 세션 획득 완료 (쿠키 %d개)', len(cookies))

    # 다운로드 + 즉시 파싱 실행
    print(f'[2단계] 다운로드+파싱 시작 ({total:,}건)')
    plog.info('[다운로드+파싱] 시작 대상:%d건', total)
    start = datetime.now()
    stats = {'success': 0, 'failed': 0, 'pdf': 0, 'jpg': 0, 'zip': 0,
             'hwp': 0, 'mp4': 0, 'unknown': 0,
             'parsed': 0, 'parse_failed': 0, 'chunks': 0}
    dt_updates = []
    consec_empty = 0
    SESSION_RETRY_THRESHOLD = 30

    PARSE_MAGIC = ('pdf', 'hwp', 'zip')

    for i, mat in enumerate(materials, 1):
        result = download_and_classify(mat, session)

        # 연속 empty_response 감지 → 세션 자동 복구
        if result['status'] == 'empty_response':
            consec_empty += 1
            if consec_empty >= SESSION_RETRY_THRESHOLD:
                log.warning('연속 empty_response %d건 → 세션 재획득 시도', consec_empty)
                print(f'  [세션 재획득] empty_response {consec_empty}건 연속 → 재로그인...')
                new_cookies = get_cookies()
                if new_cookies:
                    session = _make_session(new_cookies)
                    consec_empty = 0
                    log.info('세션 재획득 성공')
                else:
                    log.error('세션 재획득 실패 — 계속 진행')
        else:
            consec_empty = 0

        # doc_type 갱신 누적
        dt_updates.append((
            result.get('doc_type') or mat['doc_type'],
            result.get('magic') or 'unknown',
            mat['id']
        ))

        if result['status'] == 'downloaded':
            file_id = save_file_record(result)
            stats['success'] += 1
            stats[result.get('magic', 'unknown')] = stats.get(result.get('magic', 'unknown'), 0) + 1

            # 즉시 파싱 (pdf/hwp/zip만)
            if file_id and result.get('magic') in PARSE_MAGIC:
                try:
                    raw_text, parse_status = extract_text(result['file_path'], result['file_type'])
                    update_file_parse(file_id, parse_status, raw_text)
                    if parse_status == 'success' and raw_text.strip():
                        chunks = build_chunks(mat['id'], file_id, raw_text)
                        save_chunks(chunks)
                        stats['parsed'] += 1
                        stats['chunks'] += len(chunks)
                        plog.debug('파싱 완료 id=%s magic=%s chunks=%d', mat['id'], result['magic'], len(chunks))
                    else:
                        stats['parse_failed'] += 1
                        plog.warning('파싱 실패 id=%s status=%s', mat['id'], parse_status)
                except Exception as e:
                    stats['parse_failed'] += 1
                    plog.error('파싱 오류 id=%s err=%s', mat['id'], e)
        else:
            stats['failed'] += 1

        # 배치 DB 저장 + 로그
        if i % batch_size == 0 or i == total:
            update_doc_type(dt_updates)
            dt_updates = []
            elapsed = (datetime.now() - start).seconds or 1
            rate = i / elapsed
            remain = int((total - i) / rate / 60) if rate > 0 else 0
            magic_str = ' | '.join(f'{k}:{v}' for k, v in stats.items()
                                   if k not in ('success', 'failed', 'parsed', 'parse_failed', 'chunks') and v > 0)
            progress_msg = (f'[{i:,}/{total:,}] 다운:{stats["success"]} 실패:{stats["failed"]} '
                            f'파싱:{stats["parsed"]} 청크:{stats["chunks"]} '
                            f'속도:{rate:.1f}건/s 잔여:{remain}분 | {magic_str}')
            print(f'  {progress_msg}')
            log.info(progress_msg)
            plog.info(progress_msg)

        time.sleep(0.1)

    # 최종 집계
    elapsed = (datetime.now() - start).seconds
    summary = (f'완료 총소요:{elapsed//60}분{elapsed%60}초 '
               f'다운:{stats["success"]}건 실패:{stats["failed"]}건 '
               f'파싱:{stats["parsed"]}건 청크:{stats["chunks"]}개 '
               f'pdf:{stats["pdf"]} zip:{stats["zip"]} hwp:{stats["hwp"]}')
    print(f'\n=== 다운로드+파싱 완료 ===')
    print(f'  총 소요: {elapsed//60}분 {elapsed%60}초')
    print(f'  다운로드 성공: {stats["success"]:,}건 / 실패: {stats["failed"]:,}건')
    print(f'  파싱 성공: {stats["parsed"]:,}건 / 실패: {stats["parse_failed"]:,}건')
    print(f'  청크 생성: {stats["chunks"]:,}개')
    rlog.info('=== %s', summary)
    plog.info('=== 완료 === %s', summary)

    # doc_type 최종 분포 출력
    conn = get_conn(); cur = conn.cursor()
    cur.execute('SELECT actual_magic, COUNT(*) FROM kosha_materials WHERE actual_magic IS NOT NULL GROUP BY actual_magic ORDER BY COUNT(*) DESC')
    print('\n=== actual_magic 분포 ===')
    for r in cur.fetchall():
        print(f'  {str(r[0]).ljust(12)} {r[1]:,}건')
    cur.close(); conn.close()


if __name__ == '__main__':
    run()

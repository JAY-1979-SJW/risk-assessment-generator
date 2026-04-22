"""
파일 매직 바이트 기반 실제 형식 분류기
Range: bytes=0-31 요청으로 파일 헤더만 가져와 분류
kosha_materials.doc_type 갱신
"""
import re, sys, requests, psycopg2, psycopg2.extras
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# 실시간 로그 (버퍼링 없이 즉시 출력)
import functools
print = functools.partial(print, flush=True)

load_dotenv(Path(__file__).parent / '.env')

DB_HOST = '127.0.0.1'
DB_PORT = 5435
DB_NAME = 'common_data'
DB_USER = 'common_admin'
DB_PASS = 'XenZ5xmKw5jEf1bWQuU2LxWRZMlJ'

REPORTS_DIR = Path(__file__).parent / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


# ── 매직 바이트 → 실제 파일 형식 ────────────────────────────────────────────

def detect_magic(header: bytes) -> str:
    if not header:
        return 'empty'
    if header[:4] == b'%PDF':
        return 'pdf'
    if header[:3] == b'\xff\xd8\xff':
        return 'jpg'
    if header[:4] == b'\x89PNG':
        return 'png'
    if header[:4] == b'PK\x03\x04':
        # ZIP 기반 → HWPX or 일반 ZIP
        return 'zip'
    if header[:4] in (b'\xd0\xcf\x11\xe0',):
        # OLE2 구조 → HWP5
        return 'hwp'
    if b'ftyp' in header[4:12]:
        return 'mp4'
    if header[:4] == b'RIFF':
        return 'avi'
    if header[:3] == b'ID3' or header[:2] == b'\xff\xfb':
        return 'mp3'
    if header[:4] == b'HWP ':
        return 'hwp'
    return 'unknown'


# ── doc_type 매핑 ────────────────────────────────────────────────────────────

def magic_to_doctype(magic: str, title: str = '', list_type: str = '') -> str:
    if magic == 'pdf':
        # PDF는 나중에 텍스트 레이어 여부로 세분화
        return 'text_pdf'
    if magic == 'jpg':
        return 'image_jpg'
    if magic == 'png':
        return 'image_png'
    if magic == 'hwp':
        return 'hwp'
    if magic == 'zip':
        # HWPX 가능성 체크 (title/keyword 기반)
        if '교재' in title or '교안' in title:
            return 'zip_doc'
        return 'zip'
    if magic in ('mp4', 'avi'):
        return 'video'
    if magic == 'empty':
        return 'no_file'
    return 'unknown'


# ── Range 요청 ───────────────────────────────────────────────────────────────

def fetch_header(row: dict) -> dict:
    result = {
        'id':          row['id'],
        'magic':       'unknown',
        'doc_type':    'unknown',
        'actual_size': None,
        'error':       None,
    }
    url = row.get('download_url', '')
    if not url:
        result['magic'] = 'empty'
        result['doc_type'] = 'no_url'
        return result
    try:
        r = requests.get(
            url,
            headers={'Range': 'bytes=0-31'},
            timeout=10,
            stream=False
        )
        header_bytes = r.content[:32]
        # Content-Range로 실제 전체 크기
        cr = r.headers.get('Content-Range', '')
        m = re.search(r'/(\d+)$', cr)
        if m:
            result['actual_size'] = int(m.group(1))
        else:
            cl = r.headers.get('Content-Length')
            if cl:
                result['actual_size'] = int(cl)

        magic = detect_magic(header_bytes)
        result['magic'] = magic
        result['doc_type'] = magic_to_doctype(magic, row.get('title', ''), row.get('list_type', ''))
    except Exception as e:
        result['error'] = str(e)[:80]
        result['doc_type'] = 'error'
    return result


def run_classify(workers: int = 30):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # 전체 자료 목록
    cur.execute("""
        SELECT id, title, list_type, download_url
        FROM kosha_materials
        ORDER BY id
    """)
    materials = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()

    total = len(materials)
    print(f'[분류] 전체 {total:,}건 Range 요청 시작 (workers={workers})')

    results: dict[int, dict] = {}
    done = 0
    magic_counter: dict[str, int] = {}
    error_count = 0
    start_time = datetime.now()

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(fetch_header, m): m['id'] for m in materials}
        for f in as_completed(futures):
            r = f.result()
            results[r['id']] = r
            done += 1
            magic_counter[r['magic']] = magic_counter.get(r['magic'], 0) + 1
            if r.get('error'):
                error_count += 1
            if done % 100 == 0:
                elapsed = (datetime.now() - start_time).seconds
                rate = done / elapsed if elapsed > 0 else 0
                remain = int((total - done) / rate) if rate > 0 else 0
                top = sorted(magic_counter.items(), key=lambda x: -x[1])[:4]
                top_str = ' | '.join(f'{k}:{v}' for k, v in top)
                print(f'  [{done:,}/{total:,}] {rate:.0f}건/s 잔여~{remain//60}분 | {top_str} | 오류:{error_count}')

    print(f'  Range 요청 완료: {total:,}건')

    # DB 갱신
    print('[저장] doc_type / actual_size 업데이트')
    conn = get_conn()
    cur = conn.cursor()

    # actual_size 컬럼 추가
    cur.execute("ALTER TABLE kosha_materials ADD COLUMN IF NOT EXISTS actual_magic VARCHAR(20)")
    conn.commit()

    updates = []
    for mid, r in results.items():
        updates.append((r['doc_type'], r['magic'], r.get('actual_size'), mid))

    psycopg2.extras.execute_batch(cur, """
        UPDATE kosha_materials
        SET doc_type=%s, actual_magic=%s, remote_size=COALESCE(%s, remote_size)
        WHERE id=%s
    """, updates)
    conn.commit()
    cur.close(); conn.close()

    # 집계 출력
    from collections import Counter
    magic_cnt  = Counter(r['magic']    for r in results.values())
    dtype_cnt  = Counter(r['doc_type'] for r in results.values())
    error_cnt  = sum(1 for r in results.values() if r.get('error'))

    print('\n=== 매직바이트 기반 실제 형식 분포 ===')
    for k, v in sorted(magic_cnt.items(), key=lambda x: -x[1]):
        print(f'  {k:<15} {v:>5,}건')

    print('\n=== doc_type 분류 결과 ===')
    for k, v in sorted(dtype_cnt.items(), key=lambda x: -x[1]):
        pct = v / total * 100
        print(f'  {k:<20} {v:>5,}건  ({pct:.1f}%)')

    print(f'\n  오류(네트워크 등): {error_cnt}건')
    return results, dtype_cnt


if __name__ == '__main__':
    run_classify(workers=30)

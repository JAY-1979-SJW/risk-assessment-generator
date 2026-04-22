"""
KOSHA 자료 이미지/전자문서 분류기
- HEAD 요청으로 Content-Type + Content-Length 수집 (파일 미다운로드)
- 제목/키워드 패턴 분석 결합
- kosha_materials.doc_type 컬럼에 저장
- 보고서 생성: reports/kosha_doc_classification_YYYYMMDD.md
"""
import re, time, requests, psycopg2, psycopg2.extras
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

DB_HOST = '127.0.0.1'
DB_PORT = 5435
DB_NAME = 'common_data'
DB_USER = 'common_admin'
DB_PASS = 'XenZ5xmKw5jEf1bWQuU2LxWRZMlJ'

REPORTS_DIR = Path(__file__).parent / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)

# ── 분류 기준 ────────────────────────────────────────────────────────────────

# doc_type 값
TYPE_IMAGE    = 'image_pdf'       # 이미지 기반 PDF (OCR 필요)
TYPE_TEXT     = 'text_pdf'        # 텍스트 기반 PDF
TYPE_HWP      = 'hwp'             # HWP/HWPX 전자문서
TYPE_VIDEO    = 'video'           # 동영상
TYPE_ZIP      = 'zip'             # 압축파일
TYPE_FOREIGN  = 'foreign_doc'     # 외국어 자료
TYPE_UNKNOWN  = 'unknown'         # 판단 불가

# 이미지 PDF로 추정하는 제목 패턴
IMAGE_TITLE_PATTERNS = [
    r'인포그래픽',
    r'포스터',
    r'그림',
    r'카드뉴스',
    r'안전그림',
    r'삽화',
    r'웹툰',
]

# 텍스트 PDF로 추정하는 제목 패턴
TEXT_TITLE_PATTERNS = [
    r'지침',
    r'규정',
    r'고시',
    r'기준',
    r'매뉴얼',
    r'가이드',
    r'해설서',
    r'교재',
    r'교안',
    r'안내서',
    r'지도서',
    r'기술자료',
]

# list_type 기반 분류 힌트
VIDEO_LIST_TYPES  = {'동영상'}
FOREIGN_LIST_TYPES = {'외국어교재', '외국어교안'}


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


def ensure_doc_type_column():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("ALTER TABLE kosha_materials ADD COLUMN IF NOT EXISTS doc_type VARCHAR(20)")
    cur.execute("ALTER TABLE kosha_materials ADD COLUMN IF NOT EXISTS content_type VARCHAR(100)")
    cur.execute("ALTER TABLE kosha_materials ADD COLUMN IF NOT EXISTS remote_size BIGINT")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_km_doc_type ON kosha_materials(doc_type)")
    conn.commit()
    cur.close(); conn.close()


# ── HEAD 요청으로 메타 수집 ──────────────────────────────────────────────────

def head_request(row: dict) -> dict:
    url = row['download_url']
    result = {
        'id':           row['id'],
        'content_type': None,
        'remote_size':  None,
        'head_status':  None,
        'ext':          None,
    }
    if not url:
        return result
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        result['head_status']  = r.status_code
        result['content_type'] = r.headers.get('Content-Type', '').split(';')[0].strip()
        cl = r.headers.get('Content-Length')
        if cl:
            result['remote_size'] = int(cl)
        # Content-Disposition 에서 확장자 추출
        cd = r.headers.get('Content-Disposition', '')
        m = re.search(r'filename[^;=\n]*=.*?\.(\w+)', cd, re.IGNORECASE)
        if m:
            result['ext'] = m.group(1).lower()
    except Exception as e:
        result['head_status'] = f'error:{e}'
    return result


def collect_head_info(materials: list[dict], workers: int = 20) -> dict[int, dict]:
    """병렬 HEAD 요청"""
    results = {}
    total = len(materials)
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(head_request, m): m['id'] for m in materials}
        for f in as_completed(futures):
            r = f.result()
            results[r['id']] = r
            done += 1
            if done % 200 == 0:
                print(f'  HEAD 요청: {done}/{total}')
    print(f'  HEAD 요청 완료: {total}건')
    return results


# ── 분류 로직 ────────────────────────────────────────────────────────────────

def classify(row: dict, head: dict | None) -> str:
    title     = (row.get('title') or '').strip()
    list_type = (row.get('list_type') or '').strip()
    keyword   = (row.get('keyword') or '').strip()
    note      = (row.get('note') or '').strip()
    combined  = f'{title} {keyword} {note}'

    # list_type 기반 우선 분류
    if list_type in VIDEO_LIST_TYPES:
        return TYPE_VIDEO
    if list_type in FOREIGN_LIST_TYPES:
        return TYPE_FOREIGN

    # Content-Type 기반
    ct = (head.get('content_type') or '') if head else ''
    ext = (head.get('ext') or '') if head else ''

    if 'hwp' in ct or 'haansoft' in ct or ext in ('hwp', 'hwpx'):
        return TYPE_HWP
    if 'zip' in ct or ext == 'zip':
        return TYPE_ZIP
    if 'video' in ct or 'mp4' in ct or ext in ('mp4', 'avi', 'mov'):
        return TYPE_VIDEO

    # 제목 패턴 — 이미지 PDF
    for pat in IMAGE_TITLE_PATTERNS:
        if re.search(pat, combined):
            return TYPE_IMAGE

    # 파일 크기 기반 (HEAD 정보 있을 때)
    size = head.get('remote_size') if head else None
    if size and size > 10 * 1024 * 1024:  # 10MB 초과 PDF → 이미지 추정
        return TYPE_IMAGE

    # 제목 패턴 — 텍스트 PDF
    for pat in TEXT_TITLE_PATTERNS:
        if re.search(pat, combined):
            return TYPE_TEXT

    # PDF이면서 작은 파일 → 텍스트 추정
    if size and size < 3 * 1024 * 1024:
        return TYPE_TEXT

    # 판단 불가 → 텍스트로 취급 (이후 다운로드 시 검증)
    return TYPE_TEXT


# ── DB 저장 ──────────────────────────────────────────────────────────────────

def save_classifications(rows: list[dict], head_map: dict[int, dict]):
    conn = get_conn()
    cur = conn.cursor()
    updates = []
    for row in rows:
        head = head_map.get(row['id'])
        doc_type = classify(row, head)
        ct   = head.get('content_type') if head else None
        size = head.get('remote_size')  if head else None
        updates.append((doc_type, ct, size, row['id']))

    psycopg2.extras.execute_batch(cur, """
        UPDATE kosha_materials
        SET doc_type=(%s), content_type=(%s), remote_size=(%s)
        WHERE id=(%s)
    """, updates)
    conn.commit()
    cur.close(); conn.close()
    return updates


# ── 집계 쿼리 ────────────────────────────────────────────────────────────────

def fetch_stats() -> dict:
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT COUNT(*) FROM kosha_materials")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT doc_type, COUNT(*) cnt,
               SUM(remote_size) total_size,
               AVG(remote_size) avg_size
        FROM kosha_materials
        GROUP BY doc_type ORDER BY cnt DESC
    """)
    by_type = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT industry, doc_type, COUNT(*) cnt
        FROM kosha_materials
        GROUP BY industry, doc_type ORDER BY industry, cnt DESC
    """)
    by_industry = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT list_type, doc_type, COUNT(*) cnt
        FROM kosha_materials
        GROUP BY list_type, doc_type ORDER BY list_type, cnt DESC
    """)
    by_list = [dict(r) for r in cur.fetchall()]

    # 이미지 PDF 목록 (샘플 100건)
    cur.execute("""
        SELECT id, title, industry, list_type, reg_date,
               remote_size, content_type, conts_atcfl_no
        FROM kosha_materials
        WHERE doc_type = 'image_pdf'
        ORDER BY remote_size DESC NULLS LAST
        LIMIT 100
    """)
    image_list = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT COUNT(*) FROM kosha_materials WHERE doc_type = 'image_pdf'")
    image_total = cur.fetchone()[0]

    # HWP 목록
    cur.execute("""
        SELECT id, title, industry, list_type, conts_atcfl_no, remote_size
        FROM kosha_materials WHERE doc_type = 'hwp'
        ORDER BY industry, list_type LIMIT 200
    """)
    hwp_list = [dict(r) for r in cur.fetchall()]

    cur.close(); conn.close()
    return {
        'total':        total,
        'by_type':      by_type,
        'by_industry':  by_industry,
        'by_list':      by_list,
        'image_list':   image_list,
        'image_total':  image_total,
        'hwp_list':     hwp_list,
    }


# ── 보고서 작성 ──────────────────────────────────────────────────────────────

def _sz(b):
    if b is None: return '-'
    if b >= 1024**3: return f'{b/1024**3:.1f}GB'
    if b >= 1024**2: return f'{b/1024**2:.1f}MB'
    return f'{b/1024:.0f}KB'


TYPE_LABEL = {
    'image_pdf':   '이미지 PDF (OCR 필요)',
    'text_pdf':    '전자문서 PDF (텍스트 추출 가능)',
    'hwp':         'HWP/HWPX 전자문서',
    'video':       '동영상',
    'zip':         '압축파일',
    'foreign_doc': '외국어 자료',
    'unknown':     '미분류',
    None:          '미처리',
}


def build_report(stats: dict, generated_at: str) -> str:
    s = stats
    lines = []
    lines += [
        '# KOSHA 자료 이미지 / 전자문서 분류 보고서', '',
        f'- 생성일시: {generated_at}',
        f'- 전체 자료: {s["total"]:,}건',
        '',
    ]

    # ── 1. 전체 분류 요약 ──
    lines += ['## 1. 전체 분류 요약', '']
    lines += ['| 분류 | doc_type | 건수 | 비율 | 총 파일크기(추정) |']
    lines += ['|------|----------|-----:|-----:|-----------------|']
    for r in s['by_type']:
        label = TYPE_LABEL.get(r['doc_type'], r['doc_type'])
        pct   = r['cnt'] / s['total'] * 100 if s['total'] else 0
        lines.append(f'| {label} | {r["doc_type"] or "-"} | {r["cnt"]:,} | {pct:.1f}% | {_sz(r["total_size"])} |')
    lines.append('')

    # ── 2. 업종별 분류 ──
    lines += ['## 2. 업종별 분류', '']
    lines += ['| 업종 | 분류 | 건수 |']
    lines += ['|------|------|-----:|']
    for r in s['by_industry']:
        label = TYPE_LABEL.get(r['doc_type'], r['doc_type'])
        lines.append(f'| {r["industry"]} | {label} | {r["cnt"]:,} |')
    lines.append('')

    # ── 3. 자료유형별 분류 ──
    lines += ['## 3. 자료유형(list_type)별 분류', '']
    lines += ['| 자료유형 | 분류 | 건수 |']
    lines += ['|----------|------|-----:|']
    for r in s['by_list']:
        label = TYPE_LABEL.get(r['doc_type'], r['doc_type'])
        lines.append(f'| {r["list_type"]} | {label} | {r["cnt"]:,} |')
    lines.append('')

    # ── 4. 이미지 PDF 목록 ──
    lines += [
        f'## 4. 이미지 PDF 목록 (전체 {s["image_total"]:,}건 중 상위 100건)',
        '',
        '> OCR 처리가 필요한 자료 — pytesseract 또는 클라우드 OCR 적용 대상',
        '',
        '| # | 제목 | 업종 | 자료유형 | 파일크기 | conts_atcfl_no |',
        '|---|------|------|----------|----------|----------------|',
    ]
    for i, r in enumerate(s['image_list'], 1):
        title = (r['title'] or '')[:60]
        lines.append(f'| {i} | {title} | {r["industry"]} | {r["list_type"]} '
                     f'| {_sz(r["remote_size"])} | {r["conts_atcfl_no"]} |')
    lines.append('')

    # ── 5. HWP 목록 ──
    if s['hwp_list']:
        lines += [
            f'## 5. HWP/HWPX 전자문서 목록 (전체 {len(s["hwp_list"])}건)',
            '',
            '> hwp5txt 또는 LibreOffice 변환 필요',
            '',
            '| # | 제목 | 업종 | 자료유형 | 파일크기 | conts_atcfl_no |',
            '|---|------|------|----------|----------|----------------|',
        ]
        for i, r in enumerate(s['hwp_list'], 1):
            title = (r['title'] or '')[:60]
            lines.append(f'| {i} | {title} | {r["industry"]} | {r["list_type"]} '
                         f'| {_sz(r["remote_size"])} | {r["conts_atcfl_no"]} |')
        lines.append('')
    else:
        lines += ['## 5. HWP/HWPX 전자문서', '', '없음 (또는 HEAD 요청 후 재분류 필요)', '']

    # ── 6. 조치 방향 ──
    lines += [
        '## 6. 후속 처리 방향', '',
        '| 분류 | 처리 방법 | 우선순위 |',
        '|------|-----------|----------|',
        '| 전자문서 PDF | pdfplumber로 텍스트 추출 → 청크 → 공종 분류 | 1순위 |',
        '| HWP/HWPX | LibreOffice headless 변환 or hwp5txt | 2순위 |',
        '| 이미지 PDF | pytesseract OCR (pdf2image 변환 후) | 3순위 |',
        '| 동영상 | 자막/스크립트 추출 또는 Skip | 4순위 |',
        '| 외국어 자료 | 번역 후 처리 또는 별도 관리 | 5순위 |',
        '',
        '---',
        f'*자동 생성: kosha_classify_docs.py*',
    ]
    return '\n'.join(lines)


# ── 실행 ─────────────────────────────────────────────────────────────────────

def run():
    print('=== KOSHA 자료 이미지/전자문서 분류 ===')

    print('[1] doc_type 컬럼 준비')
    ensure_doc_type_column()

    print('[2] 전체 자료 목록 조회')
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT id, title, industry, list_type, keyword, note,
               download_url, conts_atcfl_no
        FROM kosha_materials
        ORDER BY id
    """)
    materials = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()
    print(f'  총 {len(materials):,}건')

    print('[3] HEAD 요청으로 Content-Type / 파일크기 수집 (병렬 20)')
    head_map = collect_head_info(materials, workers=20)

    print('[4] 분류 및 DB 저장')
    updates = save_classifications(materials, head_map)
    print(f'  {len(updates):,}건 분류 완료')

    print('[5] 집계 및 보고서 생성')
    stats = fetch_stats()
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report = build_report(stats, generated_at)

    fname = f'kosha_doc_classification_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
    fpath = REPORTS_DIR / fname
    fpath.write_text(report, encoding='utf-8')
    print(f'  보고서 저장: {fpath}')

    # 콘솔 요약
    print('\n=== 분류 결과 요약 ===')
    for r in stats['by_type']:
        label = TYPE_LABEL.get(r['doc_type'], r['doc_type'])
        pct = r['cnt'] / stats['total'] * 100 if stats['total'] else 0
        print(f'  {label:<30} {r["cnt"]:>5,}건 ({pct:.1f}%)')

    return str(fpath)


if __name__ == '__main__':
    run()

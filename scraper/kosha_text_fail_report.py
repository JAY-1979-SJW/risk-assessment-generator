"""
텍스트 추출 불가 항목 보고서 생성기
실행: python kosha_text_fail_report.py
결과: scraper/reports/kosha_text_fail_YYYYMMDD.md
"""
import psycopg2, psycopg2.extras
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

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


def collect_data():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # 전체 처리 현황
    cur.execute("SELECT COUNT(*) FROM kosha_materials")
    total_materials = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM kosha_material_files")
    total_files = cur.fetchone()[0]

    cur.execute("""
        SELECT parse_status, COUNT(*) cnt
        FROM kosha_material_files
        GROUP BY parse_status ORDER BY cnt DESC
    """)
    status_dist = cur.fetchall()

    cur.execute("""
        SELECT download_status, COUNT(*) cnt
        FROM kosha_material_files
        GROUP BY download_status ORDER BY cnt DESC
    """)
    dl_dist = cur.fetchall()

    # 텍스트 추출 실패 유형 1: parse_status = failed / unsupported
    cur.execute("""
        SELECT kmf.id, km.title, km.industry, km.list_type, km.reg_date,
               kmf.file_type, kmf.file_size, kmf.parse_status,
               kmf.mime_type, km.conts_atcfl_no, km.download_url,
               length(coalesce(kmf.raw_text,'')) AS text_len
        FROM kosha_material_files kmf
        JOIN kosha_materials km ON km.id = kmf.material_id
        WHERE kmf.parse_status IN ('failed', 'unsupported')
        ORDER BY kmf.parse_status, km.industry, kmf.file_type
    """)
    explicit_fails = cur.fetchall()

    # 텍스트 추출 실패 유형 2: parse_status=success 이지만 텍스트 길이 < 50 (이미지 기반 PDF)
    cur.execute("""
        SELECT kmf.id, km.title, km.industry, km.list_type, km.reg_date,
               kmf.file_type, kmf.file_size, kmf.parse_status,
               kmf.mime_type, km.conts_atcfl_no, km.download_url,
               length(coalesce(kmf.raw_text,'')) AS text_len
        FROM kosha_material_files kmf
        JOIN kosha_materials km ON km.id = kmf.material_id
        WHERE kmf.parse_status = 'success'
          AND length(coalesce(kmf.raw_text,'')) < 50
        ORDER BY km.industry, km.list_type, km.title
    """)
    empty_success = cur.fetchall()

    # 다운로드 실패
    cur.execute("""
        SELECT kmf.id, km.title, km.industry, km.list_type,
               kmf.download_status, km.download_url, km.conts_atcfl_no
        FROM kosha_material_files kmf
        JOIN kosha_materials km ON km.id = kmf.material_id
        WHERE kmf.download_status = 'failed'
        ORDER BY km.industry, km.list_type
    """)
    dl_fails = cur.fetchall()

    # 업종별 집계 (이미지 PDF)
    cur.execute("""
        SELECT km.industry, km.list_type, COUNT(*) cnt,
               SUM(kmf.file_size) total_size
        FROM kosha_material_files kmf
        JOIN kosha_materials km ON km.id = kmf.material_id
        WHERE kmf.parse_status = 'success'
          AND length(coalesce(kmf.raw_text,'')) < 50
        GROUP BY km.industry, km.list_type
        ORDER BY cnt DESC
    """)
    image_by_industry = cur.fetchall()

    # 파일 타입별 집계 (이미지 PDF)
    cur.execute("""
        SELECT kmf.file_type, COUNT(*) cnt
        FROM kosha_material_files kmf
        WHERE kmf.parse_status = 'success'
          AND length(coalesce(kmf.raw_text,'')) < 50
        GROUP BY kmf.file_type ORDER BY cnt DESC
    """)
    image_by_type = cur.fetchall()

    cur.close(); conn.close()

    return {
        'total_materials':  total_materials,
        'total_files':      total_files,
        'status_dist':      [dict(r) for r in status_dist],
        'dl_dist':          [dict(r) for r in dl_dist],
        'explicit_fails':   [dict(r) for r in explicit_fails],
        'empty_success':    [dict(r) for r in empty_success],
        'dl_fails':         [dict(r) for r in dl_fails],
        'image_by_industry': [dict(r) for r in image_by_industry],
        'image_by_type':    [dict(r) for r in image_by_type],
    }


def _size_str(b):
    if b is None:
        return '-'
    if b >= 1024 * 1024:
        return f'{b / 1024 / 1024:.1f}MB'
    return f'{b / 1024:.0f}KB'


def build_report(data: dict, generated_at: str) -> str:
    d = data
    total_fail = len(d['explicit_fails']) + len(d['empty_success']) + len(d['dl_fails'])

    lines = []
    lines.append(f'# KOSHA 텍스트 추출 불가 항목 보고서')
    lines.append(f'')
    lines.append(f'- 생성일시: {generated_at}')
    lines.append(f'- 대상 DB: common_data (127.0.0.1:5435)')
    lines.append(f'')

    # ── 요약 ──
    lines.append('## 1. 요약')
    lines.append('')
    lines.append(f'| 항목 | 건수 |')
    lines.append(f'|------|-----:|')
    lines.append(f'| 전체 자료(kosha_materials) | {d["total_materials"]:,} |')
    lines.append(f'| 처리된 파일(kosha_material_files) | {d["total_files"]:,} |')
    lines.append(f'| **텍스트 추출 불가 합계** | **{total_fail:,}** |')
    lines.append(f'| - 파싱 실패/미지원 (parse_status≠success) | {len(d["explicit_fails"]):,} |')
    lines.append(f'| - 이미지 기반 PDF (추출 텍스트 < 50자) | {len(d["empty_success"]):,} |')
    lines.append(f'| - 다운로드 실패 | {len(d["dl_fails"]):,} |')
    lines.append('')

    # ── parse_status 분포 ──
    lines.append('## 2. 파싱 상태 분포')
    lines.append('')
    lines.append('| parse_status | 건수 |')
    lines.append('|--------------|-----:|')
    for r in d['status_dist']:
        lines.append(f'| {r["parse_status"] or "NULL"} | {r["cnt"]:,} |')
    lines.append('')

    # ── 이미지 기반 PDF (유형별 핵심) ──
    lines.append('## 3. 이미지 기반 PDF (텍스트 추출 불가)')
    lines.append('')
    lines.append('> parse_status=success이나 추출 텍스트 길이 < 50자 → pdfplumber가 텍스트를 읽지 못한 이미지 PDF')
    lines.append('')

    if d['image_by_industry']:
        lines.append('### 3-1. 업종/자료유형별 집계')
        lines.append('')
        lines.append('| 업종 | 자료유형 | 건수 | 총 파일크기 |')
        lines.append('|------|----------|-----:|------------|')
        for r in d['image_by_industry']:
            lines.append(f'| {r["industry"]} | {r["list_type"]} | {r["cnt"]:,} | {_size_str(r["total_size"])} |')
        lines.append('')

    if d['image_by_type']:
        lines.append('### 3-2. 파일 타입별 집계')
        lines.append('')
        lines.append('| 파일타입 | 건수 |')
        lines.append('|----------|-----:|')
        for r in d['image_by_type']:
            lines.append(f'| {r["file_type"]} | {r["cnt"]:,} |')
        lines.append('')

    if d['empty_success']:
        lines.append('### 3-3. 전체 목록')
        lines.append('')
        lines.append('| # | 제목 | 업종 | 자료유형 | 파일크기 | conts_atcfl_no |')
        lines.append('|---|------|------|----------|----------|----------------|')
        for i, r in enumerate(d['empty_success'], 1):
            title = (r['title'] or '')[:60]
            lines.append(f'| {i} | {title} | {r["industry"]} | {r["list_type"]} '
                         f'| {_size_str(r["file_size"])} | {r["conts_atcfl_no"]} |')
        lines.append('')

    # ── 파싱 실패/미지원 ──
    if d['explicit_fails']:
        lines.append('## 4. 파싱 실패 / 미지원 형식')
        lines.append('')
        lines.append('| # | 제목 | 업종 | 파일타입 | parse_status | 파일크기 |')
        lines.append('|---|------|------|----------|--------------|----------|')
        for i, r in enumerate(d['explicit_fails'], 1):
            title = (r['title'] or '')[:60]
            lines.append(f'| {i} | {title} | {r["industry"]} | {r["file_type"]} '
                         f'| {r["parse_status"]} | {_size_str(r["file_size"])} |')
        lines.append('')
    else:
        lines.append('## 4. 파싱 실패 / 미지원 형식')
        lines.append('')
        lines.append('없음')
        lines.append('')

    # ── 다운로드 실패 ──
    if d['dl_fails']:
        lines.append('## 5. 다운로드 실패')
        lines.append('')
        lines.append('| # | 제목 | 업종 | conts_atcfl_no | download_url |')
        lines.append('|---|------|------|----------------|--------------|')
        for i, r in enumerate(d['dl_fails'], 1):
            title = (r['title'] or '')[:50]
            url = (r['download_url'] or '')[:80]
            lines.append(f'| {i} | {title} | {r["industry"]} | {r["conts_atcfl_no"]} | {url} |')
        lines.append('')
    else:
        lines.append('## 5. 다운로드 실패')
        lines.append('')
        lines.append('없음')
        lines.append('')

    # ── 조치 권고 ──
    lines.append('## 6. 조치 권고')
    lines.append('')
    lines.append('### 이미지 기반 PDF (OCR 필요)')
    lines.append('')
    lines.append('| 우선순위 | 방법 | 설명 |')
    lines.append('|----------|------|------|')
    lines.append('| 1 | pytesseract + pdf2image | PDF → 이미지 → OCR 텍스트 추출 |')
    lines.append('| 2 | AWS Textract / Google Document AI | 클라우드 OCR API 활용 |')
    lines.append('| 3 | pymupdf (fitz) | pdfplumber 대체, 일부 이미지 PDF 처리 가능 |')
    lines.append('')
    lines.append('### HWP/HWPX 미지원')
    lines.append('')
    lines.append('- hwp5txt (hwp5 패키지) 설치 후 재시도')
    lines.append('- 또는 LibreOffice headless 변환: `soffice --headless --convert-to txt`')
    lines.append('')
    lines.append('### 다운로드 실패')
    lines.append('')
    lines.append('- download_status=failed 건 재시도: `python kosha_pipeline.py --retry-failed`')
    lines.append('')
    lines.append('---')
    lines.append(f'*자동 생성: kosha_text_fail_report.py*')

    return '\n'.join(lines)


def run(save: bool = True) -> str:
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[보고서] 데이터 수집 중...')
    data = collect_data()
    print(f'[보고서] 마크다운 생성 중...')
    report = build_report(data, generated_at)

    if save:
        fname = f'kosha_text_fail_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
        fpath = REPORTS_DIR / fname
        fpath.write_text(report, encoding='utf-8')
        print(f'[보고서] 저장 완료: {fpath}')
        return str(fpath)
    else:
        print(report)
        return ''


if __name__ == '__main__':
    run(save=True)

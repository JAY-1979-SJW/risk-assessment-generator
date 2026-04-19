"""
KOSHA 전체 파이프라인 오케스트레이터
순서: materials → download → parse → chunk → classify → tag
"""
import time, argparse, psycopg2, psycopg2.extras
from pathlib import Path
from datetime import datetime
from logger import get_pipeline_logger, get_run_logger
from config import get_conn
from kosha_parser import ensure_tables, process_material
from kosha_classifier import run_classify_all

plog = get_pipeline_logger()
rlog = get_run_logger('pipeline')


# ── 인덱스 생성 (단계 11) ─────────────────────────────────────────────────────

EXTRA_INDEXES = [
    # kosha_materials
    "CREATE INDEX IF NOT EXISTS idx_km_industry_list ON kosha_materials(industry, list_type)",
    "CREATE INDEX IF NOT EXISTS idx_km_reg_date      ON kosha_materials(reg_date)",
    # kosha_material_chunks
    "CREATE INDEX IF NOT EXISTS idx_kmc_mat_section  ON kosha_material_chunks(material_id, section_type)",
    # kosha_chunk_tags
    "CREATE INDEX IF NOT EXISTS idx_kct_chunk   ON kosha_chunk_tags(chunk_id)",
    "CREATE INDEX IF NOT EXISTS idx_kct_trade   ON kosha_chunk_tags(trade_type)",
    "CREATE INDEX IF NOT EXISTS idx_kct_work    ON kosha_chunk_tags(work_type)",
    "CREATE INDEX IF NOT EXISTS idx_kct_hazard  ON kosha_chunk_tags(hazard_type)",
    # Full-text search on normalized_text
    """CREATE INDEX IF NOT EXISTS idx_kmc_fts ON kosha_material_chunks
       USING gin(to_tsvector('simple', coalesce(normalized_text,'')))""",
    # title + keyword 검색 보조 (kosha_materials)
    """CREATE INDEX IF NOT EXISTS idx_km_title_kw ON kosha_materials
       USING gin(to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(keyword,'')))""",
]


def create_indexes():
    conn = get_conn()
    cur = conn.cursor()
    for sql in EXTRA_INDEXES:
        try:
            cur.execute(sql)
            conn.commit()
            name = sql.split('idx_')[1].split(' ')[0] if 'idx_' in sql else '?'
            plog.info('[인덱스] idx_%s OK', name)
            print(f'  [인덱스] idx_{name} OK')
        except Exception as e:
            conn.rollback()
            plog.error('[인덱스 실패] %s', e)
            print(f'  [인덱스 실패] {e}')
    cur.close(); conn.close()
    plog.info('[인덱스] 전체 완료')
    print('[인덱스] 전체 완료')


# ── 다운로드 + 파싱 파이프라인 ───────────────────────────────────────────────

def run_download_parse(limit: int = 0, skip_existing: bool = True):
    """kosha_materials 기준 전체 자료 다운로드 + 파싱"""
    plog.info('[2단계] 다운로드+파싱 시작 limit=%d skip_existing=%s', limit, skip_existing)
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if skip_existing:
        # kosha_material_files가 없는 자료만 처리
        cur.execute("""
            SELECT km.id, km.title, km.conts_atcfl_no, km.download_url,
                   km.industry, km.list_type, km.reg_date
            FROM kosha_materials km
            WHERE km.download_url IS NOT NULL AND km.download_url != ''
              AND NOT EXISTS (
                  SELECT 1 FROM kosha_material_files kmf WHERE kmf.material_id = km.id
              )
            ORDER BY km.id
            {}
        """.format(f'LIMIT {limit}' if limit > 0 else ''))
    else:
        cur.execute("""
            SELECT id, title, conts_atcfl_no, download_url, industry, list_type, reg_date
            FROM kosha_materials
            WHERE download_url IS NOT NULL AND download_url != ''
            ORDER BY id
            {}
        """.format(f'LIMIT {limit}' if limit > 0 else ''))

    materials = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()

    plog.info('처리 대상: %d건', len(materials))
    print(f'[파이프라인] 처리 대상: {len(materials)}건')
    if not materials:
        plog.info('처리 대상 없음 — 종료')
        return {'processed': 0, 'success': 0, 'failed': 0, 'chunks': 0}

    stats = {'processed': 0, 'success': 0, 'failed': 0, 'chunks': 0}
    for mat in materials:
        r = process_material(mat, verbose=True)
        stats['processed'] += 1
        if r['status'] == 'success':
            stats['success'] += 1
            stats['chunks'] += r['chunks']
            plog.debug('파싱 성공 id=%s chunks=%d', mat['id'], r['chunks'])
        else:
            stats['failed'] += 1
            plog.warning('파싱 실패 id=%s status=%s', mat['id'], r.get('status'))
        time.sleep(0.3)

    plog.info('[2단계 완료] 처리:%d 성공:%d 실패:%d 청크:%d',
              stats['processed'], stats['success'], stats['failed'], stats['chunks'])
    print(f'\n[파이프라인 완료] 처리:{stats["processed"]} 성공:{stats["success"]} '
          f'실패:{stats["failed"]} 청크:{stats["chunks"]}')
    return stats


# ── 전체 파이프라인 실행 ─────────────────────────────────────────────────────

def run_full(limit: int = 0):
    start = datetime.now()
    rlog.info('=== 파이프라인 시작 === limit=%d', limit)
    print('=' * 60)
    print('KOSHA 지식 DB 구축 파이프라인')
    print('=' * 60)

    plog.info('[1단계] 테이블/인덱스 준비 시작')
    print('\n[1단계] 테이블/인덱스 준비')
    ensure_tables()
    create_indexes()
    plog.info('[1단계] 완료')

    plog.info('[2단계] 파일 다운로드 + 텍스트 추출 + 청크 저장 시작')
    print('\n[2단계] 파일 다운로드 + 텍스트 추출 + 청크 저장')
    stats = run_download_parse(limit=limit, skip_existing=True)

    plog.info('[3단계] 공종 분류 시작')
    print('\n[3단계] 공종 분류')
    classified = run_classify_all()

    elapsed = (datetime.now() - start).seconds
    rlog.info('=== 파이프라인 완료 === 성공:%d 청크:%d 분류:%d 소요:%d초',
              stats["success"], stats["chunks"], classified, elapsed)
    print('\n' + '=' * 60)
    print('파이프라인 완료')
    print(f'  다운로드/파싱 성공: {stats["success"]}건')
    print(f'  청크 생성: {stats["chunks"]}개')
    print(f'  공종 분류: {classified}건')
    print('=' * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KOSHA 파이프라인')
    parser.add_argument('--limit', type=int, default=0, help='처리 건수 (0=전체)')
    parser.add_argument('--classify-only', action='store_true', help='분류만 실행')
    parser.add_argument('--index-only', action='store_true', help='인덱스만 생성')
    args = parser.parse_args()

    if args.index_only:
        ensure_tables()
        create_indexes()
    elif args.classify_only:
        run_classify_all()
    else:
        run_full(limit=args.limit)

"""
KOSHA DB 검증 스크립트 (단계 12)
- chunk 수, trade_type null/기타/미분류 건수 = 0 검증
- 공종별 분포 상위 30개
- 샘플 50건 출력
"""
import json, psycopg2, psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

DB_HOST = '127.0.0.1'
DB_PORT = 5435
DB_NAME = 'common_data'
DB_USER = 'common_admin'
DB_PASS = 'XenZ5xmKw5jEf1bWQuU2LxWRZMlJ'

BANNED_VALUES = {'기타', '미분류', 'unknown', 'Unknown', 'UNKNOWN', None, ''}


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


def run_verification():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    print('=' * 60)
    print('KOSHA DB 검증 보고서')
    print('=' * 60)

    # ── 기본 카운트 ──────────────────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM kosha_materials")
    mat_total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM kosha_material_files")
    file_total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM kosha_material_chunks")
    chunk_total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM kosha_chunk_tags")
    tag_total = cur.fetchone()[0]

    print(f'\n[기본 현황]')
    print(f'  kosha_materials     : {mat_total:>8,}건')
    print(f'  kosha_material_files: {file_total:>8,}건')
    print(f'  kosha_material_chunks:{chunk_total:>8,}건')
    print(f'  kosha_chunk_tags    : {tag_total:>8,}건')

    # ── trade_type 검증 ──────────────────────────────────────────────────────
    print(f'\n[trade_type 검증]')

    cur.execute("SELECT COUNT(*) FROM kosha_chunk_tags WHERE trade_type IS NULL")
    null_cnt = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM kosha_chunk_tags WHERE trade_type = '기타'")
    gita_cnt = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM kosha_chunk_tags WHERE trade_type = '미분류'")
    unclassified_cnt = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM kosha_chunk_tags WHERE trade_type IN ('unknown','Unknown','UNKNOWN','')")
    unknown_cnt = cur.fetchone()[0]

    null_ok      = 'PASS' if null_cnt == 0 else f'FAIL({null_cnt}건)'
    gita_ok      = 'PASS' if gita_cnt == 0 else f'FAIL({gita_cnt}건)'
    unclass_ok   = 'PASS' if unclassified_cnt == 0 else f'FAIL({unclassified_cnt}건)'
    unknown_ok   = 'PASS' if unknown_cnt == 0 else f'FAIL({unknown_cnt}건)'

    print(f'  trade_type IS NULL     : {null_ok}')
    print(f'  trade_type = "기타"    : {gita_ok}')
    print(f'  trade_type = "미분류"  : {unclass_ok}')
    print(f'  trade_type = "unknown" : {unknown_ok}')

    # 미분류 chunk (태그 없는 것)
    cur.execute("""
        SELECT COUNT(*) FROM kosha_material_chunks kmc
        WHERE NOT EXISTS (SELECT 1 FROM kosha_chunk_tags kct WHERE kct.chunk_id = kmc.id)
    """)
    untagged = cur.fetchone()[0]
    untagged_ok = 'PASS' if untagged == 0 else f'WARN({untagged}건 미분류)'
    print(f'  태그 없는 chunk        : {untagged_ok}')

    # ── 공종별 분포 상위 30개 ────────────────────────────────────────────────
    print(f'\n[공종별 분포 상위 30개]')
    cur.execute("""
        SELECT trade_type, COUNT(*) AS cnt
        FROM kosha_chunk_tags
        GROUP BY trade_type
        ORDER BY cnt DESC
        LIMIT 30
    """)
    rows = cur.fetchall()
    for rank, row in enumerate(rows, 1):
        bar = '#' * min(40, row['cnt'] // max(1, tag_total // 400))
        print(f'  {rank:>2}. {row["trade_type"]:<15} {row["cnt"]:>6,}건  {bar}')

    # ── 다운로드 상태 ────────────────────────────────────────────────────────
    print(f'\n[다운로드 상태]')
    cur.execute("""
        SELECT download_status, COUNT(*) AS cnt
        FROM kosha_material_files
        GROUP BY download_status ORDER BY cnt DESC
    """)
    for row in cur.fetchall():
        print(f'  {row["download_status"] or "NULL":<20}: {row["cnt"]:>6,}건')

    # ── 파싱 상태 ────────────────────────────────────────────────────────────
    print(f'\n[파싱 상태]')
    cur.execute("""
        SELECT parse_status, COUNT(*) AS cnt
        FROM kosha_material_files
        GROUP BY parse_status ORDER BY cnt DESC
    """)
    for row in cur.fetchall():
        print(f'  {row["parse_status"] or "NULL":<20}: {row["cnt"]:>6,}건')

    # ── 샘플 50건 ────────────────────────────────────────────────────────────
    print(f'\n[샘플 50건 (수동 검토용)]')
    cur.execute("""
        SELECT km.title,
               kmc.raw_text,
               kct.trade_type,
               kct.confidence,
               kct.candidate_trades
        FROM kosha_chunk_tags kct
        JOIN kosha_material_chunks kmc ON kmc.id = kct.chunk_id
        JOIN kosha_materials km        ON km.id  = kmc.material_id
        ORDER BY kct.confidence ASC   -- 신뢰도 낮은 것 먼저 (검토 필요)
        LIMIT 50
    """)
    samples = cur.fetchall()
    for i, s in enumerate(samples, 1):
        candidates = s['candidate_trades']
        if isinstance(candidates, str):
            try:
                candidates = json.loads(candidates)
            except Exception:
                candidates = {}
        cand_str = ', '.join(f'{k}:{v:.2f}' for k, v in
                             sorted((candidates or {}).items(), key=lambda x: -x[1])[:3])
        title_short = (s['title'] or '')[:40]
        text_short  = (s['raw_text'] or '')[:60].replace('\n', ' ')
        print(f'\n  [{i:02d}] 자료: {title_short}')
        print(f'       텍스트: {text_short}')
        print(f'       분류: {s["trade_type"]}  신뢰도: {s["confidence"]}')
        print(f'       후보: {cand_str}')

    # ── 분류 애매 사례 10건 ──────────────────────────────────────────────────
    print(f'\n[분류 애매 사례 상위 10건 (confidence < 0.3)]')
    cur.execute("""
        SELECT km.title,
               kmc.raw_text,
               kct.trade_type,
               kct.confidence,
               kct.candidate_trades
        FROM kosha_chunk_tags kct
        JOIN kosha_material_chunks kmc ON kmc.id = kct.chunk_id
        JOIN kosha_materials km        ON km.id  = kmc.material_id
        WHERE kct.confidence < 0.3
        ORDER BY kct.confidence ASC
        LIMIT 10
    """)
    ambiguous = cur.fetchall()
    if not ambiguous:
        print('  없음 (모든 chunk confidence >= 0.3)')
    for i, s in enumerate(ambiguous, 1):
        candidates = s['candidate_trades']
        if isinstance(candidates, str):
            try:
                candidates = json.loads(candidates)
            except Exception:
                candidates = {}
        cand_str = ', '.join(f'{k}:{v:.2f}' for k, v in
                             sorted((candidates or {}).items(), key=lambda x: -x[1])[:3])
        print(f'\n  [{i}] {(s["title"] or "")[:40]}')
        print(f'      {(s["raw_text"] or "")[:60].replace(chr(10), " ")}')
        print(f'      => {s["trade_type"]} ({s["confidence"]}) | 후보: {cand_str}')

    cur.close(); conn.close()

    # 최종 판정
    print('\n' + '=' * 60)
    all_pass = (null_cnt == 0 and gita_cnt == 0 and
                unclassified_cnt == 0 and unknown_cnt == 0 and untagged == 0)
    print('최종 판정:', 'PASS - 모든 검증 통과' if all_pass else 'FAIL - 위 항목 확인 필요')
    print('=' * 60)
    return all_pass


if __name__ == '__main__':
    run_verification()

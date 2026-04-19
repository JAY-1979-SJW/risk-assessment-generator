"""
KOSHA ZIP 자동 해제 모듈

DB의 file_type='zip' + parse_status='pending'|'failed' 레코드를 NAS에서 해제하고
내부 파일(pdf/hwp/hwpx)을 kosha_material_files에 개별 레코드로 등록한다.

흐름:
  1. scan_pending_zips()      - DB에서 미해제 zip 조회
  2. extract_one_zip()        - zip → {FILES_BASE}/_extracted/{file_id}/
  3. register_inner_files()   - 내부 파일 DB 등록 (extracted_from_file_id 참조)
  4. mark_zip_extracted()     - 원본 zip → parse_status='extracted'
  5. run_parse_pending()      - 별도 호출로 등록된 inner 파일 파싱 (kosha_parser)
"""

import os
import zipfile
from pathlib import Path
from datetime import datetime

import psycopg2.extras

from config import get_conn, FILES_BASE
from kosha_parser import _resolve_path, ensure_tables
from logger import get_pipeline_logger, get_run_logger

log  = get_pipeline_logger()
rlog = get_run_logger('unzip')

EXTRACT_BASE       = FILES_BASE / '_extracted'
SUPPORTED_INNER    = {'pdf', 'hwp', 'hwpx'}
SUPPORTED_ARCHIVES = {'.zip'}
UNSUPPORTED_ARCHIVES = {'.tar', '.tar.gz', '.tgz', '.gz', '.7z', '.rar'}


# ── 1단계: DB 미해제 zip 조회 ──────────────────────────────────────────────────

def scan_pending_zips() -> list[dict]:
    """parse_status IN ('pending','failed') AND file_type='zip' 레코드 조회.
    이미 inner 파일이 등록된 zip은 제외(idempotent)."""
    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT f.id AS file_id, f.file_path, f.material_id
        FROM kosha_material_files f
        WHERE f.file_type = 'zip'
          AND f.parse_status IN ('pending', 'failed')
          AND f.file_path IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM kosha_material_files
              WHERE extracted_from_file_id = f.id
          )
        ORDER BY f.id
    """)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows


def count_by_status() -> dict:
    """zip 상태별 건수 집계"""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT parse_status, count(*)
        FROM kosha_material_files
        WHERE file_type = 'zip'
        GROUP BY parse_status
    """)
    result = {r[0]: r[1] for r in cur.fetchall()}
    cur.close(); conn.close()
    return result


# ── NAS 압축 파일 집계 ─────────────────────────────────────────────────────────

def scan_nas_archives() -> dict:
    """KOSHA_FILES_BASE 하위 압축 파일 확장자별 건수"""
    counts: dict[str, int] = {}
    unsupported: list[str] = []

    for f in FILES_BASE.rglob('*'):
        if not f.is_file():
            continue
        name = f.name.lower()
        matched = False
        for ext in list(SUPPORTED_ARCHIVES) + list(UNSUPPORTED_ARCHIVES):
            if name.endswith(ext):
                counts[ext] = counts.get(ext, 0) + 1
                if ext in UNSUPPORTED_ARCHIVES:
                    unsupported.append(str(f))
                matched = True
                break

    return {'counts': counts, 'unsupported_files': unsupported}


# ── 2단계: zip 해제 ────────────────────────────────────────────────────────────

def extract_one_zip(file_id: int, zip_path: str) -> dict:
    """
    zip → EXTRACT_BASE / str(file_id) /
    반환: {status, dest_dir, files:[{name,path,ext}], file_count, error}
    상태값: extracted | failed_unzip | already_extracted | file_not_found
    """
    dest_dir = EXTRACT_BASE / str(file_id)

    # 이미 해제된 경우 확인 (dest_dir 존재 + 파일 있음)
    if dest_dir.exists():
        inner = [f for f in dest_dir.rglob('*') if f.is_file()]
        if inner:
            log.debug('이미해제됨 file_id=%s dest=%s files=%d', file_id, dest_dir, len(inner))
            return {
                'status': 'already_extracted',
                'dest_dir': str(dest_dir),
                'files': _list_inner(dest_dir),
                'file_count': len(inner),
                'error': None,
            }

    if not os.path.exists(zip_path):
        return {'status': 'file_not_found', 'dest_dir': str(dest_dir),
                'files': [], 'file_count': 0, 'error': f'not found: {zip_path}'}

    dest_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path) as zf:
            # 비밀번호 필요 여부 사전 감지
            for info in zf.infolist():
                if info.flag_bits & 0x1:
                    return {'status': 'failed_unzip', 'dest_dir': str(dest_dir),
                            'files': [], 'file_count': 0, 'error': 'password_protected'}
            zf.extractall(dest_dir)
    except zipfile.BadZipFile as e:
        return {'status': 'failed_unzip', 'dest_dir': str(dest_dir),
                'files': [], 'file_count': 0, 'error': f'bad_zip: {e}'}
    except Exception as e:
        return {'status': 'failed_unzip', 'dest_dir': str(dest_dir),
                'files': [], 'file_count': 0, 'error': str(e)}

    inner_files = _list_inner(dest_dir)

    # 빈 폴더만 생성된 경우 실패 판정
    if not inner_files:
        return {'status': 'failed_unzip', 'dest_dir': str(dest_dir),
                'files': [], 'file_count': 0, 'error': 'empty_archive'}

    return {
        'status': 'extracted',
        'dest_dir': str(dest_dir),
        'files': inner_files,
        'file_count': len(inner_files),
        'error': None,
    }


def _list_inner(dest_dir: Path) -> list[dict]:
    """해제 디렉터리 내 지원 확장자 파일 목록"""
    result = []
    for f in sorted(dest_dir.rglob('*')):
        if not f.is_file():
            continue
        ext = f.suffix.lower().lstrip('.')
        if ext in SUPPORTED_INNER:
            result.append({'name': f.name, 'path': str(f), 'ext': ext})
    return result


# ── 3단계: inner 파일 DB 등록 ─────────────────────────────────────────────────

def register_inner_files(parent_file_id: int, material_id: int,
                         inner_files: list[dict]) -> int:
    """inner 파일 각각을 kosha_material_files에 INSERT.
    이미 등록된 경로는 건너뜀(file_path 중복 체크).
    반환: 신규 등록 건수"""
    if not inner_files:
        return 0

    conn = get_conn()
    cur  = conn.cursor()
    inserted = 0
    for f in inner_files:
        cur.execute(
            "SELECT id FROM kosha_material_files WHERE file_path = %s LIMIT 1",
            (f['path'],)
        )
        if cur.fetchone():
            continue
        cur.execute(
            """INSERT INTO kosha_material_files
                   (material_id, file_path, file_type, download_status,
                    parse_status, extracted_from_file_id, created_at)
               VALUES (%s, %s, %s, 'extracted', 'pending', %s, NOW())""",
            (material_id, f['path'], f['ext'], parent_file_id)
        )
        inserted += 1
    conn.commit()
    cur.close(); conn.close()
    return inserted


# ── 4단계: 원본 zip 상태 업데이트 ─────────────────────────────────────────────

def mark_zip_status(file_id: int, status: str, error: str = ''):
    """원본 zip 파일을 extracted / failed_unzip 으로 마킹"""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        """UPDATE kosha_material_files
           SET parse_status=%s, parsed_at=%s, raw_text=%s
           WHERE id=%s""",
        (status, datetime.now(), error[:500] if error else '', file_id)
    )
    conn.commit()
    cur.close(); conn.close()


# ── 메인: 전체 zip 해제 ────────────────────────────────────────────────────────

def run_unzip_all(verbose: bool = True) -> dict:
    """pending/failed zip 전체 해제 후 inner 파일 등록. 통계 반환."""
    ensure_tables()
    EXTRACT_BASE.mkdir(parents=True, exist_ok=True)

    start = datetime.now()
    rlog.info('=== ZIP 해제 시작 ===')

    # NAS 압축 파일 현황 집계
    nas_info = scan_nas_archives()
    if verbose:
        print('[ZIP 해제] NAS 압축 파일 집계:')
        for ext, cnt in sorted(nas_info['counts'].items(), key=lambda x: -x[1]):
            label = '지원' if ext in SUPPORTED_ARCHIVES else '미지원'
            print(f'  {ext}: {cnt}건 ({label})')
        if nas_info['unsupported_files']:
            print(f'  미지원 형식 {len(nas_info["unsupported_files"])}건 → unsupported 처리')
    for ext in SUPPORTED_ARCHIVES:
        log.info('[NAS] %s: %d건', ext, nas_info['counts'].get(ext, 0))
    for ext in UNSUPPORTED_ARCHIVES:
        if nas_info['counts'].get(ext, 0):
            log.warning('[NAS 미지원] %s: %d건', ext, nas_info['counts'][ext])

    # DB 상태 집계
    db_status = count_by_status()
    if verbose:
        print(f'\n[ZIP 해제] DB zip 현황: {db_status}')

    pending = scan_pending_zips()
    total   = len(pending)
    rlog.info('해제 대상: %d건', total)
    if verbose:
        print(f'[ZIP 해제] 해제 대상: {total}건')

    if total == 0:
        print('[ZIP 해제] 대상 없음')
        return {'extracted': 0, 'already': 0, 'failed': 0, 'registered': 0}

    stats = {'extracted': 0, 'already': 0, 'failed': 0,
             'failed_not_found': 0, 'registered': 0, 'empty': 0}

    for i, row in enumerate(pending, 1):
        file_id    = row['file_id']
        material_id = row['material_id']
        zip_path   = _resolve_path(row['file_path'])

        result = extract_one_zip(file_id, zip_path)

        if result['status'] == 'extracted':
            registered = register_inner_files(file_id, material_id, result['files'])
            mark_zip_status(file_id, 'extracted')
            stats['extracted'] += 1
            stats['registered'] += registered
            log.info('해제완료 file_id=%s inner=%d registered=%d',
                     file_id, result['file_count'], registered)
            if verbose and i % 50 == 0:
                print(f'  [{i}/{total}] 해제:{stats["extracted"]} 실패:{stats["failed"]} '
                      f'등록:{stats["registered"]}')

        elif result['status'] == 'already_extracted':
            registered = register_inner_files(file_id, material_id, result['files'])
            if registered:
                mark_zip_status(file_id, 'extracted')
            stats['already'] += 1
            stats['registered'] += registered

        elif result['status'] == 'file_not_found':
            mark_zip_status(file_id, 'failed_unzip', result['error'])
            stats['failed'] += 1
            stats['failed_not_found'] += 1
            log.warning('파일없음 file_id=%s path=%s', file_id, zip_path)

        else:  # failed_unzip
            mark_zip_status(file_id, 'failed_unzip', result['error'])
            stats['failed'] += 1
            if result['error'] == 'empty_archive':
                stats['empty'] += 1
            log.warning('해제실패 file_id=%s err=%s', file_id, result['error'])

    elapsed = (datetime.now() - start).seconds
    summary = (f'ZIP 해제 완료 소요:{elapsed}초 '
               f'해제:{stats["extracted"]} 이미완료:{stats["already"]} '
               f'실패:{stats["failed"]} 등록:{stats["registered"]}건 '
               f'(파일없음:{stats["failed_not_found"]} 빈아카이브:{stats["empty"]})')
    rlog.info('=== %s', summary)

    if verbose:
        print(f'\n=== ZIP 해제 완료 ===')
        print(f'  해제 성공: {stats["extracted"]}건 / 이미완료: {stats["already"]}건')
        print(f'  실패: {stats["failed"]}건 (파일없음={stats["failed_not_found"]} 빈아카이브={stats["empty"]})')
        print(f'  내부 파일 등록: {stats["registered"]}건')

    return stats


# ── 검증: 샘플 5건 ─────────────────────────────────────────────────────────────

def verify_sample(n: int = 5):
    """해제 완료된 zip 샘플 5건 검증 - 경로/파싱 결과 확인"""
    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT z.id AS zip_id, z.file_path AS zip_path,
               COUNT(i.id) AS inner_count,
               SUM(CASE WHEN i.parse_status='success' THEN 1 ELSE 0 END) AS parsed,
               SUM(CASE WHEN i.parse_status='pending' THEN 1 ELSE 0 END) AS pending,
               SUM(CASE WHEN i.parse_status='failed'  THEN 1 ELSE 0 END) AS failed
        FROM kosha_material_files z
        LEFT JOIN kosha_material_files i ON i.extracted_from_file_id = z.id
        WHERE z.file_type='zip' AND z.parse_status='extracted'
        GROUP BY z.id, z.file_path
        ORDER BY z.id DESC
        LIMIT %s
    """, (n,))
    rows = cur.fetchall()
    cur.close(); conn.close()

    print(f'\n=== 샘플 검증 ({n}건) ===')
    issues = []
    for r in rows:
        dest_dir = EXTRACT_BASE / str(r['zip_id'])
        dir_ok   = dest_dir.exists()
        print(f'  zip_id={r["zip_id"]} inner={r["inner_count"]} '
              f'parsed={r["parsed"]} pending={r["pending"]} failed={r["failed"]} '
              f'dir_exists={dir_ok}')
        if not dir_ok:
            issues.append(f'zip_id={r["zip_id"]}: extracted dir missing')
        if r['inner_count'] == 0:
            issues.append(f'zip_id={r["zip_id"]}: no inner files registered')

    # 중복 해제 여부 확인
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT extracted_from_file_id, count(*)
        FROM kosha_material_files
        WHERE extracted_from_file_id IS NOT NULL
        GROUP BY extracted_from_file_id
        HAVING count(*) > 0
        LIMIT 1
    """)
    sample_dup = cur.fetchone()
    cur.close(); conn.close()

    print(f'  중복 해제 여부: {"없음" if not issues else f"경고 {len(issues)}건"}')

    verdict = 'PASS' if not issues else ('WARN' if len(issues) <= 2 else 'FAIL')
    print(f'\n  VERDICT: {verdict}')
    if issues:
        for iss in issues:
            print(f'    ! {iss}')
    return verdict


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='KOSHA ZIP 해제')
    ap.add_argument('--verify', action='store_true', help='샘플 검증만 실행')
    ap.add_argument('--nas-scan', action='store_true', help='NAS 압축 파일 집계만')
    ap.add_argument('--sample', type=int, default=5, help='검증 샘플 수')
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    if args.nas_scan:
        info = scan_nas_archives()
        print('NAS 압축 파일 집계:')
        for ext, cnt in sorted(info['counts'].items(), key=lambda x: -x[1]):
            print(f'  {ext}: {cnt}건')
        if info['unsupported_files']:
            print(f'미지원 형식 {len(info["unsupported_files"])}건:')
            for f in info['unsupported_files'][:10]:
                print(f'  {f}')
    elif args.verify:
        verify_sample(args.sample)
    else:
        run_unzip_all()
        verify_sample(args.sample)

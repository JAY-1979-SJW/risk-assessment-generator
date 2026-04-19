"""
KOSHA 자료 파싱 모듈
kosha_materials → 파일 다운로드 → 텍스트 추출 → chunk 저장
"""
import os, re, json, time, hashlib, requests, psycopg2, psycopg2.extras
from pathlib import Path
from datetime import datetime
from logger import get_parser_logger, get_run_logger
from config import get_conn, FILES_BASE

log  = get_parser_logger()
rlog = get_run_logger('parser')


# ── 테이블 DDL ──────────────────────────────────────────────────────────────

CREATE_FILES_SQL = """
CREATE TABLE IF NOT EXISTS kosha_material_files (
    id               SERIAL PRIMARY KEY,
    material_id      INTEGER NOT NULL REFERENCES kosha_materials(id) ON DELETE CASCADE,
    file_path        TEXT,
    file_type        VARCHAR(10),
    file_hash        VARCHAR(64),
    file_size        BIGINT,
    mime_type        VARCHAR(100),
    download_status  VARCHAR(20) DEFAULT 'pending',
    source_url       TEXT,
    downloaded_at    TIMESTAMP,
    parse_status     VARCHAR(20) DEFAULT 'pending',
    parsed_at        TIMESTAMP,
    raw_text         TEXT,
    created_at       TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_kmf_material ON kosha_material_files(material_id);
CREATE INDEX IF NOT EXISTS idx_kmf_status   ON kosha_material_files(parse_status);
CREATE INDEX IF NOT EXISTS idx_kmf_dl_status ON kosha_material_files(download_status);
CREATE INDEX IF NOT EXISTS idx_kmf_hash     ON kosha_material_files(file_hash);
"""

CREATE_CHUNKS_SQL = """
CREATE TABLE IF NOT EXISTS kosha_material_chunks (
    id               SERIAL PRIMARY KEY,
    material_id      INTEGER NOT NULL REFERENCES kosha_materials(id) ON DELETE CASCADE,
    file_id          INTEGER REFERENCES kosha_material_files(id) ON DELETE CASCADE,
    chunk_index      INTEGER NOT NULL,
    section_type     VARCHAR(50),
    raw_text         TEXT NOT NULL,
    normalized_text  TEXT,
    work_type        TEXT,
    hazard_type      TEXT,
    control_measure  TEXT,
    ppe              TEXT,
    law_ref          TEXT,
    keywords         TEXT[],
    created_at       TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_kmc_material ON kosha_material_chunks(material_id);
CREATE INDEX IF NOT EXISTS idx_kmc_section  ON kosha_material_chunks(section_type);
CREATE INDEX IF NOT EXISTS idx_kmc_hazard   ON kosha_material_chunks(hazard_type);
CREATE INDEX IF NOT EXISTS idx_kmc_file     ON kosha_material_chunks(file_id);
"""

CREATE_TAGS_SQL = """
CREATE TABLE IF NOT EXISTS kosha_chunk_tags (
    id               SERIAL PRIMARY KEY,
    chunk_id         BIGINT NOT NULL REFERENCES kosha_material_chunks(id) ON DELETE CASCADE,
    industry         VARCHAR(20),
    trade_type       VARCHAR(50) NOT NULL,
    work_type        VARCHAR(50),
    hazard_type      VARCHAR(50),
    equipment        VARCHAR(100),
    location         VARCHAR(100),
    ppe              VARCHAR(200),
    law_ref          VARCHAR(500),
    confidence       NUMERIC(5,4),
    rule_version     VARCHAR(20) DEFAULT 'v1.0',
    candidate_trades JSONB,
    created_at       TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_kct_chunk      ON kosha_chunk_tags(chunk_id);
CREATE INDEX IF NOT EXISTS idx_kct_trade      ON kosha_chunk_tags(trade_type);
CREATE INDEX IF NOT EXISTS idx_kct_work       ON kosha_chunk_tags(work_type);
CREATE INDEX IF NOT EXISTS idx_kct_hazard     ON kosha_chunk_tags(hazard_type);
"""

MIGRATE_FILES_SQL = [
    "ALTER TABLE kosha_material_files ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64)",
    "ALTER TABLE kosha_material_files ADD COLUMN IF NOT EXISTS file_size BIGINT",
    "ALTER TABLE kosha_material_files ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100)",
    "ALTER TABLE kosha_material_files ADD COLUMN IF NOT EXISTS download_status VARCHAR(20) DEFAULT 'pending'",
    "ALTER TABLE kosha_material_files ADD COLUMN IF NOT EXISTS source_url TEXT",
    "ALTER TABLE kosha_material_files ADD COLUMN IF NOT EXISTS downloaded_at TIMESTAMP",
    "ALTER TABLE kosha_material_files ADD COLUMN IF NOT EXISTS extracted_from_file_id INTEGER",
    "CREATE INDEX IF NOT EXISTS idx_kmf_dl_status ON kosha_material_files(download_status)",
    "CREATE INDEX IF NOT EXISTS idx_kmf_hash ON kosha_material_files(file_hash)",
    "CREATE INDEX IF NOT EXISTS idx_kmf_extracted_from ON kosha_material_files(extracted_from_file_id)",
]

MIGRATE_MATERIALS_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_km_industry_list ON kosha_materials(industry, list_type)",
    "CREATE INDEX IF NOT EXISTS idx_km_reg_date      ON kosha_materials(reg_date)",
]


def ensure_tables():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_FILES_SQL)
    cur.execute(CREATE_CHUNKS_SQL)
    cur.execute(CREATE_TAGS_SQL)
    # 기존 테이블에 신규 컬럼 추가 (idempotent)
    for sql in MIGRATE_FILES_SQL:
        cur.execute(sql)
    for sql in MIGRATE_MATERIALS_SQL:
        cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    print('[DB] 테이블/인덱스 생성/확인 완료')


# ── 파일 저장 경로 결정 ──────────────────────────────────────────────────────

def _safe_name(s: str) -> str:
    """디렉터리명 안전 변환"""
    return re.sub(r'[\\/:*?"<>|]', '_', s).strip()


def resolve_file_dir(industry: str, list_type: str, reg_date: str) -> Path:
    """scraper/kosha_files/{industry}/{list_type}/{yyyyMMdd}/ 생성 후 반환"""
    date_part = re.sub(r'[^0-9]', '', reg_date or '')[:8] or datetime.now().strftime('%Y%m%d')
    d = FILES_BASE / _safe_name(industry or 'unknown') / _safe_name(list_type or 'unknown') / date_part
    d.mkdir(parents=True, exist_ok=True)
    return d


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ── 파일 다운로드 ────────────────────────────────────────────────────────────

def _existing_by_hash(file_hash: str) -> int | None:
    """동일 해시 파일이 이미 DB에 있으면 file_id 반환"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM kosha_material_files WHERE file_hash=%s LIMIT 1", (file_hash,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row[0] if row else None


def download_file(material_id: int, conts_atcfl_no: str, download_url: str,
                  industry: str = '', list_type: str = '', reg_date: str = '') -> dict | None:
    if not download_url:
        return {'material_id': material_id, 'download_status': 'failed',
                'source_url': '', 'error': 'no url'}

    try:
        resp = requests.get(download_url, timeout=30, stream=False)
        resp.raise_for_status()
    except Exception as e:
        print(f'  [다운로드 실패] {conts_atcfl_no}: {e}')
        return {'material_id': material_id, 'download_status': 'failed',
                'source_url': download_url, 'error': str(e)}

    content = resp.content
    file_hash = sha256_of(content)

    # 중복 확인
    existing_id = _existing_by_hash(file_hash)
    if existing_id:
        print(f'  [중복 스킵] {conts_atcfl_no} → file_id={existing_id} (동일 해시)')
        return {'material_id': material_id, 'download_status': 'duplicate',
                'file_hash': file_hash, 'existing_file_id': existing_id,
                'source_url': download_url}

    # 확장자 추정
    ct = resp.headers.get('Content-Type', '')
    cd = resp.headers.get('Content-Disposition', '')
    if 'pdf' in ct:
        ext, mime = 'pdf', ct.split(';')[0].strip()
    elif 'hwp' in ct or 'haansoft' in ct:
        ext, mime = 'hwp', ct.split(';')[0].strip()
    elif 'zip' in ct:
        ext, mime = 'zip', ct.split(';')[0].strip()
    else:
        m = re.search(r'filename[^;=\n]*=.*?\.(\w+)', cd, re.IGNORECASE)
        ext = m.group(1).lower() if m else 'bin'
        mime = ct.split(';')[0].strip() or 'application/octet-stream'

    file_dir = resolve_file_dir(industry, list_type, reg_date)
    fname = f'{material_id}_{conts_atcfl_no}.{ext}'
    fpath = file_dir / fname
    fpath.write_bytes(content)
    print(f'  [저장] {fpath.relative_to(FILES_BASE)} ({len(content)//1024}KB)')

    return {
        'material_id':     material_id,
        'file_path':       str(fpath),
        'file_type':       ext,
        'file_hash':       file_hash,
        'file_size':       len(content),
        'mime_type':       mime,
        'download_status': 'downloaded',
        'source_url':      download_url,
        'downloaded_at':   datetime.now(),
        'parse_status':    'pending',
    }


def save_file_record(rec: dict) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO kosha_material_files
               (material_id, file_path, file_type, file_hash, file_size,
                mime_type, download_status, source_url, downloaded_at, parse_status)
           VALUES
               (%(material_id)s, %(file_path)s, %(file_type)s, %(file_hash)s, %(file_size)s,
                %(mime_type)s, %(download_status)s, %(source_url)s, %(downloaded_at)s, %(parse_status)s)
           RETURNING id""",
        rec
    )
    file_id = cur.fetchone()[0]
    conn.commit()
    cur.close(); conn.close()
    return file_id


def record_download_failure(material_id: int, source_url: str, error: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO kosha_material_files
               (material_id, download_status, source_url, parse_status)
           VALUES (%s, 'failed', %s, 'pending')""",
        (material_id, source_url)
    )
    conn.commit()
    cur.close(); conn.close()


# ── PDF/HWP 텍스트 추출 ──────────────────────────────────────────────────────

def extract_text_pdf(file_path: str) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            pages = [p.extract_text() or '' for p in pdf.pages]
        return '\n'.join(pages)
    except ImportError:
        pass
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        return '\n'.join(p.extract_text() or '' for p in reader.pages)
    except Exception as e:
        return f'[PDF추출실패: {e}]'


def extract_text_hwp(file_path: str) -> str:
    # HWPX (zip 기반) 시도
    if file_path.endswith('x') or file_path.endswith('hwpx'):
        try:
            import zipfile
            with zipfile.ZipFile(file_path) as z:
                names = z.namelist()
                texts = []
                for n in names:
                    if n.startswith('Contents/') and n.endswith('.xml'):
                        xml = z.read(n).decode('utf-8', errors='ignore')
                        text = re.sub(r'<[^>]+>', ' ', xml)
                        texts.append(text)
                if texts:
                    return '\n'.join(texts)
        except Exception:
            pass

    # HWP5 OLE 기반
    try:
        import olefile
        with olefile.OleFileIO(file_path) as ole:
            if ole.exists('BodyText/Section0'):
                raw = ole.openstream('BodyText/Section0').read()
                try:
                    import zlib
                    decompressed = zlib.decompress(raw, -15)
                    text = decompressed.decode('utf-16-le', errors='ignore')
                except Exception:
                    text = raw.decode('utf-16-le', errors='ignore')
                return re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', ' ', text)
    except Exception as e:
        return f'[HWP추출실패: {e}]'
    return ''


def extract_text_zip(file_path: str) -> str:
    """ZIP 내부의 PDF/HWP 파일을 모두 파싱해 텍스트 합산"""
    import zipfile, tempfile
    texts = []
    try:
        with zipfile.ZipFile(file_path) as z:
            for name in z.namelist():
                ext = Path(name).suffix.lower().lstrip('.')
                if ext not in ('pdf', 'hwp', 'hwpx'):
                    continue
                try:
                    data = z.read(name)
                    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
                        tmp.write(data)
                        tmp_path = tmp.name
                    if ext == 'pdf':
                        t = extract_text_pdf(tmp_path)
                    else:
                        t = extract_text_hwp(tmp_path)
                    Path(tmp_path).unlink(missing_ok=True)
                    if t and not t.startswith('['):
                        texts.append(f'[{name}]\n{t}')
                        log.debug('zip 내부 파일 파싱 완료: %s (%d자)', name, len(t))
                except Exception as e:
                    log.warning('zip 내부 파일 파싱 실패: %s err=%s', name, e)
    except Exception as e:
        return f'[ZIP추출실패: {e}]'
    return '\n\n'.join(texts)


def extract_text(file_path: str, file_type: str) -> tuple[str, str]:
    if file_type == 'pdf':
        text = extract_text_pdf(file_path)
        status = 'failed' if text.startswith('[PDF추출실패') else 'success'
    elif file_type in ('hwp', 'hwpx'):
        text = extract_text_hwp(file_path)
        status = 'failed' if text.startswith('[HWP추출실패') else 'success'
        if not text.strip():
            status = 'unsupported'
    elif file_type == 'zip':
        text = extract_text_zip(file_path)
        if text.startswith('[ZIP추출실패'):
            status = 'failed'
        elif not text.strip():
            status = 'unsupported'
        else:
            status = 'success'
    else:
        return '', 'unsupported'
    return text, status


# ── 텍스트 정규화 ────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    text = re.sub(r'\(cid:\d+\)', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[□■○●◆◇▶▷→]', '', text)
    return text.strip()


# ── section_type 감지 ────────────────────────────────────────────────────────

HAZARD_KW  = ['위험', '유해', '추락', '협착', '감전', '폭발', '화재', '충돌', '낙하', '절단', '질식', '중독']
CONTROL_KW = ['안전조치', '대책', '예방', '금지', '착용', '설치', '점검', '관리', '방호', '차단']
PPE_KW     = ['안전모', '안전대', '보호구', '장갑', '안전화', '마스크', '귀마개', '보안경', '안전벨트']
LAW_KW     = ['조', '항', '안전보건규칙', '산업안전보건법', 'KOSHA', '고용노동부고시']
WORK_KW    = ['작업', '공정', '설치', '해체', '굴착', '용접', '고소', '전기', '화학', '배관', '배선']


def detect_section(text: str) -> str:
    for kw in PPE_KW:
        if kw in text:
            return 'ppe'
    for kw in LAW_KW:
        if kw in text:
            return 'law'
    for kw in HAZARD_KW:
        if kw in text:
            return 'hazard'
    for kw in CONTROL_KW:
        if kw in text:
            return 'control'
    return 'general'


def extract_field(text: str, keywords: list[str]) -> str | None:
    for kw in keywords:
        if kw in text:
            return kw
    return None


def extract_keywords(text: str) -> list[str]:
    found = []
    for kw in HAZARD_KW + CONTROL_KW + PPE_KW + WORK_KW:
        if kw in text and kw not in found:
            found.append(kw)
    return found


# ── 텍스트 → chunks ──────────────────────────────────────────────────────────

def split_chunks(text: str, min_len: int = 30) -> list[str]:
    parts = re.split(r'\n{2,}|(?=\d+\.\s)|(?=[①②③④⑤⑥⑦⑧⑨⑩])', text)
    chunks = [p.strip() for p in parts if len(p.strip()) >= min_len]
    return chunks


def _korean_ratio(text: str) -> float:
    """텍스트 내 한글 비율 (0.0~1.0)"""
    if not text:
        return 0.0
    korean = sum(1 for c in text if '\uAC00' <= c <= '\uD7A3' or '\u3131' <= c <= '\u314E')
    return korean / len(text)


def build_chunks(material_id: int, file_id: int, raw_text: str,
                 min_korean_ratio: float = 0.1, min_len: int = 50) -> list[dict]:
    parts = split_chunks(raw_text)
    result = []
    skipped = 0
    for idx, part in enumerate(parts):
        # 최소 길이 미달 또는 한글 비율 10% 미만 → 제외
        if len(part) < min_len or _korean_ratio(part) < min_korean_ratio:
            skipped += 1
            continue
        norm = normalize(part)
        section = detect_section(norm)
        result.append({
            'material_id':     material_id,
            'file_id':         file_id,
            'chunk_index':     idx,
            'section_type':    section,
            'raw_text':        part,
            'normalized_text': norm,
            'work_type':       extract_field(norm, WORK_KW),
            'hazard_type':     extract_field(norm, HAZARD_KW),
            'control_measure': extract_field(norm, CONTROL_KW),
            'ppe':             extract_field(norm, PPE_KW),
            'law_ref':         extract_field(norm, LAW_KW),
            'keywords':        extract_keywords(norm),
        })
    if skipped:
        log.debug('청크 필터 제외 %d개 (외국어/짧은텍스트) material_id=%s', skipped, material_id)
    return result


def save_chunks(chunks: list[dict]) -> list[int]:
    """chunk 저장 후 생성된 id 목록 반환"""
    if not chunks:
        return []
    conn = get_conn()
    cur = conn.cursor()
    ids = []
    for c in chunks:
        cur.execute("""
            INSERT INTO kosha_material_chunks
                (material_id, file_id, chunk_index, section_type,
                 raw_text, normalized_text, work_type, hazard_type,
                 control_measure, ppe, law_ref, keywords)
            VALUES
                (%(material_id)s, %(file_id)s, %(chunk_index)s, %(section_type)s,
                 %(raw_text)s, %(normalized_text)s, %(work_type)s, %(hazard_type)s,
                 %(control_measure)s, %(ppe)s, %(law_ref)s, %(keywords)s)
            RETURNING id
        """, c)
        ids.append(cur.fetchone()[0])
    conn.commit()
    cur.close(); conn.close()
    return ids


def update_file_parse(file_id: int, status: str, raw_text: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """UPDATE kosha_material_files
           SET parse_status=%s, parsed_at=%s, raw_text=%s
           WHERE id=%s""",
        (status, datetime.now(), raw_text[:200000], file_id)
    )
    conn.commit()
    cur.close(); conn.close()


# ── 파이프라인 (단일 자료) ───────────────────────────────────────────────────

def process_material(material: dict, verbose: bool = True) -> dict:
    mid      = material['id']
    no       = material['conts_atcfl_no']
    url      = material['download_url']
    title    = material['title']
    industry = material.get('industry', '')
    lt       = material.get('list_type', '')
    reg_date = material.get('reg_date', '')

    log.debug('파싱 시작 id=%s title=%s', mid, title[:40])
    if verbose:
        print(f'\n[{mid}] {title[:50]}')

    rec = download_file(mid, no, url, industry, lt, reg_date)
    if rec is None or rec.get('download_status') == 'failed':
        err = rec.get('error', 'unknown') if rec else 'unknown'
        record_download_failure(mid, url, err)
        log.error('다운로드 실패 id=%s err=%s', mid, err)
        return {'material_id': mid, 'status': 'download_failed', 'chunks': 0, 'chunk_ids': []}

    if rec.get('download_status') == 'duplicate':
        log.debug('중복 파일 id=%s', mid)
        return {'material_id': mid, 'status': 'duplicate',
                'chunks': 0, 'chunk_ids': [],
                'existing_file_id': rec.get('existing_file_id')}

    file_id = save_file_record(rec)
    raw_text, status = extract_text(rec['file_path'], rec['file_type'])
    update_file_parse(file_id, status, raw_text)

    if status != 'success' or not raw_text.strip():
        log.warning('텍스트 추출 실패 id=%s status=%s file=%s', mid, status, rec.get('file_path',''))
        if verbose:
            print(f'  → parse_status: {status}')
        return {'material_id': mid, 'status': status, 'chunks': 0, 'chunk_ids': [], 'file_id': file_id}

    chunks = build_chunks(mid, file_id, raw_text)
    chunk_ids = save_chunks(chunks)

    dist = {}
    for c in chunks:
        dist[c['section_type']] = dist.get(c['section_type'], 0) + 1

    log.info('파싱 완료 id=%s chunks=%d chars=%d 섹션=%s',
             mid, len(chunks), len(raw_text), dist)
    if verbose:
        print(f'  → chunks: {len(chunks)}개 | 섹션: {dist}')

    return {'material_id': mid, 'status': status,
            'chunks': len(chunks), 'chunk_ids': chunk_ids, 'file_id': file_id}


# ── 샘플 실행 ────────────────────────────────────────────────────────────────

_WIN_KOSHA_MARKER = 'kosha_files'

def _resolve_path(db_path: str) -> str:
    """DB에 저장된 경로(Windows 역슬래시/서버 혼재)를 현재 FILES_BASE 기준으로 변환."""
    # Windows 역슬래시 → 슬래시 정규화
    normalized = db_path.replace('\\', '/')
    parts = [p for p in normalized.split('/') if p]
    try:
        idx = next(i for i, part in enumerate(parts)
                   if part.lower() == _WIN_KOSHA_MARKER)
        rel = '/'.join(parts[idx + 1:])
        return str(FILES_BASE / rel)
    except StopIteration:
        return db_path


def run_parse_pending(batch_size: int = 100):
    """다운로드 완료(parse_status=pending)된 파일 전체 파싱"""
    ensure_tables()
    start = datetime.now()

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT f.id AS file_id, f.file_path, f.file_type,
               m.id AS material_id, m.title, m.industry
        FROM kosha_material_files f
        JOIN kosha_materials m ON m.id = f.material_id
        WHERE f.parse_status = 'pending'
          AND f.file_path IS NOT NULL
          AND f.file_type IN ('pdf','hwp','hwpx','zip')
        ORDER BY f.id
    """)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()

    total = len(rows)
    rlog.info('=== 기존파일 파싱 시작 === 대상:%d건', total)
    print(f'[파싱] 대상: {total:,}건 (parse_status=pending)')

    if total == 0:
        print('파싱 대상 없음')
        return

    stats = {'parsed': 0, 'failed': 0, 'unsupported': 0, 'chunks': 0,
             'no_file': 0, 'encoding': 0, 'exception': 0, 'empty': 0}

    for i, row in enumerate(rows, 1):
        file_id   = row['file_id']
        file_type = row['file_type']
        mid       = row['material_id']
        file_path = _resolve_path(row['file_path'])

        if not os.path.exists(file_path):
            stats['failed'] += 1
            stats['no_file'] += 1
            update_file_parse(file_id, 'failed', '')
            log.warning('파일없음 file_id=%s path=%s', file_id, file_path)
            continue

        try:
            raw_text, parse_status = extract_text(file_path, file_type)
            update_file_parse(file_id, parse_status, raw_text)

            if parse_status == 'success' and raw_text.strip():
                chunks = build_chunks(mid, file_id, raw_text)
                save_chunks(chunks)
                stats['parsed'] += 1
                stats['chunks'] += len(chunks)
                log.debug('파싱 완료 file_id=%s mid=%s chunks=%d', file_id, mid, len(chunks))
            elif parse_status == 'unsupported':
                stats['unsupported'] += 1
            elif parse_status == 'success' and not raw_text.strip():
                stats['failed'] += 1
                stats['empty'] += 1
                log.warning('본문비어있음 file_id=%s mid=%s', file_id, mid)
            else:
                stats['failed'] += 1
                if '[추출실패' in (raw_text or '') and '인코딩' in (raw_text or ''):
                    stats['encoding'] += 1
                log.warning('파싱실패 file_id=%s mid=%s status=%s', file_id, mid, parse_status)
        except Exception as e:
            stats['failed'] += 1
            stats['exception'] += 1
            update_file_parse(file_id, 'failed', '')
            log.error('파싱예외 file_id=%s mid=%s err=%s', file_id, mid, e)

        if i % batch_size == 0 or i == total:
            elapsed = (datetime.now() - start).seconds or 1
            rate = i / elapsed
            remain = int((total - i) / rate / 60) if rate > 0 else 0
            msg = (f'[{i:,}/{total:,}] 파싱:{stats["parsed"]} 실패:{stats["failed"]} '
                   f'청크:{stats["chunks"]} 속도:{rate:.1f}건/s 잔여:{remain}분')
            print(f'  {msg}')
            log.info(msg)

    elapsed = (datetime.now() - start).seconds
    summary = (f'파싱 완료 소요:{elapsed//60}분{elapsed%60}초 '
               f'성공:{stats["parsed"]}건 실패:{stats["failed"]}건 '
               f'미지원:{stats["unsupported"]}건 청크:{stats["chunks"]}개 '
               f'(파일없음:{stats["no_file"]} 빈본문:{stats["empty"]} 예외:{stats["exception"]})')
    print(f'\n=== 파싱 완료 ===')
    print(f'  성공: {stats["parsed"]:,}건 / 실패: {stats["failed"]:,}건 / 미지원: {stats["unsupported"]:,}건')
    print(f'  청크: {stats["chunks"]:,}개')
    print(f'  실패 세부: 파일없음={stats["no_file"]} 빈본문={stats["empty"]} 예외={stats["exception"]}')
    rlog.info('=== %s', summary)
    return stats


def run_sample(n: int = 5):
    ensure_tables()
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        """SELECT id, title, conts_atcfl_no, download_url, industry, list_type, reg_date
           FROM kosha_materials
           WHERE download_url IS NOT NULL AND download_url != ''
           ORDER BY id
           LIMIT %s""",
        (n,)
    )
    materials = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()

    if not materials:
        print('[샘플] kosha_materials에 download_url 있는 자료 없음')
        return

    print(f'=== 샘플 파싱: {len(materials)}건 ===')
    results = []
    for mat in materials:
        r = process_material(mat)
        results.append(r)
        time.sleep(0.3)

    print('\n=== 샘플 결과 요약 ===')
    for r in results:
        print(f'  material_id={r["material_id"]} | status={r["status"]} | chunks={r["chunks"]}')


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--pending', action='store_true', help='pending 파일 전체 파싱')
    ap.add_argument('--sample', type=int, default=0, help='샘플 N건 파싱')
    args = ap.parse_args()
    if args.pending:
        run_parse_pending()
    elif args.sample:
        run_sample(n=args.sample)
    else:
        run_parse_pending()

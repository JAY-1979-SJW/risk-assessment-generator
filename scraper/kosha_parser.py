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
    "ALTER TABLE kosha_material_files ADD COLUMN IF NOT EXISTS lang_verdict VARCHAR(20)",
    "CREATE INDEX IF NOT EXISTS idx_kmf_dl_status ON kosha_material_files(download_status)",
    "CREATE INDEX IF NOT EXISTS idx_kmf_hash ON kosha_material_files(file_hash)",
    "CREATE INDEX IF NOT EXISTS idx_kmf_extracted_from ON kosha_material_files(extracted_from_file_id)",
    "CREATE INDEX IF NOT EXISTS idx_kmf_lang ON kosha_material_files(lang_verdict)",
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
# 우선순위: hazard > control > law > ppe > general
# - HAZARD: '위험요인','추락' 등 구체적 사고 키워드 (과거의 '위험','유해' 단독 제거 — 너무 광범위)
# - CONTROL: '안전조치','안전대책' 등 복합어만 사용 (과거 '관리','설치','점검' 등 단독어 제거)
# - LAW: '산업안전보건법','안전보건규칙' 등 명확한 법령명만 (과거 '조','항' 제거 — 일반 단어에 오매칭)
# - PPE: 보호구 종류 (hazard/control 미검출 시 보조 분류)

HAZARD_KW  = ['위험요인', '유해요인', '사고원인', '재해원인', '재해사례',
              '추락', '협착', '감전', '폭발', '화재', '충돌', '낙하', '절단', '질식', '중독',
              '위험성평가']
CONTROL_KW = ['안전조치', '안전대책', '예방대책', '방호조치', '재해예방',
              '안전수칙', '대책', '방호', '안전관리']
PPE_KW     = ['안전모', '안전대', '보호구', '안전화', '마스크', '귀마개', '보안경', '안전벨트', '장갑']
LAW_KW     = ['산업안전보건법', '안전보건규칙', '기준에 관한 규칙', '고용노동부고시', 'KOSHA', '시행규칙']
WORK_KW    = ['작업', '공정', '설치', '해체', '굴착', '용접', '고소', '전기', '화학', '배관', '배선']


def detect_section(text: str) -> str:
    for kw in HAZARD_KW:
        if kw in text:
            return 'hazard'
    for kw in CONTROL_KW:
        if kw in text:
            return 'control'
    for kw in LAW_KW:
        if kw in text:
            return 'law'
    for kw in PPE_KW:
        if kw in text:
            return 'ppe'
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


def _is_korean(c: str) -> bool:
    return '\uAC00' <= c <= '\uD7A3' or '\u3131' <= c <= '\u314E'


def _korean_ratio(text: str) -> float:
    """알파벳 문자(한글+영문+CJK) 중 한글 비율. 숫자·공백·특수문자 제외."""
    if not text:
        return 0.0
    alpha = [c for c in text if c.isalpha()]
    if not alpha:
        return 0.0
    korean = sum(1 for c in alpha if _is_korean(c))
    return korean / len(alpha)


# 한글 비율 기준 (알파벳 대비): keep≥0.60 / mixed≥0.30 / foreign<0.30
LANG_KEEP_THRESHOLD   = 0.60
LANG_MIXED_THRESHOLD  = 0.30

def classify_language(text: str) -> tuple[str, float]:
    """raw_text 전체에 대한 언어 판정. ('keep'|'mixed'|'foreign', ratio) 반환"""
    ratio = _korean_ratio(text)
    if ratio >= LANG_KEEP_THRESHOLD:
        return 'keep', ratio
    if ratio >= LANG_MIXED_THRESHOLD:
        return 'mixed', ratio
    return 'foreign', ratio


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


def update_file_parse(file_id: int, status: str, raw_text: str, lang_verdict: str | None = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """UPDATE kosha_material_files
           SET parse_status=%s, parsed_at=%s, raw_text=%s, lang_verdict=%s
           WHERE id=%s""",
        (status, datetime.now(), raw_text[:200000], lang_verdict, file_id)
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


def run_parse_pending(batch_size: int = 50):
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
          AND f.file_type = 'pdf'
        ORDER BY f.id
    """)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()

    total = len(rows)
    rlog.info('=== 기존파일 파싱 시작 === 대상:%d건', total)
    print(f'[파싱] 대상: {total:,}건 (parse_status=pending, pdf+한국어만)')

    if total == 0:
        print('파싱 대상 없음')
        return

    stats = {'parsed': 0, 'failed': 0, 'unsupported': 0, 'chunks': 0,
             'no_file': 0, 'encoding': 0, 'exception': 0, 'empty': 0,
             'excluded_foreign': 0, 'excluded_mixed': 0}

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

            if parse_status == 'success' and raw_text.strip():
                verdict, ratio = classify_language(raw_text)
                if verdict == 'foreign':
                    update_file_parse(file_id, 'excluded_foreign', raw_text, 'foreign')
                    stats['excluded_foreign'] += 1
                    log.info('외국어 제외 file_id=%s mid=%s ratio=%.2f', file_id, mid, ratio)
                    continue
                if verdict == 'mixed':
                    update_file_parse(file_id, 'excluded_mixed', raw_text, 'mixed')
                    stats['excluded_mixed'] += 1
                    log.info('혼합언어 제외 file_id=%s mid=%s ratio=%.2f', file_id, mid, ratio)
                    continue
                update_file_parse(file_id, parse_status, raw_text, 'keep')
                chunks = build_chunks(mid, file_id, raw_text)
                save_chunks(chunks)
                stats['parsed'] += 1
                stats['chunks'] += len(chunks)
                log.debug('파싱 완료 file_id=%s mid=%s chunks=%d ratio=%.2f', file_id, mid, len(chunks), ratio)
            elif parse_status == 'unsupported':
                update_file_parse(file_id, parse_status, raw_text)
                stats['unsupported'] += 1
            elif parse_status == 'success' and not raw_text.strip():
                update_file_parse(file_id, 'image_pdf', raw_text)
                stats.setdefault('image_pdf', 0)
                stats['image_pdf'] += 1
                log.info('이미지PDF 분류 file_id=%s mid=%s', file_id, mid)
            else:
                update_file_parse(file_id, parse_status, raw_text)
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
                   f'이미지PDF:{stats.get("image_pdf",0)} '
                   f'외국어제외:{stats["excluded_foreign"]} 혼합제외:{stats["excluded_mixed"]} '
                   f'청크:{stats["chunks"]} 속도:{rate:.1f}건/s 잔여:{remain}분')
            print(f'  {msg}', flush=True)
            log.info(msg)

    elapsed = (datetime.now() - start).seconds
    summary = (f'파싱 완료 소요:{elapsed//60}분{elapsed%60}초 '
               f'성공:{stats["parsed"]}건 실패:{stats["failed"]}건 '
               f'이미지PDF:{stats.get("image_pdf",0)}건 '
               f'미지원:{stats["unsupported"]}건 청크:{stats["chunks"]}개 '
               f'외국어제외:{stats["excluded_foreign"]} 혼합제외:{stats["excluded_mixed"]} '
               f'(파일없음:{stats["no_file"]} 예외:{stats["exception"]})')
    print(f'\n=== 파싱 완료 ===', flush=True)
    print(f'  성공: {stats["parsed"]:,}건 / 이미지PDF: {stats.get("image_pdf",0):,}건 / 실패: {stats["failed"]:,}건', flush=True)
    print(f'  외국어 제외: {stats["excluded_foreign"]:,}건 / 혼합 제외: {stats["excluded_mixed"]:,}건', flush=True)
    print(f'  청크: {stats["chunks"]:,}개', flush=True)
    print(f'  실패 세부: 파일없음={stats["no_file"]} 예외={stats["exception"]}', flush=True)
    rlog.info('=== %s', summary)
    return stats


def run_reclassify_language(batch_size: int = 200):
    """기존 success 파일의 raw_text로 언어 재판정. foreign/mixed → 청크 비활성(삭제) + 상태 업데이트."""
    ensure_tables()
    start = datetime.now()

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT id AS file_id, material_id, raw_text
        FROM kosha_material_files
        WHERE parse_status = 'success'
          AND raw_text IS NOT NULL
          AND lang_verdict IS NULL
        ORDER BY id
    """)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()

    total = len(rows)
    rlog.info('=== 언어 재판정 시작 === 대상:%d건', total)
    print(f'[재판정] 대상: {total:,}건')
    if total == 0:
        print('재판정 대상 없음')
        return

    stats = {'keep': 0, 'foreign': 0, 'mixed': 0, 'chunks_deleted': 0}

    conn = get_conn()
    cur = conn.cursor()
    for i, row in enumerate(rows, 1):
        file_id = row['file_id']
        mid     = row['material_id']
        text    = row['raw_text'] or ''
        verdict, ratio = classify_language(text)

        if verdict in ('foreign', 'mixed'):
            new_status = 'excluded_foreign' if verdict == 'foreign' else 'excluded_mixed'
            cur.execute(
                "UPDATE kosha_material_files SET parse_status=%s, lang_verdict=%s WHERE id=%s",
                (new_status, verdict, file_id)
            )
            # 해당 파일의 청크 삭제 (검색 대상 제외)
            cur.execute("DELETE FROM kosha_material_chunks WHERE file_id=%s RETURNING id", (file_id,))
            deleted = cur.rowcount
            stats[verdict] += 1
            stats['chunks_deleted'] += deleted
            log.info('재판정 제외 file_id=%s mid=%s verdict=%s ratio=%.2f chunks_deleted=%d',
                     file_id, mid, verdict, ratio, deleted)
        else:
            cur.execute(
                "UPDATE kosha_material_files SET lang_verdict=%s WHERE id=%s",
                ('keep', file_id)
            )
            stats['keep'] += 1

        if i % batch_size == 0 or i == total:
            conn.commit()
            msg = (f'[{i:,}/{total:,}] keep:{stats["keep"]} '
                   f'foreign:{stats["foreign"]} mixed:{stats["mixed"]} '
                   f'chunks_deleted:{stats["chunks_deleted"]}')
            print(f'  {msg}', flush=True)
            rlog.info(msg)

    conn.commit()
    cur.close(); conn.close()

    elapsed = (datetime.now() - start).seconds
    summary = (f'재판정 완료 소요:{elapsed//60}분{elapsed%60}초 '
               f'keep:{stats["keep"]} foreign:{stats["foreign"]} mixed:{stats["mixed"]} '
               f'청크삭제:{stats["chunks_deleted"]}개')
    print(f'\n=== 재판정 완료 ===', flush=True)
    print(f'  keep: {stats["keep"]:,}건 / foreign 제외: {stats["foreign"]:,}건 / mixed 제외: {stats["mixed"]:,}건', flush=True)
    print(f'  청크 삭제: {stats["chunks_deleted"]:,}개', flush=True)
    rlog.info('=== %s', summary)
    return stats


def run_resection(batch_size: int = 500):
    """저장된 모든 청크의 section_type을 새 detect_section으로 일괄 재분류.
    normalized_text 기반으로 재판정 — raw_text/hazard_type 등 다른 필드는 변경하지 않음."""
    start = datetime.now()
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, normalized_text FROM kosha_material_chunks ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()

    total = len(rows)
    rlog.info('=== section 재분류 시작 === 대상:%d개', total)
    print(f'[section 재분류] 대상: {total:,}개 청크')
    if total == 0:
        print('재분류 대상 없음')
        return

    stats: dict[str, int] = {}
    conn = get_conn()
    cur = conn.cursor()
    for i, row in enumerate(rows, 1):
        new_section = detect_section(row['normalized_text'] or '')
        cur.execute(
            "UPDATE kosha_material_chunks SET section_type=%s WHERE id=%s",
            (new_section, row['id'])
        )
        stats[new_section] = stats.get(new_section, 0) + 1

        if i % batch_size == 0 or i == total:
            conn.commit()
            msg = (f'[{i:,}/{total:,}] ' +
                   ' '.join(f'{k}:{v}' for k, v in sorted(stats.items())))
            print(f'  {msg}', flush=True)
            rlog.info(msg)

    conn.commit()
    cur.close(); conn.close()

    elapsed = (datetime.now() - start).seconds
    summary = (f'section 재분류 완료 소요:{elapsed//60}분{elapsed%60}초 결과:{stats}')
    print(f'\n=== section 재분류 완료 ===', flush=True)
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f'  {k}: {v:,}개', flush=True)
    rlog.info('=== %s', summary)
    return stats


def fix_chunk_text(text: str) -> str:
    """청크 raw_text의 3가지 파싱 오류 패턴 수정.
    1. (cid:숫자) 폰트 인코딩 오류 제거
    2. 음절 뒤섞임 글리치 → 원문 치환
    3. 한글 2중 반복 문자 정리 (교교육육 → 교육)
    """
    if not text:
        return text
    # 1. cid 패턴 제거
    text = re.sub(r'\(cid:\d+\)', ' ', text)
    # 2. 고정 글리치 패턴 치환 (건설업 공종별 위험성평가 뒤섞임)
    text = text.replace('건산설재업취 공약정계별층 위 사험고성예평방가', '건설업 공종별 위험성평가')
    text = text.replace('건산설재업취 공약정계별층 위사험성평방가', '건설업 공종별 위험성평가')
    # 3. 한글 인접 2중 반복 문자 제거 (교교육육 → 교육)
    text = re.sub(r'([가-힣])\1', r'\1', text)
    # 연속 공백 정리
    text = re.sub(r'  +', ' ', text)
    return text


def run_fix_chunks():
    """저장된 청크에서 파싱 오류 패턴을 수정하고 normalized_text·section_type 재생성."""
    start = datetime.now()

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # 오류 패턴이 있는 청크만 대상
    cur.execute("""
        SELECT id, raw_text, normalized_text
        FROM kosha_material_chunks
        WHERE raw_text LIKE '%(cid:%'
           OR raw_text LIKE '%건산설재업취%'
           OR raw_text LIKE '%공약정계별층%'
           OR raw_text LIKE '%교교육육%'
           OR raw_text LIKE '%미미디디%'
    """)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); conn.close()

    total = len(rows)
    rlog.info('=== 청크 오류 수정 시작 === 대상:%d개', total)
    print(f'[청크 오류 수정] 대상: {total:,}개')
    if total == 0:
        print('수정 대상 없음')
        return

    stats = {'fixed': 0, 'skipped': 0}
    conn = get_conn()
    cur = conn.cursor()
    for row in rows:
        fixed = fix_chunk_text(row['raw_text'])
        if fixed == row['raw_text']:
            stats['skipped'] += 1
            continue
        norm = normalize(fixed)
        section = detect_section(norm)
        cur.execute(
            """UPDATE kosha_material_chunks
               SET raw_text=%s, normalized_text=%s, section_type=%s
               WHERE id=%s""",
            (fixed, norm, section, row['id'])
        )
        stats['fixed'] += 1

    conn.commit()
    cur.close(); conn.close()

    elapsed = (datetime.now() - start).seconds
    print(f'\n=== 청크 오류 수정 완료 ===', flush=True)
    print(f'  수정: {stats["fixed"]:,}개 / 변화없음: {stats["skipped"]:,}개', flush=True)
    rlog.info('청크 오류 수정 완료 fixed:%d skipped:%d 소요:%ds',
              stats['fixed'], stats['skipped'], elapsed)
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
    ap.add_argument('--reclassify', action='store_true', help='기존 success 파일 언어 재판정')
    ap.add_argument('--resection', action='store_true', help='전체 청크 section_type 재분류')
    ap.add_argument('--fixchunks', action='store_true', help='청크 파싱 오류 패턴 수정')
    args = ap.parse_args()
    if args.pending:
        run_parse_pending()
    elif args.sample:
        run_sample(n=args.sample)
    elif args.reclassify:
        run_reclassify_language()
    elif args.resection:
        run_resection()
    elif args.fixchunks:
        run_fix_chunks()
    else:
        run_parse_pending()

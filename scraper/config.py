"""
환경별 설정 공유 모듈
.env 파일에서 로드 → 로컬/서버 동일 코드, 환경별 .env만 다름

필수 환경변수:
  COMMON_DATA_URL   postgresql://user:pass@host:port/dbname
  KOSHA_FILES_BASE  파일 저장 루트 경로 (로컬: 로컬경로, 서버: /nas/kosha-files)
  KOSHA_ID / KOSHA_PW  KOSHA 포털 계정
"""
import os
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

# ── DB ───────────────────────────────────────────────────────────────────────
COMMON_DATA_URL: str = os.environ['COMMON_DATA_URL']

def get_conn() -> psycopg2.extensions.connection:
    return psycopg2.connect(COMMON_DATA_URL)

def get_dict_conn() -> psycopg2.extensions.connection:
    return psycopg2.connect(COMMON_DATA_URL,
                            cursor_factory=psycopg2.extras.DictCursor)

# ── 파일 저장 경로 ────────────────────────────────────────────────────────────
_files_base_env = os.getenv('KOSHA_FILES_BASE', '')
FILES_BASE = Path(_files_base_env) if _files_base_env else Path(__file__).parent / 'kosha_files'
FILES_BASE.mkdir(parents=True, exist_ok=True)

# ── KOSHA 포털 ────────────────────────────────────────────────────────────────
KOSHA_ID: str = os.getenv('KOSHA_ID', '')
KOSHA_PW: str = os.getenv('KOSHA_PW', '')
KOSHA_BASE = 'https://portal.kosha.or.kr'

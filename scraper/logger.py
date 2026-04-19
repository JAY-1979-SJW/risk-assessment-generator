"""
KOSHA 스크래퍼 공통 로거
로그 파일 (logs/)
  scraper.log       : 운영 로그  INFO+   RotatingFile 5MB×5  (다운로드·파싱·분류 전체)
  scraper.error.log : 에러 로그  ERROR+  RotatingFile 2MB×3
  parser.log        : 파싱 이력  INFO+   RotatingFile 5MB×5  (파일별 텍스트 추출 결과)
  classifier.log    : 분류 이력  INFO+   RotatingFile 5MB×5  (청크별 공종 분류 결과)
  pipeline.log      : 라우터 로그 INFO+  RotatingFile 2MB×3  (파이프라인 단계별 흐름)
  run_history.log   : 실행 이력  INFO+   RotatingFile 2MB×3  (스크립트 시작/종료/통계)
  콘솔              : stdout     INFO+
민감정보(비밀번호·쿠키·토큰)는 마스킹 처리
"""
import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGS_DIR = Path(__file__).parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

_MASK_KEYS = re.compile(
    r'(password|passwd|pw|token|secret|cookie|session|authorization|api_key)',
    re.IGNORECASE
)

_FMT = '%(asctime)s [%(levelname)s] %(name)s | %(message)s'
_DATE = '%Y-%m-%d %H:%M:%S'


class _FlushFileHandler(RotatingFileHandler):
    """매 레코드 즉시 flush — nohup/리다이렉트 환경에서도 실시간 기록"""
    def emit(self, record):
        super().emit(record)
        self.flush()


def _make_handler(path: Path, level: int, max_bytes=5*1024*1024, backup=5):
    h = _FlushFileHandler(path, maxBytes=max_bytes, backupCount=backup, encoding='utf-8')
    h.setLevel(level)
    h.setFormatter(logging.Formatter(_FMT, _DATE))
    return h


def _console_handler():
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(logging.INFO)
    h.setFormatter(logging.Formatter(_FMT, _DATE))
    return h


def get_logger(name: str) -> logging.Logger:
    """모든 모듈에서 get_logger(__name__)으로 사용"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_make_handler(LOGS_DIR / 'scraper.log', logging.INFO))
    logger.addHandler(_make_handler(LOGS_DIR / 'scraper.error.log', logging.ERROR, 2*1024*1024, 3))
    logger.addHandler(_console_handler())
    logger.propagate = False
    return logger


def get_run_logger(name: str) -> logging.Logger:
    """실행 이력 전용 로거 (스크립트 시작/종료/통계)"""
    logger = logging.getLogger(f'run.{name}')
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logger.addHandler(_make_handler(LOGS_DIR / 'run_history.log', logging.INFO, 2*1024*1024, 3))
    logger.addHandler(_console_handler())
    logger.propagate = False
    return logger


def get_parser_logger() -> logging.Logger:
    """파싱 이력 로거 — 파일별 텍스트 추출 결과"""
    logger = logging.getLogger('kosha.parser')
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_make_handler(LOGS_DIR / 'parser.log', logging.INFO))
    logger.addHandler(_make_handler(LOGS_DIR / 'scraper.error.log', logging.ERROR, 2*1024*1024, 3))
    logger.addHandler(_console_handler())
    logger.propagate = False
    return logger


def get_classifier_logger() -> logging.Logger:
    """분류 이력 로거 — 청크별 공종 분류 결과"""
    logger = logging.getLogger('kosha.classifier')
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_make_handler(LOGS_DIR / 'classifier.log', logging.INFO))
    logger.addHandler(_make_handler(LOGS_DIR / 'scraper.error.log', logging.ERROR, 2*1024*1024, 3))
    logger.propagate = False
    return logger


def get_pipeline_logger() -> logging.Logger:
    """파이프라인 라우터 로거 — 단계별 흐름 추적"""
    logger = logging.getLogger('kosha.pipeline')
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logger.addHandler(_make_handler(LOGS_DIR / 'pipeline.log', logging.INFO, 2*1024*1024, 3))
    logger.addHandler(_make_handler(LOGS_DIR / 'scraper.error.log', logging.ERROR, 2*1024*1024, 3))
    logger.addHandler(_console_handler())
    logger.propagate = False
    return logger


def mask(text: str) -> str:
    """로그 문자열에서 민감정보 마스킹"""
    if not isinstance(text, str):
        text = str(text)

    def _replace(m):
        key = m.group(1)
        rest = m.group(2)
        # 값 부분만 마스킹 (앞 2자 + *** + 뒤 2자)
        eq_val = re.sub(r"(['\"]?)([^'\"\s,}]{4,})(['\"]?)",
                        lambda v: v.group(1) + v.group(2)[:2] + '***' + v.group(2)[-2:] + v.group(3),
                        rest, count=1)
        return key + eq_val

    return re.sub(
        r'(' + _MASK_KEYS.pattern + r')([\s:=]+[^\s,}\n]{2,})',
        _replace, text, flags=re.IGNORECASE
    )

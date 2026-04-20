"""
KOSHA chunk loader wrapper for the connector layer.
Wraps engine/rag_risk_engine/loader.py with explicit options and logging.
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def load_kosha_chunks(
    limit: int = 5000,
    use_db: bool = True,
    json_path: Optional[str] = None,
    exclude_noise: bool = True,
) -> tuple[List[Dict[str, Any]], int]:
    """
    Load KOSHA chunks and return (chunks, count).

    Priority:
      1. json_path if provided
      2. DB (KOSHA_DB_URL or COMMON_DATA_URL or tunnel defaults)
      3. Local cache (chunks_cache.json)

    Args:
        limit:         Max rows from DB (ignored for JSON)
        use_db:        Force DB load (default True)
        json_path:     Explicit JSON file path
        exclude_noise: Skip rows with no normalized_text AND no raw_text

    Returns:
        (chunks, count) where count is total loaded before noise filter
    """
    from engine.rag_risk_engine.loader import load_from_json, load_from_db

    # 1) 명시적 JSON 경로
    if json_path:
        chunks = load_from_json(json_path)
        raw_count = len(chunks)
        if exclude_noise:
            chunks = _filter_noise(chunks)
        logger.info('KOSHA 로더: JSON 파일=%s 로드=%d 필터 후=%d', json_path, raw_count, len(chunks))
        return chunks, raw_count

    # 2) DB 로드 (환경변수에서 연결 정보 가져옴)
    if use_db:
        try:
            _apply_kosha_db_env()
            chunks = load_from_db(limit=limit)
            raw_count = len(chunks)
            if exclude_noise:
                chunks = _filter_noise(chunks)
            logger.info('KOSHA 로더: DB 로드=%d 필터 후=%d', raw_count, len(chunks))
            return chunks, raw_count
        except Exception as exc:
            logger.warning('KOSHA DB 로드 실패, 캐시 파일 시도: %s', exc)

    # 3) 로컬 캐시
    cache = os.path.join(os.path.dirname(__file__), '..', 'rag_risk_engine', 'data', 'chunks_cache.json')
    cache = os.path.abspath(cache)
    if os.path.isfile(cache):
        chunks = load_from_json(cache)
        raw_count = len(chunks)
        if exclude_noise:
            chunks = _filter_noise(chunks)
        logger.info('KOSHA 로더: 캐시=%s 로드=%d 필터 후=%d', cache, raw_count, len(chunks))
        return chunks, raw_count

    raise RuntimeError(
        'KOSHA 청크를 로드할 수 없습니다. '
        'COMMON_DATA_URL 또는 KOSHA_DB_URL 환경변수를 확인하거나, '
        '--chunks 옵션으로 JSON 파일을 지정하세요.'
    )


def _apply_kosha_db_env():
    """KOSHA DB 접속 환경변수를 loader 기대 형식으로 변환."""
    url = os.getenv('KOSHA_DB_URL') or os.getenv('COMMON_DATA_URL')
    if url:
        # postgresql://user:pass@host:port/dbname 파싱
        from urllib.parse import urlparse
        parsed = urlparse(url)
        os.environ.setdefault('KOSHA_DB_HOST', parsed.hostname or '127.0.0.1')
        os.environ.setdefault('KOSHA_DB_PORT', str(parsed.port or 5435))
        os.environ.setdefault('KOSHA_DB_NAME', parsed.path.lstrip('/') or 'common_data')
        os.environ.setdefault('KOSHA_DB_USER', parsed.username or 'common_admin')
        os.environ.setdefault('KOSHA_DB_PASS', parsed.password or '')


def _filter_noise(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """텍스트가 전혀 없는 빈 행 제거."""
    return [
        c for c in chunks
        if (c.get('normalized_text') or '').strip()
        or (c.get('raw_text') or '').strip()
    ]

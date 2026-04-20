#!/usr/bin/env python3
"""
KRAS Assessment Engine CLI.

Usage:
    python engine/run_assessment_engine.py --assessment-id 1
    python engine/run_assessment_engine.py --assessment-id 1 --pretty
    python engine/run_assessment_engine.py --assessment-id 1 --no-save
    python engine/run_assessment_engine.py --assessment-id 1 --limit-chunks 2000

Requires:
    KRAS_DB_URL or DATABASE_URL   → KRAS PostgreSQL (project_assessments)
    COMMON_DATA_URL or KOSHA_DB_URL → KOSHA PostgreSQL (chunks)
"""

import argparse
import json
import logging
import os
import sys

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)


def _load_env():
    """Load .env from scraper/.env or project root .env if present."""
    for candidate in [
        os.path.join(_root, 'scraper', '.env'),
        os.path.join(_root, '.env'),
    ]:
        if os.path.isfile(candidate):
            with open(candidate) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, val = line.partition('=')
                        os.environ.setdefault(key.strip(), val.strip())
            break


def main():
    _load_env()

    parser = argparse.ArgumentParser(
        description='KRAS Assessment → RAG Engine 단건 실행'
    )
    parser.add_argument('--assessment-id', type=int, required=True,
                        help='project_assessments.id')
    parser.add_argument('--pretty', action='store_true',
                        help='출력 JSON을 들여쓰기 포맷으로 표시')
    parser.add_argument('--no-save', action='store_true',
                        help='결과를 DB에 저장하지 않음')
    parser.add_argument('--limit-chunks', type=int, default=5000,
                        help='KOSHA 청크 최대 로드 수 (기본 5000)')
    parser.add_argument('--chunks-file', type=str, default=None,
                        help='KOSHA JSON 파일 경로 (DB 대신 파일 사용)')
    parser.add_argument('--verbose', action='store_true',
                        help='DEBUG 로그 출력')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format='%(levelname)s %(name)s: %(message)s',
    )

    from engine.kras_connector.kosha_loader import load_kosha_chunks
    from engine.kras_connector.service import run_for_assessment

    # KOSHA 청크 사전 로드 (한 번만)
    try:
        chunks, chunk_count = load_kosha_chunks(
            limit=args.limit_chunks,
            json_path=args.chunks_file,
        )
    except Exception as exc:
        print(json.dumps({'error': f'KOSHA 로드 실패: {exc}', 'status': 'engine_error'}),
              file=sys.stderr)
        sys.exit(1)

    print(f'[KOSHA] 청크 로드 완료: 로드={chunk_count} / 유효={len(chunks)}', file=sys.stderr)

    # 엔진 실행
    result = run_for_assessment(
        assessment_id=args.assessment_id,
        chunks=chunks,
        chunk_count_loaded=chunk_count,
        save=not args.no_save,
    )

    # stdout: 요약
    summary = {
        'assessment_id': result['assessment_id'],
        'status':        result['status'],
        'confidence':    result.get('confidence'),
        'hazard_count':  result.get('hazard_count'),
        'action_count':  result.get('action_count'),
        'source_chunk_ids_sample': (result.get('source_chunk_ids') or [])[:5],
        'result_id':     result.get('result_id'),
        'error':         result.get('error'),
    }

    indent = 2 if args.pretty else None
    print(json.dumps(summary, ensure_ascii=False, indent=indent))

    # 실패 시 전체 출력 및 비정상 종료
    if result['status'] != 'success':
        print(json.dumps({'full_error': result.get('error')},
                         ensure_ascii=False), file=sys.stderr)
        sys.exit(2)

    # pretty 모드: 전체 output_json도 출력
    if args.pretty and result.get('output_json'):
        print('\n--- Engine Output ---')
        print(json.dumps(result['output_json'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

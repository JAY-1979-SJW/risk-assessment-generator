#!/usr/bin/env python3
"""
CLI entrypoint for RAG Risk Engine v1.

Usage:
  # From JSON file:
  python -m engine.rag_risk_engine.cli --input samples/sample_fall_scaffold.json \
         --chunks /path/to/chunks.json

  # Inline JSON:
  python -m engine.rag_risk_engine.cli \
    --json '{"process":"건축","sub_work":"비계설치","risk_situation":"작업발판 위에서 추락 위험"}' \
    --chunks /path/to/chunks.json

  # With DB:
  python -m engine.rag_risk_engine.cli --input samples/sample_fall_scaffold.json --use-db
"""

import argparse
import json
import os
import sys

# Allow running as `python -m engine.rag_risk_engine.cli` from project root
_proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)

from engine.rag_risk_engine.engine import run_engine
from engine.rag_risk_engine.loader import load_chunks
from engine.rag_risk_engine.schema import validate_input


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='rag-risk-engine',
        description='KOSHA 지식 베이스 기반 위험성 평가 RAG 엔진 v1',
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument(
        '--input', '-i',
        metavar='FILE',
        help='입력 JSON 파일 경로',
    )
    src.add_argument(
        '--json', '-j',
        metavar='JSON',
        dest='inline_json',
        help='인라인 JSON 문자열',
    )

    chunks_src = p.add_mutually_exclusive_group()
    chunks_src.add_argument(
        '--chunks', '-c',
        metavar='FILE',
        help='청크 JSON 파일 경로 (기본: engine/rag_risk_engine/data/chunks_cache.json)',
    )
    chunks_src.add_argument(
        '--use-db',
        action='store_true',
        help='PostgreSQL DB에서 청크 로드 (SSH 터널 필요)',
    )

    p.add_argument(
        '--pretty',
        action='store_true',
        help='들여쓰기 적용 JSON 출력',
    )
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    # Load input
    if args.input:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                raw_input = json.load(f)
        except FileNotFoundError:
            _exit_error(f'입력 파일을 찾을 수 없습니다: {args.input}')
        except json.JSONDecodeError as e:
            _exit_error(f'입력 파일 JSON 파싱 오류: {e}')
    else:
        try:
            raw_input = json.loads(args.inline_json)
        except json.JSONDecodeError as e:
            _exit_error(f'인라인 JSON 파싱 오류: {e}')

    # Validate input early to give clear error messages
    try:
        validate_input(raw_input)
    except ValueError as e:
        _exit_error(f'입력 검증 오류: {e}')

    # Load chunks
    try:
        chunks = load_chunks(
            source=args.chunks,
            use_db=args.use_db,
        )
    except (FileNotFoundError, RuntimeError) as e:
        _exit_error(f'청크 로드 오류: {e}')

    if not chunks:
        _exit_error('청크 데이터가 비어 있습니다.')

    # Run engine
    try:
        result = run_engine(raw_input, chunks)
    except ValueError as e:
        _exit_error(f'엔진 실행 오류: {e}')

    # Output
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))


def _exit_error(msg: str):
    print(json.dumps({'error': msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
    main()

"""
analyze_generic_work_types.py — read-only

Lists distribution of work_type values in the KOSHA chunk corpus.
Shows which values are "generic" (in GENERIC_WORK_TYPES) vs domain-specific,
and calculates what percentage of chunks carry a retrieval-bonus-eligible work_type.

Usage:
    python scripts/analyze_generic_work_types.py [--chunks-file PATH] [--top N]
"""

import argparse
import json
import sys
import os
from pathlib import Path
from collections import Counter

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.rag_risk_engine.retrieval import GENERIC_WORK_TYPES


def load_chunks(chunks_file: str | None) -> list[dict]:
    """Load chunks from JSON file or KOSHA DB."""
    if chunks_file:
        with open(chunks_file, encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get('chunks', [])

    # Try KOSHA DB via connector loader
    try:
        from engine.kras_connector.kosha_loader import load_kosha_chunks
        chunks, count = load_kosha_chunks()
        print(f"[DB] {count}건 로드 완료")
        return chunks
    except Exception as e:
        print(f"[ERROR] KOSHA DB 로드 실패: {e}", file=sys.stderr)
        sys.exit(1)


def analyze(chunks: list[dict], top_n: int) -> None:
    total = len(chunks)
    counter: Counter = Counter()
    no_tag = 0

    for c in chunks:
        wt = (c.get('work_type') or '').strip()
        if wt:
            counter[wt] += 1
        else:
            no_tag += 1

    print(f"\n{'='*60}")
    print(f"전체 청크: {total:,}건")
    print(f"work_type 없음: {no_tag:,}건 ({no_tag/total*100:.1f}%)")
    print(f"work_type 있음: {total-no_tag:,}건 ({(total-no_tag)/total*100:.1f}%)")

    generic_count = sum(v for k, v in counter.items() if k in GENERIC_WORK_TYPES)
    specific_count = sum(v for k, v in counter.items() if k not in GENERIC_WORK_TYPES)

    print(f"\n--- GENERIC_WORK_TYPES (보너스 제외) ---")
    print(f"해당 청크: {generic_count:,}건 ({generic_count/total*100:.1f}%)")
    for wt in sorted(GENERIC_WORK_TYPES):
        cnt = counter.get(wt, 0)
        if cnt:
            print(f"  '{wt}': {cnt:,}건")

    print(f"\n--- 도메인 특이적 work_type (보너스 적용) ---")
    print(f"해당 청크: {specific_count:,}건 ({specific_count/total*100:.1f}%)")

    print(f"\n--- 상위 {top_n}개 work_type ---")
    for rank, (wt, cnt) in enumerate(counter.most_common(top_n), 1):
        tag = ' [GENERIC]' if wt in GENERIC_WORK_TYPES else ''
        print(f"  {rank:3}. '{wt}': {cnt:,}건{tag}")

    print(f"\n--- 분석 요약 ---")
    bonus_eligible = specific_count
    print(f"검색 보너스 적용 가능 청크: {bonus_eligible:,}건 ({bonus_eligible/total*100:.1f}%)")
    print(f"검색 보너스 제외 청크 (generic): {generic_count:,}건 ({generic_count/total*100:.1f}%)")
    print(f"태그 없음 (패널티 적용): {no_tag:,}건 ({no_tag/total*100:.1f}%)")
    print('='*60)


def main():
    parser = argparse.ArgumentParser(description='KOSHA work_type 분포 분석')
    parser.add_argument('--chunks-file', help='로컬 JSON 청크 파일 경로')
    parser.add_argument('--top', type=int, default=30, help='상위 N개 출력 (기본: 30)')
    args = parser.parse_args()

    chunks = load_chunks(args.chunks_file)
    analyze(chunks, args.top)


if __name__ == '__main__':
    main()

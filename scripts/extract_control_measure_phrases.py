"""
extract_control_measure_phrases.py — read-only

Analyzes control_measure field quality in the KOSHA chunk corpus.
Reports:
  - phrase length distribution
  - generic vs specific phrase ratio
  - top N most common phrases
  - phrases extractable by sliding-window extractor

Usage:
    python scripts/extract_control_measure_phrases.py [--chunks-file PATH] [--top N] [--sample N]
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.rag_risk_engine.assembler import (
    _split_field,
    _extract_action_phrases,
    _is_generic_action,
    _GENERIC_ACTIONS,
    _MAX_PHRASE_LEN,
)


def load_chunks(chunks_file: str | None) -> list[dict]:
    if chunks_file:
        with open(chunks_file, encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get('chunks', [])

    try:
        from engine.kras_connector.kosha_loader import load_kosha_chunks
        chunks, count = load_kosha_chunks()
        print(f"[DB] {count}건 로드 완료")
        return chunks
    except Exception as e:
        print(f"[ERROR] KOSHA DB 로드 실패: {e}", file=sys.stderr)
        sys.exit(1)


def analyze(chunks: list[dict], top_n: int, sample_n: int) -> None:
    total = len(chunks)
    no_cm = 0
    generic_count = 0
    specific_count = 0
    phrase_counter: Counter = Counter()
    len_buckets: Counter = Counter()
    extracted_phrases: Counter = Counter()

    for c in chunks:
        cm = c.get('control_measure') or ''
        if not cm.strip():
            no_cm += 1
            continue

        parts = _split_field(cm)
        for p in parts:
            if _is_generic_action(p):
                generic_count += 1
            else:
                specific_count += 1
                phrase_counter[p] += 1
                # Length bucketing
                ln = len(p)
                if ln <= 5:
                    len_buckets['1-5자'] += 1
                elif ln <= 10:
                    len_buckets['6-10자'] += 1
                elif ln <= 20:
                    len_buckets['11-20자'] += 1
                elif ln <= _MAX_PHRASE_LEN:
                    len_buckets[f'21-{_MAX_PHRASE_LEN}자'] += 1
                else:
                    len_buckets[f'{_MAX_PHRASE_LEN+1}자+'] += 1

        # Sliding window extraction from normalized_text
        text = c.get('normalized_text') or c.get('raw_text') or ''
        for phrase in _extract_action_phrases(text):
            if not _is_generic_action(phrase):
                extracted_phrases[phrase] += 1

    print(f"\n{'='*60}")
    print(f"전체 청크: {total:,}건")
    print(f"control_measure 없음: {no_cm:,}건 ({no_cm/total*100:.1f}%)")
    print(f"control_measure 있음: {total-no_cm:,}건 ({(total-no_cm)/total*100:.1f}%)")

    total_parts = generic_count + specific_count
    if total_parts:
        print(f"\n--- control_measure 구문 품질 ---")
        print(f"전체 구문 수: {total_parts:,}개")
        print(f"  generic (필터 대상): {generic_count:,}개 ({generic_count/total_parts*100:.1f}%)")
        print(f"  specific (활용 가능): {specific_count:,}개 ({specific_count/total_parts*100:.1f}%)")

    print(f"\n--- generic 판정 기준 ({len(_GENERIC_ACTIONS)}개 단어) ---")
    print(f"  {', '.join(sorted(_GENERIC_ACTIONS))}")

    if len_buckets:
        print(f"\n--- specific 구문 길이 분포 ---")
        for bucket in ['1-5자', '6-10자', '11-20자', f'21-{_MAX_PHRASE_LEN}자', f'{_MAX_PHRASE_LEN+1}자+']:
            cnt = len_buckets.get(bucket, 0)
            bar = '█' * min(40, cnt // max(1, specific_count // 40))
            print(f"  {bucket:>10}: {cnt:6,}개 {bar}")

    print(f"\n--- 상위 {top_n}개 specific control_measure 구문 ---")
    for rank, (phrase, cnt) in enumerate(phrase_counter.most_common(top_n), 1):
        print(f"  {rank:3}. [{cnt:4}x] {phrase}")

    print(f"\n--- 슬라이딩 윈도우 추출 구문 상위 {top_n}개 ---")
    print(f"(정규화 텍스트에서 동사 기반 추출, MAX_LEN={_MAX_PHRASE_LEN}자)")
    for rank, (phrase, cnt) in enumerate(extracted_phrases.most_common(top_n), 1):
        print(f"  {rank:3}. [{cnt:4}x] {phrase}")

    if sample_n and extracted_phrases:
        print(f"\n--- 추출 구문 샘플 (다양성 확인) ---")
        samples = list(extracted_phrases.keys())[:sample_n]
        for p in samples:
            mark = '✓' if len(p) <= _MAX_PHRASE_LEN else '✗ LONG'
            print(f"  {mark} [{len(p):2}자] {p}")

    print('='*60)


def main():
    parser = argparse.ArgumentParser(description='KOSHA control_measure 구문 분석')
    parser.add_argument('--chunks-file', help='로컬 JSON 청크 파일 경로')
    parser.add_argument('--top', type=int, default=20, help='상위 N개 출력 (기본: 20)')
    parser.add_argument('--sample', type=int, default=30, help='샘플 구문 출력 수 (기본: 30)')
    args = parser.parse_args()

    chunks = load_chunks(args.chunks_file)
    analyze(chunks, args.top, args.sample)


if __name__ == '__main__':
    main()

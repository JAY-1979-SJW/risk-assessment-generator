"""
analyze_generic_hazards.py — read-only

Lists distribution of hazard_type values in the KOSHA chunk corpus.
Identifies "generic" vs specific hazard tags using GENERIC_HAZARD_TAGS from
hazard_classifier.py, and shows how many chunks would be filtered.

Usage:
    python scripts/analyze_generic_hazards.py [--chunks-file PATH] [--top N]
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.rag_risk_engine.hazard_classifier import GENERIC_HAZARD_TAGS, classify_hazard_from_text


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


def analyze(chunks: list[dict], top_n: int) -> None:
    total = len(chunks)
    tag_counter: Counter = Counter()
    classifier_counter: Counter = Counter()
    no_tag = 0

    for c in chunks:
        ht = (c.get('hazard_type') or '').strip()
        if ht:
            tag_counter[ht] += 1
        else:
            no_tag += 1

        text = (c.get('normalized_text') or c.get('raw_text') or '')
        for label in classify_hazard_from_text(text):
            classifier_counter[label] += 1

    print(f"\n{'='*60}")
    print(f"전체 청크: {total:,}건")
    print(f"hazard_type 없음: {no_tag:,}건 ({no_tag/total*100:.1f}%)")
    print(f"hazard_type 있음: {total-no_tag:,}건 ({(total-no_tag)/total*100:.1f}%)")

    generic_count = sum(v for k, v in tag_counter.items() if k in GENERIC_HAZARD_TAGS)
    specific_count = sum(v for k, v in tag_counter.items() if k not in GENERIC_HAZARD_TAGS)

    print(f"\n--- GENERIC_HAZARD_TAGS (빈도 집계 제외) ---")
    print(f"해당 청크: {generic_count:,}건 ({generic_count/total*100:.1f}%)")
    for ht in sorted(GENERIC_HAZARD_TAGS):
        cnt = tag_counter.get(ht, 0)
        if cnt:
            print(f"  '{ht}': {cnt:,}건")

    print(f"\n--- 도메인 특이적 hazard_type (빈도 집계 적용) ---")
    print(f"해당 청크: {specific_count:,}건 ({specific_count/total*100:.1f}%)")

    print(f"\n--- 상위 {top_n}개 hazard_type (태그 기반) ---")
    for rank, (ht, cnt) in enumerate(tag_counter.most_common(top_n), 1):
        tag = ' [GENERIC]' if ht in GENERIC_HAZARD_TAGS else ''
        print(f"  {rank:3}. '{ht}': {cnt:,}건{tag}")

    print(f"\n--- 텍스트 분류기 감지 결과 (상위 {top_n}개) ---")
    for rank, (label, cnt) in enumerate(classifier_counter.most_common(top_n), 1):
        print(f"  {rank:3}. '{label}': {cnt}개 청크에서 감지")

    print(f"\n--- 위험 유형별 커버리지 (태그 vs 분류기) ---")
    all_labels = set(tag_counter.keys()) | set(classifier_counter.keys())
    for label in sorted(all_labels - GENERIC_HAZARD_TAGS):
        tag_cnt = tag_counter.get(label, 0)
        cls_cnt = classifier_counter.get(label, 0)
        if tag_cnt or cls_cnt:
            print(f"  '{label}': 태그={tag_cnt:,}건, 분류기={cls_cnt:,}건")
    print('='*60)


def main():
    parser = argparse.ArgumentParser(description='KOSHA hazard_type 분포 분석')
    parser.add_argument('--chunks-file', help='로컬 JSON 청크 파일 경로')
    parser.add_argument('--top', type=int, default=20, help='상위 N개 출력 (기본: 20)')
    args = parser.parse_args()

    chunks = load_chunks(args.chunks_file)
    analyze(chunks, args.top)


if __name__ == '__main__':
    main()

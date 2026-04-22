"""
통합 간단 검색기

사용법:
  python -m scripts.search.simple_search "비계 작업 추락"
  python -m scripts.search.simple_search "밀폐공간 질식" --top 10
  python -m scripts.search.simple_search "용접 화재" --source kosha,expc

입력: data/index/unified_index.jsonl
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
INDEX_PATH = ROOT / "data" / "index" / "unified_index.jsonl"

# 검색어 → hazard/work_type 코드 힌트 매핑 (빠른 필터용)
_HAZARD_HINT = {
    "추락": "추락", "떨어짐": "추락", "낙하": "추락",
    "끼임": "끼임", "협착": "협착", "압착": "협착",
    "충돌": "충돌", "부딪힘": "충돌",
    "붕괴": "붕괴", "무너짐": "붕괴",
    "감전": "감전", "전기": "감전",
    "화재": "화재폭발", "폭발": "화재폭발", "인화": "화재폭발",
    "질식": "질식", "산소결핍": "질식",
    "중량물": "중량물",
    "화학물질": "화학물질", "유해물질": "화학물질",
    "전도": "전도", "미끄러짐": "전도",
    "비래": "비래낙하", "낙하물": "비래낙하",
    "소음": "소음진동", "진동": "소음진동",
    "고온": "온도", "폭염": "온도", "저온": "온도",
}

_WORK_HINT = {
    "비계": "비계_조립", "조립": "비계_조립",
    "고소": "고소작업", "고소작업대": "고소작업",
    "굴착": "굴착", "터파기": "굴착",
    "철골": "철골",
    "용접": "용접",
    "전기공사": "전기", "배선": "전기",
    "도장": "도장", "페인트": "도장",
    "배관": "배관",
    "양중": "양중", "크레인작업": "양중", "리프팅": "양중",
    "밀폐공간": "밀폐공간", "맨홀": "밀폐공간",
    "콘크리트": "콘크리트", "타설": "콘크리트",
    "지붕": "지붕",
    "해체": "해체", "철거": "해체",
    "운반": "운반", "하역": "운반",
    "정비": "기계정비", "수리": "기계정비",
    "방수": "방수",
    "절단": "절단", "그라인더": "절단",
    "발파": "발파",
    "화학": "화학취급",
}


def _tokenize(query: str) -> list[str]:
    return [t for t in re.split(r"[\s,]+", query.strip()) if t]


def _score(record: dict, tokens: list[str], hint_hazards: set[str], hint_works: set[str]) -> float:
    weight = record.get("score_weight", 1.0)
    title = record.get("title", "")
    body  = record.get("body_text", "")
    text  = title + " " + body
    r_hazards   = set(record.get("hazards", []))
    r_works     = set(record.get("work_types", []))

    score = 0.0

    # 1. 키워드 텍스트 매칭 (제목 2배, 본문 1배)
    for tok in tokens:
        if tok in title:
            score += 2.0
        elif tok in body:
            score += 1.0

    # 2. hazard 코드 일치 (힌트 기반)
    for haz in hint_hazards & r_hazards:
        score += 3.0

    # 3. work_type 코드 일치 (힌트 기반)
    for wt in hint_works & r_works:
        score += 3.0

    # 4. source weight 적용
    score *= weight

    return round(score, 3)


def search(
    query: str,
    top: int = 5,
    sources: list[str] | None = None,
    diverse: bool = True,
) -> list[dict]:
    """
    diverse=True(기본): 소스별 상위 결과를 라운드로빈으로 섞어 반환.
      - 각 소스 최소 1건 보장, 나머지는 점수 순 채움.
    diverse=False: 순수 top-N (소스 편중 발생 가능).
    """
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"인덱스 없음: {INDEX_PATH}\n→ python -m scripts.search.build_index 먼저 실행")

    tokens = _tokenize(query)

    hint_hazards: set[str] = set()
    hint_works:   set[str] = set()
    for tok in tokens:
        if tok in _HAZARD_HINT:
            hint_hazards.add(_HAZARD_HINT[tok])
        if tok in _WORK_HINT:
            hint_works.add(_WORK_HINT[tok])

    buckets: dict[str, list[tuple[float, dict]]] = {"kosha": [], "law": [], "expc": []}

    with INDEX_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            src = rec.get("source", "")

            if sources and src not in sources:
                continue

            s = _score(rec, tokens, hint_hazards, hint_works)
            if s > 0 and src in buckets:
                buckets[src].append((s, rec))

    for src in buckets:
        buckets[src].sort(key=lambda x: x[0], reverse=True)

    if not diverse or sources:
        flat = [(s, r) for src in buckets for s, r in buckets[src]]
        flat.sort(key=lambda x: x[0], reverse=True)
        return [{"score": s, **r} for s, r in flat[:top]]

    # 라운드로빈: 소스별 최소 1건 우선 확보 후 점수순 채움
    order = ["kosha", "expc", "law"]
    taken: dict[str, int] = {s: 0 for s in order}
    result: list[tuple[float, dict]] = []

    # 1라운드: 각 소스 top-1 확보
    for src in order:
        if buckets[src]:
            result.append(buckets[src][0])
            taken[src] = 1

    # 나머지: 남은 자리를 점수 순 채움 (소스 무관)
    remaining = []
    for src in order:
        for item in buckets[src][taken[src]:]:
            remaining.append(item)
    remaining.sort(key=lambda x: x[0], reverse=True)
    result.extend(remaining[: top - len(result)])

    result.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, **r} for s, r in result[:top]]


def _print_results(query: str, hits: list[dict]) -> None:
    print(f"\n{'='*60}")
    print(f"검색어: {query!r}  |  결과: {len(hits)}건")
    print('='*60)
    for i, h in enumerate(hits, 1):
        print(f"\n[{i}] [{h['source'].upper():5s}] score={h['score']:.2f}  weight={h['score_weight']}")
        print(f"    제목: {h['title'][:70]}")
        print(f"    hazards   : {h['hazards']}")
        print(f"    work_types: {h['work_types']}")
        snippet = h.get("body_text", "")[:120].replace("\n", " ")
        if snippet:
            print(f"    본문요약  : {snippet}…")
    if not hits:
        print("  결과 없음")
    print()


def run_demo() -> None:
    queries = [
        "비계 작업 추락",
        "밀폐공간 질식",
        "용접 화재",
    ]
    for q in queries:
        hits = search(q, top=5, diverse=True)
        _print_results(q, hits)

    # 품질 평가
    print("="*60)
    print("결과 품질 평가")
    print("="*60)
    all_pass = True
    for q in queries:
        hits = search(q, top=5, diverse=True)
        sources_hit = {h["source"] for h in hits}
        has_mixed   = len(sources_hit) >= 2
        has_result  = len(hits) >= 3
        ok = has_result and has_mixed
        if not ok:
            all_pass = False
        status = "PASS" if ok else "WARN"
        print(f"  {q!r:20s}  결과:{len(hits)}건  소스:{sorted(sources_hit)}  [{status}]")
    print(f"\n  전체: {'PASS' if all_pass else 'WARN'}")
    print()


def main() -> None:
    if len(sys.argv) == 1:
        run_demo()
        return

    parser = argparse.ArgumentParser(description="통합 안전보건 검색")
    parser.add_argument("query", nargs="?", default="", help="검색어")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--source", type=str, default="", help="kosha,expc,law")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo or not args.query:
        run_demo()
        return

    sources = [s.strip() for s in args.source.split(",") if s.strip()] or None
    hits = search(args.query, top=args.top, sources=sources)
    _print_results(args.query, hits)


if __name__ == "__main__":
    main()

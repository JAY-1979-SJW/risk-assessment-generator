"""
위험성 평가 요약 생성기 (rule 기반)

사용법:
  python -m scripts.search.risk_summary "비계 작업"
  python -m scripts.search.risk_summary --demo
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

# ── 위험요인별 조치사항 규칙 사전 ──────────────────────────────────────────
_CONTROLS: dict[str, list[str]] = {
    "추락":     ["안전난간 설치", "안전대(하네스) 착용", "작업발판 고정", "개구부 덮개 설치"],
    "끼임":     ["방호덮개 설치", "기계 정지 후 작업", "인터록 장치 확인", "손 끼임 방지장갑"],
    "충돌":     ["유도원 배치", "후진 경보장치", "접근금지 구역 설정", "시야 확보"],
    "붕괴":     ["지반 조사·보강", "흙막이 설치", "동바리 조립 상태 점검", "토사 과적 금지"],
    "감전":     ["접지 확인", "절연 장갑·장화 착용", "누전차단기 설치", "활선 작업 금지"],
    "화재폭발": ["소화기 배치", "화기 관리대장 운영", "용접불티 비산방지포 설치", "인화물 제거"],
    "질식":     ["작업 전 산소농도 측정", "강제 환기 실시", "공기호흡기 비치", "감시인 배치"],
    "중량물":   ["보조기구(호이스트) 사용", "팀 리프팅 2인 이상", "허리 보호대 착용", "무게 표시"],
    "화학물질": ["MSDS 게시·숙지", "보호구(방독마스크·장갑) 착용", "국소배기 설치", "물질 밀봉 보관"],
    "협착":     ["방호울 설치", "안전블록 체결", "작업 중 기계 정지", "협착점 방호 확인"],
    "전도":     ["미끄럼 방지 매트 설치", "통로 정리정돈", "안전화 착용", "조명 확보"],
    "비래낙하": ["낙하물 방지망 설치", "안전모 착용", "자재 결속·적재 점검", "출입금지 구역 설정"],
    "소음진동": ["귀마개·귀덮개 착용", "방진 장갑 착용", "소음 저감 설비", "노출 시간 제한"],
    "온도":     ["폭염·한랭 작업 휴식 부여", "냉·온수 제공", "적정 복장 착용", "건강 모니터링"],
}

# ── hazard → 검색 보강 쿼리 ────────────────────────────────────────────────
_HAZARD_EXPAND: dict[str, str] = {
    "추락":     "추락",
    "질식":     "질식 밀폐공간",
    "화재폭발": "화재 폭발",
    "감전":     "감전",
    "끼임":     "끼임 협착",
    "붕괴":     "붕괴",
    "충돌":     "충돌",
    "중량물":   "중량물",
    "화학물질": "화학물질",
    "협착":     "협착",
    "전도":     "전도 미끄러짐",
    "비래낙하": "낙하물",
    "소음진동": "소음",
    "온도":     "폭염 고온",
}


def generate_summary(query: str, top: int = 5) -> dict:
    from scripts.search.simple_search import search  # 기존 검색 재사용

    hits = search(query, top=top, diverse=True)

    # ── 1. hazard 빈도 집계 ─────────────────────────────────────────────────
    hazard_counter: Counter = Counter()
    for h in hits:
        for haz in h.get("hazards", []):
            hazard_counter[haz] += 1

    top_hazards = [haz for haz, _ in hazard_counter.most_common(3)]
    main_hazard = top_hazards[0] if top_hazards else ""

    # ── 2. work_type 빈도 집계 ──────────────────────────────────────────────
    wt_counter: Counter = Counter()
    for h in hits:
        for wt in h.get("work_types", []):
            wt_counter[wt] += 1
    main_work_type = wt_counter.most_common(1)[0][0] if wt_counter else ""

    # ── 3. 조치사항 (top 3 hazard 기준 합산, 중복 제거) ─────────────────────
    controls: list[str] = []
    seen: set[str] = set()
    for haz in top_hazards:
        for ctrl in _CONTROLS.get(haz, []):
            if ctrl not in seen:
                controls.append(ctrl)
                seen.add(ctrl)
    controls = controls[:6]  # 최대 6개

    # ── 4. 법령 추출 (LAW source 상위 2건) ──────────────────────────────────
    laws: list[dict] = []
    for h in hits:
        if h.get("source") == "law":
            laws.append({
                "title": h.get("title", ""),
                "body_snippet": (h.get("body_text") or "")[:120].replace("\n", " "),
                "score": h.get("score", 0),
            })
        if len(laws) >= 2:
            break

    # LAW가 hits에 없으면 law-only 재검색
    if not laws and main_hazard:
        law_hits = search(_HAZARD_EXPAND.get(main_hazard, main_hazard), top=5, sources=["law"])
        for h in law_hits[:2]:
            laws.append({
                "title": h.get("title", ""),
                "body_snippet": (h.get("body_text") or "")[:120].replace("\n", " "),
                "score": h.get("score", 0),
            })

    # ── 5. 사례 추출 (EXPC 우선, 없으면 KOSHA 1건) ──────────────────────────
    cases: list[dict] = []
    for src in ("expc", "kosha"):
        for h in hits:
            if h.get("source") == src:
                cases.append({
                    "source": src,
                    "title":  h.get("title", ""),
                    "body_snippet": (h.get("body_text") or "")[:150].replace("\n", " "),
                    "score": h.get("score", 0),
                })
                break
        if cases:
            break

    return {
        "query":      query,
        "main_hazard": main_hazard,
        "sub_hazards": top_hazards[1:],
        "work_type":  main_work_type,
        "controls":   controls,
        "laws":       laws,
        "cases":      cases,
    }


def _print_summary(summary: dict) -> None:
    print(f"\n{'='*62}")
    print(f"검색어     : {summary['query']}")
    print(f"주요 위험  : {summary['main_hazard']}")
    if summary["sub_hazards"]:
        print(f"부가 위험  : {', '.join(summary['sub_hazards'])}")
    print(f"작업유형   : {summary['work_type']}")
    print(f"\n[조치사항]")
    for i, c in enumerate(summary["controls"], 1):
        print(f"  {i}. {c}")
    print(f"\n[관련 법령]")
    if summary["laws"]:
        for law in summary["laws"]:
            print(f"  · {law['title'][:65]}")
            if law["body_snippet"]:
                print(f"    {law['body_snippet'][:80]}…")
    else:
        print("  (없음)")
    print(f"\n[사례]")
    if summary["cases"]:
        for case in summary["cases"]:
            print(f"  [{case['source'].upper()}] {case['title'][:60]}")
            if case["body_snippet"]:
                print(f"    {case['body_snippet'][:100]}…")
    else:
        print("  (없음)")
    print()


def _evaluate(summary: dict) -> tuple[bool, list[str]]:
    issues = []
    if not summary["main_hazard"]:
        issues.append("main_hazard 없음")
    if not summary["controls"]:
        issues.append("controls 없음")
    if not summary["laws"]:
        issues.append("법령 없음")
    if not summary["cases"]:
        issues.append("사례 없음")
    return len(issues) == 0, issues


def run_demo() -> None:
    queries = ["비계 작업", "밀폐공간 작업", "용접 작업"]

    print("\n" + "="*62)
    print("위험성 평가 요약 데모")
    print("="*62)

    results = []
    for q in queries:
        s = generate_summary(q)
        _print_summary(s)
        ok, issues = _evaluate(s)
        results.append((q, ok, issues, s))

    print("="*62)
    print("품질 평가")
    print("="*62)
    all_pass = True
    for q, ok, issues, s in results:
        status = "PASS" if ok else "WARN"
        if not ok:
            all_pass = False
        detail = f"  문제: {issues}" if issues else ""
        has_law  = "Y" if s["laws"]  else "N"
        has_case = "Y" if s["cases"] else "N"
        print(f"  {q!r:18s}  hazard:{s['main_hazard']:8s}  법령:{has_law}  사례:{has_case}  [{status}]{detail}")

    print(f"\n  전체: {'PASS' if all_pass else 'WARN'}")
    print()


def main() -> None:
    if len(sys.argv) == 1 or "--demo" in sys.argv:
        run_demo()
        return

    query = " ".join(a for a in sys.argv[1:] if not a.startswith("--"))
    if not query:
        run_demo()
        return

    s = generate_summary(query)
    _print_summary(s)
    ok, issues = _evaluate(s)
    print(f"판정: {'PASS' if ok else 'WARN'}" + (f"  ({', '.join(issues)})" if issues else ""))


if __name__ == "__main__":
    main()

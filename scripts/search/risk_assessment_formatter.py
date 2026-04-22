"""
위험성평가표 출력용 JSON 포매터

사용법:
  python -m scripts.search.risk_assessment_formatter "비계 작업"
  python -m scripts.search.risk_assessment_formatter --demo
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

# ── 위험요인 + 작업유형 조합 → risk_factor 문장 템플릿 ────────────────────
_RF_TEMPLATES: dict[tuple[str, str], list[str]] = {
    ("추락",     "비계_조립"):  ["비계 조립·해체 중 작업발판 끝 또는 개구부에서 추락 위험",
                                 "안전난간 미설치 구간에서 균형 상실로 인한 추락 위험"],
    ("추락",     "비계_해체"):  ["비계 해체 중 고소 위치에서 추락 위험",
                                 "해체 순서 미준수로 인한 비계 붕괴·추락 위험"],
    ("추락",     "고소작업"):   ["고소작업대 탑승 중 플랫폼 가장자리 추락 위험",
                                 "작업대 이동 중 충격에 의한 추락 위험"],
    ("추락",     "철골"):       ["철골 구조물 위 이동 중 발 미끄러짐에 의한 추락 위험",
                                 "볼트 체결 작업 중 추락 위험"],
    ("추락",     "지붕"):       ["지붕 경사면 이동 중 미끄러짐 추락 위험",
                                 "슬레이트·패널 파손에 의한 추락 위험"],
    ("붕괴",     "굴착"):       ["굴착면 토사 붕괴로 인한 작업자 매몰 위험",
                                 "흙막이 지지대 파손에 의한 굴착면 붕괴 위험"],
    ("화재폭발", "용접"):       ["용접 불티 비산에 의한 주변 가연물 화재 위험",
                                 "인화성 물질 근처 용접 작업 중 폭발 위험"],
    ("질식",     "밀폐공간"):   ["밀폐공간 내 산소 결핍 또는 유해가스 축적에 의한 질식 위험",
                                 "작업 중 환기 불량으로 인한 의식 상실 위험"],
    ("감전",     "전기"):       ["충전부 접촉에 의한 감전 위험",
                                 "절연 불량 전기기기 취급 중 누전 감전 위험"],
    ("화학물질", "도장"):       ["도료·희석제 증기 흡입에 의한 유기용제 중독 위험",
                                 "스프레이 도장 중 인화성 증기 누적에 의한 화재 위험"],
    ("중량물",   "양중"):       ["인양 중 자재 낙하로 인한 하부 작업자 비래 위험",
                                 "과하중 리프팅에 의한 크레인 전도 위험"],
    ("끼임",     "기계정비"):   ["회전·가동 부위 정지 미확인 후 정비 중 끼임 위험",
                                 "기계 운전 중 방호장치 해제 상태로 작업 시 협착 위험"],
}

# 템플릿 미매칭 시 범용 문장
_GENERIC_RF: dict[str, list[str]] = {
    "추락":     ["고소 작업 위치에서 추락 위험", "작업발판 불안정으로 인한 추락 위험"],
    "끼임":     ["회전 기계 가동 부위에 신체 끼임 위험", "자동화 설비 동작 중 협착 위험"],
    "충돌":     ["이동 차량·장비와 보행자 충돌 위험", "중장비 선회 반경 내 작업자 접촉 위험"],
    "붕괴":     ["가설 구조물 과하중으로 인한 붕괴 위험", "토사 불안정으로 인한 사면 붕괴 위험"],
    "감전":     ["전기설비 충전부 직접 접촉 감전 위험", "젖은 상태에서 전기기기 취급 중 감전 위험"],
    "화재폭발": ["인화성 물질 취급 중 화재·폭발 위험", "화기 작업 중 주변 가연물 착화 위험"],
    "질식":     ["밀폐 공간 내 유해가스 축적에 의한 질식 위험", "작업 중 환기 불량으로 인한 산소 결핍 위험"],
    "중량물":   ["중량물 수동 취급 중 요추 부상 위험", "자재 낙하·전도로 인한 충격 위험"],
    "화학물질": ["유해화학물질 흡입·피부 접촉에 의한 중독 위험", "화학물질 누출에 의한 환경·안전 위험"],
    "협착":     ["문·덮개·게이트 작동 중 신체 협착 위험", "기계 가동 중 접근 시 압착 위험"],
    "전도":     ["바닥 이물질·물기로 인한 미끄러짐·넘어짐 위험", "경사로 이동 중 전도 위험"],
    "비래낙하": ["상부 작업 중 공구·자재 낙하에 의한 비래 위험", "고소 적재물 결속 불량으로 인한 낙하 위험"],
    "소음진동": ["고소음 장비 장시간 사용에 의한 청력 손상 위험", "진동 공구 사용에 의한 수완 진동 장해 위험"],
    "온도":     ["하절기 고온 환경에서 열사병 위험", "동절기 저온 노출에 의한 동상 위험"],
}


def _build_risk_factors(summary: dict) -> list[str]:
    main_haz = summary.get("main_hazard", "")
    wt       = summary.get("representative_work_type", "")
    sub_haz  = summary.get("sub_hazards", [])

    factors: list[str] = []
    seen: set[str] = set()

    def _add(items: list[str]) -> None:
        for s in items:
            if s not in seen and len(factors) < 5:
                factors.append(s)
                seen.add(s)

    # 주 hazard + work_type 조합 템플릿 우선
    _add(_RF_TEMPLATES.get((main_haz, wt), []))
    # 주 hazard 범용 템플릿
    _add(_GENERIC_RF.get(main_haz, []))
    # 부 hazard 범용 템플릿 (최대 1건씩)
    for sh in sub_haz[:2]:
        _add([_GENERIC_RF.get(sh, [sh + " 관련 위험"])[0]])

    if not factors and main_haz:
        factors.append(f"{main_haz} 관련 작업 위험")

    return factors[:5]


def _build_controls(summary: dict) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for c in summary.get("controls", []):
        if c not in seen:
            result.append(c)
            seen.add(c)
    return result[:6]


def _build_legal_basis(summary: dict) -> list[dict]:
    result = []
    for law in summary.get("laws", [])[:2]:
        result.append({
            "title":  law.get("title", ""),
            "source": "law",
        })
    return result


def _build_reference_cases(summary: dict) -> list[dict]:
    result = []
    for case in summary.get("cases", [])[:2]:
        result.append({
            "title":  case.get("title", ""),
            "source": case.get("source", ""),
        })
    return result


def _source_summary(hits: list[dict]) -> dict:
    cnt: dict[str, int] = {"kosha": 0, "law": 0, "expc": 0}
    for h in hits:
        src = h.get("source", "")
        if src in cnt:
            cnt[src] += 1
    return {f"{k}_count": v for k, v in cnt.items()}


def _evaluate_output(result: dict) -> dict:
    checks = {
        "main_hazard":      bool(result.get("main_hazard")),
        "controls_3+":      len(result.get("controls", [])) >= 3,
        "legal_basis_1+":   len(result.get("legal_basis", [])) >= 1,
        "reference_case_1+": len(result.get("reference_cases", [])) >= 1,
        "risk_factors_3+":  len(result.get("risk_factors", [])) >= 3,
    }
    passed = all(checks.values())
    return {
        "passed": passed,
        "status": "PASS" if passed else "WARN",
        "checks": checks,
    }


def format_assessment(query: str) -> dict:
    from scripts.search.risk_summary import generate_summary

    summary = generate_summary(query)
    hits    = summary.get("hits", [])

    risk_factors    = _build_risk_factors(summary)
    controls        = _build_controls(summary)
    legal_basis     = _build_legal_basis(summary)
    reference_cases = _build_reference_cases(summary)

    result = {
        "query":                    query,
        "work_name":                query,
        "representative_work_type": summary.get("representative_work_type", ""),
        "main_hazard":              summary.get("main_hazard", ""),
        "sub_hazards":              summary.get("sub_hazards", []),
        "risk_factors":             risk_factors,
        "controls":                 controls,
        "legal_basis":              legal_basis,
        "reference_cases":          reference_cases,
        "source_summary":           _source_summary(hits),
        "meta": {
            "hazard_selection_mode": summary.get("hazard_selection_mode", "frequency"),
            "generated_at":          datetime.now(timezone.utc).isoformat(),
        },
    }
    return result


def _print_assessment(r: dict) -> None:
    print(f"\n{'='*64}")
    print(f"작업명           : {r['work_name']}")
    print(f"대표 작업유형    : {r['representative_work_type']}")
    print(f"주요 위험        : {r['main_hazard']}  (선정방식: {r['meta']['hazard_selection_mode']})")
    print(f"부가 위험        : {', '.join(r['sub_hazards']) or '-'}")
    print(f"\n[위험요인]")
    for f in r["risk_factors"]:
        print(f"  · {f}")
    print(f"\n[조치사항]")
    for i, c in enumerate(r["controls"], 1):
        print(f"  {i}. {c}")
    print(f"\n[법적 근거]")
    for lb in r["legal_basis"]:
        print(f"  [{lb['source'].upper()}] {lb['title'][:65]}")
    if not r["legal_basis"]:
        print("  (없음)")
    print(f"\n[참고 사례]")
    for rc in r["reference_cases"]:
        print(f"  [{rc['source'].upper()}] {rc['title'][:60]}")
    if not r["reference_cases"]:
        print("  (없음)")
    ss = r["source_summary"]
    print(f"\n[소스 현황] kosha:{ss['kosha_count']} law:{ss['law_count']} expc:{ss['expc_count']}")


def run_demo() -> None:
    queries = ["비계 작업", "밀폐공간 작업", "용접 작업"]

    print("\n" + "="*64)
    print("위험성평가표 출력 데모")
    print("="*64)

    eval_results = []
    for q in queries:
        r  = format_assessment(q)
        ev = _evaluate_output(r)
        _print_assessment(r)
        eval_results.append((q, r, ev))

    print("\n" + "="*64)
    print("품질 평가")
    print("="*64)
    all_pass = True
    for q, r, ev in eval_results:
        if not ev["passed"]:
            all_pass = False
        fails = [k for k, v in ev["checks"].items() if not v]
        fail_str = f"  미달: {fails}" if fails else ""
        print(
            f"  {q!r:18s}"
            f"  wt:{r['representative_work_type']:12s}"
            f"  hazard:{r['main_hazard']:8s}"
            f"  ctrl:{len(r['controls'])}  law:{len(r['legal_basis'])}  case:{len(r['reference_cases'])}"
            f"  [{ev['status']}]{fail_str}"
        )
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

    r  = format_assessment(query)
    ev = _evaluate_output(r)
    _print_assessment(r)
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    print(f"\n판정: {ev['status']}")


if __name__ == "__main__":
    main()

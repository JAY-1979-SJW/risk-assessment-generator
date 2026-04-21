"""
수집 스크립트 통합 실행 진입점

사용법:
  python scripts/run_collect.py                         # 전체 (law_all + kosha)
  python scripts/run_collect.py statutes                # 법령 목록
  python scripts/run_collect.py admin_rules             # 행정규칙 목록
  python scripts/run_collect.py licbyl                  # 별표서식 목록
  python scripts/run_collect.py expc                    # 법령해석례 목록
  python scripts/run_collect.py law_content             # 법령 본문 (조문 분해)
  python scripts/run_collect.py admrul_content          # 행정규칙 본문
  python scripts/run_collect.py kosha                   # KOSHA 가이드
  python scripts/run_collect.py law_all                 # 목록 전체 (statutes+admin_rules+licbyl+expc)
  python scripts/run_collect.py content_all             # 본문 전체 (law_content+admrul_content)

수집 모듈 분류:
  [목록 수집 — apis.data.go.kr GW API]
  statutes    — target=law        (법, 시행령, 시행규칙)
  admin_rules — target=admrul     (고시, 예규, 훈령)
  licbyl      — target=licbyl     (별표서식)
  expc        — target=expc       (법령해석례)

  [본문 수집 — law.go.kr DRF lawService.do]
  law_content    — 법령 XML → 조문 단위 분해 (LAW_GO_KR_OC 필요)
  admrul_content — 행정규칙 HTML → 텍스트 (LAW_GO_KR_OC 필요)

  [기타]
  kosha       — portal.kosha.or.kr (KOSHA 가이드)

환경변수:
  DATA_GO_KR_SERVICE_KEY  공공데이터포털 인증키 (목록 수집, 없으면 dry-run)
  LAW_GO_KR_OC            law.go.kr DRF 키 (본문 수집, 없으면 dry-run)
  LAW_API_TIMEOUT         요청 타임아웃 초 (기본 30)
  LAW_API_NUM_OF_ROWS     페이지당 결과 수 (기본 100)
  LAW_API_MAX_PAGES       최대 페이지 수 (기본 50)
  LAW_API_RETRY_COUNT     재시도 횟수 (기본 3)
  KOSHA_ID                KOSHA 인증 (없으면 dry-run)

[LEGACY]
  scripts/collect/law_moel_expc.py  (law.go.kr/DRF moelCgmExpc)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.collect import (
    law_statutes,
    law_admin_rules,
    law_licbyl,
    law_expc,
    law_content,
    admrul_content,
    kosha_guides,
)
from scripts.collect._base import get_logger

log = get_logger("run_collect")

# 표준 수집 모듈
COLLECTORS: dict[str, tuple[str, callable]] = {
    "statutes":       ("법령 목록 (target=law)",           law_statutes.run),
    "admin_rules":    ("행정규칙 목록 (target=admrul)",     law_admin_rules.run),
    "licbyl":         ("별표서식 목록 (target=licbyl)",     law_licbyl.run),
    "expc":           ("법령해석례 목록 (target=expc)",     law_expc.run),
    "law_content":    ("법령 본문 (XML → 조문 분해)",       law_content.run),
    "admrul_content": ("행정규칙 본문 (HTML → 텍스트)",     admrul_content.run),
    "kosha":          ("KOSHA 가이드",                     kosha_guides.run),
}

# 그룹 정의
LAW_ALL     = ["statutes", "admin_rules", "licbyl", "expc"]
CONTENT_ALL = ["law_content", "admrul_content"]


def main(targets: list[str]) -> int:
    # 그룹 확장
    expanded: list[str] = []
    for t in targets:
        if t == "law_all":
            expanded.extend(LAW_ALL)
        elif t == "content_all":
            expanded.extend(CONTENT_ALL)
        else:
            expanded.append(t)

    # all → 전체 (law_all + content_all + kosha)
    if not expanded or expanded == ["all"]:
        expanded = LAW_ALL + CONTENT_ALL + ["kosha"]

    unknown = [t for t in expanded if t not in COLLECTORS]
    if unknown:
        log.error(f"알 수 없는 수집 대상: {unknown}")
        log.error(f"사용 가능: {list(COLLECTORS.keys())} + law_all")
        return 1

    results: dict[str, bool] = {}
    for key in expanded:
        label, fn = COLLECTORS[key]
        log.info(f"▶ [{key}] {label}")
        try:
            results[key] = fn()
        except Exception as e:
            log.error(f"[{key}] 실행 중 예외: {e}")
            results[key] = False

    log.info("=== 전체 수집 결과 ===")
    all_ok = True
    for key, ok in results.items():
        mark = "✓" if ok else "✗"
        log.info(f"  {mark} {key}")
        if not ok:
            all_ok = False

    return 0 if all_ok else 1


if __name__ == "__main__":
    args = sys.argv[1:] or ["all"]
    sys.exit(main(args))

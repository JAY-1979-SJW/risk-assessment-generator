"""
[LEGACY] 고용노동부 법령해석 목록 수집 — law.go.kr/DRF  target=moelCgmExpc
이 모듈은 보류 상태입니다. 표준 수집축은 law_expc.py (data.go.kr GW API)를 사용하세요.
삭제하지 말고 유지. run_collect.py 표준 수집 목록에서 제외됨.

대상: 위험성평가·안전보건 관련 키워드
저장: data/risk_db/law_raw/moel_expc_index.json
환경변수: LAW_API_KEY  (없으면 dry-run)

요청 파라미터:
  OC, target=moelCgmExpc, type, query, search(1:해석명/2:본문),
  display(max=100), page, inq(질의기관코드), rpl(해석기관코드),
  explYd(해석일자범위 20090101~20090130), sort, itmno(안건번호)
"""
import time
import requests
from ._base import get_logger, get_env, save_json, write_status, now_iso, ROOT

log = get_logger("law_moel_expc")

API_URL = "https://www.law.go.kr/DRF/lawSearch.do"
DELAY = 1.0
OUT_PATH = ROOT / "data/risk_db/law_raw/moel_expc_index.json"

# 수집 대상 키워드 (각각 별도 요청)
KEYWORDS = [
    "위험성평가",
    "안전보건관리책임자",
    "추락재해",
    "감전재해",
    "밀폐공간",
    "안전관리계획",
]


def _search(query: str, api_key: str, page: int = 1) -> dict:
    try:
        r = requests.get(
            API_URL,
            params={
                "OC": api_key,
                "target": "moelCgmExpc",
                "type": "JSON",
                "query": query,
                "search": 1,      # 1=해석명 검색
                "display": 20,
                "page": page,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("LawSearch", {})
    except Exception as e:
        log.warning(f"검색 실패 [{query}]: {e}")
        return {}


def _parse_items(raw: dict, keyword: str) -> list[dict]:
    items = raw.get("expc", [])
    if isinstance(items, dict):
        items = [items]
    results = []
    for item in items:
        serial = item.get("법령해석일련번호", "")
        detail = item.get("법령해석상세링크", "")
        results.append({
            "law_code":     f"EXPC-{serial}" if serial else None,
            "law_name":     item.get("안건명"),
            "law_type":     "interpretation",
            "article_no":   item.get("안건번호"),
            "source":       "law.go.kr",
            "source_org":   item.get("해석기관명") or "고용노동부",
            "raw_url":      f"https://www.law.go.kr{detail}" if detail else None,
            "is_active":    True,
            "mst":          serial,
            "interpreted_at": item.get("해석일자"),
            "inq_org":      item.get("질의기관명"),
            "keyword":      keyword,
        })
    return results


def _collect_keyword(keyword: str, api_key: str) -> list[dict]:
    log.info(f"수집: '{keyword}'")
    if not api_key:
        log.warning(f"LAW_API_KEY 미설정 — dry-run: {keyword}")
        return [{
            "law_code": None, "law_name": None, "law_type": "interpretation",
            "source": "law.go.kr", "source_org": "고용노동부",
            "keyword": keyword, "status": "dry_run",
        }]

    raw = _search(keyword, api_key)
    time.sleep(DELAY)
    items = _parse_items(raw, keyword)
    total = int(raw.get("totalCnt", 0))
    log.info(f"  → {len(items)}건 (총 {total}건)")
    return items


def run() -> bool:
    api_key = get_env("LAW_API_KEY")
    log.info("=== 고용노동부 법령해석 수집 시작 ===")
    all_items: list[dict] = []
    success, fail = 0, 0

    for kw in KEYWORDS:
        try:
            items = _collect_keyword(kw, api_key)
            all_items.extend(items)
            success += 1
        except Exception as e:
            log.error(f"예외 [{kw}]: {e}")
            fail += 1

    # law_code 중복 제거 (같은 해석례가 여러 키워드에서 수집될 수 있음)
    seen, deduped = set(), []
    for item in all_items:
        key = item.get("law_code") or item.get("law_name")
        if key and key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    save_json(OUT_PATH, {
        "version": "1.0", "fetched_at": now_iso(), "source": "law.go.kr",
        "api_target": "moelCgmExpc",
        "keywords": KEYWORDS,
        "total": len(deduped), "success": success, "fail": fail,
        "laws": deduped,
    })
    status = "SUCCESS" if fail == 0 else ("PARTIAL" if success > 0 else "FAIL")
    write_status("law_moel_expc", status, success, fail)
    log.info(f"=== 완료: {status} — {len(deduped)}건 저장 ({OUT_PATH}) ===")
    return fail == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

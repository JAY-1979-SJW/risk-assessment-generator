"""
KOSHA 건설안전 가이드 메타데이터 수집
저장: data/risk_db/guide_raw/kosha_guides_index.json
환경변수: KOSHA_ID  (없으면 dry-run)
"""
import time
import requests
from ._base import get_logger, get_env, save_json, write_status, now_iso, ROOT

log = get_logger("kosha_guides")

KOSHA_BASE = "https://portal.kosha.or.kr"
DELAY = 1.5
OUT_PATH = ROOT / "data/risk_db/guide_raw/kosha_guides_index.json"

TARGETS = [
    {"guide_code": "KOSHA-G-CONST-001", "title": "건설공사 위험성평가 지침",        "category": "건설안전", "search_keyword": "건설공사 위험성평가"},
    {"guide_code": "KOSHA-G-CONST-002", "title": "건설현장 추락재해 예방 가이드",    "category": "건설안전", "search_keyword": "추락재해 예방"},
    {"guide_code": "KOSHA-G-CONST-003", "title": "거푸집 및 동바리 붕괴 예방",      "category": "건설안전", "search_keyword": "거푸집 동바리"},
    {"guide_code": "KOSHA-G-CONST-004", "title": "건설현장 감전재해 예방 가이드",    "category": "건설안전", "search_keyword": "건설현장 감전"},
    {"guide_code": "KOSHA-G-CONST-005", "title": "크레인 및 양중기 안전작업 가이드", "category": "건설안전", "search_keyword": "크레인 양중기"},
]


def _probe(keyword: str) -> dict:
    try:
        r = requests.get(
            f"{KOSHA_BASE}/kosha/data/publicDataList.do",
            params={"searchKeyword": keyword},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        return {"http_status": r.status_code, "accessible": r.status_code == 200}
    except Exception as e:
        return {"http_status": None, "accessible": False, "error": str(e)}


def _collect_one(guide: dict, has_auth: bool) -> dict:
    log.info(f"수집: {guide['title']}")
    result = {
        "guide_code": guide["guide_code"],
        "title":      guide["title"],
        "category":   guide["category"],
        "source":     "kosha.or.kr",
        "source_org": "한국산업안전보건공단",
        "raw_url":    f"{KOSHA_BASE}/kosha/data/publicDataList.do",
        "fetched_at": now_iso(),
        "status":     "dry_run",
        "error":      None,
    }
    if not has_auth:
        log.warning(f"KOSHA_ID 미설정 — dry-run: {guide['title']}")
        return result

    probe = _probe(guide["search_keyword"])
    time.sleep(DELAY)
    if probe.get("accessible"):
        result["status"] = "meta_ok"
        log.info(f"접근 확인: {guide['title']}")
    else:
        result["status"] = "fetch_warn"
        result["error"] = probe.get("error", f"HTTP {probe.get('http_status')}")
        log.warning(f"접근 불가 [{guide['title']}]: {result['error']}")
    return result


def run() -> bool:
    has_auth = bool(get_env("KOSHA_ID"))
    log.info("=== KOSHA 가이드 수집 시작 ===")
    results, success, fail = [], 0, 0
    for g in TARGETS:
        try:
            item = _collect_one(g, has_auth)
            results.append(item)
            if item["status"] in ("meta_ok", "dry_run"):
                success += 1
            else:
                fail += 1
        except Exception as e:
            log.error(f"예외 [{g['title']}]: {e}")
            results.append({"guide_code": g["guide_code"], "title": g["title"],
                            "status": "error", "error": str(e), "fetched_at": now_iso()})
            fail += 1

    save_json(OUT_PATH, {
        "version": "1.1", "fetched_at": now_iso(), "source": "kosha.or.kr",
        "total": len(results), "success": success, "fail": fail, "guides": results,
    })
    status = "SUCCESS" if fail == 0 else ("PARTIAL" if success > 0 else "FAIL")
    write_status("kosha_guides", status, success, fail)
    log.info(f"=== 완료: {status} ({OUT_PATH}) ===")
    return fail == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

"""
KOSHA 건설안전 핵심 가이드 메타데이터 수집기 (최소 샘플)
대상: 건설안전 핵심 가이드 5개 (고정 목록)
저장: data/risk_db/guide_raw/kosha_guides_index.json
로그: logs/law_collect/kosha_guides.log
환경변수: KOSHA_ID (없으면 dry-run)
"""
import os
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
load_dotenv(SCRIPTS_DIR / ".env")
load_dotenv(BASE_DIR / ".env", override=False)

LOG_DIR = BASE_DIR / "logs" / "law_collect"
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR = BASE_DIR / "data" / "risk_db" / "guide_raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "kosha_guides.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

KOSHA_ID = os.getenv("KOSHA_ID", "")
KOSHA_BASE = "https://portal.kosha.or.kr"
REQUEST_DELAY = 1.5

TARGET_GUIDES = [
    {
        "guide_code": "KOSHA-G-CONST-001",
        "title": "건설공사 위험성평가 지침",
        "category": "건설안전",
        "search_keyword": "건설공사 위험성평가",
        "source_org": "한국산업안전보건공단",
    },
    {
        "guide_code": "KOSHA-G-CONST-002",
        "title": "건설현장 추락재해 예방 가이드",
        "category": "건설안전",
        "search_keyword": "추락재해 예방",
        "source_org": "한국산업안전보건공단",
    },
    {
        "guide_code": "KOSHA-G-CONST-003",
        "title": "거푸집 및 동바리 붕괴 예방",
        "category": "건설안전",
        "search_keyword": "거푸집 동바리",
        "source_org": "한국산업안전보건공단",
    },
    {
        "guide_code": "KOSHA-G-CONST-004",
        "title": "건설현장 감전재해 예방 가이드",
        "category": "건설안전",
        "search_keyword": "건설현장 감전",
        "source_org": "한국산업안전보건공단",
    },
    {
        "guide_code": "KOSHA-G-CONST-005",
        "title": "크레인 및 양중기 안전작업 가이드",
        "category": "건설안전",
        "search_keyword": "크레인 양중기",
        "source_org": "한국산업안전보건공단",
    },
]


def try_fetch_guide_meta(keyword: str) -> dict:
    """KOSHA 포털 접근 가능 여부만 확인 (인증 불필요 공개 엔드포인트)"""
    url = f"{KOSHA_BASE}/kosha/data/publicDataList.do"
    try:
        r = requests.get(
            url,
            params={"searchKeyword": keyword},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        return {"http_status": r.status_code, "accessible": r.status_code == 200}
    except Exception as e:
        return {"http_status": None, "accessible": False, "error": str(e)}


def collect_guide_meta(guide: dict) -> dict:
    log.info(f"수집 시작: {guide['title']}")
    result = {
        "guide_code": guide["guide_code"],
        "title": guide["title"],
        "category": guide["category"],
        "source": "kosha.or.kr",
        "source_org": guide["source_org"],
        "raw_url": f"{KOSHA_BASE}/kosha/data/publicDataList.do",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "error": None,
    }

    if not KOSHA_ID:
        log.warning(f"KOSHA_ID 미설정 — dry-run: {guide['title']}")
        result["status"] = "dry_run"
        return result

    fetch_result = try_fetch_guide_meta(guide["search_keyword"])
    time.sleep(REQUEST_DELAY)

    if fetch_result.get("accessible"):
        result["status"] = "meta_ok"
        log.info(f"접근 확인: {guide['title']}")
    else:
        result["status"] = "fetch_warn"
        result["error"] = fetch_result.get("error", f"HTTP {fetch_result.get('http_status')}")
        log.warning(f"접근 불가 [{guide['title']}]: {result['error']}")

    return result


def run() -> bool:
    log.info("=== KOSHA 가이드 메타 수집 시작 ===")
    results = []
    success, fail = 0, 0

    for guide in TARGET_GUIDES:
        try:
            item = collect_guide_meta(guide)
            results.append(item)
            if item["status"] in ("meta_ok", "dry_run"):
                success += 1
            else:
                fail += 1
        except Exception as e:
            log.error(f"예외 발생 [{guide['title']}]: {e}")
            results.append({
                "guide_code": guide["guide_code"],
                "title": guide["title"],
                "status": "error",
                "error": str(e),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
            fail += 1

    output = {
        "version": "1.0",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "kosha.or.kr",
        "total": len(results),
        "success": success,
        "fail": fail,
        "guides": results,
    }

    out_path = OUT_DIR / "kosha_guides_index.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"저장 완료: {out_path} (성공={success}, 실패={fail})")

    status = "SUCCESS" if fail == 0 else ("PARTIAL" if success > 0 else "FAIL")
    (LOG_DIR / "kosha_guides.status").write_text(
        f"{status}\nrun_at={datetime.now(timezone.utc).isoformat()}\nsuccess={success}\nfail={fail}\n",
        encoding="utf-8",
    )
    log.info(f"=== 완료: {status} ===")
    return fail == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

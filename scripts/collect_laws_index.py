"""
법제처 국가법령정보 공개API 기반 법령 메타데이터 수집기
대상: 산업안전보건 관련 핵심 법령 6개 (고정 목록)
저장: data/risk_db/law_raw/laws_index.json
로그: logs/law_collect/laws_index.log
환경변수: LAW_API_KEY (law.go.kr OC 코드) — 없으면 dry-run
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
# scripts/.env 우선, 없으면 프로젝트 루트 .env
load_dotenv(SCRIPTS_DIR / ".env")
load_dotenv(BASE_DIR / ".env", override=False)

LOG_DIR = BASE_DIR / "logs" / "law_collect"
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR = BASE_DIR / "data" / "risk_db" / "law_raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "laws_index.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

LAW_API_KEY = os.getenv("LAW_API_KEY", "")
LAW_API_BASE = "https://www.law.go.kr/DRF"
REQUEST_DELAY = 1.0

TARGET_LAWS = [
    {"query": "산업안전보건법", "law_type": "law", "source_org": "고용노동부"},
    {"query": "산업안전보건법 시행령", "law_type": "enforcement_decree", "source_org": "고용노동부"},
    {"query": "산업안전보건법 시행규칙", "law_type": "enforcement_rule", "source_org": "고용노동부"},
    {"query": "산업안전보건기준에 관한 규칙", "law_type": "enforcement_rule", "source_org": "고용노동부"},
    {"query": "건설업 산업안전보건관리비 계상 및 사용기준", "law_type": "notice", "source_org": "고용노동부"},
    {"query": "사업장 위험성평가에 관한 지침", "law_type": "notice", "source_org": "고용노동부"},
]


def search_law(query: str) -> dict | None:
    url = f"{LAW_API_BASE}/lawSearch.do"
    params = {
        "OC": LAW_API_KEY,
        "target": "law",
        "type": "JSON",
        "query": query,
        "display": 3,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        laws = data.get("LawSearch", {}).get("law", [])
        if isinstance(laws, dict):
            laws = [laws]
        for item in laws:
            if item.get("법령명한글", "").strip() == query.strip():
                return item
        return laws[0] if laws else None
    except Exception as e:
        log.warning(f"법령 검색 실패 [{query}]: {e}")
        return None


def collect_law_meta(target: dict) -> dict:
    query = target["query"]
    log.info(f"수집 시작: {query}")

    result = {
        "law_code": None,
        "law_name": query,
        "law_type": target["law_type"],
        "source": "law.go.kr",
        "source_org": target["source_org"],
        "mst": None,
        "effective_date": None,
        "raw_url": None,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "status": "pending",
        "error": None,
    }

    if not LAW_API_KEY:
        log.warning(f"LAW_API_KEY 미설정 — dry-run: {query}")
        result["status"] = "dry_run"
        return result

    meta = search_law(query)
    time.sleep(REQUEST_DELAY)

    if not meta:
        result["status"] = "not_found"
        result["error"] = "검색 결과 없음"
        log.warning(f"결과 없음: {query}")
        return result

    mst = meta.get("법령일련번호", "")
    result["law_code"] = f"LAW-{mst}" if mst else None
    result["law_name"] = meta.get("법령명한글", query)
    result["mst"] = mst
    result["effective_date"] = meta.get("시행일자", "")
    result["raw_url"] = (
        f"https://www.law.go.kr/법령/{result['law_name'].replace(' ', '')}" if mst else None
    )
    result["status"] = "ok"
    log.info(f"수집 완료: {result['law_name']} (mst={mst})")
    return result


def run() -> bool:
    log.info("=== 법령 메타 수집 시작 ===")
    results = []
    success, fail = 0, 0

    for target in TARGET_LAWS:
        try:
            item = collect_law_meta(target)
            results.append(item)
            if item["status"] in ("ok", "dry_run"):
                success += 1
            else:
                fail += 1
        except Exception as e:
            log.error(f"예외 발생 [{target['query']}]: {e}")
            results.append({
                "law_name": target["query"],
                "status": "error",
                "error": str(e),
                "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            })
            fail += 1

    output = {
        "version": "1.0",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "law.go.kr",
        "total": len(results),
        "success": success,
        "fail": fail,
        "laws": results,
    }

    out_path = OUT_DIR / "laws_index.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"저장 완료: {out_path} (성공={success}, 실패={fail})")

    status = "SUCCESS" if fail == 0 else ("PARTIAL" if success > 0 else "FAIL")
    (LOG_DIR / "laws_index.status").write_text(
        f"{status}\nrun_at={datetime.now(timezone.utc).isoformat()}\nsuccess={success}\nfail={fail}\n",
        encoding="utf-8",
    )
    log.info(f"=== 완료: {status} ===")
    return fail == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

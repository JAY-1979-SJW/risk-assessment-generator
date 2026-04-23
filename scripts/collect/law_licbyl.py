"""
별표서식 목록 수집
엔드포인트: http://apis.data.go.kr/1170000/law/licbylSearchList.do
target: licbyl
저장: data/risk_db/law_raw/licbyl_index.json
환경변수: DATA_GO_KR_SERVICE_KEY  (없으면 dry-run)

주요 응답 필드:
  별표일련번호, 별표명, 관련법령명, 별표종류(서식/별표),
  소관부처명, 공포일자, 별표서식파일링크, 별표서식PDF파일링크, 별표법령상세링크
"""
import time
from ._base import (
    get_logger, get_service_key, gw_collect_all,
    save_json, write_status, today_str, ROOT,
)

log = get_logger("law_licbyl")

ENDPOINT = "http://apis.data.go.kr/1170000/law/licbylSearchList.do"
TARGET    = "licbyl"
OUT_PATH  = ROOT / "data/risk_db/law_raw/licbyl_index.json"

QUERIES = [
    "산업안전보건",
    "위험성평가",
    "안전보건관리",
]


def run() -> bool:
    service_key = get_service_key()
    log.info("=== 별표서식 수집 시작 ===")

    all_items: list[dict] = []
    result_code, result_msg = "00", "success"
    success, fail = 0, 0

    for q in QUERIES:
        log.info(f"수집: {q}")
        result = gw_collect_all(ENDPOINT, TARGET, q, service_key, log)

        if result["result_code"] == "dry_run":
            log.warning(f"DATA_GO_KR_SERVICE_KEY 미설정 — dry-run: {q}")
            success += 1
            continue

        if result["result_code"] != "00":
            log.warning(f"오류 [{q}]: {result['result_code']} {result['result_msg']}")
            result_code = result["result_code"]
            result_msg  = result["result_msg"]
            fail += 1
            continue

        all_items.extend(result["items"])
        log.info(f"완료: {q} → {len(result['items'])}건")
        success += 1
        time.sleep(1.0)

    # 별표일련번호 기준 중복 제거
    seen, deduped = set(), []
    for item in all_items:
        key = item.get("별표일련번호") or item.get("별표명")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    is_dry = not service_key
    save_json(OUT_PATH, {
        "source":      "data.go.kr",
        "target":      TARGET,
        "endpoint":    ENDPOINT,
        "fetched_at":  today_str(),
        "queries":     QUERIES,
        "num_of_rows": 100,
        "total_count": len(deduped),
        "result_code": "dry_run" if is_dry else result_code,
        "result_msg":  "no key — dry-run" if is_dry else result_msg,
        "status":      "dry_run" if is_dry else ("success" if fail == 0 else "partial"),
        "items":       deduped,
    })

    status = "SUCCESS" if fail == 0 else ("PARTIAL" if success > 0 else "FAIL")
    write_status("law_licbyl", status, success, fail)
    log.info(f"=== 완료: {status} — {len(deduped)}건 ({OUT_PATH}) ===")
    return fail == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

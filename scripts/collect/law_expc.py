"""
법령해석례 목록 수집  target=expc
엔드포인트: data.go.kr GW API

저장:
  data/risk_db/law_raw/expc_index.json
  data/raw/law_api/expc/YYYY-MM-DD/expc_index.json

주요 응답 필드:
  법령해석례일련번호, 안건명, 안건번호, 질의기관명, 회신기관명, 회신일자, 법령해석례상세링크
"""
import time
from ._base import (
    get_logger, get_service_key,
    gw_collect_all,
    save_json, save_raw_dated, write_status, today_str, ROOT,
)

log = get_logger("law_expc")

ENDPOINT = "http://apis.data.go.kr/1170000/law/expcSearchList.do"
TARGET   = "expc"
OUT_PATH = ROOT / "data/risk_db/law_raw/expc_index.json"

# ── 수집 쿼리 ─────────────────────────────────────────────────────────────────
# 기본 + 4대 worktype 위험요인 키워드 보강
QUERIES = [
    # 기본 산업안전
    "산업안전보건",
    "위험성평가",
    # FALL / TEMP_SCAFF
    "추락",
    "비계",
    "작업발판",
    # ELEC / ELEC_LIVE
    "감전",
    "활선",
    "전기안전",
    # ASPHYX / WATER_MANHOLE
    "밀폐공간",
    "질식",
    "산소결핍",
    # LIFT_RIGGING / DROP
    "크레인",
    "양중",
    "낙하",
    # ENTRAP / 기계
    "협착",
    # COLLAPSE
    "붕괴",
    # 화학
    "화학물질",
]


def run() -> bool:
    service_key = get_service_key()
    log.info("=== 법령해석례 수집 시작 (target=expc) ===")

    all_items: list[dict] = []
    result_code, result_msg = "00", "success"
    success, fail = 0, 0

    for q in QUERIES:
        log.info(f"  [{q}]")
        result = gw_collect_all(ENDPOINT, TARGET, q, service_key, log)

        if result["result_code"] == "dry_run":
            log.warning(f"  DATA_GO_KR_SERVICE_KEY 미설정 — dry-run: {q}")
            success += 1
            continue

        if result["result_code"] != "00":
            log.warning(f"  오류 [{q}]: {result['result_code']} {result['result_msg']}")
            result_code = result["result_code"]
            result_msg  = result["result_msg"]
            fail += 1
            continue

        all_items.extend(result["items"])
        log.info(f"  완료: {q} → {len(result['items'])}건")
        success += 1
        time.sleep(1.0)

    # 법령해석례일련번호 기준 중복 제거
    seen, deduped = set(), []
    for item in all_items:
        key = item.get("법령해석례일련번호") or item.get("안건번호") or item.get("안건명")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    is_dry = not service_key
    output = {
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
    }
    save_json(OUT_PATH, output)
    save_raw_dated(TARGET, "expc_index.json", {k: v for k, v in output.items() if k != "fetched_at"})

    status = "SUCCESS" if fail == 0 else ("PARTIAL" if success > 0 else "FAIL")
    write_status("law_expc", status, success, fail)
    log.info(f"=== 완료: {status} — {len(deduped)}건 저장 ({OUT_PATH}) ===")
    return fail == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

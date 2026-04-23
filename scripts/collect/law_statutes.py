"""
법령 목록 수집  (target=law)
엔드포인트 A: data.go.kr  GW API  (DATA_GO_KR_SERVICE_KEY)
엔드포인트 B: law.go.kr   DRF API (LAW_GO_KR_OC) — 키 있으면 추가 수집

저장:
  data/risk_db/law_raw/laws_index.json          (pipeline 입력용, 항상 덮어씀)
  data/raw/law_api/law/YYYY-MM-DD/laws_index.json  (날짜 archive)
"""
import json
import time
from ._base import (
    get_logger, get_service_key, get_oc_key,
    gw_collect_all, drf_collect_all,
    save_json, save_raw_dated, write_status, now_iso, ROOT,
)

log = get_logger("law_statutes")

GW_ENDPOINT = "http://apis.data.go.kr/1170000/law/lawSearchList.do"
TARGET       = "law"
OUT_PATH     = ROOT / "data/risk_db/law_raw/laws_index.json"

# ── 수집 쿼리 ─────────────────────────────────────────────────────────────────
# 핵심 안전보건 법령 + 4대 worktype(ELEC_LIVE/WATER_MANHOLE/TEMP_SCAFF/LIFT_RIGGING) 보강
GW_QUERIES = [
    # 기본 산업안전보건 법령 계열
    "산업안전보건법",
    "산업안전보건법 시행령",
    "산업안전보건법 시행규칙",
    "산업안전보건기준에 관한 규칙",
    # ELEC_LIVE — 전기 관련 법령
    "전기안전관리법",
    "전기사업법",
    # LIFT_RIGGING — 크레인·건설기계 관련
    "건설기계관리법",
    # WATER_MANHOLE — 밀폐공간·상하수도 관련
    "도시가스사업법",
    # 화학물질 (CHEM/POISON)
    "화학물질관리법",
    # 건설 일반
    "건설기술 진흥법",
]

# DRF 전용 쿼리 (law.go.kr OC 키 있을 때 추가 수집)
DRF_QUERIES = [
    "산업안전보건법",
    "산업안전보건기준에 관한 규칙",
    "전기안전관리법",
    "건설기계관리법",
    "화학물질관리법",
]

# 중복 제거 키
_DEDUP_KEY = lambda item: item.get("법령일련번호") or item.get("법령명한글") or item.get("법령명_한글")


def _stable_law_sort_key(item: dict) -> tuple:
    return (
        str(item.get("법령ID") or ""),
        str(item.get("법령일련번호") or ""),
        str(item.get("시행일자") or ""),
        str(item.get("법령명한글") or ""),
        json.dumps(item, ensure_ascii=False, sort_keys=True),
    )


def run() -> bool:
    service_key = get_service_key()
    oc_key      = get_oc_key()
    log.info("=== 법령 수집 시작 (target=law) ===")

    all_items: list[dict] = []
    result_code, result_msg = "00", "success"
    success, fail = 0, 0

    # ── A. GW API ──────────────────────────────────────────────────────────────
    log.info("── A. GW API (data.go.kr) ──")
    for q in GW_QUERIES:
        log.info(f"  GW [{q}]")
        result = gw_collect_all(GW_ENDPOINT, TARGET, q, service_key, log)

        if result["result_code"] == "dry_run":
            log.warning(f"  DATA_GO_KR_SERVICE_KEY 미설정 — dry-run: {q}")
            success += 1
            continue

        if result["result_code"] != "00":
            log.warning(f"  GW 오류 [{q}]: {result['result_code']} {result['result_msg']}")
            result_code = result["result_code"]
            result_msg  = result["result_msg"]
            fail += 1
            continue

        all_items.extend(result["items"])
        log.info(f"  GW 완료: {q} → {len(result['items'])}건")
        success += 1
        time.sleep(1.0)

    # ── B. DRF API ─────────────────────────────────────────────────────────────
    if oc_key:
        log.info("── B. DRF API (law.go.kr) ──")
        for q in DRF_QUERIES:
            result = drf_collect_all(TARGET, q, oc_key, log)
            if result["result_code"] in ("dry_run", "03"):
                continue
            if result["result_code"] != "00":
                log.warning(f"  DRF 오류 [{q}]: {result['result_code']} {result['result_msg']}")
                continue
            # DRF 응답 필드 통일 (법령명_한글 → 법령명한글)
            for item in result["items"]:
                if "법령명_한글" in item and "법령명한글" not in item:
                    item["법령명한글"] = item["법령명_한글"]
            all_items.extend(result["items"])
            log.info(f"  DRF 완료: {q} → {len(result['items'])}건")
            time.sleep(1.0)
    else:
        log.info("── B. DRF API 건너뜀 (LAW_GO_KR_OC 미설정) ──")

    # ── 중복 제거 ──────────────────────────────────────────────────────────────
    seen, deduped = set(), []
    for item in all_items:
        key = _DEDUP_KEY(item)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    deduped = sorted(deduped, key=_stable_law_sort_key)

    is_dry = (not service_key and not oc_key)
    output = {
        "source":      "data.go.kr+law.go.kr",
        "target":      TARGET,
        "endpoint":    GW_ENDPOINT,
        "fetched_at":  now_iso(),
        "queries":     GW_QUERIES,
        "num_of_rows": 100,
        "total_count": len(deduped),
        "result_code": "dry_run" if is_dry else result_code,
        "result_msg":  "no key — dry-run" if is_dry else result_msg,
        "status":      "dry_run" if is_dry else ("success" if fail == 0 else "partial"),
        "items":       deduped,
    }
    save_json(OUT_PATH, output)
    save_raw_dated(TARGET, "laws_index.json", output)

    status = "SUCCESS" if fail == 0 else ("PARTIAL" if success > 0 else "FAIL")
    write_status("law_statutes", status, success, fail)
    log.info(f"=== 완료: {status} — {len(deduped)}건 저장 ({OUT_PATH}) ===")
    return fail == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

"""
행정규칙 목록 수집 (고시·예규·훈령)  target=admrul
엔드포인트: data.go.kr GW API

저장:
  data/risk_db/law_raw/admin_rules_index.json
  data/raw/law_api/admrul/YYYY-MM-DD/admin_rules_index.json

note: 고시류는 target=law로 검색 불가. 반드시 target=admrul 사용.
"""
import time
from ._base import (
    get_logger, get_service_key,
    gw_collect_all,
    save_json, save_raw_dated, write_status, now_iso, ROOT,
)

log = get_logger("law_admin_rules")

ENDPOINT = "https://apis.data.go.kr/1170000/law/admrulSearchList.do"
TARGET   = "admrul"
OUT_PATH = ROOT / "data/risk_db/law_raw/admin_rules_index.json"

# ── 수집 쿼리 ─────────────────────────────────────────────────────────────────
QUERIES = [
    # 위험성평가 기본
    "건설업 산업안전보건관리비 계상 및 사용기준",
    "사업장 위험성평가에 관한 지침",
    # 밀폐공간 / 산소결핍
    "밀폐공간 작업",
    "산소결핍",
    # 전기
    "전기설비기술기준",
    "활선작업",
    # 가설·추락
    "비계 안전",
    "추락재해 예방",
    # 양중·리깅
    "크레인 안전",
    "달기기구",
    # 개인보호구
    "개인보호구",
    # 화학물질 (P3: 화학물질 허용기준 고시)
    "물질안전보건자료",
    "화학물질의 허용기준",
    "작업환경측정",
    "특수건강진단",
    # 기계기구 안전인증 (P3: 크레인·리프트·방호장치)
    "안전인증",
    "위험기계기구",
    "방호장치",
    # 소방 관련 고시 (화재안전 축)
    "소방시설",
    "위험물 저장",
    # 건설·중대재해
    "중대재해",
    "건설현장 안전",
]


def run() -> bool:
    service_key = get_service_key()
    log.info("=== 행정규칙 수집 시작 (target=admrul) ===")

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

    # 행정규칙일련번호 기준 중복 제거
    seen, deduped = set(), []
    for item in all_items:
        key = item.get("행정규칙일련번호") or item.get("행정규칙명")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    is_dry = not service_key
    output = {
        "source":      "data.go.kr",
        "target":      TARGET,
        "endpoint":    ENDPOINT,
        "fetched_at":  now_iso(),
        "queries":     QUERIES,
        "num_of_rows": 100,
        "total_count": len(deduped),
        "result_code": "dry_run" if is_dry else result_code,
        "result_msg":  "no key — dry-run" if is_dry else result_msg,
        "status":      "dry_run" if is_dry else ("success" if fail == 0 else "partial"),
        "items":       deduped,
    }
    save_json(OUT_PATH, output)
    save_raw_dated(TARGET, "admin_rules_index.json", output)

    status = "SUCCESS" if fail == 0 else ("PARTIAL" if success > 0 else "FAIL")
    write_status("law_admin_rules", status, success, fail)
    log.info(f"=== 완료: {status} — {len(deduped)}건 저장 ({OUT_PATH}) ===")
    return fail == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

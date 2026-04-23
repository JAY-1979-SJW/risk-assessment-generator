"""공통 유틸: 로깅 설정, dry-run 처리, JSON 저장, .status 기록, GW API 클라이언트, DRF 클라이언트"""
import json
import logging
import os
import time as _time
import warnings
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests as _requests
import urllib3
from dotenv import load_dotenv

# law.go.kr SSL 인증서 검증 우회 — 정부 사이트 읽기 전용 수집용
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(__file__).parent.parent.parent
_SCRIPTS_DIR = Path(__file__).parent.parent
load_dotenv(_SCRIPTS_DIR / ".env")
load_dotenv(ROOT / ".env", override=False)
load_dotenv(ROOT / "scraper" / ".env", override=False)  # KOSHA_ID/KOSHA_PW

LOG_BASE = ROOT / "logs" / "law_collect"
RAW_DATED_BASE = ROOT / "data" / "raw" / "law_api"


def get_logger(name: str) -> logging.Logger:
    LOG_BASE.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(LOG_BASE / f"{name}.log", encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def save_json(path: Path, data: dict) -> bool:
    """canonical JSON으로 저장. 기존 내용과 동일하면 write skip → mtime 불변.
    반환: True=written, False=skipped
    """
    canonical = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            if path.read_text(encoding="utf-8") == canonical:
                return False
        except OSError:
            pass
    path.write_text(canonical, encoding="utf-8")
    return True


def write_status(log_name: str, status: str, success: int, fail: int) -> None:
    LOG_BASE.mkdir(parents=True, exist_ok=True)
    (LOG_BASE / f"{log_name}.status").write_text(
        f"{status}\nrun_at={now_iso()}\nsuccess={success}\nfail={fail}\n",
        encoding="utf-8",
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_env(key: str) -> str:
    return os.getenv(key, "")


def raw_dated_path(target: str, filename: str) -> Path:
    """data/raw/law_api/{target}/YYYY-MM-DD/{filename} 경로 반환."""
    return RAW_DATED_BASE / target / today_str() / filename


def save_raw_dated(target: str, filename: str, data: dict) -> Path:
    """날짜 경로 archived raw 저장 (pipeline 원본 파일과 별도)."""
    path = raw_dated_path(target, filename)
    save_json(path, data)
    return path


# ─── 공공데이터포털 GW API ──────────────────────────────────────────────────

GW_BASE_URL = "http://apis.data.go.kr/1170000"


def get_service_key() -> str:
    """DATA_GO_KR_SERVICE_KEY 반환. 없으면 LAW_API_KEY로 fallback (deprecated)."""
    key = get_env("DATA_GO_KR_SERVICE_KEY")
    if key:
        return key
    legacy = get_env("LAW_API_KEY")
    if legacy:
        import warnings
        warnings.warn(
            "LAW_API_KEY는 deprecated. DATA_GO_KR_SERVICE_KEY 사용 권장.",
            DeprecationWarning, stacklevel=2,
        )
    return legacy


def gw_request(
    endpoint: str,
    target: str,
    query: str,
    num_of_rows: int = 100,
    page_no: int = 1,
    service_key: str = "",
) -> dict:
    """공공데이터포털 GW API 호출 → XML 파싱 결과 반환.

    serviceKey는 data.go.kr 정책상 URL에 직접 삽입해야 함 (params= 방식은 재인코딩으로 502 발생).
    """
    from urllib.parse import quote
    retry_count = int(get_env("LAW_API_RETRY_COUNT") or 3)
    timeout     = int(get_env("LAW_API_TIMEOUT")     or 20)

    # serviceKey를 URL에 직접 삽입, 나머지 파라미터는 requests params=
    query_enc = quote(query, safe="")
    url = f"{endpoint}?serviceKey={service_key}&target={target}&query={query_enc}&numOfRows={num_of_rows}&pageNo={page_no}"

    last_err = ""
    for attempt in range(1, retry_count + 1):
        try:
            r = _requests.get(url, timeout=timeout)
            r.raise_for_status()
            return _parse_gw_xml(r.text, target)
        except Exception as e:
            last_err = str(e)
            if attempt < retry_count:
                _time.sleep(1.0 * attempt)

    return {"result_code": "99", "result_msg": last_err, "total_count": 0, "items": []}


def _parse_gw_xml(xml_text: str, item_tag: str) -> dict:
    try:
        root = ET.fromstring(xml_text)
        result_code = (_xml_text(root, "resultCode") or "00").strip()
        result_msg  = (_xml_text(root, "resultMsg")  or "success").strip()
        total_count = int(_xml_text(root, "totalCnt") or 0)
        items = []
        for elem in root.findall(item_tag):
            row = {child.tag: (child.text or "").strip() for child in elem}
            row["_id"] = elem.get("id", "")
            items.append(row)
        return {
            "result_code": result_code,
            "result_msg":  result_msg,
            "total_count": total_count,
            "items":       items,
        }
    except ET.ParseError as e:
        return {
            "result_code": "99",
            "result_msg":  f"XML parse error: {e}",
            "total_count": 0,
            "items":       [],
        }


def _xml_text(root: ET.Element, tag: str) -> str | None:
    elem = root.find(tag)
    return elem.text if elem is not None else None


def gw_collect_all(
    endpoint: str,
    target: str,
    query: str,
    service_key: str,
    log=None,
) -> dict:
    """
    단일 query 기준으로 전체 페이지 수집 후 items 집계.
    dry-run(service_key 없음) 시 즉시 반환.
    """
    if not service_key:
        return {"result_code": "dry_run", "result_msg": "no key", "total_count": 0, "items": []}

    num_of_rows = int(get_env("LAW_API_NUM_OF_ROWS") or 100)
    max_pages   = int(get_env("LAW_API_MAX_PAGES")   or 50)
    delay       = 1.0

    all_items: list[dict] = []
    last: dict = {}
    for page in range(1, max_pages + 1):
        last = gw_request(endpoint, target, query, num_of_rows, page, service_key)
        items = last.get("items", [])
        all_items.extend(items)
        total = last.get("total_count", 0)
        if log:
            log.info(f"  [{query}] p{page}: +{len(items)}건 / 누적 {len(all_items)}/{total}")
        if len(all_items) >= total or not items:
            break
        _time.sleep(delay)

    return {
        "result_code": last.get("result_code", "00"),
        "result_msg":  last.get("result_msg",  "success"),
        "total_count": last.get("total_count", len(all_items)),
        "items":       all_items,
    }


# ─── law.go.kr DRF API ────────────────────────────────────────────────────────
# 발급: https://www.law.go.kr/LSO/openApi/guideMain.do
# 환경변수: LAW_GO_KR_OC (없으면 dry-run)

DRF_BASE_URL = "https://www.law.go.kr/DRF"

# DRF 에러코드 (API 가이드 §4)
_DRF_ERROR_MAP = {
    "01": "인증키 오류",
    "02": "필수 파라미터 누락",
    "03": "데이터 없음",
    "09": "일시적 시스템 오류",
    "99": "기타 오류",
}

# DRF target → 검색 엔드포인트, JSON 응답 루트 키, 항목 키
_DRF_TARGET_META: dict[str, tuple[str, str, str]] = {
    "law":         ("lawSearch.do",    "LawSearch", "law"),
    "admrul":      ("admrulSearch.do", "LawSearch", "admrul"),
    "expc":        ("expcSearch.do",   "LawSearch", "expc"),
    "moelCgmExpc": ("lawSearch.do",   "CgmExpc",   "cgmExpc"),
}


def get_oc_key() -> str:
    """law.go.kr DRF OC 키 반환. 없으면 빈문자열 (dry-run)."""
    return get_env("LAW_GO_KR_OC") or get_env("LAW_API_KEY")


def drf_request(
    target: str,
    query: str,
    page: int = 1,
    display: int = 100,
    oc_key: str = "",
) -> dict:
    """law.go.kr DRF API 1 페이지 요청 → 파싱 결과 반환.

    에러코드 01/02/03/09/99 감지 및 반환.
    """
    if target not in _DRF_TARGET_META:
        return {"result_code": "02", "result_msg": f"unknown target: {target}", "total_count": 0, "items": []}

    endpoint_suffix, root_key, item_key = _DRF_TARGET_META[target]
    url = f"{DRF_BASE_URL}/{endpoint_suffix}"
    retry_count = int(get_env("LAW_API_RETRY_COUNT") or 3)
    timeout     = int(get_env("LAW_API_TIMEOUT")     or 20)

    last_err = ""
    for attempt in range(1, retry_count + 1):
        try:
            r = _requests.get(
                url,
                params={"OC": oc_key, "target": target, "type": "JSON",
                        "query": query, "page": page, "display": display},
                timeout=timeout,
            )
            r.raise_for_status()
            return _parse_drf_json(r.text, root_key, item_key)
        except Exception as e:
            last_err = str(e)
            if attempt < retry_count:
                _time.sleep(1.0 * attempt)

    return {"result_code": "99", "result_msg": last_err, "total_count": 0, "items": []}


def _parse_drf_json(text: str, root_key: str, item_key: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"result_code": "99", "result_msg": "JSON parse error", "total_count": 0, "items": []}

    # 에러 응답: {"LawSearch": {"errorCode": "01", ...}}
    root = data.get(root_key, data)
    err_code = str(root.get("errorCode", "") or root.get("resultCode", "")).strip()
    if err_code and err_code != "00" and err_code != "0":
        msg = _DRF_ERROR_MAP.get(err_code, root.get("errorMsg", "unknown"))
        return {"result_code": err_code, "result_msg": msg, "total_count": 0, "items": []}

    total = int(root.get("totalCnt", 0) or 0)
    raw_items = root.get(item_key, [])
    if isinstance(raw_items, dict):
        raw_items = [raw_items]

    items = []
    for i, item in enumerate(raw_items or []):
        row = {k: (v or "") for k, v in item.items()}
        row.setdefault("_id", str(i + 1))
        items.append(row)

    return {"result_code": "00", "result_msg": "success", "total_count": total, "items": items}


def drf_collect_all(
    target: str,
    query: str,
    oc_key: str,
    log=None,
) -> dict:
    """law.go.kr DRF 전체 페이지 수집.
    dry-run(oc_key 없음) 시 즉시 반환.
    에러코드 01/02/09는 즉시 중단. 03은 빈 결과.
    """
    if not oc_key:
        return {"result_code": "dry_run", "result_msg": "no OC key", "total_count": 0, "items": []}

    display   = int(get_env("LAW_API_NUM_OF_ROWS") or 100)
    max_pages = int(get_env("LAW_API_MAX_PAGES")   or 50)

    all_items: list[dict] = []
    last: dict = {}
    for page in range(1, max_pages + 1):
        last = drf_request(target, query, page, display, oc_key)
        code = last.get("result_code", "00")

        # 즉시 중단 에러
        if code in ("01", "02", "09", "99"):
            if log:
                log.error(f"  DRF [{query}] 중단: {code} — {last.get('result_msg')}")
            break

        # 데이터 없음 — 빈 결과로 정상 종료
        if code == "03":
            if log:
                log.info(f"  DRF [{query}] 결과 없음 (03)")
            break

        items = last.get("items", [])
        all_items.extend(items)
        total = last.get("total_count", 0)
        if log:
            log.info(f"  DRF [{query}] p{page}: +{len(items)}건 / 누적 {len(all_items)}/{total}")
        if len(all_items) >= total or not items:
            break
        _time.sleep(1.0)

    return {
        "result_code": last.get("result_code", "00"),
        "result_msg":  last.get("result_msg",  "success"),
        "total_count": last.get("total_count", len(all_items)),
        "items":       all_items,
    }


# ─── law.go.kr DRF 본문 수집 ──────────────────────────────────────────────────

def drf_service_get(
    target: str,
    doc_id: str,
    oc_key: str,
    content_type: str = "XML",
) -> dict:
    """
    law.go.kr/DRF/lawService.do 호출 → 본문 raw text 반환.

    target      : "law" | "admrul" | "expc"
    doc_id      : 법령일련번호(MST) 또는 행정규칙/해석례 일련번호
    oc_key      : LAW_GO_KR_OC 키
    content_type: "XML" (법령) | "HTML" (행정규칙·해석례)

    반환:
      {"ok": True,  "text": "...", "url": "..."}
      {"ok": False, "error": "...", "url": "..."}
    dry-run (oc_key 없음):
      {"ok": False, "error": "dry_run", "url": ""}
    """
    if not oc_key:
        return {"ok": False, "error": "dry_run", "url": ""}

    param_key = "MST" if target == "law" else "ID"
    url = f"{DRF_BASE_URL}/lawService.do"
    params = {"OC": oc_key, "target": target, param_key: doc_id,
              "type": content_type, "mobileYn": ""}

    retry_count = int(get_env("LAW_API_RETRY_COUNT") or 3)
    timeout     = int(get_env("LAW_API_TIMEOUT")     or 30)
    full_url    = f"{url}?OC={oc_key}&target={target}&{param_key}={doc_id}&type={content_type}"

    last_err = ""
    for attempt in range(1, retry_count + 1):
        try:
            r = _requests.get(url, params=params, timeout=timeout, verify=False)
            r.raise_for_status()
            if not r.text or len(r.text) < 50:
                return {"ok": False, "error": "empty_response", "url": full_url}
            return {"ok": True, "text": r.text, "url": full_url}
        except Exception as e:
            last_err = str(e)
            if attempt < retry_count:
                _time.sleep(2.0 * attempt)

    return {"ok": False, "error": last_err, "url": full_url}

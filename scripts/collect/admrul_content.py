"""
행정규칙 본문 수집 (target=admrul)

입력: data/risk_db/law_raw/admin_rules_index.json
출력:
  data/raw/law_content/admrul/YYYY-MM-DD/admrul_content.jsonl   (unified schema)
  data/raw/law_content/admrul/YYYY-MM-DD/admrul_content_meta.json

HTML 파싱: BeautifulSoup (html.parser). 없으면 raw HTML 저장 + has_text=False.
"""
import json
import time
from pathlib import Path

from ._base import (
    get_logger, get_oc_key,
    drf_service_get,
    save_json, write_status, now_iso, today_str, ROOT,
)

log = get_logger("admrul_content")

INDEX_PATH    = ROOT / "data/risk_db/law_raw/admin_rules_index.json"
OUT_DIR       = ROOT / "data/raw/law_content/admrul"
REQUEST_DELAY = 1.5

try:
    from bs4 import BeautifulSoup
    _BS4_OK = True
except ImportError:
    _BS4_OK = False
    log.warning("beautifulsoup4 미설치 — HTML 텍스트 추출 불가. has_text=False 저장.")


def _html_to_text(html: str) -> str:
    """HTML → 텍스트. bs4 없으면 빈 문자열."""
    if not _BS4_OK:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    # 불필요 태그 제거
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # 연속 공백 정리
    import re
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _fmt_date(raw: str) -> str | None:
    raw = (raw or "").strip().replace(".", "-")
    if len(raw) == 8 and raw.replace("-", "").isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return raw or None


def _make_record(item: dict, content_text: str, source_url: str) -> dict:
    rule_id   = item.get("행정규칙일련번호", "")
    title     = item.get("행정규칙명", "")
    pub_date  = item.get("발령일자", "")
    enf_date  = item.get("시행일자", "")
    ministry  = item.get("소관부처명", "")
    rule_type = item.get("행정규칙종류", "")
    rev_type  = item.get("제개정구분명", "")
    admrul_id = item.get("행정규칙ID", "")

    return {
        "doc_id":           f"admrul_{rule_id}",
        "source_type":      "admrul",
        "source_org":       "moleg",
        "title":            title,
        "content_raw":      content_text if content_text else None,
        "has_text":         bool(content_text),
        "attachment_url":   None,
        "source_url":       source_url,
        "published_at":     _fmt_date(pub_date),
        "collected_at":     now_iso(),
        # 법령 확장 필드
        "law_id":           admrul_id,
        "raw_id":           rule_id,
        "article_no":       None,
        "paragraph_no":     None,
        "law_type":         rule_type,
        "ministry":         ministry,
        "enforcement_date": _fmt_date(enf_date),
        "revision_type":    rev_type,
    }


def run() -> bool:
    oc_key = get_oc_key()
    log.info("=== 행정규칙 본문 수집 시작 (target=admrul) ===")

    if not INDEX_PATH.exists():
        log.error(f"인덱스 파일 없음: {INDEX_PATH}")
        return False

    with open(INDEX_PATH, encoding="utf-8") as f:
        index = json.load(f)
    items = index.get("items", [])
    log.info(f"인덱스 로드: {len(items)}건")

    today = today_str()
    out_dir = OUT_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "admrul_content.jsonl"
    meta_path  = out_dir / "admrul_content_meta.json"

    # 재실행 중복 방지
    done_ids: set[str] = set()
    if jsonl_path.exists():
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        done_ids.add(json.loads(line)["doc_id"])
                    except Exception:
                        pass
        log.info(f"이미 수집된 기록: {len(done_ids)}개")

    stats = {"total": len(items), "success": 0, "fail": 0,
             "has_text": 0, "no_text": 0}
    fail_list: list[dict] = []

    with open(jsonl_path, "a", encoding="utf-8") as out_f:
        for item in items:
            rule_id = item.get("행정규칙일련번호", "")
            name    = item.get("행정규칙명", "?")
            doc_id  = f"admrul_{rule_id}"

            if doc_id in done_ids:
                log.info(f"  [SKIP] {name[:40]}")
                stats["success"] += 1
                continue

            log.info(f"  [{name[:45]}] ID={rule_id}")
            result = drf_service_get("admrul", rule_id, oc_key, "HTML")

            if not result["ok"]:
                log.warning(f"  FAIL {name[:40]}: {result['error']}")
                stats["fail"] += 1
                fail_list.append({"id": rule_id, "name": name, "error": result["error"]})
                continue

            content_text = _html_to_text(result["text"])
            rec = _make_record(item, content_text, result["url"])
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            if rec["has_text"]:
                stats["has_text"] += 1
            else:
                stats["no_text"] += 1
                log.warning(f"  has_text=False (bs4 미설치 또는 빈 응답): {name[:40]}")

            log.info(f"  OK {name[:40]}: {len(content_text)}자")
            stats["success"] += 1
            time.sleep(REQUEST_DELAY)

    summary = {
        "collected_at": now_iso(),
        "index_date":   today,
        "stats":        stats,
        "fail_list":    fail_list,
        "output":       str(jsonl_path),
    }
    save_json(meta_path, summary)

    status = "SUCCESS" if stats["fail"] == 0 else ("PARTIAL" if stats["success"] > 0 else "FAIL")
    write_status("admrul_content", status, stats["success"], stats["fail"])
    log.info(f"=== 완료: {status} | {stats['success']}/{stats['total']}건 | "
             f"본문有: {stats['has_text']} 無: {stats['no_text']} ===")
    return stats["fail"] == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

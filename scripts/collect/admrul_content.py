"""
행정규칙 본문 수집 (target=admrul)

입력: data/risk_db/law_raw/admin_rules_index.json
출력:
  data/raw/law_content/admrul/YYYY-MM-DD/admrul_content.jsonl   (unified schema)
  data/raw/law_content/admrul/YYYY-MM-DD/admrul_content_meta.json

XML 파싱: DRF type=XML → <AdmRulService><조문내용> CDATA 합산.
HTML 응답은 JS/iframe 기반으로 텍스트 추출 불가 — XML 전용 사용.
"""
import json
import re
import time
import xml.etree.ElementTree as ET
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


def _parse_admrul_xml(xml_text: str) -> tuple[dict, str]:
    """
    행정규칙 XML → (기본정보 dict, 조문 전문 텍스트).
    <AdmRulService> → <행정규칙기본정보> + <조문내용> CDATA 목록.
    """
    root = ET.fromstring(xml_text)
    info_el = root.find("행정규칙기본정보")

    def _t(tag: str) -> str:
        el = info_el.find(tag) if info_el is not None else None
        return (el.text or "").strip() if el is not None else ""

    meta = {
        "rule_id":          _t("행정규칙일련번호"),
        "law_id":           _t("행정규칙ID"),
        "title":            _t("행정규칙명"),
        "law_type":         _t("행정규칙종류"),
        "ministry":         _t("소관부처명"),
        "enforcement_date": _t("시행일자"),
        "promulgation_date": _t("발령일자"),
        "revision_type":    _t("제개정구분명"),
    }

    # 조문내용 CDATA 전체 합산
    parts = []
    for el in root.findall("조문내용"):
        text = (el.text or "").strip()
        if text:
            parts.append(text)

    full_text = "\n".join(parts)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()
    return meta, full_text


def _fmt_date(raw: str) -> str | None:
    raw = (raw or "").strip().replace(".", "-")
    if len(raw) == 8 and raw.replace("-", "").isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return raw or None


def _make_record(item: dict, xml_meta: dict, content_text: str, source_url: str) -> dict:
    rule_id  = item.get("행정규칙일련번호", "")
    title    = item.get("행정규칙명", "")
    pub_date = item.get("발령일자", "")
    enf_date = item.get("시행일자", "")
    ministry = item.get("소관부처명", "")
    rule_type = item.get("행정규칙종류", "")
    rev_type  = item.get("제개정구분명", "")
    admrul_id = item.get("행정규칙ID", "")

    # XML에서 얻은 값이 있으면 우선 사용
    if xml_meta.get("title"):
        title = xml_meta["title"]
    if xml_meta.get("ministry"):
        ministry = xml_meta["ministry"]

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
    log.info("=== 행정규칙 본문 수집 시작 (target=admrul, type=XML) ===")

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
            result = drf_service_get("admrul", rule_id, oc_key, "XML")

            if not result["ok"]:
                log.warning(f"  FAIL {name[:40]}: {result['error']}")
                stats["fail"] += 1
                fail_list.append({"id": rule_id, "name": name, "error": result["error"]})
                continue

            try:
                xml_meta, content_text = _parse_admrul_xml(result["text"])
            except ET.ParseError as e:
                log.warning(f"  XML 파싱 오류 {name[:40]}: {e}")
                stats["fail"] += 1
                fail_list.append({"id": rule_id, "name": name, "error": f"xml_parse: {e}"})
                continue

            rec = _make_record(item, xml_meta, content_text, result["url"])
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            if rec["has_text"]:
                stats["has_text"] += 1
                log.info(f"  OK {name[:40]}: {len(content_text)}자")
            else:
                stats["no_text"] += 1
                log.warning(f"  has_text=False (조문내용 없음): {name[:40]}")

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

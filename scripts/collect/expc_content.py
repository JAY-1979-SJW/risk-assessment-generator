"""
법령해석례 본문 수집 (target=expc)

입력: data/risk_db/law_raw/expc_index.json
출력:
  data/raw/law_content/expc/YYYY-MM-DD/expc_content.jsonl   (unified schema)
  data/raw/law_content/expc/YYYY-MM-DD/expc_content_meta.json

XML 파싱: DRF type=XML → <ExpcService>
  <질의요지> + <회답> + <이유> CDATA 합산
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

log = get_logger("expc_content")

INDEX_PATH    = ROOT / "data/risk_db/law_raw/expc_index.json"
OUT_DIR       = ROOT / "data/raw/law_content/expc"
REQUEST_DELAY = 1.5


def _parse_expc_xml(xml_text: str) -> tuple[dict, str]:
    """
    법령해석례 XML → (기본정보 dict, 본문 텍스트).
    <ExpcService> → <질의요지> + <회답> + <이유> 합산.
    """
    root = ET.fromstring(xml_text)

    def _t(tag: str) -> str:
        el = root.find(tag)
        return (el.text or "").strip() if el is not None else ""

    meta = {
        "expc_id":     _t("법령해석례일련번호"),
        "title":       _t("안건명"),
        "case_no":     _t("안건번호"),
        "decided_at":  _t("해석일자"),
        "org":         _t("해석기관명"),
        "petitioner":  _t("질의기관명"),
    }

    parts = []
    for tag in ["질의요지", "회답", "이유"]:
        el = root.find(tag)
        text = (el.text or "").strip() if el is not None else ""
        if text:
            parts.append(f"[{tag}]\n{text}")

    full_text = "\n\n".join(parts)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()
    return meta, full_text


def _fmt_date(raw: str) -> str | None:
    raw = (raw or "").strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return raw or None


def _make_record(item: dict, xml_meta: dict, content_text: str, source_url: str) -> dict:
    expc_id = item.get("법령해석례일련번호", "")
    title   = xml_meta.get("title") or item.get("안건명", "")
    decided = xml_meta.get("decided_at") or item.get("회신일자", "")
    org     = xml_meta.get("org") or item.get("회신기관명", "")

    return {
        "doc_id":           f"expc_{expc_id}",
        "source_type":      "expc",
        "source_org":       "moleg",
        "title":            title,
        "content_raw":      content_text if content_text else None,
        "has_text":         bool(content_text),
        "attachment_url":   None,
        "source_url":       source_url,
        "published_at":     _fmt_date(decided),
        "collected_at":     now_iso(),
        "law_id":           None,
        "raw_id":           expc_id,
        "article_no":       None,
        "paragraph_no":     None,
        "law_type":         "expc",
        "ministry":         xml_meta.get("petitioner") or item.get("질의기관명", ""),
        "enforcement_date": None,
        "revision_type":    None,
    }


def run() -> bool:
    oc_key = get_oc_key()
    log.info("=== 법령해석례 본문 수집 시작 (target=expc, type=XML) ===")

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
    jsonl_path = out_dir / "expc_content.jsonl"
    meta_path  = out_dir / "expc_content_meta.json"

    done_ids: set[str] = set()
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").strip().splitlines():
            if line.strip():
                try:
                    done_ids.add(json.loads(line)["doc_id"])
                except Exception:
                    pass
        log.info(f"이미 수집된 기록: {len(done_ids)}개")

    stats = {"total": len(items), "success": 0, "fail": 0, "has_text": 0, "no_text": 0}
    fail_list: list[dict] = []

    with open(jsonl_path, "a", encoding="utf-8") as out_f:
        for item in items:
            expc_id = item.get("법령해석례일련번호", "")
            title   = item.get("안건명", "?")
            doc_id  = f"expc_{expc_id}"

            if doc_id in done_ids:
                log.info(f"  [SKIP] {title[:45]}")
                stats["success"] += 1
                continue

            log.info(f"  [{title[:50]}] ID={expc_id}")
            result = drf_service_get("expc", expc_id, oc_key, "XML")

            if not result["ok"]:
                log.warning(f"  FAIL {title[:40]}: {result['error']}")
                stats["fail"] += 1
                fail_list.append({"id": expc_id, "title": title, "error": result["error"]})
                continue

            try:
                xml_meta, content_text = _parse_expc_xml(result["text"])
            except ET.ParseError as e:
                log.warning(f"  XML 파싱 오류 {title[:40]}: {e}")
                stats["fail"] += 1
                fail_list.append({"id": expc_id, "title": title, "error": f"xml_parse: {e}"})
                continue

            rec = _make_record(item, xml_meta, content_text, result["url"])
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            if rec["has_text"]:
                stats["has_text"] += 1
                log.info(f"  OK {title[:40]}: {len(content_text)}자")
            else:
                stats["no_text"] += 1
                log.warning(f"  has_text=False: {title[:40]}")

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
    write_status("expc_content", status, stats["success"], stats["fail"])
    log.info(f"=== 완료: {status} | {stats['success']}/{stats['total']}건 | "
             f"본문有: {stats['has_text']} 無: {stats['no_text']} ===")
    return stats["fail"] == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

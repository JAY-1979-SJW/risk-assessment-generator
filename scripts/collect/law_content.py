"""
법령 본문 수집 (target=law)

입력: data/risk_db/law_raw/laws_index.json (MST 목록)
출력:
  data/raw/law_content/law/YYYY-MM-DD/law_content.jsonl   (unified schema, 조문 단위)
  data/raw/law_content/law/YYYY-MM-DD/law_content_meta.json (수집 결과 요약)

unified schema 참고: data/risk_db/collection_schema/unified_storage_schema.json
"""
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from ._base import (
    get_logger, get_oc_key,
    drf_service_get,
    save_json, write_status, now_iso, today_str, ROOT,
)

log = get_logger("law_content")

INDEX_PATH   = ROOT / "data/risk_db/law_raw/laws_index.json"
OUT_DIR      = ROOT / "data/raw/law_content/law"
REQUEST_DELAY = 1.5  # 서버 부하 방지


def _iter_text(elem: ET.Element) -> str:
    """Element 하위 모든 text를 재귀 결합."""
    parts = []
    if elem.text and elem.text.strip():
        parts.append(elem.text.strip())
    for child in elem:
        parts.append(_iter_text(child))
        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())
    return " ".join(p for p in parts if p)


def _parse_law_xml(xml_text: str, mst: str) -> tuple[dict, list[dict]]:
    """
    법령 XML → (기본정보 dict, 조문단위 list).
    조문단위 list 각 항목: {조문번호, 조문여부, 조문제목, content_raw}
    """
    root = ET.fromstring(xml_text)
    info_el = root.find("기본정보")

    def _t(tag: str) -> str:
        el = info_el.find(tag) if info_el is not None else None
        return (el.text or "").strip() if el is not None else ""

    meta = {
        "law_id":           _t("법령ID"),
        "title_ko":         _t("법령명_한글"),
        "law_type":         _t("법종구분"),
        "ministry":         _t("소관부처"),
        "enforcement_date": _t("시행일자"),
        "promulgation_date": _t("공포일자"),
        "revision_type":    _t("제개정구분"),
    }

    articles = []
    조문_el = root.find("조문")
    if 조문_el is None:
        return meta, articles

    for 단위 in 조문_el.findall("조문단위"):
        번호_el  = 단위.find("조문번호")
        여부_el  = 단위.find("조문여부")
        제목_el  = 단위.find("조문제목")
        내용_el  = 단위.find("조문내용")

        번호  = (번호_el.text  or "").strip() if 번호_el  is not None else ""
        여부  = (여부_el.text  or "").strip() if 여부_el  is not None else ""
        제목  = (제목_el.text  or "").strip() if 제목_el  is not None else ""
        내용  = (내용_el.text  or "").strip() if 내용_el  is not None else ""

        # 항/호/목 텍스트 추가 수집
        sub_texts = []
        for child in 단위:
            if child.tag in ("조문번호", "조문여부", "조문제목", "조문내용",
                             "조문시행일자", "조문이동이전", "조문이동이후", "조문변경여부"):
                continue
            t = _iter_text(child)
            if t:
                sub_texts.append(t)

        full_text = 내용
        if sub_texts:
            full_text = full_text + " " + " ".join(sub_texts)
        full_text = full_text.strip()

        articles.append({
            "article_no":   번호,
            "article_type": 여부,
            "article_title": 제목,
            "content_raw":  full_text,
        })

    return meta, articles


def _make_record(meta: dict, article: dict, mst: str, source_url: str, seq: int) -> dict:
    """통합 스키마 기준 단일 조문 레코드 생성. seq: 법령 내 0-based 순번."""
    art_no  = article["article_no"]
    art_title = article["article_title"]
    content = article["content_raw"]

    title_parts = [meta["title_ko"]]
    if art_no:
        title_parts.append(f"제{art_no}조")
    if art_title:
        title_parts.append(f"({art_title})")

    return {
        "doc_id":           f"law_{mst}_{seq:04d}",
        "source_type":      "law",
        "source_org":       "moleg",
        "title":            " ".join(title_parts),
        "content_raw":      content if content else None,
        "has_text":         bool(content),
        "attachment_url":   None,
        "source_url":       source_url,
        "published_at":     _fmt_date(meta.get("enforcement_date", "")),
        "collected_at":     now_iso(),
        # 법령 확장 필드
        "law_id":           meta.get("law_id", ""),
        "raw_id":           mst,
        "article_no":       f"제{art_no}조" if art_no else "",
        "paragraph_no":     None,
        "law_type":         meta.get("law_type", ""),
        "ministry":         meta.get("ministry", ""),
        "enforcement_date": _fmt_date(meta.get("enforcement_date", "")),
        "revision_type":    meta.get("revision_type", ""),
    }


def _fmt_date(raw: str) -> str | None:
    """YYYYMMDD → YYYY-MM-DD. 형식 아니면 None."""
    raw = raw.strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return raw or None


def run() -> bool:
    oc_key = get_oc_key()
    log.info("=== 법령 본문 수집 시작 (target=law) ===")

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
    jsonl_path = out_dir / "law_content.jsonl"
    meta_path  = out_dir / "law_content_meta.json"

    # 이미 수집된 doc_id 로드 (재실행 시 중복 방지)
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
             "articles_total": 0, "articles_has_text": 0}
    fail_list: list[dict] = []

    with open(jsonl_path, "a", encoding="utf-8") as out_f:
        for item in items:
            mst  = item.get("법령일련번호", "")
            name = item.get("법령명한글", item.get("법령명_한글", "?"))

            # 이미 수집된 법령이면 건너뜀 (첫 조문 doc_id 기준)
            if f"law_{mst}_0000" in done_ids:
                log.info(f"  [SKIP] {name} (MST={mst})")
                stats["success"] += 1
                continue

            log.info(f"  [{name}] MST={mst}")
            result = drf_service_get("law", mst, oc_key, "XML")

            if not result["ok"]:
                log.warning(f"  FAIL {name}: {result['error']}")
                stats["fail"] += 1
                fail_list.append({"mst": mst, "name": name, "error": result["error"]})
                continue

            try:
                meta, articles = _parse_law_xml(result["text"], mst)
            except ET.ParseError as e:
                log.warning(f"  XML 파싱 오류 {name}: {e}")
                stats["fail"] += 1
                fail_list.append({"mst": mst, "name": name, "error": f"xml_parse: {e}"})
                continue

            for seq, article in enumerate(articles):
                rec = _make_record(meta, article, mst, result["url"], seq)
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                stats["articles_total"] += 1
                if rec["has_text"]:
                    stats["articles_has_text"] += 1

            log.info(f"  OK {name}: {len(articles)}개 조문단위")
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
    write_status("law_content", status, stats["success"], stats["fail"])
    log.info(f"=== 완료: {status} | 법령 {stats['success']}/{stats['total']} | "
             f"조문 {stats['articles_total']}개 (본문有: {stats['articles_has_text']}) ===")
    return stats["fail"] == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

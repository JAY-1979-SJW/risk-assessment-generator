"""
전공종 핵심 법령 증분 수집기 — 누락 법령만 kras DB에 직접 upsert.

- 입력: 아래 TARGET_LAWS 하드코딩 목록 (MST 기준)
- 출력: documents (law_statute + law_article) + law_meta upsert
- 원칙: ON CONFLICT(source_type, source_id) DO UPDATE — 중복 삽입 없음
- 신규 row 삽입만. 총건수 증가는 새 법령 분만큼 허용.

text_quality/기술기준 metadata 태깅 기준 (5단계):
  metadata.related_trade    : 공종 (소방/전기/기계설비/건설공통 등)
  metadata.document_level   : law / decree / rule / technical_standard
  metadata.standard_family  : fire_safety_standard / electrical_standard 등 (해당 시만)

실행:
  python3 -m scripts.collect.collect_missing_laws
  python3 -m scripts.collect.collect_missing_laws --dry-run
  python3 -m scripts.collect.collect_missing_laws --only 소방시설공사업법
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from contextlib import closing
from typing import Optional

import psycopg2
from psycopg2.extras import execute_values

from ._base import get_logger, get_oc_key, drf_service_get, now_iso

log = get_logger("collect_missing_laws")

REQUEST_DELAY = 1.0

# ─── 수집 대상 목록 ───────────────────────────────────────────────────────────
# (law_name, MST, related_trade, document_level, standard_family_or_None)
TARGET_LAWS: list[tuple[str, str, str, str, Optional[str]]] = [
    # ── 소방 ──────────────────────────────────────────────────────────────────
    ("소방시설공사업법",            "259473", "소방", "law",    None),
    ("소방시설공사업법 시행령",      "284779", "소방", "decree", None),
    ("소방시설공사업법 시행규칙",    "282735", "소방", "rule",   None),
    # ── 기계설비 ──────────────────────────────────────────────────────────────
    ("기계설비법",                  "219239", "기계설비", "law",    None),
    ("기계설비법 시행령",            "280545", "기계설비", "decree", None),
    ("기계설비법 시행규칙",          "285589", "기계설비", "rule",   None),
    # ── 건축물 관리 / 철거·해체 ────────────────────────────────────────────────
    ("건축물관리법",                "266691", "건축", "law",    None),
    ("건축물관리법 시행령",          "284661", "건축", "decree", None),
    ("건축물관리법 시행규칙",        "271531", "건축", "rule",   None),
    # ── 수도 / 하수 ───────────────────────────────────────────────────────────
    ("수도법",                      "276757", "기계설비", "law",    None),
    ("수도법 시행령",                "281605", "기계설비", "decree", None),
    ("수도법 시행규칙",              "285093", "기계설비", "rule",   None),
    ("하수도법",                    "276803", "기계설비", "law",    None),
    ("하수도법 시행령",              "284903", "기계설비", "decree", None),
    ("하수도법 시행규칙",            "285059", "기계설비", "rule",   None),
    # ── 조경 ──────────────────────────────────────────────────────────────────
    ("조경진흥법",                  "277023", "조경", "law",    None),
    ("조경진흥법 시행령",            "204695", "조경", "decree", None),
    ("조경진흥법 시행규칙",          "179483", "조경", "rule",   None),
    # ── 에너지 ────────────────────────────────────────────────────────────────
    ("에너지이용 합리화법",          "280035", "기계설비", "law",    None),
    ("에너지이용 합리화법 시행령",   "278397", "기계설비", "decree", None),
    ("에너지이용 합리화법 시행규칙", "278965", "기계설비", "rule",   None),
    # ── 환경 ──────────────────────────────────────────────────────────────────
    ("환경영향평가법",              "276833", "환경", "law",    None),
    ("환경영향평가법 시행령",        "279237", "환경", "decree", None),
    ("환경영향평가법 시행규칙",      "279277", "환경", "rule",   None),
    ("물환경보전법",                "283441", "환경", "law",    None),
    ("물환경보전법 시행령",          "284747", "환경", "decree", None),
    ("토양환경보전법",              "281911", "환경", "law",    None),
    ("토양환경보전법 시행령",        "284891", "환경", "decree", None),
    ("건설폐기물의 재활용촉진에 관한 법률",       "276695", "환경", "law",    None),
    ("건설폐기물의 재활용촉진에 관한 법률 시행령","278497", "환경", "decree", None),
    # ── 정보통신 기술기준 ─────────────────────────────────────────────────────
    ("방송통신설비의 기술기준에 관한 규정", "263865", "정보통신", "technical_standard",
     "broadcast_comm_standard"),
]


# ─── DB 연결 ──────────────────────────────────────────────────────────────────

def _get_conn():
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "risk-assessment-db"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "kras"),
        user=os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "kras"),
        password=os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", ""),
    )


def _existing_source_ids(conn, mst: str) -> set[str]:
    """이미 수집된 source_id 집합 반환 (statute + articles)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source_id FROM documents WHERE source_type='law' AND source_id LIKE %s",
            (f"%{mst}%",),
        )
        return {r[0] for r in cur.fetchall()}


# ─── XML 파싱 ─────────────────────────────────────────────────────────────────

def _iter_text(elem: ET.Element) -> str:
    parts = []
    if elem.text and elem.text.strip():
        parts.append(elem.text.strip())
    for child in elem:
        parts.append(_iter_text(child))
        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())
    return " ".join(p for p in parts if p)


def _fmt_date(raw: str) -> Optional[str]:
    raw = (raw or "").strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return raw or None


def _parse_law_xml(xml_text: str, mst: str) -> tuple[dict, list[dict]]:
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
        "promulgation_date":_t("공포일자"),
        "revision_type":    _t("제개정구분"),
    }

    articles: list[dict] = []
    조문_el = root.find("조문")
    if 조문_el is None:
        return meta, articles

    for 단위 in 조문_el.findall("조문단위"):
        def _child_text(tag: str) -> str:
            el = 단위.find(tag)
            return (el.text or "").strip() if el is not None else ""

        번호  = _child_text("조문번호")
        여부  = _child_text("조문여부")
        제목  = _child_text("조문제목")
        내용  = _child_text("조문내용")

        sub_texts = []
        skip = {"조문번호","조문여부","조문제목","조문내용",
                "조문시행일자","조문이동이전","조문이동이후","조문변경여부"}
        for child in 단위:
            if child.tag not in skip:
                t = _iter_text(child)
                if t:
                    sub_texts.append(t)

        full_text = 내용
        if sub_texts:
            full_text = (full_text + " " + " ".join(sub_texts)).strip()
        full_text = re.sub(r"\s{3,}", "  ", full_text).strip()

        articles.append({
            "번호": 번호, "여부": 여부, "제목": 제목, "text": full_text,
        })

    return meta, articles


# ─── DB upsert ────────────────────────────────────────────────────────────────

def _upsert_statute(conn, mst: str, law_name: str, meta: dict,
                    trade: str, doc_level: str, std_family: Optional[str],
                    dry_run: bool) -> dict:
    """법령 단위 row (doc_category=law_statute) upsert."""
    now = now_iso()
    pub_date = _fmt_date(meta.get("promulgation_date", ""))
    enf_date = _fmt_date(meta.get("enforcement_date", ""))
    title    = meta.get("title_ko") or law_name
    metadata = {"related_trade": trade, "document_level": doc_level}
    if std_family:
        metadata["standard_family"] = std_family

    if dry_run:
        return {"mst": mst, "status": "dry_run_statute", "title": title}

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO documents
                (source_type, source_id, doc_category, title,
                 body_text, has_text, content_length, language, status,
                 published_at, collected_at, metadata)
            VALUES ('law', %s, 'law_statute', %s,
                    NULL, FALSE, 0, 'ko', 'active',
                    %s, %s, %s::jsonb)
            ON CONFLICT (source_type, source_id)
            DO UPDATE SET
                title      = EXCLUDED.title,
                published_at = COALESCE(EXCLUDED.published_at, documents.published_at),
                metadata   = documents.metadata || EXCLUDED.metadata,
                updated_at = now()
            RETURNING id
        """, (mst, title, enf_date or pub_date, now,
              __import__("json").dumps(metadata, ensure_ascii=False)))
        doc_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO law_meta (document_id, law_name, law_id, article_no,
                                  promulgation_date, effective_date, ministry, extra)
            VALUES (%s, %s, %s, '', %s, %s, %s, '{}'::jsonb)
            ON CONFLICT (document_id)
            DO UPDATE SET
                law_name         = EXCLUDED.law_name,
                effective_date   = COALESCE(EXCLUDED.effective_date, law_meta.effective_date),
                promulgation_date= COALESCE(EXCLUDED.promulgation_date, law_meta.promulgation_date),
                ministry         = COALESCE(NULLIF(EXCLUDED.ministry,''), law_meta.ministry)
        """, (doc_id, title, meta.get("law_id",""), pub_date, enf_date,
              meta.get("ministry","")))

    conn.commit()
    return {"mst": mst, "status": "statute_ok", "doc_id": doc_id, "title": title}


def _upsert_articles(conn, mst: str, law_name: str, meta: dict,
                     articles: list[dict], existing_ids: set[str],
                     trade: str, doc_level: str, std_family: Optional[str],
                     dry_run: bool) -> dict:
    """조문 단위 row 배치 upsert."""
    import json as _json
    now   = now_iso()
    title_ko = meta.get("title_ko") or law_name
    pub_date = _fmt_date(meta.get("promulgation_date", ""))
    enf_date = _fmt_date(meta.get("enforcement_date", ""))
    metadata = {"related_trade": trade, "document_level": doc_level}
    if std_family:
        metadata["standard_family"] = std_family
    metadata_json = _json.dumps(metadata, ensure_ascii=False)

    new_cnt = 0
    skipped = 0
    for seq, art in enumerate(articles):
        sid  = f"law_{mst}_{seq:04d}"
        번호  = art["번호"]
        제목  = art["제목"]
        text  = art["text"]

        title_parts = [title_ko]
        if 번호:
            title_parts.append(f"제{번호}조")
        if 제목:
            title_parts.append(f"({제목})")
        title = " ".join(title_parts)

        if sid in existing_ids:
            skipped += 1
            continue

        if dry_run:
            new_cnt += 1
            continue

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents
                    (source_type, source_id, doc_category, title,
                     body_text, has_text, content_length, language, status,
                     published_at, collected_at, metadata)
                VALUES ('law', %s, 'law_article', %s,
                        %s, %s, %s, 'ko', 'active',
                        %s, %s, %s::jsonb)
                ON CONFLICT (source_type, source_id)
                DO UPDATE SET
                    title          = EXCLUDED.title,
                    body_text      = COALESCE(EXCLUDED.body_text, documents.body_text),
                    has_text       = EXCLUDED.has_text,
                    content_length = EXCLUDED.content_length,
                    metadata       = documents.metadata || EXCLUDED.metadata,
                    updated_at     = now()
                RETURNING id
            """, (sid, title,
                  text or None, bool(text), len(text),
                  enf_date or pub_date, now, metadata_json))
            doc_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO law_meta (document_id, law_name, law_id, article_no,
                                      promulgation_date, effective_date, ministry, extra)
                VALUES (%s, %s, %s, %s, %s, %s, %s, '{}'::jsonb)
                ON CONFLICT (document_id)
                DO UPDATE SET
                    law_name  = EXCLUDED.law_name,
                    article_no= COALESCE(NULLIF(EXCLUDED.article_no,''), law_meta.article_no)
            """, (doc_id, title_ko, meta.get("law_id",""),
                  f"제{번호}조" if 번호 else "",
                  pub_date, enf_date, meta.get("ministry","")))
            new_cnt += 1

    if not dry_run:
        conn.commit()

    return {"new": new_cnt, "skipped": skipped, "total_articles": len(articles)}


# ─── 단건 처리 ────────────────────────────────────────────────────────────────

def _process_one(conn, entry: tuple, oc_key: str, dry_run: bool) -> dict:
    law_name, mst, trade, doc_level, std_family = entry

    existing = _existing_source_ids(conn, mst)
    statute_exists = mst in existing

    result = drf_service_get("law", mst, oc_key, "XML")
    if not result["ok"]:
        return {"law_name": law_name, "mst": mst, "status": f"fetch_fail:{result['error']}"}

    try:
        meta, articles = _parse_law_xml(result["text"], mst)
    except ET.ParseError as e:
        return {"law_name": law_name, "mst": mst, "status": f"parse_fail:{e}"}

    # law_statute row
    if not statute_exists:
        s_r = _upsert_statute(conn, mst, law_name, meta, trade, doc_level, std_family, dry_run)
    else:
        s_r = {"mst": mst, "status": "statute_skip"}

    # law_article rows
    a_r = _upsert_articles(conn, mst, law_name, meta, articles,
                           existing, trade, doc_level, std_family, dry_run)

    return {
        "law_name": law_name, "mst": mst,
        "trade": trade, "doc_level": doc_level,
        "statute": s_r.get("status"),
        "articles_new": a_r["new"],
        "articles_skip": a_r["skipped"],
        "articles_total": a_r["total_articles"],
        "status": "ok",
    }


# ─── run ──────────────────────────────────────────────────────────────────────

def run(only: list[str] | None = None, dry_run: bool = False) -> bool:
    oc_key = get_oc_key()
    if not oc_key:
        log.error("LAW_GO_KR_OC 미설정")
        return False

    targets = TARGET_LAWS
    if only:
        targets = [t for t in targets if t[0] in only]
        if not targets:
            log.error(f"--only 목록에 해당하는 법령 없음: {only}")
            return False

    log.info(f"=== 전공종 핵심 법령 증분 수집 시작 | {len(targets)}개 | dry_run={dry_run} ===")

    stats = {"total": len(targets), "ok": 0, "fail": 0,
             "articles_new": 0, "articles_skip": 0}
    results: list[dict] = []

    with closing(_get_conn()) as conn:
        for i, entry in enumerate(targets, 1):
            law_name = entry[0]
            log.info(f"  [{i}/{len(targets)}] {law_name} (MST={entry[1]})")
            r = _process_one(conn, entry, oc_key, dry_run)
            results.append(r)

            if r.get("status") == "ok":
                stats["ok"] += 1
                stats["articles_new"]  += r.get("articles_new", 0)
                stats["articles_skip"] += r.get("articles_skip", 0)
                log.info(f"    → articles +{r['articles_new']} (skip {r['articles_skip']}) "
                         f"| statute={r['statute']}")
            else:
                stats["fail"] += 1
                log.warning(f"    → FAIL: {r.get('status')}")

            time.sleep(REQUEST_DELAY)

    log.info(f"=== 완료: {stats} ===")
    log.info("=== 결과 요약 (성공만) ===")
    for r in results:
        if r.get("status") == "ok":
            log.info(f"  [{r['trade']}/{r['doc_level']}] {r['law_name']} "
                     f"| +{r['articles_new']}조문 | MST={r['mst']}")

    return stats["fail"] == 0


def _cli() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="+", default=None,
                    help="특정 법령명만 처리 (공백 포함 시 따옴표 사용)")
    args = ap.parse_args()
    return 0 if run(only=args.only, dry_run=args.dry_run) else 1


if __name__ == "__main__":
    sys.exit(_cli())

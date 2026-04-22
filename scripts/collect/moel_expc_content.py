"""
고용노동부 법령해석(moelCgmExpc) 본문 수집 — 샘플 단위 검증용 (1단계).

- 입력: kras DB  (documents WHERE source_type='moel_expc')
- 출력: 같은 documents 행의 body_text/content_length/has_text 업데이트
         + moel_expc_meta.text_quality 갱신
- API : law.go.kr  DRF  target=moelCgmExpc  type=XML
- 파서: <CgmExpcService> → <질의요지> + <회답> + <이유> CDATA 합산

text_quality 규칙 (단일 소스 오브 트루스):
    본문 길이 0        → 'title_only'
    본문 길이 1~299    → 'partial_body'
    본문 길이 300 이상 → 'full_body'

실행 예:
    python3 -m scripts.collect.moel_expc_content --limit 20 --mix
    python3 -m scripts.collect.moel_expc_content --source-id 237576

이번 단계에서는 9,573건 전량 배치를 돌리지 않는다. 인자 --all 없이는
기본 20건(최근 10 + 과거 10)만 처리한다.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from contextlib import closing
from typing import Iterable

import psycopg2
from psycopg2.extras import DictCursor

from ._base import get_logger, get_oc_key, drf_service_get, now_iso

log = get_logger("moel_expc_content")

DRF_TARGET    = "moelCgmExpc"
REQUEST_DELAY = 1.2

FULL_BODY_MIN = 300   # >= 300자 → full_body
PARTIAL_MIN   = 1     # 1~299자 → partial_body; 0자 → title_only


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


# ─── 샘플 선정 ────────────────────────────────────────────────────────────────

def _pick_sample_ids(conn, limit: int, mix: bool) -> list[str]:
    """
    mix=True  : 최근 limit/2 + 과거 limit/2 (interpreted_at 기준)
    mix=False : 최근 limit 건
    """
    half = max(1, limit // 2)
    with conn.cursor() as cur:
        if mix:
            cur.execute("""
                (SELECT d.source_id
                   FROM documents d
                   JOIN moel_expc_meta m ON m.document_id = d.id
                  WHERE d.source_type = 'moel_expc'
                    AND m.text_quality = 'title_only'
                  ORDER BY m.interpreted_at DESC NULLS LAST, d.id DESC
                  LIMIT %s)
                UNION ALL
                (SELECT d.source_id
                   FROM documents d
                   JOIN moel_expc_meta m ON m.document_id = d.id
                  WHERE d.source_type = 'moel_expc'
                    AND m.text_quality = 'title_only'
                  ORDER BY m.interpreted_at ASC NULLS LAST, d.id ASC
                  LIMIT %s)
            """, (half, limit - half))
        else:
            cur.execute("""
                SELECT d.source_id
                  FROM documents d
                  JOIN moel_expc_meta m ON m.document_id = d.id
                 WHERE d.source_type = 'moel_expc'
                   AND m.text_quality = 'title_only'
                 ORDER BY m.interpreted_at DESC NULLS LAST, d.id DESC
                 LIMIT %s
            """, (limit,))
        return [r[0] for r in cur.fetchall()]


# ─── XML 파싱 ─────────────────────────────────────────────────────────────────

def _parse_cgm_expc_xml(xml_text: str) -> tuple[dict, str]:
    """
    고용노동부 법령해석 XML → (기본정보 dict, 본문 텍스트).
    <CgmExpcService> 루트 — <질의요지> + <회답> + <이유> CDATA 합산.
    """
    root = ET.fromstring(xml_text)
    # 네임스페이스/예외 케이스 대비: root 태그가 다르면 그대로 진행 (필드 find는 실패하면 "")

    def _t(tag: str) -> str:
        el = root.find(tag)
        return (el.text or "").strip() if el is not None else ""

    meta = {
        "serial_no":      _t("법령해석일련번호"),
        "title":          _t("안건명"),
        "case_no":        _t("안건번호"),
        "interpreted_at": _t("해석일자"),
        "interpret_org":  _t("해석기관명"),
        "interpret_code": _t("해석기관코드"),
        "inquire_org":    _t("질의기관명"),
        "inquire_code":   _t("질의기관코드"),
        "data_std_dt":    _t("데이터기준일시"),
    }

    parts = []
    for tag in ("질의요지", "회답", "이유"):
        el = root.find(tag)
        text = (el.text or "").strip() if el is not None else ""
        if text:
            parts.append(f"[{tag}]\n{text}")

    body = "\n\n".join(parts)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return meta, body


def _classify_quality(body_len: int) -> str:
    if body_len >= FULL_BODY_MIN:
        return "full_body"
    if body_len >= PARTIAL_MIN:
        return "partial_body"
    return "title_only"


# ─── upsert ──────────────────────────────────────────────────────────────────

def _upsert(conn, source_id: str, meta: dict, body: str, dry_run: bool) -> dict:
    body_len = len(body)
    quality  = _classify_quality(body_len)

    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute(
            "SELECT id FROM documents WHERE source_type='moel_expc' AND source_id=%s",
            (source_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"source_id": source_id, "status": "not_found",
                    "body_len": body_len, "text_quality": quality}
        doc_id = row["id"]

        if dry_run:
            return {"source_id": source_id, "document_id": doc_id,
                    "status": "dry_run", "body_len": body_len,
                    "text_quality": quality, "title": meta.get("title", "")}

        cur.execute("""
            UPDATE documents
               SET body_text      = %s,
                   content_length = %s,
                   has_text       = %s,
                   updated_at     = now()
             WHERE id = %s
        """, (body or None, body_len, body_len > 0, doc_id))

        cur.execute("""
            UPDATE moel_expc_meta
               SET case_no        = COALESCE(NULLIF(%s,''),  case_no),
                   interpret_org  = COALESCE(NULLIF(%s,''),  interpret_org),
                   interpret_code = COALESCE(NULLIF(%s,''),  interpret_code),
                   inquire_org    = COALESCE(NULLIF(%s,''),  inquire_org),
                   inquire_code   = COALESCE(NULLIF(%s,''),  inquire_code),
                   interpreted_at = COALESCE(NULLIF(%s,''),  interpreted_at),
                   data_std_dt    = COALESCE(NULLIF(%s,''),  data_std_dt),
                   text_quality   = %s
             WHERE document_id = %s
        """, (
            meta.get("case_no", ""),
            meta.get("interpret_org", ""),
            meta.get("interpret_code", ""),
            meta.get("inquire_org", ""),
            meta.get("inquire_code", ""),
            meta.get("interpreted_at", ""),
            meta.get("data_std_dt", ""),
            quality,
            doc_id,
        ))
    conn.commit()
    return {"source_id": source_id, "document_id": doc_id, "status": "ok",
            "body_len": body_len, "text_quality": quality,
            "title": meta.get("title", "")}


# ─── 단건 처리 ────────────────────────────────────────────────────────────────

def _fetch_and_store(conn, source_id: str, oc_key: str, dry_run: bool) -> dict:
    result = drf_service_get(DRF_TARGET, source_id, oc_key, "XML")
    if not result["ok"]:
        log.warning(f"  FAIL fetch ID={source_id}: {result['error']}")
        return {"source_id": source_id, "status": f"fetch_fail:{result['error']}"}

    try:
        meta, body = _parse_cgm_expc_xml(result["text"])
    except ET.ParseError as e:
        log.warning(f"  FAIL parse ID={source_id}: {e}")
        return {"source_id": source_id, "status": f"parse_fail:{e}"}

    return _upsert(conn, source_id, meta, body, dry_run)


# ─── run ──────────────────────────────────────────────────────────────────────

def run(ids: Iterable[str], dry_run: bool) -> bool:
    oc_key = get_oc_key()
    if not oc_key:
        log.error("LAW_GO_KR_OC 미설정 — .env 확인")
        return False

    ids = list(ids)
    log.info(f"=== moel_expc 본문 수집 시작 | 대상 {len(ids)}건 | dry_run={dry_run} ===")

    stats = {"total": len(ids), "ok": 0, "full_body": 0,
             "partial_body": 0, "title_only_body": 0,
             "fetch_fail": 0, "parse_fail": 0, "not_found": 0}
    samples: list[dict] = []

    with closing(_get_conn()) as conn:
        for i, sid in enumerate(ids, 1):
            log.info(f"  [{i}/{len(ids)}] ID={sid}")
            r = _fetch_and_store(conn, sid, oc_key, dry_run)
            samples.append(r)

            status = r.get("status", "")
            if status == "ok" or status == "dry_run":
                stats["ok"] += 1
                q = r.get("text_quality", "")
                if q == "full_body":
                    stats["full_body"] += 1
                elif q == "partial_body":
                    stats["partial_body"] += 1
                else:
                    stats["title_only_body"] += 1
                log.info(f"    → len={r.get('body_len')} quality={q}")
            elif status.startswith("fetch_fail"):
                stats["fetch_fail"] += 1
            elif status.startswith("parse_fail"):
                stats["parse_fail"] += 1
            elif status == "not_found":
                stats["not_found"] += 1

            time.sleep(REQUEST_DELAY)

    log.info(f"=== 완료 @ {now_iso()} ===")
    log.info(f"stats = {stats}")
    log.info("=== 샘플 5건 예시 ===")
    for s in samples[:5]:
        log.info(f"  {s.get('source_id')} | {s.get('title','')[:30]} "
                 f"| len={s.get('body_len')} | {s.get('text_quality')} | {s.get('status')}")

    return stats["fetch_fail"] == 0 and stats["parse_fail"] == 0


def _cli() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20,
                    help="샘플 크기 (기본 20)")
    ap.add_argument("--mix", action="store_true",
                    help="최근/과거 혼합 (default off)")
    ap.add_argument("--source-id", action="append", default=[],
                    help="특정 source_id 직접 지정 (반복 허용)")
    ap.add_argument("--dry-run", action="store_true",
                    help="DB 갱신 없이 fetch/parse만 수행")
    args = ap.parse_args()

    if args.source_id:
        ids = args.source_id
    else:
        with closing(_get_conn()) as conn:
            ids = _pick_sample_ids(conn, args.limit, args.mix)
        if not ids:
            log.error("샘플 대상을 찾지 못했습니다.")
            return 1

    ok = run(ids, dry_run=args.dry_run)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_cli())

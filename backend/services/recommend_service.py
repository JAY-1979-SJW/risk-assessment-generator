"""
서식 추천 서비스 — scripts/engine/recommend_forms.py 의 랭킹 로직을
백엔드 컨테이너에서 직접 사용할 수 있도록 이식.

점수 규칙 (scripts/engine/recommend_forms.py 와 동일)
    hazard_match    가중치 3
    work_type_match 가중치 2
    form_type_match 가중치 2
    law_match       가중치 1
    frequency       가중치 1 (문서가 보유한 전체 매핑 수 기반, 0~2 정규화)

대상 소스 (기본)
    kosha_form, moel_form, licbyl

원칙
    - SQL/점수체계 변경 없음
    - law source 는 추천 대상이 아님 (매칭 근거)
"""
from __future__ import annotations

import psycopg2.extras

from db import get_conn


DEFAULT_SOURCES = ("kosha_form", "moel_form", "licbyl")

W_HAZARD = 3
W_WORK = 2
W_FORM = 2
W_LAW = 1
W_FREQ = 1

MAX_TOP_N = 50
BODY_PREVIEW_CHARS = 160


def _clean_list(items: list[str] | None) -> list[str]:
    if not items:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for v in items:
        if not isinstance(v, str):
            continue
        s = v.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _clean_form_type(v: str | None) -> str | None:
    if v is None:
        return None
    s = v.strip()
    return s or None


def recommend_forms(
    hazards: list[str] | None = None,
    work_types: list[str] | None = None,
    form_type: str | None = None,
    laws: list[str] | None = None,
    top_n: int = 10,
    sources: tuple[str, ...] = DEFAULT_SOURCES,
) -> dict:
    """
    추천 결과 dict 반환.
    { "items": [...], "meta": { "top_n": int, "total_candidates": int, "query": {...} } }
    """
    hazards = _clean_list(hazards)
    work_types = _clean_list(work_types)
    laws = _clean_list(laws)
    form_type = _clean_form_type(form_type)

    if top_n <= 0:
        raise ValueError("top_n must be > 0")
    top_n = min(top_n, MAX_TOP_N)

    if not (hazards or work_types or laws or form_type):
        raise ValueError("At least one of hazards/work_types/laws/form_type must be provided")

    params = {
        "hazards": hazards,
        "work_types": work_types,
        "law_names": laws,
        "form_type": form_type,
        "sources": list(sources),
        "top_n": top_n,
        "w_hazard": W_HAZARD,
        "w_work": W_WORK,
        "w_form": W_FORM,
        "w_law": W_LAW,
        "w_freq": W_FREQ,
        "preview_chars": BODY_PREVIEW_CHARS,
    }

    sql = """
    WITH
    cand AS (
        SELECT DISTINCT document_id AS doc_id
          FROM document_hazard_map
         WHERE hazard_code = ANY(%(hazards)s)
        UNION
        SELECT DISTINCT document_id
          FROM document_work_type_map
         WHERE work_type_code = ANY(%(work_types)s)
        UNION
        SELECT DISTINCT document_id
          FROM document_law_map
         WHERE law_name = ANY(%(law_names)s)
    ),
    cand_ft AS (
        SELECT id AS doc_id
          FROM documents
         WHERE %(form_type)s IS NOT NULL
           AND metadata->>'form_type' = %(form_type)s
           AND source_type = ANY(%(sources)s)
    ),
    cand_all AS (
        SELECT doc_id FROM cand
        UNION
        SELECT doc_id FROM cand_ft
    ),
    hz AS (
        SELECT document_id AS doc_id,
               COUNT(*) AS cnt,
               array_agg(hazard_code) AS codes
          FROM document_hazard_map
         WHERE hazard_code = ANY(%(hazards)s)
         GROUP BY document_id
    ),
    wt AS (
        SELECT document_id AS doc_id,
               COUNT(*) AS cnt,
               array_agg(work_type_code) AS codes
          FROM document_work_type_map
         WHERE work_type_code = ANY(%(work_types)s)
         GROUP BY document_id
    ),
    lw AS (
        SELECT dlm.document_id AS doc_id,
               COUNT(DISTINCT dlm.law_name) AS cnt,
               array_agg(DISTINCT
                   CASE
                     WHEN dlm.match_type = 'article' AND lm.article_no IS NOT NULL
                       THEN dlm.law_name || ' ' || lm.article_no
                     ELSE dlm.law_name
                   END
               ) AS names
          FROM document_law_map dlm
          LEFT JOIN law_meta lm ON lm.document_id = dlm.law_document_id
         WHERE dlm.law_name = ANY(%(law_names)s)
         GROUP BY dlm.document_id
    ),
    freq AS (
        SELECT doc_id, SUM(n) AS total FROM (
            SELECT document_id AS doc_id, COUNT(*) AS n FROM document_hazard_map     GROUP BY document_id
            UNION ALL
            SELECT document_id,           COUNT(*)       FROM document_work_type_map GROUP BY document_id
            UNION ALL
            SELECT document_id,           COUNT(*)       FROM document_law_map       GROUP BY document_id
            UNION ALL
            SELECT document_id,           COUNT(*)       FROM document_equipment_map GROUP BY document_id
        ) x GROUP BY doc_id
    ),
    freq_norm AS (
        SELECT doc_id,
               CASE WHEN (SELECT MAX(total) FROM freq) > 0
                    THEN ROUND( (total::float / (SELECT MAX(total) FROM freq)) * 2 )::int
                    ELSE 0
               END AS score
          FROM freq
    )
    SELECT d.id                                  AS document_id,
           d.source_type                         AS source_type,
           d.source_id                           AS source_id,
           d.title                               AS title,
           d.doc_category                        AS doc_category,
           d.metadata->>'form_type'              AS form_type,
           d.hwpx_path                           AS hwpx_path,
           d.pdf_path                            AS pdf_path,
           LEFT(COALESCE(d.body_text, ''), %(preview_chars)s) AS body_preview,
           COALESCE(hz.cnt, 0) * %(w_hazard)s    AS hazard_score,
           COALESCE(wt.cnt, 0) * %(w_work)s      AS work_type_score,
           (CASE WHEN %(form_type)s IS NOT NULL
                  AND d.metadata->>'form_type' = %(form_type)s
                 THEN 1 ELSE 0 END) * %(w_form)s AS form_type_score,
           COALESCE(lw.cnt, 0) * %(w_law)s       AS law_score,
           COALESCE(fn.score, 0) * %(w_freq)s    AS frequency_score,
           (COALESCE(hz.cnt, 0) * %(w_hazard)s
          + COALESCE(wt.cnt, 0) * %(w_work)s
          + (CASE WHEN %(form_type)s IS NOT NULL
                   AND d.metadata->>'form_type' = %(form_type)s
                  THEN 1 ELSE 0 END) * %(w_form)s
          + COALESCE(lw.cnt, 0) * %(w_law)s
          + COALESCE(fn.score, 0) * %(w_freq)s)  AS score,
           COALESCE(hz.codes, ARRAY[]::varchar[]) AS hazard_matches,
           COALESCE(wt.codes, ARRAY[]::varchar[]) AS work_type_matches,
           COALESCE(lw.names, ARRAY[]::text[])    AS law_matches
      FROM cand_all c
      JOIN documents d ON d.id = c.doc_id
 LEFT JOIN hz         ON hz.doc_id = c.doc_id
 LEFT JOIN wt         ON wt.doc_id = c.doc_id
 LEFT JOIN lw         ON lw.doc_id = c.doc_id
 LEFT JOIN freq_norm fn ON fn.doc_id = c.doc_id
     WHERE d.source_type = ANY(%(sources)s)
     ORDER BY score DESC, d.id ASC
     LIMIT %(top_n)s
    """

    count_sql = """
    WITH
    cand AS (
        SELECT DISTINCT document_id AS doc_id FROM document_hazard_map
         WHERE hazard_code = ANY(%(hazards)s)
        UNION
        SELECT DISTINCT document_id FROM document_work_type_map
         WHERE work_type_code = ANY(%(work_types)s)
        UNION
        SELECT DISTINCT document_id FROM document_law_map
         WHERE law_name = ANY(%(law_names)s)
    ),
    cand_ft AS (
        SELECT id AS doc_id FROM documents
         WHERE %(form_type)s IS NOT NULL
           AND metadata->>'form_type' = %(form_type)s
           AND source_type = ANY(%(sources)s)
    )
    SELECT COUNT(*) FROM (
        SELECT doc_id FROM cand
        UNION
        SELECT doc_id FROM cand_ft
    ) c
    JOIN documents d ON d.id = c.doc_id
    WHERE d.source_type = ANY(%(sources)s)
    """

    items: list[dict] = []
    total_candidates = 0
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            for row in cur.fetchall():
                d = dict(row)
                d["hazard_matches"] = list(d.get("hazard_matches") or [])
                d["work_type_matches"] = list(d.get("work_type_matches") or [])
                d["law_matches"] = list(d.get("law_matches") or [])
                for k in ("hazard_score", "work_type_score", "form_type_score",
                          "law_score", "frequency_score", "score"):
                    d[k] = int(d.get(k) or 0)
                items.append({
                    "document_id": int(d["document_id"]),
                    "source_type": d["source_type"],
                    "source_id": d["source_id"],
                    "title": d["title"],
                    "doc_category": d["doc_category"],
                    "form_type": d["form_type"],
                    "hwpx_path": d["hwpx_path"],
                    "pdf_path": d["pdf_path"],
                    "body_preview": d["body_preview"],
                    "score": d["score"],
                    "hazard_matches": d["hazard_matches"],
                    "work_type_matches": d["work_type_matches"],
                    "law_matches": d["law_matches"],
                    "detail": {
                        "hazard_score": d["hazard_score"],
                        "work_type_score": d["work_type_score"],
                        "form_type_score": d["form_type_score"],
                        "law_score": d["law_score"],
                        "frequency_score": d["frequency_score"],
                    },
                })
        with conn.cursor() as cur:
            cur.execute(count_sql, params)
            r = cur.fetchone()
            total_candidates = int(r[0]) if r else 0

    return {
        "items": items,
        "meta": {
            "top_n": top_n,
            "total_candidates": total_candidates,
            "query": {
                "hazards": hazards,
                "work_types": work_types,
                "form_type": form_type,
                "laws": laws,
            },
        },
    }

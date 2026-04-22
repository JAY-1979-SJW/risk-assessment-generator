"""
서식/문서 추천 엔진 — 랭킹 로직.

입력
    hazards      : list[str]  예) ['추락', '감전']
    work_types   : list[str]  예) ['고소작업', '용접']
    form_type    : str | None 예) 'risk_assessment'
    law_names    : list[str]  예) ['산업안전보건법']
    top_n        : int        기본 10
    sources      : tuple[str] 기본 ('kosha_form','moel_form','licbyl')

점수 (가중치)
    hazard_match        * 3   (문서의 hazard ∩ 입력 hazard 개수)
    work_type_match     * 2   (문서의 work_type ∩ 입력 work_type 개수)
    form_type_match     * 2   (문서의 form_type == 입력 form_type)
    law_match           * 1   (문서의 law_name ∩ 입력 law_name 개수)
    frequency           * 1   (문서가 보유한 총 매핑 수 — 인기도 대리값)

반환
    [
      {
        "doc_id": 1234,
        "title": "...",
        "source_type": "kosha_form",
        "form_type": "risk_assessment",
        "hazard_score": 6, "work_score": 4, "form_score": 2,
        "law_score": 1,    "freq_score": 3,
        "total_score": 16,
        "matched_hazards":  ["추락"],
        "matched_work_types": ["고소작업"],
        "matched_laws":     ["산업안전보건법"],
      },
      ...
    ]

CLI
    python scripts/engine/recommend_forms.py --hazards 추락,감전 --work-types 고소작업 --form-type risk_assessment --top 10
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    for env in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env.exists():
            load_dotenv(env, override=False)


def get_db_connection():
    import psycopg2  # type: ignore
    _load_dotenv()
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    database = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    if not (host and database and user):
        raise RuntimeError("DB 접속 정보 누락")
    return psycopg2.connect(
        host=host, port=int(port), dbname=database, user=user, password=password or ""
    )


DEFAULT_SOURCES = ("kosha_form", "moel_form", "licbyl")

W_HAZARD = 3
W_WORK = 2
W_FORM = 2
W_LAW = 1
W_FREQ = 1


def recommend(
    conn,
    hazards: list[str] | None = None,
    work_types: list[str] | None = None,
    form_type: str | None = None,
    law_names: list[str] | None = None,
    top_n: int = 10,
    sources: tuple[str, ...] = DEFAULT_SOURCES,
) -> list[dict]:
    hazards = list(hazards or [])
    work_types = list(work_types or [])
    law_names = list(law_names or [])

    # 입력이 전부 비어있으면 의미 없음
    if not (hazards or work_types or form_type or law_names):
        return []

    sql = """
    WITH
    -- 입력과 매핑이 있는 후보 문서 집합
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
    -- form_type 만 주어진 경우에도 후보 확보 (hazards/work_types 가 비었을 때)
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
    -- hazard 매칭
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
        SELECT document_id AS doc_id,
               COUNT(DISTINCT law_name) AS cnt,
               array_agg(DISTINCT law_name) AS names
          FROM document_law_map
         WHERE law_name = ANY(%(law_names)s)
         GROUP BY document_id
    ),
    -- frequency: 문서가 보유한 전체 매핑 개수 (인기도 대리값)
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
        -- 0~1 정규화 후 반올림 점수(0~2). top_n 비교 안정성 위해 정수화.
        SELECT doc_id,
               CASE WHEN (SELECT MAX(total) FROM freq) > 0
                    THEN ROUND( (total::float / (SELECT MAX(total) FROM freq)) * 2 )::int
                    ELSE 0
               END AS score
          FROM freq
    )
    SELECT d.id,
           d.title,
           d.source_type,
           d.metadata->>'form_type' AS form_type,
           COALESCE(hz.cnt, 0) * %(w_hazard)s AS hazard_score,
           COALESCE(wt.cnt, 0) * %(w_work)s   AS work_score,
           (CASE WHEN %(form_type)s IS NOT NULL
                  AND d.metadata->>'form_type' = %(form_type)s
                 THEN 1 ELSE 0 END) * %(w_form)s AS form_score,
           COALESCE(lw.cnt, 0) * %(w_law)s AS law_score,
           COALESCE(fn.score, 0) * %(w_freq)s AS freq_score,
           (COALESCE(hz.cnt, 0) * %(w_hazard)s
          + COALESCE(wt.cnt, 0) * %(w_work)s
          + (CASE WHEN %(form_type)s IS NOT NULL
                   AND d.metadata->>'form_type' = %(form_type)s
                  THEN 1 ELSE 0 END) * %(w_form)s
          + COALESCE(lw.cnt, 0) * %(w_law)s
          + COALESCE(fn.score, 0) * %(w_freq)s) AS total_score,
           COALESCE(hz.codes, ARRAY[]::varchar[]) AS matched_hazards,
           COALESCE(wt.codes, ARRAY[]::varchar[]) AS matched_work_types,
           COALESCE(lw.names, ARRAY[]::text[])   AS matched_laws
      FROM cand_all c
      JOIN documents d ON d.id = c.doc_id
 LEFT JOIN hz         ON hz.doc_id = c.doc_id
 LEFT JOIN wt         ON wt.doc_id = c.doc_id
 LEFT JOIN lw         ON lw.doc_id = c.doc_id
 LEFT JOIN freq_norm fn ON fn.doc_id = c.doc_id
     WHERE d.source_type = ANY(%(sources)s)
     ORDER BY total_score DESC, d.id ASC
     LIMIT %(top_n)s
    """

    params = {
        "hazards": hazards,
        "work_types": work_types,
        "law_names": law_names,
        "form_type": form_type,
        "sources": list(sources),
        "top_n": top_n,
        "w_hazard": W_HAZARD,
        "w_work": W_WORK,
        "w_form": W_FORM,
        "w_law": W_LAW,
        "w_freq": W_FREQ,
    }

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    out: list[dict] = []
    for r in rows:
        (
            doc_id, title, source_type, ft,
            hazard_score, work_score, form_score, law_score, freq_score, total,
            matched_h, matched_w, matched_l,
        ) = r
        out.append({
            "doc_id": int(doc_id),
            "title": title,
            "source_type": source_type,
            "form_type": ft,
            "hazard_score": int(hazard_score),
            "work_score": int(work_score),
            "form_score": int(form_score),
            "law_score": int(law_score),
            "freq_score": int(freq_score),
            "total_score": int(total),
            "matched_hazards": list(matched_h or []),
            "matched_work_types": list(matched_w or []),
            "matched_laws": list(matched_l or []),
        })
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _split_csv(s: str | None) -> list[str]:
    if not s:
        return []
    return [t.strip() for t in s.split(",") if t.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hazards", type=str, default="", help="쉼표구분. 예) 추락,감전")
    ap.add_argument("--work-types", type=str, default="", help="쉼표구분")
    ap.add_argument("--form-type", type=str, default=None)
    ap.add_argument("--laws", type=str, default="", help="쉼표구분 법령명")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--sources", type=str, default=",".join(DEFAULT_SOURCES))
    ap.add_argument("--format", choices=("json", "table"), default="table")
    args = ap.parse_args()

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 3
    try:
        results = recommend(
            conn,
            hazards=_split_csv(args.hazards),
            work_types=_split_csv(args.work_types),
            form_type=args.form_type,
            law_names=_split_csv(args.laws),
            top_n=args.top,
            sources=tuple(_split_csv(args.sources)) or DEFAULT_SOURCES,
        )
    finally:
        conn.close()

    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    # table
    print(
        f"{'#':<3} {'total':>5} {'hz':>3} {'wt':>3} {'ft':>3} {'lw':>3} {'fq':>3} "
        f"{'source':<11} {'form_type':<20} title"
    )
    print("-" * 120)
    for i, r in enumerate(results, 1):
        title = (r["title"] or "")[:70]
        print(
            f"{i:<3} {r['total_score']:>5} "
            f"{r['hazard_score']:>3} {r['work_score']:>3} {r['form_score']:>3} "
            f"{r['law_score']:>3} {r['freq_score']:>3} "
            f"{r['source_type']:<11} {(r['form_type'] or ''):<20} {title}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

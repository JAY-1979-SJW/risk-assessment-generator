"""
build_kosha_context_index.py — KOSHA 컨텍스트 인덱스 적재기 v1.0

kosha_material_classifications(2,047건) + kosha_material_chunks를 결합해
kosha_context_index에 적재한다. 위험성평가 엔진의 검색용 read-only 인덱스.

Usage:
    python scripts/build_kosha_context_index.py --dry-run
    python scripts/build_kosha_context_index.py --apply [--rebuild] [--limit N]
    python scripts/build_kosha_context_index.py --report
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CLASSIFIER_VERSION = "v1.0"
CHUNK_TEXT_PREVIEW = 800   # search_text에 포함할 chunk 앞부분 길이
SEARCH_TEXT_MAX    = 1200  # search_text 최대 길이

# ── DB ───────────────────────────────────────────────────────────────────────

def get_conn():
    url = (
        os.getenv("COMMON_DATA_URL")
        or os.getenv("KRAS_DB_URL")
        or os.getenv("DATABASE_URL")
    )
    if not url:
        env_file = ROOT / "scraper" / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("COMMON_DATA_URL="):
                    url = line.split("=", 1)[1].strip()
                    break
    if not url:
        sys.exit("[ERROR] COMMON_DATA_URL 환경변수 또는 scraper/.env 가 필요합니다.")
    return psycopg2.connect(url, connect_timeout=10)


# ── context_score 계산 ────────────────────────────────────────────────────────

def calc_score(cls: dict) -> float:
    score = 0.0
    if cls.get("kosha_guide_code"):
        score += 0.25
    if cls.get("hazard_tags") and cls["hazard_tags"] != "[]":
        score += 0.25
    if cls.get("work_type_tags") and cls["work_type_tags"] != "[]":
        score += 0.20
    if cls.get("equipment_tags") and cls["equipment_tags"] != "[]":
        score += 0.15
    if cls.get("primary_industry") == "construction":
        score += 0.10
    confidence = float(cls.get("confidence") or 0)
    score += confidence * 0.05
    return round(min(score, 1.0), 4)


def text_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def build_search_text(title: str, cls: dict, chunk_text: str) -> str:
    parts = [title or ""]
    if cls.get("kosha_guide_code"):
        parts.append(cls["kosha_guide_code"])
    for tag_field in ("hazard_tags", "work_type_tags", "equipment_tags"):
        try:
            tags = json.loads(cls.get(tag_field) or "[]")
            parts.extend(tags)
        except Exception:
            pass
    if chunk_text:
        parts.append(chunk_text[:CHUNK_TEXT_PREVIEW])
    combined = " ".join(parts)
    return combined[:SEARCH_TEXT_MAX]


# ── 데이터 조회 ───────────────────────────────────────────────────────────────

FETCH_CHUNKS_SQL = """
SELECT
    cls.id          AS cls_id,
    cls.material_id,
    cls.file_id,
    cls.source_type,
    cls.primary_industry,
    cls.kosha_guide_code,
    cls.kosha_guide_group,
    cls.kosha_guide_group_name,
    cls.safety_domain,
    cls.document_type,
    cls.hazard_tags::text      AS hazard_tags,
    cls.work_type_tags::text   AS work_type_tags,
    cls.equipment_tags::text   AS equipment_tags,
    cls.confidence,
    cls.classifier_version,
    m.title,
    c.id            AS chunk_id,
    c.chunk_index,
    COALESCE(c.normalized_text, c.raw_text) AS chunk_text
FROM kosha_material_classifications cls
JOIN kosha_materials m ON m.id = cls.material_id
JOIN kosha_material_chunks c ON c.file_id = cls.file_id
ORDER BY cls.file_id, c.chunk_index
"""

FETCH_FALLBACK_SQL = """
SELECT
    cls.id          AS cls_id,
    cls.material_id,
    cls.file_id,
    cls.source_type,
    cls.primary_industry,
    cls.kosha_guide_code,
    cls.kosha_guide_group,
    cls.kosha_guide_group_name,
    cls.safety_domain,
    cls.document_type,
    cls.hazard_tags::text      AS hazard_tags,
    cls.work_type_tags::text   AS work_type_tags,
    cls.equipment_tags::text   AS equipment_tags,
    cls.confidence,
    cls.classifier_version,
    m.title,
    f.raw_text      AS chunk_text
FROM kosha_material_classifications cls
JOIN kosha_materials m ON m.id = cls.material_id
JOIN kosha_material_files f ON f.id = cls.file_id
LEFT JOIN kosha_material_chunks c ON c.file_id = cls.file_id
WHERE c.id IS NULL
ORDER BY cls.file_id
"""

UPSERT_CHUNK_SQL = """
INSERT INTO kosha_context_index
    (material_id, file_id, chunk_id, chunk_index, title,
     source_type, primary_industry,
     kosha_guide_code, kosha_guide_group, kosha_guide_group_name,
     safety_domain, document_type,
     hazard_tags, work_type_tags, equipment_tags,
     chunk_text, chunk_text_hash, search_text,
     context_score, confidence, classifier_version,
     is_fallback, indexed_at)
VALUES
    (%(material_id)s, %(file_id)s, %(chunk_id)s, %(chunk_index)s, %(title)s,
     %(source_type)s, %(primary_industry)s,
     %(kosha_guide_code)s, %(kosha_guide_group)s, %(kosha_guide_group_name)s,
     %(safety_domain)s, %(document_type)s,
     %(hazard_tags)s::jsonb, %(work_type_tags)s::jsonb, %(equipment_tags)s::jsonb,
     %(chunk_text)s, %(chunk_text_hash)s, %(search_text)s,
     %(context_score)s, %(confidence)s, %(classifier_version)s,
     %(is_fallback)s, NOW())
ON CONFLICT (chunk_id) DO UPDATE SET
    title                = EXCLUDED.title,
    primary_industry     = EXCLUDED.primary_industry,
    kosha_guide_code     = EXCLUDED.kosha_guide_code,
    kosha_guide_group    = EXCLUDED.kosha_guide_group,
    kosha_guide_group_name = EXCLUDED.kosha_guide_group_name,
    safety_domain        = EXCLUDED.safety_domain,
    document_type        = EXCLUDED.document_type,
    hazard_tags          = EXCLUDED.hazard_tags,
    work_type_tags       = EXCLUDED.work_type_tags,
    equipment_tags       = EXCLUDED.equipment_tags,
    chunk_text           = EXCLUDED.chunk_text,
    chunk_text_hash      = EXCLUDED.chunk_text_hash,
    search_text          = EXCLUDED.search_text,
    context_score        = EXCLUDED.context_score,
    confidence           = EXCLUDED.confidence,
    classifier_version   = EXCLUDED.classifier_version,
    indexed_at           = NOW()
"""

UPSERT_FALLBACK_SQL = """
INSERT INTO kosha_context_index
    (material_id, file_id, chunk_id, chunk_index, title,
     source_type, primary_industry,
     kosha_guide_code, kosha_guide_group, kosha_guide_group_name,
     safety_domain, document_type,
     hazard_tags, work_type_tags, equipment_tags,
     chunk_text, chunk_text_hash, search_text,
     context_score, confidence, classifier_version,
     is_fallback, indexed_at)
VALUES
    (%(material_id)s, %(file_id)s, NULL, 0, %(title)s,
     %(source_type)s, %(primary_industry)s,
     %(kosha_guide_code)s, %(kosha_guide_group)s, %(kosha_guide_group_name)s,
     %(safety_domain)s, %(document_type)s,
     %(hazard_tags)s::jsonb, %(work_type_tags)s::jsonb, %(equipment_tags)s::jsonb,
     %(chunk_text)s, %(chunk_text_hash)s, %(search_text)s,
     %(context_score)s, %(confidence)s, %(classifier_version)s,
     TRUE, NOW())
ON CONFLICT (file_id) WHERE chunk_id IS NULL DO UPDATE SET
    title                = EXCLUDED.title,
    primary_industry     = EXCLUDED.primary_industry,
    kosha_guide_code     = EXCLUDED.kosha_guide_code,
    kosha_guide_group    = EXCLUDED.kosha_guide_group,
    kosha_guide_group_name = EXCLUDED.kosha_guide_group_name,
    safety_domain        = EXCLUDED.safety_domain,
    document_type        = EXCLUDED.document_type,
    hazard_tags          = EXCLUDED.hazard_tags,
    work_type_tags       = EXCLUDED.work_type_tags,
    equipment_tags       = EXCLUDED.equipment_tags,
    chunk_text           = EXCLUDED.chunk_text,
    chunk_text_hash      = EXCLUDED.chunk_text_hash,
    search_text          = EXCLUDED.search_text,
    context_score        = EXCLUDED.context_score,
    confidence           = EXCLUDED.confidence,
    classifier_version   = EXCLUDED.classifier_version,
    indexed_at           = NOW()
"""


# ── 모드별 실행 ───────────────────────────────────────────────────────────────

def run_dry(conn) -> None:
    print("\n[DRY-RUN] chunk join 샘플 5건:")
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(FETCH_CHUNKS_SQL + " LIMIT 5")
        rows = cur.fetchall()
    for r in rows:
        score = calc_score(r)
        ct = (r["chunk_text"] or "")[:80].replace("\n", " ")
        print(
            f"  file={r['file_id']} chunk={r['chunk_id']} idx={r['chunk_index']} "
            f"ind={r['primary_industry']} score={score:.2f} text={ct!r}"
        )

    print("\n[DRY-RUN] fallback 샘플 5건 (chunk 없는 자료):")
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(FETCH_FALLBACK_SQL + " LIMIT 5")
        rows = cur.fetchall()
    for r in rows:
        score = calc_score(r)
        ct = (r["chunk_text"] or "")[:80].replace("\n", " ")
        print(
            f"  file={r['file_id']} (fallback) ind={r['primary_industry']} "
            f"score={score:.2f} text={ct!r}"
        )


def run_apply(conn, rebuild: bool = False, limit: Optional[int] = None) -> dict:
    if rebuild:
        print("[REBUILD] 기존 kosha_context_index 전체 삭제...")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kosha_context_index")
            deleted = cur.rowcount
        conn.commit()
        print(f"  → {deleted:,}건 삭제 완료")

    print("[APPLY] chunk 행 적재 중...")
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        sql = FETCH_CHUNKS_SQL
        if limit:
            sql += f" LIMIT {limit}"
        cur.execute(sql)
        chunk_rows = cur.fetchall()

    print(f"  → {len(chunk_rows):,}건 로드")

    ok = err = 0
    batch_size = 500
    with conn.cursor() as cur:
        for i, r in enumerate(chunk_rows):
            score = calc_score(r)
            ct = r["chunk_text"] or ""
            params = {
                "material_id":        r["material_id"],
                "file_id":            r["file_id"],
                "chunk_id":           r["chunk_id"],
                "chunk_index":        r["chunk_index"],
                "title":              r["title"],
                "source_type":        r["source_type"] or "KOSHA",
                "primary_industry":   r["primary_industry"],
                "kosha_guide_code":   r["kosha_guide_code"],
                "kosha_guide_group":  r["kosha_guide_group"],
                "kosha_guide_group_name": r["kosha_guide_group_name"],
                "safety_domain":      r["safety_domain"],
                "document_type":      r["document_type"],
                "hazard_tags":        r["hazard_tags"] or "[]",
                "work_type_tags":     r["work_type_tags"] or "[]",
                "equipment_tags":     r["equipment_tags"] or "[]",
                "chunk_text":         ct[:4000],
                "chunk_text_hash":    text_hash(ct),
                "search_text":        build_search_text(r["title"] or "", r, ct),
                "context_score":      score,
                "confidence":         float(r["confidence"] or 0),
                "classifier_version": r["classifier_version"] or CLASSIFIER_VERSION,
                "is_fallback":        False,
            }
            try:
                cur.execute(UPSERT_CHUNK_SQL, params)
                ok += 1
            except Exception as e:
                err += 1
                print(f"  [ERR chunk] chunk_id={r['chunk_id']}: {e}")
                conn.rollback()
                continue
            if (i + 1) % batch_size == 0:
                conn.commit()
                print(f"  → {i+1:,}건 처리 중...")
        conn.commit()

    print(f"[APPLY] fallback 행 적재 중...")
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(FETCH_FALLBACK_SQL)
        fallback_rows = cur.fetchall()

    print(f"  → {len(fallback_rows):,}건 fallback 로드")
    fb_ok = fb_err = 0
    with conn.cursor() as cur:
        for r in fallback_rows:
            score = calc_score(r)
            ct = r["chunk_text"] or ""
            params = {
                "material_id":        r["material_id"],
                "file_id":            r["file_id"],
                "source_type":        r["source_type"] or "KOSHA",
                "primary_industry":   r["primary_industry"],
                "kosha_guide_code":   r["kosha_guide_code"],
                "kosha_guide_group":  r["kosha_guide_group"],
                "kosha_guide_group_name": r["kosha_guide_group_name"],
                "safety_domain":      r["safety_domain"],
                "document_type":      r["document_type"],
                "hazard_tags":        r["hazard_tags"] or "[]",
                "work_type_tags":     r["work_type_tags"] or "[]",
                "equipment_tags":     r["equipment_tags"] or "[]",
                "chunk_text":         ct[:4000],
                "chunk_text_hash":    text_hash(ct),
                "search_text":        build_search_text(r["title"] or "", r, ct),
                "context_score":      score,
                "confidence":         float(r["confidence"] or 0),
                "classifier_version": r["classifier_version"] or CLASSIFIER_VERSION,
                "title":              r["title"],
            }
            try:
                cur.execute(UPSERT_FALLBACK_SQL, params)
                fb_ok += 1
            except Exception as e:
                fb_err += 1
                print(f"  [ERR fallback] file_id={r['file_id']}: {e}")
                conn.rollback()
                continue
        conn.commit()

    print(f"\n[APPLY 완료]")
    print(f"  chunk 행: {ok:,}건 성공 / {err:,}건 실패")
    print(f"  fallback 행: {fb_ok:,}건 성공 / {fb_err:,}건 실패")
    print(f"  총 적재: {ok + fb_ok:,}건")
    return {"chunk_ok": ok, "chunk_err": err, "fb_ok": fb_ok, "fb_err": fb_err}


# ── 검색 검증 ─────────────────────────────────────────────────────────────────

SEARCH_CASES = [
    ("건설업+추락",       "primary_industry='construction'", "hazard_tags @> '[\"추락\"]'::jsonb"),
    ("건설업+굴착",       "primary_industry='construction'", "work_type_tags @> '[\"굴착\"]'::jsonb"),
    ("굴착기+협착",       "equipment_tags @> '[\"굴착기\"]'::jsonb", "hazard_tags @> '[\"협착\"]'::jsonb"),
    ("이동식크레인+양중", "equipment_tags @> '[\"이동식크레인\"]'::jsonb", "work_type_tags @> '[\"양중\"]'::jsonb"),
    ("밀폐공간+질식",     "hazard_tags @> '[\"질식\"]'::jsonb", "search_text ILIKE '%밀폐%'"),
    ("용접+화재폭발",     "work_type_tags @> '[\"용접절단\"]'::jsonb", "hazard_tags @> '[\"화재폭발\"]'::jsonb"),
    ("전기+감전",         "hazard_tags @> '[\"감전\"]'::jsonb", "search_text ILIKE '%전기%'"),
    ("작업환경측정",      "search_text ILIKE '%작업환경측정%'", None),
    ("특수건강진단",      "search_text ILIKE '%특수건강진단%'", None),
    ("MSDS/화학물질",     "search_text ILIKE '%MSDS%' OR search_text ILIKE '%화학물질%'", None),
]


def run_search_validation(conn) -> dict[str, int]:
    results: dict[str, int] = {}
    print("\n[검색 검증] 샘플 10개 케이스:\n")
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for label, cond1, cond2 in SEARCH_CASES:
            where = f"WHERE {cond1}"
            if cond2:
                where += f" AND {cond2}"
            sql = f"""
                SELECT title, primary_industry, context_score,
                       hazard_tags, work_type_tags, equipment_tags
                FROM kosha_context_index
                {where}
                ORDER BY context_score DESC, id
                LIMIT 10
            """
            try:
                cur.execute(sql)
                rows = cur.fetchall()
                cnt = len(rows)
                results[label] = cnt
                flag = "WARN" if cnt == 0 else "OK"
                print(f"  [{flag}] {label}: {cnt}건")
                if cnt > 0:
                    t = (rows[0]["title"] or "")[:50]
                    print(f"       top1: {t} (score={rows[0]['context_score']})")
            except Exception as e:
                results[label] = -1
                print(f"  [ERR] {label}: {e}")
    return results


# ── 리포트 ────────────────────────────────────────────────────────────────────

def run_report(output_path: str = "docs/reports/kosha_context_index_report.md") -> None:
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

            cur.execute("SELECT COUNT(*) AS n FROM kosha_context_index")
            total = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(DISTINCT material_id) AS n FROM kosha_context_index")
            mat_cnt = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(DISTINCT chunk_id) AS n FROM kosha_context_index WHERE chunk_id IS NOT NULL")
            chunk_cnt = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM kosha_context_index WHERE is_fallback")
            fallback_cnt = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM kosha_context_index WHERE primary_industry='construction'")
            construction_cnt = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM kosha_context_index WHERE hazard_tags != '[]'::jsonb")
            hazard_cnt = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM kosha_context_index WHERE work_type_tags != '[]'::jsonb")
            work_cnt = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM kosha_context_index WHERE equipment_tags != '[]'::jsonb")
            equip_cnt = cur.fetchone()["n"]

            cur.execute("""
                SELECT COUNT(*) AS n FROM kosha_context_index
                WHERE kosha_guide_code IS NULL
                  AND hazard_tags='[]'::jsonb
                  AND work_type_tags='[]'::jsonb
            """)
            unknown_cnt = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM kosha_context_index WHERE context_score IS NULL")
            null_score = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM kosha_context_index WHERE search_text IS NULL")
            null_search = cur.fetchone()["n"]

            # 업종별 분포
            cur.execute("""
                SELECT primary_industry, COUNT(*) AS n
                FROM kosha_context_index
                GROUP BY primary_industry ORDER BY n DESC
            """)
            industry_dist = cur.fetchall()

            # context_score 분포
            cur.execute("""
                SELECT
                  CASE WHEN context_score >= 0.75 THEN '0.75+'
                       WHEN context_score >= 0.50 THEN '0.50-0.74'
                       WHEN context_score >= 0.25 THEN '0.25-0.49'
                       ELSE '<0.25' END AS band,
                  COUNT(*) AS n
                FROM kosha_context_index
                GROUP BY band ORDER BY band DESC
            """)
            score_dist = cur.fetchall()

        search_results = run_search_validation(conn)
        zero_cases = [k for k, v in search_results.items() if v == 0]

    finally:
        conn.close()

    from datetime import datetime
    kst_now = datetime.now().strftime("%Y-%m-%d %H:%M KST")

    lines = [
        "# KOSHA Context Index 품질 리포트",
        "",
        f"생성일시: {kst_now}  |  분류기버전: {CLASSIFIER_VERSION}",
        "",
        "## 요약",
        "",
        "| 항목 | 수치 |",
        "|------|------|",
        f"| 분류 source (classifications) | 2,047건 |",
        f"| indexed total rows | {total:,} |",
        f"| indexed materials (distinct) | {mat_cnt:,} |",
        f"| indexed chunks (distinct) | {chunk_cnt:,} |",
        f"| fallback 행 (chunk 없는 자료) | {fallback_cnt:,} |",
        f"| 건설업 indexed | {construction_cnt:,} |",
        f"| 위험요인 태그 있는 행 | {hazard_cnt:,} |",
        f"| 작업유형 태그 있는 행 | {work_cnt:,} |",
        f"| 장비 태그 있는 행 | {equip_cnt:,} |",
        f"| UNKNOWN 행 (태그 전무) | {unknown_cnt:,} |",
        f"| context_score null | {null_score} |",
        f"| search_text null | {null_search} |",
        "",
        "## 업종별 분포",
        "",
        "| 업종 | 행 수 |",
        "|------|-------|",
    ]
    for r in industry_dist:
        lines.append(f"| {r['primary_industry'] or '-'} | {r['n']:,} |")

    lines += [
        "",
        "## Context Score 분포",
        "",
        "| 구간 | 행 수 |",
        "|------|-------|",
    ]
    for r in score_dist:
        lines.append(f"| {r['band']} | {r['n']:,} |")

    lines += [
        "",
        "## 검색 검증 결과",
        "",
        "| 케이스 | 결과 건수 | 판정 |",
        "|--------|-----------|------|",
    ]
    for label, cnt in search_results.items():
        flag = "WARN" if cnt == 0 else ("ERR" if cnt < 0 else "OK")
        lines.append(f"| {label} | {cnt} | {flag} |")

    if zero_cases:
        lines += [
            "",
            f"**0건 케이스:** {', '.join(zero_cases)}",
        ]

    lines += [
        "",
        "## Backlog",
        "",
        "| 유형 | 건수 | 집계 SQL |",
        "|------|------|---------|",
        "| image_pdf | 2,434 | `WHERE parse_status='image_pdf'` |",
        "| failed_unzip | 111 | `WHERE parse_status='failed_unzip'` |",
        "| hwp pending | 9 | `WHERE parse_status='pending' AND file_type='hwp'` |",
        "| text_pdf failed | 64 | `WHERE parse_status='failed' AND file_type='pdf'` |",
        "",
        "## 다음 단계",
        "",
        "- [ ] 위험성평가 생성 엔진에서 `kosha_context_index` read-only 연결",
        "- [ ] context_score 임계값(≥0.50) 기준 엔진 필터링 설계",
        "- [ ] 0건 검색 케이스 보강: 키워드 사전 확장 또는 FTS 보완",
        "- [ ] image_pdf 2,434건 OCR 후 분류·인덱싱 확장",
    ]

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[REPORT] {out} 생성 완료")


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="KOSHA Context Index 적재기")
    ap.add_argument("--dry-run",  action="store_true", help="샘플 미리보기만")
    ap.add_argument("--apply",    action="store_true", help="전체 적재 (upsert)")
    ap.add_argument("--rebuild",  action="store_true", help="TRUNCATE 후 재적재 (--apply 필요)")
    ap.add_argument("--report",   action="store_true", help="품질 리포트 생성")
    ap.add_argument("--limit",    type=int, default=None, help="chunk 처리 건수 제한")
    ap.add_argument("--output",   default="docs/reports/kosha_context_index_report.md")
    args = ap.parse_args()

    if not (args.dry_run or args.apply or args.report):
        ap.print_help()
        sys.exit(0)

    conn = get_conn()
    try:
        if args.dry_run:
            run_dry(conn)

        if args.apply:
            run_apply(conn, rebuild=args.rebuild, limit=args.limit)

        if args.report:
            run_search_validation(conn)

    finally:
        conn.close()

    if args.report:
        run_report(output_path=args.output)


if __name__ == "__main__":
    main()

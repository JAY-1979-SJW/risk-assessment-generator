-- ======================================================================
-- Migration 0002 : MOEL 해석례 9,573건 upsert into documents + moel_expc_meta
-- Idempotent. Re-runnable via source_key.
-- ======================================================================

BEGIN;

-- 1) staging
CREATE TEMP TABLE stg_moel_expc (
    source_id      varchar(100),
    title          text,
    case_no        text,
    inquire_org    text,
    interpret_org  text,
    interpret_code text,
    inquire_code   text,
    interpreted_at text,
    detail_url     text,
    data_std_dt    text,
    collected_at   text
);

\copy stg_moel_expc FROM '/tmp/moel_expc_load.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '')

SELECT 'stg rows'::text, count(*) FROM stg_moel_expc;

-- 2) upsert into documents
--    source_type='moel_expc', source_id=serial_no
--    url = https://www.law.go.kr + detail_url
WITH ins AS (
    INSERT INTO documents (
        source_type, source_id, doc_category, title, title_normalized,
        body_text, has_text, content_length,
        url, file_url, pdf_path, language, status,
        published_at, collected_at, metadata
    )
    SELECT
        'moel_expc',
        s.source_id,
        'law_moel_expc',
        COALESCE(NULLIF(s.title,''), '(제목없음)'),
        NULL,
        NULL,
        false,
        0,
        CASE WHEN s.detail_url LIKE '/DRF/%'
             THEN 'https://www.law.go.kr' || s.detail_url
             ELSE NULLIF(s.detail_url,'') END,
        NULL, NULL, 'ko', 'active',
        CASE WHEN s.interpreted_at ~ '^\d{4}\.\d{2}\.\d{2}$'
             THEN to_date(s.interpreted_at, 'YYYY.MM.DD')
             ELSE NULL END,
        CASE WHEN s.collected_at ~ '^\d{4}-\d{2}-\d{2}'
             THEN (s.collected_at)::timestamp
             ELSE now() END,
        jsonb_build_object(
            'source', 'law.go.kr/moelCgmExpc',
            'case_no', s.case_no,
            'inquire_org', s.inquire_org,
            'interpret_org', s.interpret_org
        )
    FROM stg_moel_expc s
    ON CONFLICT (source_type, source_id) DO UPDATE
       SET title = EXCLUDED.title,
           url   = EXCLUDED.url,
           published_at = EXCLUDED.published_at,
           metadata = documents.metadata || EXCLUDED.metadata,
           updated_at = now()
    RETURNING id, source_id
)
SELECT 'documents upserted'::text, count(*) FROM ins;

-- 3) upsert moel_expc_meta
INSERT INTO moel_expc_meta (
    document_id, case_no, interpret_org, interpret_code,
    inquire_org, inquire_code, interpreted_at, data_std_dt,
    text_quality, extra
)
SELECT d.id,
       NULLIF(s.case_no,''),
       NULLIF(s.interpret_org,''),
       NULLIF(s.interpret_code,''),
       NULLIF(s.inquire_org,''),
       NULLIF(s.inquire_code,''),
       NULLIF(s.interpreted_at,''),
       NULLIF(s.data_std_dt,''),
       'title_only',
       '{}'::jsonb
FROM stg_moel_expc s
JOIN documents d
  ON d.source_type='moel_expc' AND d.source_id=s.source_id
ON CONFLICT (document_id) DO UPDATE
   SET case_no       = EXCLUDED.case_no,
       interpret_org = EXCLUDED.interpret_org,
       interpret_code= EXCLUDED.interpret_code,
       inquire_org   = EXCLUDED.inquire_org,
       inquire_code  = EXCLUDED.inquire_code,
       interpreted_at= EXCLUDED.interpreted_at,
       data_std_dt   = EXCLUDED.data_std_dt;

SELECT 'moel_expc_meta count'::text, count(*) FROM moel_expc_meta;

-- 4) collection_runs 이력
INSERT INTO collection_runs (
    source_type, run_date, status, total_count, success_count, fail_count,
    note, started_at, finished_at
)
SELECT 'moel_expc', CURRENT_DATE, 'ok',
       (SELECT count(*) FROM stg_moel_expc),
       (SELECT count(*) FROM stg_moel_expc),
       0,
       'Bulk import from local moel_expc.db (title-only, detail_url preserved). Body-level crawl pending.',
       now(), now();

COMMIT;

-- 결과 요약
SELECT source_type, COUNT(*) AS docs, COUNT(*) FILTER (WHERE has_text) AS has_text
  FROM documents WHERE source_type='moel_expc' GROUP BY 1;
SELECT 'meta rows'::text, COUNT(*) FROM moel_expc_meta;

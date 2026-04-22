-- ======================================================================
-- Migration 0006 : 5단계 교정 — mis-inserted 1841건 제거 + med_seq 기반 재적재
-- mis-inserted 기준: metadata->>'source' = 'common_data/kosha' AND doc_category_src key present
-- ======================================================================

BEGIN;

-- (0) 잘못 삽입된 1841건 제거 (방금 0005에서 내부 material_id를 source_id로 넣은 것)
WITH to_del AS (
    SELECT id FROM documents
     WHERE source_type='kosha'
       AND metadata->>'source' = 'common_data/kosha'
)
DELETE FROM documents WHERE id IN (SELECT id FROM to_del);

SELECT 'kosha after cleanup'::text, COUNT(*) FROM documents WHERE source_type='kosha';

-- (1) staging (med_seq 기반)
CREATE TEMP TABLE stg_kosha (
    source_id     text,   -- = med_seq
    internal_material_id text,
    title         text,
    category      text,
    list_type     text,
    industry      text,
    reg_date      text,
    download_url  text,
    conts_atcfl_no text,
    doc_category  text,
    source        text,
    keyword       text,
    file_path     text,
    file_hash     text,
    rt_len        int,
    raw_text      text
);
\copy stg_kosha FROM '/tmp/kosha_incremental_v2.csv' WITH (FORMAT csv, DELIMITER ',', HEADER true, QUOTE '"', NULL '')

SELECT 'stg rows'::text, COUNT(*) FROM stg_kosha;

-- (2) 분류: update vs new
CREATE TEMP TABLE stg_new AS
SELECT s.*
FROM stg_kosha s
LEFT JOIN documents d ON d.source_type='kosha' AND d.source_id=s.source_id
WHERE d.id IS NULL;

CREATE TEMP TABLE stg_upd AS
SELECT s.*, d.id AS existing_id, d.content_length AS cur_len, d.has_text AS cur_has_text,
       d.doc_category AS cur_doc_category
FROM stg_kosha s
JOIN documents d ON d.source_type='kosha' AND d.source_id=s.source_id;

SELECT 'new'::text, COUNT(*) FROM stg_new
UNION ALL SELECT 'update', COUNT(*) FROM stg_upd;

-- (3) 신규 INSERT
INSERT INTO documents (
    source_type, source_id, doc_category, title,
    body_text, has_text, content_length,
    url, file_url, pdf_path, file_sha256, language, status,
    published_at, collected_at, metadata
)
SELECT
    'kosha', s.source_id,
    CASE
      WHEN s.list_type='OPS' THEN 'kosha_opl'
      WHEN s.list_type='기타' THEN 'kosha_generic'
      ELSE 'kosha_other'
    END,
    COALESCE(NULLIF(s.title,''),'(제목없음)'),
    NULLIF(s.raw_text,''),
    true,
    s.rt_len,
    NULLIF(s.download_url,''),
    NULLIF(s.download_url,''),
    NULLIF(s.file_path,''),
    NULLIF(s.file_hash,''),
    'ko','active',
    CASE WHEN s.reg_date ~ '^\d{8}$' THEN to_date(s.reg_date,'YYYYMMDD')
         WHEN s.reg_date ~ '^\d{4}-\d{2}-\d{2}$' THEN s.reg_date::date
         ELSE NULL END,
    now(),
    jsonb_build_object(
        'source','common_data/kosha',
        'internal_material_id', s.internal_material_id,
        'category', s.category,
        'list_type', s.list_type,
        'industry', s.industry,
        'doc_category_src', s.doc_category,
        'conts_atcfl_no', s.conts_atcfl_no,
        'keyword', s.keyword
    )
FROM stg_new s
ON CONFLICT (source_type, source_id) DO NOTHING;

-- (4) 기존 보강 (missing_source 복구 포함)
UPDATE documents d
   SET body_text      = CASE WHEN s.rt_len > d.content_length THEN s.raw_text
                              ELSE d.body_text END,
       has_text       = true,
       content_length = GREATEST(d.content_length, s.rt_len),
       doc_category   = CASE
                          WHEN d.doc_category='kosha_opl_missing_source' THEN 'kosha_opl'
                          WHEN d.doc_category IS NULL THEN 'kosha_opl'
                          ELSE d.doc_category
                        END,
       pdf_path       = COALESCE(d.pdf_path, NULLIF(s.file_path,'')),
       file_sha256    = COALESCE(d.file_sha256, NULLIF(s.file_hash,'')),
       file_url       = COALESCE(d.file_url, NULLIF(s.download_url,'')),
       metadata       = d.metadata || jsonb_build_object(
                          'recovered_from','common_data/kosha',
                          'recovery_at', to_jsonb(now()::text),
                          'category', s.category,
                          'industry', s.industry,
                          'internal_material_id', s.internal_material_id
                        ),
       updated_at     = now()
FROM stg_upd s
WHERE d.id = s.existing_id
  AND (d.has_text = false OR s.rt_len > d.content_length);

-- (5) image_only OCR 플래그
UPDATE documents d
   SET metadata = d.metadata || jsonb_build_object('needs_ocr', true, 'ocr_reason','image_only')
 WHERE d.source_type='kosha' AND d.doc_category='kosha_opl_image_only'
   AND NOT (d.metadata ? 'needs_ocr');

-- (6) kosha_meta 보강
INSERT INTO kosha_meta (document_id, industry, tags)
SELECT d.id, NULLIF(s.industry,''),
       jsonb_build_array(s.category, s.list_type, s.doc_category)
FROM stg_kosha s
JOIN documents d ON d.source_type='kosha' AND d.source_id=s.source_id
ON CONFLICT (document_id) DO UPDATE
   SET industry = COALESCE(EXCLUDED.industry, kosha_meta.industry),
       tags     = kosha_meta.tags || EXCLUDED.tags;

-- (7) collection_runs 이력
INSERT INTO collection_runs (source_type, run_date, status, total_count, success_count, fail_count, note, started_at, finished_at)
VALUES ('kosha_inc', CURRENT_DATE, 'ok',
        (SELECT COUNT(*) FROM stg_kosha),
        (SELECT COUNT(*) FROM stg_new)+(SELECT COUNT(*) FROM stg_upd),
        0,
        'common_data→kras (med_seq-keyed). missing_source 복구 + 신규증분.',
        now(), now());

COMMIT;

-- 요약
SELECT 'kosha total'::text, COUNT(*) FROM documents WHERE source_type='kosha'
UNION ALL SELECT 'kosha has_text', COUNT(*) FROM documents WHERE source_type='kosha' AND has_text
UNION ALL SELECT 'kosha missing_source(남은)', COUNT(*) FROM documents WHERE source_type='kosha' AND doc_category='kosha_opl_missing_source'
UNION ALL SELECT 'kosha image_only w/ OCR flag', COUNT(*) FROM documents WHERE source_type='kosha' AND doc_category='kosha_opl_image_only' AND metadata ? 'needs_ocr'
UNION ALL SELECT 'recovered from common_data', COUNT(*) FROM documents WHERE source_type='kosha' AND metadata ? 'recovered_from';

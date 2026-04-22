-- ======================================================================
-- Migration 0005 : KOSHA 증분 적재 + missing_source 복구 + image_only 플래그
-- Policy:
--   • 본문 없는 것(kras)에 common_data 본문이 있으면 복구
--   • 길이가 더 긴 본문이 common_data에 있으면 교체
--   • 새 material이면 신규 삽입
--   • image_only 128건에 OCR 플래그만 부여
-- ======================================================================

BEGIN;

CREATE TEMP TABLE stg_kosha (
    material_id    text,
    title          text,
    category       text,
    list_type      text,
    industry       text,
    reg_date       text,
    download_url   text,
    conts_atcfl_no text,
    doc_category   text,
    source         text,
    keyword        text,
    file_path      text,
    file_hash      text,
    rt_len         int,
    raw_text       text
);
\copy stg_kosha FROM '/tmp/kosha_incremental.csv' WITH (FORMAT csv, DELIMITER ',', HEADER true, QUOTE '"', NULL '')

SELECT 'stg rows'::text, COUNT(*) FROM stg_kosha;

-- 1) 기존 vs 신규 분류
CREATE TEMP TABLE stg_kosha_new AS
SELECT s.*
FROM stg_kosha s
LEFT JOIN documents d
  ON d.source_type='kosha' AND d.source_id=s.material_id
WHERE d.id IS NULL;

CREATE TEMP TABLE stg_kosha_update AS
SELECT s.*, d.id AS existing_id, d.content_length AS cur_len, d.has_text AS cur_has_text,
       d.doc_category AS cur_doc_category
FROM stg_kosha s
JOIN documents d
  ON d.source_type='kosha' AND d.source_id=s.material_id;

SELECT 'new materials'::text, COUNT(*) FROM stg_kosha_new
UNION ALL SELECT 'update candidates', COUNT(*) FROM stg_kosha_update;

-- 2) 신규 INSERT
INSERT INTO documents (
    source_type, source_id, doc_category, title, title_normalized,
    body_text, has_text, content_length,
    url, file_url, pdf_path, file_sha256, language, status,
    published_at, collected_at, metadata
)
SELECT
    'kosha', s.material_id,
    CASE
      WHEN s.category ILIKE '%_기타%' OR s.list_type='기타' THEN 'kosha_generic'
      WHEN s.list_type='OPS' THEN 'kosha_opl'
      ELSE 'kosha_other'
    END,
    COALESCE(NULLIF(s.title,''),'(제목없음)'),
    NULL,
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
        'category', s.category,
        'list_type', s.list_type,
        'industry', s.industry,
        'doc_category_src', s.doc_category,
        'conts_atcfl_no', s.conts_atcfl_no,
        'keyword', s.keyword
    )
FROM stg_kosha_new s
ON CONFLICT (source_type, source_id) DO NOTHING;

-- 3) 기존 보강 (missing_source 복구 포함)
UPDATE documents d
   SET body_text      = COALESCE(
                         CASE WHEN s.rt_len > d.content_length THEN s.raw_text
                              ELSE d.body_text END,
                         s.raw_text),
       has_text       = true,
       content_length = GREATEST(d.content_length, s.rt_len),
       doc_category   = CASE
                          WHEN d.doc_category='kosha_opl_missing_source' THEN 'kosha_opl'
                          WHEN d.doc_category='kosha_opl_image_only'     THEN 'kosha_opl_image_only'
                          ELSE d.doc_category
                        END,
       pdf_path       = COALESCE(d.pdf_path, NULLIF(s.file_path,'')),
       file_sha256    = COALESCE(d.file_sha256, NULLIF(s.file_hash,'')),
       file_url       = COALESCE(d.file_url, NULLIF(s.download_url,'')),
       metadata       = d.metadata || jsonb_build_object(
                          'recovered_from','common_data/kosha',
                          'recovery_at', to_jsonb(now()),
                          'category', s.category,
                          'industry', s.industry
                        ),
       updated_at     = now()
FROM stg_kosha_update s
WHERE d.id = s.existing_id
  AND (d.has_text = false OR s.rt_len > d.content_length);

-- 4) image_only에 OCR 플래그 부여 (본문 추가 안함)
UPDATE documents d
   SET metadata = d.metadata || jsonb_build_object('needs_ocr', true, 'ocr_reason','image_only')
 WHERE d.source_type='kosha' AND d.doc_category='kosha_opl_image_only'
   AND NOT (d.metadata ? 'needs_ocr');

-- 5) kosha_meta 보강
INSERT INTO kosha_meta (document_id, industry, tags)
SELECT d.id, NULLIF(s.industry,''),
       jsonb_build_array(s.category, s.list_type, s.doc_category)
FROM stg_kosha s
JOIN documents d ON d.source_type='kosha' AND d.source_id=s.material_id
ON CONFLICT (document_id) DO UPDATE
   SET industry = COALESCE(EXCLUDED.industry, kosha_meta.industry),
       tags     = kosha_meta.tags || EXCLUDED.tags;

-- 6) collection_runs 이력
INSERT INTO collection_runs (source_type, run_date, status, total_count, success_count, fail_count, note, started_at, finished_at)
VALUES ('kosha_inc', CURRENT_DATE, 'ok',
        (SELECT COUNT(*) FROM stg_kosha),
        (SELECT COUNT(*) FROM stg_kosha_new)+(SELECT COUNT(*) FROM stg_kosha_update),
        0,
        'common_data/kosha_materials+files → kras documents upsert (1841 candidates)',
        now(), now());

COMMIT;

-- 결과
SELECT 'kosha total'::text, COUNT(*) FROM documents WHERE source_type='kosha'
UNION ALL
SELECT 'kosha has_text', COUNT(*) FROM documents WHERE source_type='kosha' AND has_text
UNION ALL
SELECT 'kosha missing_source', COUNT(*) FROM documents WHERE source_type='kosha' AND doc_category='kosha_opl_missing_source'
UNION ALL
SELECT 'kosha image_only w/ OCR flag', COUNT(*) FROM documents
  WHERE source_type='kosha' AND doc_category='kosha_opl_image_only' AND metadata ? 'needs_ocr';

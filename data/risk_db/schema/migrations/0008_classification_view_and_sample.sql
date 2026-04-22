-- ======================================================================
-- Migration 0008 : 통합 분류 뷰 + 샘플 hazard 매핑 (moel_expc, admrul 신규)
-- ======================================================================

BEGIN;

-- 1) 통합 분류 뷰 (source별 meta + 분류 매핑 aggregation)
DROP VIEW IF EXISTS v_classified_documents CASCADE;
CREATE VIEW v_classified_documents AS
SELECT
    d.id,
    d.source_type,
    d.corrected_source_type,
    d.doc_category,
    d.title,
    d.has_text,
    d.content_length,
    d.published_at,
    d.url,
    COALESCE(lm.law_name,     NULL) AS law_name,
    COALESCE(lm.article_no,   NULL) AS article_no,
    COALESCE(lm.normalized_type, d.source_type) AS normalized_type,
    COALESCE(km.industry,     NULL) AS kosha_industry,
    (SELECT jsonb_agg(DISTINCT h.hazard_code)
       FROM document_hazard_map h WHERE h.document_id=d.id) AS hazard_codes,
    (SELECT jsonb_agg(DISTINCT w.work_type_code)
       FROM document_work_type_map w WHERE w.document_id=d.id) AS work_type_codes,
    (SELECT jsonb_agg(DISTINCT e.equipment_code)
       FROM document_equipment_map e WHERE e.document_id=d.id) AS equipment_codes,
    (SELECT jsonb_agg(DISTINCT c.control_code)
       FROM document_control_map c WHERE c.document_id=d.id) AS control_codes
FROM documents d
LEFT JOIN law_meta       lm ON lm.document_id=d.id
LEFT JOIN kosha_meta     km ON km.document_id=d.id;

-- 2) hazard_keywords 임시 테이블에 적재
DROP TABLE IF EXISTS hazard_keywords_map;
CREATE UNLOGGED TABLE hazard_keywords_map (
    hazard_code varchar(50),
    keyword     text
);
\copy hazard_keywords_map FROM '/tmp/hazard_keywords.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '')

CREATE INDEX ON hazard_keywords_map(hazard_code);

SELECT 'hazard_keywords'::text, COUNT(*) FROM hazard_keywords_map;

-- 3) 샘플 자동분류 — moel_expc + admrul 신규(34→191, 9573 new)에 대해 title/body에 keyword 포함 매핑
INSERT INTO document_hazard_map (document_id, hazard_code, is_primary)
SELECT DISTINCT d.id, hk.hazard_code, false
FROM documents d
JOIN hazard_keywords_map hk
  ON (d.title ILIKE '%'||hk.keyword||'%'
      OR (d.body_text IS NOT NULL AND d.body_text ILIKE '%'||hk.keyword||'%'))
WHERE d.source_type IN ('moel_expc','admrul')
ON CONFLICT DO NOTHING;

-- 4) KOSHA 신규 194건도 포함
INSERT INTO document_hazard_map (document_id, hazard_code, is_primary)
SELECT DISTINCT d.id, hk.hazard_code, false
FROM documents d
JOIN hazard_keywords_map hk
  ON (d.title ILIKE '%'||hk.keyword||'%'
      OR (d.body_text IS NOT NULL AND d.body_text ILIKE '%'||hk.keyword||'%'))
WHERE d.source_type='kosha' AND d.metadata->>'source'='common_data/kosha'
ON CONFLICT DO NOTHING;

DROP TABLE hazard_keywords_map;

COMMIT;

-- 결과
SELECT d.source_type,
       COUNT(*) AS docs,
       COUNT(DISTINCT h.document_id) AS docs_with_hazard,
       COUNT(h.*) AS hazard_links
FROM documents d
LEFT JOIN document_hazard_map h ON h.document_id=d.id
WHERE d.source_type IN ('moel_expc','admrul','kosha')
GROUP BY 1
ORDER BY 2 DESC;

-- 뷰 샘플
SELECT id, source_type, title, hazard_codes
FROM v_classified_documents
WHERE source_type='moel_expc' AND hazard_codes IS NOT NULL
LIMIT 5;

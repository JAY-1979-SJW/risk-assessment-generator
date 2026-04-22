-- ======================================================================
-- Migration 0004 : admrul 본문 191건 upsert (누락 67건 포함)
-- Policy: 기존 레코드의 본문을 덮어쓰지 않음 (더 긴 내용이 들어올 때만 업데이트)
-- ======================================================================

BEGIN;

CREATE TEMP TABLE stg_admrul (
    source_id text, title text, body_text text, has_text text,
    source_url text, published_at text, collected_at text,
    law_id text, law_type text, ministry text,
    enforcement_date text, revision_type text
);
\copy stg_admrul FROM '/tmp/admrul_content.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '', QUOTE '"')

SELECT 'stg rows'::text, COUNT(*) FROM stg_admrul;

-- 1) documents upsert
INSERT INTO documents (
    source_type, source_id, doc_category, title, body_text, has_text, content_length,
    url, language, status, published_at, collected_at, metadata
)
SELECT 'admrul', s.source_id, 'law_admrul',
       COALESCE(NULLIF(s.title,''), '(제목없음)'),
       NULLIF(s.body_text,''),
       (s.has_text='t'),
       COALESCE(length(s.body_text), 0),
       NULLIF(s.source_url,''),
       'ko', 'active',
       CASE WHEN s.published_at ~ '^\d{4}-\d{2}-\d{2}$' THEN s.published_at::date ELSE NULL END,
       CASE WHEN s.collected_at ~ '^\d{4}-\d{2}-\d{2}' THEN s.collected_at::timestamp ELSE now() END,
       jsonb_build_object(
           'law_type', s.law_type,
           'ministry', s.ministry,
           'enforcement_date', s.enforcement_date,
           'revision_type', s.revision_type,
           'source', 'law.go.kr/admrul'
       )
FROM stg_admrul s
ON CONFLICT (source_type, source_id) DO UPDATE
   SET body_text      = CASE WHEN COALESCE(length(EXCLUDED.body_text),0) > COALESCE(length(documents.body_text),0)
                              THEN EXCLUDED.body_text ELSE documents.body_text END,
       has_text       = documents.has_text OR EXCLUDED.has_text,
       content_length = GREATEST(documents.content_length, EXCLUDED.content_length),
       url            = COALESCE(documents.url, EXCLUDED.url),
       published_at   = COALESCE(documents.published_at, EXCLUDED.published_at),
       metadata       = documents.metadata || EXCLUDED.metadata,
       updated_at     = now();

-- 2) law_meta upsert (for admrul)
INSERT INTO law_meta (document_id, law_name, law_id, article_no, promulgation_date, effective_date, ministry, extra)
SELECT d.id, d.title, NULLIF(s.law_id,''),
       NULL,
       CASE WHEN s.published_at ~ '^\d{4}-\d{2}-\d{2}$' THEN s.published_at::date ELSE NULL END,
       CASE WHEN s.enforcement_date ~ '^\d{4}-\d{2}-\d{2}$' THEN s.enforcement_date::date ELSE NULL END,
       NULLIF(s.ministry,''),
       jsonb_build_object('law_type', s.law_type, 'revision_type', s.revision_type)
FROM stg_admrul s
JOIN documents d ON d.source_type='admrul' AND d.source_id=s.source_id
ON CONFLICT (document_id) DO UPDATE
   SET law_name     = COALESCE(law_meta.law_name, EXCLUDED.law_name),
       law_id       = COALESCE(EXCLUDED.law_id, law_meta.law_id),
       promulgation_date = COALESCE(law_meta.promulgation_date, EXCLUDED.promulgation_date),
       effective_date    = COALESCE(law_meta.effective_date, EXCLUDED.effective_date),
       ministry     = COALESCE(EXCLUDED.ministry, law_meta.ministry),
       extra        = law_meta.extra || EXCLUDED.extra;

-- 3) 결과
SELECT 'admrul total'::text, COUNT(*), COUNT(*) FILTER (WHERE has_text) AS has_text,
       SUM(content_length) AS total_chars
FROM documents WHERE source_type='admrul';

-- 4) ledger
INSERT INTO collection_runs (source_type, run_date, status, total_count, success_count, fail_count, note, started_at, finished_at)
VALUES ('admrul', CURRENT_DATE, 'ok',
       (SELECT count(*) FROM stg_admrul),
       (SELECT count(*) FROM stg_admrul WHERE has_text='t'),
       (SELECT count(*) FROM stg_admrul WHERE has_text<>'t'),
       'admrul_content.jsonl 191건 upsert (기존 34건 + 누락 67건 신규 + 90건 추가)',
       now(), now());

COMMIT;

-- 결과 확인
SELECT 'documents admrul'::text, COUNT(*) FROM documents WHERE source_type='admrul'
UNION ALL
SELECT 'law_meta(admrul)', COUNT(*) FROM law_meta lm JOIN documents d ON d.id=lm.document_id WHERE d.source_type='admrul';

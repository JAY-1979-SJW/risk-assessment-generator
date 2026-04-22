-- ======================================================================
-- Migration 0003 : master/rules CSV → controls / sentence_normalization /
--                  sentence_labels / rule_sets / rules
-- Idempotent.
-- ======================================================================

BEGIN;

-- 1) controls (upsert)
CREATE TEMP TABLE stg_controls (
    control_code text, control_name text, category text, extra_json text
);
\copy stg_controls FROM '/tmp/controls.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '')

INSERT INTO controls (control_code, control_name, category, sort_order, is_active, extra)
SELECT s.control_code, COALESCE(NULLIF(s.control_name,''),'(이름없음)'),
       NULLIF(s.category,''),
       0, true,
       COALESCE(NULLIF(s.extra_json,'')::jsonb, '{}'::jsonb)
FROM stg_controls s
WHERE s.control_code IS NOT NULL AND s.control_code<>''
ON CONFLICT (control_code) DO UPDATE
   SET control_name = EXCLUDED.control_name,
       category     = EXCLUDED.category,
       extra        = EXCLUDED.extra;

SELECT 'controls count'::text, COUNT(*) FROM controls;

-- 2) sentence_normalization (append, dedupe by source_file+row_no via stage)
CREATE TEMP TABLE stg_sn (
    source_file text, row_no int, raw_sentence text,
    normalized_sentence text, version text, extra_json text
);
\copy stg_sn FROM '/tmp/sentence_normalization_v2.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '')

-- 재실행 대비: 기존 동일 source_file+version 삭제 후 재삽입
DELETE FROM sentence_normalization
 WHERE source_file IN (SELECT DISTINCT source_file FROM stg_sn)
   AND version    IN (SELECT DISTINCT version     FROM stg_sn);

INSERT INTO sentence_normalization (source_file,row_no,raw_sentence,normalized_sentence,version,extra)
SELECT s.source_file, s.row_no, NULLIF(s.raw_sentence,''),
       NULLIF(s.normalized_sentence,''), s.version,
       COALESCE(NULLIF(s.extra_json,'')::jsonb, '{}'::jsonb)
FROM stg_sn s;

SELECT 'sentence_normalization count'::text, COUNT(*) FROM sentence_normalization;

-- 3) sentence_labels (append, dedupe by source_file)
CREATE TEMP TABLE stg_sl (
    source_file text, row_no int, sentence text, label text,
    sub_label text, extra_json text
);
\copy stg_sl FROM '/tmp/sentence_labels.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '')

DELETE FROM sentence_labels
 WHERE source_file IN (SELECT DISTINCT source_file FROM stg_sl);

INSERT INTO sentence_labels (source_file,row_no,sentence,label,sub_label,extra)
SELECT s.source_file, s.row_no, s.sentence,
       NULLIF(s.label,''), NULLIF(s.sub_label,''),
       COALESCE(NULLIF(s.extra_json,'')::jsonb, '{}'::jsonb)
FROM stg_sl s
WHERE s.sentence IS NOT NULL AND s.sentence<>'';

SELECT 'sentence_labels count'::text, COUNT(*) FROM sentence_labels;

-- 4) rule_sets + rules
CREATE TEMP TABLE stg_rs (
    rule_set_name text, source_file text, version text, description text
);
\copy stg_rs FROM '/tmp/rule_set.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '')

INSERT INTO rule_sets (rule_set_name, source_file, version, description)
SELECT rule_set_name, source_file, NULLIF(version,''), NULLIF(description,'')
FROM stg_rs
ON CONFLICT (rule_set_name, version) DO UPDATE
   SET description = EXCLUDED.description,
       source_file = EXCLUDED.source_file,
       loaded_at   = now();

CREATE TEMP TABLE stg_rules (
    rule_key text, pattern text, action text, enabled text, extra_json text
);
\copy stg_rules FROM '/tmp/rules.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '')

-- 재삽입을 위해 현재 rule_set에 연결된 기존 rules 삭제
DELETE FROM rules r
 USING rule_sets rs
 WHERE r.rule_set_id = rs.id
   AND rs.rule_set_name='safety_rules';

INSERT INTO rules (rule_set_id, rule_key, pattern, action, enabled, extra)
SELECT rs.id, s.rule_key, NULLIF(s.pattern,''), NULLIF(s.action,''),
       CASE WHEN s.enabled='t' THEN true ELSE false END,
       COALESCE(NULLIF(s.extra_json,'')::jsonb, '{}'::jsonb)
FROM stg_rules s
JOIN rule_sets rs ON rs.rule_set_name='safety_rules'
WHERE s.rule_key IS NOT NULL AND s.rule_key<>'';

SELECT 'rule_sets,rules'::text, (SELECT COUNT(*) FROM rule_sets), (SELECT COUNT(*) FROM rules);

-- 5) collection_runs 이력
INSERT INTO collection_runs (source_type, run_date, status, total_count, success_count, fail_count, note, started_at, finished_at)
VALUES ('master_csv', CURRENT_DATE, 'ok',
        (SELECT COUNT(*) FROM controls) + (SELECT COUNT(*) FROM sentence_normalization) + (SELECT COUNT(*) FROM sentence_labels) + (SELECT COUNT(*) FROM rules),
        (SELECT COUNT(*) FROM controls) + (SELECT COUNT(*) FROM sentence_normalization) + (SELECT COUNT(*) FROM sentence_labels) + (SELECT COUNT(*) FROM rules),
        0,
        'controls_master_draft_v2 + sentence_normalization_sample_v2 + sentence_labeling_sample_v2 + sentence_control_mapping_sample_v2 + safety_rules.json',
        now(), now());

COMMIT;

-- 결과
SELECT 'controls'::text, COUNT(*) FROM controls
UNION ALL SELECT 'sentence_normalization', COUNT(*) FROM sentence_normalization
UNION ALL SELECT 'sentence_labels', COUNT(*) FROM sentence_labels
UNION ALL SELECT 'rule_sets', COUNT(*) FROM rule_sets
UNION ALL SELECT 'rules', COUNT(*) FROM rules;

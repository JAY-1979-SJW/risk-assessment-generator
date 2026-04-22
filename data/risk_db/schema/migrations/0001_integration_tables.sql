-- ======================================================================
-- Migration 0001 : Integration tables for data集合/분류
-- Target: kras DB on risk-assessment-db
-- Idempotent (CREATE IF NOT EXISTS)
-- Destructive 작업 없음
-- ======================================================================

BEGIN;

-- ---------------------------------------------------------------
-- 1) MOEL 해석례 전용 메타 (source_type='moel_expc' 대응)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS moel_expc_meta (
    document_id   bigint PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    case_no       varchar(100),
    interpret_org varchar(200),
    interpret_code varchar(50),
    inquire_org   varchar(200),
    inquire_code  varchar(50),
    interpreted_at varchar(20),
    data_std_dt   varchar(20),
    text_quality  varchar(20) NOT NULL DEFAULT 'title_only',
    extra         jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS ix_moel_expc_meta_interp
    ON moel_expc_meta(interpreted_at);
CREATE INDEX IF NOT EXISTS ix_moel_expc_meta_quality
    ON moel_expc_meta(text_quality);

-- ---------------------------------------------------------------
-- 2) Controls 마스터 + 문서-제어 매핑 (hazards/equipment 패턴)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS controls (
    control_code varchar(50) PRIMARY KEY,
    control_name varchar(200) NOT NULL,
    category     varchar(100),
    sort_order   integer DEFAULT 0,
    is_active    boolean DEFAULT true,
    extra        jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_controls_name
    ON controls(control_name);

CREATE TABLE IF NOT EXISTS document_control_map (
    document_id  bigint NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    control_code varchar(50) NOT NULL REFERENCES controls(control_code) ON DELETE RESTRICT,
    is_primary   boolean DEFAULT false,
    created_at   timestamp NOT NULL DEFAULT now(),
    PRIMARY KEY (document_id, control_code)
);
CREATE INDEX IF NOT EXISTS ix_dcm_control_code
    ON document_control_map(control_code);

-- ---------------------------------------------------------------
-- 3) Sentence normalization (원본 1:1 staging)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sentence_normalization (
    id                  bigserial PRIMARY KEY,
    source_file         varchar(300) NOT NULL,
    row_no              integer,
    raw_sentence        text,
    normalized_sentence text,
    version             varchar(10),
    extra               jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at          timestamp NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sn_source_file
    ON sentence_normalization(source_file);
CREATE INDEX IF NOT EXISTS ix_sn_version
    ON sentence_normalization(version);

-- ---------------------------------------------------------------
-- 4) Sentence labeling (staging)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sentence_labels (
    id          bigserial PRIMARY KEY,
    source_file varchar(300) NOT NULL,
    row_no      integer,
    sentence    text NOT NULL,
    label       varchar(100),
    sub_label   varchar(100),
    extra       jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamp NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sl_source_file
    ON sentence_labels(source_file);
CREATE INDEX IF NOT EXISTS ix_sl_label
    ON sentence_labels(label);

-- ---------------------------------------------------------------
-- 5) Rule sets + rules (원본 보존형 staging)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rule_sets (
    id            bigserial PRIMARY KEY,
    rule_set_name varchar(200) NOT NULL,
    source_file   varchar(500) NOT NULL,
    version       varchar(20),
    description   text,
    loaded_at     timestamp NOT NULL DEFAULT now(),
    UNIQUE(rule_set_name, version)
);

CREATE TABLE IF NOT EXISTS rules (
    id          bigserial PRIMARY KEY,
    rule_set_id bigint NOT NULL REFERENCES rule_sets(id) ON DELETE CASCADE,
    rule_key    varchar(200),
    pattern     text,
    action      text,
    enabled     boolean NOT NULL DEFAULT true,
    extra       jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamp NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_rules_set
    ON rules(rule_set_id);
CREATE INDEX IF NOT EXISTS ix_rules_key
    ON rules(rule_key);

-- ---------------------------------------------------------------
-- 6) 정제 보정 필드 (데이터 훼손 금지 — 원본 유지, 보정만 신규 컬럼)
-- ---------------------------------------------------------------
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS corrected_source_type varchar(30);
CREATE INDEX IF NOT EXISTS ix_documents_corrected_type
    ON documents(corrected_source_type)
    WHERE corrected_source_type IS NOT NULL;

ALTER TABLE law_meta
    ADD COLUMN IF NOT EXISTS corrected_law_name text,
    ADD COLUMN IF NOT EXISTS normalized_type   varchar(30);
CREATE INDEX IF NOT EXISTS ix_law_meta_norm_type
    ON law_meta(normalized_type)
    WHERE normalized_type IS NOT NULL;

COMMIT;

-- end of 0001

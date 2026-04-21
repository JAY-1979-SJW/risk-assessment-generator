-- 엔진 고도화 1차 — 추적성 컬럼 추가 (ADDITIVE ONLY, 기존 컬럼 무변경)
-- Migration: 004
-- Depends on: 001_assessment_engine_results.sql

-- 1. engine_version 기본값 변경 (신규 INSERT부터 적용)
ALTER TABLE assessment_engine_results
    ALTER COLUMN engine_version SET DEFAULT 'v2.0';

-- 2. risk_db 연계 결과 추적용 컬럼 (모두 nullable — 기존 행 영향 없음)
ALTER TABLE assessment_engine_results
    ADD COLUMN IF NOT EXISTS risk_db_ref_ids    TEXT[]  DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS boosted_conditions TEXT[]  DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS boosted_taxonomy   TEXT[]  DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS evidence_sources   JSONB;

-- 3. 조건 시나리오 매칭 조회용 인덱스 (배열 원소 검색)
CREATE INDEX IF NOT EXISTS idx_aer_boosted_conditions
    ON assessment_engine_results USING GIN (boosted_conditions);

COMMENT ON COLUMN assessment_engine_results.risk_db_ref_ids IS
    '참조된 risk_db 레코드 IDs (조건 시나리오 IDs 등)';
COMMENT ON COLUMN assessment_engine_results.boosted_conditions IS
    '매칭된 condition_scenario IDs (예: SC-001, SC-007)';
COMMENT ON COLUMN assessment_engine_results.boosted_taxonomy IS
    '적용된 work_type codes (예: TEMP_SCAFF, ELEC_PANEL)';
COMMENT ON COLUMN assessment_engine_results.evidence_sources IS
    'retrieval vs risk_db 결과 분리 추적 (evidence_sources JSON)';

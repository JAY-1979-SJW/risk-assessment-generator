-- ======================================================================
-- Migration 0021 : Create document_generation_jobs table
-- Target  : risk-assessment DB
-- Purpose : V1.1 신축공사 MVP — 문서 생성 요청/실행 추적
-- Idempotent : YES
-- 비파괴   : 신규 테이블만 생성
-- ======================================================================

BEGIN;

-- ---------------------------------------------------------------
-- document_generation_jobs : 문서 생성 작업 큐
--  • safety_events → document_generation_jobs → packages/files
--  • job_type: form (핵심서류) | supplemental (부대서류) | package (묶음)
--  • input_snapshot_json: 생성 시점의 입력 데이터 스냅샷 (재생성용)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_generation_jobs (
    id                       SERIAL PRIMARY KEY,
    project_id               INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    safety_event_id          INTEGER REFERENCES safety_events(id) ON DELETE SET NULL,
    requested_by_user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,

    job_type                 VARCHAR(50),
        -- 허용값(주석): form | supplemental | package | manual

    -- 대상 문서 타입 (form_registry / supplementary_registry 키)
    form_type                VARCHAR(150),
    supplemental_type        VARCHAR(150),

    status                   VARCHAR(30) DEFAULT 'pending',
        -- 허용값(주석): pending | running | done | failed | cancelled

    input_snapshot_json      JSONB,
        -- 생성 시점 입력 데이터 스냅샷
    error_message            TEXT,

    started_at               TIMESTAMP,
    finished_at              TIMESTAMP,

    created_at               TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_doc_gen_jobs_project_id     ON document_generation_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_doc_gen_jobs_safety_event   ON document_generation_jobs(safety_event_id);
CREATE INDEX IF NOT EXISTS idx_doc_gen_jobs_status         ON document_generation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_doc_gen_jobs_form_type      ON document_generation_jobs(form_type);
CREATE INDEX IF NOT EXISTS idx_doc_gen_jobs_supplemental   ON document_generation_jobs(supplemental_type);
CREATE INDEX IF NOT EXISTS idx_doc_gen_jobs_requested_by   ON document_generation_jobs(requested_by_user_id);

COMMIT;

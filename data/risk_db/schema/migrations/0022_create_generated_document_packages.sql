-- ======================================================================
-- Migration 0022 : Create generated_document_packages table
-- Target  : risk-assessment DB
-- Purpose : V1.1 신축공사 MVP — 핵심서류 + 부대서류 패키지 관리
-- Idempotent : YES
-- 비파괴   : 신규 테이블만 생성
-- ======================================================================

BEGIN;

-- ---------------------------------------------------------------
-- generated_document_packages : 생성된 문서 패키지(묶음)
--  • Rule 트리거 단위로 핵심서류 + 부대서류를 한 패키지로 묶음
--  • 예) Rule-01(신규근로자) → 패키지: 교육이수증 + PPE지급대장 + 배치확인서
--  • storage_key: 객체스토리지 키 (선택)
--  • zip_file_path: 사용자 다운로드용 압축 파일 경로 (선택)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS generated_document_packages (
    id                       SERIAL PRIMARY KEY,
    project_id               INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    safety_event_id          INTEGER REFERENCES safety_events(id) ON DELETE SET NULL,
    generation_job_id        INTEGER REFERENCES document_generation_jobs(id) ON DELETE SET NULL,

    package_type             VARCHAR(100),
        -- 허용값(주석): worker_onboarding | equipment_intake | phase_kickoff | daily_tbm | etc
    package_name             VARCHAR(200),
    rule_id                  VARCHAR(100),
        -- Rule 식별자 (Rule-01, Rule-02, ...)

    status                   VARCHAR(30) DEFAULT 'created',
        -- 허용값(주석): created | partial | done | failed

    document_count           INTEGER DEFAULT 0,
    storage_key              TEXT,
    zip_file_path            TEXT,

    created_by_user_id       INTEGER REFERENCES users(id) ON DELETE SET NULL,

    created_at               TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_doc_packages_project_id       ON generated_document_packages(project_id);
CREATE INDEX IF NOT EXISTS idx_doc_packages_safety_event     ON generated_document_packages(safety_event_id);
CREATE INDEX IF NOT EXISTS idx_doc_packages_job_id           ON generated_document_packages(generation_job_id);
CREATE INDEX IF NOT EXISTS idx_doc_packages_type             ON generated_document_packages(package_type);
CREATE INDEX IF NOT EXISTS idx_doc_packages_rule_id          ON generated_document_packages(rule_id);
CREATE INDEX IF NOT EXISTS idx_doc_packages_status           ON generated_document_packages(status);

COMMIT;

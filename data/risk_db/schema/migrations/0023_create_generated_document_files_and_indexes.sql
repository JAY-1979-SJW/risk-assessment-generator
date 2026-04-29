-- ======================================================================
-- Migration 0023 : Create generated_document_files + V1.1 final indexes
-- Target  : risk-assessment DB
-- Purpose : V1.1 신축공사 MVP — 개별 문서 파일 메타 + 추가 인덱스
-- Idempotent : YES
-- 비파괴   : 신규 테이블 + 추가 인덱스만 생성
-- ======================================================================

BEGIN;

-- ---------------------------------------------------------------
-- generated_document_files : 패키지 내 개별 문서 파일
--  • 한 패키지 내에 여러 form/supplemental 문서가 있음
--  • document_kind: form (form_registry) | supplemental (supplementary_registry)
--  • storage_key 또는 file_path 중 하나에 위치 정보 보관
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS generated_document_files (
    id                       SERIAL PRIMARY KEY,
    package_id               INTEGER REFERENCES generated_document_packages(id) ON DELETE CASCADE,
    project_id               INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    generation_job_id        INTEGER REFERENCES document_generation_jobs(id) ON DELETE SET NULL,

    document_kind            VARCHAR(50),
        -- 허용값(주석): form | supplemental

    -- form_registry / supplementary_registry 키
    form_type                VARCHAR(150),
    supplemental_type        VARCHAR(150),

    display_name             VARCHAR(200),
        -- 사용자에게 표시되는 한글 문서명
    file_name                VARCHAR(255),
        -- 실제 파일명 (예: 신규근로자교육이수증_20260429.xlsx)
    file_path                TEXT,
        -- 로컬/컨테이너 경로 (선택)
    storage_key              TEXT,
        -- 객체 스토리지 키 (선택)
    file_size                BIGINT,
    mime_type                VARCHAR(100),

    status                   VARCHAR(30) DEFAULT 'created',
        -- 허용값(주석): created | done | failed | archived

    created_at               TIMESTAMP NOT NULL DEFAULT NOW()
);

-- generated_document_files 인덱스
CREATE INDEX IF NOT EXISTS idx_doc_files_package_id     ON generated_document_files(package_id);
CREATE INDEX IF NOT EXISTS idx_doc_files_project_id     ON generated_document_files(project_id);
CREATE INDEX IF NOT EXISTS idx_doc_files_job_id         ON generated_document_files(generation_job_id);
CREATE INDEX IF NOT EXISTS idx_doc_files_kind           ON generated_document_files(document_kind);
CREATE INDEX IF NOT EXISTS idx_doc_files_form_type      ON generated_document_files(form_type);
CREATE INDEX IF NOT EXISTS idx_doc_files_supplemental   ON generated_document_files(supplemental_type);
CREATE INDEX IF NOT EXISTS idx_doc_files_status         ON generated_document_files(status);

-- ---------------------------------------------------------------
-- V1.1 추가 인덱스 (성능 최적화 — 0014~0022 보충)
-- 모든 인덱스는 IF NOT EXISTS 로 멱등성 보장
-- ---------------------------------------------------------------

-- (다른 테이블의 핵심 인덱스는 각 0014~0022 마이그레이션에서 이미 생성됨)
-- 여기서는 누락 가능 항목과 복합 인덱스만 보강

-- projects: manager_id 인덱스 (0014에서 이미 생성, 안전 차원에서 재선언)
CREATE INDEX IF NOT EXISTS idx_projects_manager_id        ON projects(manager_id);

-- workers: 복합 인덱스 (조회 패턴 최적화)
CREATE INDEX IF NOT EXISTS idx_workers_project_status     ON workers(project_id, status);

-- project_equipment: 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_project_equipment_project_status   ON project_equipment(project_id, status);

-- safety_events: 미처리 이벤트 빠른 스캔
CREATE INDEX IF NOT EXISTS idx_safety_events_project_status
    ON safety_events(project_id, status);

-- document_generation_jobs: 미처리 작업 빠른 스캔
CREATE INDEX IF NOT EXISTS idx_doc_gen_jobs_project_status
    ON document_generation_jobs(project_id, status);

-- generated_document_packages: 프로젝트별 최신순 정렬
CREATE INDEX IF NOT EXISTS idx_doc_packages_project_created
    ON generated_document_packages(project_id, created_at DESC);

-- ---------------------------------------------------------------
-- updated_at 자동 갱신 트리거
--   기존 update_updated_at() 함수가 infra/init.sql 에 정의되어 있음.
--   본 마이그레이션에서는 트리거 적용을 보류하고 Stage 2B-3 으로 분리한다.
--   이유: 함수 존재 가정의 안정성 확보, 본 단계는 스키마 생성에 집중.
--
--   TODO(Stage 2B-3 또는 별도 0024 migration):
--     - DROP TRIGGER IF EXISTS trg_<table>_updated_at ON <table>;
--     - CREATE TRIGGER trg_<table>_updated_at
--         BEFORE UPDATE ON <table>
--         FOR EACH ROW EXECUTE FUNCTION update_updated_at();
--   대상 테이블: users, sites, contractors, workers, project_equipment,
--               work_schedules, safety_events,
--               document_generation_jobs, generated_document_packages
-- ---------------------------------------------------------------

COMMIT;

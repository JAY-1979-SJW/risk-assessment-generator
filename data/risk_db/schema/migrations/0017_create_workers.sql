-- ======================================================================
-- Migration 0017 : Create workers table
-- Target  : risk-assessment DB
-- Purpose : V1.1 신축공사 MVP — 근로자 등록 (Rule-01: 신규근로자 트리거)
-- Idempotent : YES
-- 비파괴   : 신규 테이블만 생성
-- ======================================================================

-- 개인정보 최소화 정책:
--   • 주민등록번호 / 외국인등록번호 미저장
--   • 민감 건강정보 미저장
--   • 전화번호도 V1.1에서는 저장하지 않음 (필요 시 V2.0)
--   • 이름/공종/직무/입사일/교육·PPE 체크 상태만 저장

BEGIN;

-- ---------------------------------------------------------------
-- workers : 프로젝트 근로자
--  • 자동생성 Rule-01: 신규근로자 등록 시 교육이수증/PPE/배치확인서 트리거
--  • contractor_id nullable: 직영 또는 미배정 가능
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workers (
    id                                    SERIAL PRIMARY KEY,
    project_id                            INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    contractor_id                         INTEGER REFERENCES contractors(id) ON DELETE SET NULL,

    worker_name                           VARCHAR(100) NOT NULL,
    trade                                 VARCHAR(100),
        -- 공종: 형틀목공 | 철근공 | 콘크리트공 | 비계공 | 전기공 등
    job_role                              VARCHAR(100),
        -- 직무: 작업자 | 반장 | 신호수 | 운전원 등
    first_work_date                       DATE,

    -- 교육/PPE 이수 체크 (Rule-01 검증용)
    construction_basic_training_checked   BOOLEAN DEFAULT FALSE,
        -- 건설업 기초안전보건교육
    new_hire_training_checked             BOOLEAN DEFAULT FALSE,
        -- 신규채용자 교육
    ppe_issued                            BOOLEAN DEFAULT FALSE,
        -- 개인보호구 지급

    status                                VARCHAR(20) DEFAULT 'active',
        -- 허용값(주석): active | retired | suspended

    created_at                            TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                            TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_workers_project_id     ON workers(project_id);
CREATE INDEX IF NOT EXISTS idx_workers_contractor_id  ON workers(contractor_id);
CREATE INDEX IF NOT EXISTS idx_workers_trade          ON workers(trade);
CREATE INDEX IF NOT EXISTS idx_workers_status         ON workers(status);
CREATE INDEX IF NOT EXISTS idx_workers_first_work_date ON workers(first_work_date);

COMMIT;

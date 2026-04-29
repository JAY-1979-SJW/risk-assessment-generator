-- ======================================================================
-- Migration 0016 : Create contractors table
-- Target  : risk-assessment DB
-- Purpose : V1.1 신축공사 MVP — 원청/협력업체 정보
-- Idempotent : YES
-- 비파괴   : 신규 테이블만 생성
-- ======================================================================

BEGIN;

-- ---------------------------------------------------------------
-- contractors : 프로젝트별 시공사/협력업체
--  • contractor_type: prime(원청) | subcontract(협력) | day_labor(일용)
--  • 사업자등록번호는 선택 (외부 일용직은 미보유)
--  • 개인정보 최소화 (대표/담당자 이름/연락처만)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contractors (
    id                          SERIAL PRIMARY KEY,
    project_id                  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    contractor_type             VARCHAR(50),
        -- 허용값(주석): prime | subcontract | day_labor
    company_name                VARCHAR(200) NOT NULL,
    business_registration_no    VARCHAR(50),
    representative_name         VARCHAR(100),

    -- 담당자
    contact_name                VARCHAR(100),
    contact_phone               VARCHAR(50),

    -- 작업 범위
    work_scope                  TEXT,

    -- 안전평가 상태
    safety_evaluation_status    VARCHAR(30),
        -- 허용값(주석): pending | approved | conditional | rejected

    status                      VARCHAR(20) DEFAULT 'active',
        -- 허용값(주석): active | terminated | suspended

    created_at                  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_contractors_project_id      ON contractors(project_id);
CREATE INDEX IF NOT EXISTS idx_contractors_type            ON contractors(contractor_type);
CREATE INDEX IF NOT EXISTS idx_contractors_status          ON contractors(status);
CREATE INDEX IF NOT EXISTS idx_contractors_business_no     ON contractors(business_registration_no);

COMMIT;

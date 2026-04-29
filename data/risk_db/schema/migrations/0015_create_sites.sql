-- ======================================================================
-- Migration 0015 : Create sites table
-- Target  : risk-assessment DB
-- Purpose : V1.1 신축공사 MVP — 현장(사이트) 정보
-- Idempotent : YES
-- 비파괴   : 신규 테이블만 생성
-- ======================================================================

BEGIN;

-- ---------------------------------------------------------------
-- sites : 프로젝트별 현장 정보
--  • 한 프로젝트에 다중 현장 가능 (분리 시공)
--  • 좌표/GPS는 V2.0 후보로 제외
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sites (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    site_name           VARCHAR(200),
    address             TEXT,
    detail_address      TEXT,

    -- 담당자 (이름/연락처만, FK 없음 — 사용자 등록과 별개로 외부 인력일 수 있음)
    site_manager_name   VARCHAR(100),
    site_manager_phone  VARCHAR(50),
    safety_manager_name VARCHAR(100),
    safety_manager_phone VARCHAR(50),

    status              VARCHAR(20) DEFAULT 'active',
        -- 허용값(주석): active | preparing | closed | suspended

    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_sites_project_id ON sites(project_id);
CREATE INDEX IF NOT EXISTS idx_sites_status     ON sites(status);

COMMIT;

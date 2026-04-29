-- ======================================================================
-- Migration 0014 : Extend projects table with V1.1 new construction fields
-- Target  : risk-assessment DB
-- Purpose : V1.1 신축공사 MVP — projects 확장
-- Idempotent : YES (ADD COLUMN IF NOT EXISTS)
-- 비파괴   : 기존 컬럼(id/title/status/created_at/updated_at) 유지, 변경 없음
-- 호환     : 기존 /api/projects CRUD 무영향
-- ======================================================================

BEGIN;

-- ---------------------------------------------------------------
-- projects 확장 : 신축공사 메타정보
--  • 모든 신규 컬럼은 nullable 또는 DEFAULT 보유
--  • NOT NULL 추가 금지 (기존 행 호환)
-- ---------------------------------------------------------------

-- 공사 분류
ALTER TABLE projects ADD COLUMN IF NOT EXISTS construction_type VARCHAR(50) DEFAULT 'new_construction';
    -- 허용값(주석): new_construction | remodeling | civil | other
ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_status     VARCHAR(30);
    -- 허용값(주석): registered | preparing | started | in_progress | completed

-- 일정
ALTER TABLE projects ADD COLUMN IF NOT EXISTS start_date         DATE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS end_date           DATE;

-- 발주/시공
ALTER TABLE projects ADD COLUMN IF NOT EXISTS client_name             VARCHAR(200);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS prime_contractor_name   VARCHAR(200);

-- 위치
ALTER TABLE projects ADD COLUMN IF NOT EXISTS site_address       TEXT;

-- 담당자 (이름)
ALTER TABLE projects ADD COLUMN IF NOT EXISTS site_manager_name   VARCHAR(100);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS safety_manager_name VARCHAR(100);

-- 구조 메타
ALTER TABLE projects ADD COLUMN IF NOT EXISTS total_floor_count       INTEGER;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS basement_floor_count    INTEGER;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS excavation_depth_m      NUMERIC(8, 2);

-- 위험설비 보유
ALTER TABLE projects ADD COLUMN IF NOT EXISTS has_tower_crane         BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS has_pile_driver         BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS has_scaffold_over_31m   BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS safety_plan_required    BOOLEAN DEFAULT FALSE;

-- 위험 등급
ALTER TABLE projects ADD COLUMN IF NOT EXISTS risk_level         VARCHAR(20);
    -- 허용값(주석): low | medium | high | critical

-- 담당 사용자 (FK to users)
ALTER TABLE projects ADD COLUMN IF NOT EXISTS manager_id         INTEGER;

-- ---------------------------------------------------------------
-- FK 제약 (idempotent — 존재 시 skip)
-- ---------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_projects_manager_id'
    ) THEN
        ALTER TABLE projects
          ADD CONSTRAINT fk_projects_manager_id
          FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ---------------------------------------------------------------
-- 인덱스
-- ---------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_projects_construction_type ON projects(construction_type);
CREATE INDEX IF NOT EXISTS idx_projects_project_status    ON projects(project_status);
CREATE INDEX IF NOT EXISTS idx_projects_manager_id        ON projects(manager_id);
CREATE INDEX IF NOT EXISTS idx_projects_risk_level        ON projects(risk_level);

COMMIT;

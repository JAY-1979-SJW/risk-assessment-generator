-- ======================================================================
-- Migration 0019 : Create work_schedules table
-- Target  : risk-assessment DB
-- Purpose : V1.1 신축공사 MVP — 공정 일정 (Phase 0~12, Rule-03 트리거)
-- Idempotent : YES
-- 비파괴   : 신규 테이블만 생성
-- ======================================================================

BEGIN;

-- ---------------------------------------------------------------
-- work_schedules : 프로젝트 공정/작업 일정
--  • Phase 0~12 단계와 연결
--  • Rule-03: 공종 착수 전 작업계획서/허가서 트리거
--  • 일일 TBM 트리거의 기반
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS work_schedules (
    id                       SERIAL PRIMARY KEY,
    project_id               INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Phase 정보
    phase_no                 INTEGER,
        -- 0~12 (Phase 0: 등록, Phase 1: 착공전준비, ...)
    phase_name               VARCHAR(100),

    -- 작업 정보
    work_type                VARCHAR(100),
        -- 허용값(주석): 굴착 | 철근 | 거푸집 | 콘크리트 | 비계 | 고소작업 | 양중 | etc
    work_name                VARCHAR(200),
    location                 TEXT,

    -- 일정
    planned_start_date       DATE,
    planned_end_date         DATE,
    actual_start_date        DATE,
    actual_end_date          DATE,

    -- Rule-03 트리거 플래그
    is_high_risk             BOOLEAN DEFAULT FALSE,
        -- 고위험 작업 여부 (작업계획서 필수)
    requires_work_plan       BOOLEAN DEFAULT FALSE,
        -- 작업계획서 필수 여부
    requires_permit          BOOLEAN DEFAULT FALSE,
        -- 작업허가서 필수 여부 (밀폐/화기/고소 등)

    status                   VARCHAR(30) DEFAULT 'planned',
        -- 허용값(주석): planned | in_progress | completed | suspended | cancelled

    created_at               TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_work_schedules_project_id     ON work_schedules(project_id);
CREATE INDEX IF NOT EXISTS idx_work_schedules_phase_no       ON work_schedules(phase_no);
CREATE INDEX IF NOT EXISTS idx_work_schedules_status         ON work_schedules(status);
CREATE INDEX IF NOT EXISTS idx_work_schedules_planned_start  ON work_schedules(project_id, planned_start_date);
CREATE INDEX IF NOT EXISTS idx_work_schedules_high_risk      ON work_schedules(is_high_risk);

COMMIT;

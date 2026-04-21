-- 위험성 평가 입력 v2 — 현장 조건 필드 추가
-- Policy: additive only (기존 컬럼 변경/삭제 금지)
-- Migration: 002  (requires 001 applied first)

ALTER TABLE project_assessments
    ADD COLUMN IF NOT EXISTS height_m          FLOAT,
    ADD COLUMN IF NOT EXISTS worker_count      INTEGER,
    ADD COLUMN IF NOT EXISTS work_environment  VARCHAR(20),
    ADD COLUMN IF NOT EXISTS night_work        BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS confined_space    BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS hot_work          BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS electrical_work   BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS heavy_equipment   BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS work_at_height    BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS surface_condition VARCHAR(20),
    ADD COLUMN IF NOT EXISTS weather           VARCHAR(20),
    ADD COLUMN IF NOT EXISTS simultaneous_work BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN project_assessments.height_m          IS '작업 높이(m) — NULL=미입력, >= 0';
COMMENT ON COLUMN project_assessments.worker_count      IS '작업 인원 수 — NULL=미입력, >= 1';
COMMENT ON COLUMN project_assessments.work_environment  IS 'indoor / outdoor / mixed';
COMMENT ON COLUMN project_assessments.night_work        IS '야간작업 여부';
COMMENT ON COLUMN project_assessments.confined_space    IS '밀폐공간 작업 여부';
COMMENT ON COLUMN project_assessments.hot_work          IS '화기작업 여부';
COMMENT ON COLUMN project_assessments.electrical_work   IS '전기작업 여부';
COMMENT ON COLUMN project_assessments.heavy_equipment   IS '중장비 사용 여부';
COMMENT ON COLUMN project_assessments.work_at_height    IS '고소작업 여부 (height_m 와 독립 플래그)';
COMMENT ON COLUMN project_assessments.surface_condition IS 'normal / wet / slippery / uneven';
COMMENT ON COLUMN project_assessments.weather           IS 'clear / rain / snow / wind / extreme';
COMMENT ON COLUMN project_assessments.simultaneous_work IS '동시작업 여부';

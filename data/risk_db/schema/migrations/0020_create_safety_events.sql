-- ======================================================================
-- Migration 0020 : Create safety_events table
-- Target  : risk-assessment DB
-- Purpose : V1.1 신축공사 MVP — 자동생성 Rule 트리거 이벤트
-- Idempotent : YES
-- 비파괴   : 신규 테이블만 생성
-- ======================================================================

BEGIN;

-- ---------------------------------------------------------------
-- safety_events : 안전 이벤트 큐 (자동생성 Rule 트리거)
--  • 모든 Rule(Rule-01: 신규근로자, Rule-02: 장비반입, Rule-03: 공종착수,
--           Rule-04: 일일TBM, Rule-05: 사고보고 등)의 진입점
--  • source_type/source_id 로 원천 추적 (workers/equipment/work_schedules)
--  • payload_json 으로 확장 데이터 보관 (스키마 확장 없이)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS safety_events (
    id                    SERIAL PRIMARY KEY,
    project_id            INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    site_id               INTEGER REFERENCES sites(id) ON DELETE SET NULL,

    event_type            VARCHAR(100) NOT NULL,
        -- 허용값(주석):
        --   worker_registered      | Rule-01 (신규근로자)
        --   equipment_registered   | Rule-02 (장비반입)
        --   work_phase_starting    | Rule-03 (공종 착수 전)
        --   daily_tbm              | Rule-04 (일일 TBM)
        --   incident_reported      | 사고/아차사고 보고
        --   improvement_required   | 개선 조치 필요
        --   completion_due         | 개선 완료 예정

    event_date            DATE NOT NULL,

    -- 원천 추적
    source_type           VARCHAR(100),
        -- 허용값(주석): worker | equipment | work_schedule | manual | scheduler
    source_id             INTEGER,
        -- 원천 테이블의 id (FK 미설정 — 다중 원천)

    status                VARCHAR(30) DEFAULT 'pending',
        -- 허용값(주석): pending | processing | done | failed | skipped

    payload_json          JSONB,
        -- 자유 형식 추가 데이터 (rule_id, 트리거 컨텍스트 등)

    created_by_user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,

    created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_safety_events_project_id       ON safety_events(project_id);
CREATE INDEX IF NOT EXISTS idx_safety_events_site_id          ON safety_events(site_id);
CREATE INDEX IF NOT EXISTS idx_safety_events_type_date        ON safety_events(event_type, event_date);
CREATE INDEX IF NOT EXISTS idx_safety_events_status           ON safety_events(status);
CREATE INDEX IF NOT EXISTS idx_safety_events_source           ON safety_events(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_safety_events_created_by       ON safety_events(created_by_user_id);

COMMIT;

-- ======================================================================
-- Migration 0018 : Create project_equipment table
-- Target  : risk-assessment DB
-- Purpose : V1.1 신축공사 MVP — 프로젝트 장비 인스턴스 (Rule-02 트리거)
-- Note    : 운영 DB 기존 equipment(마스터/룩업) 테이블과의 이름 충돌 회피를 위해
--           project_equipment 로 명명.
-- Idempotent : YES
-- 비파괴   : 신규 테이블만 생성
-- ======================================================================

BEGIN;

-- ---------------------------------------------------------------
-- project_equipment : 프로젝트 장비 인스턴스
--  • 자동생성 Rule-02: 장비 반입 시 운전원 자격증/보험증/검사증 트리거
--  • contractor_id nullable: 직영 또는 임대 가능
--  • 운전원 이름만 저장 (자격증 사본은 별도 storage)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS project_equipment (
    id                                SERIAL PRIMARY KEY,
    project_id                        INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    contractor_id                     INTEGER REFERENCES contractors(id) ON DELETE SET NULL,

    equipment_name                    VARCHAR(200) NOT NULL,
    equipment_type                    VARCHAR(100),
        -- 허용값(주석): tower_crane | mobile_crane | excavator | forklift | pile_driver | lift | etc
    registration_no                   VARCHAR(100),
        -- 등록번호/일련번호
    entry_date                        DATE,
    exit_date                         DATE,

    -- 운전원 정보 (이름만)
    operator_name                     VARCHAR(100),

    -- Rule-02 검증 상태
    operator_qualification_checked    BOOLEAN DEFAULT FALSE,
        -- 운전자격증 확인
    insurance_checked                 BOOLEAN DEFAULT FALSE,
        -- 보험증 확인
    inspection_certificate_checked    BOOLEAN DEFAULT FALSE,
        -- 검사증 확인 (안전인증, 정기검사)

    daily_check_required              BOOLEAN DEFAULT TRUE,
        -- 일일점검 대상 여부

    status                            VARCHAR(20) DEFAULT 'active',
        -- 허용값(주석): active | removed | suspended

    created_at                        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                        TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_project_equipment_project_id     ON project_equipment(project_id);
CREATE INDEX IF NOT EXISTS idx_project_equipment_contractor_id  ON project_equipment(contractor_id);
CREATE INDEX IF NOT EXISTS idx_project_equipment_type           ON project_equipment(equipment_type);
CREATE INDEX IF NOT EXISTS idx_project_equipment_status         ON project_equipment(status);
CREATE INDEX IF NOT EXISTS idx_project_equipment_registration   ON project_equipment(registration_no);

COMMIT;

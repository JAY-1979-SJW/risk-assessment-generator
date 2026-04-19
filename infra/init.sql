-- KRAS 위험성평가표 자동생성기 DB 스키마
-- PostgreSQL 16+

-- ── 프로젝트 ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(200) NOT NULL DEFAULT '새 위험성평가',
    status      VARCHAR(20)  NOT NULL DEFAULT 'draft',  -- draft / active / completed
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── 기본정보 (1:1) ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_company_info (
    id             SERIAL PRIMARY KEY,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    company_name   VARCHAR(200) DEFAULT '',
    ceo_name       VARCHAR(100) DEFAULT '',
    business_type  VARCHAR(100) DEFAULT '',
    address        TEXT         DEFAULT '',
    site_name      VARCHAR(200) DEFAULT '',
    work_type      VARCHAR(100) DEFAULT '',
    eval_date      DATE,
    eval_type      VARCHAR(20)  DEFAULT '정기평가',
    safety_policy  TEXT         DEFAULT '',
    safety_goal    TEXT         DEFAULT '',
    UNIQUE (project_id)
);

-- ── 조직구성 (1:N) ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_org_members (
    id             SERIAL PRIMARY KEY,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    sort_order     INTEGER NOT NULL DEFAULT 0,
    position       VARCHAR(100) DEFAULT '',
    name           VARCHAR(100) DEFAULT '',
    role           VARCHAR(100) DEFAULT '',
    responsibility TEXT         DEFAULT ''
);

-- ── 위험성평가 항목 (1:N) ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_assessments (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    sort_order          INTEGER NOT NULL DEFAULT 0,
    process             VARCHAR(200) DEFAULT '',
    sub_work            VARCHAR(200) DEFAULT '',
    risk_category       VARCHAR(100) DEFAULT '',
    risk_detail         VARCHAR(100) DEFAULT '',
    risk_situation      TEXT         DEFAULT '',
    legal_basis         TEXT         DEFAULT '',
    current_measures    TEXT         DEFAULT '',
    eval_scale          VARCHAR(10)  DEFAULT '3x3',
    possibility         SMALLINT     DEFAULT 1 CHECK (possibility BETWEEN 1 AND 3),
    severity            SMALLINT     DEFAULT 1 CHECK (severity    BETWEEN 1 AND 3),
    current_risk        SMALLINT     GENERATED ALWAYS AS (possibility * severity) STORED,
    current_risk_level  VARCHAR(10)  DEFAULT '낮음',
    reduction_measures  TEXT         DEFAULT '',
    after_possibility   SMALLINT     DEFAULT 1 CHECK (after_possibility BETWEEN 1 AND 3),
    after_severity      SMALLINT     DEFAULT 1 CHECK (after_severity    BETWEEN 1 AND 3),
    after_risk          SMALLINT     GENERATED ALWAYS AS (after_possibility * after_severity) STORED,
    after_risk_level    VARCHAR(10)  DEFAULT '낮음',
    due_date            DATE,
    complete_date       DATE,
    manager             VARCHAR(100) DEFAULT '',
    note                TEXT         DEFAULT '',
    created_at          TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── 회의/교육/안전점검 (각 1:1) ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_forms (
    id          SERIAL PRIMARY KEY,
    project_id  INTEGER     NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    form_type   VARCHAR(20) NOT NULL,  -- meeting / education / safety_meeting
    held_date   DATE,
    location    VARCHAR(200) DEFAULT '',
    agenda      TEXT         DEFAULT '',
    result      TEXT         DEFAULT '',
    next_action TEXT         DEFAULT '',
    UNIQUE (project_id, form_type)
);

CREATE TABLE IF NOT EXISTS project_form_attendees (
    id          SERIAL PRIMARY KEY,
    form_id     INTEGER     NOT NULL REFERENCES project_forms(id) ON DELETE CASCADE,
    sort_order  INTEGER     NOT NULL DEFAULT 0,
    department  VARCHAR(100) DEFAULT '',
    position    VARCHAR(100) DEFAULT '',
    name        VARCHAR(100) DEFAULT ''
);

-- ── 인덱스 ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_company_project  ON project_company_info(project_id);
CREATE INDEX IF NOT EXISTS idx_org_project      ON project_org_members(project_id);
CREATE INDEX IF NOT EXISTS idx_assess_project   ON project_assessments(project_id);
CREATE INDEX IF NOT EXISTS idx_forms_project    ON project_forms(project_id);
CREATE INDEX IF NOT EXISTS idx_attendees_form   ON project_form_attendees(form_id);

-- ── updated_at 자동 갱신 트리거 ───────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_projects_updated_at ON projects;
CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

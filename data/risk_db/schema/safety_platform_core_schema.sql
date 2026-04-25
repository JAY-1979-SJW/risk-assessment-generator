-- =====================================================================
-- Safety Platform Core Schema (확장 스키마)
-- 버전  : 1.0
-- 작성일: 2026-04-24
-- 목적  : 프로젝트/근로자/장비/교육/서류/점검/법령 도메인 연결 골격
-- 범위  : DDL 초안 — 실제 DB 적용 금지 (설계 확정 단계)
-- 규칙  : 기존 테이블(documents, hazards, work_types, equipment 등) 변경 없음
--        신규 테이블은 sp_ prefix 사용하여 충돌 방지
--        CREATE TABLE IF NOT EXISTS 기반 (멱등성 보장)
--        trigger/function/enum 타입 미생성 (기존 스키마 정책 동일)
-- =====================================================================


-- =====================================================================
-- A. 현장/프로젝트
-- =====================================================================

-- ---------------------------------------------------------------------
-- A1) sp_projects : 공사 현장 / 사업장 단위
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_projects (
    id                  BIGSERIAL PRIMARY KEY,
    project_code        VARCHAR(50)  NOT NULL UNIQUE,
    name                TEXT         NOT NULL,
    address             TEXT,
    industry_type       VARCHAR(50),
        -- 예: construction | manufacturing | logistics | chemical
    contract_amount     NUMERIC(15, 0),
    start_date          DATE,
    end_date            DATE,
    status              VARCHAR(20)  NOT NULL DEFAULT 'active',
        -- 허용값(주석): active | closed | suspended
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sp_projects_status ON sp_projects(status);
CREATE INDEX IF NOT EXISTS ix_sp_projects_industry ON sp_projects(industry_type);


-- ---------------------------------------------------------------------
-- A2) sp_work_items : 현장 내 개별 작업 항목
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_work_items (
    id                  BIGSERIAL PRIMARY KEY,
    project_id          BIGINT       NOT NULL,
    work_type_code      VARCHAR(50),
        -- Knowledge DB work_types.work_type_code 참조 (FK 미설정 — 운영 단계에서 추가)
    work_name           TEXT         NOT NULL,
    work_location       TEXT,
    planned_start       DATE,
    planned_end         DATE,
    status              VARCHAR(20)  NOT NULL DEFAULT 'planned',
        -- 허용값(주석): planned | active | completed | suspended
    hazard_level        VARCHAR(10)  DEFAULT 'medium',
        -- 허용값(주석): low | medium | high | critical
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_work_items_project
        FOREIGN KEY (project_id) REFERENCES sp_projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_sp_work_items_project ON sp_work_items(project_id);
CREATE INDEX IF NOT EXISTS ix_sp_work_items_work_type ON sp_work_items(work_type_code);
CREATE INDEX IF NOT EXISTS ix_sp_work_items_status ON sp_work_items(status);


-- =====================================================================
-- B. 근로자/관리자
-- =====================================================================

-- ---------------------------------------------------------------------
-- B1) sp_worker_roles : 역할 코드 마스터
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_worker_roles (
    role_code           VARCHAR(30)  PRIMARY KEY,
    role_name           VARCHAR(100) NOT NULL UNIQUE,
    is_manager          BOOLEAN      DEFAULT FALSE,
        -- TRUE: 안전관리자/보건관리자/관리감독자
    sort_order          INTEGER      DEFAULT 0,
    is_active           BOOLEAN      DEFAULT TRUE
);


-- ---------------------------------------------------------------------
-- B2) sp_workers : 근로자/관리자 개인 정보
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_workers (
    id                  BIGSERIAL PRIMARY KEY,
    worker_no           VARCHAR(50)  UNIQUE,
        -- 사내 직번 또는 외부 ID
    name                TEXT         NOT NULL,
    birth_date          DATE,
    contact             VARCHAR(50),
    company_name        TEXT,
        -- 도급업체명 (직영이면 NULL 또는 주계약사명)
    is_subcontractor    BOOLEAN      DEFAULT FALSE,
    status              VARCHAR(20)  NOT NULL DEFAULT 'active',
        -- 허용값(주석): active | retired | suspended
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sp_workers_status ON sp_workers(status);
CREATE INDEX IF NOT EXISTS ix_sp_workers_company ON sp_workers(company_name);


-- ---------------------------------------------------------------------
-- B3) sp_worker_assignments : 근로자 현장 배치
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_worker_assignments (
    id                  BIGSERIAL PRIMARY KEY,
    worker_id           BIGINT       NOT NULL,
    project_id          BIGINT       NOT NULL,
    role_code           VARCHAR(30),
    assigned_date       DATE         NOT NULL,
    released_date       DATE,
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_wa_worker
        FOREIGN KEY (worker_id) REFERENCES sp_workers(id) ON DELETE CASCADE,
    CONSTRAINT fk_sp_wa_project
        FOREIGN KEY (project_id) REFERENCES sp_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_sp_wa_role
        FOREIGN KEY (role_code) REFERENCES sp_worker_roles(role_code) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS ix_sp_wa_worker ON sp_worker_assignments(worker_id);
CREATE INDEX IF NOT EXISTS ix_sp_wa_project ON sp_worker_assignments(project_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_sp_wa_active
    ON sp_worker_assignments(worker_id, project_id)
    WHERE released_date IS NULL;


-- ---------------------------------------------------------------------
-- B4) sp_worker_licenses : 자격/면허 보유 이력
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_worker_licenses (
    id                  BIGSERIAL PRIMARY KEY,
    worker_id           BIGINT       NOT NULL,
    license_type        VARCHAR(100) NOT NULL,
        -- 예: 크레인운전기능사 | 타워크레인운전기능사 | 지게차운전기능사 등
    license_no          VARCHAR(100),
    issued_date         DATE,
    expiry_date         DATE,
    issuing_authority   VARCHAR(200),
    source_type         VARCHAR(30)  DEFAULT 'law',
        -- 허용값(주석): law | kosha | moel | practical | NEEDS_VERIFICATION
    status              VARCHAR(20)  DEFAULT 'valid',
        -- 허용값(주석): valid | expired | revoked
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_wl_worker
        FOREIGN KEY (worker_id) REFERENCES sp_workers(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_sp_wl_worker ON sp_worker_licenses(worker_id);
CREATE INDEX IF NOT EXISTS ix_sp_wl_type ON sp_worker_licenses(license_type);


-- =====================================================================
-- C. 장비 (인스턴스 레벨)
-- =====================================================================

-- ---------------------------------------------------------------------
-- C1) sp_equipment_types : 장비 유형 분류 마스터
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_equipment_types (
    type_code           VARCHAR(30)  PRIMARY KEY,
        -- 예: access | lifting | transport | earthwork 등
    type_name_ko        VARCHAR(100) NOT NULL UNIQUE,
    description         TEXT,
    knowledge_eq_prefix VARCHAR(20),
        -- Knowledge DB equipment.equipment_code의 대응 prefix (예: EQ_SCAFF → EQ_)
    sort_order          INTEGER      DEFAULT 0,
    is_active           BOOLEAN      DEFAULT TRUE
);


-- ---------------------------------------------------------------------
-- C2) sp_equipments : 현장 배치 장비 인스턴스
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_equipments (
    id                  BIGSERIAL PRIMARY KEY,
    project_id          BIGINT       NOT NULL,
    equipment_code      VARCHAR(50)  NOT NULL,
        -- Knowledge DB equipment.equipment_code 참조
    serial_no           VARCHAR(100),
    manufacturer        TEXT,
    model_name          TEXT,
    capacity            TEXT,
        -- 예: 10ton, 5m3, 80kW 등
    installed_date      DATE,
    removed_date        DATE,
    status              VARCHAR(20)  NOT NULL DEFAULT 'active',
        -- 허용값(주석): active | removed | suspended
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_eq_project
        FOREIGN KEY (project_id) REFERENCES sp_projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_sp_eq_project ON sp_equipments(project_id);
CREATE INDEX IF NOT EXISTS ix_sp_eq_code ON sp_equipments(equipment_code);
CREATE INDEX IF NOT EXISTS ix_sp_eq_status ON sp_equipments(status);


-- ---------------------------------------------------------------------
-- C3) sp_equipment_assignments : 장비 작업 항목 배치
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_equipment_assignments (
    id                  BIGSERIAL PRIMARY KEY,
    equipment_id        BIGINT       NOT NULL,
    work_item_id        BIGINT       NOT NULL,
    assigned_date       DATE         NOT NULL,
    released_date       DATE,
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_eqa_equipment
        FOREIGN KEY (equipment_id) REFERENCES sp_equipments(id) ON DELETE CASCADE,
    CONSTRAINT fk_sp_eqa_work_item
        FOREIGN KEY (work_item_id) REFERENCES sp_work_items(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_sp_eqa_equipment ON sp_equipment_assignments(equipment_id);
CREATE INDEX IF NOT EXISTS ix_sp_eqa_work_item ON sp_equipment_assignments(work_item_id);


-- ---------------------------------------------------------------------
-- C4) sp_equipment_inspections : 장비 점검 기록
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_equipment_inspections (
    id                  BIGSERIAL PRIMARY KEY,
    equipment_id        BIGINT       NOT NULL,
    inspection_type     VARCHAR(50)  NOT NULL,
        -- 허용값(주석): daily | monthly | quarterly | annual | pre_work | special
    inspection_date     DATE         NOT NULL,
    inspector_worker_id BIGINT,
    result              VARCHAR(20)  NOT NULL DEFAULT 'pass',
        -- 허용값(주석): pass | fail | conditional
    defect_note         TEXT,
    action_taken        TEXT,
    next_inspection_date DATE,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_ei_equipment
        FOREIGN KEY (equipment_id) REFERENCES sp_equipments(id) ON DELETE CASCADE,
    CONSTRAINT fk_sp_ei_inspector
        FOREIGN KEY (inspector_worker_id) REFERENCES sp_workers(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_sp_ei_equipment ON sp_equipment_inspections(equipment_id);
CREATE INDEX IF NOT EXISTS ix_sp_ei_date ON sp_equipment_inspections(inspection_date);


-- =====================================================================
-- D. 교육
-- =====================================================================

-- ---------------------------------------------------------------------
-- D1) sp_training_types : 교육 유형 마스터
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_training_types (
    training_code       VARCHAR(50)  PRIMARY KEY,
    training_name       VARCHAR(200) NOT NULL UNIQUE,
    category            VARCHAR(50),
        -- 허용값(주석): regular | onboarding | special | tbm | msds | confined_space | etc
    required_hours      NUMERIC(5, 1),
    cycle               VARCHAR(50),
        -- 예: 매반기 | 매분기 | 채용시 | 작업변경시 | 수시
    legal_basis         TEXT,
    source_type         VARCHAR(30)  DEFAULT 'law',
        -- 허용값(주석): law | kosha | moel | practical | internal | NEEDS_VERIFICATION
    is_mandatory        BOOLEAN      DEFAULT TRUE,
    sort_order          INTEGER      DEFAULT 0,
    is_active           BOOLEAN      DEFAULT TRUE
);


-- ---------------------------------------------------------------------
-- D2) sp_training_requirements : 작업유형/장비별 필수 교육 매핑 마스터
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_training_requirements (
    id                  BIGSERIAL PRIMARY KEY,
    target_type         VARCHAR(20)  NOT NULL,
        -- 허용값(주석): work_type | equipment | hazard | role
    target_code         VARCHAR(50)  NOT NULL,
        -- target_type에 따라 work_type_code / equipment_code / hazard_code / role_code
    training_code       VARCHAR(50)  NOT NULL,
    required_hours      NUMERIC(5, 1),
    note                TEXT,
    source_type         VARCHAR(30)  DEFAULT 'law',
    verification_status VARCHAR(30)  DEFAULT 'confirmed',
        -- 허용값(주석): confirmed | NEEDS_VERIFICATION | TODO

    CONSTRAINT fk_sp_tr_training
        FOREIGN KEY (training_code) REFERENCES sp_training_types(training_code) ON DELETE CASCADE,
    CONSTRAINT uq_sp_tr UNIQUE (target_type, target_code, training_code)
);
CREATE INDEX IF NOT EXISTS ix_sp_tr_target ON sp_training_requirements(target_type, target_code);
CREATE INDEX IF NOT EXISTS ix_sp_tr_training ON sp_training_requirements(training_code);


-- ---------------------------------------------------------------------
-- D3) sp_training_sessions : 교육 실시 기록 (현장 단위)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_training_sessions (
    id                  BIGSERIAL PRIMARY KEY,
    project_id          BIGINT       NOT NULL,
    training_code       VARCHAR(50)  NOT NULL,
    session_date        DATE         NOT NULL,
    duration_hours      NUMERIC(5, 1),
    instructor_name     TEXT,
    instructor_org      TEXT,
    location            TEXT,
    topic               TEXT,
    attendee_count      INTEGER      DEFAULT 0,
    document_instance_id BIGINT,
        -- 생성된 교육일지 서류 인스턴스 (FK 아래 참조)
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_ts_project
        FOREIGN KEY (project_id) REFERENCES sp_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_sp_ts_training
        FOREIGN KEY (training_code) REFERENCES sp_training_types(training_code) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS ix_sp_ts_project ON sp_training_sessions(project_id);
CREATE INDEX IF NOT EXISTS ix_sp_ts_date ON sp_training_sessions(session_date);
CREATE INDEX IF NOT EXISTS ix_sp_ts_training ON sp_training_sessions(training_code);


-- ---------------------------------------------------------------------
-- D4) sp_worker_training_history : 개인별 교육 이수 이력
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_worker_training_history (
    id                  BIGSERIAL PRIMARY KEY,
    worker_id           BIGINT       NOT NULL,
    session_id          BIGINT,
        -- sp_training_sessions 참조 (외부 교육은 NULL)
    training_code       VARCHAR(50)  NOT NULL,
    completed_date      DATE         NOT NULL,
    completed_hours     NUMERIC(5, 1),
    pass_yn             BOOLEAN      DEFAULT TRUE,
    certificate_no      VARCHAR(100),
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_wth_worker
        FOREIGN KEY (worker_id) REFERENCES sp_workers(id) ON DELETE CASCADE,
    CONSTRAINT fk_sp_wth_session
        FOREIGN KEY (session_id) REFERENCES sp_training_sessions(id) ON DELETE SET NULL,
    CONSTRAINT fk_sp_wth_training
        FOREIGN KEY (training_code) REFERENCES sp_training_types(training_code) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS ix_sp_wth_worker ON sp_worker_training_history(worker_id);
CREATE INDEX IF NOT EXISTS ix_sp_wth_training ON sp_worker_training_history(training_code);
CREATE INDEX IF NOT EXISTS ix_sp_wth_date ON sp_worker_training_history(completed_date);


-- =====================================================================
-- E. 서류
-- =====================================================================

-- ---------------------------------------------------------------------
-- E1) sp_document_catalog : 90종 서류 마스터
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_document_catalog (
    doc_id              VARCHAR(20)  PRIMARY KEY,
        -- 예: RISK-001, EDU-001, WP-001 등
    doc_name_ko         TEXT         NOT NULL,
    category_lv1        VARCHAR(50),
        -- 예: 위험성평가 | 교육기록 | 작업계획서 | 재해보고 | 회의록 | 도급관리 | 유해위험방지
    category_lv2        VARCHAR(50),
    legal_basis         TEXT,
    obligation_type     VARCHAR(100),
        -- 예: 작성·보존 | 작성·비치 | 제출 | 작성·보존(3년)
    legal_form_exists   BOOLEAN      DEFAULT FALSE,
    source_authority    VARCHAR(30),
        -- 허용값(주석): A_OFFICIAL | B_GUIDE | GEN_INTERNAL
    current_status      VARCHAR(20)  NOT NULL DEFAULT 'TODO',
        -- 허용값(주석): DONE | PARTIAL | TODO | EXCLUDED
    form_type           VARCHAR(100),
        -- form_registry.py의 form_type 키 (builder 있으면 연결)
    autofill_ratio      NUMERIC(5, 2),
        -- 자동 채움 가능 비율 0.0~1.0
    priority            VARCHAR(5),
        -- 허용값(주석): P0 | P1 | P2 | P3 | P4 | EXCLUDED
    verification_status VARCHAR(30)  DEFAULT 'confirmed',
        -- 허용값(주석): confirmed | NEEDS_VERIFICATION | TODO
    note                TEXT,
    sort_order          INTEGER      DEFAULT 0,
    is_active           BOOLEAN      DEFAULT TRUE,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sp_dc_category ON sp_document_catalog(category_lv1);
CREATE INDEX IF NOT EXISTS ix_sp_dc_status ON sp_document_catalog(current_status);
CREATE INDEX IF NOT EXISTS ix_sp_dc_priority ON sp_document_catalog(priority);


-- ---------------------------------------------------------------------
-- E2) sp_document_templates : 빌더/템플릿 연결 정보
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_document_templates (
    id                  BIGSERIAL PRIMARY KEY,
    doc_id              VARCHAR(20)  NOT NULL,
    template_version    VARCHAR(20)  NOT NULL DEFAULT 'v1',
    form_type           VARCHAR(100),
        -- form_registry.py form_type 키
    builder_module      TEXT,
        -- 예: engine.output.form_registry
    template_file_path  TEXT,
        -- data/forms/ 아래 원본 파일 경로
    source_authority    VARCHAR(30),
    is_current          BOOLEAN      DEFAULT TRUE,
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_dt_catalog
        FOREIGN KEY (doc_id) REFERENCES sp_document_catalog(doc_id) ON DELETE CASCADE,
    CONSTRAINT uq_sp_dt UNIQUE (doc_id, template_version)
);
CREATE INDEX IF NOT EXISTS ix_sp_dt_doc ON sp_document_templates(doc_id);
CREATE INDEX IF NOT EXISTS ix_sp_dt_form_type ON sp_document_templates(form_type);


-- ---------------------------------------------------------------------
-- E3) sp_document_instances : 실제 생성/보존 서류 인스턴스
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_document_instances (
    id                  BIGSERIAL PRIMARY KEY,
    doc_id              VARCHAR(20)  NOT NULL,
    project_id          BIGINT       NOT NULL,
    work_item_id        BIGINT,
    generated_at        TIMESTAMP    NOT NULL DEFAULT now(),
    generated_by        VARCHAR(100),
    file_path           TEXT,
    file_sha256         VARCHAR(64),
    retention_until     DATE,
    status              VARCHAR(20)  NOT NULL DEFAULT 'draft',
        -- 허용값(주석): draft | finalized | submitted | archived | superseded
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_di_catalog
        FOREIGN KEY (doc_id) REFERENCES sp_document_catalog(doc_id) ON DELETE RESTRICT,
    CONSTRAINT fk_sp_di_project
        FOREIGN KEY (project_id) REFERENCES sp_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_sp_di_work_item
        FOREIGN KEY (work_item_id) REFERENCES sp_work_items(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_sp_di_project ON sp_document_instances(project_id);
CREATE INDEX IF NOT EXISTS ix_sp_di_doc ON sp_document_instances(doc_id);
CREATE INDEX IF NOT EXISTS ix_sp_di_status ON sp_document_instances(status);


-- =====================================================================
-- F. 점검/허가
-- =====================================================================

-- ---------------------------------------------------------------------
-- F1) sp_inspection_types : 점검 유형 마스터
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_inspection_types (
    inspection_code     VARCHAR(50)  PRIMARY KEY,
    inspection_name     VARCHAR(200) NOT NULL UNIQUE,
    target_type         VARCHAR(30),
        -- 허용값(주석): equipment | workplace | process | chemical
    cycle               VARCHAR(50),
        -- 예: 작업 전 매일 | 월 1회 | 분기 1회
    legal_basis         TEXT,
    source_type         VARCHAR(30)  DEFAULT 'law',
    sort_order          INTEGER      DEFAULT 0,
    is_active           BOOLEAN      DEFAULT TRUE
);


-- ---------------------------------------------------------------------
-- F2) sp_inspection_records : 점검 실시 기록
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_inspection_records (
    id                  BIGSERIAL PRIMARY KEY,
    project_id          BIGINT       NOT NULL,
    inspection_code     VARCHAR(50)  NOT NULL,
    target_type         VARCHAR(30),
        -- equipment | work_item | area
    target_id           BIGINT,
        -- sp_equipments.id 또는 sp_work_items.id
    inspection_date     DATE         NOT NULL,
    inspector_worker_id BIGINT,
    result              VARCHAR(20)  NOT NULL DEFAULT 'pass',
    defect_items        JSONB        DEFAULT '[]'::jsonb,
    action_taken        TEXT,
    document_instance_id BIGINT,
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_ir_project
        FOREIGN KEY (project_id) REFERENCES sp_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_sp_ir_type
        FOREIGN KEY (inspection_code) REFERENCES sp_inspection_types(inspection_code) ON DELETE RESTRICT,
    CONSTRAINT fk_sp_ir_inspector
        FOREIGN KEY (inspector_worker_id) REFERENCES sp_workers(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_sp_ir_project ON sp_inspection_records(project_id);
CREATE INDEX IF NOT EXISTS ix_sp_ir_type ON sp_inspection_records(inspection_code);
CREATE INDEX IF NOT EXISTS ix_sp_ir_date ON sp_inspection_records(inspection_date);


-- ---------------------------------------------------------------------
-- F3) sp_permit_types : 작업허가서 유형 마스터
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_permit_types (
    permit_code         VARCHAR(50)  PRIMARY KEY,
    permit_name         VARCHAR(200) NOT NULL UNIQUE,
    legal_basis         TEXT,
    source_type         VARCHAR(30)  DEFAULT 'law',
    doc_id              VARCHAR(20),
        -- sp_document_catalog.doc_id 참조 (허가서 서류가 있으면)
    is_active           BOOLEAN      DEFAULT TRUE
);


-- ---------------------------------------------------------------------
-- F4) sp_permit_records : 작업허가서 발행 이력
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_permit_records (
    id                  BIGSERIAL PRIMARY KEY,
    project_id          BIGINT       NOT NULL,
    permit_code         VARCHAR(50)  NOT NULL,
    work_item_id        BIGINT,
    issued_at           TIMESTAMP    NOT NULL DEFAULT now(),
    issued_by           VARCHAR(100),
    valid_from          TIMESTAMP,
    valid_until         TIMESTAMP,
    approved_by         VARCHAR(100),
    status              VARCHAR(20)  NOT NULL DEFAULT 'issued',
        -- 허용값(주석): issued | completed | cancelled | revoked
    document_instance_id BIGINT,
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_pr_project
        FOREIGN KEY (project_id) REFERENCES sp_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_sp_pr_permit_type
        FOREIGN KEY (permit_code) REFERENCES sp_permit_types(permit_code) ON DELETE RESTRICT,
    CONSTRAINT fk_sp_pr_work_item
        FOREIGN KEY (work_item_id) REFERENCES sp_work_items(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_sp_pr_project ON sp_permit_records(project_id);
CREATE INDEX IF NOT EXISTS ix_sp_pr_permit ON sp_permit_records(permit_code);
CREATE INDEX IF NOT EXISTS ix_sp_pr_status ON sp_permit_records(status);


-- =====================================================================
-- G. 법령/근거 (Compliance)
-- =====================================================================

-- ---------------------------------------------------------------------
-- G1) sp_compliance_sources : 법령/고시/KOSHA 출처 마스터
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_compliance_sources (
    source_code         VARCHAR(50)  PRIMARY KEY,
    source_name         TEXT         NOT NULL,
    source_type         VARCHAR(30)  NOT NULL,
        -- 허용값(주석): law | kosha | moel | practical | internal | NEEDS_VERIFICATION
    issuing_authority   VARCHAR(200),
    effective_date      DATE,
    knowledge_doc_id    BIGINT,
        -- Knowledge DB documents.id 참조 (있는 경우)
    url                 TEXT,
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sp_cs_type ON sp_compliance_sources(source_type);


-- ---------------------------------------------------------------------
-- G2) sp_compliance_clauses : 조항 단위 항목
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_compliance_clauses (
    id                  BIGSERIAL PRIMARY KEY,
    source_code         VARCHAR(50)  NOT NULL,
    article_no          VARCHAR(100) NOT NULL,
    paragraph_no        VARCHAR(50),
    item_no             VARCHAR(50),
    clause_text         TEXT,
    obligation_type     VARCHAR(50),
        -- 예: 작성의무 | 비치의무 | 교육의무 | 점검의무 | 신고의무
    verification_status VARCHAR(30)  DEFAULT 'confirmed',
        -- 허용값(주석): confirmed | NEEDS_VERIFICATION | TODO
    note                TEXT,
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_cc_source
        FOREIGN KEY (source_code) REFERENCES sp_compliance_sources(source_code) ON DELETE CASCADE,
    CONSTRAINT uq_sp_cc UNIQUE (source_code, article_no, paragraph_no, item_no)
);
CREATE INDEX IF NOT EXISTS ix_sp_cc_source ON sp_compliance_clauses(source_code);
CREATE INDEX IF NOT EXISTS ix_sp_cc_obligation ON sp_compliance_clauses(obligation_type);


-- ---------------------------------------------------------------------
-- G3) sp_compliance_links : 서류/교육/점검과 법령 조항의 N:M 연결
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_compliance_links (
    id                  BIGSERIAL PRIMARY KEY,
    clause_id           BIGINT       NOT NULL,
    target_type         VARCHAR(20)  NOT NULL,
        -- 허용값(주석): document | training | inspection | license | permit
    target_id           VARCHAR(50)  NOT NULL,
        -- target_type에 따라 doc_id / training_code / inspection_code / license_type / permit_code
    link_note           TEXT,
    verification_status VARCHAR(30)  DEFAULT 'confirmed',
        -- 허용값(주석): confirmed | NEEDS_VERIFICATION | TODO
    created_at          TIMESTAMP    NOT NULL DEFAULT now(),

    CONSTRAINT fk_sp_cl_clause
        FOREIGN KEY (clause_id) REFERENCES sp_compliance_clauses(id) ON DELETE CASCADE,
    CONSTRAINT uq_sp_cl UNIQUE (clause_id, target_type, target_id)
);
CREATE INDEX IF NOT EXISTS ix_sp_cl_clause ON sp_compliance_links(clause_id);
CREATE INDEX IF NOT EXISTS ix_sp_cl_target ON sp_compliance_links(target_type, target_id);


-- =====================================================================
-- H. 핵심 매핑 (Requirements)
-- =====================================================================

-- ---------------------------------------------------------------------
-- H1) sp_work_document_requirements : 작업유형별 필수 서류
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_work_document_requirements (
    id                  BIGSERIAL PRIMARY KEY,
    work_type_code      VARCHAR(50)  NOT NULL,
        -- Knowledge DB work_types.work_type_code 참조
    doc_id              VARCHAR(20)  NOT NULL,
    condition_note      TEXT,
        -- 예: 굴착면 2m 이상인 경우 | 100인 이상 사업장
    source_type         VARCHAR(30)  DEFAULT 'law',
    verification_status VARCHAR(30)  DEFAULT 'confirmed',

    CONSTRAINT fk_sp_wdr_doc
        FOREIGN KEY (doc_id) REFERENCES sp_document_catalog(doc_id) ON DELETE CASCADE,
    CONSTRAINT uq_sp_wdr UNIQUE (work_type_code, doc_id)
);
CREATE INDEX IF NOT EXISTS ix_sp_wdr_work_type ON sp_work_document_requirements(work_type_code);
CREATE INDEX IF NOT EXISTS ix_sp_wdr_doc ON sp_work_document_requirements(doc_id);


-- ---------------------------------------------------------------------
-- H2) sp_equipment_document_requirements : 장비별 필수 서류
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_equipment_document_requirements (
    id                  BIGSERIAL PRIMARY KEY,
    equipment_code      VARCHAR(50)  NOT NULL,
        -- Knowledge DB equipment.equipment_code 참조
    doc_id              VARCHAR(20)  NOT NULL,
    condition_note      TEXT,
    source_type         VARCHAR(30)  DEFAULT 'law',
    verification_status VARCHAR(30)  DEFAULT 'confirmed',

    CONSTRAINT fk_sp_edr_doc
        FOREIGN KEY (doc_id) REFERENCES sp_document_catalog(doc_id) ON DELETE CASCADE,
    CONSTRAINT uq_sp_edr UNIQUE (equipment_code, doc_id)
);
CREATE INDEX IF NOT EXISTS ix_sp_edr_equipment ON sp_equipment_document_requirements(equipment_code);
CREATE INDEX IF NOT EXISTS ix_sp_edr_doc ON sp_equipment_document_requirements(doc_id);


-- ---------------------------------------------------------------------
-- H3) sp_equipment_training_requirements : 장비별 필수 교육
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_equipment_training_requirements (
    id                  BIGSERIAL PRIMARY KEY,
    equipment_code      VARCHAR(50)  NOT NULL,
    training_code       VARCHAR(50)  NOT NULL,
    required_hours      NUMERIC(5, 1),
    condition_note      TEXT,
    source_type         VARCHAR(30)  DEFAULT 'law',
    verification_status VARCHAR(30)  DEFAULT 'confirmed',

    CONSTRAINT fk_sp_etr_training
        FOREIGN KEY (training_code) REFERENCES sp_training_types(training_code) ON DELETE CASCADE,
    CONSTRAINT uq_sp_etr UNIQUE (equipment_code, training_code)
);
CREATE INDEX IF NOT EXISTS ix_sp_etr_equipment ON sp_equipment_training_requirements(equipment_code);
CREATE INDEX IF NOT EXISTS ix_sp_etr_training ON sp_equipment_training_requirements(training_code);


-- ---------------------------------------------------------------------
-- H4) sp_work_training_requirements : 작업유형별 필수 교육
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_work_training_requirements (
    id                  BIGSERIAL PRIMARY KEY,
    work_type_code      VARCHAR(50)  NOT NULL,
    training_code       VARCHAR(50)  NOT NULL,
    required_hours      NUMERIC(5, 1),
    condition_note      TEXT,
    source_type         VARCHAR(30)  DEFAULT 'law',
    verification_status VARCHAR(30)  DEFAULT 'confirmed',

    CONSTRAINT fk_sp_wtr_training
        FOREIGN KEY (training_code) REFERENCES sp_training_types(training_code) ON DELETE CASCADE,
    CONSTRAINT uq_sp_wtr UNIQUE (work_type_code, training_code)
);
CREATE INDEX IF NOT EXISTS ix_sp_wtr_work_type ON sp_work_training_requirements(work_type_code);
CREATE INDEX IF NOT EXISTS ix_sp_wtr_training ON sp_work_training_requirements(training_code);


-- ---------------------------------------------------------------------
-- H5) sp_hazard_document_requirements : 위험요인별 관련 서류
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_hazard_document_requirements (
    id                  BIGSERIAL PRIMARY KEY,
    hazard_code         VARCHAR(50)  NOT NULL,
        -- Knowledge DB hazards.hazard_code 참조
    doc_id              VARCHAR(20)  NOT NULL,
    condition_note      TEXT,
    source_type         VARCHAR(30)  DEFAULT 'practical',
    verification_status VARCHAR(30)  DEFAULT 'NEEDS_VERIFICATION',

    CONSTRAINT fk_sp_hdr_doc
        FOREIGN KEY (doc_id) REFERENCES sp_document_catalog(doc_id) ON DELETE CASCADE,
    CONSTRAINT uq_sp_hdr UNIQUE (hazard_code, doc_id)
);
CREATE INDEX IF NOT EXISTS ix_sp_hdr_hazard ON sp_hazard_document_requirements(hazard_code);
CREATE INDEX IF NOT EXISTS ix_sp_hdr_doc ON sp_hazard_document_requirements(doc_id);


-- ---------------------------------------------------------------------
-- H6) sp_hazard_training_requirements : 위험요인별 관련 교육
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_hazard_training_requirements (
    id                  BIGSERIAL PRIMARY KEY,
    hazard_code         VARCHAR(50)  NOT NULL,
    training_code       VARCHAR(50)  NOT NULL,
    condition_note      TEXT,
    source_type         VARCHAR(30)  DEFAULT 'practical',
    verification_status VARCHAR(30)  DEFAULT 'NEEDS_VERIFICATION',

    CONSTRAINT fk_sp_htr_training
        FOREIGN KEY (training_code) REFERENCES sp_training_types(training_code) ON DELETE CASCADE,
    CONSTRAINT uq_sp_htr UNIQUE (hazard_code, training_code)
);
CREATE INDEX IF NOT EXISTS ix_sp_htr_hazard ON sp_hazard_training_requirements(hazard_code);
CREATE INDEX IF NOT EXISTS ix_sp_htr_training ON sp_hazard_training_requirements(training_code);


-- ---------------------------------------------------------------------
-- H7) sp_equipment_inspection_requirements : 장비별 점검 주기/유형 요구사항
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sp_equipment_inspection_requirements (
    id                  BIGSERIAL PRIMARY KEY,
    equipment_code      VARCHAR(50)  NOT NULL,
    inspection_code     VARCHAR(50)  NOT NULL,
    cycle               VARCHAR(50),
        -- 예: 작업 시작 전 매일 | 월 1회 | 분기 1회
    legal_basis         TEXT,
    source_type         VARCHAR(30)  DEFAULT 'law',
    verification_status VARCHAR(30)  DEFAULT 'confirmed',

    CONSTRAINT fk_sp_eir_inspection
        FOREIGN KEY (inspection_code) REFERENCES sp_inspection_types(inspection_code) ON DELETE CASCADE,
    CONSTRAINT uq_sp_eir UNIQUE (equipment_code, inspection_code)
);
CREATE INDEX IF NOT EXISTS ix_sp_eir_equipment ON sp_equipment_inspection_requirements(equipment_code);
CREATE INDEX IF NOT EXISTS ix_sp_eir_inspection ON sp_equipment_inspection_requirements(inspection_code);


-- =====================================================================
-- 끝. (본 파일은 설계 초안이며 실제 마이그레이션 단계에서 재검토 필요)
-- 기존 테이블(documents, hazards, work_types, equipment 등)은 변경 없음.
-- =====================================================================

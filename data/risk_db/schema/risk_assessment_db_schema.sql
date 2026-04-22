-- =====================================================================
-- 위험성평가표 자동생성기 - 운영 DB 스키마 (초안 v1.0)
-- 대상 DBMS : PostgreSQL 14+
-- 작성일   : 2026-04-22
-- 목적     : 파일 기반 JSON 구조(normalized) → 운영형 PostgreSQL 구조로 이관
-- 범위     : DB 설계 확정 단계 (DDL 초안). 실제 실행/적재는 수행하지 않음.
-- 주의     : 모든 DDL 은 CREATE ... IF NOT EXISTS 기반이며 파괴적 구문 없음.
--            trigger / function / enum 타입은 본 단계에서 생성하지 않는다.
-- =====================================================================


-- =====================================================================
-- A. 공통 문서 본체
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1) documents
--    KOSHA / law / expc / video 등 모든 소스의 공통 본체 테이블.
--    normalized JSON 의 상단 공통 필드와 1:1 대응.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id                BIGSERIAL PRIMARY KEY,

    -- 원천 식별
    source_type       VARCHAR(20)  NOT NULL,
        -- 허용값(주석): kosha | law | expc | video
        -- CHECK 는 운영 확장 시점에 별도 마이그레이션에서 부여
    source_id         VARCHAR(200) NOT NULL,
    doc_category      VARCHAR(100),
        -- 예: kosha_opl, kosha_guide, law_statute, law_admrul, law_expc

    -- 제목/본문
    title             TEXT NOT NULL,
    title_normalized  TEXT,
    body_text         TEXT,
    has_text          BOOLEAN NOT NULL DEFAULT FALSE,
    content_length    INTEGER NOT NULL DEFAULT 0,

    -- 원본 링크/파일
    url               TEXT,
    file_url          TEXT,
    pdf_path          TEXT,
    file_sha256       VARCHAR(64),

    -- 언어/상태
    language          VARCHAR(20) DEFAULT 'ko',
        -- 허용값(주석): ko | en | unknown
    status            VARCHAR(30) DEFAULT 'active',
        -- 허용값(주석): active | excluded | draft | archived

    -- 시점
    published_at      DATE,
    collected_at      TIMESTAMP,

    -- 감사
    created_at        TIMESTAMP NOT NULL DEFAULT now(),
    updated_at        TIMESTAMP NOT NULL DEFAULT now(),

    -- 원천 내 유일성 보장
    CONSTRAINT uq_documents_source UNIQUE (source_type, source_id)
);


-- =====================================================================
-- B. 표준 분류
-- =====================================================================

-- ---------------------------------------------------------------------
-- 2) hazards : 위험요인 표준 코드
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hazards (
    hazard_code   VARCHAR(50)  PRIMARY KEY,
    hazard_name   VARCHAR(100) NOT NULL UNIQUE,
    sort_order    INTEGER      DEFAULT 0,
    is_active     BOOLEAN      DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 3) work_types : 작업유형 표준 코드
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS work_types (
    work_type_code  VARCHAR(50)  PRIMARY KEY,
    work_type_name  VARCHAR(100) NOT NULL UNIQUE,
    sort_order      INTEGER      DEFAULT 0,
    is_active       BOOLEAN      DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 4) equipment : 장비/설비 표준 코드
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS equipment (
    equipment_code  VARCHAR(50)  PRIMARY KEY,
    equipment_name  VARCHAR(100) NOT NULL UNIQUE,
    sort_order      INTEGER      DEFAULT 0,
    is_active       BOOLEAN      DEFAULT TRUE
);


-- =====================================================================
-- C. 문서-분류 매핑 (N:M)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 5) document_hazard_map
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_hazard_map (
    document_id   BIGINT      NOT NULL,
    hazard_code   VARCHAR(50) NOT NULL,
    is_primary    BOOLEAN     DEFAULT FALSE,
    created_at    TIMESTAMP   DEFAULT now(),

    PRIMARY KEY (document_id, hazard_code),

    CONSTRAINT fk_dhm_document
        FOREIGN KEY (document_id) REFERENCES documents(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_dhm_hazard
        FOREIGN KEY (hazard_code) REFERENCES hazards(hazard_code)
        ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- 6) document_work_type_map
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_work_type_map (
    document_id     BIGINT      NOT NULL,
    work_type_code  VARCHAR(50) NOT NULL,
    is_primary      BOOLEAN     DEFAULT FALSE,
    created_at      TIMESTAMP   DEFAULT now(),

    PRIMARY KEY (document_id, work_type_code),

    CONSTRAINT fk_dwtm_document
        FOREIGN KEY (document_id) REFERENCES documents(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_dwtm_work_type
        FOREIGN KEY (work_type_code) REFERENCES work_types(work_type_code)
        ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- 7) document_equipment_map
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_equipment_map (
    document_id     BIGINT      NOT NULL,
    equipment_code  VARCHAR(50) NOT NULL,
    is_primary      BOOLEAN     DEFAULT FALSE,
    created_at      TIMESTAMP   DEFAULT now(),

    PRIMARY KEY (document_id, equipment_code),

    CONSTRAINT fk_dem_document
        FOREIGN KEY (document_id) REFERENCES documents(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_dem_equipment
        FOREIGN KEY (equipment_code) REFERENCES equipment(equipment_code)
        ON DELETE RESTRICT
);


-- =====================================================================
-- D. 소스별 상세 메타 (documents.id 1:1)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 8) kosha_meta
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kosha_meta (
    document_id  BIGINT PRIMARY KEY,
    industry     VARCHAR(100),
    tags         JSONB DEFAULT '[]'::jsonb,

    CONSTRAINT fk_kosha_meta_document
        FOREIGN KEY (document_id) REFERENCES documents(id)
        ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- 9) law_meta
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS law_meta (
    document_id         BIGINT PRIMARY KEY,
    law_name            TEXT,
    law_id              VARCHAR(100),
    article_no          VARCHAR(100),
    promulgation_date   DATE,
    effective_date      DATE,
    ministry            VARCHAR(200),
    extra               JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT fk_law_meta_document
        FOREIGN KEY (document_id) REFERENCES documents(id)
        ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- 10) expc_meta  (해석례/행정해석)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS expc_meta (
    document_id        BIGINT PRIMARY KEY,
    agenda_no          VARCHAR(100),
    agency_question    VARCHAR(200),
    agency_answer      VARCHAR(200),
    reply_date         DATE,
    question_summary   TEXT,
    answer_summary     TEXT,
    reason_text        TEXT,
    extra              JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT fk_expc_meta_document
        FOREIGN KEY (document_id) REFERENCES documents(id)
        ON DELETE CASCADE
);


-- =====================================================================
-- E. 위험성평가 결과 (캐시/로그성, 초기형)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 11) risk_assessment_results
--     formatter(format_risk_assessment) 결과물 저장용. 재생성 가능.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_assessment_results (
    id                           BIGSERIAL PRIMARY KEY,
    query                        TEXT NOT NULL,
    representative_work_type     VARCHAR(50),
    main_hazard                  VARCHAR(50),
    sub_hazards                  JSONB NOT NULL DEFAULT '[]'::jsonb,
    risk_factors                 JSONB NOT NULL DEFAULT '[]'::jsonb,
    controls                     JSONB NOT NULL DEFAULT '[]'::jsonb,
    legal_basis                  JSONB NOT NULL DEFAULT '[]'::jsonb,
    reference_cases              JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_summary               JSONB NOT NULL DEFAULT '{}'::jsonb,
    meta                         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                   TIMESTAMP NOT NULL DEFAULT now()
);


-- =====================================================================
-- F. 운영 이력 (최소)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 12) collection_runs : 원천 수집 실행 이력
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS collection_runs (
    id              BIGSERIAL PRIMARY KEY,
    source_type     VARCHAR(20) NOT NULL,
    run_date        DATE        NOT NULL,
    status          VARCHAR(30) NOT NULL,
        -- 허용값(주석): running | success | partial | failed
    total_count     INTEGER DEFAULT 0,
    success_count   INTEGER DEFAULT 0,
    fail_count      INTEGER DEFAULT 0,
    note            TEXT,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 13) normalization_runs : 정규화 실행 이력
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS normalization_runs (
    id              BIGSERIAL PRIMARY KEY,
    source_type     VARCHAR(20) NOT NULL,
    run_date        DATE        NOT NULL,
    status          VARCHAR(30) NOT NULL,
        -- 허용값(주석): running | success | partial | failed
    total_count     INTEGER DEFAULT 0,
    success_count   INTEGER DEFAULT 0,
    fail_count      INTEGER DEFAULT 0,
    note            TEXT,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT now()
);


-- =====================================================================
-- G. 인덱스
-- =====================================================================

-- documents
CREATE INDEX IF NOT EXISTS ix_documents_source_type     ON documents(source_type);
CREATE INDEX IF NOT EXISTS ix_documents_doc_category    ON documents(doc_category);
CREATE INDEX IF NOT EXISTS ix_documents_status          ON documents(status);
CREATE INDEX IF NOT EXISTS ix_documents_collected_at    ON documents(collected_at);
CREATE INDEX IF NOT EXISTS ix_documents_published_at    ON documents(published_at);
CREATE INDEX IF NOT EXISTS ix_documents_file_sha256     ON documents(file_sha256);

-- maps
CREATE INDEX IF NOT EXISTS ix_dhm_hazard_code           ON document_hazard_map(hazard_code);
CREATE INDEX IF NOT EXISTS ix_dwtm_work_type_code       ON document_work_type_map(work_type_code);
CREATE INDEX IF NOT EXISTS ix_dem_equipment_code        ON document_equipment_map(equipment_code);

-- law_meta
CREATE INDEX IF NOT EXISTS ix_law_meta_law_name         ON law_meta(law_name);
CREATE INDEX IF NOT EXISTS ix_law_meta_article_no       ON law_meta(article_no);

-- expc_meta
CREATE INDEX IF NOT EXISTS ix_expc_meta_agenda_no       ON expc_meta(agenda_no);

-- runs
CREATE INDEX IF NOT EXISTS ix_collection_runs_src_date
    ON collection_runs(source_type, run_date);
CREATE INDEX IF NOT EXISTS ix_normalization_runs_src_date
    ON normalization_runs(source_type, run_date);


-- =====================================================================
-- H. 전문검색(GIN) 인덱스 — 이번 단계에서는 생성하지 않음 (주석만)
-- =====================================================================
--
-- 향후 전문검색 활성화 시 아래와 같이 적용 예정.
-- 한국어 전용 tsearch 설정(mecab/nori 등)은 운영 DB 환경 확정 후에 결정한다.
--
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
--
-- CREATE INDEX IF NOT EXISTS ix_documents_title_trgm
--     ON documents USING gin (title gin_trgm_ops);
--
-- CREATE INDEX IF NOT EXISTS ix_documents_body_text_trgm
--     ON documents USING gin (body_text gin_trgm_ops);
--
-- -- 또는 tsvector 컬럼을 별도로 두고 GIN 인덱스를 거는 방식도 검토.
-- -- CREATE INDEX IF NOT EXISTS ix_documents_body_tsv
-- --     ON documents USING gin (to_tsvector('simple', coalesce(body_text,'')));


-- =====================================================================
-- 끝. (본 파일은 설계 초안이며 실제 실행/마이그레이션 단계에서 재검토 필요)
-- =====================================================================

-- Risk Data DB — 위험성 평가 데이터 자산 스키마
-- Policy: 신규 테이블만 생성. 기존 테이블 변경/삭제 금지.
-- Prefix: rd_ (risk_data) — 기존 테이블과 충돌 방지
-- Migration: 003

-- ══════════════════════════════════════════════════════════════════
-- [1] Work Taxonomy DB — 공종/작업 분류체계
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS rd_work_trades (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(10)  NOT NULL UNIQUE,    -- 'CIVIL', 'STEEL' 등
    name_ko     VARCHAR(50)  NOT NULL,           -- '토공사'
    category    VARCHAR(20)  NOT NULL,           -- 'construction'/'manufacturing'/'other'
    description TEXT,
    source      VARCHAR(100) NOT NULL DEFAULT '건설기술진흥법 시행령 별표 공종분류',
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rd_work_types (
    id           SERIAL PRIMARY KEY,
    trade_code   VARCHAR(10)  NOT NULL,          -- FK to rd_work_trades.code
    code         VARCHAR(20)  NOT NULL UNIQUE,   -- 'CIVIL_EXCAV'
    name_ko      VARCHAR(50)  NOT NULL,          -- '터파기'
    description  TEXT,
    risk_level   SMALLINT     DEFAULT 2,         -- 1=low, 2=medium, 3=high
    source       VARCHAR(100) NOT NULL DEFAULT 'KOSHA 안전보건교육 자료',
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (trade_code) REFERENCES rd_work_trades(code)
);

CREATE TABLE IF NOT EXISTS rd_work_hazards_map (
    id            SERIAL PRIMARY KEY,
    work_type_code VARCHAR(20) NOT NULL,
    hazard_code    VARCHAR(20) NOT NULL,
    frequency      SMALLINT DEFAULT 2,     -- 1=rare, 2=occasional, 3=frequent
    severity       SMALLINT DEFAULT 2,     -- 1=minor, 2=moderate, 3=severe
    source         VARCHAR(100) NOT NULL DEFAULT 'KOSHA chunk 기반',
    UNIQUE (work_type_code, hazard_code)
);

-- ══════════════════════════════════════════════════════════════════
-- [2] Hazard-Action DB — 위험요인/조치/보호구
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS rd_hazards (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20)  NOT NULL UNIQUE,  -- 'FALL', 'ELEC' 등
    name_ko         VARCHAR(30)  NOT NULL,          -- '추락'
    name_en         VARCHAR(30),
    description     TEXT,
    severity_class  VARCHAR(10)  DEFAULT 'high',    -- high/medium/low
    source          VARCHAR(100) NOT NULL DEFAULT 'hazard_classifier.py 분류체계',
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rd_hazard_scenarios (
    id              SERIAL PRIMARY KEY,
    hazard_code     VARCHAR(20)  NOT NULL,
    scenario_title  VARCHAR(100) NOT NULL,    -- '비계 위 작업 중 추락'
    scenario_desc   TEXT         NOT NULL,
    work_context    VARCHAR(50),              -- 관련 work_type
    source          VARCHAR(200) NOT NULL,    -- 출처 (KOSHA chunk_id 또는 법령)
    source_chunk_id INTEGER,                  -- kosha_material_chunks.id 참조
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rd_hazard_controls (
    id              SERIAL PRIMARY KEY,
    hazard_code     VARCHAR(20)  NOT NULL,
    control_text    VARCHAR(200) NOT NULL,    -- '안전난간 설치'
    control_type    VARCHAR(20)  DEFAULT 'engineering',  -- engineering/admin/ppe
    priority        SMALLINT     DEFAULT 2,   -- 1=primary, 2=secondary, 3=supplementary
    law_ref         VARCHAR(100),             -- 관련 법령 조항
    source          VARCHAR(200) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rd_hazard_ppe (
    id           SERIAL PRIMARY KEY,
    hazard_code  VARCHAR(20)  NOT NULL,
    ppe_name     VARCHAR(50)  NOT NULL,    -- '안전대'
    ppe_standard VARCHAR(100),            -- 'KS G 9027' 등
    mandatory    BOOLEAN      DEFAULT TRUE,
    source       VARCHAR(200) NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════
-- [3] Equipment/Material DB — 장비/자재 위험
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS rd_equipment_master (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20)  NOT NULL UNIQUE,
    name_ko         VARCHAR(50)  NOT NULL,
    equipment_type  VARCHAR(30),             -- lifting/access/cutting/electrical/etc
    description     TEXT,
    inspection_cycle VARCHAR(50),
    law_ref         VARCHAR(200),
    source          VARCHAR(200) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rd_equipment_hazards (
    id              SERIAL PRIMARY KEY,
    equipment_code  VARCHAR(20)  NOT NULL,
    hazard_code     VARCHAR(20)  NOT NULL,
    condition_desc  TEXT,                    -- 어떤 상황에서 위험한지
    source          VARCHAR(200) NOT NULL,
    UNIQUE (equipment_code, hazard_code)
);

CREATE TABLE IF NOT EXISTS rd_equipment_controls (
    id              SERIAL PRIMARY KEY,
    equipment_code  VARCHAR(20)  NOT NULL,
    control_text    VARCHAR(200) NOT NULL,
    control_type    VARCHAR(20)  DEFAULT 'pre_use',  -- pre_use/during/post_use
    source          VARCHAR(200) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════
-- [4] Real Case DB — 실사례
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS rd_real_cases (
    id              SERIAL PRIMARY KEY,
    case_title      VARCHAR(200) NOT NULL,
    trade_code      VARCHAR(10),
    work_type_code  VARCHAR(20),
    hazard_codes    VARCHAR(20)[],           -- 복수 위험
    work_desc       TEXT,
    risk_factors    TEXT,
    control_measures TEXT,
    outcome         VARCHAR(20),             -- 'incident'/'near_miss'/'prevented'
    source_type     VARCHAR(20) NOT NULL,    -- 'kosha_chunk'/'assessment_record'/'manual'
    source_ref      VARCHAR(200) NOT NULL,
    anonymized      BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════
-- [5] Law/Standard DB — 법령/기준
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS rd_safety_laws (
    id           SERIAL PRIMARY KEY,
    law_code     VARCHAR(50)  NOT NULL UNIQUE,   -- 'OSHA-R-43'
    law_title    VARCHAR(200) NOT NULL,
    article_no   VARCHAR(20),                    -- '제43조'
    clause_title VARCHAR(200),
    clause_text  TEXT,
    effective_date DATE,
    source_url   VARCHAR(300),
    source       VARCHAR(200) NOT NULL DEFAULT '산업안전보건기준에 관한 규칙',
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rd_law_hazard_map (
    id           SERIAL PRIMARY KEY,
    law_code     VARCHAR(50)  NOT NULL,
    hazard_code  VARCHAR(20)  NOT NULL,
    relevance    VARCHAR(20)  DEFAULT 'direct',   -- direct/indirect
    note         TEXT,
    UNIQUE (law_code, hazard_code)
);

-- ══════════════════════════════════════════════════════════════════
-- Indexes
-- ══════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_rd_wt_trade   ON rd_work_types (trade_code);
CREATE INDEX IF NOT EXISTS idx_rd_whm_work   ON rd_work_hazards_map (work_type_code);
CREATE INDEX IF NOT EXISTS idx_rd_hs_hazard  ON rd_hazard_scenarios (hazard_code);
CREATE INDEX IF NOT EXISTS idx_rd_hc_hazard  ON rd_hazard_controls (hazard_code);
CREATE INDEX IF NOT EXISTS idx_rd_hp_hazard  ON rd_hazard_ppe (hazard_code);
CREATE INDEX IF NOT EXISTS idx_rd_eh_equip   ON rd_equipment_hazards (equipment_code);
CREATE INDEX IF NOT EXISTS idx_rd_lhm_law    ON rd_law_hazard_map (law_code);
CREATE INDEX IF NOT EXISTS idx_rd_lhm_hazard ON rd_law_hazard_map (hazard_code);

COMMENT ON TABLE rd_work_trades       IS 'Risk DB: 공종 마스터. source=건설기술진흥법 시행령 별표';
COMMENT ON TABLE rd_work_types        IS 'Risk DB: 세부작업 마스터. source=KOSHA 안전보건교육 자료';
COMMENT ON TABLE rd_work_hazards_map  IS 'Risk DB: 작업-위험 연계';
COMMENT ON TABLE rd_hazards           IS 'Risk DB: 위험요인 마스터. source=hazard_classifier.py 분류체계';
COMMENT ON TABLE rd_hazard_scenarios  IS 'Risk DB: 위험 시나리오. source=KOSHA chunk';
COMMENT ON TABLE rd_hazard_controls   IS 'Risk DB: 위험별 조치사항';
COMMENT ON TABLE rd_hazard_ppe        IS 'Risk DB: 위험별 보호구';
COMMENT ON TABLE rd_equipment_master  IS 'Risk DB: 장비 마스터. source=산업안전보건기준에 관한 규칙';
COMMENT ON TABLE rd_equipment_hazards IS 'Risk DB: 장비-위험 연계';
COMMENT ON TABLE rd_equipment_controls IS 'Risk DB: 장비별 조치';
COMMENT ON TABLE rd_real_cases        IS 'Risk DB: 실사례. source_type=kosha_chunk 등';
COMMENT ON TABLE rd_safety_laws       IS 'Risk DB: 법령 마스터. source=산업안전보건기준에 관한 규칙';
COMMENT ON TABLE rd_law_hazard_map    IS 'Risk DB: 법령-위험 연계';

-- ======================================================================
-- Migration 0009 : risk_mapping_core — 최소 매핑 엔진 (고소작업 4 hazard)
-- ======================================================================
-- 원칙: documents 테이블 read-only. 신규 테이블만 생성 및 삽입.
-- ======================================================================

BEGIN;

-- ─── 1. 테이블 생성 ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS risk_mapping_core (
    id              BIGSERIAL PRIMARY KEY,
    work_type       TEXT        NOT NULL,
    hazard          TEXT        NOT NULL,
    related_law_ids JSONB       NOT NULL DEFAULT '[]',   -- documents.id 배열 (source_type=law)
    related_expc_ids JSONB      NOT NULL DEFAULT '[]',   -- documents.id 배열 (source_type=moel_expc)
    related_kosha_ids JSONB     NOT NULL DEFAULT '[]',   -- documents.id 배열 (source_type=kosha)
    control_measures JSONB      NOT NULL DEFAULT '[]',   -- 안전조치 텍스트 배열
    confidence_score NUMERIC(3,2) NOT NULL DEFAULT 0.00
        CHECK (confidence_score BETWEEN 0 AND 1),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (work_type, hazard)
);

COMMENT ON TABLE risk_mapping_core IS
    '작업 유형 × 위험요인 단위의 최소 매핑 엔진. documents 테이블 참조만 수행(read-only).';
COMMENT ON COLUMN risk_mapping_core.related_law_ids IS
    'documents.id 배열 (source_type IN (''law''))';
COMMENT ON COLUMN risk_mapping_core.related_expc_ids IS
    'documents.id 배열 (source_type = ''moel_expc'')';
COMMENT ON COLUMN risk_mapping_core.related_kosha_ids IS
    'documents.id 배열 (source_type IN (''kosha'',''kosha_form''))';
COMMENT ON COLUMN risk_mapping_core.control_measures IS
    '안전조치 텍스트 배열. {"measures": [...], "source": "law|kosha|manual"}';

-- ─── 2. 고소작업 4 hazard 삽입 ─────────────────────────────────────────

-- 2-1. 추락
-- law: 제13조(안전난간), 제32조(보호구), 제42조(추락의 방지)
-- moel_expc: 높이에 따른 부상/A형 사다리 고소작업/타워크레인 안전장치
-- kosha: 업종직종 안전보건 OPL / 기초안전보건교육 연구 / 해빙기 건설현장 안전수칙
INSERT INTO risk_mapping_core
    (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
     control_measures, confidence_score)
VALUES (
    '고소작업',
    '추락',
    '[16733, 16754, 16767]',
    '[26331, 23752, 31947]',
    '[1726, 35368, 3057]',
    '{"source": "law+kosha", "measures": [
        "안전난간 설치 (산업안전보건기준에 관한 규칙 제13조)",
        "안전대(안전벨트) 착용 및 체결설비 확보 (제32조)",
        "작업발판 설치 및 추락방지망 설치 (제42조)",
        "고소작업 전 작업계획서 작성",
        "2m 이상 고소작업 시 추락 위험구역 표시 및 출입통제"
    ]}',
    0.90
)
ON CONFLICT (work_type, hazard) DO UPDATE
    SET related_law_ids   = EXCLUDED.related_law_ids,
        related_expc_ids  = EXCLUDED.related_expc_ids,
        related_kosha_ids = EXCLUDED.related_kosha_ids,
        control_measures  = EXCLUDED.control_measures,
        confidence_score  = EXCLUDED.confidence_score;

-- 2-2. 낙하물
-- law: 제14조(낙하물 위험 방지), 제193조(낙하물 위험 방지), 제198조(낙하물 보호구조)
-- moel_expc: 안전보건관리책임자/타워크레인 운영/낙하물 위험 방지 조치
-- kosha: 업종직종 OPL / 기초안전보건교육 / 해빙기 건설현장
INSERT INTO risk_mapping_core
    (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
     control_measures, confidence_score)
VALUES (
    '고소작업',
    '낙하물',
    '[16734, 16957, 16964]',
    '[24497, 31953, 25997]',
    '[1726, 35368, 3057]',
    '{"source": "law+kosha", "measures": [
        "낙하물 방지망 설치 (산업안전보건기준에 관한 규칙 제14조)",
        "투하설비 설치 및 감시인 배치 (제193조)",
        "낙하물 보호구조 설치 (제198조)",
        "상·하 동시 작업 금지 또는 격리 조치",
        "공구·자재 결속 및 공구 주머니 사용"
    ]}',
    0.88
)
ON CONFLICT (work_type, hazard) DO UPDATE
    SET related_law_ids   = EXCLUDED.related_law_ids,
        related_expc_ids  = EXCLUDED.related_expc_ids,
        related_kosha_ids = EXCLUDED.related_kosha_ids,
        control_measures  = EXCLUDED.control_measures,
        confidence_score  = EXCLUDED.confidence_score;

-- 2-3. 전도
-- law: 제42조(추락의 방지 — 발판 전도 포함), 제68조(이동식비계), 제186조(고소작업대 설치 조치)
-- moel_expc: 타워크레인 운영/노후위험기계/풍속계 안전관리비
-- kosha: 업종직종 OPL / 기초안전보건교육 / 해빙기 건설현장
INSERT INTO risk_mapping_core
    (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
     control_measures, confidence_score)
VALUES (
    '고소작업',
    '전도',
    '[16767, 16801, 16948]',
    '[31953, 31619, 30056]',
    '[1726, 35368, 3057]',
    '{"source": "law+kosha", "measures": [
        "작업발판 수평 유지 및 고정 (산업안전보건기준에 관한 규칙 제42조)",
        "이동식비계 바퀴 잠금장치 확인 (제68조)",
        "고소작업대 아웃트리거 완전 전개 및 지반 지지력 확인 (제186조)",
        "작업대 위 과적 금지 (정격하중 준수)",
        "강풍·악천후 시 작업 중지"
    ]}',
    0.85
)
ON CONFLICT (work_type, hazard) DO UPDATE
    SET related_law_ids   = EXCLUDED.related_law_ids,
        related_expc_ids  = EXCLUDED.related_expc_ids,
        related_kosha_ids = EXCLUDED.related_kosha_ids,
        control_measures  = EXCLUDED.control_measures,
        confidence_score  = EXCLUDED.confidence_score;

-- 2-4. 협착
-- law: 제415조(추락·충돌·협착 등의 방지), 제6조(도급인 안전보건 조치 장소), 제11조(도급인 지배관리 장소)
-- moel_expc: 중대재해조사/지게차 작업계획서/수상작업 및 중량물
-- kosha: 해빙기 건설현장 / 차량탑재형 이동식크레인 / 중대사고 이슈리포트
INSERT INTO risk_mapping_core
    (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
     control_measures, confidence_score)
VALUES (
    '고소작업',
    '협착',
    '[17237, 15812, 22357]',
    '[31223, 31271, 28679]',
    '[3057, 35243, 35334]',
    '{"source": "law+kosha", "measures": [
        "고소작업 장비 작업반경 내 출입통제 (산업안전보건기준에 관한 규칙 제415조)",
        "장비 이동 전 신호수 배치 및 경보장치 작동 확인",
        "작업구역 표시(로프·표지판) 및 관계자 외 접근 금지",
        "고소작업대 붐 회전 반경 내 작업자 위치 통보",
        "잠금·표지(LOTO) 절차 적용"
    ]}',
    0.80
)
ON CONFLICT (work_type, hazard) DO UPDATE
    SET related_law_ids   = EXCLUDED.related_law_ids,
        related_expc_ids  = EXCLUDED.related_expc_ids,
        related_kosha_ids = EXCLUDED.related_kosha_ids,
        control_measures  = EXCLUDED.control_measures,
        confidence_score  = EXCLUDED.confidence_score;

-- ─── 3. 인덱스 ─────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_rmc_work_type ON risk_mapping_core (work_type);
CREATE INDEX IF NOT EXISTS idx_rmc_hazard    ON risk_mapping_core (hazard);
CREATE INDEX IF NOT EXISTS idx_rmc_law_ids   ON risk_mapping_core USING GIN (related_law_ids);
CREATE INDEX IF NOT EXISTS idx_rmc_expc_ids  ON risk_mapping_core USING GIN (related_expc_ids);
CREATE INDEX IF NOT EXISTS idx_rmc_kosha_ids ON risk_mapping_core USING GIN (related_kosha_ids);

COMMIT;

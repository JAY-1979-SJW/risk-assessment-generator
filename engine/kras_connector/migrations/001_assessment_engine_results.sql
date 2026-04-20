-- 엔진 실행 결과 저장 테이블
-- Policy: 이력 누적 저장 (재실행 시 신규 row 추가, latest는 executed_at DESC 기준 조회)
-- Migration: 001

CREATE TABLE IF NOT EXISTS assessment_engine_results (
    id                  SERIAL PRIMARY KEY,
    assessment_id       INTEGER     NOT NULL,               -- project_assessments.id
    engine_version      VARCHAR(20) NOT NULL DEFAULT 'v1.1',
    input_snapshot      JSONB       NOT NULL,               -- 실행 당시 입력 전체
    output_json         JSONB,                              -- 엔진 출력 전체 (실패 시 NULL)
    source_chunk_ids    INTEGER[]   NOT NULL DEFAULT '{}',
    confidence          VARCHAR(10),
    warnings            TEXT[]      NOT NULL DEFAULT '{}',
    chunk_count_loaded  INTEGER,                            -- 로더가 읽은 청크 수
    executed_at         TIMESTAMP   NOT NULL DEFAULT NOW(),
    status              VARCHAR(20) NOT NULL DEFAULT 'success',
    error_message       TEXT        -- 실패 시 오류 메시지
);

-- assessment_id 기준 최신 결과 조회 최적화
CREATE INDEX IF NOT EXISTS idx_aer_assessment_time
    ON assessment_engine_results (assessment_id, executed_at DESC);

-- status 필터 조회
CREATE INDEX IF NOT EXISTS idx_aer_status
    ON assessment_engine_results (status);

COMMENT ON TABLE assessment_engine_results IS
    'RAG 엔진 실행 결과 이력. 재실행 시 누적 저장. latest = MAX(executed_at) by assessment_id.';

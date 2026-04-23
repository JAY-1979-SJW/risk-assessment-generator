-- ======================================================================
-- Migration 0011 : risk_mapping_core — related_moel_expc_ids 컬럼 추가
-- ======================================================================
-- 목적:
--   · source_type 명칭 기준 통일: related_expc_ids → related_moel_expc_ids
--   · 기존 related_expc_ids 데이터를 신규 컬럼으로 복사
--   · 기존 컬럼 related_expc_ids 유지 (하위 호환)
--   · 고소작업 기존 4 row 수정 금지 — 데이터 복사만 수행
-- ======================================================================

BEGIN;

-- 1. 신규 컬럼 추가
ALTER TABLE risk_mapping_core
  ADD COLUMN IF NOT EXISTS related_moel_expc_ids JSONB NOT NULL DEFAULT '[]';

-- 2. 기존 related_expc_ids 데이터를 새 컬럼으로 복사 (전체 row)
UPDATE risk_mapping_core
   SET related_moel_expc_ids = related_expc_ids
 WHERE related_moel_expc_ids = '[]'::jsonb
   AND related_expc_ids != '[]'::jsonb;

-- 3. 신규 컬럼 GIN 인덱스
CREATE INDEX IF NOT EXISTS idx_rmc_moel_expc_ids
  ON risk_mapping_core USING GIN (related_moel_expc_ids);

-- 4. 고소작업 diff 확인 (변경 없음 검증용 — 로그용 SELECT)
-- 아래 결과: 고소작업 related_moel_expc_ids = related_expc_ids 이면 정상
DO $$
DECLARE
  diff_cnt INT;
BEGIN
  SELECT COUNT(*) INTO diff_cnt
  FROM risk_mapping_core
  WHERE work_type = '고소작업'
    AND related_moel_expc_ids != related_expc_ids;

  IF diff_cnt > 0 THEN
    RAISE EXCEPTION '고소작업 diff 감지: % row 불일치. 중단.', diff_cnt;
  ELSE
    RAISE NOTICE '고소작업 diff 검증 OK: related_moel_expc_ids = related_expc_ids';
  END IF;
END $$;

COMMIT;

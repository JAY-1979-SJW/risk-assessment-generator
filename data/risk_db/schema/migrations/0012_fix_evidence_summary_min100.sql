-- ======================================================================
-- Migration 0012 : risk_mapping_core — evidence_summary 최소 100자 보정
-- ======================================================================
-- 목적:
--   · 이동식비계 작업 / 낙하물 evidence_summary 99자 → 100자+ 보완
--   · 고소작업 4 row 비접촉 (WHERE 절로 완전 제외)
--   · 다른 row 미변경
-- ======================================================================

BEGIN;

-- 사전 검증: 고소작업 row 건수 (변동 없어야 함)
DO $$
DECLARE
  gosojakup_cnt INT;
BEGIN
  SELECT COUNT(*) INTO gosojakup_cnt
  FROM risk_mapping_core
  WHERE work_type = '고소작업';

  IF gosojakup_cnt != 4 THEN
    RAISE EXCEPTION '고소작업 row 건수 이상: %, 예상 4. 중단.', gosojakup_cnt;
  ELSE
    RAISE NOTICE '고소작업 row 건수 OK: %', gosojakup_cnt;
  END IF;
END $$;

-- 보정: 이동식비계 작업 / 낙하물 (고소작업 제외 명시)
UPDATE risk_mapping_core
   SET evidence_summary =
     '산안기준규칙 제14조(낙하물에 의한 위험의 방지), 제42조, 제193조(낙하물에 의한 위험방지) 근거. moel_expc: 낙하물 위험방지 조치 해석례(25997) 직접 관련. KOSHA OPL(1726) 낙하물 예방 조치 확인.'
 WHERE work_type = '이동식비계 작업'
   AND hazard = '낙하물'
   AND work_type != '고소작업';  -- 이중 안전장치

-- 사후 검증: 수정 row의 evidence_summary 길이 확인
DO $$
DECLARE
  es_len INT;
BEGIN
  SELECT LENGTH(evidence_summary) INTO es_len
  FROM risk_mapping_core
  WHERE work_type = '이동식비계 작업' AND hazard = '낙하물';

  IF es_len IS NULL THEN
    RAISE EXCEPTION '이동식비계/낙하물 row 없음. 중단.';
  ELSIF es_len < 100 THEN
    RAISE EXCEPTION 'evidence_summary 길이 부족: %자 (최소 100자 필요)', es_len;
  ELSE
    RAISE NOTICE '이동식비계/낙하물 evidence_summary 길이 OK: %자', es_len;
  END IF;
END $$;

-- 사후 검증: 고소작업 evidence_summary 무결성 (변경 없음 확인)
DO $$
DECLARE
  rec RECORD;
BEGIN
  FOR rec IN
    SELECT hazard, LENGTH(evidence_summary) AS len
    FROM risk_mapping_core
    WHERE work_type = '고소작업'
    ORDER BY id
  LOOP
    RAISE NOTICE '고소작업 [%] evidence_summary 길이: %자', rec.hazard, rec.len;
  END LOOP;
END $$;

COMMIT;

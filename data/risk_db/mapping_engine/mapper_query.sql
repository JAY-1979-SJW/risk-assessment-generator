-- risk_mapping_core → build_risk_assessment() 조회 쿼리
-- 사용처: engine/kras_connector/mapper.py :: build_risk_assessment()
-- 주의: related_expc_ids 사용 금지 — related_moel_expc_ids 만 사용

SELECT
    id,
    work_type,
    hazard,
    related_law_ids,
    related_moel_expc_ids,
    related_kosha_ids,
    control_measures,
    confidence_score,
    evidence_summary
FROM risk_mapping_core
WHERE work_type = %(work_type)s
  AND hazard IS NOT NULL
  AND evidence_summary IS NOT NULL
  AND control_measures IS NOT NULL
ORDER BY confidence_score DESC;

-- 예시 실행:
-- SELECT ... FROM risk_mapping_core WHERE work_type = '고소작업' ORDER BY confidence_score DESC;

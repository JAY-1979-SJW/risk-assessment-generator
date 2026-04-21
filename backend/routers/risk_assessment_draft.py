"""
위험성평가표 초안 생성 라우터 (9단계 — 초안 전용, 운영 미반영)
POST /api/risk-assessment/draft/recommend
POST /api/risk-assessment/draft/recalculate
"""
from fastapi import APIRouter, HTTPException
from schemas.risk_assessment_draft import RecommendRequest, RecalculateRequest, DraftResponse
from services.risk_assessment_engine import recommend, recalculate, EngineError

router = APIRouter(prefix="/risk-assessment/draft", tags=["risk-assessment-draft"])


@router.post("/recommend", response_model=DraftResponse)
def recommend_draft(req: RecommendRequest):
    """worktype 기준 위험성평가표 초안 생성."""
    try:
        result = recommend(
            work_type_code=req.work.work_type_code,
            work_sub_type_code=req.work.work_sub_type_code or "",
            work_name=req.work.work_name or "",
            condition_flags=req.site_context.condition_flags,
            max_hazards=req.options.max_hazards,
            max_controls_per_hazard=req.options.max_controls_per_hazard,
            max_laws_per_row=req.options.max_laws_per_row,
            include_law_evidence=req.options.include_law_evidence,
            include_scores=req.options.include_scores,
            preferred_hazard_codes=req.user_inputs.preferred_hazard_codes,
            excluded_hazard_codes=req.user_inputs.excluded_hazard_codes,
            preferred_control_codes=req.user_inputs.preferred_control_codes,
        )
    except EngineError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return result


@router.post("/recalculate", response_model=DraftResponse)
def recalculate_draft(req: RecalculateRequest):
    """사용자 수정 row 기반 control/law evidence 재조립."""
    try:
        result = recalculate(
            work_type_code=req.draft_context.work_type_code,
            work_sub_type_code=req.draft_context.work_sub_type_code or "",
            condition_flags=req.draft_context.condition_flags,
            rows_input=[r.model_dump() for r in req.rows],
            rebuild_law_evidence=req.options.rebuild_law_evidence,
            rescore_controls=req.options.rescore_controls,
            max_laws_per_row=req.options.max_laws_per_row,
        )
    except EngineError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return result

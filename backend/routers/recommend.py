"""
추천 API 라우터.
  POST /api/recommend/forms
입력 파라미터 중 hazards/work_types/laws/form_type 중 최소 1개는 필수.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from services.recommend_service import MAX_TOP_N, recommend_forms

router = APIRouter(prefix="/recommend", tags=["recommend"])


class RecommendFormsRequest(BaseModel):
    hazards: list[str] = Field(default_factory=list)
    work_types: list[str] = Field(default_factory=list)
    form_type: Optional[str] = None
    laws: list[str] = Field(default_factory=list)
    top_n: int = 10

    @field_validator("top_n")
    @classmethod
    def _validate_top_n(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("top_n must be > 0")
        if v > MAX_TOP_N:
            return MAX_TOP_N
        return v


class RecommendDetail(BaseModel):
    hazard_score: int
    work_type_score: int
    form_type_score: int
    law_score: int
    frequency_score: int


class RecommendItem(BaseModel):
    document_id: int
    source_type: str
    source_id: str
    title: str
    doc_category: Optional[str] = None
    form_type: Optional[str] = None
    hwpx_path: Optional[str] = None
    pdf_path: Optional[str] = None
    body_preview: Optional[str] = None
    score: int
    hazard_matches: list[str] = Field(default_factory=list)
    work_type_matches: list[str] = Field(default_factory=list)
    law_matches: list[str] = Field(default_factory=list)
    detail: RecommendDetail


class RecommendMetaQuery(BaseModel):
    hazards: list[str]
    work_types: list[str]
    form_type: Optional[str]
    laws: list[str]


class RecommendMeta(BaseModel):
    top_n: int
    total_candidates: int
    query: RecommendMetaQuery


class RecommendFormsResponse(BaseModel):
    items: list[RecommendItem]
    meta: RecommendMeta


@router.post("/forms", response_model=RecommendFormsResponse)
def recommend_forms_endpoint(req: RecommendFormsRequest) -> dict:
    try:
        result = recommend_forms(
            hazards=req.hazards,
            work_types=req.work_types,
            form_type=req.form_type,
            laws=req.laws,
            top_n=req.top_n,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result

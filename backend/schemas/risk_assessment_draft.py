"""
위험성평가표 초안 생성 API — Pydantic 스키마
POST /api/risk-assessment/draft/recommend
POST /api/risk-assessment/draft/recalculate
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# ── 공통 enum 값 ──────────────────────────────────────────────────────────────

VALID_CONDITION_FLAGS = frozenset([
    "high_place", "confined_space", "live_electric", "night_work", "chemical_use"
])


def _validate_condition_flags(v: List[str]) -> List[str]:
    invalid = set(v) - VALID_CONDITION_FLAGS
    if invalid:
        raise ValueError(f"invalid condition_flags: {invalid}. allowed: {sorted(VALID_CONDITION_FLAGS)}")
    return v

OPTIONS_MAX_HAZARDS_LIMIT = 10
OPTIONS_MAX_CONTROLS_LIMIT = 10
OPTIONS_MAX_LAWS_LIMIT = 10


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class SiteContext(BaseModel):
    project_type: str = ""
    trade_type: str = ""
    location_type: str = ""
    condition_flags: List[str] = Field(default_factory=list)

    @field_validator("condition_flags")
    @classmethod
    def validate_flags(cls, v: List[str]) -> List[str]:
        return _validate_condition_flags(v)


class WorkInput(BaseModel):
    work_type_code: str = Field(..., min_length=1)
    work_sub_type_code: str = ""
    work_name: str = ""


class RecommendOptions(BaseModel):
    max_hazards: int = Field(default=5, ge=1, le=OPTIONS_MAX_HAZARDS_LIMIT)
    max_controls_per_hazard: int = Field(default=3, ge=1, le=OPTIONS_MAX_CONTROLS_LIMIT)
    max_laws_per_row: int = Field(default=3, ge=1, le=OPTIONS_MAX_LAWS_LIMIT)
    include_law_evidence: bool = True
    include_scores: bool = True


class UserInputs(BaseModel):
    preferred_hazard_codes: List[str] = Field(default_factory=list)
    excluded_hazard_codes: List[str] = Field(default_factory=list)
    preferred_control_codes: List[str] = Field(default_factory=list)
    notes: str = ""


class RecommendRequest(BaseModel):
    site_context: SiteContext = Field(default_factory=SiteContext)
    work: WorkInput
    options: RecommendOptions = Field(default_factory=RecommendOptions)
    user_inputs: UserInputs = Field(default_factory=UserInputs)


class DraftContext(BaseModel):
    work_type_code: str = Field(..., min_length=1)
    work_sub_type_code: str = ""
    condition_flags: List[str] = Field(default_factory=list)

    @field_validator("condition_flags")
    @classmethod
    def validate_flags(cls, v: List[str]) -> List[str]:
        return _validate_condition_flags(v)


class RecalculateRow(BaseModel):
    row_id: str = Field(..., min_length=1)
    hazard_code: str = Field(..., min_length=1)
    selected_control_codes: List[str] = Field(default_factory=list)
    custom_control_texts: List[str] = Field(default_factory=list)
    excluded_law_ids: List[str] = Field(default_factory=list)
    memo: str = ""


class RecalculateOptions(BaseModel):
    rebuild_law_evidence: bool = True
    rescore_controls: bool = True
    max_laws_per_row: int = Field(default=3, ge=1, le=OPTIONS_MAX_LAWS_LIMIT)


class RecalculateRequest(BaseModel):
    draft_context: DraftContext
    rows: List[RecalculateRow] = Field(..., min_length=1)
    options: RecalculateOptions = Field(default_factory=RecalculateOptions)


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class WorkInfo(BaseModel):
    work_type_code: str
    work_sub_type_code: Optional[str]
    work_name: str


class DraftSummary(BaseModel):
    hazard_count: int
    control_count: int
    law_count: int


class HazardInfo(BaseModel):
    hazard_code: str
    hazard_name: str
    hazard_score: int
    hazard_reason: str


class ControlInfo(BaseModel):
    control_code: str
    control_name: str
    control_score: int
    reason: str


class LawInfo(BaseModel):
    law_id: str
    law_title: str
    law_score: float
    evidence_paths: List[str]
    detail_link: Optional[str]


class EditableFields(BaseModel):
    hazard_text: str
    control_texts: List[str]
    memo: str


class DraftRow(BaseModel):
    row_id: str
    hazard: HazardInfo
    controls: List[ControlInfo]
    laws: List[LawInfo]
    editable: EditableFields
    row_flags: List[str]


class EngineMeta(BaseModel):
    pipeline_version: str
    sources_used: List[str]


class DraftResponse(BaseModel):
    request_id: str
    generated_at: str
    work: WorkInfo
    summary: DraftSummary
    rows: List[DraftRow]
    review_flags: List[str]
    engine_meta: EngineMeta

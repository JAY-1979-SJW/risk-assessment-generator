"""
Request / response Pydantic models for POST /api/v1/risk-assessment/build.
Mirrors openapi_draft.yaml — related_expc_ids 노출 금지.
"""
from typing import List

from pydantic import BaseModel, ConfigDict


class References(BaseModel):
    model_config = ConfigDict(extra="forbid")

    law_ids: List[int]
    moel_expc_ids: List[int]
    kosha_ids: List[int]


class HazardItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hazard: str
    controls: List[str]
    references: References
    confidence_score: float
    evidence_summary: str


class RiskAssessmentBuildResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_type: str
    hazards: List[HazardItem]

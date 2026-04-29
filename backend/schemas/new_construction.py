# V1.1 신축공사 API pydantic schemas.

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Project profile ────────────────────────────────────────────────────────

class ProjectProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime

    construction_type: Optional[str] = None
    project_status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    client_name: Optional[str] = None
    prime_contractor_name: Optional[str] = None
    site_address: Optional[str] = None
    site_manager_name: Optional[str] = None
    safety_manager_name: Optional[str] = None
    total_floor_count: Optional[int] = None
    basement_floor_count: Optional[int] = None
    excavation_depth_m: Optional[Decimal] = None
    has_tower_crane: Optional[bool] = None
    has_pile_driver: Optional[bool] = None
    has_scaffold_over_31m: Optional[bool] = None
    safety_plan_required: Optional[bool] = None
    risk_level: Optional[str] = None
    manager_id: Optional[int] = None


class ProjectProfileUpdate(BaseModel):
    construction_type: Optional[str] = Field(default=None, max_length=50)
    project_status: Optional[str] = Field(default=None, max_length=30)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    client_name: Optional[str] = Field(default=None, max_length=200)
    prime_contractor_name: Optional[str] = Field(default=None, max_length=200)
    site_address: Optional[str] = None
    site_manager_name: Optional[str] = Field(default=None, max_length=100)
    safety_manager_name: Optional[str] = Field(default=None, max_length=100)
    total_floor_count: Optional[int] = None
    basement_floor_count: Optional[int] = None
    excavation_depth_m: Optional[Decimal] = None
    has_tower_crane: Optional[bool] = None
    has_pile_driver: Optional[bool] = None
    has_scaffold_over_31m: Optional[bool] = None
    safety_plan_required: Optional[bool] = None
    risk_level: Optional[str] = Field(default=None, max_length=20)
    manager_id: Optional[int] = None


# ── Sites ──────────────────────────────────────────────────────────────────

class SiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    site_name: Optional[str] = None
    address: Optional[str] = None
    detail_address: Optional[str] = None
    site_manager_name: Optional[str] = None
    site_manager_phone: Optional[str] = None
    safety_manager_name: Optional[str] = None
    safety_manager_phone: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SiteListResponse(BaseModel):
    items: list[SiteResponse]


class SiteCreate(BaseModel):
    site_name: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = None
    detail_address: Optional[str] = None
    site_manager_name: Optional[str] = Field(default=None, max_length=100)
    site_manager_phone: Optional[str] = Field(default=None, max_length=50)
    safety_manager_name: Optional[str] = Field(default=None, max_length=100)
    safety_manager_phone: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, max_length=20)


class SiteUpdate(BaseModel):
    site_name: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = None
    detail_address: Optional[str] = None
    site_manager_name: Optional[str] = Field(default=None, max_length=100)
    site_manager_phone: Optional[str] = Field(default=None, max_length=50)
    safety_manager_name: Optional[str] = Field(default=None, max_length=100)
    safety_manager_phone: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, max_length=20)

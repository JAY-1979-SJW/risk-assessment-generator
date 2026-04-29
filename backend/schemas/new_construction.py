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


# ── Contractors ────────────────────────────────────────────────────────────

class ContractorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    contractor_type: Optional[str] = None
    company_name: Optional[str] = None
    business_registration_no: Optional[str] = None
    representative_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    work_scope: Optional[str] = None
    safety_evaluation_status: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ContractorListResponse(BaseModel):
    items: list[ContractorResponse]


class ContractorCreate(BaseModel):
    contractor_type: Optional[str] = Field(default=None, max_length=50)
    company_name: str = Field(..., max_length=200)
    business_registration_no: Optional[str] = Field(default=None, max_length=50)
    representative_name: Optional[str] = Field(default=None, max_length=100)
    contact_name: Optional[str] = Field(default=None, max_length=100)
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    work_scope: Optional[str] = None
    safety_evaluation_status: Optional[str] = Field(default=None, max_length=30)
    status: Optional[str] = Field(default=None, max_length=20)


class ContractorUpdate(BaseModel):
    contractor_type: Optional[str] = Field(default=None, max_length=50)
    company_name: Optional[str] = Field(default=None, max_length=200)
    business_registration_no: Optional[str] = Field(default=None, max_length=50)
    representative_name: Optional[str] = Field(default=None, max_length=100)
    contact_name: Optional[str] = Field(default=None, max_length=100)
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    work_scope: Optional[str] = None
    safety_evaluation_status: Optional[str] = Field(default=None, max_length=30)
    status: Optional[str] = Field(default=None, max_length=20)


# ── Workers ────────────────────────────────────────────────────────────────
# 개인정보 최소화: 주민/외국인등록번호·전화번호·건강정보 필드 정의 금지.

class WorkerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    contractor_id: Optional[int] = None
    worker_name: Optional[str] = None
    trade: Optional[str] = None
    job_role: Optional[str] = None
    first_work_date: Optional[date] = None
    construction_basic_training_checked: Optional[bool] = None
    new_hire_training_checked: Optional[bool] = None
    ppe_issued: Optional[bool] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WorkerListResponse(BaseModel):
    items: list[WorkerResponse]


class WorkerCreate(BaseModel):
    contractor_id: Optional[int] = None
    worker_name: str = Field(..., max_length=100)
    trade: Optional[str] = Field(default=None, max_length=100)
    job_role: Optional[str] = Field(default=None, max_length=100)
    first_work_date: Optional[date] = None
    construction_basic_training_checked: Optional[bool] = None
    new_hire_training_checked: Optional[bool] = None
    ppe_issued: Optional[bool] = None
    status: Optional[str] = Field(default=None, max_length=20)


class WorkerUpdate(BaseModel):
    contractor_id: Optional[int] = None
    worker_name: Optional[str] = Field(default=None, max_length=100)
    trade: Optional[str] = Field(default=None, max_length=100)
    job_role: Optional[str] = Field(default=None, max_length=100)
    first_work_date: Optional[date] = None
    construction_basic_training_checked: Optional[bool] = None
    new_hire_training_checked: Optional[bool] = None
    ppe_issued: Optional[bool] = None
    status: Optional[str] = Field(default=None, max_length=20)


# ── Project Equipment ──────────────────────────────────────────────────────
# DB 테이블은 'project_equipment'. URL은 /equipment 사용. 마스터 'equipment' 미접근.

class ProjectEquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    contractor_id: Optional[int] = None
    equipment_name: Optional[str] = None
    equipment_type: Optional[str] = None
    registration_no: Optional[str] = None
    entry_date: Optional[date] = None
    exit_date: Optional[date] = None
    operator_name: Optional[str] = None
    operator_qualification_checked: Optional[bool] = None
    insurance_checked: Optional[bool] = None
    inspection_certificate_checked: Optional[bool] = None
    daily_check_required: Optional[bool] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectEquipmentListResponse(BaseModel):
    items: list[ProjectEquipmentResponse]


class ProjectEquipmentCreate(BaseModel):
    contractor_id: Optional[int] = None
    equipment_name: str = Field(..., max_length=200)
    equipment_type: Optional[str] = Field(default=None, max_length=100)
    registration_no: Optional[str] = Field(default=None, max_length=100)
    entry_date: Optional[date] = None
    exit_date: Optional[date] = None
    operator_name: Optional[str] = Field(default=None, max_length=100)
    operator_qualification_checked: Optional[bool] = None
    insurance_checked: Optional[bool] = None
    inspection_certificate_checked: Optional[bool] = None
    daily_check_required: Optional[bool] = None
    status: Optional[str] = Field(default=None, max_length=20)


class ProjectEquipmentUpdate(BaseModel):
    contractor_id: Optional[int] = None
    equipment_name: Optional[str] = Field(default=None, max_length=200)
    equipment_type: Optional[str] = Field(default=None, max_length=100)
    registration_no: Optional[str] = Field(default=None, max_length=100)
    entry_date: Optional[date] = None
    exit_date: Optional[date] = None
    operator_name: Optional[str] = Field(default=None, max_length=100)
    operator_qualification_checked: Optional[bool] = None
    insurance_checked: Optional[bool] = None
    inspection_certificate_checked: Optional[bool] = None
    daily_check_required: Optional[bool] = None
    status: Optional[str] = Field(default=None, max_length=20)

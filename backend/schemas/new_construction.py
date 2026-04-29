# V1.1 신축공사 API pydantic schemas.

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


# ── Work Schedules ─────────────────────────────────────────────────────────

class WorkScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    phase_no: Optional[int] = None
    phase_name: Optional[str] = None
    work_type: Optional[str] = None
    work_name: Optional[str] = None
    location: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    is_high_risk: Optional[bool] = None
    requires_work_plan: Optional[bool] = None
    requires_permit: Optional[bool] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WorkScheduleListResponse(BaseModel):
    items: list[WorkScheduleResponse]


class WorkScheduleCreate(BaseModel):
    phase_no: Optional[int] = Field(default=None, ge=0, le=12)
    phase_name: Optional[str] = Field(default=None, max_length=100)
    work_type: Optional[str] = Field(default=None, max_length=100)
    work_name: Optional[str] = Field(default=None, max_length=200)
    location: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    is_high_risk: Optional[bool] = None
    requires_work_plan: Optional[bool] = None
    requires_permit: Optional[bool] = None
    status: Optional[str] = Field(default=None, max_length=30)

    @model_validator(mode="after")
    def _check(self):
        if not (self.work_name or self.phase_name):
            raise ValueError("work_name or phase_name required")
        if self.planned_start_date and self.planned_end_date and self.planned_end_date < self.planned_start_date:
            raise ValueError("planned_end_date must be on/after planned_start_date")
        return self


class WorkScheduleUpdate(BaseModel):
    phase_no: Optional[int] = Field(default=None, ge=0, le=12)
    phase_name: Optional[str] = Field(default=None, max_length=100)
    work_type: Optional[str] = Field(default=None, max_length=100)
    work_name: Optional[str] = Field(default=None, max_length=200)
    location: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    is_high_risk: Optional[bool] = None
    requires_work_plan: Optional[bool] = None
    requires_permit: Optional[bool] = None
    status: Optional[str] = Field(default=None, max_length=30)

    @model_validator(mode="after")
    def _check(self):
        if self.planned_start_date and self.planned_end_date and self.planned_end_date < self.planned_start_date:
            raise ValueError("planned_end_date must be on/after planned_start_date")
        return self


# ── Safety Events ──────────────────────────────────────────────────────────
# 자동생성 Rule 실행은 본 모듈에서 다루지 않음. CRUD 입력 검증만 수행.

SafetyEventType = Literal[
    "worker_registered",
    "equipment_registered",
    "work_phase_starting",
    "daily_tbm",
    "incident_reported",
    "improvement_required",
    "completion_due",
]


class SafetyEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    site_id: Optional[int] = None
    event_type: Optional[str] = None
    event_date: Optional[date] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    status: Optional[str] = None
    payload_json: Optional[dict[str, Any]] = None
    created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class SafetyEventListResponse(BaseModel):
    items: list[SafetyEventResponse]


class SafetyEventCreate(BaseModel):
    site_id: Optional[int] = None
    event_type: SafetyEventType
    event_date: date
    source_type: Optional[str] = Field(default=None, max_length=100)
    source_id: Optional[int] = None
    status: Optional[str] = Field(default=None, max_length=30)
    payload_json: Optional[dict[str, Any]] = None
    created_by_user_id: Optional[int] = None


class SafetyEventUpdate(BaseModel):
    site_id: Optional[int] = None
    event_type: Optional[SafetyEventType] = None
    event_date: Optional[date] = None
    source_type: Optional[str] = Field(default=None, max_length=100)
    source_id: Optional[int] = None
    status: Optional[str] = Field(default=None, max_length=30)
    payload_json: Optional[dict[str, Any]] = None
    created_by_user_id: Optional[int] = None

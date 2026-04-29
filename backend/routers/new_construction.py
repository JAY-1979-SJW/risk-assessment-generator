# NOTE: V1.1 신축공사 라우터.
#       장비 엔드포인트 추가 시 'project_equipment' 테이블만 사용한다.
#       기존 마스터 'equipment' 테이블은 절대 read/write 금지.

from fastapi import APIRouter, HTTPException

from repositories import new_construction_repository as repo
from schemas.new_construction import (
    ContractorCreate,
    ContractorListResponse,
    ContractorResponse,
    ContractorUpdate,
    ProjectEquipmentCreate,
    ProjectEquipmentListResponse,
    ProjectEquipmentResponse,
    ProjectEquipmentUpdate,
    ProjectProfileResponse,
    ProjectProfileUpdate,
    SiteCreate,
    SiteListResponse,
    SiteResponse,
    SiteUpdate,
    WorkerCreate,
    WorkerListResponse,
    WorkerResponse,
    WorkerUpdate,
)

router = APIRouter(prefix="/v1/new-construction", tags=["v1.1 new-construction"])


# ── Project profile ────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/profile", response_model=ProjectProfileResponse)
def get_project_profile(project_id: int):
    row = repo.get_project_profile(project_id)
    if row is None:
        raise HTTPException(404, "Project not found")
    return row


@router.patch("/projects/{project_id}/profile", response_model=ProjectProfileResponse)
def update_project_profile(project_id: int, body: ProjectProfileUpdate):
    fields = body.model_dump(exclude_unset=True)
    row = repo.update_project_profile(project_id, fields)
    if row is None:
        raise HTTPException(404, "Project not found")
    return row


# ── Sites ──────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/sites", response_model=SiteListResponse)
def list_sites(project_id: int):
    return {"items": repo.list_sites(project_id)}


@router.post("/projects/{project_id}/sites", response_model=SiteResponse, status_code=201)
def create_site(project_id: int, body: SiteCreate):
    row = repo.create_site(project_id, body.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(404, "Project not found")
    return row


@router.patch("/sites/{site_id}", response_model=SiteResponse)
def update_site(site_id: int, body: SiteUpdate):
    row = repo.update_site(site_id, body.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(404, "Site not found")
    return row


@router.delete("/sites/{site_id}", status_code=204)
def delete_site(site_id: int):
    if not repo.soft_delete_site(site_id):
        raise HTTPException(404, "Site not found")


# ── Contractors ────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/contractors", response_model=ContractorListResponse)
def list_contractors(project_id: int):
    return {"items": repo.list_contractors(project_id)}


@router.post("/projects/{project_id}/contractors", response_model=ContractorResponse, status_code=201)
def create_contractor(project_id: int, body: ContractorCreate):
    row = repo.create_contractor(project_id, body.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(404, "Project not found")
    return row


@router.patch("/contractors/{contractor_id}", response_model=ContractorResponse)
def update_contractor(contractor_id: int, body: ContractorUpdate):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "No fields to update")
    row = repo.update_contractor(contractor_id, fields)
    if row is None:
        raise HTTPException(404, "Contractor not found")
    return row


@router.delete("/contractors/{contractor_id}", status_code=204)
def delete_contractor(contractor_id: int):
    if not repo.soft_delete_contractor(contractor_id):
        raise HTTPException(404, "Contractor not found")


# ── Workers ────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/workers", response_model=WorkerListResponse)
def list_workers(project_id: int):
    return {"items": repo.list_workers(project_id)}


@router.post("/projects/{project_id}/workers", response_model=WorkerResponse, status_code=201)
def create_worker(project_id: int, body: WorkerCreate):
    row, err = repo.create_worker(project_id, body.model_dump(exclude_unset=True))
    if err == "project_not_found":
        raise HTTPException(404, "Project not found")
    if err == "contractor_mismatch":
        raise HTTPException(400, "contractor_id does not belong to this project")
    return row


@router.patch("/workers/{worker_id}", response_model=WorkerResponse)
def update_worker(worker_id: int, body: WorkerUpdate):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "No fields to update")
    row, err = repo.update_worker(worker_id, fields)
    if err == "not_found":
        raise HTTPException(404, "Worker not found")
    if err == "contractor_mismatch":
        raise HTTPException(400, "contractor_id does not belong to this project")
    return row


@router.delete("/workers/{worker_id}", status_code=204)
def delete_worker(worker_id: int):
    if not repo.soft_delete_worker(worker_id):
        raise HTTPException(404, "Worker not found")


# ── Project Equipment (URL: /equipment, DB: project_equipment) ─────────────
# NOTE: URL 경로는 /equipment 이지만 DB 테이블은 project_equipment 만 사용한다.

@router.get("/projects/{project_id}/equipment", response_model=ProjectEquipmentListResponse)
def list_equipment(project_id: int):
    return {"items": repo.list_project_equipment(project_id)}


@router.post("/projects/{project_id}/equipment", response_model=ProjectEquipmentResponse, status_code=201)
def create_equipment(project_id: int, body: ProjectEquipmentCreate):
    row, err = repo.create_project_equipment(project_id, body.model_dump(exclude_unset=True))
    if err == "project_not_found":
        raise HTTPException(404, "Project not found")
    if err == "contractor_mismatch":
        raise HTTPException(400, "contractor_id does not belong to this project")
    return row


@router.patch("/equipment/{equipment_id}", response_model=ProjectEquipmentResponse)
def update_equipment(equipment_id: int, body: ProjectEquipmentUpdate):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "No fields to update")
    row, err = repo.update_project_equipment(equipment_id, fields)
    if err == "not_found":
        raise HTTPException(404, "Equipment not found")
    if err == "contractor_mismatch":
        raise HTTPException(400, "contractor_id does not belong to this project")
    return row


@router.delete("/equipment/{equipment_id}", status_code=204)
def delete_equipment(equipment_id: int):
    if not repo.soft_delete_project_equipment(equipment_id):
        raise HTTPException(404, "Equipment not found")

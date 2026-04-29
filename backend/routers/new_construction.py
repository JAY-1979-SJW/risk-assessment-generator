# NOTE: V1.1 신축공사 라우터.
#       장비 엔드포인트 추가 시 'project_equipment' 테이블만 사용한다.
#       기존 마스터 'equipment' 테이블은 절대 read/write 금지.

from fastapi import APIRouter, HTTPException

from repositories import new_construction_repository as repo
from schemas.new_construction import (
    ProjectProfileResponse,
    ProjectProfileUpdate,
    SiteCreate,
    SiteListResponse,
    SiteResponse,
    SiteUpdate,
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

# NOTE: V1.1 신축공사 라우터.
#       장비 엔드포인트 추가 시 'project_equipment' 테이블만 사용한다.
#       기존 마스터 'equipment' 테이블은 절대 read/write 금지.

from urllib.parse import quote as _urlquote

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from repositories import new_construction_repository as repo
from services import new_construction_rules as rules_svc
from services import new_construction_excel_runner as excel_runner
from services import new_construction_zip_builder as zip_builder
from services import new_construction_downloads as downloads_svc
from schemas.new_construction import (
    DocumentJobRunResponse,
    DocumentPackageZipBuildResponse,
    RuleDefinitionResponse,
    RuleGenerateRequest,
    RuleGenerateResponse,
    RuleListResponse,
    RulePreviewRequest,
    RulePreviewResponse,
    ContractorCreate,
    ContractorListResponse,
    ContractorResponse,
    ContractorUpdate,
    DocumentGenerationJobCreate,
    DocumentGenerationJobListResponse,
    DocumentGenerationJobResponse,
    DocumentGenerationJobUpdate,
    GeneratedDocumentFileCreate,
    GeneratedDocumentFileListResponse,
    GeneratedDocumentFileResponse,
    GeneratedDocumentFileUpdate,
    GeneratedDocumentPackageCreate,
    GeneratedDocumentPackageListResponse,
    GeneratedDocumentPackageResponse,
    GeneratedDocumentPackageUpdate,
    ProjectEquipmentCreate,
    ProjectEquipmentListResponse,
    ProjectEquipmentResponse,
    ProjectEquipmentUpdate,
    ProjectProfileResponse,
    ProjectProfileUpdate,
    SafetyEventCreate,
    SafetyEventListResponse,
    SafetyEventResponse,
    SafetyEventUpdate,
    SiteCreate,
    SiteListResponse,
    SiteResponse,
    SiteUpdate,
    WorkerCreate,
    WorkerListResponse,
    WorkerResponse,
    WorkerUpdate,
    WorkScheduleCreate,
    WorkScheduleListResponse,
    WorkScheduleResponse,
    WorkScheduleUpdate,
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


# ── Work Schedules ─────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/work-schedules", response_model=WorkScheduleListResponse)
def list_work_schedules(project_id: int):
    return {"items": repo.list_work_schedules(project_id)}


@router.post("/projects/{project_id}/work-schedules", response_model=WorkScheduleResponse, status_code=201)
def create_work_schedule(project_id: int, body: WorkScheduleCreate):
    row = repo.create_work_schedule(project_id, body.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(404, "Project not found")
    return row


@router.patch("/work-schedules/{schedule_id}", response_model=WorkScheduleResponse)
def update_work_schedule(schedule_id: int, body: WorkScheduleUpdate):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "No fields to update")
    row = repo.update_work_schedule(schedule_id, fields)
    if row is None:
        raise HTTPException(404, "Work schedule not found")
    return row


@router.delete("/work-schedules/{schedule_id}", status_code=204)
def delete_work_schedule(schedule_id: int):
    if not repo.soft_delete_work_schedule(schedule_id):
        raise HTTPException(404, "Work schedule not found")


# ── Safety Events ──────────────────────────────────────────────────────────
# Rule 실행/트리거는 본 라우터에서 처리하지 않고 CRUD만 노출한다.

@router.get("/projects/{project_id}/safety-events", response_model=SafetyEventListResponse)
def list_safety_events(project_id: int):
    return {"items": repo.list_safety_events(project_id)}


@router.post("/projects/{project_id}/safety-events", response_model=SafetyEventResponse, status_code=201)
def create_safety_event(project_id: int, body: SafetyEventCreate):
    row, err = repo.create_safety_event(project_id, body.model_dump(exclude_unset=True))
    if err == "project_not_found":
        raise HTTPException(404, "Project not found")
    if err == "site_mismatch":
        raise HTTPException(400, "site_id does not belong to this project")
    return row


@router.patch("/safety-events/{event_id}", response_model=SafetyEventResponse)
def update_safety_event(event_id: int, body: SafetyEventUpdate):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "No fields to update")
    row, err = repo.update_safety_event(event_id, fields)
    if err == "not_found":
        raise HTTPException(404, "Safety event not found")
    if err == "site_mismatch":
        raise HTTPException(400, "site_id does not belong to this project")
    return row


@router.delete("/safety-events/{event_id}", status_code=204)
def delete_safety_event(event_id: int):
    if not repo.soft_delete_safety_event(event_id):
        raise HTTPException(404, "Safety event not found")


# ── Document Generation Jobs ───────────────────────────────────────────────
# 메타데이터만. 실제 builder 실행/Excel 생성/Rule 트리거는 본 라우터에서 다루지 않는다.

@router.get("/projects/{project_id}/document-jobs", response_model=DocumentGenerationJobListResponse)
def list_document_jobs(project_id: int):
    return {"items": repo.list_document_jobs(project_id)}


@router.post("/projects/{project_id}/document-jobs", response_model=DocumentGenerationJobResponse, status_code=201)
def create_document_job(project_id: int, body: DocumentGenerationJobCreate):
    row, err = repo.create_document_job(project_id, body.model_dump(exclude_unset=True))
    if err == "project_not_found":
        raise HTTPException(404, "Project not found")
    if err == "safety_event_mismatch":
        raise HTTPException(400, "safety_event_id does not belong to this project")
    return row


@router.get("/document-jobs/{job_id}", response_model=DocumentGenerationJobResponse)
def get_document_job(job_id: int):
    row = repo.get_document_job(job_id)
    if row is None:
        raise HTTPException(404, "Document job not found")
    return row


@router.patch("/document-jobs/{job_id}", response_model=DocumentGenerationJobResponse)
def update_document_job(job_id: int, body: DocumentGenerationJobUpdate):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "No fields to update")
    row, err = repo.update_document_job(job_id, fields)
    if err == "not_found":
        raise HTTPException(404, "Document job not found")
    if err == "safety_event_mismatch":
        raise HTTPException(400, "safety_event_id does not belong to this project")
    return row


# ── Generated Document Packages ────────────────────────────────────────────

@router.get("/projects/{project_id}/document-packages", response_model=GeneratedDocumentPackageListResponse)
def list_document_packages(project_id: int):
    return {"items": repo.list_document_packages(project_id)}


@router.post("/projects/{project_id}/document-packages", response_model=GeneratedDocumentPackageResponse, status_code=201)
def create_document_package(project_id: int, body: GeneratedDocumentPackageCreate):
    row, err = repo.create_document_package(project_id, body.model_dump(exclude_unset=True))
    if err == "project_not_found":
        raise HTTPException(404, "Project not found")
    if err == "safety_event_mismatch":
        raise HTTPException(400, "safety_event_id does not belong to this project")
    if err == "generation_job_mismatch":
        raise HTTPException(400, "generation_job_id does not belong to this project")
    return row


@router.get("/document-packages/{package_id}", response_model=GeneratedDocumentPackageResponse)
def get_document_package(package_id: int):
    row = repo.get_document_package(package_id)
    if row is None:
        raise HTTPException(404, "Document package not found")
    return row


@router.patch("/document-packages/{package_id}", response_model=GeneratedDocumentPackageResponse)
def update_document_package(package_id: int, body: GeneratedDocumentPackageUpdate):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "No fields to update")
    row, err = repo.update_document_package(package_id, fields)
    if err == "not_found":
        raise HTTPException(404, "Document package not found")
    if err == "safety_event_mismatch":
        raise HTTPException(400, "safety_event_id does not belong to this project")
    if err == "generation_job_mismatch":
        raise HTTPException(400, "generation_job_id does not belong to this project")
    return row


# ── Generated Document Files ───────────────────────────────────────────────
# 다운로드/스트리밍 엔드포인트는 본 단계에서 구현하지 않는다 (메타만).

@router.get("/document-packages/{package_id}/files", response_model=GeneratedDocumentFileListResponse)
def list_document_files(package_id: int):
    if repo.get_document_package(package_id) is None:
        raise HTTPException(404, "Document package not found")
    return {"items": repo.list_document_files(package_id)}


@router.post("/document-packages/{package_id}/files", response_model=GeneratedDocumentFileResponse, status_code=201)
def create_document_file(package_id: int, body: GeneratedDocumentFileCreate):
    row, err = repo.create_document_file(package_id, body.model_dump(exclude_unset=True))
    if err == "package_not_found":
        raise HTTPException(404, "Document package not found")
    if err == "generation_job_mismatch":
        raise HTTPException(400, "generation_job_id does not belong to this project")
    return row


@router.get("/document-files/{file_id}", response_model=GeneratedDocumentFileResponse)
def get_document_file(file_id: int):
    row = repo.get_document_file(file_id)
    if row is None:
        raise HTTPException(404, "Document file not found")
    return row


@router.patch("/document-files/{file_id}", response_model=GeneratedDocumentFileResponse)
def update_document_file(file_id: int, body: GeneratedDocumentFileUpdate):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "No fields to update")
    row, err = repo.update_document_file(file_id, fields)
    if err == "not_found":
        raise HTTPException(404, "Document file not found")
    if err == "generation_job_mismatch":
        raise HTTPException(400, "generation_job_id does not belong to this project")
    return row


# ── Rule MVP (list / preview / generate metadata) ─────────────────────────
# preview: DB 쓰기 없음. generate: 메타 4테이블 INSERT (Excel/ZIP/파일 미생성).

@router.get("/rules", response_model=RuleListResponse)
def list_rules():
    return {"items": rules_svc.list_rules()}


@router.post("/projects/{project_id}/rules/{rule_id}/preview", response_model=RulePreviewResponse)
def preview_rule(project_id: int, rule_id: str, body: RulePreviewRequest):
    payload = body.model_dump(exclude_unset=True)
    row, err = rules_svc.preview(project_id, rule_id, payload)
    if err == "rule_not_found":
        raise HTTPException(404, "Rule not found")
    if err == "project_not_found":
        raise HTTPException(404, "Project not found")
    if err == "safety_event_mismatch":
        raise HTTPException(400, "safety_event_id does not belong to this project")
    return row


@router.post("/projects/{project_id}/rules/{rule_id}/generate", response_model=RuleGenerateResponse, status_code=201)
def generate_rule(project_id: int, rule_id: str, body: RuleGenerateRequest):
    payload = body.model_dump(exclude_unset=True)
    force = bool(payload.pop("force", False))
    row, err = rules_svc.generate(project_id, rule_id, payload, force=force)
    if err == "rule_not_found":
        raise HTTPException(404, "Rule not found")
    if err == "project_not_found":
        raise HTTPException(404, "Project not found")
    if err == "safety_event_mismatch":
        raise HTTPException(400, "safety_event_id does not belong to this project")
    if err == "not_ready":
        raise HTTPException(400, {"message": "Rule preconditions not met", "missing_fields": row["missing_fields"]})
    return row


# ── Excel 실행 (Stage 2B-5A) ───────────────────────────────────────────────
# 명시 실행 only. ZIP/다운로드/자동 background worker 미포함.

@router.post("/document-jobs/{job_id}/run-excel", response_model=DocumentJobRunResponse)
def run_document_job_excel(job_id: int):
    row, err = excel_runner.run_excel(job_id)
    if err == "job_not_found":
        raise HTTPException(404, "Document job not found")
    if err == "package_not_found":
        raise HTTPException(404, "Document package not found for this job")
    if err == "no_files":
        raise HTTPException(400, "No document files to generate")
    if err == "invalid_status":
        raise HTTPException(409, {
            "message": "Job is not runnable (only pending/failed allowed)",
            "current_status": row.get("status") if row else None,
        })
    return row


# ── ZIP 생성 (Stage 2B-5C) ────────────────────────────────────────────────
# 명시 실행 only. 다운로드 endpoint / StreamingResponse / FileResponse 미포함.

@router.post(
    "/document-packages/{package_id}/build-zip",
    response_model=DocumentPackageZipBuildResponse,
)
def build_document_package_zip(package_id: int):
    row, err = zip_builder.build_zip(package_id)
    if err == "package_not_found":
        raise HTTPException(404, "Document package not found")
    if err == "no_files":
        raise HTTPException(400, "No document files in package")
    if err == "invalid_status":
        raise HTTPException(409, {
            "message": "Package is not zippable (only ready/created allowed)",
            "current_status": row.get("status") if row else None,
        })
    if err == "files_not_ready":
        raise HTTPException(400, {
            "message": "Some files are not ready",
            "not_ready_file_ids": (row or {}).get("not_ready_file_ids", []),
        })
    if err == "file_missing":
        raise HTTPException(400, {
            "message": "Some files are missing on disk",
            "missing": (row or {}).get("missing", []),
        })
    return row


# ── ZIP 다운로드 (Stage 2B-5D) ─────────────────────────────────────────────
# DB 의 zip_file_path 를 그대로 신뢰하지 않고 base_dir 하위 / `.zip` / 실제
# 파일 여부를 검증한 뒤 FileResponse 로 반환. 상태 변경 / ZIP 재생성 / Excel
# builder 실행 일체 없음.

@router.get("/document-packages/{package_id}/download-zip")
def download_document_package_zip(package_id: int):
    pkg = repo.get_document_package(package_id)
    if pkg is None:
        raise HTTPException(404, "Document package not found")
    if pkg.get("status") != "ready":
        raise HTTPException(409, {
            "message": "Package is not ready for download",
            "current_status": pkg.get("status"),
        })

    resolved, err = downloads_svc.resolve_zip_path(pkg.get("zip_file_path"))
    if err == "zip_not_built":
        raise HTTPException(400, "ZIP has not been built for this package")
    if err == "unsafe_path":
        raise HTTPException(400, "Unsafe ZIP file path")
    if err == "zip_file_missing":
        raise HTTPException(404, "ZIP file is missing on disk")

    filename = downloads_svc.safe_download_filename(package_id, pkg.get("package_name"))
    # RFC 5987: ASCII fallback + UTF-8 encoded form for non-ASCII filenames.
    ascii_fallback = f"package_{int(package_id)}.zip"
    content_disposition = (
        f'attachment; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{_urlquote(filename)}"
    )
    return FileResponse(
        path=str(resolved),
        media_type="application/zip",
        headers={"Content-Disposition": content_disposition},
    )

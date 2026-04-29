# NOTE: V1.1 신축공사 전용 repository.
#       장비 관련 함수는 모두 'project_equipment' 테이블만 사용한다.
#       기존 마스터 'equipment'(equipment_code PK, document_equipment_map FK)는 절대 접근 금지.

import psycopg2.extras
from psycopg2.extras import Json

from db import fetchone, fetchall, execute, get_conn

PROJECT_PROFILE_FIELDS = (
    "construction_type",
    "project_status",
    "start_date",
    "end_date",
    "client_name",
    "prime_contractor_name",
    "site_address",
    "site_manager_name",
    "safety_manager_name",
    "total_floor_count",
    "basement_floor_count",
    "excavation_depth_m",
    "has_tower_crane",
    "has_pile_driver",
    "has_scaffold_over_31m",
    "safety_plan_required",
    "risk_level",
    "manager_id",
)

PROJECT_PROFILE_SELECT = ", ".join(("id", "title", "status", "created_at", "updated_at") + PROJECT_PROFILE_FIELDS)

SITE_FIELDS = (
    "site_name",
    "address",
    "detail_address",
    "site_manager_name",
    "site_manager_phone",
    "safety_manager_name",
    "safety_manager_phone",
    "status",
)

SITE_SELECT = "id, project_id, " + ", ".join(SITE_FIELDS) + ", created_at, updated_at"


def _project_exists(project_id: int) -> bool:
    return fetchone("SELECT 1 AS x FROM projects WHERE id = %s", (project_id,)) is not None


# ── projects ────────────────────────────────────────────────────────────────

def get_project_profile(project_id: int) -> dict | None:
    return fetchone(
        f"SELECT {PROJECT_PROFILE_SELECT} FROM projects WHERE id = %s",
        (project_id,),
    )


def update_project_profile(project_id: int, fields: dict) -> dict | None:
    allowed = {k: v for k, v in fields.items() if k in PROJECT_PROFILE_FIELDS}
    if not allowed:
        return get_project_profile(project_id)
    if not _project_exists(project_id):
        return None
    set_clause = ", ".join(f"{k} = %s" for k in allowed.keys())
    params = list(allowed.values()) + [project_id]
    execute(
        f"UPDATE projects SET {set_clause}, updated_at = NOW() WHERE id = %s",
        params,
    )
    return get_project_profile(project_id)


# ── sites ──────────────────────────────────────────────────────────────────

def list_sites(project_id: int) -> list[dict]:
    return fetchall(
        f"SELECT {SITE_SELECT} FROM sites WHERE project_id = %s ORDER BY created_at DESC",
        (project_id,),
    )


def get_site(site_id: int) -> dict | None:
    return fetchone(f"SELECT {SITE_SELECT} FROM sites WHERE id = %s", (site_id,))


def create_site(project_id: int, payload: dict) -> dict | None:
    if not _project_exists(project_id):
        return None
    allowed = {k: v for k, v in payload.items() if k in SITE_FIELDS}
    cols = ["project_id"] + list(allowed.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    params = [project_id] + list(allowed.values())
    new_id = execute(
        f"INSERT INTO sites ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
        params,
    )
    return get_site(new_id)


def update_site(site_id: int, fields: dict) -> dict | None:
    if get_site(site_id) is None:
        return None
    allowed = {k: v for k, v in fields.items() if k in SITE_FIELDS}
    if not allowed:
        return get_site(site_id)
    set_clause = ", ".join(f"{k} = %s" for k in allowed.keys())
    params = list(allowed.values()) + [site_id]
    execute(
        f"UPDATE sites SET {set_clause}, updated_at = NOW() WHERE id = %s",
        params,
    )
    return get_site(site_id)


def soft_delete_site(site_id: int) -> bool:
    if get_site(site_id) is None:
        return False
    execute(
        "UPDATE sites SET status = 'inactive', updated_at = NOW() WHERE id = %s",
        (site_id,),
    )
    return True


# ── contractors ────────────────────────────────────────────────────────────

CONTRACTOR_FIELDS = (
    "contractor_type",
    "company_name",
    "business_registration_no",
    "representative_name",
    "contact_name",
    "contact_phone",
    "work_scope",
    "safety_evaluation_status",
    "status",
)

CONTRACTOR_SELECT = "id, project_id, " + ", ".join(CONTRACTOR_FIELDS) + ", created_at, updated_at"


def list_contractors(project_id: int) -> list[dict]:
    return fetchall(
        f"SELECT {CONTRACTOR_SELECT} FROM contractors WHERE project_id = %s ORDER BY created_at DESC",
        (project_id,),
    )


def get_contractor(contractor_id: int) -> dict | None:
    return fetchone(f"SELECT {CONTRACTOR_SELECT} FROM contractors WHERE id = %s", (contractor_id,))


def _contractor_belongs_to_project(contractor_id: int, project_id: int) -> bool:
    row = fetchone(
        "SELECT 1 AS x FROM contractors WHERE id = %s AND project_id = %s",
        (contractor_id, project_id),
    )
    return row is not None


def create_contractor(project_id: int, payload: dict) -> dict | None:
    if not _project_exists(project_id):
        return None
    allowed = {k: v for k, v in payload.items() if k in CONTRACTOR_FIELDS}
    cols = ["project_id"] + list(allowed.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    params = [project_id] + list(allowed.values())
    new_id = execute(
        f"INSERT INTO contractors ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
        params,
    )
    return get_contractor(new_id)


def update_contractor(contractor_id: int, fields: dict) -> dict | None:
    if get_contractor(contractor_id) is None:
        return None
    allowed = {k: v for k, v in fields.items() if k in CONTRACTOR_FIELDS}
    if not allowed:
        return get_contractor(contractor_id)
    set_clause = ", ".join(f"{k} = %s" for k in allowed.keys())
    params = list(allowed.values()) + [contractor_id]
    execute(
        f"UPDATE contractors SET {set_clause}, updated_at = NOW() WHERE id = %s",
        params,
    )
    return get_contractor(contractor_id)


def soft_delete_contractor(contractor_id: int) -> bool:
    if get_contractor(contractor_id) is None:
        return False
    execute(
        "UPDATE contractors SET status = 'inactive', updated_at = NOW() WHERE id = %s",
        (contractor_id,),
    )
    return True


# ── workers ────────────────────────────────────────────────────────────────
# 개인정보 최소화: 주민/외국인등록번호·전화번호·건강정보 저장 금지.

WORKER_FIELDS = (
    "contractor_id",
    "worker_name",
    "trade",
    "job_role",
    "first_work_date",
    "construction_basic_training_checked",
    "new_hire_training_checked",
    "ppe_issued",
    "status",
)

WORKER_SELECT = "id, project_id, " + ", ".join(WORKER_FIELDS) + ", created_at, updated_at"


def list_workers(project_id: int) -> list[dict]:
    return fetchall(
        f"SELECT {WORKER_SELECT} FROM workers WHERE project_id = %s ORDER BY created_at DESC",
        (project_id,),
    )


def get_worker(worker_id: int) -> dict | None:
    return fetchone(f"SELECT {WORKER_SELECT} FROM workers WHERE id = %s", (worker_id,))


def create_worker(project_id: int, payload: dict) -> tuple[dict | None, str | None]:
    """returns (row, err). err in {None, 'project_not_found', 'contractor_mismatch'}."""
    if not _project_exists(project_id):
        return None, "project_not_found"
    allowed = {k: v for k, v in payload.items() if k in WORKER_FIELDS}
    cid = allowed.get("contractor_id")
    if cid is not None and not _contractor_belongs_to_project(cid, project_id):
        return None, "contractor_mismatch"
    cols = ["project_id"] + list(allowed.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    params = [project_id] + list(allowed.values())
    new_id = execute(
        f"INSERT INTO workers ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
        params,
    )
    return get_worker(new_id), None


def update_worker(worker_id: int, fields: dict) -> tuple[dict | None, str | None]:
    current = get_worker(worker_id)
    if current is None:
        return None, "not_found"
    allowed = {k: v for k, v in fields.items() if k in WORKER_FIELDS}
    if not allowed:
        return current, None
    if "contractor_id" in allowed and allowed["contractor_id"] is not None:
        if not _contractor_belongs_to_project(allowed["contractor_id"], current["project_id"]):
            return None, "contractor_mismatch"
    set_clause = ", ".join(f"{k} = %s" for k in allowed.keys())
    params = list(allowed.values()) + [worker_id]
    execute(
        f"UPDATE workers SET {set_clause}, updated_at = NOW() WHERE id = %s",
        params,
    )
    return get_worker(worker_id), None


def soft_delete_worker(worker_id: int) -> bool:
    if get_worker(worker_id) is None:
        return False
    execute(
        "UPDATE workers SET status = 'inactive', updated_at = NOW() WHERE id = %s",
        (worker_id,),
    )
    return True


# ── project_equipment ──────────────────────────────────────────────────────
# DB 테이블은 'project_equipment'. 운영 DB의 마스터 'equipment' 테이블은 접근 금지.

PROJECT_EQUIPMENT_FIELDS = (
    "contractor_id",
    "equipment_name",
    "equipment_type",
    "registration_no",
    "entry_date",
    "exit_date",
    "operator_name",
    "operator_qualification_checked",
    "insurance_checked",
    "inspection_certificate_checked",
    "daily_check_required",
    "status",
)

PROJECT_EQUIPMENT_SELECT = "id, project_id, " + ", ".join(PROJECT_EQUIPMENT_FIELDS) + ", created_at, updated_at"


def list_project_equipment(project_id: int) -> list[dict]:
    return fetchall(
        f"SELECT {PROJECT_EQUIPMENT_SELECT} FROM project_equipment WHERE project_id = %s ORDER BY created_at DESC",
        (project_id,),
    )


def get_project_equipment(equipment_id: int) -> dict | None:
    return fetchone(
        f"SELECT {PROJECT_EQUIPMENT_SELECT} FROM project_equipment WHERE id = %s",
        (equipment_id,),
    )


def create_project_equipment(project_id: int, payload: dict) -> tuple[dict | None, str | None]:
    if not _project_exists(project_id):
        return None, "project_not_found"
    allowed = {k: v for k, v in payload.items() if k in PROJECT_EQUIPMENT_FIELDS}
    cid = allowed.get("contractor_id")
    if cid is not None and not _contractor_belongs_to_project(cid, project_id):
        return None, "contractor_mismatch"
    cols = ["project_id"] + list(allowed.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    params = [project_id] + list(allowed.values())
    new_id = execute(
        f"INSERT INTO project_equipment ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
        params,
    )
    return get_project_equipment(new_id), None


def update_project_equipment(equipment_id: int, fields: dict) -> tuple[dict | None, str | None]:
    current = get_project_equipment(equipment_id)
    if current is None:
        return None, "not_found"
    allowed = {k: v for k, v in fields.items() if k in PROJECT_EQUIPMENT_FIELDS}
    if not allowed:
        return current, None
    if "contractor_id" in allowed and allowed["contractor_id"] is not None:
        if not _contractor_belongs_to_project(allowed["contractor_id"], current["project_id"]):
            return None, "contractor_mismatch"
    set_clause = ", ".join(f"{k} = %s" for k in allowed.keys())
    params = list(allowed.values()) + [equipment_id]
    execute(
        f"UPDATE project_equipment SET {set_clause}, updated_at = NOW() WHERE id = %s",
        params,
    )
    return get_project_equipment(equipment_id), None


def soft_delete_project_equipment(equipment_id: int) -> bool:
    if get_project_equipment(equipment_id) is None:
        return False
    execute(
        "UPDATE project_equipment SET status = 'inactive', updated_at = NOW() WHERE id = %s",
        (equipment_id,),
    )
    return True


# ── work_schedules ─────────────────────────────────────────────────────────

WORK_SCHEDULE_FIELDS = (
    "phase_no",
    "phase_name",
    "work_type",
    "work_name",
    "location",
    "planned_start_date",
    "planned_end_date",
    "actual_start_date",
    "actual_end_date",
    "is_high_risk",
    "requires_work_plan",
    "requires_permit",
    "status",
)

WORK_SCHEDULE_SELECT = "id, project_id, " + ", ".join(WORK_SCHEDULE_FIELDS) + ", created_at, updated_at"


def list_work_schedules(project_id: int) -> list[dict]:
    return fetchall(
        f"SELECT {WORK_SCHEDULE_SELECT} FROM work_schedules WHERE project_id = %s "
        f"ORDER BY COALESCE(planned_start_date, created_at::date) ASC, id ASC",
        (project_id,),
    )


def get_work_schedule(schedule_id: int) -> dict | None:
    return fetchone(f"SELECT {WORK_SCHEDULE_SELECT} FROM work_schedules WHERE id = %s", (schedule_id,))


def create_work_schedule(project_id: int, payload: dict) -> dict | None:
    if not _project_exists(project_id):
        return None
    allowed = {k: v for k, v in payload.items() if k in WORK_SCHEDULE_FIELDS}
    cols = ["project_id"] + list(allowed.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    params = [project_id] + list(allowed.values())
    new_id = execute(
        f"INSERT INTO work_schedules ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
        params,
    )
    return get_work_schedule(new_id)


def update_work_schedule(schedule_id: int, fields: dict) -> dict | None:
    if get_work_schedule(schedule_id) is None:
        return None
    allowed = {k: v for k, v in fields.items() if k in WORK_SCHEDULE_FIELDS}
    if not allowed:
        return get_work_schedule(schedule_id)
    set_clause = ", ".join(f"{k} = %s" for k in allowed.keys())
    params = list(allowed.values()) + [schedule_id]
    execute(
        f"UPDATE work_schedules SET {set_clause}, updated_at = NOW() WHERE id = %s",
        params,
    )
    return get_work_schedule(schedule_id)


def soft_delete_work_schedule(schedule_id: int) -> bool:
    if get_work_schedule(schedule_id) is None:
        return False
    execute(
        "UPDATE work_schedules SET status = 'cancelled', updated_at = NOW() WHERE id = %s",
        (schedule_id,),
    )
    return True


# ── safety_events ──────────────────────────────────────────────────────────
# 자동생성 Rule 실행 로직은 본 단계에서 구현하지 않음 (CRUD만).

SAFETY_EVENT_FIELDS = (
    "site_id",
    "event_type",
    "event_date",
    "source_type",
    "source_id",
    "status",
    "payload_json",
    "created_by_user_id",
)

SAFETY_EVENT_SELECT = "id, project_id, " + ", ".join(SAFETY_EVENT_FIELDS) + ", created_at, updated_at"


def _site_belongs_to_project(site_id: int, project_id: int) -> bool:
    row = fetchone(
        "SELECT 1 AS x FROM sites WHERE id = %s AND project_id = %s",
        (site_id, project_id),
    )
    return row is not None


def _wrap_payload(allowed: dict) -> dict:
    """psycopg2: dict → JSONB needs Json() adapter."""
    if "payload_json" in allowed and allowed["payload_json"] is not None:
        allowed = dict(allowed)
        allowed["payload_json"] = Json(allowed["payload_json"])
    return allowed


def list_safety_events(project_id: int) -> list[dict]:
    return fetchall(
        f"SELECT {SAFETY_EVENT_SELECT} FROM safety_events WHERE project_id = %s "
        f"ORDER BY event_date DESC, id DESC",
        (project_id,),
    )


def get_safety_event(event_id: int) -> dict | None:
    return fetchone(f"SELECT {SAFETY_EVENT_SELECT} FROM safety_events WHERE id = %s", (event_id,))


def create_safety_event(project_id: int, payload: dict) -> tuple[dict | None, str | None]:
    if not _project_exists(project_id):
        return None, "project_not_found"
    allowed = {k: v for k, v in payload.items() if k in SAFETY_EVENT_FIELDS}
    sid = allowed.get("site_id")
    if sid is not None and not _site_belongs_to_project(sid, project_id):
        return None, "site_mismatch"
    allowed = _wrap_payload(allowed)
    cols = ["project_id"] + list(allowed.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    params = [project_id] + list(allowed.values())
    new_id = execute(
        f"INSERT INTO safety_events ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
        params,
    )
    return get_safety_event(new_id), None


def update_safety_event(event_id: int, fields: dict) -> tuple[dict | None, str | None]:
    current = get_safety_event(event_id)
    if current is None:
        return None, "not_found"
    allowed = {k: v for k, v in fields.items() if k in SAFETY_EVENT_FIELDS}
    if not allowed:
        return current, None
    if "site_id" in allowed and allowed["site_id"] is not None:
        if not _site_belongs_to_project(allowed["site_id"], current["project_id"]):
            return None, "site_mismatch"
    allowed = _wrap_payload(allowed)
    set_clause = ", ".join(f"{k} = %s" for k in allowed.keys())
    params = list(allowed.values()) + [event_id]
    execute(
        f"UPDATE safety_events SET {set_clause}, updated_at = NOW() WHERE id = %s",
        params,
    )
    return get_safety_event(event_id), None


def soft_delete_safety_event(event_id: int) -> bool:
    if get_safety_event(event_id) is None:
        return False
    execute(
        "UPDATE safety_events SET status = 'cancelled', updated_at = NOW() WHERE id = %s",
        (event_id,),
    )
    return True


# ── helpers : cross-project ownership ──────────────────────────────────────

def _safety_event_belongs_to_project(event_id: int, project_id: int) -> bool:
    return fetchone(
        "SELECT 1 AS x FROM safety_events WHERE id = %s AND project_id = %s",
        (event_id, project_id),
    ) is not None


def _generation_job_belongs_to_project(job_id: int, project_id: int) -> bool:
    return fetchone(
        "SELECT 1 AS x FROM document_generation_jobs WHERE id = %s AND project_id = %s",
        (job_id, project_id),
    ) is not None


def _package_belongs_to_project(package_id: int, project_id: int) -> bool:
    return fetchone(
        "SELECT 1 AS x FROM generated_document_packages WHERE id = %s AND project_id = %s",
        (package_id, project_id),
    ) is not None


# ── document_generation_jobs ───────────────────────────────────────────────
# 본 단계는 메타데이터 CRUD만. Excel builder / Rule 실행 / ZIP 생성 미포함.

DOC_JOB_FIELDS = (
    "safety_event_id",
    "requested_by_user_id",
    "job_type",
    "form_type",
    "supplemental_type",
    "status",
    "input_snapshot_json",
    "error_message",
    "started_at",
    "finished_at",
)

DOC_JOB_SELECT = "id, project_id, " + ", ".join(DOC_JOB_FIELDS) + ", created_at, updated_at"


def _wrap_input_snapshot(allowed: dict) -> dict:
    if "input_snapshot_json" in allowed and allowed["input_snapshot_json"] is not None:
        allowed = dict(allowed)
        allowed["input_snapshot_json"] = Json(allowed["input_snapshot_json"])
    return allowed


def list_document_jobs(project_id: int) -> list[dict]:
    return fetchall(
        f"SELECT {DOC_JOB_SELECT} FROM document_generation_jobs WHERE project_id = %s "
        f"ORDER BY created_at DESC, id DESC",
        (project_id,),
    )


def get_document_job(job_id: int) -> dict | None:
    return fetchone(f"SELECT {DOC_JOB_SELECT} FROM document_generation_jobs WHERE id = %s", (job_id,))


def create_document_job(project_id: int, payload: dict) -> tuple[dict | None, str | None]:
    if not _project_exists(project_id):
        return None, "project_not_found"
    allowed = {k: v for k, v in payload.items() if k in DOC_JOB_FIELDS}
    sev = allowed.get("safety_event_id")
    if sev is not None and not _safety_event_belongs_to_project(sev, project_id):
        return None, "safety_event_mismatch"
    allowed = _wrap_input_snapshot(allowed)
    cols = ["project_id"] + list(allowed.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    params = [project_id] + list(allowed.values())
    new_id = execute(
        f"INSERT INTO document_generation_jobs ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
        params,
    )
    return get_document_job(new_id), None


def update_document_job(job_id: int, fields: dict) -> tuple[dict | None, str | None]:
    current = get_document_job(job_id)
    if current is None:
        return None, "not_found"
    allowed = {k: v for k, v in fields.items() if k in DOC_JOB_FIELDS}
    if not allowed:
        return current, None
    if "safety_event_id" in allowed and allowed["safety_event_id"] is not None:
        if not _safety_event_belongs_to_project(allowed["safety_event_id"], current["project_id"]):
            return None, "safety_event_mismatch"
    allowed = _wrap_input_snapshot(allowed)
    set_clause = ", ".join(f"{k} = %s" for k in allowed.keys())
    params = list(allowed.values()) + [job_id]
    execute(
        f"UPDATE document_generation_jobs SET {set_clause}, updated_at = NOW() WHERE id = %s",
        params,
    )
    return get_document_job(job_id), None


# ── generated_document_packages ────────────────────────────────────────────

DOC_PACKAGE_FIELDS = (
    "safety_event_id",
    "generation_job_id",
    "package_type",
    "package_name",
    "rule_id",
    "status",
    "document_count",
    "storage_key",
    "zip_file_path",
    "created_by_user_id",
)

DOC_PACKAGE_SELECT = "id, project_id, " + ", ".join(DOC_PACKAGE_FIELDS) + ", created_at, updated_at"


def list_document_packages(project_id: int) -> list[dict]:
    return fetchall(
        f"SELECT {DOC_PACKAGE_SELECT} FROM generated_document_packages WHERE project_id = %s "
        f"ORDER BY created_at DESC, id DESC",
        (project_id,),
    )


def get_document_package(package_id: int) -> dict | None:
    return fetchone(
        f"SELECT {DOC_PACKAGE_SELECT} FROM generated_document_packages WHERE id = %s",
        (package_id,),
    )


def create_document_package(project_id: int, payload: dict) -> tuple[dict | None, str | None]:
    if not _project_exists(project_id):
        return None, "project_not_found"
    allowed = {k: v for k, v in payload.items() if k in DOC_PACKAGE_FIELDS}
    sev = allowed.get("safety_event_id")
    if sev is not None and not _safety_event_belongs_to_project(sev, project_id):
        return None, "safety_event_mismatch"
    job = allowed.get("generation_job_id")
    if job is not None and not _generation_job_belongs_to_project(job, project_id):
        return None, "generation_job_mismatch"
    cols = ["project_id"] + list(allowed.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    params = [project_id] + list(allowed.values())
    new_id = execute(
        f"INSERT INTO generated_document_packages ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
        params,
    )
    return get_document_package(new_id), None


def update_document_package(package_id: int, fields: dict) -> tuple[dict | None, str | None]:
    current = get_document_package(package_id)
    if current is None:
        return None, "not_found"
    allowed = {k: v for k, v in fields.items() if k in DOC_PACKAGE_FIELDS}
    if not allowed:
        return current, None
    pid = current["project_id"]
    if "safety_event_id" in allowed and allowed["safety_event_id"] is not None:
        if not _safety_event_belongs_to_project(allowed["safety_event_id"], pid):
            return None, "safety_event_mismatch"
    if "generation_job_id" in allowed and allowed["generation_job_id"] is not None:
        if not _generation_job_belongs_to_project(allowed["generation_job_id"], pid):
            return None, "generation_job_mismatch"
    set_clause = ", ".join(f"{k} = %s" for k in allowed.keys())
    params = list(allowed.values()) + [package_id]
    execute(
        f"UPDATE generated_document_packages SET {set_clause}, updated_at = NOW() WHERE id = %s",
        params,
    )
    return get_document_package(package_id), None


# ── generated_document_files ───────────────────────────────────────────────
# 주의: 이 테이블은 updated_at 컬럼이 없다 (0023 마이그레이션 참조).

DOC_FILE_FIELDS = (
    "generation_job_id",
    "document_kind",
    "form_type",
    "supplemental_type",
    "display_name",
    "file_name",
    "file_path",
    "storage_key",
    "file_size",
    "mime_type",
    "status",
)

DOC_FILE_SELECT = "id, package_id, project_id, " + ", ".join(DOC_FILE_FIELDS) + ", created_at"


def list_document_files(package_id: int) -> list[dict]:
    return fetchall(
        f"SELECT {DOC_FILE_SELECT} FROM generated_document_files WHERE package_id = %s "
        f"ORDER BY id ASC",
        (package_id,),
    )


def get_document_file(file_id: int) -> dict | None:
    return fetchone(f"SELECT {DOC_FILE_SELECT} FROM generated_document_files WHERE id = %s", (file_id,))


def create_document_file(package_id: int, payload: dict) -> tuple[dict | None, str | None]:
    pkg = get_document_package(package_id)
    if pkg is None:
        return None, "package_not_found"
    project_id = pkg["project_id"]
    allowed = {k: v for k, v in payload.items() if k in DOC_FILE_FIELDS}
    job = allowed.get("generation_job_id")
    if job is not None and not _generation_job_belongs_to_project(job, project_id):
        return None, "generation_job_mismatch"
    cols = ["package_id", "project_id"] + list(allowed.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    params = [package_id, project_id] + list(allowed.values())
    new_id = execute(
        f"INSERT INTO generated_document_files ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id",
        params,
    )
    return get_document_file(new_id), None


def update_document_file(file_id: int, fields: dict) -> tuple[dict | None, str | None]:
    current = get_document_file(file_id)
    if current is None:
        return None, "not_found"
    allowed = {k: v for k, v in fields.items() if k in DOC_FILE_FIELDS}
    if not allowed:
        return current, None
    if "generation_job_id" in allowed and allowed["generation_job_id"] is not None:
        if not _generation_job_belongs_to_project(allowed["generation_job_id"], current["project_id"]):
            return None, "generation_job_mismatch"
    set_clause = ", ".join(f"{k} = %s" for k in allowed.keys())
    params = list(allowed.values()) + [file_id]
    # 주의: updated_at 컬럼 없음 — SET 절에 포함하지 않는다.
    execute(
        f"UPDATE generated_document_files SET {set_clause} WHERE id = %s",
        params,
    )
    return get_document_file(file_id), None


# ── rule package metadata (transactional) ──────────────────────────────────
# Excel/ZIP/파일 생성 없음 — 메타 4테이블 INSERT 한 트랜잭션으로 묶는다.

def create_rule_package_metadata(
    *,
    project_id: int,
    rule_id: str,
    package_type: str,
    event_type: str,
    event_date,
    existing_safety_event_id: int | None,
    user_id: int | None,
    documents: list[dict],
    input_snapshot: dict,
    event_payload: dict,
) -> dict:
    """단일 connection·BEGIN/COMMIT 으로 metadata 4건+를 적재한다.

    실패 시 ROLLBACK. 호출자 책임으로 사전 검증(rule_id/project_id 등) 완료 가정.
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # 1) safety_events (없으면 생성)
                if existing_safety_event_id is not None:
                    safety_event_id = existing_safety_event_id
                else:
                    cur.execute(
                        "INSERT INTO safety_events (project_id, event_type, event_date, "
                        "source_type, status, payload_json, created_by_user_id) "
                        "VALUES (%s, %s, %s, %s, 'pending', %s, %s) RETURNING id",
                        (project_id, event_type, event_date, "rule", Json(event_payload), user_id),
                    )
                    safety_event_id = cur.fetchone()["id"]

                # 2) document_generation_jobs
                cur.execute(
                    "INSERT INTO document_generation_jobs (project_id, safety_event_id, "
                    "requested_by_user_id, job_type, status, input_snapshot_json) "
                    "VALUES (%s, %s, %s, 'package', 'pending', %s) RETURNING id",
                    (project_id, safety_event_id, user_id, Json(input_snapshot)),
                )
                job_id = cur.fetchone()["id"]

                # 3) generated_document_packages
                cur.execute(
                    "INSERT INTO generated_document_packages (project_id, safety_event_id, "
                    "generation_job_id, package_type, rule_id, status, document_count, "
                    "created_by_user_id) VALUES (%s, %s, %s, %s, %s, 'created', %s, %s) "
                    "RETURNING id",
                    (project_id, safety_event_id, job_id, package_type, rule_id,
                     len(documents), user_id),
                )
                package_id = cur.fetchone()["id"]

                # 4) generated_document_files
                file_ids: list[int] = []
                for d in documents:
                    form_type = d["key"] if d["kind"] == "form" else None
                    supplemental_type = d["key"] if d["kind"] == "supplemental" else None
                    cur.execute(
                        "INSERT INTO generated_document_files (package_id, project_id, "
                        "generation_job_id, document_kind, form_type, supplemental_type, "
                        "display_name, status) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, 'created') RETURNING id",
                        (package_id, project_id, job_id, d["kind"],
                         form_type, supplemental_type, d.get("label")),
                    )
                    file_ids.append(cur.fetchone()["id"])
        return {
            "safety_event_id": safety_event_id,
            "job_id": job_id,
            "package_id": package_id,
            "file_ids": file_ids,
        }
    finally:
        conn.close()

# NOTE: V1.1 신축공사 전용 repository.
#       장비 관련 함수는 모두 'project_equipment' 테이블만 사용한다.
#       기존 마스터 'equipment'(equipment_code PK, document_equipment_map FK)는 절대 접근 금지.

from db import fetchone, fetchall, execute

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

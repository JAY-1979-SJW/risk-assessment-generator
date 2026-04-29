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

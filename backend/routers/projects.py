from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from db import fetchall, fetchone, execute

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    title: str = "새 위험성평가"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


@router.get("")
def list_projects():
    rows = fetchall(
        "SELECT id, title, status, created_at, updated_at FROM projects ORDER BY updated_at DESC"
    )
    return {"projects": rows}


@router.post("", status_code=201)
def create_project(body: ProjectCreate):
    pid = execute(
        "INSERT INTO projects (title) VALUES (%s) RETURNING id", (body.title,)
    )
    # 기본 기본정보 행 생성
    execute("INSERT INTO project_company_info (project_id) VALUES (%s) ON CONFLICT DO NOTHING", (pid,))
    return {"id": pid, "title": body.title}


@router.get("/{pid}")
def get_project(pid: int):
    row = fetchone("SELECT * FROM projects WHERE id = %s", (pid,))
    if not row:
        raise HTTPException(404, "Project not found")
    return row


@router.put("/{pid}")
def update_project(pid: int, body: ProjectUpdate):
    fields, vals = [], []
    if body.title is not None:
        fields.append("title = %s"); vals.append(body.title)
    if body.status is not None:
        fields.append("status = %s"); vals.append(body.status)
    if not fields:
        raise HTTPException(400, "No fields to update")
    vals.append(pid)
    execute(f"UPDATE projects SET {', '.join(fields)} WHERE id = %s", vals)
    return {"ok": True}


@router.delete("/{pid}", status_code=204)
def delete_project(pid: int):
    execute("DELETE FROM projects WHERE id = %s", (pid,))

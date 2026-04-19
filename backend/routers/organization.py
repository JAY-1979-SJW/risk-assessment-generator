from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from db import fetchall, fetchone, execute

router = APIRouter(prefix="/projects/{pid}/organization", tags=["organization"])

DEFAULT_MEMBERS = [
    ("대표이사(사업주)", "총괄관리",   "사업장의 안전보건에 관한 최고 의사결정권 행사 및 책임"),
    ("안전보건관리책임자", "실무총괄", "위험성평가 계획 수립 및 전반적인 실시 총괄"),
    ("관리감독자",        "현장실시", "소관 작업의 위험성평가 직접 실시 및 위험요인 파악"),
    ("안전관리자/담당자", "기술지원", "위험성평가 기법 지원 및 결과 검토"),
    ("근로자대표",        "참여/협의", "위험성평가 참여 및 결과 확인·서명"),
]


class MemberCreate(BaseModel):
    position: str = ""
    name: str = ""
    role: str = ""
    responsibility: str = ""
    sort_order: int = 0


class MemberUpdate(BaseModel):
    position: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    responsibility: Optional[str] = None
    sort_order: Optional[int] = None


@router.get("")
def get_organization(pid: int):
    rows = fetchall(
        "SELECT * FROM project_org_members WHERE project_id = %s ORDER BY sort_order, id",
        (pid,)
    )
    if not rows:
        # 기본 템플릿 반환 (DB 미저장)
        return {"members": [
            {"id": None, "project_id": pid, "sort_order": i,
             "position": p, "name": "", "role": r, "responsibility": res}
            for i, (p, r, res) in enumerate(DEFAULT_MEMBERS)
        ]}
    return {"members": rows}


@router.post("", status_code=201)
def add_member(pid: int, body: MemberCreate):
    mid = execute(
        """INSERT INTO project_org_members
           (project_id, sort_order, position, name, role, responsibility)
           VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
        (pid, body.sort_order, body.position, body.name, body.role, body.responsibility)
    )
    execute("UPDATE projects SET updated_at = NOW() WHERE id = %s", (pid,))
    return {"id": mid}


@router.put("/bulk")
def bulk_save_members(pid: int, body: list[MemberCreate]):
    """전체 멤버를 한 번에 저장 (기존 삭제 후 재삽입)."""
    execute("DELETE FROM project_org_members WHERE project_id = %s", (pid,))
    for i, m in enumerate(body):
        execute(
            """INSERT INTO project_org_members
               (project_id, sort_order, position, name, role, responsibility)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (pid, i, m.position, m.name, m.role, m.responsibility)
        )
    execute("UPDATE projects SET updated_at = NOW() WHERE id = %s", (pid,))
    return {"ok": True, "count": len(body)}


@router.put("/{mid}")
def update_member(pid: int, mid: int, body: MemberUpdate):
    fields, vals = [], []
    for f in ("position", "name", "role", "responsibility", "sort_order"):
        v = getattr(body, f)
        if v is not None:
            fields.append(f"{f} = %s"); vals.append(v)
    if not fields:
        raise HTTPException(400, "No fields")
    vals += [mid, pid]
    execute(f"UPDATE project_org_members SET {', '.join(fields)} WHERE id=%s AND project_id=%s", vals)
    return {"ok": True}


@router.delete("/{mid}", status_code=204)
def delete_member(pid: int, mid: int):
    execute("DELETE FROM project_org_members WHERE id=%s AND project_id=%s", (mid, pid))

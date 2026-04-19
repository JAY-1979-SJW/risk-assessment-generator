from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from db import fetchone, execute

router = APIRouter(prefix="/projects/{pid}/company-info", tags=["company"])


class CompanyInfo(BaseModel):
    company_name: Optional[str] = ""
    ceo_name: Optional[str] = ""
    business_type: Optional[str] = ""
    address: Optional[str] = ""
    site_name: Optional[str] = ""
    work_type: Optional[str] = ""
    eval_date: Optional[str] = None
    eval_type: Optional[str] = "정기평가"
    safety_policy: Optional[str] = ""
    safety_goal: Optional[str] = ""


@router.get("")
def get_company_info(pid: int):
    row = fetchone("SELECT * FROM project_company_info WHERE project_id = %s", (pid,))
    if not row:
        raise HTTPException(404, "Not found")
    return row


@router.put("")
def upsert_company_info(pid: int, body: CompanyInfo):
    execute("""
        INSERT INTO project_company_info
            (project_id, company_name, ceo_name, business_type, address,
             site_name, work_type, eval_date, eval_type, safety_policy, safety_goal)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (project_id) DO UPDATE SET
            company_name  = EXCLUDED.company_name,
            ceo_name      = EXCLUDED.ceo_name,
            business_type = EXCLUDED.business_type,
            address       = EXCLUDED.address,
            site_name     = EXCLUDED.site_name,
            work_type     = EXCLUDED.work_type,
            eval_date     = EXCLUDED.eval_date,
            eval_type     = EXCLUDED.eval_type,
            safety_policy = EXCLUDED.safety_policy,
            safety_goal   = EXCLUDED.safety_goal
    """, (pid, body.company_name, body.ceo_name, body.business_type,
          body.address, body.site_name, body.work_type,
          body.eval_date or None, body.eval_type,
          body.safety_policy, body.safety_goal))
    execute("UPDATE projects SET updated_at = NOW() WHERE id = %s", (pid,))
    return {"ok": True}

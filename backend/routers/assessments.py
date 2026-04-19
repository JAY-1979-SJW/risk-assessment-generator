import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from db import fetchall, fetchone, execute, risk_level

router = APIRouter(prefix="/projects/{pid}/assessments", tags=["assessments"])

_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _validate_date(v):
    if v and not _DATE_RE.match(v):
        raise ValueError('날짜 형식은 YYYY-MM-DD이어야 합니다')
    return v or None


class AssessmentCreate(BaseModel):
    process:            str = ""
    sub_work:           str = ""
    risk_category:      str = ""
    risk_detail:        str = ""
    risk_situation:     str = ""
    legal_basis:        str = ""
    current_measures:   str = ""
    possibility:        int = Field(default=2, ge=1, le=3)
    severity:           int = Field(default=2, ge=1, le=3)
    reduction_measures: str = ""
    after_possibility:  int = Field(default=1, ge=1, le=3)
    after_severity:     int = Field(default=2, ge=1, le=3)
    due_date:      Optional[str] = None
    complete_date: Optional[str] = None
    manager:  str = ""
    note:     str = ""
    sort_order: int = 0

    @field_validator('due_date', 'complete_date', mode='before')
    @classmethod
    def validate_dates(cls, v):
        return _validate_date(v)


class AssessmentUpdate(BaseModel):
    process:            Optional[str] = None
    sub_work:           Optional[str] = None
    risk_category:      Optional[str] = None
    risk_detail:        Optional[str] = None
    risk_situation:     Optional[str] = None
    legal_basis:        Optional[str] = None
    current_measures:   Optional[str] = None
    possibility:        Optional[int] = Field(default=None, ge=1, le=3)
    severity:           Optional[int] = Field(default=None, ge=1, le=3)
    reduction_measures: Optional[str] = None
    after_possibility:  Optional[int] = Field(default=None, ge=1, le=3)
    after_severity:     Optional[int] = Field(default=None, ge=1, le=3)
    due_date:      Optional[str] = None
    complete_date: Optional[str] = None
    manager: Optional[str] = None
    note:    Optional[str] = None

    @field_validator('due_date', 'complete_date', mode='before')
    @classmethod
    def validate_dates(cls, v):
        return _validate_date(v)


def _with_levels(row: dict) -> dict:
    row["current_risk_level"] = risk_level(row.get("current_risk", 0))
    row["after_risk_level"]   = risk_level(row.get("after_risk", 0))
    return row


@router.get("")
def list_assessments(pid: int):
    rows = fetchall(
        "SELECT * FROM project_assessments WHERE project_id=%s ORDER BY sort_order, id",
        (pid,)
    )
    return {"assessments": [_with_levels(r) for r in rows]}


@router.post("", status_code=201)
def add_assessment(pid: int, body: AssessmentCreate):
    prob = body.possibility
    sev  = body.severity
    ap   = body.after_possibility
    as_  = body.after_severity
    aid = execute(
        """INSERT INTO project_assessments
           (project_id, sort_order, process, sub_work, risk_category, risk_detail,
            risk_situation, legal_basis, current_measures,
            possibility, severity, current_risk_level,
            reduction_measures, after_possibility, after_severity, after_risk_level,
            due_date, complete_date, manager, note)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           RETURNING id""",
        (pid, body.sort_order, body.process, body.sub_work,
         body.risk_category, body.risk_detail, body.risk_situation,
         body.legal_basis, body.current_measures, prob, sev,
         risk_level(prob * sev), body.reduction_measures,
         ap, as_, risk_level(ap * as_),
         body.due_date, body.complete_date,
         body.manager, body.note)
    )
    execute("UPDATE projects SET updated_at = NOW() WHERE id=%s", (pid,))
    return {"id": aid}


@router.post("/bulk", status_code=201)
def bulk_add_assessments(pid: int, body: list[AssessmentCreate]):
    ids = []
    for i, item in enumerate(body):
        item.sort_order = i
        result = add_assessment(pid, item)
        ids.append(result["id"])
    return {"ids": ids, "count": len(ids)}


@router.put("/{aid}")
def update_assessment(pid: int, aid: int, body: AssessmentUpdate):
    fields, vals = [], []
    scalar_fields = [
        "process", "sub_work", "risk_category", "risk_detail", "risk_situation",
        "legal_basis", "current_measures", "reduction_measures",
        "due_date", "complete_date", "manager", "note"
    ]
    for f in scalar_fields:
        v = getattr(body, f)
        if v is not None:
            fields.append(f"{f} = %s"); vals.append(v)

    for f in ("possibility", "severity", "after_possibility", "after_severity"):
        v = getattr(body, f)
        if v is not None:
            fields.append(f"{f} = %s"); vals.append(v)

    if not fields:
        raise HTTPException(400, "No fields to update")

    row = fetchone(
        "SELECT possibility, severity, after_possibility, after_severity "
        "FROM project_assessments WHERE id=%s",
        (aid,)
    )
    if row:
        p   = body.possibility       or row["possibility"]
        s   = body.severity          or row["severity"]
        ap  = body.after_possibility or row["after_possibility"]
        as_ = body.after_severity    or row["after_severity"]
        fields += ["current_risk_level = %s", "after_risk_level = %s"]
        vals   += [risk_level(p * s), risk_level(ap * as_)]

    vals += [aid, pid]
    execute(
        f"UPDATE project_assessments SET {', '.join(fields)} WHERE id=%s AND project_id=%s",
        vals
    )
    execute("UPDATE projects SET updated_at = NOW() WHERE id=%s", (pid,))
    return {"ok": True}


@router.delete("/{aid}", status_code=204)
def delete_assessment(pid: int, aid: int):
    execute("DELETE FROM project_assessments WHERE id=%s AND project_id=%s", (aid, pid))


@router.delete("", status_code=204)
def clear_assessments(pid: int):
    execute("DELETE FROM project_assessments WHERE project_id=%s", (pid,))

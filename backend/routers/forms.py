import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
from db import fetchone, fetchall, execute

router = APIRouter(prefix="/projects/{pid}", tags=["forms"])

FORM_TYPES = ("meeting", "education", "safety_meeting")

_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


class FormData(BaseModel):
    held_date:   Optional[str]        = None
    location:    Optional[str]        = ""
    agenda:      Optional[str]        = ""
    result:      Optional[str]        = ""
    next_action: Optional[str]        = ""
    attendees:   Optional[list[dict]] = None

    @field_validator('held_date', mode='before')
    @classmethod
    def validate_held_date(cls, v):
        if v and not _DATE_RE.match(str(v)):
            raise ValueError('held_date 형식은 YYYY-MM-DD이어야 합니다')
        return v or None


def _get_or_create_form(pid: int, form_type: str) -> dict:
    row = fetchone(
        "SELECT * FROM project_forms WHERE project_id=%s AND form_type=%s",
        (pid, form_type)
    )
    if not row:
        fid = execute(
            "INSERT INTO project_forms (project_id, form_type) VALUES (%s,%s) RETURNING id",
            (pid, form_type)
        )
        row = {"id": fid, "project_id": pid, "form_type": form_type,
               "held_date": None, "location": "", "agenda": "",
               "result": "", "next_action": ""}
    attendees = fetchall(
        "SELECT * FROM project_form_attendees WHERE form_id=%s ORDER BY sort_order, id",
        (row["id"],)
    )
    row["attendees"] = attendees
    return row


def _upsert_form(pid: int, form_type: str, body: FormData):
    fid = execute(
        """INSERT INTO project_forms
               (project_id, form_type, held_date, location, agenda, result, next_action)
           VALUES (%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (project_id, form_type) DO UPDATE SET
               held_date   = EXCLUDED.held_date,
               location    = EXCLUDED.location,
               agenda      = EXCLUDED.agenda,
               result      = EXCLUDED.result,
               next_action = EXCLUDED.next_action
           RETURNING id""",
        (pid, form_type, body.held_date or None,
         body.location, body.agenda, body.result, body.next_action)
    )
    if body.attendees is not None:
        execute("DELETE FROM project_form_attendees WHERE form_id=%s", (fid,))
        for i, a in enumerate(body.attendees):
            execute(
                """INSERT INTO project_form_attendees
                       (form_id, sort_order, department, position, name)
                   VALUES (%s,%s,%s,%s,%s)""",
                (fid, i, a.get("department", ""), a.get("position", ""), a.get("name", ""))
            )
    execute("UPDATE projects SET updated_at=NOW() WHERE id=%s", (pid,))
    return {"ok": True, "form_id": fid}


# ── 회의 결과 ─────────────────────────────────────────────────────────────────
@router.get("/meeting")
def get_meeting(pid: int):
    return _get_or_create_form(pid, "meeting")


@router.put("/meeting")
def upsert_meeting(pid: int, body: FormData):
    return _upsert_form(pid, "meeting", body)


# ── 교육 결과 ─────────────────────────────────────────────────────────────────
@router.get("/education")
def get_education(pid: int):
    return _get_or_create_form(pid, "education")


@router.put("/education")
def upsert_education(pid: int, body: FormData):
    return _upsert_form(pid, "education", body)


# ── 작업 전 안전점검회의 ──────────────────────────────────────────────────────
@router.get("/safety-meeting")
def get_safety_meeting(pid: int):
    return _get_or_create_form(pid, "safety_meeting")


@router.put("/safety-meeting")
def upsert_safety_meeting(pid: int, body: FormData):
    return _upsert_form(pid, "safety_meeting", body)

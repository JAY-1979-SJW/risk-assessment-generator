from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from db import fetchone, fetchall, execute

router = APIRouter(prefix="/projects/{pid}", tags=["forms"])

FORM_TYPES = ("meeting", "education", "safety_meeting")


class FormData(BaseModel):
    form_date: Optional[str] = None
    time_start: Optional[str] = ""
    time_end: Optional[str] = ""
    location: Optional[str] = ""
    content: Optional[str] = ""
    attendees: Optional[list[dict]] = None


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
               "form_date": None, "time_start": "", "time_end": "",
               "location": "", "content": ""}
    attendees = fetchall(
        "SELECT * FROM project_form_attendees WHERE form_id=%s ORDER BY sort_order, id",
        (row["id"],)
    )
    row["attendees"] = attendees
    return row


def _upsert_form(pid: int, form_type: str, body: FormData):
    fid = execute(
        """INSERT INTO project_forms (project_id, form_type, form_date, time_start, time_end, location, content)
           VALUES (%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (project_id, form_type) DO UPDATE SET
               form_date  = EXCLUDED.form_date,
               time_start = EXCLUDED.time_start,
               time_end   = EXCLUDED.time_end,
               location   = EXCLUDED.location,
               content    = EXCLUDED.content
           RETURNING id""",
        (pid, form_type, body.form_date or None, body.time_start,
         body.time_end, body.location, body.content)
    )
    if body.attendees is not None:
        execute("DELETE FROM project_form_attendees WHERE form_id=%s", (fid,))
        for i, a in enumerate(body.attendees):
            execute(
                """INSERT INTO project_form_attendees (form_id, sort_order, department, name, signature)
                   VALUES (%s,%s,%s,%s,%s)""",
                (fid, i, a.get("department",""), a.get("name",""), a.get("signature",""))
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

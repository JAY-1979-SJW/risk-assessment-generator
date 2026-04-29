# V1.1 Stage 2B-5A — Rule metadata 기반 Excel 생성 실행 서비스.
#
# 명시 실행 only (자동 background worker 금지).
# generated_document_files 의 form_type / supplemental_type 을 이용해
# 기존 form_registry / supplementary_registry 의 builder 를 그대로 호출한다.
# ZIP 생성 / 다운로드 endpoint / 자동 트리거 미포함.

from __future__ import annotations

import logging
import os
import re
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# 프로젝트 루트 sys.path (engine.* 접근)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from engine.output.form_registry import (
    UnsupportedFormTypeError,
    build_form_excel,
    get_form_spec,
)
from engine.output.supplementary_registry import (
    build_supplemental_excel,
    get_supplemental_spec,
)

from repositories import new_construction_repository as repo

_logger = logging.getLogger(__name__)
_KST = timezone(timedelta(hours=9))
_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_DEFAULT_BASE_DIR = "/tmp/risk_assessment_generated_documents"
_FILENAME_SAFE_RE = re.compile(r"[^0-9A-Za-z가-힣._-]+")


def _kst_now_iso() -> str:
    return datetime.now(_KST).isoformat()


def _base_dir() -> Path:
    raw = os.getenv("GENERATED_DOCUMENTS_DIR") or _DEFAULT_BASE_DIR
    return Path(raw).resolve()


def _safe_filename_part(name: str) -> str:
    name = (name or "document").strip()
    name = name.replace("\\", "_").replace("/", "_")
    name = _FILENAME_SAFE_RE.sub("_", name)
    name = re.sub(r"_+", "_", name).strip("._-") or "document"
    if len(name) > 80:
        name = name[:80]
    return name


def _resolve_path(project_id: int, package_id: int, file_id: int, display_name: str) -> Path:
    base = _base_dir()
    out_dir = (base / f"project_{int(project_id)}" / f"package_{int(package_id)}").resolve()
    # traversal 방지
    if base not in out_dir.parents and out_dir != base:
        try:
            out_dir.relative_to(base)
        except ValueError:
            raise RuntimeError("invalid output directory")
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{int(file_id)}_{_safe_filename_part(display_name)}.xlsx"
    return out_dir / fname


# ── form_data 구성 ─────────────────────────────────────────────────────────

def _project_common(project: dict | None) -> dict[str, Any]:
    p = project or {}
    return {
        "project_id": p.get("id"),
        "project_name": p.get("title"),
        "title": p.get("title"),
        "site_name": p.get("title"),
        "construction_type": p.get("construction_type"),
        "site_address": p.get("site_address"),
        "site_manager_name": p.get("site_manager_name"),
        "safety_manager_name": p.get("safety_manager_name"),
    }


def _subject_extras(snapshot: dict | None) -> dict[str, Any]:
    """input_snapshot_json 의 subject 정보를 form_data 키로 매핑한다."""
    snap = snapshot or {}
    subj = snap.get("subject") or {}
    extras: dict[str, Any] = {}
    kind = subj.get("kind")
    if kind == "worker":
        extras["worker_name"] = subj.get("worker_name") or ""
        extras["trade"] = subj.get("trade") or ""
        extras["first_work_date"] = subj.get("first_work_date") or ""
    elif kind == "equipment":
        extras["equipment_name"] = subj.get("equipment_name") or ""
        extras["equipment_type"] = subj.get("equipment_type") or ""
        extras["entry_date"] = subj.get("entry_date") or ""
    elif kind == "date":
        extras["target_date"] = subj.get("target_date") or ""
    ctx = snap.get("context") or {}
    if ctx.get("target_date"):
        extras.setdefault("target_date", ctx["target_date"])
    return extras


def _fill_required(spec_required: tuple, repeat_field: str | None, extra_lists: tuple,
                   form_data: dict) -> dict:
    """builder 호출 전 누락 required 필드를 빈값으로 채워 ValidationError 회피."""
    out = dict(form_data)
    list_fields = set(extra_lists or ())
    if repeat_field:
        list_fields.add(repeat_field)
    for f in spec_required:
        if out.get(f) is None:
            out[f] = [] if f in list_fields else ""
    if repeat_field and repeat_field not in out:
        out[repeat_field] = []
    for elf in extra_lists or ():
        out.setdefault(elf, [])
    return out


def _build_core_form_data(form_type: str, common: dict, subj: dict, meta: dict) -> dict:
    spec = get_form_spec(form_type)
    base = dict(common)
    base.update(subj)
    base.update(meta)
    return _fill_required(
        tuple(spec["required_fields"]),
        spec.get("repeat_field"),
        tuple(spec.get("extra_list_fields") or ()),
        base,
    )


def _build_supp_form_data(supp_type: str, common: dict, subj: dict, meta: dict) -> dict:
    spec = get_supplemental_spec(supp_type)
    base = dict(common)
    base.update(subj)
    base.update(meta)
    return _fill_required(
        tuple(spec["required_fields"]),
        spec.get("repeat_field"),
        (),
        base,
    )


# ── 메인 진입점 ─────────────────────────────────────────────────────────────

def run_excel(job_id: int) -> tuple[dict | None, str | None]:
    """returns (response_dict, err).

    err in {None, 'job_not_found', 'package_not_found', 'no_files',
            'invalid_status'}.
    invalid_status 시 response_dict 에 현재 status 포함.
    """
    job = repo.get_document_job(job_id)
    if job is None:
        return None, "job_not_found"

    if job["status"] not in ("pending", "failed"):
        return {"job_id": job_id, "status": job["status"]}, "invalid_status"

    package = repo.get_package_for_job(job_id)
    if package is None:
        return None, "package_not_found"

    files = repo.list_files_for_package(package["id"])
    if not files:
        return None, "no_files"

    project = repo.get_project_profile(job["project_id"])
    snapshot = job.get("input_snapshot_json") or {}
    common = _project_common(project)
    subj_extras = _subject_extras(snapshot)

    repo.update_document_job_status(job_id, "running", started=True)

    results: list[dict] = []
    failed_count = 0
    generated_count = 0

    for f in files:
        fid = f["id"]
        meta = {
            "rule_id": (snapshot.get("rule_id") or package.get("rule_id")),
            "package_id": package["id"],
            "document_display_name": f.get("display_name") or "",
            "generated_at": _kst_now_iso(),
        }
        form_type = f.get("form_type")
        supp_type = f.get("supplemental_type")
        try:
            if form_type:
                form_data = _build_core_form_data(form_type, common, subj_extras, meta)
                xlsx_bytes = build_form_excel(form_type, form_data)
            elif supp_type:
                form_data = _build_supp_form_data(supp_type, common, subj_extras, meta)
                xlsx_bytes = build_supplemental_excel(supp_type, form_data)
            else:
                raise ValueError("file has neither form_type nor supplemental_type")

            if not isinstance(xlsx_bytes, (bytes, bytearray)):
                raise TypeError(f"builder returned non-bytes: {type(xlsx_bytes).__name__}")

            out_path = _resolve_path(
                project_id=job["project_id"],
                package_id=package["id"],
                file_id=fid,
                display_name=f.get("display_name") or form_type or supp_type or f"file_{fid}",
            )
            with open(out_path, "wb") as fp:
                fp.write(xlsx_bytes)
            size = out_path.stat().st_size

            repo.update_document_file_ready(
                file_id=fid,
                file_path=str(out_path),
                file_size=size,
                mime_type=_XLSX_MIME,
                file_name=out_path.name,
            )
            results.append({
                "file_id": fid,
                "status": "ready",
                "file_path": str(out_path),
                "file_size": size,
                "form_type": form_type,
                "supplemental_type": supp_type,
            })
            generated_count += 1
        except (UnsupportedFormTypeError, KeyError, NotImplementedError,
                TypeError, ValueError, OSError, Exception) as exc:  # noqa: BLE001
            err_name = type(exc).__name__
            err_msg = f"{err_name}: {exc}"[:500]
            _logger.error(
                "excel_runner_file_failed job_id=%s file_id=%s form=%s supp=%s err=%s",
                job_id, fid, form_type, supp_type, err_name, exc_info=True,
            )
            try:
                repo.update_document_file_failed(file_id=fid, error_message=err_msg)
            except Exception:  # noqa: BLE001
                _logger.exception("failed to mark file failed file_id=%s", fid)
            results.append({
                "file_id": fid,
                "status": "failed",
                "error_message": err_msg,
                "form_type": form_type,
                "supplemental_type": supp_type,
            })
            failed_count += 1

    if failed_count == 0:
        repo.update_document_job_status(job_id, "completed", finished=True)
        repo.update_document_package_status(package["id"], "ready")
        final_status = "completed"
    else:
        msg = f"{failed_count} of {len(files)} files failed"
        repo.update_document_job_status(
            job_id, "failed", finished=True, error_message=msg,
        )
        repo.update_document_package_status(package["id"], "failed")
        final_status = "failed"

    return {
        "job_id": job_id,
        "package_id": package["id"],
        "status": final_status,
        "generated_count": generated_count,
        "failed_count": failed_count,
        "files": results,
    }, None

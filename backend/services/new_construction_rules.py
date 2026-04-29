# V1.1 자동생성 Rule MVP — 코드 상수 + preview/generate 함수.
#
# 본 모듈은 메타데이터(safety_events / document_generation_jobs /
# generated_document_packages / generated_document_files) 만 적재한다.
# Excel builder / ZIP 생성 / 파일 다운로드 / 자동 트리거는 본 단계 범위 외.

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone, timedelta
from typing import Any

from engine.output.form_registry import _REGISTRY as _FORM_REG
from engine.output.supplementary_registry import _SUPPLEMENTARY_REGISTRY as _SUPP_REG

from repositories import new_construction_repository as repo

RULE_VERSION = "1.1.0"


@dataclass(frozen=True)
class RuleDoc:
    kind: str          # "form" | "supplemental"
    key: str           # registry key
    label: str
    code: str | None = None  # 예: ED-001


@dataclass(frozen=True)
class RuleSpec:
    rule_id: str
    display_name: str
    trigger_event_type: str
    package_type: str
    subject_kind: str  # "worker" | "equipment" | "date"
    documents: tuple[RuleDoc, ...]


RULE_DEFINITIONS: dict[str, RuleSpec] = {
    "RULE_NEW_WORKER": RuleSpec(
        rule_id="RULE_NEW_WORKER",
        display_name="신규 근로자 등록 서류 패키지",
        trigger_event_type="worker_registered",
        package_type="worker_onboarding",
        subject_kind="worker",
        documents=(
            RuleDoc("form", "education_log", "안전보건교육 교육일지", "ED-001"),
            RuleDoc("form", "ppe_issuance_ledger", "보호구 지급 대장", "PPE-001"),
            RuleDoc("supplemental", "attendance_roster", "출근부/배치부"),
            RuleDoc("supplemental", "ppe_receipt_confirmation", "보호구 수령 확인서"),
            RuleDoc("supplemental", "document_attachment_list", "문서 첨부 리스트"),
        ),
    ),
    "RULE_EQUIPMENT_INTAKE": RuleSpec(
        rule_id="RULE_EQUIPMENT_INTAKE",
        display_name="장비 반입 서류 패키지",
        trigger_event_type="equipment_registered",
        package_type="equipment_intake",
        subject_kind="equipment",
        documents=(
            RuleDoc("form", "construction_equipment_entry_request", "건설 장비 반입 신청서", "PPE-002"),
            RuleDoc("form", "equipment_insurance_inspection_check", "건설 장비 보험·정기검사증 확인서", "PPE-003"),
            RuleDoc("form", "construction_equipment_daily_checklist", "건설 장비 일일 사전 점검표", "CL-003"),
            RuleDoc("supplemental", "equipment_operator_qualification_check", "운전원 자격증 확인서"),
            RuleDoc("supplemental", "document_attachment_list", "문서 첨부 리스트"),
            RuleDoc("supplemental", "photo_attachment_sheet", "사진 첨부 시트"),
        ),
    ),
    "RULE_DAILY_TBM": RuleSpec(
        rule_id="RULE_DAILY_TBM",
        display_name="매일 TBM 서류 패키지",
        trigger_event_type="daily_tbm",
        package_type="daily_tbm",
        subject_kind="date",
        documents=(
            RuleDoc("form", "tbm_log", "TBM 일지", "RA-004"),
            RuleDoc("form", "pre_work_safety_check", "작업 전 안전 확인서", "DL-005"),
            RuleDoc("supplemental", "attendance_roster", "출근부"),
            RuleDoc("supplemental", "photo_attachment_sheet", "사진 첨부 시트"),
        ),
    ),
}


def _validate_registry_keys() -> None:
    """모듈 import 시점에 registry 키 존재를 검증한다 (배포 안전망)."""
    missing: list[str] = []
    for spec in RULE_DEFINITIONS.values():
        for d in spec.documents:
            reg = _FORM_REG if d.kind == "form" else _SUPP_REG
            if d.key not in reg:
                missing.append(f"{spec.rule_id}:{d.kind}:{d.key}")
    if missing:
        raise RuntimeError(f"Rule registry keys missing: {missing}")


_validate_registry_keys()


def _kst_now_iso() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat()


def list_rules() -> list[dict]:
    return [_rule_to_dict(spec) for spec in RULE_DEFINITIONS.values()]


def _rule_to_dict(spec: RuleSpec) -> dict:
    return {
        "rule_id": spec.rule_id,
        "display_name": spec.display_name,
        "trigger_event_type": spec.trigger_event_type,
        "package_type": spec.package_type,
        "subject_kind": spec.subject_kind,
        "core_documents": [
            {"kind": d.kind, "key": d.key, "label": d.label, "code": d.code}
            for d in spec.documents if d.kind == "form"
        ],
        "supplementary_documents": [
            {"kind": d.kind, "key": d.key, "label": d.label}
            for d in spec.documents if d.kind == "supplemental"
        ],
        "total_document_count": len(spec.documents),
    }


def get_rule(rule_id: str) -> RuleSpec | None:
    return RULE_DEFINITIONS.get(rule_id)


# ── preview / generate ─────────────────────────────────────────────────────

def _resolve_subject(spec: RuleSpec, project_id: int, payload: dict) -> tuple[dict | None, list[str]]:
    """returns (subject_summary, missing_fields)."""
    missing: list[str] = []
    summary: dict[str, Any] = {"kind": spec.subject_kind}
    if spec.subject_kind == "worker":
        sid = payload.get("subject_id")
        if not sid:
            missing.append("subject_id")
            return summary, missing
        worker = repo.get_worker(int(sid))
        if worker is None or worker["project_id"] != project_id:
            missing.append("subject_id (worker not found in this project)")
            return summary, missing
        summary["id"] = worker["id"]
        summary["worker_name"] = worker.get("worker_name")
        summary["trade"] = worker.get("trade")
        summary["first_work_date"] = (
            worker["first_work_date"].isoformat() if worker.get("first_work_date") else None
        )
        if not worker.get("first_work_date"):
            missing.append("worker.first_work_date")
    elif spec.subject_kind == "equipment":
        sid = payload.get("subject_id")
        if not sid:
            missing.append("subject_id")
            return summary, missing
        eq = repo.get_project_equipment(int(sid))
        if eq is None or eq["project_id"] != project_id:
            missing.append("subject_id (equipment not found in this project)")
            return summary, missing
        summary["id"] = eq["id"]
        summary["equipment_name"] = eq.get("equipment_name")
        summary["equipment_type"] = eq.get("equipment_type")
        summary["entry_date"] = eq["entry_date"].isoformat() if eq.get("entry_date") else None
        if not eq.get("entry_date"):
            missing.append("equipment.entry_date")
        if not eq.get("operator_name"):
            missing.append("equipment.operator_name")
    elif spec.subject_kind == "date":
        td = payload.get("target_date")
        if not td:
            missing.append("target_date")
            return summary, missing
        summary["target_date"] = td.isoformat() if isinstance(td, date) else str(td)
    return summary, missing


def _document_view(spec: RuleSpec, missing: list[str]) -> tuple[list[dict], list[dict], int]:
    core = [
        {"kind": d.kind, "key": d.key, "label": d.label, "code": d.code,
         "ready": not missing}
        for d in spec.documents if d.kind == "form"
    ]
    supp = [
        {"kind": d.kind, "key": d.key, "label": d.label,
         "ready": not missing}
        for d in spec.documents if d.kind == "supplemental"
    ]
    return core, supp, len(spec.documents)


def preview(project_id: int, rule_id: str, payload: dict) -> tuple[dict | None, str | None]:
    spec = get_rule(rule_id)
    if spec is None:
        return None, "rule_not_found"
    if not repo._project_exists(project_id):  # noqa: SLF001
        return None, "project_not_found"
    sev = payload.get("safety_event_id")
    if sev is not None and not repo._safety_event_belongs_to_project(int(sev), project_id):  # noqa: SLF001
        return None, "safety_event_mismatch"
    summary, missing = _resolve_subject(spec, project_id, payload)
    core, supp, total = _document_view(spec, missing)
    return {
        "rule_id": spec.rule_id,
        "project_id": project_id,
        "ready": not missing,
        "missing_fields": missing,
        "subject": summary,
        "core_documents": core,
        "supplementary_documents": supp,
        "total_document_count": total,
    }, None


def _build_input_snapshot(spec: RuleSpec, project_id: int, summary: dict, payload: dict) -> dict:
    project = repo.get_project_profile(project_id) or {}
    return {
        "rule_id": spec.rule_id,
        "rule_version": RULE_VERSION,
        "generated_at": _kst_now_iso(),
        "subject": summary,
        "project": {
            "id": project.get("id"),
            "title": project.get("title"),
            "site_address": project.get("site_address"),
            "construction_type": project.get("construction_type"),
        },
        "context": {
            "target_date": (
                payload["target_date"].isoformat()
                if isinstance(payload.get("target_date"), date) else payload.get("target_date")
            ),
            "notes": payload.get("notes"),
        },
        "included_documents": [
            {"kind": d.kind, "key": d.key, "code": d.code}
            for d in spec.documents
        ],
    }


def generate(project_id: int, rule_id: str, payload: dict, *, force: bool = False) -> tuple[dict | None, str | None]:
    spec = get_rule(rule_id)
    if spec is None:
        return None, "rule_not_found"
    if not repo._project_exists(project_id):  # noqa: SLF001
        return None, "project_not_found"
    sev = payload.get("safety_event_id")
    if sev is not None and not repo._safety_event_belongs_to_project(int(sev), project_id):  # noqa: SLF001
        return None, "safety_event_mismatch"

    summary, missing = _resolve_subject(spec, project_id, payload)
    if missing and not force:
        return {"missing_fields": missing}, "not_ready"

    snapshot = _build_input_snapshot(spec, project_id, summary, payload)
    event_date = payload.get("target_date") or date.today()
    user_id = payload.get("user_id")

    rows = repo.create_rule_package_metadata(
        project_id=project_id,
        rule_id=spec.rule_id,
        package_type=spec.package_type,
        event_type=spec.trigger_event_type,
        event_date=event_date,
        existing_safety_event_id=sev,
        user_id=user_id,
        documents=[
            {"kind": d.kind, "key": d.key, "label": d.label, "code": d.code}
            for d in spec.documents
        ],
        input_snapshot=snapshot,
        event_payload={"rule_id": spec.rule_id, "subject": summary},
    )
    return {
        "rule_id": spec.rule_id,
        "project_id": project_id,
        "safety_event_id": rows["safety_event_id"],
        "job_id": rows["job_id"],
        "package_id": rows["package_id"],
        "file_count": len(rows["file_ids"]),
        "file_ids": rows["file_ids"],
        "status": "pending",
        "subject": summary,
    }, None

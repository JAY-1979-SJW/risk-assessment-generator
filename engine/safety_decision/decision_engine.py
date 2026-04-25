"""
SafetyDecisionEngine — 장비/작업 입력 → 필요 서류·교육·근거 자동 산출 (read-only)
"""
from __future__ import annotations

from .master_loader import MasterLoader

_loader: MasterLoader | None = None


def _get_loader() -> MasterLoader:
    global _loader
    if _loader is None:
        _loader = MasterLoader()
    return _loader


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────

def _clause_summary(clause: dict | None) -> dict:
    if not clause:
        return {}
    return {
        "clause_id": clause.get("id"),
        "law_name": clause.get("law_name"),
        "clause": clause.get("clause"),
        "title": clause.get("title"),
        "source_level": clause.get("source_level"),
        "law_type": clause.get("law_type"),
    }


def _resolve_doc_basis(loader: MasterLoader, doc_id: str) -> tuple[list[dict], bool]:
    links = loader.compliance_links("document", doc_id)
    if not links:
        return [], False
    basis = [
        {
            "link_id": lk["link_id"],
            "clause_id": lk["clause_id"],
            "relation_type": lk["relation_type"],
            **_clause_summary(loader.get_clause(lk["clause_id"])),
        }
        for lk in links
    ]
    return basis, True


def _build_document_entry(loader: MasterLoader, doc_id: str, row: dict) -> dict:
    doc = loader.get_document(doc_id)
    basis, has_basis = _resolve_doc_basis(loader, doc_id)
    return {
        "id": doc_id,
        "name": doc.get("name") if doc else doc_id,
        "category_code": doc.get("category_code") if doc else None,
        "implementation_status": doc.get("implementation_status") if doc else None,
        "form_type": doc.get("form_type") if doc else None,
        "condition_note": row.get("condition_note"),
        "basis": basis,
        "basis_status": "confirmed" if has_basis else "missing",
    }


def _build_training_entry(loader: MasterLoader, training_code: str, row: dict) -> dict:
    t = loader.get_training(training_code)
    return {
        "id": training_code,
        "name": t.get("training_name") if t else training_code,
        "required_hours": row.get("required_hours"),
        "cycle": t.get("cycle") if t else None,
        "target_role": t.get("target_role") if t else None,
        "condition_note": row.get("condition_note"),
        "basis": [],
        "basis_status": "missing",
    }


def _build_inspection_entry(loader: MasterLoader, insp_code: str, row: dict) -> dict:
    insp = loader.get_inspection(insp_code)
    basis_links = loader.compliance_links("inspection", insp_code)
    basis = [
        {
            "link_id": lk["link_id"],
            "clause_id": lk["clause_id"],
            "relation_type": lk["relation_type"],
            **_clause_summary(loader.get_clause(lk["clause_id"])),
        }
        for lk in basis_links
    ]
    return {
        "id": insp_code,
        "name": insp.get("inspection_name") if insp else insp_code,
        "cycle": insp.get("cycle") if insp else None,
        "is_mandatory": insp.get("is_mandatory") if insp else None,
        "condition_note": row.get("condition_note"),
        "legal_basis": row.get("legal_basis"),
        "basis": basis,
        "basis_status": "confirmed" if basis else "missing",
    }


def _collect_warnings(
    required_documents: list[dict],
    required_inspections: list[dict],
) -> list[dict]:
    warnings: list[dict] = []
    for doc in required_documents:
        if doc["basis_status"] == "missing":
            warnings.append({
                "type": "basis_missing",
                "target_type": "document",
                "target_id": doc["id"],
                "message": f"문서 {doc['id']}({doc['name']})에 연결된 compliance_links 없음",
            })
    for insp in required_inspections:
        if insp["basis_status"] == "missing":
            warnings.append({
                "type": "inspection_basis_missing",
                "target_type": "inspection",
                "target_id": insp["id"],
                "message": f"점검 {insp['id']}({insp['name']})에 연결된 compliance_links 없음",
            })
    return warnings


# ── 공개 API ─────────────────────────────────────────────────────────────

def resolve_by_equipment(equipment_type_id: str) -> dict:
    """장비 코드 입력 → 필요 서류·교육·근거 산출.

    Args:
        equipment_type_id: equipment_types.yml의 code 값 (예: EQ_CRANE_TOWER)

    Returns:
        판정 결과 dict (required_documents, required_training, compliance_basis, warnings 포함)

    Raises:
        ValueError: 등록되지 않은 장비 코드
    """
    loader = _get_loader()
    eq = loader.get_equipment(equipment_type_id)

    required_documents = [
        _build_document_entry(loader, r["doc_id"], r)
        for r in loader.eq_doc_requirements(equipment_type_id)
    ]
    required_training = [
        _build_training_entry(loader, r["training_code"], r)
        for r in loader.eq_train_requirements(equipment_type_id)
    ]

    # inspection
    insp_row = loader.eq_insp_requirement(equipment_type_id)
    if insp_row:
        required_inspections = [
            _build_inspection_entry(loader, code, insp_row)
            for code in insp_row.get("required_inspections", [])
        ]
    else:
        required_inspections = []

    eq_links = loader.compliance_links("equipment", equipment_type_id)
    compliance_basis = [
        {
            "link_id": lk["link_id"],
            "clause_id": lk["clause_id"],
            "relation_type": lk["relation_type"],
            "notes": lk.get("notes"),
            **_clause_summary(loader.get_clause(lk["clause_id"])),
        }
        for lk in eq_links
    ]

    return {
        "input": {
            "type": "equipment",
            "id": equipment_type_id,
            "name": eq.get("name_ko", equipment_type_id),
        },
        "required_documents": required_documents,
        "required_training": required_training,
        "required_inspections": required_inspections,
        "compliance_basis": compliance_basis,
        "warnings": _collect_warnings(required_documents, required_inspections),
    }


def resolve_by_work_type(work_type_code: str) -> dict:
    """작업 유형 코드 입력 → 필요 서류·교육·근거 산출.

    Args:
        work_type_code: work_types.yml의 code 값 (예: WT_CONFINED_SPACE)

    Returns:
        판정 결과 dict

    Raises:
        ValueError: 등록되지 않은 작업 유형 코드
    """
    loader = _get_loader()
    wt = loader.get_work_type(work_type_code)

    required_documents = [
        _build_document_entry(loader, r["doc_id"], r)
        for r in loader.wt_doc_requirements(work_type_code)
    ]
    required_training = [
        _build_training_entry(loader, r["training_code"], r)
        for r in loader.wt_train_requirements(work_type_code)
    ]

    wt_links = loader.compliance_links("work", work_type_code)
    compliance_basis = [
        {
            "link_id": lk["link_id"],
            "clause_id": lk["clause_id"],
            "relation_type": lk["relation_type"],
            "notes": lk.get("notes"),
            **_clause_summary(loader.get_clause(lk["clause_id"])),
        }
        for lk in wt_links
    ]

    return {
        "input": {
            "type": "work",
            "id": work_type_code,
            "name": wt.get("name", work_type_code),
        },
        "required_documents": required_documents,
        "required_training": required_training,
        "required_inspections": [],
        "compliance_basis": compliance_basis,
        "warnings": _collect_warnings(required_documents, []),
    }


def resolve_compliance_basis(target_type: str, target_id: str) -> list[dict]:
    """대상(문서/장비/작업/교육)의 compliance 근거 조항 목록 반환.

    Args:
        target_type: 'document' | 'equipment' | 'work' | 'training'
        target_id: 대상 ID

    Returns:
        근거 조항 list (비어 있으면 [] 반환)
    """
    loader = _get_loader()
    links = loader.compliance_links(target_type, target_id)
    return [
        {
            "link_id": lk["link_id"],
            "clause_id": lk["clause_id"],
            "relation_type": lk["relation_type"],
            "notes": lk.get("notes"),
            **_clause_summary(loader.get_clause(lk["clause_id"])),
        }
        for lk in links
    ]


def build_decision_summary(input_type: str, input_id: str) -> dict:
    """통합 판정 진입점.

    Args:
        input_type: 'equipment' | 'work'
        input_id: 장비 코드 또는 작업 유형 코드

    Returns:
        판정 결과 dict

    Raises:
        ValueError: 지원하지 않는 input_type 또는 미등록 ID
    """
    if input_type == "equipment":
        return resolve_by_equipment(input_id)
    elif input_type == "work":
        return resolve_by_work_type(input_id)
    else:
        raise ValueError(
            f"지원하지 않는 input_type: '{input_type}'. 사용 가능: equipment, work"
        )

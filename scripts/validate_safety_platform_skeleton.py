"""
Safety Platform 골격 정합성 검증 스크립트.
검증 결과는 PASS / WARN / FAIL 로 출력.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────
# document_catalog 검증 상수
# ─────────────────────────────────────────────────────────────────────

EXPECTED_CATEGORY_COUNTS: dict[str, int] = {
    "WP": 15, "EQ": 16, "RA": 6, "ED": 5, "PTW": 8,
    "DL": 5, "CL": 10, "PPE": 4, "CM": 7, "EM": 6, "TS": 5, "SP": 4,
}
ALLOWED_LEGAL_STATUS: set[str] = {
    "legal", "practical", "optional", "excluded", "needs_verification",
}
ALLOWED_IMPL_STATUS: set[str] = {"DONE", "TODO", "EXCLUDED", "OUT", "PARTIAL"}
ALLOWED_PRIORITY: set[str] = {"DONE", "P0", "P1", "P2", "P3", "OUT", "EXCLUDED"}

# 구 ID 패턴 — 매핑 파일에 남아 있으면 FAIL
_OLD_ID_RE = re.compile(r"\b(RISK-|DOC-|FORM-|OLD-|WP0|EQ0)")


def _get_registry_form_types() -> set[str]:
    """form_registry에서 지원 form_type 목록 로드. 실패 시 하드코딩 폴백."""
    try:
        sys.path.insert(0, str(ROOT))
        from engine.output.form_registry import list_supported_forms  # noqa: PLC0415
        return {f["form_type"] for f in list_supported_forms()}
    except Exception:
        return {
            "excavation_workplan", "vehicle_construction_workplan",
            "material_handling_workplan", "risk_assessment", "education_log",
            "tower_crane_workplan", "mobile_crane_workplan",
            "confined_space_workplan", "tbm_log",
            "confined_space_permit", "confined_space_checklist",
        }

# ─────────────────────────────────────────────────────────────────────
# 검증 결과 수집
# ─────────────────────────────────────────────────────────────────────

_results: list[tuple[str, str, str]] = []  # (status, category, message)


def ok(category: str, msg: str) -> None:
    _results.append(("PASS", category, msg))


def warn(category: str, msg: str) -> None:
    _results.append(("WARN", category, msg))


def fail(category: str, msg: str) -> None:
    _results.append(("FAIL", category, msg))


# ─────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────

def check_file(path: Path, category: str) -> bool:
    if path.exists():
        ok(category, f"존재: {path.relative_to(ROOT)}")
        return True
    fail(category, f"없음: {path.relative_to(ROOT)}")
    return False


def load_yaml(path: Path) -> dict | list | None:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        fail("YAML 파싱", f"{path.name}: {e}")
        return None


def collect_ids(data: dict | list | None, id_field: str, list_key: str | None = None) -> list[str]:
    """YAML에서 ID 목록 추출."""
    if data is None:
        return []
    items = data.get(list_key, []) if isinstance(data, dict) and list_key else (data if isinstance(data, list) else [])
    return [str(item[id_field]) for item in items if isinstance(item, dict) and id_field in item]


# ─────────────────────────────────────────────────────────────────────
# 1. 필수 폴더 존재 여부
# ─────────────────────────────────────────────────────────────────────

REQUIRED_DIRS = [
    "data/masters/safety",
    "data/masters/safety/documents",
    "data/masters/safety/equipment",
    "data/masters/safety/training",
    "data/masters/safety/inspection",
    "data/masters/safety/compliance",
    "data/masters/safety/mappings",
    "data/risk_db/schema",
    "docs/design",
]


def check_dirs() -> None:
    for d in REQUIRED_DIRS:
        p = ROOT / d
        if p.is_dir():
            ok("폴더", d)
        else:
            fail("폴더", f"없음: {d}")


# ─────────────────────────────────────────────────────────────────────
# 2. 필수 README 존재 여부
# ─────────────────────────────────────────────────────────────────────

README_DIRS = [
    "data/masters/safety",
    "data/masters/safety/documents",
    "data/masters/safety/equipment",
    "data/masters/safety/training",
    "data/masters/safety/inspection",
    "data/masters/safety/compliance",
    "data/masters/safety/mappings",
]


def check_readmes() -> None:
    for d in README_DIRS:
        check_file(ROOT / d / "README.md", "README")


# ─────────────────────────────────────────────────────────────────────
# 3. 필수 마스터 파일 존재 여부
# ─────────────────────────────────────────────────────────────────────

REQUIRED_MASTERS = [
    "data/masters/safety/documents/document_catalog.yml",
    "data/masters/safety/equipment/equipment_types.yml",
    "data/masters/safety/training/training_types.yml",
    "data/masters/safety/inspection/inspection_types.yml",
    "data/masters/safety/work_types.yml",
    "data/masters/safety/mappings/equipment_document_requirements.yml",
    "data/masters/safety/mappings/equipment_training_requirements.yml",
    "data/masters/safety/mappings/work_document_requirements.yml",
    "data/masters/safety/mappings/work_training_requirements.yml",
    "data/masters/safety/compliance/compliance_clauses.yml",
    "data/masters/safety/compliance/compliance_links.yml",
    "data/masters/safety/mappings/equipment_inspection_requirements.yml",
]

REQUIRED_SCHEMA_FILES = [
    "data/risk_db/schema/safety_platform_core_schema.sql",
    "docs/design/safety_platform_domain_architecture.md",
]

REQUIRED_ENGINE_FILES = [
    "engine/safety_decision/__init__.py",
    "engine/safety_decision/master_loader.py",
    "engine/safety_decision/decision_engine.py",
    "scripts/smoke_test_safety_decision_engine.py",
]


def check_master_files() -> None:
    for f in REQUIRED_MASTERS + REQUIRED_SCHEMA_FILES:
        check_file(ROOT / f, "파일")


def check_engine_files() -> None:
    for f in REQUIRED_ENGINE_FILES:
        check_file(ROOT / f, "엔진파일")


# ─────────────────────────────────────────────────────────────────────
# 4. document_catalog.yml 검증 (ID 중복 + 90종 구조 + form_type 정합성)
# ─────────────────────────────────────────────────────────────────────

def _check_document_catalog_extended(data: dict | list | None) -> None:
    """카탈로그 구조·값 검증 (category_code 개수, DONE→form_type, 허용값)."""
    if data is None:
        return
    docs = (data or {}).get("documents", [])
    if not docs:
        return

    # category_code별 개수
    cat_counter = Counter(
        d.get("category_code") for d in docs if isinstance(d, dict)
    )
    all_ok = True
    for code, expected in EXPECTED_CATEGORY_COUNTS.items():
        actual = cat_counter.get(code, 0)
        if actual == expected:
            ok("document_catalog", f"  {code}: {actual}종")
        else:
            fail("document_catalog", f"  {code} 개수 오류: 기대 {expected}, 실제 {actual}")
            all_ok = False
    if all_ok:
        ok("document_catalog", "12대분류 개수 모두 정확")

    # DONE → form_type 필수 / form_type → registry 존재
    registry_types = _get_registry_form_types()
    for d in docs:
        if not isinstance(d, dict):
            continue
        doc_id = d.get("id", "?")
        impl = d.get("implementation_status")
        form_type = d.get("form_type")
        if impl == "DONE" and not form_type:
            fail("document_catalog", f"{doc_id}: DONE이지만 form_type 없음")
        if form_type and form_type not in registry_types:
            fail("document_catalog", f"{doc_id}: form_type '{form_type}' 미등록")

    # 허용값 검사
    bad_legal = [
        d.get("id", "?") for d in docs
        if isinstance(d, dict) and d.get("legal_status") not in ALLOWED_LEGAL_STATUS
    ]
    if bad_legal:
        fail("document_catalog", f"legal_status 오류: {bad_legal}")
    else:
        ok("document_catalog", "legal_status 값 모두 유효")

    bad_impl = [
        d.get("id", "?") for d in docs
        if isinstance(d, dict) and d.get("implementation_status") not in ALLOWED_IMPL_STATUS
    ]
    if bad_impl:
        fail("document_catalog", f"implementation_status 오류: {bad_impl}")
    else:
        ok("document_catalog", "implementation_status 값 모두 유효")

    bad_priority = [
        d.get("id", "?") for d in docs
        if isinstance(d, dict) and d.get("priority") not in ALLOWED_PRIORITY
    ]
    if bad_priority:
        fail("document_catalog", f"priority 오류: {bad_priority}")
    else:
        ok("document_catalog", "priority 값 모두 유효")


def check_document_catalog() -> list[str]:
    path = ROOT / "data/masters/safety/documents/document_catalog.yml"
    if not path.exists():
        warn("document_catalog", "파일 없음 — 건너뜀")
        return []
    data = load_yaml(path)
    ids = collect_ids(data, "id", "documents")
    if not ids:
        warn("document_catalog", "id 목록이 비어 있음")
        return []

    # 중복 검사
    dupes = [x for x in ids if ids.count(x) > 1]
    if dupes:
        fail("document_catalog", f"id 중복: {sorted(set(dupes))}")
    else:
        ok("document_catalog", f"id 중복 없음 (총 {len(ids)}건)")

    # 총 항목 수 — meta.total_defined 기준으로 동적 비교
    total = len(ids)
    expected_total = data.get("_meta", {}).get("total_defined", 90)
    if total == expected_total:
        ok("document_catalog", f"총 항목 수 {total}개 확인 (meta.total_defined={expected_total})")
    else:
        fail("document_catalog", f"총 항목 수 오류: 기대 {expected_total}, 실제 {total}")

    # 구조·값 확장 검증
    _check_document_catalog_extended(data)

    return list(set(ids))


# ─────────────────────────────────────────────────────────────────────
# 5. equipment_types.yml equipment_code 중복 검사
# ─────────────────────────────────────────────────────────────────────

def check_equipment_types() -> list[str]:
    path = ROOT / "data/masters/safety/equipment/equipment_types.yml"
    if not path.exists():
        warn("equipment_types", "파일 없음 — 건너뜀")
        return []
    data = load_yaml(path)
    all_codes: list[str] = []
    types = (data or {}).get("equipment_types", [])
    for t in types:
        for eq in t.get("equipment", []):
            code = eq.get("code")
            if code:
                all_codes.append(str(code))
    if not all_codes:
        warn("equipment_types", "equipment code 목록이 비어 있음")
        return []
    dupes = [x for x in all_codes if all_codes.count(x) > 1]
    if dupes:
        fail("equipment_types", f"equipment_code 중복: {sorted(set(dupes))}")
    else:
        ok("equipment_types", f"equipment_code 중복 없음 (총 {len(all_codes)}건)")
    return list(set(all_codes))


# ─────────────────────────────────────────────────────────────────────
# 6. training_types.yml training_code 중복 검사
# ─────────────────────────────────────────────────────────────────────

def check_training_types() -> list[str]:
    path = ROOT / "data/masters/safety/training/training_types.yml"
    if not path.exists():
        warn("training_types", "파일 없음 — 건너뜀")
        return []
    data = load_yaml(path)
    ids = collect_ids(data, "training_code", "training_types")
    if not ids:
        warn("training_types", "training_code 목록이 비어 있음")
        return []
    dupes = [x for x in ids if ids.count(x) > 1]
    if dupes:
        fail("training_types", f"training_code 중복: {sorted(set(dupes))}")
    else:
        ok("training_types", f"training_code 중복 없음 (총 {len(ids)}건)")
    return list(set(ids))


# ─────────────────────────────────────────────────────────────────────
# 7a. 매핑 파일 구 ID 패턴 감지
# ─────────────────────────────────────────────────────────────────────

def check_old_id_patterns() -> None:
    """RISK- / DOC- / FORM- / OLD- / WP0 / EQ0 패턴 잔존 여부 검사 → FAIL."""
    mapping_dir = ROOT / "data/masters/safety/mappings"
    if not mapping_dir.exists():
        return
    for yml in sorted(mapping_dir.glob("*.yml")):
        try:
            content = yml.read_text(encoding="utf-8")
        except Exception as e:
            warn("구ID패턴", f"{yml.name} 읽기 실패: {e}")
            continue
        hits = _OLD_ID_RE.findall(content)
        if hits:
            fail("구ID패턴", f"{yml.name}: 구 패턴 감지 → {sorted(set(hits))}")
        else:
            ok("구ID패턴", f"{yml.name}: 구 ID 패턴 없음")


# ─────────────────────────────────────────────────────────────────────
# 7b. 매핑 파일 참조 ID 존재 확인
# ─────────────────────────────────────────────────────────────────────

def check_mapping_refs(
    doc_ids: list[str],
    eq_codes: list[str],
    training_codes: list[str],
    work_type_codes: list[str] | None = None,
) -> None:
    mappings = {
        "equipment_document_requirements.yml": ("equipment_code", "doc_id", eq_codes, doc_ids),
        "equipment_training_requirements.yml": ("equipment_code", "training_code", eq_codes, training_codes),
        "work_document_requirements.yml": ("work_type_code", "doc_id", work_type_codes, doc_ids),
        "work_training_requirements.yml": ("work_type_code", "training_code", work_type_codes, training_codes),
    }
    for fname, (fk1, fk2, fk1_valid, fk2_valid) in mappings.items():
        path = ROOT / "data/masters/safety/mappings" / fname
        if not path.exists():
            warn("매핑", f"{fname} 없음 — 건너뜀")
            continue
        data = load_yaml(path)
        items = (data or {}).get("requirements", [])
        if not items:
            warn("매핑", f"{fname}: requirements 목록 비어 있음")
            continue
        # fk1 검사 (None이면 마스터 미확정 → WARN)
        if fk1_valid is not None:
            missing_fk1 = [
                str(item.get(fk1, ""))
                for item in items
                if str(item.get(fk1, "")) not in fk1_valid
            ]
            if missing_fk1:
                fail("매핑", f"{fname}: {fk1} 미등록 참조 → {sorted(set(missing_fk1))}")
            else:
                ok("매핑", f"{fname}: {fk1} 참조 유효")
        else:
            wt_codes = sorted({str(item.get(fk1, "")) for item in items})
            warn("매핑", f"{fname}: {fk1} 마스터 미확정 — {wt_codes}")

        # fk2 검사
        missing_fk2 = []
        for item in items:
            v2 = str(item.get(fk2, ""))
            if fk2_valid and v2 not in fk2_valid:
                missing_fk2.append(v2)
        if missing_fk2:
            fail("매핑", f"{fname}: {fk2} 미등록 참조 → {sorted(set(missing_fk2))}")
        else:
            ok("매핑", f"{fname}: {fk2} 참조 유효 ({len(items)}건)")


# ─────────────────────────────────────────────────────────────────────
# 8. work_types.yml work_type_code 중복 검사
# ─────────────────────────────────────────────────────────────────────

def check_work_types() -> list[str] | None:
    path = ROOT / "data/masters/safety/work_types.yml"
    if not path.exists():
        warn("work_types", "파일 없음 — 건너뜀")
        return None
    data = load_yaml(path)
    ids = collect_ids(data, "code", "work_types")
    if not ids:
        warn("work_types", "code 목록이 비어 있음")
        return None
    dupes = [x for x in ids if ids.count(x) > 1]
    if dupes:
        fail("work_types", f"work_type_code 중복: {sorted(set(dupes))}")
    else:
        ok("work_types", f"work_type_code 중복 없음 (총 {len(ids)}건)")
    return list(set(ids))


# ─────────────────────────────────────────────────────────────────────
# 9. compliance 검증
# ─────────────────────────────────────────────────────────────────────

ALLOWED_SOURCE_LEVELS: set[str] = {"LAW", "ENFORCEMENT", "TECHNICAL", "GUIDELINE"}
ALLOWED_LAW_TYPES: set[str] = {
    "OSHA", "CONSTRUCTION", "ELECTRICAL", "FIRE", "COMMUNICATION", "CHEMICAL", "GENERAL",
}
ALLOWED_RELATION_TYPES: set[str] = {"required", "recommended", "reference"}
ALLOWED_LINK_TARGET_TYPES: set[str] = {"document", "equipment", "work", "training"}


def check_compliance(
    doc_ids: list[str],
    eq_codes: list[str],
    work_type_codes: list[str] | None,
    insp_codes: list[str] | None = None,
) -> None:
    clauses_path = ROOT / "data/masters/safety/compliance/compliance_clauses.yml"
    links_path = ROOT / "data/masters/safety/compliance/compliance_links.yml"

    # 파일 존재
    if not clauses_path.exists():
        fail("compliance", f"없음: {clauses_path.relative_to(ROOT)}")
        return
    if not links_path.exists():
        fail("compliance", f"없음: {links_path.relative_to(ROOT)}")

    # clauses 파싱
    clauses_data = load_yaml(clauses_path)
    clauses = (clauses_data or {}).get("compliance_clauses", [])
    if not clauses:
        fail("compliance", "compliance_clauses 목록 비어 있음")
        return

    # clause_id 중복
    clause_ids = [str(c.get("id", "")) for c in clauses if isinstance(c, dict)]
    dupes = [x for x in clause_ids if clause_ids.count(x) > 1]
    if dupes:
        fail("compliance", f"clause_id 중복: {sorted(set(dupes))}")
    else:
        ok("compliance", f"clause_id 중복 없음 (총 {len(clause_ids)}건)")

    # source_level 값 검증
    bad_sl = [
        str(c.get("id", "?"))
        for c in clauses
        if isinstance(c, dict) and c.get("source_level") not in ALLOWED_SOURCE_LEVELS
    ]
    if bad_sl:
        fail("compliance", f"source_level 오류: {bad_sl}")
    else:
        ok("compliance", "source_level 값 모두 유효")

    # law_type 값 검증
    bad_lt = [
        str(c.get("id", "?"))
        for c in clauses
        if isinstance(c, dict) and c.get("law_type") not in ALLOWED_LAW_TYPES
    ]
    if bad_lt:
        fail("compliance", f"law_type 오류: {bad_lt}")
    else:
        ok("compliance", "law_type 값 모두 유효")

    # links 파싱
    if not links_path.exists():
        return
    links_data = load_yaml(links_path)
    links = (links_data or {}).get("compliance_links", [])
    if not links:
        fail("compliance", "compliance_links 목록 비어 있음")
        return

    clause_id_set = set(clause_ids)

    # relation_type 값 검증
    bad_rt = [
        str(lk.get("link_id", "?"))
        for lk in links
        if isinstance(lk, dict) and lk.get("relation_type") not in ALLOWED_RELATION_TYPES
    ]
    if bad_rt:
        fail("compliance", f"relation_type 오류: {bad_rt}")
    else:
        ok("compliance", "relation_type 값 모두 유효")

    # clause_id 참조 존재
    missing_clause = [
        str(lk.get("link_id", "?"))
        for lk in links
        if isinstance(lk, dict) and str(lk.get("clause_id", "")) not in clause_id_set
    ]
    if missing_clause:
        fail("compliance", f"미존재 clause_id 참조 — link: {missing_clause}")
    else:
        ok("compliance", f"compliance_links clause_id 참조 모두 유효 ({len(links)}건)")

    # target_id 존재 검증 (document / equipment / work / inspection)
    doc_id_set = set(doc_ids)
    eq_code_set = set(eq_codes)
    wt_code_set = set(work_type_codes) if work_type_codes else None
    insp_code_set = set(insp_codes) if insp_codes else None

    missing_targets: list[str] = []
    for lk in links:
        if not isinstance(lk, dict):
            continue
        ttype = lk.get("target_type", "")
        tid = str(lk.get("target_id", ""))
        lid = str(lk.get("link_id", "?"))
        if ttype == "document" and tid not in doc_id_set:
            missing_targets.append(f"{lid}({tid})")
        elif ttype == "equipment" and tid not in eq_code_set:
            missing_targets.append(f"{lid}({tid})")
        elif ttype == "work" and wt_code_set is not None and tid not in wt_code_set:
            missing_targets.append(f"{lid}({tid})")
        elif ttype == "inspection" and insp_code_set is not None and tid not in insp_code_set:
            missing_targets.append(f"{lid}({tid})")

    if missing_targets:
        fail("compliance", f"target_id 미존재: {missing_targets}")
    else:
        ok("compliance", "compliance_links target_id 참조 모두 유효")


# ─────────────────────────────────────────────────────────────────────
# 10. inspection_types.yml inspection_code 중복 검사
# ─────────────────────────────────────────────────────────────────────

def check_inspection_types() -> list[str]:
    path = ROOT / "data/masters/safety/inspection/inspection_types.yml"
    if not path.exists():
        warn("inspection_types", "파일 없음 — 건너뜀")
        return []
    data = load_yaml(path)
    ids = collect_ids(data, "inspection_code", "inspection_types")
    if not ids:
        warn("inspection_types", "inspection_code 목록이 비어 있음")
        return []
    dupes = [x for x in ids if ids.count(x) > 1]
    if dupes:
        fail("inspection_types", f"inspection_code 중복: {sorted(set(dupes))}")
    else:
        ok("inspection_types", f"inspection_code 중복 없음 (총 {len(ids)}건)")
    return list(set(ids))


# ─────────────────────────────────────────────────────────────────────
# 11. equipment_inspection_requirements.yml 검증
# ─────────────────────────────────────────────────────────────────────

def check_equipment_inspection_requirements(
    eq_codes: list[str],
    insp_codes: list[str],
) -> None:
    path = ROOT / "data/masters/safety/mappings/equipment_inspection_requirements.yml"
    if not path.exists():
        fail("eq_insp_mapping", f"없음: {path.relative_to(ROOT)}")
        return

    data = load_yaml(path)
    rows = (data or {}).get("requirements", [])
    if not rows:
        warn("eq_insp_mapping", "requirements 목록 비어 있음")
        return

    eq_code_set = set(eq_codes)
    insp_code_set = set(insp_codes)
    seen_pairs: set[tuple[str, str]] = set()
    missing_eq: list[str] = []
    missing_insp: list[str] = []
    dup_insp: list[str] = []

    for row in rows:
        eq = str(row.get("equipment_code", ""))
        if eq not in eq_code_set:
            missing_eq.append(eq)

        for code in row.get("required_inspections", []):
            code = str(code)
            if code not in insp_code_set:
                missing_insp.append(code)
            pair = (eq, code)
            if pair in seen_pairs:
                dup_insp.append(f"{eq}:{code}")
            seen_pairs.add(pair)

    if missing_eq:
        fail("eq_insp_mapping", f"equipment_code 미등록 참조: {sorted(set(missing_eq))}")
    else:
        ok("eq_insp_mapping", f"equipment_code 참조 유효 ({len(rows)}건)")

    if missing_insp:
        fail("eq_insp_mapping", f"inspection_code 미등록 참조: {sorted(set(missing_insp))}")
    else:
        total_pairs = len(seen_pairs)
        ok("eq_insp_mapping", f"inspection_code 참조 유효 (총 {total_pairs}건)")

    if dup_insp:
        fail("eq_insp_mapping", f"중복 inspection 참조: {sorted(set(dup_insp))}")
    else:
        ok("eq_insp_mapping", "중복 inspection 참조 없음")


# ─────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 60)
    print("Safety Platform 골격 검증")
    print("=" * 60)

    check_dirs()
    check_readmes()
    check_master_files()
    check_engine_files()
    doc_ids = check_document_catalog()
    eq_codes = check_equipment_types()
    training_codes = check_training_types()
    work_type_codes = check_work_types()
    insp_codes = check_inspection_types()
    check_old_id_patterns()
    check_mapping_refs(doc_ids, eq_codes, training_codes, work_type_codes)
    check_compliance(doc_ids, eq_codes, work_type_codes, insp_codes)
    check_equipment_inspection_requirements(eq_codes, insp_codes)

    # ── 결과 출력 ──
    passes = [r for r in _results if r[0] == "PASS"]
    warns  = [r for r in _results if r[0] == "WARN"]
    fails  = [r for r in _results if r[0] == "FAIL"]

    print()
    for status, cat, msg in _results:
        icon = {"PASS": "✓", "WARN": "△", "FAIL": "✗"}[status]
        print(f"  [{status}] {icon} [{cat}] {msg}")

    print()
    print(f"  PASS: {len(passes)}  WARN: {len(warns)}  FAIL: {len(fails)}")
    print()

    if fails:
        print("최종 판정: FAIL")
        return 1
    if warns:
        print("최종 판정: WARN")
        return 0
    print("최종 판정: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

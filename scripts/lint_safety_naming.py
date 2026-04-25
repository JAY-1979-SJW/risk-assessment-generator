"""
안전서류 명명 규칙 가드 스크립트.

목적:
    안전서류 90종 확장 과정에서 발생할 수 있는 명명 규칙 오류를
    자동으로 검출하기 위한 read-only 린트 스크립트.

검증 대상:
    - data/masters/safety/documents/document_catalog.yml
    - data/evidence/safety_law_refs/  (evidence JSON 파일들)
    - engine/output/form_registry.py  (등록된 form_type 목록)

검증 규칙:
    1. document_id 는 {CAT}-{NNN} 형식이어야 한다.
    2. CAT ∈ {WP, EQ, RA, ED, PTW, DL, CL, PPE, CM, HM, EM, TS, SP}.
    3. document_id 접두어와 category_code 가 불일치하면 FAIL.
    4. evidence 파일명은 {DOC_ID}-{TYPE}{N}_{snake_case}.json 형식.
    5. TYPE ∈ {L, K, M, P}.
    6. COMMON evidence pack 접두어 (ELEC-001, FIRE-001, LIFT-001,
       HEIGHT-001, CONFINED-001) 는 예외 허용.
    7. evidence JSON 내부 evidence_id 가 있으면 파일명 접두어와 일치해야 한다.
    8. DONE 문서는 form_type 이 있어야 한다.
    9. DONE 문서의 form_type 은 form_registry.py 에 등록되어 있어야 한다.
   10. legacy 구조 때문에 자동판단이 어려운 항목은 FAIL 이 아니라 WARN.

출력 (top-level keys):
    checked_documents              — 카탈로그 documents 검사 건수
    checked_evidence_files         — evidence/*.json 검사 건수 (재귀)
    checked_registry_form_types    — form_registry.py 등록 form_type 종 수
    checked_recursive_paths        — 재귀 스캔 대상 경로 + 패턴 목록
                                     status: present | not_present (INFO)
    registry_count_note            — registry 카운트 의미 설명 (validate_form_registry 의 38/38 과 다름)
    warning_count                  — WARN 메시지 총 수 (≠ 영향 파일 수)
    legacy_warning_count           — legacy 분류 WARN 수
    standard_warning_count         — 표준 명명 분류 WARN 수
    affected_evidence_files        — WARN 을 1건 이상 발생시킨 evidence 파일 수
                                     (1 파일이 여러 WARN 을 동시 유발할 수 있음)
    future_blocking_errors         — 정규화 배치 시 즉시 FAIL 로 승격될 후보 메시지
    errors                         — FAIL 메시지 리스트
    warnings                       — WARN 메시지 리스트
    final_status                   — PASS / WARN / FAIL

종료 코드:
    0 — PASS (errors=0, warnings=0)
    0 — WARN (errors=0, warnings>0)  # PASS-with-warnings 도 0 으로 처리
    2 — FAIL (errors>0)

실행:
    python scripts/lint_safety_naming.py
    python scripts/lint_safety_naming.py --json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CATALOG_PATH = ROOT / "data" / "masters" / "safety" / "documents" / "document_catalog.yml"
EVIDENCE_DIR = ROOT / "data" / "evidence" / "safety_law_refs"
ENGINE_OUTPUT_DIR = ROOT / "engine" / "output"
ENGINE_OUTPUT_BUILDERS_DIR = ENGINE_OUTPUT_DIR / "builders"

# 재귀 스캔 대상 — lint 결과의 checked_recursive_paths 에 노출.
RECURSIVE_SCAN_TARGETS: list[dict[str, str]] = [
    {
        "purpose": "evidence",
        "path": "data/evidence/safety_law_refs",
        "pattern": "**/*.json",
    },
    {
        "purpose": "engine_output_root",
        "path": "engine/output",
        "pattern": "*.py",
    },
    {
        "purpose": "engine_output_builders_subdir",
        "path": "engine/output/builders",
        "pattern": "**/*.py",
    },
]

REGISTRY_COUNT_NOTE = (
    "checked_registry_form_types 는 form_registry._REGISTRY 에 등록된 "
    "form_type 종 수다. validate_form_registry.py 의 '38/38 PASS' 는 "
    "동 스크립트가 수행한 38개의 개별 assertion 통과 수이며 별개 개념이다. "
    "lint 는 catalog DONE 문서의 form_type 이 registry 에 모두 등록되어 "
    "있는지 (Rule 9) 를 검사한다."
)

VALID_CATEGORIES: frozenset[str] = frozenset({
    "WP", "EQ", "RA", "ED", "PTW", "DL", "CL",
    "PPE", "CM", "HM", "EM", "TS", "SP",
})

VALID_EVIDENCE_TYPES: frozenset[str] = frozenset({"L", "K", "M", "P"})

COMMON_EVIDENCE_PACKS: frozenset[str] = frozenset({
    "ELEC-001",
    "FIRE-001",
    "LIFT-001",
    "HEIGHT-001",
    "CONFINED-001",
})

DOCUMENT_ID_RE = re.compile(r"^([A-Z]{2,4})-(\d{3})$")
EVIDENCE_TYPE_RE = re.compile(r"^([LKMP])(\d+)$")


def _load_catalog() -> dict[str, Any]:
    with CATALOG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _load_registry_form_types() -> set[str]:
    try:
        from engine.output.form_registry import list_supported_forms
    except Exception as exc:  # pragma: no cover - import-time guard only
        raise RuntimeError(f"form_registry import 실패: {exc}") from exc
    return {spec["form_type"] for spec in list_supported_forms()}


def _split_evidence_filename(stem: str) -> tuple[list[str], str]:
    """파일 stem 을 head 토큰리스트와 설명 문자열로 분리.

    예: "WP-005-L1_safety_rule_article_38" -> (["WP","005","L1"], "safety_rule_article_38")
    예: "ELEC-001-L1_safety_rule_..."     -> (["ELEC","001","L1"], "safety_rule_...")
    예: "WP-015_safety_rule_..."          -> (["WP","015"], "safety_rule_...")
    """
    if "_" in stem:
        head, desc = stem.split("_", 1)
    else:
        head, desc = stem, ""
    return head.split("-"), desc


def _classify_evidence_filename(filename: str) -> dict[str, Any]:
    """evidence 파일명을 파싱하여 분류 결과 반환.

    Returns dict with:
        kind: "standard" | "common_pack" | "extended" | "legacy_no_suffix" | "legacy_other"
        doc_id: 도출된 document_id 또는 None
        type_token: "{TYPE}{N}" 토큰 또는 None
        type_letter: TYPE 문자 또는 None
        extra_suffix: TYPE/N 이후 추가 토큰 (예: "BYL4") 또는 None
        head: 원본 head 문자열
    """
    stem = filename[:-5] if filename.endswith(".json") else filename
    tokens, _desc = _split_evidence_filename(stem)
    head = "-".join(tokens)

    result: dict[str, Any] = {
        "kind": "legacy_other",
        "doc_id": None,
        "type_token": None,
        "type_letter": None,
        "extra_suffix": None,
        "head": head,
    }

    if len(tokens) < 2:
        return result

    cat = tokens[0]
    nnn = tokens[1]
    common_id = f"{cat}-{nnn}"

    is_common = common_id in COMMON_EVIDENCE_PACKS
    is_standard_cat = (cat in VALID_CATEGORIES) and bool(re.fullmatch(r"\d{3}", nnn))

    if not (is_common or is_standard_cat):
        return result

    doc_id = common_id
    result["doc_id"] = doc_id

    # TYPE/N 토큰이 있는지 확인
    if len(tokens) == 2:
        # WP-015_... 처럼 TYPE/N 없음
        result["kind"] = "legacy_no_suffix"
        return result

    type_token = tokens[2]
    type_match = EVIDENCE_TYPE_RE.match(type_token)
    if not type_match:
        # 예상치 못한 토큰 패턴 — legacy 로 둔다.
        result["kind"] = "legacy_no_suffix"
        return result

    result["type_token"] = type_token
    result["type_letter"] = type_match.group(1)

    if len(tokens) > 3:
        result["extra_suffix"] = "-".join(tokens[3:])
        result["kind"] = "common_pack" if is_common else "extended"
    else:
        result["kind"] = "common_pack" if is_common else "standard"

    return result


def _load_evidence_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _is_legacy_warning(msg: str) -> bool:
    """WARN 메시지를 legacy / standard 로 분류한다.

    legacy 분류:
      - "legacy 명명 ..."
      - "legacy evidence_id 불일치 ..."
    """
    return "legacy" in msg


def _scan_recursive_paths() -> tuple[list[dict[str, Any]], list[Path]]:
    """RECURSIVE_SCAN_TARGETS 를 순회하며 evidence json 파일 목록을 수집한다.

    Returns:
        (scan_summary, evidence_files)
        scan_summary 는 lint 출력의 checked_recursive_paths 로 노출된다.
        evidence_files 는 검증 루프가 사용한다 (evidence 목적의 결과만).
    """
    summary: list[dict[str, Any]] = []
    evidence_files: list[Path] = []

    for target in RECURSIVE_SCAN_TARGETS:
        rel = target["path"]
        pattern = target["pattern"]
        purpose = target["purpose"]
        abs_path = ROOT / rel
        exists = abs_path.exists()

        # 디렉토리가 없는 경우는 오류가 아니라 INFO/NOT_PRESENT 로 분류한다.
        # 현재 레포 구조에서는 engine/output/builders/ 가 도입 전 상태이며
        # builder 들은 engine/output/ 직하에 평면 배치되어 있다.
        record: dict[str, Any] = {
            "purpose": purpose,
            "path": rel,
            "pattern": pattern,
            "status": "present" if exists else "not_present_info",
            "matched": 0,
        }

        if exists:
            matched = sorted(abs_path.glob(pattern))
            record["matched"] = len(matched)
            if purpose == "evidence":
                evidence_files = [p for p in matched if p.is_file()]

        summary.append(record)

    return summary, evidence_files


def lint() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    catalog = _load_catalog()
    documents: list[dict[str, Any]] = catalog.get("documents") or []
    registry_form_types = _load_registry_form_types()
    checked_documents = 0
    checked_evidence_files = 0
    checked_registry_form_types = len(registry_form_types)

    catalog_doc_ids: set[str] = set()
    future_blocking_errors: list[str] = []

    # ── 1) 카탈로그 documents 검증 ──────────────────────────────────────
    for entry in documents:
        if not isinstance(entry, dict):
            errors.append(f"[catalog] non-dict entry detected: {entry!r}")
            continue
        checked_documents += 1
        doc_id = entry.get("id") or ""
        category_code = entry.get("category_code") or ""
        impl_status = entry.get("implementation_status") or ""
        form_type = entry.get("form_type")

        # Rule 1 + 2: id format
        m = DOCUMENT_ID_RE.match(doc_id)
        if not m:
            errors.append(
                f"[catalog] document_id 형식 위반: {doc_id!r} "
                "(기대: {CAT}-{NNN}, 3자리 숫자)"
            )
            continue
        cat_prefix = m.group(1)
        if cat_prefix not in VALID_CATEGORIES:
            errors.append(
                f"[catalog] 알 수 없는 category 접두어: id={doc_id} "
                f"(허용: {sorted(VALID_CATEGORIES)})"
            )
            continue

        catalog_doc_ids.add(doc_id)

        # Rule 3: category_code mismatch
        if category_code != cat_prefix:
            errors.append(
                f"[catalog] category_code 불일치: id={doc_id} "
                f"prefix={cat_prefix} category_code={category_code!r}"
            )

        # Rule 8 + 9: DONE 문서 form_type 검증
        if impl_status == "DONE":
            if not form_type:
                errors.append(
                    f"[catalog] DONE 문서에 form_type 누락: id={doc_id}"
                )
            elif form_type not in registry_form_types:
                errors.append(
                    f"[catalog] DONE 문서의 form_type 이 registry 미등록: "
                    f"id={doc_id} form_type={form_type!r}"
                )

    # ── 2) evidence 파일명 검증 (재귀 스캔) ────────────────────────────
    recursive_scan_summary, evidence_files = _scan_recursive_paths()
    if not EVIDENCE_DIR.exists():
        warnings.append(
            f"[evidence] 디렉토리가 존재하지 않음: {EVIDENCE_DIR.relative_to(ROOT)}"
        )

    for path in evidence_files:
        checked_evidence_files += 1
        filename = path.name
        info = _classify_evidence_filename(filename)
        kind = info["kind"]
        doc_id = info["doc_id"]
        type_letter = info["type_letter"]

        # Rule 5: TYPE 검증 (type_letter 가 있다면 무조건 검사)
        if type_letter is not None and type_letter not in VALID_EVIDENCE_TYPES:
            errors.append(
                f"[evidence] TYPE 문자 위반: file={filename} "
                f"TYPE={type_letter!r} (허용: L, K, M, P)"
            )

        # Rule 4 + 6 + 10: 파일명 패턴 분류 처리
        if kind == "standard":
            pass  # OK
        elif kind == "common_pack":
            # 예외 허용 (Rule 6) — 단, 알려진 COMMON pack 에 한정
            if doc_id not in COMMON_EVIDENCE_PACKS:
                errors.append(
                    f"[evidence] COMMON pack 접두어 미허용: file={filename} "
                    f"prefix={doc_id!r}"
                )
        elif kind == "extended":
            # 표준 suffix 뒤에 추가 segment (예: WP-005-L1-BYL4) — 허용 PASS,
            # 단 lint 보고서에 가시성 확보를 위해 WARN 으로 노출하지는 않는다.
            pass
        elif kind == "legacy_no_suffix":
            warnings.append(
                f"[evidence] legacy 명명 (TYPE/N 누락): file={filename} "
                f"doc_id={doc_id!r} — 신규 파일은 {{DOC_ID}}-{{TYPE}}{{N}}_... 사용 필요"
            )
        else:  # legacy_other
            warnings.append(
                f"[evidence] legacy 명명 (DOC_ID 미준수): file={filename} "
                "— 신규 evidence 는 카탈로그 document_id 또는 COMMON pack 접두어 사용 필요"
            )

        # Rule 7: 내부 evidence_id 가 있으면 파일명 접두어와 일치
        data = _load_evidence_json(path)
        if data is None:
            warnings.append(
                f"[evidence] JSON 파싱 실패 또는 비-dict: file={filename}"
            )
            continue

        evidence_id_value = data.get("evidence_id")
        if evidence_id_value is None:
            # 누락은 legacy 가능성이 있으므로 WARN 처리.
            if kind in {"standard", "common_pack", "extended"}:
                warnings.append(
                    f"[evidence] evidence_id 필드 없음: file={filename}"
                )
            continue

        if not isinstance(evidence_id_value, str):
            errors.append(
                f"[evidence] evidence_id 가 문자열이 아님: file={filename} "
                f"value={evidence_id_value!r}"
            )
            continue

        # 비교 대상 head: 파일명에서 첫 '_' 앞 부분
        expected_head = info["head"]
        if evidence_id_value != expected_head:
            # 표준/공통팩/확장 패턴에서는 FAIL, legacy 에서는 WARN
            if kind in {"standard", "common_pack", "extended"}:
                errors.append(
                    f"[evidence] evidence_id 불일치: file={filename} "
                    f"evidence_id={evidence_id_value!r} expected_head={expected_head!r}"
                )
            else:
                warnings.append(
                    f"[evidence] legacy evidence_id 불일치: file={filename} "
                    f"evidence_id={evidence_id_value!r} expected_head={expected_head!r}"
                )
                # 내부 evidence_id 가 표준 패턴 (예: WP-015-L1) 인데 파일명만
                # legacy 인 경우 → 정규화 배치 시 즉시 FAIL 영역으로 이동할 후보.
                if re.fullmatch(r"[A-Z]{2,8}-\d{3}-[LKMP]\d+(-[A-Z0-9]+)?", evidence_id_value):
                    future_blocking_errors.append(
                        f"[evidence] 정규화 배치 시 FAIL 후보: "
                        f"file={filename} → 표준명 head={evidence_id_value}"
                    )

    # ── 3) final_status 결정 ───────────────────────────────────────────
    if errors:
        final_status = "FAIL"
    elif warnings:
        final_status = "WARN"
    else:
        final_status = "PASS"

    legacy_warning_count = sum(1 for w in warnings if _is_legacy_warning(w))
    standard_warning_count = len(warnings) - legacy_warning_count

    # affected_evidence_files: WARN 메시지에서 "file=<name>" 패턴을 추출해 distinct 카운트.
    # 한 파일이 여러 WARN 을 동시 유발할 수 있으므로 warning_count 와 분리해 노출한다.
    file_pat = re.compile(r"file=([^\s]+\.json)")
    affected_files: set[str] = set()
    for msg in warnings:
        m = file_pat.search(msg)
        if m:
            affected_files.add(m.group(1))

    return {
        "checked_documents": checked_documents,
        "checked_evidence_files": checked_evidence_files,
        "checked_registry_form_types": checked_registry_form_types,
        "checked_recursive_paths": recursive_scan_summary,
        "registry_count_note": REGISTRY_COUNT_NOTE,
        "warning_count": len(warnings),
        "legacy_warning_count": legacy_warning_count,
        "standard_warning_count": standard_warning_count,
        "affected_evidence_files": len(affected_files),
        "future_blocking_errors": future_blocking_errors,
        "errors": errors,
        "warnings": warnings,
        "final_status": final_status,
    }


def _print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print("=" * 72)
    print("[lint_safety_naming] 안전서류 명명 규칙 가드 결과")
    print("=" * 72)
    print(f"checked_documents             : {report['checked_documents']}")
    print(f"checked_evidence_files        : {report['checked_evidence_files']}")
    print(f"checked_registry_form_types   : {report['checked_registry_form_types']}")
    print(f"errors                        : {len(report['errors'])}")
    print(f"warning_count (메시지 수)     : {report['warning_count']}")
    print(f"  ├─ legacy_warning_count     : {report['legacy_warning_count']}")
    print(f"  └─ standard_warning_count   : {report['standard_warning_count']}")
    print(f"affected_evidence_files (파일 수) : {report['affected_evidence_files']}")
    print(f"future_blocking_errors        : {len(report['future_blocking_errors'])}")
    print(f"final_status                  : {report['final_status']}")
    print()
    print("[checked_recursive_paths]")
    for rec in report["checked_recursive_paths"]:
        if rec["status"] == "present":
            tag = "PRESENT"
        else:
            tag = "INFO/NOT_PRESENT"
        print(
            f"  [{tag}] {rec['purpose']:<35s} "
            f"{rec['path']}/{rec['pattern']}  → matched={rec['matched']}"
        )
    print()
    print("[registry_count_note]")
    print(f"  {report['registry_count_note']}")
    if report["errors"]:
        print("\n[ERRORS]")
        for msg in report["errors"]:
            print(f"  - {msg}")
    if report["warnings"]:
        print("\n[WARNINGS]")
        for msg in report["warnings"]:
            print(f"  - {msg}")
    if report["future_blocking_errors"]:
        print("\n[FUTURE_BLOCKING_ERRORS]")
        for msg in report["future_blocking_errors"]:
            print(f"  - {msg}")


def main() -> int:
    as_json = "--json" in sys.argv[1:]
    report = lint()
    _print_report(report, as_json)
    return 2 if report["final_status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())

"""
안전서류 추천 엔진 검증 스크립트 (validate_document_recommender.py)

v1 검증 시나리오:
  1. 고소작업       → RA-001, RA-004, PTW-003, CL-001, CL-007 포함
  2. 중량물 인양    → WP-005, PTW-007, CL-003, RA-001, RA-004 포함
  3. 화기작업       → PTW-002 필수, CL-005 추천·미구현(missing_builders)
  4. 전기작업       → PTW-004 필수·미구현, WP-011·CL-004 추천·미구현
  5. 밀폐공간       → WP-014, PTW-001, CL-010 포함
  6. 차량계 건설기계 → CL-003, RA-001, RA-004 포함
  7. 차량계 하역운반기계 → CL-003, RA-001, RA-004 포함
  8. 복합 조건      → work_at_height + hot_work 동시 입력
  9. missing_builders 집합 검증
  10. 지원 패키지 목록 확인

v1.1 추가 검증 시나리오:
  11. conditional_required_documents 분류
  12. blocker_missing / advisory_missing 분리
  13. package_status (READY/CONDITIONAL_READY/INCOMPLETE/NOT_SUPPORTED)
  14. v1.1 required/conditional/optional 완성률
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from engine.recommendation.document_recommender import (
    recommend_documents,
    build_work_condition,
    list_supported_work_packages,
    invalidate_cache,
)

# ──────────────────────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────────────────────

def _check(ok: bool, name: str, detail: str = "") -> tuple[str, str, str]:
    verdict = "PASS" if ok else "FAIL"
    return (verdict, name, detail)


def _doc_ids(docs: list[dict]) -> set[str]:
    return {d["doc_id"] for d in docs}


# ──────────────────────────────────────────────────────────────
# 개별 검증 함수
# ──────────────────────────────────────────────────────────────

def test_work_at_height() -> list[tuple]:
    """고소작업 → RA-001, RA-004, PTW-003, CL-001, CL-007 포함"""
    results = []
    condition = build_work_condition("work_at_height")
    result    = recommend_documents(condition)

    req_ids  = _doc_ids(result["required_documents"])
    opt_ids  = _doc_ids(result["optional_documents"])
    all_ids  = req_ids | opt_ids

    results.append(_check(bool(result["required_documents"]), "고소작업: required_documents 비어있지 않음"))
    results.append(_check("RA-001"  in req_ids, "고소작업: RA-001 (위험성평가표) required 포함"))
    results.append(_check("RA-004"  in req_ids, "고소작업: RA-004 (TBM 일지) required 포함"))
    results.append(_check("PTW-003" in req_ids, "고소작업: PTW-003 (고소작업 허가서) required 포함"))
    results.append(_check("CL-001"  in all_ids, "고소작업: CL-001 (비계점검표) 포함"))
    results.append(_check("CL-007"  in all_ids, "고소작업: CL-007 (추락방호설비점검표) 포함"))

    # PTW-003, CL-001, CL-007 모두 구현됨 확인
    for doc in result["required_documents"] + result["optional_documents"]:
        if doc["doc_id"] in ("PTW-003", "CL-001", "CL-007"):
            results.append(_check(
                doc["is_implemented"],
                f"고소작업: {doc['doc_id']} is_implemented == True",
                f"status={doc['implementation_status']}",
            ))

    # source_trace 확인
    results.append(_check(
        any("work_at_height" in s or "COMMON_WORK_AT_HEIGHT" in s
            for s in result["source_trace"]),
        "고소작업: source_trace에 work_at_height 포함",
        repr(result["source_trace"]),
    ))
    return results


def test_heavy_lifting() -> list[tuple]:
    """중량물 인양 → WP-005, PTW-007, CL-003, RA-001, RA-004 포함"""
    results = []
    condition = build_work_condition("heavy_lifting")
    result    = recommend_documents(condition)

    req_ids = _doc_ids(result["required_documents"])
    opt_ids = _doc_ids(result["optional_documents"])
    all_ids = req_ids | opt_ids

    results.append(_check("RA-001"  in req_ids, "중량물: RA-001 required 포함"))
    results.append(_check("RA-004"  in req_ids, "중량물: RA-004 required 포함"))
    results.append(_check("WP-005"  in req_ids, "중량물: WP-005 (중량물 작업계획서) required 포함"))
    results.append(_check("PTW-007" in all_ids, "중량물: PTW-007 (인양 허가서) 포함"))
    results.append(_check("CL-003"  in all_ids, "중량물: CL-003 (장비점검표) 포함"))

    # WP-005, PTW-007, CL-003 구현 확인
    for doc in result["required_documents"] + result["optional_documents"]:
        if doc["doc_id"] in ("WP-005", "PTW-007", "CL-003"):
            results.append(_check(
                doc["is_implemented"],
                f"중량물: {doc['doc_id']} is_implemented == True",
                f"status={doc['implementation_status']}",
            ))
    return results


def test_hot_work() -> list[tuple]:
    """화기작업 → PTW-002 필수, CL-005 구현 완료 (builder v1.0, 2026-04-25)"""
    results = []
    condition = build_work_condition("hot_work")
    result    = recommend_documents(condition)

    req_ids     = _doc_ids(result["required_documents"])
    opt_ids     = _doc_ids(result["optional_documents"])
    missing_ids = _doc_ids(result["missing_builders"])

    results.append(_check("PTW-002" in req_ids, "화기: PTW-002 (화기작업허가서) required 포함"))

    # PTW-002 구현 확인
    for doc in result["required_documents"]:
        if doc["doc_id"] == "PTW-002":
            results.append(_check(doc["is_implemented"], "화기: PTW-002 is_implemented == True"))

    # CL-005 추천에 포함
    results.append(_check("CL-005" in opt_ids, "화기: CL-005 (화재예방점검표) optional 포함",
                          repr(opt_ids) if "CL-005" not in opt_ids else ""))

    # CL-005 구현 완료 → missing_builders에서 제거됨
    results.append(_check(
        "CL-005" not in missing_ids,
        "화기: CL-005 missing_builders에 없음 (DONE)",
        repr(missing_ids) if "CL-005" in missing_ids else "",
    ))

    # CL-005 is_implemented == True 확인
    for doc in result["optional_documents"]:
        if doc["doc_id"] == "CL-005":
            results.append(_check(
                doc["is_implemented"],
                "화기: CL-005 is_implemented == True (구현 완료)",
                f"status={doc['implementation_status']}",
            ))

    return results


def test_electrical_work() -> list[tuple]:
    """전기작업 → PTW-004 필수, WP-011 구현됨, CL-004 추천 + missing_builders"""
    results = []
    condition = build_work_condition("electrical_work")
    result    = recommend_documents(condition)

    req_ids     = _doc_ids(result["required_documents"])
    opt_ids     = _doc_ids(result["optional_documents"])
    missing_ids = _doc_ids(result["missing_builders"])

    results.append(_check("PTW-004" in req_ids, "전기: PTW-004 (전기작업허가서) required 포함"))

    # PTW-004 구현 완료 → missing_builders에서 제거됨
    results.append(_check(
        "PTW-004" not in missing_ids,
        "전기: PTW-004 missing_builders에 없음 (DONE)",
        repr(missing_ids) if "PTW-004" in missing_ids else "",
    ))

    results.append(_check("WP-011" in opt_ids, "전기: WP-011 (전기작업계획서) optional 포함",
                          repr(opt_ids) if "WP-011" not in opt_ids else ""))
    results.append(_check("CL-004" in opt_ids, "전기: CL-004 (전기안전점검표) optional 포함",
                          repr(opt_ids) if "CL-004" not in opt_ids else ""))

    # WP-011 구현 완료 → missing_builders에서 제거
    results.append(_check(
        "WP-011" not in missing_ids,
        "전기: WP-011 missing_builders에 없음 (DONE)",
        repr(missing_ids) if "WP-011" in missing_ids else "",
    ))
    results.append(_check(
        "CL-004" not in missing_ids,
        "전기: CL-004 missing_builders에 없음 (DONE)",
        repr(missing_ids) if "CL-004" in missing_ids else "",
    ))
    return results


def test_confined_space() -> list[tuple]:
    """밀폐공간 → WP-014, PTW-001, CL-010 포함 + 모두 구현됨"""
    results = []
    condition = build_work_condition("confined_space")
    result    = recommend_documents(condition)

    req_ids = _doc_ids(result["required_documents"])
    opt_ids = _doc_ids(result["optional_documents"])
    all_ids = req_ids | opt_ids

    results.append(_check("WP-014"  in req_ids, "밀폐: WP-014 (밀폐공간작업계획서) required 포함"))
    results.append(_check("PTW-001" in req_ids, "밀폐: PTW-001 (밀폐공간허가서) required 포함"))
    results.append(_check("CL-010"  in all_ids, "밀폐: CL-010 (사전안전점검표) 포함"))

    # WP-014, PTW-001, CL-010 구현 확인
    for doc in result["required_documents"] + result["optional_documents"]:
        if doc["doc_id"] in ("WP-014", "PTW-001", "CL-010"):
            results.append(_check(
                doc["is_implemented"],
                f"밀폐: {doc['doc_id']} is_implemented == True",
                f"status={doc['implementation_status']}",
            ))
    return results


def test_vehicle_construction() -> list[tuple]:
    """차량계 건설기계 → CL-003, RA-001, RA-004 포함"""
    results = []
    condition = build_work_condition("vehicle_construction")
    result    = recommend_documents(condition)

    req_ids = _doc_ids(result["required_documents"])
    opt_ids = _doc_ids(result["optional_documents"])
    all_ids = req_ids | opt_ids

    results.append(_check("RA-001" in req_ids, "건설기계: RA-001 required 포함"))
    results.append(_check("RA-004" in req_ids, "건설기계: RA-004 required 포함"))
    results.append(_check("CL-003" in all_ids, "건설기계: CL-003 (장비일일점검표) 포함"))
    return results


def test_material_handling() -> list[tuple]:
    """차량계 하역운반기계 → CL-003, RA-001, RA-004 포함"""
    results = []
    condition = build_work_condition("material_handling")
    result    = recommend_documents(condition)

    req_ids = _doc_ids(result["required_documents"])
    all_ids = req_ids | _doc_ids(result["optional_documents"])

    results.append(_check("RA-001" in req_ids, "하역운반: RA-001 required 포함"))
    results.append(_check("RA-004" in req_ids, "하역운반: RA-004 required 포함"))
    results.append(_check("CL-003" in all_ids, "하역운반: CL-003 포함"))
    return results


def test_combined_work() -> list[tuple]:
    """복합 조건: work_at_height + hot_work → 양쪽 서류 합집합"""
    results = []
    condition = build_work_condition(["work_at_height", "hot_work"])
    result    = recommend_documents(condition)

    req_ids = _doc_ids(result["required_documents"])
    all_ids = req_ids | _doc_ids(result["optional_documents"])

    # 고소작업 서류
    results.append(_check("PTW-003" in req_ids, "복합: PTW-003 required 포함"))
    # 화기작업 서류
    results.append(_check("PTW-002" in req_ids, "복합: PTW-002 required 포함"))
    # 공통
    results.append(_check("RA-001"  in req_ids, "복합: RA-001 required 포함"))
    results.append(_check("RA-004"  in req_ids, "복합: RA-004 required 포함"))
    # source_trace 2개 이상
    results.append(_check(
        len(result["source_trace"]) >= 2,
        f"복합: source_trace 2개 이상 — {len(result['source_trace'])}개",
    ))
    return results


def test_missing_builders_set() -> list[tuple]:
    """missing_builders는 required/optional의 미구현 서류만 포함해야 함"""
    results = []
    # 전기작업 (WP-011 DONE; PTW-004·CL-004 TODO)
    condition = build_work_condition("electrical_work")
    result    = recommend_documents(condition)

    all_ids     = _doc_ids(result["required_documents"]) | _doc_ids(result["optional_documents"])
    missing_ids = _doc_ids(result["missing_builders"])

    # missing은 required/optional에 포함된 서류여야 함
    spurious = missing_ids - all_ids
    results.append(_check(
        len(spurious) == 0,
        "missing_builders는 required/optional 범위 이내",
        repr(spurious) if spurious else "",
    ))

    # 구현된 서류가 missing에 없어야 함
    for doc in result["required_documents"] + result["optional_documents"]:
        if doc["is_implemented"] and doc["doc_id"] in missing_ids:
            results.append(_check(
                False,
                f"구현된 서류 {doc['doc_id']} 가 missing_builders에 잘못 포함됨",
            ))

    results.append(_check(
        len(missing_ids) > 0,
        f"전기작업: missing_builders 1개 이상 — {len(missing_ids)}건",
    ))
    return results


def test_list_supported_packages() -> list[tuple]:
    """list_supported_work_packages() 반환값 검증"""
    results = []
    packages = list_supported_work_packages()
    results.append(_check(isinstance(packages, list), "list_supported_work_packages() → list"))
    results.append(_check(len(packages) == 7, f"지원 패키지 7개 — 실제 {len(packages)}개"))

    expected_keys = {"work_type", "display_name", "trade_id"}
    for pkg in packages:
        results.append(_check(
            set(pkg.keys()) >= expected_keys,
            f"패키지 '{pkg.get('work_type')}' 필수 키 포함",
        ))
    return results


def test_completion_status_structure() -> list[tuple]:
    """completion_status 필드 구조 검증"""
    results = []
    condition = build_work_condition("work_at_height")
    result    = recommend_documents(condition)
    cs = result.get("completion_status", {})

    for key in ("required_total", "required_done", "required_missing",
                "optional_total", "optional_done", "optional_missing",
                "total", "implemented", "missing_builders", "completion_rate_pct"):
        results.append(_check(key in cs, f"completion_status.{key} 존재"))

    # 합산 일관성 확인
    results.append(_check(
        cs.get("required_total", -1) == cs.get("required_done", 0) + cs.get("required_missing", 0),
        "completion_status: required_total == done + missing",
    ))
    results.append(_check(
        0 <= cs.get("completion_rate_pct", -1) <= 100,
        f"completion_rate_pct 범위 0~100 — 실제 {cs.get('completion_rate_pct')}",
    ))
    return results


def test_legal_practical_split() -> list[tuple]:
    """legal / practical 서류 분류 검증"""
    results = []
    condition = build_work_condition("work_at_height")
    result    = recommend_documents(condition)

    legal_ids     = result.get("legal_documents", [])
    practical_ids = result.get("practical_documents", [])

    results.append(_check(isinstance(legal_ids, list), "legal_documents → list"))
    results.append(_check(isinstance(practical_ids, list), "practical_documents → list"))

    # RA-001, PTW-003, CL-007 중 하나라도 legal 또는 practical에 포함
    all_classified = set(legal_ids) | set(practical_ids)
    results.append(_check(
        len(all_classified) > 0,
        f"legal+practical 분류 {len(all_classified)}건 이상",
    ))
    return results


def test_hazard_based_recommendation() -> list[tuple]:
    """위험요인 직접 지정 → related_documents 확인"""
    results = []
    condition = build_work_condition(
        work_types="work_at_height",
        hazards=["FALL_FROM_HEIGHT"],
    )
    result = recommend_documents(condition)

    # PTW-003, CL-007은 hazard related에도 있어야 함
    all_ids = (
        _doc_ids(result["required_documents"])
        | _doc_ids(result["optional_documents"])
        | _doc_ids(result["related_documents"])
    )
    results.append(_check("PTW-003" in all_ids, "위험요인: FALL_FROM_HEIGHT → PTW-003 포함"))
    results.append(_check("CL-007"  in all_ids, "위험요인: FALL_FROM_HEIGHT → CL-007 포함"))
    return results


def test_unknown_work_type_warning() -> list[tuple]:
    """알 수 없는 work_type 입력 시 warnings 반환"""
    results = []
    condition = build_work_condition("unknown_work_xyz")
    result    = recommend_documents(condition)
    has_warn  = any("UNKNOWN_WORK_TYPE" in w for w in result.get("warnings", []))
    results.append(_check(has_warn, "미지원 work_type → warnings에 UNKNOWN_WORK_TYPE 포함"))
    return results


# ──────────────────────────────────────────────────────────────
# v1.1 신규 검증
# ──────────────────────────────────────────────────────────────

def test_v11_classification() -> list[tuple]:
    """v1.1 conditional_required / blocker_missing / advisory_missing 분류 검증"""
    results = []

    # ── 고소작업 ─────────────────────────────────────────────
    r = recommend_documents(build_work_condition("work_at_height"))
    v11_req  = _doc_ids(r["v11_required_documents"])
    v11_cond = _doc_ids(r["conditional_required_documents"])
    blocker  = _doc_ids(r["blocker_missing"])
    advisory = _doc_ids(r["advisory_missing"])

    results.append(_check("PTW-003" in v11_req,   "v1.1 고소작업: PTW-003 required"))
    results.append(_check("CL-007"  in v11_cond,  "v1.1 고소작업: CL-007 conditional_required"))
    results.append(_check("CL-001"  in v11_cond,  "v1.1 고소작업: CL-001 conditional_required"))
    results.append(_check("PPE-001" not in blocker, "v1.1 고소작업: PPE-001 blocker_missing 미포함"))
    results.append(_check("PPE-001" in advisory,  "v1.1 고소작업: PPE-001 advisory_missing 포함"))

    # ── 중량물 ───────────────────────────────────────────────
    r = recommend_documents(build_work_condition("heavy_lifting"))
    v11_req  = _doc_ids(r["v11_required_documents"])
    v11_cond = _doc_ids(r["conditional_required_documents"])

    results.append(_check("WP-005"  in v11_req,  "v1.1 중량물: WP-005 required"))
    results.append(_check("PTW-007" in v11_req,  "v1.1 중량물: PTW-007 required"))
    results.append(_check("CL-003"  in v11_cond, "v1.1 중량물: CL-003 conditional_required"))

    # ── 화기작업 ─────────────────────────────────────────────
    r = recommend_documents(build_work_condition("hot_work"))
    v11_req  = _doc_ids(r["v11_required_documents"])
    v11_cond = _doc_ids(r["conditional_required_documents"])
    blocker  = _doc_ids(r["blocker_missing"])

    results.append(_check("PTW-002" in v11_req,    "v1.1 화기: PTW-002 required"))
    results.append(_check("CL-005"  in v11_cond,   "v1.1 화기: CL-005 conditional_required"))
    results.append(_check(len(blocker) == 0,        "v1.1 화기: blocker_missing 없음 (required 모두 구현)"))

    # ── 전기작업 ─────────────────────────────────────────────
    r = recommend_documents(build_work_condition("electrical_work"))
    v11_req  = _doc_ids(r["v11_required_documents"])
    v11_cond = _doc_ids(r["conditional_required_documents"])
    blocker  = _doc_ids(r["blocker_missing"])

    results.append(_check("WP-011"  in v11_req,      "v1.1 전기: WP-011 required"))
    results.append(_check("PTW-004" in v11_cond,     "v1.1 전기: PTW-004 conditional_required"))
    results.append(_check("CL-004"  in v11_cond,     "v1.1 전기: CL-004 conditional_required"))
    results.append(_check("WP-011"  not in blocker,  "v1.1 전기: WP-011 blocker_missing 없음 (DONE)"))

    # ── 밀폐공간 ─────────────────────────────────────────────
    r = recommend_documents(build_work_condition("confined_space"))
    v11_req  = _doc_ids(r["v11_required_documents"])
    v11_cond = _doc_ids(r["conditional_required_documents"])

    results.append(_check("WP-014"  in v11_req,  "v1.1 밀폐: WP-014 required"))
    results.append(_check("PTW-001" in v11_req,  "v1.1 밀폐: PTW-001 required"))
    results.append(_check("CL-010"  in v11_cond, "v1.1 밀폐: CL-010 conditional_required"))

    return results


def test_v11_package_status() -> list[tuple]:
    """v1.1 package_status 로직 검증"""
    results = []

    # READY: WP-011·PTW-004·CL-004 모두 구현됨 (전기작업 CL-004 builder v1.0 완료 2026-04-25)
    r = recommend_documents(build_work_condition("electrical_work"))
    results.append(_check(
        r["package_status"] == "READY",
        f"v1.1 status: required/conditional 모두 구현 → READY (전기작업) — {r['package_status']}",
    ))
    results.append(_check(r["blocker_count"] == 0,
                          f"v1.1 status: blocker_count == 0 (전기작업, WP-011 DONE) — {r['blocker_count']}"))

    # READY: required/conditional 모두 구현 (화기작업 CL-005 builder v1.0 완료 2026-04-25)
    r = recommend_documents(build_work_condition("hot_work"))
    results.append(_check(
        r["package_status"] == "READY",
        f"v1.1 status: required/conditional 모두 구현 → READY (화기작업) — {r['package_status']}",
    ))
    results.append(_check(len(r["blocker_missing"]) == 0,
                          f"v1.1 화기: blocker_missing 0건 — {len(r['blocker_missing'])}"))

    # READY: required/conditional 모두 구현 (고소작업)
    r = recommend_documents(build_work_condition("work_at_height"))
    results.append(_check(
        r["package_status"] == "READY",
        f"v1.1 status: 모두 구현 → READY (고소작업) — {r['package_status']}",
    ))

    # optional 미구현(advisory)이 있어도 READY 유지
    results.append(_check(
        r["advisory_count"] > 0 and r["package_status"] == "READY",
        f"v1.1 status: advisory_missing 있어도 READY 유지 — "
        f"advisory={r['advisory_count']}, status={r['package_status']}",
    ))

    # NOT_SUPPORTED: 알 수 없는 work_type
    r = recommend_documents(build_work_condition("unknown_work_xyz"))
    results.append(_check(
        r["package_status"] == "NOT_SUPPORTED",
        f"v1.1 status: 미지원 패키지 → NOT_SUPPORTED — {r['package_status']}",
    ))

    return results


def test_v11_completion_rates() -> list[tuple]:
    """v1.1 completion_rate 계산 검증"""
    results = []

    r = recommend_documents(build_work_condition("work_at_height"))

    for key in ("required_completion_rate", "conditional_completion_rate", "total_completion_rate"):
        val = r.get(key, -1)
        results.append(_check(0 <= val <= 100, f"v1.1 {key} 범위 0~100 — {val}"))

    results.append(_check(isinstance(r["blocker_count"], int),
                          f"v1.1 blocker_count int 타입"))
    results.append(_check(isinstance(r["advisory_count"], int),
                          f"v1.1 advisory_count int 타입"))

    # 고소작업: required 모두 구현 → 100%
    results.append(_check(
        r["required_completion_rate"] == 100,
        f"v1.1 고소작업: required_completion_rate == 100 — {r['required_completion_rate']}",
    ))

    # 전기작업: WP-011 구현됨 → required_completion_rate == 100
    r_elec = recommend_documents(build_work_condition("electrical_work"))
    results.append(_check(
        r_elec["required_completion_rate"] == 100,
        f"v1.1 전기: required_completion_rate == 100 (WP-011 DONE) — {r_elec['required_completion_rate']}",
    ))

    return results


# ──────────────────────────────────────────────────────────────
# 메인 실행
# ──────────────────────────────────────────────────────────────

def run_all() -> None:
    invalidate_cache()   # 항상 신선한 마스터로 시작

    all_results: list[tuple[str, str, str]] = []

    suites = [
        ("고소작업",                    test_work_at_height),
        ("중량물 인양",                  test_heavy_lifting),
        ("화기작업",                    test_hot_work),
        ("전기작업",                    test_electrical_work),
        ("밀폐공간 작업",                test_confined_space),
        ("차량계 건설기계",               test_vehicle_construction),
        ("차량계 하역운반기계",            test_material_handling),
        ("복합 조건",                    test_combined_work),
        ("missing_builders 집합",        test_missing_builders_set),
        ("지원 패키지 목록",              test_list_supported_packages),
        ("completion_status 구조",       test_completion_status_structure),
        ("legal/practical 분류",         test_legal_practical_split),
        ("위험요인 기반 추천",             test_hazard_based_recommendation),
        ("미지원 work_type 경고",         test_unknown_work_type_warning),
        # v1.1 신규
        ("v1.1 conditional_required",   test_v11_classification),
        ("v1.1 package_status",         test_v11_package_status),
        ("v1.1 completion_rate",        test_v11_completion_rates),
    ]

    for suite_name, suite_fn in suites:
        try:
            results = suite_fn()
            all_results.extend(results)
        except Exception as exc:
            import traceback as _tb
            tb = _tb.format_exc().strip().splitlines()[-1]
            all_results.append(("FAIL", f"{suite_name} 실행 중 예외", tb))

    # 추천 결과 샘플 출력 (고소작업)
    print("\n" + "=" * 80)
    print("  안전서류 추천 엔진 v1.1 검증 — document_recommender.py")
    print("=" * 80)

    pass_cnt = warn_cnt = fail_cnt = 0
    overall = "PASS"
    for verdict, name, detail in all_results:
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[verdict]
        line = f"  {icon} [{verdict}] {name}"
        if detail:
            line += f" — {detail}"
        print(line)
        if verdict == "PASS":        pass_cnt += 1
        elif verdict == "WARN":      warn_cnt += 1
        else:                        fail_cnt += 1; overall = "FAIL"

    print("-" * 62)
    total = len(all_results)
    print(f"  합계: PASS {pass_cnt}/{total}  WARN {warn_cnt}  FAIL {fail_cnt}")

    # 추천 결과 샘플 출력
    print("\n" + "─" * 62)
    print("  [고소작업 추천 결과 샘플]")
    sample = recommend_documents(build_work_condition("work_at_height"))
    print(f"  required_documents ({len(sample['required_documents'])}건):")
    for d in sample["required_documents"]:
        impl = "✓" if d["is_implemented"] else "✗"
        print(f"    {impl} {d['doc_id']:10} {d['doc_name']}")
    print(f"  optional_documents ({len(sample['optional_documents'])}건):")
    for d in sample["optional_documents"]:
        impl = "✓" if d["is_implemented"] else "✗"
        print(f"    {impl} {d['doc_id']:10} {d['doc_name']}")
    print(f"  missing_builders   ({len(sample['missing_builders'])}건):")
    for d in sample["missing_builders"]:
        print(f"    ✗ {d['doc_id']:10} {d['doc_name']} [{d['implementation_status']}]")
    cs = sample["completion_status"]
    print(f"  completion_rate (v1): {cs['completion_rate_pct']}% ({cs['implemented']}/{cs['total']})")
    print(f"  [v1.1] package_status={sample['package_status']}")
    print(f"  [v1.1] required_completion_rate={sample['required_completion_rate']}%"
          f"  conditional_completion_rate={sample['conditional_completion_rate']}%"
          f"  total={sample['total_completion_rate']}%")
    print(f"  [v1.1] blocker_count={sample['blocker_count']}  advisory_count={sample['advisory_count']}")
    print(f"  [v1.1] conditional_required:")
    for d in sample["conditional_required_documents"]:
        impl = "✓" if d["is_implemented"] else "✗"
        print(f"    {impl} {d['doc_id']:10} {d['doc_name']}")

    print("\n" + "─" * 62)
    print("  [전기작업 추천 결과 샘플]")
    sample_e = recommend_documents(build_work_condition("electrical_work"))
    print(f"  required_documents ({len(sample_e['required_documents'])}건):")
    for d in sample_e["required_documents"]:
        impl = "✓" if d["is_implemented"] else "✗"
        print(f"    {impl} {d['doc_id']:10} {d['doc_name']}")
    print(f"  missing_builders   ({len(sample_e['missing_builders'])}건):")
    for d in sample_e["missing_builders"]:
        print(f"    ✗ {d['doc_id']:10} {d['doc_name']}")
    print(f"  [v1.1] package_status={sample_e['package_status']}")
    print(f"  [v1.1] v11_required: {[d['doc_id'] for d in sample_e['v11_required_documents']]}")
    print(f"  [v1.1] conditional : {[d['doc_id'] for d in sample_e['conditional_required_documents']]}")
    print(f"  [v1.1] blocker     : {[d['doc_id'] for d in sample_e['blocker_missing']]}")

    print("─" * 62)
    print(f"\n  최종 판정: {overall}")
    print("=" * 62 + "\n")

    sys.exit(0 if overall != "FAIL" else 1)


if __name__ == "__main__":
    run_all()

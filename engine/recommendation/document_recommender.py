"""
안전서류 추천 엔진 v1  (document_recommender.py)

작업 조건을 입력하면 필요한 안전서류 패키지를 자동 추천한다.

주요 함수:
  recommend_documents(condition)           - 작업 조건 → 서류 패키지 추천
  build_work_condition(...)                - WorkCondition dict 생성 헬퍼
  list_supported_work_packages()           - 지원 작업 패키지 목록

지원 작업 패키지 (work_type 키):
  work_at_height          → COMMON_WORK_AT_HEIGHT
  heavy_lifting           → COMMON_HEAVY_LIFTING
  vehicle_construction    → COMMON_EQUIPMENT_OPERATION (차량계 건설기계)
  material_handling       → COMMON_EQUIPMENT_OPERATION (차량계 하역운반기계)
  hot_work                → COMMON_HOT_WORK
  electrical_work         → COMMON_ELECTRICAL_WORK
  confined_space          → COMMON_CONFINED_SPACE

출력 키:
  required_documents      필수 서류 (법령 의무 또는 공종 필수)
  optional_documents      권장 서류 (조건부·권장)
  missing_builders        추천됐지만 미구현(TODO) 서류
  legal_documents         legal_status == "legal" 인 서류 ID 목록
  practical_documents     legal_status == "practical" 인 서류 ID 목록
  related_documents       위험요인 연계 추가 서류
  completion_status       구현 통계
  source_trace            추천 근거 출처 목록
  warnings                처리 중 경고 메시지
"""

from __future__ import annotations

import pathlib
from copy import deepcopy
from typing import Any

import yaml

# ──────────────────────────────────────────────────────────────
# 경로 상수
# ──────────────────────────────────────────────────────────────
_THIS_DIR   = pathlib.Path(__file__).parent
_REPO_ROOT  = _THIS_DIR.parent.parent
_SAFETY_DIR = _REPO_ROOT / "data" / "masters" / "safety"

# ──────────────────────────────────────────────────────────────
# 지원 작업 패키지 → trade_id 매핑
# ──────────────────────────────────────────────────────────────
WORK_PACKAGE_MAP: dict[str, str] = {
    "work_at_height":       "COMMON_WORK_AT_HEIGHT",
    "heavy_lifting":        "COMMON_HEAVY_LIFTING",
    "vehicle_construction": "COMMON_EQUIPMENT_OPERATION",
    "material_handling":    "COMMON_EQUIPMENT_OPERATION",
    "hot_work":             "COMMON_HOT_WORK",
    "electrical_work":      "COMMON_ELECTRICAL_WORK",
    "confined_space":       "COMMON_CONFINED_SPACE",
}

WORK_PACKAGE_NAMES: dict[str, str] = {
    "work_at_height":       "고소작업",
    "heavy_lifting":        "중량물 취급·인양",
    "vehicle_construction": "차량계 건설기계 작업",
    "material_handling":    "차량계 하역운반기계 작업",
    "hot_work":             "화기작업",
    "electrical_work":      "전기작업",
    "confined_space":       "밀폐공간 작업",
}

# ──────────────────────────────────────────────────────────────
# v1.1 분류 규칙 (현장 실사용 기준)
# ──────────────────────────────────────────────────────────────
_V11_PACKAGE_RULES: dict[str, dict[str, list[str]]] = {
    "work_at_height": {
        "required":             ["RA-001", "RA-004", "PTW-003"],
        "conditional_required": ["CL-007", "CL-001"],
        "optional":             ["PPE-001"],
    },
    "heavy_lifting": {
        "required":             ["RA-001", "RA-004", "WP-005", "PTW-007"],
        "conditional_required": ["CL-003"],
        "optional":             ["PPE-001"],
    },
    "vehicle_construction": {
        "required":             ["RA-001", "RA-004", "WP-008"],
        "conditional_required": ["CL-003", "EQ-002"],
        "optional":             ["PPE-001"],
    },
    "material_handling": {
        "required":             ["RA-001", "RA-004", "WP-009"],
        "conditional_required": ["CL-003", "EQ-001"],
        "optional":             ["PPE-001"],
    },
    "hot_work": {
        "required":             ["RA-001", "RA-004", "PTW-002"],
        "conditional_required": ["CL-005"],
        "optional":             ["PPE-001"],
    },
    "electrical_work": {
        "required":             ["RA-001", "RA-004", "WP-011"],
        "conditional_required": ["PTW-004", "CL-004"],
        "optional":             ["PPE-001"],
    },
    "confined_space": {
        "required":             ["RA-001", "RA-004", "WP-014", "PTW-001"],
        "conditional_required": ["CL-010"],
        "optional":             ["PPE-001"],
    },
}

# ──────────────────────────────────────────────────────────────
# 내부 유틸
# ──────────────────────────────────────────────────────────────

def _load_yaml(path: pathlib.Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _dedup(items: list) -> list:
    seen: set = set()
    out: list = []
    for x in items:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


# ──────────────────────────────────────────────────────────────
# 마스터 캐시
# ──────────────────────────────────────────────────────────────
_CACHE: dict | None = None


def _get_masters() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = _load_masters()
    return _CACHE


def _load_masters() -> dict:
    """YAML 마스터 파일들을 로드해 내부 조회 구조로 변환."""
    safety = _SAFETY_DIR
    masters: dict[str, Any] = {
        "work_types": {},   # trade_id → trade dict
        "hazards":    {},   # hazard_id → hazard dict
        "doc_map":    {},   # trade_id → document mapping dict
        "catalog":    {},   # doc_id → catalog entry dict
        "errors":     [],
    }

    # 공통 고위험작업 (work_at_height, hot_work, confined_space 등)
    _load_work_types_file(
        safety / "work_types" / "common_high_risk_work_types.yml",
        masters,
    )

    # hazard_master
    hm_path = safety / "hazards" / "hazard_master.yml"
    if hm_path.exists():
        try:
            for h in _load_yaml(hm_path).get("hazards", []):
                hid = h.get("hazard_id")
                if hid:
                    masters["hazards"][hid] = h
        except yaml.YAMLError as exc:
            masters["errors"].append(f"hazard_master.yml parse: {exc}")
    else:
        masters["errors"].append(f"파일 없음: {hm_path}")

    # trade_document_mapping
    dm_path = safety / "mappings" / "trade_document_mapping.yml"
    if dm_path.exists():
        try:
            for m in _load_yaml(dm_path).get("mappings", []):
                tid = m.get("trade_id")
                if tid:
                    masters["doc_map"][tid] = m
        except yaml.YAMLError as exc:
            masters["errors"].append(f"trade_document_mapping.yml parse: {exc}")
    else:
        masters["errors"].append(f"파일 없음: {dm_path}")

    # document_catalog
    cat_path = safety / "documents" / "document_catalog.yml"
    if cat_path.exists():
        try:
            for doc in _load_yaml(cat_path).get("documents", []):
                did = doc.get("id")
                if did:
                    masters["catalog"][did] = doc
        except yaml.YAMLError as exc:
            masters["errors"].append(f"document_catalog.yml parse: {exc}")
    else:
        masters["errors"].append(f"파일 없음: {cat_path}")

    return masters


def _load_work_types_file(path: pathlib.Path, masters: dict) -> None:
    if not path.exists():
        masters["errors"].append(f"파일 없음: {path}")
        return
    try:
        for t in _load_yaml(path).get("trades", []):
            tid = t.get("trade_id")
            if tid and t.get("enabled", True):
                masters["work_types"][tid] = t
    except yaml.YAMLError as exc:
        masters["errors"].append(f"{path.name} parse: {exc}")


# ──────────────────────────────────────────────────────────────
# 공개 API
# ──────────────────────────────────────────────────────────────

def list_supported_work_packages() -> list[dict[str, str]]:
    """지원 작업 패키지 목록을 반환."""
    return [
        {"work_type": wt, "display_name": WORK_PACKAGE_NAMES[wt], "trade_id": WORK_PACKAGE_MAP[wt]}
        for wt in WORK_PACKAGE_MAP
    ]


def build_work_condition(
    work_types: list[str] | str,
    trade_ids: list[str] | None = None,
    equipment: list[str] | None = None,
    hazards: list[str] | None = None,
    work_location: str = "",
    work_date: str = "",
    is_subcontractor: bool = False,
) -> dict:
    """
    WorkCondition dict를 생성한다.

    work_types: 지원 패키지 키 또는 목록
        예) "work_at_height", ["work_at_height", "hot_work"]
    trade_ids: 추가 공종 trade_id 목록 (trade_document_mapping.yml 기준)
    equipment: 사용 장비 목록 (YAML의 common_equipment 키 형식)
    hazards: 위험요인 ID 목록 (hazard_master.yml의 hazard_id)
    """
    if isinstance(work_types, str):
        work_types = [work_types]
    return {
        "work_types":      work_types,
        "trade_ids":       trade_ids or [],
        "equipment":       equipment or [],
        "hazards":         hazards or [],
        "work_location":   work_location,
        "work_date":       work_date,
        "is_subcontractor": is_subcontractor,
    }


def recommend_documents(condition: dict) -> dict:
    """
    WorkCondition dict를 받아 안전서류 추천 패키지를 반환.

    Returns dict with keys:
        required_documents   list[DocInfo]
        optional_documents   list[DocInfo]
        missing_builders     list[DocInfo]  (required+optional 중 TODO)
        legal_documents      list[str]  doc_ids
        practical_documents  list[str]  doc_ids
        related_documents    list[DocInfo]
        completion_status    dict
        source_trace         list[str]
        warnings             list[str]
    """
    masters   = _get_masters()
    warnings  = list(masters["errors"])

    work_types  = condition.get("work_types", [])
    trade_ids   = condition.get("trade_ids", [])
    hazard_ids  = condition.get("hazards", [])

    source_trace: list[str] = []
    required_set:    dict[str, str] = {}   # doc_id → source label
    optional_set:    dict[str, str] = {}
    conditional_set: dict[str, str] = {}
    hazard_doc_set:  dict[str, str] = {}

    # ── 1. work_types → common_high_risk_work_types.yml ─────────────
    for wt in work_types:
        trade_id = WORK_PACKAGE_MAP.get(wt)
        if trade_id is None:
            warnings.append(f"[UNKNOWN_WORK_TYPE] '{wt}' — 지원 패키지 아님. 무시됨.")
            continue

        trade = masters["work_types"].get(trade_id)
        if trade is None:
            warnings.append(f"[TRADE_NOT_FOUND] trade_id '{trade_id}' — work_types 마스터에 없음.")
            continue

        source_label = f"work_type:{wt}"
        source_trace.append(source_label)

        for did in trade.get("required_documents", []):
            required_set.setdefault(did, source_label)
        for did in trade.get("recommended_documents", []):
            optional_set.setdefault(did, source_label)

        # mapping 파일 보강
        mapping = masters["doc_map"].get(trade_id, {})
        for did in mapping.get("required_documents", []):
            required_set.setdefault(did, f"mapping:{trade_id}")
        for did in mapping.get("recommended_documents", []):
            optional_set.setdefault(did, f"mapping:{trade_id}")
        for did in mapping.get("conditional_documents", []):
            conditional_set.setdefault(did, f"mapping:{trade_id}")

    # ── 2. 추가 trade_ids → trade_document_mapping.yml ──────────────
    for tid in trade_ids:
        mapping = masters["doc_map"].get(tid, {})
        if not mapping:
            warnings.append(f"[TRADE_MAPPING_NOT_FOUND] trade_id '{tid}' — trade_document_mapping에 없음.")
            continue
        source_label = f"trade:{tid}"
        source_trace.append(source_label)
        for did in mapping.get("required_documents", []):
            required_set.setdefault(did, source_label)
        for did in mapping.get("recommended_documents", []):
            optional_set.setdefault(did, source_label)
        for did in mapping.get("conditional_documents", []):
            conditional_set.setdefault(did, source_label)

    # ── 3. hazards → hazard_master.yml related_documents ────────────
    for hid in hazard_ids:
        hazard = masters["hazards"].get(hid)
        if hazard is None:
            warnings.append(f"[UNKNOWN_HAZARD] hazard_id '{hid}' — hazard_master에 없음.")
            continue
        source_label = f"hazard:{hid}"
        source_trace.append(source_label)
        for did in hazard.get("related_documents", []):
            hazard_doc_set.setdefault(did, source_label)

    # ── 4. 조건부 서류는 optional에 병합 (중복 없이) ────────────────
    for did, src in conditional_set.items():
        optional_set.setdefault(did, src + "(conditional)")

    # ── 5. 위험요인 서류를 required/optional에 없으면 related로 분류 ─
    all_recommended_ids = set(required_set) | set(optional_set)
    related_set: dict[str, str] = {}
    for did, src in hazard_doc_set.items():
        if did not in all_recommended_ids:
            related_set[did] = src
        else:
            # 이미 required/optional에 있으면 source_trace 보강만
            pass

    # ── 6. 카탈로그에서 서류 상세 정보 조회 ────────────────────────
    catalog = masters["catalog"]

    def _enrich(doc_id: str, source: str) -> dict:
        entry = catalog.get(doc_id, {})
        status = entry.get("implementation_status", "UNKNOWN")
        return {
            "doc_id":     doc_id,
            "doc_name":   entry.get("name", doc_id),
            "form_type":  entry.get("form_type") or None,
            "is_implemented": status == "DONE",
            "implementation_status": status,
            "legal_status": entry.get("legal_status", ""),
            "category_code": entry.get("category_code", ""),
            "source":     source,
        }

    required_docs  = [_enrich(d, s) for d, s in required_set.items()]
    optional_docs  = [_enrich(d, s) for d, s in optional_set.items()]
    related_docs   = [_enrich(d, s) for d, s in related_set.items()]

    # ── 7. missing_builders — required + optional 중 미구현 ─────────
    missing_docs = [
        doc for doc in (required_docs + optional_docs)
        if not doc["is_implemented"]
    ]
    # 중복 제거 (required와 optional 양쪽에 있을 수 있음)
    seen_missing: set[str] = set()
    missing_dedup: list[dict] = []
    for doc in missing_docs:
        if doc["doc_id"] not in seen_missing:
            seen_missing.add(doc["doc_id"])
            missing_dedup.append(doc)

    # ── 8. legal / practical 분류 ────────────────────────────────────
    all_docs = required_docs + optional_docs + related_docs
    legal_ids     = _dedup([d["doc_id"] for d in all_docs if d["legal_status"] == "legal"])
    practical_ids = _dedup([d["doc_id"] for d in all_docs if d["legal_status"] == "practical"])

    # ── 9. 완료 통계 ─────────────────────────────────────────────────
    total_req     = len(required_docs)
    done_req      = sum(1 for d in required_docs if d["is_implemented"])
    total_opt     = len(optional_docs)
    done_opt      = sum(1 for d in optional_docs if d["is_implemented"])
    total_all     = total_req + total_opt
    done_all      = done_req + done_opt
    missing_count = len(missing_dedup)

    completion_status = {
        "required_total":      total_req,
        "required_done":       done_req,
        "required_missing":    total_req - done_req,
        "optional_total":      total_opt,
        "optional_done":       done_opt,
        "optional_missing":    total_opt - done_opt,
        "total":               total_all,
        "implemented":         done_all,
        "missing_builders":    missing_count,
        "completion_rate_pct": round(done_all / total_all * 100) if total_all else 0,
    }

    # ── V1.1 분류 ────────────────────────────────────────────────────
    _v11_req_seen:  set[str] = set()
    _v11_cond_seen: set[str] = set()
    _v11_opt_seen:  set[str] = set()
    v11_req_ids:  list[str] = []
    v11_cond_ids: list[str] = []
    v11_opt_ids:  list[str] = []

    for wt in work_types:
        rules = _V11_PACKAGE_RULES.get(wt, {})
        for did in rules.get("required", []):
            if did not in _v11_req_seen:
                _v11_req_seen.add(did); v11_req_ids.append(did)
        for did in rules.get("conditional_required", []):
            if did not in _v11_cond_seen and did not in _v11_req_seen:
                _v11_cond_seen.add(did); v11_cond_ids.append(did)
        for did in rules.get("optional", []):
            if did not in _v11_opt_seen and did not in _v11_req_seen and did not in _v11_cond_seen:
                _v11_opt_seen.add(did); v11_opt_ids.append(did)

    v11_req_docs  = [_enrich(d, "v11:required")    for d in v11_req_ids]
    v11_cond_docs = [_enrich(d, "v11:conditional") for d in v11_cond_ids]
    v11_opt_docs  = [_enrich(d, "v11:optional")    for d in v11_opt_ids]

    blocker_docs  = [d for d in v11_req_docs  if not d["is_implemented"]]
    cond_missing  = [d for d in v11_cond_docs if not d["is_implemented"]]
    advisory_docs = [d for d in v11_opt_docs  if not d["is_implemented"]]

    has_v11 = any(wt in _V11_PACKAGE_RULES for wt in work_types)
    if not work_types or not has_v11:
        pkg_status: str = "NOT_SUPPORTED"
    elif blocker_docs:
        pkg_status = "INCOMPLETE"
    elif cond_missing:
        pkg_status = "CONDITIONAL_READY"
    else:
        pkg_status = "READY"

    _req_t  = len(v11_req_docs);  _req_d  = sum(1 for d in v11_req_docs  if d["is_implemented"])
    _cond_t = len(v11_cond_docs); _cond_d = sum(1 for d in v11_cond_docs if d["is_implemented"])
    _opt_t  = len(v11_opt_docs);  _opt_d  = sum(1 for d in v11_opt_docs  if d["is_implemented"])
    _all_t  = _req_t + _cond_t + _opt_t
    _all_d  = _req_d + _cond_d + _opt_d

    required_completion_rate    = round(_req_d  / _req_t  * 100) if _req_t  else 0
    conditional_completion_rate = round(_cond_d / _cond_t * 100) if _cond_t else 0
    total_completion_rate       = round(_all_d  / _all_t  * 100) if _all_t  else 0

    return {
        # ── v1 backward compat ──────────────────────────────
        "required_documents":  required_docs,
        "optional_documents":  optional_docs,
        "missing_builders":    missing_dedup,
        "legal_documents":     legal_ids,
        "practical_documents": practical_ids,
        "related_documents":   related_docs,
        "completion_status":   completion_status,
        "source_trace":        _dedup(source_trace),
        "warnings":            warnings,
        # ── v1.1 ────────────────────────────────────────────
        "v11_required_documents":         v11_req_docs,
        "conditional_required_documents": v11_cond_docs,
        "v11_optional_documents":         v11_opt_docs,
        "blocker_missing":                blocker_docs,
        "advisory_missing":               advisory_docs,
        "package_status":                 pkg_status,
        "required_completion_rate":       required_completion_rate,
        "conditional_completion_rate":    conditional_completion_rate,
        "total_completion_rate":          total_completion_rate,
        "blocker_count":                  len(blocker_docs),
        "advisory_count":                 len(advisory_docs),
    }


def invalidate_cache() -> None:
    """마스터 캐시를 초기화한다 (테스트·개발 시 사용)."""
    global _CACHE
    _CACHE = None

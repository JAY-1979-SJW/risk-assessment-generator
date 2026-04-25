"""
공종별 위험성평가 프리셋 추천 엔진 v1

주요 함수:
  load_trade_risk_masters()               - 마스터 데이터 일괄 로드
  get_trade_preset(trade_id)              - 단일 공종 프리셋 조회
  build_trade_risk_recommendation()       - 추천 payload 생성
  merge_common_high_risk_presets()        - 공종 + 공통 고위험작업 merge
  validate_recommendation_payload()       - payload 필드·참조 검증
"""

from __future__ import annotations

import pathlib
from copy import deepcopy
from typing import Any

import yaml

# ──────────────────────────────────────────────────────────────
# 경로 상수
# ──────────────────────────────────────────────────────────────
_THIS_DIR = pathlib.Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent
_SAFETY_DIR = _REPO_ROOT / "data" / "masters" / "safety"
_WORK_TYPES_DIR = _SAFETY_DIR / "work_types"
_HAZARDS_DIR = _SAFETY_DIR / "hazards"
_MAPPINGS_DIR = _SAFETY_DIR / "mappings"
_DOCS_DIR = _SAFETY_DIR / "documents"
_TRAINING_DIR = _SAFETY_DIR / "training"

_DETAIL_FILES = [
    "firefighting_work_types.yml",
    "electrical_work_types.yml",
    "mechanical_work_types.yml",
    "common_high_risk_work_types.yml",
]

_MAPPING_FILES = {
    "document": "trade_document_mapping.yml",
    "training": "trade_training_mapping.yml",
    "equipment": "trade_equipment_mapping.yml",
    "permit": "trade_permit_mapping.yml",
}

_ALLOWED_SOURCE_STATUS = {"VERIFIED", "PARTIAL_VERIFIED", "PRACTICAL", "NEEDS_VERIFICATION"}

# ──────────────────────────────────────────────────────────────
# 내부 유틸
# ──────────────────────────────────────────────────────────────

def _load_yaml(path: pathlib.Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _dedup_list(items: list) -> list:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ──────────────────────────────────────────────────────────────
# 1. 마스터 데이터 로드
# ──────────────────────────────────────────────────────────────

def load_trade_risk_masters(base_dir: pathlib.Path | None = None) -> dict:
    """
    work_types, hazards, mappings, documents, trainings를 로드해 dict로 반환.
    base_dir: data/masters/safety 경로 (None이면 기본 경로 사용)
    """
    safety_dir = pathlib.Path(base_dir) if base_dir else _SAFETY_DIR
    work_dir = safety_dir / "work_types"
    hazards_dir = safety_dir / "hazards"
    mappings_dir = safety_dir / "mappings"

    masters: dict[str, Any] = {
        "trades": {},           # trade_id -> trade dict
        "hazards": {},          # hazard_id -> hazard dict
        "controls": {},         # hazard_id -> list[control dict]
        "mappings": {           # mapping_key -> {trade_id -> mapping dict}
            "document": {},
            "training": {},
            "equipment": {},
            "permit": {},
        },
        "valid_doc_ids": set(),
        "valid_training_codes": set(),
        "_load_errors": [],
    }

    # 공종 상세 파일 로드
    for fname in _DETAIL_FILES:
        fpath = work_dir / fname
        if not fpath.exists():
            masters["_load_errors"].append(f"파일 없음: {fpath}")
            continue
        try:
            data = _load_yaml(fpath)
        except yaml.YAMLError as e:
            masters["_load_errors"].append(f"YAML parse 오류 [{fname}]: {e}")
            continue
        for trade in data.get("trades", []):
            tid = trade.get("trade_id")
            if tid:
                masters["trades"][tid] = trade

    # hazard_master 로드
    hm_path = hazards_dir / "hazard_master.yml"
    if hm_path.exists():
        try:
            hm_data = _load_yaml(hm_path)
            for h in hm_data.get("hazards", []):
                hid = h.get("hazard_id")
                if hid:
                    masters["hazards"][hid] = h
        except yaml.YAMLError as e:
            masters["_load_errors"].append(f"YAML parse 오류 [hazard_master.yml]: {e}")
    else:
        masters["_load_errors"].append(f"파일 없음: {hm_path}")

    # hazard_controls 로드
    hc_path = hazards_dir / "hazard_controls.yml"
    if hc_path.exists():
        try:
            hc_data = _load_yaml(hc_path)
            for item in hc_data.get("controls", []):
                hid = item.get("hazard_id")
                if hid:
                    masters["controls"][hid] = item.get("standard_controls", [])
        except yaml.YAMLError as e:
            masters["_load_errors"].append(f"YAML parse 오류 [hazard_controls.yml]: {e}")
    else:
        masters["_load_errors"].append(f"파일 없음: {hc_path}")

    # mapping 파일 로드
    for key, fname in _MAPPING_FILES.items():
        mpath = mappings_dir / fname
        if not mpath.exists():
            masters["_load_errors"].append(f"파일 없음: {mpath}")
            continue
        try:
            mdata = _load_yaml(mpath)
            for m in mdata.get("mappings", []):
                tid = m.get("trade_id")
                if tid:
                    masters["mappings"][key][tid] = m
        except yaml.YAMLError as e:
            masters["_load_errors"].append(f"YAML parse 오류 [{fname}]: {e}")

    # document catalog 로드
    cat_path = safety_dir / "documents" / "document_catalog.yml"
    if cat_path.exists():
        try:
            cat_data = _load_yaml(cat_path)
            for doc in cat_data.get("documents", []):
                did = doc.get("id")
                if did:
                    masters["valid_doc_ids"].add(did)
        except yaml.YAMLError as e:
            masters["_load_errors"].append(f"YAML parse 오류 [document_catalog.yml]: {e}")

    # training_types 로드
    tt_path = safety_dir / "training" / "training_types.yml"
    if tt_path.exists():
        try:
            tt_data = _load_yaml(tt_path)
            for t in tt_data.get("training_types", []):
                code = t.get("training_code")
                if code:
                    masters["valid_training_codes"].add(code)
        except yaml.YAMLError as e:
            masters["_load_errors"].append(f"YAML parse 오류 [training_types.yml]: {e}")

    return masters


# ──────────────────────────────────────────────────────────────
# 싱글턴 캐시 (같은 프로세스 내 재사용)
# ──────────────────────────────────────────────────────────────
_MASTERS_CACHE: dict | None = None


def _get_masters() -> dict:
    global _MASTERS_CACHE
    if _MASTERS_CACHE is None:
        _MASTERS_CACHE = load_trade_risk_masters()
    return _MASTERS_CACHE


# ──────────────────────────────────────────────────────────────
# 2. 단일 공종 프리셋 조회
# ──────────────────────────────────────────────────────────────

def get_trade_preset(trade_id: str, include_disabled: bool = False) -> dict:
    """
    trade_id로 공종 프리셋 dict를 반환.
    enabled=false 공종은 기본적으로 제외 (include_disabled=True 시 포함).
    없거나 disabled이면 ValueError.
    """
    masters = _get_masters()
    trade = masters["trades"].get(trade_id)
    if trade is None:
        raise ValueError(
            f"trade_id '{trade_id}'를 찾을 수 없습니다. "
            f"상세 파일(소방/전기/기계/공통)에 등록된 trade_id만 조회 가능합니다."
        )
    if not include_disabled and not trade.get("enabled", True):
        raise ValueError(
            f"trade_id '{trade_id}'는 enabled=false 상태입니다. "
            f"include_disabled=True 옵션으로 강제 조회 가능합니다."
        )
    return deepcopy(trade)


# ──────────────────────────────────────────────────────────────
# 3. 추천 payload 생성
# ──────────────────────────────────────────────────────────────

def build_trade_risk_recommendation(
    trade_id: str,
    site_context: dict | None = None,
) -> dict:
    """
    trade_id 기준 표준 추천 payload를 생성해 반환.
    site_context는 metadata에 포함되지만 위험도 계산에는 미사용.
    """
    masters = _get_masters()
    trade = get_trade_preset(trade_id)

    payload = _build_payload_from_trade(trade, masters, source_trade_ids=[trade_id])
    payload["site_context"] = _normalize_site_context(site_context)
    payload["source_trace"] = [trade_id]

    # 경고 수집
    warnings = validate_recommendation_payload(payload, masters)
    payload["warnings"] = warnings

    return payload


# ──────────────────────────────────────────────────────────────
# 4. 공통 고위험작업 merge
# ──────────────────────────────────────────────────────────────

def merge_common_high_risk_presets(
    trade_preset: dict,
    selected_common_work_ids: list[str],
) -> dict:
    """
    단일 공종 프리셋 dict에 공통 고위험작업 프리셋들을 merge.
    중복 hazard/document/permit/training은 제거하고 source_trace에 출처 기록.
    """
    masters = _get_masters()

    base_trade_id = trade_preset.get("trade_id", "UNKNOWN")
    merged_source_ids = [base_trade_id] + list(selected_common_work_ids)

    # 기본 공종 payload 구성
    merged = _build_payload_from_trade(trade_preset, masters, source_trade_ids=[base_trade_id])

    # 공통 고위험작업 순차 merge
    for common_id in selected_common_work_ids:
        try:
            common_trade = get_trade_preset(common_id)
        except ValueError as e:
            merged["warnings"].append(f"공통 고위험작업 조회 실패: {e}")
            continue

        common_payload = _build_payload_from_trade(
            common_trade, masters, source_trade_ids=[common_id]
        )

        # risk_items merge (hazard_id 기준 중복 제거)
        existing_hazard_ids = {ri["hazard_id"] for ri in merged["risk_items"]}
        for ri in common_payload["risk_items"]:
            if ri["hazard_id"] not in existing_hazard_ids:
                ri_copy = deepcopy(ri)
                ri_copy["source_trade_ids"] = [common_id]
                merged["risk_items"].append(ri_copy)
                existing_hazard_ids.add(ri["hazard_id"])

        # 리스트 필드 merge (중복 제거 유지)
        for field in ("required_documents", "recommended_documents",
                      "required_trainings", "required_permits",
                      "common_equipment", "ppe"):
            merged[field] = _dedup_list(merged[field] + common_payload[field])

    # source_trace 갱신
    merged["source_trace"] = merged_source_ids

    # source_status_summary 재집계
    merged["source_status_summary"] = _summarize_source_status(merged["risk_items"])

    # 경고 재수집
    merged["warnings"] = validate_recommendation_payload(merged, masters)

    return merged


# ──────────────────────────────────────────────────────────────
# 5. payload 검증
# ──────────────────────────────────────────────────────────────

def validate_recommendation_payload(
    payload: dict,
    masters: dict | None = None,
) -> list[str]:
    """
    payload 필드 누락 및 참조 무결성 검사.
    warning 메시지 리스트를 반환 (FAIL이 아닌 WARN 수준만 포함).
    """
    if masters is None:
        masters = _get_masters()

    warnings: list[str] = []
    valid_doc_ids = masters["valid_doc_ids"]
    valid_training_codes = masters["valid_training_codes"]
    valid_hazard_ids = set(masters["hazards"].keys())
    controls_map = masters["controls"]

    # 필수 필드 존재 확인
    required_fields = [
        "trade_id", "trade_name", "trade_group", "risk_items",
        "required_documents", "recommended_documents",
        "required_trainings", "required_permits",
        "common_equipment", "ppe", "source_trace", "source_status_summary",
    ]
    for field in required_fields:
        if field not in payload:
            warnings.append(f"[MISSING_FIELD] payload에 '{field}' 필드 없음")

    # document_id 참조 검증
    if valid_doc_ids:
        for did in payload.get("required_documents", []):
            if did not in valid_doc_ids:
                warnings.append(f"[UNKNOWN_DOC] required_documents: '{did}' catalog에 없음")
        for did in payload.get("recommended_documents", []):
            if did not in valid_doc_ids:
                warnings.append(f"[UNKNOWN_DOC] recommended_documents: '{did}' catalog에 없음")
        for did in payload.get("required_permits", []):
            if did not in valid_doc_ids:
                warnings.append(f"[UNKNOWN_PERMIT] required_permits: '{did}' catalog에 없음")

    # training_code 참조 검증
    if valid_training_codes:
        for tcode in payload.get("required_trainings", []):
            if tcode not in valid_training_codes:
                warnings.append(f"[UNKNOWN_TRAINING] required_trainings: '{tcode}' training_types에 없음")

    # risk_items 검증
    for ri in payload.get("risk_items", []):
        hid = ri.get("hazard_id", "")
        if valid_hazard_ids and hid not in valid_hazard_ids:
            warnings.append(f"[UNKNOWN_HAZARD] risk_item hazard_id '{hid}' hazard_master에 없음")
        if not ri.get("controls"):
            warnings.append(f"[NO_CONTROLS] hazard '{hid}' 에 감소대책(controls)이 없음")

    return warnings


# ──────────────────────────────────────────────────────────────
# 내부 헬퍼
# ──────────────────────────────────────────────────────────────

def _build_payload_from_trade(
    trade: dict,
    masters: dict,
    source_trade_ids: list[str],
) -> dict:
    trade_id = trade["trade_id"]
    hazards_map = masters["hazards"]
    controls_map = masters["controls"]
    doc_map = masters["mappings"]["document"]
    training_map = masters["mappings"]["training"]
    equip_map = masters["mappings"]["equipment"]
    permit_map = masters["mappings"]["permit"]

    # risk_items 구성
    risk_items = []
    for hid in trade.get("default_hazards", []):
        hazard = hazards_map.get(hid, {})
        controls = controls_map.get(hid, [])
        risk_items.append({
            "hazard_id": hid,
            "hazard_name": hazard.get("hazard_name", hid),
            "category": hazard.get("category", ""),
            "risk_scenario": _make_risk_scenario(trade, hazard),
            "typical_causes": deepcopy(hazard.get("typical_causes", [])),
            "typical_consequences": deepcopy(hazard.get("typical_consequences", [])),
            "controls": deepcopy(controls),
            "related_documents": deepcopy(hazard.get("related_documents", [])),
            "source_trade_ids": list(source_trade_ids),
            "source_status": trade.get("source_status", "PRACTICAL"),
        })

    # mapping 파일에서 서류·교육·장비·허가서 조회
    doc_m = doc_map.get(trade_id, {})
    train_m = training_map.get(trade_id, {})
    equip_m = equip_map.get(trade_id, {})
    permit_m = permit_map.get(trade_id, {})

    required_docs = _dedup_list(
        list(trade.get("required_documents", [])) +
        list(doc_m.get("required_documents", []))
    )
    recommended_docs = _dedup_list(
        list(trade.get("recommended_documents", [])) +
        list(doc_m.get("recommended_documents", []))
    )
    required_trainings = _dedup_list(
        list(trade.get("required_trainings", [])) +
        list(train_m.get("required_trainings", []))
    )
    required_permits = _dedup_list(
        list(trade.get("required_permits", [])) +
        list(permit_m.get("required_permits", []))
    )
    common_equipment = _dedup_list(
        list(trade.get("common_equipment", [])) +
        list(equip_m.get("common_equipment", []))
    )
    ppe = list(trade.get("ppe", []))

    source_status_summary = _summarize_source_status(risk_items)

    return {
        "trade_id": trade_id,
        "trade_name": trade.get("trade_name", ""),
        "trade_group": trade.get("trade_group", ""),
        "site_context": _normalize_site_context(None),
        "risk_items": risk_items,
        "required_documents": required_docs,
        "recommended_documents": recommended_docs,
        "required_trainings": required_trainings,
        "required_permits": required_permits,
        "common_equipment": common_equipment,
        "ppe": ppe,
        "warnings": [],
        "source_trace": list(source_trade_ids),
        "source_status_summary": source_status_summary,
    }


def _normalize_site_context(ctx: dict | None) -> dict:
    default = {
        "site_name": None,
        "work_location": None,
        "work_date": None,
        "workers_count": None,
        "equipment_used": [],
    }
    if ctx:
        default.update({k: v for k, v in ctx.items() if k in default})
    return default


def _make_risk_scenario(trade: dict, hazard: dict) -> str:
    trade_name = trade.get("trade_name", "")
    hazard_name = hazard.get("hazard_name", "")
    if trade_name and hazard_name:
        return f"{trade_name} 작업 중 {hazard_name} 발생 가능"
    return ""


def _summarize_source_status(risk_items: list[dict]) -> dict:
    summary: dict[str, int] = {
        "VERIFIED": 0,
        "PARTIAL_VERIFIED": 0,
        "NEEDS_VERIFICATION": 0,
        "PRACTICAL": 0,
    }
    for ri in risk_items:
        ss = ri.get("source_status", "PRACTICAL")
        if ss in summary:
            summary[ss] += 1
        else:
            summary["PRACTICAL"] += 1
    return summary

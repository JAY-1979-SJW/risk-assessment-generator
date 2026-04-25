"""
trade_risk_recommendation payload → TBM 안전점검 일지 변환 어댑터 v1

주요 함수:
  build_tbm_input_from_trade_recommendation(recommendation)
      - payload → tbm_log_builder 입력 dict 변환
  build_tbm_input_from_trade_id(trade_id, ...)
      - trade_id → recommender 호출 → TBM 입력 반환
  validate_tbm_input(payload)
      - 필수 필드 누락·hazard/안전수칙·허가서 반영 여부 검사 → warning list

고정 문구 (법정 고지):
  1. TBM 일지는 법정 안전보건교육 수료증을 대체하지 않는다.
  2. 공종별 프리셋 기반 초안 — 관리감독자·근로자 검토·보완 필요.
  3. 작업허가서·점검표·보호구·장비 상태는 현장 최종 확인.
  4. TBM 사진은 법정 필수 고정항목 아님 — 점검 대응 권장 증빙.

사진 증빙 정책:
  TBM_MEETING, WORK_AREA_BEFORE → RECOMMENDED
  PPE_CHECK, PERMIT_OR_CHECKLIST → OPTIONAL
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# ──────────────────────────────────────────────────────────────
# 고정 문구
# ──────────────────────────────────────────────────────────────

FIXED_NOTICES: tuple[str, ...] = (
    "본 TBM 일지는 작업 전 위험요인 공유 및 안전작업 지시 기록이며, "
    "법정 안전보건교육 수료증을 대체하지 않는다.",
    "본 내용은 공종별 프리셋 기반 초안이며, "
    "현장 조건에 따라 관리감독자와 근로자가 검토·보완해야 한다.",
    "작업허가서, 점검표, 보호구, 장비 상태는 작업 전 현장에서 최종 확인한다.",
    "TBM 사진은 법정 필수 고정항목이 아니라 점검 대응을 위한 권장 증빙으로 관리한다.",
)

_PHOTO_EVIDENCE_DEFAULT: dict[str, str] = {
    "TBM_MEETING": "RECOMMENDED",
    "WORK_AREA_BEFORE": "RECOMMENDED",
    "PPE_CHECK": "OPTIONAL",
    "PERMIT_OR_CHECKLIST": "OPTIONAL",
}


# ──────────────────────────────────────────────────────────────
# 내부 유틸
# ──────────────────────────────────────────────────────────────

def _dedup(items: list) -> list:
    seen: set = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _normalize_tbm_site_context(ctx: dict | None) -> dict:
    default: dict[str, Any] = {
        "site_name": None,
        "work_location": None,
        "work_date": None,
        "workers_count": None,
        "equipment_used": [],
        "work_description": None,
    }
    if ctx:
        default.update({k: v for k, v in ctx.items() if k in default})
    return default


def _build_hazard_points(risk_items: list[dict]) -> str:
    lines = []
    for ri in risk_items:
        name = ri.get("hazard_name", "")
        scenario = ri.get("risk_scenario", "")
        if not name:
            continue
        line = f"• {name}" + (f": {scenario}" if scenario else "")
        lines.append(line)
    return "\n".join(lines)


def _build_safety_instructions(risk_items: list[dict]) -> str:
    seen: set[str] = set()
    lines: list[str] = []
    # sort controls by priority within each risk_item
    for ri in risk_items:
        controls = sorted(ri.get("controls", []), key=lambda c: c.get("priority", 9))
        for ctrl in controls:
            desc = ctrl.get("description", "").strip()
            if desc and desc not in seen:
                seen.add(desc)
                lines.append(f"• {desc}")
    return "\n".join(lines)


def _build_pre_work_checks(
    required_documents: list[str],
    recommended_documents: list[str],
    common_equipment: list[str],
    ppe: list[str],
    related_docs_from_risks: list[str],
) -> str:
    lines: list[str] = []

    for doc_id in required_documents:
        lines.append(f"[서류] {doc_id} 확인")
    for doc_id in related_docs_from_risks:
        if doc_id not in required_documents:
            lines.append(f"[참고서류] {doc_id} 확인")
    for doc_id in recommended_documents[:3]:
        if doc_id not in required_documents and doc_id not in related_docs_from_risks:
            lines.append(f"[권장서류] {doc_id} 확인")
    for equip in common_equipment:
        lines.append(f"[장비] {equip} 사전 점검")
    for p in ppe:
        lines.append(f"[보호구] {p} 착용 확인")

    return "\n".join(f"• {l}" for l in lines) if lines else ""


def _build_permit_check(
    required_permits: list[str],
    conditional_permits: list[str],
    warnings_out: list[str],
) -> str:
    lines: list[str] = []
    for pid in required_permits:
        lines.append(f"• [필수] {pid} 허가서 번호 및 유효기간 확인")
    for pid in conditional_permits:
        warnings_out.append(
            f"[CONDITIONAL_PERMIT] '{pid}'는 조건부 허가서입니다. "
            "현장 조건 확인 후 필요 여부를 판단하세요."
        )
    return "\n".join(lines)


def _build_training_notes(required_trainings: list[str]) -> str:
    lines = [f"• 필수 교육 이수 확인: {tc}" for tc in required_trainings]
    lines.append(f"• {FIXED_NOTICES[0]}")
    return "\n".join(lines)


def _collect_related_docs(risk_items: list[dict]) -> list[str]:
    docs: list[str] = []
    for ri in risk_items:
        for d in ri.get("related_documents", []):
            if d not in docs:
                docs.append(d)
    return docs


# ──────────────────────────────────────────────────────────────
# 1. payload → TBM 입력 변환
# ──────────────────────────────────────────────────────────────

def build_tbm_input_from_trade_recommendation(recommendation: dict) -> dict:
    """
    trade_risk_recommendation payload를 tbm_log_builder 입력 구조로 변환.

    반환 dict 구조:
      - tbm_log_builder 직접 입력 필드 (required + optional):
          tbm_date, today_work, hazard_points, safety_instructions,
          site_name, project_name, tbm_location, trade_name,
          pre_work_checks, permit_check, ppe_check,
          worker_opinion, action_items, attendees
      - 확장 메타 필드 (builder에 미전달, 검증·감사용):
          supervisor_signature, training_notes,
          photo_evidence, fixed_notices, _meta
    """
    ctx = _normalize_tbm_site_context(recommendation.get("site_context"))
    trade_name = recommendation.get("trade_name", "")
    risk_items = recommendation.get("risk_items", [])
    required_permits = list(recommendation.get("required_permits", []))
    conditional_permits: list[str] = []
    required_documents = list(recommendation.get("required_documents", []))
    recommended_documents = list(recommendation.get("recommended_documents", []))
    required_trainings = list(recommendation.get("required_trainings", []))
    ppe = list(recommendation.get("ppe", []))
    common_equipment = list(recommendation.get("common_equipment", []))
    related_docs = _collect_related_docs(risk_items)

    adapter_warnings: list[str] = []

    hazard_points = _build_hazard_points(risk_items)
    safety_instructions = _build_safety_instructions(risk_items)
    pre_work_checks = _build_pre_work_checks(
        required_documents, recommended_documents,
        common_equipment, ppe, related_docs,
    )
    permit_check = _build_permit_check(required_permits, conditional_permits, adapter_warnings)

    ppe_lines = [f"• {p}" for p in ppe]
    ppe_check = "\n".join(ppe_lines)

    training_notes = _build_training_notes(required_trainings)

    work_description = ctx.get("work_description")
    if work_description:
        today_work = work_description
    elif trade_name:
        today_work = f"{trade_name} 작업"
    else:
        today_work = ""

    all_warnings = adapter_warnings + list(recommendation.get("warnings", []))

    result: dict[str, Any] = {
        # ── tbm_log_builder required ──────────────────────────
        "tbm_date": ctx.get("work_date") or "",
        "today_work": today_work,
        "hazard_points": hazard_points,
        "safety_instructions": safety_instructions,
        # ── tbm_log_builder optional ──────────────────────────
        "site_name": ctx.get("site_name") or "",
        "project_name": "",
        "tbm_location": ctx.get("work_location") or "",
        "trade_name": trade_name,
        "pre_work_checks": pre_work_checks,
        "permit_check": permit_check,
        "ppe_check": ppe_check,
        "worker_opinion": "",
        "action_items": "",
        "attendees": [],
        # ── 확장 메타 필드 ─────────────────────────────────────
        "supervisor_signature": "",
        "training_notes": training_notes,
        "photo_evidence": deepcopy(_PHOTO_EVIDENCE_DEFAULT),
        "fixed_notices": list(FIXED_NOTICES),
        "_meta": {
            "trade_id": recommendation.get("trade_id", ""),
            "trade_name": trade_name,
            "trade_group": recommendation.get("trade_group", ""),
            "source_trace": list(recommendation.get("source_trace", [])),
            "source_status_summary": dict(recommendation.get("source_status_summary", {})),
            "required_permits": required_permits,
            "conditional_permits": conditional_permits,
            "required_trainings": required_trainings,
            "required_documents": required_documents,
            "recommended_documents": recommended_documents,
            "ppe": ppe,
            "common_equipment": common_equipment,
            "risk_items_count": len(risk_items),
            "warnings": all_warnings,
        },
    }
    return result


# ──────────────────────────────────────────────────────────────
# 2. trade_id → TBM 입력 변환
# ──────────────────────────────────────────────────────────────

def build_tbm_input_from_trade_id(
    trade_id: str,
    common_work_ids: list[str] | None = None,
    site_context: dict | None = None,
) -> dict:
    """
    trade_id → recommender → TBM 입력 dict.
    common_work_ids가 있으면 공통 고위험작업을 merge한다.
    site_context에 work_description 포함 가능 (recommender에는 전달하지 않음).
    """
    from engine.recommendation.trade_risk_recommender import (
        build_trade_risk_recommendation,
        get_trade_preset,
        merge_common_high_risk_presets,
    )

    # recommender가 받을 수 있는 키만 걸러냄 (work_description 제외)
    _recommender_keys = {"site_name", "work_location", "work_date", "workers_count", "equipment_used"}
    ctx_for_recommender = {
        k: v for k, v in (site_context or {}).items()
        if k in _recommender_keys
    } or None

    if common_work_ids:
        base = get_trade_preset(trade_id)
        recommendation = merge_common_high_risk_presets(base, list(common_work_ids))
        if site_context:
            recommendation["site_context"] = _normalize_tbm_site_context(site_context)
    else:
        recommendation = build_trade_risk_recommendation(trade_id, site_context=ctx_for_recommender)
        if site_context:
            recommendation["site_context"] = _normalize_tbm_site_context(site_context)

    return build_tbm_input_from_trade_recommendation(recommendation)


# ──────────────────────────────────────────────────────────────
# 3. TBM 입력 검증
# ──────────────────────────────────────────────────────────────

def validate_tbm_input(payload: dict) -> list[str]:
    """
    TBM 입력 dict 검사. warning 메시지 리스트 반환.
    FAIL 수준: 빈 hazard_points / safety_instructions / permit_check(허가서 있을 때)
    WARN 수준: trade_name 없음 / pre_work_checks 없음 / 사진 없음 / 현장정보 미입력
    """
    warnings: list[str] = []

    # 필수 필드 존재
    required_keys = ["tbm_date", "today_work", "hazard_points", "safety_instructions",
                     "attendees", "supervisor_signature", "fixed_notices", "photo_evidence"]
    for k in required_keys:
        if k not in payload:
            warnings.append(f"[MISSING_FIELD] '{k}' 필드 없음")

    # trade_name
    if not payload.get("trade_name"):
        warnings.append("[WARN] trade_name 미입력 — 공종명 없이 TBM 생성됨")

    # hazard_points
    if not (payload.get("hazard_points") or "").strip():
        warnings.append("[FAIL] hazard_points 없음 — 위험요인 최소 1개 필요")

    # safety_instructions
    if not (payload.get("safety_instructions") or "").strip():
        warnings.append("[FAIL] safety_instructions 없음 — 안전수칙 최소 1개 필요")

    # pre_work_checks
    if not (payload.get("pre_work_checks") or "").strip():
        warnings.append("[WARN] pre_work_checks 없음 — 작업 전 확인사항 입력 권장")

    # permit_check (required_permits가 있으면 필수)
    meta = payload.get("_meta", {})
    required_permits = meta.get("required_permits", [])
    if required_permits and not (payload.get("permit_check") or "").strip():
        warnings.append(
            f"[FAIL] required_permits {required_permits} 있으나 permit_check 미입력"
        )

    # supervisor_signature 필드 존재 확인 (빈 문자열이면 WARN)
    if "supervisor_signature" in payload and payload["supervisor_signature"] == "":
        warnings.append("[WARN] supervisor_signature 미입력 — 현장 서명 후 보관")

    # attendees 존재 확인 (빈 리스트면 WARN)
    attendees = payload.get("attendees", [])
    if not attendees:
        warnings.append("[WARN] attendees 없음 — 참석자 명단 현장 작성 필요")

    # photo_evidence
    photo = payload.get("photo_evidence", {})
    if not photo:
        warnings.append("[WARN] photo_evidence 없음 — 사진 증빙 설정 권장")
    else:
        for key in ("TBM_MEETING", "WORK_AREA_BEFORE"):
            if photo.get(key) not in ("RECOMMENDED", "REQUIRED"):
                warnings.append(f"[WARN] photo_evidence.{key} 권장 상태 아님: {photo.get(key)!r}")

    # fixed_notices 4개 포함
    notices = payload.get("fixed_notices", [])
    for notice in FIXED_NOTICES:
        if notice not in notices:
            warnings.append(f"[FAIL] 필수 고정 문구 누락: '{notice[:40]}...'")

    # 현장 정보 미입력 → WARN
    for field, label in [("site_name", "사업장명"), ("tbm_location", "실시 장소"),
                         ("tbm_date", "실시 일시")]:
        if not (payload.get(field) or "").strip():
            warnings.append(f"[WARN] '{field}'({label}) 미입력 — 빈칸으로 출력됨")

    return warnings

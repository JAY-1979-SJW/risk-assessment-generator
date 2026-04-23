"""
Risk assessment table builder.

Converts v2 API result (from build_risk_assessment + apply_rules) into a
field-submission-ready table structure.

Design: docs/design/risk_scoring_rule.md
Schema: data/risk_db/api_schema/risk_assessment_table_schema.json

Principles:
- Pure data transformation (no DB/IO side effects in the transform core).
- No data fabrication; preserve hazard/controls/references ordering.
- Deterministic risk level mapping from confidence_score.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

MAX_CONTROLS_PER_ROW = 7
EVIDENCE_MAX_LEN = 140
EVIDENCE_MIN_SENTENCE_LEN = 40

_LEVEL_DOWNGRADE = {"High": "Medium", "Medium": "Low", "Low": "Low"}


def _confidence_to_level(score: float) -> str:
    """confidence_score → risk level (규칙: ≥0.9 High / 0.8~0.89 Medium / <0.8 Low)."""
    try:
        s = float(score)
    except (TypeError, ValueError):
        s = 0.0
    if s >= 0.9:
        return "High"
    if s >= 0.8:
        return "Medium"
    return "Low"


def _residual_level(current: str, has_controls: bool) -> str:
    """current_risk에서 1단계 감소. controls가 비어 있으면 감소 없음."""
    if not has_controls:
        return current
    return _LEVEL_DOWNGRADE.get(current, "Low")


def _first_sentence(evidence: str, max_len: int = EVIDENCE_MAX_LEN) -> str:
    """evidence_summary에서 첫 온전한 문장 추출. 절삭 시 '…' 부착."""
    ev = (evidence or "").strip()
    if not ev:
        return ""
    upper = min(len(ev), max_len + 1)
    for i in range(EVIDENCE_MIN_SENTENCE_LEN, upper):
        # Korean/English period followed by whitespace or newline
        if ev[i] == "." and (i + 1 == len(ev) or ev[i + 1] in (" ", "\n", "\t")):
            return ev[:i + 1].strip()
    if len(ev) <= max_len:
        return ev
    return ev[:max_len].rstrip() + "…"


def _reference_count_note(references: Optional[Dict[str, List[int]]]) -> str:
    """references 3축 건수 요약 표기."""
    refs = references or {}
    law_n = len(refs.get("law_ids") or [])
    moel_n = len(refs.get("moel_expc_ids") or [])
    kosha_n = len(refs.get("kosha_ids") or [])
    if law_n == 0 and moel_n == 0 and kosha_n == 0:
        return "[참조 없음]"
    return f"[법령 {law_n}건 · 해석례 {moel_n}건 · KOSHA {kosha_n}건]"


def _summarize(evidence: str, references: Optional[Dict[str, List[int]]]) -> str:
    sentence = _first_sentence(evidence)
    note = _reference_count_note(references)
    if sentence:
        return f"{sentence} {note}"
    return note


def _truncate_controls(controls: Optional[List[str]]) -> List[str]:
    if not controls:
        return []
    cleaned = [str(c).strip() for c in controls if c and str(c).strip()]
    return cleaned[:MAX_CONTROLS_PER_ROW]


def build_risk_table_from_result(api_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure transformation: v2 API dict → table dict.

    Does not call DB or network. Accepts the exact structure returned by
    POST /api/v1/risk-assessment/build (with or without input_context).
    """
    work_type = str(api_result.get("work_type") or "").strip()
    hazards = api_result.get("hazards") or []

    rows: List[Dict[str, Any]] = []
    for h in hazards:
        if not isinstance(h, dict):
            continue
        hazard_name = str(h.get("hazard") or "").strip()
        if not hazard_name:
            continue
        controls = _truncate_controls(h.get("controls"))
        current = _confidence_to_level(h.get("confidence_score", 0.0))
        residual = _residual_level(current, has_controls=bool(controls))
        summary = _summarize(h.get("evidence_summary", ""), h.get("references"))

        rows.append({
            "process": work_type,
            "hazard": hazard_name,
            "current_risk": current,
            "control_measures": controls,
            "residual_risk": residual,
            "references_summary": summary,
        })

    return {"work_type": work_type, "rows": rows}


def build_risk_table(
    work_type: str,
    input_context: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    """
    Convenience wrapper: mapper + enrichment + transform.

    Calls:
      - engine.kras_connector.mapper.build_risk_assessment(work_type)
      - engine.kras_connector.enrichment.apply_rules(result, ctx) when context 제공
    Then runs build_risk_table_from_result on the enriched output.

    input_context format: {"equipment": [...], "location": [...], "conditions": [...]}.
    Whitelist/normalization are the caller's responsibility (handled by the API route).
    """
    # 지연 import — 순환/DB 의존 분리
    from engine.kras_connector.mapper import build_risk_assessment
    from engine.kras_connector.enrichment import apply_rules, context_is_empty

    base = build_risk_assessment(work_type)
    if not base.get("hazards"):
        return {"work_type": base.get("work_type", work_type), "rows": []}

    ctx = {
        "equipment": list((input_context or {}).get("equipment") or []),
        "location":  list((input_context or {}).get("location")  or []),
        "conditions":list((input_context or {}).get("conditions")or []),
    }

    if context_is_empty(ctx):
        return build_risk_table_from_result(base)

    enriched = apply_rules(base, ctx)
    return build_risk_table_from_result(enriched)

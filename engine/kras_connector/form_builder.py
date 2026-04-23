"""
KRAS 표준 위험성평가표 본표 생성 엔진 (v1).

Input:
  - table_data: engine.kras_connector.table_builder.build_risk_table_from_result() 출력
  - header_input: 사용자 제공 상단 메타
  - optional_input: 사용자 제공 운영 필드 (선택)

Output:
  - kras_standard_form_v1 스키마 준수 JSON 딕셔너리

Spec lock:  docs/standards/form_builder_spec_lock.md
Risk rule:  docs/design/form_risk_mapping_rule.md
Schema:     data/risk_db/api_schema/kras_standard_form_v1.json

Principles:
- 공종(work_category) 필드 추가 금지.
- hazard_category_major/minor, current_measures 는 자동 생성 금지 → 항상 null.
- 없는 값 임의 생성 금지. 사용자 미입력 필드는 null 유지.
- 공식 본표 4개 서식(F1 KRAS 12컬럼, F2/F3/F4 공문기반 16컬럼) 헤더 실증 준수.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

FORM_VERSION = "kras-standard-v1"
RISK_SCALE = "3x3"
MAX_CONTROL_MEASURES = 7

# table_builder level → (probability, severity) 역산
_LEVEL_TO_PS = {
    "High":   (3, 3),
    "Medium": (2, 3),
    "Low":    (2, 2),
}

_HEADER_KEYS = (
    "company_name", "site_name", "industry", "representative",
    "assessment_type", "assessment_date", "work_type",
)

_OPTIONAL_ROW_KEYS = (
    "sub_work", "target_date", "completion_date", "responsible_person",
)


def _risk_band(level: int) -> str:
    """risk_level 정수 → risk_band 문자열."""
    if level >= 9:
        return "critical"
    if level >= 6:
        return "high"
    if level >= 3:
        return "medium"
    return "low"


def _compute_current(level_label: str) -> Dict[str, Any]:
    prob, sev = _LEVEL_TO_PS.get(level_label, _LEVEL_TO_PS["Low"])
    rl = prob * sev
    return {
        "probability": prob,
        "severity": sev,
        "risk_level": rl,
        "risk_band": _risk_band(rl),
    }


def _compute_residual(current_label: str) -> Dict[str, Any]:
    """
    residual 역산 (v1 규칙):
      - severity 불변
      - probability 1단계 감소 (최소 1)
      - current=Low 의 경우 변경 없음 (Low→Low)
    """
    prob, sev = _LEVEL_TO_PS.get(current_label, _LEVEL_TO_PS["Low"])
    if current_label == "Low":
        r_prob, r_sev = prob, sev
    else:
        r_prob = max(1, prob - 1)
        r_sev = sev
    r_level = r_prob * r_sev
    return {
        "residual_probability": r_prob,
        "residual_severity": r_sev,
        "residual_risk_level": r_level,
        "residual_risk_band": _risk_band(r_level),
    }


def _extract_legal_basis(references_summary: Optional[str]) -> Optional[str]:
    """
    references_summary 말미의 '[법령 N건 · 해석례 N건 · KOSHA N건]' 카운트 주석 제거.
    """
    if not references_summary:
        return None
    text = references_summary.strip()
    idx = text.rfind(" [")
    if idx > 0:
        text = text[:idx].strip()
    return text or None


def _scale_definition() -> Dict[str, Any]:
    return {
        "notation": RISK_SCALE,
        "probability_levels": {"1": "하", "2": "중", "3": "상"},
        "severity_levels":    {"1": "소", "2": "중", "3": "대"},
        "risk_bands": {
            "low":      [1, 2],
            "medium":   [3, 4],
            "high":     [6],
            "critical": [9],
        },
    }


def _build_header(header_input: Optional[Dict[str, Any]], work_type_fallback: str) -> Dict[str, Any]:
    hi = header_input or {}
    out = {k: (hi.get(k) if hi.get(k) not in ("",) else None) for k in _HEADER_KEYS}
    if not out.get("work_type"):
        out["work_type"] = work_type_fallback or None
    return out


def _row_optional_value(
    optional_input: Optional[Dict[str, Any]],
    idx: int,
    key: str,
) -> Any:
    """
    optional_input 에서 row 인덱스 idx 의 key 값을 꺼낸다.
    우선순위: rows[idx][key] > flat[key] > None.
    빈 문자열은 None 으로 취급.
    """
    if not isinstance(optional_input, dict):
        return None

    rows = optional_input.get("rows")
    if isinstance(rows, list) and 0 <= idx < len(rows):
        row_opt = rows[idx]
        if isinstance(row_opt, dict) and key in row_opt:
            v = row_opt[key]
            return v if v not in ("",) else None

    v = optional_input.get(key)
    return v if v not in ("", None) else None


def build_risk_assessment_form(
    table_data: Dict[str, Any],
    header_input: Dict[str, Any],
    optional_input: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    KRAS 표준 본표 (위험성평가실시표) 생성.

    v1 정책:
      - 공정명 + 세부작업명 2단 구조 유지.
      - 공종(work_category) 필드 미포함.
      - hazard_category_major/minor, current_measures 는 항상 null (자동/사용자 입력 모두 금지).
      - sub_work, target_date, completion_date, responsible_person 은 optional_input 기반.
    """
    work_type = (table_data or {}).get("work_type") or ""
    header = _build_header(header_input, work_type)

    scale_def = _scale_definition()

    rows_in = (table_data or {}).get("rows") or []
    rows_out: List[Dict[str, Any]] = []

    for idx, r in enumerate(rows_in):
        if not isinstance(r, dict):
            continue
        hazard = (r.get("hazard") or "").strip()
        if not hazard:
            continue

        current_label = r.get("current_risk") or "Low"
        current = _compute_current(current_label)
        residual = _compute_residual(current_label)

        controls = r.get("control_measures") or []
        controls = [str(c).strip() for c in controls if c and str(c).strip()][:MAX_CONTROL_MEASURES]

        rows_out.append({
            "no": idx + 1,  # 정렬 후 재부여
            "process": (r.get("process") or work_type or "").strip(),
            "sub_work": _row_optional_value(optional_input, idx, "sub_work"),
            "hazard_category_major": None,
            "hazard_category_minor": None,
            "hazard": hazard,
            "legal_basis": _extract_legal_basis(r.get("references_summary")),
            "current_measures": None,
            "risk_scale": RISK_SCALE,
            "probability": current["probability"],
            "severity": current["severity"],
            "risk_level": current["risk_level"],
            "risk_band": current["risk_band"],
            "control_measures": controls,
            "residual_probability": residual["residual_probability"],
            "residual_severity": residual["residual_severity"],
            "residual_risk_level": residual["residual_risk_level"],
            "residual_risk_band": residual["residual_risk_band"],
            "target_date": _row_optional_value(optional_input, idx, "target_date"),
            "completion_date": _row_optional_value(optional_input, idx, "completion_date"),
            "responsible_person": _row_optional_value(optional_input, idx, "responsible_person"),
            "references_detail": None,
        })

    # risk_level DESC → probability DESC → severity DESC 정렬, no 재부여
    rows_out.sort(
        key=lambda rr: (-rr["risk_level"], -rr["probability"], -rr["severity"]),
    )
    for i, rr in enumerate(rows_out):
        rr["no"] = i + 1

    return {
        "form_version": FORM_VERSION,
        "header": header,
        "scale_definition": scale_def,
        "rows": rows_out,
    }

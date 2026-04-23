"""
Risk assessment enrichment engine (v2).

Applies rule-based post-processing on top of build_risk_assessment() output
using equipment / location / conditions input context.

Design: docs/design/enrichment_rulebook.md
Rules:  data/risk_db/rules/enrichment_rule_matrix.json
Catalog: data/risk_db/api_schema/input_option_catalog.json

Principles:
- Never remove or modify existing hazards, controls, references.
- Re-order hazards by confidence_score DESC after applying boosts (v1 invariant).
- related_expc_ids must never be exposed.
- No AI, no free-text matching — whitelist + substring only.
"""
from __future__ import annotations

import json
import logging
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── 자원 경로 ─────────────────────────────────────────────────────────────────
# /app/data (컨테이너) 및 프로젝트 루트 양쪽 지원
_THIS_DIR = Path(__file__).resolve().parent


def _find_data_root() -> Path:
    candidates = [
        Path("/app/data"),
        _THIS_DIR.parent.parent / "data",
    ]
    for c in candidates:
        if (c / "risk_db" / "api_schema" / "input_option_catalog.json").exists():
            return c
    return candidates[-1]


_DATA_ROOT = _find_data_root()
_CATALOG_PATH = _DATA_ROOT / "risk_db" / "api_schema" / "input_option_catalog.json"
_RULES_PATH = _DATA_ROOT / "risk_db" / "rules" / "enrichment_rule_matrix.json"

_catalog_cache: Optional[Dict[str, Any]] = None
_rules_cache: Optional[List[Dict[str, Any]]] = None


def _load_catalog() -> Dict[str, Any]:
    global _catalog_cache
    if _catalog_cache is None:
        with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
            _catalog_cache = json.load(f)
    return _catalog_cache


def _load_rules() -> List[Dict[str, Any]]:
    global _rules_cache
    if _rules_cache is None:
        with open(_RULES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        _rules_cache = sorted(data.get("rules", []), key=lambda r: r.get("id", ""))
    return _rules_cache


def allowed_values(field: str) -> List[str]:
    cat = _load_catalog()
    return list(cat.get(field, []))


# ── 입력 검증 ─────────────────────────────────────────────────────────────────
class InvalidInputOption(ValueError):
    """Raised when equipment/location/conditions fails validation."""

    def __init__(self, field: str, value: Any, allowed: List[str]):
        self.field = field
        self.value = value
        self.allowed = allowed
        super().__init__(
            f"INVALID_INPUT_OPTION: field={field} value={value!r}"
        )


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def normalize_input_context(body: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate and normalize equipment/location/conditions.

    - Each field is optional; missing/null/empty-array ⇒ [] (no rule apply).
    - Each element: non-empty string, NFC normalized, in whitelist.
    - Duplicates are deduped preserving first-seen order.

    Raises InvalidInputOption with (field, value, allowed) on any violation.
    """
    out: Dict[str, List[str]] = {
        "equipment": [],
        "location": [],
        "conditions": [],
    }

    for field in ("equipment", "location", "conditions"):
        raw = body.get(field)
        if raw is None:
            continue
        if not isinstance(raw, list):
            raise InvalidInputOption(field, raw, allowed_values(field))

        allowed = allowed_values(field)
        allowed_set = set(allowed)
        seen: set = set()
        cleaned: List[str] = []
        for item in raw:
            if not isinstance(item, str):
                raise InvalidInputOption(field, item, allowed)
            norm = _nfc(item.strip())
            if norm == "":
                raise InvalidInputOption(field, item, allowed)
            if norm not in allowed_set:
                raise InvalidInputOption(field, item, allowed)
            if norm in seen:
                continue  # auto-dedupe
            seen.add(norm)
            cleaned.append(norm)
        out[field] = cleaned

    return out


def context_is_empty(ctx: Dict[str, List[str]]) -> bool:
    """True if no enrichment input was provided — v1 path."""
    return not (ctx["equipment"] or ctx["location"] or ctx["conditions"])


# ── 규칙 매칭 / 적용 ───────────────────────────────────────────────────────────
def _rule_matches(rule: Dict[str, Any], work_type: str, ctx: Dict[str, List[str]]) -> bool:
    when = rule.get("when", {})

    rule_wt = when.get("work_type")
    if rule_wt is not None and rule_wt != work_type:
        return False

    for key, field in (
        ("equipment_any", "equipment"),
        ("location_any", "location"),
        ("conditions_any", "conditions"),
    ):
        required = when.get(key)
        if required:
            if not any(v in ctx[field] for v in required):
                return False
    return True


def _pick_hazard_by_contains(
    hazards: List[Dict[str, Any]], needle: str
) -> Optional[int]:
    """Return index of hazard with substring match AND highest confidence_score."""
    needle_n = _nfc(needle)
    candidates = [
        (i, h.get("confidence_score", 0.0))
        for i, h in enumerate(hazards)
        if needle_n in _nfc(h.get("hazard", ""))
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda t: (-t[1], t[0]))
    return candidates[0][0]


def _apply_boost(hazards: List[Dict[str, Any]], idx: int, delta: float) -> None:
    delta = max(0.0, min(0.1, float(delta)))  # cap
    current = float(hazards[idx].get("confidence_score", 0.0) or 0.0)
    new = min(1.0, current + delta)
    hazards[idx]["confidence_score"] = round(new, 4)


def _apply_add_controls(
    hazards: List[Dict[str, Any]],
    idx: int,
    new_controls: List[str],
    added_counter: Dict[int, int],
) -> None:
    max_added_per_hazard = 2
    existing = list(hazards[idx].get("controls", []))
    existing_set = {c.strip() for c in existing}
    for c in new_controls:
        if added_counter.get(idx, 0) >= max_added_per_hazard:
            break
        c_stripped = c.strip()
        if not c_stripped or c_stripped in existing_set:
            continue
        existing.append(c_stripped)
        existing_set.add(c_stripped)
        added_counter[idx] = added_counter.get(idx, 0) + 1
    hazards[idx]["controls"] = existing


def _apply_tag_evidence(hazards: List[Dict[str, Any]], idx: int, note: str) -> None:
    tag = f" [조건 반영: {note}]"
    summary = hazards[idx].get("evidence_summary") or ""
    if tag in summary:
        return
    hazards[idx]["evidence_summary"] = (summary + tag).strip()


def _apply_add_hazard(
    hazards: List[Dict[str, Any]],
    rule_effect: Dict[str, Any],
) -> bool:
    name = rule_effect.get("hazard", "").strip()
    if not name:
        return False
    # Skip if a hazard with the same name already exists
    for h in hazards:
        if _nfc(h.get("hazard", "")) == _nfc(name):
            return False
    controls = [c.strip() for c in rule_effect.get("controls", []) if c.strip()][:2]
    hazards.append({
        "hazard": name,
        "controls": controls,
        "references": {"law_ids": [], "moel_expc_ids": [], "kosha_ids": []},
        "confidence_score": float(rule_effect.get("confidence_score", 0.70)),
        "evidence_summary": rule_effect.get("evidence_summary", "").strip(),
    })
    return True


def apply_rules(
    base_result: Dict[str, Any],
    ctx: Dict[str, List[str]],
) -> Dict[str, Any]:
    """
    Apply enrichment rules to base risk assessment result.

    base_result format (from mapper.build_risk_assessment):
        {"work_type": str, "hazards": [...]}

    Returns:
        Shallow-copied result with hazards enriched and input_context added
        (only when ctx is non-empty).
    """
    work_type = base_result.get("work_type", "")
    hazards = [dict(h) for h in base_result.get("hazards", [])]
    # deep-copy controls and references to avoid mutating mapper output
    for h in hazards:
        h["controls"] = list(h.get("controls", []))
        refs = h.get("references", {})
        h["references"] = {
            "law_ids": list(refs.get("law_ids", [])),
            "moel_expc_ids": list(refs.get("moel_expc_ids", [])),
            "kosha_ids": list(refs.get("kosha_ids", [])),
        }

    if context_is_empty(ctx):
        return {"work_type": work_type, "hazards": hazards}

    added_counter: Dict[int, int] = {}
    add_hazard_used = 0
    add_hazard_limit = 1
    changed_any = False

    for rule in _load_rules():
        if not _rule_matches(rule, work_type, ctx):
            continue

        for effect in rule.get("effects", []):
            etype = effect.get("type")
            if etype in ("boost_hazard", "add_controls", "tag_evidence"):
                needle = effect.get("match_hazard_contains", "")
                idx = _pick_hazard_by_contains(hazards, needle) if needle else None
                if idx is None:
                    continue
                if etype == "boost_hazard":
                    _apply_boost(hazards, idx, effect.get("delta", 0.0))
                    changed_any = True
                elif etype == "add_controls":
                    before = len(hazards[idx]["controls"])
                    _apply_add_controls(
                        hazards, idx, effect.get("controls", []), added_counter
                    )
                    if len(hazards[idx]["controls"]) > before:
                        changed_any = True
                elif etype == "tag_evidence":
                    _apply_tag_evidence(hazards, idx, effect.get("note", ""))
                    changed_any = True
            elif etype == "add_hazard":
                if add_hazard_used >= add_hazard_limit:
                    continue
                if _apply_add_hazard(hazards, effect):
                    add_hazard_used += 1
                    changed_any = True
            else:
                logger.warning("unknown effect type: %r (rule=%s)", etype, rule.get("id"))

    if changed_any:
        hazards.sort(
            key=lambda h: (-float(h.get("confidence_score", 0.0) or 0.0),
                           h.get("hazard", "")),
        )

    return {"work_type": work_type, "hazards": hazards}

"""
위험성평가표 초안 생성 서비스 — 4축 추천 엔진 최소 구현
책임: 후보 계산 + 조립 (HTTP/응답 직렬화는 라우터 담당)
"""
from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── 데이터 파일 경로 ───────────────────────────────────────────────────────────

_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[2]
_DATA = _ROOT / "data" / "risk_db"
_CONTAINER_DATA = Path("/app/data/risk_db")


def _data(rel: str) -> Path:
    p = _DATA / rel
    if p.exists():
        return p
    cp = _CONTAINER_DATA / rel
    if cp.exists():
        return cp
    raise FileNotFoundError(f"data file not found: {rel}")


def _load(rel: str) -> Any:
    with open(_data(rel), encoding="utf-8") as f:
        return json.load(f)


# ── 엔진 상수 ─────────────────────────────────────────────────────────────────

_FREQ_COEF = 20
_SEV_COEF = 10
_RULE_BASE = 65
_SCORE_MAX = 98

_CONDITION_BONUS: dict[str, dict[str, int]] = {
    "high_place":     {"FALL": 15, "DROP": 10},
    "confined_space": {"ASPHYX": 15, "EXPLO": 10, "POISON": 8},
    "live_electric":  {"ELEC": 15},
    "night_work":     {"COLLIDE": 8, "TRIP": 8, "FALL": 5},
    "chemical_use":   {"CHEM": 12, "POISON": 12, "DUST": 6},
}

_CONTROL_SCORE: dict[str, int] = {
    "engineering__1": 90, "admin__1": 85, "ppe__1": 80,
    "engineering__2": 80, "admin__2": 75, "ppe__2": 72,
}

_LAW_PATH_WEIGHT: dict[str, float] = {
    "control_law": 1.0,
    "hazard_law": 0.9,
    "worktype_law": 0.8,
}

# Evidence type priority for deterministic ordering (lower = higher priority)
# control_law present → 0 (control-specific, most relevant)
# hazard_law present, no control_law → 1 (hazard-specific)
# worktype_law only → 2 (generic fallback)
_EV_TYPE_PRIORITY: dict[str, int] = {
    "control_law": 0,
    "hazard_law": 1,
    "worktype_law": 2,
}

_GENERIC_LAW_CAP_WITH_SPECIFIC = 1   # max generic laws when specific exist
_GENERIC_LAW_CAP_FALLBACK = 2        # max generic laws when no specific exist

_PIPELINE_VERSION = "1.0"

_SOURCES_USED: list[str] = [
    "work_hazards_map",
    "controls_normalized",
    "law_hazard_map",
    "law_worktype_map",
    "law_control_map",
]

_RECOMMENDED_FLAGS: dict[str, list[str]] = {
    "ELEC_LIVE":      ["live_electric"],
    "WATER_MANHOLE":  ["confined_space"],
    "WATER_PIPEINST": ["confined_space"],
    "DEMO_ASBESTOS":  ["chemical_use"],
}

_PPE_TYPES = {"ppe"}
_LOW_SCORE_THRESHOLD = 60
_LOW_LAW_SCORE = 55.0


# ── 데이터 로더 — 이중 캐시 (raw JSON + 조립된 dict) ──────────────────────────

_cache: dict[str, Any] = {}


def _get(key: str) -> Any:
    """raw JSON을 캐시. 두 번째 호출부터 파일 I/O 없음."""
    if key not in _cache:
        _cache[key] = _load(key)
    return _cache[key]


def _get_proc(key: str, builder: Any) -> Any:
    """조립된 dict/인덱스를 캐시. 두 번째 호출부터 재조립 없음."""
    proc_key = f"_proc:{key}"
    if proc_key not in _cache:
        _cache[proc_key] = builder()
    return _cache[proc_key]


def _work_types() -> dict[str, dict]:
    return _get_proc("work_types", lambda: {
        w["code"]: w
        for w in _get("work_taxonomy/work_types.json")["work_types"]
    })


def _hazard_map() -> dict[str, list[dict]]:
    def _build():
        result: dict[str, list[dict]] = defaultdict(list)
        for m in _get("work_taxonomy/work_hazards_map.json")["mappings"]:
            result[m["work_type_code"]].append(m)
        return result
    return _get_proc("hazard_map", _build)


def _hazards() -> dict[str, dict]:
    return _get_proc("hazards", lambda: {
        h["code"]: h
        for h in _get("hazard_action/hazards.json")["hazards"]
    })


def _controls_indexes() -> tuple[dict[str, list[dict]], dict[str, dict]]:
    """controls_normalized.json을 한 번만 순회해 두 인덱스를 동시에 구축."""
    def _build():
        by_hazard: dict[str, list[dict]] = defaultdict(list)
        by_code: dict[str, dict] = {}
        for c in _get("hazard_action_normalized/controls_normalized.json")["items"]:
            by_hazard[c["hazard_code"]].append(c)
            by_code[c["control_code"]] = c
        return by_hazard, by_code
    return _get_proc("controls_indexes", _build)


def _controls_by_hazard() -> dict[str, list[dict]]:
    return _controls_indexes()[0]


def _controls_by_code() -> dict[str, dict]:
    return _controls_indexes()[1]


def _law_worktype_map() -> dict[str, list[dict]]:
    def _build():
        result: dict[str, list[dict]] = defaultdict(list)
        for item in _get("law_mapping/law_worktype_map.json")["items"]:
            result[item["work_type_code"]].append(item)
        return result
    return _get_proc("law_worktype_map", _build)


def _law_hazard_map() -> dict[str, list[dict]]:
    def _build():
        result: dict[str, list[dict]] = defaultdict(list)
        for item in _get("law_mapping/law_hazard_map.json")["items"]:
            result[item["hazard_code"]].append(item)
        return result
    return _get_proc("law_hazard_map", _build)


def _law_control_map() -> dict[str, list[dict]]:
    def _build():
        result: dict[str, list[dict]] = defaultdict(list)
        for item in _get("law_mapping/law_control_map.json")["items"]:
            result[item["control_code"]].append(item)
        return result
    return _get_proc("law_control_map", _build)


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _control_score(control: dict) -> int:
    ctype = control.get("control_type", "ppe")
    priority = control.get("priority", 2)
    return _CONTROL_SCORE.get(f"{ctype}__{priority}", 70)


def _hazard_base_score(mapping: dict) -> int:
    freq = mapping.get("frequency", 2)
    sev = mapping.get("severity", 2)
    return min(freq * _FREQ_COEF + sev * _SEV_COEF, _SCORE_MAX)


def _apply_condition_bonus(score: int, hazard_code: str, flags: list[str]) -> int:
    bonus = sum(_CONDITION_BONUS.get(f, {}).get(hazard_code, 0) for f in flags)
    return min(score + bonus, _SCORE_MAX)


def _merge_law_evidence(
    work_type_code: str,
    hazard_code: str,
    control_codes: list[str],
    max_laws: int,
    include_law_evidence: bool,
) -> list[dict]:
    if not include_law_evidence:
        return []

    wt_map = _law_worktype_map()
    hz_map = _law_hazard_map()
    ct_map = _law_control_map()

    law_evidence: dict[str, dict] = {}

    def _add(items: list[dict], path_key: str):
        weight = _LAW_PATH_WEIGHT[path_key]
        for item in items:
            lid = item["law_id"]
            weighted = item.get("match_score", 50) * weight
            if lid not in law_evidence:
                law_evidence[lid] = {
                    "law_id": lid,
                    "law_title": item.get("law_title", ""),
                    "law_score": weighted,
                    "evidence_paths": [path_key],
                    "detail_link": item.get("detail_link"),
                }
            else:
                existing = law_evidence[lid]
                if weighted > existing["law_score"]:
                    existing["law_score"] = weighted
                if path_key not in existing["evidence_paths"]:
                    existing["evidence_paths"].append(path_key)

    _add(wt_map.get(work_type_code, []), "worktype_law")
    _add(hz_map.get(hazard_code, []), "hazard_law")
    for cc in control_codes:
        _add(ct_map.get(cc, []), "control_law")

    def _ev_priority(paths: list[str]) -> int:
        for key in ("control_law", "hazard_law", "worktype_law"):
            if key in paths:
                return _EV_TYPE_PRIORITY[key]
        return 2

    candidates = list(law_evidence.values())
    # Deterministic sort: evidence priority ASC → score DESC → law_id ASC (tie-break)
    candidates.sort(key=lambda x: (_ev_priority(x["evidence_paths"]), -x["law_score"], x["law_id"]))

    # Cap generic (worktype-only) laws: max 1 when specific laws exist, 2 otherwise
    specific = [x for x in candidates if _ev_priority(x["evidence_paths"]) < 2]
    generic = [x for x in candidates if _ev_priority(x["evidence_paths"]) == 2]
    max_generic = _GENERIC_LAW_CAP_WITH_SPECIFIC if specific else _GENERIC_LAW_CAP_FALLBACK
    final = specific + generic[:max_generic]

    return final[:max_laws]


def _make_row_id(work_type_code: str, hazard_code: str, seq: int) -> str:
    return f"{work_type_code}_{hazard_code}_{seq:03d}"


def _compute_review_flags_for_row(
    controls: list[dict], laws: list[dict], hazard_score: int, hazard_reason: str
) -> list[str]:
    flags = []
    if len(laws) <= 1 and all(l["law_score"] < _LOW_LAW_SCORE for l in laws):
        flags.append("LOW_LAW_EVIDENCE")
    if controls and all(c.get("control_type") in _PPE_TYPES for c in controls):
        flags.append("CONTROL_ONLY_GENERAL_PPE")
    if hazard_score < _LOW_SCORE_THRESHOLD:
        flags.append("HAZARD_SCORE_LOW")
    if "rule_based_inference" in hazard_reason:
        flags.append("MANUAL_REVIEW_RECOMMENDED")
    return flags


def _compute_response_flags(
    rows_data: list[dict],
    work_type_code: str,
    condition_flags: list[str],
    total_hazard_candidates: int,
    max_hazards: int,
) -> list[str]:
    flags = []

    recommended = _RECOMMENDED_FLAGS.get(work_type_code, [])
    if recommended and not any(f in condition_flags for f in recommended):
        flags.append("CONDITION_FLAG_MISSING")

    if total_hazard_candidates > max_hazards:
        flags.append("MAX_ROWS_REACHED")

    seen_controls: set[str] = set()
    for row in rows_data:
        for c in row.get("controls", []):
            cc = c["control_code"]
            if cc in seen_controls:
                flags.append("DUPLICATE_CONTROL_ACROSS_ROWS")
                return flags
            seen_controls.add(cc)

    return flags


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

class EngineError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def recommend(
    work_type_code: str,
    work_sub_type_code: str,
    work_name: str,
    condition_flags: list[str],
    max_hazards: int,
    max_controls_per_hazard: int,
    max_laws_per_row: int,
    include_law_evidence: bool,
    include_scores: bool,
    preferred_hazard_codes: list[str],
    excluded_hazard_codes: list[str],
    preferred_control_codes: list[str],
) -> dict:
    # Step 1 — worktype 검증
    wt_lookup = _work_types()
    if work_type_code not in wt_lookup:
        raise EngineError(f"work_type_code '{work_type_code}' not found", status_code=404)
    if not work_name:
        work_name = wt_lookup[work_type_code].get("name_ko", work_type_code)

    # Step 2-3 — hazard 후보 수집 및 정렬
    hz_lookup = _hazards()
    excluded_set = set(excluded_hazard_codes)
    hazard_candidates = []
    seen_codes: set[str] = set()
    for m in _hazard_map().get(work_type_code, []):
        hcode = m["hazard_code"]
        if hcode in excluded_set or hcode in seen_codes:
            continue
        seen_codes.add(hcode)
        score = _apply_condition_bonus(_hazard_base_score(m), hcode, condition_flags)
        hazard_candidates.append({
            "hazard_code": hcode,
            "hazard_name": hz_lookup.get(hcode, {}).get("name_ko", hcode),
            "hazard_score": score,
            "hazard_reason": m.get("source", "work_hazards_map"),
            "_preferred": hcode in preferred_hazard_codes,
        })

    hazard_candidates.sort(key=lambda x: (not x["_preferred"], -x["hazard_score"]))
    total_candidates = len(hazard_candidates)
    hazard_candidates = hazard_candidates[:max_hazards]

    if not hazard_candidates:
        hinfo = hz_lookup.get("FALL", {})
        hazard_candidates = [{
            "hazard_code": "FALL",
            "hazard_name": hinfo.get("name_ko", "FALL"),
            "hazard_score": _RULE_BASE,
            "hazard_reason": "rule_based_inference",
            "_preferred": False,
        }]
        total_candidates = 1

    # Step 4-7 — 각 hazard별 row 조립
    ctrl_by_hz = _controls_by_hazard()
    preferred_ctrl_set = set(preferred_control_codes)

    def _ctrl_sort_key(c: dict) -> tuple:
        return (c["control_code"] not in preferred_ctrl_set, -_control_score(c))

    rows_data: list[dict] = []
    for seq, hz in enumerate(hazard_candidates, start=1):
        hcode = hz["hazard_code"]
        ctrls = sorted(ctrl_by_hz.get(hcode, []), key=_ctrl_sort_key)[:max_controls_per_hazard]

        control_list = [{
            "control_code": c["control_code"],
            "control_name": c["control_name"],
            "control_score": _control_score(c) if include_scores else 0,
            "reason": f"{c.get('control_type', 'ppe')} priority={c.get('priority', 2)}",
            "control_type": c.get("control_type", "ppe"),
        } for c in ctrls]

        law_list = _merge_law_evidence(
            work_type_code, hcode,
            [c["control_code"] for c in ctrls],
            max_laws_per_row, include_law_evidence,
        )
        if not include_scores:
            for lw in law_list:
                lw["law_score"] = 0.0

        row_flags = _compute_review_flags_for_row(
            ctrls, law_list, hz["hazard_score"], hz["hazard_reason"]
        )
        rows_data.append({
            "row_id": _make_row_id(work_type_code, hcode, seq),
            "hazard": {
                "hazard_code": hcode,
                "hazard_name": hz["hazard_name"],
                "hazard_score": hz["hazard_score"] if include_scores else 0,
                "hazard_reason": hz["hazard_reason"],
            },
            "controls": control_list,
            "laws": law_list,
            "editable": {
                "hazard_text": hz["hazard_name"],
                "control_texts": [c["control_name"] for c in ctrls],
                "memo": "",
            },
            "row_flags": row_flags,
        })

    return {
        "request_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "work": {
            "work_type_code": work_type_code,
            "work_sub_type_code": work_sub_type_code or None,
            "work_name": work_name,
        },
        "summary": {
            "hazard_count": len(rows_data),
            "control_count": sum(len(r["controls"]) for r in rows_data),
            "law_count": sum(len(r["laws"]) for r in rows_data),
        },
        "rows": rows_data,
        "review_flags": _compute_response_flags(
            rows_data, work_type_code, condition_flags, total_candidates, max_hazards
        ),
        "engine_meta": {
            "pipeline_version": _PIPELINE_VERSION,
            "sources_used": _SOURCES_USED,
        },
    }


def recalculate(
    work_type_code: str,
    work_sub_type_code: str,
    condition_flags: list[str],
    rows_input: list[dict],
    rebuild_law_evidence: bool,
    rescore_controls: bool,
    max_laws_per_row: int = 3,  # must match recommend default (RecommendOptions.max_laws_per_row)
) -> dict:
    """사용자 수정 row 기반 control/law 재조립. hazard row 구조 유지."""
    wt_lookup = _work_types()
    if work_type_code not in wt_lookup:
        raise EngineError(f"work_type_code '{work_type_code}' not found", status_code=404)

    ctrl_lookup = _controls_by_code()
    ctrl_by_hz = _controls_by_hazard()
    hz_lookup = _hazards()
    hz_map = _hazard_map()  # 루프 진입 전 1회만 조회

    rows_data: list[dict] = []
    for row_in in rows_input:
        row_id = row_in["row_id"]
        hcode = row_in["hazard_code"]
        selected_codes = row_in.get("selected_control_codes", [])
        custom_texts = row_in.get("custom_control_texts", [])
        excluded_law_ids = set(row_in.get("excluded_law_ids", []))
        memo = row_in.get("memo", "")

        if not row_id.startswith(f"{work_type_code}_{hcode}_"):
            raise EngineError(
                f"row_id '{row_id}' does not match work_type_code='{work_type_code}' "
                f"and hazard_code='{hcode}'",
                status_code=422,
            )

        hz_name = hz_lookup.get(hcode, {}).get("name_ko", hcode)

        unknown_ctrl_codes: list[str] = []
        control_list = []
        if selected_codes:
            for cc in selected_codes:
                ctrl = ctrl_lookup.get(cc)
                if ctrl is None:
                    unknown_ctrl_codes.append(cc)
                    continue
                control_list.append({
                    "control_code": cc,
                    "control_name": ctrl["control_name"],
                    "control_score": _control_score(ctrl) if rescore_controls else 0,
                    "reason": f"{ctrl.get('control_type', 'ppe')} priority={ctrl.get('priority', 2)}",
                    "control_type": ctrl.get("control_type", "ppe"),
                })
        else:
            for c in ctrl_by_hz.get(hcode, [])[:3]:
                control_list.append({
                    "control_code": c["control_code"],
                    "control_name": c["control_name"],
                    "control_score": _control_score(c) if rescore_controls else 0,
                    "reason": f"{c.get('control_type', 'ppe')} priority={c.get('priority', 2)}",
                    "control_type": c.get("control_type", "ppe"),
                })

        if rebuild_law_evidence:
            law_list = _merge_law_evidence(
                work_type_code, hcode,
                [c["control_code"] for c in control_list],
                max_laws_per_row, include_law_evidence=True,
            )
            law_list = [lw for lw in law_list if lw["law_id"] not in excluded_law_ids]
        else:
            law_list = []

        hz_mapping = next(
            (m for m in hz_map.get(work_type_code, []) if m["hazard_code"] == hcode), None
        )
        if hz_mapping:
            hz_score = _apply_condition_bonus(
                _hazard_base_score(hz_mapping), hcode, condition_flags
            )
            hz_reason = hz_mapping.get("source", "work_hazards_map")
        else:
            hz_score = _RULE_BASE
            hz_reason = "rule_based_inference"

        row_flags = _compute_review_flags_for_row(control_list, law_list, hz_score, hz_reason)
        if unknown_ctrl_codes and "MANUAL_REVIEW_RECOMMENDED" not in row_flags:
            row_flags.append("MANUAL_REVIEW_RECOMMENDED")

        rows_data.append({
            "row_id": row_id,
            "hazard": {
                "hazard_code": hcode,
                "hazard_name": hz_name,
                "hazard_score": hz_score,
                "hazard_reason": hz_reason,
            },
            "controls": control_list,
            "laws": law_list,
            "editable": {
                "hazard_text": hz_name,
                "control_texts": custom_texts or [c["control_name"] for c in control_list],
                "memo": memo,
            },
            "row_flags": row_flags,
        })

    return {
        "request_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "work": {
            "work_type_code": work_type_code,
            "work_sub_type_code": work_sub_type_code or None,
            "work_name": wt_lookup[work_type_code].get("name_ko", work_type_code),
        },
        "summary": {
            "hazard_count": len(rows_data),
            "control_count": sum(len(r["controls"]) for r in rows_data),
            "law_count": sum(len(r["laws"]) for r in rows_data),
        },
        "rows": rows_data,
        "review_flags": _compute_response_flags(
            rows_data, work_type_code, condition_flags, len(rows_data), len(rows_data)
        ),
        "engine_meta": {
            "pipeline_version": _PIPELINE_VERSION,
            "sources_used": _SOURCES_USED,
        },
    }

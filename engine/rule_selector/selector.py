"""Rule DB 조회 및 평가 — 메인 진입점."""
import json
import logging
from pathlib import Path
from typing import List, Dict

from .schema import RuleSelectorInput, RuleSelectorOutput, RuleResultItem

logger = logging.getLogger(__name__)

_RULES_FILE = Path(__file__).resolve().parents[2] / "data/risk_db/rules/safety_rules.json"

# needs_review 확정 금지 rule_id — 이 목록은 항상 needs_review 상태 유지
_LOCKED_NEEDS_REVIEW = frozenset({"CERT-AWP-001", "WC-HOTWORK-004", "WC-EXCAVATION-004"})

# rule_type → output 키 매핑
_TYPE_TO_KEY = {
    "education": "education",
    "certification": "certification",
    "inspection": "inspection",
    "work_condition": "work_conditions",
}


def _load_rules() -> List[dict]:
    data = json.loads(_RULES_FILE.read_text(encoding="utf-8"))
    return data.get("rules", [])


def _condition_match(rule: dict, subject_codes: set, conditions: dict) -> bool:
    """
    subject_codes: equipment + work_types 통합 코드셋.
    조건 매칭: validate_safety_rules.py condition_match 로직 이식.
    """
    sc = rule.get("subject_code", "")

    # subject_code 매칭 — 정확 일치 또는 prefix 허용 (CRANE_SIGNAL 등 파생 코드 포함)
    if subject_codes:
        matched = False
        for inp_sc in subject_codes:
            if sc == inp_sc or sc.startswith(inp_sc + "_") or inp_sc.startswith(sc + "_"):
                matched = True
                break
        if not matched:
            return False

    expr = rule.get("condition_expr", "always")
    if expr == "always":
        return True

    tokens = [t.strip() for t in expr.split("AND")]
    for token in tokens:
        token = token.strip()
        if ">=" in token:
            key, val = token.split(">=", 1)
            key, val = key.strip(), val.strip()
            try:
                threshold = float(val)
                actual = conditions.get(key)
                if actual is None or float(actual) < threshold:
                    return False
            except (ValueError, TypeError):
                return False
        elif "<" in token:
            key, val = token.split("<", 1)
            key, val = key.strip(), val.strip()
            try:
                threshold = float(val)
                actual = conditions.get(key)
                if actual is None or float(actual) >= threshold:
                    return False
            except (ValueError, TypeError):
                return False
        elif "=" in token:
            key, val = token.split("=", 1)
            key, val = key.strip(), val.strip()
            if val.lower() in ("true", "false"):
                expected = val.lower() == "true"
                if conditions.get(key) != expected:
                    return False
            else:
                if conditions.get(key) != val:
                    return False

    return True


def _evaluate(rule: dict, conditions: dict) -> tuple[str, str]:
    """
    반환: (status, reason)
    - needs_review 잠금 규칙 → "needs_review"
    - rule.needs_review=true  → "needs_review"
    - 조건 값 누락으로 AND 일부 미확인 → "warn"
    - 정상 매칭               → "pass"
    """
    rule_id = rule.get("rule_id", "")

    if rule_id in _LOCKED_NEEDS_REVIEW:
        # 기존 devlog의 needs_review 사유를 reason에 포함
        reason_map = {
            "CERT-AWP-001": "차량탑재형/자주식 구분·도로주행 여부에 따라 면허 판단이 달라짐 — 현장 확인 필요",
            "WC-HOTWORK-004": "화기작업 허가제는 법적 강제 아닌 KOSHA 권고 — 사업장 규정 의존",
            "WC-EXCAVATION-004": "5m 이상 흙막이 전문검토의 실무 적용 기준 불명확 — 감리/설계자 확인 필요",
        }
        return "needs_review", reason_map[rule_id]

    if rule.get("needs_review"):
        return "needs_review", "rule DB에 needs_review 플래그 설정됨 — 법령 해석 불확실"

    # AND 조건 중 입력값이 없는 키가 있으면 warn
    expr = rule.get("condition_expr", "always")
    if expr != "always":
        tokens = [t.strip() for t in expr.split("AND")]
        missing_keys = []
        for token in tokens:
            for op in (">=", "<", "="):
                if op in token:
                    key = token.split(op, 1)[0].strip()
                    if conditions.get(key) is None:
                        missing_keys.append(key)
                    break
        if missing_keys:
            return "warn", f"조건 값 미제공으로 완전 확인 불가: {', '.join(missing_keys)}"

    return "pass", "조건 충족"


def select_rules(inp: RuleSelectorInput) -> RuleSelectorOutput:
    """
    equipment + work_types + conditions 입력 → Rule DB 조회 + 평가 결과 반환.
    """
    equipment: List[str] = inp.get("equipment") or []
    work_types: List[str] = inp.get("work_types") or []
    conditions: Dict = inp.get("conditions") or {}

    subject_codes = set(equipment) | set(work_types)

    rules = _load_rules()

    matched: List[RuleResultItem] = []
    for rule in rules:
        if not _condition_match(rule, subject_codes, conditions):
            continue
        status, reason = _evaluate(rule, conditions)
        item: RuleResultItem = {
            "rule_id": rule["rule_id"],
            "rule_type": rule["rule_type"],
            "subject_code": rule.get("subject_code", ""),
            "obligation": rule.get("obligation", ""),
            "obligation_type": rule.get("obligation_type", ""),
            "source_ref": rule.get("source_ref", ""),
            "priority": rule.get("priority", 9),
            "status": status,
            "reason": reason,
            "needs_review": bool(rule.get("needs_review", False)),
        }
        matched.append(item)

    # priority ASC, rule_id ASC 정렬
    matched.sort(key=lambda x: (x["priority"], x["rule_id"]))

    # category별 분리
    by_type: Dict[str, List[RuleResultItem]] = {
        "education": [],
        "certification": [],
        "inspection": [],
        "work_conditions": [],
    }
    for item in matched:
        key = _TYPE_TO_KEY.get(item["rule_type"])
        if key:
            by_type[key].append(item)

    # summary 집계
    summary = {"pass": 0, "warn": 0, "fail": 0, "needs_review": 0}
    for item in matched:
        s = item["status"]
        if s in summary:
            summary[s] += 1
        else:
            summary["fail"] += 1

    return RuleSelectorOutput(
        input_echo={
            "equipment": equipment,
            "work_types": work_types,
            "conditions": conditions,
        },
        matched_rules=matched,
        education=by_type["education"],
        certification=by_type["certification"],
        inspection=by_type["inspection"],
        work_conditions=by_type["work_conditions"],
        summary=summary,
    )

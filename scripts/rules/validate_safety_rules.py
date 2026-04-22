"""
safety_rules.json 샘플 시나리오 검증 스크립트.
시나리오별 조건 입력 → 매칭 규칙 출력 → PASS/WARN/FAIL 판정.
"""
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_FILE = ROOT / "data/risk_db/rules/safety_rules.json"

SCENARIOS = [
    {
        "name": "고소작업대 작업 (차량탑재형, 2m 이상)",
        "conditions": {"subject_code": "AWP", "work_height": 2, "awp_type": "vehicle_mounted"},
        "expected_types": ["education", "certification", "inspection", "work_condition"],
        "min_rules": 4,
    },
    {
        "name": "이동식 크레인 양중 (5톤)",
        "conditions": {
            "subject_code": "CRANE",
            "crane_lift": True,
            "crane_capacity_ton": 5,
        },
        "expected_types": ["education", "certification", "inspection", "work_condition"],
        "min_rules": 6,
    },
    {
        "name": "가스 용접 작업",
        "conditions": {"subject_code": "WELDING", "welding_type": "gas"},
        "expected_types": ["education", "work_condition"],
        "min_rules": 3,
    },
    {
        "name": "굴착 작업 (3m)",
        "conditions": {"subject_code": "EXCAVATION", "excavation_depth": 3},
        "expected_types": ["education", "work_condition"],
        "min_rules": 4,
    },
    {
        "name": "밀폐공간 작업",
        "conditions": {"subject_code": "CONFINED_SPACE", "confined_space": True},
        "expected_types": ["education", "work_condition"],
        "min_rules": 5,
    },
    {
        "name": "인화성 물질 주변 화기작업",
        "conditions": {
            "subject_code": "HOT_WORK",
            "hot_work": True,
            "flammable_material": True,
            "flammable_gas": True,
        },
        "expected_types": ["education", "work_condition"],
        "min_rules": 4,
    },
    {
        "name": "지게차 운전",
        "conditions": {"subject_code": "FORKLIFT"},
        "expected_types": ["education", "certification", "inspection"],
        "min_rules": 3,
    },
    {
        "name": "굴착기 운전 (0.5톤)",
        "conditions": {"subject_code": "EXCAVATOR", "excavator_weight_ton": 0.5},
        "expected_types": ["education", "certification", "inspection"],
        "min_rules": 3,
    },
]


def load_rules() -> list[dict]:
    data = json.loads(RULES_FILE.read_text(encoding="utf-8"))
    return data.get("rules", [])


def condition_match(rule: dict, conditions: dict) -> bool:
    """rule.condition_expr 를 조건 dict 에 대해 간이 평가."""
    sc = rule.get("subject_code", "")
    input_sc = conditions.get("subject_code", "")

    # subject_code 매칭: 입력 subject와 같거나 prefix 포함
    if input_sc and sc not in (input_sc, input_sc + "_GAS", input_sc + "_SIGNAL"):
        # 양방향 prefix 허용
        if not (sc.startswith(input_sc) or input_sc.startswith(sc)):
            return False

    expr = rule.get("condition_expr", "always")
    if expr == "always":
        return True

    # 조건 토큰 파싱 (단순 AND 처리)
    tokens = [t.strip() for t in expr.split("AND")]
    for token in tokens:
        token = token.strip()
        if "=" in token and ">=" not in token and "<=" not in token:
            key, val = token.split("=", 1)
            key = key.strip()
            val = val.strip()
            if val.lower() in ("true", "false"):
                bool_val = val.lower() == "true"
                if conditions.get(key) != bool_val:
                    return False
            else:
                # 문자열 값 비교
                if conditions.get(key) != val:
                    return False
        elif ">=" in token:
            key, val = token.split(">=", 1)
            key = key.strip()
            try:
                threshold = float(val.strip())
                if float(conditions.get(key, 0)) < threshold:
                    return False
            except ValueError:
                pass
        elif "<" in token and ">=" not in token:
            key, val = token.split("<", 1)
            key = key.strip()
            try:
                threshold = float(val.strip())
                if float(conditions.get(key, 9999)) >= threshold:
                    return False
            except ValueError:
                pass

    return True


@dataclass
class ScenarioResult:
    name: str
    matched_rules: list[dict] = field(default_factory=list)
    matched_types: set = field(default_factory=set)
    verdict: str = "FAIL"
    warnings: list[str] = field(default_factory=list)


def run_scenario(scenario: dict, rules: list[dict]) -> ScenarioResult:
    result = ScenarioResult(name=scenario["name"])

    for rule in rules:
        if condition_match(rule, scenario["conditions"]):
            result.matched_rules.append(rule)
            result.matched_types.add(rule["rule_type"])

    expected = set(scenario.get("expected_types", []))
    min_rules = scenario.get("min_rules", 1)

    missing_types = expected - result.matched_types
    rule_count = len(result.matched_rules)

    if missing_types:
        result.warnings.append(f"누락 rule_type: {', '.join(missing_types)}")
    if rule_count < min_rules:
        result.warnings.append(f"rule 수 부족: {rule_count} < {min_rules}(기대)")

    reviews = [r["rule_id"] for r in result.matched_rules if r.get("needs_review")]
    if reviews:
        result.warnings.append(f"[review] {', '.join(reviews)}")

    if not missing_types and rule_count >= min_rules:
        result.verdict = "PASS" if not reviews else "WARN"
    else:
        result.verdict = "FAIL"

    return result


def print_result(res: ScenarioResult) -> None:
    icon = {"PASS": "[OK]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[res.verdict]
    print(f"\n{icon} [{res.verdict}] {res.name}")
    print(f"   매칭 규칙: {len(res.matched_rules)}건 | 유형: {sorted(res.matched_types)}")
    for rule in res.matched_rules:
        review_flag = " [REVIEW]" if rule.get("needs_review") else ""
        print(f"   - {rule['rule_id']} ({rule['obligation_type']}){review_flag}")
        print(f"     → {rule['obligation'][:70]}{'...' if len(rule['obligation']) > 70 else ''}")
    if res.warnings:
        for w in res.warnings:
            print(f"   [!] {w}")


def main() -> int:
    rules = load_rules()
    print(f"규칙 총 {len(rules)}건 로드")
    print("=" * 60)
    print("샘플 시나리오 검증")
    print("=" * 60)

    results = [run_scenario(s, rules) for s in SCENARIOS]
    for r in results:
        print_result(r)

    totals = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for r in results:
        totals[r.verdict] += 1

    print("\n" + "=" * 60)
    print(f"결과: PASS={totals['PASS']} / WARN={totals['WARN']} / FAIL={totals['FAIL']}")
    pass_rate = (totals["PASS"] + totals["WARN"]) / len(results) * 100
    print(f"PASS율(WARN 포함): {pass_rate:.0f}%")

    if totals["FAIL"] > 0:
        print("최종 판정: FAIL")
        return 1
    if totals["WARN"] > 0:
        print("최종 판정: WARN")
        return 0
    print("최종 판정: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

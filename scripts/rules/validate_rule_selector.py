"""
19단계 — Rule Selector 샘플 시나리오 검증.
입력 JSON → 매칭 규칙 → 평가 결과를 시나리오별로 출력.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.rule_selector import select_rules

SCENARIOS = [
    {
        "name": "S01 — 고소작업대 (차량탑재형)",
        "input": {
            "equipment": ["AWP"],
            "work_types": [],
            "conditions": {"awp_type": "vehicle_mounted"},
        },
        "expect_min": 4,
        "expect_types": {"education", "certification", "inspection"},
        "expect_needs_review_ids": {"CERT-AWP-001"},
    },
    {
        "name": "S02 — 이동식 크레인 양중 (5톤)",
        "input": {
            "equipment": ["CRANE"],
            "work_types": [],
            "conditions": {"crane_lift": True, "crane_capacity_ton": 5},
        },
        "expect_min": 6,
        "expect_types": {"education", "certification", "inspection", "work_condition"},
        "expect_needs_review_ids": set(),
    },
    {
        "name": "S03 — 화기작업 (인화성 물질 있음)",
        "input": {
            "equipment": [],
            "work_types": ["HOT_WORK", "WELDING"],
            "conditions": {
                "hot_work": True,
                "flammable_material": True,
                "flammable_gas": True,
            },
        },
        "expect_min": 4,
        "expect_types": {"education", "work_condition"},
        "expect_needs_review_ids": {"WC-HOTWORK-004"},
    },
    {
        "name": "S04 — 굴착 작업 (3m)",
        "input": {
            "equipment": [],
            "work_types": ["EXCAVATION"],
            "conditions": {"excavation_depth": 3},
        },
        "expect_min": 4,
        "expect_types": {"education", "work_condition"},
        "expect_needs_review_ids": set(),
    },
    {
        "name": "S05 — 밀폐공간 작업",
        "input": {
            "equipment": [],
            "work_types": ["CONFINED_SPACE"],
            "conditions": {"confined_space": True},
        },
        "expect_min": 5,
        "expect_types": {"education", "work_condition"},
        "expect_needs_review_ids": set(),
    },
    {
        "name": "S06 — 지게차 작업",
        "input": {
            "equipment": ["FORKLIFT"],
            "work_types": [],
            "conditions": {},
        },
        "expect_min": 3,
        "expect_types": {"education", "certification", "inspection"},
        "expect_needs_review_ids": set(),
    },
    {
        "name": "S07 — 굴착기 (0.5톤)",
        "input": {
            "equipment": ["EXCAVATOR"],
            "work_types": [],
            "conditions": {"excavator_weight_ton": 0.5},
        },
        "expect_min": 3,
        "expect_types": {"education", "certification", "inspection"},
        "expect_needs_review_ids": set(),
    },
    {
        "name": "S08 — 복합: 크레인 5톤 + 밀폐공간",
        "input": {
            "equipment": ["CRANE"],
            "work_types": ["CONFINED_SPACE"],
            "conditions": {
                "crane_capacity_ton": 5,
                "crane_lift": True,
                "confined_space": True,
            },
        },
        "expect_min": 8,
        "expect_types": {"education", "certification", "inspection", "work_condition"},
        "expect_needs_review_ids": set(),
    },
    {
        "name": "S09 — 복합: 굴착기 + 굴착 6m + 화기작업",
        "input": {
            "equipment": ["EXCAVATOR"],
            "work_types": ["EXCAVATION", "HOT_WORK"],
            "conditions": {
                "excavator_weight_ton": 2,
                "excavation_depth": 6,
                "hot_work": True,
                "flammable_material": False,
            },
        },
        "expect_min": 7,
        "expect_types": {"education", "certification", "inspection", "work_condition"},
        "expect_needs_review_ids": {"WC-HOTWORK-004", "WC-EXCAVATION-004"},
    },
    {
        "name": "S10 — 전기 작업 (220V)",
        "input": {
            "equipment": [],
            "work_types": ["ELECTRIC_WORK"],
            "conditions": {"electric_voltage": 220},
        },
        "expect_min": 1,
        "expect_types": {"education"},
        "expect_needs_review_ids": set(),
    },
]


def _status_icon(s: str) -> str:
    return {"pass": "✓", "warn": "△", "fail": "✗", "needs_review": "?"}.get(s, "?")


def run_scenario(scenario: dict) -> bool:
    """반환: True=PASS, False=FAIL"""
    name = scenario["name"]
    inp = scenario["input"]
    result = select_rules(inp)

    actual_types = {item["rule_type"] for item in result["matched_rules"]}
    # work_condition → work_condition (rule_type 값 그대로 비교)
    expected_types = scenario["expect_types"]
    missing_types = expected_types - actual_types
    rule_count = len(result["matched_rules"])
    actual_nr_ids = {
        item["rule_id"] for item in result["matched_rules"] if item["status"] == "needs_review"
    }
    expected_nr_ids = scenario["expect_needs_review_ids"]
    missing_nr = expected_nr_ids - actual_nr_ids

    verdict_ok = (
        rule_count >= scenario["expect_min"]
        and not missing_types
        and not missing_nr
    )

    icon = "PASS" if verdict_ok else "FAIL"
    print(f"\n[{icon}] {name}")
    print(f"  매칭: {rule_count}건 | summary: {result['summary']}")

    for cat in ("education", "certification", "inspection", "work_conditions"):
        items = result[cat]
        if not items:
            continue
        print(f"  [{cat}]")
        for item in items:
            si = _status_icon(item["status"])
            print(f"    {si} {item['rule_id']} ({item['status']}) — {item['obligation'][:55]}{'…' if len(item['obligation']) > 55 else ''}")
            if item["status"] in ("warn", "needs_review"):
                print(f"        reason: {item['reason']}")

    if missing_types:
        print(f"  [!] 누락 rule_type: {missing_types}")
    if rule_count < scenario["expect_min"]:
        print(f"  [!] rule 수 부족: {rule_count} < {scenario['expect_min']}")
    if missing_nr:
        print(f"  [!] needs_review 누락 rule_id: {missing_nr}")

    return verdict_ok


def main() -> int:
    print("=" * 70)
    print("19단계 — Rule Selector 샘플 시나리오 검증")
    print("=" * 70)

    results = [run_scenario(s) for s in SCENARIOS]

    pass_count = sum(results)
    fail_count = len(results) - pass_count

    print("\n" + "=" * 70)
    print(f"결과: PASS={pass_count} / FAIL={fail_count} / 총={len(results)}")

    if fail_count == 0:
        print("최종 판정: PASS")
        return 0
    print("최종 판정: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())

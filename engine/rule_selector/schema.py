"""입출력 스키마 정의 — Rule DB 기반 안전 의무 선택기."""
from typing import TypedDict, List, Dict, Literal, Optional

# ── 입력 ─────────────────────────────────────────────────────────────────────

class RuleSelectorInput(TypedDict, total=False):
    """
    최소 입력 필드: equipment, work_types, conditions.

    equipment   : Rule DB subject_code 목록 (e.g. ["AWP", "CRANE"])
    work_types  : 작업 유형 목록       (e.g. ["HOT_WORK", "CONFINED_SPACE"])
    conditions  : Rule DB condition_expr 판정에 쓰이는 key-value 쌍
                  (e.g. {"crane_capacity_ton": 5, "confined_space": True})
    """
    equipment: List[str]    # required — 사용 장비 코드 목록
    work_types: List[str]   # required — 작업 유형 코드 목록
    conditions: Dict        # required — 조건 값 (수치/bool/문자열)


# ── 출력 — 개별 규칙 항목 ──────────────────────────────────────────────────

RuleStatus = Literal["pass", "warn", "fail", "needs_review"]

class RuleResultItem(TypedDict):
    rule_id: str
    rule_type: str          # education | certification | inspection | work_condition
    subject_code: str
    obligation: str
    obligation_type: str
    source_ref: str
    priority: int
    status: RuleStatus
    reason: str             # 판정 이유 (warn/needs_review 시 필수)
    needs_review: bool      # 원본 플래그


# ── 출력 — summary ────────────────────────────────────────────────────────

class SummaryCount(TypedDict):
    pass_: int              # JSON 직렬화 시 "pass" 키로 출력
    warn: int
    fail: int
    needs_review: int


# ── 출력 — 최종 결과 ──────────────────────────────────────────────────────

class RuleSelectorOutput(TypedDict):
    input_echo: Dict                    # 입력 그대로 반환 (디버깅용)
    matched_rules: List[RuleResultItem] # 전체 매칭 규칙 (순서: priority ASC, rule_id ASC)
    education: List[RuleResultItem]
    certification: List[RuleResultItem]
    inspection: List[RuleResultItem]
    work_conditions: List[RuleResultItem]
    summary: Dict[str, int]            # {"pass": N, "warn": N, "fail": N, "needs_review": N}


# ── 입력 예시 (문서/테스트용) ─────────────────────────────────────────────

EXAMPLE_INPUTS = [
    {
        "_desc": "고소작업대 (차량탑재형)",
        "equipment": ["AWP"],
        "work_types": [],
        "conditions": {
            "awp_type": "vehicle_mounted",
        },
    },
    {
        "_desc": "이동식 크레인 5톤 양중 + 밀폐공간",
        "equipment": ["CRANE"],
        "work_types": ["CONFINED_SPACE"],
        "conditions": {
            "crane_lift": True,
            "crane_capacity_ton": 5,
            "confined_space": True,
        },
    },
    {
        "_desc": "굴착기 0.5톤 + 굴착 3m + 화기작업",
        "equipment": ["EXCAVATOR"],
        "work_types": ["EXCAVATION", "HOT_WORK"],
        "conditions": {
            "excavator_weight_ton": 0.5,
            "excavation_depth": 3,
            "hot_work": True,
            "flammable_material": False,
        },
    },
]

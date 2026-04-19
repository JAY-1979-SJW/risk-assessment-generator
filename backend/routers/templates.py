import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import APIRouter
from db import risk_level

router = APIRouter(prefix="/templates", tags=["templates"])

POLICIES = {
    "공통": "우리 사업장은 근로자의 안전과 건강을 최우선으로 생각하며, 모든 작업에서 위험요인을 사전에 파악하고 제거하기 위해 지속적으로 노력합니다.",
    "건설업": "당사는 건설현장의 모든 작업자가 안전하게 작업할 수 있도록 체계적인 위험성평가를 실시하고, 위험요인을 사전에 제거·감소시켜 무재해 현장을 실현합니다.",
    "소방시설공사업": "당사는 소방시설 공사 전 과정에서 근로자 안전을 최우선으로 하며, 작업별 위험요인을 체계적으로 평가하여 안전한 작업환경을 조성합니다.",
    "전기공사업": "당사는 전기공사 시 감전, 추락, 화재 등 위험요인에 대한 철저한 위험성평가를 통해 근로자의 안전·보건을 확보합니다.",
    "제조업": "당사는 제조 공정의 모든 단계에서 기계·설비 위험, 화학물질 노출 등 유해위험요인을 파악하고 적절한 감소대책을 시행합니다.",
    "서비스업": "당사는 서비스 업무 수행 시 발생할 수 있는 모든 위험요인을 사전에 평가하고 개선하여 쾌적하고 안전한 근무환경을 조성합니다.",
}

GOALS = {
    "공통": "1. 위험성평가 연 1회 이상 정기 실시\n2. 신규 작업 및 변경 작업 시 수시 위험성평가 실시\n3. 평가 결과에 따른 위험감소 대책 100% 이행\n4. 전 근로자 위험성평가 교육 실시",
    "건설업": "1. 착공 전 초기 위험성평가 실시\n2. 공정 변경 시 수시 위험성평가 실시\n3. 고위험 작업(고소·굴착·중장비) 별도 안전대책 수립\n4. 협력업체 포함 전 근로자 안전교육 실시",
    "소방시설공사업": "1. 공종별 위험성평가 실시 및 안전대책 수립\n2. 고소작업·밀폐공간 특별 안전조치 이행\n3. 화재·폭발 위험요인 사전 제거\n4. 전 근로자 안전보건교육 연 2회 이상 실시",
    "전기공사업": "1. 활선 작업 시 절연보호구 100% 착용\n2. 정전 작업 전 잠금/표지(LOTO) 절차 준수\n3. 전기화재 예방 정기점검 실시\n4. 감전사고 예방 전문교육 실시",
    "제조업": "1. 기계·설비 정기 안전검사 실시\n2. 화학물질 취급 안전보건 수칙 준수\n3. 공정별 위험요인 지속 발굴 및 개선\n4. 아차사고 보고제도 운영",
    "서비스업": "1. 직무스트레스 예방 프로그램 운영\n2. 근골격계질환 예방을 위한 작업환경 개선\n3. 감정노동 근로자 보호 대책 수립\n4. 전 근로자 건강검진 100% 실시",
}

RISK_CRITERIA = {
    "method": "빈도·강도법",
    "matrix": "3x3",
    "possibility": {
        "3": {"label": "상", "description": "발생가능성이 높음. 일상적으로 장시간 이루어지는 작업에 수반하는 것으로 피하기 어려운 것"},
        "2": {"label": "중", "description": "발생가능성이 있음. 일상적인 작업에 수반하는 것으로 피할 수 있는 것"},
        "1": {"label": "하", "description": "발생가능성이 낮음. 비정상적인 작업에 수반하는 것으로 피할 수 있는 것"},
    },
    "severity": {
        "3": {"label": "대", "description": "사망 또는 영구적 장해 유발 (입원치료 이상)"},
        "2": {"label": "중", "description": "부상 또는 일시적 장해 유발 (외래치료)"},
        "1": {"label": "소", "description": "경미한 부상 (응급처치)"},
    },
    "risk_level": {
        "낮음": {"range": "1~2", "acceptable": True,  "action": "현재의 안전보건 관리 유지"},
        "보통": {"range": "3~4", "acceptable": False, "action": "합리적으로 실행 가능한 감소대책 수립"},
        "높음": {"range": "6~9", "acceptable": False, "action": "즉시 작업 중지 후 개선 조치"},
    }
}


@router.get("/categories")
def get_categories():
    return {"categories": list(POLICIES.keys())}


@router.get("/policy/{category}")
def get_policy(category: str):
    return {"policy": POLICIES.get(category, POLICIES["공통"])}


@router.get("/goal/{category}")
def get_goal(category: str):
    return {"goal": GOALS.get(category, GOALS["공통"])}


@router.get("/risk-criteria")
def get_risk_criteria():
    return RISK_CRITERIA

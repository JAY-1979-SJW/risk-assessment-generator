# -*- coding: utf-8 -*-
"""
KRAS 표준 위험성평가표 엑셀 출력 테스트
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from core.data_manager import DataManager
from export.excel_exporter import ExcelExporter


def create_test_data():
    """테스트 데이터 생성"""
    dm = DataManager()

    # 회사 기본정보
    dm.company_info = {
        "company_name": "(주)테스트소방설비",
        "site_name": "OO빌딩 소방시설공사",
        "business_type": "소방시설공사업",
        "ceo_name": "홍길동",
        "address": "서울특별시 강남구 테헤란로 123, 456호",
        "eval_date": "2025-01-14",
        "eval_type": "정기평가",
        "safety_policy": """1. 우리 회사는 모든 근로자의 안전과 건강을 최우선으로 합니다.
2. 산업재해 예방을 위해 위험성평가를 철저히 실시합니다.
3. 안전보건 법령을 준수하고 지속적인 개선을 추진합니다.
4. 모든 근로자는 안전수칙을 준수하고 상호 협력합니다.""",
        "safety_goal": """1. 산업재해 발생률 ZERO 달성
2. 위험성평가 실시율 100%
3. 안전교육 이수율 100%
4. 안전점검 정상화율 100%"""
    }

    # 조직 구성
    dm.organization = {
        "members": [
            {"position": "대표이사", "name": "홍길동", "role": "총괄관리", "responsibility": "위험성평가 총괄책임, 안전보건방침 결정, 예산 승인"},
            {"position": "현장소장", "name": "김철수", "role": "실무책임", "responsibility": "위험성평가 실시 총괄, 개선대책 수립 및 이행 확인"},
            {"position": "안전관리자", "name": "이영희", "role": "안전관리", "responsibility": "위험성평가 실무, 안전교육 실시, 위험요인 점검"},
            {"position": "공사반장", "name": "박민수", "role": "현장감독", "responsibility": "작업자 지휘·감독, 위험요인 발굴 및 보고"},
            {"position": "근로자대표", "name": "정수진", "role": "근로자대표", "responsibility": "위험성평가 참여, 근로자 의견 수렴 및 전달"},
        ]
    }

    # 회의 정보
    dm.meeting = {
        "date": "2025-01-14",
        "time_start": "09:00",
        "time_end": "10:30",
        "location": "현장 사무실 회의실",
        "content": """1. 위험성평가 개요 및 실시 목적 설명
2. 금일 작업 공정별 유해위험요인 파악
3. 위험성 추정 및 결정
4. 위험성 감소대책 논의
5. 담당자 및 개선일정 확정
6. 질의응답 및 근로자 의견 수렴""",
        "attendees": [
            {"department": "본사", "position": "대표이사", "name": "홍길동"},
            {"department": "현장", "position": "현장소장", "name": "김철수"},
            {"department": "현장", "position": "안전관리자", "name": "이영희"},
            {"department": "현장", "position": "공사반장", "name": "박민수"},
            {"department": "현장", "position": "근로자대표", "name": "정수진"},
            {"department": "현장", "position": "전기기사", "name": "최동훈"},
        ]
    }

    # 위험성평가 데이터
    dm.assessments = [
        {
            "process": "소화배관 설치",
            "sub_work": "천장 배관 고정",
            "risk_category": "떨어짐",
            "risk_detail": "고소작업",
            "risk_situation": "사다리 작업 중 균형을 잃어 추락할 수 있음",
            "legal_basis": "산안법 제38조",
            "current_measures": "안전대 착용, 사다리 고정",
            "possibility": 2,
            "severity": 3,
            "current_risk": 6,
            "current_risk_level": "높음",
            "reduction_measures": "이동식 작업대 사용, 2인 1조 작업, 안전모 착용",
            "after_risk": 2,
            "after_risk_level": "낮음",
            "manager": "박민수",
            "due_date": "2025-01-15",
            "complete_date": ""
        },
        {
            "process": "소화배관 설치",
            "sub_work": "배관 용접",
            "risk_category": "화재·폭발",
            "risk_detail": "용접작업",
            "risk_situation": "용접 불티로 인해 주변 가연물에 화재 발생 가능",
            "legal_basis": "산안법 제39조",
            "current_measures": "소화기 비치, 용접포 설치",
            "possibility": 2,
            "severity": 2,
            "current_risk": 4,
            "current_risk_level": "보통",
            "reduction_measures": "화기작업허가서 발급, 화재감시자 배치, 주변 정리정돈",
            "after_risk": 1,
            "after_risk_level": "낮음",
            "manager": "이영희",
            "due_date": "2025-01-14",
            "complete_date": "2025-01-14"
        },
        {
            "process": "감지기 설치",
            "sub_work": "천장 감지기 부착",
            "risk_category": "떨어짐",
            "risk_detail": "고소작업",
            "risk_situation": "천장 작업 중 발을 헛디뎌 추락할 수 있음",
            "legal_basis": "산안법 제38조",
            "current_measures": "안전대 착용",
            "possibility": 2,
            "severity": 2,
            "current_risk": 4,
            "current_risk_level": "보통",
            "reduction_measures": "고소작업대 사용, 안전난간 설치",
            "after_risk": 1,
            "after_risk_level": "낮음",
            "manager": "박민수",
            "due_date": "2025-01-16",
            "complete_date": ""
        },
        {
            "process": "전선관 배선",
            "sub_work": "전선 인입",
            "risk_category": "감전",
            "risk_detail": "전기작업",
            "risk_situation": "활선 접촉으로 감전될 수 있음",
            "legal_basis": "산안법 제303조",
            "current_measures": "절연장갑 착용, 전원 차단 확인",
            "possibility": 1,
            "severity": 3,
            "current_risk": 3,
            "current_risk_level": "보통",
            "reduction_measures": "작업 전 전원 차단 및 잠금/태그, 검전기 사용",
            "after_risk": 1,
            "after_risk_level": "낮음",
            "manager": "최동훈",
            "due_date": "2025-01-17",
            "complete_date": ""
        },
        {
            "process": "자재 운반",
            "sub_work": "배관 자재 이동",
            "risk_category": "끼임/협착",
            "risk_detail": "중량물 취급",
            "risk_situation": "중량 배관 운반 중 손가락이 끼일 수 있음",
            "legal_basis": "산안법 제39조",
            "current_measures": "안전장갑 착용",
            "possibility": 2,
            "severity": 1,
            "current_risk": 2,
            "current_risk_level": "낮음",
            "reduction_measures": "2인 1조 작업, 안전장갑 착용, 자재 운반 손수레 사용",
            "after_risk": 1,
            "after_risk_level": "낮음",
            "manager": "박민수",
            "due_date": "2025-01-14",
            "complete_date": "2025-01-14"
        },
    ]

    return dm


def main():
    """테스트 실행"""
    print("=" * 60)
    print("KRAS 표준 위험성평가표 엑셀 출력 테스트")
    print("=" * 60)

    # 테스트 데이터 생성
    print("\n[1] 테스트 데이터 생성 중...")
    dm = create_test_data()
    print(f"    - 회사명: {dm.company_info['company_name']}")
    print(f"    - 현장명: {dm.company_info['site_name']}")
    print(f"    - 평가항목: {len(dm.assessments)}건")

    # 엑셀 내보내기
    print("\n[2] 엑셀 파일 생성 중...")
    exporter = ExcelExporter(dm)

    output_path = PROJECT_DIR / "export" / "위험성평가표_표준양식_테스트.xlsx"
    exporter.export(str(output_path))

    print(f"\n[3] 파일 생성 완료!")
    print(f"    경로: {output_path}")

    print("\n" + "=" * 60)
    print("생성된 시트:")
    print("  1. 안전보건방침")
    print("  2. 조직구성")
    print("  3. 위험성기준")
    print("  4. 회의결과")
    print("  5. 위험성평가실시")
    print("=" * 60)


if __name__ == "__main__":
    main()

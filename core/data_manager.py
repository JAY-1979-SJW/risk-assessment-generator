# -*- coding: utf-8 -*-
"""
데이터 관리 모듈
모든 위험성평가 데이터를 중앙 관리
"""

import json
from datetime import datetime
from typing import Dict, List, Any


class DataManager:
    """위험성평가 데이터 중앙 관리 클래스"""

    def __init__(self):
        self.clear()

    def clear(self):
        """모든 데이터 초기화"""
        # 기본 정보
        self.company_info = {
            "company_name": "",           # 회사명
            "site_name": "",              # 현장명
            "business_type": "",          # 업종
            "ceo_name": "",               # 대표자
            "address": "",                # 주소
            "eval_date": datetime.now().strftime("%Y-%m-%d"),  # 평가일자
            "eval_type": "정기평가",       # 평가유형 (최초/정기/수시)
            "safety_policy": "",          # 안전보건방침
            "safety_goal": "",            # 추진목표
        }

        # 조직 구성 (표1, 표2 반영)
        self.organization = {
            "members": [
                # {"position": "대표이사", "name": "", "role": "총괄관리", "responsibility": "..."}
            ]
        }

        # 위험성 추정 및 결정 기준
        self.risk_criteria = {
            "method": "빈도·강도법",
            "matrix": "3x3",
            # 가능성(빈도) 기준
            "possibility": {
                3: {"label": "상", "description": "발생가능성이 높음. 일상적으로 장시간 이루어지는 작업에 수반하는 것으로 피하기 어려운 것"},
                2: {"label": "중", "description": "발생가능성이 있음. 일상적인 작업에 수반하는 것으로 피할 수 있는 것"},
                1: {"label": "하", "description": "발생가능성이 낮음. 비정상적인 작업에 수반하는 것으로 피할 수 있는 것"},
            },
            # 중대성(강도) 기준
            "severity": {
                3: {"label": "대", "description": "사망을 초래할 수 있는 사고. 신체 일부에 영구손상을 수반하는 것"},
                2: {"label": "중", "description": "휴업재해, 한번에 다수의 피해자가 수반하는 것. 실명, 절단 등 상해를 초래할 수 있는 사고"},
                1: {"label": "소", "description": "아차 사고. 처치 후 바로 원래의 작업을 수행할 수 있는 경미한 부상 또는 질병"},
            },
            # 위험성 수준 결정
            "risk_level": {
                "낮음": {"range": "1~2", "acceptable": True, "action": "근로자에게 유해 위험성 정보를 제공 및 교육"},
                "보통": {"range": "3~4", "acceptable": False, "action": "안전보건대책을 수립하고 개선"},
                "높음": {"range": "6~9", "acceptable": False, "action": "작업을 지속하려면 즉시 개선을 실행"},
            }
        }

        # 위험성평가 실시 데이터
        self.assessments = [
            # {
            #     "process": "공정명",
            #     "sub_work": "세부작업명",
            #     "risk_category": "위험분류",
            #     "risk_detail": "위험세부분류",
            #     "risk_situation": "위험발생 상황 및 결과",
            #     "legal_basis": "관련근거(법적기준)",
            #     "current_measures": "현재의 안전보건조치",
            #     "eval_scale": "3x3",
            #     "possibility": 1,
            #     "severity": 1,
            #     "current_risk": 1,
            #     "current_risk_level": "낮음",
            #     "reduction_measures": "위험성 감소대책",
            #     "after_risk": 1,
            #     "after_risk_level": "낮음",
            #     "due_date": "",
            #     "complete_date": "",
            #     "manager": "",
            #     "note": ""
            # }
        ]

        # 회의 결과 (서식2)
        self.meeting = {
            "date": "",
            "time_start": "",
            "time_end": "",
            "location": "",
            "content": "",
            "attendees": [
                # {"department": "", "position": "", "name": "", "signature": ""}
            ]
        }

        # 교육 결과 (서식1)
        self.education = {
            "date": "",
            "content": "",
            "attendees": []
        }

        # 작업 전 안전점검회의 (서식3)
        self.safety_meeting = {
            "date": "",
            "content": "",
            "attendees": []
        }

    def calculate_risk(self, possibility: int, severity: int) -> tuple:
        """
        위험성 계산

        Args:
            possibility: 가능성(빈도) 1~3
            severity: 중대성(강도) 1~3

        Returns:
            (위험성 점수, 위험성 등급)
        """
        score = possibility * severity

        if score <= 2:
            level = "낮음"
        elif score <= 4:
            level = "보통"
        else:
            level = "높음"

        return score, level

    def format_possibility(self, value: int) -> str:
        """가능성 값 포맷팅"""
        labels = {1: "1(하)", 2: "2(중)", 3: "3(상)"}
        return labels.get(value, str(value))

    def format_severity(self, value: int) -> str:
        """중대성 값 포맷팅"""
        labels = {1: "1(소)", 2: "2(중)", 3: "3(대)"}
        return labels.get(value, str(value))

    def format_risk_level(self, score: int, level: str) -> str:
        """위험성 등급 포맷팅"""
        return f"{score}({level})"

    def save_to_file(self, file_path: str):
        """데이터를 JSON 파일로 저장"""
        data = {
            "company_info": self.company_info,
            "organization": self.organization,
            "risk_criteria": self.risk_criteria,
            "assessments": self.assessments,
            "meeting": self.meeting,
            "education": self.education,
            "safety_meeting": self.safety_meeting,
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, file_path: str):
        """JSON 파일에서 데이터 로드"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.company_info = data.get("company_info", self.company_info)
        self.organization = data.get("organization", self.organization)
        self.risk_criteria = data.get("risk_criteria", self.risk_criteria)
        self.assessments = data.get("assessments", self.assessments)
        self.meeting = data.get("meeting", self.meeting)
        self.education = data.get("education", self.education)
        self.safety_meeting = data.get("safety_meeting", self.safety_meeting)

    def add_assessment(self, assessment: dict):
        """위험성평가 항목 추가"""
        self.assessments.append(assessment)

    def remove_assessment(self, index: int):
        """위험성평가 항목 삭제"""
        if 0 <= index < len(self.assessments):
            self.assessments.pop(index)

    def get_all_data(self) -> dict:
        """모든 데이터 반환"""
        return {
            "company_info": self.company_info,
            "organization": self.organization,
            "risk_criteria": self.risk_criteria,
            "assessments": self.assessments,
            "meeting": self.meeting,
            "education": self.education,
            "safety_meeting": self.safety_meeting,
        }

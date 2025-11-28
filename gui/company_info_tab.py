# -*- coding: utf-8 -*-
"""
기본 정보 입력 탭
회사정보, 현장정보, 안전보건방침, 추진목표
자동 연동: 기본정보 입력 시 다른 탭에 자동으로 데이터 전달
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QGroupBox,
    QDateEdit, QFormLayout, QPushButton, QMessageBox
)
from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6.QtGui import QFont

from core.policy_templates import (
    get_policy_template, get_goal_template, get_categories
)


class CompanyInfoTab(QWidget):
    """기본 정보 입력 탭"""

    # 데이터 변경 시그널
    data_changed = pyqtSignal()

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 회사 정보 그룹
        company_group = QGroupBox("회사 정보")
        company_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        company_layout = QGridLayout(company_group)

        # 회사명
        company_layout.addWidget(QLabel("회사명:"), 0, 0)
        self.txt_company_name = QLineEdit()
        self.txt_company_name.setPlaceholderText("예: ㈜OOO")
        company_layout.addWidget(self.txt_company_name, 0, 1)

        # 대표자
        company_layout.addWidget(QLabel("대표자:"), 0, 2)
        self.txt_ceo_name = QLineEdit()
        company_layout.addWidget(self.txt_ceo_name, 0, 3)

        # 업종
        company_layout.addWidget(QLabel("업종:"), 1, 0)
        self.txt_business_type = QLineEdit()
        self.txt_business_type.setPlaceholderText("예: 소방시설공사업")
        company_layout.addWidget(self.txt_business_type, 1, 1)

        # 주소
        company_layout.addWidget(QLabel("주소:"), 1, 2)
        self.txt_address = QLineEdit()
        company_layout.addWidget(self.txt_address, 1, 3)

        layout.addWidget(company_group)

        # 현장 정보 그룹
        site_group = QGroupBox("현장/평가 정보")
        site_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        site_layout = QGridLayout(site_group)

        # 현장명
        site_layout.addWidget(QLabel("현장명:"), 0, 0)
        self.txt_site_name = QLineEdit()
        self.txt_site_name.setPlaceholderText("예: OO건물 신축공사(소방)")
        site_layout.addWidget(self.txt_site_name, 0, 1)

        # 평가일자
        site_layout.addWidget(QLabel("평가일자:"), 0, 2)
        self.date_eval = QDateEdit()
        self.date_eval.setCalendarPopup(True)
        self.date_eval.setDate(QDate.currentDate())
        site_layout.addWidget(self.date_eval, 0, 3)

        # 평가유형
        site_layout.addWidget(QLabel("평가유형:"), 1, 0)
        self.cmb_eval_type = QComboBox()
        self.cmb_eval_type.addItems(["최초평가", "정기평가", "수시평가"])
        site_layout.addWidget(self.cmb_eval_type, 1, 1)

        layout.addWidget(site_group)

        # 업종 선택 그룹 (안전보건방침/추진목표 템플릿)
        template_group = QGroupBox("업종별 템플릿 선택")
        template_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        template_layout = QHBoxLayout(template_group)

        template_layout.addWidget(QLabel("업종 선택:"))
        self.cmb_industry = QComboBox()
        self.cmb_industry.addItems(get_categories())
        self.cmb_industry.setCurrentText("소방시설공사업")  # 기본값
        self.cmb_industry.currentTextChanged.connect(self.on_industry_changed)
        template_layout.addWidget(self.cmb_industry)

        self.btn_apply_template = QPushButton("템플릿 적용")
        self.btn_apply_template.clicked.connect(self.apply_template)
        template_layout.addWidget(self.btn_apply_template)

        template_layout.addStretch()
        layout.addWidget(template_group)

        # 안전보건방침 그룹
        policy_group = QGroupBox("안전보건방침")
        policy_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        policy_layout = QVBoxLayout(policy_group)

        self.txt_safety_policy = QTextEdit()
        # 기본 템플릿 (소방시설공사업)
        self.txt_safety_policy.setPlainText(get_policy_template("소방시설공사업"))
        self.txt_safety_policy.setMaximumHeight(140)
        policy_layout.addWidget(self.txt_safety_policy)

        layout.addWidget(policy_group)

        # 추진목표 그룹
        goal_group = QGroupBox("추진목표")
        goal_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        goal_layout = QVBoxLayout(goal_group)

        self.txt_safety_goal = QTextEdit()
        # 기본 템플릿 (소방시설공사업)
        self.txt_safety_goal.setPlainText(get_goal_template("소방시설공사업"))
        self.txt_safety_goal.setMaximumHeight(120)
        goal_layout.addWidget(self.txt_safety_goal)

        layout.addWidget(goal_group)

        # 적용 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_apply = QPushButton("다른 탭에 적용")
        self.btn_apply.setFixedSize(150, 35)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_apply.clicked.connect(self.apply_to_other_tabs)
        btn_layout.addWidget(self.btn_apply)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def connect_signals(self):
        """입력 필드 변경 시 시그널 연결"""
        # 텍스트 변경 시 자동 연동 (실시간)
        self.txt_company_name.textChanged.connect(self.on_data_changed)
        self.txt_site_name.textChanged.connect(self.on_data_changed)
        self.date_eval.dateChanged.connect(self.on_data_changed)

    def on_data_changed(self):
        """데이터 변경 시 호출 (실시간 연동)"""
        # 데이터 수집 후 시그널 발생
        self.collect_data()
        self.data_changed.emit()

    def on_industry_changed(self, industry: str):
        """업종 변경 시 호출"""
        # work_type 업데이트 (위험성평가 실시표 공정명에 사용)
        self.data_manager.company_info["work_type"] = industry

    def apply_template(self):
        """선택한 업종의 템플릿 적용"""
        industry = self.cmb_industry.currentText()
        self.txt_safety_policy.setPlainText(get_policy_template(industry))
        self.txt_safety_goal.setPlainText(get_goal_template(industry))
        QMessageBox.information(self, "템플릿 적용", f"'{industry}' 템플릿이 적용되었습니다.")

    def apply_to_other_tabs(self):
        """다른 탭에 적용 버튼 클릭 시"""
        self.collect_data()
        self.data_changed.emit()
        QMessageBox.information(self, "적용 완료", "기본정보가 다른 탭에 적용되었습니다.")

    def collect_data(self):
        """입력된 데이터 수집"""
        self.data_manager.company_info["company_name"] = self.txt_company_name.text()
        self.data_manager.company_info["ceo_name"] = self.txt_ceo_name.text()
        self.data_manager.company_info["business_type"] = self.txt_business_type.text()
        self.data_manager.company_info["address"] = self.txt_address.text()
        self.data_manager.company_info["site_name"] = self.txt_site_name.text()
        self.data_manager.company_info["eval_date"] = self.date_eval.date().toString("yyyy-MM-dd")
        self.data_manager.company_info["eval_type"] = self.cmb_eval_type.currentText()
        self.data_manager.company_info["safety_policy"] = self.txt_safety_policy.toPlainText()
        self.data_manager.company_info["safety_goal"] = self.txt_safety_goal.toPlainText()
        # 업종 선택 값을 work_type으로 저장 (위험성평가 실시표 공정명에 사용)
        self.data_manager.company_info["work_type"] = self.cmb_industry.currentText()

    def refresh_data(self):
        """데이터 새로고침"""
        info = self.data_manager.company_info

        # 시그널 임시 차단
        self.txt_company_name.blockSignals(True)
        self.txt_site_name.blockSignals(True)
        self.date_eval.blockSignals(True)

        self.txt_company_name.setText(info.get("company_name", ""))
        self.txt_ceo_name.setText(info.get("ceo_name", ""))
        self.txt_business_type.setText(info.get("business_type", ""))
        self.txt_address.setText(info.get("address", ""))
        self.txt_site_name.setText(info.get("site_name", ""))

        eval_date = info.get("eval_date", "")
        if eval_date:
            self.date_eval.setDate(QDate.fromString(eval_date, "yyyy-MM-dd"))

        eval_type = info.get("eval_type", "정기평가")
        index = self.cmb_eval_type.findText(eval_type)
        if index >= 0:
            self.cmb_eval_type.setCurrentIndex(index)

        self.txt_safety_policy.setPlainText(info.get("safety_policy", ""))
        self.txt_safety_goal.setPlainText(info.get("safety_goal", ""))

        # 시그널 다시 활성화
        self.txt_company_name.blockSignals(False)
        self.txt_site_name.blockSignals(False)
        self.date_eval.blockSignals(False)

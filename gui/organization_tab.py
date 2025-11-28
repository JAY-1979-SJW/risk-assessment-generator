# -*- coding: utf-8 -*-
"""
조직 구성 탭
위험성평가 실시 담당 조직 구성 및 역할/책임
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class OrganizationTab(QWidget):
    """조직 구성 탭"""

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 설명
        desc_label = QLabel(
            "위험성평가 실시 담당 조직의 구성과 역할/책임을 입력합니다.\n"
            "(표준실시규정 제3조, 제4조 참조)"
        )
        desc_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(desc_label)

        # 조직 구성 테이블
        org_group = QGroupBox("위험성평가 실시 담당 조직 구성 (표1, 표2)")
        org_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        org_layout = QVBoxLayout(org_group)

        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["직위/직책", "성명", "역할", "책임"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.table.setMinimumHeight(300)
        org_layout.addWidget(self.table)

        # 버튼
        btn_layout = QHBoxLayout()

        btn_add = QPushButton("행 추가")
        btn_add.clicked.connect(self.add_row)
        btn_layout.addWidget(btn_add)

        btn_remove = QPushButton("행 삭제")
        btn_remove.clicked.connect(self.remove_row)
        btn_layout.addWidget(btn_remove)

        btn_template = QPushButton("기본 템플릿 적용")
        btn_template.clicked.connect(self.apply_template)
        btn_layout.addWidget(btn_template)

        btn_layout.addStretch()
        org_layout.addLayout(btn_layout)

        layout.addWidget(org_group)

        # 기본 템플릿 적용
        self.apply_template()

    def add_row(self):
        """행 추가"""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)

    def remove_row(self):
        """선택된 행 삭제"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
        else:
            QMessageBox.warning(self, "알림", "삭제할 행을 선택하세요.")

    def apply_template(self):
        """기본 템플릿 적용"""
        template = [
            {
                "position": "대표이사(사업주)",
                "name": "",
                "role": "총괄관리",
                "responsibility": "위험성평가 실시 총괄, 예산 지원, 최종 승인"
            },
            {
                "position": "안전보건관리책임자",
                "name": "",
                "role": "실무총괄",
                "responsibility": "위험성평가 계획 수립, 실시 감독, 결과 보고"
            },
            {
                "position": "관리감독자",
                "name": "",
                "role": "현장실시",
                "responsibility": "유해위험요인 파악, 위험성 결정, 감소대책 실행"
            },
            {
                "position": "안전관리자/담당자",
                "name": "",
                "role": "기술지원",
                "responsibility": "위험성평가 교육, 기술지원, 기록 관리"
            },
            {
                "position": "근로자대표",
                "name": "",
                "role": "참여/협의",
                "responsibility": "위험성평가 참여, 근로자 의견 수렴 및 전달"
            },
        ]

        self.table.setRowCount(0)
        for item in template:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item["position"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["role"]))
            self.table.setItem(row, 3, QTableWidgetItem(item["responsibility"]))

    def collect_data(self):
        """입력된 데이터 수집"""
        members = []
        for row in range(self.table.rowCount()):
            member = {
                "position": self._get_cell_text(row, 0),
                "name": self._get_cell_text(row, 1),
                "role": self._get_cell_text(row, 2),
                "responsibility": self._get_cell_text(row, 3),
            }
            members.append(member)

        self.data_manager.organization["members"] = members

    def _get_cell_text(self, row, col):
        """셀 텍스트 가져오기"""
        item = self.table.item(row, col)
        return item.text() if item else ""

    def refresh_data(self):
        """데이터 새로고침"""
        members = self.data_manager.organization.get("members", [])

        self.table.setRowCount(0)
        for member in members:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(member.get("position", "")))
            self.table.setItem(row, 1, QTableWidgetItem(member.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(member.get("role", "")))
            self.table.setItem(row, 3, QTableWidgetItem(member.get("responsibility", "")))

    def update_company_info(self):
        """기본정보 탭에서 연동된 데이터 업데이트"""
        # 조직 구성에서 대표자 이름 자동 설정
        info = self.data_manager.company_info
        ceo_name = info.get("ceo_name", "")
        if ceo_name and self.table.rowCount() > 0:
            # 첫 번째 행(대표이사)의 이름 자동 설정
            self.table.setItem(0, 1, QTableWidgetItem(ceo_name))

# -*- coding: utf-8 -*-
"""
위험성 추정·결정 기준 탭
빈도·강도법 기준표 표시 및 설정
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor


class RiskCriteriaTab(QWidget):
    """위험성 추정·결정 기준 탭"""

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 스크롤 영역 생성
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(20)

        # 제목
        title_label = QLabel("위험성 추정 및 결정 방법")
        title_label.setFont(QFont("맑은 고딕", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title_label)

        # 부제목
        subtitle_label = QLabel("곱셈식에 의한 위험성 추정 및 결정표")
        subtitle_label.setFont(QFont("맑은 고딕", 12))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #34495e;")
        layout.addWidget(subtitle_label)

        # 설명
        desc_label = QLabel("실시방법: 가능성과 중대성을 추정한 수치를 곱셈에 의해 위험성을 구하고 위험성 수준을 결정함")
        desc_label.setFont(QFont("맑은 고딕", 11))
        desc_label.setStyleSheet("""
            color: #2c3e50;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 8px;
            border: 1px solid #bdc3c7;
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 수평 레이아웃 (가능성, 중대성)
        criteria_layout = QHBoxLayout()
        criteria_layout.setSpacing(20)

        # 가능성(빈도) 테이블
        possibility_group = QGroupBox("가능성(빈도)")
        possibility_group.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
        possibility_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #3498db;
            }
        """)
        possibility_layout = QVBoxLayout(possibility_group)
        possibility_layout.setSpacing(10)

        possibility_desc = QLabel("사고나 질병으로 이어질 가능성(확률)을 파악하는 것으로 발생빈도 수준을 측정")
        possibility_desc.setStyleSheet("color: #7f8c8d; padding: 5px;")
        possibility_desc.setWordWrap(True)
        possibility_layout.addWidget(possibility_desc)

        self.possibility_table = QTableWidget()
        self.possibility_table.setColumnCount(3)
        self.possibility_table.setHorizontalHeaderLabels(["구분", "점수", "기준"])
        self.possibility_table.setRowCount(3)
        self.possibility_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                font-size: 11pt;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        possibility_data = [
            ("상", "3", "발생가능성이 높음. 일상적으로 장시간 이루어지는 작업에 수반하는 것으로 피하기 어려운 것"),
            ("중", "2", "발생가능성이 있음. 일상적인 작업에 수반하는 것으로 피할 수 있는 것"),
            ("하", "1", "발생가능성이 낮음. 비정상적인 작업에 수반하는 것으로 피할 수 있는 것"),
        ]

        for row, (level, score, desc) in enumerate(possibility_data):
            item0 = QTableWidgetItem(level)
            item0.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
            item1 = QTableWidgetItem(score)
            item1.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
            item2 = QTableWidgetItem(desc)
            item2.setFont(QFont("맑은 고딕", 10))

            self.possibility_table.setItem(row, 0, item0)
            self.possibility_table.setItem(row, 1, item1)
            self.possibility_table.setItem(row, 2, item2)
            self.possibility_table.item(row, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.possibility_table.item(row, 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.possibility_table.setRowHeight(row, 60)

        header = self.possibility_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.possibility_table.setColumnWidth(0, 60)
        self.possibility_table.setColumnWidth(1, 60)
        self.possibility_table.setMinimumHeight(220)
        possibility_layout.addWidget(self.possibility_table)

        criteria_layout.addWidget(possibility_group)

        # 중대성(강도) 테이블
        severity_group = QGroupBox("중대성(강도)")
        severity_group.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
        severity_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e74c3c;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #e74c3c;
            }
        """)
        severity_layout = QVBoxLayout(severity_group)
        severity_layout.setSpacing(10)

        severity_desc = QLabel("사고나 질병으로 이어졌을 때 그 중대성(강도)을 파악하는 것으로 부상의 경중(심각성)을 측정")
        severity_desc.setStyleSheet("color: #7f8c8d; padding: 5px;")
        severity_desc.setWordWrap(True)
        severity_layout.addWidget(severity_desc)

        self.severity_table = QTableWidget()
        self.severity_table.setColumnCount(3)
        self.severity_table.setHorizontalHeaderLabels(["구분", "점수", "기준"])
        self.severity_table.setRowCount(3)
        self.severity_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                font-size: 11pt;
            }
            QHeaderView::section {
                background-color: #e74c3c;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        severity_data = [
            ("대", "3", "사망을 초래할 수 있는 사고. 신체 일부에 영구손상을 수반하는 것"),
            ("중", "2", "휴업재해, 한번에 다수의 피해자가 수반하는 것. 실명, 절단 등 상해를 초래할 수 있는 사고"),
            ("소", "1", "아차 사고. 처치 후 바로 원래의 작업을 수행할 수 있는 경미한 부상 또는 질병"),
        ]

        for row, (level, score, desc) in enumerate(severity_data):
            item0 = QTableWidgetItem(level)
            item0.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
            item1 = QTableWidgetItem(score)
            item1.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
            item2 = QTableWidgetItem(desc)
            item2.setFont(QFont("맑은 고딕", 10))

            self.severity_table.setItem(row, 0, item0)
            self.severity_table.setItem(row, 1, item1)
            self.severity_table.setItem(row, 2, item2)
            self.severity_table.item(row, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.severity_table.item(row, 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.severity_table.setRowHeight(row, 60)

        header = self.severity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.severity_table.setColumnWidth(0, 60)
        self.severity_table.setColumnWidth(1, 60)
        self.severity_table.setMinimumHeight(220)
        severity_layout.addWidget(self.severity_table)

        criteria_layout.addWidget(severity_group)

        layout.addLayout(criteria_layout)

        # 공식
        formula_label = QLabel("※ 가능성(빈도) × 중대성(강도) = 위험성 추정")
        formula_label.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
        formula_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formula_label.setStyleSheet("""
            color: #e74c3c;
            padding: 15px;
            background-color: #fdf2f2;
            border: 2px solid #e74c3c;
            border-radius: 8px;
        """)
        layout.addWidget(formula_label)

        # 하단 영역 (위험성 결정 + 매트릭스)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)

        # 위험성 결정 테이블
        decision_group = QGroupBox("위험성 결정")
        decision_group.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
        decision_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #27ae60;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #27ae60;
            }
        """)
        decision_layout = QVBoxLayout(decision_group)
        decision_layout.setSpacing(10)

        decision_desc = QLabel("평가 3단계로 구분하고 평가 점수가 높은 순서대로 우선순위 결정")
        decision_desc.setStyleSheet("color: #7f8c8d; padding: 5px;")
        decision_layout.addWidget(decision_desc)

        self.decision_table = QTableWidget()
        self.decision_table.setColumnCount(4)
        self.decision_table.setHorizontalHeaderLabels(["위험성 수준", "등급", "허용가능범위", "비고(조치)"])
        self.decision_table.setRowCount(3)
        self.decision_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                font-size: 11pt;
            }
            QHeaderView::section {
                background-color: #27ae60;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        decision_data = [
            ("1~2", "낮음", "허용가능", "근로자에게 유해 위험성 정보를 제공 및 교육"),
            ("3~4", "보통", "허용 불가능", "안전보건대책을 수립하고 개선"),
            ("6~9", "높음", "허용 불가능", "작업을 지속하려면 즉시 개선을 실행"),
        ]

        colors = [
            (QColor("#92D050"), QColor("#000000")),  # 낮음 - 초록 배경, 검정 글씨
            (QColor("#FFA500"), QColor("#000000")),  # 보통 - 주황 배경, 검정 글씨
            (QColor("#FF0000"), QColor("#FFFFFF")),  # 높음 - 빨강 배경, 흰색 글씨
        ]

        for row, (level, grade, acceptable, action) in enumerate(decision_data):
            item0 = QTableWidgetItem(level)
            item0.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
            item1 = QTableWidgetItem(grade)
            item1.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
            item2 = QTableWidgetItem(acceptable)
            item2.setFont(QFont("맑은 고딕", 10))
            item3 = QTableWidgetItem(action)
            item3.setFont(QFont("맑은 고딕", 10))

            self.decision_table.setItem(row, 0, item0)
            self.decision_table.setItem(row, 1, item1)
            self.decision_table.setItem(row, 2, item2)
            self.decision_table.setItem(row, 3, item3)

            # 등급 셀에 배경색 및 글자색 적용
            bg_color, text_color = colors[row]
            self.decision_table.item(row, 1).setBackground(bg_color)
            self.decision_table.item(row, 1).setForeground(text_color)

            for col in range(4):
                self.decision_table.item(row, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.decision_table.setRowHeight(row, 50)

        header = self.decision_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.decision_table.setColumnWidth(0, 100)
        self.decision_table.setColumnWidth(1, 80)
        self.decision_table.setColumnWidth(2, 120)
        self.decision_table.setMinimumHeight(200)
        decision_layout.addWidget(self.decision_table)

        bottom_layout.addWidget(decision_group, 2)

        # 3x3 매트릭스
        matrix_group = QGroupBox("위험성 매트릭스 (3x3)")
        matrix_group.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
        matrix_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #9b59b6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #9b59b6;
            }
        """)
        matrix_layout = QVBoxLayout(matrix_group)

        # 매트릭스 설명
        matrix_desc = QLabel("가능성 × 중대성 = 위험성 점수")
        matrix_desc.setStyleSheet("color: #7f8c8d; padding: 5px;")
        matrix_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        matrix_layout.addWidget(matrix_desc)

        self.matrix_table = QTableWidget()
        self.matrix_table.setColumnCount(4)
        self.matrix_table.setRowCount(4)
        self.matrix_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #7f8c8d;
                font-size: 11pt;
            }
            QHeaderView::section {
                background-color: #9b59b6;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        # 헤더 설정
        self.matrix_table.setHorizontalHeaderLabels(["중대성→", "1(소)", "2(중)", "3(대)"])
        self.matrix_table.setVerticalHeaderLabels(["가능성↓", "3(상)", "2(중)", "1(하)"])

        # 매트릭스 데이터
        matrix_data = [
            [("3", "보통"), ("6", "높음"), ("9", "높음")],
            [("2", "낮음"), ("4", "보통"), ("6", "높음")],
            [("1", "낮음"), ("2", "낮음"), ("3", "보통")],
        ]

        color_map = {
            "낮음": (QColor("#92D050"), QColor("#000000")),  # 초록 배경, 검정 글씨
            "보통": (QColor("#FFA500"), QColor("#000000")),  # 주황 배경, 검정 글씨
            "높음": (QColor("#FF0000"), QColor("#FFFFFF")),  # 빨강 배경, 흰색 글씨
        }

        for row, row_data in enumerate(matrix_data):
            for col, (score, level) in enumerate(row_data):
                item = QTableWidgetItem(f"{score}\n({level})")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                bg_color, text_color = color_map[level]
                item.setBackground(bg_color)
                item.setForeground(text_color)
                item.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
                self.matrix_table.setItem(row, col + 1, item)
            self.matrix_table.setRowHeight(row, 60)

        # 첫 번째 열은 빈 셀로 설정
        for row in range(3):
            empty_item = QTableWidgetItem("")
            self.matrix_table.setItem(row, 0, empty_item)

        header = self.matrix_table.horizontalHeader()
        for col in range(4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        self.matrix_table.setMinimumHeight(230)
        self.matrix_table.setMinimumWidth(350)
        matrix_layout.addWidget(self.matrix_table)

        bottom_layout.addWidget(matrix_group, 1)

        layout.addLayout(bottom_layout)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

    def collect_data(self):
        """데이터 수집 (기준표는 고정값이므로 별도 수집 불필요)"""
        pass

    def refresh_data(self):
        """데이터 새로고침"""
        pass

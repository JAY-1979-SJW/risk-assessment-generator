# -*- coding: utf-8 -*-
"""
회의 및 서식 탭
위험성평가 회의 결과(서식2), 교육 결과(서식1), 작업전 안전점검회의(서식3)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QTimeEdit, QTabWidget
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont


class MeetingFormTab(QWidget):
    """회의 및 서식 탭"""

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 서브 탭
        sub_tabs = QTabWidget()
        sub_tabs.addTab(self.create_meeting_tab(), "위험성평가 회의 결과 (서식2)")
        sub_tabs.addTab(self.create_education_tab(), "위험성평가 교육 결과 (서식1)")
        sub_tabs.addTab(self.create_safety_meeting_tab(), "작업 전 안전점검회의 (서식3)")

        layout.addWidget(sub_tabs)

    def create_meeting_tab(self):
        """위험성평가 회의 결과 서식"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 제목
        title = QLabel("위험성 평가 회의 결과")
        title.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 회의 정보
        info_group = QGroupBox("회의 정보")
        info_layout = QGridLayout(info_group)

        # 회의일시
        info_layout.addWidget(QLabel("회의일시:"), 0, 0)
        self.meeting_date = QDateEdit()
        self.meeting_date.setCalendarPopup(True)
        self.meeting_date.setDate(QDate.currentDate())
        info_layout.addWidget(self.meeting_date, 0, 1)

        info_layout.addWidget(QLabel("시작시간:"), 0, 2)
        self.meeting_time_start = QTimeEdit()
        self.meeting_time_start.setTime(QTime(9, 0))
        info_layout.addWidget(self.meeting_time_start, 0, 3)

        info_layout.addWidget(QLabel("종료시간:"), 0, 4)
        self.meeting_time_end = QTimeEdit()
        self.meeting_time_end.setTime(QTime(10, 0))
        info_layout.addWidget(self.meeting_time_end, 0, 5)

        # 회의장소
        info_layout.addWidget(QLabel("회의장소:"), 1, 0)
        self.meeting_location = QLineEdit()
        self.meeting_location.setPlaceholderText("예: 회의실")
        info_layout.addWidget(self.meeting_location, 1, 1, 1, 5)

        layout.addWidget(info_group)

        # 회의내용
        content_group = QGroupBox("회의내용")
        content_layout = QVBoxLayout(content_group)

        self.meeting_content = QTextEdit()
        self.meeting_content.setPlaceholderText(
            "예시)\n"
            "• 위험성평가 추진을 위한 계획수립의 적정성\n"
            "• 위험성평가 실시에 따른 책임과 역할 부여\n"
            "• 위험성평가와 관련한 관심사항 토론 등"
        )
        self.meeting_content.setMinimumHeight(150)
        content_layout.addWidget(self.meeting_content)

        layout.addWidget(content_group)

        # 참석자 명단
        attendee_group = QGroupBox("참석자 명단")
        attendee_layout = QVBoxLayout(attendee_group)

        # 버튼
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("참석자 추가")
        btn_add.clicked.connect(self.add_meeting_attendee)
        btn_layout.addWidget(btn_add)

        btn_remove = QPushButton("참석자 삭제")
        btn_remove.clicked.connect(self.remove_meeting_attendee)
        btn_layout.addWidget(btn_remove)
        btn_layout.addStretch()
        attendee_layout.addLayout(btn_layout)

        # 테이블
        self.meeting_attendees_table = QTableWidget()
        self.meeting_attendees_table.setColumnCount(3)
        self.meeting_attendees_table.setHorizontalHeaderLabels(["소속/직책", "성명", "서명"])

        header = self.meeting_attendees_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        attendee_layout.addWidget(self.meeting_attendees_table)

        layout.addWidget(attendee_group)

        return widget

    def create_education_tab(self):
        """위험성평가 교육 결과 서식"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 제목
        title = QLabel("위험성평가 교육 결과")
        title.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 교육 정보
        info_group = QGroupBox("교육 정보")
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel("교육일자:"), 0, 0)
        self.edu_date = QDateEdit()
        self.edu_date.setCalendarPopup(True)
        self.edu_date.setDate(QDate.currentDate())
        info_layout.addWidget(self.edu_date, 0, 1)

        layout.addWidget(info_group)

        # 교육내용
        content_group = QGroupBox("교육내용")
        content_layout = QVBoxLayout(content_group)

        self.edu_content = QTextEdit()
        self.edu_content.setPlaceholderText("교육 내용을 입력하세요.")
        self.edu_content.setMinimumHeight(150)
        content_layout.addWidget(self.edu_content)

        layout.addWidget(content_group)

        # 참석자 명단
        attendee_group = QGroupBox("참석자 명단")
        attendee_layout = QVBoxLayout(attendee_group)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("참석자 추가")
        btn_add.clicked.connect(self.add_edu_attendee)
        btn_layout.addWidget(btn_add)

        btn_remove = QPushButton("참석자 삭제")
        btn_remove.clicked.connect(self.remove_edu_attendee)
        btn_layout.addWidget(btn_remove)
        btn_layout.addStretch()
        attendee_layout.addLayout(btn_layout)

        self.edu_attendees_table = QTableWidget()
        self.edu_attendees_table.setColumnCount(3)
        self.edu_attendees_table.setHorizontalHeaderLabels(["소속/직책", "성명", "서명"])

        header = self.edu_attendees_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        attendee_layout.addWidget(self.edu_attendees_table)

        layout.addWidget(attendee_group)

        return widget

    def create_safety_meeting_tab(self):
        """작업 전 안전점검회의 서식"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 제목
        title = QLabel("작업 전 안전점검회의 결과")
        title.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 회의 정보
        info_group = QGroupBox("회의 정보")
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel("회의일자:"), 0, 0)
        self.safety_date = QDateEdit()
        self.safety_date.setCalendarPopup(True)
        self.safety_date.setDate(QDate.currentDate())
        info_layout.addWidget(self.safety_date, 0, 1)

        layout.addWidget(info_group)

        # 회의내용
        content_group = QGroupBox("회의내용")
        content_layout = QVBoxLayout(content_group)

        self.safety_content = QTextEdit()
        self.safety_content.setPlaceholderText("작업 전 안전점검회의 내용을 입력하세요.")
        self.safety_content.setMinimumHeight(150)
        content_layout.addWidget(self.safety_content)

        layout.addWidget(content_group)

        # 참석자 명단
        attendee_group = QGroupBox("참석자 명단")
        attendee_layout = QVBoxLayout(attendee_group)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("참석자 추가")
        btn_add.clicked.connect(self.add_safety_attendee)
        btn_layout.addWidget(btn_add)

        btn_remove = QPushButton("참석자 삭제")
        btn_remove.clicked.connect(self.remove_safety_attendee)
        btn_layout.addWidget(btn_remove)
        btn_layout.addStretch()
        attendee_layout.addLayout(btn_layout)

        self.safety_attendees_table = QTableWidget()
        self.safety_attendees_table.setColumnCount(3)
        self.safety_attendees_table.setHorizontalHeaderLabels(["소속/직책", "성명", "서명"])

        header = self.safety_attendees_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        attendee_layout.addWidget(self.safety_attendees_table)

        layout.addWidget(attendee_group)

        return widget

    def add_meeting_attendee(self):
        """회의 참석자 추가"""
        row = self.meeting_attendees_table.rowCount()
        self.meeting_attendees_table.insertRow(row)

    def remove_meeting_attendee(self):
        """회의 참석자 삭제"""
        current_row = self.meeting_attendees_table.currentRow()
        if current_row >= 0:
            self.meeting_attendees_table.removeRow(current_row)

    def add_edu_attendee(self):
        """교육 참석자 추가"""
        row = self.edu_attendees_table.rowCount()
        self.edu_attendees_table.insertRow(row)

    def remove_edu_attendee(self):
        """교육 참석자 삭제"""
        current_row = self.edu_attendees_table.currentRow()
        if current_row >= 0:
            self.edu_attendees_table.removeRow(current_row)

    def add_safety_attendee(self):
        """안전회의 참석자 추가"""
        row = self.safety_attendees_table.rowCount()
        self.safety_attendees_table.insertRow(row)

    def remove_safety_attendee(self):
        """안전회의 참석자 삭제"""
        current_row = self.safety_attendees_table.currentRow()
        if current_row >= 0:
            self.safety_attendees_table.removeRow(current_row)

    def _get_attendees_from_table(self, table):
        """테이블에서 참석자 목록 추출"""
        attendees = []
        for row in range(table.rowCount()):
            dept_item = table.item(row, 0)
            name_item = table.item(row, 1)
            attendees.append({
                "department": dept_item.text() if dept_item else "",
                "name": name_item.text() if name_item else "",
                "signature": ""
            })
        return attendees

    def collect_data(self):
        """데이터 수집"""
        # 회의 결과
        self.data_manager.meeting = {
            "date": self.meeting_date.date().toString("yyyy-MM-dd"),
            "time_start": self.meeting_time_start.time().toString("HH:mm"),
            "time_end": self.meeting_time_end.time().toString("HH:mm"),
            "location": self.meeting_location.text(),
            "content": self.meeting_content.toPlainText(),
            "attendees": self._get_attendees_from_table(self.meeting_attendees_table)
        }

        # 교육 결과
        self.data_manager.education = {
            "date": self.edu_date.date().toString("yyyy-MM-dd"),
            "content": self.edu_content.toPlainText(),
            "attendees": self._get_attendees_from_table(self.edu_attendees_table)
        }

        # 안전점검회의
        self.data_manager.safety_meeting = {
            "date": self.safety_date.date().toString("yyyy-MM-dd"),
            "content": self.safety_content.toPlainText(),
            "attendees": self._get_attendees_from_table(self.safety_attendees_table)
        }

    def refresh_data(self):
        """데이터 새로고침"""
        # 회의 결과
        meeting = self.data_manager.meeting
        if meeting.get("date"):
            self.meeting_date.setDate(QDate.fromString(meeting["date"], "yyyy-MM-dd"))
        if meeting.get("time_start"):
            self.meeting_time_start.setTime(QTime.fromString(meeting["time_start"], "HH:mm"))
        if meeting.get("time_end"):
            self.meeting_time_end.setTime(QTime.fromString(meeting["time_end"], "HH:mm"))
        self.meeting_location.setText(meeting.get("location", ""))
        self.meeting_content.setPlainText(meeting.get("content", ""))

        self._load_attendees_to_table(self.meeting_attendees_table, meeting.get("attendees", []))

        # 교육 결과
        education = self.data_manager.education
        if education.get("date"):
            self.edu_date.setDate(QDate.fromString(education["date"], "yyyy-MM-dd"))
        self.edu_content.setPlainText(education.get("content", ""))
        self._load_attendees_to_table(self.edu_attendees_table, education.get("attendees", []))

        # 안전점검회의
        safety = self.data_manager.safety_meeting
        if safety.get("date"):
            self.safety_date.setDate(QDate.fromString(safety["date"], "yyyy-MM-dd"))
        self.safety_content.setPlainText(safety.get("content", ""))
        self._load_attendees_to_table(self.safety_attendees_table, safety.get("attendees", []))

    def _load_attendees_to_table(self, table, attendees):
        """참석자 목록을 테이블에 로드"""
        table.setRowCount(0)
        for attendee in attendees:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(attendee.get("department", "")))
            table.setItem(row, 1, QTableWidgetItem(attendee.get("name", "")))
            table.setItem(row, 2, QTableWidgetItem(""))

    def update_company_info(self):
        """기본정보 탭에서 연동된 데이터 업데이트"""
        # 회의 날짜를 평가일자로 자동 설정 (비어있을 경우)
        info = self.data_manager.company_info
        eval_date = info.get("eval_date", "")
        if eval_date and not self.data_manager.meeting.get("date"):
            self.meeting_date.setDate(QDate.fromString(eval_date, "yyyy-MM-dd"))
            self.edu_date.setDate(QDate.fromString(eval_date, "yyyy-MM-dd"))
            self.safety_date.setDate(QDate.fromString(eval_date, "yyyy-MM-dd"))

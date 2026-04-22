# -*- coding: utf-8 -*-
"""
위험성평가 실시 탭
KRAS 표준 양식 기반 위험성평가 실시표
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QComboBox, QSpinBox, QDialog, QFormLayout, QDialogButtonBox,
    QScrollArea, QListWidget, QListWidgetItem, QCheckBox,
    QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.risk_data import (
    RISK_DATA, KEYWORD_MAPPING, find_risks_for_work,
    get_categories, get_work_types_by_category, get_risks_by_work_type,
    WORK_CATEGORIES
)


class AIGenerateWorker(QThread):
    """OpenAI + KOSHA DB 위험성평가 생성 백그라운드 워커"""
    finished = pyqtSignal(list)   # 성공: 항목 리스트
    error = pyqtSignal(str)       # 실패: 에러 메시지

    def __init__(self, process_name: str, trade_type: str, work_type: str = ""):
        super().__init__()
        self.process_name = process_name
        self.trade_type = trade_type
        self.work_type = work_type

    def run(self):
        try:
            from core.db_connector import fetch_chunks_for_work
            from core.openai_engine import generate_risk_items
            chunks = fetch_chunks_for_work(self.trade_type, self.work_type or None)
            if not chunks:
                self.error.emit(
                    f"KOSHA DB에서 '{self.trade_type}' 관련 자료를 찾지 못했습니다.\n"
                    "SSH 터널(5435) 연결 여부와 검색어를 확인하세요."
                )
                return
            raw_texts = [c["raw_text"] for c in chunks if c.get("raw_text")]
            items = generate_risk_items(self.process_name, self.trade_type, raw_texts, self.work_type)
            self.finished.emit(items)
        except Exception as exc:
            self.error.emit(str(exc))


class RiskDialog(QDialog):
    """위험요소 추가/수정 다이얼로그"""

    def __init__(self, parent=None, data_manager=None, edit_data=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.edit_data = edit_data  # 수정 시 기존 데이터
        self.result_data = None
        self.init_ui()
        if edit_data:
            self.load_data(edit_data)

    def init_ui(self):
        title = "위험요소 수정" if self.edit_data else "위험요소 추가"
        self.setWindowTitle(title)
        self.setMinimumWidth(650)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # 공정명
        self.txt_process = QLineEdit()
        self.txt_process.setText("소방시설공사")
        form_layout.addRow("공정명:", self.txt_process)

        # 세부작업명
        self.txt_sub_work = QLineEdit()
        form_layout.addRow("세부작업명:", self.txt_sub_work)

        # 위험분류
        self.cmb_risk_category = QComboBox()
        self.cmb_risk_category.addItems([
            "기계적 요인", "전기적 요인", "화학(물질)적 요인",
            "작업환경 요인", "작업특성 요인", "기타"
        ])
        form_layout.addRow("위험분류:", self.cmb_risk_category)

        # 위험세부분류
        self.txt_risk_detail = QLineEdit()
        form_layout.addRow("위험세부분류:", self.txt_risk_detail)

        # 위험발생 상황 및 결과
        self.txt_risk_situation = QTextEdit()
        self.txt_risk_situation.setMaximumHeight(80)
        form_layout.addRow("위험발생 상황 및 결과:", self.txt_risk_situation)

        # 관련근거
        self.txt_legal_basis = QLineEdit()
        form_layout.addRow("관련근거(법적기준):", self.txt_legal_basis)

        # 현재의 안전보건조치
        self.txt_current_measures = QTextEdit()
        self.txt_current_measures.setMaximumHeight(60)
        form_layout.addRow("현재의 안전보건조치:", self.txt_current_measures)

        # 현재 위험성 평가 그룹
        current_group = QGroupBox("현재 위험성 평가")
        current_layout = QHBoxLayout(current_group)

        current_layout.addWidget(QLabel("가능성(빈도):"))
        self.spn_possibility = QSpinBox()
        self.spn_possibility.setRange(1, 3)
        self.spn_possibility.setValue(2)
        self.spn_possibility.valueChanged.connect(self.update_risk_display)
        current_layout.addWidget(self.spn_possibility)

        current_layout.addWidget(QLabel("중대성(강도):"))
        self.spn_severity = QSpinBox()
        self.spn_severity.setRange(1, 3)
        self.spn_severity.setValue(2)
        self.spn_severity.valueChanged.connect(self.update_risk_display)
        current_layout.addWidget(self.spn_severity)

        current_layout.addWidget(QLabel("현재 위험성:"))
        self.lbl_current_risk = QLabel("4(보통)")
        self.lbl_current_risk.setStyleSheet("font-weight: bold; padding: 5px;")
        current_layout.addWidget(self.lbl_current_risk)

        current_layout.addStretch()
        form_layout.addRow(current_group)

        # 위험성 감소대책
        self.txt_reduction = QTextEdit()
        self.txt_reduction.setMaximumHeight(80)
        form_layout.addRow("위험성 감소대책:", self.txt_reduction)

        # 개선 후 위험성 평가 그룹
        after_group = QGroupBox("개선 후 위험성 평가")
        after_layout = QHBoxLayout(after_group)

        after_layout.addWidget(QLabel("가능성(빈도):"))
        self.spn_after_possibility = QSpinBox()
        self.spn_after_possibility.setRange(1, 3)
        self.spn_after_possibility.setValue(1)
        self.spn_after_possibility.valueChanged.connect(self.update_after_risk_display)
        after_layout.addWidget(self.spn_after_possibility)

        after_layout.addWidget(QLabel("중대성(강도):"))
        self.spn_after_severity = QSpinBox()
        self.spn_after_severity.setRange(1, 3)
        self.spn_after_severity.setValue(1)
        self.spn_after_severity.valueChanged.connect(self.update_after_risk_display)
        after_layout.addWidget(self.spn_after_severity)

        after_layout.addWidget(QLabel("개선후 위험성:"))
        self.lbl_after_risk = QLabel("1(낮음)")
        self.lbl_after_risk.setStyleSheet("font-weight: bold; padding: 5px;")
        after_layout.addWidget(self.lbl_after_risk)

        after_layout.addStretch()
        form_layout.addRow(after_group)

        # 담당자
        self.txt_manager = QLineEdit()
        form_layout.addRow("담당자:", self.txt_manager)

        layout.addLayout(form_layout)

        # 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # 초기 위험성 표시 업데이트
        self.update_risk_display()
        self.update_after_risk_display()

    def load_data(self, data):
        """기존 데이터 로드 (수정 시)"""
        self.txt_process.setText(data.get("process", ""))
        self.txt_sub_work.setText(data.get("sub_work", ""))

        category = data.get("risk_category", "")
        index = self.cmb_risk_category.findText(category)
        if index >= 0:
            self.cmb_risk_category.setCurrentIndex(index)

        self.txt_risk_detail.setText(data.get("risk_detail", ""))
        self.txt_risk_situation.setPlainText(data.get("risk_situation", ""))
        self.txt_legal_basis.setText(data.get("legal_basis", ""))
        self.txt_current_measures.setPlainText(data.get("current_measures", ""))
        self.spn_possibility.setValue(data.get("possibility", 2))
        self.spn_severity.setValue(data.get("severity", 2))
        self.txt_reduction.setPlainText(data.get("reduction_measures", ""))
        self.spn_after_possibility.setValue(data.get("after_possibility", 1))
        self.spn_after_severity.setValue(data.get("after_severity", 1))
        self.txt_manager.setText(data.get("manager", ""))

    def update_risk_display(self):
        """현재 위험성 표시 업데이트"""
        score, level = self._calculate_risk(
            self.spn_possibility.value(),
            self.spn_severity.value()
        )
        self.lbl_current_risk.setText(f"{score}({level})")
        self._set_risk_color(self.lbl_current_risk, level)

    def update_after_risk_display(self):
        """개선 후 위험성 표시 업데이트"""
        score, level = self._calculate_risk(
            self.spn_after_possibility.value(),
            self.spn_after_severity.value()
        )
        self.lbl_after_risk.setText(f"{score}({level})")
        self._set_risk_color(self.lbl_after_risk, level)

    def _calculate_risk(self, possibility, severity):
        """위험성 계산"""
        score = possibility * severity
        if score <= 2:
            level = "낮음"
        elif score <= 4:
            level = "보통"
        else:
            level = "높음"
        return score, level

    def _set_risk_color(self, label, level):
        """위험성 등급에 따른 색상 설정"""
        colors = {
            "낮음": "background-color: #92D050; font-weight: bold; padding: 5px;",
            "보통": "background-color: #FFA500; color: #000000; font-weight: bold; padding: 5px;",
            "높음": "background-color: #FF0000; color: white; font-weight: bold; padding: 5px;",
        }
        label.setStyleSheet(colors.get(level, ""))

    def accept(self):
        """확인 버튼"""
        possibility = self.spn_possibility.value()
        severity = self.spn_severity.value()
        score, level = self._calculate_risk(possibility, severity)

        after_possibility = self.spn_after_possibility.value()
        after_severity = self.spn_after_severity.value()
        after_score, after_level = self._calculate_risk(after_possibility, after_severity)

        self.result_data = {
            "process": self.txt_process.text(),
            "sub_work": self.txt_sub_work.text(),
            "risk_category": self.cmb_risk_category.currentText(),
            "risk_detail": self.txt_risk_detail.text(),
            "risk_situation": self.txt_risk_situation.toPlainText(),
            "legal_basis": self.txt_legal_basis.text(),
            "current_measures": self.txt_current_measures.toPlainText(),
            "eval_scale": "3x3",
            "possibility": possibility,
            "severity": severity,
            "current_risk": score,
            "current_risk_level": level,
            "reduction_measures": self.txt_reduction.toPlainText(),
            "after_possibility": after_possibility,
            "after_severity": after_severity,
            "after_risk": after_score,
            "after_risk_level": after_level,
            "due_date": "",
            "complete_date": "",
            "manager": self.txt_manager.text(),
            "note": ""
        }
        super().accept()


# 하위 호환성을 위한 별칭
AddRiskDialog = RiskDialog


class RiskAssessmentTab(QWidget):
    """위험성평가 실시 탭"""

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 상단: 기본정보 표시 (자동 연동)
        info_group = QGroupBox("기본정보 (자동 연동)")
        info_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        info_layout = QHBoxLayout(info_group)

        self.lbl_company = QLabel("회사명: -")
        info_layout.addWidget(self.lbl_company)

        self.lbl_site = QLabel("현장명: -")
        info_layout.addWidget(self.lbl_site)

        self.lbl_date = QLabel("평가일자: -")
        info_layout.addWidget(self.lbl_date)

        info_layout.addStretch()
        layout.addWidget(info_group)

        # ===== 상단: 키워드 입력 방식 =====
        auto_group = QGroupBox("① 작업사항 입력 → 위험요소 검색 및 선택")
        auto_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        auto_group.setStyleSheet("QGroupBox { border: 2px solid #2196F3; border-radius: 5px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { color: #2196F3; }")
        auto_layout = QVBoxLayout(auto_group)

        # 작업사항 입력 및 목록 영역 (좌우 배치)
        work_input_layout = QHBoxLayout()

        # 좌측: 작업사항 입력
        work_add_widget = QWidget()
        work_add_layout = QVBoxLayout(work_add_widget)
        work_add_layout.setContentsMargins(0, 0, 5, 0)

        lbl_work_input = QLabel("작업사항 입력:")
        lbl_work_input.setFont(QFont("맑은 고딕", 9, QFont.Weight.Bold))
        work_add_layout.addWidget(lbl_work_input)

        work_entry_layout = QHBoxLayout()
        self.txt_work_input = QLineEdit()
        self.txt_work_input.setPlaceholderText("작업 키워드 입력 (예: 배관, 감지기)")
        self.txt_work_input.setMinimumHeight(28)
        self.txt_work_input.returnPressed.connect(self.add_work_item)
        work_entry_layout.addWidget(self.txt_work_input)

        btn_add_work = QPushButton("추가")
        btn_add_work.setMinimumWidth(60)
        btn_add_work.setMinimumHeight(28)
        btn_add_work.clicked.connect(self.add_work_item)
        work_entry_layout.addWidget(btn_add_work)
        work_add_layout.addLayout(work_entry_layout)

        # 작업사항 목록
        self.list_work_items = QListWidget()
        self.list_work_items.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_work_items.setMinimumHeight(80)
        self.list_work_items.setMaximumHeight(100)
        self.list_work_items.itemClicked.connect(self.on_work_item_clicked)
        work_add_layout.addWidget(self.list_work_items)

        # 작업사항 관리 버튼
        work_btn_layout = QHBoxLayout()
        btn_remove_work = QPushButton("선택 삭제")
        btn_remove_work.setMinimumHeight(24)
        btn_remove_work.clicked.connect(self.remove_work_item)
        work_btn_layout.addWidget(btn_remove_work)

        btn_clear_work = QPushButton("전체 삭제")
        btn_clear_work.setMinimumHeight(24)
        btn_clear_work.clicked.connect(self.clear_work_items)
        work_btn_layout.addWidget(btn_clear_work)

        btn_search_all = QPushButton("전체 검색")
        btn_search_all.setMinimumHeight(24)
        btn_search_all.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        btn_search_all.clicked.connect(self.search_all_work_items)
        work_btn_layout.addWidget(btn_search_all)
        work_add_layout.addLayout(work_btn_layout)

        work_input_layout.addWidget(work_add_widget, 1)

        # 우측: 검색 결과 미리보기
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_layout.setContentsMargins(5, 0, 0, 0)

        self.lbl_keyword_result = QLabel("검색 결과: 작업사항을 추가하고 클릭하거나 '전체 검색'을 누르세요")
        self.lbl_keyword_result.setFont(QFont("맑은 고딕", 9, QFont.Weight.Bold))
        self.lbl_keyword_result.setStyleSheet("color: #666;")
        result_layout.addWidget(self.lbl_keyword_result)

        self.list_keyword_risks = QListWidget()
        self.list_keyword_risks.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list_keyword_risks.setMinimumHeight(80)
        self.list_keyword_risks.setMaximumHeight(130)
        self.list_keyword_risks.setStyleSheet("QListWidget { border: 1px solid #2196F3; }")
        self.list_keyword_risks.itemDoubleClicked.connect(self.add_double_clicked_risk)
        result_layout.addWidget(self.list_keyword_risks)

        # 검색 결과 버튼
        keyword_btn_layout = QHBoxLayout()
        btn_keyword_select_all = QPushButton("전체 선택")
        btn_keyword_select_all.setMinimumHeight(24)
        btn_keyword_select_all.clicked.connect(self.select_all_keyword_risks)
        keyword_btn_layout.addWidget(btn_keyword_select_all)

        btn_keyword_deselect_all = QPushButton("전체 해제")
        btn_keyword_deselect_all.setMinimumHeight(24)
        btn_keyword_deselect_all.clicked.connect(self.deselect_all_keyword_risks)
        keyword_btn_layout.addWidget(btn_keyword_deselect_all)

        btn_add_keyword_selected = QPushButton("선택 항목 추가")
        btn_add_keyword_selected.setMinimumWidth(100)
        btn_add_keyword_selected.setMinimumHeight(24)
        btn_add_keyword_selected.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_add_keyword_selected.clicked.connect(self.add_keyword_selected_risks)
        keyword_btn_layout.addWidget(btn_add_keyword_selected)
        result_layout.addLayout(keyword_btn_layout)

        work_input_layout.addWidget(result_widget, 2)

        auto_layout.addLayout(work_input_layout)
        layout.addWidget(auto_group)

        # ===== 하단: 공종별 목록 선택 방식 =====
        select_group = QGroupBox("② 공종별 작업 목록에서 선택")
        select_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        select_group.setStyleSheet("QGroupBox { border: 2px solid #4CAF50; border-radius: 5px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { color: #4CAF50; }")
        select_layout = QVBoxLayout(select_group)

        # 공종 선택 콤보박스
        category_layout = QHBoxLayout()
        lbl_category = QLabel("공종 선택:")
        lbl_category.setFont(QFont("맑은 고딕", 10))
        category_layout.addWidget(lbl_category)
        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumWidth(200)
        self.cmb_category.setMinimumHeight(28)
        self.cmb_category.addItems(get_categories())
        self.cmb_category.currentTextChanged.connect(self.on_category_changed)
        category_layout.addWidget(self.cmb_category)
        category_layout.addStretch()
        select_layout.addLayout(category_layout)

        # 작업 유형 및 위험요소 목록 (좌우 배치)
        list_layout = QHBoxLayout()

        # 작업 유형 목록
        work_type_widget = QWidget()
        work_type_layout = QVBoxLayout(work_type_widget)
        work_type_layout.setContentsMargins(0, 0, 5, 0)
        lbl_work_type = QLabel("작업 유형:")
        lbl_work_type.setFont(QFont("맑은 고딕", 9, QFont.Weight.Bold))
        work_type_layout.addWidget(lbl_work_type)
        self.list_work_types = QListWidget()
        self.list_work_types.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_work_types.itemClicked.connect(self.on_work_type_selected)
        self.list_work_types.setMinimumHeight(120)
        self.list_work_types.setMaximumHeight(150)
        work_type_layout.addWidget(self.list_work_types)
        list_layout.addWidget(work_type_widget, 1)

        # 위험요소 목록
        risk_widget = QWidget()
        risk_layout = QVBoxLayout(risk_widget)
        risk_layout.setContentsMargins(5, 0, 0, 0)
        lbl_risks = QLabel("위험요소 (클릭하여 다중 선택):")
        lbl_risks.setFont(QFont("맑은 고딕", 9, QFont.Weight.Bold))
        risk_layout.addWidget(lbl_risks)
        self.list_risks = QListWidget()
        self.list_risks.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list_risks.setMinimumHeight(120)
        self.list_risks.setMaximumHeight(150)
        self.list_risks.itemDoubleClicked.connect(self.add_double_clicked_category_risk)
        risk_layout.addWidget(self.list_risks)
        list_layout.addWidget(risk_widget, 2)

        select_layout.addLayout(list_layout)

        # 선택 추가 버튼
        btn_select_layout = QHBoxLayout()
        btn_select_layout.addStretch()

        btn_select_all = QPushButton("전체 선택")
        btn_select_all.setMinimumHeight(28)
        btn_select_all.clicked.connect(self.select_all_risks)
        btn_select_layout.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("전체 해제")
        btn_deselect_all.setMinimumHeight(28)
        btn_deselect_all.clicked.connect(self.deselect_all_risks)
        btn_select_layout.addWidget(btn_deselect_all)

        btn_add_selected = QPushButton("선택 항목 추가")
        btn_add_selected.setMinimumWidth(120)
        btn_add_selected.setMinimumHeight(28)
        btn_add_selected.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_add_selected.clicked.connect(self.add_selected_risks)
        btn_select_layout.addWidget(btn_add_selected)

        select_layout.addLayout(btn_select_layout)

        layout.addWidget(select_group)

        # 초기 공종 로드
        self.on_category_changed(self.cmb_category.currentText())

        # ===== AI 자동생성 섹션 =====
        ai_group = QGroupBox("③ AI 자동생성 (KOSHA DB + OpenAI)")
        ai_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        ai_group.setStyleSheet(
            "QGroupBox { border: 2px solid #9C27B0; border-radius: 5px; "
            "margin-top: 10px; padding-top: 10px; } "
            "QGroupBox::title { color: #9C27B0; }"
        )
        ai_layout = QVBoxLayout(ai_group)

        ai_input_layout = QHBoxLayout()

        ai_input_layout.addWidget(QLabel("공정명:"))
        self.txt_ai_process = QLineEdit()
        self.txt_ai_process.setPlaceholderText("예: 소방시설공사")
        self.txt_ai_process.setMinimumHeight(28)
        self.txt_ai_process.setMinimumWidth(140)
        ai_input_layout.addWidget(self.txt_ai_process)

        ai_input_layout.addWidget(QLabel("공종/업종:"))
        self.txt_ai_trade = QLineEdit()
        self.txt_ai_trade.setPlaceholderText("예: 소방, 배관, 전기")
        self.txt_ai_trade.setMinimumHeight(28)
        self.txt_ai_trade.setMinimumWidth(140)
        ai_input_layout.addWidget(self.txt_ai_trade)

        ai_input_layout.addWidget(QLabel("세부작업(선택):"))
        self.txt_ai_work = QLineEdit()
        self.txt_ai_work.setPlaceholderText("예: 배관, 감지기")
        self.txt_ai_work.setMinimumHeight(28)
        self.txt_ai_work.setMinimumWidth(120)
        ai_input_layout.addWidget(self.txt_ai_work)

        self.btn_ai_generate = QPushButton("AI 자동생성")
        self.btn_ai_generate.setMinimumHeight(28)
        self.btn_ai_generate.setMinimumWidth(110)
        self.btn_ai_generate.setStyleSheet(
            "background-color: #9C27B0; color: white; font-weight: bold;"
        )
        self.btn_ai_generate.clicked.connect(self._on_ai_generate_clicked)
        ai_input_layout.addWidget(self.btn_ai_generate)

        ai_input_layout.addStretch()
        ai_layout.addLayout(ai_input_layout)

        self.lbl_ai_status = QLabel("KOSHA DB에서 관련 자료를 검색하고 OpenAI로 위험성평가 항목을 자동 생성합니다.")
        self.lbl_ai_status.setStyleSheet("color: #666; font-size: 9pt;")
        ai_layout.addWidget(self.lbl_ai_status)

        layout.addWidget(ai_group)
        self._ai_worker = None

        # 테이블
        table_group = QGroupBox("위험성평가 실시표 (KRAS 표준 양식)")
        table_group.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        table_layout = QVBoxLayout(table_group)

        # 버튼
        btn_layout = QHBoxLayout()

        btn_add = QPushButton("수동 추가")
        btn_add.clicked.connect(self.add_risk_manual)
        btn_layout.addWidget(btn_add)

        btn_edit = QPushButton("수정")
        btn_edit.clicked.connect(self.edit_risk)
        btn_layout.addWidget(btn_edit)

        btn_remove = QPushButton("삭제")
        btn_remove.clicked.connect(self.remove_risk)
        btn_layout.addWidget(btn_remove)

        btn_clear = QPushButton("전체 삭제")
        btn_clear.clicked.connect(self.clear_all)
        btn_layout.addWidget(btn_clear)

        btn_layout.addStretch()
        table_layout.addLayout(btn_layout)

        # 테이블 위젯
        self.table = QTableWidget()
        self.table.setColumnCount(16)
        self.table.setHorizontalHeaderLabels([
            "공정명", "세부작업명", "위험분류", "위험세부분류",
            "위험발생 상황 및 결과", "관련근거(법적기준)", "현재의 안전보건조치",
            "평가척도", "가능성(빈도)", "중대성(강도)", "현재 위험성",
            "위험성 감소대책", "개선후 위험성", "개선예정일", "완료일", "담당자"
        ])

        # 열 너비 설정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 100)   # 공정명
        self.table.setColumnWidth(1, 150)   # 세부작업명
        self.table.setColumnWidth(2, 100)   # 위험분류
        self.table.setColumnWidth(3, 120)   # 위험세부분류
        self.table.setColumnWidth(4, 250)   # 위험발생 상황
        self.table.setColumnWidth(5, 180)   # 관련근거
        self.table.setColumnWidth(6, 200)   # 현재조치
        self.table.setColumnWidth(7, 60)    # 평가척도
        self.table.setColumnWidth(8, 80)    # 가능성
        self.table.setColumnWidth(9, 80)    # 중대성
        self.table.setColumnWidth(10, 80)   # 현재위험성
        self.table.setColumnWidth(11, 250)  # 감소대책
        self.table.setColumnWidth(12, 80)   # 개선후
        self.table.setColumnWidth(13, 80)   # 예정일
        self.table.setColumnWidth(14, 80)   # 완료일
        self.table.setColumnWidth(15, 60)   # 담당자

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_layout.addWidget(self.table)

        layout.addWidget(table_group)

    def on_category_changed(self, category: str):
        """공종 선택 변경 시 작업 유형 목록 업데이트"""
        self.list_work_types.clear()
        self.list_risks.clear()

        work_types = get_work_types_by_category(category)
        for work_type in work_types:
            # RISK_DATA에 실제로 있는 작업만 표시
            if work_type in RISK_DATA:
                item = QListWidgetItem(work_type)
                risk_count = len(RISK_DATA[work_type])
                item.setText(f"{work_type} ({risk_count}개)")
                item.setData(Qt.ItemDataRole.UserRole, work_type)
                self.list_work_types.addItem(item)

    def on_work_type_selected(self, item: QListWidgetItem):
        """작업 유형 선택 시 위험요소 목록 업데이트"""
        self.list_risks.clear()

        work_type = item.data(Qt.ItemDataRole.UserRole)
        risks = get_risks_by_work_type(work_type)

        for i, risk in enumerate(risks):
            risk_text = f"[{risk['위험분류']}] {risk['위험세부분류']}: {risk['위험상황'][:40]}..."
            list_item = QListWidgetItem(risk_text)
            list_item.setData(Qt.ItemDataRole.UserRole, risk)
            self.list_risks.addItem(list_item)

    def select_all_risks(self):
        """위험요소 전체 선택"""
        for i in range(self.list_risks.count()):
            self.list_risks.item(i).setSelected(True)

    def deselect_all_risks(self):
        """위험요소 전체 해제"""
        for i in range(self.list_risks.count()):
            self.list_risks.item(i).setSelected(False)

    def add_selected_risks(self):
        """선택한 위험요소 추가"""
        selected_items = self.list_risks.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "알림", "추가할 위험요소를 선택하세요.")
            return

        # 선택된 작업 유형 가져오기
        work_type_item = self.list_work_types.currentItem()
        if work_type_item:
            selected_work_type = work_type_item.data(Qt.ItemDataRole.UserRole)
        else:
            selected_work_type = None

        count = 0
        for item in selected_items:
            risk = item.data(Qt.ItemDataRole.UserRole)
            assessment = self._create_assessment_from_risk(risk, selected_work_type)
            self.data_manager.add_assessment(assessment)
            self._add_row_to_table(assessment)
            count += 1

        # 선택 해제
        self.deselect_all_risks()
        QMessageBox.information(self, "완료", f"{count}개의 위험요소가 추가되었습니다.")

    def _create_assessment_from_risk(self, risk: dict, selected_work_type: str = None) -> dict:
        """위험 데이터로부터 평가 데이터 생성

        Args:
            risk: 위험 데이터 딕셔너리
            selected_work_type: 선택된 작업 유형 (공종별 선택 시 사용)
        """
        possibility = risk["가능성"]
        severity = risk["중대성"]
        score = possibility * severity

        if score <= 2:
            level = "낮음"
        elif score <= 4:
            level = "보통"
        else:
            level = "높음"

        # 개선 후 위험성은 한 단계 낮게 기본 설정
        after_possibility = max(1, possibility - 1)
        after_severity = severity
        after_score = after_possibility * after_severity

        if after_score <= 2:
            after_level = "낮음"
        elif after_score <= 4:
            after_level = "보통"
        else:
            after_level = "높음"

        # 선택된 작업 유형이 있으면 세부작업명으로 사용
        sub_work = selected_work_type if selected_work_type else risk["세부작업명"]

        # 기본정보 탭에서 선택한 업종을 공정명으로 변환하여 사용 (없으면 원본 데이터 사용)
        # 업종명에서 "업" 제거: "소방시설공사업" -> "소방시설공사"
        work_type = self.data_manager.company_info.get("work_type", "")
        if work_type:
            # 업종명을 공정명으로 변환 (끝에 "업"이 있으면 제거)
            if work_type.endswith("업"):
                process_name = work_type[:-1]
            else:
                process_name = work_type
        else:
            process_name = risk["공정명"]

        return {
            "process": process_name,
            "sub_work": sub_work,
            "risk_category": risk["위험분류"],
            "risk_detail": risk["위험세부분류"],
            "risk_situation": risk["위험상황"],
            "legal_basis": risk["관련근거"],
            "current_measures": "",
            "eval_scale": "3x3",
            "possibility": possibility,
            "severity": severity,
            "current_risk": score,
            "current_risk_level": level,
            "reduction_measures": risk["감소대책"],
            "after_possibility": after_possibility,
            "after_severity": after_severity,
            "after_risk": after_score,
            "after_risk_level": after_level,
            "due_date": "",
            "complete_date": "",
            "manager": "",
            "note": ""
        }

    def add_work_item(self):
        """작업사항 목록에 추가"""
        work_text = self.txt_work_input.text().strip()
        if not work_text:
            return

        # 중복 체크
        for i in range(self.list_work_items.count()):
            if self.list_work_items.item(i).text() == work_text:
                QMessageBox.warning(self, "알림", f"'{work_text}'은(는) 이미 추가되어 있습니다.")
                return

        self.list_work_items.addItem(work_text)
        self.txt_work_input.clear()
        self.txt_work_input.setFocus()

    def remove_work_item(self):
        """선택한 작업사항 삭제"""
        current_row = self.list_work_items.currentRow()
        if current_row >= 0:
            self.list_work_items.takeItem(current_row)

    def clear_work_items(self):
        """작업사항 전체 삭제"""
        self.list_work_items.clear()
        self.list_keyword_risks.clear()
        self.lbl_keyword_result.setText("검색 결과: 작업사항을 추가하고 클릭하거나 '전체 검색'을 누르세요")
        self.lbl_keyword_result.setStyleSheet("color: #666;")

    def on_work_item_clicked(self, item: QListWidgetItem):
        """작업사항 클릭 시 해당 항목만 검색"""
        work_text = item.text()
        self._search_and_display_risks([work_text])

    def search_all_work_items(self):
        """모든 작업사항에 대해 위험요소 검색"""
        if self.list_work_items.count() == 0:
            QMessageBox.warning(self, "알림", "검색할 작업사항을 추가하세요.")
            return

        work_items = []
        for i in range(self.list_work_items.count()):
            work_items.append(self.list_work_items.item(i).text())

        self._search_and_display_risks(work_items)

    def _search_and_display_risks(self, work_items: list):
        """작업사항 목록으로 위험요소 검색하여 표시"""
        self.list_keyword_risks.clear()

        all_risks = []
        found_keywords = []
        not_found_keywords = []

        for work_text in work_items:
            risks = find_risks_for_work(work_text)
            if risks:
                found_keywords.append(work_text)
                for risk in risks:
                    # 중복 방지 (같은 위험상황이면 스킵)
                    is_duplicate = False
                    for existing in all_risks:
                        if existing[0]["위험상황"] == risk["위험상황"]:
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        work_type = risk.get("세부작업명", "")
                        all_risks.append((risk, work_type, work_text))
            else:
                not_found_keywords.append(work_text)

        if not all_risks:
            self.lbl_keyword_result.setText(f"검색 결과: 위험요소를 찾을 수 없습니다. 아래 '공종별 선택' 또는 하단 테이블의 '수동 추가' 버튼을 이용하세요.")
            self.lbl_keyword_result.setStyleSheet("color: #FF5722;")
            return

        # 결과 메시지 구성
        result_msg = f"검색 결과: {len(all_risks)}개 위험요소 발견"
        if not_found_keywords:
            result_msg += f" (미발견: {', '.join(not_found_keywords)})"
        self.lbl_keyword_result.setText(result_msg)
        self.lbl_keyword_result.setStyleSheet("color: #4CAF50; font-weight: bold;")

        for risk, work_type, keyword in all_risks:
            # [키워드] [작업유형] [위험분류] 위험상황 표시
            risk_text = f"[{keyword}] [{work_type}] {risk['위험분류']}: {risk['위험상황'][:45]}..."
            list_item = QListWidgetItem(risk_text)
            list_item.setData(Qt.ItemDataRole.UserRole, risk)
            list_item.setData(Qt.ItemDataRole.UserRole + 1, work_type)
            self.list_keyword_risks.addItem(list_item)

    def add_double_clicked_risk(self, item: QListWidgetItem):
        """키워드 검색 결과에서 더블클릭한 위험요소 바로 추가"""
        risk = item.data(Qt.ItemDataRole.UserRole)
        work_type = item.data(Qt.ItemDataRole.UserRole + 1)
        assessment = self._create_assessment_from_risk(risk, work_type)
        self.data_manager.add_assessment(assessment)
        self._add_row_to_table(assessment)

        # 추가된 항목 목록에서 제거
        row = self.list_keyword_risks.row(item)
        self.list_keyword_risks.takeItem(row)

        # 결과 메시지 업데이트
        remaining = self.list_keyword_risks.count()
        if remaining > 0:
            self.lbl_keyword_result.setText(f"1개 추가 완료! 남은 항목: {remaining}개")
        else:
            self.lbl_keyword_result.setText("모든 항목이 추가되었습니다.")
        self.lbl_keyword_result.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def add_double_clicked_category_risk(self, item: QListWidgetItem):
        """공종별 선택에서 더블클릭한 위험요소 바로 추가"""
        risk = item.data(Qt.ItemDataRole.UserRole)

        # 선택된 작업 유형 가져오기
        work_type_item = self.list_work_types.currentItem()
        if work_type_item:
            selected_work_type = work_type_item.data(Qt.ItemDataRole.UserRole)
        else:
            selected_work_type = None

        assessment = self._create_assessment_from_risk(risk, selected_work_type)
        self.data_manager.add_assessment(assessment)
        self._add_row_to_table(assessment)

        # 추가된 항목 목록에서 제거
        row = self.list_risks.row(item)
        self.list_risks.takeItem(row)

    def select_all_keyword_risks(self):
        """키워드 검색 결과 전체 선택"""
        for i in range(self.list_keyword_risks.count()):
            self.list_keyword_risks.item(i).setSelected(True)

    def deselect_all_keyword_risks(self):
        """키워드 검색 결과 전체 해제"""
        for i in range(self.list_keyword_risks.count()):
            self.list_keyword_risks.item(i).setSelected(False)

    def add_keyword_selected_risks(self):
        """키워드 검색에서 선택한 위험요소 추가"""
        selected_items = self.list_keyword_risks.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "알림", "추가할 위험요소를 선택하세요.")
            return

        count = 0
        for item in selected_items:
            risk = item.data(Qt.ItemDataRole.UserRole)
            work_type = item.data(Qt.ItemDataRole.UserRole + 1)
            assessment = self._create_assessment_from_risk(risk, work_type)
            self.data_manager.add_assessment(assessment)
            self._add_row_to_table(assessment)
            count += 1

        # 선택 해제
        self.deselect_all_keyword_risks()
        QMessageBox.information(self, "완료", f"{count}개의 위험요소가 추가되었습니다.")

    def add_risk_manual(self):
        """수동으로 위험요소 추가"""
        dialog = AddRiskDialog(self, self.data_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            self.data_manager.add_assessment(dialog.result_data)
            self._add_row_to_table(dialog.result_data)

    def edit_risk(self):
        """선택한 위험요소 수정"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "알림", "수정할 항목을 선택하세요.")
            return

        if current_row >= len(self.data_manager.assessments):
            QMessageBox.warning(self, "알림", "유효하지 않은 항목입니다.")
            return

        # 기존 데이터 가져오기
        existing_data = self.data_manager.assessments[current_row]

        # 수정 다이얼로그 표시
        dialog = RiskDialog(self, self.data_manager, edit_data=existing_data)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            # 데이터 업데이트
            self.data_manager.assessments[current_row] = dialog.result_data
            # 테이블 새로고침
            self._update_row(current_row, dialog.result_data)
            QMessageBox.information(self, "완료", "위험요소가 수정되었습니다.")

    def remove_risk(self):
        """선택한 위험요소 삭제"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "알림", "삭제할 항목을 선택하세요.")
            return

        reply = QMessageBox.question(
            self, "삭제 확인",
            "선택한 항목을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.remove_assessment(current_row)
            self.table.removeRow(current_row)

    def clear_all(self):
        """전체 삭제"""
        if self.table.rowCount() == 0:
            return

        reply = QMessageBox.question(
            self, "전체 삭제 확인",
            "모든 위험요소를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.assessments.clear()
            self.table.setRowCount(0)

    def _add_row_to_table(self, data: dict):
        """테이블에 행 추가"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._set_row_data(row, data)

    def _update_row(self, row: int, data: dict):
        """테이블 행 업데이트"""
        self._set_row_data(row, data)

    def _set_row_data(self, row: int, data: dict):
        """테이블 행에 데이터 설정"""
        # 위험성 레벨에 따른 배경색 및 글자색
        color_map = {
            "낮음": (QColor("#92D050"), QColor("#000000")),  # 초록 배경, 검정 글씨
            "보통": (QColor("#FFA500"), QColor("#000000")),  # 주황 배경, 검정 글씨
            "높음": (QColor("#FF0000"), QColor("#FFFFFF")),  # 빨강 배경, 흰색 글씨
        }

        current_level = data.get("current_risk_level", "")
        after_level = data.get("after_risk_level", "")
        current_bg, current_fg = color_map.get(current_level, (QColor("#FFFFFF"), QColor("#000000")))
        after_bg, after_fg = color_map.get(after_level, (QColor("#FFFFFF"), QColor("#000000")))

        items = [
            data.get("process", ""),
            data.get("sub_work", ""),
            data.get("risk_category", ""),
            data.get("risk_detail", ""),
            data.get("risk_situation", ""),
            data.get("legal_basis", ""),
            data.get("current_measures", ""),
            data.get("eval_scale", "3x3"),
            self.data_manager.format_possibility(data.get("possibility", 1)),
            self.data_manager.format_severity(data.get("severity", 1)),
            self.data_manager.format_risk_level(data.get("current_risk", 1), current_level),
            data.get("reduction_measures", ""),
            self.data_manager.format_risk_level(data.get("after_risk", 1), after_level),
            data.get("due_date", ""),
            data.get("complete_date", ""),
            data.get("manager", ""),
        ]

        for col, value in enumerate(items):
            item = QTableWidgetItem(str(value))
            if col == 10:  # 현재 위험성 컬럼
                item.setBackground(current_bg)
                item.setForeground(current_fg)
            elif col == 12:  # 개선후 위험성 컬럼
                item.setBackground(after_bg)
                item.setForeground(after_fg)
            self.table.setItem(row, col, item)

    def collect_data(self):
        """테이블에서 데이터 수집 (이미 data_manager에 저장되어 있음)"""
        pass

    def refresh_data(self):
        """데이터 새로고침"""
        self.table.setRowCount(0)
        for assessment in self.data_manager.assessments:
            self._add_row_to_table(assessment)
        self.update_company_info()

    def update_company_info(self):
        """기본정보 탭에서 연동된 데이터 업데이트"""
        info = self.data_manager.company_info
        self.lbl_company.setText(f"회사명: {info.get('company_name', '-')}")
        self.lbl_site.setText(f"현장명: {info.get('site_name', '-')}")
        self.lbl_date.setText(f"평가일자: {info.get('eval_date', '-')}")

        # AI 입력 필드에 공정명 자동 채우기 (비어 있을 때만)
        if not self.txt_ai_process.text():
            work_type = info.get("work_type", "")
            if work_type:
                process = work_type[:-1] if work_type.endswith("업") else work_type
                self.txt_ai_process.setText(process)

    # ── AI 자동생성 ─────────────────────────────────────────────────────────

    def _on_ai_generate_clicked(self):
        """AI 자동생성 버튼 클릭"""
        trade_type = self.txt_ai_trade.text().strip()
        if not trade_type:
            QMessageBox.warning(self, "입력 오류", "공종/업종을 입력하세요.")
            return

        if self._ai_worker and self._ai_worker.isRunning():
            return

        process_name = self.txt_ai_process.text().strip() or trade_type
        work_type = self.txt_ai_work.text().strip()

        self.btn_ai_generate.setEnabled(False)
        self.lbl_ai_status.setText("KOSHA DB 검색 중...")
        self.lbl_ai_status.setStyleSheet("color: #FF6600; font-weight: bold;")

        self._ai_worker = AIGenerateWorker(process_name, trade_type, work_type)
        self._ai_worker.finished.connect(self._on_ai_finished)
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.start()

    def _on_ai_finished(self, items: list):
        """AI 생성 완료"""
        self.btn_ai_generate.setEnabled(True)
        if not items:
            self.lbl_ai_status.setText("생성된 항목이 없습니다. 검색어를 바꿔보세요.")
            self.lbl_ai_status.setStyleSheet("color: #FF5722;")
            return

        for item in items:
            assessment = self._create_assessment_from_ai_item(item)
            self.data_manager.add_assessment(assessment)
            self._add_row_to_table(assessment)

        self.lbl_ai_status.setText(f"완료: {len(items)}개 항목이 추가되었습니다.")
        self.lbl_ai_status.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def _on_ai_error(self, msg: str):
        """AI 생성 오류"""
        self.btn_ai_generate.setEnabled(True)
        self.lbl_ai_status.setText(f"오류: {msg[:80]}")
        self.lbl_ai_status.setStyleSheet("color: #F44336; font-weight: bold;")
        QMessageBox.critical(self, "AI 자동생성 오류", msg)

    def _create_assessment_from_ai_item(self, item: dict) -> dict:
        """OpenAI 엔진 결과를 assessment dict로 변환"""
        prob = item.get("가능성", 2)
        sev = item.get("중대성", 2)
        score = prob * sev
        level = item.get("위험등급", "보통")

        after_prob = max(1, prob - 1)
        after_sev = sev
        after_score = after_prob * after_sev
        if after_score <= 2:
            after_level = "낮음"
        elif after_score <= 4:
            after_level = "보통"
        else:
            after_level = "높음"

        return {
            "process": item.get("공정명", ""),
            "sub_work": item.get("세부작업명", ""),
            "risk_category": item.get("위험분류", "기타"),
            "risk_detail": item.get("위험세부분류", ""),
            "risk_situation": item.get("위험상황", ""),
            "legal_basis": item.get("관련근거", ""),
            "current_measures": item.get("현재조치", ""),
            "eval_scale": "3x3",
            "possibility": prob,
            "severity": sev,
            "current_risk": score,
            "current_risk_level": level,
            "reduction_measures": item.get("감소대책", ""),
            "after_possibility": after_prob,
            "after_severity": after_sev,
            "after_risk": after_score,
            "after_risk_level": after_level,
            "due_date": "",
            "complete_date": "",
            "manager": "",
            "note": "",
        }

# -*- coding: utf-8 -*-
"""
위험성평가표 자동생성기 - 메인 애플리케이션
PyQt6 기반 GUI
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QStatusBar, QMenuBar, QMenu,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMetaObject, Q_ARG, Qt as QtCore
from PyQt6.QtGui import QAction, QFont

from gui.company_info_tab import CompanyInfoTab
from gui.organization_tab import OrganizationTab
from gui.risk_assessment_tab import RiskAssessmentTab
from gui.meeting_form_tab import MeetingFormTab
from gui.risk_criteria_tab import RiskCriteriaTab
from core.data_manager import DataManager
from export.excel_exporter import ExcelExporter

# 앱 소켓 모듈 경로 추가
_socket_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "00. 앱런처")
sys.path.insert(0, _socket_path)
print(f"[DEBUG] 소켓 모듈 경로: {_socket_path}")
try:
    from app_socket import AppSocketServer
    print("[DEBUG] app_socket 모듈 import 성공")
except ImportError as e:
    print(f"[ERROR] app_socket import 실패: {e}")
    AppSocketServer = None


class MainWindow(QMainWindow):
    """메인 윈도우"""

    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.init_ui()
        self.connect_signals()
        self.init_socket_server()

    def init_socket_server(self):
        """소켓 서버 초기화 - MCP 연동"""
        if AppSocketServer is None:
            print("[ERROR] AppSocketServer를 사용할 수 없습니다.")
            self.socket_server = None
            return

        try:
            print("[DEBUG] 소켓 서버 초기화 시작...")
            self.socket_server = AppSocketServer(port=8002)
            print("[DEBUG] AppSocketServer 객체 생성 완료")

            # 핸들러 등록
            self.socket_server.register_handler("get_status", self._handle_get_status)
            self.socket_server.register_handler("set_company_info", self._handle_set_company_info)
            self.socket_server.register_handler("add_assessment", self._handle_add_assessment)
            self.socket_server.register_handler("get_assessments", self._handle_get_assessments)
            self.socket_server.register_handler("get_all_data", self._handle_get_all_data)
            self.socket_server.register_handler("clear_data", self._handle_clear_data)
            self.socket_server.register_handler("save_to_file", self._handle_save_to_file)
            self.socket_server.register_handler("export_excel", self._handle_export_excel)
            # 조직구성
            self.socket_server.register_handler("set_organization", self._handle_set_organization)
            self.socket_server.register_handler("add_member", self._handle_add_member)
            # 회의/교육/안전점검회의
            self.socket_server.register_handler("set_meeting", self._handle_set_meeting)
            self.socket_server.register_handler("add_meeting_attendee", self._handle_add_meeting_attendee)
            self.socket_server.register_handler("set_education", self._handle_set_education)
            self.socket_server.register_handler("set_safety_meeting", self._handle_set_safety_meeting)
            print("[DEBUG] 핸들러 등록 완료")

            self.socket_server.start()

            # 서버 시작 확인
            import socket
            import time
            time.sleep(0.5)
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = test_sock.connect_ex(('127.0.0.1', 8002))
            test_sock.close()

            if result == 0:
                print("[DEBUG] 소켓 서버 정상 작동 (포트 8002 열림)")
                self.statusBar().showMessage("준비 완료 - MCP 연동 활성화 (포트 8002)")
            else:
                print(f"[WARNING] 소켓 서버 포트 확인 실패 (결과: {result})")
                self.statusBar().showMessage("준비 완료 - MCP 연동 확인 필요")

        except Exception as e:
            print(f"[ERROR] 소켓 서버 시작 실패: {e}")
            import traceback
            traceback.print_exc()
            self.socket_server = None

    def _handle_get_status(self, params):
        """앱 상태 조회"""
        return {
            "status": "ok",
            "app_name": "위험성평가표 자동생성기",
            "company_info": self.data_manager.company_info,
            "assessment_count": len(self.data_manager.assessments)
        }

    def _handle_set_company_info(self, params):
        """기본정보 설정"""
        for key, value in params.items():
            if key in self.data_manager.company_info:
                self.data_manager.company_info[key] = value
        # UI 업데이트 제거 - 안정성 우선
        return {"status": "ok", "message": "기본정보가 설정되었습니다."}

    def _handle_add_assessment(self, params):
        """위험성평가 항목 추가"""
        # 필수 필드 확인
        required = ["process", "sub_work", "risk_situation"]
        for field in required:
            if field not in params:
                return {"status": "error", "message": f"필수 필드 누락: {field}"}

        # 기본값 설정
        assessment = {
            "process": params.get("process", ""),
            "sub_work": params.get("sub_work", ""),
            "risk_category": params.get("risk_category", ""),
            "risk_detail": params.get("risk_detail", ""),
            "risk_situation": params.get("risk_situation", ""),
            "legal_basis": params.get("legal_basis", ""),
            "current_measures": params.get("current_measures", ""),
            "eval_scale": "3x3",
            "possibility": params.get("possibility", 2),
            "severity": params.get("severity", 2),
            "current_risk": 0,
            "current_risk_level": "",
            "reduction_measures": params.get("reduction_measures", ""),
            "after_risk": 0,
            "after_risk_level": "",
            "due_date": params.get("due_date", ""),
            "complete_date": "",
            "manager": params.get("manager", ""),
            "note": params.get("note", "")
        }

        # 위험성 계산
        score, level = self.data_manager.calculate_risk(
            assessment["possibility"],
            assessment["severity"]
        )
        assessment["current_risk"] = score
        assessment["current_risk_level"] = level

        # 감소 후 위험성 계산 (가능성 1 감소 가정)
        after_possibility = max(1, assessment["possibility"] - 1)
        after_score, after_level = self.data_manager.calculate_risk(
            after_possibility,
            assessment["severity"]
        )
        assessment["after_risk"] = after_score
        assessment["after_risk_level"] = after_level

        self.data_manager.add_assessment(assessment)
        # UI 업데이트 제거 - 안정성 우선

        return {
            "status": "ok",
            "message": "위험성평가 항목이 추가되었습니다.",
            "assessment": assessment,
            "total_count": len(self.data_manager.assessments)
        }

    def _handle_get_assessments(self, params):
        """위험성평가 목록 조회"""
        return {
            "status": "ok",
            "count": len(self.data_manager.assessments),
            "assessments": self.data_manager.assessments
        }

    def _handle_get_all_data(self, params):
        """전체 데이터 조회"""
        # collect_all_data() 제거 - UI에서 데이터를 수집하면 소켓으로 설정한 데이터가 덮어씌워짐
        return {
            "status": "ok",
            "data": self.data_manager.get_all_data()
        }

    def _handle_clear_data(self, params):
        """데이터 초기화"""
        self.data_manager.clear()
        # UI 업데이트 제거 - 안정성 우선
        return {"status": "ok", "message": "데이터가 초기화되었습니다."}

    def _handle_save_to_file(self, params):
        """파일로 저장"""
        file_path = params.get("file_path", "")
        if not file_path:
            return {"status": "error", "message": "file_path가 필요합니다."}

        # collect_all_data() 제거 - 소켓으로 설정한 데이터 유지
        self.data_manager.save_to_file(file_path)
        return {"status": "ok", "message": f"저장 완료: {file_path}"}

    def _handle_export_excel(self, params):
        """엑셀 내보내기"""
        file_path = params.get("file_path", "")
        if not file_path:
            return {"status": "error", "message": "file_path가 필요합니다."}

        # collect_all_data() 제거 - 소켓으로 설정한 데이터 유지
        exporter = ExcelExporter(self.data_manager)
        exporter.export(file_path)
        return {"status": "ok", "message": f"엑셀 내보내기 완료: {file_path}"}

    # ========== 조직구성 핸들러 ==========
    def _handle_set_organization(self, params):
        """조직구성 설정"""
        members = params.get("members", [])
        self.data_manager.organization["members"] = members
        # UI 업데이트 제거 - 안정성 우선
        return {"status": "ok", "message": f"조직구성 {len(members)}명 설정됨"}

    def _handle_add_member(self, params):
        """조직구성원 추가"""
        member = {
            "position": params.get("position", ""),
            "name": params.get("name", ""),
            "role": params.get("role", ""),
            "responsibility": params.get("responsibility", "")
        }
        self.data_manager.organization["members"].append(member)
        # UI 업데이트 제거 - 안정성 우선
        return {"status": "ok", "message": f"구성원 '{member['name']}' 추가됨", "total": len(self.data_manager.organization["members"])}

    # ========== 회의 결과 핸들러 ==========
    def _handle_set_meeting(self, params):
        """회의 결과 설정"""
        self.data_manager.meeting["date"] = params.get("date", "")
        self.data_manager.meeting["time_start"] = params.get("time_start", "")
        self.data_manager.meeting["time_end"] = params.get("time_end", "")
        self.data_manager.meeting["location"] = params.get("location", "")
        self.data_manager.meeting["content"] = params.get("content", "")
        if "attendees" in params:
            self.data_manager.meeting["attendees"] = params["attendees"]
        # UI 업데이트 제거 - 안정성 우선
        return {"status": "ok", "message": "회의 결과 설정됨"}

    def _handle_add_meeting_attendee(self, params):
        """회의 참석자 추가"""
        attendee = {
            "department": params.get("department", ""),
            "position": params.get("position", ""),
            "name": params.get("name", ""),
            "signature": params.get("signature", "")
        }
        self.data_manager.meeting["attendees"].append(attendee)
        # UI 업데이트 제거 - 안정성 우선
        return {"status": "ok", "message": f"참석자 '{attendee['name']}' 추가됨"}

    # ========== 교육 결과 핸들러 ==========
    def _handle_set_education(self, params):
        """교육 결과 설정"""
        self.data_manager.education["date"] = params.get("date", "")
        self.data_manager.education["content"] = params.get("content", "")
        if "attendees" in params:
            self.data_manager.education["attendees"] = params["attendees"]
        # UI 업데이트 제거 - 안정성 우선
        return {"status": "ok", "message": "교육 결과 설정됨"}

    # ========== 안전점검회의 핸들러 ==========
    def _handle_set_safety_meeting(self, params):
        """작업 전 안전점검회의 설정"""
        self.data_manager.safety_meeting["date"] = params.get("date", "")
        self.data_manager.safety_meeting["content"] = params.get("content", "")
        if "attendees" in params:
            self.data_manager.safety_meeting["attendees"] = params["attendees"]
        # UI 업데이트 제거 - 안정성 우선
        return {"status": "ok", "message": "안전점검회의 설정됨"}

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("위험성평가표 자동생성기 v2.0")
        self.setMinimumSize(1200, 800)

        # 메뉴바 설정
        self.setup_menubar()

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 상단 타이틀
        title_label = QLabel("위험성평가표 자동생성기")
        title_label.setFont(QFont("맑은 고딕", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(title_label)

        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("맑은 고딕", 10))
        main_layout.addWidget(self.tab_widget)

        # 탭 추가
        self.company_info_tab = CompanyInfoTab(self.data_manager)
        self.organization_tab = OrganizationTab(self.data_manager)
        self.risk_criteria_tab = RiskCriteriaTab(self.data_manager)
        self.risk_assessment_tab = RiskAssessmentTab(self.data_manager)
        self.meeting_form_tab = MeetingFormTab(self.data_manager)

        self.tab_widget.addTab(self.company_info_tab, "1. 기본정보")
        self.tab_widget.addTab(self.organization_tab, "2. 조직구성")
        self.tab_widget.addTab(self.risk_criteria_tab, "3. 위험성 추정·결정 기준")
        self.tab_widget.addTab(self.risk_assessment_tab, "4. 위험성평가 실시")
        self.tab_widget.addTab(self.meeting_form_tab, "5. 회의 및 서식")

        # 하단 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_save = QPushButton("저장")
        self.btn_save.setFixedSize(120, 40)
        self.btn_save.clicked.connect(self.save_data)
        button_layout.addWidget(self.btn_save)

        self.btn_load = QPushButton("불러오기")
        self.btn_load.setFixedSize(120, 40)
        self.btn_load.clicked.connect(self.load_data)
        button_layout.addWidget(self.btn_load)

        self.btn_export = QPushButton("엑셀 내보내기")
        self.btn_export.setFixedSize(150, 40)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.btn_export.clicked.connect(self.export_to_excel)
        button_layout.addWidget(self.btn_export)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 상태바
        self.statusBar().showMessage("준비 완료")

    def connect_signals(self):
        """시그널 연결 - 기본정보 변경 시 다른 탭 자동 업데이트"""
        self.company_info_tab.data_changed.connect(self.on_company_info_changed)

    def on_company_info_changed(self):
        """기본정보 변경 시 호출"""
        # 기본정보 수집
        self.company_info_tab.collect_data()

        # 다른 탭들에 정보 전달
        self.risk_assessment_tab.update_company_info()
        self.meeting_form_tab.update_company_info()
        self.organization_tab.update_company_info()

        self.statusBar().showMessage("기본정보가 업데이트되었습니다.")

    def setup_menubar(self):
        """메뉴바 설정"""
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")

        new_action = QAction("새로 만들기(&N)", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_document)
        file_menu.addAction(new_action)

        open_action = QAction("열기(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_data)
        file_menu.addAction(open_action)

        save_action = QAction("저장(&S)", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_data)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        export_action = QAction("엑셀로 내보내기(&E)", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_to_excel)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")

        about_action = QAction("정보(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def new_document(self):
        """새 문서 만들기"""
        reply = QMessageBox.question(
            self, "새로 만들기",
            "현재 내용을 모두 지우고 새로 시작하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.clear()
            self.refresh_all_tabs()
            self.statusBar().showMessage("새 문서가 생성되었습니다.")

    def save_data(self):
        """데이터 저장"""
        self.collect_all_data()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "저장", "", "JSON 파일 (*.json)"
        )
        if file_path:
            self.data_manager.save_to_file(file_path)
            self.statusBar().showMessage(f"저장 완료: {file_path}")

    def load_data(self):
        """데이터 불러오기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "열기", "", "JSON 파일 (*.json)"
        )
        if file_path:
            self.data_manager.load_from_file(file_path)
            self.refresh_all_tabs()
            self.statusBar().showMessage(f"불러오기 완료: {file_path}")

    def export_to_excel(self):
        """엑셀로 내보내기"""
        self.collect_all_data()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "엑셀로 내보내기", "", "Excel 파일 (*.xlsx)"
        )
        if file_path:
            exporter = ExcelExporter(self.data_manager)
            exporter.export(file_path)
            self.statusBar().showMessage(f"엑셀 내보내기 완료: {file_path}")
            QMessageBox.information(self, "완료", f"엑셀 파일이 생성되었습니다.\n{file_path}")

    def collect_all_data(self):
        """모든 탭에서 데이터 수집"""
        self.company_info_tab.collect_data()
        self.organization_tab.collect_data()
        self.risk_criteria_tab.collect_data()
        self.risk_assessment_tab.collect_data()
        self.meeting_form_tab.collect_data()

    def refresh_all_tabs(self):
        """모든 탭 새로고침"""
        self.company_info_tab.refresh_data()
        self.organization_tab.refresh_data()
        self.risk_criteria_tab.refresh_data()
        self.risk_assessment_tab.refresh_data()
        self.meeting_form_tab.refresh_data()

    def show_about(self):
        """프로그램 정보"""
        QMessageBox.about(
            self, "위험성평가표 자동생성기",
            "위험성평가표 자동생성기 v2.0\n\n"
            "KRAS 표준 위험성평가 양식 기준\n"
            "빈도·강도법에 의한 위험성 평가\n\n"
            "참조: 사업장 위험성평가에 관한 지침"
        )

    def closeEvent(self, event):
        """앱 종료 시 소켓 서버 중지"""
        if hasattr(self, 'socket_server') and self.socket_server:
            self.socket_server.stop()
            print("[DEBUG] 소켓 서버 종료됨")
        event.accept()


def main():
    app = QApplication(sys.argv)

    # 스타일 설정
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

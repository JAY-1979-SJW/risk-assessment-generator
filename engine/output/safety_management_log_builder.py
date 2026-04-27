"""
안전관리 일지 — Excel 출력 모듈 (v1).

법적 근거: 중대재해처벌법 시행령 제4조 (안전보건관리체계 구축 의무)
분류: PRACTICAL — 법정 별지 서식 없음, 실무 자체 표준 일지서식

요약:
    현장 관리자가 현장의 당일 안전관리 현황을 종합적으로 기록하는 일지입니다.
    작업 현황, 인원 현황, 위험작업 관리, TBM/위험성평가/보호구 확인,
    안전순찰 결과, 지적사항, 사고·아차사고, 개선조치 등을 포함합니다.

Required form_data keys:
    site_name           str  현장명
    log_date            str  일지 작성 일자
    writer_name         str  작성자 성명
    weather             str  날씨
    work_summary        str  당일 주요 작업 요약

Optional form_data keys:
    project_name                str  공사명
    department                  str  소속 부서
    position                    str  직책
    work_location               str  작업 구역
    work_start_time             str  작업 시작 시간
    work_end_time               str  작업 종료 시간
    worker_count                str  당일 작업 인원
    subcontractor_count         str  협력업체 인원
    visitor_count               str  방문자 수
    main_work                   str  주요 작업 내용 (상세)
    high_risk_work              str  위험작업 여부 및 내용
    safety_meeting_done         str  안전조회 실시 여부
    tbm_done                    str  TBM 실시 여부
    risk_assessment_checked     str  위험성평가 확인 여부
    equipment_check_done        str  장비·공구 점검 완료 여부
    ppe_check_done              str  보호구 착용 확인 여부
    site_patrol_done            str  안전순찰 실시 여부
    nonconformance_found        str  불안전 사항 발견 여부
    corrective_action           str  조치 내용
    accident_or_near_miss       str  사고·아차사고 여부
    weather_condition           str  기상 상세
    heat_cold_risk              str  온열/한랭 질환 위험 여부
    emergency_contact_checked   str  비상연락망 확인 여부
    remarks                     str  특이사항 및 종합 의견
    reviewer_name               str  검토자
    approver_name               str  승인자
    equipment_status            str  장비 상태
    housekeeping_status         str  작업장 정리정돈 상태
    management_notes            str  관리사항
    accident_detail             str  사고·아차사고 상세 내용
    corrective_action_completed str  조치 완료 여부
    follow_up_items             str  후속관리 사항
    nonconformance_items        list[dict]  지적사항 반복행 (max 10)
        location                str  위치
        description             str  지적내용
        action                  str  조치내용
        status                  str  상태
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

SHEET_NAME = "안전관리일지"
SHEET_HEADING = "안전관리 일지"
SHEET_SUBTITLE = "「중대재해처벌법」 시행령 제4조에 따른 현장 안전관리 종합기록"
DOC_ID = "DL-001"

TOTAL_COLS = 8
MAX_NONCONFORMANCE_ROWS = 10

_FONT_TITLE = Font(name="맑은 고딕", size=14, bold=True)
_FONT_SUBTITLE = Font(name="맑은 고딕", size=9, italic=True)
_FONT_BOLD = Font(name="맑은 고딕", size=10, bold=True)
_FONT_DEFAULT = Font(name="맑은 고딕", size=10)
_FONT_SMALL = Font(name="맑은 고딕", size=9)

_FILL_LABEL = PatternFill(fill_type="solid", fgColor="F2F2F2")
_FILL_SECTION = PatternFill(fill_type="solid", fgColor="D9E1F2")
_FILL_HEADER = PatternFill(fill_type="solid", fgColor="E2EFDA")
_FILL_NONE = PatternFill()

_THIN = Side(border_style="thin", color="808080")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)

_ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
_ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
_ALIGN_LABEL = Alignment(horizontal="center", vertical="center")

_COL_WIDTHS: Dict[int, int] = {1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10}

_L1, _V1_START, _V1_END = 1, 2, 4
_L2, _V2_START, _V2_END = 5, 6, 8


def _v(data: Dict[str, Any], key: str) -> Any:
    val = data.get(key)
    return "" if val is None else val


def _border_rect(ws, row1: int, col1: int, row2: int, col2: int) -> None:
    for r in range(row1, row2 + 1):
        for c in range(col1, col2 + 1):
            ws.cell(row=r, column=c).border = _BORDER


def _write_cell(ws, row: int, col1: int, col2: int, value: Any, *,
                font=None, fill=None, align=None,
                height: Optional[int] = None) -> None:
    if col2 > col1:
        ws.merge_cells(start_row=row, start_column=col1,
                       end_row=row, end_column=col2)
    cell = ws.cell(row=row, column=col1)
    cell.value = "" if value is None else value
    cell.font = font or _FONT_DEFAULT
    cell.fill = fill or _FILL_NONE
    cell.alignment = align or _ALIGN_LEFT
    _border_rect(ws, row, col1, row, col2)
    if height is not None:
        ws.row_dimensions[row].height = height


def _write_lv(ws, row: int, label: str, value: Any,
              label_col: int, val_col1: int, val_col2: int) -> None:
    _write_cell(ws, row, label_col, label_col, label,
                font=_FONT_BOLD, fill=_FILL_LABEL, align=_ALIGN_LABEL)
    _write_cell(ws, row, val_col1, val_col2, value,
                font=_FONT_DEFAULT, align=_ALIGN_LEFT)


def _apply_col_widths(ws) -> None:
    for col_idx, width in _COL_WIDTHS.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width


def _write_title(ws, row: int) -> int:
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=TOTAL_COLS)
    cell = ws.cell(row=row, column=1, value=SHEET_HEADING)
    cell.font = _FONT_TITLE
    cell.alignment = _ALIGN_CENTER
    ws.row_dimensions[row].height = 28
    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=TOTAL_COLS)
    sub = ws.cell(row=row, column=1, value=SHEET_SUBTITLE)
    sub.font = _FONT_SUBTITLE
    sub.alignment = _ALIGN_CENTER
    ws.row_dimensions[row].height = 16
    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=TOTAL_COLS)
    doc_id = ws.cell(row=row, column=1, value=f"(문서ID: {DOC_ID})")
    doc_id.font = _FONT_SMALL
    doc_id.alignment = _ALIGN_CENTER
    ws.row_dimensions[row].height = 12
    return row + 1


def _write_site_info(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "현장 기본정보",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_lv(ws, r, "현장명", _v(data, "site_name"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "공사명", _v(data, "project_name"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_lv(ws, r, "소속 부서", _v(data, "department"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "직책", _v(data, "position"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    return r


def _write_log_info(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "일지 기본정보",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_lv(ws, r, "작성 일자", _v(data, "log_date"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "날씨", _v(data, "weather"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_lv(ws, r, "기상 상세", _v(data, "weather_condition"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "작성자", _v(data, "writer_name"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    return r


def _write_work_status(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "당일 작업 현황",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_lv(ws, r, "작업 구역", _v(data, "work_location"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "시작 시간", _v(data, "work_start_time"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_lv(ws, r, "종료 시간", _v(data, "work_end_time"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "주요 작업", _v(data, "main_work"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, f"위험작업: {_v(data, 'high_risk_work')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, f"작업 요약: {_v(data, 'work_summary')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    return r


def _write_personnel(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "인원 및 협력업체 현황",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_lv(ws, r, "작업 인원", _v(data, "worker_count"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "협력업체", _v(data, "subcontractor_count"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_lv(ws, r, "방문자 수", _v(data, "visitor_count"), _L1, _V1_START, _V1_END)
    ws.row_dimensions[r].height = H
    r += 1
    return r


def _write_risk_management(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "주요 위험작업 및 관리사항",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, f"위험작업: {_v(data, 'high_risk_work')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, f"온열/한랭 위험: {_v(data, 'heat_cold_risk')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, f"관리사항: {_v(data, 'management_notes')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    return r


def _write_safety_checks(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "TBM / 위험성평가 / 보호구 확인",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_lv(ws, r, "안전조회", _v(data, "safety_meeting_done"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "TBM", _v(data, "tbm_done"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_lv(ws, r, "위험성평가 확인", _v(data, "risk_assessment_checked"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "보호구 확인", _v(data, "ppe_check_done"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_lv(ws, r, "비상연락망", _v(data, "emergency_contact_checked"), _L1, _V1_START, _V1_END)
    ws.row_dimensions[r].height = H
    r += 1
    return r


def _write_equipment_check(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "장비·공구·작업장 상태 확인",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_lv(ws, r, "점검 완료", _v(data, "equipment_check_done"), _L1, _V1_START, _V1_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, f"장비 상태: {_v(data, 'equipment_status')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, f"정리정돈: {_v(data, 'housekeeping_status')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    return r


def _write_safety_patrol(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "안전순찰 및 지적사항",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_lv(ws, r, "순찰 실시", _v(data, "site_patrol_done"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "지적사항 발견", _v(data, "nonconformance_found"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1

    _write_cell(ws, r, 1, 2, "위치", font=_FONT_BOLD, fill=_FILL_HEADER, align=_ALIGN_CENTER)
    _write_cell(ws, r, 3, 5, "지적내용", font=_FONT_BOLD, fill=_FILL_HEADER, align=_ALIGN_CENTER)
    _write_cell(ws, r, 6, 7, "조치내용", font=_FONT_BOLD, fill=_FILL_HEADER, align=_ALIGN_CENTER)
    _write_cell(ws, r, 8, 8, "상태", font=_FONT_BOLD, fill=_FILL_HEADER, align=_ALIGN_CENTER)
    ws.row_dimensions[r].height = 18
    r += 1

    items = data.get("nonconformance_items", [])
    if not isinstance(items, list):
        items = []

    num_items = min(len(items), MAX_NONCONFORMANCE_ROWS)
    for i in range(MAX_NONCONFORMANCE_ROWS):
        if i < num_items:
            item = items[i]
            _write_cell(ws, r, 1, 2, _v(item, "location"), align=_ALIGN_LEFT, height=H)
            _write_cell(ws, r, 3, 5, _v(item, "description"), align=_ALIGN_LEFT, height=H)
            _write_cell(ws, r, 6, 7, _v(item, "action"), align=_ALIGN_LEFT, height=H)
            _write_cell(ws, r, 8, 8, _v(item, "status"), align=_ALIGN_CENTER, height=H)
        else:
            _write_cell(ws, r, 1, 2, "", height=H)
            _write_cell(ws, r, 3, 5, "", height=H)
            _write_cell(ws, r, 6, 7, "", height=H)
            _write_cell(ws, r, 8, 8, "", height=H)
        r += 1

    return r


def _write_accident_record(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "사고·아차사고·이상상황 기록",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_lv(ws, r, "발생 여부", _v(data, "accident_or_near_miss"), _L1, _V1_START, _V1_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, f"상세 내용: {_v(data, 'accident_detail')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    return r


def _write_corrective_actions(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "개선조치 및 후속관리",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, f"조치 내용: {_v(data, 'corrective_action')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    _write_lv(ws, r, "완료 여부", _v(data, "corrective_action_completed"), _L1, _V1_START, _V1_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, f"후속관리: {_v(data, 'follow_up_items')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    return r


def _write_remarks(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "종합 의견",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS, _v(data, "remarks"),
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    return r


def _write_signatures(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "작성 / 검토 / 승인 서명란",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_lv(ws, r, "작성자", _v(data, "writer_name"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "검토자", _v(data, "reviewer_name"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_lv(ws, r, "승인자", _v(data, "approver_name"), _L1, _V1_START, _V1_END)
    ws.row_dimensions[r].height = H
    r += 1
    return r


def build_safety_management_log(form_data: Dict[str, Any]) -> bytes:
    """안전관리 일지 Excel 생성."""
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    _apply_col_widths(ws)

    r = _write_title(ws, 1)
    r += 1
    r = _write_site_info(ws, r, form_data)
    r = _write_log_info(ws, r, form_data)
    r += 1
    r = _write_work_status(ws, r, form_data)
    r += 1
    r = _write_personnel(ws, r, form_data)
    r += 1
    r = _write_risk_management(ws, r, form_data)
    r += 1
    r = _write_safety_checks(ws, r, form_data)
    r += 1
    r = _write_equipment_check(ws, r, form_data)
    r += 1
    r = _write_safety_patrol(ws, r, form_data)
    r += 1
    r = _write_accident_record(ws, r, form_data)
    r += 1
    r = _write_corrective_actions(ws, r, form_data)
    r += 1
    r = _write_remarks(ws, r, form_data)
    r += 1
    r = _write_signatures(ws, r, form_data)

    output = BytesIO()
    wb.save(output)
    return output.getvalue()

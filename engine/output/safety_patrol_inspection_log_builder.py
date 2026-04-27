"""
안전순찰 점검 일지 — Excel 출력 모듈 (v1).

법적 근거: 산업안전보건법 제17조 (안전관리자 직무)
분류: PRACTICAL — 법정 별지 서식 없음, 현장 실무 안전순찰 기록 목적

요약:
    안전관리자·순찰 담당자가 현장을 순찰하며 발견한 결함·위험요인을 기록하고
    시정조치 이행 여부 및 미시정 이월 사항을 관리하는 일지입니다.

Required form_data keys:
    site_name       str  현장명
    patrol_date     str  순찰 일자
    patrol_time     str  순찰 시간
    patrol_route    str  순찰 구간/경로
    patrol_officer  str  순찰자 성명
    writer_name     str  작성자 성명

Optional form_data keys:
    project_name            str  공사명
    department              str  소속 부서
    position                str  직책
    weather                 str  날씨
    total_workers           str  당일 전체 작업 인원
    hazard_summary          str  위험요인 발견 요약
    corrective_summary      str  시정조치 현황 요약
    carryover_items         str  미시정 이월 항목 요약
    remarks                 str  종합 의견
    reviewer_name           str  검토자
    approver_name           str  승인자
    patrol_items            list[dict]  순찰 구간별 점검 결과 반복행 (max 15)
        area                str  구간·위치
        hazard_or_deficiency str 결함·위험요인 내용
        risk_level          str  위험 수준 (상/중/하)
        corrective_action   str  시정조치 내용
        responsible_person  str  담당자
        due_date            str  완료 기한
        status              str  상태 (완료/진행중/이월)
        corrected_at        str  조치 완료 일시
        remarks             str  비고
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

SHEET_NAME = "안전순찰점검일지"
SHEET_HEADING = "안전순찰 점검 일지"
SHEET_SUBTITLE = "「산업안전보건법」 제17조에 따른 현장 안전순찰 결과 기록"
DOC_ID = "DL-003"

TOTAL_COLS = 9
MAX_PATROL_ROWS = 15

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

_COL_WIDTHS: Dict[int, int] = {1: 12, 2: 14, 3: 16, 4: 8, 5: 16, 6: 10, 7: 10, 8: 10, 9: 12}

_L1, _V1_START, _V1_END = 1, 2, 5
_L2, _V2_START, _V2_END = 6, 7, 9


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
    return r


def _write_patrol_info(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "순찰 기본정보",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_lv(ws, r, "순찰 일자", _v(data, "patrol_date"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "순찰 시간", _v(data, "patrol_time"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_lv(ws, r, "순찰자", _v(data, "patrol_officer"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "소속·직책", _v(data, "position"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_lv(ws, r, "순찰 구간", _v(data, "patrol_route"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "날씨", _v(data, "weather"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    _write_lv(ws, r, "당일 작업 인원", _v(data, "total_workers"), _L1, _V1_START, _V1_END)
    _write_lv(ws, r, "소속 부서", _v(data, "department"), _L2, _V2_START, _V2_END)
    ws.row_dimensions[r].height = H
    r += 1
    return r


def _write_patrol_items(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "순찰 구간 및 점검 결과",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1

    headers = ["구간·위치", "결함·위험요인", "위험수준", "시정조치", "담당자", "완료기한", "상태", "조치완료일시", "비고"]
    col_spans = [(1, 1), (2, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (9, 9)]
    # 9 columns: 구간(1), 결함(2-3), 위험수준(4), 시정조치(5), 담당자(6), 완료기한(7), 상태(8), 조치완료(9)
    header_cols = [
        (1, 1, "구간·위치"),
        (2, 3, "결함·위험요인"),
        (4, 4, "위험수준"),
        (5, 5, "시정조치"),
        (6, 6, "담당자"),
        (7, 7, "완료기한"),
        (8, 8, "상태"),
        (9, 9, "비고"),
    ]
    for c1, c2, label in header_cols:
        _write_cell(ws, r, c1, c2, label,
                    font=_FONT_BOLD, fill=_FILL_HEADER, align=_ALIGN_CENTER)
    ws.row_dimensions[r].height = 18
    r += 1

    items = data.get("patrol_items", [])
    if not isinstance(items, list):
        items = []

    num_items = min(len(items), MAX_PATROL_ROWS)
    for i in range(MAX_PATROL_ROWS):
        if i < num_items:
            item = items[i]
            _write_cell(ws, r, 1, 1, _v(item, "area"), align=_ALIGN_LEFT, height=H)
            _write_cell(ws, r, 2, 3, _v(item, "hazard_or_deficiency"), align=_ALIGN_LEFT, height=H)
            _write_cell(ws, r, 4, 4, _v(item, "risk_level"), align=_ALIGN_CENTER, height=H)
            _write_cell(ws, r, 5, 5, _v(item, "corrective_action"), align=_ALIGN_LEFT, height=H)
            _write_cell(ws, r, 6, 6, _v(item, "responsible_person"), align=_ALIGN_LEFT, height=H)
            _write_cell(ws, r, 7, 7, _v(item, "due_date"), align=_ALIGN_CENTER, height=H)
            _write_cell(ws, r, 8, 8, _v(item, "status"), align=_ALIGN_CENTER, height=H)
            _write_cell(ws, r, 9, 9, _v(item, "remarks"), align=_ALIGN_LEFT, height=H)
        else:
            for c in range(1, TOTAL_COLS + 1):
                _write_cell(ws, r, c, c, "", height=H)
            # re-merge 2-3 for empty rows
            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
        r += 1

    return r


def _write_corrective_summary(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "시정조치 현황 요약",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS,
                f"위험요인 발견 요약: {_v(data, 'hazard_summary')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS,
                f"시정조치 현황 요약: {_v(data, 'corrective_summary')}",
                font=_FONT_DEFAULT, align=_ALIGN_LEFT, height=H)
    r += 1
    return r


def _write_carryover(ws, start_row: int, data: Dict[str, Any]) -> int:
    H, r = 20, start_row
    _write_cell(ws, r, 1, TOTAL_COLS, "미시정 이월관리",
                font=_FONT_BOLD, fill=_FILL_SECTION, align=_ALIGN_CENTER, height=18)
    r += 1
    _write_cell(ws, r, 1, TOTAL_COLS,
                f"이월 항목 요약: {_v(data, 'carryover_items')}",
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


def build_safety_patrol_inspection_log(form_data: Dict[str, Any]) -> bytes:
    """안전순찰 점검 일지 Excel 생성."""
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    _apply_col_widths(ws)

    r = _write_title(ws, 1)
    r += 1
    r = _write_site_info(ws, r, form_data)
    r += 1
    r = _write_patrol_info(ws, r, form_data)
    r += 1
    r = _write_patrol_items(ws, r, form_data)
    r += 1
    r = _write_corrective_summary(ws, r, form_data)
    r += 1
    r = _write_carryover(ws, r, form_data)
    r += 1
    r = _write_remarks(ws, r, form_data)
    r += 1
    r = _write_signatures(ws, r, form_data)

    output = BytesIO()
    wb.save(output)
    return output.getvalue()

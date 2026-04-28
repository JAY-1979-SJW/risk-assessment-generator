from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_BOLD,
    FONT_DEFAULT,
    FONT_SMALL,
    FILL_LABEL,
    FILL_SECTION,
    FILL_HEADER,
    FILL_NONE,
    ALIGN_CENTER,
    ALIGN_LEFT,
    ALIGN_LABEL,
    write_cell,
    apply_col_widths,
    v,
)

DOC_ID     = "ED-002"
FORM_TYPE  = "annual_safety_education_plan"
SHEET_NAME = "연간안전보건교육계획서"
SHEET_HEADING  = "연간 안전보건교육 계획서"
SHEET_SUBTITLE = (
    "산업안전보건법 제29조, 시행규칙 별표4에 따른 연간 교육 계획 수립 실무 서식"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 6, 2: 16, 3: 10, 4: 10, 5: 10, 6: 10, 7: 12, 8: 12,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_PLAN_ROWS = 24
MIN_PLAN_ROWS = 12


def _lv(ws, row: int, label: str, value: Any,
        lc: int, vs: int, ve: int, height: float = 20) -> None:
    write_cell(ws, row, lc, lc, label,
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, vs, ve, value,
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height


def _section_header(ws, row: int, title: str) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, title,
               font=FONT_BOLD, fill=FILL_SECTION, align=ALIGN_CENTER, height=22)
    return row + 1


def _write_title(ws, row: int) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_SECTION, align=ALIGN_CENTER, height=28)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, height=18)
    return row + 1


def _write_meta(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 기본 정보 (핵심 기재사항)")
    _lv(ws, row, "사업장명",   v(data, "workplace_name"),  _L1, _V1S, _V1E)
    _lv(ws, row, "계획 연도",  v(data, "plan_year"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "업체명",     v(data, "company_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "안전보건관리자", v(data, "safety_manager"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "총 근로자수", v(data, "total_workers"),  _L1, _V1S, _V1E)
    _lv(ws, row, "작성일자",   v(data, "prepared_date"),   _L2, _V2S, _V2E)
    return row + 1


def _write_education_plan(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 월별 교육 계획 (핵심 기재사항)")

    hdr_spans = [(1, 1), (2, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)]
    hdr_texts = ["번호", "교육 과정명", "교육 대상", "교육 월", "교육 시간", "교육 방법", "담당 강사"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("education_plan")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_PLAN_ROWS, len(items))
    display = min(display, MAX_PLAN_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                      font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 3, v(item, "course_name"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 4, v(item, "target"),           font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(item, "month"),            font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(item, "hours"),            font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "method"),           font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "instructor"),       font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_education_types(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 교육 유형별 연간 시간 (실무 기재사항)")

    hdr_spans = [(1, 3), (4, 5), (6, 6), (7, 7), (8, 8)]
    hdr_texts = ["교육 유형", "교육 대상", "법정 시간", "계획 시간", "비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("education_types")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    for _ in range(max(4, len(items))):
        item = items[_] if _ < len(items) else {}
        write_cell(ws, row, 1, 3, v(item, "edu_type"),         font=FONT_DEFAULT, align=ALIGN_LEFT,   height=22)
        write_cell(ws, row, 4, 5, v(item, "target"),           font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(item, "legal_hours"),      font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "planned_hours"),    font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),          font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    _lv(ws, row, "작성자",   v(data, "prepared_by"), _L1, _V1S, _V1E)
    _lv(ws, row, "승인자",   v(data, "approver"),    _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 2, "서명", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    write_cell(ws, row, 3, 4, "",     font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "서명", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "",     font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _finalize_sheet(ws) -> None:
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75


def build_annual_safety_education_plan_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 연간 안전보건교육 계획서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_education_plan(ws, row, data)
    row = _write_education_types(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

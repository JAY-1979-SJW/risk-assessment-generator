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

DOC_ID     = "EM-002"
FORM_TYPE  = "near_miss_report"
SHEET_NAME = "아차사고보고서"
SHEET_HEADING  = "아차사고 보고서"
SHEET_SUBTITLE = (
    "중대재해처벌법 시행령 제4조에 따른 안전보건 개선 의무 이행 실무 서식"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_CAUSE_ROWS = 8
MIN_CAUSE_ROWS = 4
MAX_ACTION_ROWS = 8
MIN_ACTION_ROWS = 4


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
    _lv(ws, row, "현장명",     v(data, "site_name"),       _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",     v(data, "project_name"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "업체명",     v(data, "company_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "보고일자",   v(data, "report_date"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작성자",     v(data, "reporter"),        _L1, _V1S, _V1E)
    _lv(ws, row, "소속/직종",  v(data, "department"),      _L2, _V2S, _V2E)
    return row + 1


def _write_incident_overview(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 아차사고 개요 (핵심 기재사항)")
    _lv(ws, row, "발생 일시",  v(data, "incident_datetime"),  _L1, _V1S, _V1E)
    _lv(ws, row, "발생 장소",  v(data, "incident_location"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업 내용",  v(data, "work_content"),       _L1, _V1S, _V1E)
    _lv(ws, row, "관련 장비",  v(data, "related_equipment"),  _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 1, "사고 경위",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=48)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "incident_description"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 48
    row += 1
    write_cell(ws, row, 1, 1, "잠재 피해",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=36)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "potential_consequence"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 36
    return row + 1


def _write_cause_analysis(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 원인 분석 (핵심 기재사항)")

    hdr_spans = [(1, 1), (2, 3), (4, 5), (6, 7), (8, 8)]
    hdr_texts = ["번호", "원인 유형", "원인 내용", "관련 위험 요인", "비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("cause_analysis")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_CAUSE_ROWS, len(items))
    display = min(display, MAX_CAUSE_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                    font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 3, v(item, "cause_type"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 5, v(item, "cause_detail"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 7, v(item, "risk_factor"),    font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "remarks"),        font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_corrective_actions(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 시정 조치 계획 (핵심 기재사항)")

    hdr_spans = [(1, 1), (2, 3), (4, 5), (6, 6), (7, 7), (8, 8)]
    hdr_texts = ["번호", "조치 내용", "담당자", "완료 예정일", "완료 여부", "비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("corrective_actions")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_ACTION_ROWS, len(items))
    display = min(display, MAX_ACTION_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                        font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 3, v(item, "action"),             font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 5, v(item, "responsible"),        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(item, "due_date"),           font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "completed"),          font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),            font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    _lv(ws, row, "보고자",   v(data, "reporter"),    _L1, _V1S, _V1E)
    _lv(ws, row, "검토자",   v(data, "reviewer"),    _L2, _V2S, _V2E)
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


def build_near_miss_report_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 아차사고 보고서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_incident_overview(ws, row, data)
    row = _write_cause_analysis(ws, row, data)
    row = _write_corrective_actions(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

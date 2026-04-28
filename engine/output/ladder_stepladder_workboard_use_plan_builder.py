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

DOC_ID     = "EQ-016"
FORM_TYPE  = "ladder_stepladder_workboard_use_plan"
SHEET_NAME = "사다리말비계작업발판사용계획서"
SHEET_HEADING  = "사다리·말비계·작업발판 사용계획서"
SHEET_SUBTITLE = (
    "산업안전보건기준에 관한 규칙 제24조~제31조, 제57조~제75조에 따른 사다리·말비계·작업발판 실무 서식"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_STEP_ROWS  = 10
MIN_STEP_ROWS  = 5
MAX_CHECK_ROWS = 10
MIN_CHECK_ROWS = 5


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
    _lv(ws, row, "업체명",     v(data, "contractor"),      _L1, _V1S, _V1E)
    _lv(ws, row, "작업일자",   v(data, "work_date"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "설치 위치",  v(data, "install_location"), _L1, _V1S, _V1E)
    _lv(ws, row, "작업책임자", v(data, "supervisor"),      _L2, _V2S, _V2E)
    return row + 1


def _write_equipment_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 장비 정보 (핵심 기재사항)")
    _lv(ws, row, "장비 종류",   v(data, "equipment_type"),   _L1, _V1S, _V1E)
    _lv(ws, row, "수량(개)",    v(data, "equipment_count"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "규격/모델",   v(data, "equipment_spec"),   _L1, _V1S, _V1E)
    _lv(ws, row, "최대 높이",   v(data, "max_height"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "사용 기간",   v(data, "use_period"),       _L1, _V1S, _V1E)
    _lv(ws, row, "사용 목적",   v(data, "use_purpose"),      _L2, _V2S, _V2E)
    return row + 1


def _write_safety_steps(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 작업 단계별 안전조치 (핵심 기재사항)")

    hdr_spans = [(1, 1), (2, 3), (4, 5), (6, 7), (8, 8)]
    hdr_texts = ["번호", "작업 단계", "위험 요인", "안전 조치", "담당자"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("safety_steps")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_STEP_ROWS, len(items))
    display = min(display, MAX_STEP_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                    font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 3, v(item, "task_step"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 5, v(item, "hazard"),         font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 7, v(item, "safety_measure"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "responsible"),    font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _write_inspection_checklist(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 사용 전 점검 항목 (실무 기재사항)")

    hdr_spans = [(1, 1), (2, 5), (6, 6), (7, 7), (8, 8)]
    hdr_texts = ["번호", "점검 항목", "양호", "불량", "조치 사항"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("inspection_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_CHECK_ROWS, len(items))
    display = min(display, MAX_CHECK_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                   font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 5, v(item, "check_item"),    font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 6, v(item, "ok"),            font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "ng"),            font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "action"),        font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    _lv(ws, row, "작성자", v(data, "prepared_by"), _L1, _V1S, _V1E)
    _lv(ws, row, "승인자", v(data, "approver"),    _L2, _V2S, _V2E)
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


def build_ladder_stepladder_workboard_use_plan_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 사다리·말비계·작업발판 사용계획서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_equipment_info(ws, row, data)
    row = _write_safety_steps(ws, row, data)
    row = _write_inspection_checklist(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

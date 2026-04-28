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

DOC_ID     = "ED-005"
FORM_TYPE  = "safety_committee_minutes"
SHEET_NAME = "안전보건협의체회의록"
SHEET_HEADING  = "안전보건협의체 회의록"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제24조, 시행규칙 제37조에 따른 법정 회의록"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_AGENDA_ROWS  = 10
MIN_AGENDA_ROWS  = 5
MAX_ATTEND_ROWS  = 12
MIN_ATTEND_ROWS  = 6


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
    row = _section_header(ws, row, "▶ 기본 정보 (법정 기재사항)")
    _lv(ws, row, "사업장명",   v(data, "workplace_name"), _L1, _V1S, _V1E)
    _lv(ws, row, "회의 일시", v(data, "meeting_date"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "회의 장소", v(data, "meeting_location"), _L1, _V1S, _V1E)
    _lv(ws, row, "회차",      v(data, "meeting_number"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "의장",      v(data, "chairperson"),      _L1, _V1S, _V1E)
    _lv(ws, row, "간사",      v(data, "secretary"),        _L2, _V2S, _V2E)
    return row + 1


def _write_attendees(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 참석자 (법정 기재사항)")
    write_cell(ws, row, 1, 1, "번호",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 2, 3, "소속",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 4, 5, "성명",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 6, "직위",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 7, "구분",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 8, "서명",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    raw: Any = data.get("attendees")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_ATTEND_ROWS, len(items))
    display = min(display, MAX_ATTEND_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                    font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 3, v(item, "organization"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 5, v(item, "name"),           font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 6, v(item, "position"),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "role"),           font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, "",                        font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_agenda(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 안건 및 협의 결과 (법정 기재사항)")

    headers   = ["번호", "안건",            "협의 내용",         "결정 사항",         "이행 기한",  "담당자"]
    col_spans = [(1, 1),  (2, 3),            (4, 5),              (6, 6),              (7, 7),       (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("agenda_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_AGENDA_ROWS, len(items))
    display = min(display, MAX_AGENDA_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                  font=FONT_DEFAULT, align=ALIGN_CENTER, height=26)
        write_cell(ws, row, 2, 3, v(item, "agenda"),       font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 5, v(item, "discussion"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 6, v(item, "decision"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, v(item, "deadline"),     font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "responsible"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _write_special_items(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 특이사항 및 건의사항")
    write_cell(ws, row, 1, 1, "내용",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "special_notes"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    row += 1
    write_cell(ws, row, 1, 1, "차기 일정",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "next_meeting_date"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    return row + 1


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    _lv(ws, row, "의장",   v(data, "chairperson"), _L1, _V1S, _V1E)
    _lv(ws, row, "간사",   v(data, "secretary"),   _L2, _V2S, _V2E)
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


def build_safety_committee_minutes_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 안전보건협의체 회의록 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_attendees(ws, row, data)
    row = _write_agenda(ws, row, data)
    row = _write_special_items(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

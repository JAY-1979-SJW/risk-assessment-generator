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

DOC_ID     = "WP-013"
FORM_TYPE  = "chemical_equipment_workplan"
SHEET_NAME = "화학설비작업계획서"
SHEET_HEADING  = "화학설비·부속설비 작업계획서"
SHEET_SUBTITLE = (
    "「산업안전보건기준에 관한 규칙」 제38조 제1항 제4호, 제224조 이하에 따른 법정 작업계획서"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_STEP_ROWS   = 10
MIN_STEP_ROWS   = 5
MAX_HAZARD_ROWS = 8
MIN_HAZARD_ROWS = 4


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
    _lv(ws, row, "현장명",       v(data, "site_name"),       _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",       v(data, "project_name"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "업체명",       v(data, "contractor"),      _L1, _V1S, _V1E)
    _lv(ws, row, "작업일자",     v(data, "work_date"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업위치",     v(data, "work_location"),   _L1, _V1S, _V1E)
    _lv(ws, row, "작업책임자",   v(data, "supervisor"),      _L2, _V2S, _V2E)
    return row + 1


def _write_equipment_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 화학설비·부속설비 정보 (법정 기재사항)")
    _lv(ws, row, "설비명",       v(data, "equipment_name"),   _L1, _V1S, _V1E)
    _lv(ws, row, "설비 종류",    v(data, "equipment_type"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "취급 물질",    v(data, "chemical_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "물질 상태",    v(data, "chemical_state"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "위험물 여부",  v(data, "is_hazardous"),     _L1, _V1S, _V1E)
    _lv(ws, row, "최고 사용압력", v(data, "max_pressure"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "최고 사용온도", v(data, "max_temperature"), _L1, _V1S, _V1E)
    _lv(ws, row, "설비 용량",    v(data, "capacity"),         _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 1, "작업 내용",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "work_summary"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _write_safety_steps(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 작업 단계별 안전조치 (법정 기재사항)")

    headers   = ["번호", "작업 단계",      "위험 요인",         "안전 조치",         "담당자"]
    col_spans = [(1, 1),  (2, 3),           (4, 5),              (6, 7),              (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
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


def _write_chemical_hazards(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 화학적 위험 및 대응 방법 (법정 기재사항)")

    headers   = ["번호", "위험 유형",      "위험 내용",         "누출·화재 대응",    "보호구"]
    col_spans = [(1, 1),  (2, 2),           (3, 4),              (5, 6),              (7, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("chemical_hazards")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_HAZARD_ROWS, len(items))
    display = min(display, MAX_HAZARD_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                      font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 2, v(item, "hazard_type"),      font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 4, v(item, "description"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 6, v(item, "response"),         font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 8, v(item, "ppe_required"),     font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_emergency(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 비상조치 계획")
    write_cell(ws, row, 1, 1, "비상조치",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "emergency_measure"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 2, "역할",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, 5, "성명",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 8, "연락처", font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    raw: Any = data.get("emergency_contacts")
    contacts: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    for _ in range(max(3, len(contacts))):
        c = contacts[_] if _ < len(contacts) else {}
        write_cell(ws, row, 1, 2, v(c, "role"),  font=FONT_DEFAULT, align=ALIGN_CENTER, height=20)
        write_cell(ws, row, 3, 5, v(c, "name"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 8, v(c, "phone"), font=FONT_DEFAULT, align=ALIGN_LEFT)
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


def build_chemical_equipment_workplan_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 화학설비·부속설비 작업계획서 xlsx 바이너리를 반환한다."""
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
    row = _write_chemical_hazards(ws, row, data)
    row = _write_emergency(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

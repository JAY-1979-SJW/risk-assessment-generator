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

DOC_ID     = "PPE-002"
FORM_TYPE  = "construction_equipment_entry_request"
SHEET_NAME = "장비반입신청서"
SHEET_HEADING  = "건설 장비 반입 신청서"
SHEET_SUBTITLE = (
    "원청 안전 관리 규정에 따른 건설 장비 반입 전 사전 신청 서식"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 6, 2: 14, 3: 12, 4: 10, 5: 12, 6: 10, 7: 12, 8: 12,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_EQUIPMENT_ROWS = 10
MIN_EQUIPMENT_ROWS = 5


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
    _lv(ws, row, "신청 업체",  v(data, "company_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "신청일자",   v(data, "request_date"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "반입 예정일", v(data, "entry_date"),     _L1, _V1S, _V1E)
    _lv(ws, row, "작업 위치",  v(data, "work_location"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "담당자",     v(data, "supervisor"),      _L1, _V1S, _V1E)
    _lv(ws, row, "연락처",     v(data, "contact"),         _L2, _V2S, _V2E)
    return row + 1


def _write_equipment_table(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 반입 장비 목록 (핵심 기재사항)")

    hdr_spans = [(1, 1), (2, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)]
    hdr_texts = ["번호", "장비 종류·규격", "차량번호", "제조사", "제조연도", "보험 유효기간", "비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("equipment_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_EQUIPMENT_ROWS, len(items))
    display = min(display, MAX_EQUIPMENT_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                        font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 3, v(item, "equipment_type"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 4, v(item, "vehicle_number"),     font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(item, "manufacturer"),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(item, "manufacture_year"),   font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "insurance_expiry"),   font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),            font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_inspection_table(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 반입 전 안전 확인 사항 (실무 기재사항)")

    hdr_spans = [(1, 4), (5, 6), (7, 8)]
    hdr_texts = ["확인 항목", "확인 결과", "비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("inspection_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    defaults = [
        "보험증권 사본 제출 여부",
        "정기검사증 유효기간 확인",
        "운전원 자격증 확인",
        "장비 외관 이상 유무",
        "안전장치 (경보기, 후방카메라 등) 작동 확인",
    ]
    n = max(len(items), len(defaults))
    for i in range(n):
        item = items[i] if i < len(items) else {}
        default_text = defaults[i] if i < len(defaults) else ""
        check_item = v(item, "check_item") or default_text
        write_cell(ws, row, 1, 4, check_item,             font=FONT_DEFAULT, align=ALIGN_LEFT,   height=22)
        write_cell(ws, row, 5, 6, v(item, "result"),      font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 8, v(item, "remarks"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 신청 및 승인")
    _lv(ws, row, "신청자",  v(data, "applicant"),  _L1, _V1S, _V1E)
    _lv(ws, row, "승인자",  v(data, "approver"),   _L2, _V2S, _V2E)
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


def build_construction_equipment_entry_request_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 건설 장비 반입 신청서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_equipment_table(ws, row, data)
    row = _write_inspection_table(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

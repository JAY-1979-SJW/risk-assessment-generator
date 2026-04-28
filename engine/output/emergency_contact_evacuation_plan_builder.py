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

DOC_ID     = "EM-003"
FORM_TYPE  = "emergency_contact_evacuation_plan"
SHEET_NAME = "비상연락망및대피계획서"
SHEET_HEADING  = "비상 연락망 및 대피 계획서"
SHEET_SUBTITLE = (
    "「산업안전보건기준에 관한 규칙」 제14조, 제622조에 따른 법정 비상대피계획서"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_CONTACT_ROWS = 12
MIN_CONTACT_ROWS = 6
MAX_ROUTE_ROWS   = 6
MIN_ROUTE_ROWS   = 3
MAX_ASSEMBLY_ROWS = 4
MIN_ASSEMBLY_ROWS = 2


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
    _lv(ws, row, "현장 주소",    v(data, "site_address"),    _L1, _V1S, _V1E)
    _lv(ws, row, "작성일자",     v(data, "prepared_date"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "안전관리자",   v(data, "safety_manager"),  _L1, _V1S, _V1E)
    _lv(ws, row, "현장소장",     v(data, "site_director"),   _L2, _V2S, _V2E)
    return row + 1


def _write_contacts(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 비상 연락망 (법정 기재사항)")

    headers   = ["번호", "역할",           "성명",   "소속",           "연락처",         "비고"]
    col_spans = [(1, 1),  (2, 3),           (4, 4),   (5, 6),           (7, 7),           (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("emergency_contacts")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_CONTACT_ROWS, len(items))
    display = min(display, MAX_CONTACT_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                    font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 3, v(item, "role"),           font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 4, v(item, "name"),           font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 6, v(item, "organization"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, v(item, "phone"),          font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),        font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1

    # 외부 기관 고정 행
    row = _section_header(ws, row, "▶ 외부 비상 연락처 (법정 기재사항)")
    ext_headers = ["기관명", "연락처", "비고"]
    ext_spans   = [(1, 3), (4, 6), (7, 8)]
    for (cs, ce), hdr in zip(ext_spans, ext_headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1
    raw_ext: Any = data.get("external_contacts")
    ext_items: List[Dict[str, Any]] = raw_ext if isinstance(raw_ext, list) else []
    defaults = [
        {"agency": "119 소방서",     "phone": "119"},
        {"agency": "112 경찰서",     "phone": "112"},
        {"agency": "관할 고용노동부", "phone": v(data, "labor_office_phone")},
    ]
    for i in range(3):
        item = ext_items[i] if i < len(ext_items) else defaults[i]
        write_cell(ws, row, 1, 3, v(item, "agency"),  font=FONT_DEFAULT, align=ALIGN_LEFT,   height=20)
        write_cell(ws, row, 4, 6, v(item, "phone"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 8, v(item, "remarks"), font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_evacuation_routes(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 대피 경로 (법정 기재사항)")

    headers   = ["번호", "구역",           "대피 경로",             "비상구 위치",     "집결지",         "담당자"]
    col_spans = [(1, 1),  (2, 2),           (3, 4),                  (5, 5),            (6, 7),           (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("evacuation_routes")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_ROUTE_ROWS, len(items))
    display = min(display, MAX_ROUTE_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                       font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 2, v(item, "zone"),              font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 4, v(item, "route_description"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 5, v(item, "exit_location"),     font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 7, v(item, "assembly_point"),    font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "responsible"),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _write_assembly_points(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 집결지 정보")

    headers   = ["번호", "집결지명",       "위치 설명",             "수용 인원",       "담당자"]
    col_spans = [(1, 1),  (2, 3),           (4, 5),                  (6, 7),            (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("assembly_points")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_ASSEMBLY_ROWS, len(items))
    display = min(display, MAX_ASSEMBLY_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                   font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 3, v(item, "point_name"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 5, v(item, "location"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 7, v(item, "capacity"),     font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "responsible"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    _lv(ws, row, "작성자",   v(data, "safety_manager"), _L1, _V1S, _V1E)
    _lv(ws, row, "승인자",   v(data, "site_director"),  _L2, _V2S, _V2E)
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


def build_emergency_contact_evacuation_plan_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 비상 연락망 및 대피 계획서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_contacts(ws, row, data)
    row = _write_evacuation_routes(ws, row, data)
    row = _write_assembly_points(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

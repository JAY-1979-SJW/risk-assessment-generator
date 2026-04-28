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

DOC_ID     = "PPE-001"
FORM_TYPE  = "ppe_issuance_ledger"
SHEET_NAME = "보호구지급대장"
SHEET_HEADING  = "보호구 지급 대장"
SHEET_SUBTITLE = (
    "「산업안전보건기준에 관한 규칙」 제32조에 따른 법정 보호구 지급·관리 대장"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 6, 2: 14, 3: 10, 4: 10, 5: 16, 6: 10, 7: 12, 8: 12,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_ISSUE_ROWS = 20
MIN_ISSUE_ROWS = 10


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
    _lv(ws, row, "업체명",       v(data, "company_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "관리책임자",   v(data, "manager"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작성기간",     v(data, "period"),          _L1, _V1S, _V1E)
    _lv(ws, row, "작성일자",     v(data, "prepared_date"),   _L2, _V2S, _V2E)
    return row + 1


def _write_issue_table(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 보호구 지급 내역 (법정 기재사항)")

    headers   = ["번호", "근로자 성명",   "직종",   "지급 보호구 종류",  "지급일자",   "수령 확인",  "반납일자",   "비고"]
    col_spans = [(1, 1),  (2, 2),          (3, 3),   (4, 5),              (6, 6),        (7, 7),        (8, 8),       (8, 8)]
    # 8컬럼 헤더 직접 매핑
    hdr_spans = [(1,1),(2,2),(3,3),(4,5),(6,6),(7,7),(8,8)]
    hdr_texts = ["번호","근로자 성명","직종","지급 보호구 종류","지급일자","수령 확인","반납/비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("issue_records")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_ISSUE_ROWS, len(items))
    display = min(display, MAX_ISSUE_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                      font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 2, v(item, "worker_name"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, v(item, "occupation"),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 5, v(item, "ppe_type"),         font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 6, v(item, "issue_date"),       font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "receipt_confirm"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "return_date"),      font=FONT_SMALL,   align=ALIGN_CENTER)
        row += 1
    return row


def _write_ppe_stock(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 보호구 재고 현황")

    hdr_spans = [(1,2),(3,4),(5,5),(6,6),(7,7),(8,8)]
    hdr_texts = ["보호구 종류","규격/모델","보유 수량","지급 수량","잔여 수량","비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("stock_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    for _ in range(max(4, len(items))):
        item = items[_] if _ < len(items) else {}
        write_cell(ws, row, 1, 2, v(item, "ppe_type"),    font=FONT_DEFAULT, align=ALIGN_LEFT,   height=22)
        write_cell(ws, row, 3, 4, v(item, "spec"),        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(item, "stock_qty"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(item, "issued_qty"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "remain_qty"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),     font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    _lv(ws, row, "관리책임자", v(data, "manager"),  _L1, _V1S, _V1E)
    _lv(ws, row, "확인자",     v(data, "approver"), _L2, _V2S, _V2E)
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


def build_ppe_issuance_ledger_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 보호구 지급 대장 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_issue_table(ws, row, data)
    row = _write_ppe_stock(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

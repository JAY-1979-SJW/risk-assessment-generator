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

DOC_ID     = "CM-001"
FORM_TYPE  = "contractor_safety_document_checklist"
SHEET_NAME = "협력업체서류확인서"
SHEET_HEADING  = "협력업체 안전보건 관련 서류 확인서"
SHEET_SUBTITLE = (
    "산업안전보건법 제63조(도급인 안전보건 조치 의무)에 따른 협력업체 서류 확인 실무 서식"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 6, 2: 20, 3: 12, 4: 10, 5: 10, 6: 10, 7: 10, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_DOC_ROWS = 20
MIN_DOC_ROWS = 10


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
    _lv(ws, row, "원청업체",   v(data, "principal_contractor"), _L1, _V1S, _V1E)
    _lv(ws, row, "협력업체",   v(data, "subcontractor"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "확인일자",   v(data, "check_date"),      _L1, _V1S, _V1E)
    _lv(ws, row, "확인 담당자", v(data, "checker"),        _L2, _V2S, _V2E)
    return row + 1


def _write_doc_checklist(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 서류 제출 현황 (핵심 기재사항)")

    hdr_spans = [(1, 1), (2, 4), (5, 5), (6, 6), (7, 7), (8, 8)]
    hdr_texts = ["번호", "서류 명칭", "제출 여부", "제출일자", "유효기간", "비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("doc_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_DOC_ROWS, len(items))
    display = min(display, MAX_DOC_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                       font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 4, v(item, "doc_name"),          font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 5, v(item, "submitted"),         font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(item, "submit_date"),       font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "expiry_date"),       font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),           font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_required_docs(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 필수 서류 목록 (실무 기재사항)")

    hdr_spans = [(1, 1), (2, 5), (6, 7), (8, 8)]
    hdr_texts = ["번호", "필수 서류명", "근거 법령", "비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("required_docs")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    for _ in range(max(5, len(items))):
        item = items[_] if _ < len(items) else {}
        write_cell(ws, row, 1, 1, _ + 1,                   font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 5, v(item, "doc_name"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 7, v(item, "legal_basis"),   font=FONT_SMALL,   align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "remarks"),       font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    _lv(ws, row, "확인 담당자", v(data, "checker"),     _L1, _V1S, _V1E)
    _lv(ws, row, "승인자",      v(data, "approver"),    _L2, _V2S, _V2E)
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


def build_contractor_safety_document_checklist_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 협력업체 안전보건 관련 서류 확인서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_doc_checklist(ws, row, data)
    row = _write_required_docs(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

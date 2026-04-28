"""
산업안전보건관리비 사용계획서 — Excel 출력 모듈 (v1.0).

법적 근거: 건설업 산업안전보건관리비 계상 및 사용기준 고시, 별지 제102호서식
분류:     legal — 건설 현장 집행 계획 및 정산용

법정 기재사항:
- 현장(공사)명, 원수급인, 도급금액, 안전보건관리비 계상액
- 항목별 사용계획(사용 항목, 계획금액, 비고)
- 작성일, 작성자, 확인자

Input — form_data dict:
    site_name              str|None   현장(공사)명
    project_name           str|None   공사명
    company_name           str|None   시공사(원수급인)
    contractor             str|None   하수급인(해당 시)
    plan_year              str|None   계획연도
    work_start_date        str|None   공사 착공일
    work_end_date          str|None   공사 완공 예정일
    total_contract_amount  str|None   도급금액 (원)
    safety_cost_rate       str|None   안전보건관리비 계상 요율 (%)
    safety_cost_amount     str|None   안전보건관리비 계상액 (원)
    supervisor             str|None   작성자
    approver               str|None   확인자
    sign_date              str|None   작성일

    cost_items  list[dict]  항목별 사용계획 (MAX_ROWS=15)
        category           str|None   사용 항목
        planned_amount     str|None   계획금액 (원)
        remarks            str|None   비고

Output — xlsx bytes (in-memory).
"""
from __future__ import annotations

from io import BytesIO
from collections.abc import Mapping
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

DOC_ID     = "TS-004"
FORM_TYPE  = "safety_cost_use_plan"
SHEET_NAME = "산업안전보건관리비 사용계획서"
SHEET_HEADING  = "산업안전보건관리비 사용계획서"
SHEET_SUBTITLE = (
    "산업안전보건관리비 사용계획 작성 보조서식"
    f" ({DOC_ID}) — 공식 제출 시 별지 제102호서식(고시) 사용"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 4, 2: 20, 3: 14, 4: 14, 5: 14, 6: 12, 7: 12, 8: 14,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8
_FULL_S, _FULL_E = 2, 8

MAX_COST_ROWS = 15
MIN_COST_ROWS = 10


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
               font=FONT_TITLE, fill=FILL_SECTION, align=ALIGN_CENTER, height=30)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, height=18)
    return row + 1


def _write_meta(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 기본 정보 (법정 기재사항)")
    _lv(ws, row, "현장(공사)명", v(data, "site_name"),   _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",       v(data, "project_name"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "원수급인",     v(data, "company_name"), _L1, _V1S, _V1E)
    _lv(ws, row, "하수급인",     v(data, "contractor"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "계획연도",     v(data, "plan_year"),         _L1, _V1S, _V1E)
    _lv(ws, row, "착공일",       v(data, "work_start_date"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "완공 예정일",  v(data, "work_end_date"),     _L1, _V1S, _V1E)
    _lv(ws, row, "도급금액(원)", v(data, "total_contract_amount"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "계상 요율(%)", v(data, "safety_cost_rate"),   _L1, _V1S, _V1E)
    _lv(ws, row, "계상액(원)",   v(data, "safety_cost_amount"), _L2, _V2S, _V2E)
    return row + 1


def _write_cost_table(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 항목별 사용계획 (법정 기재사항)")

    headers   = ["번호", "사용 항목",    "계획금액(원)",  "집행금액(원)", "잔액(원)",    "집행율(%)", "비고"]
    col_spans = [(1, 1),  (2, 3),         (4, 4),          (5, 5),         (6, 6),         (7, 7),      (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("cost_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_COST_ROWS, len(items))
    display = min(display, MAX_COST_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                    font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 3, v(item, "category"),       font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 4, v(item, "planned_amount"), font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, "",                        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, "",                        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, "",                        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),        font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1

    # 합계 행
    write_cell(ws, row, 1, 3, "합  계",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=22)
    for c in range(4, 9):
        write_cell(ws, row, c, c, "", font=FONT_BOLD, align=ALIGN_CENTER)
    return row + 1


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    write_cell(ws, row, 1, 1, "작성일",            font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 2, 3, v(data, "sign_date"), font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 4, 5, "작성자",             font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 6, v(data, "supervisor"), font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 7, 7, "확인자",             font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 8, v(data, "approver"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    write_cell(ws, row, 2, 3, "",       font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 4, 5, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 6, "",       font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 7, 7, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 8, "",       font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _finalize_sheet(ws) -> None:
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75


def build_safety_cost_use_plan_excel(
    form_data: Mapping[str, Any],
) -> bytes:
    """form_data dict를 받아 산업안전보건관리비 사용계획서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_cost_table(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

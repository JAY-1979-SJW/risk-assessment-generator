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

DOC_ID     = "TS-005"
FORM_TYPE  = "asbestos_removal_workplan"
SHEET_NAME = "석면해체제거작업계획서"
SHEET_HEADING  = "석면 해체·제거 작업 계획서"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제119조, 시행규칙 제175조 이하에 따른 법정 작업계획서"
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
MAX_WORKER_ROWS = 8
MIN_WORKER_ROWS = 4


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
    _lv(ws, row, "건축물명",     v(data, "building_name"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "업체명",       v(data, "contractor"),      _L1, _V1S, _V1E)
    _lv(ws, row, "작업기간",     v(data, "work_period"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업위치",     v(data, "work_location"),   _L1, _V1S, _V1E)
    _lv(ws, row, "작업책임자",   v(data, "supervisor"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "석면조사기관", v(data, "survey_agency"),   _L1, _V1S, _V1E)
    _lv(ws, row, "조사 완료일",  v(data, "survey_date"),     _L2, _V2S, _V2E)
    return row + 1


def _write_asbestos_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 석면 함유 자재 정보 (법정 기재사항)")
    _lv(ws, row, "석면 종류",    v(data, "asbestos_type"),    _L1, _V1S, _V1E)
    _lv(ws, row, "함유 자재",    v(data, "material_name"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "함유량",       v(data, "content_ratio"),    _L1, _V1S, _V1E)
    _lv(ws, row, "예상 면적/량", v(data, "estimated_qty"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "위치·층수",    v(data, "material_location"), _L1, _V1S, _V1E)
    _lv(ws, row, "해체 방법",    v(data, "removal_method"),   _L2, _V2S, _V2E)
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


def _write_workers(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 작업 종사자 및 보호구 (법정 기재사항)")

    headers   = ["번호", "성명",    "직종",   "특수건강진단 여부", "지급 보호구",         "비고"]
    col_spans = [(1, 1),  (2, 2),   (3, 3),   (4, 4),             (5, 7),                (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("workers")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_WORKER_ROWS, len(items))
    display = min(display, MAX_WORKER_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                        font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 2, v(item, "name"),               font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, v(item, "occupation"),         font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 4, v(item, "health_exam"),        font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 5, 7, v(item, "ppe"),                font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "remarks"),            font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_waste_disposal(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 폐석면 처리 계획 (법정 기재사항)")
    _lv(ws, row, "폐기물 처리업체", v(data, "waste_contractor"),  _L1, _V1S, _V1E)
    _lv(ws, row, "처리 방법",       v(data, "disposal_method"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "보관 장소",       v(data, "storage_location"),  _L1, _V1S, _V1E)
    _lv(ws, row, "비상조치",        v(data, "emergency_measure"), _L2, _V2S, _V2E)
    return row + 1


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


def build_asbestos_removal_workplan_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 석면 해체·제거 작업 계획서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_asbestos_info(ws, row, data)
    row = _write_safety_steps(ws, row, data)
    row = _write_workers(ws, row, data)
    row = _write_waste_disposal(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

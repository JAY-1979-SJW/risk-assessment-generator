"""
터널 굴착 작업계획서 Excel builder — WP-002 (v1.0)

법적 근거: 산업안전보건기준에 관한 규칙 제38조 제1항 제7호, 제46조 이하
적용 범위: 터널공사 한정
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from collections.abc import Mapping
from typing import Any, Dict, List, Optional

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

DOC_ID     = "WP-002"
FORM_TYPE  = "tunnel_excavation_workplan"
SHEET_NAME = "터널굴착작업계획서"
SHEET_HEADING  = "터널 굴착 작업계획서"
SHEET_SUBTITLE = (
    "「산업안전보건기준에 관한 규칙」 제38조 제1항 제7호·제46조 이하에 따른 터널 굴착 작업계획서"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 14, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8
_FULL_S, _FULL_E = 2, 8

MAX_SAFETY_ROWS = 10
MIN_SAFETY_ROWS = 5
MAX_HAZARD_ROWS = 10
MIN_HAZARD_ROWS = 5


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
    row = _section_header(ws, row, "▶ 기본 정보")
    _lv(ws, row, "현장명",   v(data, "site_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",   v(data, "project_name"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "업체명",   v(data, "contractor"),   _L1, _V1S, _V1E)
    _lv(ws, row, "작업일자", v(data, "work_date"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업위치", v(data, "work_location"), _L1, _V1S, _V1E)
    _lv(ws, row, "작업종류", v(data, "tunnel_type"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업책임자", v(data, "supervisor"),  _L1, _V1S, _V1E)
    _lv(ws, row, "작성자",     v(data, "prepared_by"), _L2, _V2S, _V2E)
    return row + 1


def _write_tunnel_plan(ws, row: int, data: Dict[str, Any]) -> int:
    """터널 굴착 계획 — 법정 기재사항 (제38조 제1항 제7호, 제46조 이하)."""
    row = _section_header(ws, row, "▶ 터널 굴착 계획 (법정 기재사항)")

    fields = [
        ("굴착 공법",       "excavation_method",   "NATM·TBM·개착식 등"),
        ("굴착 단면·규모",  "tunnel_section",      "폭×높이, 연장(m) 등"),
        ("지반 조건",       "ground_condition",    "암반 등급·토질 특성 등"),
        ("발파 계획",       "blasting_plan",       "화약 종류·장약량·기폭방법 등 (해당 시)"),
        ("환기 계획",       "ventilation_plan",    "환기 방식·환기량·측정 주기 등"),
        ("조명 계획",       "lighting_plan",       "조명 기준·비상조명 설치 계획"),
        ("낙반·붕괴 방지",  "support_measure",     "숏크리트·록볼트·강지보 등 지보 계획"),
        ("출입구역 설정",   "access_control",      "작업구역·대피로·출입 통제 방법"),
        ("비상조치 방법",   "emergency_measure",   "사고 유형별 대응 절차·대피 계획"),
    ]

    for label, key, example in fields:
        write_cell(ws, row, 1, 1, label,
                   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=22)
        val = v(data, key)
        write_cell(ws, row, 2, TOTAL_COLS, val if val else "",
                   font=FONT_DEFAULT, align=ALIGN_LEFT, height=22)
        row += 1

    return row


def _write_safety_steps(ws, row: int, data: Dict[str, Any]) -> int:
    """단계별 안전작업 절차."""
    row = _section_header(ws, row, "▶ 단계별 안전작업 절차")

    headers   = ["번호", "작업 단계",    "위험 요인",  "안전 조치",   "담당자"]
    col_spans = [(1, 1),  (2, 3),         (4, 5),        (6, 7),        (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("safety_steps")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_SAFETY_ROWS, len(items))
    display = min(display, MAX_SAFETY_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                    font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 3, v(item, "task_step"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 5, v(item, "hazard"),         font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 7, v(item, "safety_measure"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "responsible"),    font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _write_emergency_contacts(ws, row: int, data: Dict[str, Any]) -> int:
    """비상연락망."""
    row = _section_header(ws, row, "▶ 비상연락망")

    write_cell(ws, row, 1, 2, "역할",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, 5, "성명",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 8, "연락처", font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    raw: Any = data.get("emergency_contacts")
    contacts: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    for i in range(max(4, len(contacts))):
        contact = contacts[i] if i < len(contacts) else {}
        write_cell(ws, row, 1, 2, v(contact, "role"),  font=FONT_DEFAULT, align=ALIGN_CENTER, height=20)
        write_cell(ws, row, 3, 5, v(contact, "name"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 8, v(contact, "phone"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    """서명란."""
    row = _section_header(ws, row, "▶ 확인")
    write_cell(ws, row, 1, 2, "작성자",             font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, 4, v(data, "prepared_by"), font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "확인자",             font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, v(data, "supervisor"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 2, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    write_cell(ws, row, 3, 4, "",      font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "",      font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _finalize_sheet(ws) -> None:
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75


def build_tunnel_excavation_workplan_excel(
    form_data: Mapping[str, Any],
) -> bytes:
    """form_data dict를 받아 터널 굴착 작업계획서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_tunnel_plan(ws, row, data)
    row = _write_safety_steps(ws, row, data)
    row = _write_emergency_contacts(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

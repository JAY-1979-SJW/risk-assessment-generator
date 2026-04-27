"""
항타기·항발기 사용 작업계획서 — Excel 출력 모듈 (v1).

법적 근거: 산업안전보건기준에 관한 규칙 제38조 제1항 제12호, 제186조 이하
분류: 법정 작업계획서 (WP-010)
      법정 별지 서식 없음 — 자체 표준서식.

EQ-009(항타기·항발기·천공기 사용계획서)가 장비 제원 중심이라면
이 서식은 작업 절차·방법·안전조치 중심의 작업계획서이다.

Required form_data keys:
    machine_type         str  사용 기계 종류 (항타기/항발기)
    work_method          str  작업방법
    operator_name        str  조종사 성명

Optional form_data keys:
    site_name            str  현장명
    project_name         str  공사명
    work_location        str  작업위치
    work_date            str  작업기간
    contractor           str  작업업체
    supervisor           str  작업책임자
    prepared_by          str  작성자
    sign_date            str  작성일
    machine_capacity     str  기계 성능·최대능력
    operator_license     str  조종사 자격
    guide_worker         str  유도자 배치 여부 및 성명
    speed_limit          str  제한 속도
    travel_route         str  이동경로
    work_radius          str  작업 반경
    signal_method        str  신호 방법
    ground_condition     str  지반 상태
    adjacent_risk        str  인접 위험요소
    emergency_measure    str  비상조치 방법
    emergency_contact    str  비상연락처
    approver             str  확인자

    work_steps    list[dict]  작업 순서 (repeat_field)
        step_no          str  순서
        task             str  작업 내용
        safety_point     str  안전 주의사항
        responsible      str  담당자

    hazard_items  list[dict]  위험요인 분석
        hazard_type          str  위험 유형
        description          str  위험 요인 내용
        measure              str  예방 대책
        responsible          str  담당자
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    FONT_TITLE, FONT_SUBTITLE, FONT_BOLD, FONT_DEFAULT, FONT_SMALL,
    FILL_LABEL, FILL_SECTION, FILL_HEADER, FILL_NONE,
    ALIGN_CENTER, ALIGN_LEFT, ALIGN_LABEL,
    v, write_cell, apply_col_widths,
)

DOC_ID     = "WP-010"
FORM_TYPE  = "piling_use_workplan"
SHEET_NAME = "항타기작업계획서"

SHEET_HEADING  = "항타기·항발기 사용 작업계획서"
SHEET_SUBTITLE = (
    "「산업안전보건기준에 관한 규칙」 제38조 제1항 제12호, 제186조 이하에 따른 "
    "항타기·항발기 사용 작업계획서 (WP-010)"
)

TOTAL_COLS       = 8
MAX_STEPS        = 8
MIN_STEPS        = 4
MAX_HAZARD_ROWS  = 10
MIN_HAZARD_ROWS  = 5

_COL_WIDTHS: Dict[int, float] = {
    1: 8, 2: 16, 3: 14, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8


# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------

def _lv(ws, row: int, label: str, value: Any,
        lc: int, vs: int, ve: int, height: float = 20) -> None:
    write_cell(ws, row, lc, lc, label,
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, vs, ve, value,
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height


def _section(ws, row: int, title: str) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, title,
               font=FONT_BOLD, fill=FILL_SECTION, align=ALIGN_CENTER, height=22)
    return row + 1


# ---------------------------------------------------------------------------
# 섹션 렌더러
# ---------------------------------------------------------------------------

def _write_title(ws, row: int) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_SECTION, align=ALIGN_CENTER, height=28)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, height=18)
    return row + 1


def _write_meta(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section(ws, row, "▶ 기본 정보")
    _lv(ws, row, "현장명",   v(data, "site_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",   v(data, "project_name"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업위치", v(data, "work_location"), _L1, _V1S, _V1E)
    _lv(ws, row, "작업기간", v(data, "work_date"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업업체", v(data, "contractor"),    _L1, _V1S, _V1E)
    _lv(ws, row, "작업책임자", v(data, "supervisor"),  _L2, _V2S, _V2E)
    return row + 1


def _write_machine_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section(ws, row, "▶ 작업 개요")
    _lv(ws, row, "기계 종류",   v(data, "machine_type"),     _L1, _V1S, _V1E)
    _lv(ws, row, "기계 성능",   v(data, "machine_capacity"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "조종사",      v(data, "operator_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "자격",        v(data, "operator_license"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "유도자",      v(data, "guide_worker"),     _L1, _V1S, _V1E)
    _lv(ws, row, "제한 속도",   v(data, "speed_limit"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업 반경",   v(data, "work_radius"),      _L1, _V1S, _V1E)
    _lv(ws, row, "신호 방법",   v(data, "signal_method"),    _L2, _V2S, _V2E)
    row += 1
    # 작업방법 — 전폭
    write_cell(ws, row, 1, 1, "작업방법",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "work_method"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    row += 1
    write_cell(ws, row, 1, 1, "이동경로",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "travel_route"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    row += 1
    write_cell(ws, row, 1, 1, "지반 상태",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "ground_condition"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    row += 1
    write_cell(ws, row, 1, 1, "인접 위험",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "adjacent_risk"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    return row + 1


def _write_work_steps(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section(ws, row, "▶ 작업 순서 및 안전조치")
    # 헤더
    headers   = ["순서", "작업 내용",     "안전 주의사항",  "담당자"]
    col_spans = [(1, 1),  (2, 4),          (5, 7),           (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("work_steps")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_STEPS, len(items))
    display = min(display, MAX_STEPS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, v(item, "step_no", str(i + 1)),
                   font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 4, v(item, "task"),
                   font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 7, v(item, "safety_point"),
                   font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "responsible"),
                   font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _write_hazard_table(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section(ws, row, "▶ 위험요인 및 안전대책")
    headers   = ["번호", "위험 유형", "위험 요인 내용",  "예방 대책",   "담당자"]
    col_spans = [(1, 1),  (2, 2),      (3, 5),            (6, 7),        (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("hazard_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_HAZARD_ROWS, len(items))
    display = min(display, MAX_HAZARD_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,               font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 2, v(item, "hazard_type"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 5, v(item, "description"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 7, v(item, "measure"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "responsible"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _write_emergency(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section(ws, row, "▶ 비상조치 계획")
    write_cell(ws, row, 1, 1, "비상조치",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=24)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "emergency_measure"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=24)
    row += 1
    write_cell(ws, row, 1, 1, "비상연락처",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "emergency_contact"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    return row + 1


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section(ws, row, "▶ 확인")
    write_cell(ws, row, 1, 2, "작성자",       font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, 4, v(data, "prepared_by"), font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "확인자",       font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, v(data, "approver"),    font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 2, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    write_cell(ws, row, 3, 4, "",      font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "",      font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def build_piling_use_workplan_excel(form_data: Dict[str, Any]) -> bytes:
    """form_data dict를 받아 항타기·항발기 사용 작업계획서 xlsx 바이너리를 반환한다."""
    data = form_data or {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_machine_info(ws, row, data)
    row = _write_work_steps(ws, row, data)
    row = _write_hazard_table(ws, row, data)
    row = _write_emergency(ws, row, data)
    row = _write_signature(ws, row, data)

    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

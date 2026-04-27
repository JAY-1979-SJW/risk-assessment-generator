"""
항타기·항발기·천공기 사용계획서 — Excel 출력 모듈 (v1).

법적 근거: 산업안전보건기준에 관한 규칙 제38조 제1항 제12호, 제186조~제197조
분류: 법정 작업계획서 (EQ-009)
      법정 별지 서식 없음 — 자체 표준서식.

Required form_data keys:
    machine_type         str  기계 종류 (항타기/항발기/천공기)
    machine_capacity     str  기계 성능 및 최대작업능력
    work_method          str  작업방법

Optional form_data keys:
    site_name            str  현장명
    project_name         str  공사명
    work_location        str  작업위치
    work_date            str  작업기간
    contractor           str  작업업체
    supervisor           str  작업책임자
    prepared_by          str  작성자
    sign_date            str  작성일
    machine_model        str  기계 모델명
    machine_capacity_kn  str  항타 능력(kN) 또는 굴착 깊이(m)
    pile_type            str  말뚝 종류 (강관말뚝/PC말뚝/H형강 등)
    pile_length          str  말뚝 길이
    pile_count           str  말뚝 본수
    ground_survey        str  지반 조사 결과 요약
    underground_facilities str 지하매설물 현황
    adjacent_structures  str  인접 구조물 현황
    noise_vibration_measure str 소음·진동 저감 대책
    dust_measure         str  분진 대책
    emergency_measure    str  비상조치 방법
    emergency_contact    str  비상연락처

    hazard_items  list[dict]  위험요인 분석 (repeat_field)
        hazard_type          str  위험 유형
        hazard_description   str  위험 요인 내용
        preventive_measure   str  예방 대책
        responsible_person   str  담당자
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    FONT_TITLE, FONT_SUBTITLE, FONT_BOLD, FONT_DEFAULT, FONT_SMALL,
    FILL_LABEL, FILL_SECTION, FILL_HEADER, FILL_NONE,
    ALIGN_CENTER, ALIGN_LEFT, ALIGN_LABEL,
    v, write_cell, border_rect, apply_col_widths, write_blank_row,
)

DOC_ID     = "EQ-009"
FORM_TYPE  = "piling_workplan"
SHEET_NAME = "항타기사용계획서"

SHEET_HEADING  = "항타기·항발기·천공기 사용계획서"
SHEET_SUBTITLE = (
    "「산업안전보건기준에 관한 규칙」 제38조 제1항 제12호, 제186조~제197조에 따른 "
    "항타기·항발기·천공기 사용 작업계획서 (EQ-009)"
)

TOTAL_COLS    = 8
MAX_HAZARD    = 10
MIN_HAZARD    = 5

_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

# 기본정보 열 구조
_L1, _V1S, _V1E        = 1, 2, 4   # 좌: 라벨=A, 값=B:D
_L2, _V2S, _V2E        = 5, 6, 8   # 우: 라벨=E, 값=F:H
_FULL_S, _FULL_E       = 2, 8      # 전폭 값 영역


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


def _write_lv(ws, row: int, label: str, value: Any,
              lc: int, vs: int, ve: int, height: float = 20) -> None:
    write_cell(ws, row, lc, lc, label,
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, vs, ve, value,
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height


def _write_meta(ws, row: int, data: Dict[str, Any]) -> int:
    _write_lv(ws, row, "현장명",   v(data, "site_name"),    _L1, _V1S, _V1E)
    _write_lv(ws, row, "공사명",   v(data, "project_name"), _L2, _V2S, _V2E)
    row += 1
    _write_lv(ws, row, "작업위치", v(data, "work_location"), _L1, _V1S, _V1E)
    _write_lv(ws, row, "작업기간", v(data, "work_date"),     _L2, _V2S, _V2E)
    row += 1
    _write_lv(ws, row, "작업업체", v(data, "contractor"),   _L1, _V1S, _V1E)
    _write_lv(ws, row, "작업책임자", v(data, "supervisor"), _L2, _V2S, _V2E)
    return row + 1


def _write_section_header(ws, row: int, title: str) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, title,
               font=FONT_BOLD, fill=FILL_SECTION, align=ALIGN_CENTER, height=22)
    return row + 1


def _write_machine_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _write_section_header(ws, row, "▶ 사용 기계 제원")
    _write_lv(ws, row, "기계 종류",         v(data, "machine_type"),        _L1, _V1S, _V1E)
    _write_lv(ws, row, "기계 모델",         v(data, "machine_model"),       _L2, _V2S, _V2E)
    row += 1
    _write_lv(ws, row, "성능·최대능력",     v(data, "machine_capacity"),    _L1, _V1S, _V1E)
    _write_lv(ws, row, "항타능력/굴착깊이", v(data, "machine_capacity_kn"), _L2, _V2S, _V2E)
    row += 1
    _write_lv(ws, row, "말뚝 종류",  v(data, "pile_type"),   _L1, _V1S, _V1E)
    _write_lv(ws, row, "말뚝 길이",  v(data, "pile_length"), _L2, _V2S, _V2E)
    row += 1
    _write_lv(ws, row, "말뚝 본수",  v(data, "pile_count"),  _L1, _V1S, _V1E)
    write_cell(ws, row, _L2, _L2, "", font=FONT_DEFAULT, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, _V2S, _V2E, "", font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 20
    return row + 1


def _write_work_overview(ws, row: int, data: Dict[str, Any]) -> int:
    row = _write_section_header(ws, row, "▶ 작업 개요")
    # 작업방법 (2행 분량)
    write_cell(ws, row, 1, 1, "작업방법",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "work_method"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    row += 1
    # 지반 조사
    write_cell(ws, row, 1, 1, "지반조사",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "ground_survey"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    row += 1
    # 지하매설물
    write_cell(ws, row, 1, 1, "지하매설물",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "underground_facilities"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    row += 1
    # 인접 구조물
    write_cell(ws, row, 1, 1, "인접구조물",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "adjacent_structures"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    return row + 1


def _write_env_measures(ws, row: int, data: Dict[str, Any]) -> int:
    row = _write_section_header(ws, row, "▶ 환경·민원 저감 대책")
    _write_lv(ws, row, "소음·진동 저감", v(data, "noise_vibration_measure"), _L1, _V1S, _FULL_E, height=24)
    row += 1
    _write_lv(ws, row, "분진 대책",      v(data, "dust_measure"),            _L1, _V1S, _FULL_E, height=24)
    return row + 1


def _write_hazard_table(ws, row: int, data: Dict[str, Any]) -> int:
    row = _write_section_header(ws, row, "▶ 위험요인 및 안전대책")
    # 헤더행
    headers = ["번호", "위험 유형", "위험 요인 내용", "예방 대책", "담당자"]
    col_spans = [(1,1), (2,2), (3,5), (6,7), (8,8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    hazard_items: List[Dict[str, Any]] = data.get("hazard_items") or []
    display_rows = max(MIN_HAZARD, len(hazard_items))
    display_rows = min(display_rows, MAX_HAZARD)

    for i in range(display_rows):
        item = hazard_items[i] if i < len(hazard_items) else {}
        write_cell(ws, row, 1, 1, i + 1, font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 2, v(item, "hazard_type"),        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 5, v(item, "hazard_description"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 7, v(item, "preventive_measure"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "responsible_person"), font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _write_emergency(ws, row: int, data: Dict[str, Any]) -> int:
    row = _write_section_header(ws, row, "▶ 비상조치 계획")
    _write_lv(ws, row, "비상조치",  v(data, "emergency_measure"), _L1, _V1S, _FULL_E, height=24)
    row += 1
    _write_lv(ws, row, "비상연락처", v(data, "emergency_contact"), _L1, _V1S, _FULL_E, height=20)
    return row + 1


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _write_section_header(ws, row, "▶ 확인")
    # 라벨행
    write_cell(ws, row, 1, 2, "작성자",      font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, 4, v(data, "prepared_by"), font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "작성일",      font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, v(data, "sign_date"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1
    # 서명 공간
    write_cell(ws, row, 1, 2, "서명",        font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    write_cell(ws, row, 3, 8, "",            font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def build_piling_workplan_excel(form_data: Dict[str, Any]) -> bytes:
    """form_data dict를 받아 항타기·항발기·천공기 사용계획서 xlsx 바이너리를 반환한다."""
    data = form_data or {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_machine_info(ws, row, data)
    row = _write_work_overview(ws, row, data)
    row = _write_env_measures(ws, row, data)
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

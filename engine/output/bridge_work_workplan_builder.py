"""교량 설치·해체·변경 작업계획서 builder (WP-004)."""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Mapping

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    ALIGN_CENTER,
    ALIGN_LABEL,
    ALIGN_LEFT,
    FILL_HEADER,
    FILL_LABEL,
    FILL_NONE,
    FILL_SECTION,
    FONT_BOLD,
    FONT_DEFAULT,
    FONT_SMALL,
    FONT_SUBTITLE,
    FONT_TITLE,
    apply_col_widths,
    v,
    write_cell,
)

# ---------------------------------------------------------------------------
# 문서 메타데이터
# ---------------------------------------------------------------------------

DOC_ID         = "WP-004"
FORM_TYPE      = "bridge_work_workplan"
SHEET_NAME     = "교량작업계획서"
SHEET_HEADING  = "교량 설치·해체·변경 작업계획서"
SHEET_SUBTITLE = (
    "「산업안전보건기준에 관한 규칙」 제38조 제1항 제8호에 따른 법정 작업계획서"
    f" ({DOC_ID})"
)

# ---------------------------------------------------------------------------
# 열 구조 (8컬럼)
# ---------------------------------------------------------------------------

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_STEP_ROWS    = 10
MIN_STEP_ROWS    = 5
MAX_CONTACT_ROWS = 3


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


def _section_header(ws, row: int, title: str) -> int:
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
    row = _section_header(ws, row, "▶ 기본 정보")
    _lv(ws, row, "현장명",   v(data, "site_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",   v(data, "project_name"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "업체명",   v(data, "contractor"),   _L1, _V1S, _V1E)
    _lv(ws, row, "작업일자", v(data, "work_date"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업위치", v(data, "work_location"), _L1, _V1S, _V1E)
    _lv(ws, row, "작업지휘자", v(data, "supervisor"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업내용", v(data, "work_summary"),  _L1, _V1S, _V1E)
    _lv(ws, row, "작성자",   v(data, "prepared_by"),   _L2, _V2S, _V2E)
    return row + 1


def _write_bridge_info(ws, row: int, data: Dict[str, Any]) -> int:
    """교량 공사 법정 기재사항 (제38조 제1항 제8호)."""
    row = _section_header(ws, row, "▶ 교량 정보 (법정 기재사항)")

    pairs = [
        ("작업 구분",     "work_type",         "설치·해체·변경"),
        ("교량 명칭",     "bridge_name",       ""),
        ("교량 형식",     "bridge_type",       ""),
        ("경간 길이(m)",  "span_length",       ""),
        ("최대 높이(m)",  "max_height",        ""),
        ("사용 장비",     "equipment",         ""),
        ("하부 조건",     "ground_condition",  ""),
        ("지지 방법",     "support_method",    ""),
    ]

    for i, (label, key, placeholder) in enumerate(pairs):
        lc = _L1 if i % 2 == 0 else _L2
        vs = _V1S if i % 2 == 0 else _V2S
        ve = _V1E if i % 2 == 0 else _V2E
        if i % 2 == 0 and i > 0:
            row += 1
        val = v(data, key) or placeholder
        _lv(ws, row, label, val, lc, vs, ve)

    row += 1
    write_cell(ws, row, 1, 1, "작업 개요",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "work_detail"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _write_safety_steps(ws, row: int, data: Dict[str, Any]) -> int:
    """작업단계별 안전조치 반복 테이블."""
    row = _section_header(ws, row, "▶ 작업단계별 안전조치")

    headers   = ["번호", "작업 단계",   "위험 요인",   "안전 조치",   "담당자"]
    col_spans = [(1, 1),  (2, 3),        (4, 5),        (6, 7),        (8, 8)]
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
        write_cell(ws, row, 8, 8, v(item, "responsible"),    font=FONT_SMALL,   align=ALIGN_CENTER)
        row += 1
    return row


def _write_emergency_contacts(ws, row: int, data: Dict[str, Any]) -> int:
    """비상연락망 및 조치 계획."""
    row = _section_header(ws, row, "▶ 비상조치 계획")

    write_cell(ws, row, 1, 2, "역할",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, 5, "성명",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 8, "연락처", font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    raw: Any = data.get("emergency_contacts")
    contacts: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    for i in range(max(MAX_CONTACT_ROWS, len(contacts))):
        contact = contacts[i] if i < len(contacts) else {}
        write_cell(ws, row, 1, 2, v(contact, "role"),  font=FONT_DEFAULT, align=ALIGN_CENTER, height=20)
        write_cell(ws, row, 3, 5, v(contact, "name"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 8, v(contact, "phone"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1

    row = _section_header(ws, row, "▶ 비상조치 방법")
    write_cell(ws, row, 1, 1, "조치 내용",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "emergency_measure"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    write_cell(ws, row, 1, 2, "작업지휘자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, 4, v(data, "supervisor"), font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "확인자",    font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, v(data, "approver"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
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


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def build_bridge_work_workplan_excel(
    form_data: Mapping[str, Any],
) -> bytes:
    """form_data dict를 받아 교량 설치·해체·변경 작업계획서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_bridge_info(ws, row, data)
    row = _write_safety_steps(ws, row, data)
    row = _write_emergency_contacts(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

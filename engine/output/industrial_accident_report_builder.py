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

DOC_ID     = "EM-001"
FORM_TYPE  = "industrial_accident_report"
SHEET_NAME = "산업재해조사표"
SHEET_HEADING  = "산업재해조사표"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제57조, 시행규칙 제73조에 따른 법정 기재항목 확인용 작성 보조서식"
    f" ({DOC_ID})"
)
SHEET_NOTICE = (
    "※ 이 서식은 법정 제출 전 내용 확인·정리를 위한 보조서식입니다. "
    "공식 제출은 고용노동부 별지 제30호서식(e-고용보험 등)을 사용하십시오."
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_CAUSE_ROWS = 6
MIN_CAUSE_ROWS = 3


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
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_NOTICE,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_CENTER, height=16)
    return row + 1


def _write_workplace_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 사업장 정보 (법정 기재사항)")
    _lv(ws, row, "사업장명",     v(data, "workplace_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "사업자등록번호", v(data, "business_reg_no"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "소재지",       v(data, "workplace_address"), _L1, _V1S, _V1E)
    _lv(ws, row, "업종",         v(data, "industry_type"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "상시근로자수", v(data, "worker_count"),      _L1, _V1S, _V1E)
    _lv(ws, row, "대표자",       v(data, "representative"),    _L2, _V2S, _V2E)
    return row + 1


def _write_victim_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 재해자 정보 (법정 기재사항)")
    _lv(ws, row, "성명",         v(data, "victim_name"),         _L1, _V1S, _V1E)
    _lv(ws, row, "성별",         v(data, "victim_gender"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "생년월일",     v(data, "victim_birth"),        _L1, _V1S, _V1E)
    _lv(ws, row, "국적",         v(data, "victim_nationality"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "고용형태",     v(data, "employment_type"),     _L1, _V1S, _V1E)
    _lv(ws, row, "직종",         v(data, "occupation"),          _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "근속기간",     v(data, "tenure"),              _L1, _V1S, _V1E)
    _lv(ws, row, "상해부위",     v(data, "injury_part"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "상해종류",     v(data, "injury_type"),         _L1, _V1S, _V1E)
    _lv(ws, row, "휴업일수",     v(data, "sick_leave_days"),     _L2, _V2S, _V2E)
    return row + 1


def _write_accident_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 재해 발생 상황 (법정 기재사항)")
    _lv(ws, row, "발생일시",     v(data, "accident_datetime"),   _L1, _V1S, _V1E)
    _lv(ws, row, "발생 장소",    v(data, "accident_location"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "재해유형",     v(data, "accident_type"),       _L1, _V1S, _V1E)
    _lv(ws, row, "기인물",       v(data, "causative_object"),    _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 1, "재해 경위",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "accident_description"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    row += 1
    write_cell(ws, row, 1, 1, "목격자",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "witness"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    return row + 1


def _write_cause_measures(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 재해 원인 및 재발방지 대책 (법정 기재사항)")

    headers   = ["번호", "원인 구분",      "원인 내용",          "재발방지 대책",      "이행 기한",  "담당자"]
    col_spans = [(1, 1),  (2, 2),           (3, 4),               (5, 6),               (7, 7),       (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("cause_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_CAUSE_ROWS, len(items))
    display = min(display, MAX_CAUSE_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                     font=FONT_DEFAULT, align=ALIGN_CENTER, height=26)
        write_cell(ws, row, 2, 2, v(item, "cause_category"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 4, v(item, "cause_detail"),    font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 6, v(item, "prevention"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, v(item, "deadline"),        font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "responsible"),     font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _write_report_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 보고 정보")
    _lv(ws, row, "보고일자",     v(data, "report_date"),         _L1, _V1S, _V1E)
    _lv(ws, row, "보고자",       v(data, "reporter"),            _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "안전보건관리책임자", v(data, "safety_manager"), _L1, _V1S, _V1E)
    _lv(ws, row, "제출처",       v(data, "submit_to"),           _L2, _V2S, _V2E)
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


def build_industrial_accident_report_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 산업재해조사표 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_workplace_info(ws, row, data)
    row = _write_victim_info(ws, row, data)
    row = _write_accident_info(ws, row, data)
    row = _write_cause_measures(ws, row, data)
    row = _write_report_info(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

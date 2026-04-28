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

DOC_ID     = "EM-004"
FORM_TYPE  = "serious_accident_immediate_report"
SHEET_NAME = "중대재해 즉시 보고서"
SHEET_HEADING  = "중대재해 발생 즉시 보고서"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제54조(중대재해 발생 시 사업주 조치·보고 의무)에 따른 초동 보고"
    f" ({DOC_ID})"
)
# 산업안전보건법 제54조는 즉시 보고 의무를 규정하나, 별지 서식이 지정되어 있지 않음.
# 이 서식은 해당 의무 이행을 지원하는 내부 초동보고 보조서식임.
SHEET_NOTICE = (
    "※ 이 서식은 법정 제출 서식이 아닙니다. 중대재해 발생 초동 대응 및 내부 보고를 위한 "
    "보조서식으로, 실제 보고는 고용노동부(☎1350) 유선·팩스 또는 e-고용보험을 통해 하십시오."
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 10, 5: 14, 6: 10, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8


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
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_CENTER, height=28)
    return row + 1


def _write_site_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 현장·공사 기본정보")
    _lv(ws, row, "현장명",   v(data, "site_name"),     _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",   v(data, "project_name"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "사업주",   v(data, "owner_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "업체명",   v(data, "company_name"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "현장소장", v(data, "site_manager"),  _L1, _V1S, _V1E)
    _lv(ws, row, "연락처",   v(data, "contact"),       _L2, _V2S, _V2E)
    return row + 1


def _write_accident_overview(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 사고 발생 개요")
    _lv(ws, row, "발생 일시", v(data, "accident_datetime"), _L1, _V1S, _V1E)
    _lv(ws, row, "발생 장소", v(data, "accident_location"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "사고 유형", v(data, "accident_type"),     _L1, _V1S, _V1E)
    _lv(ws, row, "작업 종류", v(data, "work_type"),         _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 1, "사고 경위",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=48)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "accident_summary"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=48)
    return row + 1


def _write_casualty(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 피해 현황")
    _lv(ws, row, "사망자 수", v(data, "death_count"),   _L1, _V1S, _V1E)
    _lv(ws, row, "부상자 수", v(data, "injury_count"),  _L2, _V2S, _V2E)
    row += 1

    write_cell(ws, row, 1, TOTAL_COLS,
               "※ 피해자 성명·주민등록번호 등 민감한 개인정보는 이 서식에 기재하지 마십시오. "
               "공식 보고서(산업재해조사표 등)에 별도 기재하십시오.",
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT, height=20)
    row += 1

    # 피해 인원 간략 현황 (가명/직종만)
    headers   = ["번호", "직종·역할",       "부상 유형",    "현재 상태",  "비고"]
    col_spans = [(1, 1),  (2, 3),            (4, 5),         (6, 7),       (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("casualty_rows")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    for i in range(max(3, len(items))):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                 font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 3, v(item, "role"),        font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 5, v(item, "injury_type"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 7, v(item, "status"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "remarks"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_immediate_actions(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 즉시 조치 사항")

    # 작업중지/출입통제
    _lv(ws, row, "작업중지 여부",  v(data, "work_stopped"),      _L1, _V1S, _V1E)
    _lv(ws, row, "출입통제 여부",  v(data, "access_controlled"), _L2, _V2S, _V2E)
    row += 1

    # 관계기관 신고
    row = _section_header(ws, row, "  관계기관 신고 현황")
    headers   = ["신고 기관",        "신고 일시",   "신고 방법",   "접수 담당자", "비고"]
    col_spans = [(1, 2),              (3, 4),        (5, 5),        (6, 7),        (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("agency_reports")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    default_agencies = ["고용노동부(1350)", "경찰서", "소방서"]
    for i in range(max(3, len(items))):
        item = items[i] if i < len(items) else {}
        agency = v(item, "agency") or (default_agencies[i] if i < len(default_agencies) else "")
        write_cell(ws, row, 1, 2, agency,               font=FONT_DEFAULT, align=ALIGN_LEFT, height=22)
        write_cell(ws, row, 3, 4, v(item, "datetime"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(item, "method"),    font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 7, v(item, "receiver"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "remarks"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_risk_and_countermeasure(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 추가 위험요인 및 재발방지 임시조치")

    write_cell(ws, row, 1, 1, "추가 위험요인",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=44)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "additional_risks"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=44)
    row += 1

    write_cell(ws, row, 1, 1, "재발방지\n임시조치",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=44)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "temporary_countermeasures"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=44)
    return row + 1


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 보고자 / 확인자")
    _lv(ws, row, "보고 일시", v(data, "report_datetime"), _L1, _V1S, _V1E)
    _lv(ws, row, "보고자",   v(data, "reporter"),         _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 2, "서명 (보고자)",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=40)
    write_cell(ws, row, 3, 4, "", font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "확인자 (현장소장)",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "", font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _finalize_sheet(ws) -> None:
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75


def build_serious_accident_immediate_report_excel(
    form_data: Mapping[str, Any],
) -> bytes:
    """form_data dict를 받아 중대재해 발생 즉시 보고서 xlsx 바이너리를 반환한다.

    법정 제출 서식 아님. 산업안전보건법 제54조 즉시 보고 의무 이행을 위한 내부 초동보고 보조서식.
    """
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_site_info(ws, row, data)
    row = _write_accident_overview(ws, row, data)
    row = _write_casualty(ws, row, data)
    row = _write_immediate_actions(ws, row, data)
    row = _write_risk_and_countermeasure(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

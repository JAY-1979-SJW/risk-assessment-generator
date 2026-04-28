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
    "산업안전보건법 시행규칙 별지 제30호서식 <개정 2025. 10. 1.> 기반 — 법정 기재항목 확인용 작성 보조서식"
    f" ({DOC_ID})"
)
SHEET_NOTICE = (
    "※ 사망 또는 3일 이상 휴업 재해 발생 시 1개월 이내 제출 의무 | "
    "근로복지공단 요양급여 신청과 별도 제출 필요 | "
    "개인정보·민감정보 최소 기재 | "
    "근로자대표 확인 및 이견 첨부 여부 확인 | "
    "공식 제출 전 최신 법령 서식 확인 필요 (고용노동부 별지 제30호서식)"
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
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_CENTER, height=28)
    return row + 1


def _write_workplace_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 사업장 정보 (법정 기재사항)")
    _lv(ws, row, "사업장명",         v(data, "workplace_name"),       _L1, _V1S, _V1E)
    _lv(ws, row, "사업자등록번호",   v(data, "business_reg_no"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "소재지",           v(data, "workplace_address"),     _L1, _V1S, _V1E)
    _lv(ws, row, "업종",             v(data, "industry_type"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "상시근로자수",     v(data, "worker_count"),          _L1, _V1S, _V1E)
    _lv(ws, row, "대표자",           v(data, "representative"),        _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "산재관리번호\n(사업개시번호)", v(data, "industrial_accident_no"), _L1, _V1S, _V1E)
    _lv(ws, row, "원·수급 구분",     v(data, "contractor_type"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "원수급 사업장명",  v(data, "prime_contractor_name"), _L1, _V1S, _V1E)
    _lv(ws, row, "발주자 구분",      v(data, "client_type"),           _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "공사현장명",       v(data, "construction_site"),     _L1, _V1S, _V1E)
    _lv(ws, row, "공사종류",         v(data, "construction_type"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "공정률",           v(data, "construction_progress"), _L1, _V1S, _V1E)
    _lv(ws, row, "공사금액",         v(data, "construction_amount"),   _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS,
               "※ 건설업·파견·수급 해당 시 원수급 사업장 정보 및 공사현장 정보 기재. 해당 없으면 공란.",
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT, height=16)
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
    _lv(ws, row, "근무형태",     v(data, "work_type"),           _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "직종",         v(data, "occupation"),          _L1, _V1S, _V1E)
    _lv(ws, row, "입사일",       v(data, "entry_date"),          _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "근속기간",     v(data, "tenure"),              _L1, _V1S, _V1E)
    _lv(ws, row, "사망 여부",    v(data, "is_fatal"),            _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "상해 부위",    v(data, "injury_part"),         _L1, _V1S, _V1E)
    _lv(ws, row, "상해 종류",    v(data, "injury_type"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "상병명",       v(data, "disease_name"),        _L1, _V1S, _V1E)
    _lv(ws, row, "휴업 예상일수", v(data, "sick_leave_days"),    _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS,
               "※ 동일 재해로 다수 재해자 발생 시 재해자별로 별도 작성 (별지 제30호서식 각칙 참고)",
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT, height=16)
    return row + 1


def _write_accident_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 재해 발생 상황 (법정 기재사항)")
    _lv(ws, row, "발생일시",     v(data, "accident_datetime"),   _L1, _V1S, _V1E)
    _lv(ws, row, "발생 장소",    v(data, "accident_location"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "재해 유형",    v(data, "accident_type"),       _L1, _V1S, _V1E)
    _lv(ws, row, "기인물",       v(data, "causative_object"),    _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 1, "작업 내용",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "work_content"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
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
    row = _section_header(ws, row, "▶ 재발방지계획 (법정 기재사항)")

    # 직접/간접 원인 요약
    _lv(ws, row, "직접 원인",    v(data, "direct_cause"),        _L1, _V1S, _V1E)
    _lv(ws, row, "간접 원인",    v(data, "indirect_cause"),      _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 1, "즉시 조치",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "immediate_action"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    row += 1

    headers   = ["번호", "원인 구분",    "원인 내용",    "개선 대책",    "완료 예정일", "책임자"]
    col_spans = [(1, 1),  (2, 2),         (3, 4),         (5, 6),         (7, 7),        (8, 8)]
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

    _lv(ws, row, "확인자",       v(data, "checker"),             _L1, _V1S, _V1E)
    _lv(ws, row, "확인일",       v(data, "check_date"),          _L2, _V2S, _V2E)
    return row + 1


def _write_report_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인 및 제출 정보")
    _lv(ws, row, "제출일",           v(data, "report_date"),         _L1, _V1S, _V1E)
    _lv(ws, row, "관할 지방고용노동관서", v(data, "submit_to"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "제출 방법",        v(data, "submit_method"),       _L1, _V1S, _V1E)
    _lv(ws, row, "안전보건관리책임자", v(data, "safety_manager"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "근로자대표 확인",  v(data, "worker_rep_confirmed"), _L1, _V1S, _V1E)
    _lv(ws, row, "근로자대표 이견",  v(data, "worker_rep_opinion"),   _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 2, "사업주\n(대표자) 서명", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=40)
    write_cell(ws, row, 3, 4, "",                        font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "작성자 서명",             font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "",                        font=FONT_DEFAULT, align=ALIGN_LEFT)
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

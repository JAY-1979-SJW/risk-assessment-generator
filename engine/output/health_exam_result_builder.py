"""
근로자 건강진단 결과 확인서 — Excel 출력 모듈 (v1.0).

법적 근거: 산업안전보건법 제129조~제131조, 시행규칙 제97조
분류:     legal — 사업장 건강진단 실시·결과 자체 관리 확인서
          (공식 검진기관 발급 결과통보서 원본을 대체하지 않음)

법정 기재사항:
- 현장명, 업체명, 건강진단 종류·기간, 검진기관
- 대상 근로자 명단: 성명, 직종, 진단 종류, 결과, 사후관리 조치
- 작성일, 작성자, 확인자

Input — form_data dict:
    site_name          str|None   현장(사업장)명
    company_name       str|None   업체명
    exam_year          str|None   건강진단 연도
    exam_type          str|None   건강진단 종류 (일반/특수/배치전/수시/임시)
    exam_period        str|None   실시 기간
    exam_agency        str|None   검진기관명
    exam_agency_contact str|None  검진기관 연락처
    total_workers      str|None   대상 근로자 수
    supervisor         str|None   작성자
    approver           str|None   확인자
    sign_date          str|None   작성일

    worker_rows  list[dict]  근로자별 결과 (MAX_ROWS=20)
        name             str|None   성명
        job_type         str|None   직종
        exam_type        str|None   진단 종류
        result           str|None   판정 결과 (정상A/일반질환B/직업병C/…)
        followup         str|None   사후관리 조치
        remarks          str|None   비고

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

DOC_ID     = "CM-003"
FORM_TYPE  = "health_exam_result"
SHEET_NAME = "근로자 건강진단 결과 확인서"
SHEET_HEADING  = "근로자 건강진단 결과 확인서"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제129조~제131조에 따른 건강진단 결과 관리 확인서"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 4, 2: 14, 3: 12, 4: 12, 5: 16, 6: 14, 7: 14, 8: 12,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_WORKER_ROWS = 20
MIN_WORKER_ROWS = 10


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
    _lv(ws, row, "현장(사업장)명", v(data, "site_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "업체명",         v(data, "company_name"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "건강진단 종류",  v(data, "exam_type"),    _L1, _V1S, _V1E)
    _lv(ws, row, "실시 기간",      v(data, "exam_period"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "진단 연도",      v(data, "exam_year"),    _L1, _V1S, _V1E)
    _lv(ws, row, "대상 근로자 수", v(data, "total_workers"),_L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "검진기관명",     v(data, "exam_agency"),         _L1, _V1S, _V1E)
    _lv(ws, row, "검진기관 연락처",v(data, "exam_agency_contact"),  _L2, _V2S, _V2E)
    return row + 1


def _write_worker_table(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 근로자별 건강진단 결과 (법정 기재사항)")

    headers   = ["번호", "성명",   "직종",   "진단 종류", "판정 결과",   "사후관리 조치", "비고"]
    col_spans = [(1, 1),  (2, 2),   (3, 3),   (4, 4),      (5, 5),        (6, 7),          (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("worker_rows")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_WORKER_ROWS, len(items))
    display = min(display, MAX_WORKER_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 2, v(item, "name"),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 3, v(item, "job_type"),   font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 4, 4, v(item, "exam_type"),  font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(item, "result"),     font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 7, v(item, "followup"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "remarks"),    font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_notice(ws, row: int) -> int:
    row = _section_header(ws, row, "▶ 유의사항")
    notice = "※ 이 확인서는 사업장 내부 관리용입니다. 공식 검진기관 발급 결과통보서 원본은 별도 보관하시기 바랍니다."
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT, height=20)
    return row + 1


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    write_cell(ws, row, 1, 1, "작성일",             font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 2, 3, v(data, "sign_date"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 4, 5, "작성자",              font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 6, v(data, "supervisor"), font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 7, 7, "확인자",              font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 8, v(data, "approver"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
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


def build_health_exam_result_excel(
    form_data: Mapping[str, Any],
) -> bytes:
    """form_data dict를 받아 근로자 건강진단 결과 확인서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_worker_table(ws, row, data)
    row = _write_notice(ws, row)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)
    ws.print_title_rows = "1:9"

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

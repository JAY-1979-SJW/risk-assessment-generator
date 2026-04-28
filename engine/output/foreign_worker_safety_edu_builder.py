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

DOC_ID     = "CM-006"
FORM_TYPE  = "foreign_worker_safety_edu"
SHEET_NAME = "외국인 근로자 안전보건 교육 확인서"
SHEET_HEADING  = "외국인 근로자 안전보건 교육 확인서"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제29조(근로자에 대한 안전보건교육)에 따른 교육 실시 확인"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 5, 2: 14, 3: 12, 4: 10, 5: 12, 6: 10, 7: 12, 8: 12,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MIN_WORKER_ROWS = 5
MAX_WORKER_ROWS = 20


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
    write_cell(ws, row, 1, TOTAL_COLS,
               "※ 이 확인서는 사업장 내부 작성 보조용입니다. 원본은 교육 관련 서류철에 보관하시기 바랍니다.",
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_CENTER, height=16)
    return row + 1


def _write_site_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 현장 및 교육 정보")
    _lv(ws, row, "현장명",     v(data, "site_name"),      _L1, _V1S, _V1E)
    _lv(ws, row, "업체명",     v(data, "company_name"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "교육일자",   v(data, "edu_date"),        _L1, _V1S, _V1E)
    _lv(ws, row, "교육시간",   v(data, "edu_duration"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "교육 과정명", v(data, "edu_course"),     _L1, _V1S, _V1E)
    _lv(ws, row, "교육 장소",  v(data, "edu_location"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "강사명",     v(data, "instructor"),      _L1, _V1S, _V1E)
    _lv(ws, row, "교육 언어",  v(data, "edu_language"),    _L2, _V2S, _V2E)
    return row + 1


def _write_edu_content(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 교육 내용 (핵심 기재사항)")
    headers   = ["번호", "교육 항목",              "비고"]
    col_spans = [(1, 1),  (2, 7),                   (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("edu_items")
    items: List[Any] = raw if isinstance(raw, list) else []
    display = max(3, len(items))
    display = min(display, 10)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        if isinstance(item, str):
            content, remark = item, ""
        else:
            content = v(item, "content")
            remark  = v(item, "remark")
        write_cell(ws, row, 1, 1, i + 1,   font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 7, content,  font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, remark,   font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_worker_table(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 교육 참여 근로자 명단")

    headers   = ["번호", "성명(가명 가능)", "국적",   "소속",    "직종",    "서명란",  "확인",   "비고"]
    col_spans = [(1, 1),  (2, 3),           (4, 4),   (5, 5),    (6, 6),    (7, 7),    (8, 8),   None]
    # 8컬럼으로 매핑
    hdr_cols = [(1,1),(2,3),(4,4),(5,5),(6,6),(7,7),(8,8)]
    hdrs     = ["번호","성명(가명 가능)","국적","소속","직종","서명란","비고"]
    for (cs, ce), hdr in zip(hdr_cols, hdrs):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    write_cell(ws, row, 1, TOTAL_COLS,
               "※ 성명란에 실명 대신 근로자 고유번호 또는 가명을 사용할 수 있습니다. 민감한 개인정보(여권번호 등)는 기재하지 마십시오.",
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT, height=16)
    row += 1

    raw: Any = data.get("worker_rows")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_WORKER_ROWS, len(items))
    display = min(display, MAX_WORKER_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,              font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 3, v(item, "name"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 4, v(item, "nation"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(item, "team"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 6, v(item, "job"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, "",                  font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 확인")
    write_cell(ws, row, 1, 2, "교육 실시자",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, 4, v(data, "instructor"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "관리감독자",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, v(data, "supervisor"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 2, "서명",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=40)
    write_cell(ws, row, 3, 4, "", font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "서명",
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


def build_foreign_worker_safety_edu_excel(
    form_data: Mapping[str, Any],
) -> bytes:
    """form_data dict를 받아 외국인 근로자 안전보건 교육 확인서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_site_info(ws, row, data)
    row = _write_edu_content(ws, row, data)
    row = _write_worker_table(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

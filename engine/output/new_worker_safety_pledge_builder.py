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

DOC_ID     = "CM-005"
FORM_TYPE  = "new_worker_safety_pledge"
SHEET_NAME = "신규 근로자 안전보건 서약서"
SHEET_HEADING  = "신규 근로자 안전보건 서약서"
SHEET_SUBTITLE = (
    "「중대재해처벌법」 시행령 제4조(안전보건관리체계 구축 의무)에 따른 안전보건 서약"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 5, 2: 16, 3: 14, 4: 14, 5: 14, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8
_FULL_S, _FULL_E = 1, 8

_DEFAULT_PLEDGE_ITEMS: List[str] = [
    "본인은 현장의 안전보건관리규정 및 작업절차서를 준수하겠습니다.",
    "개인보호구(안전모·안전화·안전벨트 등)를 작업 시 반드시 착용하겠습니다.",
    "안전보건교육을 성실히 이수하고, 교육 내용을 업무에 적용하겠습니다.",
    "위험·유해 작업 발견 즉시 작업을 중지하고 관리감독자에게 보고하겠습니다.",
    "음주·약물 복용 상태에서는 절대 작업에 종사하지 않겠습니다.",
    "동료 근로자의 안전보건을 위협하는 행위를 하지 않겠습니다.",
    "비상시 대피 경로 및 비상연락처를 숙지하고 이를 준수하겠습니다.",
]


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
               "※ 이 서약서는 사업장 내부 작성 보조용입니다. 원본은 근로자 입사 서류철에 보관하시기 바랍니다.",
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_CENTER, height=16)
    return row + 1


def _write_site_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 현장 및 업체 정보")
    _lv(ws, row, "현장명",   v(data, "site_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "업체명",   v(data, "company_name"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작성일자", v(data, "sign_date"),     _L1, _V1S, _V1E)
    _lv(ws, row, "소속 부서", v(data, "department"),   _L2, _V2S, _V2E)
    return row + 1


def _write_worker_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 근로자 정보")
    _lv(ws, row, "성명",   v(data, "worker_name"),  _L1, _V1S, _V1E)
    _lv(ws, row, "직종·직위", v(data, "job_title"), _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS,
               "※ 주민등록번호 등 민감한 개인정보는 이 서식에 기재하지 마십시오.",
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT, height=16)
    return row + 1


def _write_pledge_body(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 안전보건 서약 사항")

    raw: Any = data.get("pledge_items")
    items: List[str] = raw if isinstance(raw, list) and raw else _DEFAULT_PLEDGE_ITEMS

    # 헤더
    write_cell(ws, row, 1, 1, "번호",
               font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, "서약 내용",
               font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    for i, text in enumerate(items, start=1):
        write_cell(ws, row, 1, 1, i,
                   font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, TOTAL_COLS, text,
                   font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1

    # 추가 서약 항목용 여백 행
    extras: Any = data.get("extra_pledge_items")
    extra_list: List[str] = extras if isinstance(extras, list) else []
    for j in range(max(2, len(extra_list))):
        text = extra_list[j] if j < len(extra_list) else ""
        write_cell(ws, row, 1, 1, len(items) + j + 1,
                   font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, TOTAL_COLS, text,
                   font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_pledge_statement(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 서약")
    statement = (
        "본인은 위 안전보건 서약 사항을 충분히 이해하였으며, "
        "이를 성실히 준수할 것을 서약합니다."
    )
    write_cell(ws, row, 1, TOTAL_COLS, statement,
               font=FONT_DEFAULT, fill=FILL_NONE, align=ALIGN_CENTER, height=28)
    row += 1

    _lv(ws, row, "서약일",   v(data, "sign_date"),     _L1, _V1S, _V1E)
    _lv(ws, row, "성명",     v(data, "worker_name"),   _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 4, "서명 (근로자)",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=40)
    write_cell(ws, row, 5, TOTAL_COLS, "",
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 4, "확인자 (관리감독자)",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 5, TOTAL_COLS, v(data, "supervisor"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 4, "서명 (확인자)",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=40)
    write_cell(ws, row, 5, TOTAL_COLS, "",
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _finalize_sheet(ws) -> None:
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75


def build_new_worker_safety_pledge_excel(
    form_data: Mapping[str, Any],
) -> bytes:
    """form_data dict를 받아 신규 근로자 안전보건 서약서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_site_info(ws, row, data)
    row = _write_worker_info(ws, row, data)
    row = _write_pledge_body(ws, row, data)
    row = _write_pledge_statement(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

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

DOC_ID     = "CM-004"
FORM_TYPE  = "safety_manager_appointment_report"
SHEET_NAME = "안전관리자 선임 보고서(건설업)"
SHEET_HEADING  = "안전관리자ㆍ보건관리자ㆍ산업보건의 선임 등 보고서(건설업)"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제17조·제18조·제22조, 시행규칙 제11조·제23조에 따른 선임 보고"
    " — 산업안전보건법 시행규칙 [별지 제3호서식] 기반"
    f" ({DOC_ID})"
)
SHEET_NOTICE = (
    "※ 이 서식은 공식 제출 전 내용 확인·정리를 위한 보조 입력서식입니다. "
    "실제 제출은 지방고용노동청(지청)에 최신 별지 제3호서식을 사용하여 제출하십시오."
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 16, 2: 14, 3: 12, 4: 10, 5: 14, 6: 10, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

# 유해위험방지계획서 대상 공종 체크항목 (별지 제3호서식 기준)
_HAZARD_PLAN_ITEMS: List[str] = [
    "지상높이 31m 이상 건축물", "연면적 3만㎡ 이상 건축물·냉동창고",
    "최대지간 50m 이상 교량", "터널", "다목적댐·발전용댐·홍수조절용댐",
    "굴착깊이 10m 이상 굴착공사", "지하철·지하터널 등 지하공사",
    "전력 또는 열 생산용 용광로·용융로·소각로",
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
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, height=20)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_NOTICE,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_CENTER, height=24)
    return row + 1


def _write_company_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 본사 정보 (법정 기재사항)")
    _lv(ws, row, "사업장명",       v(data, "company_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "사업자등록번호", v(data, "biz_reg_no"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "대표자",         v(data, "ceo_name"),        _L1, _V1S, _V1E)
    _lv(ws, row, "본사 소재지",    v(data, "company_address"), _L2, _V2S, _V2E)
    return row + 1


def _write_site_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 현장 개요 (법정 기재사항)")
    _lv(ws, row, "현장명",             v(data, "site_name"),          _L1, _V1S, _V1E)
    _lv(ws, row, "사업개시번호",       v(data, "biz_start_no"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "도급인(총괄관리자)", v(data, "general_contractor"), _L1, _V1S, _V1E)
    _lv(ws, row, "공사 기간",          v(data, "construction_period"),_L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "공사금액(원)",       v(data, "contract_amount"),    _L1, _V1S, _V1E)
    _lv(ws, row, "상시근로자 수",      v(data, "worker_count"),       _L2, _V2S, _V2E)
    row += 1

    # 유해위험방지계획서 대상 여부
    write_cell(ws, row, 1, 1, "유해위험\n방지계획서\n대상 여부",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=60)
    hazard_val: Any = data.get("hazard_plan_targets")
    if isinstance(hazard_val, list) and hazard_val:
        checked = "ㆍ".join(str(h) for h in hazard_val)
    else:
        hazard_yn = v(data, "hazard_plan_yn") or "해당 없음"
        checked = hazard_yn
    write_cell(ws, row, 2, TOTAL_COLS, checked,
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=60)
    return row + 1


def _write_client_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 건설공사 발주자 정보 (법정 기재사항)")
    _lv(ws, row, "발주자명",         v(data, "client_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "발주자 구분",      v(data, "client_type"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "발주자 주소",      v(data, "client_address"), _L1, _V1S, _V1E)
    _lv(ws, row, "발주자 연락처",    v(data, "client_contact"), _L2, _V2S, _V2E)
    return row + 1


def _write_manager_table(ws, row: int, title: str,
                         field_key: str, data: Dict[str, Any]) -> int:
    """안전관리자 / 보건관리자 / 산업보건의 공통 테이블."""
    row = _section_header(ws, row, title)

    write_cell(ws, row, 1, TOTAL_COLS,
               "※ 성명·생년월일·자격번호 등 개인정보는 실제 제출 서식에만 기재하고, "
               "이 보조서식에는 직책·자격종류 등 최소 정보만 기재하십시오.",
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT, height=16)
    row += 1

    hdrs     = ["번호", "성명",      "생년월일",  "자격·면허번호",  "선임일",    "전담/겸임", "연락처",  "비고"]
    col_spans= [(1, 1), (2, 3),      (4, 4),      (5, 5),           (6, 6),      (7, 7),      (8, 8),    None]
    hdr_cols = [(1,1),  (2,3),       (4,4),       (5,5),            (6,6),       (7,7),       (8,8)]
    for (cs, ce), hdr in zip(hdr_cols, hdrs[:7]):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get(field_key)
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    for i in range(max(2, len(items))):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                   font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 3, v(item, "name"),          font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 4, v(item, "birth_date"),    font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(item, "license_no"),    font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 6, v(item, "appointed_date"),font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "duty_type"),     font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "contact"),       font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_submission_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 제출 및 확인")
    write_cell(ws, row, 1, TOTAL_COLS,
               "제출처: 지방고용노동청장(지청장) 귀하 — 선임일로부터 14일 이내 제출 (산업안전보건법 시행규칙 제11조)",
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT, height=18)
    row += 1
    _lv(ws, row, "보고 일자",  v(data, "report_date"),  _L1, _V1S, _V1E)
    _lv(ws, row, "보고인",     v(data, "reporter"),     _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 4, "대표자 서명",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=40)
    write_cell(ws, row, 5, 8, "",
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


def build_safety_manager_appointment_report_excel(
    form_data: Mapping[str, Any],
) -> bytes:
    """form_data dict를 받아 안전관리자 선임 등 보고서(건설업) xlsx 바이너리를 반환한다.

    산업안전보건법 시행규칙 별지 제3호서식(건설업) 기반 보조 입력서식.
    실제 제출은 지방고용노동청에 공식 최신 서식을 사용할 것.
    """
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_company_info(ws, row, data)
    row = _write_site_info(ws, row, data)
    row = _write_client_info(ws, row, data)
    row = _write_manager_table(
        ws, row, "▶ 안전관리자 정보 (법정 기재사항)", "safety_managers", data)
    row = _write_manager_table(
        ws, row, "▶ 보건관리자 정보 (법정 기재사항)", "health_managers", data)
    row = _write_manager_table(
        ws, row, "▶ 산업보건의 정보 (법정 기재사항)", "occupational_physicians", data)
    row = _write_submission_info(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

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

DOC_ID     = "PTW-008"
FORM_TYPE  = "temp_electrical_installation_permit"
SHEET_NAME = "임시전기설치허가서"
SHEET_HEADING  = "임시전기 설치·연결 허가서"
SHEET_SUBTITLE = (
    "「산업안전보건기준에 관한 규칙」 제301조 이하에 따른 임시전기 설치·연결 작업 허가 확인"
    f" ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 6, 2: 16, 3: 10, 4: 10, 5: 14, 6: 10, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_WORKER_ROWS = 10
MIN_WORKER_ROWS = 3

# 핵심 점검 항목 (기본 제공)
_DEFAULT_CHECK_ITEMS = [
    ("전원 인입 경로 및 분전반 위치 확인", ""),
    ("임시 배선 규격·절연 상태 확인 (450/750V 이상)", ""),
    ("누전차단기 설치 여부 확인 (30mA 이하, 0.03초 이내)", ""),
    ("접지 연결 상태 확인", ""),
    ("과부하 방지 장치(퓨즈·차단기) 설치 확인", ""),
    ("배선 노출·손상 구간 방호 조치 확인", ""),
    ("방수·방진 등급 적합 여부 (옥외·습윤 장소)", ""),
    ("작업구역 통전 경고 표지 부착", ""),
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
    return row + 1


def _write_meta(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 기본 정보 (핵심 기재사항)")
    _lv(ws, row, "현장명",      v(data, "site_name"),       _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",      v(data, "project_name"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "업체명",      v(data, "company_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "허가번호",    v(data, "permit_no"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업일자",    v(data, "work_date"),       _L1, _V1S, _V1E)
    _lv(ws, row, "유효기간",    v(data, "validity_period"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업 위치",   v(data, "work_location"),   _L1, _V1S, _V1E)
    _lv(ws, row, "작업책임자",  v(data, "work_supervisor"), _L2, _V2S, _V2E)
    return row + 1


def _write_work_overview(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 작업 개요 (핵심 기재사항)")
    _lv(ws, row, "작업명",        v(data, "work_name"),        _L1, _V1S, _V1E)
    _lv(ws, row, "전압(V)",       v(data, "voltage"),          _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "전원 인입점",   v(data, "power_source"),     _L1, _V1S, _V1E)
    _lv(ws, row, "분전반 위치",   v(data, "distribution_panel"), _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, _L1, _L1, "작업 내용",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, _V1S, TOTAL_COLS, v(data, "work_description"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _write_check_table(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 임시전기 안전 확인 사항 (실무 기재사항)")

    hdr_spans = [(1, 5), (6, 7), (8, 8)]
    hdr_texts = ["확인 항목", "확인 결과", "비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("check_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    # 기본 항목 병합: 입력 데이터 우선, 부족하면 기본값으로 채움
    n = max(len(items), len(_DEFAULT_CHECK_ITEMS))
    for i in range(n):
        item = items[i] if i < len(items) else {}
        default_text, _ = _DEFAULT_CHECK_ITEMS[i] if i < len(_DEFAULT_CHECK_ITEMS) else ("", "")
        check_text = v(item, "check_item") or default_text
        write_cell(ws, row, 1, 5, check_text,          font=FONT_DEFAULT, align=ALIGN_LEFT,   height=22)
        write_cell(ws, row, 6, 7, v(item, "result"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_worker_table(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 작업자 명단 (실무 기재사항)")

    hdr_spans = [(1, 1), (2, 4), (5, 6), (7, 8)]
    hdr_texts = ["번호", "성명", "직종", "비고"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("workers")
    workers: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_WORKER_ROWS, len(workers))
    display = min(display, MAX_WORKER_ROWS)

    for i in range(display):
        worker = workers[i] if i < len(workers) else {}
        write_cell(ws, row, 1, 1, i + 1,                    font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 4, v(worker, "name"),        font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 6, v(worker, "job_type"),    font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 8, v(worker, "remarks"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 허가 확인")
    _lv(ws, row, "신청자",   v(data, "work_supervisor"), _L1, _V1S, _V1E)
    _lv(ws, row, "허가자",   v(data, "permit_issuer"),   _L2, _V2S, _V2E)
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


def build_temp_electrical_installation_permit_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 임시전기 설치·연결 허가서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_work_overview(ws, row, data)
    row = _write_check_table(ws, row, data)
    row = _write_worker_table(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

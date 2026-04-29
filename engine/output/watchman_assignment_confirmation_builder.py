"""
감시인 배치 확인서 — 부대서류 Excel 출력 모듈 (v1).

밀폐공간·화기작업·고소작업·방사선 투과검사 등 고위험 작업에서
감시인/입회자/화재감시자/출입감시자의 배치 여부, 역할, 연락체계, 교대, 확인 서명을
기록하는 부대서류.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

supplemental_type: watchman_assignment_confirmation
함수명:            build_watchman_assignment_confirmation(form_data)

Required form_data keys:
    site_name       str  현장명
    permit_date     str  작업허가 일자
    work_location   str  작업 장소

Optional form_data keys:
    parent_doc_id       str   연결 문서 ID
    parent_doc_name     str   연결 문서명
    parent_form_type    str   연결 form_type
    project_name        str   공사명
    company_name        str   회사명
    permit_no           str   작업허가서 번호
    work_type           str   작업 종류
    hazard_desc         str   감시 대상 위험요인 설명
    watch_zone          str   감시 구역 설명
    watch_start         str   감시 시작 시각
    watch_end           str   감시 종료 시각
    relief_plan         str   교대 계획
    emergency_contact   str   비상연락 체계
    stop_criteria       str   작업중지 기준
    ppe_required        str   감시인 필요 보호구
    supplement_items    str   보완사항
    supervisor          str   작업책임자 성명
    supervisor_pos      str   작업책임자 직책
    confirmer           str   확인자 성명
    confirmer_pos       str   확인자 직책
    confirm_date        str   확인 일자
    remarks             str   비고

    watchmen  list[dict]  감시인 목록 (repeat, 최대 8건)
        각 항목:
            no           int|str  순번
            name         str      성명
            company      str      소속
            role         str      역할 (감시인/화재감시자/출입통제/입회자)
            zone         str      담당구역
            start_time   str      배치 시작 시각
            contact      str      연락처
            relief_by    str      교대자
            signed       str      확인 서명 (○/-)
            remarks      str      비고
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    ALIGN_CENTER, ALIGN_LABEL, ALIGN_LEFT,
    FILL_HEADER, FILL_LABEL, FILL_NONE, FILL_NOTICE, FILL_SECTION, FILL_WARN,
    FONT_BOLD, FONT_DEFAULT, FONT_NOTICE, FONT_SMALL, FONT_SUBTITLE, FONT_TITLE,
    apply_col_widths,
    apply_a4_page_setup, set_print_area_to_used_range, v, write_cell,
)

SUPPLEMENTAL_TYPE = "watchman_assignment_confirmation"
SHEET_NAME        = "감시인배치확인서"
SHEET_HEADING     = "감시인 배치 확인서"
SHEET_SUBTITLE    = (
    "고위험 작업(밀폐공간·화기·고소·방사선 등) 감시인·입회자·화재감시자 배치 확인  "
    "[watchman_assignment_confirmation]  부대서류"
)

TOTAL_COLS   = 10
MAX_WM_ROWS  = 8

_COL_WIDTHS: Dict[int, float] = {
    1:  5,   # 순번
    2:  10,  # 성명
    3:  10,  # 소속
    4:  12,  # 역할
    5:  12,  # 담당구역
    6:  11,  # 배치시간
    7:  12,  # 연락처
    8:  10,  # 교대자
    9:  9,   # 확인 서명
    10: 12,  # 비고
}

_SIGNED_FILL = {
    "○": FILL_HEADER,
    "-": FILL_NOTICE,
}

DEFAULT_WATCHMEN: List[Dict[str, Any]] = [
    {"no":"1", "name":"", "company":"", "role":"감시인",     "zone":"작업구역 입구", "start_time":"", "contact":"", "relief_by":"", "signed":"", "remarks":""},
    {"no":"2", "name":"", "company":"", "role":"화재감시자", "zone":"작업구역 내부", "start_time":"", "contact":"", "relief_by":"", "signed":"", "remarks":"화기작업 시"},
    {"no":"3", "name":"", "company":"", "role":"출입통제",   "zone":"접근금지구역", "start_time":"", "contact":"", "relief_by":"", "signed":"", "remarks":""},
]


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _two_col(ws, row: int,
             label1: str, val1: Any,
             label2: str, val2: Any,
             height: float = 20) -> int:
    write_cell(ws, row, 1, 1, label1, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 5, val1,   font=FONT_DEFAULT, fill=FILL_NONE,  align=ALIGN_LEFT)
    write_cell(ws, row, 6, 6, label2, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 7, 10, val2,  font=FONT_DEFAULT, fill=FILL_NONE,  align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height
    return row + 1


def _full_row(ws, row: int, label: str, val: Any, height: float = 20) -> int:
    write_cell(ws, row, 1, 1, label, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, TOTAL_COLS, val, font=FONT_DEFAULT, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height
    return row + 1


def _section_header(ws, row: int, title: str) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, title,
               font=FONT_BOLD, fill=FILL_SECTION, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    return row + 1


def _blank(ws, row: int, height: float = 6) -> int:
    ws.row_dimensions[row].height = height
    return row + 1


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def build_watchman_assignment_confirmation(form_data: Dict[str, Any]) -> bytes:
    """감시인 배치 확인서 부대서류 Excel bytes 반환."""
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1

    # ── 제목 ──────────────────────────────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_HEADER, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 36
    row += 1

    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NOTICE, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1
    row = _blank(ws, row, 6)

    # ── s1. 기본정보 ───────────────────────────────────────────────────────
    row = _section_header(ws, row, "① 감시인 배치 확인서 기본정보")
    row = _two_col(ws, row, "현장명",       v(form_data, "site_name"),
                             "작업허가 일자", v(form_data, "permit_date"))
    row = _two_col(ws, row, "공사명",       v(form_data, "project_name"),
                             "회사명",       v(form_data, "company_name"))
    row = _blank(ws, row, 6)

    # ── s2. 연결 문서 정보 ─────────────────────────────────────────────────
    row = _section_header(ws, row, "② 연결 문서 정보  (부대서류)")
    row = _two_col(ws, row, "연결 문서 ID",   v(form_data, "parent_doc_id"),
                             "연결 문서명",    v(form_data, "parent_doc_name"))
    row = _two_col(ws, row, "연결 form_type", v(form_data, "parent_form_type"),
                             "비고",           v(form_data, "remarks"))
    row = _blank(ws, row, 6)

    # ── s3. 작업 정보 ──────────────────────────────────────────────────────
    row = _section_header(ws, row, "③ 작업 정보")
    row = _two_col(ws, row, "작업허가서 번호", v(form_data, "permit_no"),
                             "작업 종류",      v(form_data, "work_type"))
    row = _two_col(ws, row, "작업 장소",       v(form_data, "work_location"),
                             "작업허가 일자",  v(form_data, "permit_date"))
    row = _blank(ws, row, 6)

    # ── s4. 감시 대상 위험요인 ─────────────────────────────────────────────
    row = _section_header(ws, row, "④ 감시 대상 위험요인")
    row = _full_row(ws, row, "위험요인", v(form_data, "hazard_desc"), height=36)
    row = _full_row(ws, row, "감시 구역", v(form_data, "watch_zone"), height=28)
    row = _blank(ws, row, 6)

    # ── s5~s7. 감시인 목록 ────────────────────────────────────────────────
    row = _section_header(ws, row,
        "⑤ 감시인/입회자 기본정보  ⑥ 감시 역할 및 담당구역  ⑦ 배치 시간 및 교대 계획")

    col_hdrs = ["순번", "성명", "소속", "역할", "담당구역",
                "배치시간", "연락처", "교대자", "확인\n서명", "비고"]
    for c, h in enumerate(col_hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 28
    row += 1

    raw_wm: List[Dict[str, Any]] = form_data.get("watchmen") or []
    watchmen = raw_wm if raw_wm else DEFAULT_WATCHMEN
    watchmen = watchmen[:MAX_WM_ROWS]

    for wm in watchmen:
        sval  = v(wm, "signed", "")
        sfill = _SIGNED_FILL.get(sval, FILL_NONE)

        write_cell(ws, row, 1,  1,  v(wm, "no"),         font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2,  2,  v(wm, "name"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 3,  3,  v(wm, "company"),    font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4,  4,  v(wm, "role"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5,  5,  v(wm, "zone"),       font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 6,  6,  v(wm, "start_time"), font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7,  7,  v(wm, "contact"),    font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 8,  8,  v(wm, "relief_by"),  font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 9,  9,  sval,                font=FONT_SMALL, fill=sfill, align=ALIGN_CENTER)
        write_cell(ws, row, 10, 10, v(wm, "remarks"),    font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 24
        row += 1

    empty = max(2, MAX_WM_ROWS - len(watchmen))
    next_no = len(watchmen) + 1
    for i in range(empty):
        write_cell(ws, row, 1, 1, str(next_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 24
        row += 1

    row = _blank(ws, row, 6)

    # ── s8. 연락체계 및 비상연락 ──────────────────────────────────────────
    row = _section_header(ws, row, "⑧ 연락체계 및 비상연락")
    row = _full_row(ws, row, "비상연락 체계", v(form_data, "emergency_contact"), height=36)
    row = _two_col(ws, row, "감시 시작",  v(form_data, "watch_start"),
                             "감시 종료",  v(form_data, "watch_end"))
    row = _full_row(ws, row, "교대 계획",  v(form_data, "relief_plan"), height=28)
    row = _blank(ws, row, 6)

    # ── s9. 작업중지 권한 및 기준 ─────────────────────────────────────────
    row = _section_header(ws, row, "⑨ 작업중지 권한 및 기준")
    default_stop = (
        "감시인은 다음 상황 발생 시 즉시 작업중지를 요청할 권한을 가진다:\n"
        "① 위험요인 발생 또는 악화  ② 이상 징후 감지  ③ 비상상황 발생  "
        "④ 작업자 이상 행동 감지  ⑤ 기상악화 등 외부 위험 발생"
    )
    row = _full_row(ws, row, "작업중지 기준",
                   v(form_data, "stop_criteria") or default_stop, height=48)
    row = _blank(ws, row, 6)

    # ── s10. 감시 장비/보호구 확인 ────────────────────────────────────────
    row = _section_header(ws, row, "⑩ 감시 장비 / 보호구 확인")
    default_ppe = "안전모, 안전화, 안전대 (고소 시), 가스감지기 (밀폐공간 시), 무전기/통신장비"
    row = _full_row(ws, row, "필요 보호구",
                   v(form_data, "ppe_required") or default_ppe, height=28)
    row = _blank(ws, row, 6)

    # ── 보완사항 ──────────────────────────────────────────────────────────
    if v(form_data, "supplement_items"):
        row = _section_header(ws, row, "보완사항")
        row = _full_row(ws, row, "보완사항", v(form_data, "supplement_items"), height=36)
        row = _blank(ws, row, 6)

    # ── s11. 배치 확인 및 서명 ────────────────────────────────────────────
    row = _section_header(ws, row, "⑪ 배치 확인 및 서명")
    write_cell(ws, row, 1,  2,  "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3,  5,  "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6,  6,  "직책",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7,  8,  "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 9,  10, "확인 일자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    signers = [
        ("작업책임자", "supervisor",  "supervisor_pos"),
        ("확인자",     "confirmer",   "confirmer_pos"),
    ]
    for role, name_key, pos_key in signers:
        write_cell(ws, row, 1,  2,  role,                          font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3,  5,  v(form_data, name_key),        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6,  6,  v(form_data, pos_key),         font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7,  8,  "",                            font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 9,  10, v(form_data, "confirm_date"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 28
        row += 1
    row = _blank(ws, row, 6)

    # ── 하단 안내 ─────────────────────────────────────────────────────────
    notice = (
        "[watchman_assignment_confirmation] 본 감시인 배치 확인서는 고위험 작업 감시인·입회자·"
        "화재감시자의 배치 여부, 역할, 연락체계, 작업중지 권한을 확인하는 부대서류입니다. "
        "document_catalog 독립 문서가 아님."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 24

    apply_a4_page_setup(ws, landscape=True)
    set_print_area_to_used_range(ws)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

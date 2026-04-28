"""
작업종료 확인서 — 부대서류 Excel 출력 모듈 (v1).

작업허가서/PTW에 따라 수행한 작업이 안전하게 종료되었는지 확인하고,
잔류위험·정리정돈·격리해제·장비회수·출입자 철수 여부를 기록하는 부대서류.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

supplemental_type: work_completion_confirmation
함수명:            build_work_completion_confirmation(form_data)

Required form_data keys:
    site_name       str  현장명
    permit_date     str  작업허가 일자
    work_location   str  작업 장소
    work_type       str  작업 종류

Optional form_data keys:
    permit_no           str   작업허가서 번호
    parent_doc_id       str   연결 문서 ID
    parent_doc_name     str   연결 문서명
    parent_form_type    str   연결 form_type
    project_name        str   공사명
    company_name        str   회사명
    work_start_time     str   작업 시작 시각
    work_end_time       str   작업 종료 시각
    completion_time     str   종료 보고 시각
    completion_reporter str   종료 보고자
    fire_watch_duration str   화재 감시 지속 시간 (화기작업)
    headcount_in        str   작업 투입 인원
    headcount_out       str   철수 확인 인원
    residual_risk       str   잔류위험 내용
    supplement_items    str   미완료·보완사항
    work_supervisor     str   작업책임자 성명
    work_supervisor_pos str   작업책임자 직책
    watchman            str   감시인 성명
    watchman_pos        str   감시인 직책
    site_manager        str   현장관리자 성명
    site_manager_pos    str   현장관리자 직책
    confirm_date        str   확인 일자
    remarks             str   비고

    check_items  list[dict]  체크리스트 항목 (repeat, 최대 15건)
        각 항목:
            no           int|str  순번
            check_name   str      확인 항목
            result       str      확인 결과 (○/×/해당없음)
            action       str      조치 내용
            checker      str      확인자
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
    apply_col_widths, v, write_cell,
)

SUPPLEMENTAL_TYPE = "work_completion_confirmation"
SHEET_NAME        = "작업종료확인서"
SHEET_HEADING     = "작업종료 확인서"
SHEET_SUBTITLE    = (
    "작업허가서(PTW) 작업 종료 후 잔류위험·정리정돈·격리해제·장비회수·출입자 철수 확인  "
    "[work_completion_confirmation]  부대서류"
)

TOTAL_COLS       = 9
MAX_CHECK_ROWS   = 15

_COL_WIDTHS: Dict[int, float] = {
    1:  5,   # 순번
    2:  24,  # 확인 항목
    3:  10,  # 확인 결과
    4:  20,  # 조치 내용
    5:  10,  # 확인자
    6:  10,  # 비고
    7:  8,   # (여백/서명용)
    8:  8,
    9:  10,
}

_RESULT_FILL = {
    "○":    FILL_HEADER,
    "완료":  FILL_HEADER,
    "×":    FILL_WARN,
    "미완료": FILL_WARN,
    "해당없음": FILL_NOTICE,
    "N/A":  FILL_NOTICE,
}

DEFAULT_CHECK_ITEMS: List[Dict[str, Any]] = [
    {"no": "1",  "check_name": "작업 완료 여부",           "result": "", "action": "", "checker": "", "remarks": ""},
    {"no": "2",  "check_name": "작업구역 정리정돈",         "result": "", "action": "", "checker": "", "remarks": ""},
    {"no": "3",  "check_name": "화기 잔불 확인",           "result": "", "action": "", "checker": "", "remarks": "화기작업 시"},
    {"no": "4",  "check_name": "전원 차단/복구 확인",       "result": "", "action": "", "checker": "", "remarks": ""},
    {"no": "5",  "check_name": "가스/압력 잔류 여부",       "result": "", "action": "", "checker": "", "remarks": ""},
    {"no": "6",  "check_name": "출입자 전원 철수",          "result": "", "action": "", "checker": "", "remarks": ""},
    {"no": "7",  "check_name": "장비·공구 회수",           "result": "", "action": "", "checker": "", "remarks": ""},
    {"no": "8",  "check_name": "폐기물/잔재물 정리",        "result": "", "action": "", "checker": "", "remarks": ""},
    {"no": "9",  "check_name": "안전시설 원상복구",         "result": "", "action": "", "checker": "", "remarks": ""},
    {"no": "10", "check_name": "잔류위험 없음",            "result": "", "action": "", "checker": "", "remarks": ""},
    {"no": "11", "check_name": "작업 후 사진 첨부",         "result": "", "action": "", "checker": "", "remarks": "선택"},
    {"no": "12", "check_name": "추가 보완사항 없음",        "result": "", "action": "", "checker": "", "remarks": ""},
]


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _two_col(ws, row: int,
             label1: str, val1: Any,
             label2: str, val2: Any,
             height: float = 20) -> int:
    write_cell(ws, row, 1, 1, label1, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, val1,   font=FONT_DEFAULT, fill=FILL_NONE,  align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, label2, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 9, val2,   font=FONT_DEFAULT, fill=FILL_NONE,  align=ALIGN_LEFT)
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

def build_work_completion_confirmation(form_data: Dict[str, Any]) -> bytes:
    """작업종료 확인서 부대서류 Excel bytes 반환."""
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

    # ── s1. 작업종료 확인서 기본정보 ───────────────────────────────────────
    row = _section_header(ws, row, "① 작업종료 확인서 기본정보")
    row = _two_col(ws, row, "현장명",    v(form_data, "site_name"),
                             "작업허가 일자", v(form_data, "permit_date"))
    row = _two_col(ws, row, "공사명",    v(form_data, "project_name"),
                             "회사명",    v(form_data, "company_name"))
    row = _blank(ws, row, 6)

    # ── s2. 연결 문서 정보 ─────────────────────────────────────────────────
    row = _section_header(ws, row, "② 연결 문서 정보  (부대서류)")
    row = _two_col(ws, row, "연결 문서 ID",   v(form_data, "parent_doc_id"),
                             "연결 문서명",    v(form_data, "parent_doc_name"))
    row = _two_col(ws, row, "연결 form_type", v(form_data, "parent_form_type"),
                             "비고",           v(form_data, "remarks"))
    row = _blank(ws, row, 6)

    # ── s3. 작업 허가 정보 ─────────────────────────────────────────────────
    row = _section_header(ws, row, "③ 작업 허가 정보")
    row = _two_col(ws, row, "작업허가서 번호", v(form_data, "permit_no"),
                             "작업 종류",      v(form_data, "work_type"))
    row = _two_col(ws, row, "작업 장소",       v(form_data, "work_location"),
                             "작업허가 일자",  v(form_data, "permit_date"))
    row = _blank(ws, row, 6)

    # ── s4. 작업 종료 시각 및 종료 보고 ───────────────────────────────────
    row = _section_header(ws, row, "④ 작업 종료 시각 및 종료 보고")
    row = _two_col(ws, row, "작업 시작 시각",  v(form_data, "work_start_time"),
                             "작업 종료 시각",  v(form_data, "work_end_time"))
    row = _two_col(ws, row, "종료 보고 시각",  v(form_data, "completion_time"),
                             "종료 보고자",     v(form_data, "completion_reporter"))
    row = _two_col(ws, row, "화재 감시 시간",  v(form_data, "fire_watch_duration"),
                             "(화기작업 시 작업 종료 후 감시 지속 시간 기재)", "")
    row = _blank(ws, row, 6)

    # ── s5~s9: 체크리스트 (섹션 헤더 통합) ────────────────────────────────
    row = _section_header(ws, row,
        "⑤ 작업구역 정리정돈  ⑥ 장비·공구·자재 회수  "
        "⑦ 에너지/격리 해제  ⑧ 잔류위험  ⑨ 출입자 철수 — 종합 확인 체크리스트")

    # 테이블 헤더
    col_hdrs = ["순번", "확인 항목", "확인 결과", "조치 내용", "확인자", "비고", "", "", ""]
    spans    = [1, 1, 1, 2, 1, 1, 0, 0, 0]
    c = 1
    for h, sp in zip(col_hdrs, spans):
        if sp == 0:
            continue
        write_cell(ws, row, c, c + sp - 1, h,
                   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
        c += sp
    ws.row_dimensions[row].height = 22
    row += 1

    raw_items: List[Dict[str, Any]] = form_data.get("check_items") or []
    items = raw_items if raw_items else DEFAULT_CHECK_ITEMS
    items = items[:MAX_CHECK_ROWS]

    for it in items:
        rval  = v(it, "result", "")
        rfill = _RESULT_FILL.get(rval, FILL_NONE)

        write_cell(ws, row, 1, 1, v(it, "no"),         font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, v(it, "check_name"), font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, rval,                font=FONT_SMALL, fill=rfill, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 5, v(it, "action"),     font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 6, v(it, "checker"),    font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 9, v(it, "remarks"),    font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 22
        row += 1

    empty = max(3, MAX_CHECK_ROWS - len(items))
    next_no = len(items) + 1
    for i in range(empty):
        write_cell(ws, row, 1, 1, str(next_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 22
        row += 1

    row = _blank(ws, row, 6)

    # ── s10. 작업 후 사진/첨부 확인 ──────────────────────────────────────
    row = _section_header(ws, row, "⑩ 작업 후 사진/첨부 확인")
    notice10 = (
        "작업 전·후 비교 사진, 정리정돈 사진, 격리 해제 사진 등 필요 시 사진대지(photo_attachment_sheet) 부대서류 첨부."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice10,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 24
    row += 1
    row = _blank(ws, row, 6)

    # ── s11. 출입자 철수 및 인원 확인 ─────────────────────────────────────
    row = _section_header(ws, row, "⑪ 출입자 철수 및 인원 확인")
    row = _two_col(ws, row, "작업 투입 인원",  v(form_data, "headcount_in"),
                             "철수 확인 인원", v(form_data, "headcount_out"))
    row = _blank(ws, row, 6)

    # ── s12. 미완료·보완사항 ──────────────────────────────────────────────
    row = _section_header(ws, row, "⑫ 미완료 · 보완사항")
    row = _full_row(ws, row, "잔류위험 내용",
                   v(form_data, "residual_risk"), height=36)
    row = _full_row(ws, row, "미완료·보완사항",
                   v(form_data, "supplement_items"), height=36)
    row = _blank(ws, row, 6)

    # ── s13. 작업책임자/감시인/현장관리자 확인 서명 ────────────────────────
    row = _section_header(ws, row, "⑬ 작업책임자 / 감시인 / 현장관리자 확인 서명")
    write_cell(ws, row, 1, 2, "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 4, "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 5, "직책",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 7, "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 9, "확인 일자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    signers = [
        ("작업책임자", "work_supervisor",  "work_supervisor_pos"),
        ("감시인",     "watchman",         "watchman_pos"),
        ("현장관리자", "site_manager",     "site_manager_pos"),
    ]
    for role, name_key, pos_key in signers:
        write_cell(ws, row, 1, 2, role,                        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 4, v(form_data, name_key),      font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(form_data, pos_key),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 7, "",                          font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 9, v(form_data, "confirm_date"),font=FONT_DEFAULT, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 28
        row += 1
    row = _blank(ws, row, 6)

    # ── 하단 안내 ─────────────────────────────────────────────────────────
    notice = (
        "[work_completion_confirmation] 본 작업종료 확인서는 작업허가서(PTW) 작업 종료 후 "
        "잔류위험·정리정돈·격리해제·장비회수·출입자 철수 여부를 확인하는 부대서류입니다. "
        "document_catalog 독립 문서가 아님."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 24

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

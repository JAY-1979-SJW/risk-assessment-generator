"""
미참석자 ��가교육 확인서 — 부대서류 Excel 출력 모듈 (v1).

정기교육·특별교육·TBM·위험성평가 결과 공지 등에서 미참석자 또는 추가교육 대상자를
별도로 교육하고 확인하는 부대서류.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

supplemental_type: education_makeup_confirmation
함수명:            build_education_makeup_confirmation(form_data)

Required form_data keys:
    site_name           str  현장명
    original_edu_date   str  원 교육 일자
    edu_subject         str  교육 과목/주제
    makeup_date         str  추가교육 실시 일자

Optional form_data keys:
    parent_doc_id       str   연결 문서 ID
    parent_doc_name     str   연결 문서명
    parent_form_type    str   연결 form_type
    project_name        str   공사명
    company_name        str   회사명
    makeup_location     str   추가교육 장소
    makeup_instructor   str   추가교육 강사
    makeup_instructor_pos str 추가교육 강사 직책
    makeup_duration     str   교육 시간
    edu_method          str   교육 방법 (집합/개별/동영상 등)
    edu_contents        str   교육 내용 요약
    total_absent        str   총 미참석자 수
    makeup_count        str   추가교육 완료 인원
    remaining_count     str   미이수 잔여 인원
    supplement_items    str   미이수·추가 보완사항
    confirmer           str   확인자 성명
    confirmer_position  str   확인자 직책
    confirm_date        str   확인 일자
    remarks             str   비고

    absent_list  list[dict]  추가교육 대상자 목록 (repeat, 최대 20건)
        각 항목:
            no              int|str  순번
            name            str      성명
            company         str      소속
            job_type        str      직종
            original_edu    str      원 교육명
            absent_reason   str      미참석 사유
            makeup_datetime str      추가교육 일시
            comprehension   str      이해도 확인 (양호/보통/미흡)
            signed          str      서명 (○/-)
            remarks         str      비고
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

SUPPLEMENTAL_TYPE   = "education_makeup_confirmation"
SHEET_NAME          = "추가교육확인서"
SHEET_HEADING       = "미참석자 추가교육 확인서"
SHEET_SUBTITLE      = (
    "안전보건교육 미참석자 / 추가교육 대상자 보완교육 실시 확인  "
    "[education_makeup_confirmation]  부대서류"
)

TOTAL_COLS       = 10
MAX_ABSENT_ROWS  = 20

_COL_WIDTHS: Dict[int, float] = {
    1:  5,   # 순번
    2:  10,  # 성명
    3:  10,  # 소속
    4:  9,   # 직종
    5:  14,  # 원 교육명
    6:  12,  # 미참석 사유
    7:  13,  # 추가교육 일시
    8:  9,   # 이해도 확인
    9:  8,   # 서명
    10: 11,  # 비고
}

_COMP_FILL = {
    "양호": FILL_HEADER,
    "보통": FILL_NONE,
    "미흡": FILL_WARN,
}

_SIGNED_FILL = {
    "○": FILL_HEADER,
    "-": FILL_NOTICE,
}

DEFAULT_ABSENT_LIST: List[Dict[str, Any]] = [
    {"no":"1", "name":"", "company":"", "job_type":"", "original_edu":"정기 안전보건교육", "absent_reason":"", "makeup_datetime":"", "comprehension":"", "signed":"", "remarks":""},
    {"no":"2", "name":"", "company":"", "job_type":"", "original_edu":"정기 안전보건교육", "absent_reason":"", "makeup_datetime":"", "comprehension":"", "signed":"", "remarks":""},
    {"no":"3", "name":"", "company":"", "job_type":"", "original_edu":"정기 안전보건교육", "absent_reason":"", "makeup_datetime":"", "comprehension":"", "signed":"", "remarks":""},
]


# ---------------------------------------------------------------------------
# 내부 헬���
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

def build_education_makeup_confirmation(form_data: Dict[str, Any]) -> bytes:
    """미참석자 추가교육 확인서 부대서류 Excel bytes 반환."""
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
    row = _section_header(ws, row, "① 추가교육 확인서 기본정보")
    row = _two_col(ws, row, "현장명",    v(form_data, "site_name"),
                             "추가교육 일자", v(form_data, "makeup_date"))
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

    # ── s3. 원 교육 정보 ───────────────────────────────────────────────────
    row = _section_header(ws, row, "③ 원 교육 정보")
    row = _two_col(ws, row, "원 교육 일자",  v(form_data, "original_edu_date"),
                             "교육 과목/주제", v(form_data, "edu_subject"))
    row = _two_col(ws, row, "총 미참석자",   v(form_data, "total_absent"),
                             "추가교육 완료", v(form_data, "makeup_count"))
    row = _blank(ws, row, 6)

    # ── s4~s6: 추가교육 대상자 목록 ──────────────────────────────────────
    row = _section_header(ws, row,
        "④ 추가교육 대상자 정보  ⑤ 추가교육 실시 내용  ⑥ 이해도 확인 및 서명")

    col_hdrs = ["순번", "성명", "소속", "직종", "원 교육명",
                "미참석 사유", "추가교육 일시", "이해도\n확인", "서명", "비고"]
    for c, h in enumerate(col_hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 28
    row += 1

    raw_list: List[Dict[str, Any]] = form_data.get("absent_list") or []
    absent = raw_list if raw_list else DEFAULT_ABSENT_LIST
    absent = absent[:MAX_ABSENT_ROWS]

    for person in absent:
        cval  = v(person, "comprehension", "")
        cfill = _COMP_FILL.get(cval, FILL_NONE)
        sval  = v(person, "signed", "")
        sfill = _SIGNED_FILL.get(sval, FILL_NONE)

        write_cell(ws, row, 1,  1,  v(person, "no"),             font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2,  2,  v(person, "name"),           font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 3,  3,  v(person, "company"),        font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4,  4,  v(person, "job_type"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5,  5,  v(person, "original_edu"),   font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 6,  6,  v(person, "absent_reason"),  font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 7,  7,  v(person, "makeup_datetime"),font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 8,  8,  cval,                        font=FONT_SMALL, fill=cfill, align=ALIGN_CENTER)
        write_cell(ws, row, 9,  9,  sval,                        font=FONT_SMALL, fill=sfill, align=ALIGN_CENTER)
        write_cell(ws, row, 10, 10, v(person, "remarks"),        font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 22
        row += 1

    empty = max(3, MAX_ABSENT_ROWS - len(absent))
    next_no = len(absent) + 1
    for i in range(empty):
        write_cell(ws, row, 1, 1, str(next_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 22
        row += 1

    row = _blank(ws, row, 6)

    # ── s7. 추가교육 실시 내용 요약 ───────────────────────────────────────
    row = _section_header(ws, row, "⑦ 추가교육 실시 내용 요약")
    row = _two_col(ws, row, "교육 장소",   v(form_data, "makeup_location"),
                             "교육 시간",   v(form_data, "makeup_duration"))
    row = _two_col(ws, row, "교육 방법",   v(form_data, "edu_method"),
                             "강사/담당",   v(form_data, "makeup_instructor"))
    row = _full_row(ws, row, "교육 내용",  v(form_data, "edu_contents"), height=40)
    row = _blank(ws, row, 6)

    # ── s8. 미이수·추가 보완사항 ──────────────────────────────────────────
    row = _section_header(ws, row, "⑧ 미이수 인원 및 추가 보완사항")
    row = _two_col(ws, row, "미이수 잔여 인원", v(form_data, "remaining_count"),
                             "",               "")
    row = _full_row(ws, row, "보완사항", v(form_data, "supplement_items"), height=36)
    row = _blank(ws, row, 6)

    # ── s9. 이해도 확인 기준 ──────────────────────────────────────────────
    row = _section_header(ws, row, "⑨ 이해도 확인 기준")
    write_cell(ws, row, 1,  3,  "양호  (청색)",
               font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 4,  6,  "보통  (표시 없음)",
               font=FONT_BOLD, fill=FILL_NONE,   align=ALIGN_CENTER)
    write_cell(ws, row, 7,  10, "미흡  (황색) → 재교육 필요",
               font=FONT_BOLD, fill=FILL_WARN,   align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 22
    row += 1
    row = _blank(ws, row, 6)

    # ── s10. 교육자/확인자 서명 ───────────────────────────────────────────
    row = _section_header(ws, row, "⑩ 교육자 / 확인자 서명")
    write_cell(ws, row, 1,  2,  "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3,  5,  "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6,  6,  "직책",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7,  8,  "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 9,  10, "확인 일자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    signers = [
        ("교육자", "makeup_instructor",  "makeup_instructor_pos"),
        ("확인자", "confirmer",          "confirmer_position"),
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
        "[education_makeup_confirmation] 본 미참석자 추가교육 확인서는 안전보건교육 미참석자·추가교육 "
        "대상자에 대한 보완교육 실시 여부를 확인하는 부대서류입니다. "
        "document_catalog 독립 문서가 아님."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 24

    apply_a4_page_setup(ws, landscape=True)
    set_print_area_to_used_range(ws)
    ws.print_title_rows = "1:17"
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

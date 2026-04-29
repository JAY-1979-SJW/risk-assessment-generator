"""
장비 운전원 자격 확인표 — 부대서류 Excel 출력 모듈 (v1).

건설기계·하역운반기계·크레인·고소작업대·지게차 등 장비 운전원의
면허/자격/교육/경력/보험 연계 확인을 기록하는 부대서류.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

supplemental_type: equipment_operator_qualification_check
함수명:            build_equipment_operator_qualification_check(form_data)

Required form_data keys:
    site_name       str  현장명
    check_date      str  확인 일자
    equipment_type  str  장비 종류

Optional form_data keys:
    parent_doc_id       str   연결 문서 ID
    parent_doc_name     str   연결 문서명
    parent_form_type    str   연결 form_type
    project_name        str   공사명
    company_name        str   회사명
    equipment_model     str   장비 모델/규격
    equipment_no        str   장비 번호/차량번호
    equipment_owner     str   장비 소유자/임대사
    insurance_no        str   보험증 번호
    insurance_expiry    str   보험 유효기간
    inspection_no       str   정기검사증 번호
    inspection_expiry   str   검사증 유효기간
    checker             str   확인자 성명
    checker_position    str   확인자 직책
    site_manager        str   현장관리자 성명
    site_manager_pos    str   현장관리자 직책
    safety_manager      str   안전관리자 성명
    safety_manager_pos  str   안전관리자 직책
    confirm_date        str   서명 확인 일자
    supplement_items    str   부적합·보완사항
    remarks             str   비고

    operators  list[dict]  운전원 목록 (repeat, 최대 12건)
        각 항목:
            no           int|str  순번
            name         str      성명
            company      str      소속
            equip_name   str      장비명
            license_name str      면허/자격명
            license_no   str      자격번호
            expiry       str      유효기간
            trained      str      교육 이수 (○/×)
            experience   str      경력
            result       str      확인 결과 (적합/부적합)
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

SUPPLEMENTAL_TYPE = "equipment_operator_qualification_check"
SHEET_NAME        = "운전원자격확인표"
SHEET_HEADING     = "장비 운전원 자격 확인표"
SHEET_SUBTITLE    = (
    "건설기계·크레인·고소작업대·지게차 등 운전원 면허·자격·교육·경력 확인  "
    "[equipment_operator_qualification_check]  부대서류"
)

TOTAL_COLS    = 11
MAX_OP_ROWS   = 12

# A4 가로 권장
_COL_WIDTHS: Dict[int, float] = {
    1:  5,   # 순번
    2:  10,  # 성명
    3:  10,  # 소속
    4:  12,  # 장비명
    5:  14,  # 면허/자격명
    6:  14,  # 자격번호
    7:  11,  # 유효기간
    8:  8,   # 교육 이수
    9:  8,   # 경력
    10: 9,   # 확인 결과
    11: 11,  # 비고
}

_RESULT_FILL = {
    "적합":   FILL_HEADER,
    "부적합": FILL_WARN,
}

_TRAINED_FILL = {
    "○":   FILL_HEADER,
    "×":   FILL_WARN,
}

DEFAULT_OPERATORS: List[Dict[str, Any]] = [
    {"no":"1", "name":"", "company":"", "equip_name":"굴착기", "license_name":"건설기계조종사면허(굴착기)", "license_no":"", "expiry":"", "trained":"", "experience":"", "result":"", "remarks":""},
    {"no":"2", "name":"", "company":"", "equip_name":"타워크레인", "license_name":"건설기계조종사면허(타워크레인)", "license_no":"", "expiry":"", "trained":"", "experience":"", "result":"", "remarks":""},
    {"no":"3", "name":"", "company":"", "equip_name":"고소작업대", "license_name":"고소작업대 특별안전교육", "license_no":"", "expiry":"", "trained":"", "experience":"", "result":"", "remarks":""},
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
    write_cell(ws, row, 7, 11, val2,  font=FONT_DEFAULT, fill=FILL_NONE,  align=ALIGN_LEFT)
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

def build_equipment_operator_qualification_check(form_data: Dict[str, Any]) -> bytes:
    """장비 운전원 자격 확인표 부대서류 Excel bytes 반환."""
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
    row = _section_header(ws, row, "① 운전원 자격 확인표 기본정보")
    row = _two_col(ws, row, "현장명",    v(form_data, "site_name"),
                             "확인 일자", v(form_data, "check_date"))
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

    # ── s3. 장비 정보 ──────────────────────────────────────────────────────
    row = _section_header(ws, row, "③ 장비 정보")
    row = _two_col(ws, row, "장비 종류",   v(form_data, "equipment_type"),
                             "모델/규격",   v(form_data, "equipment_model"))
    row = _two_col(ws, row, "장비 번호",   v(form_data, "equipment_no"),
                             "소유자/임대사", v(form_data, "equipment_owner"))
    row = _blank(ws, row, 6)

    # ── s4. 운전원 목록 (s4~s7 통합) ──────────────────────────────────────
    row = _section_header(ws, row,
        "④ 운전원 기본정보  ⑤ 면허/자격 정보  ⑥ 교육 이수  ⑦ 경력 및 확인 결과")

    col_hdrs = ["순번", "성명", "소속", "장비명",
                "면허/자격명", "자격번호", "유효기간",
                "교육\n이수", "경력", "확인\n결과", "비고"]
    for c, h in enumerate(col_hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 28
    row += 1

    raw_ops: List[Dict[str, Any]] = form_data.get("operators") or []
    ops = raw_ops if raw_ops else DEFAULT_OPERATORS
    ops = ops[:MAX_OP_ROWS]

    for op in ops:
        rval  = v(op, "result",  "")
        rfill = _RESULT_FILL.get(rval, FILL_NONE)
        tval  = v(op, "trained", "")
        tfill = _TRAINED_FILL.get(tval, FILL_NONE)

        write_cell(ws, row, 1,  1,  v(op, "no"),           font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2,  2,  v(op, "name"),         font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 3,  3,  v(op, "company"),      font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4,  4,  v(op, "equip_name"),   font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 5,  5,  v(op, "license_name"), font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 6,  6,  v(op, "license_no"),   font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7,  7,  v(op, "expiry"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 8,  8,  tval,                  font=FONT_SMALL, fill=tfill, align=ALIGN_CENTER)
        write_cell(ws, row, 9,  9,  v(op, "experience"),   font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 10, 10, rval,                  font=FONT_SMALL, fill=rfill, align=ALIGN_CENTER)
        write_cell(ws, row, 11, 11, v(op, "remarks"),      font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 22
        row += 1

    empty = max(3, MAX_OP_ROWS - len(ops))
    next_no = len(ops) + 1
    for i in range(empty):
        write_cell(ws, row, 1, 1, str(next_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 22
        row += 1

    row = _blank(ws, row, 6)

    # ── s8. 보험/검사증/반입서류 연계 확인 ────────────────────────────────
    row = _section_header(ws, row, "⑧ 보험 / 검사증 / 장비 반입서류 연계 확인")
    row = _two_col(ws, row, "보험증 번호",    v(form_data, "insurance_no"),
                             "보험 유효기간", v(form_data, "insurance_expiry"))
    row = _two_col(ws, row, "정기검사증 번호", v(form_data, "inspection_no"),
                             "검사증 유효기간", v(form_data, "inspection_expiry"))
    row = _blank(ws, row, 6)

    # ── s9. 자격증 사본 첨부 확인 ─────────────────────────────────────────
    row = _section_header(ws, row, "⑨ 자격증 사본 첨부 확인")
    notice9 = (
        "운전원별 면허증·자격증 사본, 특별교육 이수증, 경력증명서 등 필요 시 "
        "첨부서류 목록표(document_attachment_list) 부대서류에 목록화하여 첨부."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice9,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 28
    row += 1
    row = _blank(ws, row, 6)

    # ── s10. 부적합/보완사항 ──────────────────────────────────────────────
    row = _section_header(ws, row, "⑩ 부적합 · 보완사항")
    row = _full_row(ws, row, "부적합·보완사항", v(form_data, "supplement_items"), height=40)
    row = _blank(ws, row, 6)

    # ── s11. 현장관리자/안전관리자 확인 서명 ──────────────────────────────
    row = _section_header(ws, row, "⑪ 현장관리자 / 안전관리자 확인 서명")
    write_cell(ws, row, 1,  2,  "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3,  5,  "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6,  6,  "직책",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7,  9,  "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 10, 11, "확인 일자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    signers = [
        ("현장관리자", "site_manager",  "site_manager_pos"),
        ("안전관리자", "safety_manager", "safety_manager_pos"),
    ]
    for role, name_key, pos_key in signers:
        write_cell(ws, row, 1,  2,  role,                          font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3,  5,  v(form_data, name_key),        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6,  6,  v(form_data, pos_key),         font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7,  9,  "",                            font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 10, 11, v(form_data, "confirm_date"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 28
        row += 1
    row = _blank(ws, row, 6)

    # ── 하단 안내 ─────────────────────────────────────────────────────────
    notice = (
        "[equipment_operator_qualification_check] 본 장비 운전원 자격 확인표는 "
        "건설기계·크레인·고소작업대·지게차 등 운전원의 면허·자격·교육·경력 확인을 기록하는 부대서류입니다. "
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

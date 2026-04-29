"""
보호구 수령 확인서 — 부대서류 Excel 출력 모듈 (v1).

안전모·안전화·안전대·보안경·마스크·귀마개·장갑·방염복 등 개인보호구를
근로자가 수령하고 착용·관리 방법을 설명받았음을 확인하는 부대서류.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

supplemental_type: ppe_receipt_confirmation
함수명:            build_ppe_receipt_confirmation(form_data)

Required form_data keys:
    site_name   str  현장명
    issue_date  str  지급 일자

Optional form_data keys:
    parent_doc_id           str   연결 문서 ID
    parent_doc_name         str   연결 문서명
    parent_form_type        str   연결 form_type
    project_name            str   공사명
    company_name            str   회사명
    work_type               str   작업/공종명
    issuer                  str   지급자 성명
    issuer_position         str   지급자 직책
    approver                str   확인자/승인자 성명
    approver_position       str   확인자/승인자 직책
    confirm_date            str   서명 확인 일자
    explanation_done        str   착용 설명 완료 여부
    replacement_criteria    str   교체·반납 기준 안내 내용
    supplement_items        str   미지급·부적합 보호구 조치사항
    remarks                 str   비고
    -- 외국인 근로자 확장 (2차 다국어 builder용 예비 필드) --
    worker_language         str   근로자 언어
    interpreter_name        str   통역자 성명
    explanation_language    str   설명 언어
    understood_confirmed    str   이해 확인 (○/-)

    ppe_items  list[dict]  근로자·보호구 수령 목록 (repeat, 최대 20건)
        각 항목:
            no           int|str  순번
            name         str      성명
            company      str      소속
            job_type     str      직종
            ppe_name     str      지급 보호구명
            qty          str      수량
            issue_date   str      지급일
            explained    str      착용 설명 (○/-)
            signed       str      수령 서명 (○/-)
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

SUPPLEMENTAL_TYPE = "ppe_receipt_confirmation"
SHEET_NAME        = "보호구수령확인서"
SHEET_HEADING     = "보호구 수령 확인서"
SHEET_SUBTITLE    = (
    "개인보호구(안전모·안전화·안전대·마스크 등) 지급 및 착용방법 설명 수령 확인  "
    "[ppe_receipt_confirmation]  부대서류"
)

TOTAL_COLS    = 10
MAX_PPE_ROWS  = 20

# A4 가로 권장
_COL_WIDTHS: Dict[int, float] = {
    1:  5,   # 순번
    2:  10,  # 성명
    3:  10,  # 소속
    4:  9,   # 직종
    5:  18,  # 지급 보호구명
    6:  6,   # 수량
    7:  10,  # 지급일
    8:  9,   # 착용 설명
    9:  9,   # 수령 서명
    10: 12,  # 비고
}

_SIGNED_FILL = {
    "○": FILL_HEADER,
    "-": FILL_NOTICE,
}

_EXPLAINED_FILL = {
    "○": FILL_HEADER,
    "-": FILL_NOTICE,
}

# 기본 보호구 예시 (데이터 없을 때 안내)
DEFAULT_PPE_ITEMS: List[Dict[str, Any]] = [
    {"no":"1",  "name":"", "company":"", "job_type":"", "ppe_name":"안전모",              "qty":"1", "issue_date":"", "explained":"", "signed":"", "remarks":""},
    {"no":"2",  "name":"", "company":"", "job_type":"", "ppe_name":"안전화",              "qty":"1", "issue_date":"", "explained":"", "signed":"", "remarks":""},
    {"no":"3",  "name":"", "company":"", "job_type":"", "ppe_name":"안전대",              "qty":"1", "issue_date":"", "explained":"", "signed":"", "remarks":"고소작업 시"},
    {"no":"4",  "name":"", "company":"", "job_type":"", "ppe_name":"보안경",              "qty":"1", "issue_date":"", "explained":"", "signed":"", "remarks":""},
    {"no":"5",  "name":"", "company":"", "job_type":"", "ppe_name":"방진마스크",          "qty":"2", "issue_date":"", "explained":"", "signed":"", "remarks":""},
    {"no":"6",  "name":"", "company":"", "job_type":"", "ppe_name":"귀마개",              "qty":"1쌍", "issue_date":"", "explained":"", "signed":"", "remarks":"소음 작업 시"},
    {"no":"7",  "name":"", "company":"", "job_type":"", "ppe_name":"보호장갑",            "qty":"1쌍", "issue_date":"", "explained":"", "signed":"", "remarks":""},
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

def build_ppe_receipt_confirmation(form_data: Dict[str, Any]) -> bytes:
    """보호구 수령 확인서 부대서류 Excel bytes 반환."""
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
    row = _section_header(ws, row, "① 보호구 수령 확인서 기본정보")
    row = _two_col(ws, row, "현장명",    v(form_data, "site_name"),
                             "지급 일자", v(form_data, "issue_date"))
    row = _two_col(ws, row, "공사명",    v(form_data, "project_name"),
                             "회사명",    v(form_data, "company_name"))
    row = _two_col(ws, row, "작업/공종", v(form_data, "work_type"),
                             "지급자",    v(form_data, "issuer"))
    row = _blank(ws, row, 6)

    # ── s2. 연결 문서 정보 ─────────────────────────────────────────────────
    row = _section_header(ws, row, "② 연결 문서 정보  (부대서류)")
    row = _two_col(ws, row, "연결 문서 ID",   v(form_data, "parent_doc_id"),
                             "연결 문서명",    v(form_data, "parent_doc_name"))
    row = _two_col(ws, row, "연결 form_type", v(form_data, "parent_form_type"),
                             "비고",           v(form_data, "remarks"))
    row = _blank(ws, row, 6)

    # ── s3. 지급/수령 대상 작업 정보 ──────────────────────────────────────
    row = _section_header(ws, row, "③ 지급 / 수령 대상 작업 정보")
    row = _two_col(ws, row, "착용 설명 완료", v(form_data, "explanation_done"),
                             "외국인 근로자 언어", v(form_data, "worker_language"))
    row = _two_col(ws, row, "통역자",         v(form_data, "interpreter_name"),
                             "설명 언어",      v(form_data, "explanation_language"))
    row = _blank(ws, row, 6)

    # ── s4~s5: 보호구 수령 목록 ───────────────────────────────────────────
    row = _section_header(ws, row,
        "④ 근로자 기본정보  ⑤ 지급 보호구 목록  /  ⑥ 착용 및 관리방법 설명 확인  ⑨ 근로자 수령 서명")

    col_hdrs = ["순번", "성명", "소속", "직종", "지급 보호구명",
                "수량", "지급일", "착용\n설명", "수령\n서명", "비고"]
    for c, h in enumerate(col_hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 28
    row += 1

    raw_items: List[Dict[str, Any]] = form_data.get("ppe_items") or []
    items = raw_items if raw_items else DEFAULT_PPE_ITEMS
    items = items[:MAX_PPE_ROWS]

    for it in items:
        eval_ = v(it, "explained", "")
        efill = _EXPLAINED_FILL.get(eval_, FILL_NONE)
        sval  = v(it, "signed",    "")
        sfill = _SIGNED_FILL.get(sval, FILL_NONE)

        write_cell(ws, row, 1,  1,  v(it, "no"),        font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2,  2,  v(it, "name"),      font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 3,  3,  v(it, "company"),   font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4,  4,  v(it, "job_type"),  font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5,  5,  v(it, "ppe_name"),  font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 6,  6,  v(it, "qty"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7,  7,  v(it, "issue_date"),font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 8,  8,  eval_,              font=FONT_SMALL, fill=efill, align=ALIGN_CENTER)
        write_cell(ws, row, 9,  9,  sval,               font=FONT_SMALL, fill=sfill, align=ALIGN_CENTER)
        write_cell(ws, row, 10, 10, v(it, "remarks"),   font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 22
        row += 1

    empty = max(3, MAX_PPE_ROWS - len(items))
    next_no = len(items) + 1
    for i in range(empty):
        write_cell(ws, row, 1, 1, str(next_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 22
        row += 1

    row = _blank(ws, row, 6)

    # ── s7. 교체/반납 기준 안내 ───────────────────────────────────────────
    row = _section_header(ws, row, "⑦ 교체 / 반납 기준 안내")
    default_replacement = (
        "① 안전모·안전화·안전대 등은 충격·파손·변형 발생 시 즉시 교체 요청.  "
        "② 방진·방독마스크 필터는 사용 기준 또는 규정 교체 주기에 따라 교체.  "
        "③ 퇴직·전출 시 지급 보호구 반납 (소모품 제외).  "
        "④ 보호구 훼손·분실 시 안전담당자에게 즉시 신고."
    )
    row = _full_row(ws, row, "교체·반납 기준",
                   v(form_data, "replacement_criteria") or default_replacement,
                   height=44)
    row = _blank(ws, row, 6)

    # ── s8. 미지급/부적합 보호구 조치사항 ─────────────────────────────────
    row = _section_header(ws, row, "⑧ 미지급 / 부적합 보호구 조치사항")
    row = _full_row(ws, row, "조치사항", v(form_data, "supplement_items"), height=36)
    row = _blank(ws, row, 6)

    # ── s10. 지급자/확인자 서명 ───────────────────────────────────────────
    row = _section_header(ws, row, "⑩ 지급자 / 확인자 서명")
    write_cell(ws, row, 1,  2,  "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3,  5,  "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6,  6,  "직책",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7,  8,  "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 9,  10, "확인 일자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    signers = [
        ("지급자", "issuer",   "issuer_position"),
        ("확인자", "approver", "approver_position"),
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
        "[ppe_receipt_confirmation] 본 보호구 수령 확인서는 개인보호구 지급 및 착용·관리방법 설명 수령을 "
        "확인하는 부대서류입니다. document_catalog 독립 문서가 아님.  "
        "외국인 근로자 다국어 확인서는 2차 부대서류 패키지에서 별도 제공."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 24

    apply_a4_page_setup(ws, landscape=True)
    set_print_area_to_used_range(ws)
    ws.print_title_rows = "1:18"
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

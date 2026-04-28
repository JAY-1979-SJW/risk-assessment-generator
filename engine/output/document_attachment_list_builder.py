"""
첨부서류 목록표 — 부대서류 공통 Excel 출력 모듈 (v1).

핵심 안전서류(90종) 제출 패키지에 첨부되는 자료, 증빙서류, 사진대지,
검사증, 교육자료, 자격증, 시험성적서, 도면, 확인서 등을 목록화하는
공통 첨부서류 목록표 부대서류.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

supplemental_type: document_attachment_list
함수명:            build_document_attachment_list(form_data)

Required form_data keys:
    site_name      str  현장명
    doc_date       str  작성 일자
    parent_doc_id  str  연결 핵심서류 ID (예: PPE-002, PTW-001)

Optional form_data keys:
    parent_doc_name    str   연결 핵심서류명
    parent_form_type   str   연결 핵심서류 form_type
    project_name       str   공사명
    company_name       str   회사명
    package_title      str   제출 패키지 제목
    package_date       str   제출 일자
    submitted_to       str   제출처
    submitted_by       str   제출자
    total_count        str   총 첨부 건수
    missing_count      str   누락/보완 필요 건수
    missing_remarks    str   누락/보완 필요사항 요약
    supplement_due     str   보완 제출 기한
    prepared_by        str   작성자
    checked_by         str   검토자
    approved_by        str   확인자
    remarks            str   비고

    attachment_items  list[dict]  첨부서류 목록 (repeat, 최대 20건)
        각 항목:
            no             int|str  순번
            doc_name       str      첨부서류명
            category       str      구분 (사진/자격증/검사증/서식/도면/기타)
            required       str      필수 여부 (필수/선택)
            original_copy  str      원본/사본 (원본/사본/전자)
            file_name      str      파일명
            submitted      str      제출 여부 (○/×/보완중)
            check_result   str      확인 결과 (적합/부적합/확인중)
            remarks        str      비고
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

SUPPLEMENTAL_TYPE = "document_attachment_list"
SHEET_NAME        = "첨부서류목록표"
SHEET_HEADING     = "첨부서류 목록표"
SHEET_SUBTITLE    = (
    "안전보건 핵심서류 제출 패키지에 포함되는 첨부서류를 목록화하는 부대서류  "
    "[document_attachment_list]"
)

TOTAL_COLS     = 9
MAX_ATTACH_ROWS = 20

_COL_WIDTHS: Dict[int, float] = {
    1: 5,   # 순번
    2: 22,  # 첨부서류명
    3: 10,  # 구분
    4: 8,   # 필수 여부
    5: 8,   # 원본/사본
    6: 16,  # 파일명
    7: 8,   # 제출 여부
    8: 10,  # 확인 결과
    9: 12,  # 비고
}

# 제출 여부별 fill
_SUBMITTED_FILL = {
    "○":    FILL_HEADER,   # 제출 완료 → 청색
    "제출":  FILL_HEADER,
    "×":    FILL_WARN,    # 미제출 → 황색
    "미제출": FILL_WARN,
    "보완중": FILL_NOTICE,
}

# 기본 첨부서류 예시 (데이터 없을 때 표시)
DEFAULT_ATTACHMENT_ITEMS: List[Dict[str, Any]] = [
    {"no":"1",  "doc_name":"사진대지",           "category":"사진",    "required":"필수", "original_copy":"전자", "file_name":"", "submitted":"", "check_result":"", "remarks":""},
    {"no":"2",  "doc_name":"참석자 명부",          "category":"서식",    "required":"필수", "original_copy":"원본", "file_name":"", "submitted":"", "check_result":"", "remarks":""},
    {"no":"3",  "doc_name":"교육자료",            "category":"기타",    "required":"선택", "original_copy":"전자", "file_name":"", "submitted":"", "check_result":"", "remarks":""},
    {"no":"4",  "doc_name":"자격증 사본",          "category":"자격증",  "required":"필수", "original_copy":"사본", "file_name":"", "submitted":"", "check_result":"", "remarks":""},
    {"no":"5",  "doc_name":"보험증 사본",          "category":"검사증",  "required":"필수", "original_copy":"사본", "file_name":"", "submitted":"", "check_result":"", "remarks":""},
    {"no":"6",  "doc_name":"정기검사증 사본",       "category":"검사증",  "required":"필수", "original_copy":"사본", "file_name":"", "submitted":"", "check_result":"", "remarks":""},
    {"no":"7",  "doc_name":"작업허가서",           "category":"서식",    "required":"필수", "original_copy":"원본", "file_name":"", "submitted":"", "check_result":"", "remarks":""},
    {"no":"8",  "doc_name":"위험성평가표",          "category":"서식",    "required":"필수", "original_copy":"원본", "file_name":"", "submitted":"", "check_result":"", "remarks":""},
    {"no":"9",  "doc_name":"개선조치 확인서",       "category":"서식",    "required":"선택", "original_copy":"원본", "file_name":"", "submitted":"", "check_result":"", "remarks":""},
    {"no":"10", "doc_name":"시험성적서",           "category":"기타",    "required":"선택", "original_copy":"원본", "file_name":"", "submitted":"", "check_result":"", "remarks":""},
]


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _two_col(ws, row: int,
             label1: str, val1: Any,
             label2: str, val2: Any,
             height: float = 20) -> int:
    write_cell(ws, row, 1, 1, label1, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, val1,   font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, label2, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 9, val2,   font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height
    return row + 1


def _full_row(ws, row: int, label: str, val: Any, height: float = 20) -> int:
    write_cell(ws, row, 1, 1, label, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, TOTAL_COLS, val, font=FONT_DEFAULT, align=ALIGN_LEFT)
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

def build_document_attachment_list(form_data: Dict[str, Any]) -> bytes:
    """첨부서류 목록표 부대서류 Excel bytes 반환."""
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

    # ── s1. 첨부서류 목록표 기본정보 ──────────────────────────────────────
    row = _section_header(ws, row, "① 첨부서류 목록표 기본정보")
    row = _two_col(ws, row, "현장명",   v(form_data, "site_name"),
                             "작성 일자", v(form_data, "doc_date"))
    row = _two_col(ws, row, "공사명",   v(form_data, "project_name"),
                             "회사명",    v(form_data, "company_name"))
    row = _blank(ws, row, 6)

    # ── s2. 연결 문서 정보 ────────────────────────────────────────────────
    row = _section_header(ws, row, "② 연결 문서 정보  (부대서류)")
    row = _two_col(ws, row, "연결 문서 ID",   v(form_data, "parent_doc_id"),
                             "연결 문서명",     v(form_data, "parent_doc_name"))
    row = _two_col(ws, row, "연결 form_type", v(form_data, "parent_form_type"),
                             "비고",            v(form_data, "remarks"))
    row = _blank(ws, row, 6)

    # ── s3. 제출 패키지 정보 ──────────────────────────────────────────────
    row = _section_header(ws, row, "③ 제출 패키지 정보")
    row = _full_row(ws, row, "패키지 제목",  v(form_data, "package_title"))
    row = _two_col(ws, row, "제출 일자",  v(form_data, "package_date"),
                             "제출처",      v(form_data, "submitted_to"))
    row = _two_col(ws, row, "제출자",     v(form_data, "submitted_by"),
                             "총 첨부 건수", v(form_data, "total_count"))
    row = _blank(ws, row, 6)

    # ── s4. 첨부서류 목록 ─────────────────────────────────────────────────
    row = _section_header(ws, row, "④ 첨부서류 목록")

    # 테이블 헤더
    col_hdrs = ["순번", "첨부서류명", "구분", "필수 여부", "원본/사본", "파일명", "제출 여부", "확인 결과", "비고"]
    for c, h in enumerate(col_hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    row += 1

    raw_items: List[Dict[str, Any]] = form_data.get("attachment_items") or []
    items = raw_items if raw_items else DEFAULT_ATTACHMENT_ITEMS
    items = items[:MAX_ATTACH_ROWS]

    for it in items:
        sub_val  = v(it, "submitted", "")
        sub_fill = _SUBMITTED_FILL.get(sub_val, FILL_NONE)
        req_val  = v(it, "required", "")
        req_fill = FILL_WARN if req_val == "필수" else FILL_NONE

        write_cell(ws, row, 1, 1, v(it, "no"),           font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, v(it, "doc_name"),     font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, v(it, "category"),     font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 4, req_val,               font=FONT_SMALL, fill=req_fill, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(it, "original_copy"),font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(it, "file_name"),    font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, sub_val,               font=FONT_SMALL, fill=sub_fill, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(it, "check_result"), font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 9, 9, v(it, "remarks", ""),  font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 20
        row += 1

    # 빈 행 여백 (최소 3행)
    empty = max(3, MAX_ATTACH_ROWS - len(items))
    empty = min(empty, MAX_ATTACH_ROWS - len(items))
    next_no = len(items) + 1
    for i in range(empty):
        write_cell(ws, row, 1, 1, str(next_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 20
        row += 1

    row = _blank(ws, row, 6)

    # ── s5. 필수/선택 구분 안내 ───────────────────────────────────────────
    row = _section_header(ws, row, "⑤ 필수 / 선택 구분")
    write_cell(ws, row, 1, 4, "필수  (황색 표시)",
               font=FONT_BOLD, fill=FILL_WARN, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 9, "선택  (표시 없음)",
               font=FONT_BOLD, fill=FILL_NONE, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    row += 1
    row = _blank(ws, row, 6)

    # ── s6. 원본/사본 구분 ────────────────────────────────────────────────
    row = _section_header(ws, row, "⑥ 원본 / 사본 구분")
    guide6 = (
        "원본: 서명·날인이 있는 실물 서류.  "
        "사본: 원본의 복사본 (필요 시 원본 대조 인 날인).  "
        "전자: 전자파일 제출 (PDF·Excel·이미지 등)."
    )
    write_cell(ws, row, 1, TOTAL_COLS, guide6,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 24
    row += 1
    row = _blank(ws, row, 6)

    # ── s7. 제출 여부 ─────────────────────────────────────────────────────
    row = _section_header(ws, row, "⑦ 제출 여부")
    write_cell(ws, row, 1, 3, "○  제출 완료 (청색)",
               font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 4, 6, "×  미제출 (황색)",
               font=FONT_BOLD, fill=FILL_WARN, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 9, "보완중  (회색)",
               font=FONT_BOLD, fill=FILL_NOTICE, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 22
    row += 1
    row = _blank(ws, row, 6)

    # ── s8. 누락/보완 필요사항 ────────────────────────────────────────────
    row = _section_header(ws, row, "⑧ 누락 / 보완 필요사항")
    row = _two_col(ws, row, "누락/보완 건수", v(form_data, "missing_count"),
                             "보완 제출 기한",  v(form_data, "supplement_due"))
    row = _full_row(ws, row, "보완 필요사항",   v(form_data, "missing_remarks"), height=36)
    row = _blank(ws, row, 6)

    # ── s9. 확인자 서명 ───────────────────────────────────────────────────
    row = _section_header(ws, row, "⑨ 확인자 서명")
    write_cell(ws, row, 1, 2, "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 4, "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 6, "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 9, "확인 일자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    for role, key in [("작성자", "prepared_by"), ("검토자", "checked_by"), ("확인자", "approved_by")]:
        write_cell(ws, row, 1, 2, role,                    font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 4, v(form_data, key),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 6, "",                      font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 9, v(form_data, "doc_date"),font=FONT_DEFAULT, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 24
        row += 1
    row = _blank(ws, row, 6)

    # ── 하단 안내 ─────────────────────────────────────────────────────────
    notice = (
        "[document_attachment_list] 본 첨부서류 목록표는 핵심 안전서류 제출 패키지에 포함되는 "
        "첨부서류를 목록화하는 부대서류입니다. document_catalog 독립 문서가 아님."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 24

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

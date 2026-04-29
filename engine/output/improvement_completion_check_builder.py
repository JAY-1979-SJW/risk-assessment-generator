"""
개선조치 완료 확인서 — 부대서류 Excel 출력 모듈 (v1).

위험성평가 개선대책, 부적합 조치, 사고 재발방지대책, 감리/점검 지적사항 등에 대한
조치 완료 확인용 부대서류.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

supplemental_type: improvement_completion_check
함수명:            build_improvement_completion_check(form_data)

Required form_data keys:
    site_name       str  현장명
    assessment_date str  평가/점검 일자

Optional form_data keys:
    parent_doc_id       str   연결 문서 ID
    parent_doc_name     str   연결 문서명
    parent_form_type    str   연결 form_type
    project_name        str   공사명
    company_name        str   회사명
    work_name           str   작업/공종명
    assessor            str   평가/점검자
    confirmer           str   확인자 성명
    confirmer_position  str   확인자 직책
    approver            str   승인자 성명
    approver_position   str   승인자 직책
    confirm_date        str   확인 일자
    before_status       str   개선 전 상태 설명
    after_status        str   개선 후 상태 설명
    residual_risk       str   잔여위험 내용
    supplement_items    str   미완료·추가 보완사항
    recurrence_plan     str   재발방지 대책
    maintenance_plan    str   유지관리 계획
    maintenance_owner   str   유지관리 담당자
    remarks             str   비고

    improvement_items  list[dict]  개선조치 목록 (repeat, 최대 12건)
        각 항목:
            no           int|str  순번
            issue        str      지적/위험 사항
            measure      str      개선대책
            due_date     str      완료 예정일
            done_date    str      완료일
            owner        str      담당자
            done         str      완료 여부 (○/×/진행중)
            evidence     str      증빙자료
            residual     str      잔여위험
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

SUPPLEMENTAL_TYPE = "improvement_completion_check"
SHEET_NAME        = "개선조치완료확인서"
SHEET_HEADING     = "개선조치 완료 확인서"
SHEET_SUBTITLE    = (
    "위험성평가 개선대책·부적합 조치·재발방지대책 이행 완료 확인  "
    "[improvement_completion_check]  부대서류"
)

TOTAL_COLS       = 10
MAX_IMPROVE_ROWS = 12

# A4 가로 권장 — 열 10개
_COL_WIDTHS: Dict[int, float] = {
    1:  5,   # 순번
    2:  20,  # 지적/위험 사항
    3:  18,  # 개선대책
    4:  10,  # 완료 예정일
    5:  10,  # 완료일
    6:  9,   # 담당자
    7:  9,   # 완료 여부
    8:  12,  # 증빙자료
    9:  10,  # 잔여위험
    10: 10,  # 비고
}

_DONE_FILL = {
    "○":    FILL_HEADER,
    "완료":  FILL_HEADER,
    "×":    FILL_WARN,
    "미완료": FILL_WARN,
    "진행중": FILL_NOTICE,
}

DEFAULT_IMPROVEMENT_ITEMS: List[Dict[str, Any]] = [
    {"no":"1",  "issue":"불안전한 작업발판 설치",    "measure":"표준 작업발판으로 교체",    "due_date":"", "done_date":"", "owner":"", "done":"", "evidence":"사진", "residual":"", "remarks":""},
    {"no":"2",  "issue":"안전대 미착용",             "measure":"안전대 지급 및 착용 교육",  "due_date":"", "done_date":"", "owner":"", "done":"", "evidence":"교육기록", "residual":"", "remarks":""},
    {"no":"3",  "issue":"가스누출 위험 배관 손상",    "measure":"배관 교체 및 점검",         "due_date":"", "done_date":"", "owner":"", "done":"", "evidence":"점검표", "residual":"", "remarks":""},
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

def build_improvement_completion_check(form_data: Dict[str, Any]) -> bytes:
    """개선조치 완료 확인서 부대서류 Excel bytes 반환."""
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
    row = _section_header(ws, row, "① 개선조치 완료 확인서 기본정보")
    row = _two_col(ws, row, "현장명",       v(form_data, "site_name"),
                             "평가/점검 일자", v(form_data, "assessment_date"))
    row = _two_col(ws, row, "공사명",       v(form_data, "project_name"),
                             "회사명",       v(form_data, "company_name"))
    row = _two_col(ws, row, "작업/공종명",  v(form_data, "work_name"),
                             "평가/점검자",  v(form_data, "assessor"))
    row = _blank(ws, row, 6)

    # ── s2. 연결 문서 정보 ─────────────────────────────────────────────────
    row = _section_header(ws, row, "② 연결 문서 정보  (부대서류)")
    row = _two_col(ws, row, "연결 문서 ID",   v(form_data, "parent_doc_id"),
                             "연결 문서명",    v(form_data, "parent_doc_name"))
    row = _two_col(ws, row, "연결 form_type", v(form_data, "parent_form_type"),
                             "비고",           v(form_data, "remarks"))
    row = _blank(ws, row, 6)

    # ── s3. 지적/위험/부적합 사항 (요약) ──────────────────────────────────
    row = _section_header(ws, row, "③ 지적 / 위험 / 부적합 사항  (요약)")
    row = _full_row(ws, row, "개선 전 상태", v(form_data, "before_status"), height=40)
    row = _blank(ws, row, 6)

    # ── s4. 개선대책 및 실행 내용 (표) ────────────────────────────────────
    row = _section_header(ws, row, "④ 개선대책 및 실행 내용  /  ⑤ 조치 완료 확인")

    col_hdrs = ["순번", "지적/위험 사항", "개선대책", "완료 예정일", "완료일",
                "담당자", "완료 여부", "증빙자료", "잔여위험", "비고"]
    for c, h in enumerate(col_hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 22
    row += 1

    raw_items: List[Dict[str, Any]] = form_data.get("improvement_items") or []
    items = raw_items if raw_items else DEFAULT_IMPROVEMENT_ITEMS
    items = items[:MAX_IMPROVE_ROWS]

    for it in items:
        dval  = v(it, "done", "")
        dfill = _DONE_FILL.get(dval, FILL_NONE)

        write_cell(ws, row, 1,  1,  v(it, "no"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2,  2,  v(it, "issue"),    font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 3,  3,  v(it, "measure"),  font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 4,  4,  v(it, "due_date"), font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5,  5,  v(it, "done_date"),font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 6,  6,  v(it, "owner"),    font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7,  7,  dval,              font=FONT_SMALL, fill=dfill, align=ALIGN_CENTER)
        write_cell(ws, row, 8,  8,  v(it, "evidence"), font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 9,  9,  v(it, "residual"), font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 10, 10, v(it, "remarks"),  font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 22
        row += 1

    empty = max(3, MAX_IMPROVE_ROWS - len(items))
    next_no = len(items) + 1
    for i in range(empty):
        write_cell(ws, row, 1, 1, str(next_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 22
        row += 1

    row = _blank(ws, row, 6)

    # ── s6. 개선 후 위험성 또는 잔여위험 ──────────────────────────────────
    row = _section_header(ws, row, "⑥ 개선 후 상태 및 잔여위험")
    row = _full_row(ws, row, "개선 후 상태",  v(form_data, "after_status"),  height=36)
    row = _full_row(ws, row, "잔여위험 내용", v(form_data, "residual_risk"), height=36)
    row = _blank(ws, row, 6)

    # ── s7. 사진/첨부 확인 ────────────────────────────────────────────────
    row = _section_header(ws, row, "⑦ 사진 / 첨부 확인")
    notice7 = (
        "개선 전·후 비교 사진, 증빙서류, 검사·시험 성적서 등 필요 시 "
        "사진대지(photo_attachment_sheet) 또는 첨부서류 목록표(document_attachment_list) 부대서류 첨부."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice7,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 28
    row += 1
    row = _blank(ws, row, 6)

    # ── s8. 미완료·추가 보완사항 ──────────────────────────────────────────
    row = _section_header(ws, row, "⑧ 미완료 · 추가 보완사항")
    row = _full_row(ws, row, "미완료·보완사항", v(form_data, "supplement_items"), height=40)
    row = _blank(ws, row, 6)

    # ── s9. 재발방지 및 유지관리 계획 ─────────────────────────────────────
    row = _section_header(ws, row, "⑨ 재발방지 대책 및 유지관리 계획")
    row = _full_row(ws, row, "재발방지 대책",  v(form_data, "recurrence_plan"),  height=40)
    row = _full_row(ws, row, "유지관리 계획",  v(form_data, "maintenance_plan"), height=36)
    row = _two_col(ws, row, "유지관리 담당자", v(form_data, "maintenance_owner"),
                             "",               "")
    row = _blank(ws, row, 6)

    # ── s10. 확인자/승인자 서명 ───────────────────────────────────────────
    row = _section_header(ws, row, "⑩ 확인자 / 승인자 서명")
    write_cell(ws, row, 1,  2,  "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3,  5,  "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6,  6,  "직책",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7,  8,  "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 9,  10, "확인 일자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    signers = [
        ("확인자", "confirmer",  "confirmer_position"),
        ("승인자", "approver",   "approver_position"),
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
        "[improvement_completion_check] 본 개선조치 완료 확인서는 위험성평가 개선대책·부적합 조치·"
        "재발방지대책 이행 완료를 확인하는 부대서류입니다. "
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

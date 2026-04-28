"""
참석자 명부 — 부대서류 공통 Excel 출력 모듈 (v1).

교육·TBM·PTW·위험성평가 회의·안전회의 등에서 공통으로 사용하는
참석자 명부 부대서류. 핵심 안전서류(90종)에서 파생 생성된다.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

supplemental_type: attendance_roster
함수명:            build_attendance_roster(form_data)

Required form_data keys:
    site_name    str  현장명
    event_date   str  행사/교육/회의 일자
    event_title  str  제목/교육명/회의명

Optional form_data keys:
    parent_doc_id      str   연결 핵심서류 ID (예: ED-001, PTW-001)
    parent_doc_name    str   연결 핵심서류명
    event_location     str   장소
    event_type         str   유형 (교육 / TBM / 회의 / 작업허가 / 기타)
    event_duration     str   소요 시간
    instructor         str   강사/진행자
    chairperson        str   주재자/책임자
    total_attendees    str   참석 인원
    absent_count       str   미참석 인원
    absent_reason      str   미참석 사유
    confirmer          str   확인자
    confirm_date       str   확인 일자
    attendees          list[dict]  참석자 목록 (repeat)
        각 항목: no, name, affiliation, job_type, contact, entry_time, exit_time, sign

참석자 목록 필드 설명:
    no           int|str  번호
    name         str      성명
    affiliation  str      소속/협력업체명
    job_type     str      직종/직위
    contact      str      연락처 (선택)
    entry_time   str      입실 시각 (PTW 모드 시)
    exit_time    str      퇴실 시각 (PTW 모드 시)
    sign         str      서명란 (공란)
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    ALIGN_CENTER, ALIGN_LABEL, ALIGN_LEFT,
    FILL_HEADER, FILL_LABEL, FILL_NONE, FILL_NOTICE, FILL_SECTION,
    FONT_BOLD, FONT_DEFAULT, FONT_NOTICE, FONT_SMALL, FONT_SUBTITLE, FONT_TITLE,
    apply_col_widths, v, write_cell,
)

SUPPLEMENTAL_TYPE = "attendance_roster"
SHEET_NAME        = "참석자명부"
SHEET_HEADING     = "참석자 명부"
SHEET_SUBTITLE    = (
    "안전보건 행사·교육·회의·작업허가 등 핵심 안전서류에 첨부하는 부대서류  "
    "[attendance_roster]"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 5,   # No.
    2: 14,  # 성명
    3: 16,  # 소속
    4: 12,  # 직종
    5: 14,  # 연락처
    6: 10,  # 입실시각
    7: 10,  # 퇴실시각
    8: 12,  # 서명
}

MAX_ATTENDEE_ROWS = 40
DEFAULT_ATTENDEE_COUNT = 20  # 데이터 없을 때 기본 빈 행 수


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
    write_cell(ws, row, 6, 8, val2,   font=FONT_DEFAULT, align=ALIGN_LEFT)
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

def build_attendance_roster(form_data: Dict[str, Any]) -> bytes:
    """참석자 명부 부대서류 Excel bytes 반환."""
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

    # ── s1. 명부 기본정보 ─────────────────────────────────────────────────
    row = _section_header(ws, row, "① 명부 기본정보")
    row = _two_col(ws, row, "현장명",   v(form_data, "site_name"),
                             "행사/회의 일자", v(form_data, "event_date"))
    row = _full_row(ws, row, "제목/교육명", v(form_data, "event_title"))
    row = _blank(ws, row, 6)

    # ── s2. 연결 문서 정보 ────────────────────────────────────────────────
    row = _section_header(ws, row, "② 연결 문서 정보  (부대서류)")
    row = _two_col(ws, row, "연결 문서 ID",  v(form_data, "parent_doc_id"),
                             "연결 문서명",    v(form_data, "parent_doc_name"))
    row = _blank(ws, row, 6)

    # ── s3. 행사/교육/회의 정보 ───────────────────────────────────────────
    row = _section_header(ws, row, "③ 행사 / 교육 / 회의 정보")
    row = _two_col(ws, row, "장소",     v(form_data, "event_location"),
                             "유형",      v(form_data, "event_type"))
    row = _two_col(ws, row, "소요 시간", v(form_data, "event_duration"),
                             "강사/진행자", v(form_data, "instructor"))
    row = _two_col(ws, row, "주재자",   v(form_data, "chairperson"),
                             "참석 인원",  v(form_data, "total_attendees"))
    row = _blank(ws, row, 6)

    # ── s4. 참석자 목록 ───────────────────────────────────────────────────
    row = _section_header(ws, row, "④ 참석자 목록")

    # 헤더 행
    headers = ["No.", "성명", "소속", "직종", "연락처", "입실시각", "퇴실시각", "서명"]
    for c, h in enumerate(headers, 1):
        write_cell(ws, row, c, c, h,
                   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    row += 1

    raw_attendees: List[Dict[str, Any]] = form_data.get("attendees") or []
    raw_attendees = raw_attendees[:MAX_ATTENDEE_ROWS]

    # 데이터 행
    for it in raw_attendees:
        write_cell(ws, row, 1, 1, v(it, "no"),          font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, v(it, "name"),         font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, v(it, "affiliation"),  font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 4, v(it, "job_type"),     font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(it, "contact"),      font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(it, "entry_time"),   font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(it, "exit_time"),    font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(it, "sign", ""),     font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 20
        row += 1

    # 빈 행 여백 (기본 DEFAULT_ATTENDEE_COUNT행, 데이터 있으면 최소 5행)
    blank_count = max(5, DEFAULT_ATTENDEE_COUNT - len(raw_attendees)) if not raw_attendees \
                  else max(3, DEFAULT_ATTENDEE_COUNT - len(raw_attendees))
    blank_count = min(blank_count, MAX_ATTENDEE_ROWS - len(raw_attendees))
    next_no = len(raw_attendees) + 1
    for i in range(blank_count):
        write_cell(ws, row, 1, 1, str(next_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 20
        row += 1

    row = _blank(ws, row, 6)

    # ── s5. 소속/직종/연락처/서명 안내 ───────────────────────────────────
    row = _section_header(ws, row, "⑤ 작성 안내")
    guide = (
        "소속: 소속 회사명 또는 협력업체명을 기입합니다.  "
        "직종: 해당 작업의 직종 또는 직위를 기입합니다.  "
        "서명: 참석자 본인이 직접 서명합니다."
    )
    write_cell(ws, row, 1, TOTAL_COLS, guide,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 28
    row += 1
    row = _blank(ws, row, 6)

    # ── s6. 미참석자 여부 ─────────────────────────────────────────────────
    row = _section_header(ws, row, "⑥ 미참석자 여부")
    row = _two_col(ws, row, "미참석 인원", v(form_data, "absent_count"),
                             "미참석 사유",  v(form_data, "absent_reason"))
    row = _blank(ws, row, 6)

    # ── s7. 확인자 서명 ───────────────────────────────────────────────────
    row = _section_header(ws, row, "⑦ 확인자 서명")

    write_cell(ws, row, 1, 2, "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 4, "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 6, "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "확인 일자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    write_cell(ws, row, 1, 2, "확인자",            font=FONT_DEFAULT, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 4, v(form_data, "confirmer"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 6, "",                          font=FONT_DEFAULT, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, v(form_data, "confirm_date"),font=FONT_DEFAULT, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 24
    row += 1
    row = _blank(ws, row, 6)

    # ── 하단 안내 ─────────────────────────────────────────────────────────
    notice = (
        "[attendance_roster] 본 서류는 핵심 안전서류(교육일지·TBM·작업허가서·위험성평가 회의 등)에 "
        "첨부하는 부대서류입니다. document_catalog 독립 문서가 아님."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 24

    # ── bytes 반환 ────────────────────────────────────────────────────────
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

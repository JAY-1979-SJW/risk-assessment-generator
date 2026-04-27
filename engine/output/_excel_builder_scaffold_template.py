"""
==============================================================================
Excel builder scaffold template — 복사 전용 파일.

이 파일은 신규 안전서류 builder 작성 시 복사 기반으로만 사용한다.
직접 form_registry에 등록하지 않는다.
production 코드에서 이 파일을 import하지 않는다.

사용 절차:
  1. 이 파일을 engine/output/{form_name}_builder.py로 복사
  2. 아래 "▶ 변경 필요" 주석 위치를 모두 수정
  3. python -m py_compile engine/output/{form_name}_builder.py 로 문법 확인
  4. engine/output/form_registry.py에 FormSpec 1건 추가
  5. data/masters/safety/documents/document_catalog.yml에서 해당 문서 DONE 갱신
  6. 검증: import check → xlsx 생성 → load_workbook 재오픈
==============================================================================
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from collections.abc import Mapping
from typing import Any, Dict, List, Optional

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

# ---------------------------------------------------------------------------
# ▶ 변경 필요: 문서 메타데이터
# ---------------------------------------------------------------------------

DOC_ID     = "XX-000"               # ▶ 예: "WP-002", "CL-008"
FORM_TYPE  = "standard_form"        # ▶ registry form_type과 일치
SHEET_NAME = "표준서식"              # ▶ 31자 이하, 특수문자 제외 권장
SHEET_HEADING  = "표준 안전서류"     # ▶ 서식 표제
SHEET_SUBTITLE = (                   # ▶ 법령 근거 문구
    "「산업안전보건기준에 관한 규칙」 제XX조에 따른 안전서류"
    f" ({DOC_ID})"
)

# ---------------------------------------------------------------------------
# 열 구조 (8컬럼 기본)
# ▶ 필요 시 컬럼 수·너비 조정
# ---------------------------------------------------------------------------

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

# 기본정보 블록 열 스팬 (좌/우 2단 구조)
_L1, _V1S, _V1E = 1, 2, 4   # 좌: 라벨=A(1), 값=B:D(2-4)
_L2, _V2S, _V2E = 5, 6, 8   # 우: 라벨=E(5), 값=F:H(6-8)
_FULL_S, _FULL_E = 2, 8      # 전폭 값 영역 B:H

# 반복 테이블 행 수
MAX_CHECKLIST_ROWS = 10
MIN_CHECKLIST_ROWS = 5
MAX_HAZARD_ROWS    = 10
MIN_HAZARD_ROWS    = 5


# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------

def _lv(ws, row: int, label: str, value: Any,
        lc: int, vs: int, ve: int, height: float = 20) -> None:
    """라벨-값 쌍 1행 기록."""
    write_cell(ws, row, lc, lc, label,
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, vs, ve, value,
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height


def _section_header(ws, row: int, title: str) -> int:
    """섹션 헤더 1행 기록 후 다음 row 반환."""
    write_cell(ws, row, 1, TOTAL_COLS, title,
               font=FONT_BOLD, fill=FILL_SECTION, align=ALIGN_CENTER, height=22)
    return row + 1


# ---------------------------------------------------------------------------
# 섹션 렌더러
# ---------------------------------------------------------------------------

def _write_title(ws, row: int) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_SECTION, align=ALIGN_CENTER, height=28)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, height=18)
    return row + 1


def _write_meta(ws, row: int, data: Dict[str, Any]) -> int:
    """현장·공사 기본정보 블록.
    ▶ 필드명은 form_data key와 일치해야 함.
    """
    row = _section_header(ws, row, "▶ 기본 정보")
    _lv(ws, row, "현장명",   v(data, "site_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",   v(data, "project_name"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "업체명",   v(data, "company_name"), _L1, _V1S, _V1E)
    _lv(ws, row, "작업일자", v(data, "work_date"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업위치", v(data, "work_location"), _L1, _V1S, _V1E)
    _lv(ws, row, "작업종류", v(data, "work_type"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "책임자",   v(data, "supervisor"),   _L1, _V1S, _V1E)
    _lv(ws, row, "작업인원", v(data, "workers"),       _L2, _V2S, _V2E)
    return row + 1


def _write_work_overview(ws, row: int, data: Dict[str, Any]) -> int:
    """작업 개요 섹션.
    ▶ work_summary, equipment 등 단순 텍스트 필드.
    """
    row = _section_header(ws, row, "▶ 작업 개요")
    write_cell(ws, row, 1, 1, "작업 내용",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "work_summary"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    row += 1
    write_cell(ws, row, 1, 1, "사용 장비",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=20)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "equipment"),
               font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
    return row + 1


def _write_checklist(ws, row: int, data: Dict[str, Any]) -> int:
    """점검 항목 반복 테이블.
    ▶ checklist_items: list[dict]
       each item: {item, standard, result, remarks}
    """
    row = _section_header(ws, row, "▶ 점검 항목")

    # 헤더
    headers   = ["번호", "점검 항목",    "기준",   "결과",   "비고"]
    col_spans = [(1, 1),  (2, 4),         (5, 5),   (6, 7),   (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("checklist_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_CHECKLIST_ROWS, len(items))
    display = min(display, MAX_CHECKLIST_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,              font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 4, v(item, "item"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 5, v(item, "standard"), font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 6, 7, v(item, "result"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_hazard_table(ws, row: int, data: Dict[str, Any]) -> int:
    """위험요인 및 안전대책 반복 테이블.
    ▶ hazard_items: list[dict]
       each item: {hazard_type, description, measure, responsible}
    """
    row = _section_header(ws, row, "▶ 위험요인 및 안전대책")

    headers   = ["번호", "위험 유형", "위험 요인",    "안전 대책",   "담당자"]
    col_spans = [(1, 1),  (2, 2),      (3, 5),         (6, 7),        (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("hazard_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_HAZARD_ROWS, len(items))
    display = min(display, MAX_HAZARD_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                   font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 2, v(item, "hazard_type"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 5, v(item, "description"),   font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 7, v(item, "measure"),       font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(item, "responsible"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _write_emergency_plan(ws, row: int, data: Dict[str, Any]) -> int:
    """비상조치 계획 섹션.
    ▶ emergency_contacts: list[dict] — {role, name, phone}
    """
    row = _section_header(ws, row, "▶ 비상조치 계획")

    # 비상연락망 테이블
    write_cell(ws, row, 1, 2, "역할",       font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, 5, "성명",       font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 8, "연락처",     font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    raw: Any = data.get("emergency_contacts")
    contacts: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    for _ in range(max(3, len(contacts))):
        contact = contacts[_] if _ < len(contacts) else {}
        write_cell(ws, row, 1, 2, v(contact, "role"),  font=FONT_DEFAULT, align=ALIGN_CENTER, height=20)
        write_cell(ws, row, 3, 5, v(contact, "name"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 8, v(contact, "phone"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    """확인자·서명란."""
    row = _section_header(ws, row, "▶ 확인")
    # 라벨행
    write_cell(ws, row, 1, 2, "작성자",                    font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, 4, v(data, "supervisor"),        font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "확인자",                    font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, v(data, "approver"),          font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1
    # 서명 공간
    write_cell(ws, row, 1, 2, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    write_cell(ws, row, 3, 4, "",      font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "",      font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _finalize_sheet(ws) -> None:
    """인쇄 설정 공통 적용 (A4 세로, 1페이지 너비 맞춤)."""
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75


# ---------------------------------------------------------------------------
# 공개 API
# ▶ 복사 후 함수명과 반환 방식을 수정한다.
# ---------------------------------------------------------------------------

def build_standard_excel(
    form_data: Mapping[str, Any],
) -> bytes:
    """form_data dict를 받아 표준 안전서류 xlsx 바이너리를 반환한다.

    ▶ 복사 후 반드시 수정:
       - 함수명: build_{form_name}_excel
       - docstring 서식명
    """
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME  # ▶ 31자 이하 확인
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_work_overview(ws, row, data)
    row = _write_checklist(ws, row, data)
    row = _write_hazard_table(ws, row, data)
    row = _write_emergency_plan(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

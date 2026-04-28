"""
사진대지 — 부대서류 공통 Excel 출력 모듈 (v1).

교육·TBM·작업허가·위험성평가 개선조치·사고/비상대응·안전문화 활동 등
핵심 안전서류(90종)에 첨부하는 공통 사진대지 부대서류.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

사진 실물 이미지 삽입은 현 단계 미구현.
image_path / file_name 필드를 통해 향후 이미지 삽입 확장 가능.

supplemental_type: photo_attachment_sheet
함수명:            build_photo_attachment_sheet(form_data)

Required form_data keys:
    site_name      str  현장명
    doc_date       str  작성 일자
    parent_doc_id  str  연결 핵심서류 ID (예: ED-001, PTW-001, EM-001)

Optional form_data keys:
    parent_doc_name  str   연결 핵심서류명
    photo_mode       str   사진대지 모드
                           default | before_after | accident | education | equipment
    project_name     str   공사명
    company_name     str   회사명
    location         str   촬영 장소 (공통)
    photographer     str   촬영자 (공통)
    total_photo_count str  총 사진 수
    confirmer        str   확인자
    confirm_date     str   확인 일자
    remarks          str   비고

    photo_items  list[dict]  사진 목록 (repeat, 최대 12건)
        각 항목:
            photo_no      int|str  사진 번호
            photo_desc    str      사진 설명
            taken_date    str      촬영 일자
            taken_time    str      촬영 시각
            taken_location str     촬영 장소
            taken_by      str      촬영자
            file_name     str      파일명 (image_path 향후 연동 예약 필드)
            before_after  str      조치 전/후 구분 (before | after | -)
            remarks       str      비고
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

SUPPLEMENTAL_TYPE = "photo_attachment_sheet"
SHEET_NAME        = "사진대지"
SHEET_HEADING     = "사진대지"
SHEET_SUBTITLE    = (
    "안전보건 핵심서류에 첨부하는 부대서류 — 사진 목록·설명·촬영정보 기록  "
    "[photo_attachment_sheet]"
)

TOTAL_COLS   = 9
MAX_PHOTO_ROWS = 12

_COL_WIDTHS: Dict[int, float] = {
    1: 6,   # No.
    2: 16,  # 사진 설명
    3: 12,  # 촬영일자
    4: 10,  # 촬영시각
    5: 14,  # 촬영장소
    6: 12,  # 촬영자
    7: 18,  # 파일명
    8: 10,  # 조치전/후
    9: 12,  # 비고
}

# 조치 전/후 구분 fill 매핑
_BEFORE_AFTER_FILL = {
    "before": FILL_WARN,
    "조치 전": FILL_WARN,
    "개선 전": FILL_WARN,
    "after":  FILL_HEADER,
    "조치 후": FILL_HEADER,
    "개선 후": FILL_HEADER,
}


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

def build_photo_attachment_sheet(form_data: Dict[str, Any]) -> bytes:
    """사진대지 부대서류 Excel bytes 반환."""
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

    # ── s1. 사진대지 기본정보 ─────────────────────────────────────────────
    row = _section_header(ws, row, "① 사진대지 기본정보")
    row = _two_col(ws, row, "현장명",  v(form_data, "site_name"),
                             "작성 일자", v(form_data, "doc_date"))
    row = _two_col(ws, row, "공사명",  v(form_data, "project_name"),
                             "회사명",   v(form_data, "company_name"))
    row = _blank(ws, row, 6)

    # ── s2. 연결 문서 정보 ────────────────────────────────────────────────
    row = _section_header(ws, row, "② 연결 문서 정보  (부대서류)")
    row = _two_col(ws, row, "연결 문서 ID",  v(form_data, "parent_doc_id"),
                             "연결 문서명",    v(form_data, "parent_doc_name"))
    mode_disp = {
        "default":     "기본 (사진 목록)",
        "before_after":"개선 전/후 비교",
        "accident":    "재해 현장",
        "education":   "교육/활동",
        "equipment":   "장비/보호구",
    }.get(v(form_data, "photo_mode"), v(form_data, "photo_mode"))
    row = _two_col(ws, row, "사진대지 모드", mode_disp,
                             "총 사진 수",     v(form_data, "total_photo_count"))
    row = _blank(ws, row, 6)

    # ── s3. 현장/공사 정보 ────────────────────────────────────────────────
    row = _section_header(ws, row, "③ 현장 / 공사 정보")
    row = _two_col(ws, row, "촬영 장소 (공통)", v(form_data, "location"),
                             "촬영자 (공통)",    v(form_data, "photographer"))
    row = _blank(ws, row, 6)

    # ── s4. 사진 목록 ─────────────────────────────────────────────────────
    row = _section_header(ws, row, "④ 사진 목록")

    # 컬럼 헤더
    col_hdrs = [
        "사진 번호", "사진 설명", "촬영일자", "촬영시각",
        "촬영장소",  "촬영자",   "파일명",   "조치전/후", "비고",
    ]
    for c, h in enumerate(col_hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    row += 1

    raw_items: List[Dict[str, Any]] = form_data.get("photo_items") or []
    raw_items = raw_items[:MAX_PHOTO_ROWS]

    for it in raw_items:
        ba_val = v(it, "before_after", "")
        ba_fill = _BEFORE_AFTER_FILL.get(ba_val.lower() if ba_val else "", FILL_NONE)

        write_cell(ws, row, 1, 1, v(it, "photo_no"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, v(it, "photo_desc"),     font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, v(it, "taken_date"),     font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 4, v(it, "taken_time"),     font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(it, "taken_location"), font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(it, "taken_by"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(it, "file_name"),      font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, ba_val,                  font=FONT_SMALL, fill=ba_fill,
                   align=ALIGN_CENTER)
        write_cell(ws, row, 9, 9, v(it, "remarks", ""),    font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 20
        row += 1

    # 빈 행 여백
    empty_count = max(3, MAX_PHOTO_ROWS - len(raw_items))
    empty_count = min(empty_count, MAX_PHOTO_ROWS - len(raw_items))
    next_no = len(raw_items) + 1
    for i in range(empty_count):
        write_cell(ws, row, 1, 1, str(next_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 20
        row += 1

    row = _blank(ws, row, 6)

    # ── s5. 사진별 설명 (확장 안내) ──────────────────────────────────────
    row = _section_header(ws, row, "⑤ 사진 설명 작성 안내")
    guide = (
        "사진 설명: 해당 사진에서 확인 가능한 위험요인·개선조치·활동 내용을 간략히 기재.  "
        "파일명: 첨부 이미지 파일명을 기입 (향후 이미지 자동 삽입 연동 예약 필드).  "
        "조치전/후: 개선 전·후 비교 사진인 경우 '개선 전' 또는 '개선 후'를 기입."
    )
    write_cell(ws, row, 1, TOTAL_COLS, guide,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 36
    row += 1
    row = _blank(ws, row, 6)

    # ── s6. 촬영일시·촬영장소 요약 ───────────────────────────────────────
    row = _section_header(ws, row, "⑥ 촬영 일시 / 촬영 장소 요약")
    row = _two_col(ws, row, "촬영 기간",   v(form_data, "location"),
                             "주요 촬영 장소", v(form_data, "location"))
    row = _blank(ws, row, 6)

    # ── s7. 조치 전/조치 후 구분 안내 ────────────────────────────────────
    row = _section_header(ws, row, "⑦ 조치 전 / 조치 후 구분")

    write_cell(ws, row, 1, 4, "개선 전 (노란색 표시)",
               font=FONT_BOLD, fill=FILL_WARN, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 9, "개선 후 (파란색 표시)",
               font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 22
    row += 1

    write_cell(ws, row, 1, 4,
               "before_after 필드에 '개선 전' 또는 '조치 전' 입력 시 표시",
               font=FONT_SMALL, fill=FILL_WARN, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 9,
               "before_after 필드에 '개선 후' 또는 '조치 후' 입력 시 표시",
               font=FONT_SMALL, fill=FILL_HEADER, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 20
    row += 1
    row = _blank(ws, row, 6)

    # ── s8. 첨부 확인 및 확인자 서명 ─────────────────────────────────────
    row = _section_header(ws, row, "⑧ 첨부 확인 및 확인자 서명")

    write_cell(ws, row, 1, 3, "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 4, 5, "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 7, "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 9, "확인 일자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    write_cell(ws, row, 1, 3, "확인자",                    font=FONT_DEFAULT, align=ALIGN_CENTER)
    write_cell(ws, row, 4, 5, v(form_data, "confirmer"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 7, "",                           font=FONT_DEFAULT, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 9, v(form_data, "confirm_date"),font=FONT_DEFAULT, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 24
    row += 1
    row = _blank(ws, row, 6)

    # ── 하단 안내 ─────────────────────────────────────────────────────────
    notice = (
        "[photo_attachment_sheet] 본 사진대지는 핵심 안전서류(교육일지·작업허가서·위험성평가·사고보고서 등)에 "
        "첨부하는 부대서류입니다. 사진 실물 이미지 첨부는 file_name 필드를 통해 별도 관리합니다. "
        "document_catalog 독립 문서가 아님."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 28

    # ── bytes 반환 ────────────────────────────────────────────────────────
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

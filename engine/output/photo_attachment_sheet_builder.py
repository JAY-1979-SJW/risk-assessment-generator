"""
사진대지 — 부대서류 공통 Excel 출력 모듈 (v2).

교육·TBM·작업허가·위험성평가 개선조치·사고/비상대응·안전문화 활동·감리/검측 등
핵심 안전서류(90종)에 첨부하는 공통 사진대지 부대서류.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

사진 실물 이미지 삽입은 현 단계 미구현.
image_path / file_name 필드를 통해 향후 이미지 삽입 확장 가능.

supplemental_type: photo_attachment_sheet
함수명:            build_photo_attachment_sheet(form_data)

[사진대지 유형 (layout_type)]

  standard           — 일반 사진대지 (기본값, 페이지당 4장, 2×2)
  evidence_large     — 중요 증빙 사진대지 (페이지당 2장, 1×2)
  activity_compact   — 활동 기록 사진대지 (페이지당 6장, 2×3)
  before_after       — 개선 전/후 비교 사진대지 (세트 단위 비교)
  inspection_sequence— 검측/공정 순서 사진대지 (순서형 번호 강조)

Required form_data keys:
    site_name      str  현장명
    doc_date       str  작성 일자
    parent_doc_id  str  연결 핵심서류 ID (예: ED-001, PTW-001, EM-001)

Optional form_data keys (공통):
    parent_doc_name   str   연결 핵심서류명
    parent_form_type  str   연결 핵심서류 form_type
    project_name      str   공사명
    company_name      str   회사명 (시공사)
    contractor_name   str   협력업체명
    document_title    str   사진대지 제목 (미입력 시 layout 기본 제목 사용)
    layout_type       str   사진대지 유형 (standard|evidence_large|activity_compact|before_after|inspection_sequence)
    photos_per_page   int   페이지당 사진 수 (2|4|6)
    location          str   촬영 장소 (공통)
    photographer      str   촬영자 (공통)
    total_photo_count str   총 사진 수
    prepared_by       str   작성자
    checked_by        str   검토자
    approved_by       str   확인자
    created_date      str   작성 일자 (doc_date과 동일, 별칭)
    remarks           str   비고

    photos / photo_items  list[dict]  사진 목록 (둘 다 지원, photos 우선)
        공통 항목:
            photo_no         int|str  사진 번호
            taken_at         str      촬영일시 (taken_date/taken_time 대신 사용 가능)
            taken_date       str      촬영일자
            taken_time       str      촬영시각
            location         str      촬영장소
            description      str      사진 설명
            file_name        str      파일명
            image_path       str      이미지 경로 (향후 삽입 확장 예약)
            category         str      분류
            before_after_type str     개선전/후 구분 (before|after|개선 전|개선 후)
            remarks          str      비고

        evidence_large 추가:
            related_issue    str      위험요인/지적사항
            action_taken     str      조치내용
            confirmer        str      확인자

        activity_compact 추가:
            activity_name    str      활동명
            participants     str      참여자
            activity_desc    str      활동내용

        before_after 추가:
            improvement_target str    개선 대상
            improvement_desc   str    개선 내용
            completed_date     str    완료일
            confirmer          str    확인자

        inspection_sequence 추가:
            work_step        str      공정 단계
            check_location   str      검측 위치
            check_content    str      검측 내용
            check_result     str      확인 결과
            confirmer        str      확인자
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    ALIGN_CENTER, ALIGN_LABEL, ALIGN_LEFT,
    FILL_HEADER, FILL_LABEL, FILL_NONE, FILL_NOTICE, FILL_SECTION, FILL_WARN,
    FONT_BOLD, FONT_DEFAULT, FONT_NOTICE, FONT_SMALL, FONT_SUBTITLE, FONT_TITLE,
    apply_col_widths,
    apply_a4_page_setup, set_print_area_to_used_range, v, write_cell,
)

SUPPLEMENTAL_TYPE = "photo_attachment_sheet"
SHEET_NAME        = "사진대지"
SHEET_SUBTITLE    = (
    "안전보건 핵심서류에 첨부하는 부대서류 — 사진 목록·설명·촬영정보 기록  "
    "[photo_attachment_sheet]"
)

TOTAL_COLS = 9

# 유형별 기본 제목
_LAYOUT_TITLES: Dict[str, str] = {
    "standard":           "사진대지",
    "evidence_large":     "사진대지 (중요 증빙)",
    "activity_compact":   "사진대지 (활동 기록)",
    "before_after":       "사진대지 (개선 전/후 비교)",
    "inspection_sequence":"사진대지 (검측·공정 순서)",
}

# 유형별 설명 안내
_LAYOUT_DESC: Dict[str, str] = {
    "standard":           "일반 현장·교육·장비·안전문화 활동 증빙 (페이지당 4장, 2×2)",
    "evidence_large":     "사고 현장·개선 전/후·감리 지적 조치 등 중요 증빙 (페이지당 2장, 1×2)",
    "activity_compact":   "안전캠페인·TBM·보호구·정리정돈 등 활동 기록 (페이지당 6장, 2×3)",
    "before_after":       "위험성평가 개선조치·부적합 조치·감리 보완 전/후 비교 (세트 단위)",
    "inspection_sequence":"검측·시공 단계별·공정 진행·매립 전/후 순서형 사진 (순서 번호 강조)",
}

# 유형별 최대 사진 수
_LAYOUT_MAX: Dict[str, int] = {
    "standard":           12,
    "evidence_large":     6,
    "activity_compact":   18,
    "before_after":       8,   # 세트 기준 4세트(전후 각 4장)
    "inspection_sequence":12,
}

# 개선 전/후 fill 매핑
_BA_FILL = {
    "before":   FILL_WARN,
    "개선 전":  FILL_WARN,
    "조치 전":  FILL_WARN,
    "after":    FILL_HEADER,
    "개선 후":  FILL_HEADER,
    "조치 후":  FILL_HEADER,
}

_COL_WIDTHS: Dict[int, float] = {
    1: 6,   2: 16, 3: 12, 4: 10,
    5: 14,  6: 12, 7: 18, 8: 10, 9: 12,
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


def _sign_row(ws, row: int,
              roles: List[tuple],  # [(구분, 성명_val, 일자_val)]
              date_label: str = "확인 일자") -> int:
    """결재/확인 행 출력."""
    write_cell(ws, row, 1, 2, "구분",      font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 4, "성명",      font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 6, "서명",      font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 9, date_label,  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1
    for role, name_val, date_val in roles:
        write_cell(ws, row, 1, 2, role,     font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 4, name_val, font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 6, "",       font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 9, date_val, font=FONT_DEFAULT, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 24
        row += 1
    return row


def _empty_photo_rows(ws, row: int, count: int, start_no: int,
                      col_count: int = 9) -> int:
    for i in range(count):
        write_cell(ws, row, 1, 1, str(start_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, col_count + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 20
        row += 1
    return row


# ---------------------------------------------------------------------------
# 유형별 사진 목록 테이블 렌더러
# ---------------------------------------------------------------------------

def _render_standard(ws, row: int, items: List[Dict], max_rows: int) -> int:
    """standard: 사진번호·설명·촬영일시·촬영장소·촬영자·파일명·구분·비고 (9컬럼)"""
    hdrs = ["사진 번호", "사진 설명", "촬영일시", "촬영일시(시각)", "촬영장소", "촬영자", "파일명", "구분", "비고"]
    for c, h in enumerate(hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    row += 1

    for it in items[:max_rows]:
        ba_val  = v(it, "before_after_type", v(it, "category", ""))
        ba_fill = _BA_FILL.get(ba_val, FILL_NONE)
        taken   = v(it, "taken_at", "")
        write_cell(ws, row, 1, 1, v(it, "photo_no"),              font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, v(it, "description"),           font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, v(it, "taken_date", taken),     font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 4, v(it, "taken_time", ""),        font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(it, "location"),              font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(it, "photographer", ""),      font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(it, "file_name"),             font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, ba_val, font=FONT_SMALL, fill=ba_fill, align=ALIGN_CENTER)
        write_cell(ws, row, 9, 9, v(it, "remarks", ""),           font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 20
        row += 1

    empty = max(3, max_rows - len(items))
    empty = min(empty, max_rows - len(items))
    row = _empty_photo_rows(ws, row, empty, len(items) + 1)
    return row


def _render_evidence_large(ws, row: int, items: List[Dict], max_rows: int) -> int:
    """evidence_large: 증빙 구분, 위험요인/지적사항, 조치내용, 확인자 추가"""
    hdrs = ["사진 번호", "사진 설명", "촬영일시", "촬영장소", "위험요인/지적사항", "조치내용", "파일명", "확인자", "비고"]
    for c, h in enumerate(hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    row += 1

    for it in items[:max_rows]:
        ba_val  = v(it, "before_after_type", "")
        ba_fill = _BA_FILL.get(ba_val, FILL_NONE)
        taken   = v(it, "taken_at", v(it, "taken_date", ""))
        write_cell(ws, row, 1, 1, v(it, "photo_no"),             font=FONT_SMALL, fill=ba_fill, align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, v(it, "description"),          font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, taken,                         font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 4, v(it, "location"),             font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(it, "related_issue", ""),    font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 6, v(it, "action_taken", ""),     font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, v(it, "file_name"),            font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(it, "confirmer", ""),        font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 9, 9, v(it, "remarks", ""),          font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 24
        row += 1

    empty = max(2, max_rows - len(items))
    empty = min(empty, max_rows - len(items))
    row = _empty_photo_rows(ws, row, empty, len(items) + 1)
    return row


def _render_activity_compact(ws, row: int, items: List[Dict], max_rows: int) -> int:
    """activity_compact: 활동명, 참여자, 활동내용 추가"""
    hdrs = ["사진 번호", "사진 설명", "촬영일시", "촬영장소", "활동명", "참여자", "파일명", "활동내용", "비고"]
    for c, h in enumerate(hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    row += 1

    for it in items[:max_rows]:
        taken = v(it, "taken_at", v(it, "taken_date", ""))
        write_cell(ws, row, 1, 1, v(it, "photo_no"),             font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, v(it, "description"),          font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, taken,                         font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 4, v(it, "location"),             font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(it, "activity_name", ""),    font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 6, v(it, "participants", ""),     font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(it, "file_name"),            font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, v(it, "activity_desc", ""),    font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 9, 9, v(it, "remarks", ""),          font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 20
        row += 1

    empty = max(4, max_rows - len(items))
    empty = min(empty, max_rows - len(items))
    row = _empty_photo_rows(ws, row, empty, len(items) + 1)
    return row


def _render_before_after(ws, row: int, items: List[Dict], max_rows: int) -> int:
    """before_after: 개선대상·개선내용·완료일·확인자 포함, 전/후 배경색 구분"""
    hdrs = ["사진 번호", "사진 설명", "촬영일시", "촬영장소",
            "개선 대상", "개선 내용", "파일명", "완료일", "확인자"]
    for c, h in enumerate(hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    row += 1

    # 개선 전 헤더 구분선
    write_cell(ws, row, 1, TOTAL_COLS, "▷ 개선 전 (Before)",
               font=FONT_BOLD, fill=FILL_WARN, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    before_items = [it for it in items if
                    v(it, "before_after_type", "").lower() in ("before", "개선 전", "조치 전")]
    after_items  = [it for it in items if
                    v(it, "before_after_type", "").lower() in ("after",  "개선 후", "조치 후")]
    other_items  = [it for it in items if it not in before_items and it not in after_items]

    # 개선 전이 없으면 전체를 before로
    if not before_items and not after_items:
        before_items = items[:max_rows // 2] or items
        after_items  = []

    def _ba_rows(ws, row, rows, fill_row):
        for it in rows:
            taken = v(it, "taken_at", v(it, "taken_date", ""))
            write_cell(ws, row, 1, 1, v(it, "photo_no"),                font=FONT_SMALL, fill=fill_row, align=ALIGN_CENTER)
            write_cell(ws, row, 2, 2, v(it, "description"),             font=FONT_SMALL, align=ALIGN_LEFT)
            write_cell(ws, row, 3, 3, taken,                            font=FONT_SMALL, align=ALIGN_CENTER)
            write_cell(ws, row, 4, 4, v(it, "location"),                font=FONT_SMALL, align=ALIGN_CENTER)
            write_cell(ws, row, 5, 5, v(it, "improvement_target", ""),  font=FONT_SMALL, align=ALIGN_LEFT)
            write_cell(ws, row, 6, 6, v(it, "improvement_desc", ""),    font=FONT_SMALL, align=ALIGN_LEFT)
            write_cell(ws, row, 7, 7, v(it, "file_name"),               font=FONT_SMALL, align=ALIGN_LEFT)
            write_cell(ws, row, 8, 8, v(it, "completed_date", ""),      font=FONT_SMALL, align=ALIGN_CENTER)
            write_cell(ws, row, 9, 9, v(it, "confirmer", ""),           font=FONT_SMALL, align=ALIGN_CENTER)
            ws.row_dimensions[row].height = 22
            row += 1
        return row

    row = _ba_rows(ws, row, before_items or items[:1], FILL_WARN)
    if not before_items:
        row = _empty_photo_rows(ws, row, 2, 1)

    # 개선 후 헤더 구분선
    write_cell(ws, row, 1, TOTAL_COLS, "▷ 개선 후 (After)",
               font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1
    row = _ba_rows(ws, row, after_items, FILL_HEADER)
    if not after_items:
        row = _empty_photo_rows(ws, row, 2, len(before_items or items) + 1)

    # 기타 항목 (전/후 미분류)
    if other_items:
        write_cell(ws, row, 1, TOTAL_COLS, "▷ 기타",
                   font=FONT_BOLD, fill=FILL_SECTION, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 18
        row += 1
        row = _ba_rows(ws, row, other_items, FILL_NONE)

    return row


def _render_inspection_sequence(ws, row: int, items: List[Dict], max_rows: int) -> int:
    """inspection_sequence: 공정단계·검측위치·검측내용·확인결과·확인자 포함"""
    hdrs = ["사진 번호", "사진 설명", "촬영일시", "공정 단계",
            "검측 위치", "검측 내용", "확인 결과", "파일명", "확인자"]
    for c, h in enumerate(hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    row += 1

    for it in items[:max_rows]:
        taken = v(it, "taken_at", v(it, "taken_date", ""))
        write_cell(ws, row, 1, 1, v(it, "photo_no"),            font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, v(it, "description"),         font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, taken,                        font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 4, v(it, "work_step", ""),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(it, "check_location", v(it, "location", "")), font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(it, "check_content", ""),   font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, v(it, "check_result", ""),    font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(it, "file_name"),           font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 9, 9, v(it, "confirmer", ""),       font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 20
        row += 1

    empty = max(3, max_rows - len(items))
    empty = min(empty, max_rows - len(items))
    row = _empty_photo_rows(ws, row, empty, len(items) + 1)
    return row


_LAYOUT_RENDERERS = {
    "standard":            _render_standard,
    "evidence_large":      _render_evidence_large,
    "activity_compact":    _render_activity_compact,
    "before_after":        _render_before_after,
    "inspection_sequence": _render_inspection_sequence,
}


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def build_photo_attachment_sheet(form_data: Dict[str, Any]) -> bytes:
    """
    사진대지 부대서류 Excel bytes 반환.

    layout_type 미지정 시 standard(4장/2×2) 레이아웃 사용.
    """
    layout = (v(form_data, "layout_type") or "standard").lower()
    if layout not in _LAYOUT_RENDERERS:
        layout = "standard"

    title    = v(form_data, "document_title") or _LAYOUT_TITLES.get(layout, "사진대지")
    max_rows = _LAYOUT_MAX.get(layout, 12)

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1

    # ── 제목 ──────────────────────────────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, title,
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
    row = _two_col(ws, row, "현장명",    v(form_data, "site_name"),
                             "작성 일자",  v(form_data, "doc_date") or v(form_data, "created_date"))
    row = _two_col(ws, row, "공사명",    v(form_data, "project_name"),
                             "회사명",     v(form_data, "company_name"))
    row = _two_col(ws, row, "협력업체명", v(form_data, "contractor_name"),
                             "총 사진 수", v(form_data, "total_photo_count"))
    row = _blank(ws, row, 6)

    # ── s2. 연결 문서 정보 ────────────────────────────────────────────────
    row = _section_header(ws, row, "② 연결 문서 정보  (부대서류)")
    row = _two_col(ws, row, "연결 문서 ID",   v(form_data, "parent_doc_id"),
                             "연결 문서명",     v(form_data, "parent_doc_name"))
    row = _two_col(ws, row, "연결 form_type", v(form_data, "parent_form_type"),
                             "비고",            v(form_data, "remarks"))
    row = _blank(ws, row, 6)

    # ── s3. 현장/공사 정보 ────────────────────────────────────────────────
    row = _section_header(ws, row, "③ 현장 / 공사 정보")
    row = _two_col(ws, row, "촬영 장소 (공통)", v(form_data, "location"),
                             "촬영자 (공통)",    v(form_data, "photographer"))
    row = _blank(ws, row, 6)

    # ── s4. 사진대지 유형 및 레이아웃 ────────────────────────────────────
    row = _section_header(ws, row, "④ 사진대지 유형 및 레이아웃")
    row = _two_col(ws, row, "사진대지 유형", layout,
                             "레이아웃 설명", _LAYOUT_DESC.get(layout, ""))
    row = _blank(ws, row, 6)

    # ── s5. 사진 목록 ─────────────────────────────────────────────────────
    row = _section_header(ws, row, "⑤ 사진 목록")

    raw = form_data.get("photos") or form_data.get("photo_items") or []
    items: List[Dict[str, Any]] = raw[:max_rows]

    renderer = _LAYOUT_RENDERERS[layout]
    row = renderer(ws, row, items, max_rows)
    row = _blank(ws, row, 6)

    # ── s6. 사진별 설명 (작성 안내) ──────────────────────────────────────
    row = _section_header(ws, row, "⑥ 사진 설명 작성 안내")
    guide_map = {
        "standard":
            "사진 설명: 해당 사진에서 확인 가능한 위험요인·개선조치·활동 내용을 간략히 기재.  "
            "파일명: 첨부 이미지 파일명 기입 (image_path 필드로 향후 이미지 자동 삽입 연동).  "
            "구분: 개선 전/개선 후/일반 중 해당 항목 기입.",
        "evidence_large":
            "위험요인/지적사항: 해당 사진에서 확인되는 위험요인 또는 감리 지적사항 기재.  "
            "조치내용: 지적사항 조치 내용을 구체적으로 기재.  "
            "확인자: 조치 완료를 확인한 담당자 성명.",
        "activity_compact":
            "활동명: 해당 사진이 촬영된 안전문화 활동명(캠페인명/TBM 등).  "
            "참여자: 사진에 나타난 주요 참여자 성명 또는 인원수.  "
            "활동내용: 사진으로 확인 가능한 활동 내용 요약.",
        "before_after":
            "개선 전/후 구분: before_after_type 필드에 '개선 전' 또는 '개선 후' 입력.  "
            "개선 대상: 개선 전 위험요인 또는 지적사항 요약.  "
            "개선 내용: 실시된 개선조치 내용 기재. 완료일·확인자 반드시 기재.",
        "inspection_sequence":
            "공정 단계: 해당 사진이 속하는 시공 단계 또는 검측 단계명 기재.  "
            "검측 위치: 구체적인 검측 위치(축번호·레벨·구간 등).  "
            "확인 결과: 합격/불합격/조건부합격 등 검측 결과.",
    }
    guide = guide_map.get(layout, "")
    write_cell(ws, row, 1, TOTAL_COLS, guide,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 36
    row += 1
    row = _blank(ws, row, 6)

    # ── s7. 유형별 추가 정보 ──────────────────────────────────────────────
    row = _section_header(ws, row, "⑦ 유형별 추가 정보")
    if layout == "before_after":
        write_cell(ws, row, 1, 4, "개선 전 (황색)",
                   font=FONT_BOLD, fill=FILL_WARN, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 9, "개선 후 (청색)",
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 22
        row += 1
    else:
        type_info = _LAYOUT_DESC.get(layout, "")
        write_cell(ws, row, 1, TOTAL_COLS, f"[{layout}] {type_info}",
                   font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 20
        row += 1
    row = _blank(ws, row, 6)

    # ── s8. 첨부 확인 및 확인자 서명 ─────────────────────────────────────
    row = _section_header(ws, row, "⑧ 첨부 확인 및 확인자 서명")
    roles = [
        ("작성자", v(form_data, "prepared_by"), v(form_data, "doc_date") or v(form_data, "created_date")),
        ("검토자", v(form_data, "checked_by"),  ""),
        ("확인자", v(form_data, "approved_by"), ""),
    ]
    row = _sign_row(ws, row, roles)
    row = _blank(ws, row, 6)

    # ── 하단 안내 ─────────────────────────────────────────────────────────
    notice = (
        "[photo_attachment_sheet] 본 사진대지는 핵심 안전서류에 첨부하는 부대서류입니다. "
        f"사진대지 유형: {layout} | 사진 실물 이미지는 file_name/image_path 필드로 별도 관리. "
        "document_catalog 독립 문서가 아님."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 28

    apply_a4_page_setup(ws, landscape=False)
    set_print_area_to_used_range(ws)
    ws.print_title_rows = "1:7"
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

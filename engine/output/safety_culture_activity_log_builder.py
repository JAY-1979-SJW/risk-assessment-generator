"""
안전문화 활동 기록부 — Excel 출력 모듈 (v1).

분류: PRACTICAL — 법정 별지 서식 없음.
      안전캠페인·TBM 우수활동·아차사고 발굴·안전제안·포상·협력업체 합동점검 등
      안전문화 활동 전반을 월간/현장 단위로 누적 기록·관리하는 실무 보조서식.
      SP-001(방침·목표 게시문), SP-003(우수사례 보고서)과 역할 분리.
      중대재해처벌법 시행령 제4조(안전보건관리체계 구축) 이행 근거 보조자료로 활용.

form_type: safety_culture_activity_log
함수명:    build_safety_culture_activity_log(form_data)

Required form_data keys:
    site_name       str  현장명
    record_period   str  기록 기간 (예: 2026년 4월)

Optional form_data keys:
    project_name          str   공사명
    company_name          str   회사명
    site_manager          str   현장소장
    record_no             str   기록부 번호
    prepared_by           str   작성자
    reviewed_by           str   검토자
    approved_by           str   승인자
    sign_date             str   서명 일자
    total_activity_count  str   총 활동 횟수
    total_participant     str   총 참여 인원
    activity_summary      str   활동 요약
    main_activity_title   str   주요 활동명
    main_activity_date    str   주요 활동 일자
    main_activity_type    str   주요 활동 유형
    main_activity_location str  주요 활동 장소
    main_activity_desc    str   주요 활동 내용
    main_activity_person  str   주요 활동 담당자
    main_participant_list str   주요 활동 참여자 명단
    main_participant_count str  주요 활동 참여 인원
    suggestion_count      str   근로자 제안 건수
    suggestion_adopted    str   채택 건수
    suggestion_summary    str   주요 제안 내용
    improvement_summary   str   개선조치 요약
    improvement_status    str   이행 상태
    photo_count           str   사진/증빙 첨부 수
    effect_quantitative   str   정량적 효과
    effect_qualitative    str   정성적 효과
    next_plan_period      str   다음 활동 기간
    next_plan_content     str   다음 활동 계획 내용
    next_plan_person      str   다음 활동 담당자
    activity_items        list[dict]  활동 목록 (repeat)
        각 항목: act_no, act_date, act_type, act_name, act_location,
                 participant_count, responsible, photo_attached, remarks
    improvement_items     list[dict]  개선조치 목록 (extra_list)
        각 항목: impr_no, source_activity, issue_content, action, person, due_date, status
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

DOC_ID     = "SP-004"
FORM_TYPE  = "safety_culture_activity_log"
SHEET_NAME    = "안전문화활동기록부"
SHEET_HEADING = "안전문화 활동 기록부"
SHEET_SUBTITLE = (
    "「중대재해처벌법 시행령」 제4조(안전보건관리체계 구축) 이행 보조서식  "
    f"[{DOC_ID}]"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 6, 2: 20, 3: 14, 4: 14, 5: 12, 6: 12, 7: 10, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_ACTIVITY_ROWS = 12
MAX_IMPROVEMENT_ROWS = 8

# ---------------------------------------------------------------------------
# 활동 유형 기본값
# ---------------------------------------------------------------------------
DEFAULT_ACTIVITY_TYPES = [
    "안전캠페인",
    "TBM 우수활동",
    "아차사고 발굴",
    "안전제안",
    "보호구 착용 캠페인",
    "추락예방 캠페인",
    "정리정돈 활동",
    "안전보건 교육·홍보",
    "협력업체 합동점검",
    "우수근로자 포상",
]

DEFAULT_ACTIVITY_ITEMS = [
    {
        "act_no": "1", "act_date": "", "act_type": "안전캠페인",
        "act_name": "추락예방 안전캠페인", "act_location": "현장 전체",
        "participant_count": "", "responsible": "", "photo_attached": "○", "remarks": "",
    },
    {
        "act_no": "2", "act_date": "", "act_type": "아차사고 발굴",
        "act_name": "아차사고 발굴 활동", "act_location": "",
        "participant_count": "", "responsible": "", "photo_attached": "○", "remarks": "",
    },
    {
        "act_no": "3", "act_date": "", "act_type": "안전제안",
        "act_name": "근로자 안전제안 수렴", "act_location": "",
        "participant_count": "", "responsible": "", "photo_attached": "—", "remarks": "",
    },
]


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _two_col(ws, row: int,
             label1: str, val1: Any,
             label2: str, val2: Any,
             height: float = 20) -> int:
    write_cell(ws, row, _L1, _L1, label1, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, _V1S, _V1E, val1,  font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, _L2, _L2, label2,  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, _V2S, _V2E, val2,  font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height
    return row + 1


def _full_row(ws, row: int, label: str, val: Any, height: float = 20) -> int:
    write_cell(ws, row, _L1, _L1, label, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, _V1S, TOTAL_COLS, val, font=FONT_DEFAULT, align=ALIGN_LEFT)
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

def build_safety_culture_activity_log(form_data: Dict[str, Any]) -> bytes:
    """안전문화 활동 기록부 Excel bytes 반환."""
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

    # ── s1. 기록부 기본정보 ───────────────────────────────────────────────
    row = _section_header(ws, row, "① 기록부 기본정보")
    row = _two_col(ws, row, "현장명",    v(form_data, "site_name"),
                             "기록부 번호", v(form_data, "record_no"))
    row = _two_col(ws, row, "공사명",    v(form_data, "project_name"),
                             "회사명",     v(form_data, "company_name"))
    row = _two_col(ws, row, "기록 기간", v(form_data, "record_period"),
                             "현장소장",   v(form_data, "site_manager"))
    row = _blank(ws, row, 6)

    # ── s2. 활동 기간 및 대상 현장 ───────────────────────────────────────
    row = _section_header(ws, row, "② 활동 기간 및 대상 현장")

    # 총괄 수치
    write_cell(ws, row, 1, 1, "구분",         font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 2, 4, "내용",         font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 5, "구분",         font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 8, "내용",         font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    row = _two_col(ws, row,
                   "총 활동 횟수", v(form_data, "total_activity_count"),
                   "총 참여 인원", v(form_data, "total_participant"))
    row = _blank(ws, row, 6)

    # ── s3. 안전문화 활동 요약 ────────────────────────────────────────────
    row = _section_header(ws, row, "③ 안전문화 활동 요약")
    row = _full_row(ws, row, "활동 요약", v(form_data, "activity_summary"), height=36)
    row = _blank(ws, row, 6)

    # ── s4. 활동 목록 ─────────────────────────────────────────────────────
    row = _section_header(ws, row, "④ 활동 목록")

    # 헤더
    hdrs = ["No.", "활동일자", "활동유형", "활동명", "장소", "참여인원", "담당자", "사진"]
    for c, h in enumerate(hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    raw_items: List[Dict[str, Any]] = form_data.get("activity_items") or []
    items = raw_items if raw_items else DEFAULT_ACTIVITY_ITEMS
    items = items[:MAX_ACTIVITY_ROWS]

    for it in items:
        write_cell(ws, row, 1, 1, v(it, "act_no"),           font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, v(it, "act_date"),         font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 3, v(it, "act_type"),         font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 4, v(it, "act_name"),         font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 5, v(it, "act_location"),     font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(it, "participant_count"),font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(it, "responsible"),      font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(it, "photo_attached"),   font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 18
        row += 1

    # 빈 행 여백 (최소 3행)
    for _ in range(max(0, 3 - len(items))):
        for c in range(1, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 18
        row += 1

    row = _blank(ws, row, 6)

    # ── s5. 주요 활동 상세 ────────────────────────────────────────────────
    row = _section_header(ws, row, "⑤ 주요 활동 상세")
    row = _two_col(ws, row, "활동명",    v(form_data, "main_activity_title"),
                             "활동 일자", v(form_data, "main_activity_date"))
    row = _two_col(ws, row, "활동 유형", v(form_data, "main_activity_type"),
                             "활동 장소", v(form_data, "main_activity_location"))
    row = _full_row(ws, row, "활동 내용", v(form_data, "main_activity_desc"), height=36)
    row = _two_col(ws, row, "담당자",    v(form_data, "main_activity_person"),
                             "참여 인원", v(form_data, "main_participant_count"))
    row = _full_row(ws, row, "참여자 명단", v(form_data, "main_participant_list"), height=24)
    row = _blank(ws, row, 6)

    # ── s6. 참여자 및 담당자 ──────────────────────────────────────────────
    row = _section_header(ws, row, "⑥ 참여자 및 담당자")
    row = _two_col(ws, row, "작성자",  v(form_data, "prepared_by"),
                             "검토자",  v(form_data, "reviewed_by"))
    row = _two_col(ws, row, "승인자",  v(form_data, "approved_by"),
                             "서명 일자", v(form_data, "sign_date"))
    row = _blank(ws, row, 6)

    # ── s7. 근로자 제안 및 의견 ───────────────────────────────────────────
    row = _section_header(ws, row, "⑦ 근로자 제안 및 의견")
    row = _two_col(ws, row, "제안 건수", v(form_data, "suggestion_count"),
                             "채택 건수", v(form_data, "suggestion_adopted"))
    row = _full_row(ws, row, "주요 제안 내용", v(form_data, "suggestion_summary"), height=36)
    row = _blank(ws, row, 6)

    # ── s8. 개선조치 및 후속관리 ──────────────────────────────────────────
    row = _section_header(ws, row, "⑧ 개선조치 및 후속관리")

    hdrs8 = ["No.", "발굴 활동", "문제점/위험요인", "개선조치", "담당자", "완료예정일", "이행상태", "비고"]
    for c, h in enumerate(hdrs8, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    raw_impr: List[Dict[str, Any]] = form_data.get("improvement_items") or []
    raw_impr = raw_impr[:MAX_IMPROVEMENT_ROWS]

    for it in raw_impr:
        write_cell(ws, row, 1, 1, v(it, "impr_no"),        font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, v(it, "source_activity"),font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 3, v(it, "issue_content"),  font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 4, v(it, "action"),         font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 5, v(it, "person"),         font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(it, "due_date"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(it, "status"),         font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(it, "remarks", ""),    font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 18
        row += 1

    for _ in range(max(0, 3 - len(raw_impr))):
        for c in range(1, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 18
        row += 1

    row = _blank(ws, row, 6)

    # ── s9. 사진/증빙 목록 ────────────────────────────────────────────────
    row = _section_header(ws, row, "⑨ 사진/증빙 목록")
    row = _two_col(ws, row, "첨부 사진 수", v(form_data, "photo_count"),
                             "비고", "활동 사진은 별도 사진대지 첨부")

    # 사진 목록 헤더
    ph_hdrs = ["No.", "활동명", "촬영일자", "촬영내용", "첨부여부", "보관위치", "비고", ""]
    for c, h in enumerate(ph_hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    for i in range(1, 5):
        write_cell(ws, row, 1, 1, str(i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 18
        row += 1

    row = _blank(ws, row, 6)

    # ── s10. 활동 효과 및 평가 ────────────────────────────────────────────
    row = _section_header(ws, row, "⑩ 활동 효과 및 평가")
    row = _full_row(ws, row, "정량적 효과", v(form_data, "effect_quantitative"), height=28)
    row = _full_row(ws, row, "정성적 효과", v(form_data, "effect_qualitative"), height=28)
    row = _blank(ws, row, 6)

    # ── s11. 다음 활동 계획 ───────────────────────────────────────────────
    row = _section_header(ws, row, "⑪ 다음 활동 계획")
    row = _two_col(ws, row, "계획 기간", v(form_data, "next_plan_period"),
                             "담당자",    v(form_data, "next_plan_person"))
    row = _full_row(ws, row, "계획 내용", v(form_data, "next_plan_content"), height=36)
    row = _blank(ws, row, 6)

    # ── s12. 작성자/검토자/승인자 확인 ───────────────────────────────────
    row = _section_header(ws, row, "⑫ 작성자 / 검토자 / 승인자 확인")

    # 결재 라인
    write_cell(ws, row, 1, 2, "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 4, "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 6, "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "일자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    for role, key in [("작성자", "prepared_by"), ("검토자", "reviewed_by"), ("승인자", "approved_by")]:
        write_cell(ws, row, 1, 2, role,                    font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 4, v(form_data, key),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 6, "",                      font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 8, v(form_data, "sign_date"), font=FONT_DEFAULT, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 24
        row += 1

    row = _blank(ws, row, 6)

    # ── 하단 안내문 ───────────────────────────────────────────────────────
    notice = (
        f"[{DOC_ID}] 본 기록부는 안전문화 활동 전반(캠페인·TBM·제안·포상·합동점검 등)의 "
        "누적 현황을 월간/현장 단위로 관리하는 실무 보조서식입니다. "
        "SP-001(방침·목표 게시문), SP-003(우수사례 보고서)과 역할이 분리됩니다."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 28

    # ── bytes 반환 ────────────────────────────────────────────────────────
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

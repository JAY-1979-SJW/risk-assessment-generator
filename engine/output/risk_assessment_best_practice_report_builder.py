"""
위험성평가 우수 사례 보고서 — Excel 출력 모듈 (v1).

분류: OPTIONAL — 법정 별지 서식 없음. 실무 선택 보조서식.
      고용노동부 위험성평가 우수 사업장 인정 제도 연계, 개선사례 기록·공유·확산용.

역할 분리:
  RA-001 위험성평가표 — 위험성평가 실시·결과 기록
  RA-005 위험성평가 실시 규정 — 절차·규정 문서
  RA-006 결과 근로자 공지문 — 결과 공지
  SP-003 (본 서식) — 우수 개선사례 기록·공유·확산 (선택 서류)

form_type: risk_assessment_best_practice_report
함수명:    build_risk_assessment_best_practice_report(form_data)

Required form_data keys:
    site_name       str  현장명
    report_date     str  보고서 작성일
    case_title      str  우수 사례 제목

Optional form_data keys:
    project_name          str   공사명
    company_name          str   회사명
    report_no             str   보고서 번호
    work_type             str   작업 유형/공종
    work_location         str   대상 작업 장소
    work_description      str   대상 작업 내용
    assessment_date       str   위험성평가 실시일
    assessor              str   위험성평가 실시자
    case_background       str   사례 발굴 배경
    before_hazard         str   개선 전 위험요인 설명
    before_likelihood     str   개선 전 발생 가능성
    before_severity       str   개선 전 중대성
    before_risk_level     str   개선 전 위험성 수준
    measure_content       str   개선대책 내용
    measure_type          str   개선대책 유형 (제거/대체/공학적/관리적/보호구)
    measure_cost          str   개선 비용
    measure_period        str   개선 실시 기간
    measure_responsible   str   개선 담당자
    after_likelihood      str   개선 후 발생 가능성
    after_severity        str   개선 후 중대성
    after_risk_level      str   개선 후 위험성 수준
    effect_qualitative    str   정성적 효과 설명
    effect_quantitative   str   정량적 효과 (사고감소율, 비용절감 등)
    effect_worker_feedback str  근로자 반응/의견
    worker_participation  str   근로자 참여 방법·인원
    worker_opinion        str   근로자 의견 요약
    spread_feasibility    str   타 현장 확산 가능성 평가
    spread_plan           str   확산 계획
    maintenance_plan      str   향후 유지관리 계획
    maintenance_cycle     str   점검 주기
    author                str   작성자
    reviewer              str   검토자
    approver              str   승인자
    sign_date             str   서명 일자
    photo_items           list[dict]  photo_no, description, location, attached
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

DOC_ID    = "SP-003"
FORM_TYPE = "risk_assessment_best_practice_report"
SHEET_NAME    = "위험성평가우수사례보고서"
SHEET_HEADING = "위험성평가 우수 사례 보고서"
SHEET_SUBTITLE = (
    "고용노동부 위험성평가 우수 사업장 인정 제도 연계 — "
    f"위험성평가 우수 개선사례 기록·공유·확산용 실무 보조서식  [{DOC_ID}]"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 16, 3: 12, 4: 12, 5: 12, 6: 12, 7: 10, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_PHOTO_ROWS = 8
MIN_PHOTO_ROWS = 4

NOTICE_OPTIONAL = (
    "본 서식은 관계 기관 공식 법정서식이 아닙니다. "
    "위험성평가 우수사례 기록·공유를 위한 선택(optional) 실무 보조서식이며, "
    "고용노동부 우수 사업장 인정 신청 또는 사내 확산 목적으로 활용한다."
)
NOTICE_COMPARE = (
    "개선 전/후 위험성 비교는 RA-001 위험성평가표 결과와 연계하여 기재한다."
)

RISK_LEVEL_OPTIONS = "높음 / 중간 / 낮음  (또는 현장 기준 3~5등급 체계 적용)"

# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _lv(ws, row: int, label: str, value: Any,
        lc: int, vs: int, ve: int, height: float = 20) -> None:
    write_cell(ws, row, lc, lc, label,
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, vs, ve, value,
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height


def _sec(ws, row: int, title: str, fill=None) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, title,
               font=FONT_BOLD, fill=fill or FILL_SECTION, align=ALIGN_CENTER, height=22)
    return row + 1


def _notice(ws, row: int, text: str) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, text,
               font=FONT_NOTICE, fill=FILL_NOTICE, align=ALIGN_LEFT, height=24)
    return row + 1


def _full_row(ws, row: int, label: str, value: Any, height: float = 36) -> int:
    write_cell(ws, row, 1, 1, label,
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=height)
    write_cell(ws, row, 2, TOTAL_COLS, value,
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height
    return row + 1


def _compare_row(ws, row: int,
                 before_label: str, before_val: Any,
                 after_label: str,  after_val:  Any,
                 height: float = 22) -> int:
    """개선 전/후 2열 비교 행."""
    write_cell(ws, row, _L1, _L1, before_label, font=FONT_BOLD, fill=FILL_WARN,   align=ALIGN_LABEL)
    write_cell(ws, row, _V1S, _V1E, before_val, font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, _L2, _L2, after_label,  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_LABEL)
    write_cell(ws, row, _V2S, _V2E, after_val,  font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height
    return row + 1


# ---------------------------------------------------------------------------
# 섹션 렌더러
# ---------------------------------------------------------------------------

def _s_title(ws, row: int) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_SECTION, align=ALIGN_CENTER, height=32)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, height=18)
    return row + 1


def _s1_basic(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "1. 보고서 기본정보")
    _lv(ws, row, "현장명",      v(d, "site_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",      v(d, "project_name"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "보고서 번호", v(d, "report_no"),    _L1, _V1S, _V1E)
    _lv(ws, row, "작성 일자",   v(d, "report_date"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "회사명",      v(d, "company_name"), _L1, _V1S, _V1E)
    _lv(ws, row, "평가 실시일", v(d, "assessment_date"), _L2, _V2S, _V2E)
    return row + 1


def _s2_overview(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "2. 우수 사례 개요")
    row = _full_row(ws, row, "사례 제목",   v(d, "case_title"),      height=28)
    row = _full_row(ws, row, "발굴 배경",   v(d, "case_background"), height=40)
    _lv(ws, row, "위험성평가 실시자", v(d, "assessor"), _L1, 2, TOTAL_COLS)
    return row + 1


def _s3_target_work(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "3. 대상 작업/공정")
    _lv(ws, row, "작업 유형/공종", v(d, "work_type"),     _L1, _V1S, _V1E)
    _lv(ws, row, "작업 장소",      v(d, "work_location"), _L2, _V2S, _V2E)
    row += 1
    row = _full_row(ws, row, "작업 내용",   v(d, "work_description"), height=40)
    return row


def _s4_before_hazard(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "4. 개선 전 위험요인")
    row = _full_row(ws, row, "개선 전 위험요인", v(d, "before_hazard"), height=48)
    _lv(ws, row, "발생 가능성",   v(d, "before_likelihood") or RISK_LEVEL_OPTIONS, _L1, _V1S, _V1E)
    _lv(ws, row, "중대성",        v(d, "before_severity")   or RISK_LEVEL_OPTIONS, _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "개선 전 위험성 수준",
        v(d, "before_risk_level") or "높음 / 중간 / 낮음",
        _L1, 2, TOTAL_COLS, height=24)
    return row + 1


def _s5_ra_result(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "5. 위험성평가 결과")
    row = _notice(ws, row, NOTICE_COMPARE)
    row = _full_row(ws, row, "위험성평가 결과 요약",
                   v(d, "ra_result_summary") or "(RA-001 위험성평가표 결과 기재)", height=40)
    return row


def _s6_measure(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "6. 개선대책 및 실행 내용")
    row = _full_row(ws, row, "개선대책 내용", v(d, "measure_content"), height=52)
    _lv(ws, row, "개선대책 유형",
        v(d, "measure_type") or "□ 제거  □ 대체  □ 공학적  □ 관리적  □ 보호구",
        _L1, _V1S, _V1E, height=24)
    _lv(ws, row, "개선 담당자",   v(d, "measure_responsible"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "개선 실시 기간", v(d, "measure_period"), _L1, _V1S, _V1E)
    _lv(ws, row, "개선 비용",      v(d, "measure_cost"),   _L2, _V2S, _V2E)
    return row + 1


def _s7_after_risk(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "7. 개선 후 위험성 변화  (개선 전/후 비교)")
    # 헤더 비교
    write_cell(ws, row, 1, 4, "개선 전",
               font=FONT_BOLD, fill=FILL_WARN,   align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 5, 8, "개선 후",
               font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1
    row = _compare_row(ws, row,
        "발생 가능성", v(d, "before_likelihood") or "",
        "발생 가능성", v(d, "after_likelihood")  or "")
    row = _compare_row(ws, row,
        "중대성",      v(d, "before_severity")   or "",
        "중대성",      v(d, "after_severity")    or "")
    row = _compare_row(ws, row,
        "위험성 수준", v(d, "before_risk_level") or "",
        "위험성 수준", v(d, "after_risk_level")  or "", height=28)
    return row


def _s8_effect(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "8. 효과 분석")
    row = _full_row(ws, row, "정성적 효과",  v(d, "effect_qualitative"),   height=40)
    row = _full_row(ws, row, "정량적 효과",  v(d, "effect_quantitative")
                   or "(사고 감소율, 비용 절감, 작업시간 단축 등 수치 기재)", height=40)
    row = _full_row(ws, row, "근로자 반응/의견", v(d, "effect_worker_feedback"), height=32)
    return row


def _s9_photos(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "9. 사진/증빙 목록  (사진대지는 별첨)")
    spans = [(1, 1), (2, 4), (5, 6), (7, 7), (8, 8)]
    texts = ["번호", "사진 설명", "촬영 위치", "첨부", "비고"]
    for (cs, ce), hdr in zip(spans, texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    photos = d.get("photo_items") or []
    display = max(MIN_PHOTO_ROWS, len(photos))
    display = min(display, MAX_PHOTO_ROWS)
    for i in range(display):
        item = photos[i] if i < len(photos) else {}
        write_cell(ws, row, 1, 1, i + 1,                font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 4, v(item, "description"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 6, v(item, "location"),    font=FONT_SMALL,   align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, v(item, "attached") or "□", font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, "",                    font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _s10_worker(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "10. 근로자 참여 및 의견")
    row = _full_row(ws, row, "근로자 참여 방법·인원", v(d, "worker_participation"), height=32)
    row = _full_row(ws, row, "근로자 의견 요약",       v(d, "worker_opinion"),       height=36)
    return row


def _s11_spread(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "11. 타 현장 확산 가능성")
    row = _full_row(ws, row, "확산 가능성 평가",
                   v(d, "spread_feasibility") or "□ 높음  □ 보통  □ 낮음  — 사유: ",
                   height=28)
    row = _full_row(ws, row, "확산 계획",
                   v(d, "spread_plan") or "(타 현장 공유, 안전문화 활동 활용, 교육 자료화 등)",
                   height=36)
    return row


def _s12_maintenance(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "12. 향후 유지관리 계획")
    row = _full_row(ws, row, "유지관리 계획", v(d, "maintenance_plan"), height=40)
    _lv(ws, row, "점검 주기", v(d, "maintenance_cycle") or "□ 월간  □ 분기  □ 반기  □ 기타",
        _L1, 2, TOTAL_COLS)
    return row + 1


def _s13_sign(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "13. 작성자 / 검토자 / 승인자 확인")
    _lv(ws, row, "작성자", v(d, "author"),   _L1, _V1S, _V1E, height=32)
    _lv(ws, row, "검토자", v(d, "reviewer"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "승인자",  v(d, "approver"),   _L1, _V1S, _V1E, height=32)
    _lv(ws, row, "서명 일자", v(d, "sign_date"), _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 8, NOTICE_OPTIONAL,
               font=FONT_NOTICE, fill=FILL_NOTICE, align=ALIGN_LEFT, height=28)
    return row + 1


# ---------------------------------------------------------------------------
# 메인 빌더
# ---------------------------------------------------------------------------

def build_risk_assessment_best_practice_report(form_data: Dict[str, Any]) -> bytes:
    """form_data dict를 받아 위험성평가 우수 사례 보고서 xlsx 바이너리를 반환한다."""
    d: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _s_title(ws, row)
    row = _s1_basic(ws, row, d)
    row = _s2_overview(ws, row, d)
    row = _s3_target_work(ws, row, d)
    row = _s4_before_hazard(ws, row, d)
    row = _s5_ra_result(ws, row, d)
    row = _s6_measure(ws, row, d)
    row = _s7_after_risk(ws, row, d)
    row = _s8_effect(ws, row, d)
    row = _s9_photos(ws, row, d)
    row = _s10_worker(ws, row, d)
    row = _s11_spread(ws, row, d)
    row = _s12_maintenance(ws, row, d)
    _s13_sign(ws, row, d)

    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

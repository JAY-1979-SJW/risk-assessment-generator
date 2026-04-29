"""
협력업체 안전보건 수준 평가표 — Excel 출력 모듈 (v1).

법적 근거:
  - 산업안전보건법 제63조(도급인의 안전보건 조치 의무)
  - 중대재해처벌법 시행령 제4조 제9호(수급인 안전보건관리 수준 평가·개선)
분류: PRACTICAL — 법정 별지 서식 없음. 도급·협력업체 안전보건 수준 정량/정성 평가 실무서식.
      CM-001(서류 확인)/CM-002(협의체 협의)와 역할 분리.

form_type: subcontractor_safety_evaluation
함수명:    build_subcontractor_safety_evaluation(form_data)

Required form_data keys:
    eval_site_name   str  평가 현장명
    eval_date        str  평가 일자
    contractor_name  str  협력업체명

Optional form_data keys:
    project_name         str   공사명
    eval_no              str   평가 번호
    eval_period          str   평가 대상 기간
    contractor_ceo       str   협력업체 대표자
    contractor_biz_no    str   사업자등록번호
    contractor_contact   str   협력업체 담당자/연락처
    work_scope           str   평가 대상 공사·작업 범위
    contract_amount      str   계약금액
    worker_count         str   투입 근로자 수
    evaluator            str   평가자
    evaluator_position   str   평가자 직책
    approval_person      str   승인자
    mgmt_items           list[dict]  name, score_max, score_got, result, note  (5절: 안전보건관리 체계)
    edu_items            list[dict]  동일 구조  (6절: 안전교육·근로자 관리)
    ra_items             list[dict]  동일 구조  (7절: 위험성평가·작업계획)
    ppe_items            list[dict]  동일 구조  (8절: 보호구·장비·작업환경)
    accident_items       list[dict]  동일 구조  (9절: 사고·비상대응·재해 이력)
    legal_items          list[dict]  동일 구조  (10절: 서류 제출·법정 의무 이행)
    improvement_items    list[dict]  category, issue, action, due_date, responsible  (12절: 개선요구사항)
    reassess_date        str   재평가 예정일
    reassess_scope       str   재평가 범위
    overall_remarks      str   종합 의견
    contractor_confirm   str   협력업체 확인자 성명
    contractor_sign_date str   협력업체 확인 일자
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    ALIGN_CENTER, ALIGN_LABEL, ALIGN_LEFT,
    FILL_HEADER, FILL_LABEL, FILL_NONE, FILL_NOTICE, FILL_SECTION, FILL_WARN,
    FONT_BOLD, FONT_DEFAULT, FONT_NOTICE, FONT_SMALL, FONT_SUBTITLE, FONT_TITLE,
    apply_col_widths, v, write_cell,
)

DOC_ID    = "SP-002"
FORM_TYPE = "subcontractor_safety_evaluation"
SHEET_NAME    = "협력업체안전보건수준평가표"
SHEET_HEADING = "협력업체 안전보건 수준 평가표"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제63조 및 「중대재해처벌법 시행령」 제4조 제9호에 따른 "
    f"협력업체 안전보건관리 수준 평가 실무서식  [{DOC_ID}]"
)

TOTAL_COLS = 10
_COL_WIDTHS: Dict[int, float] = {
    1: 5, 2: 20, 3: 6, 4: 6, 5: 8, 6: 16, 7: 12, 8: 10, 9: 10, 10: 10,
}

_L1, _V1S, _V1E = 1, 2,  5
_L2, _V2S, _V2E = 6, 7, 10

MAX_IMPR_ROWS = 8
MIN_IMPR_ROWS = 4

# ---------------------------------------------------------------------------
# 등급 기준
# ---------------------------------------------------------------------------

GRADE_CRITERIA = "A: 90점 이상 / B: 75~89점 / C: 60~74점 / D: 59점 이하"
NOTICE_GRADE = (
    "C등급(60~74점) 이하 또는 단일 항목 0점 취득 시 개선요구사항 작성 필수. "
    "D등급(59점 이하)은 작업투입 제한 및 즉시 시정조치 대상."
)
NOTICE_LEGAL = (
    "본 서식은 관계 기관 공식 법정서식이 아닙니다. "
    "산업안전보건법 제63조·중대재해처벌법 시행령 제4조 기반 실무 평가 보조서식이며, "
    "현장 발주처·원청 기준에 따라 보완 적용한다."
)

# ---------------------------------------------------------------------------
# 평가 항목 기본값 (form_data 없을 때 사용)
# ---------------------------------------------------------------------------

DEFAULT_MGMT_ITEMS = [
    {"name": "안전보건관리자(담당자) 선임 여부",        "score_max": 5, "score_got": "", "result": "", "note": ""},
    {"name": "안전보건방침·목표 수립 및 게시",          "score_max": 4, "score_got": "", "result": "", "note": ""},
    {"name": "안전보건교육 책임자 지정",                "score_max": 3, "score_got": "", "result": "", "note": ""},
    {"name": "안전점검·자체 순찰 계획 수립",            "score_max": 4, "score_got": "", "result": "", "note": ""},
    {"name": "협력업체 안전관리 조직도 비치",           "score_max": 4, "score_got": "", "result": "", "note": ""},
]

DEFAULT_EDU_ITEMS = [
    {"name": "채용 시 안전보건교육 실시 (8시간)",       "score_max": 5, "score_got": "", "result": "", "note": ""},
    {"name": "정기 안전보건교육 실시 (매월)",           "score_max": 5, "score_got": "", "result": "", "note": ""},
    {"name": "특별 안전보건교육 실시 (해당 작업)",      "score_max": 5, "score_got": "", "result": "", "note": ""},
    {"name": "외국인 근로자 모국어 교육 실시",          "score_max": 5, "score_got": "", "result": "", "note": ""},
]

DEFAULT_RA_ITEMS = [
    {"name": "위험성평가 실시 (최근 1년)",              "score_max": 8, "score_got": "", "result": "", "note": ""},
    {"name": "작업계획서 작성·준수",                   "score_max": 6, "score_got": "", "result": "", "note": ""},
    {"name": "TBM(작업 전 안전점검) 실시",             "score_max": 6, "score_got": "", "result": "", "note": ""},
]

DEFAULT_PPE_ITEMS = [
    {"name": "보호구 지급·착용 관리",                  "score_max": 6, "score_got": "", "result": "", "note": ""},
    {"name": "건설장비·기계·공구 안전 점검",           "score_max": 7, "score_got": "", "result": "", "note": ""},
    {"name": "작업환경 측정·유해인자 관리",            "score_max": 7, "score_got": "", "result": "", "note": ""},
]

DEFAULT_ACCIDENT_ITEMS = [
    {"name": "최근 3년 재해 이력 (무사고 가점)",       "score_max": 5, "score_got": "", "result": "", "note": ""},
    {"name": "비상대응 계획 수립·훈련 실시",           "score_max": 5, "score_got": "", "result": "", "note": ""},
]

DEFAULT_LEGAL_ITEMS = [
    {"name": "법정 서류 제출 적시성",                  "score_max": 5, "score_got": "", "result": "", "note": ""},
    {"name": "법정 안전보건교육 이수 관리",             "score_max": 5, "score_got": "", "result": "", "note": ""},
]

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
               font=FONT_NOTICE, fill=FILL_NOTICE, align=ALIGN_LEFT, height=28)
    return row + 1


def _eval_table_header(ws, row: int) -> int:
    """평가 항목 테이블 공통 헤더."""
    spans = [(1, 1), (2, 6), (7, 7), (8, 8), (9, 9), (10, 10)]
    texts = ["번호", "평가 항목", "배점", "득점", "결과", "비고"]
    for (cs, ce), hdr in zip(spans, texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    return row + 1


def _eval_table_rows(ws, row: int, items: List[Dict[str, Any]],
                     defaults: List[Dict[str, Any]]) -> int:
    """평가 항목 행 렌더링. items가 없으면 defaults 사용."""
    src = items if items else defaults
    for i, item in enumerate(src):
        write_cell(ws, row, 1, 1, i + 1,                    font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 6, v(item, "name"),           font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, v(item, "score_max"),      font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "score_got"),      font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 9, 9, v(item, "result"),         font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 10, 10, v(item, "note"),         font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    # 소계 행
    max_total = sum(item.get("score_max", 0) for item in src if isinstance(item.get("score_max"), int))
    got_total_vals = [item.get("score_got") for item in src]
    got_display = ""
    if all(isinstance(g, (int, float)) for g in got_total_vals if g != ""):
        nums = [g for g in got_total_vals if g != ""]
        got_display = str(sum(nums)) if nums else ""
    write_cell(ws, row, 1, 6, "소  계",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 7, 7, max_total or "",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 8, got_display,       font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 9, 9, "",                font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 10, 10, "",              font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    return row + 1


# ---------------------------------------------------------------------------
# 섹션 렌더러
# ---------------------------------------------------------------------------

def _s_title(ws, row: int) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_SECTION, align=ALIGN_CENTER, height=30)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, height=18)
    return row + 1


def _s1_eval_basic(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "1. 평가 기본정보")
    _lv(ws, row, "평가 현장명", v(d, "eval_site_name"), _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",      v(d, "project_name"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "평가 번호",   v(d, "eval_no"),         _L1, _V1S, _V1E)
    _lv(ws, row, "평가 일자",   v(d, "eval_date"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "평가 대상 기간", v(d, "eval_period"),  _L1, _V1S, _V1E)
    _lv(ws, row, "평가자 직책",  v(d, "evaluator_position"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "평가자",      v(d, "evaluator"),       _L1, _V1S, _V1E)
    _lv(ws, row, "승인자",      v(d, "approval_person"), _L2, _V2S, _V2E)
    return row + 1


def _s2_contractor(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "2. 협력업체 기본정보")
    _lv(ws, row, "협력업체명",    v(d, "contractor_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "대표자",        v(d, "contractor_ceo"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "사업자등록번호", v(d, "contractor_biz_no"), _L1, _V1S, _V1E)
    _lv(ws, row, "담당자/연락처", v(d, "contractor_contact"), _L2, _V2S, _V2E)
    return row + 1


def _s3_scope(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "3. 평가 대상 공사/작업 범위")
    write_cell(ws, row, 1, 1, "작업 범위",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=36)
    write_cell(ws, row, 2, TOTAL_COLS, v(d, "work_scope"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 36
    row += 1
    _lv(ws, row, "계약금액",      v(d, "contract_amount"), _L1, _V1S, _V1E)
    _lv(ws, row, "투입 근로자 수", v(d, "worker_count"),    _L2, _V2S, _V2E)
    return row + 1


def _s4_criteria(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "4. 평가 기준 및 등급")
    row = _notice(ws, row, NOTICE_GRADE)
    write_cell(ws, row, 1, 2, "등급 기준",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=24)
    write_cell(ws, row, 3, TOTAL_COLS, GRADE_CRITERIA,
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1
    # 결과 코드 설명
    write_cell(ws, row, 1, 2, "결과 코드",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 3, TOTAL_COLS,
               "○: 적합 (배점 100%)  △: 보완 필요 (배점 50%)  ✕: 부적합 (0점)",
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _s5_mgmt(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "5. 안전보건관리 체계 평가  (배점: 20점)")
    row = _eval_table_header(ws, row)
    items = d.get("mgmt_items") or []
    row = _eval_table_rows(ws, row, items, DEFAULT_MGMT_ITEMS)
    return row


def _s6_edu(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "6. 안전교육 및 근로자 관리 평가  (배점: 20점)")
    row = _eval_table_header(ws, row)
    items = d.get("edu_items") or []
    row = _eval_table_rows(ws, row, items, DEFAULT_EDU_ITEMS)
    return row


def _s7_ra(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "7. 위험성평가 및 작업계획 평가  (배점: 20점)")
    row = _eval_table_header(ws, row)
    items = d.get("ra_items") or []
    row = _eval_table_rows(ws, row, items, DEFAULT_RA_ITEMS)
    return row


def _s8_ppe(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "8. 보호구·장비·작업환경 관리 평가  (배점: 20점)")
    row = _eval_table_header(ws, row)
    items = d.get("ppe_items") or []
    row = _eval_table_rows(ws, row, items, DEFAULT_PPE_ITEMS)
    return row


def _s9_accident(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "9. 사고·비상대응 및 재해 이력 평가  (배점: 10점)")
    row = _eval_table_header(ws, row)
    items = d.get("accident_items") or []
    row = _eval_table_rows(ws, row, items, DEFAULT_ACCIDENT_ITEMS)
    return row


def _s10_legal(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "10. 서류 제출 및 법정 의무 이행 평가  (배점: 10점)")
    row = _eval_table_header(ws, row)
    items = d.get("legal_items") or []
    row = _eval_table_rows(ws, row, items, DEFAULT_LEGAL_ITEMS)
    return row


def _s11_total(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "11. 종합 점수 및 등급", fill=FILL_HEADER)
    spans = [(1, 4), (5, 6), (7, 7), (8, 8), (9, 10)]
    texts = ["평가 영역", "배점", "득점", "등급", "비고"]
    for (cs, ce), hdr in zip(spans, texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    area_rows = [
        ("안전보건관리 체계",         20),
        ("안전교육 및 근로자 관리",    20),
        ("위험성평가 및 작업계획",     20),
        ("보호구·장비·작업환경",      20),
        ("사고·비상대응·재해 이력",   10),
        ("서류 제출·법정 의무 이행",  10),
    ]
    for area_name, score_max in area_rows:
        write_cell(ws, row, 1, 4, area_name,    font=FONT_DEFAULT, align=ALIGN_LEFT, height=22)
        write_cell(ws, row, 5, 6, score_max,    font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, "",           font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, "",           font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 9, 10, "",          font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1

    write_cell(ws, row, 1, 4, "총  점",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=24)
    write_cell(ws, row, 5, 6, 100,
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 7, v(d, "total_score"),
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 8, v(d, "total_grade"),
               font=FONT_BOLD, fill=FILL_WARN, align=ALIGN_CENTER)
    write_cell(ws, row, 9, 10, v(d, "total_remark"),
               font=FONT_SMALL, fill=FILL_LABEL, align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "종합 의견",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=40)
    write_cell(ws, row, 2, TOTAL_COLS, v(d, "overall_remarks"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 40
    return row + 1


def _s12_improvement(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "12. 개선요구사항  (C등급 이하 또는 부적합 항목 필수 기재)", fill=FILL_WARN)
    spans = [(1, 1), (2, 3), (4, 6), (7, 8), (9, 9), (10, 10)]
    texts = ["번호", "평가 영역", "지적 사항", "개선 조치", "완료 기한", "담당자"]
    for (cs, ce), hdr in zip(spans, texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    impr_items = d.get("improvement_items") or []
    display = max(MIN_IMPR_ROWS, len(impr_items))
    display = min(display, MAX_IMPR_ROWS)
    for i in range(display):
        item = impr_items[i] if i < len(impr_items) else {}
        write_cell(ws, row, 1, 1, i + 1,                  font=FONT_DEFAULT, align=ALIGN_CENTER, height=24)
        write_cell(ws, row, 2, 3, v(item, "category"),     font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 6, v(item, "issue"),        font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 8, v(item, "action"),       font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 9, 9, v(item, "due_date"),     font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 10, 10, v(item, "responsible"), font=FONT_SMALL,   align=ALIGN_CENTER)
        row += 1
    return row


def _s13_reassess(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "13. 재평가 계획")
    _lv(ws, row, "재평가 예정일",  v(d, "reassess_date"),  _L1, _V1S, _V1E)
    _lv(ws, row, "재평가 범위",    v(d, "reassess_scope") or "C등급 이하 또는 부적합 항목 중심",
        _L2, _V2S, _V2E)
    return row + 1


def _s14_sign(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "14. 평가자 / 협력업체 확인 서명")
    _lv(ws, row, "평가자 서명",         v(d, "evaluator"),          _L1, _V1S, _V1E, height=36)
    _lv(ws, row, "협력업체 확인자 서명", v(d, "contractor_confirm"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "승인자 서명",         v(d, "approval_person"),    _L1, _V1S, _V1E, height=36)
    _lv(ws, row, "협력업체 확인 일자",  v(d, "contractor_sign_date"), _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, NOTICE_LEGAL,
               font=FONT_NOTICE, fill=FILL_NOTICE, align=ALIGN_LEFT, height=28)
    return row + 1


# ---------------------------------------------------------------------------
# 메인 빌더
# ---------------------------------------------------------------------------

def build_subcontractor_safety_evaluation(form_data: Dict[str, Any]) -> bytes:
    """form_data dict를 받아 협력업체 안전보건 수준 평가표 xlsx 바이너리를 반환한다."""
    d: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _s_title(ws, row)
    row = _s1_eval_basic(ws, row, d)
    row = _s2_contractor(ws, row, d)
    row = _s3_scope(ws, row, d)
    row = _s4_criteria(ws, row, d)
    row = _s5_mgmt(ws, row, d)
    row = _s6_edu(ws, row, d)
    row = _s7_ra(ws, row, d)
    row = _s8_ppe(ws, row, d)
    row = _s9_accident(ws, row, d)
    row = _s10_legal(ws, row, d)
    row = _s11_total(ws, row, d)
    row = _s12_improvement(ws, row, d)
    row = _s13_reassess(ws, row, d)
    _s14_sign(ws, row, d)

    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.print_title_rows = "1:2"  # 제목+부제 반복
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

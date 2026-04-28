"""
안전보건 방침 및 목표 게시문 — Excel 출력 모듈 (v1).

법적 근거:
  - 중대재해처벌법 시행령 제4조 제1호 (안전보건 목표와 경영방침 수립·이행 의무)
  - 산업안전보건법 제14조 (안전보건관리책임자의 안전보건계획 수립 직무)
  - 산업안전보건법 제24조 (산업안전보건위원회 심의·의결 — 방침·목표)
분류: PRACTICAL — 법정 별지 서식 없음. 현장 게시용 안전보건 방침·목표 실무 보조서식.
      RA-006(위험성평가 결과 근로자 공지문)과 역할 분리.

form_type: safety_policy_goal_notice
함수명:    build_safety_policy_goal_notice(form_data)

Required form_data keys:
    site_name       str  현장명
    notice_year     str  적용 연도

Optional form_data keys:
    project_name          str   공사명
    company_name          str   회사명
    ceo_name              str   대표자명
    site_manager          str   현장 책임자
    notice_date           str   게시 일자
    effective_date        str   적용 시작일
    expiry_date           str   적용 만료일
    policy_items          list[str]  안전보건 방침 문장 (기본값 내장, 최대 5개)
    goal_items            list[dict] goal, target — 안전보건 목표 (기본값 내장)
    action_items          list[str]  핵심 실행과제 (기본값 내장)
    worker_duties         list[str]  근로자 준수사항 (기본값 내장)
    supervisor_duties     list[str]  관리감독자/협력업체 준수사항 (기본값 내장)
    posting_locations     list[str]  게시 위치 목록
    posting_period        str   게시 기간
    revision_history      list[dict] rev_no, rev_date, change_content, revised_by
    worker_confirm_count  str   공지 확인 근로자 수
    sign_date             str   서명 일자
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

DOC_ID    = "SP-001"
FORM_TYPE = "safety_policy_goal_notice"
SHEET_NAME    = "안전보건방침및목표게시문"
SHEET_HEADING = "안전보건 방침 및 목표 게시문"
SHEET_SUBTITLE = (
    "「중대재해처벌법 시행령」 제4조 제1호 및 「산업안전보건법」 제14조에 따른 "
    f"안전보건 방침·목표 현장 게시용 실무서식  [{DOC_ID}]"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 6, 2: 20, 3: 14, 4: 14, 5: 14, 6: 12, 7: 10, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_POLICY   = 5
MAX_GOALS    = 8
MAX_ACTIONS  = 8
MAX_DUTIES   = 8
MAX_REVISIONS = 5

# ---------------------------------------------------------------------------
# 기본값 — 한국 건설현장 표준 안전보건 방침·목표
# ---------------------------------------------------------------------------

DEFAULT_POLICY_ITEMS = [
    "우리는 모든 작업에서 근로자의 생명과 건강을 최우선으로 보호한다.",
    "우리는 법령과 기준을 철저히 준수하고 위험요인을 사전에 발굴·제거한다.",
    "우리는 근로자가 안전하게 작업할 수 있는 환경을 지속적으로 개선한다.",
    "우리는 안전보건 활동에 모든 구성원이 참여하고 책임을 다한다.",
]

DEFAULT_GOAL_ITEMS = [
    {"goal": "중대재해 발생",          "target": "0건"},
    {"goal": "추락·붕괴·협착 재해",   "target": "전년 대비 50% 감소"},
    {"goal": "TBM 실시율",             "target": "100%"},
    {"goal": "보호구 착용률",          "target": "100%"},
    {"goal": "위험성평가 개선조치 완료율", "target": "90% 이상"},
    {"goal": "안전보건교육 이수율",    "target": "100%"},
]

DEFAULT_ACTION_ITEMS = [
    "매일 TBM(작업 전 안전점검) 실시 및 위험요인 공유",
    "작업 전 위험성평가 실시 및 개선조치 이행",
    "보호구 지급·착용 관리 철저",
    "안전보건교육 정기 실시 및 신규 근로자 채용 시 교육 이행",
    "중대재해 예방 5대 의무(추락·붕괴·감전·충돌·협착) 집중 관리",
    "협력업체 안전관리 수준 평가 및 지도",
]

DEFAULT_WORKER_DUTIES = [
    "작업 전 반드시 TBM에 참여하고 위험요인을 확인한다.",
    "보호구(안전모·안전대·안전화 등)를 착용하지 않으면 작업하지 않는다.",
    "허가 없이 위험 구역에 출입하지 않는다.",
    "이상·위험 발견 시 즉시 작업을 중단하고 관리감독자에게 보고한다.",
    "안전보건교육에 빠짐없이 참여한다.",
]

DEFAULT_SUPERVISOR_DUTIES = [
    "작업 전 위험성평가를 실시하고 안전조치를 확인한다.",
    "근로자 보호구 착용 및 안전수칙 준수 여부를 수시로 점검한다.",
    "협력업체 근로자를 포함하여 TBM을 매일 실시한다.",
    "이상·위험 발생 시 즉시 작업을 중단시키고 원인을 제거한다.",
    "법령 및 현장 안전보건 기준을 준수하고 근로자에게 교육한다.",
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
               font=FONT_NOTICE, fill=FILL_NOTICE, align=ALIGN_LEFT, height=24)
    return row + 1


def _bullet_list(ws, row: int, items: List[str], defaults: List[str]) -> int:
    """불릿 항목 목록 렌더링. items가 없으면 defaults 사용."""
    src = items if items else defaults
    for item in src:
        write_cell(ws, row, 1, TOTAL_COLS, f"▷  {item}",
                   font=FONT_DEFAULT, align=ALIGN_LEFT, height=22)
        row += 1
    return row


# ---------------------------------------------------------------------------
# 섹션 렌더러
# ---------------------------------------------------------------------------

def _s_title(ws, row: int) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_SECTION, align=ALIGN_CENTER, height=36)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, height=18)
    return row + 1


def _s1_basic(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "1. 게시문 기본정보")
    _lv(ws, row, "현장명",     v(d, "site_name"),      _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",     v(d, "project_name"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "회사명",     v(d, "company_name"),   _L1, _V1S, _V1E)
    _lv(ws, row, "적용 연도",  v(d, "notice_year"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "게시 일자",  v(d, "notice_date"),    _L1, _V1S, _V1E)
    _lv(ws, row, "적용 기간",
        f"{v(d, 'effective_date')} ~ {v(d, 'expiry_date')}" if v(d, "effective_date") else "",
        _L2, _V2S, _V2E)
    return row + 1


def _s2_policy(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "2. 안전보건 방침")
    row = _notice(ws, row,
        "우리 현장의 안전보건 방침을 전 구성원에게 공표하고 이를 성실히 이행할 것을 선언합니다.")
    items = d.get("policy_items") or []
    src = items[:MAX_POLICY] if items else DEFAULT_POLICY_ITEMS
    for item in src:
        write_cell(ws, row, 1, TOTAL_COLS, f"■  {item}",
                   font=FONT_BOLD, fill=FILL_NONE, align=ALIGN_LEFT, height=24)
        row += 1
    return row


def _s3_goals(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "3. 안전보건 목표")
    # 헤더
    write_cell(ws, row, 1, 5, "목표 항목",
               font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    write_cell(ws, row, 6, 8, "목표 수치 / 기준",
               font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    items = d.get("goal_items") or []
    src = items[:MAX_GOALS] if items else DEFAULT_GOAL_ITEMS
    for i, item in enumerate(src):
        write_cell(ws, row, 1, 1, i + 1,               font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 5, v(item, "goal"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 8, v(item, "target"),    font=FONT_BOLD,    align=ALIGN_CENTER)
        row += 1
    return row


def _s4_actions(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "4. 핵심 실행과제")
    items = d.get("action_items") or []
    row = _bullet_list(ws, row, items[:MAX_ACTIONS] if items else [], DEFAULT_ACTION_ITEMS)
    return row


def _s5_worker_duties(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "5. 근로자 준수사항")
    items = d.get("worker_duties") or []
    row = _bullet_list(ws, row, items[:MAX_DUTIES] if items else [], DEFAULT_WORKER_DUTIES)
    return row


def _s6_supervisor_duties(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "6. 관리감독자/협력업체 준수사항")
    items = d.get("supervisor_duties") or []
    row = _bullet_list(ws, row, items[:MAX_DUTIES] if items else [], DEFAULT_SUPERVISOR_DUTIES)
    return row


def _s7_posting(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "7. 게시 위치 및 게시 기간")
    # 게시 위치
    locations = d.get("posting_locations") or []
    loc_text = ",  ".join(locations) if locations else "현장 사무소, 근로자 출입구, 식당, 작업장 주요 위치"
    write_cell(ws, row, 1, 1, "게시 위치",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=28)
    write_cell(ws, row, 2, TOTAL_COLS, loc_text,
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 28
    row += 1
    _lv(ws, row, "게시 기간",
        v(d, "posting_period") or f"{v(d, 'effective_date')} ~ {v(d, 'expiry_date')}",
        _L1, 2, TOTAL_COLS)
    return row + 1


def _s8_revision(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "8. 개정 이력")
    spans = [(1, 1), (2, 3), (4, 6), (7, 7), (8, 8)]
    texts = ["개정 번호", "개정 일자", "주요 변경 내용", "개정자", "승인자"]
    for (cs, ce), hdr in zip(spans, texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    revisions = d.get("revision_history") or []
    n = max(3, len(revisions))
    n = min(n, MAX_REVISIONS)
    for i in range(n):
        item = revisions[i] if i < len(revisions) else {}
        write_cell(ws, row, 1, 1, v(item, "rev_no") or i + 1,
                   font=FONT_DEFAULT, align=ALIGN_CENTER, height=20)
        write_cell(ws, row, 2, 3, v(item, "rev_date"),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 4, 6, v(item, "change_content"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, v(item, "revised_by"),     font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "approver"),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        row += 1
    return row


def _s9_sign(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "9. 대표자 / 현장책임자 서명", fill=FILL_HEADER)
    _lv(ws, row, "대표자",      v(d, "ceo_name"),      _L1, _V1S, _V1E, height=36)
    _lv(ws, row, "현장책임자",  v(d, "site_manager"),  _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 2, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    write_cell(ws, row, 3, 4, "",      font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "",      font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1
    _lv(ws, row, "서명 일자",   v(d, "sign_date"),     _L1, 2, TOTAL_COLS)
    return row + 1


def _s10_worker_confirm(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "10. 근로자 공지 확인")
    row = _notice(ws, row,
        "본 안전보건 방침 및 목표를 근로자에게 공지하고 내용을 숙지하였음을 확인합니다.")
    _lv(ws, row, "공지 확인 근로자 수",
        v(d, "worker_confirm_count") or "",
        _L1, _V1S, _V1E, height=28)
    _lv(ws, row, "공지 일자",
        v(d, "notice_date") or "",
        _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS,
               "본 서식은 관계 기관 공식 법정서식이 아닙니다. "
               "중대재해처벌법 시행령 제4조 제1호·산업안전보건법 제14조 기반 "
               "안전보건 방침·목표 현장 게시용 실무 보조서식이며, 현장·발주처 기준에 따라 보완 적용한다.",
               font=FONT_NOTICE, fill=FILL_NOTICE, align=ALIGN_LEFT, height=28)
    return row + 1


# ---------------------------------------------------------------------------
# 메인 빌더
# ---------------------------------------------------------------------------

def build_safety_policy_goal_notice(form_data: Dict[str, Any]) -> bytes:
    """form_data dict를 받아 안전보건 방침 및 목표 게시문 xlsx 바이너리를 반환한다."""
    d: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _s_title(ws, row)
    row = _s1_basic(ws, row, d)
    row = _s2_policy(ws, row, d)
    row = _s3_goals(ws, row, d)
    row = _s4_actions(ws, row, d)
    row = _s5_worker_duties(ws, row, d)
    row = _s6_supervisor_duties(ws, row, d)
    row = _s7_posting(ws, row, d)
    row = _s8_revision(ws, row, d)
    row = _s9_sign(ws, row, d)
    _s10_worker_confirm(ws, row, d)

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

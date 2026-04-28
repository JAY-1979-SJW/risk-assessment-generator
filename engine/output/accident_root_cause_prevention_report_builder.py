from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

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

DOC_ID         = "EM-005"
FORM_TYPE      = "accident_root_cause_prevention_report"
SHEET_NAME     = "재해원인분석재발방지보고서"
SHEET_HEADING  = "재해 원인 분석 및 재발 방지 보고서"
SHEET_SUBTITLE = (
    "산업안전보건법 제57조 제2항·중대재해처벌법 제4조 기반 — 공식 제출 서식 아님"
    " — 내부 원인분석·재발방지 이행관리 보조서식"
    f" ({DOC_ID})"
)
SHEET_NOTICE = (
    "※ 공식 제출 서식 아님 — 산업재해조사표(EM-001) 및 중대재해 즉시보고(EM-004) 이후 내부 원인분석·재발방지 이행관리 보조서식 | "
    "재발방지 대책은 담당자·기한·이행상태까지 관리 | "
    "중대재해처벌법상 재발방지 대책 수립·이행 조치와 연계 | "
    "산업재해조사표 제출 의무와 별도 관리 | "
    "개인정보·민감정보 최소 기재 | "
    "사진·영상·진술 등 증빙자료는 별도 보관"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 14, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_WHY_ROWS        = 5
MAX_PREVENTION_ROWS = 10
MIN_PREVENTION_ROWS = 5
MAX_ACTION_ROWS     = 10
MIN_ACTION_ROWS     = 5


def _lv(ws, row: int, label: str, value: Any,
        lc: int, vs: int, ve: int, height: float = 20) -> None:
    write_cell(ws, row, lc, lc, label,
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, vs, ve, value,
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height


def _section_header(ws, row: int, title: str) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, title,
               font=FONT_BOLD, fill=FILL_SECTION, align=ALIGN_CENTER, height=22)
    return row + 1


def _write_title(ws, row: int) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_SECTION, align=ALIGN_CENTER, height=28)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, height=18)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_NOTICE,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_CENTER, height=28)
    return row + 1


def _write_doc_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 1. 문서 기본정보")
    _lv(ws, row, "공사명",           v(data, "project_name"),      _L1, _V1S, _V1E)
    _lv(ws, row, "현장명",           v(data, "site_name"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작성일",           v(data, "prepared_date"),     _L1, _V1S, _V1E)
    _lv(ws, row, "사고번호",         v(data, "accident_no"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "EM-001 제출 여부", v(data, "em001_submitted"),   _L1, _V1S, _V1E)
    _lv(ws, row, "EM-004 즉시보고",  v(data, "em004_reported"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작성자",           v(data, "author"),            _L1, _V1S, _V1E)
    _lv(ws, row, "검토자",           v(data, "reviewer"),          _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "승인자",           v(data, "approver"),          _L1, _V1S, _V1E)
    return row + 1


def _write_accident_overview(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 2. 재해 개요")
    _lv(ws, row, "발생일시",         v(data, "accident_datetime"),  _L1, _V1S, _V1E)
    _lv(ws, row, "발생장소",         v(data, "accident_location"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업공종",         v(data, "work_type"),          _L1, _V1S, _V1E)
    _lv(ws, row, "작업내용",         v(data, "work_content"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "사고유형",         v(data, "accident_type"),      _L1, _V1S, _V1E)
    _lv(ws, row, "피해자 수",        v(data, "victim_count"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "사망 여부",        v(data, "is_fatal"),           _L1, _V1S, _V1E)
    _lv(ws, row, "휴업 예상일수",    v(data, "sick_leave_days"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "물적 피해",        v(data, "property_damage"),    _L1, _V1S, _V1E)
    _lv(ws, row, "관계기관 신고",    v(data, "agency_notified"),    _L2, _V2S, _V2E)
    return row + 1


def _write_accident_sequence(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 3. 사고 경위")
    _lv(ws, row, "사고 전 작업상황",  v(data, "pre_accident_situation"), _L1, _V1S, _V1E)
    _lv(ws, row, "사고 발생 과정",    v(data, "accident_sequence"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "사고 직후 조치",    v(data, "immediate_action"),        _L1, _V1S, _V1E)
    _lv(ws, row, "작업중지 여부",     v(data, "work_stopped"),            _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "현장보존 여부",     v(data, "scene_preserved"),         _L1, _V1S, _V1E)
    _lv(ws, row, "목격자 진술 요약",  v(data, "witness_summary"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "사진/영상 자료",    v(data, "evidence_media"),          _L1, _V1S, _V1E)
    return row + 1


def _write_cause_analysis(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 4. 원인 분석")
    _lv(ws, row, "직접 원인",          v(data, "direct_cause"),         _L1, _V1S, _V1E)
    _lv(ws, row, "간접 원인",          v(data, "indirect_cause"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "인적 요인",          v(data, "human_factor"),         _L1, _V1S, _V1E)
    _lv(ws, row, "설비/장비 요인",     v(data, "equipment_factor"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업방법 요인",      v(data, "method_factor"),        _L1, _V1S, _V1E)
    _lv(ws, row, "관리감독 요인",      v(data, "supervision_factor"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "교육/훈련 요인",     v(data, "training_factor"),      _L1, _V1S, _V1E)
    _lv(ws, row, "작업환경 요인",      v(data, "environment_factor"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "도급/협력업체 요인", v(data, "contractor_factor"),    _L1, _V1S, _V1E)
    _lv(ws, row, "위험성평가 반영",    v(data, "ra_reflected"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업계획서 반영",    v(data, "workplan_reflected"),   _L1, _V1S, _V1E)
    return row + 1


def _write_five_why(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 5. 5-Why 분석")
    headers   = ["단계", "Why 질문 / 답변",              "근거자료"]
    col_spans = [(1, 1), (2, 6),                          (7, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("five_why_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    labels = ["Why 1", "Why 2", "Why 3", "Why 4", "Why 5"]
    for i in range(MAX_WHY_ROWS):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, labels[i],              font=FONT_BOLD,    fill=FILL_LABEL,  align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 6, v(item, "answer"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 7, 8, v(item, "evidence"),    font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1

    _lv(ws, row, "근본 원인",  v(data, "root_cause"),      _L1, _V1S, _V1E, height=24)
    _lv(ws, row, "근거자료",   v(data, "root_cause_basis"), _L2, _V2S, _V2E, height=24)
    return row + 1


def _write_prevention(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 6. 재발방지 대책")
    headers   = ["번호", "구분",          "대책 내용",             "담당자",     "완료 예정일", "비고"]
    col_spans = [(1, 1), (2, 2),          (3, 5),                  (6, 6),       (7, 7),        (8, 8)]
    for (cs, ce), hdr in zip(col_spans, headers):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("prevention_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_PREVENTION_ROWS, len(items))
    display = min(display, MAX_PREVENTION_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                   font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 2, v(item, "category"),     font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 5, v(item, "description"),  font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 6, 6, v(item, "responsible"),  font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "deadline"),     font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "remarks"),      font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_action_tracking(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 7. 이행관리")
    headers   = ["번호", "개선 항목",     "담당자",  "완료예정일", "완료일",  "이행상태", "확인자", "미완료사유"]
    col_spans = [(1, 1), (2, 3),          (4, 4),    (5, 5),       (6, 6),    (7, 7),     (8, 8),   None]
    # 8열로 맞춤
    headers   = ["번호", "개선 항목",     "담당자",  "완료예정일", "완료일",  "이행상태", "확인자", "미완료사유/비고"]
    col_spans = [(1, 1), (2, 3),          (4, 4),    (5, 5),       (6, 6),    (7, 7),     (8, 8),   None]
    header_defs = list(zip(
        [(1,1),(2,3),(4,4),(5,5),(6,6),(7,7),(8,8)],
        ["번호","개선 항목","담당자","완료예정일","완료일","이행상태","확인자/비고"]
    ))
    for (cs, ce), hdr in header_defs:
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("action_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_ACTION_ROWS, len(items))
    display = min(display, MAX_ACTION_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, i + 1,                      font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 3, v(item, "improvement"),      font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 4, 4, v(item, "responsible"),      font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(item, "deadline"),         font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(item, "completed_date"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 7, 7, v(item, "status"),           font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "checker"),          font=FONT_SMALL,   align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 8. 확인 및 승인")
    _lv(ws, row, "작성자",            v(data, "author"),            _L1, _V1S, _V1E)
    _lv(ws, row, "안전관리자",        v(data, "safety_manager"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "관리감독자",        v(data, "supervisor"),        _L1, _V1S, _V1E)
    _lv(ws, row, "현장소장",          v(data, "site_director"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "협력업체 책임자",   v(data, "subcon_manager"),    _L1, _V1S, _V1E)
    _lv(ws, row, "근로자대표 의견",   v(data, "worker_rep_opinion"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "최종 승인일",       v(data, "final_approved_date"), _L1, _V1S, _V1E)
    row += 1
    write_cell(ws, row, 1, 2, "서명", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    write_cell(ws, row, 3, 4, "",    font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "서명", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "",    font=FONT_DEFAULT, align=ALIGN_LEFT)
    return row + 1


def _finalize_sheet(ws) -> None:
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75


def build_accident_root_cause_prevention_report_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 재해 원인 분석 및 재발 방지 보고서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_doc_info(ws, row, data)
    row = _write_accident_overview(ws, row, data)
    row = _write_accident_sequence(ws, row, data)
    row = _write_cause_analysis(ws, row, data)
    row = _write_five_why(ws, row, data)
    row = _write_prevention(ws, row, data)
    row = _write_action_tracking(ws, row, data)
    row = _write_signature(ws, row, data)
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

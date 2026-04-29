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

DOC_ID     = "EM-002"
FORM_TYPE  = "near_miss_report"
SHEET_NAME = "아차사고보고서"
SHEET_HEADING  = "아차사고 보고서 (Near Miss Report)"
SHEET_SUBTITLE = (
    "아차사고 및 위험징후 기록을 통한 사고예방 보조서식"
    " — 공식 제출 서식 아님"
    f" ({DOC_ID})"
)
SHEET_NOTICE = (
    "※ 공식 제출 서식 아님 — 아차사고 및 위험징후 기록을 통한 사고예방 보조서식 | "
    "실제 재해 발생 전 위험요인을 기록하고 개선조치까지 관리 | "
    "위험성평가 및 TBM 교육에 반영 필요 | "
    "중대재해·산업재해 발생 시 EM-004, EM-001, EM-006과 별도 관리 | "
    "개인정보·민감정보 최소 기재 | "
    "사진·영상 등 증빙자료는 별도 보관"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_ACTION_ROWS = 8
MIN_ACTION_ROWS = 4


def _lv(ws, row: int, label: str, value: Any,
        lc: int, vs: int, ve: int, height: float = 20) -> None:
    write_cell(ws, row, lc, lc, label, font=FONT_BOLD, fill=FILL_LABEL,
               align=ALIGN_LABEL, height=height)
    write_cell(ws, row, vs, ve, value, font=FONT_DEFAULT, fill=FILL_NONE,
               align=ALIGN_LEFT)


def _section_header(ws, row: int, title: str) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, title,
               font=FONT_BOLD, fill=FILL_SECTION, align=ALIGN_LEFT, height=22)
    return row + 1


def _write_title(ws, row: int) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_HEADER, align=ALIGN_CENTER, height=36)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_HEADER, align=ALIGN_CENTER, height=28)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_NOTICE,
               font=FONT_SMALL, fill=FILL_LABEL, align=ALIGN_LEFT, height=36)
    return row + 1


def _write_meta(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 1. 문서 기본정보")
    _lv(ws, row, "공사명",         v(data, "project_name"),   _L1, _V1S, _V1E)
    _lv(ws, row, "현장명",         v(data, "site_name"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작성일",         v(data, "written_date"),   _L1, _V1S, _V1E)
    _lv(ws, row, "아차사고 번호",  v(data, "near_miss_no"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "발견자",         v(data, "discoverer"),     _L1, _V1S, _V1E)
    _lv(ws, row, "작성자",         v(data, "author"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "검토자",         v(data, "reviewer"),       _L1, _V1S, _V1E)
    _lv(ws, row, "승인자",         v(data, "approver"),       _L2, _V2S, _V2E)
    return row + 1


def _write_incident_overview(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 2. 아차사고 개요")
    _lv(ws, row, "발생일시",         v(data, "incident_datetime"),  _L1, _V1S, _V1E)
    _lv(ws, row, "발생장소",         v(data, "incident_location"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업공종",         v(data, "work_type"),          _L1, _V1S, _V1E)
    _lv(ws, row, "작업내용",         v(data, "work_content"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "관련 장비/설비",   v(data, "related_equipment"),  _L1, _V1S, _V1E)
    _lv(ws, row, "관련 협력업체",    v(data, "related_company"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "아차사고 유형",    v(data, "near_miss_type"),     _L1, _V1S, _V1E)
    _lv(ws, row, "재해 발생 여부",   v(data, "actual_accident"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "인적 피해 없음",   v(data, "no_human_damage"),    _L1, _V1S, _V1E)
    _lv(ws, row, "물적 피해 없음",   v(data, "no_property_damage"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업중지 여부",    v(data, "work_stopped"),       _L1, _V1S, _V1E)
    return row + 1


def _write_hazard_detail(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 3. 위험상황 상세")
    write_cell(ws, row, 1, 1, "상황 경위",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=48)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "situation_description"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 48
    row += 1
    write_cell(ws, row, 1, 1, "사고 이어질 경위",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=36)
    write_cell(ws, row, 2, TOTAL_COLS, v(data, "potential_sequence"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 36
    row += 1
    _lv(ws, row, "예상 재해 유형",  v(data, "expected_accident_type"), _L1, _V1S, _V1E)
    _lv(ws, row, "예상 피해 정도",  v(data, "expected_severity"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "직접 위험요인",   v(data, "direct_hazard"),          _L1, _V1S, _V1E)
    _lv(ws, row, "간접 위험요인",   v(data, "indirect_hazard"),        _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "당시 작업조건",   v(data, "work_conditions"),        _L1, _V1S, _V1E)
    _lv(ws, row, "사진/영상 자료",  v(data, "evidence_media"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "목격자 여부",     v(data, "witness"),                _L1, _V1S, _V1E)
    return row + 1


def _write_hazard_classification(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 4. 위험요인 분류  (해당 항목 체크)")
    hazards = [
        ("추락",         "haz_fall"),
        ("낙하/비래",    "haz_falling_obj"),
        ("끼임",         "haz_entanglement"),
        ("감전",         "haz_electric"),
        ("붕괴",         "haz_collapse"),
        ("전도",         "haz_overturn"),
        ("화재",         "haz_fire"),
        ("폭발",         "haz_explosion"),
        ("질식",         "haz_asphyxia"),
        ("유해물질 노출","haz_chemical"),
        ("장비 충돌",    "haz_collision"),
        ("중량물 낙하",  "haz_heavy_obj"),
        ("기타",         "haz_other"),
    ]
    for i, (label, key) in enumerate(hazards):
        if i % 2 == 0:
            _lv(ws, row, label, v(data, key), _L1, _V1S, _V1E)
        else:
            _lv(ws, row, label, v(data, key), _L2, _V2S, _V2E)
            row += 1
    if len(hazards) % 2 != 0:
        row += 1
    return row + 1


def _write_immediate_actions(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 5. 즉시 조치")
    actions = [
        ("작업중지",      "imm_work_stop"),
        ("위험구역 통제", "imm_zone_control"),
        ("장비 정지",     "imm_equip_stop"),
        ("전원 차단",     "imm_power_cut"),
        ("가스 차단",     "imm_gas_cut"),
        ("임시 방호조치", "imm_temp_guard"),
        ("근로자 대피",   "imm_evacuation"),
        ("관리자 보고",   "imm_reported"),
        ("협력업체 통보", "imm_sub_notified"),
        ("기타 조치",     "imm_other"),
    ]
    for i, (label, key) in enumerate(actions):
        if i % 2 == 0:
            _lv(ws, row, label, v(data, key), _L1, _V1S, _V1E)
        else:
            _lv(ws, row, label, v(data, key), _L2, _V2S, _V2E)
            row += 1
    if len(actions) % 2 != 0:
        row += 1
    return row + 1


def _write_cause_analysis(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 6. 원인 분석")
    causes = [
        ("불안전한 상태",          "ca_unsafe_condition"),
        ("불안전한 행동",          "ca_unsafe_act"),
        ("작업절차 미준수",        "ca_procedure_violation"),
        ("교육 부족",              "ca_lack_of_training"),
        ("관리감독 미흡",          "ca_poor_supervision"),
        ("장비/설비 결함",         "ca_equipment_defect"),
        ("보호구 미착용",          "ca_no_ppe"),
        ("작업환경 문제",          "ca_work_environment"),
        ("도급/협력업체 관리 문제","ca_contractor_mgmt"),
        ("위험성평가 누락",        "ca_ra_missed"),
    ]
    for i, (label, key) in enumerate(causes):
        if i % 2 == 0:
            _lv(ws, row, label, v(data, key), _L1, _V1S, _V1E)
        else:
            _lv(ws, row, label, v(data, key), _L2, _V2S, _V2E)
            row += 1
    if len(causes) % 2 != 0:
        row += 1
    return row + 1


def _write_prevention_measures(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 7. 개선 및 예방대책")
    measures = [
        ("즉시 개선조치",         "prev_immediate"),
        ("단기 개선대책",         "prev_short_term"),
        ("중장기 개선대책",       "prev_long_term"),
        ("작업절차 개정",         "prev_procedure_update"),
        ("위험성평가 재검토",     "prev_ra_review"),
        ("TBM 전파교육",          "prev_tbm"),
        ("협력업체 교육",         "prev_sub_edu"),
        ("보호구 보완",           "prev_ppe_update"),
        ("설비/방호장치 보완",    "prev_guard_update"),
        ("유사 작업 전파",        "prev_lateral_spread"),
    ]
    for i, (label, key) in enumerate(measures):
        if i % 2 == 0:
            _lv(ws, row, label, v(data, key), _L1, _V1S, _V1E)
        else:
            _lv(ws, row, label, v(data, key), _L2, _V2S, _V2E)
            row += 1
    if len(measures) % 2 != 0:
        row += 1
    return row + 1


def _write_action_tracking(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 8. 이행관리")
    hdrs = ["개선 항목", "담당자", "완료 예정일", "완료일", "이행상태", "증빙자료", "확인자", "미완료 사유"]
    spans = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)]
    for (cs, ce), hdr in zip(spans, hdrs):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw: Any = data.get("action_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    display = max(MIN_ACTION_ROWS, len(items))
    display = min(display, MAX_ACTION_ROWS)

    for i in range(display):
        item = items[i] if i < len(items) else {}
        write_cell(ws, row, 1, 1, v(item, "improvement"),   font=FONT_DEFAULT, align=ALIGN_LEFT,   height=24)
        write_cell(ws, row, 2, 2, v(item, "responsible"),   font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3, 3, v(item, "due_date"),      font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 4, 4, v(item, "completed_date"),font=FONT_SMALL,   align=ALIGN_CENTER)
        write_cell(ws, row, 5, 5, v(item, "status"),        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6, 6, v(item, "evidence"),      font=FONT_SMALL,   align=ALIGN_LEFT)
        write_cell(ws, row, 7, 7, v(item, "checker"),       font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 8, 8, v(item, "incomplete_reason"), font=FONT_SMALL, align=ALIGN_LEFT)
        row += 1
    return row


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 9. 확인 및 승인")
    _lv(ws, row, "작성자",          v(data, "sig_author"),       _L1, _V1S, _V1E)
    _lv(ws, row, "안전관리자",      v(data, "sig_safety_mgr"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "관리감독자",      v(data, "sig_supervisor"),   _L1, _V1S, _V1E)
    _lv(ws, row, "현장소장",        v(data, "sig_site_director"),_L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "협력업체 책임자", v(data, "sig_sub_manager"),  _L1, _V1S, _V1E)
    _lv(ws, row, "근로자대표 의견", v(data, "worker_rep_opinion"),_L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "최종 확인일",     v(data, "sig_confirmed_date"),_L1, _V1S, _V1E)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, "서명",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    return row + 1


def _finalize_sheet(ws) -> None:
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.print_title_rows = "1:2"  # 제목+부제 반복
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75


def build_near_miss_report_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 아차사고 보고서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_incident_overview(ws, row, data)
    row = _write_hazard_detail(ws, row, data)
    row = _write_hazard_classification(ws, row, data)
    row = _write_immediate_actions(ws, row, data)
    row = _write_cause_analysis(ws, row, data)
    row = _write_prevention_measures(ws, row, data)
    row = _write_action_tracking(ws, row, data)
    row = _write_signature(ws, row, data)
    write_cell(ws, row, 1, TOTAL_COLS, "", height=6)  # 하단 여백
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

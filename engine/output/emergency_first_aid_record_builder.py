from __future__ import annotations

from io import BytesIO
from typing import Any, Dict

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

DOC_ID     = "EM-006"
FORM_TYPE  = "emergency_first_aid_record"
SHEET_NAME = "응급조치실시기록서"
SHEET_HEADING  = "응급조치 실시 기록서"
SHEET_SUBTITLE = (
    "산업안전보건기준에 관한 규칙 제82조 구급용구 관리와 연계한 현장 응급조치 이행기록 보조서식"
    " — 공식 제출 서식 아님"
    f" ({DOC_ID})"
)
SHEET_NOTICE = (
    "※ 공식 제출 서식 아님 — 현장 응급조치 실시 내용 및 이송·인계 기록 보조서식 | "
    "산업안전보건기준에 관한 규칙 제82조 구급용구 관리와 연계 | "
    "응급상황 발생 시 즉시 119 신고 및 작업중지 | "
    "구급용구 사용 후 보충 및 관리책임자 확인 필요 | "
    "산업재해조사표(EM-001)·중대재해 즉시보고(EM-004)와 별도 관리 | "
    "개인정보·민감정보 최소 기재 | "
    "사진·영상·진술 등 증빙자료는 별도 보관"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8


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
    _lv(ws, row, "공사명",   v(data, "project_name"),  _L1, _V1S, _V1E)
    _lv(ws, row, "현장명",   v(data, "site_name"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작성일",   v(data, "written_date"),   _L1, _V1S, _V1E)
    _lv(ws, row, "사고번호", v(data, "accident_no"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "EM-004 즉시보고 여부", v(data, "em004_reported"),  _L1, _V1S, _V1E)
    _lv(ws, row, "EM-001 조사표 작성",   v(data, "em001_prepared"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작성자", v(data, "author"),   _L1, _V1S, _V1E)
    _lv(ws, row, "검토자", v(data, "reviewer"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "승인자", v(data, "approver"), _L1, _V1S, _V1E)
    return row + 1


def _write_incident_overview(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 2. 사고 및 응급상황 개요")
    _lv(ws, row, "발생일시",       v(data, "incident_datetime"),  _L1, _V1S, _V1E)
    _lv(ws, row, "발생장소",       v(data, "incident_location"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업공종",       v(data, "work_type"),          _L1, _V1S, _V1E)
    _lv(ws, row, "작업내용",       v(data, "work_content"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "응급상황 유형",  v(data, "emergency_type"),     _L1, _V1S, _V1E)
    _lv(ws, row, "재해자 수",      v(data, "victim_count"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "의식 여부",      v(data, "conscious"),          _L1, _V1S, _V1E)
    _lv(ws, row, "호흡 여부",      v(data, "breathing"),          _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "출혈 여부",      v(data, "bleeding"),           _L1, _V1S, _V1E)
    _lv(ws, row, "골절 의심",      v(data, "fracture_suspected"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "화상 여부",      v(data, "burn"),               _L1, _V1S, _V1E)
    _lv(ws, row, "질식/중독 의심", v(data, "asphyxia_suspected"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "감전 여부",      v(data, "electric_shock"),     _L1, _V1S, _V1E)
    _lv(ws, row, "기타 증상",      v(data, "other_symptoms"),     _L2, _V2S, _V2E)
    return row + 1


def _write_victim_info(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 3. 재해자 기본정보  ※ 개인정보 최소 기재")
    _lv(ws, row, "성명",          v(data, "victim_name"),         _L1, _V1S, _V1E)
    _lv(ws, row, "소속",          v(data, "victim_company"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "직종",          v(data, "victim_job"),          _L1, _V1S, _V1E)
    _lv(ws, row, "연락처",        v(data, "victim_contact"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "생년월일/식별", v(data, "victim_birthdate"),    _L1, _V1S, _V1E)
    _lv(ws, row, "보호자 연락",   v(data, "guardian_contacted"),  _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS,
               "※ 개인정보·민감정보는 목적 범위 내 최소 기재 — 별도 개인정보 보호 절차 준수",
               font=FONT_SMALL, fill=FILL_LABEL, align=ALIGN_LEFT, height=18)
    return row + 1


def _write_first_aid_actions(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 4. 응급조치 실시 내용")
    _lv(ws, row, "조치 시작 시각", v(data, "aid_start_time"),    _L1, _V1S, _V1E)
    _lv(ws, row, "조치 종료 시각", v(data, "aid_end_time"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "실시자",        v(data, "first_aider"),        _L1, _V1S, _V1E)
    _lv(ws, row, "응급처치 자격", v(data, "aider_qualified"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "지혈",          v(data, "aid_hemostasis"),     _L1, _V1S, _V1E)
    _lv(ws, row, "심폐소생술",    v(data, "aid_cpr"),            _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "AED 사용",      v(data, "aid_aed"),            _L1, _V1S, _V1E)
    _lv(ws, row, "부목 고정",     v(data, "aid_splint"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "화상 처치",     v(data, "aid_burn_care"),      _L1, _V1S, _V1E)
    _lv(ws, row, "산소 공급",     v(data, "aid_oxygen"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "질식/가스 대피 후 조치", v(data, "aid_asphyxia"), _L1, _V1S, _V1E)
    _lv(ws, row, "감전 전원 차단", v(data, "aid_power_cut"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "체온/폭염 조치", v(data, "aid_temperature"),   _L1, _V1S, _V1E)
    _lv(ws, row, "기타 조치",      v(data, "aid_other"),         _L2, _V2S, _V2E)
    return row + 1


def _write_equipment_log(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 5. 구급용구 및 장비 사용 기록  (산업안전보건기준 제82조)")
    _lv(ws, row, "구급함 사용",          v(data, "eq_kit"),         _L1, _V1S, _V1E)
    _lv(ws, row, "붕대/거즈/소독약",     v(data, "eq_bandage"),     _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "지혈대 사용",          v(data, "eq_tourniquet"),  _L1, _V1S, _V1E)
    _lv(ws, row, "부목 사용",            v(data, "eq_splint"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "들것 사용",            v(data, "eq_stretcher"),   _L1, _V1S, _V1E)
    _lv(ws, row, "AED 사용",             v(data, "eq_aed"),         _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "산소/호흡보조 장비",   v(data, "eq_oxygen"),      _L1, _V1S, _V1E)
    _lv(ws, row, "송기마스크/공기호흡기", v(data, "eq_air_supply"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "가스측정기",           v(data, "eq_gas_meter"),   _L1, _V1S, _V1E)
    _lv(ws, row, "보충 필요 여부",       v(data, "eq_replenish"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "구급용구 관리자 확인", v(data, "eq_manager"),     _L1, _V1S, _V1E)
    return row + 1


def _write_transport_log(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 6. 신고 및 이송 기록")
    _lv(ws, row, "119 신고 시각",        v(data, "call_119_time"),   _L1, _V1S, _V1E)
    _lv(ws, row, "소방/구급대 도착",     v(data, "ems_arrive_time"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "병원 이송 시각",       v(data, "hospital_time"),   _L1, _V1S, _V1E)
    _lv(ws, row, "이송 병원명",          v(data, "hospital_name"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "이송 수단",            v(data, "transport_means"), _L1, _V1S, _V1E)
    _lv(ws, row, "동행자",               v(data, "escort"),          _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "보호자 연락 시각",     v(data, "guardian_time"),   _L1, _V1S, _V1E)
    _lv(ws, row, "경찰/관서 신고 여부",  v(data, "authority_notified"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "인계자",               v(data, "handover_from"),   _L1, _V1S, _V1E)
    _lv(ws, row, "인수자",               v(data, "handover_to"),     _L2, _V2S, _V2E)
    return row + 1


def _write_site_control(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 7. 현장 통제 및 2차 재해 방지")
    _lv(ws, row, "작업중지 여부",     v(data, "ctrl_work_stop"),   _L1, _V1S, _V1E)
    _lv(ws, row, "위험구역 통제",     v(data, "ctrl_zone"),        _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "전원 차단 여부",   v(data, "ctrl_power"),        _L1, _V1S, _V1E)
    _lv(ws, row, "가스 차단 여부",   v(data, "ctrl_gas"),          _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "장비 정지 여부",   v(data, "ctrl_equipment"),    _L1, _V1S, _V1E)
    _lv(ws, row, "추가 대피 여부",   v(data, "ctrl_evacuated"),    _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "현장보존 여부",    v(data, "ctrl_preserved"),    _L1, _V1S, _V1E)
    _lv(ws, row, "사진/영상 기록",   v(data, "ctrl_recorded"),     _L2, _V2S, _V2E)
    return row + 1


def _write_followup(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 8. 사후 조치")
    _lv(ws, row, "구급용구 보충",         v(data, "fu_kit_replenish"),     _L1, _V1S, _V1E)
    _lv(ws, row, "응급조치 교육 필요",    v(data, "fu_training_needed"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "비상연락망 수정 필요",  v(data, "fu_contact_update"),    _L1, _V1S, _V1E)
    _lv(ws, row, "대피계획 수정 필요",    v(data, "fu_evac_update"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "위험성평가 재검토",     v(data, "fu_risk_review"),       _L1, _V1S, _V1E)
    _lv(ws, row, "재발방지 보고서 연계",  v(data, "fu_em005_linked"),      _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "후속 담당자",           v(data, "fu_responsible"),       _L1, _V1S, _V1E)
    _lv(ws, row, "완료 예정일",           v(data, "fu_due_date"),          _L2, _V2S, _V2E)
    return row + 1


def _write_signature(ws, row: int, data: Dict[str, Any]) -> int:
    row = _section_header(ws, row, "▶ 9. 확인 및 승인")
    _lv(ws, row, "응급조치 실시자", v(data, "sig_first_aider"),  _L1, _V1S, _V1E)
    _lv(ws, row, "안전관리자",      v(data, "sig_safety_mgr"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "관리감독자",      v(data, "sig_supervisor"),   _L1, _V1S, _V1E)
    _lv(ws, row, "현장소장",        v(data, "sig_site_director"),_L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "협력업체 책임자", v(data, "sig_sub_manager"),  _L1, _V1S, _V1E)
    _lv(ws, row, "확인일",          v(data, "sig_confirmed_date"),_L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, "서명",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    return row + 1


def _finalize_sheet(ws) -> None:
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75
    ws.print_title_rows = "1:2"


def build_emergency_first_aid_record_excel(
    form_data,
) -> bytes:
    """form_data dict를 받아 응급조치 실시 기록서 xlsx 바이너리를 반환한다."""
    data: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _write_title(ws, row)
    row = _write_meta(ws, row, data)
    row = _write_incident_overview(ws, row, data)
    row = _write_victim_info(ws, row, data)
    row = _write_first_aid_actions(ws, row, data)
    row = _write_equipment_log(ws, row, data)
    row = _write_transport_log(ws, row, data)
    row = _write_site_control(ws, row, data)
    row = _write_followup(ws, row, data)
    row = _write_signature(ws, row, data)
    write_cell(ws, row, 1, TOTAL_COLS, "", height=6)  # 하단 여백
    _finalize_sheet(ws)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

"""
콤프레샤·공압장비 사용계획서 — Excel 출력 모듈 (v1).

법적 근거:
  - 산업안전보건기준에 관한 규칙 제261조~제276조 (압력용기 사용제한·안전밸브·압력 표시)
  - 산업안전보건기준에 관한 규칙 제269조(공기저장탱크의 설치 등)
  - 산업안전보건기준에 관한 규칙 제297조(호스·배관 끼임·이탈 방지)
  - 산업안전보건기준에 관한 규칙 제512조~제517조(소음으로 인한 건강장해 방지)
분류: OPTIONAL — 법정 별지 서식 없음. 콤프레샤·공압장비 현장 실무 안전관리 보조서식.

form_type: compressor_pneumatic_equipment_plan
함수명:    build_compressor_pneumatic_equipment_plan(form_data)

Required form_data keys:
    site_name       str  현장명
    equipment_name  str  장비명/기종
    work_date       str  사용 일자

Optional form_data keys:
    project_name           str   공사명
    contractor             str   작업업체
    supervisor             str   작업책임자
    work_location          str   사용 장소
    work_purpose           str   사용 목적·작업 내용
    compressor_type        str   콤프레샤 유형 (왕복/스크루/베인 등)
    compressor_model       str   모델명·제조사
    compressor_serial_no   str   제조번호
    max_pressure           str   최고사용압력 (MPa/kgf/cm²)
    rated_pressure         str   정격 압력
    tank_capacity          str   공기저장탱크 용량 (L)
    motor_output           str   모터 출력 (kW)
    use_period             str   사용 기간
    operator_name          str   운전 담당자
    operator_license       str   자격·면허
    pressure_gauge_ok      str   압력계 정상 여부
    safety_valve_ok        str   안전밸브 작동 여부
    drain_valve_ok         str   드레인밸브 정상 여부
    tank_inspection_date   str   탱크 최근 점검일
    hose_condition         str   에어호스 상태
    coupler_condition      str   커플러·연결부 상태
    hose_tie_down          str   호스 고정·결박 여부
    pneumatic_tools        str   공압공구 종류·수량
    tool_max_pressure      str   공압공구 최고사용압력
    grounding_ok           str   접지 확인 여부
    power_supply           str   전원 공급 방식
    leakage_protection_ok  str   누전차단기 설치 여부
    noise_level            str   예상 소음 수준 (dB)
    hearing_protection     str   청력보호구 지급 여부
    dust_protection        str   분진 방호대책
    spray_prevention       str   비산 방지대책
    hose_blowout_measure   str   호스 이탈 방지 대책
    pressure_release_plan  str   압력 해제 절차
    depressure_before_work str   작업 전 압력 해제 확인
    stop_work_criteria     str   작업중지 기준
    emergency_contact      str   비상연락처
    emergency_procedure    str   비상 시 조치 절차
    prepared_by            str   작성자
    approver               str   승인자
    safety_steps           list[dict]  task_step, hazard, safety_measure, responsible
    inspection_items       list[dict]  check_item, ok, ng, action
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

DOC_ID    = "EQ-015"
FORM_TYPE = "compressor_pneumatic_equipment_plan"
SHEET_NAME    = "콤프레샤공압장비사용계획서"
SHEET_HEADING = "콤프레샤·공압장비 사용계획서"
SHEET_SUBTITLE = (
    "산업안전보건기준에 관한 규칙 제261조~제276조·제269조·제297조·제512조에 따른 "
    f"콤프레샤·공압장비 실무 안전관리 보조서식 ({DOC_ID})"
)

TOTAL_COLS = 8
_COL_WIDTHS: Dict[int, float] = {
    1: 14, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 10,
}

_L1, _V1S, _V1E = 1, 2, 4
_L2, _V2S, _V2E = 5, 6, 8

MAX_STEP_ROWS  = 10
MIN_STEP_ROWS  = 4
MAX_CHECK_ROWS = 10
MIN_CHECK_ROWS = 5

# ---------------------------------------------------------------------------
# 작업 전 점검 기본 항목 (데이터 없을 때 기본 표시)
# ---------------------------------------------------------------------------

DEFAULT_INSPECTION_ITEMS = [
    "압력계 정상 지시 여부 확인",
    "안전밸브 작동 상태 확인 (제266조)",
    "드레인밸브 개방·수분 제거",
    "공기저장탱크 외관 이상 여부 확인 (제269조)",
    "에어호스 균열·손상·이음부 점검",
    "커플러·연결부 체결 상태 확인",
    "호스 고정·결박 상태 확인",
    "공압공구 최고사용압력 초과 여부 확인",
    "접지선 연결 상태 확인",
    "누전차단기 설치·작동 확인",
    "소음 보호구(귀마개/귀덮개) 지급 확인 (제516조)",
    "비산·분진 방호 조치 확인",
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


# ---------------------------------------------------------------------------
# 섹션 렌더러
# ---------------------------------------------------------------------------

def _s_title(ws, row: int) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_SECTION, align=ALIGN_CENTER, height=28)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, height=18)
    return row + 1


def _s1_site(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "1. 공사/현장 기본정보")
    _lv(ws, row, "현장명",   v(d, "site_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",   v(d, "project_name"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업업체", v(d, "contractor"),   _L1, _V1S, _V1E)
    _lv(ws, row, "사용 일자", v(d, "work_date"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업책임자", v(d, "supervisor"), _L1, _V1S, _V1E)
    _lv(ws, row, "사용 기간", v(d, "use_period"),  _L2, _V2S, _V2E)
    return row + 1


def _s2_equip_basic(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "2. 장비 기본정보")
    _lv(ws, row, "장비명/기종",  v(d, "equipment_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "모델·제조사",  v(d, "compressor_model"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "콤프레샤 유형", v(d, "compressor_type"),  _L1, _V1S, _V1E)
    _lv(ws, row, "제조번호",      v(d, "compressor_serial_no"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "운전 담당자",  v(d, "operator_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "자격·면허",    v(d, "operator_license"), _L2, _V2S, _V2E)
    return row + 1


def _s3_location(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "3. 사용 장소 및 작업 내용")
    _lv(ws, row, "사용 장소", v(d, "work_location"), _L1, _V1S, _V1E)
    _lv(ws, row, "전원 공급", v(d, "power_supply"),  _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 1, "사용 목적·작업 내용",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=36)
    write_cell(ws, row, 2, TOTAL_COLS, v(d, "work_purpose"),
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 36
    return row + 1


def _s4_spec(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "4. 콤프레샤/공압장비 제원  (제265조 최고사용압력 표시)")
    _lv(ws, row, "최고사용압력", v(d, "max_pressure"),   _L1, _V1S, _V1E)
    _lv(ws, row, "정격 압력",    v(d, "rated_pressure"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "탱크 용량(L)",  v(d, "tank_capacity"), _L1, _V1S, _V1E)
    _lv(ws, row, "모터 출력(kW)", v(d, "motor_output"),  _L2, _V2S, _V2E)
    return row + 1


def _s5_pressure_device(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "5. 압력계·안전밸브·드레인 상태  (산안규칙 제266조·제269조)")
    _lv(ws, row, "압력계 정상 여부",  v(d, "pressure_gauge_ok") or "□ 정상  □ 이상",
        _L1, _V1S, _V1E)
    _lv(ws, row, "안전밸브 작동 여부", v(d, "safety_valve_ok") or "□ 정상  □ 이상",
        _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "드레인밸브 상태",   v(d, "drain_valve_ok") or "□ 정상  □ 이상",
        _L1, _V1S, _V1E)
    _lv(ws, row, "탱크 최근 점검일",  v(d, "tank_inspection_date"),
        _L2, _V2S, _V2E)
    return row + 1


def _s6_hose(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "6. 에어호스·커플러·연결부 점검  (산안규칙 제297조)")
    _lv(ws, row, "에어호스 상태",   v(d, "hose_condition") or "□ 양호  □ 불량",
        _L1, _V1S, _V1E)
    _lv(ws, row, "커플러·연결부 상태", v(d, "coupler_condition") or "□ 양호  □ 불량",
        _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "호스 고정·결박 여부", v(d, "hose_tie_down") or "□ 완료  □ 미완료",
        _L1, 2, TOTAL_COLS, height=24)
    return row + 1


def _s7_tools(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "7. 공압공구 사용계획")
    _lv(ws, row, "공압공구 종류·수량",   v(d, "pneumatic_tools"),     _L1, _V1S, _V1E)
    _lv(ws, row, "공구 최고사용압력",    v(d, "tool_max_pressure"),   _L2, _V2S, _V2E)
    return row + 1


def _s8_electrical(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "8. 전원·접지·누전보호 확인")
    _lv(ws, row, "접지 확인 여부",    v(d, "grounding_ok") or "□ 확인  □ 미확인",
        _L1, _V1S, _V1E)
    _lv(ws, row, "누전차단기 설치 여부", v(d, "leakage_protection_ok") or "□ 설치  □ 미설치",
        _L2, _V2S, _V2E)
    return row + 1


def _s9_noise_dust(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "9. 소음·비산·분진 관리대책  (산안규칙 제512조~제517조)")
    _lv(ws, row, "예상 소음(dB)",   v(d, "noise_level"),       _L1, _V1S, _V1E)
    _lv(ws, row, "청력보호구 지급", v(d, "hearing_protection") or "□ 지급  □ 미지급",
        _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "분진 방호대책",  v(d, "dust_protection"),   _L1, _V1S, _V1E)
    _lv(ws, row, "비산 방지대책",  v(d, "spray_prevention"),  _L2, _V2S, _V2E)
    return row + 1


def _s10_hose_pressure(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "10. 호스 이탈·파열·압력해제 안전대책  (산안규칙 제297조)")
    _lv(ws, row, "호스 이탈 방지 대책",
        v(d, "hose_blowout_measure") or "호스 안전핀·체인·고정클램프 설치",
        _L1, 2, TOTAL_COLS, height=28)
    row += 1
    _lv(ws, row, "압력 해제 절차",
        v(d, "pressure_release_plan") or "작업 전 탱크 압력 0으로 해제 후 호스 분리",
        _L1, 2, TOTAL_COLS, height=28)
    row += 1
    _lv(ws, row, "작업 전 압력 해제 확인",
        v(d, "depressure_before_work") or "□ 확인  □ 미확인",
        _L1, 2, TOTAL_COLS)
    return row + 1


def _s11_checklist(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "11. 작업 전 점검 체크리스트")

    hdr_spans = [(1, 1), (2, 5), (6, 6), (7, 7), (8, 8)]
    hdr_texts = ["번호", "점검 항목", "양호", "불량", "조치사항"]
    for (cs, ce), hdr in zip(hdr_spans, hdr_texts):
        write_cell(ws, row, cs, ce, hdr,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=20)
    row += 1

    raw = d.get("inspection_items")
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []

    if items:
        display = min(max(MIN_CHECK_ROWS, len(items)), MAX_CHECK_ROWS)
        for i in range(display):
            item = items[i] if i < len(items) else {}
            write_cell(ws, row, 1, 1, i + 1,               font=FONT_DEFAULT, align=ALIGN_CENTER, height=22)
            write_cell(ws, row, 2, 5, v(item, "check_item"), font=FONT_DEFAULT, align=ALIGN_LEFT)
            write_cell(ws, row, 6, 6, v(item, "ok"),          font=FONT_DEFAULT, align=ALIGN_CENTER)
            write_cell(ws, row, 7, 7, v(item, "ng"),           font=FONT_DEFAULT, align=ALIGN_CENTER)
            write_cell(ws, row, 8, 8, v(item, "action"),       font=FONT_SMALL,   align=ALIGN_LEFT)
            row += 1
    else:
        for i, item_text in enumerate(DEFAULT_INSPECTION_ITEMS):
            write_cell(ws, row, 1, 1, i + 1,       font=FONT_DEFAULT, align=ALIGN_CENTER, height=20)
            write_cell(ws, row, 2, 5, item_text,    font=FONT_DEFAULT, align=ALIGN_LEFT)
            write_cell(ws, row, 6, 6, "",            font=FONT_DEFAULT, align=ALIGN_CENTER)
            write_cell(ws, row, 7, 7, "",            font=FONT_DEFAULT, align=ALIGN_CENTER)
            write_cell(ws, row, 8, 8, "",            font=FONT_SMALL,   align=ALIGN_LEFT)
            row += 1
    return row


def _s12_edu_ppe(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "12. 작업자 교육 및 보호구")
    row = _notice(ws, row,
        "콤프레샤 고압·소음 작업 전 취급 방법 및 비상조치 교육 실시 필요. "
        "소음 노출 기준 초과 시 귀마개·귀덮개 착용 의무 (산안규칙 제516조).")
    write_cell(ws, row, 1, 1, "보호구",
               font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=32)
    write_cell(ws, row, 2, TOTAL_COLS,
               v(d, "ppe_issued") or "□ 귀마개  □ 귀덮개  □ 안전화  □ 보안경  □ 방진마스크",
               font=FONT_DEFAULT, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 32
    return row + 1


def _s13_emergency(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "13. 비상조치 및 작업중지 기준", fill=FILL_WARN)
    _lv(ws, row, "작업중지 기준",
        v(d, "stop_work_criteria") or "이상 소음·진동·압력 초과·호스 이탈 시 즉시 중단",
        _L1, 2, TOTAL_COLS, height=28)
    row += 1
    _lv(ws, row, "비상연락처",       v(d, "emergency_contact"),   _L1, _V1S, _V1E)
    row += 1
    _lv(ws, row, "비상 시 조치 절차",
        v(d, "emergency_procedure") or "전원 차단 → 압력 해제 → 대피 → 관리감독자 보고",
        _L1, 2, TOTAL_COLS, height=32)
    return row + 1


def _s14_sign(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "14. 승인/확인 서명")
    _lv(ws, row, "작성자", v(d, "prepared_by"), _L1, _V1S, _V1E, height=36)
    _lv(ws, row, "승인자", v(d, "approver"),    _L2, _V2S, _V2E)
    row += 1
    write_cell(ws, row, 1, 2, "서명", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=36)
    write_cell(ws, row, 3, 4, "",     font=FONT_DEFAULT, align=ALIGN_LEFT)
    write_cell(ws, row, 5, 6, "서명", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "",     font=FONT_DEFAULT, align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS,
               "본 서식은 관계 기관 공식 법정서식이 아닙니다. "
               "현장 조건·발주처·원청 기준에 따라 보완 적용한다.",
               font=FONT_NOTICE, fill=FILL_NOTICE, align=ALIGN_LEFT, height=24)
    return row + 1


# ---------------------------------------------------------------------------
# 메인 빌더
# ---------------------------------------------------------------------------

def build_compressor_pneumatic_equipment_plan(form_data: Dict[str, Any]) -> bytes:
    """form_data dict를 받아 콤프레샤·공압장비 사용계획서 xlsx 바이너리를 반환한다."""
    d: Dict[str, Any] = dict(form_data) if form_data else {}

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1
    row = _s_title(ws, row)
    row = _s1_site(ws, row, d)
    row = _s2_equip_basic(ws, row, d)
    row = _s3_location(ws, row, d)
    row = _s4_spec(ws, row, d)
    row = _s5_pressure_device(ws, row, d)
    row = _s6_hose(ws, row, d)
    row = _s7_tools(ws, row, d)
    row = _s8_electrical(ws, row, d)
    row = _s9_noise_dust(ws, row, d)
    row = _s10_hose_pressure(ws, row, d)
    row = _s11_checklist(ws, row, d)
    row = _s12_edu_ppe(ws, row, d)
    row = _s13_emergency(ws, row, d)
    _s14_sign(ws, row, d)

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

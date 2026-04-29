"""
궤도 작업계획서 — Excel 출력 모듈 (v1.0)  [WP-012]

법적 근거:
    산업안전보건기준에 관한 규칙 제38조 제1항 제12호
        — 궤도나 그 밖의 관련 설비의 보수·점검작업 시 작업계획서 작성 의무
    산업안전보건기준에 관한 규칙 제38조 제2항
        — 작업계획서 내용을 해당 근로자에게 주지시킬 의무
    산업안전보건기준에 관한 규칙 제38조 제4항
        — 궤도작업차량 사용 시 열차 운행관계자와 사전 협의 의무
    산업안전보건기준에 관한 규칙 별표 4
        — 사전조사 및 작업계획서 내용 (궤도 보수·점검작업 관련 항목)

분류: PRACTICAL — 법정 별지 서식 없음
      산안규칙 제38조 제1항 제12호 법정 작업계획서 의무 이행용 실무서식
      legal_status: legal (법정 의무 작성서식)
      궤도·철도 현장 한정 사용

역할 분리:
    WP-012 (본 서식): 궤도 보수·점검작업 전체 작업계획서
    PTW 계열: 개별 작업 허가 (WP와 별개)
    CL 계열: 작업 중·후 점검표

Required form_data keys:
    site_name          str  사업장명(현장명)
    work_date          str  작업 예정일
    supervisor         str  작업지휘자

Optional form_data keys:
    project_name            str  공사명
    contractor              str  도급사(시공사)
    subcontractor           str  하수급인
    prepared_by             str  작성자
    approved_by             str  승인자
    prepare_date            str  작성일
    -- 섹션2: 작업 구간 및 범위 --
    track_line              str  선로명(노선명)
    track_section_start     str  작업 구간 시점
    track_section_end       str  작업 구간 종점
    track_type              str  궤도 종류 (일반/고속/지하철 등)
    work_type               str  작업 종류 (선로 보수/레일 교체/침목 교체 등)
    work_scope              str  작업 범위 및 내용
    work_start_time         str  작업 개시 시간
    work_end_time           str  작업 종료 시간
    track_possession        str  선로 점용 여부 (점용/비점용)
    -- 섹션3: 사전조사 결과 (별표4) --
    track_condition         str  궤도 상태 사전조사 결과
    hazard_structures       str  인근 구조물·설비 현황
    train_schedule          str  열차 운행 시간표 확인 결과
    weather_condition       str  기상 조건 확인
    underground_facilities  str  지하매설물 현황
    survey_conducted_by     str  사전조사 수행자
    survey_date             str  사전조사 일자
    -- 섹션4: 작업 인원 --
    worker_count            str  작업 인원 수
    supervisor_name         str  작업지휘자 성명
    supervisor_cert         str  자격 사항
    safety_manager          str  안전담당자
    watchman_name           str  감시원 성명
    worker_list             str  작업원 명단(별첨 여부)
    -- 섹션5: 작업장비/궤도작업차량 --
    equipment_items         list[dict]  장비 목록 (equipment_type, model, count, operator, cert_no)
    rail_vehicle_used       str  궤도작업차량 사용 여부
    rail_vehicle_type       str  궤도작업차량 종류
    rail_vehicle_operator   str  운전자 성명 및 자격
    -- 섹션6: 열차 운행관계자 협의 (제38조 제4항) --
    rail_operator_name      str  열차 운행관계자(기관) 명칭
    consultation_date       str  협의 일시
    consultation_person     str  협의 담당자
    consultation_content    str  협의 내용
    work_window_granted     str  작업 시간대 승인 여부
    train_halt_required     str  열차 운행 중지 필요 여부
    train_halt_time         str  열차 운행 중지 시간대
    -- 섹션7: 신호·통신·감시 체계 --
    signal_method           str  신호 방법 (무선/신호기/수신호 등)
    communication_device    str  통신 수단
    watchman_position       str  감시원 배치 위치
    alarm_method            str  경보 방법
    evacuation_signal       str  대피 신호 방법
    -- 섹션8: 위험요인 및 안전대책 --
    hazard_items            list[dict]  위험요인별 대책 (hazard, measure, responsible)
    ppe_required            str  착용 보호구 목록
    access_prohibition      str  출입 금지 구역 설정 여부
    -- 섹션9: 작업 순서 및 출입통제 --
    work_sequence           str  작업 순서
    entry_control_method    str  출입 통제 방법
    barrier_type            str  방호 시설 종류 (차단봉/표지판/로프 등)
    restricted_zone         str  접근 제한 구역
    -- 섹션10: 비상대응 및 연락체계 --
    emergency_contact_119   str  119 신고 체계
    emergency_contact_rail  str  열차 운행 기관 비상 연락처
    emergency_contact_site  str  현장 비상 연락처
    evacuation_route        str  대피 경로
    first_aid_location      str  응급처치 장비 위치
    -- 섹션11: 근로자 주지 확인 (제38조 제2항) --
    worker_briefing_done    str  작업계획서 주지 여부
    briefing_date           str  주지 일시
    briefing_method         str  주지 방법
    worker_signatures       str  근로자 서명 여부(별첨)
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    FONT_TITLE, FONT_SUBTITLE, FONT_BOLD, FONT_DEFAULT, FONT_SMALL, FONT_NOTICE,
    FILL_LABEL, FILL_SECTION, FILL_HEADER, FILL_NONE,
    ALIGN_CENTER, ALIGN_LEFT, ALIGN_LABEL,
    v, write_cell, apply_col_widths, normalize_signature_row_heights,
)

DOC_ID        = "WP-012"
SHEET_NAME    = "궤도작업계획서"
SHEET_HEADING = "궤도 작업계획서"
SHEET_SUBTITLE = (
    "「산업안전보건기준에 관한 규칙」 제38조 제1항 제12호·제2항·제4항·별표4 "
    "— 궤도 보수·점검작업 법정 작업계획서"
)

TOTAL_COLS  = 8
MAX_EQUIP   = 6
MAX_HAZARD  = 8

_COL_WIDTHS: Dict[int, float] = {
    1: 16, 2: 14, 3: 12, 4: 12,
    5: 14, 6: 12, 7: 12, 8: 12,
}


def build_track_maintenance_workplan(form_data: Dict[str, Any]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.paperSize   = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth  = 1
    ws.print_title_rows = "1:2"  # 제목+부제 반복
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75

    apply_col_widths(ws, _COL_WIDTHS)

    row = 1

    # ── 제목 ──────────────────────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, align=ALIGN_CENTER, height=25)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, align=ALIGN_CENTER)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, f"[{DOC_ID}]  ※ 궤도·철도 현장 한정",
               font=FONT_SMALL, align=ALIGN_CENTER)
    row += 1
    row += 1  # 공백

    # ── 섹션1: 공사/작업 기본정보 ─────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 1. 공사/작업 기본정보",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "사업장명",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "site_name"),    align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "공사명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "project_name"), align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "도급사",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "contractor"),    align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "하수급인",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "subcontractor"), align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "작업 예정일", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "work_date"),     align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "작업지휘자",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "supervisor"),    align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "작성자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "prepared_by"),   align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "작성일",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "prepare_date"),  align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션2: 궤도 작업 구간 및 작업 범위 ───────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 2. 궤도 작업 구간 및 작업 범위",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "선로명(노선)", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "track_line"),    align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "궤도 종류",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "track_type"),    align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "구간 시점",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "track_section_start"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "구간 종점",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "track_section_end"),   align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "작업 종류",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "work_type"),     align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "선로 점용",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "track_possession"), align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "작업 개시",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "work_start_time"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "작업 종료",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "work_end_time"),   align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "작업 범위\n및 내용",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=36)
    write_cell(ws, row, 2, 8, v(form_data, "work_scope"), align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션3: 사전조사 결과 (별표4) ──────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS,
               "▣ 3. 사전조사 결과  (산안규칙 별표4 — 사전조사 및 작업계획서 내용)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "궤도 상태",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8, v(form_data, "track_condition"), align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "인근 구조물\n·설비 현황", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 8, v(form_data, "hazard_structures"), align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "열차 운행\n시간표 확인", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 8, v(form_data, "train_schedule"), align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "기상 조건",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "weather_condition"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "지하매설물",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "underground_facilities"), align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "사전조사자",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "survey_conducted_by"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "조사 일자",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "survey_date"), align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션4: 작업 인원 및 작업지휘자 ───────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 4. 작업 인원 및 작업지휘자",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "작업 인원",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "worker_count"),    align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "안전담당자",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "safety_manager"),  align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "작업지휘자",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "supervisor_name"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "자격 사항",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "supervisor_cert"), align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "감시원",      font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "watchman_name"),   align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "작업원 명단", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "worker_list"),     align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션5: 작업장비/궤도작업차량 ─────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS,
               "▣ 5. 작업장비/궤도작업차량 사용계획  (제38조 제4항 — 궤도작업차량 사전협의 의무)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "궤도작업차량\n사용 여부", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 4, v(form_data, "rail_vehicle_used"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "차량 종류",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "rail_vehicle_type"), align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "운전자/자격",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8, v(form_data, "rail_vehicle_operator"), align=ALIGN_LEFT)
    row += 1

    # 장비 목록 헤더
    write_cell(ws, row, 1, 2, "장비 종류",  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 4, "규격/모델",  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 5, "대수",       font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 7, "운전자",     font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 8, "자격증번호", font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    equip_items: List[Dict[str, Any]] = form_data.get("equipment_items", [])
    for idx in range(MAX_EQUIP):
        item = equip_items[idx] if idx < len(equip_items) else {}
        write_cell(ws, row, 1, 2, item.get("equipment_type",""), align=ALIGN_LEFT)
        write_cell(ws, row, 3, 4, item.get("model",""),           align=ALIGN_LEFT)
        write_cell(ws, row, 5, 5, item.get("count",""),           align=ALIGN_CENTER)
        write_cell(ws, row, 6, 7, item.get("operator",""),        align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, item.get("cert_no",""),         align=ALIGN_CENTER)
        row += 1
    row += 1  # 공백

    # ── 섹션6: 열차 운행관계자 협의 (제38조 제4항) ───────────────
    write_cell(ws, row, 1, TOTAL_COLS,
               "▣ 6. 열차 운행관계자 협의 사항  (산안규칙 제38조 제4항 — 사전 협의 의무)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "운행관계자\n기관명", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 4, v(form_data, "rail_operator_name"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "협의 일시",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "consultation_date"), align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "협의 담당자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "consultation_person"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "작업시간 승인", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "work_window_granted"), align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "협의 내용",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8, v(form_data, "consultation_content"), align=ALIGN_LEFT, height=36)
    row += 1
    write_cell(ws, row, 1, 1, "열차 운행\n중지 필요", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 4, v(form_data, "train_halt_required"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "중지 시간대", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "train_halt_time"),     align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션7: 신호·통신·감시 체계 ───────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 7. 신호·통신·감시 체계",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "신호 방법",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "signal_method"),     align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "통신 수단",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "communication_device"), align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "감시원 위치", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "watchman_position"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "경보 방법",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "alarm_method"),      align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "대피 신호",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8, v(form_data, "evacuation_signal"), align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션8: 위험요인 및 안전대책 ──────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 8. 위험요인 및 안전대책",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 4, "위험요인",  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 7, "안전대책",  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 8, "담당자",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    hazard_items: List[Dict[str, Any]] = form_data.get("hazard_items", [])
    for idx in range(MAX_HAZARD):
        item = hazard_items[idx] if idx < len(hazard_items) else {}
        write_cell(ws, row, 1, 4, item.get("hazard",""),      align=ALIGN_LEFT)
        write_cell(ws, row, 5, 7, item.get("measure",""),     align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, item.get("responsible",""), align=ALIGN_CENTER)
        row += 1

    write_cell(ws, row, 1, 1, "착용 보호구", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "ppe_required"),       align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "출입 금지\n구역 설정", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 6, 8, v(form_data, "access_prohibition"), align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션9: 작업 순서 및 출입통제 ─────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 9. 작업 순서 및 출입통제",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "작업 순서",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8, v(form_data, "work_sequence"),      align=ALIGN_LEFT, height=36)
    row += 1
    write_cell(ws, row, 1, 1, "출입 통제\n방법", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 4, v(form_data, "entry_control_method"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "방호 시설",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "barrier_type"),        align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "접근 제한\n구역", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 8, v(form_data, "restricted_zone"),     align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션10: 비상대응 및 연락체계 ─────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 10. 비상대응 및 연락체계",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "119 신고",    font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "emergency_contact_119"),  align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "철도기관\n비상연락", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 6, 8, v(form_data, "emergency_contact_rail"), align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "현장 비상\n연락처", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 4, v(form_data, "emergency_contact_site"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "대피 경로",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "evacuation_route"),       align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "응급처치\n장비 위치", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 8, v(form_data, "first_aid_location"),     align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션11: 근로자 주지 확인 (제38조 제2항) ──────────────────
    write_cell(ws, row, 1, TOTAL_COLS,
               "▣ 11. 근로자 주지 확인  (산안규칙 제38조 제2항 — 작업계획서 내용 주지 의무)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "주지 여부",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "worker_briefing_done"), align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "주지 일시",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "briefing_date"),        align=ALIGN_LEFT)
    row += 1
    write_cell(ws, row, 1, 1, "주지 방법",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "briefing_method"),      align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "근로자 서명",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "worker_signatures"),    align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션12: 승인/확인 서명 ────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 12. 승인/확인 서명",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "작성자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 3, v(form_data, "prepared_by"),   align=ALIGN_LEFT)
    write_cell(ws, row, 4, 4, "작업지휘자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 5, 6, v(form_data, "supervisor"),    align=ALIGN_LEFT)
    write_cell(ws, row, 7, 7, "승인자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 8, 8, v(form_data, "approved_by"),   align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "안전담당자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 3, v(form_data, "safety_manager"),  align=ALIGN_LEFT)
    write_cell(ws, row, 4, 4, "감시원",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 5, 6, v(form_data, "watchman_name"),   align=ALIGN_LEFT)
    write_cell(ws, row, 7, 7, "작성 일자",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 8, 8, v(form_data, "prepare_date"),    align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 법적 고지 ─────────────────────────────────────────────────
    write_cell(
        ws, row, 1, TOTAL_COLS,
        "※ 본 서식은 산업안전보건기준에 관한 규칙 제38조 제1항 제12호에 따른 법정 작업계획서 "
        "작성 의무 이행용 실무서식입니다. 관계 기관 공식 별지 서식이 아닙니다. "
        "궤도작업차량 사용 시 열차 운행관계자와 사전 협의(제38조 제4항)를 완료한 후 작업을 개시하십시오.",
        font=FONT_NOTICE, align=ALIGN_LEFT,
    )

    normalize_signature_row_heights(ws)
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.read()

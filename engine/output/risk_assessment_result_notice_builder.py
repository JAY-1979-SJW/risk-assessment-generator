"""
위험성평가 결과 근로자 공지문 — Excel 출력 모듈 (v1.0)  [RA-006]

법적 근거:
    산업안전보건법 제36조 제3항
        — 사업주는 위험성평가 결과를 근로자에게 알려야 함
    고용노동부고시 제2023-19호 제21조
        — 위험성평가 결과 및 조치사항을 근로자가 알 수 있도록 게시·공지 권고
    고용노동부고시 제2023-19호 제3조
        — 근로자 참여 보장 의무 (평가 결과 공유 포함)

역할 분리:
    RA-006 (본 서식): 위험성평가 결과를 근로자에게 공지·주지하는 게시용 증빙 서식
                      "무엇이 위험하고 어떻게 대처해야 하는가"를 근로자가 이해하도록 요약 공지
    RA-001: 개별 위험성평가표 (평가 실시 원본 기록 — 관리자 보관용)
    RA-005: 위험성평가 실시 규정 (운영 체계·절차·기준 규정서)
    RA-003: 위험성평가 참여 회의록 (근로자 참여 과정 기록)

분류: PRACTICAL — 법정 별지 서식 없음
      산안법 제36조 제3항 공지 의무 및 고용노동부고시 제2023-19호 제21조 이행용 현장 게시용 서식

Required form_data keys:
    site_name       str  사업장명(현장명)
    notice_date     str  공지 일자
    supervisor      str  관리감독자

Optional form_data keys:
    project_name        str  공사명
    company_name        str  사업자명
    safety_manager      str  안전관리자
    ra_ref_no           str  위험성평가 번호 (RA-001 참조)
    ra_date             str  위험성평가 실시일
    posting_period      str  게시 기간
    posting_location    str  게시 위치
    -- 섹션2: 공지 대상 작업/공정 --
    work_type           str  작업 공종
    work_location       str  작업 장소
    work_period         str  작업 기간
    target_workers      str  공지 대상 근로자
    -- 섹션3: 위험성평가 실시 개요 --
    ra_summary          str  평가 개요 (대상 공정, 참여자, 평가 방법)
    ra_participants     str  참여자 (관리감독자, 근로자 대표 등)
    ra_method           str  평가 방법 (빈도×강도 행렬법 등)
    total_hazards       str  총 유해·위험요인 수
    high_risk_count     str  높음 건수
    medium_risk_count   str  보통 건수
    low_risk_count      str  낮음 건수
    -- 섹션4~6: 위험요인·결과·대책 목록 --
    hazard_items        list[dict]  위험요인별 요약 (항목 아래 참조)
        hazard_no           str  번호
        hazard_name         str  유해·위험요인
        work_step           str  해당 작업 단계
        risk_level          str  위험성 수준 (높음/보통/낮음)
        risk_score          str  위험성 점수 (선택)
        measure             str  감소대책
        measure_status      str  이행 여부 (완료/진행중/예정)
        deadline            str  완료 예정일
    -- 섹션7: 작업 전 준수사항 --
    precaution_items    list[dict]  준수사항 목록 (no, precaution)
    -- 섹션8: 보호구 및 출입통제 --
    ppe_required        str  착용 의무 보호구 목록
    restricted_zone     str  출입 제한 구역
    access_condition    str  출입 조건
    -- 섹션9: 근로자 확인/서명 --
    worker_sign_items   list[dict]  근로자 확인 (name, position, date, sign)
    -- 섹션10: 게시 정보 --
    post_start_date     str  게시 시작일
    post_end_date       str  게시 종료일
    post_location_1     str  게시 위치 1
    post_location_2     str  게시 위치 2
    -- 섹션11: 관리감독자 확인 --
    confirm_date        str  확인 일자
    approver            str  승인자
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    FONT_TITLE, FONT_SUBTITLE, FONT_BOLD, FONT_DEFAULT, FONT_SMALL, FONT_NOTICE,
    FILL_LABEL, FILL_SECTION, FILL_HEADER, FILL_NONE, FILL_WARN,
    ALIGN_CENTER, ALIGN_LEFT, ALIGN_LABEL,
    v, write_cell, apply_col_widths, normalize_signature_row_heights,
)

DOC_ID        = "RA-006"
SHEET_NAME    = "위험성평가결과공지문"
SHEET_HEADING = "위험성평가 결과 근로자 공지문"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제36조 제3항(위험성평가 결과 주지) 및 "
    "고용노동부고시 제2023-19호 제21조(게시·공지 권고) 이행 서식"
)

TOTAL_COLS        = 9
MAX_HAZARDS       = 12
MAX_PRECAUTIONS   = 8
MAX_WORKER_SIGNS  = 10

_COL_WIDTHS: Dict[int, float] = {
    1: 6,  2: 14, 3: 12, 4: 10,
    5: 10, 6: 16, 7: 12, 8: 12, 9: 10,
}


def build_risk_assessment_result_notice(form_data: Dict[str, Any]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.paperSize  = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
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
    write_cell(ws, row, 1, TOTAL_COLS,
               f"[{DOC_ID}]  ※ 작업 현장 잘 보이는 곳에 게시하십시오",
               font=FONT_SMALL, align=ALIGN_CENTER)
    row += 1
    row += 1  # 공백

    # ── 섹션1: 공지 기본정보 ──────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 1. 공지 기본정보",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "현장명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 5, v(form_data, "site_name"),     align=ALIGN_LEFT)
    write_cell(ws, row, 6, 6, "공사명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 7, 9, v(form_data, "project_name"),  align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "공지 일자",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 5, v(form_data, "notice_date"),   align=ALIGN_LEFT)
    write_cell(ws, row, 6, 6, "안전관리자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 7, 9, v(form_data, "safety_manager"), align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "평가 번호",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 5, v(form_data, "ra_ref_no"),     align=ALIGN_LEFT)
    write_cell(ws, row, 6, 6, "평가 실시일", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 7, 9, v(form_data, "ra_date"),       align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션2: 공지 대상 작업/공정 ───────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 2. 공지 대상 작업/공정",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "작업 공종",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 5, v(form_data, "work_type"),     align=ALIGN_LEFT)
    write_cell(ws, row, 6, 6, "작업 장소",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 7, 9, v(form_data, "work_location"), align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "작업 기간",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 5, v(form_data, "work_period"),    align=ALIGN_LEFT)
    write_cell(ws, row, 6, 6, "공지 대상",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 7, 9, v(form_data, "target_workers"), align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션3: 위험성평가 실시 개요 ──────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 3. 위험성평가 실시 개요  (산안법 제36조, 고용노동부고시 제2023-19호)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "평가 방법",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 5, v(form_data, "ra_method") or "가능성(빈도)×중대성(강도) 행렬법",
               align=ALIGN_LEFT)
    write_cell(ws, row, 6, 6, "참여자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 7, 9, v(form_data, "ra_participants"), align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "평가 개요",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 9, v(form_data, "ra_summary"), align=ALIGN_LEFT, height=30)
    row += 1

    # 위험성 수준 집계
    write_cell(ws, row, 1, 1, "총 위험요인", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 3, v(form_data, "total_hazards"),    align=ALIGN_CENTER)
    write_cell(ws, row, 4, 4, "높음",        font=FONT_BOLD, fill=FILL_WARN, align=ALIGN_LABEL)
    write_cell(ws, row, 5, 5, v(form_data, "high_risk_count"),  align=ALIGN_CENTER, fill=FILL_WARN)
    write_cell(ws, row, 6, 6, "보통",        font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 7, 7, v(form_data, "medium_risk_count"), align=ALIGN_CENTER)
    write_cell(ws, row, 8, 8, "낮음",        font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 9, 9, v(form_data, "low_risk_count"),   align=ALIGN_CENTER)
    row += 1
    row += 1  # 공백

    # ── 섹션4~6: 위험요인·결과·대책 목록 ─────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS,
               "▣ 4~6. 주요 유해·위험요인 / 위험성 결정 결과 / 감소대책",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    # 헤더
    write_cell(ws, row, 1, 1, "No.",          font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 2, 3, "유해·위험요인\n(작업 단계)", font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER, height=36)
    write_cell(ws, row, 4, 5, "위험성\n수준·점수",         font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 7, "위험성 감소대책",            font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 8, "이행 여부",                  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 9, 9, "완료 예정",                  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    hazard_items: List[Dict[str, Any]] = form_data.get("hazard_items", [])
    for idx in range(1, MAX_HAZARDS + 1):
        item = hazard_items[idx - 1] if idx <= len(hazard_items) else {}
        lvl = item.get("risk_level", "")
        fill = FILL_WARN if lvl == "높음" else FILL_NONE
        hazard_info = item.get("hazard_name", "")
        if item.get("work_step"):
            hazard_info = f"{item['work_step']}\n{hazard_info}"
        risk_info = lvl
        if item.get("risk_score"):
            risk_info = f"{lvl}\n({item['risk_score']})"

        write_cell(ws, row, 1, 1, str(idx),                      align=ALIGN_CENTER, fill=fill, height=24)
        write_cell(ws, row, 2, 3, hazard_info,                    align=ALIGN_LEFT,   fill=fill)
        write_cell(ws, row, 4, 5, risk_info,                      align=ALIGN_CENTER, fill=fill)
        write_cell(ws, row, 6, 7, item.get("measure", ""),        align=ALIGN_LEFT)
        write_cell(ws, row, 8, 8, item.get("measure_status", ""), align=ALIGN_CENTER)
        write_cell(ws, row, 9, 9, item.get("deadline", ""),       align=ALIGN_CENTER)
        row += 1

    row += 1  # 공백

    # ── 섹션7: 작업 전 준수사항 ──────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 7. 작업 전 준수사항  ★ 반드시 확인하고 작업을 시작하십시오",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    default_precautions: List[Dict[str, str]] = [
        {"no": "①", "precaution": "작업 전 반드시 본 공지문을 확인하고 위험요인을 숙지하십시오."},
        {"no": "②", "precaution": "지정된 보호구를 반드시 착용하고 작업에 임하십시오."},
        {"no": "③", "precaution": "위험 구역 및 출입 제한 구역에는 허가 없이 접근하지 마십시오."},
        {"no": "④", "precaution": "이상 발견 시 즉시 작업을 중지하고 관리감독자에게 보고하십시오."},
    ]
    prec_items: List[Dict[str, Any]] = form_data.get("precaution_items") or default_precautions
    for idx in range(MAX_PRECAUTIONS):
        item = prec_items[idx] if idx < len(prec_items) else {}
        write_cell(ws, row, 1, 1, item.get("no", ""),         align=ALIGN_CENTER, height=22)
        write_cell(ws, row, 2, 9, item.get("precaution", ""), align=ALIGN_LEFT)
        row += 1
    row += 1  # 공백

    # ── 섹션8: 보호구 및 출입통제 ────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 8. 보호구 및 출입통제 사항",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "착용 의무\n보호구", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 9, v(form_data, "ppe_required"), align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "출입 제한\n구역", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 5, v(form_data, "restricted_zone"),  align=ALIGN_LEFT)
    write_cell(ws, row, 6, 6, "출입 조건",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 7, 9, v(form_data, "access_condition"), align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션9: 근로자 확인/서명 ──────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS,
               "▣ 9. 근로자 확인/서명  (산안법 제36조 제3항 — 공지 수령 확인)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 2, "성명",    font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 4, "직종/소속", font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 6, "확인 일자", font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 9, "서명",    font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    sign_items: List[Dict[str, Any]] = form_data.get("worker_sign_items", [])
    for idx in range(MAX_WORKER_SIGNS):
        item = sign_items[idx] if idx < len(sign_items) else {}
        write_cell(ws, row, 1, 2, item.get("name",""),     align=ALIGN_LEFT, height=20)
        write_cell(ws, row, 3, 4, item.get("position",""), align=ALIGN_LEFT)
        write_cell(ws, row, 5, 6, item.get("date",""),     align=ALIGN_CENTER)
        write_cell(ws, row, 7, 9, item.get("sign",""),     align=ALIGN_CENTER)
        row += 1
    row += 1  # 공백

    # ── 섹션10: 게시 위치 및 게시 기간 ──────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 10. 게시 위치 및 게시 기간  (고용노동부고시 제2023-19호 제21조)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "게시 시작일", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "post_start_date"),  align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "게시 종료일", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 9, v(form_data, "post_end_date"),    align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "게시 위치 1", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "post_location_1"),  align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "게시 위치 2", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 9, v(form_data, "post_location_2"),  align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션11: 관리감독자 확인 ──────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 11. 관리감독자 확인",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "관리감독자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "supervisor"),    align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "안전관리자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 7, v(form_data, "safety_manager"), align=ALIGN_LEFT)
    write_cell(ws, row, 8, 8, "승인자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 9, 9, v(form_data, "approver"),      align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "확인 일자",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 9, v(form_data, "confirm_date"),  align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 법적 고지 ─────────────────────────────────────────────────
    write_cell(
        ws, row, 1, TOTAL_COLS,
        "※ 본 서식은 산업안전보건법 제36조 제3항(위험성평가 결과 주지) 및 "
        "고용노동부고시 제2023-19호 제21조(결과 게시·공지) 이행을 위한 실무 서식입니다. "
        "관계 기관 공식 법정서식이 아닙니다. 개별 평가 원본(RA-001)과 함께 3년 이상 보존하십시오.",
        font=FONT_NOTICE, align=ALIGN_LEFT,
    )

    normalize_signature_row_heights(ws)
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.read()

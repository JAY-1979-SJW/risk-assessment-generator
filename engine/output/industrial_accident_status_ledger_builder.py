"""
산업재해 발생 현황 관리 대장 — Excel 출력 모듈 (v1.0)  [CM-007]

법적 근거:
    산업안전보건법 제57조 — 산업재해 기록·보존 의무
        (사망·3일 이상 휴업 재해 발생 시 해당 재해 내용 기록·보존 3년)
    산업안전보건법 시행규칙 제73조 — 산업재해 발생 기록 의무

역할 분리:
    CM-007 (본 서식): 현장 내 산업재해 발생 전체 현황을 집계·관리하는 대장
                      다수 재해를 연번으로 목록화하고 원인·대책·후속조치를 관리
    EM-001: 개별 재해에 대한 법정 조사표 (고용노동부 제출, 별지 제30호서식)
    EM-005: 특정 재해에 대한 원인 분석 및 재발방지 보고서 (심화 분석)

분류: PRACTICAL — 법정 별지 서식 없음
      산업안전보건법 제57조·시행규칙 제73조 기록·보존 의무 이행용 실무 관리 대장

Required form_data keys:
    site_name      str  사업장명(현장명)
    manager        str  관리책임자

Optional form_data keys:
    project_name        str  공사명
    company_name        str  사업자명
    period              str  관리 기간
    safety_manager      str  안전관리자
    prepared_date       str  작성일자
    approver            str  승인자
    accident_records    list[dict]  재해 발생 목록 (아래 항목 포함)
        no                  str  연번
        accident_date       str  발생 일시
        location            str  발생 장소
        worker_name         str  재해자 성명
        age                 str  연령
        gender              str  성별
        occupation          str  직종
        work_experience     str  경력
        affiliation         str  소속
        accident_type       str  재해 유형 (떨어짐/끼임/부딪힘 등)
        injury_type         str  상해 종류 (골절/타박상 등)
        injury_part         str  상해 부위
        severity            str  상해 정도 (사망/입원/통원/무휴업)
        sick_leave_days     str  요양일수
        work_content        str  작업 내용
        accident_cause      str  원인 분류 (불안전행동/불안전상태/관리적결함)
        cause_detail        str  세부 원인
        immediate_action    str  즉시 조치 사항
        em001_submitted     str  산업재해조사표 제출 여부
        prevention_measure  str  재발방지 대책
        followup_status     str  후속 조치 현황
        remarks             str  비고
    total_accidents     str  합계 재해 건수
    total_workers       str  합계 재해자 수
    total_fatality      str  사망자 수
    total_sick_leave    str  요양재해자 수
    total_no_leave      str  무휴업재해자 수
    summary_remarks     str  종합 비고
    supervisor_name     str  관리감독자
    confirm_date        str  확인일자
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    FONT_TITLE, FONT_SUBTITLE, FONT_BOLD, FONT_DEFAULT, FONT_SMALL, FONT_NOTICE,
    FILL_LABEL, FILL_SECTION, FILL_HEADER, FILL_NONE, FILL_WARN,
    ALIGN_CENTER, ALIGN_LEFT, ALIGN_LABEL,
    v, write_cell, apply_col_widths,
)

DOC_ID        = "CM-007"
SHEET_NAME    = "재해발생현황관리대장"
SHEET_HEADING = "산업재해 발생 현황 관리 대장"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제57조(산업재해 기록·보존), "
    "시행규칙 제73조 이행 관리 대장"
)

TOTAL_COLS   = 10
MAX_RECORDS  = 20

_COL_WIDTHS: Dict[int, float] = {
    1: 6,  2: 13, 3: 11, 4: 10, 5: 9,
    6: 9,  7: 11, 8: 11, 9: 12, 10: 14,
}


def build_industrial_accident_status_ledger(form_data: Dict[str, Any]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.paperSize  = ws.PAPERSIZE_A4
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth  = 1
    ws.page_margins.left   = 0.4
    ws.page_margins.right  = 0.4
    ws.page_margins.top    = 0.6
    ws.page_margins.bottom = 0.6

    apply_col_widths(ws, _COL_WIDTHS)

    row = 1

    # ── 제목 ──────────────────────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, align=ALIGN_CENTER, height=25)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, align=ALIGN_CENTER)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, f"[{DOC_ID}]",
               font=FONT_SMALL, align=ALIGN_CENTER)
    row += 1
    row += 1  # 공백

    # ── 섹션1: 사업장/현장 기본정보 ───────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 1. 사업장/현장 기본정보",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1,  1, "사업장명",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2,  4, v(form_data, "site_name"),    align=ALIGN_LEFT)
    write_cell(ws, row, 5,  5, "공사명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 10, v(form_data, "project_name"), align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1,  1, "사업자명",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2,  4, v(form_data, "company_name"), align=ALIGN_LEFT)
    write_cell(ws, row, 5,  5, "관리 기간",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 10, v(form_data, "period"),       align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1,  1, "관리책임자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2,  4, v(form_data, "manager"),       align=ALIGN_LEFT)
    write_cell(ws, row, 5,  5, "안전관리자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 10, v(form_data, "safety_manager"), align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션2~9: 재해 발생 현황 목록 (통합 테이블) ────────────────
    write_cell(ws, row, 1, TOTAL_COLS,
               "▣ 2~9. 재해 발생 현황 목록  (산안법 제57조·시행규칙 제73조 기록 의무)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    # 헤더 행 1
    hdrs1 = [
        (1, 1,  "연번"),
        (2, 2,  "발생일시"),
        (3, 3,  "발생장소"),
        (4, 5,  "재해자 기본정보"),
        (6, 6,  "직종/경력"),
        (7, 7,  "재해 유형"),
        (8, 8,  "상해 정도"),
        (9, 9,  "즉시조치/보고"),
        (10, 10, "재발방지/후속조치"),
    ]
    for c1, c2, label in hdrs1:
        write_cell(ws, row, c1, c2, label,
                   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    # 헤더 행 2 (세부)
    hdrs2 = [
        (1, 1,  ""),
        (2, 2,  "일시"),
        (3, 3,  "장소/작업내용"),
        (4, 4,  "성명/연령/성별"),
        (5, 5,  "소속/경력"),
        (6, 6,  "직종"),
        (7, 7,  "재해유형\n상해종류\n상해부위"),
        (8, 8,  "상해정도\n요양일수"),
        (9, 9,  "즉시조치\nEM-001제출"),
        (10, 10, "원인/대책\n후속조치"),
    ]
    for c1, c2, label in hdrs2:
        write_cell(ws, row, c1, c2, label,
                   font=FONT_SMALL, fill=FILL_HEADER, align=ALIGN_CENTER, height=40)
    row += 1

    # 데이터 행
    records: List[Dict[str, Any]] = form_data.get("accident_records", [])
    for idx in range(1, MAX_RECORDS + 1):
        rec = records[idx - 1] if idx <= len(records) else {}
        h = 30 if rec else 18

        worker_info = "\n".join(filter(None, [
            rec.get("worker_name",""), rec.get("age",""), rec.get("gender","")
        ]))
        affil_info = "\n".join(filter(None, [
            rec.get("affiliation",""), rec.get("work_experience","")
        ]))
        injury_info = "\n".join(filter(None, [
            rec.get("accident_type",""), rec.get("injury_type",""), rec.get("injury_part","")
        ]))
        severity_info = "\n".join(filter(None, [
            rec.get("severity",""), rec.get("sick_leave_days","")
        ]))
        action_info = "\n".join(filter(None, [
            rec.get("immediate_action",""), rec.get("em001_submitted","")
        ]))
        prevention_info = "\n".join(filter(None, [
            rec.get("cause_detail",""), rec.get("prevention_measure",""), rec.get("followup_status","")
        ]))
        loc_work = "\n".join(filter(None, [
            rec.get("location",""), rec.get("work_content","")
        ]))

        write_cell(ws, row, 1,  1,  str(idx) if rec else str(idx), align=ALIGN_CENTER, height=h)
        write_cell(ws, row, 2,  2,  rec.get("accident_date",""),   align=ALIGN_CENTER)
        write_cell(ws, row, 3,  3,  loc_work,                       align=ALIGN_LEFT)
        write_cell(ws, row, 4,  4,  worker_info,                    align=ALIGN_CENTER)
        write_cell(ws, row, 5,  5,  affil_info,                     align=ALIGN_CENTER)
        write_cell(ws, row, 6,  6,  rec.get("occupation",""),       align=ALIGN_CENTER)
        write_cell(ws, row, 7,  7,  injury_info,                    align=ALIGN_LEFT)
        write_cell(ws, row, 8,  8,  severity_info,                  align=ALIGN_CENTER)
        write_cell(ws, row, 9,  9,  action_info,                    align=ALIGN_LEFT)
        write_cell(ws, row, 10, 10, prevention_info,                align=ALIGN_LEFT)
        row += 1

    row += 1  # 공백

    # ── 집계 행 ───────────────────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 집계",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1,  1, "재해 건수",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2,  2, v(form_data, "total_accidents"),  align=ALIGN_CENTER)
    write_cell(ws, row, 3,  3, "재해자 수",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 4,  4, v(form_data, "total_workers"),    align=ALIGN_CENTER)
    write_cell(ws, row, 5,  5, "사망자 수",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6,  6, v(form_data, "total_fatality"),   align=ALIGN_CENTER)
    write_cell(ws, row, 7,  7, "요양재해자",    font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 8,  8, v(form_data, "total_sick_leave"), align=ALIGN_CENTER)
    write_cell(ws, row, 9,  9, "무휴업재해자",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 10, 10, v(form_data, "total_no_leave"),  align=ALIGN_CENTER)
    row += 1

    write_cell(ws, row, 1,  1, "종합 비고",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 10, v(form_data, "summary_remarks"),  align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션10: 관리감독자/안전관리자 확인 ───────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 10. 관리감독자/안전관리자 확인",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1,  1, "확인일자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2,  3, v(form_data, "confirm_date"),     align=ALIGN_LEFT)
    write_cell(ws, row, 4,  4, "작성자",       font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 5,  6, v(form_data, "prepared_date"),    align=ALIGN_LEFT)
    write_cell(ws, row, 7,  7, "승인자",       font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 8, 10, v(form_data, "approver"),         align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1,  1, "관리감독자",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2,  4, v(form_data, "supervisor_name"),  align=ALIGN_LEFT)
    write_cell(ws, row, 5,  5, "안전관리자",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6,  8, v(form_data, "safety_manager"),   align=ALIGN_LEFT)
    write_cell(ws, row, 9,  9, "관리책임자",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 10, 10, v(form_data, "manager"),         align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 법적 고지 ─────────────────────────────────────────────────
    write_cell(
        ws, row, 1, TOTAL_COLS,
        "※ 본 서식은 산업안전보건법 제57조(산업재해 기록·보존) 및 시행규칙 제73조 이행을 위한 "
        "실무 관리 대장입니다. 관계 기관 공식 법정서식이 아닙니다. "
        "개별 재해에 대한 법정 조사표(고용노동부 별지 제30호서식)는 EM-001을 사용하십시오.",
        font=FONT_NOTICE, align=ALIGN_LEFT,
    )

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.read()

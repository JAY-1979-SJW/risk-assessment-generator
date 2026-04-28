"""
위험성평가 실시 규정 — Excel 출력 모듈 (v1.0)  [RA-005]

법적 근거:
    산업안전보건법 제36조 — 위험성평가 실시 의무
    산업안전보건법 시행규칙 제37조 — 위험성평가의 방법·절차·시기
    고용노동부고시 제2023-19호 제9조 — 사업주는 위험성평가 실시 규정을 작성할 것을 권고

역할 분리:
    RA-005 (본 서식): 사업장 위험성평가 운영 체계 문서화
                      절차·역할·주기·추정기준·기록관리 방침을 규정하는 운영 규정서
    RA-001: 개별 위험성평가표 (실제 유해위험요인 기록·평가)
    RA-002: 위험성평가 관리 등록부 (평가 건수·현황 집계)
    RA-003: 위험성평가 참여 회의록 (근로자 참여 기록)
    RA-006: 위험성평가 결과 근로자 공지문 (결과 게시·공지)

분류: PRACTICAL — 법정 별지 서식 없음
      고용노동부고시 제2023-19호 제9조 실시규정 작성 권고 이행용 실무 규정서

Required form_data keys:
    company_name    str  사업장명
    established_by  str  작성/제정자
    issue_date      str  제정일

Optional form_data keys:
    doc_no              str  문서 번호
    revision            str  개정번호
    revision_date       str  개정일
    approver            str  승인자
    reviewer            str  검토자
    applicable_site     str  적용 현장명
    -- 섹션2: 목적 및 적용범위 --
    purpose             str  목적
    scope               str  적용범위
    -- 섹션3: 용어 정의 --
    term_items          list[dict]  용어 목록 (term, definition)
    -- 섹션4: 책임과 권한 --
    role_items          list[dict]  역할/책임 목록 (role, responsibility)
    -- 섹션5: 위험성평가 실시 시기 --
    timing_initial      str  최초 평가 실시 시기
    timing_regular      str  정기 평가 주기 (1회/년 이상)
    timing_occasional   str  수시 평가 실시 조건
    timing_tbm          str  TBM 등 상시 평가 시행 여부
    -- 섹션6: 위험성평가 절차 --
    step_items          list[dict]  절차 단계 (step_no, step_name, description, responsible)
    -- 섹션7: 위험성 추정 및 결정 기준 --
    risk_matrix_desc    str  위험성 추정 방법 설명 (빈도×강도 행렬 등)
    risk_level_high     str  위험성 결정 기준 — 높음 (즉시 작업중지)
    risk_level_medium   str  위험성 결정 기준 — 보통 (개선 기한 지정)
    risk_level_low      str  위험성 결정 기준 — 낮음 (지속 관리)
    acceptable_level    str  허용 가능한 위험성 수준
    -- 섹션8: 감소대책 수립 및 실행 --
    measure_priority    str  위험성 감소대책 우선순위 원칙
    measure_tracking    str  감소대책 이행 추적 방법
    measure_verify      str  이행 완료 확인 방법
    -- 섹션9: 근로자 참여 및 교육 --
    participation_method  str  근로자 참여 방법
    education_timing      str  교육 실시 시기
    education_content     str  교육 내용
    -- 섹션10: 기록 작성·보존·공지 --
    record_items        list[dict]  기록 목록 (record_name, form_id, retention_period, storage)
    disclosure_method   str  근로자 공지 방법
    -- 섹션11: 수시/정기 검토 및 개정관리 --
    review_cycle        str  정기 검토 주기
    review_trigger      str  수시 검토 조건
    revision_procedure  str  개정 절차
    revision_history    list[dict]  개정 이력 (rev_no, date, description, author)
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    FONT_TITLE, FONT_SUBTITLE, FONT_BOLD, FONT_DEFAULT, FONT_SMALL, FONT_NOTICE,
    FILL_LABEL, FILL_SECTION, FILL_HEADER, FILL_NONE,
    ALIGN_CENTER, ALIGN_LEFT, ALIGN_LABEL,
    v, write_cell, apply_col_widths,
)

DOC_ID        = "RA-005"
SHEET_NAME    = "위험성평가실시규정"
SHEET_HEADING = "위험성평가 실시 규정"
SHEET_SUBTITLE = (
    "「산업안전보건법」 제36조·시행규칙 제37조 및 "
    "고용노동부고시 제2023-19호 제9조에 따른 위험성평가 실시 규정"
)

TOTAL_COLS     = 8
MAX_TERMS      = 8
MAX_ROLES      = 8
MAX_STEPS      = 10
MAX_RECORDS    = 8
MAX_REVISIONS  = 6

_COL_WIDTHS: Dict[int, float] = {
    1: 18, 2: 14, 3: 14, 4: 12,
    5: 14, 6: 14, 7: 12, 8: 12,
}


def build_risk_assessment_procedure(form_data: Dict[str, Any]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.paperSize  = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
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
    write_cell(ws, row, 1, TOTAL_COLS, f"[{DOC_ID}]",
               font=FONT_SMALL, align=ALIGN_CENTER)
    row += 1
    row += 1  # 공백

    # ── 섹션1: 문서 기본정보 ───────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 1. 문서 기본정보",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "사업장명",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "company_name"),    align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "적용 현장",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "applicable_site"), align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "문서 번호",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "doc_no"),          align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "개정번호",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "revision"),        align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "제정일",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4, v(form_data, "issue_date"),      align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "개정일",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8, v(form_data, "revision_date"),   align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "작성자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 3, v(form_data, "established_by"),  align=ALIGN_LEFT)
    write_cell(ws, row, 4, 4, "검토자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 5, 6, v(form_data, "reviewer"),        align=ALIGN_LEFT)
    write_cell(ws, row, 7, 7, "승인자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 8, 8, v(form_data, "approver"),        align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션2: 목적 및 적용범위 ───────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 2. 목적 및 적용범위  (산안법 제36조)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    purpose_default = (
        "본 규정은 산업안전보건법 제36조 및 고용노동부고시 제2023-19호에 따라 "
        "사업장 내 유해·위험요인을 파악하고 위험성을 결정하여 감소대책을 수립·이행함으로써 "
        "근로자의 안전·보건을 확보함을 목적으로 한다."
    )
    write_cell(ws, row, 1, 1, "목적",       font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8, v(form_data, "purpose") or purpose_default,
               align=ALIGN_LEFT, height=36)
    row += 1

    scope_default = "본 규정은 해당 사업장(현장) 내 모든 작업 공정 및 협력업체 근로자에게 적용한다."
    write_cell(ws, row, 1, 1, "적용범위",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8, v(form_data, "scope") or scope_default,
               align=ALIGN_LEFT, height=30)
    row += 1
    row += 1  # 공백

    # ── 섹션3: 용어 정의 ──────────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 3. 용어 정의  (고용노동부고시 제2023-19호 제2조)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 2, "용어",       font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 8, "정의",       font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    default_terms: List[Dict[str, str]] = [
        {"term": "위험성평가",     "definition": "사업주가 스스로 유해·위험요인을 파악하고 위험성 수준을 결정하여 감소대책을 수립·이행하는 과정"},
        {"term": "유해·위험요인", "definition": "유해·위험을 일으킬 잠재적 가능성이 있는 것의 고유한 특징이나 속성"},
        {"term": "위험성",        "definition": "유해·위험요인이 부상 또는 질병으로 이어질 수 있는 가능성(빈도)과 중대성(강도)을 조합한 것"},
        {"term": "허용 가능한 위험성", "definition": "현재의 기술 수준과 여건상 이 이상의 감소가 합리적으로 실현 불가능한 위험성"},
    ]
    term_items: List[Dict[str, Any]] = form_data.get("term_items") or default_terms
    for idx in range(MAX_TERMS):
        item = term_items[idx] if idx < len(term_items) else {}
        write_cell(ws, row, 1, 2, item.get("term",""),       align=ALIGN_LEFT)
        write_cell(ws, row, 3, 8, item.get("definition",""), align=ALIGN_LEFT)
        row += 1
    row += 1  # 공백

    # ── 섹션4: 책임과 권한 ────────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 4. 책임과 권한  (산안법 제36조 제1항·제3항)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 2, "역할",       font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 8, "책임 및 권한", font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    default_roles: List[Dict[str, str]] = [
        {"role": "사업주(대표)",     "responsibility": "위험성평가 총괄, 실시 규정 승인, 자원 지원"},
        {"role": "안전관리자",       "responsibility": "위험성평가 실시 계획·지원, 결과 검토, 기록 보존"},
        {"role": "관리감독자",       "responsibility": "소관 작업 위험성평가 주도, 감소대책 이행 확인"},
        {"role": "근로자",           "responsibility": "유해·위험요인 발굴 참여, 감소대책 이행"},
    ]
    role_items: List[Dict[str, Any]] = form_data.get("role_items") or default_roles
    for idx in range(MAX_ROLES):
        item = role_items[idx] if idx < len(role_items) else {}
        write_cell(ws, row, 1, 2, item.get("role",""),           align=ALIGN_LEFT)
        write_cell(ws, row, 3, 8, item.get("responsibility",""), align=ALIGN_LEFT)
        row += 1
    row += 1  # 공백

    # ── 섹션5: 위험성평가 실시 시기 ──────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS,
               "▣ 5. 위험성평가 실시 시기  (시행규칙 제37조 제1항·고용노동부고시 제2023-19호 제15조)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "최초 평가",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "timing_initial") or "사업 개시 후 1개월 이내 또는 신규 공정 도입 시",
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "정기 평가",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "timing_regular") or "매년 1회 이상 (전년도 위험성평가 결과를 반영하여 실시)",
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "수시 평가",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "timing_occasional") or (
                   "① 중대재해·산업재해 발생 시  ② 작업 방법·설비·원자재 변경 시  "
                   "③ 건설물·기계·설비 신설·이전 시  ④ 법령 개정으로 기준 변경 시"
               ),
               align=ALIGN_LEFT, height=30)
    row += 1

    write_cell(ws, row, 1, 1, "상시 평가",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "timing_tbm") or "TBM(Tool Box Meeting) 등 작업 전 일상적 위험성 확인 포함",
               align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션6: 위험성평가 절차 ────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS,
               "▣ 6. 위험성평가 절차  (고용노동부고시 제2023-19호 제10조~제14조)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "단계",       font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 2, 2, "절차명",     font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 6, "내용",       font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "담당자",     font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    default_steps: List[Dict[str, str]] = [
        {"step_no": "1", "step_name": "사전준비",        "description": "평가 대상 공정 선정, 관련 자료(공정도·작업절차서·MSDS) 수집, 팀 구성", "responsible": "안전관리자"},
        {"step_no": "2", "step_name": "유해·위험요인 파악", "description": "작업 현장 순회, 근로자 면담, 사고 이력 분석을 통한 유해·위험요인 도출", "responsible": "관리감독자+근로자"},
        {"step_no": "3", "step_name": "위험성 추정",      "description": "가능성(빈도)×중대성(강도) 행렬로 위험성 수준 산정", "responsible": "관리감독자"},
        {"step_no": "4", "step_name": "위험성 결정",      "description": "허용 가능 수준과 비교하여 감소대책 필요 여부 결정", "responsible": "사업주·안전관리자"},
        {"step_no": "5", "step_name": "감소대책 수립",    "description": "제거→대체→공학적→관리적→PPE 순으로 감소대책 수립", "responsible": "관리감독자"},
        {"step_no": "6", "step_name": "감소대책 이행",    "description": "기한 내 감소대책 실행 및 이행 완료 확인", "responsible": "관리감독자"},
        {"step_no": "7", "step_name": "결과 기록·공지",   "description": "평가 결과 기록 보존(3년), 근로자에게 공지", "responsible": "안전관리자"},
    ]
    step_items: List[Dict[str, Any]] = form_data.get("step_items") or default_steps
    for idx in range(MAX_STEPS):
        item = step_items[idx] if idx < len(step_items) else {}
        write_cell(ws, row, 1, 1, item.get("step_no",""),   align=ALIGN_CENTER)
        write_cell(ws, row, 2, 2, item.get("step_name",""), align=ALIGN_LEFT)
        write_cell(ws, row, 3, 6, item.get("description",""), align=ALIGN_LEFT)
        write_cell(ws, row, 7, 8, item.get("responsible",""), align=ALIGN_CENTER)
        row += 1
    row += 1  # 공백

    # ── 섹션7: 위험성 추정 및 결정 기준 ──────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 7. 위험성 추정 및 결정 기준  (고용노동부고시 제2023-19호 제12조·제13조)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "추정 방법",  font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "risk_matrix_desc") or "가능성(빈도) × 중대성(강도) 행렬법 적용. 각 3단계(상/중/하) 조합으로 9단계 위험성 수준 산정.",
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "높음 (즉시)", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "risk_level_high") or "즉시 작업 중지, 감소대책 완료 전 재개 금지 (가능성·중대성 모두 상)",
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "보통 (개선)", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "risk_level_medium") or "기한을 정해 감소대책 수립·이행 필요 (중간 수준)",
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "낮음 (관리)", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "risk_level_low") or "현재 대책 유지, 지속 모니터링 (가능성·중대성 모두 하)",
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "허용 가능\n위험성 수준", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 8,
               v(form_data, "acceptable_level") or "낮음 이하 (현 기술·여건상 추가 감소가 합리적으로 실현 불가능한 수준)",
               align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션8: 감소대책 수립 및 실행 ─────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 8. 감소대책 수립 및 실행  (고용노동부고시 제2023-19호 제14조)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "우선순위\n원칙", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=36)
    write_cell(ws, row, 2, 8,
               v(form_data, "measure_priority") or (
                   "① 제거(위험원 원천 제거)  "
                   "② 대체(저위험 물질·공정으로 교체)  "
                   "③ 공학적 대책(격리·방호)  "
                   "④ 관리적 대책(교육·절차 변경)  "
                   "⑤ 개인보호구(PPE) 지급"
               ),
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "이행 추적", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "measure_tracking") or "위험성평가 관리 등록부(RA-002)에 담당자·기한·완료일 기재 후 추적",
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "완료 확인", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "measure_verify") or "관리감독자 현장 확인 후 서명, 안전관리자 최종 검토",
               align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션9: 근로자 참여 및 교육 ───────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 9. 근로자 참여 및 교육  (산안법 제36조 제3항·고용노동부고시 제2023-19호 제3조)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "참여 방법", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "participation_method") or "위험성평가 참여 회의록(RA-003) 작성, TBM 시 유해·위험요인 발굴 의견 제출",
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "교육 시기", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 4,
               v(form_data, "education_timing") or "평가 실시 전·후 및 감소대책 변경 시",
               align=ALIGN_LEFT)
    write_cell(ws, row, 5, 5, "교육 내용", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 6, 8,
               v(form_data, "education_content") or "위험성평가 절차, 유해·위험요인, 감소대책",
               align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션10: 기록 작성·보존·공지 ──────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS,
               "▣ 10. 기록 작성·보존·공지  (시행규칙 제37조 제2항 — 기록 3년 보존)",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 2, "기록 명칭",  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 3, 3, "서식 ID",    font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 4, 5, "보존 기간",  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 6, 8, "보관 장소",  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    default_records: List[Dict[str, str]] = [
        {"record_name": "위험성평가표",           "form_id": "RA-001", "retention_period": "3년", "storage": "현장 사무실/전산 시스템"},
        {"record_name": "위험성평가 관리 등록부", "form_id": "RA-002", "retention_period": "3년", "storage": "현장 사무실/전산 시스템"},
        {"record_name": "위험성평가 참여 회의록", "form_id": "RA-003", "retention_period": "3년", "storage": "현장 사무실"},
        {"record_name": "근로자 공지 확인서",     "form_id": "RA-006", "retention_period": "3년", "storage": "현장 사무실"},
    ]
    record_items: List[Dict[str, Any]] = form_data.get("record_items") or default_records
    for idx in range(MAX_RECORDS):
        item = record_items[idx] if idx < len(record_items) else {}
        write_cell(ws, row, 1, 2, item.get("record_name",""),     align=ALIGN_LEFT)
        write_cell(ws, row, 3, 3, item.get("form_id",""),         align=ALIGN_CENTER)
        write_cell(ws, row, 4, 5, item.get("retention_period",""), align=ALIGN_CENTER)
        write_cell(ws, row, 6, 8, item.get("storage",""),         align=ALIGN_LEFT)
        row += 1

    write_cell(ws, row, 1, 1, "공지 방법", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "disclosure_method") or "현장 게시판 게시(RA-006), TBM 시 구두 공지, 작업 전 회의 활용",
               align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 섹션11: 수시/정기 검토 및 개정관리 ───────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 11. 수시/정기 검토 및 개정관리",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "정기 검토\n주기", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 8,
               v(form_data, "review_cycle") or "연 1회 정기 검토 (매년 위험성평가 실시 전)",
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "수시 검토\n조건", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL, height=30)
    write_cell(ws, row, 2, 8,
               v(form_data, "review_trigger") or "법령 개정, 중대재해 발생, 공정 변경, 위험성평가 결과의 현저한 변화 시",
               align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "개정 절차", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 8,
               v(form_data, "revision_procedure") or "담당자 초안 작성 → 안전관리자 검토 → 사업주(대표) 승인 → 배포·시행",
               align=ALIGN_LEFT)
    row += 1

    # 개정 이력 테이블
    write_cell(ws, row, 1, 1, "개정번호",   font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 2, 3, "개정일",     font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 4, 6, "개정 내용",  font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    write_cell(ws, row, 7, 8, "작성자",     font=FONT_BOLD, fill=FILL_HEADER, align=ALIGN_CENTER)
    row += 1

    revision_history: List[Dict[str, Any]] = form_data.get("revision_history", [])
    for idx in range(MAX_REVISIONS):
        item = revision_history[idx] if idx < len(revision_history) else {}
        write_cell(ws, row, 1, 1, item.get("rev_no",""),     align=ALIGN_CENTER)
        write_cell(ws, row, 2, 3, item.get("date",""),       align=ALIGN_CENTER)
        write_cell(ws, row, 4, 6, item.get("description",""), align=ALIGN_LEFT)
        write_cell(ws, row, 7, 8, item.get("author",""),     align=ALIGN_CENTER)
        row += 1
    row += 1  # 공백

    # ── 섹션12: 승인/확인 서명 ────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, "▣ 12. 승인/확인 서명",
               font=FONT_BOLD, fill=FILL_SECTION)
    row += 1

    write_cell(ws, row, 1, 1, "작성자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 3, v(form_data, "established_by"), align=ALIGN_LEFT)
    write_cell(ws, row, 4, 4, "검토자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 5, 6, v(form_data, "reviewer"),       align=ALIGN_LEFT)
    write_cell(ws, row, 7, 7, "승인자",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 8, 8, v(form_data, "approver"),       align=ALIGN_LEFT)
    row += 1

    write_cell(ws, row, 1, 1, "제정일",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, 3, v(form_data, "issue_date"),     align=ALIGN_LEFT)
    write_cell(ws, row, 4, 4, "개정일",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 5, 6, v(form_data, "revision_date"),  align=ALIGN_LEFT)
    write_cell(ws, row, 7, 7, "개정번호",   font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 8, 8, v(form_data, "revision"),       align=ALIGN_LEFT)
    row += 1
    row += 1  # 공백

    # ── 법적 고지 ─────────────────────────────────────────────────
    write_cell(
        ws, row, 1, TOTAL_COLS,
        "※ 본 서식은 고용노동부고시 제2023-19호 제9조 위험성평가 실시 규정 작성 권고에 따른 "
        "실무 운영 규정서입니다. 관계 기관 공식 법정서식이 아닙니다. "
        "개별 위험성평가 기록(RA-001)·관리 등록부(RA-002)·참여 회의록(RA-003)·공지문(RA-006)과 함께 사용하십시오.",
        font=FONT_NOTICE, align=ALIGN_LEFT,
    )

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.read()

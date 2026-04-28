"""
밀폐공간 가스농도 측정기록표 — 부대서류 Excel 출력 모듈 (v1).

밀폐공간 작업 전·중·후 산소 및 유해가스 농도 측정 결과를 기록하는 부대서류.
산업안전보건기준에 관한 규칙(밀폐공간 작업 관련 조항) 기준.

document_catalog.yml 및 form_registry.py에 등록하지 않음.
supplementary_registry.py를 통해 관리.

supplemental_type: confined_space_gas_measurement
함수명:            build_confined_space_gas_measurement(form_data)

Required form_data keys:
    site_name       str  현장명
    work_date       str  작업 일자
    work_location   str  밀폐공간 위치

Optional form_data keys:
    permit_no           str   작업허가서 번호 (예: PTW-001)
    parent_doc_id       str   연결 문서 ID
    parent_doc_name     str   연결 문서명
    parent_form_type    str   연결 form_type
    project_name        str   공사명
    company_name        str   회사명
    work_description    str   작업 내용
    equipment_type      str   측정기기 종류
    equipment_model     str   측정기기 모델
    equipment_cert_no   str   검교정 번호
    equipment_cert_date str   검교정 유효기간
    measurer            str   측정자 성명
    measurer_position   str   측정자 직책
    measurer_contact    str   측정자 연락처
    o2_std_min          str   산소농도 정상 하한 (기본: 18%)
    o2_std_max          str   산소농도 정상 상한 (기본: 23.5%)
    h2s_std             str   황화수소 허용기준 (기본: 10 ppm 이하)
    co_std              str   일산화탄소 허용기준 (기본: 30 ppm 이하)
    lel_std             str   가연성가스 허용기준 (기본: 10% LEL 이하)
    co2_std             str   이산화탄소 허용기준
    ventilation_done    str   환기 실시 여부
    ventilation_method  str   환기 방법
    work_possible       str   작업 가능 여부 판정
    work_possible_by    str   판정자
    emergency_plan      str   비상조치 계획
    confirmer           str   확인자 성명
    confirmer_position  str   확인자 직책
    confirm_date        str   확인 일자
    remarks             str   비고

    measure_records  list[dict]  측정 기록 목록 (repeat, 최대 12건)
        각 항목:
            no           int|str  순번
            datetime     str      측정일시
            location     str      측정위치
            o2           str      산소농도 (%)
            h2s          str      황화수소 (ppm)
            co           str      일산화탄소 (ppm)
            lel          str      가연성가스 (% LEL)
            co2          str      이산화탄소 (%)
            ventilation  str      환기상태 (실시/미실시)
            judgment     str      판정 (적합/부적합)
            measurer     str      측정자
            remarks      str      비고
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook
from openpyxl.styles import Alignment

from engine.output.excel_style_helpers import (
    ALIGN_CENTER, ALIGN_LABEL, ALIGN_LEFT,
    FILL_HEADER, FILL_LABEL, FILL_NONE, FILL_NOTICE, FILL_SECTION, FILL_WARN,
    FONT_BOLD, FONT_DEFAULT, FONT_NOTICE, FONT_SMALL, FONT_SUBTITLE, FONT_TITLE,
    apply_col_widths, v, write_cell,
)

SUPPLEMENTAL_TYPE = "confined_space_gas_measurement"
SHEET_NAME        = "가스농도측정기록표"
SHEET_HEADING     = "밀폐공간 가스농도 측정기록표"
SHEET_SUBTITLE    = (
    "밀폐공간 작업 전·중·후 산소 및 유해가스 농도 측정 결과 기록  "
    "[confined_space_gas_measurement]  부대서류"
)

TOTAL_COLS      = 12
MAX_MEASURE_ROWS = 12

# A4 가로 권장 — 열 12개 분산
_COL_WIDTHS: Dict[int, float] = {
    1:  5,   # 순번
    2:  14,  # 측정일시
    3:  12,  # 측정위치
    4:  8,   # 산소농도(%)
    5:  8,   # 황화수소(ppm)
    6:  8,   # 일산화탄소(ppm)
    7:  9,   # 가연성가스(%LEL)
    8:  8,   # 이산화탄소(%)
    9:  9,   # 환기상태
    10: 9,   # 판정
    11: 10,  # 측정자
    12: 12,  # 비고
}

_JUDGMENT_FILL = {
    "적합":   FILL_HEADER,
    "부적합": FILL_WARN,
}

_VENTILATION_FILL = {
    "실시":   FILL_NONE,
    "미실시": FILL_NOTICE,
}


# ---------------------------------------------------------------------------
# 기본 측정 예시 (데이터 없을 때 표시)
# ---------------------------------------------------------------------------

DEFAULT_MEASURE_RECORDS: List[Dict[str, Any]] = [
    {"no": "1", "datetime": "", "location": "하부(바닥면)", "o2": "", "h2s": "",
     "co": "", "lel": "", "co2": "", "ventilation": "", "judgment": "", "measurer": "", "remarks": ""},
    {"no": "2", "datetime": "", "location": "중간(작업면)", "o2": "", "h2s": "",
     "co": "", "lel": "", "co2": "", "ventilation": "", "judgment": "", "measurer": "", "remarks": ""},
    {"no": "3", "datetime": "", "location": "상부(입구면)", "o2": "", "h2s": "",
     "co": "", "lel": "", "co2": "", "ventilation": "", "judgment": "", "measurer": "", "remarks": ""},
]


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _two_col(ws, row: int,
             label1: str, val1: Any,
             label2: str, val2: Any,
             span1: int = 2, span2: int = 2,
             height: float = 20) -> int:
    write_cell(ws, row, 1,           1,           label1, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2,           1 + span1,   val1,   font=FONT_DEFAULT, fill=FILL_NONE,  align=ALIGN_LEFT)
    write_cell(ws, row, 2 + span1,   2 + span1,   label2, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 3 + span1,   3 + span1 + span2 - 1, val2, font=FONT_DEFAULT, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height
    return row + 1


def _four_col(ws, row: int,
              l1: str, v1: Any,
              l2: str, v2: Any,
              l3: str, v3: Any,
              l4: str, v4: Any,
              height: float = 20) -> int:
    write_cell(ws, row, 1,  1,  l1, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2,  3,  v1, font=FONT_DEFAULT, fill=FILL_NONE,  align=ALIGN_LEFT)
    write_cell(ws, row, 4,  4,  l2, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 5,  6,  v2, font=FONT_DEFAULT, fill=FILL_NONE,  align=ALIGN_LEFT)
    write_cell(ws, row, 7,  7,  l3, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 8,  9,  v3, font=FONT_DEFAULT, fill=FILL_NONE,  align=ALIGN_LEFT)
    write_cell(ws, row, 10, 10, l4, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 11, 12, v4, font=FONT_DEFAULT, fill=FILL_NONE,  align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height
    return row + 1


def _full_row(ws, row: int, label: str, val: Any, height: float = 20) -> int:
    write_cell(ws, row, 1, 1, label, font=FONT_BOLD,    fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, 2, TOTAL_COLS, val, font=FONT_DEFAULT, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = height
    return row + 1


def _section_header(ws, row: int, title: str) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, title,
               font=FONT_BOLD, fill=FILL_SECTION, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 20
    return row + 1


def _blank(ws, row: int, height: float = 6) -> int:
    ws.row_dimensions[row].height = height
    return row + 1


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def build_confined_space_gas_measurement(form_data: Dict[str, Any]) -> bytes:
    """밀폐공간 가스농도 측정기록표 부대서류 Excel bytes 반환."""
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, _COL_WIDTHS)

    row = 1

    # ── 제목 ──────────────────────────────────────────────────────────────
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_HEADER, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 36
    row += 1

    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NOTICE, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1
    row = _blank(ws, row, 6)

    # ── s1. 측정기록표 기본정보 ────────────────────────────────────────────
    row = _section_header(ws, row, "① 측정기록표 기본정보")
    row = _four_col(ws, row,
                    "현장명",    v(form_data, "site_name"),
                    "작업 일자", v(form_data, "work_date"),
                    "공사명",    v(form_data, "project_name"),
                    "회사명",    v(form_data, "company_name"))
    row = _four_col(ws, row,
                    "밀폐공간 위치", v(form_data, "work_location"),
                    "작업허가서 번호", v(form_data, "permit_no"),
                    "작업 내용",   v(form_data, "work_description"),
                    "비고",       v(form_data, "remarks"))
    row = _blank(ws, row, 6)

    # ── s2. 연결 문서 정보 ─────────────────────────────────────────────────
    row = _section_header(ws, row, "② 연결 문서 정보  (부대서류)")
    row = _four_col(ws, row,
                    "연결 문서 ID",    v(form_data, "parent_doc_id"),
                    "연결 문서명",      v(form_data, "parent_doc_name"),
                    "연결 form_type",  v(form_data, "parent_form_type"),
                    "",               "")
    row = _blank(ws, row, 6)

    # ── s3. 밀폐공간 작업 정보 ─────────────────────────────────────────────
    row = _section_header(ws, row, "③ 밀폐공간 작업 정보")
    row = _four_col(ws, row,
                    "작업 내용",   v(form_data, "work_description"),
                    "작업 장소",   v(form_data, "work_location"),
                    "허가서 번호", v(form_data, "permit_no"),
                    "작업 일자",   v(form_data, "work_date"))
    row = _blank(ws, row, 6)

    # ── s4. 측정기기 정보 ──────────────────────────────────────────────────
    row = _section_header(ws, row, "④ 측정기기 정보")
    row = _four_col(ws, row,
                    "기기 종류",    v(form_data, "equipment_type"),
                    "모델명",       v(form_data, "equipment_model"),
                    "검교정 번호",  v(form_data, "equipment_cert_no"),
                    "검교정 유효기간", v(form_data, "equipment_cert_date"))
    row = _blank(ws, row, 6)

    # ── s5. 측정자 정보 ────────────────────────────────────────────────────
    row = _section_header(ws, row, "⑤ 측정자 정보")
    row = _four_col(ws, row,
                    "측정자 성명", v(form_data, "measurer"),
                    "직책",        v(form_data, "measurer_position"),
                    "연락처",      v(form_data, "measurer_contact"),
                    "",           "")
    row = _blank(ws, row, 6)

    # ── s6. 측정 위치 및 시간 ──────────────────────────────────────────────
    row = _section_header(ws, row, "⑥ 측정 위치 및 시간")
    notice6 = (
        "측정 위치: 밀폐공간 내 하부(바닥면) · 중간(작업면) · 상부(입구면) 3개소 이상 측정 권장.  "
        "측정 시간: 작업 전, 작업 중 (30분 간격), 작업 후 환기 확인 후 각 1회 이상."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice6,
               font=FONT_SMALL, fill=FILL_NONE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 30
    row += 1
    row = _blank(ws, row, 6)

    # ── s7. 산소농도 측정 결과 (판정 기준) ────────────────────────────────
    row = _section_header(ws, row, "⑦ 산소농도 측정 결과 및 판정 기준")
    row = _four_col(ws, row,
                    "정상 하한 (%)",   v(form_data, "o2_std_min",  "18"),
                    "정상 상한 (%)",   v(form_data, "o2_std_max",  "23.5"),
                    "기준 미달 시 조치", "작업중지 · 환기 후 재측정",
                    "",               "")
    row = _blank(ws, row, 6)

    # ── s8. 유해가스 측정 결과 (판정 기준) ────────────────────────────────
    row = _section_header(ws, row, "⑧ 유해가스 측정 결과 및 허용기준")
    row = _four_col(ws, row,
                    "황화수소 H₂S",    v(form_data, "h2s_std",  "10 ppm 이하"),
                    "일산화탄소 CO",   v(form_data, "co_std",   "30 ppm 이하"),
                    "가연성가스 LEL",  v(form_data, "lel_std",  "10% LEL 이하"),
                    "이산화탄소 CO₂",  v(form_data, "co2_std",  "1.5% 이하"))
    row = _blank(ws, row, 6)

    # ── s9. 환기 및 재측정 기록 ────────────────────────────────────────────
    row = _section_header(ws, row, "⑨ 환기 및 재측정 기록")
    row = _four_col(ws, row,
                    "환기 실시 여부",  v(form_data, "ventilation_done"),
                    "환기 방법",       v(form_data, "ventilation_method"),
                    "",              "",
                    "",              "")
    notice9 = (
        "기준 초과 시 즉시 작업중지 → 환기 실시 → 재측정 → 기준 이내 확인 후 작업 재개.  "
        "측정기기 이상(경보 오류, 배터리 부족 등) 발견 시 즉시 작업중지."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice9,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 28
    row += 1
    row = _blank(ws, row, 6)

    # ── s10. 측정 기록 (표) ────────────────────────────────────────────────
    row = _section_header(ws, row, "⑩ 산소 · 유해가스 농도 측정 기록")

    col_hdrs = [
        "순번", "측정일시", "측정위치",
        "산소농도\n(%)", "황화수소\n(ppm)", "일산화탄소\n(ppm)",
        "가연성가스\n(%LEL)", "이산화탄소\n(%)",
        "환기상태", "판정", "측정자", "비고",
    ]
    for c, h in enumerate(col_hdrs, 1):
        write_cell(ws, row, c, c, h, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 30
    row += 1

    raw_items: List[Dict[str, Any]] = form_data.get("measure_records") or []
    items = raw_items if raw_items else DEFAULT_MEASURE_RECORDS
    items = items[:MAX_MEASURE_ROWS]

    for it in items:
        jval  = v(it, "judgment",    "")
        jfill = _JUDGMENT_FILL.get(jval, FILL_NONE)
        vval  = v(it, "ventilation", "")
        vfill = _VENTILATION_FILL.get(vval, FILL_NONE)

        write_cell(ws, row, 1,  1,  v(it, "no"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 2,  2,  v(it, "datetime"), font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 3,  3,  v(it, "location"), font=FONT_SMALL, align=ALIGN_LEFT)
        write_cell(ws, row, 4,  4,  v(it, "o2"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 5,  5,  v(it, "h2s"),      font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 6,  6,  v(it, "co"),       font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 7,  7,  v(it, "lel"),      font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 8,  8,  v(it, "co2"),      font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 9,  9,  vval,              font=FONT_SMALL, fill=vfill, align=ALIGN_CENTER)
        write_cell(ws, row, 10, 10, jval,              font=FONT_SMALL, fill=jfill, align=ALIGN_CENTER)
        write_cell(ws, row, 11, 11, v(it, "measurer"), font=FONT_SMALL, align=ALIGN_CENTER)
        write_cell(ws, row, 12, 12, v(it, "remarks"),  font=FONT_SMALL, align=ALIGN_LEFT)
        ws.row_dimensions[row].height = 22
        row += 1

    empty = max(3, MAX_MEASURE_ROWS - len(items))
    next_no = len(items) + 1
    for i in range(empty):
        write_cell(ws, row, 1, 1, str(next_no + i), font=FONT_SMALL, align=ALIGN_CENTER)
        for c in range(2, TOTAL_COLS + 1):
            write_cell(ws, row, c, c, "", font=FONT_SMALL, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 22
        row += 1

    row = _blank(ws, row, 6)

    # ── s11. 작업 가능 여부 판정 ──────────────────────────────────────────
    row = _section_header(ws, row, "⑪ 작업 가능 여부 판정")
    row = _four_col(ws, row,
                    "작업 가능 여부", v(form_data, "work_possible"),
                    "판정자",         v(form_data, "work_possible_by"),
                    "",              "",
                    "",              "")
    notice11 = (
        "작업 가능: 산소농도 18%~23.5%, 황화수소 10 ppm 이하, 일산화탄소 30 ppm 이하, "
        "가연성가스 10% LEL 이하 — 모든 항목 동시 충족 시.  "
        "기준 초과 항목이 1개라도 있으면 작업중지."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice11,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 36
    row += 1
    row = _blank(ws, row, 6)

    # ── s12. 비상조치 및 작업중지 기준 ────────────────────────────────────
    row = _section_header(ws, row, "⑫ 비상조치 및 작업중지 기준")
    notice12 = (
        "▶ 작업중지 기준: 산소농도 18% 미만 또는 23.5% 초과 / 황화수소 10 ppm 초과 / "
        "일산화탄소 30 ppm 초과 / 가연성가스 10% LEL 초과 / 측정기기 이상 경보 시\n"
        "▶ 비상조치: 즉시 작업중지 → 작업자 대피 → 환기 실시 → 원인 파악 → "
        "재측정 후 기준 이내 확인 → 작업 재개 허가 → 관리감독자 보고"
    )
    write_cell(ws, row, 1, TOTAL_COLS, v(form_data, "emergency_plan") or notice12,
               font=FONT_SMALL, fill=FILL_WARN, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 48
    row += 1
    row = _blank(ws, row, 6)

    # ── s13. 확인자 서명 ──────────────────────────────────────────────────
    row = _section_header(ws, row, "⑬ 확인자 서명")
    write_cell(ws, row, 1,  2,  "구분",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 3,  5,  "성명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 6,  8,  "직책",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 9,  10, "서명",     font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 11, 12, "확인 일자", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    ws.row_dimensions[row].height = 18
    row += 1

    for role, name_key, pos_key, date_key in [
        ("측정자", "measurer",   "measurer_position", "work_date"),
        ("확인자", "confirmer",  "confirmer_position", "confirm_date"),
    ]:
        write_cell(ws, row, 1,  2,  role,                          font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 3,  5,  v(form_data, name_key),        font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 6,  8,  v(form_data, pos_key),         font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 9,  10, "",                            font=FONT_DEFAULT, align=ALIGN_CENTER)
        write_cell(ws, row, 11, 12, v(form_data, date_key),        font=FONT_DEFAULT, align=ALIGN_CENTER)
        ws.row_dimensions[row].height = 28
        row += 1
    row = _blank(ws, row, 6)

    # ── 하단 안내 ─────────────────────────────────────────────────────────
    notice = (
        "[confined_space_gas_measurement] 본 가스농도 측정기록표는 밀폐공간 작업 전·중·후 "
        "산소 및 유해가스 농도 측정 결과를 기록하는 부대서류입니다. "
        "document_catalog 독립 문서가 아님.  산업안전보건기준에 관한 규칙 밀폐공간 작업 기준 적용."
    )
    write_cell(ws, row, 1, TOTAL_COLS, notice,
               font=FONT_SMALL, fill=FILL_NOTICE, align=ALIGN_LEFT)
    ws.row_dimensions[row].height = 24

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

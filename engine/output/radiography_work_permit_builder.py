"""
방사선 투과검사 작업 허가서 — Excel 출력 모듈 (v1).

법적 근거:
  - 산업안전보건기준에 관한 규칙 제573조(정의), 제574조(방사성물질의 밀폐 등),
    제575조(방사선관리구역의 지정 등), 제579조(게시 등),
    제580조(차폐물 설치 등)
  - 원자력안전법 제91조(방사선장해방지조치), 제106조(교육훈련)
  - 원자력안전법 시행규칙 제2조(방사선관리구역 기준)
  - 비파괴검사기술의 진흥 및 관리에 관한 법률 제2조(방사선 비파괴검사 분류)
분류: PRACTICAL — 법정 별지 서식 없음. 산안규칙 의무 항목 기반 실무 서식.
      방사선 투과검사(RT) 현장 작업 전 안전통제 및 허가용 서식.

form_type: radiography_work_permit
함수명:    build_radiography_work_permit(form_data)

Required form_data keys:
    site_name          str  현장명
    permit_date        str  허가일자
    work_location      str  작업장소
    work_supervisor    str  작업책임자

Optional form_data keys:
    project_name              str   공사명
    permit_no                 str   허가번호
    permit_time_start         str   작업 시작 예정시각
    permit_time_end           str   작업 종료 예정시각
    inspection_object         str   검사 대상 (부재/배관/용접부 등)
    inspection_method         str   검사 방법 (촬영 방향, 노출 조건 등)
    inspection_area           str   검사 부위 수
    radiation_source_type     str   방사선원 종류 (Ir-192, Se-75 등)
    source_activity           str   선원 강도 (Ci/GBq)
    source_serial_no          str   선원 일련번호
    equipment_model           str   조사기(카메라) 모델/번호
    source_inspector          str   선원 보관 관리자
    rt_supervisor             str   방사선투과검사 책임자
    radiation_safety_officer  str   방사선안전관리자
    rt_operator               str   조작자 (방사선취급자격자)
    rt_operator_cert_no       str   조작자 자격증 번호
    control_zone_radius       str   방사선관리구역 반경 (m)
    control_zone_method       str   구역 설정 방법 (rope/표지판/임시차단막 등)
    control_zone_confirmed    str   구역 설정 확인 여부
    shielding_material        str   차폐재 종류·두께
    shielding_confirmed       str   차폐 확인 여부
    warning_sign_placed       str   경고표지 설치 위치
    watchman_name             str   감시인 성명
    watchman_post             str   감시인 배치 위치
    dosimeter_supervisor      str   선량계 지급 관리자
    dosimeter_type            str   개인선량계 종류 (포켓선량계/OSL/TLD 등)
    ppe_confirmed             str   보호구 지급 확인
    evacuation_scope          str   대피 범위·인원
    evacuation_route          str   대피 경로
    emergency_contact         str   비상연락망
    emergency_procedure       str   비상 시 조치 절차
    stop_work_criteria        str   작업중지 기준 (선량률 기준치 등)
    post_work_source_check    str   작업 완료 후 선원 회수 확인
    post_work_zone_release    str   방사선관리구역 해제 확인
    pre_work_checks           list[str]  작업 전 허가 조건 이행 항목
    during_work_checks        list[str]  작업 중 준수사항 이행 항목
    workers                   list[dict] name, cert_no, dosimeter_id — 작업자 명단
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict

from openpyxl import Workbook

from engine.output.excel_style_helpers import (
    ALIGN_CENTER, ALIGN_LABEL, ALIGN_LEFT,
    FILL_HEADER, FILL_LABEL, FILL_NONE, FILL_NOTICE, FILL_SECTION, FILL_WARN,
    FONT_BOLD, FONT_DEFAULT, FONT_NOTICE, FONT_SUBTITLE, FONT_TITLE,
    apply_col_widths, v, write_cell,
)

SHEET_NAME    = "방사선투과검사작업허가서"
SHEET_HEADING = "방사선 투과검사 작업 허가서"
SHEET_SUBTITLE = (
    "「산업안전보건기준에 관한 규칙」 제574조·제575조·제579조·제580조에 따른 "
    "방사선 작업 전 안전통제 및 허가 기록 서식  [PTW-006]"
)

TOTAL_COLS   = 10
MAX_WORKERS  = 6

COL_WIDTHS = {1: 16, 2: 12, 3: 12, 4: 12, 5: 10, 6: 12, 7: 12, 8: 12, 9: 10, 10: 10}

_L1, _V1S, _V1E = 1, 2,  5
_L2, _V2S, _V2E = 6, 7, 10
_FVS, _FVE       = 2, 10

# ---------------------------------------------------------------------------
# 고정 문구
# ---------------------------------------------------------------------------

NOTICE_LEGAL = (
    "본 서식은 관계 기관 공식 법정서식이 아닙니다. "
    "산안규칙 제573조 이하, 원자력안전법 제91조·제106조 의무 항목 기반 실무 서식이며, "
    "현장 조건·발주처·원청 기준에 따라 보완 적용한다."
)
NOTICE_ZONE = (
    "방사선관리구역은 방사선량률이 주당 400μSv를 초과하는 구역이며, "
    "경계·출입통제·경고표지 설치 의무가 있다 (산안규칙 제575조·제579조)."
)
NOTICE_DOSIMETER = (
    "방사선작업종사자는 개인선량계를 착용하여야 하며 연간 50mSv, "
    "5년 100mSv 선량한도를 초과할 수 없다 (원자력안전법 제91조)."
)
NOTICE_STOP_WORK = (
    "선량률이 설정 기준치를 초과하거나 선원 회수 불가 상황 발생 시 즉시 작업중지하고 "
    "방사선안전관리자 및 관할 기관에 보고한다."
)
NOTICE_POST_WORK = (
    "작업 완료 후 방사선원 회수 여부를 반드시 확인하고 방사선관리구역을 해제한다. "
    "미회수 시 즉시 비상조치 절차를 시행한다."
)

# ---------------------------------------------------------------------------
# 고정 체크리스트
# ---------------------------------------------------------------------------

PRE_WORK_ITEMS = [
    "방사선관리구역 반경 확인 및 rope·표지판 설치",
    "경고표지 설치 확인 (방사선위험, 출입금지)",
    "감시인 배치 완료",
    "차폐재 설치 및 두께 확인",
    "방사선원 종류·강도·일련번호 확인",
    "조사기(카메라) 이상 여부 점검",
    "개인선량계(포켓선량계) 작동 및 초기값 확인",
    "보호구(납앞치마, 고글 등) 지급 확인",
    "주변 작업자 대피 완료 확인",
    "대피 경로·비상연락처 숙지 확인",
    "방사선안전관리자 현장 입회 확인",
    "인근 공종 작업 일시중지 협의 완료",
]

DURING_WORK_ITEMS = [
    "작업 중 구역 이탈자 즉시 통제",
    "선량률 모니터링 및 이상 시 즉시 중단",
    "선원 이상 거동(걸림, 미회수 등) 즉시 보고",
    "감시인 상시 배치 유지",
    "무단 출입 시 작업 즉시 중단",
]

POST_WORK_ITEMS = [
    "방사선원 회수 완료 확인",
    "조사기 잠금 상태 확인",
    "방사선관리구역 해제 (표지·rope 제거)",
    "작업자 선량계 수거 및 기록",
    "작업일지 작성 완료",
]

# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _sec(ws, row: int, title: str, fill=None) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, title,
               font=FONT_BOLD, fill=fill or FILL_SECTION,
               align=ALIGN_CENTER, height=20)
    return row + 1


def _lv(ws, row: int, lbl: str, val: Any,
        l: int, vs: int, ve: int, h: int = 20) -> None:
    write_cell(ws, row, l,  l,  lbl, font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_LABEL)
    write_cell(ws, row, vs, ve, val, font=FONT_DEFAULT, align=ALIGN_LEFT, height=h)


def _notice(ws, row: int, text: str) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, text,
               font=FONT_NOTICE, fill=FILL_NOTICE, align=ALIGN_LEFT, height=28)
    return row + 1


def _checklist(ws, row: int, items: list[str], checked: set) -> int:
    for item in items:
        mark = "■" if item in checked else "□"
        write_cell(ws, row, 1, TOTAL_COLS, f"{mark}  {item}",
                   font=FONT_DEFAULT, align=ALIGN_LEFT, height=20)
        row += 1
    return row


# ---------------------------------------------------------------------------
# 섹션 렌더러
# ---------------------------------------------------------------------------

def _s_title(ws, row: int) -> int:
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_HEADING,
               font=FONT_TITLE, fill=FILL_NONE, align=ALIGN_CENTER, border=False, height=32)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, SHEET_SUBTITLE,
               font=FONT_SUBTITLE, fill=FILL_NONE, align=ALIGN_CENTER, border=False, height=16)
    return row + 1


def _s1_basic(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "1. 작업 허가 기본정보")
    _lv(ws, row, "현장명",    v(d, "site_name"),    _L1, _V1S, _V1E)
    _lv(ws, row, "공사명",    v(d, "project_name"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "허가번호",  v(d, "permit_no"),    _L1, _V1S, _V1E)
    _lv(ws, row, "허가일자",  v(d, "permit_date"),  _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "작업 시작",  v(d, "permit_time_start"), _L1, _V1S, _V1E)
    _lv(ws, row, "작업 종료",  v(d, "permit_time_end"),   _L2, _V2S, _V2E)
    row += 1
    return row


def _s2_location(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "2. 작업 장소 및 검사 대상")
    _lv(ws, row, "작업장소",   v(d, "work_location"),   _L1, _FVS, _FVE, h=24)
    row += 1
    _lv(ws, row, "검사 대상",  v(d, "inspection_object"), _L1, _V1S, _V1E)
    _lv(ws, row, "검사 부위수", v(d, "inspection_area"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "검사 방법",  v(d, "inspection_method"), _L1, _FVS, _FVE, h=28)
    row += 1
    return row


def _s3_source(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "3. 방사선원 및 장비 정보")
    _lv(ws, row, "방사선원 종류",   v(d, "radiation_source_type"), _L1, _V1S, _V1E)
    _lv(ws, row, "선원 강도",       v(d, "source_activity"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "선원 일련번호",   v(d, "source_serial_no"),      _L1, _V1S, _V1E)
    _lv(ws, row, "조사기 모델/번호", v(d, "equipment_model"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "선원 보관 관리자", v(d, "source_inspector"),      _L1, _FVS, _FVE)
    row += 1
    return row


def _s4_workers(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "4. 작업자 및 방사선안전관리자 정보")
    _lv(ws, row, "작업책임자",        v(d, "work_supervisor"),          _L1, _V1S, _V1E)
    _lv(ws, row, "방사선안전관리자",   v(d, "radiation_safety_officer"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "RT 검사 책임자",    v(d, "rt_supervisor"),             _L1, _V1S, _V1E)
    _lv(ws, row, "조작자(자격증 번호)", v(d, "rt_operator") + "  " + v(d, "rt_operator_cert_no"),
        _L2, _V2S, _V2E)
    row += 1
    # 작업자 명단 테이블
    write_cell(ws, row, 1, 1,  "순번", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER, height=18)
    write_cell(ws, row, 2, 4,  "성명", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 5, 7,  "자격증 번호", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    write_cell(ws, row, 8, 10, "개인선량계 번호", font=FONT_BOLD, fill=FILL_LABEL, align=ALIGN_CENTER)
    row += 1
    workers = d.get("workers") or []
    for i in range(MAX_WORKERS):
        item = workers[i] if i < len(workers) else {}
        write_cell(ws, row, 1, 1,  i + 1,                font=FONT_DEFAULT, align=ALIGN_CENTER, height=20)
        write_cell(ws, row, 2, 4,  v(item, "name"),       font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 5, 7,  v(item, "cert_no"),    font=FONT_DEFAULT, align=ALIGN_LEFT)
        write_cell(ws, row, 8, 10, v(item, "dosimeter_id"), font=FONT_DEFAULT, align=ALIGN_LEFT)
        row += 1
    return row


def _s5_pre_conditions(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "5. 작업 전 허가 조건  (이행 항목에 ■ 표시)")
    checked = set(d.get("pre_work_checks") or [])
    row = _checklist(ws, row, PRE_WORK_ITEMS, checked)
    return row


def _s6_control_zone(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "6. 방사선관리구역 설정 및 출입통제  (산안규칙 제575조)")
    row = _notice(ws, row, NOTICE_ZONE)
    _lv(ws, row, "구역 반경",    v(d, "control_zone_radius"),   _L1, _V1S, _V1E)
    _lv(ws, row, "설정 방법",    v(d, "control_zone_method"),   _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "구역 설정 확인", v(d, "control_zone_confirmed") or "□ 확인  □ 미확인",
        _L1, _FVS, _FVE)
    row += 1
    return row


def _s7_shielding(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "7. 차폐·경고표지·감시인 배치  (산안규칙 제579조·제580조)")
    _lv(ws, row, "차폐재 종류/두께", v(d, "shielding_material"),  _L1, _V1S, _V1E)
    _lv(ws, row, "차폐 확인",        v(d, "shielding_confirmed") or "□ 확인  □ 미확인",
        _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "경고표지 위치", v(d, "warning_sign_placed"), _L1, _FVS, _FVE)
    row += 1
    _lv(ws, row, "감시인 성명",  v(d, "watchman_name"), _L1, _V1S, _V1E)
    _lv(ws, row, "배치 위치",   v(d, "watchman_post"), _L2, _V2S, _V2E)
    row += 1
    return row


def _s8_dosimeter(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "8. 개인선량계 및 보호구 확인  (산안규칙 제574조, 원자력안전법 제91조)")
    row = _notice(ws, row, NOTICE_DOSIMETER)
    _lv(ws, row, "선량계 관리자", v(d, "dosimeter_supervisor"), _L1, _V1S, _V1E)
    _lv(ws, row, "선량계 종류",   v(d, "dosimeter_type"),       _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "보호구 지급 확인",
        v(d, "ppe_confirmed") or "□ 납앞치마  □ 납고글  □ 방사선 경보기  □ 포켓선량계",
        _L1, _FVS, _FVE, h=24)
    row += 1
    return row


def _s9_evacuation(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "9. 주변 작업자 대피 및 연락체계")
    _lv(ws, row, "대피 범위/인원", v(d, "evacuation_scope"), _L1, _V1S, _V1E)
    _lv(ws, row, "대피 경로",      v(d, "evacuation_route"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "비상연락망",   v(d, "emergency_contact"), _L1, _FVS, _FVE, h=28)
    row += 1
    return row


def _s10_during_work(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "10. 작업 중 준수사항  (이행 항목에 ■ 표시)")
    checked = set(d.get("during_work_checks") or [])
    row = _checklist(ws, row, DURING_WORK_ITEMS, checked)
    return row


def _s11_emergency(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "11. 비상상황 대응 및 작업중지 기준", fill=FILL_WARN)
    row = _notice(ws, row, NOTICE_STOP_WORK)
    _lv(ws, row, "작업중지 기준",  v(d, "stop_work_criteria") or "선량률 기준치 초과 시 즉시 중단",
        _L1, _FVS, _FVE, h=28)
    row += 1
    _lv(ws, row, "비상 시 조치 절차",
        v(d, "emergency_procedure") or "선원회수불가 → 전원대피 → 방사선안전관리자 보고 → 관할기관 신고",
        _L1, _FVS, _FVE, h=36)
    row += 1
    return row


def _s12_post_work(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "12. 작업 완료 후 확인사항")
    row = _notice(ws, row, NOTICE_POST_WORK)
    checked_post = set(d.get("post_work_checks") or [])
    row = _checklist(ws, row, POST_WORK_ITEMS, checked_post)
    _lv(ws, row, "선원 회수 확인",    v(d, "post_work_source_check") or "□ 회수 완료  □ 미회수 (비상조치)",
        _L1, _V1S, _V1E, h=24)
    _lv(ws, row, "구역 해제 확인",    v(d, "post_work_zone_release") or "□ 해제 완료  □ 미해제",
        _L2, _V2S, _V2E)
    row += 1
    return row


def _s13_approval(ws, row: int, d: Dict[str, Any]) -> int:
    row = _sec(ws, row, "13. 작업책임자 / 방사선안전관리자 / 현장관리자 승인", fill=FILL_HEADER)
    _lv(ws, row, "작업책임자 서명",        v(d, "work_supervisor"),          _L1, _V1S, _V1E, h=36)
    _lv(ws, row, "방사선안전관리자 서명",   v(d, "radiation_safety_officer"), _L2, _V2S, _V2E)
    row += 1
    _lv(ws, row, "현장관리자 승인 서명",
        v(d, "site_manager_sign") or "",
        _L1, _FVS, _FVE, h=36)
    row += 1
    write_cell(ws, row, 1, TOTAL_COLS, NOTICE_LEGAL,
               font=FONT_NOTICE, fill=FILL_NOTICE, align=ALIGN_LEFT, height=28)
    row += 1
    return row


# ---------------------------------------------------------------------------
# 메인 빌더
# ---------------------------------------------------------------------------

def build_radiography_work_permit(form_data: Dict[str, Any]) -> bytes:
    """form_data dict를 받아 방사선 투과검사 작업 허가서 xlsx 바이너리를 반환."""
    d  = form_data or {}
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    apply_col_widths(ws, COL_WIDTHS)

    row = 1
    row = _s_title(ws, row)
    row = _s1_basic(ws, row, d)
    row = _s2_location(ws, row, d)
    row = _s3_source(ws, row, d)
    row = _s4_workers(ws, row, d)
    row = _s5_pre_conditions(ws, row, d)
    row = _s6_control_zone(ws, row, d)
    row = _s7_shielding(ws, row, d)
    row = _s8_dosimeter(ws, row, d)
    row = _s9_evacuation(ws, row, d)
    row = _s10_during_work(ws, row, d)
    row = _s11_emergency(ws, row, d)
    row = _s12_post_work(ws, row, d)
    _s13_approval(ws, row, d)

    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.print_title_rows = "1:2"  # 제목+부제 반복
    ws.page_margins.left   = 0.5
    ws.page_margins.right  = 0.5
    ws.page_margins.top    = 0.75
    ws.page_margins.bottom = 0.75

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

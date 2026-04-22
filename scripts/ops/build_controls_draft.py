"""
controls master 초안 CSV + 샘플 문장 → control 매핑 CSV 생성기.

입력
  - data/risk_db/schema/sentence_labeling_sample.csv (400 샘플)
출력
  - data/risk_db/master/controls_master_draft.csv  (master 초안, 1레코드=1 control)
  - data/risk_db/master/sentence_control_mapping_sample.csv (샘플 매핑 후보)

원칙
  - read-only on DB. 파일 쓰기만 수행.
  - master 는 hand-crafted list (50 개 내외, 12 category 커버).
  - 샘플 매핑은 rule hit 기반 candidate. confidence 3 단계.
"""
from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()

# ---------------------------------------------------------------------------
# controls master 초안 (50 레코드)
# ---------------------------------------------------------------------------

# 컬럼: code, name_ko, name_en, category, type, description, keywords, verbs,
#       sentence_types, hazards, equipments, work_types, legal_req, review, note
CONTROLS_DRAFT: list[dict] = [
    # ---- engineering_control ----
    dict(code="ctrl_fall_protection_install", name_ko="추락방지설비 설치",
         category="engineering_control", type="fall_protection_install",
         description="작업발판·안전난간·개구부 덮개 등 추락방지 설비를 설치하고 상태를 확인한다",
         keywords="안전난간|안전난간대|작업발판|개구부 덮개|방호선|추락방지망",
         verbs="설치|부착|고정",
         sentence_types="equipment_rule,requirement",
         hazards="추락", equipments="비계,고소작업",
         work_types="고소작업,비계_조립,비계_해체",
         legal_req="Y", note="산안규칙 제43조·42조 연계"),
    dict(code="ctrl_local_ventilation_install", name_ko="국소배기장치 설치·운전",
         category="engineering_control", type="local_ventilation_install",
         description="국소배기장치를 설치·운전하고 성능을 확인한다",
         keywords="국소배기장치|국소배기|배기설비|환기장치",
         verbs="설치|운전|가동",
         sentence_types="equipment_rule,requirement",
         hazards="소음진동", equipments="",
         work_types="용접,도장",
         legal_req="Y", note="산안규칙 제72조·제74조"),
    dict(code="ctrl_guard_installation", name_ko="방호장치 설치",
         category="engineering_control", type="guard_installation",
         description="회전·절단부에 방호장치를 설치하고 탈착 여부를 점검한다",
         keywords="방호장치|가드|안전덮개|인터록|과부하방지장치",
         verbs="설치|부착",
         sentence_types="equipment_rule,requirement",
         hazards="끼임,협착,절단", equipments="기계정비",
         work_types="기계정비",
         legal_req="Y"),
    dict(code="ctrl_lockout_tagout", name_ko="기동장치 잠금·표지(LOTO)",
         category="engineering_control", type="lockout_tagout",
         description="정비·청소 시 기동장치를 잠그고 LOTO 표지를 부착한다",
         keywords="기동장치|잠금|LOTO|전원차단",
         verbs="잠그고|차단|부착",
         sentence_types="equipment_rule,requirement",
         hazards="감전,끼임", equipments="",
         work_types="기계정비", legal_req="Y"),
    dict(code="ctrl_electrical_isolation", name_ko="충전전로 정전·접지",
         category="engineering_control", type="electrical_isolation",
         description="정전 후 검전기로 확인하고 접지한 뒤 작업한다",
         keywords="충전전로|정전|접지|검전기|활선",
         verbs="정전|접지|차단",
         sentence_types="equipment_rule,requirement",
         hazards="감전", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_confined_space_ventilation", name_ko="밀폐공간 환기·산소 공급",
         category="engineering_control", type="confined_space_ventilation",
         description="밀폐공간 작업 전·중 환기를 실시하고 산소농도를 유지한다",
         keywords="밀폐공간|산소농도|환기",
         verbs="환기|공급",
         sentence_types="equipment_rule,requirement",
         hazards="질식", equipments="", work_types="밀폐공간", legal_req="Y"),
    dict(code="ctrl_drop_prevention", name_ko="자재 낙하 방지",
         category="engineering_control", type="drop_prevention",
         description="자재 낙하 방지망·방호선반·결속구를 설치한다",
         keywords="낙하방지|낙하물 방지망|방호선반|결속",
         verbs="설치|결속",
         sentence_types="equipment_rule",
         hazards="비래낙하", equipments="양중,비계", work_types="양중", legal_req="Y"),
    # ---- ppe_control ----
    dict(code="ctrl_ppe_wear", name_ko="보호구 착용",
         category="ppe_control", type="ppe_wear",
         description="해당 작업에 적합한 보호구(안전모·안전대·보안경 등)를 착용한다",
         keywords="보호구|안전모|안전대|안전화|방진마스크|호흡보호구|내화학장갑|보안경|보호복|귀마개",
         verbs="착용",
         sentence_types="ppe_rule,requirement",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_ppe_provision", name_ko="보호구 지급·관리",
         category="ppe_control", type="ppe_provision",
         description="작업에 적합한 보호구를 근로자에게 지급하고 교체 주기를 관리한다",
         keywords="보호구 지급|보호구 비치",
         verbs="지급|비치|교체",
         sentence_types="ppe_rule,document_rule",
         hazards="", equipments="", work_types="", legal_req="Y"),
    # ---- training_control ----
    dict(code="ctrl_special_training", name_ko="특별안전보건교육 실시",
         category="training_control", type="special_training",
         description="해당 작업 근로자에게 특별안전보건교육을 실시한다",
         keywords="특별교육|특별안전교육|특별안전보건교육",
         verbs="실시|이수",
         sentence_types="education_rule",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_pre_work_briefing", name_ko="작업 전 안전교육(TBM)",
         category="training_control", type="pre_work_briefing",
         description="작업 전 위험요인·작업순서·보호구를 주지(TBM)한다",
         keywords="작업 전 교육|TBM|툴박스미팅|조회|일일안전",
         verbs="실시|주지|숙지",
         sentence_types="education_rule,procedure",
         hazards="", equipments="", work_types="", legal_req="N",
         note="법적 의무는 아니나 현장 표준"),
    dict(code="ctrl_safety_training_general", name_ko="정기 안전보건교육",
         category="training_control", type="safety_training_general",
         description="법정 안전보건교육을 분기/반기별로 실시한다",
         keywords="안전보건교육|안전교육|정기교육",
         verbs="실시|이수",
         sentence_types="education_rule",
         hazards="", equipments="", work_types="", legal_req="Y"),
    # ---- inspection_control ----
    dict(code="ctrl_periodic_inspection", name_ko="정기 점검",
         category="inspection_control", type="periodic_inspection",
         description="설비의 방호장치·과부하장치 등을 정기적으로 점검한다",
         keywords="정기점검|자체점검|매일 점검|매월|6개월마다|연 1회",
         verbs="점검|검사|확인",
         sentence_types="inspection_rule,requirement",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_pre_work_inspection", name_ko="작업 전 점검",
         category="inspection_control", type="pre_work_inspection",
         description="작업 전 설비 및 작업환경 이상 유무를 점검한다",
         keywords="작업 전 점검|시업 전 점검|작업 시작 전",
         verbs="점검|확인",
         sentence_types="inspection_rule,procedure",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_atmospheric_measurement", name_ko="가스·산소 농도 측정",
         category="inspection_control", type="atmospheric_measurement",
         description="밀폐공간 작업 전 산소·유해가스 농도를 측정한다",
         keywords="산소농도|유해가스|가스농도|농도 측정",
         verbs="측정|확인",
         sentence_types="inspection_rule",
         hazards="질식", equipments="", work_types="밀폐공간", legal_req="Y"),
    dict(code="ctrl_working_environment_measurement", name_ko="작업환경측정",
         category="inspection_control", type="working_environment_measurement",
         description="분진·소음 등 유해인자에 대해 작업환경측정을 실시한다",
         keywords="작업환경측정|유해인자 측정",
         verbs="측정|실시",
         sentence_types="inspection_rule",
         hazards="소음진동", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_checklist_verification", name_ko="체크리스트 점검",
         category="inspection_control", type="checklist_verification",
         description="표준 점검표로 작업 전·중 상태를 점검·기록한다",
         keywords="체크리스트|점검표|자율점검",
         verbs="점검|기록|확인",
         sentence_types="inspection_rule,document_rule",
         hazards="", equipments="", work_types="", legal_req="N"),
    # ---- document_control ----
    dict(code="ctrl_msds_posting", name_ko="MSDS·경고표지 게시",
         category="document_control", type="msds_posting",
         description="취급 물질의 MSDS·경고표지를 게시하고 비치한다",
         keywords="MSDS|물질안전보건자료|경고표지",
         verbs="게시|비치|부착",
         sentence_types="document_rule",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_record_retention", name_ko="점검·교육 기록 보존",
         category="document_control", type="record_retention",
         description="점검·교육·측정 기록을 법정 기간 보존한다",
         keywords="기록|보존|관리대장",
         verbs="보존|기록",
         sentence_types="document_rule",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_work_plan_preparation", name_ko="작업계획서 작성",
         category="document_control", type="work_plan_preparation",
         description="해당 작업의 작업계획서를 작성하고 근로자에게 주지한다",
         keywords="작업계획서|작업계획",
         verbs="작성|주지",
         sentence_types="document_rule,requirement",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_safety_sign_posting", name_ko="안전보건표지 부착",
         category="document_control", type="safety_sign_posting",
         description="작업장 출입구·위험구역에 안전보건표지를 부착한다",
         keywords="안전보건표지|주의표지|경고표지(표지)",
         verbs="부착|설치",
         sentence_types="document_rule",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_incident_report", name_ko="재해·사고 보고",
         category="document_control", type="incident_report",
         description="중대재해·산업재해 발생 시 고용노동부에 보고한다",
         keywords="산업재해|중대재해|보고",
         verbs="보고|신고",
         sentence_types="document_rule,requirement",
         hazards="", equipments="", work_types="", legal_req="Y"),
    # ---- supervision_control ----
    dict(code="ctrl_supervisor_assignment", name_ko="관리감독자 배치",
         category="supervision_control", type="supervisor_assignment",
         description="해당 작업에 관리감독자(작업지휘자)를 배치한다",
         keywords="관리감독자|작업지휘자",
         verbs="배치|지정",
         sentence_types="requirement",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_signalman_assignment", name_ko="신호수 배치",
         category="supervision_control", type="signalman_assignment",
         description="중량물 인양·차량계 건설기계 작업에 신호수를 배치한다",
         keywords="신호수|유도자",
         verbs="배치",
         sentence_types="requirement",
         hazards="충돌", equipments="양중", work_types="양중", legal_req="Y"),
    dict(code="ctrl_standby_person_assignment", name_ko="감시인 배치",
         category="supervision_control", type="standby_person_assignment",
         description="밀폐공간 등 고위험 작업 외부에 감시인을 상시 배치한다",
         keywords="감시인|감시자|외부 감시",
         verbs="배치",
         sentence_types="requirement,emergency_rule",
         hazards="질식", equipments="", work_types="밀폐공간", legal_req="Y"),
    dict(code="ctrl_fire_watch_assignment", name_ko="화재감시인 배치",
         category="supervision_control", type="fire_watch_assignment",
         description="화기작업 중 화재감시인을 배치하고 작업 후 30분 이상 잔류한다",
         keywords="화재감시인|화기감시",
         verbs="배치",
         sentence_types="requirement",
         hazards="", equipments="", work_types="용접", legal_req="Y"),
    # ---- permit_control ----
    dict(code="ctrl_work_permit_issue", name_ko="작업허가서 발행",
         category="permit_control", type="work_permit_issue",
         description="해당 작업에 대해 작업허가서를 발행하고 승인 후 착수한다",
         keywords="작업허가서|작업허가",
         verbs="발행|승인",
         sentence_types="document_rule,requirement",
         hazards="", equipments="", work_types="", legal_req="N",
         note="법정 의무는 제한적 — 화기/밀폐/굴착 등 제한"),
    dict(code="ctrl_confined_space_permit", name_ko="밀폐공간 작업허가",
         category="permit_control", type="confined_space_permit",
         description="밀폐공간 진입 전 작업허가서·가스농도·환기를 확인한다",
         keywords="밀폐공간 작업허가",
         verbs="발행|확인",
         sentence_types="permit,requirement",
         hazards="질식", equipments="", work_types="밀폐공간", legal_req="Y"),
    dict(code="ctrl_hot_work_permit", name_ko="화기작업 허가",
         category="permit_control", type="hot_work_permit",
         description="용접·용단 등 화기작업 허가서를 발행하고 주변 가연물을 제거한다",
         keywords="화기작업 허가",
         verbs="발행|제거",
         sentence_types="permit,requirement",
         hazards="", equipments="", work_types="용접", legal_req="N"),
    # ---- administrative_control ----
    dict(code="ctrl_access_restriction", name_ko="출입금지·구역 통제",
         category="administrative_control", type="access_restriction",
         description="위험구역 출입금지 표지·차단 설비를 설치하고 관계자 외 접근을 통제한다",
         keywords="출입금지|출입통제|관계자 외 출입",
         verbs="통제|제한|설치",
         sentence_types="requirement,prohibition",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_work_zone_separation", name_ko="작업구역 분리",
         category="administrative_control", type="work_zone_separation",
         description="작업 구역을 분리하고 혼재 시 사전 협의·조정을 수행한다",
         keywords="작업구역 분리|혼재작업",
         verbs="분리|조정",
         sentence_types="requirement",
         hazards="충돌", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_simultaneous_work_coordination", name_ko="혼재작업 안전조정",
         category="administrative_control", type="simultaneous_work_coordination",
         description="도급·수급·자사 혼재작업 간 위험요인을 협의·조정한다",
         keywords="혼재작업|안전보건협의체",
         verbs="협의|조정",
         sentence_types="requirement",
         hazards="", equipments="", work_types="", legal_req="Y"),
    # ---- emergency_control ----
    dict(code="ctrl_emergency_evacuation", name_ko="비상 대피체계 수립",
         category="emergency_control", type="emergency_evacuation",
         description="비상 시 대피 경로·집결지·연락체계를 수립·주지한다",
         keywords="대피|피난|비상연락|집결지",
         verbs="수립|주지|확보",
         sentence_types="emergency_rule,requirement",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_first_aid_setup", name_ko="응급처치 체계",
         category="emergency_control", type="first_aid_setup",
         description="응급처치 장비·구급함·응급연락망을 비치·주지한다",
         keywords="응급처치|구급함|응급연락",
         verbs="비치|주지",
         sentence_types="emergency_rule",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_fire_extinguisher_setup", name_ko="소화설비 비치",
         category="emergency_control", type="fire_extinguisher_setup",
         description="소화기·소화전 등 소화설비를 비치하고 사용법을 주지한다",
         keywords="소화기|소화전|소화설비",
         verbs="비치|주지",
         sentence_types="emergency_rule,equipment_rule",
         hazards="", equipments="", work_types="용접", legal_req="Y"),
    # ---- health_control ----
    dict(code="ctrl_special_health_check", name_ko="특수건강진단",
         category="health_control", type="special_health_check",
         description="유해인자 노출 근로자에게 특수건강진단을 실시한다",
         keywords="특수건강진단|배치전건강진단",
         verbs="실시",
         sentence_types="requirement",
         hazards="", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_exposure_monitoring", name_ko="유해인자 노출 관리",
         category="health_control", type="exposure_monitoring",
         description="유해인자 노출 기준을 초과하지 않도록 관리한다",
         keywords="노출기준|허용기준|TLV",
         verbs="관리|유지",
         sentence_types="requirement",
         hazards="", equipments="", work_types="", legal_req="Y"),
    # ---- housekeeping_control ----
    dict(code="ctrl_housekeeping_cleanup", name_ko="정리·정돈·청소",
         category="housekeeping_control", type="housekeeping_cleanup",
         description="작업장·통로의 자재 적치, 누유·분진을 정리한다",
         keywords="정리정돈|적치|통로 확보|미끄럼",
         verbs="정리|청소|제거",
         sentence_types="requirement,procedure",
         hazards="전도", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_slip_prevention", name_ko="미끄럼 방지",
         category="housekeeping_control", type="slip_prevention",
         description="바닥 누유·결빙·빗물로 인한 미끄럼을 방지한다",
         keywords="미끄럼|결빙|누유",
         verbs="방지|제거",
         sentence_types="requirement",
         hazards="전도", equipments="", work_types="", legal_req="Y"),
    # ---- traffic_control ----
    dict(code="ctrl_traffic_guide_assignment", name_ko="차량 유도자 배치",
         category="traffic_control", type="traffic_guide_assignment",
         description="중장비·차량 이동 구간에 신호수·유도자를 배치한다",
         keywords="유도자|신호수|차량 동선",
         verbs="배치|유도",
         sentence_types="requirement",
         hazards="충돌", equipments="양중", work_types="", legal_req="Y"),
    dict(code="ctrl_backup_alarm_use", name_ko="후진경보 사용",
         category="traffic_control", type="backup_alarm_use",
         description="후진 시 경보장치·유도자로 충돌을 방지한다",
         keywords="후진경보|후진 시 경보",
         verbs="사용|배치",
         sentence_types="requirement",
         hazards="충돌", equipments="", work_types="", legal_req="Y"),
    # ---- mixed / 추가 ----
    dict(code="ctrl_scaffold_inspection", name_ko="비계 점검",
         category="inspection_control", type="scaffold_inspection",
         description="비계 조립 후 및 매일 작업 시작 전 점검한다",
         keywords="비계 점검|비계 조립",
         verbs="점검",
         sentence_types="inspection_rule,equipment_rule",
         hazards="붕괴,추락", equipments="비계", work_types="비계_조립,비계_해체", legal_req="Y"),
    dict(code="ctrl_crane_signal_rule", name_ko="크레인 신호체계",
         category="supervision_control", type="crane_signal_rule",
         description="크레인 작업 시 정해진 신호체계로만 작업지시를 전달한다",
         keywords="크레인 신호|신호체계|수신호",
         verbs="준수|전달",
         sentence_types="procedure,requirement",
         hazards="비래낙하,중량물", equipments="양중", work_types="양중", legal_req="Y"),
    dict(code="ctrl_pre_energization_check", name_ko="통전 전 확인",
         category="inspection_control", type="pre_energization_check",
         description="전기 투입 전 주변 작업자 철수·접지 해제 여부를 확인한다",
         keywords="통전|전원 투입|활선 확인",
         verbs="확인|철수",
         sentence_types="inspection_rule,procedure",
         hazards="감전", equipments="", work_types="", legal_req="Y"),
    dict(code="ctrl_hot_work_area_clear", name_ko="화기작업 주변 가연물 제거",
         category="housekeeping_control", type="hot_work_area_clear",
         description="용접·용단 작업 전 10m 이내 가연물을 제거하거나 격리한다",
         keywords="가연물|가연물 제거|10m",
         verbs="제거|격리",
         sentence_types="requirement,procedure",
         hazards="", equipments="", work_types="용접", legal_req="Y"),
    dict(code="ctrl_harness_attachment", name_ko="안전대 부착설비 설치",
         category="engineering_control", type="harness_attachment",
         description="고소작업 시 안전대를 걸 수 있는 부착설비(생명선)를 설치한다",
         keywords="안전대 부착설비|생명선|lifeline",
         verbs="설치",
         sentence_types="equipment_rule,requirement",
         hazards="추락", equipments="고소작업", work_types="고소작업", legal_req="Y"),
    dict(code="ctrl_noise_exposure_limit", name_ko="소음 노출한도 관리",
         category="health_control", type="noise_exposure_limit",
         description="소음 노출시간·강도를 기준 이내로 관리한다",
         keywords="소음|dB|청력보존",
         verbs="관리|측정",
         sentence_types="requirement,inspection_rule",
         hazards="소음진동", equipments="", work_types="", legal_req="Y"),
]


# ---------------------------------------------------------------------------
# master 저장
# ---------------------------------------------------------------------------

OUT_MASTER = PROJECT_ROOT / "data" / "risk_db" / "master" / "controls_master_draft.csv"
OUT_MAP    = PROJECT_ROOT / "data" / "risk_db" / "master" / "sentence_control_mapping_sample.csv"
IN_SAMPLE  = PROJECT_ROOT / "data" / "risk_db" / "schema" / "sentence_labeling_sample.csv"


def write_master() -> int:
    OUT_MASTER.parent.mkdir(parents=True, exist_ok=True)
    fields = ["control_code","control_name_ko","control_name_en","control_category","control_type",
              "description","typical_keywords","typical_verbs",
              "related_sentence_types","related_hazard_codes","related_equipment_codes",
              "related_work_type_codes","legal_required_possible","review_status","note"]
    with open(OUT_MASTER, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in CONTROLS_DRAFT:
            w.writerow({
                "control_code": r["code"],
                "control_name_ko": r["name_ko"],
                "control_name_en": r.get("type", ""),
                "control_category": r["category"],
                "control_type": r["type"],
                "description": r["description"],
                "typical_keywords": r["keywords"],
                "typical_verbs": r["verbs"],
                "related_sentence_types": r["sentence_types"],
                "related_hazard_codes": r.get("hazards") or "",
                "related_equipment_codes": r.get("equipments") or "",
                "related_work_type_codes": r.get("work_types") or "",
                "legal_required_possible": r.get("legal_req", "N"),
                "review_status": "draft",
                "note": r.get("note", ""),
            })
    return len(CONTROLS_DRAFT)


# ---------------------------------------------------------------------------
# 샘플 매핑
# ---------------------------------------------------------------------------

# (category, control_code, 키워드들) — 순서대로 탐색, 첫 매칭 승리
CTRL_RULES: list[tuple[str, str, list[str]]] = [
    # 우선순위 높은 구체 규칙
    ("emergency_control",   "ctrl_emergency_evacuation", ["대피","피난","비상연락","집결지"]),
    ("emergency_control",   "ctrl_fire_extinguisher_setup", ["소화기","소화전","소화설비"]),
    ("supervision_control", "ctrl_fire_watch_assignment", ["화재감시인"]),
    ("supervision_control", "ctrl_standby_person_assignment", ["감시인","감시자"]),
    ("supervision_control", "ctrl_signalman_assignment", ["신호수","유도자"]),
    ("supervision_control", "ctrl_supervisor_assignment", ["관리감독자","작업지휘자"]),
    ("permit_control",      "ctrl_confined_space_permit", ["밀폐공간 작업허가"]),
    ("permit_control",      "ctrl_hot_work_permit", ["화기작업 허가"]),
    ("permit_control",      "ctrl_work_permit_issue", ["작업허가서","작업허가"]),
    ("inspection_control",  "ctrl_atmospheric_measurement", ["산소농도","유해가스","가스농도","농도 측정"]),
    ("inspection_control",  "ctrl_working_environment_measurement", ["작업환경측정","유해인자 측정"]),
    ("inspection_control",  "ctrl_pre_work_inspection", ["작업 전 점검","시업 전 점검","작업 시작 전 점검"]),
    ("inspection_control",  "ctrl_scaffold_inspection", ["비계 점검"]),
    ("inspection_control",  "ctrl_periodic_inspection", ["정기점검","자체점검","매일 점검","매월","6개월마다"]),
    ("inspection_control",  "ctrl_checklist_verification", ["체크리스트","점검표","자율점검"]),
    ("document_control",    "ctrl_msds_posting", ["MSDS","물질안전보건자료","경고표지"]),
    ("document_control",    "ctrl_incident_report", ["중대재해","산업재해","재해 발생 시"]),
    ("document_control",    "ctrl_work_plan_preparation", ["작업계획서","작업계획"]),
    ("document_control",    "ctrl_safety_sign_posting", ["안전보건표지","주의표지"]),
    ("document_control",    "ctrl_record_retention", ["보존","기록","관리대장"]),
    ("training_control",    "ctrl_special_training", ["특별교육","특별안전교육","특별안전보건교육"]),
    ("training_control",    "ctrl_pre_work_briefing", ["TBM","툴박스미팅","조회","작업 전 교육"]),
    ("training_control",    "ctrl_safety_training_general", ["안전보건교육","안전교육","교육을 실시","정기교육"]),
    ("ppe_control",         "ctrl_ppe_provision", ["보호구를 지급","보호구 지급","보호구를 비치"]),
    ("ppe_control",         "ctrl_ppe_wear", ["보호구","안전모","안전대","안전화","방진마스크","호흡보호구","내화학장갑","보안경","보호복","귀마개"]),
    ("engineering_control", "ctrl_harness_attachment", ["안전대 부착설비","생명선"]),
    ("engineering_control", "ctrl_fall_protection_install", ["안전난간","안전난간대","작업발판","개구부 덮개","방호선","추락방지망"]),
    ("engineering_control", "ctrl_local_ventilation_install", ["국소배기","환기장치","배기설비"]),
    ("engineering_control", "ctrl_guard_installation", ["방호장치","가드","안전덮개","인터록","과부하방지장치"]),
    ("engineering_control", "ctrl_lockout_tagout", ["LOTO","기동장치를 잠","전원차단"]),
    ("engineering_control", "ctrl_electrical_isolation", ["충전전로","정전","접지","활선"]),
    ("engineering_control", "ctrl_confined_space_ventilation", ["밀폐공간 환기"]),
    ("engineering_control", "ctrl_drop_prevention", ["낙하방지","낙하물 방지망","방호선반"]),
    ("housekeeping_control","ctrl_hot_work_area_clear", ["가연물 제거"]),
    ("housekeeping_control","ctrl_slip_prevention", ["미끄럼"]),
    ("housekeeping_control","ctrl_housekeeping_cleanup", ["정리정돈","적치","통로"]),
    ("administrative_control","ctrl_access_restriction", ["출입금지","출입통제","관계자 외 출입"]),
    ("administrative_control","ctrl_work_zone_separation", ["작업구역 분리"]),
    ("administrative_control","ctrl_simultaneous_work_coordination", ["혼재작업","안전보건협의체"]),
    ("traffic_control",     "ctrl_traffic_guide_assignment", ["차량 동선","유도자 배치"]),
    ("traffic_control",     "ctrl_backup_alarm_use", ["후진경보"]),
    ("health_control",      "ctrl_special_health_check", ["특수건강진단","배치전건강진단"]),
    ("health_control",      "ctrl_noise_exposure_limit", ["dB","청력보존"]),
    ("health_control",      "ctrl_exposure_monitoring", ["노출기준","허용기준","TLV"]),
]

# control_type 별 category 역색인 — master 와 일치 보장
CODE_TO_CATEGORY = {r["code"]: r["category"] for r in CONTROLS_DRAFT}
CODE_TO_NAME     = {r["code"]: r["name_ko"] for r in CONTROLS_DRAFT}


ELIGIBLE_STYPE = {
    "requirement","equipment_rule","ppe_rule","inspection_rule",
    "education_rule","document_rule","emergency_rule","procedure",
    "condition_trigger",
}


def map_sentence(stype: str, text: str) -> tuple[str, str, str, str]:
    """return (category, code, name_ko, confidence)"""
    if stype not in ELIGIBLE_STYPE:
        return ("", "", "", "low")
    for cat, code, kws in CTRL_RULES:
        if any(kw in text for kw in kws):
            name = CODE_TO_NAME.get(code, "")
            # 단일 키워드 1회 hit 은 medium, 2회 이상 hit 은 high
            hits = sum(1 for kw in kws if kw in text)
            conf = "high" if hits >= 2 else "medium"
            # sentence_type 과 일치하지 않으면 confidence 한 단계 내림
            return (cat, code, name, conf)
    return ("", "", "", "low")


def write_mapping() -> tuple[int, dict]:
    if not IN_SAMPLE.exists():
        print(f"[WARN] missing {IN_SAMPLE}", file=sys.stderr)
        return (0, {})
    OUT_MAP.parent.mkdir(parents=True, exist_ok=True)

    out_fields = [
        "sample_id","sentence_text","source_type","sentence_type",
        "obligation_level","action_type","condition_type",
        "hazard_candidate","equipment_candidate","work_type_candidate",
        "control_category_candidate","control_type_candidate",
        "control_name_candidate","legal_required_possible",
        "confidence","review_note",
    ]
    cat_counter: dict[str, int] = {}
    code_counter: dict[str, int] = {}
    hit_count = 0

    with open(IN_SAMPLE, "r", encoding="utf-8-sig") as rf, \
         open(OUT_MAP, "w", encoding="utf-8-sig", newline="") as wf:
        rdr = csv.DictReader(rf)
        wtr = csv.DictWriter(wf, fieldnames=out_fields)
        wtr.writeheader()
        for row in rdr:
            sid = row["sample_id"]
            stype = row.get("sentence_type_candidate","")
            text = row.get("sentence_text","")
            cat, code, name, conf = map_sentence(stype, text)
            if code:
                hit_count += 1
                cat_counter[cat] = cat_counter.get(cat, 0) + 1
                code_counter[code] = code_counter.get(code, 0) + 1
            # master 에서 legal_req 표식 가져오기
            legal = ""
            for r in CONTROLS_DRAFT:
                if r["code"] == code:
                    legal = r.get("legal_req","")
                    break
            wtr.writerow({
                "sample_id": sid,
                "sentence_text": text,
                "source_type": row.get("source_type",""),
                "sentence_type": stype,
                "obligation_level": row.get("obligation_level_candidate",""),
                "action_type": row.get("action_type_candidate",""),
                "condition_type": row.get("condition_type_candidate",""),
                "hazard_candidate": row.get("hazard_candidate",""),
                "equipment_candidate": row.get("equipment_candidate",""),
                "work_type_candidate": row.get("work_type_candidate",""),
                "control_category_candidate": cat,
                "control_type_candidate": code,
                "control_name_candidate": name,
                "legal_required_possible": legal,
                "confidence": conf,
                "review_note": "",
            })
    return hit_count, {"category": cat_counter, "code_top": sorted(code_counter.items(), key=lambda kv:-kv[1])[:10]}


def main() -> int:
    n_master = write_master()
    n_hit, stats = write_mapping()
    print(f"[MASTER] {OUT_MASTER}  rows={n_master}")
    print(f"[MAPPING] {OUT_MAP}  hit={n_hit}")
    print(f"[BY_CATEGORY] {stats.get('category')}")
    print(f"[TOP_CODES]   {stats.get('code_top')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

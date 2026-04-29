# 신축공사 안전서류 일정 매트릭스

**작성일**: 2026-04-29  
**범위**: 일반 건축 신축공사 (소방·전기·기계설비 포함) — 착공~준공  
**기준**: 핵심 안전서류 87종 + 1차 부대서류 10종  
**목적**: 웹 자동생성 규칙의 설계 기준 문서

> **제외 범위**: 리모델링, 개보수, 철거·해체 단독공사, 석면해체, 소방감리 전용,  
> 외국인 근로자 다국어 서류, 유지보수·소규모 보수공사

---

## 목차

1. [법령 근거 요약](#1-법령-근거-요약)
2. [일정 단계 개요](#2-일정-단계-개요)
3. [단계별 안전서류 매트릭스](#3-단계별-안전서류-매트릭스)
   - [Phase 0 — 공사 등록/계약 직후](#phase-0--공사-등록계약-직후)
   - [Phase 1 — 착공 전](#phase-1--착공-전)
   - [Phase 2 — 착공계 제출 / 현장 개설](#phase-2--착공계-제출--현장-개설)
   - [Phase 3 — 근로자 최초 투입 전](#phase-3--근로자-최초-투입-전)
   - [Phase 4 — 장비 최초 반입 전](#phase-4--장비-최초-반입-전)
   - [Phase 5 — 공종별 착수 전](#phase-5--공종별-착수-전)
   - [Phase 6 — 매일 작업 전](#phase-6--매일-작업-전)
   - [Phase 7 — 작업 중 / 작업 종료](#phase-7--작업-중--작업-종료)
   - [Phase 8 — 주간 반복](#phase-8--주간-반복)
   - [Phase 9 — 월간 반복](#phase-9--월간-반복)
   - [Phase 10 — 이벤트 발생 시](#phase-10--이벤트-발생-시)
   - [Phase 11 — 준공 2~4주 전](#phase-11--준공-24주-전)
   - [Phase 12 — 준공 시 / 준공 후 보존](#phase-12--준공-시--준공-후-보존)
4. [웹 자동생성 트리거 규칙](#4-웹-자동생성-트리거-규칙)
5. [부대서류 연동 매핑](#5-부대서류-연동-매핑)
6. [향후 후보 서류 (미구현)](#6-향후-후보-서류-미구현)

---

## 1. 법령 근거 요약

### 1-1. 산업안전보건법

| 조항 | 내용 | 관련 서류 |
|------|------|-----------|
| 제15조 | 안전보건관리책임자 지정 | safety_manager_appointment_report |
| 제17조 | 안전관리자 선임 | safety_manager_appointment_report |
| 제29조 | 근로자 안전보건교육 (채용 시, 정기, 특별) | education_log, special_education_log |
| 제36조 | 위험성평가 실시 | risk_assessment, risk_assessment_register |
| 제37조 | 위험성평가 결과 공지 | risk_assessment_result_notice |
| 제64조 | 도급인의 안전조치 — 협력업체 안전보건 협의 | contractor_safety_consultation |
| 제66조 | 도급인의 안전조치 — 협력업체 안전서류 확인 | contractor_safety_document_checklist |
| 제72조 | 산업안전보건관리비 계상·사용 | safety_cost_use_plan |
| 제54조 | 중대재해 발생 시 즉시 보고 | serious_accident_immediate_report |
| 제57조 | 산업재해 기록 및 보고 | industrial_accident_report, industrial_accident_status_ledger |
| 제125조 | 작업환경측정 | work_environment_measurement |
| 제130조 | 건강진단 실시 | health_exam_result, special_health_examination |

### 1-2. 산업안전보건기준에 관한 규칙 — 제38조 작업계획서 대상

| 작업 종류 | 해당 법령 | 관련 서류 |
|-----------|-----------|-----------|
| 굴착 작업 | 제38조 제1항 1호 | excavation_workplan, excavation_work_permit |
| 차량계 건설기계 사용 | 제38조 제1항 4호 | vehicle_construction_workplan |
| 차량계 하역운반기계 사용 | 제38조 제1항 5호 | material_handling_workplan |
| 고소작업대 사용 | 제38조 제1항 6호 | aerial_work_platform_use_plan |
| 중량물 취급 | 제38조 제1항 7호 | heavy_lifting_workplan |
| 타워크레인 설치·해체·변경 | 제38조 제1항 8호 | tower_crane_workplan |
| 항타기·항발기 사용 | 제38조 제1항 | piling_workplan, piling_use_workplan |
| 거푸집·동바리 설치·해체 | 별도 기준 | formwork_shoring_workplan |
| 비계 설치·해체 | 별도 기준 | scaffold_installation_checklist |
| 전기 작업 | 제319조~제320조 | electrical_workplan, electrical_work_permit |
| 밀폐공간 작업 | 제618조~ | confined_space_workplan, confined_space_permit |
| 화기 작업 | 제241조 | hot_work_workplan, hot_work_permit |

### 1-3. 건설기술진흥법

| 항목 | 내용 | 비고 |
|------|------|------|
| 안전관리계획서 | 1종 시설물 또는 지하 10m 이상 굴착 등 대상 공사 의무 수립 | 향후 후보 |
| 공정별 안전점검 | 건설사고 예방 목적 | safety_patrol_inspection_log |
| 비상조치계획 | 계획서 구성 항목 | emergency_contact_evacuation_plan |

---

## 2. 일정 단계 개요

```
Phase 0  공사 등록/계약 직후
Phase 1  착공 전                          ← 기본 안전체계 수립
Phase 2  착공계 제출 / 현장 개설
Phase 3  근로자 최초 투입 전              ← 교육/PPE/서약
Phase 4  장비 최초 반입 전               ← 장비 자격/반입
Phase 5  공종별 착수 전                  ← 작업계획서/PTW/특별교육
  5-1  토공·굴착
  5-2  기초·파일
  5-3  골조·거푸집·동바리
  5-4  비계·고소작업
  5-5  양중·크레인·중량물
  5-6  전기·화기·MSDS
  5-7  설비·소방설비 작업
Phase 6  매일 작업 전                    ← TBM / 일상 점검
Phase 7  작업 중 / 작업 종료
Phase 8  주간 반복
Phase 9  월간 반복
Phase 10 이벤트 발생 시                  ← 사고/비상/개선조치
Phase 11 준공 2~4주 전
Phase 12 준공 시 / 준공 후 보존
```

---

## 3. 단계별 안전서류 매트릭스

### Phase 0 — 공사 등록/계약 직후

| 시점/트리거 | 해야 할 업무 | 핵심서류 form_type | 서류명 | 부대서류 | 작성 주체 | 확인/승인 | 법정/실무 | 보존/제출 | 비고 |
|------------|------------|-------------------|--------|----------|-----------|----------|----------|----------|------|
| 계약 체결 직후 | 안전관리자 선임 보고 | safety_manager_appointment_report | 안전관리자 선임 보고서 | — | 원도급사 | 고용노동부 | 법정 | 제출 | 착공 전 선임 의무 |
| 계약 직후 | 안전보건관리비 사용계획 수립 | safety_cost_use_plan | 산업안전보건관리비 사용계획서 | — | 원도급사 | 현장소장 | 법정 | 보존 | 산업안전보건법 제72조 |

---

### Phase 1 — 착공 전

| 시점/트리거 | 해야 할 업무 | 핵심서류 form_type | 서류명 | 부대서류 | 작성 주체 | 확인/승인 | 법정/실무 | 보존/제출 | 비고 |
|------------|------------|-------------------|--------|----------|-----------|----------|----------|----------|------|
| 착공 전 | 안전보건 방침·목표 수립 및 게시 | safety_policy_goal_notice | 안전보건 방침 및 목표 게시문 | — | 현장소장 | 대표이사 | 법정 | 현장 게시 | |
| 착공 전 | 위험성평가 실시 규정 수립 | risk_assessment_procedure | 위험성평가 실시 규정 | — | 안전관리자 | 현장소장 | 법정 | 보존 | 산안법 제36조 |
| 착공 전 | 연간 교육계획 수립 | annual_safety_education_plan | 연간 안전보건교육 계획서 | attendance_roster | 안전관리자 | 현장소장 | 법정 | 보존 | |
| 착공 전 | 비상연락망·대피계획 수립 | emergency_contact_evacuation_plan | 비상 연락망 및 대피 계획서 | attendance_roster, photo_attachment_sheet | 안전관리자 | 현장소장 | 법정 | 보존·게시 | |
| 착공 전 | 안전보건관리비 사용계획 확정 | safety_cost_use_plan | 산업안전보건관리비 사용계획서 | — | 원도급사 | 현장소장 | 법정 | 보존 | |
| 착공 전 | 협력업체 사전 안전서류 확인 | contractor_safety_document_checklist | 협력업체 안전보건 관련 서류 확인서 | document_attachment_list | 안전관리자 | 현장소장 | 법정 | 보존 | |
| 착공 전 | 도급 안전보건 협의서 작성 | contractor_safety_consultation | 도급·용역 안전보건 협의서 | attendance_roster | 원도급·수급인 | 현장소장 | 법정 | 보존 | 산안법 제64조 |
| 착공 전 | 협력업체 안전보건 수준 평가 | subcontractor_safety_evaluation | 협력업체 안전보건 수준 평가표 | — | 안전관리자 | 현장소장 | 실무 | 보존 | |

---

### Phase 2 — 착공계 제출 / 현장 개설

| 시점/트리거 | 해야 할 업무 | 핵심서류 form_type | 서류명 | 부대서류 | 작성 주체 | 확인/승인 | 법정/실무 | 보존/제출 | 비고 |
|------------|------------|-------------------|--------|----------|-----------|----------|----------|----------|------|
| 착공계 제출일 | 위험성평가 최초 실시 | risk_assessment | 위험성평가표 | improvement_completion_check | 관리감독자·근로자 | 안전관리자 | 법정 | 보존 3년 | |
| 착공계 제출일 | 위험성평가 등록부 개설 | risk_assessment_register | 위험성평가 관리 등록부 | — | 안전관리자 | 현장소장 | 법정 | 보존 3년 | |
| 착공계 제출일 | 산재 발생 현황 대장 개설 | industrial_accident_status_ledger | 산업재해 발생 현황 관리 대장 | — | 안전관리자 | 현장소장 | 법정 | 보존 | |

---

### Phase 3 — 근로자 최초 투입 전

| 시점/트리거 | 해야 할 업무 | 핵심서류 form_type | 서류명 | 부대서류 | 작성 주체 | 확인/승인 | 법정/실무 | 보존/제출 | 비고 |
|------------|------------|-------------------|--------|----------|-----------|----------|----------|----------|------|
| 신규 근로자 등록 시 | 채용 시 교육 실시 | education_log | 안전보건교육 교육일지 | attendance_roster, ppe_receipt_confirmation | 안전관리자 | 현장소장 | 법정 | 보존 3년 | 8시간 이상 |
| 신규 근로자 등록 시 | 안전보건 서약서 징구 | new_worker_safety_pledge | 신규 근로자 안전보건 서약서 | attendance_roster | 근로자 | 관리감독자 | 실무 | 보존 | |
| 신규 근로자 등록 시 | 보호구 지급 및 수령 확인 | ppe_issue_register | 보호구 지급 대장 | ppe_receipt_confirmation | 안전관리자 | 현장소장 | 법정 | 보존 | |
| 신규 근로자 등록 시 | 보호구 점검표 작성 | ppe_management_checklist | 보호구 지급 및 관리 점검표 | ppe_receipt_confirmation | 안전관리자 | 현장소장 | 실무 | 보존 | |
| 근로자 투입 전 전체 | 위험성평가 결과 공지 | risk_assessment_result_notice | 위험성평가 결과 근로자 공지문 | attendance_roster | 안전관리자 | 현장소장 | 법정 | 보존 | |
| 건강진단 대상자 확인 | 건강진단 결과 관리 | health_exam_result | 근로자 건강진단 결과 확인서 | — | 안전관리자 | 현장소장 | 법정 | 보존 | |
| MSDS 해당 물질 반입 시 | MSDS 비치 및 교육 | msds_posting_education_check | MSDS 비치 및 교육 확인서 | attendance_roster | 안전관리자 | 현장소장 | 법정 | 보존 | |

---

### Phase 4 — 장비 최초 반입 전

| 시점/트리거 | 해야 할 업무 | 핵심서류 form_type | 서류명 | 부대서류 | 작성 주체 | 확인/승인 | 법정/실무 | 보존/제출 | 비고 |
|------------|------------|-------------------|--------|----------|-----------|----------|----------|----------|------|
| 장비 반입 등록 | 장비 반입 신청 | equipment_entry_application | 건설 장비 반입 신청서 (v2) | equipment_operator_qualification_check, document_attachment_list | 협력업체 | 안전관리자 | 법정 | 보존 | |
| 장비 반입 등록 | 보험·검사증 확인 | equipment_insurance_inspection_check | 건설 장비 보험·정기검사증 확인서 | document_attachment_list, photo_attachment_sheet | 안전관리자 | 현장소장 | 법정 | 보존 | |
| 타워크레인 최초 설치 | 타워크레인 작업계획서 수립 | tower_crane_workplan | 타워크레인 작업계획서 | equipment_operator_qualification_check, attendance_roster | 협력업체 | 안전관리자 | 법정 | 보존 | 설치 전 제출 |
| 타워크레인 최초 설치 | 운전원 자격 확인 | equipment_entry_application | — | equipment_operator_qualification_check | 안전관리자 | 현장소장 | 법정 | 보존 | |
| 이동식 크레인 반입 | 이동식 크레인 작업계획서 | mobile_crane_workplan | 이동식 크레인 작업계획서 | equipment_operator_qualification_check | 협력업체 | 안전관리자 | 법정 | 보존 | |
| 덤프·롤러·불도저 반입 | 차량계 건설기계 작업계획서 | vehicle_construction_workplan | 차량계 건설기계 작업계획서 | equipment_operator_qualification_check | 협력업체 | 안전관리자 | 법정 | 보존 | |
| 하역운반기계 반입 | 하역운반기계 작업계획서 | material_handling_workplan | 차량계 하역운반기계 작업계획서 | equipment_operator_qualification_check | 협력업체 | 안전관리자 | 법정 | 보존 | |
| 장비 반입 후 매일 | 장비 일일 사전점검 | construction_equipment_daily_checklist | 건설장비 일일 사전점검표 | photo_attachment_sheet | 운전원 | 관리감독자 | 법정 | 보존 | |

---

### Phase 5 — 공종별 착수 전

#### 5-1. 토공 · 굴착

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|----------|------|
| 굴착 착수 D-3 이전 | excavation_workplan | 굴착 작업계획서 | attendance_roster | 법정 | 산안규칙 제38조 |
| 굴착 착수 전 | excavation_work_permit | 굴착 작업 허가서 | watchman_assignment_confirmation, work_completion_confirmation | 실무 | PTW |
| 굴착 착수 전 | risk_assessment | 위험성평가표 (굴착) | improvement_completion_check | 법정 | 공종별 별도 평가 |
| 굴착 착수 전 | special_education_log | 특별 안전보건교육 (굴착) | attendance_roster, education_makeup_confirmation | 법정 | 16시간 이상 |
| 굴착 중 추락위험 | fall_protection_checklist | 추락 방호 설비 점검표 | photo_attachment_sheet | 법정 | |

#### 5-2. 기초 · 파일

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|----------|------|
| 항타기 착수 전 | piling_workplan | 항타기·항발기·천공기 사용계획서 | equipment_operator_qualification_check | 법정 | |
| 항타기 사용 전 | piling_use_workplan | 항타기·항발기 사용 작업계획서 | equipment_operator_qualification_check | 법정 | |

#### 5-3. 골조 · 거푸집 · 동바리

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|----------|------|
| 거푸집·동바리 착수 전 | formwork_shoring_workplan | 거푸집·동바리 작업계획서 | attendance_roster | 법정 | |
| 설치 완료 후 | formwork_shoring_installation_checklist | 거푸집 및 동바리 설치 점검표 | photo_attachment_sheet | 법정 | |
| 거푸집 작업 시 | risk_assessment | 위험성평가표 (거푸집) | improvement_completion_check | 법정 | |

#### 5-4. 비계 · 고소작업

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|----------|------|
| 비계 설치 완료 후 | scaffold_installation_checklist | 비계 설치 점검표 | photo_attachment_sheet | 법정 | |
| 고소작업 착수 전 | work_at_height_permit | 고소작업 허가서 | watchman_assignment_confirmation, work_completion_confirmation | 실무 | PTW |
| 고소작업대 사용 전 | aerial_work_platform_use_plan | 고소작업대 사용계획서 | equipment_operator_qualification_check | 법정 | |
| 사다리·작업발판 사용 | ladder_stepladder_workboard_use_plan | 사다리·말비계·작업발판 사용계획서 | — | 실무 | |
| 고소작업 착수 전 | fall_protection_checklist | 추락 방호 설비 점검표 | photo_attachment_sheet | 법정 | |

#### 5-5. 양중 · 크레인 · 중량물

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|----------|------|
| 중량물 작업 착수 전 | heavy_lifting_workplan | 중량물 취급 작업계획서 | equipment_operator_qualification_check | 법정 | 산안규칙 제38조 |
| 양중기·호이스트 사용 전 | lifting_equipment_workplan | 양중기·호이스트·윈치 작업계획서 | equipment_operator_qualification_check | 법정 | |
| 리프트·곤돌라 사용 전 | lift_gondola_use_plan | 리프트·곤돌라 사용계획서 | equipment_operator_qualification_check | 법정 | |
| 중량물 인양 시 | lifting_work_permit | 중량물 인양·중장비사용 작업 허가서 | watchman_assignment_confirmation, work_completion_confirmation | 실무 | PTW |
| 타워크레인 자체점검 | tower_crane_self_inspection_checklist | 타워크레인 자체 점검표 | photo_attachment_sheet | 법정 | |

#### 5-6. 전기 · 화기 · MSDS

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|----------|------|
| 전기 작업 착수 전 | electrical_workplan | 전기 작업계획서 | attendance_roster | 법정 | |
| 전기 작업 허가 | electrical_work_permit | 전기작업 허가서 / LOTO | watchman_assignment_confirmation, work_completion_confirmation | 법정 | PTW |
| 임시전기 설치 | temp_electrical_installation_permit | 임시전기 설치·연결 허가서 | work_completion_confirmation | 실무 | PTW |
| 임시전기·발전기 사용 | temp_power_generator_use_plan | 임시전기·발전기 사용계획서 | — | 실무 | |
| 용접·화기 작업 착수 전 | hot_work_workplan | 용접·용단·화기작업 계획서 | attendance_roster | 실무 | |
| 화기작업 허가 | hot_work_permit | 화기작업 허가서 | watchman_assignment_confirmation, work_completion_confirmation | 실무 | PTW |
| 화기 후 감시 필요 | hot_work_permit | — | watchman_assignment_confirmation | 실무 | 30분 이상 감시 |
| 유해화학물질 반입 | hazardous_chemical_checklist | 유해화학물질 취급 점검표 | — | 법정 | |
| 유해화학물질 반입 | msds_posting_education_check | MSDS 비치 및 교육 확인서 | attendance_roster | 법정 | |
| 전기설비 정기점검 | electrical_facility_checklist | 전기설비 정기 점검표 | photo_attachment_sheet | 법정 | |

#### 5-7. 설비 · 소방설비 작업

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|----------|------|
| 콤프레샤·공압장비 사용 | compressor_pneumatic_equipment_plan | 콤프레샤·공압장비 사용계획서 | — | 실무 | |
| 밀폐공간 작업 발생 시 | confined_space_workplan | 밀폐공간 작업계획서 | attendance_roster | 법정 | 저수조·맨홀 등 |
| 밀폐공간 허가 | confined_space_permit | 밀폐공간 작업허가서 | confined_space_gas_measurement, watchman_assignment_confirmation, work_completion_confirmation | 법정 | PTW |
| 밀폐공간 점검 | confined_space_checklist | 밀폐공간 사전 안전점검표 | confined_space_gas_measurement | 법정 | |
| 특수건강진단 대상자 | special_health_examination | 특수건강진단 대상자 및 결과 관리대장 | — | 법정 | |
| 화재예방 주기적 점검 | fire_prevention_checklist | 화재 예방 점검표 | photo_attachment_sheet | 실무 | |

---

### Phase 6 — 매일 작업 전

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 작성 주체 | 확인/승인 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|-----------|----------|----------|------|
| 매일 오전 작업 시작 전 | tbm_log | TBM 안전점검 일지 | attendance_roster, photo_attachment_sheet | 관리감독자 | 안전관리자 | 법정 | |
| 매일 오전 | pre_work_safety_check | 작업 전 안전 확인서 | — | 관리감독자 | 현장소장 | 실무 | |
| 매일 오전 | weather_condition_log | 기상 조건 기록 일지 | — | 안전관리자 | 현장소장 | 실무 | 강풍·강우 작업중지 판단 |
| 매일 | safety_management_log | 안전관리 일지 | — | 안전관리자 | 현장소장 | 법정 | |
| 매일 | supervisor_safety_log | 관리감독자 안전보건 업무 일지 | — | 관리감독자 | 현장소장 | 법정 | |
| 장비 사용일 매일 | construction_equipment_daily_checklist | 건설장비 일일 사전점검표 | — | 운전원 | 관리감독자 | 법정 | |

---

### Phase 7 — 작업 중 / 작업 종료

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 작성 주체 | 확인/승인 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|-----------|----------|----------|------|
| PTW 작업 종료 후 | 해당 PTW — | — | work_completion_confirmation | 작업책임자 | 안전관리자 | 실무 | 화기·고소·전기·굴착·밀폐·중량물 공통 |
| 밀폐공간 작업 중 | confined_space_permit | — | confined_space_gas_measurement | 측정자 | 안전관리자 | 법정 | 30분 간격 재측정 |
| 고위험 작업 시 | 해당 PTW — | — | watchman_assignment_confirmation | 안전관리자 | 현장소장 | 실무 | 감시인 배치 확인 |
| 순찰 중 | safety_patrol_inspection_log | 안전순찰 점검 일지 | photo_attachment_sheet, improvement_completion_check | 안전관리자 | 현장소장 | 실무 | |

---

### Phase 8 — 주간 반복

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 작성 주체 | 확인/승인 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|-----------|----------|----------|------|
| 주 1회 | risk_assessment | 위험성평가표 (공정 변경 시) | improvement_completion_check | 관리감독자 | 안전관리자 | 법정 | 작업내용 변경 시 수시평가 |
| 주 1회 | safety_patrol_inspection_log | 안전순찰 점검 일지 | photo_attachment_sheet | 안전관리자 | 현장소장 | 실무 | |
| 주 1회 (고소) | fall_protection_checklist | 추락 방호 설비 점검표 | photo_attachment_sheet | 안전관리자 | 현장소장 | 법정 | |
| 주 1회 (화재위험) | fire_prevention_checklist | 화재 예방 점검표 | photo_attachment_sheet | 안전관리자 | 현장소장 | 실무 | |
| 주 1회 (타워크레인) | tower_crane_self_inspection_checklist | 타워크레인 자체 점검표 | photo_attachment_sheet | 운전원 | 안전관리자 | 법정 | |

---

### Phase 9 — 월간 반복

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 작성 주체 | 확인/승인 | 법정/실무 | 비고 |
|------------|-------------------|--------|----------|-----------|----------|----------|------|
| 월 1회 | education_log | 정기 안전보건교육 일지 | attendance_roster, education_makeup_confirmation | 안전관리자 | 현장소장 | 법정 | 매월 2시간 이상 |
| 월 1회 | risk_assessment_meeting_minutes | 위험성평가 참여 회의록 | attendance_roster | 안전관리자 | 현장소장 | 법정 | |
| 월 1회 | safety_committee_minutes | 안전보건협의체 회의록 | attendance_roster | 안전관리자 | 현장소장 | 법정 | 관계수급인 참여 |
| 월 1회 | ppe_management_checklist | 보호구 지급 및 관리 점검표 | ppe_receipt_confirmation | 안전관리자 | 현장소장 | 법정 | |
| 월 1회 | subcontractor_safety_evaluation | 협력업체 안전보건 수준 평가표 | — | 안전관리자 | 현장소장 | 실무 | |
| 월 1회 | electrical_facility_checklist | 전기설비 정기 점검표 | photo_attachment_sheet | 안전관리자 | 현장소장 | 법정 | |
| 월 1회 | safety_culture_activity_log | 안전문화 활동 기록부 | photo_attachment_sheet, attendance_roster | 안전관리자 | 현장소장 | 실무 | |

---

### Phase 10 — 이벤트 발생 시

#### 10-1. 산업재해 발생

| 이벤트 | 핵심서류 form_type | 서류명 | 부대서류 | 제출 기한 | 법정/실무 |
|--------|-------------------|--------|----------|----------|----------|
| 재해 즉시 | emergency_first_aid_record | 응급조치 실시 기록서 | photo_attachment_sheet | 즉시 | 실무 |
| 중대재해 즉시 | serious_accident_immediate_report | 중대재해 발생 즉시 보고서 | — | 즉시 (고용부 보고) | 법정 |
| 재해 발생 후 1개월 이내 | industrial_accident_report | 산업재해조사표 | photo_attachment_sheet, document_attachment_list | 1개월 이내 | 법정 |
| 재해 후 원인 분석 | accident_root_cause_prevention_report | 재해 원인 분석 및 재발 방지 보고서 | improvement_completion_check, photo_attachment_sheet | 30일 이내 | 법정 |
| 재해 기록 | industrial_accident_status_ledger | 산업재해 발생 현황 관리 대장 | — | 상시 | 법정 |

#### 10-2. 아차사고 / 불안전 행동 발견

| 이벤트 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 |
|--------|-------------------|--------|----------|----------|
| 아차사고 발견 즉시 | near_miss_report | 아차사고 보고서 | photo_attachment_sheet, improvement_completion_check | 실무 |
| 개선조치 후 | risk_assessment | 위험성평가표 (재평가) | improvement_completion_check | 법정 |

#### 10-3. 위험성평가 개선조치 완료

| 이벤트 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 |
|--------|-------------------|--------|----------|----------|
| 개선대책 실행 완료 | risk_assessment_register | 위험성평가 관리 등록부 (업데이트) | improvement_completion_check | 법정 |
| 개선 후 공지 | risk_assessment_result_notice | 위험성평가 결과 근로자 공지문 | attendance_roster | 법정 |

#### 10-4. 교육 미참석자 발생

| 이벤트 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 |
|--------|-------------------|--------|----------|----------|
| 미참석자 추가교육 실시 | education_log | 안전보건교육 교육일지 | education_makeup_confirmation, attendance_roster | 법정 |

#### 10-5. 방사선 투과검사 실시

| 이벤트 | 핵심서류 form_type | 서류명 | 부대서류 | 법정/실무 |
|--------|-------------------|--------|----------|----------|
| 방사선 작업 허가 | radiography_work_permit | 방사선 투과검사 작업 허가서 | watchman_assignment_confirmation, work_completion_confirmation | 법정 |

---

### Phase 11 — 준공 2~4주 전

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 작성 주체 | 확인/승인 | 비고 |
|------------|-------------------|--------|----------|-----------|----------|------|
| 준공 D-30 | risk_assessment | 위험성평가표 (마감 공종) | improvement_completion_check | 관리감독자 | 안전관리자 | 마감·설비 공종 |
| 준공 D-30 | safety_patrol_inspection_log | 안전순찰 점검 일지 (전수 점검) | photo_attachment_sheet, improvement_completion_check | 안전관리자 | 현장소장 | 잔여 위험요인 점검 |
| 준공 D-30 | contractor_safety_document_checklist | 협력업체 서류 최종 확인 | document_attachment_list | 안전관리자 | 현장소장 | |
| 준공 D-14 | improvement_completion_check — | — (개선조치 미완료 잔여 확인) | improvement_completion_check | 안전관리자 | 현장소장 | 미완료 항목 전수 재확인 |
| 준공 D-14 | risk_assessment_best_practice_report | 위험성평가 우수 사례 보고서 | photo_attachment_sheet, attendance_roster | 안전관리자 | 현장소장 | 선택 |

---

### Phase 12 — 준공 시 / 준공 후 보존

| 시점/트리거 | 핵심서류 form_type | 서류명 | 부대서류 | 보존 기간 | 비고 |
|------------|-------------------|--------|----------|----------|------|
| 준공 시 | 전 서류 일괄 — | 서류 목록화 | document_attachment_list | — | 프로젝트 보관함으로 이관 |
| 준공 후 | industrial_accident_report | 산업재해조사표 | — | 3년 | 법정 |
| 준공 후 | risk_assessment | 위험성평가표 | — | 3년 | 법정 |
| 준공 후 | education_log | 안전보건교육 교육일지 | — | 3년 | 법정 |
| 준공 후 | safety_management_log | 안전관리 일지 | — | 3년 | 법정 |
| 준공 후 | industrial_accident_status_ledger | 산업재해 발생 현황 관리 대장 | — | 3년 | 법정 |
| 준공 후 | health_exam_result | 근로자 건강진단 결과 확인서 | — | 5년 | 법정 |
| 준공 후 | special_health_examination | 특수건강진단 대상자 및 결과 관리대장 | — | 30년 (발암물질) | 법정 |

---

## 4. 웹 자동생성 트리거 규칙

웹 UI에서 특정 이벤트 발생 시 자동으로 생성 또는 생성 제안할 서류 목록.

### Rule-01 — 신규 근로자 등록

```
트리거:  신규 근로자 등록 (DB 신규 근로자 레코드 생성)
자동 생성 제안:
  - education_log               안전보건교육 교육일지 (채용 시 교육)
  - new_worker_safety_pledge    신규 근로자 안전보건 서약서
  - ppe_issue_register          보호구 지급 대장
  부대서류:
  - attendance_roster
  - ppe_receipt_confirmation
  - education_makeup_confirmation (교육 미참석 발생 시)
조건:  근로자 투입일 D-1 이전
```

### Rule-02 — 공종 착수 전 (공종 유형 = 굴착)

```
트리거:  프로젝트 공종 '굴착' 착수 예정일 D-3
자동 생성 제안:
  - excavation_workplan         굴착 작업계획서
  - excavation_work_permit      굴착 작업 허가서
  - risk_assessment             위험성평가표 (굴착)
  - special_education_log       특별 안전보건교육 (굴착)
  부대서류:
  - attendance_roster
  - photo_attachment_sheet
  - watchman_assignment_confirmation
  - work_completion_confirmation
  - improvement_completion_check
조건:  해당 공종 착수 예정일 입력 시
```

### Rule-03 — 장비 반입 등록

```
트리거:  장비 반입 신청 등록
자동 생성 제안:
  - equipment_entry_application          건설 장비 반입 신청서
  - equipment_insurance_inspection_check 보험·정기검사증 확인서
  - construction_equipment_daily_checklist 일일 사전점검표 (반입일부터 반복)
  부대서류:
  - equipment_operator_qualification_check
  - document_attachment_list
  - photo_attachment_sheet
조건:  장비 종류 + 운전원 정보 입력 시
```

### Rule-04 — PTW 화기작업 허가 발행

```
트리거:  화기작업 허가서 신규 발행
자동 생성 제안:
  - hot_work_permit             화기작업 허가서
  부대서류:
  - watchman_assignment_confirmation   (화재감시자 배치)
  - work_completion_confirmation       (작업 종료 시)
  - photo_attachment_sheet             (작업 전·후 사진)
조건:  허가서 발행 버튼 클릭
```

### Rule-05 — PTW 밀폐공간 허가 발행

```
트리거:  밀폐공간 작업허가서 신규 발행
자동 생성 제안:
  - confined_space_permit       밀폐공간 작업허가서
  - confined_space_checklist    밀폐공간 사전 안전점검표
  부대서류:
  - confined_space_gas_measurement     (산소·가스농도 측정기록표)
  - watchman_assignment_confirmation   (감시인 배치)
  - work_completion_confirmation       (작업 종료)
  - attendance_roster
조건:  허가서 발행 버튼 클릭
```

### Rule-06 — 매일 작업일 오전

```
트리거:  작업일 오전 (매일 반복)
자동 생성 제안:
  - tbm_log                     TBM 안전점검 일지
  - pre_work_safety_check       작업 전 안전 확인서
  - weather_condition_log       기상 조건 기록 일지
  - safety_management_log       안전관리 일지
  부대서류:
  - attendance_roster
  - photo_attachment_sheet (선택)
조건:  작업 시작 버튼 또는 날짜 자동
```

### Rule-07 — 아차사고 / 불안전 행동 등록

```
트리거:  아차사고 보고서 신규 등록
자동 생성 제안:
  - near_miss_report            아차사고 보고서
  부대서류:
  - photo_attachment_sheet
  - improvement_completion_check  (개선조치 완료 확인)
조건:  등록 즉시 자동
```

### Rule-08 — 산업재해 발생 등록

```
트리거:  산업재해 발생 신고 등록
자동 생성 제안:
  - emergency_first_aid_record          응급조치 실시 기록서
  - industrial_accident_report          산업재해조사표
  - accident_root_cause_prevention_report 재해 원인 분석 및 재발 방지 보고서
  - industrial_accident_status_ledger   산업재해 발생 현황 관리 대장 (업데이트)
  중대재해 시 추가:
  - serious_accident_immediate_report   중대재해 발생 즉시 보고서 (즉시 제출)
  부대서류:
  - photo_attachment_sheet
  - improvement_completion_check
  - document_attachment_list
조건:  재해 유형 선택 즉시
```

### Rule-09 — 월간 정기 교육

```
트리거:  매월 교육 일정 도래 (월 1회)
자동 생성 제안:
  - education_log               안전보건교육 교육일지 (정기)
  부대서류:
  - attendance_roster
  - education_makeup_confirmation  (미참석자 발생 시)
조건:  교육 완료 후 서명
```

### Rule-10 — 준공 D-30

```
트리거:  준공 예정일 D-30
자동 생성 제안:
  - safety_patrol_inspection_log 안전순찰 점검 일지 (전수 점검)
  - risk_assessment              위험성평가표 (마감 공종)
  - contractor_safety_document_checklist 협력업체 서류 최종 확인
  부대서류:
  - improvement_completion_check  (잔여 개선조치 확인)
  - document_attachment_list      (전체 서류 목록화)
  - photo_attachment_sheet
조건:  준공일 입력 시 자동 알림
```

---

## 5. 부대서류 연동 매핑

| 부대서류 supplemental_type | 주요 연동 핵심서류 | 주요 발생 Phase |
|---------------------------|------------------|----------------|
| `attendance_roster` | education_log, tbm_log, risk_assessment_meeting_minutes, 모든 PTW | Phase 1~9 (상시) |
| `photo_attachment_sheet` | near_miss_report, safety_patrol_inspection_log, industrial_accident_report | Phase 5~11 |
| `document_attachment_list` | equipment_entry_application, industrial_accident_report, contractor_safety_document_checklist | Phase 1, 4, 10, 11 |
| `confined_space_gas_measurement` | confined_space_permit, confined_space_checklist | Phase 5-7, 7 |
| `work_completion_confirmation` | 모든 PTW (hot, height, electrical, excavation, lifting, temp_electrical) | Phase 5~7 |
| `improvement_completion_check` | risk_assessment, near_miss_report, accident_root_cause_prevention_report | Phase 2, 8~11 |
| `equipment_operator_qualification_check` | equipment_entry_application, tower_crane_workplan, mobile_crane_workplan, heavy_lifting_workplan | Phase 4 |
| `watchman_assignment_confirmation` | confined_space_permit, hot_work_permit, radiography_work_permit | Phase 5-6, 5-7 |
| `education_makeup_confirmation` | education_log, special_education_log | Phase 3, 9, 10 |
| `ppe_receipt_confirmation` | ppe_issue_register, ppe_management_checklist | Phase 3, 9 |

---

## 6. 향후 후보 서류 (미구현)

다음 서류는 현재 87종 핵심서류에 포함되지 않으나 신축공사에서 실무적으로 필요하다.  
**신규 document_id 미부여. 2차 이후 패키지에서 별도 설계 예정.**

| 후보 서류명 | 용도 | 관련 법령/기준 |
|------------|------|----------------|
| 안전관리계획서 | 건기법 대상 공사 필수 | 건설기술진흥법 시행령 제98조 |
| 가설구조물 구조 검토서 | 동바리·비계 구조 안전성 검토 | 건기법, 가설기자재 기준 |
| 착공 전 안전점검 결과서 | 착공 전 현장 안전상태 확인 | 건기법 |
| 근로자 안전보건 교육훈련 계획서 | 공사 전체 교육 로드맵 | 산안법 제29조 |
| 화학물질 목록표 | 현장 반입 화학물질 전수 목록 | 화학물질관리법 |
| 지하매설물 사전 조사 확인서 | 굴착 전 지하매설물 확인 | 도시가스사업법 등 |
| 소음·진동 측정 결과 보고서 | 인접 주민 피해 모니터링 | 소음진동관리법 |
| 누전차단기 설치 확인서 | 임시전기 누전차단기 설치 확인 | 전기설비기술기준 |
| 외국인 근로자 다국어 보호구 확인서 | 외국인 근로자 보호구 수령 확인 | 2차 부대서류 패키지 |
| 석면 사전 조사 결과서 | 기존 건물 철거 포함 시 | 산안법 제119조 (신축 제외) |

---

*본 문서는 웹 자동생성 규칙의 설계 기준 문서이며, builder 구현 계획을 포함하지 않는다.*  
*90종 핵심서류 + 10종 부대서류 범위 내에서만 매핑하였다.*

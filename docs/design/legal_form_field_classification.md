# 법정서류 항목 유형 분류

**작성일**: 2026-04-24  
**입력**: legal_form_field_inventory.md (168개 항목)  
**목적**: 각 항목의 성격을 6개 유형으로 분류하여 builder 입력 설계와 검증 로직 설계에 활용

---

## 분류 코드 정의

| 코드 | 명칭 | 정의 | 판단 기준 |
|------|------|------|---------|
| `LAW` | 법정 필수 | 법령·고시에서 명시 작성 요구 | 미기재 시 과태료·행정처분 근거 |
| `PRAC` | 실무 권장 | 법령 미규정이나 감독 시 실질 확인 | 법적 의무는 없으나 현장에서 사실상 필수 |
| `EVID` | 증빙 필수 | 서명·날인·자격증 번호 등 법적 효력 | 없으면 문서 자체의 법적 효력 문제 |
| `AUTO` | 자동 채움 후보 | 시스템/기존 데이터로 자동 입력 가능 | 사업장 마스터 데이터, 시스템 날짜 등 |
| `USER` | 사용자 입력 필수 | 현장 특수 정보로 사용자만 알 수 있음 | 재해 경위, 실제 운행경로 등 |
| `FORB` | 불필요 추가 금지 | 개인정보보호법·법령 제한으로 포함 금지 | 주민등록번호 직접 기재, 병명 노출 등 |

> 한 항목에 복수 코드 병기 가능. `LAW+AUTO` = 법정 필수이나 자동 채움 가능.

---

## 1. 위험성평가표 항목 분류

| # | 항목명 | field_key | LAW | PRAC | EVID | AUTO | USER | FORB |
|---|--------|-----------|:---:|:----:|:----:|:----:|:----:|:----:|
| 1 | 사업장명 | `company_name` | ✓ | | | ✓ | | |
| 2 | 업종 | `industry` | ✓ | | | ✓ | | |
| 3 | 공정명 | `process` | ✓ | | | | ✓ | |
| 4 | 세부작업명 | `sub_work` | | ✓ | | | ✓ | |
| 5 | 위험분류(대) | `hazard_category_major` | | ✓ | | ✓ | | |
| 6 | 위험분류(중) | `hazard_category_minor` | | ✓ | | ✓ | | |
| 7 | 유해위험요인 | `hazard` | ✓ | | | | ✓ | |
| 8 | 관련근거(법적기준) | `legal_basis` | | ✓ | | ✓ | | |
| 9 | 현재의 안전보건조치 | `current_measures` | ✓ | | | | ✓ | |
| 10 | 평가척도 | `risk_scale` | | ✓ | | ✓ | | |
| 11 | 가능성(빈도) | `probability` | ✓ | | | | ✓ | |
| 12 | 중대성(강도) | `severity` | ✓ | | | | ✓ | |
| 13 | 위험성 수준 | `risk_level` | ✓ | | | ✓ | | |
| 14 | 위험성 감소대책 | `control_measures` | ✓ | | | | ✓ | |
| 15 | 개선후 위험성 | `residual_risk_level` | | ✓ | | | ✓ | |
| 16 | 개선 예정일 | `target_date` | | ✓ | | | ✓ | |
| 17 | 개선 완료일 | `completion_date` | | ✓ | ✓ | | ✓ | |
| 18 | 담당자 | `responsible_person` | ✓ | | ✓ | | ✓ | |
| 19 | 평가 실시일 | `assessment_date` | ✓ | | | ✓ | | |
| 20 | 평가종류 | `assessment_type` | ✓ | | | | ✓ | |
| 21 | 대표자명 | `representative` | | ✓ | | ✓ | | |
| 22 | 작업유형 | `work_type` | | ✓ | | | ✓ | |
| 23 | 현장명 | `site_name` | | ✓ | | ✓ | | |
| 24 | 일련번호 | `no` | | ✓ | | ✓ | | |

---

## 2. 안전보건교육일지 항목 분류

| # | 항목명 | field_key | LAW | PRAC | EVID | AUTO | USER | FORB |
|---|--------|-----------|:---:|:----:|:----:|:----:|:----:|:----:|
| 1 | 교육 종류 | `education_type` | ✓ | | | | ✓ | |
| 2 | 교육 일시 | `education_date` | ✓ | | | ✓ | | |
| 3 | 교육 장소 | `education_location` | ✓ | | | | ✓ | |
| 4 | 교육 시간 합계 | `education_duration_hours` | ✓ | | | ✓ | | |
| 5 | 교육 대상 직종 | `education_target_job` | ✓ | | | | ✓ | |
| 6 | 교육 과목명 | `subjects[].subject_name` | ✓ | | | ✓ | | |
| 7 | 교육 내용 요약 | `subjects[].subject_content` | ✓ | | | | ✓ | |
| 8 | 과목별 시간 | `subjects[].subject_hours` | ✓ | | | ✓ | | |
| 9 | 강사명 | `instructor_name` | ✓ | | ✓ | | ✓ | |
| 10 | 강사 자격 | `instructor_qualification` | ✓ | | ✓ | | ✓ | |
| 11 | 수강자 성명 | `attendees[].attendee_name` | ✓ | | ✓ | | ✓ | |
| 12 | 수강자 직종 | `attendees[].attendee_job_type` | ✓ | | | | ✓ | |
| 13 | 수강자 서명란 | *(수기)* | ✓ | | ✓ | | | |
| 14 | 확인자 성명 | `confirmer_name` | ✓ | | ✓ | | ✓ | |
| 15 | 확인자 직위 | `confirmer_role` | ✓ | | ✓ | | ✓ | |
| 16 | 사업장명 | `site_name` | | ✓ | | ✓ | | |
| 17 | 사업장 소재지 | `site_address` | | ✓ | | ✓ | | |
| 18 | 확인 일자 | `confirm_date` | | ✓ | | ✓ | | |
| 19 | 강사 소속 | *(미정의)* | | ✓ | ✓ | | ✓ | |

---

## 3. 굴착 작업계획서 항목 분류

| # | 항목명 | field_key | LAW | PRAC | EVID | AUTO | USER | FORB |
|---|--------|-----------|:---:|:----:|:----:|:----:|:----:|:----:|
| 1 | 굴착의 방법 | `excavation_method` | ✓ | | | | ✓ | |
| 2 | 흙막이 지보공 종류·설치방법 | `earth_retaining` | ✓ | | | | ✓ | |
| 3 | 굴착기계 종류 및 성능 | `excavation_machine` | ✓ | | | | ✓ | |
| 4 | 토석 운반방법·적재장소 | `soil_disposal` | ✓ | | | | ✓ | |
| 5 | 용수 처리방법 | `water_disposal` | ✓ | | | | ✓ | |
| 6 | 작업 방법 | `work_method` | ✓ | | | | ✓ | |
| 7 | 긴급조치 계획 | `emergency_measure` | ✓ | | | | ✓ | |
| 8 | 사업장명 | `site_name` | | ✓ | | ✓ | | |
| 9 | 현장명 | `project_name` | | ✓ | | ✓ | | |
| 10 | 작업위치 | `work_location` | | ✓ | | | ✓ | |
| 11 | 작업 일자/기간 | `work_date` | | ✓ | | | ✓ | |
| 12 | 작업 책임자 | `supervisor` | | ✓ | ✓ | | ✓ | |
| 13 | 도급업체 | `contractor` | | ✓ | | ✓ | | |
| 14 | 작업단계 | `safety_steps[].task_step` | | ✓ | | | ✓ | |
| 15 | 위험요인 | `safety_steps[].hazard` | | ✓ | | ✓ | | |
| 16 | 안전조치 | `safety_steps[].safety_measure` | | ✓ | | ✓ | | |
| 17 | 유도자 배치 계획 | *(미정의)* | | ✓ | | | ✓ | |
| 18 | 출입통제 범위 | *(미정의)* | | ✓ | | | ✓ | |
| 19 | 지형·지반 사전조사 | *(미정의)* | | ✓ | | | ✓ | |
| 20 | 인접 구조물 영향 | *(미정의)* | | ✓ | | | ✓ | |
| 21 | 작성일 | `sign_date` | | ✓ | | ✓ | | |

---

## 4. 차량계 건설기계 작업계획서 항목 분류

| # | 항목명 | field_key | LAW | PRAC | EVID | AUTO | USER | FORB |
|---|--------|-----------|:---:|:----:|:----:|:----:|:----:|:----:|
| 1 | 기계 종류 | `machine_type` | ✓ | | | | ✓ | |
| 2 | 기계 성능(최대 작업능력) | `machine_capacity` | ✓ | | | | ✓ | |
| 3 | 운행경로 | `travel_route` | ✓ | | | | ✓ | |
| 4 | 작업방법 | `work_method` | ✓ | | | | ✓ | |
| 5 | 현장명/사업장명 | `site_name` | | ✓ | | ✓ | | |
| 6 | 작업위치 | `work_location` | | ✓ | | | ✓ | |
| 7 | 작업기간 | `work_date` | | ✓ | | | ✓ | |
| 8 | 지형·지반 사전조사 | `ground_survey` | | ✓ | | | ✓ | |
| 9 | 유도자 배치 계획 | `guide_worker_plan` | | ✓ | | | ✓ | |
| 10 | 출입통제 방법 | `access_control` | | ✓ | | | ✓ | |
| 11 | 작업반경 | `work_radius` | | ✓ | | | ✓ | |
| 12 | 비상조치 | `emergency_measure` | | ✓ | | | ✓ | |
| 13 | 작업 전 점검항목 | `pre_check_items` | | ✓ | | | ✓ | |
| 14 | 운전자 자격/면허 | `operator_license` | | ✓ | ✓ | | ✓ | |
| 15 | 작업지휘자 성명 | `supervisor` | | ✓ | ✓ | | ✓ | |
| 16 | 안전속도 제한 | `speed_limit` | | ✓ | | | ✓ | |
| 17 | 작성일·서명 | `sign_date` | | ✓ | ✓ | ✓ | | |

---

## 5. 차량계 하역운반기계 작업계획서 항목 분류

| # | 항목명 | field_key | LAW | PRAC | EVID | AUTO | USER | FORB |
|---|--------|-----------|:---:|:----:|:----:|:----:|:----:|:----:|
| 1 | 기계 종류 | `machine_type` | ✓ | | | | ✓ | |
| 2 | 기계 최대 하중(능력) | `machine_max_load` | ✓ | | | | ✓ | |
| 3 | 운행경로 | `travel_route` | ✓ | | | | ✓ | |
| 4 | 작업방법 | `work_method` | ✓ | | | | ✓ | |
| 5 | 현장명/사업장명 | `site_name` | | ✓ | | ✓ | | |
| 6 | 하역화물 종류·중량 | `cargo_type_weight` | | ✓ | | | ✓ | |
| 7 | 보행자 동선 분리 방법 | `pedestrian_separation` | | ✓ | | | ✓ | |
| 8 | 유도자 배치 계획 | `guide_worker_plan` | | ✓ | | | ✓ | |
| 9 | 출입통제 구역 | `access_control` | | ✓ | | | ✓ | |
| 10 | 제한속도 | `speed_limit` | | ✓ | | | ✓ | |
| 11 | 충전/주유 장소 | `refuel_location` | | ✓ | | | ✓ | |
| 12 | 작업 전 점검항목 | `pre_check_items` | | ✓ | | | ✓ | |
| 13 | 운전자 자격/면허 | `operator_license` | | ✓ | ✓ | | ✓ | |
| 14 | 하역 위치·방법 | `unloading_method` | | ✓ | | | ✓ | |
| 15 | 작업지휘자 성명 | `supervisor` | | ✓ | ✓ | | ✓ | |
| 16 | 비상조치 | `emergency_measure` | | ✓ | | | ✓ | |

---

## 6. 산업재해조사표 항목 분류

| # | 항목명 | field_key | LAW | PRAC | EVID | AUTO | USER | FORB |
|---|--------|-----------|:---:|:----:|:----:|:----:|:----:|:----:|
| 1 | 사업장 명칭 | `workplace_name` | ✓ | | | ✓ | | |
| 2 | 사업장 소재지 | `workplace_address` | ✓ | | | ✓ | | |
| 3 | 업종 | `industry` | ✓ | | | ✓ | | |
| 4 | 상시근로자수 | `total_workers` | ✓ | | | ✓ | | |
| 5 | 재해자 성명 | `victim_name` | ✓ | | ✓ | | ✓ | |
| 6 | 재해자 생년월일 | `victim_birth` | ✓ | | | | ✓ | |
| 7 | 재해자 성별 | `victim_gender` | ✓ | | | | ✓ | |
| 8 | 재해자 직종 | `victim_job` | ✓ | | | | ✓ | |
| 9 | 근속기간 | `tenure_period` | ✓ | | | | ✓ | |
| 10 | 고용형태 | `employment_type` | ✓ | | | | ✓ | |
| 11 | 재해 발생일시 | `accident_datetime` | ✓ | | | | ✓ | |
| 12 | 재해 발생장소 | `accident_location` | ✓ | | | | ✓ | |
| 13 | 재해 당시 작업내용 | `work_at_accident` | ✓ | | | | ✓ | |
| 14 | 재해 발생경위 | `accident_description` | ✓ | | | | ✓ | |
| 15 | 기인물 | `cause_object` | ✓ | | | | ✓ | |
| 16 | 불안전한 상태 | `unsafe_condition` | ✓ | | | | ✓ | |
| 17 | 불안전한 행동 | `unsafe_act` | ✓ | | | | ✓ | |
| 18 | 재해 종류 | `accident_severity` | ✓ | | | | ✓ | |
| 19 | 상해 종류 | `injury_type` | ✓ | | | | ✓ | |
| 20 | 상해 부위 | `injury_location` | ✓ | | | | ✓ | |
| 21 | 휴업 일수 | `days_off` | ✓ | | | | ✓ | |
| 22 | 재발방지 대책 | `prevention_measure` | ✓ | | | | ✓ | |
| 23 | 작성일 | `report_date` | ✓ | | | ✓ | | |
| 24 | 작성자 직위·성명 | `reporter_info` | ✓ | | ✓ | | ✓ | |
| 25 | 도급/하도급 관계 | `subcontract_info` | | ✓ | | | ✓ | |
| 26 | 안전교육 이수 여부 | `safety_training_done` | | ✓ | | | ✓ | |
| 27 | 보호구 착용 여부 | `ppe_status` | | ✓ | | | ✓ | |
| 28 | 재해자 주민등록번호 | *(사용 금지)* | | | | | | ✓ |

> **FORB** 항목: 개인정보보호법에 따라 주민등록번호는 별지 30호에서 요구하더라도 디지털 시스템에 원문 저장 금지.

---

## 7. 산업안전보건위원회 회의록 항목 분류

| # | 항목명 | field_key | LAW | PRAC | EVID | AUTO | USER | FORB |
|---|--------|-----------|:---:|:----:|:----:|:----:|:----:|:----:|
| 1 | 개최일시 | `meeting_datetime` | ✓ | | | ✓ | | |
| 2 | 개최장소 | `meeting_location` | ✓ | | | | ✓ | |
| 3 | 위원장 성명 | `chairperson_name` | ✓ | | ✓ | | ✓ | |
| 4 | 근로자위원 명단 | `labor_members` | ✓ | | ✓ | | ✓ | |
| 5 | 사용자위원 명단 | `employer_members` | ✓ | | ✓ | | ✓ | |
| 6 | 심의사항 (의안) | `agenda_items` | ✓ | | | | ✓ | |
| 7 | 의결사항 | `resolution` | ✓ | | | | ✓ | |
| 8 | 의장 서명 | `chairperson_signature` | ✓ | | ✓ | | | |
| 9 | 회의 번호/차수 | `meeting_no` | | ✓ | | ✓ | | |
| 10 | 심의 내용 요약 | `discussion_summary` | | ✓ | | | ✓ | |
| 11 | 결과 이행 담당자·기한 | `action_items` | | ✓ | | | ✓ | |
| 12 | 차기 회의 예정일 | `next_meeting_date` | | ✓ | | | ✓ | |

---

## 8. 도급승인 신청서 항목 분류

| # | 항목명 | field_key | LAW | PRAC | EVID | AUTO | USER | FORB |
|---|--------|-----------|:---:|:----:|:----:|:----:|:----:|:----:|
| 1 | 신청 사업장 상호 | `requester_name` | ✓ | | | ✓ | | |
| 2 | 신청 사업장 대표자 | `requester_ceo` | ✓ | | ✓ | ✓ | | |
| 3 | 신청 사업장 주소 | `requester_address` | ✓ | | | ✓ | | |
| 4 | 도급 내용 (작업 종류) | `contract_work_type` | ✓ | | | | ✓ | |
| 5 | 도급 기간 | `contract_period` | ✓ | | | | ✓ | |
| 6 | 도급 작업 장소 | `contract_location` | ✓ | | | | ✓ | |
| 7 | 수급사업자 명칭 | `contractor_name` | ✓ | | | | ✓ | |
| 8 | 수급사업자 대표자 | `contractor_ceo` | ✓ | | | | ✓ | |
| 9 | 유해·위험 요인 | `hazard_factors` | ✓ | | | | ✓ | |
| 10 | 재해예방 조치 계획 | `prevention_plan` | ✓ | | | | ✓ | |
| 11 | 건강진단 실시 계획 | `health_exam_plan` | ✓ | | | | ✓ | |
| 12 | 도급금액 | `contract_amount` | | ✓ | | | ✓ | |
| 13 | 안전보건 협의체 운영 계획 | `safety_council_plan` | | ✓ | | | ✓ | |
| 14 | 수급사업자 안전관리 실적 | `contractor_safety_record` | | ✓ | | | ✓ | |

---

## 9. 유해위험방지계획서 항목 분류

| # | 항목명 | field_key | LAW | PRAC | EVID | AUTO | USER | FORB |
|---|--------|-----------|:---:|:----:|:----:|:----:|:----:|:----:|
| 1 | 공사 개요 | `project_summary` | ✓ | | | ✓ | | |
| 2 | 공사지역 및 환경 | `project_environment` | ✓ | | | | ✓ | |
| 3 | 공종별 안전보건 계획 | `safety_plan_by_work` | ✓ | | | | ✓ | |
| 4 | 붕괴·추락 위험 방지 계획 | `collapse_fall_plan` | ✓ | | | | ✓ | |
| 5 | 유해물질 취급 계획 | `hazmat_plan` | ✓ | | | | ✓ | |
| 6 | 건설기계·장비 사용 계획 | `equipment_plan` | ✓ | | | | ✓ | |
| 7 | 안전보건 관리체계 | `safety_org` | ✓ | | | ✓ | | |
| 8 | 긴급 대피 계획 | `evacuation_plan` | ✓ | | | | ✓ | |
| 9 | 첨부서류 목록 | `attachments` | ✓ | | | | ✓ | |
| 10 | 사업장 개요 (제조업) | `factory_summary` | ✓ | | | ✓ | | |
| 11 | 주요 설비 목록 | `major_equipment` | ✓ | | | | ✓ | |
| 12 | 유해·위험 설비 현황 | `hazardous_equipment` | ✓ | | | | ✓ | |
| 13 | 주요 위험요인 | `major_hazards` | ✓ | | | | ✓ | |
| 14 | 위험요인별 재해예방 계획 | `hazard_prevention_plan` | ✓ | | | | ✓ | |
| 15 | 공정별 위험성평가 연계 | `risk_assessment_ref` | | ✓ | | ✓ | | |
| 16 | 협력업체 안전관리 계획 | `subcon_safety_plan` | | ✓ | | | ✓ | |
| 17 | 계측관리 계획 | `monitoring_plan` | | ✓ | | | ✓ | |
| 18 | 안전관리 조직 (제조업) | `safety_org_mfg` | ✓ | | | | ✓ | |

---

## 분류 집계 요약

### 전체 항목 유형별 수

| 분류 | 항목 수 | 비율 |
|------|--------|------|
| LAW (법정 필수) | 100 | 60% |
| PRAC (실무 권장) | 68 | 40% |
| EVID (증빙 필수) | 29 | 17% |
| AUTO (자동 채움 후보) | 42 | 25% |
| USER (사용자 입력 필수) | 115 | 68% |
| FORB (불필요 추가 금지) | 1 | 1% |

> 복수 코드 병기 항목은 중복 계산.

### 핵심 패턴 분석

**LAW + AUTO (법정 필수이나 자동 채움 가능)**: 20개
→ 사업장명, 업종, 날짜, 일련번호 등 — builder 생성 시 사업장 마스터 데이터에서 자동 채움 권장

**LAW + USER (법정 필수이며 반드시 사용자 입력)**: 80개
→ 재해경위, 운행경로, 작업방법 등 — 입력 없이 Excel 생성 불가

**PRAC + AUTO (실무 권장이며 자동 채움 가능)**: 18개
→ 현장명, 확인일자, 회의 번호 등 — 자동 채움으로 실무 편의 제공

**EVID 단독 (증빙 전용 — 수기 서명 공란)**: 5개
→ 수강자 서명란, 의장 서명 등 — 시스템에서 빈 셀로 출력, 수기 서명 유도

**FORB**: 1개
→ 주민등록번호 — 디지털 처리 금지, 관련 field_key 미정의 권고

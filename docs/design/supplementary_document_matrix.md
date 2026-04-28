# 부대서류 자동생성 매트릭스

**기준**: 안전서류 Excel Builder v1.0 (safety-builder-v1.0)  
**작성일**: 2026-04-29  
**대상**: catalog DONE 90종 기준 분석 (OUT 3종 제외)  
**목적**: 핵심 안전서류 제출 시 자동 파생 생성되어야 할 부대서류 목록 및 구현 방식 설계

---

## 개요

### 부대서류 정의

| 구분 | 정의 |
|------|------|
| **핵심서류** | 법정 또는 실무 요건을 충족하는 주요 안전서류 (90종 DONE) |
| **부대서류** | 핵심서류 작성·제출 시 함께 생성되어야 하는 파생 출력물 |

### 공통 builder 설계 방향

핵심서류별 독립 부대서류 대신 **공통 builder 3종**을 설계하여 다수 핵심서류에서 재사용한다.

| 공통 builder | 예상 form_type | 재사용 대상 |
|-------------|---------------|-----------|
| 참석자·출입자 명부 | `attendance_roster` | ED·PTW·EM 전반 |
| 사진대지 | `photo_attachment_sheet` | 전 카테고리 |
| 첨부서류 목록표 | `document_attachment_list` | 전 카테고리 |

---

## 1. 교육·근로자 투입 부대서류

### 1.1 ED-001 안전보건교육 교육일지

| 항목 | 내용 |
|------|------|
| 핵심서류 | ED-001 안전보건교육 교육일지 |
| form_type | `education_log` |
| **부대서류** | **① 교육 참석자 명부** |
| 생성 조건 | 교육일지 작성 시 자동 연동; 수강 인원 ≥ 1명 |
| 필요 입력 | site_name, edu_date, edu_subject, trainee_list[name, dept, sign] |
| 출력 형식 | A4 세로, 성명·소속·서명란 최대 30행 |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster) |
| 우선순위 | **P1** |
| 연결 문서 | ED-001, ED-003, CM-005, CM-006 |

| 항목 | 내용 |
|------|------|
| 핵심서류 | ED-001 안전보건교육 교육일지 |
| form_type | `education_log` |
| **부대서류** | **② 교육 사진대지** |
| 생성 조건 | 교육일지 작성 시 선택 생성 |
| 필요 입력 | site_name, edu_date, photo_items[desc, date] |
| 출력 형식 | A4 가로, 2×3 사진 슬롯 |
| 구현 방식 | **공통 사진대지 builder** (photo_attachment_sheet) |
| 우선순위 | **P2** |
| 연결 문서 | ED-001, ED-003, SP-004 |

| 항목 | 내용 |
|------|------|
| 핵심서류 | ED-001 안전보건교육 교육일지 |
| form_type | `education_log` |
| **부대서류** | **③ 미참석자 추가교육 확인서** |
| 생성 조건 | 미참석자 ≥ 1명이고 추후 보완교육 실시 시 |
| 필요 입력 | site_name, original_edu_date, absent_list[name, reason], makeup_date, makeup_edu_subject |
| 출력 형식 | A4 세로 단순 확인서 |
| 구현 방식 | **독립 부대서류 builder** (education_makeup_confirmation) |
| 우선순위 | **P2** |
| 연결 문서 | ED-001, ED-003 |

---

### 1.2 ED-003 특별 안전보건교육 교육일지

| 항목 | 내용 |
|------|------|
| 핵심서류 | ED-003 특별 안전보건교육 교육일지 |
| form_type | `special_education_log` |
| **부대서류** | **④ 특별교육 참석자 명부** |
| 생성 조건 | 특별교육일지 작성 시 자동 연동 |
| 필요 입력 | site_name, edu_date, work_type, trainee_list[name, dept, job, sign] |
| 출력 형식 | A4 세로, 성명·직종·서명란 30행 |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster) |
| 우선순위 | **P1** |
| 연결 문서 | ED-001, ED-003, CM-006 |

---

### 1.3 CM-005 신규 근로자 안전보건 서약서

| 항목 | 내용 |
|------|------|
| 핵심서류 | CM-005 신규 근로자 안전보건 서약서 |
| form_type | `new_worker_safety_pledge` |
| **부대서류** | **⑤ 신규 근로자 투입 명부** |
| 생성 조건 | 서약서 작성 시 자동 연동 |
| 필요 입력 | site_name, entry_date, workers[name, affiliation, job, id_no, sign] |
| 출력 형식 | A4 세로, 30행 명부 |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster) |
| 우선순위 | **P2** |
| 연결 문서 | CM-005, CM-006, ED-001 |

---

## 2. 작업허가·PTW 부대서류

### 2.1 PTW-001 밀폐공간 작업 허가서

| 항목 | 내용 |
|------|------|
| 핵심서류 | PTW-001 밀폐공간 작업 허가서 |
| form_type | `confined_space_permit` |
| **부대서류** | **⑥ 작업 출입자 명부** |
| 생성 조건 | 허가서 발급 시 자동 연동 |
| 필요 입력 | site_name, permit_date, work_location, workers[name, entry_time, exit_time, sign] |
| 출력 형식 | A4 세로, 입출입 시각 포함 20행 |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster, mode=entry_exit) |
| 우선순위 | **P1** |
| 연결 문서 | PTW-001, CL-010, WP-014 |

| 항목 | 내용 |
|------|------|
| 핵심서류 | PTW-001 밀폐공간 작업 허가서 |
| form_type | `confined_space_permit` |
| **부대서류** | **⑦ 산소·가스농도 측정기록표** |
| 생성 조건 | 허가서 발급 시 자동 연동; 밀폐공간 진입 전 필수 |
| 필요 입력 | site_name, work_date, location, measure_items[time, O2, CO, H2S, LEL, measurer] |
| 출력 형식 | A4 세로, 시간대별 측정값 기록 |
| 구현 방식 | **독립 부대서류 builder** (confined_space_gas_measurement) |
| 우선순위 | **P1** |
| 연결 문서 | PTW-001, CL-010, WP-014 |

| 항목 | 내용 |
|------|------|
| 핵심서류 | PTW-001 밀폐공간 작업 허가서 |
| form_type | `confined_space_permit` |
| **부대서류** | **⑧ 감시인 배치 확인서** |
| 생성 조건 | 허가서 발급 시 선택 생성; 감시인 지정 시 |
| 필요 입력 | site_name, permit_date, location, watchman_name, watchman_position, duty_desc |
| 출력 형식 | A4 세로 단순 확인서 |
| 구현 방식 | **독립 부대서류 builder** (watchman_assignment_confirmation) |
| 우선순위 | **P2** |
| 연결 문서 | PTW-001, PTW-002, PTW-003, PTW-006 |

---

### 2.2 PTW-002 화기작업 허가서

| 항목 | 내용 |
|------|------|
| 핵심서류 | PTW-002 화기작업 허가서 |
| form_type | `hot_work_permit` |
| **부대서류** | **⑨ 화기작업 출입자 명부** |
| 생성 조건 | 허가서 발급 시 자동 연동 |
| 필요 입력 | site_name, permit_date, work_location, workers[name, affiliation, entry_time, exit_time, sign] |
| 출력 형식 | A4 세로, 입출입 시각 포함 20행 |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster, mode=entry_exit) |
| 우선순위 | **P2** |
| 연결 문서 | PTW-002, EQ-014, CL-005 |

| 항목 | 내용 |
|------|------|
| 핵심서류 | PTW-002 화기작업 허가서 |
| form_type | `hot_work_permit` |
| **부대서류** | **⑩ 작업 종료 확인서** |
| 생성 조건 | 허가서 발급 시 자동 연동; 작업 종료 후 서명 |
| 필요 입력 | site_name, permit_date, work_location, completion_time, fire_watch_duration, completed_by, supervisor |
| 출력 형식 | A4 세로, 종료확인·소방순찰 포함 |
| 구현 방식 | **독립 부대서류 builder** (work_completion_confirmation) |
| 우선순위 | **P1** |
| 연결 문서 | PTW-001, PTW-002, PTW-003, PTW-004, PTW-005, PTW-006, PTW-007, PTW-008 |

---

### 2.3 PTW-006 방사선 투과검사 작업 허가서

| 항목 | 내용 |
|------|------|
| 핵심서류 | PTW-006 방사선 투과검사 작업 허가서 |
| form_type | `radiography_work_permit` |
| **부대서류** | **⑪ 방사선 관리구역 출입 통제 명부** |
| 생성 조건 | 허가서 발급 시 자동 연동 |
| 필요 입력 | site_name, permit_date, control_zone_location, workers[name, cert_no, entry_time, exit_time, dosimeter_no] |
| 출력 형식 | A4 세로, 개인선량계 번호 포함 |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster, mode=radiation_zone) |
| 우선순위 | **P2** |
| 연결 문서 | PTW-006 |

---

## 3. 장비·보호구·자재 부대서류

### 3.1 PPE-002 건설 장비 반입 신청서

| 항목 | 내용 |
|------|------|
| 핵심서류 | PPE-002 건설 장비 반입 신청서 |
| form_type | `equipment_entry_application` |
| **부대서류** | **⑫ 운전원 자격 확인표** |
| 생성 조건 | 반입 신청서 작성 시 선택 생성; 유자격 장비 |
| 필요 입력 | site_name, entry_date, equipment_type, operators[name, cert_type, cert_no, cert_expiry, sign] |
| 출력 형식 | A4 세로, 자격증 사본 첨부란 포함 |
| 구현 방식 | **독립 부대서류 builder** (equipment_operator_qualification_check) |
| 우선순위 | **P1** |
| 연결 문서 | PPE-002, PPE-003, WP-006, WP-007, EQ-003, EQ-004 |

| 항목 | 내용 |
|------|------|
| 핵심서류 | PPE-003 건설 장비 보험·정기검사증 확인서 |
| form_type | `equipment_insurance_inspection_check` |
| **부대서류** | **⑬ 보험증·검사증 첨부 확인표** |
| 생성 조건 | 검사증 확인서 작성 시 자동 연동 |
| 필요 입력 | site_name, check_date, equipment_type, documents[doc_type, doc_no, issue_date, expiry, attached] |
| 출력 형식 | A4 세로, 서류별 첨부 체크리스트 |
| 구현 방식 | **공통 첨부목록 builder** (document_attachment_list) |
| 우선순위 | **P2** |
| 연결 문서 | PPE-002, PPE-003, WP-006~WP-010 |

---

### 3.2 PPE-001 보호구 지급 대장

| 항목 | 내용 |
|------|------|
| 핵심서류 | PPE-001 보호구 지급 대장 |
| form_type | `ppe_issue_register` |
| **부대서류** | **⑭ 보호구 수령 확인서** |
| 생성 조건 | 지급 대장 작성 시 자동 연동; 수령자 서명 |
| 필요 입력 | site_name, issue_date, ppe_items[name, spec, qty, recipient_name, sign, date] |
| 출력 형식 | A4 세로, 수령자 서명 포함 |
| 구현 방식 | **독립 부대서류 builder** (ppe_receipt_confirmation) |
| 우선순위 | **P2** |
| 연결 문서 | PPE-001, CL-008 |

---

### 3.3 PPE-004 MSDS 비치 및 교육 확인서

| 항목 | 내용 |
|------|------|
| 핵심서류 | PPE-004 MSDS 비치 및 교육 확인서 |
| form_type | `msds_posting_education_check` |
| **부대서류** | **⑮ MSDS 교육 참석자 명부** |
| 생성 조건 | 교육 확인서 작성 시 자동 연동 |
| 필요 입력 | site_name, edu_date, chemical_name, trainees[name, dept, sign] |
| 출력 형식 | A4 세로, 물질명 포함 30행 |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster) |
| 우선순위 | **P2** |
| 연결 문서 | PPE-004, HM-001, HM-002 |

---

## 4. 위험성평가·TBM 부대서류

### 4.1 RA-001 위험성평가표

| 항목 | 내용 |
|------|------|
| 핵심서류 | RA-001 위험성평가표 |
| form_type | `risk_assessment` |
| **부대서류** | **⑯ 위험성평가 참여 확인 명부** |
| 생성 조건 | 위험성평가 실시 시 자동 연동; 근로자 참여 |
| 필요 입력 | site_name, assessment_date, work_name, participants[name, dept, role, sign] |
| 출력 형식 | A4 세로, 역할 포함 20행 |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster, mode=ra_participation) |
| 우선순위 | **P1** |
| 연결 문서 | RA-001, RA-003, RA-006 |

| 항목 | 내용 |
|------|------|
| 핵심서류 | RA-001 위험성평가표 |
| form_type | `risk_assessment` |
| **부대서류** | **⑰ 개선조치 완료 확인서** |
| 생성 조건 | 위험성평가 결과 개선필요 항목 ≥ 1개 |
| 필요 입력 | site_name, assessment_date, improvement_items[hazard, measure, person, due_date, completed_date, confirmer] |
| 출력 형식 | A4 세로, 완료확인란 포함 |
| 구현 방식 | **독립 부대서류 builder** (improvement_completion_check) |
| 우선순위 | **P1** |
| 연결 문서 | RA-001, RA-002, RA-005, SP-003 |

---

### 4.2 RA-003 위험성평가 참여 회의록

| 항목 | 내용 |
|------|------|
| 핵심서류 | RA-003 위험성평가 참여 회의록 |
| form_type | `risk_assessment_meeting_minutes` |
| **부대서류** | **⑱ 회의 참석자 서명 명부** |
| 생성 조건 | 회의록 작성 시 자동 연동 |
| 필요 입력 | site_name, meeting_date, agenda, attendees[name, dept, sign] |
| 출력 형식 | A4 세로, 성명·소속·서명 20행 |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster) |
| 우선순위 | **P2** |
| 연결 문서 | RA-003, ED-005, RA-001 |

---

### 4.3 RA-004 TBM 안전점검 일지

| 항목 | 내용 |
|------|------|
| 핵심서류 | RA-004 TBM 안전점검 일지 |
| form_type | `tbm_log` |
| **부대서류** | **⑲ TBM 참석자 서명부** |
| 생성 조건 | TBM 일지 작성 시 자동 연동; 매일 |
| 필요 입력 | site_name, tbm_date, work_area, attendees[name, sign] |
| 출력 형식 | A4 세로, 40행 (현장 특성상 서명 많음) |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster, mode=tbm) |
| 우선순위 | **P1** |
| 연결 문서 | RA-004, DL-001, DL-002 |

---

## 5. 사고·비상대응 부대서류

### 5.1 EM-001 산업재해조사표

| 항목 | 내용 |
|------|------|
| 핵심서류 | EM-001 산업재해조사표 |
| form_type | `industrial_accident_report` |
| **부대서류** | **⑳ 재해 현장 사진대지** |
| 생성 조건 | 재해조사표 작성 시 자동 연동 |
| 필요 입력 | site_name, accident_date, location, photo_items[photo_no, desc, taken_by, date] |
| 출력 형식 | A4 가로, 2×3 사진 슬롯 |
| 구현 방식 | **공통 사진대지 builder** (photo_attachment_sheet, mode=accident) |
| 우선순위 | **P1** |
| 연결 문서 | EM-001, EM-004, EM-005 |

| 항목 | 내용 |
|------|------|
| 핵심서류 | EM-005 재해 원인 분석 및 재발방지 보고서 |
| form_type | `accident_root_cause_prevention_report` |
| **부대서류** | **㉑ 재발방지 조치 사진대지** |
| 생성 조건 | 재발방지 보고서 작성 시 자동 연동 |
| 필요 입력 | site_name, report_date, measure_items[measure_name, before_photo, after_photo, date] |
| 출력 형식 | A4 가로, 개선 전/후 비교 슬롯 |
| 구현 방식 | **공통 사진대지 builder** (photo_attachment_sheet, mode=before_after) |
| 우선순위 | **P1** |
| 연결 문서 | EM-005, SP-003, RA-001 |

| 항목 | 내용 |
|------|------|
| 핵심서류 | EM-002 아차사고 보고서 |
| form_type | `near_miss_report` |
| **부대서류** | **㉒ 아차사고 사진대지** |
| 생성 조건 | 아차사고 보고서 작성 시 선택 생성 |
| 필요 입력 | site_name, report_date, photo_items[photo_no, desc, taken_date] |
| 출력 형식 | A4 가로, 2×3 사진 슬롯 |
| 구현 방식 | **공통 사진대지 builder** (photo_attachment_sheet) |
| 우선순위 | **P2** |
| 연결 문서 | EM-002, EM-001, RA-001 |

---

### 5.2 EM-003 비상 연락망 및 대피 계획서

| 항목 | 내용 |
|------|------|
| 핵심서류 | EM-003 비상 연락망 및 대피 계획서 |
| form_type | `emergency_contact_evacuation_plan` |
| **부대서류** | **㉓ 비상대피 훈련 참석자 명부** |
| 생성 조건 | 비상대피 훈련 실시 시 선택 생성 |
| 필요 입력 | site_name, drill_date, scenario, attendees[name, dept, sign, evacuation_route] |
| 출력 형식 | A4 세로, 대피경로 포함 30행 |
| 구현 방식 | **공통 참석자 명부 builder** (attendance_roster, mode=evacuation_drill) |
| 우선순위 | **P2** |
| 연결 문서 | EM-003, EM-004, ED-001 |

---

## 6. 공통 사진대지·첨부목록 부대서류

### 6.1 전 카테고리 공통

| 항목 | 내용 |
|------|------|
| **부대서류** | **㉔ 공통 사진대지 (범용)** |
| 생성 조건 | 어떤 핵심서류와도 연동 가능; 사진 첨부 필요 시 |
| 필요 입력 | parent_doc_id, parent_doc_name, site_name, date, photo_items[slot_no, desc, taken_date, photographer, notes] |
| 출력 형식 | A4 가로, 2×3 슬롯 (슬롯당 사진 설명·일자) |
| 구현 방식 | **공통 사진대지 builder** (photo_attachment_sheet) |
| 우선순위 | **P1** |
| 연결 문서 | ED·PTW·EM·SP 전반, WP·EQ 주요 서류 |

| 항목 | 내용 |
|------|------|
| **부대서류** | **㉕ 공통 첨부서류 목록표** |
| 생성 조건 | 제출 패키지 구성 시; 부대서류 2개 이상 |
| 필요 입력 | parent_doc_id, parent_doc_name, site_name, date, attachment_items[no, doc_name, pages, attached, remarks] |
| 출력 형식 | A4 세로, 첨부 체크리스트 20행 |
| 구현 방식 | **공통 첨부목록 builder** (document_attachment_list) |
| 우선순위 | **P1** |
| 연결 문서 | 전 카테고리 |

---

## 7. 구현 계획

### 7.1 공통 builder 3종 (우선 구현)

| builder | form_type | 설명 | 우선순위 |
|---------|-----------|------|--------|
| 참석자·출입자 명부 | `attendance_roster` | mode 파라미터로 TBM/교육/PTW/입출입 등 전환 | **P1** |
| 사진대지 | `photo_attachment_sheet` | 2×3 슬롯, 개선 전/후 비교 모드 지원 | **P1** |
| 첨부서류 목록표 | `document_attachment_list` | 핵심서류 ID 연동, 첨부 체크리스트 | **P1** |

### 7.2 독립 부대서류 builder (선택 구현)

| builder | form_type | 연결 핵심서류 | 우선순위 |
|---------|-----------|------------|--------|
| 산소·가스농도 측정기록표 | `confined_space_gas_measurement` | PTW-001, CL-010 | **P1** |
| 작업 종료 확인서 | `work_completion_confirmation` | PTW-001~008 전반 | **P1** |
| 개선조치 완료 확인서 | `improvement_completion_check` | RA-001, RA-002 | **P1** |
| 운전원 자격 확인표 | `equipment_operator_qualification_check` | PPE-002, WP-006~010 | **P1** |
| 감시인 배치 확인서 | `watchman_assignment_confirmation` | PTW-001, PTW-002, PTW-006 | **P2** |
| 미참석자 추가교육 확인서 | `education_makeup_confirmation` | ED-001, ED-003 | **P2** |
| 보호구 수령 확인서 | `ppe_receipt_confirmation` | PPE-001, CL-008 | **P2** |

### 7.3 1차 구현 추천 10종

| 순위 | form_type | 이유 |
|------|-----------|------|
| 1 | `attendance_roster` | 교육·TBM·PTW·RA 전반 재사용, 공통 builder |
| 2 | `photo_attachment_sheet` | 사진첨부 전 카테고리 필요, 공통 builder |
| 3 | `document_attachment_list` | 제출 패키지 필수 구성요소, 공통 builder |
| 4 | `confined_space_gas_measurement` | PTW-001 법정 측정 의무 |
| 5 | `work_completion_confirmation` | PTW 전체 8종 작업 종료 시 필수 |
| 6 | `improvement_completion_check` | RA-001 개선조치 이행증빙 핵심 |
| 7 | `equipment_operator_qualification_check` | PPE-002 유자격 운전원 확인 법정 요건 |
| 8 | `watchman_assignment_confirmation` | PTW-001 밀폐공간 감시인 배치 법정 의무 |
| 9 | `education_makeup_confirmation` | 교육 미참석자 보완 이행 증빙 |
| 10 | `ppe_receipt_confirmation` | PPE 지급 후 수령 서명 필수 |

---

## 8. 기술 구현 가이드

### 8.1 공통 builder mode 파라미터 설계

```python
# attendance_roster — mode별 출력 차이
MODES = {
    "default":         {"cols": ["성명", "소속", "서명"], "rows": 30},
    "entry_exit":      {"cols": ["성명", "소속", "입실시각", "퇴실시각", "서명"], "rows": 20},
    "tbm":             {"cols": ["성명", "서명", "성명", "서명"], "rows": 40, "split_col": True},
    "ra_participation":{"cols": ["성명", "소속", "역할", "서명"], "rows": 20},
    "radiation_zone":  {"cols": ["성명", "자격증번호", "선량계번호", "입실", "퇴실"], "rows": 15},
    "evacuation_drill":{"cols": ["성명", "소속", "대피경로", "확인시각", "서명"], "rows": 30},
}

# photo_attachment_sheet — mode별 슬롯 구성
PHOTO_MODES = {
    "default":     {"layout": "2x3", "slots": 6},
    "accident":    {"layout": "2x3", "slots": 6, "header": "재해 현장 사진"},
    "before_after":{"layout": "2x2", "slots": 4, "labels": ["개선 전", "개선 후"]},
}
```

### 8.2 핵심서류 → 부대서류 자동 연동 흐름 (향후 웹 구현 기준)

```
[사용자: 핵심서류 form_type 선택]
       ↓
[SUPPLEMENTARY_MAP 조회]
       ↓
[자동 생성 대상 부대서류 목록 표시]
       ↓
[사용자: 부대서류 선택/해제]
       ↓
[공통 builder or 독립 builder 호출]
       ↓
[ZIP 패키지: 핵심서류 + 선택 부대서류 + 첨부목록]
```

### 8.3 연동 매핑 상수 설계 (Python)

```python
SUPPLEMENTARY_MAP: dict[str, list[str]] = {
    "education_log":               ["attendance_roster", "photo_attachment_sheet", "education_makeup_confirmation"],
    "special_education_log":       ["attendance_roster", "photo_attachment_sheet"],
    "confined_space_permit":       ["attendance_roster:entry_exit", "confined_space_gas_measurement", "watchman_assignment_confirmation", "work_completion_confirmation"],
    "hot_work_permit":             ["attendance_roster:entry_exit", "work_completion_confirmation"],
    "work_at_height_permit":       ["attendance_roster:entry_exit", "work_completion_confirmation"],
    "electrical_work_permit":      ["attendance_roster:entry_exit", "work_completion_confirmation"],
    "excavation_work_permit":      ["attendance_roster:entry_exit", "work_completion_confirmation"],
    "radiography_work_permit":     ["attendance_roster:radiation_zone", "work_completion_confirmation"],
    "lifting_work_permit":         ["attendance_roster:entry_exit", "equipment_operator_qualification_check", "work_completion_confirmation"],
    "temp_electrical_installation_permit": ["attendance_roster:entry_exit", "work_completion_confirmation"],
    "risk_assessment":             ["attendance_roster:ra_participation", "improvement_completion_check"],
    "risk_assessment_meeting_minutes": ["attendance_roster"],
    "tbm_log":                     ["attendance_roster:tbm"],
    "equipment_entry_application": ["equipment_operator_qualification_check", "document_attachment_list"],
    "equipment_insurance_inspection_check": ["document_attachment_list"],
    "ppe_issue_register":          ["ppe_receipt_confirmation"],
    "industrial_accident_report":  ["photo_attachment_sheet:accident", "document_attachment_list"],
    "near_miss_report":            ["photo_attachment_sheet"],
    "accident_root_cause_prevention_report": ["photo_attachment_sheet:before_after", "improvement_completion_check"],
    "emergency_contact_evacuation_plan": ["attendance_roster:evacuation_drill"],
    "msds_posting_education_check": ["attendance_roster"],
    "new_worker_safety_pledge":    ["attendance_roster"],
}
```

---

## 9. 검증 기준

| 항목 | 기준 |
|------|------|
| catalog 기준 | DONE 90종 기반 분석 (OUT 3종 제외) |
| 신규 document_id 추가 | 없음 (부대서류는 파생 출력물, catalog 미포함) |
| registry 수정 | 없음 (설계 문서만 생성) |
| 코드 수정 | 없음 |
| 우선순위 P1 부대서류 | 10종 (공통 3 + 독립 7) |
| 총 설계 부대서류 | 25종 (번호 ① ~ ㉕) |

---

**문서 버전**: v1.0  
**다음 단계**: 공통 builder 3종(attendance_roster, photo_attachment_sheet, document_attachment_list) 구현 → 독립 builder 7종 구현 → 핵심서류 ZIP 패키지 API 연동

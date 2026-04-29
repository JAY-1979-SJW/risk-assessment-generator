# Excel A4 레이아웃 품질 감사 보고서

**생성일**: 2026-04-29  
**검사 대상**: 핵심서류 87종 + 부대서류 10종 = **총 97종**  
**분석 완료**: 97종  

---

## 1. 전체 요약

| 구분 | 검사 수 | PASS | WARN | FAIL 후보 | ERROR |
|------|---------|------|------|-----------|-------|
| 핵심서류 | 87 | 60 | 27 | 0 | 0 |
| 부대서류 | 10 | 8 | 2 | 0 | 0 |
| **합계** | **97** | **68** | **29** | **0** | **0** |

## 2. A4 페이지 설정 요약

| 항목 | 수량 | 비율 |
|------|------|------|
| fitToWidth=1 적용 | 97 | 100% |
| fitToWidth 미설정 | 0 | 0% |
| fitToHeight=1 (강제 축소) | 0 | 0% |
| scale 80 미만 | 0 | 0% |
| 가로 (landscape) | 10 | 10% |
| print_area 미설정 | 78 | 80% |

## 3. 페이지 폭 활용도

**여백 과다** (활용도 < 70%): **0종**  
**폭 초과** (활용도 > 125%): **85종**  

### 3-2. 폭 초과 상위 (최대 20종)

| form_type | 표시명 | 활용도 | 열너비합(in) | 출력폭(in) |
|-----------|--------|--------|-------------|-----------|
| risk_assessment | 위험성평가표 | 259% | 28.77 | 11.09 |
| confined_space_checklist | 밀폐공간 사전 안전점검표 | 187% | 13.62 | 7.27 |
| radiography_work_permit | 방사선 투과검사 작업 허가서 | 178% | 12.96 | 7.27 |
| hazardous_chemical_checklist | 유해화학물질 취급 점검표 | 172% | 12.52 | 7.27 |
| msds_posting_education_check | MSDS 비치 및 교육 확인서 | 172% | 12.52 | 7.27 |
| protective_equipment_checklist | 보호구 지급 및 관리 점검표 | 172% | 12.52 | 7.27 |
| supervisor_safety_log | 관리감독자 안전보건 업무 일지 | 169% | 12.30 | 7.27 |
| risk_assessment_meeting_minutes | 위험성평가 참여 회의록 | 168% | 12.19 | 7.27 |
| risk_assessment_procedure | 위험성평가 실시 규정 | 166% | 12.08 | 7.27 |
| photo_attachment_sheet | 사진대지 | 166% | 12.08 | 7.27 |
| subcontractor_safety_evaluation | 협력업체 안전보건 수준 평가표 | 162% | 11.75 | 7.27 |
| manager_job_training_record | 안전보건관리자 직무교육 이수 확인서 | 160% | 11.64 | 7.27 |
| equipment_entry_application | 건설 장비 반입 신청서 (v2) | 159% | 11.53 | 7.27 |
| equipment_insurance_inspection_check | 건설 장비 보험·정기검사증 확인서 | 159% | 11.53 | 7.27 |
| ppe_issue_register | 보호구 지급 대장 (v2) | 159% | 11.53 | 7.27 |
| ppe_management_checklist | 보호구 지급 및 관리 점검표 (v2) | 159% | 11.53 | 7.27 |
| pre_work_safety_check | 작업 전 안전 확인서 | 159% | 11.53 | 7.27 |
| safety_patrol_inspection_log | 안전순찰 점검 일지 | 159% | 11.53 | 7.27 |
| weather_condition_log | 기상 조건 기록 일지 | 159% | 11.53 | 7.27 |
| work_completion_confirmation | 작업 종료 확인서 | 159% | 11.53 | 7.27 |

## 4. 페이지 분할 / 반복 헤더

**행 수 > 45인 문서**: 54종  
**반복 헤더 미설정**: 12종  
**반복 헤더 설정**: 52종  

### 반복 헤더 필요 후보

| form_type | 표시명 | used_rows | 표형 |
|-----------|--------|-----------|------|
| compressor_pneumatic_equipment_plan | 콤프레샤·공압장비 사용계획서 | 58 | - |
| emergency_first_aid_record | 응급조치 실시 기록서 | 58 | - |
| heavy_lifting_workplan | 중량물 취급 작업계획서 | 57 | - |
| pre_work_safety_check | 작업 전 안전 확인서 | 56 | Y |
| accident_root_cause_prevention_report | 재해 원인 분석 및 재발 방지 보고서 | 55 | - |
| safety_policy_goal_notice | 안전보건 방침 및 목표 게시문 | 55 | - |
| weather_condition_log | 기상 조건 기록 일지 | 53 | Y |
| risk_assessment_best_practice_report | 위험성평가 우수 사례 보고서 | 52 | - |
| material_handling_workplan | 차량계 하역운반기계 작업계획서 | 51 | - |
| vehicle_construction_workplan | 차량계 건설기계 작업계획서 | 49 | - |
| protective_equipment_checklist | 보호구 지급 및 관리 점검표 | 48 | Y |
| risk_assessment_meeting_minutes | 위험성평가 참여 회의록 | 47 | - |

## 5. 셀 겹침 / 잘림 위험 요약

| 위험 유형 | 건수 |
|----------|------|
| 긴 문구 wrap_text 누락 | 6 |
| 서명란 높이 부족 가능 | 12 |
| 서명란 페이지 끝 잘림 가능 | 5 |

## 6. 문서별 위험도 Top 30

| # | form_type | 표시명 | 판정 | FAIL수 | WARN수 | 주요 문제 | 권장 조치 |
|---|-----------|--------|------|--------|--------|----------|----------|
| 1 | msds_posting_education_check | MSDS 비치 및 교육 확인서 | **WARN** | 0 | 4 | 열 너비 합계 12.52in > 출력폭 7.27in (172%) — fitToWidth=1 | 인쇄설정 추가 |
| 2 | risk_assessment_procedure | 위험성평가 실시 규정 | **WARN** | 0 | 4 | 열 너비 합계 12.08in > 출력폭 7.27in (166%) — fitToWidth=1 | 인쇄설정 추가 |
| 3 | construction_equipment_daily_checklist | 건설장비 일일 사전점검표 | **WARN** | 0 | 3 | 긴 문구 wrap_text 누락 5건; R79 서명란 높이 15pt < 18pt; R82  | 서명란 높이 조정 |
| 4 | hazardous_chemical_checklist | 유해화학물질 취급 점검표 | **WARN** | 0 | 3 | 열 너비 합계 12.52in > 출력폭 7.27in (172%) — fitToWidth=1 | 인쇄설정 추가 |
| 5 | protective_equipment_checklist | 보호구 지급 및 관리 점검표 | **WARN** | 0 | 3 | 열 너비 합계 12.52in > 출력폭 7.27in (172%) — fitToWidth=1 | 인쇄설정 추가 |
| 6 | accident_root_cause_prevention_report | 재해 원인 분석 및 재발 방지 보 | **WARN** | 0 | 2 | used_rows=55 > 45 — 반복 헤더 권장; 서명란(R55)이 최종행 — 페이지  | print_title_rows 추가 |
| 7 | emergency_first_aid_record | 응급조치 실시 기록서 | **WARN** | 0 | 2 | used_rows=58 > 45 — 반복 헤더 권장; 서명란(R58)이 최종행 — 페이지  | print_title_rows 추가 |
| 8 | heavy_lifting_workplan | 중량물 취급 작업계획서 | **WARN** | 0 | 2 | used_rows=57 > 45 — 반복 헤더 권장; 긴 문구 wrap_text 누락 1건 | print_title_rows 추가 |
| 9 | manager_job_training_record | 안전보건관리자 직무교육 이수 확인 | **WARN** | 0 | 2 | 열 너비 합계 11.64in > 출력폭 7.27in (160%) — fitToWidth=1 | 인쇄설정 추가 |
| 10 | ppe_issue_register | 보호구 지급 대장 (v2) | **WARN** | 0 | 2 | 긴 문구 wrap_text 누락 1건; R31 서명란 높이 16pt < 18pt | 서명란 높이 조정 |
| 11 | risk_assessment_meeting_minutes | 위험성평가 참여 회의록 | **WARN** | 0 | 2 | 열 너비 합계 12.19in > 출력폭 7.27in (168%) — fitToWidth=1 | 인쇄설정 추가 |
| 12 | weather_condition_log | 기상 조건 기록 일지 | **WARN** | 0 | 2 | used_rows=53 > 45 — 반복 헤더 권장; 서명란(R53)이 최종행 — 페이지  | print_title_rows 추가 |
| 13 | work_safety_checklist | 작업 전 안전 확인서 | **WARN** | 0 | 2 | 긴 문구 wrap_text 누락 1건; 서명란(R51)이 최종행 — 페이지 분리 시 잘림  | 서명란 높이 조정 |
| 14 | compressor_pneumatic_equipment_plan | 콤프레샤·공압장비 사용계획서 | **WARN** | 0 | 1 | used_rows=58 > 45 — 반복 헤더 권장 | print_title_rows 추가 |
| 15 | confined_space_checklist | 밀폐공간 사전 안전점검표 | **WARN** | 0 | 1 | 열 너비 합계 13.62in > 출력폭 7.27in (187%) — fitToWidth=1 | 인쇄설정 추가 |
| 16 | industrial_accident_status_ledger | 산업재해 발생 현황 관리 대장 | **WARN** | 0 | 1 | R39 서명란 높이 15pt < 18pt | 서명란 높이 조정 |
| 17 | material_handling_workplan | 차량계 하역운반기계 작업계획서 | **WARN** | 0 | 1 | used_rows=51 > 45 — 반복 헤더 권장 | print_title_rows 추가 |
| 18 | near_miss_report | 아차사고 보고서 | **WARN** | 0 | 1 | 서명란(R64)이 최종행 — 페이지 분리 시 잘림 가능 | 서명란 높이 조정 |
| 19 | ppe_management_checklist | 보호구 지급 및 관리 점검표 (v | **WARN** | 0 | 1 | 긴 문구 wrap_text 누락 2건 | 개별 확인 |
| 20 | pre_work_safety_check | 작업 전 안전 확인서 | **WARN** | 0 | 1 | used_rows=56 > 45 — 반복 헤더 권장 | print_title_rows 추가 |
| 21 | radiography_work_permit | 방사선 투과검사 작업 허가서 | **WARN** | 0 | 1 | 열 너비 합계 12.96in > 출력폭 7.27in (178%) — fitToWidth=1 | 인쇄설정 추가 |
| 22 | risk_assessment | 위험성평가표 | **WARN** | 0 | 1 | 열 너비 합계 28.77in > 출력폭 11.09in (259%) — fitToWidth= | 인쇄설정 추가 |
| 23 | risk_assessment_best_practice_report | 위험성평가 우수 사례 보고서 | **WARN** | 0 | 1 | used_rows=52 > 45 — 반복 헤더 권장 | print_title_rows 추가 |
| 24 | safety_policy_goal_notice | 안전보건 방침 및 목표 게시문 | **WARN** | 0 | 1 | used_rows=55 > 45 — 반복 헤더 권장 | print_title_rows 추가 |
| 25 | subcontractor_safety_evaluation | 협력업체 안전보건 수준 평가표 | **WARN** | 0 | 1 | 열 너비 합계 11.75in > 출력폭 7.27in (162%) — fitToWidth=1 | 인쇄설정 추가 |
| 26 | supervisor_safety_log | 관리감독자 안전보건 업무 일지 | **WARN** | 0 | 1 | 열 너비 합계 12.30in > 출력폭 7.27in (169%) — fitToWidth=1 | 인쇄설정 추가 |
| 27 | vehicle_construction_workplan | 차량계 건설기계 작업계획서 | **WARN** | 0 | 1 | used_rows=49 > 45 — 반복 헤더 권장 | print_title_rows 추가 |
| 28 | photo_attachment_sheet | 사진대지 | **WARN** | 0 | 1 | 열 너비 합계 12.08in > 출력폭 7.27in (166%) — fitToWidth=1 | 인쇄설정 추가 |
| 29 | work_completion_confirmation | 작업 종료 확인서 | **WARN** | 0 | 1 | 긴 문구 wrap_text 누락 1건 | 개별 확인 |

## 7. 공통 원인 분석

| 원인 분류 | 해당 문서 수 | 설명 |
|----------|------------|------|
| excel_style_helpers 공통 보정 | 12 | fitToWidth, print_area, 여백 미설정 |
| 개별 builder 보정 필요 | 14 | 열너비 초과/부족, 반복 헤더 누락 |
| 부대서류 보정 필요 | 2 | 부대서류 builder 레이아웃 개선 |

### 7-1. excel_style_helpers에서 공통 보정 가능한 항목

- `apply_col_widths()` 호출 시 `fitToWidth=1`, `print_area` 자동 설정 추가
- 공통 `set_print_setup(ws, landscape=False)` 헬퍼 함수 추가 권장
- 여백: `ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.75, bottom=0.75)`

### 7-2. 개별 builder 보정이 필요한 항목

- 열 너비 합계가 출력폭 초과하는 경우 → 각 builder의 `_COL_WIDTHS` 조정
- 45행 이상 표형 문서 → `ws.print_title_rows = '1:3'` 추가
- 서명란 row_height 부족 → 서명 행에 `ws.row_dimensions[row].height = 30` 적용

### 7-3. 부대서류 전용 보정 필요

- 부대서류 10종은 excel_style_helpers 기반으로 작성되었으나 인쇄 설정 미추가
- `build_*` 함수 말미에 공통 `set_print_setup(ws)` 호출 추가로 일괄 해결 가능

## 8. 다음 단계

| 단계 | 작업 | 예상 효과 |
|------|------|----------|
| 2단계 | excel_style_helpers에 `set_print_setup()` 공통 함수 추가 | fitToWidth/print_area 일괄 적용 |
| 3단계 | 핵심서류 Top 위험 문서 개별 열너비·반복헤더 보정 | FAIL 후보 0건 목표 |
| 4단계 | 부대서류 10종 인쇄 설정 일괄 추가 | 부대서류 WARN 해소 |
| 5단계 | 전체 97종 재감사 — Excel Layout QA v1.0 마감 보고서 작성 | PASS 90% 이상 목표 |

---

```
전체: 97종  |  PASS: 68  |  WARN: 29  |  FAIL 후보: 0  |  ERROR: 0
핵심: 87종  PASS: 60  WARN: 27  FAIL: 0
부대: 10종  PASS: 8  WARN: 2  FAIL: 0
최종 판정: PASS
```

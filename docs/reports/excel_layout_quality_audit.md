# Excel A4 레이아웃 품질 감사 보고서

**생성일**: 2026-04-29  
**검사 대상**: 핵심서류 87종 + 부대서류 10종 = **총 97종**  
**분석 완료**: 97종  

---

## 1. 전체 요약

| 구분 | 검사 수 | PASS | WARN | FAIL 후보 | ERROR |
|------|---------|------|------|-----------|-------|
| 핵심서류 | 87 | 86 | 1 | 0 | 0 |
| 부대서류 | 10 | 10 | 0 | 0 | 0 |
| **합계** | **97** | **96** | **1** | **0** | **0** |

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
| equipment_entry_application | 건설 장비 반입 신청서 (v2) | 159% | 11.53 | 7.27 |
| equipment_insurance_inspection_check | 건설 장비 보험·정기검사증 확인서 | 159% | 11.53 | 7.27 |
| hazardous_chemical_checklist | 유해화학물질 취급 점검표 | 159% | 11.53 | 7.27 |
| manager_job_training_record | 안전보건관리자 직무교육 이수 확인서 | 159% | 11.53 | 7.27 |
| msds_posting_education_check | MSDS 비치 및 교육 확인서 | 159% | 11.53 | 7.27 |
| ppe_issue_register | 보호구 지급 대장 (v2) | 159% | 11.53 | 7.27 |
| ppe_management_checklist | 보호구 지급 및 관리 점검표 (v2) | 159% | 11.53 | 7.27 |
| pre_work_safety_check | 작업 전 안전 확인서 | 159% | 11.53 | 7.27 |
| protective_equipment_checklist | 보호구 지급 및 관리 점검표 | 159% | 11.53 | 7.27 |
| radiography_work_permit | 방사선 투과검사 작업 허가서 | 159% | 11.53 | 7.27 |
| risk_assessment_meeting_minutes | 위험성평가 참여 회의록 | 159% | 11.53 | 7.27 |
| risk_assessment_procedure | 위험성평가 실시 규정 | 159% | 11.53 | 7.27 |
| safety_patrol_inspection_log | 안전순찰 점검 일지 | 159% | 11.53 | 7.27 |
| weather_condition_log | 기상 조건 기록 일지 | 159% | 11.53 | 7.27 |
| work_completion_confirmation | 작업 종료 확인서 | 159% | 11.53 | 7.27 |
| confined_space_checklist | 밀폐공간 사전 안전점검표 | 157% | 11.42 | 7.27 |
| safety_cost_use_plan | 산업안전보건관리비 사용계획서 | 157% | 11.42 | 7.27 |
| supervisor_safety_log | 관리감독자 안전보건 업무 일지 | 157% | 11.42 | 7.27 |
| track_maintenance_workplan | 궤도 작업계획서 | 157% | 11.42 | 7.27 |

## 4. 페이지 분할 / 반복 헤더

**행 수 > 45인 문서**: 54종  
**반복 헤더 미설정**: 0종  
**반복 헤더 설정**: 66종  

## 5. 셀 겹침 / 잘림 위험 요약

| 위험 유형 | 건수 |
|----------|------|
| 긴 문구 wrap_text 누락 | 0 |
| 서명란 높이 부족 가능 | 0 |
| 서명란 페이지 끝 잘림 가능 | 0 |

## 6. 문서별 위험도 Top 30

| # | form_type | 표시명 | 판정 | FAIL수 | WARN수 | 주요 문제 | 권장 조치 |
|---|-----------|--------|------|--------|--------|----------|----------|
| 1 | risk_assessment | 위험성평가표 | **WARN** | 0 | 1 | 열 너비 합계 28.77in > 출력폭 11.09in (259%) — fitToWidth= | 인쇄설정 추가 |

## 7. 공통 원인 분석

| 원인 분류 | 해당 문서 수 | 설명 |
|----------|------------|------|
| excel_style_helpers 공통 보정 | 1 | fitToWidth, print_area, 여백 미설정 |
| 개별 builder 보정 필요 | 0 | 열너비 초과/부족, 반복 헤더 누락 |
| 부대서류 보정 필요 | 0 | 부대서류 builder 레이아웃 개선 |

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
전체: 97종  |  PASS: 96  |  WARN: 1  |  FAIL 후보: 0  |  ERROR: 0
핵심: 87종  PASS: 86  WARN: 1  FAIL: 0
부대: 10종  PASS: 10  WARN: 0  FAIL: 0
최종 판정: PASS
```

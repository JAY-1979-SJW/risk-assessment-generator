---
title: 굴착 작업계획서 누락 3필드 보완 재검증 결과
date: 2026-04-24
status: PASS
---

# 굴착 작업계획서 재검증 결과

## 1. 변경 요약

| 파일 | 변경 내용 |
|------|---------|
| `engine/output/workplan_builder.py` | LEGAL_LABELS 3개 추가, legal_rows 3행 추가, 섹션 헤더 라벨 수정, print_area A1:H32 |
| `engine/output/form_registry.py` | excavation_workplan optional_fields에 3개 추가 |
| `scripts/validate_form_registry.py` | excavation_workplan 샘플에 3필드 추가 |
| `scripts/validate_export_api.py` | _EXC_FULL 샘플에 3필드 추가 |

## 2. 레이아웃 검증

openpyxl 재열기 기준:

| Row | A열 값 | 상태 |
|-----|--------|------|
| 7 | 법정 기재 사항 (산업안전보건기준에 관한 규칙 제38조·제82조) | ✓ 수정됨 |
| 8~14 | 기존 법정 7항목 | ✓ 유지됨 |
| 15 | 유도자 배치 | ✓ NEW |
| 16 | 출입통제 방법 | ✓ NEW |
| 17 | 비상연락망 | ✓ NEW |
| 18 | 작업단계별 안전조치 | ✓ 이동됨 (기존 15→18) |
| 19 | 순번 (표 헤더) | ✓ 이동됨 (기존 16→19) |
| 20~29 | 안전조치 10행 | ✓ 이동됨 (기존 17-26→20-29) |
| 30 | 확인 및 서명 | ✓ 이동됨 (기존 27→30) |
| 31~32 | 서명란 | ✓ 이동됨 (기존 28-29→31-32) |

**print_area**: `$A$1:$H$32` ✓

## 3. 신규 3필드 값 렌더링 확인

| field_key | Row | 라벨 | 입력값 | 렌더값 |
|-----------|-----|------|-------|-------|
| `guide_worker_required` | 15 | 유도자 배치 | '유도자 1명' | ✓ 정상 |
| `access_control` | 16 | 출입통제 방법 | '울타리설치' | ✓ 정상 |
| `emergency_contact` | 17 | 비상연락망 | '119, 현장소장' | ✓ 정상 |

빈 form_data 입력 시: 라벨 출력, 값 셀 공란 ✓

## 4. 회귀 검증 결과

### validate_form_registry.py

```
결과: 38/38 PASS, 0 FAIL
최종 판정: PASS
```

- list_supported_forms() 3종 포함: PASS
- get_form_spec('excavation_workplan'): PASS (required_fields, optional_fields, repeat_field, max_repeat_rows, version)
- get_form_spec('education_log'): PASS (영향 없음)
- get_form_spec('risk_assessment'): PASS (영향 없음)
- build_form_excel('excavation_workplan', sample) → 7,382 bytes: PASS
- build_form_excel('education_log', sample) → 7,785 bytes: PASS
- build_form_excel('risk_assessment', sample) → 6,359 bytes: PASS
- build_form_excel('excavation_workplan', {}) → 7,104 bytes (공란): PASS
- 미지원 form_type UnsupportedFormTypeError: PASS (4종 × 2개)

### validate_export_api.py

```
결과: 49/49 PASS, 0 FAIL
최종 판정: PASS
```

- GET /api/forms/types 3종 반환: PASS
- POST education_log file 7,833 bytes: PASS (회귀 없음)
- POST excavation_workplan base64 7,412 bytes: PASS (3필드 포함)
- POST risk_assessment file 6,402 bytes: PASS (영향 없음)
- POST risk_assessment base64 위험성평가표 display_name: PASS
- 미지원 form_type 400 UNSUPPORTED_FORM_TYPE: PASS
- required_field 누락 400 MISSING_REQUIRED_FIELDS: PASS
- repeat 한도 초과 400 REPEAT_LIMIT_EXCEEDED: PASS
- 스칼라 타입 오류 422 INVALID_FIELD_TYPE: PASS
- filename override RFC5987 인코딩: PASS

## 5. 판정

| 항목 | 결과 |
|------|------|
| 신규 3필드 라벨 출력 | ✓ PASS |
| 신규 3필드 값 렌더링 | ✓ PASS |
| 기존 법정 7항목 유지 | ✓ PASS |
| print_area A1:H32 | ✓ PASS |
| education_log 회귀 없음 | ✓ PASS |
| risk_assessment 회귀 없음 | ✓ PASS |
| export API 전 케이스 | ✓ 49/49 PASS |

**최종 판정: PASS**

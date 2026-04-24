# 현재 서식 생성 기능 현황

**작성일**: 2026-04-24  
**기준**: `engine/output/form_registry.py` v1.1, export API `/api/forms/export`

---

## 1. form_registry 등록 현황

현재 `form_registry.py`에 등록된 form_type: **2종**

### education_log (v1.1)

| 항목 | 내용 |
|------|------|
| 표시명 | 안전보건교육일지 |
| builder | `engine/output/education_log_builder.py` → `build_education_log_excel()` |
| required_fields | `education_type`, `education_date`, `education_location`, `education_duration_hours`, `education_target_job`, `instructor_name`, `instructor_qualification`, `confirmer_name`, `confirmer_role` (9개) |
| optional_fields | `site_name`, `site_address`, `subjects`, `attendees`, `confirm_date` |
| repeat_field | `attendees` (최대 30행) |
| API 경로 | `POST /api/forms/export` → `form_type: "education_log"` |
| 법령 근거 | 산업안전보건법 제29조, 시행규칙 제32조 |

### excavation_workplan (v1.0)

| 항목 | 내용 |
|------|------|
| 표시명 | 굴착 작업계획서 |
| builder | `engine/output/workplan_builder.py` → `build_excavation_workplan_excel()` |
| required_fields | `excavation_method`, `earth_retaining`, `excavation_machine`, `soil_disposal`, `water_disposal`, `work_method`, `emergency_measure` (7개) |
| optional_fields | `site_name`, `project_name`, `work_location`, `work_date`, `supervisor`, `contractor`, `safety_steps`, `sign_date` |
| repeat_field | `safety_steps` (최대 10행) |
| API 경로 | `POST /api/forms/export` → `form_type: "excavation_workplan"` |
| 법령 근거 | 기준 규칙 제38조 제1항 제6호, 제82조 |

---

## 2. registry 외 builder 파일

### form_excel_builder.py

| 항목 | 내용 |
|------|------|
| 용도 | 위험성평가표 (실시표) Excel 생성 |
| 공개 함수 | `build_form_excel(form_data)` |
| form_data 출처 | `engine.kras_connector.form_builder.build_risk_assessment_form()` 출력 (kras_standard_form_v1 스키마) |
| 컬럼 구성 | 번호, 공정명, 세부작업명, 위험분류(대/중), 유해위험요인, 관련근거, 현재안전보건조치, 평가척도, 가능성, 중대성, 위험성, 위험성감소대책, 개선후위험성, 개선예정일 |
| registry 등록 | ✗ (별도 라우터에서 직접 호출, form_registry API와 분리) |
| API 경로 | 기존 별도 export 경로 (form_registry 거치지 않음) |
| 상태 | **PARTIAL** — builder는 완성이나 통합 API 미연결 |

---

## 3. API 엔드포인트 현황

### GET /api/forms/types

현재 응답 (registry 기준):

```json
{
  "forms": [
    {
      "form_type": "education_log",
      "display_name": "안전보건교육일지",
      "version": "1.1",
      "required_fields": ["education_type", "education_date", "..."],
      "optional_fields": ["site_name", "..."],
      "repeat_field": "attendees",
      "max_repeat_rows": 30
    },
    {
      "form_type": "excavation_workplan",
      "display_name": "굴착 작업계획서",
      "version": "1.0",
      "required_fields": ["excavation_method", "..."],
      "optional_fields": ["site_name", "..."],
      "repeat_field": "safety_steps",
      "max_repeat_rows": 10
    }
  ]
}
```

### POST /api/forms/export

| 기능 | 지원 여부 |
|------|----------|
| file 모드 (xlsx binary) | ✓ |
| base64 모드 (JSON 응답) | ✓ |
| 한글 파일명 (RFC 5987) | ✓ |
| 5단계 입력 검증 | ✓ |
| form_data 원문 미기록 (보안) | ✓ |

---

## 4. source_map.csv 수집 현황 요약

| 등급 | 건수 | 내용 |
|------|------|------|
| A-grade (법정 서식/별지) | 88건 | 산업안전보건법 시행규칙 별지·별표 원본 |
| B-grade (반공식 지침) | 78건 | 고용노동부·KOSHA 가이드라인, 표준모델 |
| C-grade (현장 실무) | 5건 | 위험성평가표 현장 샘플 |

A-grade 내 법적 서식 핵심 수집 목록:

| 별지/별표 번호 | 서류명 | 비고 |
|--------------|--------|------|
| 별지 제16호서식 | 제조업 등 유해위험방지계획서 | 수집됨 |
| 별지 제17호서식 | 건설공사 유해위험방지계획서 | 수집됨 |
| 별지 제18호서식 | 유해위험방지계획서 자체심사서 | 수집됨 |
| 별지 제19호서식 | 유해위험방지계획서 관련 | 수집됨 |
| 별지 제20호서식 | 유해위험방지계획서 심사결과 통지서 | 행정 서식 |
| 별지 제22호서식 | 유해위험방지계획서 관련 | 수집됨 |
| 별지 제30호서식 | 산업재해조사표 | 수집됨 |
| 별지 제31호서식 | 유해·위험작업 도급승인 신청서 | 수집됨 |
| 별지 제32호서식 | 유해·위험작업 도급승인 연장신청서 | 수집됨 |
| 별지 제33호서식 | 유해·위험작업 도급승인 변경신청서 | 수집됨 |
| 별지 제34호서식 | 유해·위험작업 도급승인서 | 행정 서식 |
| 별지 제103호서식 | 유해위험방지계획서 자체확인 결과서 | 수집됨 |
| 별표 제2의2 | 산업안전보건위원회 회의록 양식 | 수집됨 |
| 별표 제4 | 안전보건교육 교육과정별 교육시간 | 참고 자료 |
| 별표 제5 | 안전보건교육 교육대상별 교육내용 | 참고 자료 |
| 별표 제9 | 산업안전보건위원회 구성 대상 | 참고 자료 |
| 별표 제10 (시행규칙) | 유해위험방지계획서 첨부서류 | 참고 자료 |

미수집:
- 별지 제52호의2서식 (안전보건교육일지 법정 별지)
- 작업계획서 공란 별지 (법정 별지 없음 — 정상)
- 공정안전보고서(PSM) 관련 서식 (범위 외)

---

## 5. 기능 완성도 요약

| 기능 구분 | 상태 |
|----------|------|
| Form Registry API (`GET /api/forms/types`) | ✓ 운영 중 |
| Form Export API (`POST /api/forms/export`) | ✓ 운영 중 |
| 교육일지 생성 | ✓ 완료 |
| 굴착 작업계획서 생성 | ✓ 완료 |
| 위험성평가표 생성 (별도 경로) | △ 운영 중 (통합 API 미연결) |
| 기타 법정서류 생성 | ✗ 미구현 |
| 법정 별지 원본 수집 | △ 일부 수집 (builder 연결은 별개) |

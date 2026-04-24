# Export API 요청 스키마 정의

**작성일**: 2026-04-24  
**대상 엔드포인트**: `POST /api/forms/export`

---

## 1. 최상위 구조

```json
{
  "form_type": "<string>",
  "form_data": { ... },
  "options": { ... }
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `form_type` | string | **필수** | registry에 등록된 식별자 |
| `form_data` | object | **필수** | form_type별 입력 데이터 |
| `options` | object | 선택 | 출력 제어 옵션 |

---

## 2. form_type

허용 값: registry 등록 값만 허용 (`GET /api/forms/types` 응답 참조)

| 값 | 설명 |
|----|------|
| `"education_log"` | 안전보건교육일지 |
| `"excavation_workplan"` | 굴착 작업계획서 |

- 대소문자 구분: `"Education_Log"` → `UNSUPPORTED_FORM_TYPE` 오류
- 신규 form_type 추가 시 registry 등록만으로 자동 지원 (API 코드 변경 불필요)

---

## 3. form_data — education_log

```json
{
  "form_data": {
    "site_name": "○○ 주식회사",
    "site_address": "서울시 강남구 테헤란로 123",
    "education_type": "정기교육",
    "education_date": "2026-04-24 09:00~11:00",
    "education_location": "본사 2층 교육실",
    "education_duration_hours": "2",
    "education_target_job": "생산직 전 직원",
    "instructor_name": "홍길동",
    "instructor_qualification": "산업안전지도사",
    "subjects": [
      {
        "subject_name": "산업안전 및 사고 예방",
        "subject_content": "추락·낙하·협착 위험 및 예방",
        "subject_hours": "1"
      }
    ],
    "attendees": [
      {
        "attendee_name": "김철수",
        "attendee_job_type": "용접공"
      }
    ],
    "confirmer_name": "이담당",
    "confirmer_role": "안전보건관리책임자",
    "confirm_date": "2026-04-24"
  }
}
```

### education_log 필드 명세

**required_fields** (9개 — 법정 필수):

| 필드 | 타입 | 설명 | 법적 근거 |
|------|------|------|---------|
| `education_type` | string | 교육 종류 | 시행규칙 제32조 |
| `education_date` | string | 교육 일시 | 시행규칙 제32조 |
| `education_location` | string | 교육 장소 | 시행규칙 제32조 |
| `education_duration_hours` | string | 교육 시간 합계 | 시행규칙 제32조 |
| `education_target_job` | string | 교육 대상 | 시행규칙 제32조 |
| `instructor_name` | string | 강사명 | 시행규칙 제32조 |
| `instructor_qualification` | string | 강사 자격 | 시행규칙 제32조 |
| `confirmer_name` | string | 확인자 성명 | 시행규칙 제32조 |
| `confirmer_role` | string | 확인자 직위 | 시행규칙 제32조 |

**optional_fields** (5개):

| 필드 | 타입 | 설명 |
|------|------|------|
| `site_name` | string\|null | 사업장명 |
| `site_address` | string\|null | 사업장 소재지 |
| `subjects` | array[SubjectItem] | 교육 내용 반복행 |
| `attendees` | array[AttendeeItem] | 수강자 명단 (≤ 30) |
| `confirm_date` | string\|null | 확인 일자 |

**SubjectItem**:

| 필드 | 타입 |
|------|------|
| `subject_name` | string\|null |
| `subject_content` | string\|null |
| `subject_hours` | string\|null |

**AttendeeItem** (repeat_field, max 30):

| 필드 | 타입 |
|------|------|
| `attendee_name` | string\|null |
| `attendee_job_type` | string\|null |

---

## 4. form_data — excavation_workplan

```json
{
  "form_data": {
    "site_name": "○○ 신축 공사",
    "project_name": "부지 북측 A구간",
    "work_location": "STA. 0+000 ~ 0+200",
    "work_date": "2026-04-25 ~ 2026-05-10",
    "supervisor": "홍길동 (010-1234-5678)",
    "contractor": "㈜한국건설",
    "excavation_method": "개착식 굴착, 심도 5m, 1:1 경사면",
    "earth_retaining": "H-Pile + 토류판, 스트럿 2단",
    "excavation_machine": "백호우 0.8m³ (CAT 320D)",
    "soil_disposal": "현장 외 반출, 처리업체 ○○환경",
    "water_disposal": "웰포인트 공법, 집수정 2개소",
    "work_method": "굴착 → 흙막이 → 스트럿 → 재굴착",
    "emergency_measure": "붕괴 징후 시 즉시 작업 중단 및 대피",
    "safety_steps": [
      {
        "task_step": "사전 지하매설물 확인",
        "hazard": "굴착 중 가스·전기 매설물 파손",
        "safety_measure": "도면 확인 및 시험굴착 실시",
        "responsible_person": "현장소장",
        "note": ""
      }
    ],
    "sign_date": "2026-04-25"
  }
}
```

### excavation_workplan 필드 명세

**required_fields** (7개 — 법정 필수):

| 필드 | 타입 | 설명 | 법적 근거 |
|------|------|------|---------|
| `excavation_method` | string | 굴착의 방법 | 제82조 제1항 제1호 |
| `earth_retaining` | string | 흙막이 지보공 및 방호망 | 제82조 제1항 제2호 |
| `excavation_machine` | string | 사용 기계 종류 및 능력 | 제82조 제1항 제3호 |
| `soil_disposal` | string | 토석 처리 방법 | 제82조 제1항 제4호 |
| `water_disposal` | string | 용수 처리 방법 | 제82조 제1항 제5호 |
| `work_method` | string | 작업 방법 | 제38조 제2항 |
| `emergency_measure` | string | 긴급조치 계획 | 제38조 제2항 |

**optional_fields** (8개):

| 필드 | 타입 | 설명 |
|------|------|------|
| `site_name` | string\|null | 사업장명 |
| `project_name` | string\|null | 현장명 |
| `work_location` | string\|null | 작업 위치 |
| `work_date` | string\|null | 작업 일자/기간 |
| `supervisor` | string\|null | 작업 책임자 |
| `contractor` | string\|null | 도급업체 |
| `safety_steps` | array[StepItem] | 안전조치 반복행 (≤ 10) |
| `sign_date` | string\|null | 작성일 (서명란) |

**StepItem** (repeat_field, max 10):

| 필드 | 타입 | 출력 여부 |
|------|------|---------|
| `task_step` | string\|null | ✓ |
| `hazard` | string\|null | ✓ |
| `safety_measure` | string\|null | ✓ |
| `responsible_person` | string\|null | ✗ (입력 허용, 레이아웃 제약으로 미출력) |
| `note` | string\|null | ✗ (입력 허용, 레이아웃 제약으로 미출력) |

---

## 5. options

```json
{
  "options": {
    "filename": "내_교육일지_2026.xlsx",
    "return_type": "file"
  }
}
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|-------|------|
| `filename` | string\|null | 파일명 규칙 자동 생성 | xlsx 파일명 override |
| `return_type` | `"file"` \| `"base64"` | `"file"` | 응답 방식 선택 |

### return_type 동작

| 값 | 응답 |
|----|------|
| `"file"` (기본) | xlsx binary stream, `Content-Disposition: attachment` |
| `"base64"` | JSON body에 base64 인코딩 문자열 포함 |

---

## 6. 전체 요청 예시

```json
POST /api/forms/export
Content-Type: application/json
Authorization: Bearer <token>

{
  "form_type": "education_log",
  "form_data": {
    "education_type": "정기교육",
    "education_date": "2026-04-24 09:00~11:00",
    "education_location": "본사 2층 교육실",
    "education_duration_hours": "2",
    "education_target_job": "생산직 전 직원",
    "instructor_name": "홍길동",
    "instructor_qualification": "산업안전지도사",
    "confirmer_name": "이담당",
    "confirmer_role": "안전보건관리책임자",
    "attendees": [
      { "attendee_name": "김철수", "attendee_job_type": "용접공" }
    ]
  },
  "options": {
    "return_type": "file"
  }
}
```

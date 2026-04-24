# Export API 검증 규칙 정의

**작성일**: 2026-04-24  
**적용 계층**: API 핸들러 (registry 진입 전)

---

## 1. 검증 순서

요청이 들어오면 아래 순서로 검증. 첫 번째 실패 시 즉시 오류 반환.

```
1. form_type 존재 여부
2. form_data 타입 확인
3. required_fields 누락 여부
4. repeat_field 길이 제한
5. 개별 필드 타입 검증
```

---

## 2. form_type 검증

| 규칙 | 오류 코드 |
|------|---------|
| `form_type` 키 자체 누락 | `MISSING_REQUIRED_FIELDS` |
| 값이 null 또는 빈 문자열 | `UNSUPPORTED_FORM_TYPE` |
| registry 미등록 값 | `UNSUPPORTED_FORM_TYPE` |
| 대소문자 불일치 (예: `"EDUCATION_LOG"`) | `UNSUPPORTED_FORM_TYPE` |

**오류 details 예시**:
```json
{
  "error_code": "UNSUPPORTED_FORM_TYPE",
  "details": {
    "requested": "EDUCATION_LOG",
    "supported": ["education_log", "excavation_workplan"]
  }
}
```

---

## 3. form_data 타입 검증

| 규칙 | 오류 코드 |
|------|---------|
| `form_data` 키 누락 | `MISSING_REQUIRED_FIELDS` |
| `form_data`가 object가 아닌 경우 (array, string 등) | `INVALID_FIELD_TYPE` |

---

## 4. required_fields 누락 검증

form_type별 `required_fields` 전체를 `form_data`에서 확인.

| 규칙 | 오류 코드 |
|------|---------|
| 하나 이상 누락 | `MISSING_REQUIRED_FIELDS` |
| 값이 `null`인 경우 | `MISSING_REQUIRED_FIELDS` (null은 누락으로 처리) |
| 빈 문자열 `""`인 경우 | **허용** (사용자가 의도적으로 비운 것으로 간주) |

**오류 details 예시**:
```json
{
  "error_code": "MISSING_REQUIRED_FIELDS",
  "details": {
    "missing_fields": ["instructor_name", "education_type"]
  }
}
```

### education_log required_fields (9개)

```
education_type, education_date, education_location,
education_duration_hours, education_target_job,
instructor_name, instructor_qualification,
confirmer_name, confirmer_role
```

### excavation_workplan required_fields (7개)

```
excavation_method, earth_retaining, excavation_machine,
soil_disposal, water_disposal, work_method, emergency_measure
```

---

## 5. repeat_field 길이 제한

| form_type | repeat_field | 최대 행 수 | 오류 코드 |
|-----------|-------------|---------|---------|
| `education_log` | `attendees` | **30** | `REPEAT_LIMIT_EXCEEDED` |
| `excavation_workplan` | `safety_steps` | **10** | `REPEAT_LIMIT_EXCEEDED` |

**규칙 상세**:

| 조건 | 처리 |
|------|------|
| repeat_field 키 없음 또는 null | 허용 (공란 행 출력) |
| 빈 배열 `[]` | 허용 (공란 행 출력) |
| 항목 수 ≤ 최대값 | 허용 |
| 항목 수 > 최대값 | `REPEAT_LIMIT_EXCEEDED` |

> 초과분 무시 처리를 원하는 경우 클라이언트가 사전에 자를 것.  
> API는 초과 시 오류 반환 (자동 잘라내기 없음 — 의도치 않은 데이터 손실 방지).

**오류 details 예시**:
```json
{
  "error_code": "REPEAT_LIMIT_EXCEEDED",
  "details": {
    "field": "attendees",
    "limit": 30,
    "received": 45
  }
}
```

---

## 6. 개별 필드 타입 검증

### 최상위 스칼라 필드

| 타입 기대값 | 허용 타입 | 비고 |
|-----------|---------|------|
| string | string, null | null → 빈 셀 출력 |
| string | integer, boolean | `INVALID_FIELD_TYPE` |

### repeat_field 배열 내 항목

| 규칙 | 오류 코드 |
|------|---------|
| 항목이 object가 아닌 경우 | `INVALID_FIELD_TYPE` |
| 항목 내 값이 string/null이 아닌 경우 | `INVALID_FIELD_TYPE` |

**오류 details 예시**:
```json
{
  "error_code": "INVALID_FIELD_TYPE",
  "details": {
    "field": "attendees[2].attendee_name",
    "expected": "string or null",
    "received": "integer"
  }
}
```

---

## 7. options 검증

| 필드 | 규칙 | 오류 |
|------|------|------|
| `options` 전체 | object 또는 null 또는 미제공 | `INVALID_FIELD_TYPE` (object 외 타입) |
| `return_type` | `"file"` 또는 `"base64"` | `INVALID_FIELD_TYPE` |
| `filename` | string 또는 null | `INVALID_FIELD_TYPE` |

---

## 8. 검증 통과 후 처리 흐름

```
유효한 요청
→ form_registry.build_form_excel(form_type, form_data)
→ 파일명 생성
→ return_type에 따라 응답 포맷 결정
→ HTTP 200 반환
```

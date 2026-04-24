# Export API 계약 문서 (통합)

**작성일**: 2026-04-24  
**상태**: DESIGN LOCK — 구현 전 계약 확정  
**구현 대상**: `POST /api/forms/export`, `GET /api/forms/types`  
**참조**: `engine/output/form_registry.py`, `docs/design/form_registry_design.md`

---

## 1. 엔드포인트

| 메서드 | 경로 | 역할 |
|--------|------|------|
| `POST` | `/api/forms/export` | form_type + form_data → xlsx 생성 반환 |
| `GET`  | `/api/forms/types`  | 지원 form_type 목록 반환 |

Base path: `/api/forms`  
버전 접두사: v1 미사용 (향후 `/api/v2/forms` 확장 가능)

---

## 2. 요청 스키마 — POST /api/forms/export

```
POST /api/forms/export
Content-Type: application/json
Authorization: Bearer <token>
```

```json
{
  "form_type": "education_log",
  "form_data": { ... },
  "options": {
    "filename": "optional_custom_name.xlsx",
    "return_type": "file"
  }
}
```

### 필드 규칙

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `form_type` | string | **필수** | registry 등록 값만 허용 (대소문자 구분) |
| `form_data` | object | **필수** | form_type별 입력 데이터 |
| `options` | object | 선택 | 출력 제어 옵션 |
| `options.return_type` | `"file"` \| `"base64"` | 선택 | 기본값: `"file"` |
| `options.filename` | string\|null | 선택 | 파일명 override |

### form_type별 required_fields

**education_log** (9개 — 산업안전보건법 시행규칙 제32조):
```
education_type, education_date, education_location,
education_duration_hours, education_target_job,
instructor_name, instructor_qualification,
confirmer_name, confirmer_role
```

**excavation_workplan** (7개 — 산업안전보건기준에 관한 규칙 제38조·제82조):
```
excavation_method, earth_retaining, excavation_machine,
soil_disposal, water_disposal, work_method, emergency_measure
```

### repeat_field 제한

| form_type | repeat_field | 최대 |
|-----------|-------------|------|
| `education_log` | `attendees` | 30 |
| `excavation_workplan` | `safety_steps` | 10 |

---

## 3. 응답 스키마

### 3.1 POST /api/forms/export — 성공 (file 모드)

```
HTTP 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="education_log_20260424_153022.xlsx"
Content-Length: <bytes>

<xlsx binary stream>
```

### 3.2 POST /api/forms/export — 성공 (base64 모드)

```
HTTP 200 OK
Content-Type: application/json
```
```json
{
  "success": true,
  "form_type": "education_log",
  "display_name": "안전보건교육일지",
  "filename": "education_log_20260424_153022.xlsx",
  "file_base64": "UEsDBBQABgAIAAAAIQBi7...",
  "size": 7786,
  "generated_at": "2026-04-24T15:30:22+09:00"
}
```

### 3.3 GET /api/forms/types — 성공

```
HTTP 200 OK
Content-Type: application/json
```
```json
{
  "forms": [
    {
      "form_type": "education_log",
      "display_name": "안전보건교육일지",
      "version": "1.1",
      "required_fields": ["education_type", "..."],
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

> `form_registry.list_supported_forms()` 출력과 1:1 매핑. builder 함수 참조 미노출.

### 3.4 오류 응답 (공통 구조)

```json
{
  "success": false,
  "error_code": "MISSING_REQUIRED_FIELDS",
  "message": "필수 입력 항목이 누락되었습니다.",
  "details": {
    "missing_fields": ["instructor_name"]
  }
}
```

---

## 4. 파일명 규칙

### 기본 규칙

```
{form_type}_{YYYYMMDD}_{HHMMSS}.xlsx
```

예:
- `education_log_20260424_153022.xlsx`
- `excavation_workplan_20260424_090507.xlsx`

### options.filename override

| 조건 | 처리 |
|------|------|
| `options.filename` 없음 | 기본 규칙 자동 생성 |
| `.xlsx` 미포함 | 자동 추가 |
| 경로 구분자 포함 (`/`, `\`, `..`) | 제거 (경로 주입 방지) |
| 255자 초과 | 255자 잘라내고 `.xlsx` 추가 |

시각 기준: **KST (UTC+9)**

---

## 5. 검증 규칙

검증 순서 (첫 번째 실패 시 즉시 반환):

```
1. form_type 존재 여부       → UNSUPPORTED_FORM_TYPE
2. form_data 타입 확인        → MISSING_REQUIRED_FIELDS / INVALID_FIELD_TYPE
3. required_fields 누락       → MISSING_REQUIRED_FIELDS
4. repeat_field 길이 초과     → REPEAT_LIMIT_EXCEEDED
5. 개별 필드 타입 검증        → INVALID_FIELD_TYPE
```

**null vs 빈 문자열**:

| 값 | 처리 |
|----|------|
| `null` (required_field) | 누락으로 처리 → `MISSING_REQUIRED_FIELDS` |
| `""` (required_field) | 허용 (빈 셀 출력) |
| `null` (optional_field) | 허용 (빈 셀 출력) |

---

## 6. 오류 코드

| error_code | HTTP | 발생 조건 |
|-----------|------|---------|
| `UNSUPPORTED_FORM_TYPE` | 400 | form_type 미등록 |
| `MISSING_REQUIRED_FIELDS` | 400 | 필수 필드 누락/null |
| `INVALID_FIELD_TYPE` | 422 | 필드 타입 불일치 |
| `REPEAT_LIMIT_EXCEEDED` | 400 | repeat_field 항목 수 초과 |
| `BUILDER_ERROR` | 500 | builder 내부 예외 |
| `UNAUTHORIZED` | 401 | 인증 토큰 없음/유효하지 않음 |

**오류 상세 examples**:

```json
// UNSUPPORTED_FORM_TYPE
{ "details": { "requested": "vehicle_workplan", "supported": ["education_log", "excavation_workplan"] } }

// MISSING_REQUIRED_FIELDS
{ "details": { "missing_fields": ["instructor_name", "education_type"] } }

// INVALID_FIELD_TYPE
{ "details": { "field": "attendees[2].attendee_name", "expected": "string or null", "received": "integer" } }

// REPEAT_LIMIT_EXCEEDED
{ "details": { "field": "attendees", "limit": 30, "received": 45 } }

// BUILDER_ERROR
{ "details": { "form_type": "education_log", "hint": "서버 로그를 확인하세요." } }
```

---

## 7. 보안

### 인증 헤더

```
Authorization: Bearer <token>
```

| 항목 | 결정 |
|------|------|
| v1 내부 전용 환경 | 인증 생략 가능 |
| v1 외부 접근 환경 | Bearer 토큰 필수 |
| 토큰 전달 | 헤더만 허용 (쿼리 파라미터 금지) |
| 토큰 저장 | 환경변수 / secrets manager (평문 DB 금지) |

### 로그 정책

| 항목 | 기록 여부 |
|------|---------|
| 요청 form_type, 시각, IP | ✓ |
| form_data 원문 | ✗ (개인정보 포함 가능) |
| 인증 토큰 값 | ✗ |
| 오류 traceback | ✓ 서버 로그 (클라이언트 미노출) |

### Rate Limiting

- 분당 60회 / 토큰
- 요청 body ≤ 1MB
- 응답 파일 ≤ 10MB

---

## 8. 구현 연결 포인트

| API 동작 | registry 함수 |
|---------|-------------|
| `GET /api/forms/types` | `list_supported_forms()` |
| form_type 검증 | `get_form_spec(form_type)` |
| xlsx 생성 | `build_form_excel(form_type, form_data)` |
| 미지원 form_type 처리 | `UnsupportedFormTypeError` catch → `UNSUPPORTED_FORM_TYPE` |
| builder 내부 오류 | `TypeError` / 일반 Exception catch → `BUILDER_ERROR` |

---

## 9. form_type 확장 절차

신규 form_type 추가 시 API 코드 변경 없이 registry만 갱신:

1. builder 모듈 구현 (`engine/output/<type>_builder.py`)
2. `_REGISTRY`에 `FormSpec` 항목 추가
3. `GET /api/forms/types` 자동 반영
4. `POST /api/forms/export` 자동 지원

---

## 10. 참조 문서

| 문서 | 경로 |
|------|------|
| 엔드포인트 정의 | `docs/design/export_api_endpoints.md` |
| 요청 스키마 | `docs/design/export_api_request_schema.md` |
| 응답 스키마 | `docs/design/export_api_response_schema.md` |
| 파일명 규칙 | `docs/design/export_api_filename_rule.md` |
| 검증 규칙 | `docs/design/export_api_validation_rules.md` |
| 오류 코드 | `docs/design/export_api_error_spec.md` |
| 보안/권한 | `docs/design/export_api_security.md` |
| Form Registry 설계 | `docs/design/form_registry_design.md` |

# Export API 오류 코드 정의

**작성일**: 2026-04-24

---

## 1. 오류 응답 구조 (공통)

```json
{
  "success": false,
  "error_code": "<ERROR_CODE>",
  "message": "<사람이 읽는 설명>",
  "details": {}
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `success` | boolean | 필수 | 항상 `false` |
| `error_code` | string | 필수 | 오류 식별 상수 |
| `message` | string | 필수 | 한국어 설명 |
| `details` | object | 선택 | 오류별 구조화 상세 |

---

## 2. 오류 코드 전체 목록

### UNSUPPORTED_FORM_TYPE

| 항목 | 내용 |
|------|------|
| HTTP 상태 | 400 Bad Request |
| 발생 조건 | form_type이 registry에 없음 |
| 구현 연결 | `UnsupportedFormTypeError` in `form_registry.py` |

```json
{
  "success": false,
  "error_code": "UNSUPPORTED_FORM_TYPE",
  "message": "지원하지 않는 서식 유형입니다.",
  "details": {
    "requested": "vehicle_workplan",
    "supported": ["education_log", "excavation_workplan"]
  }
}
```

---

### MISSING_REQUIRED_FIELDS

| 항목 | 내용 |
|------|------|
| HTTP 상태 | 400 Bad Request |
| 발생 조건 | required_fields 중 하나 이상 누락 또는 null |

```json
{
  "success": false,
  "error_code": "MISSING_REQUIRED_FIELDS",
  "message": "필수 입력 항목이 누락되었습니다.",
  "details": {
    "missing_fields": ["instructor_name", "education_type"]
  }
}
```

---

### INVALID_FIELD_TYPE

| 항목 | 내용 |
|------|------|
| HTTP 상태 | 422 Unprocessable Entity |
| 발생 조건 | 필드 값의 타입이 스키마와 불일치 |

```json
{
  "success": false,
  "error_code": "INVALID_FIELD_TYPE",
  "message": "필드 타입이 올바르지 않습니다.",
  "details": {
    "field": "attendees[1].attendee_name",
    "expected": "string or null",
    "received": "integer"
  }
}
```

---

### REPEAT_LIMIT_EXCEEDED

| 항목 | 내용 |
|------|------|
| HTTP 상태 | 400 Bad Request |
| 발생 조건 | repeat_field 항목 수가 max_repeat_rows 초과 |

```json
{
  "success": false,
  "error_code": "REPEAT_LIMIT_EXCEEDED",
  "message": "반복 행 수가 허용 한도를 초과했습니다.",
  "details": {
    "field": "attendees",
    "limit": 30,
    "received": 45
  }
}
```

---

### BUILDER_ERROR

| 항목 | 내용 |
|------|------|
| HTTP 상태 | 500 Internal Server Error |
| 발생 조건 | 검증 통과 후 builder 내부에서 예외 발생 |
| 구현 연결 | `TypeError` in `build_form_excel()` 또는 openpyxl 예외 |

```json
{
  "success": false,
  "error_code": "BUILDER_ERROR",
  "message": "서식 파일 생성 중 내부 오류가 발생했습니다.",
  "details": {
    "form_type": "education_log",
    "hint": "서버 로그를 확인하세요."
  }
}
```

> `details`에 예외 메시지 원문을 노출하지 않음 (보안). 서버 로그에는 full traceback 기록.

---

## 3. 오류 코드 — HTTP 상태 코드 매핑 요약

| error_code | HTTP | 원인 계층 |
|-----------|------|---------|
| `UNSUPPORTED_FORM_TYPE` | 400 | 요청 입력 |
| `MISSING_REQUIRED_FIELDS` | 400 | 요청 입력 |
| `INVALID_FIELD_TYPE` | 422 | 요청 입력 |
| `REPEAT_LIMIT_EXCEEDED` | 400 | 요청 입력 |
| `BUILDER_ERROR` | 500 | 서버 내부 |

---

## 4. 클라이언트 처리 지침

| error_code | 권장 처리 |
|-----------|---------|
| `UNSUPPORTED_FORM_TYPE` | `GET /api/forms/types`로 목록 재조회 후 재시도 |
| `MISSING_REQUIRED_FIELDS` | `details.missing_fields`로 누락 필드 UI 강조 |
| `INVALID_FIELD_TYPE` | `details.field`로 문제 필드 위치 표시 |
| `REPEAT_LIMIT_EXCEEDED` | `details.limit`로 최대 행 수 안내 |
| `BUILDER_ERROR` | 관리자에게 문의 안내 (사용자 재시도 불가) |

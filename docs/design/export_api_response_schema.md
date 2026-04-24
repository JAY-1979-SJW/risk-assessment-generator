# Export API 응답 스키마 정의

**작성일**: 2026-04-24  
**대상 엔드포인트**: `POST /api/forms/export`, `GET /api/forms/types`

---

## 1. POST /api/forms/export — 성공 응답

### 1.1 return_type = "file" (기본)

```
HTTP 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="education_log_20260424_153022.xlsx"
Content-Length: <bytes>

<xlsx binary stream>
```

- 응답 body: xlsx 바이너리 직접 스트림
- 별도 JSON wrapper 없음
- 클라이언트는 body를 파일로 저장하거나 Blob으로 처리

### 1.2 return_type = "base64"

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

| 필드 | 타입 | 설명 |
|------|------|------|
| `success` | boolean | 항상 `true` |
| `form_type` | string | 요청한 form_type |
| `display_name` | string | form 한글명 |
| `filename` | string | 생성된 파일명 |
| `file_base64` | string | xlsx 바이너리 base64 인코딩 |
| `size` | integer | 파일 크기 (bytes) |
| `generated_at` | string | 생성 시각 (ISO 8601, KST) |

---

## 2. GET /api/forms/types — 성공 응답

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
      "required_fields": [
        "education_type",
        "education_date",
        "education_location",
        "education_duration_hours",
        "education_target_job",
        "instructor_name",
        "instructor_qualification",
        "confirmer_name",
        "confirmer_role"
      ],
      "optional_fields": [
        "site_name",
        "site_address",
        "subjects",
        "attendees",
        "confirm_date"
      ],
      "repeat_field": "attendees",
      "max_repeat_rows": 30
    },
    {
      "form_type": "excavation_workplan",
      "display_name": "굴착 작업계획서",
      "version": "1.0",
      "required_fields": [
        "excavation_method",
        "earth_retaining",
        "excavation_machine",
        "soil_disposal",
        "water_disposal",
        "work_method",
        "emergency_measure"
      ],
      "optional_fields": [
        "site_name",
        "project_name",
        "work_location",
        "work_date",
        "supervisor",
        "contractor",
        "safety_steps",
        "sign_date"
      ],
      "repeat_field": "safety_steps",
      "max_repeat_rows": 10
    }
  ]
}
```

> `form_registry.list_supported_forms()` 출력과 1:1 매핑. builder 함수 참조는 미노출.

---

## 3. 오류 응답 (공통 구조)

```
HTTP 4xx / 5xx
Content-Type: application/json
```

```json
{
  "success": false,
  "error_code": "MISSING_REQUIRED_FIELDS",
  "message": "필수 필드가 누락되었습니다.",
  "details": {
    "missing_fields": ["education_type", "instructor_name"]
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `success` | boolean | 항상 `false` |
| `error_code` | string | 오류 식별 코드 (상수) |
| `message` | string | 사람이 읽는 오류 설명 |
| `details` | object | 오류 상세 (선택, 오류 종류별 구조 상이) |

---

## 4. HTTP 상태 코드 매핑

| 상황 | HTTP 코드 |
|------|---------|
| 성공 | 200 |
| form_type 미지원 | 400 |
| required_fields 누락 | 400 |
| 필드 타입 오류 | 422 |
| repeat 행 초과 | 400 |
| builder 내부 오류 | 500 |

---

## 5. 응답 헤더 (file 모드)

| 헤더 | 값 | 비고 |
|------|---|------|
| `Content-Type` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | xlsx MIME |
| `Content-Disposition` | `attachment; filename="<파일명>"` | 파일명 규칙 참조 |
| `Content-Length` | `<bytes>` | 파일 크기 |
| `X-Form-Type` | `education_log` | 디버깅용 (선택) |
| `X-Generated-At` | `2026-04-24T15:30:22+09:00` | 생성 시각 (선택) |

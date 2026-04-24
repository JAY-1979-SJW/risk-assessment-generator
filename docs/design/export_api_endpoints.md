# Export API 엔드포인트 정의

**작성일**: 2026-04-24  
**상태**: DESIGN LOCK — 구현 전 계약 확정  
**참조**: `engine/output/form_registry.py`, `docs/design/form_registry_design.md`

---

## 1. 엔드포인트 목록

| 메서드 | 경로 | 역할 |
|--------|------|------|
| `POST` | `/api/forms/export` | form_type + form_data → xlsx 파일 생성 반환 |
| `GET`  | `/api/forms/types`  | 지원 form_type 목록 반환 |

---

## 2. POST /api/forms/export

### 역할

`form_type`과 `form_data`를 받아 xlsx 파일을 생성하고 반환.  
`options.return_type`에 따라 파일 직접 스트림 또는 base64 인코딩 선택.

### 요청

```
POST /api/forms/export
Content-Type: application/json
Authorization: Bearer <token>      ← v1: 내부 환경에서 생략 가능
```

### 응답 (file 모드)

```
HTTP 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="education_log_20260424_153022.xlsx"
```

### 응답 (base64 모드)

```
HTTP 200 OK
Content-Type: application/json
```

### 오류

```
HTTP 400 Bad Request   — 입력 검증 실패
HTTP 422 Unprocessable — 필드 타입/형식 오류
HTTP 500 Internal      — builder 내부 오류
```

---

## 3. GET /api/forms/types

### 역할

`form_registry`에 등록된 지원 form_type 목록을 반환.  
프론트엔드 폼 선택 UI 및 입력 스키마 조회에 사용.

### 요청

```
GET /api/forms/types
Authorization: Bearer <token>      ← v1: 생략 가능
```

### 응답

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
      "required_fields": ["education_type", "education_date", "..."],
      "optional_fields": ["site_name", "..."],
      "repeat_field": "attendees",
      "max_repeat_rows": 30
    },
    {
      "form_type": "excavation_workplan",
      "display_name": "굴착 작업계획서",
      "version": "1.0",
      "required_fields": ["excavation_method", "earth_retaining", "..."],
      "optional_fields": ["site_name", "..."],
      "repeat_field": "safety_steps",
      "max_repeat_rows": 10
    }
  ]
}
```

> 응답은 `form_registry.list_supported_forms()` 출력과 1:1 매핑.

---

## 4. URL 규칙

| 항목 | 결정 |
|------|------|
| Base path | `/api/forms` |
| 버전 접두사 | v1에서는 미사용 (향후 `/api/v2/forms` 확장 가능) |
| Content negotiation | `options.return_type` 파라미터로 결정 (Accept 헤더 미사용) |
| 인코딩 | UTF-8 |

---

## 5. 향후 확장 포인트

| 확장 | 경로 예시 | 비고 |
|------|----------|------|
| 신규 form_type | registry에 등록 시 자동 지원 | 엔드포인트 추가 불필요 |
| 작업 이력 조회 | `GET /api/forms/history` | v2 예정 |
| 비동기 생성 | `POST /api/forms/export/async` | 대용량 대응, v2 예정 |

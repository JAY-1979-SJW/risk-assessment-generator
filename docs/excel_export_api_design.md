# Excel 본표 Export API 설계 (v1 draft)

**상태**: 설계 단계 — **구현 금지** (본 단계는 인터페이스 확정만)
**대상 엔드포인트**: `POST /api/v1/risk-assessment/export-form-excel`
**관련 모듈**:
- 렌더러: `engine/output/form_excel_builder.py` (`build_form_excel(form_data) -> bytes`)
- 폼 빌더: `engine/kras_connector/form_builder.py` (`build_risk_assessment_form(...)`)
- 표 빌더: `engine/kras_connector/table_builder.py` (`build_risk_table_from_result(...)`)
- 매퍼/보강: `engine/kras_connector/mapper.py`, `enrichment.py`

---

## 1. 엔드포인트 요약

| 항목 | 값 |
|------|----|
| Method | `POST` |
| Path | `/api/v1/risk-assessment/export-form-excel` |
| 인증 | 기존 `risk_assessment_build` 와 동일 정책 (현재 공개) |
| 라우터 파일(예정) | `backend/routers/risk_assessment_export_form_excel.py` |
| operation_id | `exportRiskAssessmentFormExcel` |

라우터 파일은 기존 `risk_assessment_build.py` 패턴을 그대로 따른다 (sys.path 인젝션, APIRouter prefix=`/v1/risk-assessment`).

---

## 2. 요청 스키마

기존 v2 build 입력을 상위 호환으로 포용하고, 본표 전용 `header_input` / `optional_input` 을 추가.

```json
{
  "work_type": "전기작업",
  "equipment": ["사다리"],
  "location": ["옥상"],
  "conditions": ["활선근접"],
  "header_input": {
    "company_name": "(주)해한 AI",
    "site_name": "OO빌딩 신축공사 옥상 전기설비",
    "industry": "전기공사업",
    "representative": "홍길동",
    "assessment_type": "수시평가",
    "assessment_date": "2026-04-23"
  },
  "optional_input": {
    "sub_work": "옥상 전기간선 포설(활선 근접)",
    "target_date": "2026-05-10",
    "responsible_person": "김안전 (안전관리자)"
  }
}
```

### 필드 규칙

| 필드 | 타입 | 필수 | 비고 |
|------|------|------|------|
| `work_type` | string | ✅ | build v2 와 동일 검증 규칙 (빈 문자열/미지정 → 400) |
| `equipment` / `location` / `conditions` | string[] | — | build v2 와 동일. 허용값 외 → 400 `INVALID_INPUT_OPTION` |
| `header_input` | object | — | 상단 메타. 누락/빈칸 허용 (엑셀에도 빈 셀) |
| `header_input.assessment_type` | enum | — | `최초평가` / `정기평가` / `수시평가` / `상시평가` 외 값은 통과(현재 단계는 경고만) |
| `header_input.assessment_date` | date(YYYY-MM-DD) | — | 포맷 검증은 v1 에서는 생략, 문자열 그대로 렌더 |
| `optional_input` | object | — | `form_builder._row_optional_value` 계약 그대로 사용 (`rows[]` 배열 또는 flat 키) |

`header_input` 의 `work_type` 은 별도 입력받지 않고 request 의 최상위 `work_type` 을 form_builder 에서 자동 채움.

---

## 3. 처리 플로우

```
1) 입력 검증
   - 기존 build v2 검증 재사용:
       normalize_input_context(body) / work_type 존재 여부
   - header_input/optional_input 은 optional (검증 없음, dict 이면 수용)

2) 엔진 파이프라인
   base_result = build_risk_assessment(work_type)
   if context_is_empty(input_ctx):
       enriched = base_result
   else:
       enriched = apply_rules(base_result, input_ctx)
       enriched["input_context"] = input_ctx

3) 표 → 본표 변환
   table_data = build_risk_table_from_result(enriched)
   form_data  = build_risk_assessment_form(table_data, header_input, optional_input)

4) 렌더링
   xlsx_bytes = build_form_excel(form_data)

5) 응답 반환
   Response(
     content=xlsx_bytes,
     media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
     headers={"Content-Disposition": 'attachment; filename="risk_assessment_form.xlsx"'}
   )
```

### 금지
- mapper / enrichment / form_builder 로직 수정 금지.
- DB write 금지 (현 엔드포인트는 stateless).
- `references_detail` 를 응답 바이트 또는 헤더로 노출 금지.

---

## 4. 응답 스펙

### 정상 응답

| 항목 | 값 |
|------|----|
| Status | `200 OK` |
| Content-Type | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| Content-Disposition | `attachment; filename="risk_assessment_form.xlsx"` (파일명 고정 또는 `site_name`/`assessment_date` 기반 선택 — v1 은 고정) |
| Body | xlsx 바이너리 (`build_form_excel` 반환값) |

### 에러 응답 (JSON, 기존 build 와 동일한 `{"error": {...}}` 포맷)

| HTTP | code | 조건 |
|------|------|------|
| 400 | `MISSING_WORK_TYPE` | `work_type` 미제공 또는 body 자체 null |
| 400 | `EMPTY_WORK_TYPE` | `work_type` 빈 문자열 |
| 400 | `INVALID_INPUT_OPTION` | equipment/location/conditions 허용값 외 |
| 404 | `UNKNOWN_WORK_TYPE` | base_result 에 hazards 없음 |
| 500 | `INTERNAL_ERROR` | mapper/enrichment/form_builder/render 중 예외 |

**주의**: Content-Type 은 에러일 때에만 `application/json`, 정상일 때에만 xlsx. 클라이언트는 상태코드로 분기한다.

---

## 5. Pydantic 스키마 (예정)

`backend/schemas/risk_assessment_export_form_excel.py` (신규) 에 정의.

```python
class HeaderInput(BaseModel):
    company_name: Optional[str] = None
    site_name: Optional[str] = None
    industry: Optional[str] = None
    representative: Optional[str] = None
    assessment_type: Optional[str] = None
    assessment_date: Optional[str] = None

class OptionalRow(BaseModel):
    sub_work: Optional[str] = None
    target_date: Optional[str] = None
    completion_date: Optional[str] = None
    responsible_person: Optional[str] = None

class OptionalInput(BaseModel):
    sub_work: Optional[str] = None
    target_date: Optional[str] = None
    completion_date: Optional[str] = None
    responsible_person: Optional[str] = None
    rows: Optional[list[OptionalRow]] = None

class RiskAssessmentExportFormExcelRequest(BaseModel):
    work_type: str
    equipment: Optional[list[str]] = None
    location: Optional[list[str]] = None
    conditions: Optional[list[str]] = None
    header_input: Optional[HeaderInput] = None
    optional_input: Optional[OptionalInput] = None
```

응답은 바이너리이므로 `response_model` 을 두지 않고 `StreamingResponse` 또는 `Response` 직접 반환.

---

## 6. OpenAPI 조각 (참고)

```yaml
paths:
  /api/v1/risk-assessment/export-form-excel:
    post:
      operationId: exportRiskAssessmentFormExcel
      tags: [risk-assessment]
      summary: 위험성평가표 본표 Excel 파일 출력
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RiskAssessmentExportFormExcelRequest"
      responses:
        '200':
          description: 정상 생성된 xlsx 바이너리
          content:
            application/vnd.openxmlformats-officedocument.spreadsheetml.sheet:
              schema:
                type: string
                format: binary
        '400':
          description: 입력 검증 실패
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ApiError" }
        '404':
          description: 등록되지 않은 작업유형
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ApiError" }
        '500':
          description: 내부 오류
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ApiError" }
```

---

## 7. 다음 단계 (구현 착수 시)

1. `backend/schemas/risk_assessment_export_form_excel.py` 생성
2. `backend/routers/risk_assessment_export_form_excel.py` 생성
3. `backend/main.py` 에 `app.include_router(...)` 추가
4. 회귀 테스트: build v2 를 export 로 대체했을 때 동일 데이터가 렌더되는지 확인
5. `docs/openapi_draft_v2.yaml` 갱신

본 문서는 위 구현 착수를 위한 인터페이스 계약을 고정한다.

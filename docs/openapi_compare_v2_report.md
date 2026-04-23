# OpenAPI v1 → v2 변경 비교 보고서

**대상**: `POST /api/v1/risk-assessment/build`
**v1 소스**: `data/risk_db/api_schema/openapi_draft.yaml`
**v2 소스**: `data/risk_db/api_schema/openapi_draft_v2.yaml`
**버전 정책**: URL `/api/v1/...` 그대로 유지 (하위호환 확장). 메이저 분기 없음.

---

## 1. 정보 필드

| 항목 | v1 | v2 |
|------|----|----|
| `info.version` | `1.0.0` | `2.0.0` |
| `info.description` | 초안 (구현 없음) | v2 변경 요약 포함 |

---

## 2. 엔드포인트 메타데이터

| 항목 | v1 | v2 | 비고 |
|------|----|----|----|
| path | `/risk-assessment/build` | `/risk-assessment/build` | 동일 |
| method | POST | POST | 동일 |
| operationId | `buildRiskAssessment` | `buildRiskAssessment` | **유지** (deploy 시 일관성) |
| tags | `[risk-assessment]` | `[risk-assessment]` | **유지** |

---

## 3. 요청 스키마

| 필드 | v1 | v2 |
|------|----|----|
| `work_type` | required string | required string (동일) |
| `equipment` | — | **신규** optional string[] (whitelist 8개) |
| `location` | — | **신규** optional string[] (whitelist 8개) |
| `conditions` | — | **신규** optional string[] (whitelist 10개) |
| `additionalProperties` | false | false (유지) |

**정책**:
- 3개 신규 필드 모두 **optional**. 빈 배열/null/미존재 시 v1 경로와 동일 동작.
- 각 원소는 enum whitelist 준수. 위반 시 400 `INVALID_INPUT_OPTION`.
- 중복값은 자동 dedupe.

---

## 4. 응답 스키마

| 필드 | v1 | v2 |
|------|----|----|
| `work_type` | string | string (동일) |
| `hazards` | HazardItem[] | HazardItem[] (동일) |
| `input_context` | — | **신규** optional InputContext |

**`input_context` 노출 정책**:
- v2 입력 제공 시에만 응답에 포함.
- v1 호환 요청(`{"work_type":"..."}`)에서는 필드 자체 미출력 → v1 응답과 바이트 동일.

**HazardItem 구조**: v1과 **완전 동일**. 보강 로직은 다음만 수행:
- `controls` 배열에 rule 기반 조치 append (hazard당 최대 2개, 중복 금지)
- `confidence_score` 상향 (+0.05 기본, 상한 1.0)
- `evidence_summary` 말미 `[조건 반영: ...]` 부착
- 전체 `hazards` 재정렬 (confidence_score DESC)

---

## 5. 에러 스키마

| code | v1 | v2 |
|------|----|----|
| `MISSING_WORK_TYPE` | ✓ (400) | ✓ (400) |
| `EMPTY_WORK_TYPE` | ✓ (400) | ✓ (400) |
| `UNKNOWN_WORK_TYPE` | ✓ (404) | ✓ (404) |
| `INVALID_INPUT_OPTION` | — | **신규** (400) |
| `INTERNAL_ERROR` | ✓ (500) | ✓ (500) |

`ApiError` 최상위 구조는 동일 (`{ error: { code, message, details? } }`). `code` enum 1건 추가.

**`INVALID_INPUT_OPTION.details` 규격** (신규):
```json
{
  "field": "equipment",
  "value": "없는장비",
  "allowed_values": ["사다리", "이동식비계", "..."]
}
```

---

## 6. components.schemas 차이

| 스키마명 | v1 | v2 | 비고 |
|---------|----|----|----|
| `RiskAssessmentBuildRequest` | ✓ | ✓ | 3개 필드 추가 |
| `RiskAssessmentBuildResponse` | ✓ | ✓ | `input_context` optional 필드 추가 |
| `InputContext` | — | **신규** | equipment/location/conditions arrays |
| `HazardItem` | ✓ | ✓ | 변경 없음 |
| `References` | ✓ | ✓ | 변경 없음 (related_expc_ids 노출 금지 정책 유지) |
| `ApiError` | ✓ | ✓ | inline error 객체를 `ApiErrorDetail` 참조로 분리 |
| `ApiErrorDetail` | (inline) | **신규 separate schema** | `code` enum에 `INVALID_INPUT_OPTION` 추가 |

> 참고: v1 draft는 `ApiError.error`를 inline object로 정의했으나, runtime(Pydantic v2) 구현상 nested model을 `ApiErrorDetail`로 자동 분리한다. v2 draft는 runtime 구조와 정확히 일치시킨 형태로 문서화.

---

## 7. 하위호환 영향도

| 기존 클라이언트 시나리오 | v2 동작 | 호환 여부 |
|---------------------|---------|---------|
| `{"work_type":"X"}` 단독 요청 | v1과 동일 응답 (`input_context` 미포함) | ✓ |
| v1 응답 파싱 (`work_type`/`hazards`만 기대) | `input_context` 미노출 → 파서 영향 없음 | ✓ |
| 기존 에러 코드 파싱 | 기존 4개 code 값 모두 보존 | ✓ |
| references 3축만 파싱 | `related_expc_ids` 노출 금지 정책 유지 | ✓ |

**결론**: URL·스키마·에러 모두 **추가형 변경**. 브레이킹 없음. API 버전 URL 분리 불필요.

---

## 8. 운영 반영 체크리스트

- [x] OpenAPI runtime 검증 (deploy 후 `/openapi.json`)
- [x] operationId `buildRiskAssessment` 유지
- [x] tags `[risk-assessment]` 유지
- [x] 에러 $ref 5개 code 포함 (`INVALID_INPUT_OPTION` 추가)
- [x] `InputContext` components 등록
- [x] hazards 불변식 회귀 없음 (6 단계 테스트 보고서 참조)
- [ ] Swagger UI 상 `InputContext` 예제 렌더링 확인 (배포 후 수동)

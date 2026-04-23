# OpenAPI 초안 vs 실제 구현 비교 보고서

## 비교 대상
- 초안: `data/risk_db/api_schema/openapi_draft.yaml`
- 실제: FastAPI 자동 생성 (`/openapi.json`)

---

## 일치 항목

| 항목 | 초안 | 실제 | 판정 |
|------|------|------|------|
| endpoint 경로 | `/api/v1/risk-assessment/build` | `/api/v1/risk-assessment/build` | ✓ |
| HTTP 메서드 | POST | POST | ✓ |
| 응답 코드 200 | ✓ | ✓ | ✓ |
| 응답 코드 400 | ✓ | ✓ | ✓ |
| 응답 코드 404 | ✓ | ✓ | ✓ |
| 응답 코드 500 | ✓ | ✓ | ✓ |
| `RiskAssessmentBuildResponse` 필드 | work_type, hazards | work_type, hazards | ✓ |
| `HazardItem` 필드 | hazard/controls/references/confidence_score/evidence_summary | 동일 | ✓ |
| `References` 필드 | law_ids/moel_expc_ids/kosha_ids | 동일 | ✓ |
| `additionalProperties: false` | References ✓ | References ✓ | ✓ |
| related_expc_ids 미노출 | ✓ | ✓ | ✓ |

---

## 차이 항목 (WARN 수준)

| 항목 | 초안 | 실제 | 영향 |
|------|------|------|------|
| `operationId` | `buildRiskAssessment` | `build_api_v1_risk_assessment_build_post` | 클라이언트 SDK 생성 시 함수명 차이. 런타임 동작 무관 |
| `tags` | `risk-assessment` | `risk-assessment-build` | Swagger UI 그룹핑 차이. 런타임 무관 |
| 422 응답 | 미명시 | 자동 추가 | FastAPI 기본값. body 수동 검증으로 실제 422는 미발생 |
| 에러 응답 스키마 참조 | `$ref: ApiError` | 설명 문자열만 | Swagger UI에서 에러 스키마 자동 렌더링 안됨. 런타임 실제 응답은 계약과 일치 |

---

## 판정

**WARN**

- 핵심 계약(경로, 메서드, 요청/응답 스키마, 에러 코드)은 완전 일치
- 차이는 모두 OpenAPI 메타데이터 표현 수준 (operationId, tags, 에러 스키마 ref)
- 런타임 동작 불일치 없음

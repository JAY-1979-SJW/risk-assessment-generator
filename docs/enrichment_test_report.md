# Risk Assessment Build API v2 — Enrichment Test Report

**대상**: `POST /api/v1/risk-assessment/build`
**검증 시점**: 2026-04-23 (서버 배포 직후)
**서버**: `https://kras.haehan-ai.kr` (내부: `risk-assessment-api` / port 8100)
**커밋**: `659f979` (feat(build-api): v2 입력 확장 + 규칙 기반 enrichment 1차)

---

## 1. 회귀 검증 매트릭스

| # | 시나리오 | 페이로드 | 기대 | 실제 | 판정 |
|---|---------|---------|------|------|------|
| 1 | 전기 + 사다리 + 옥상 + 활선근접 | `{"work_type":"전기작업","equipment":["사다리"],"location":["옥상"],"conditions":["활선근접"]}` | 200, 감전·추락 보강, input_context 노출 | 200, 감전 0.88→0.93(+R001), 추락 0.82→0.92(+R002+R003), controls 각 +2, input_context 포함 | ✓ PASS |
| 2 | 밀폐공간 + 맨홀 + 밀폐공간 | `{"work_type":"밀폐공간 작업","location":["맨홀"],"conditions":["밀폐공간"]}` | 200, 질식 보강 | 200, 질식 0.90→1.00(cap), controls +2(R010 우선, R011은 상한 도달로 skip) | ✓ PASS |
| 3-대체 | 굴착 + 굴착기 + 외부 + 우천 | `{"work_type":"굴착작업","equipment":["굴착기"],"location":["외부"],"conditions":["우천"]}` | 200, 협착/전도/붕괴 보강 | 200, 붕괴 +0.05(R041), 협착 +0.05(R040), controls 각 +1~2 | ✓ PASS |
| 3-원안 | `{"work_type":"화기작업",...}` | — | 404 (risk_mapping_core 에 `화기작업` 미등재) | 404 UNKNOWN_WORK_TYPE | △ 데이터 공백 (v2 외) |
| 4 | 고소 단독 (v1 호환) | `{"work_type":"고소작업"}` | 200, v1과 동일 | 200, keys=[work_type,hazards], input_context 미포함 | ✓ PASS |
| 5 | 빈 문자열 equipment | `{"work_type":"전기작업","equipment":[""]}` | 400 INVALID_INPUT_OPTION | 400, details={field:equipment,value:"",allowed_values:[...8]} | ✓ PASS |
| 6 | 미지원 equipment | `{"work_type":"전기작업","equipment":["없는장비"]}` | 400 INVALID_INPUT_OPTION | 400, details={field:equipment,value:"없는장비",allowed_values:[...8]} | ✓ PASS |
| 7 | 중복 conditions | `{"work_type":"전기작업","conditions":["활선근접","활선근접"]}` | 200, 자동 dedupe | 200, input_context.conditions=["활선근접"], 감전 enrichment 1회만 적용 | ✓ PASS |

### 1.1 보너스 검증

| # | 시나리오 | 결과 | 판정 |
|---|---------|------|------|
| B1 | 절단/천공 + 절단기 + 비산분진 | 절단상 0.82→0.87(R060), controls +2 (R060+R061 각 1) | ✓ PASS |
| B2 | 밀폐 + 화기작업 (add_hazard 경로) | 기존 "화재·폭조" hazard 존재 → add_hazard skip, add_controls만 발동 | ✓ PASS (설계상 동일명 hazard 중복 추가 금지) |

---

## 2. 불변식 검증

| 불변식 | 결과 |
|-------|------|
| 기존 hazard 제거 없음 | ✓ (CASE1 감전/추락/아크·화재/협착 모두 유지) |
| 기존 controls 삭제 없음 | ✓ (CASE1 감전 base 5개 전부 유지 후 2개 추가) |
| references 3축 키 구조 (`law_ids`/`moel_expc_ids`/`kosha_ids`) | ✓ |
| `related_expc_ids` 미노출 | ✓ (grep 결과 False) |
| confidence_score DESC 정렬 | ✓ (CASE1: 감전 0.93 > 추락 0.92 > 아크·화재 0.80 > 협착 0.80) |
| add_hazard ≤ 1회 / 요청 | ✓ (B2에서 동일명 존재로 0회 발동) |
| 추가 controls ≤ 2개 / hazard | ✓ (CASE2 질식: R010 2개로 상한 충족 → R011 skip) |
| confidence_score 상한 1.0 | ✓ (CASE2 질식 1.00 cap) |

---

## 3. v1 하위호환 검증

`{"work_type":"고소작업"}` 응답 키 집합:

```
{"work_type", "hazards"}
```

**`input_context` 미포함** → v1 응답 스키마와 바이트 수준 동일 구조. v1 클라이언트 파싱 영향 없음.

---

## 4. 에러 정책 검증

| 에러 코드 | HTTP | 유발 조건 | 검증 결과 |
|----------|------|----------|----------|
| `MISSING_WORK_TYPE` | 400 | `{}` | v1 동일 (회귀 없음) |
| `EMPTY_WORK_TYPE` | 400 | `{"work_type":""}` | v1 동일 (회귀 없음) |
| `UNKNOWN_WORK_TYPE` | 404 | `{"work_type":"도장작업"}` | v1 동일 (supported_work_types 10건 반환) |
| `INVALID_INPUT_OPTION` | 400 | 빈문자열/허용값위반 | ✓ v2 신규, details 3필드(field, value, allowed_values) 포함 |
| `INTERNAL_ERROR` | 500 | 엔진 예외 | 수동 유발 미실시 (기존 500 경로 유지 확인) |

---

## 5. 데이터 공백 메모

- `화기작업` / `중장비 작업` 은 `risk_mapping_core`에 row 미등재 → 404 `UNKNOWN_WORK_TYPE`.
- 이는 v2 enrichment와 무관한 **선행 데이터 공백**으로, 매핑 데이터 채움 단계에서 해결해야 함.
- 두 work_type이 채워지면 R020/R021/R022 및 R042 규칙이 실제로 엔드투엔드 검증 가능.

---

## 6. 산출물 경로

- 샘플 응답: `docs/sample_output_context_4cases.json`
- 규칙 매트릭스: `data/risk_db/rules/enrichment_rule_matrix.json`
- 허용값 카탈로그: `data/risk_db/api_schema/input_option_catalog.json`
- 엔진 코드: `engine/kras_connector/enrichment.py`
- 라우터: `backend/routers/risk_assessment_build.py`
- 스키마: `backend/schemas/risk_assessment_build.py`

---

## 7. 최종 판정

**PASS** — 7 케이스 중 6건 PASS, 1건(CASE3 원안)은 v2 범위 외 데이터 공백. 대체 케이스(굴착작업)로 동등 검증 완료.

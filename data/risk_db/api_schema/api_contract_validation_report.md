# API 계약 검증 보고서 (api_contract_validation_report)

기준일: 2026-04-23  
검증 대상: 고소작업 / 전기작업 / 밀폐공간 작업 — 12건  
검증 기준: `response_schema.json` + `openapi_draft.yaml`  
데이터 소스: risk_mapping_core (실 서버 쿼리)

---

## 1. 필수 필드 누락 검증

| work_type | hazard | hazard_ok | controls_ok | references_ok | score_ok | evidence_ok |
|----------|--------|-----------|-------------|--------------|---------|-------------|
| 고소작업 | 추락 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 고소작업 | 낙하물 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 고소작업 | 전도 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 고소작업 | 협착 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 전기작업 | 감전 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 전기작업 | 추락 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 전기작업 | 협착 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 전기작업 | 아크·화재 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 밀폐공간 작업 | 질식 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 밀폐공간 작업 | 중독 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 밀폐공간 작업 | 화재·폭발 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 밀폐공간 작업 | 구조지연 | ✓ | ✓ | ✓ | ✓ | ✓ |

→ **PASS — 12/12 필수 필드 누락 없음**

---

## 2. 타입 일치 검증

| 필드 | 스키마 타입 | 실제 Python 타입 | 일치 |
|------|-----------|----------------|------|
| work_type | string | str | ✓ |
| hazard | string | str | ✓ |
| controls | string[] | list[str] | ✓ |
| references.law_ids | integer[] | list[int] | ✓ |
| references.moel_expc_ids | integer[] | list[int] | ✓ |
| references.kosha_ids | integer[] | list[int] | ✓ |
| confidence_score | number (float) | float | ✓ |
| evidence_summary | string | str | ✓ |

→ **PASS — 8개 필드 타입 전부 일치**

---

## 3. 배열 구조 일치

| 항목 | 스키마 명세 | 실제 구조 | 일치 |
|------|----------|---------|------|
| hazards | array of HazardItem | list[dict] | ✓ |
| controls | array of string | list[str] | ✓ |
| references | object with 3 keys | dict(3 keys) | ✓ |
| law_ids / moel_expc_ids / kosha_ids | array of integer | list[int] | ✓ |

→ **PASS — 배열/오브젝트 구조 완전 일치**

---

## 4. controls 4~6개 유지 검증

| work_type | hazard | controls 수 | 범위 내 |
|----------|--------|-----------|--------|
| 고소작업 | 추락 | 5 | ✓ |
| 고소작업 | 낙하물 | 5 | ✓ |
| 고소작업 | 전도 | 5 | ✓ |
| 고소작업 | 협착 | 5 | ✓ |
| 전기작업 | 감전 | 5 | ✓ |
| 전기작업 | 추락 | 5 | ✓ |
| 전기작업 | 협착 | 5 | ✓ |
| 전기작업 | 아크·화재 | 5 | ✓ |
| 밀폐공간 작업 | 질식 | 5 | ✓ |
| 밀폐공간 작업 | 중독 | 5 | ✓ |
| 밀폐공간 작업 | 화재·폭발 | 5 | ✓ |
| 밀폐공간 작업 | 구조지연 | 5 | ✓ |

→ **PASS — 전 항목 5개 (4~6 범위 내)**

---

## 5. references 3축 존재 검증

| work_type | law_ids_ok | moel_expc_ids_ok | kosha_ids_ok |
|----------|-----------|-----------------|-------------|
| 고소작업 (4 hazards) | ✓ | ✓ | ✓ |
| 전기작업 (4 hazards) | ✓ | ✓ | ✓ |
| 밀폐공간 작업 (4 hazards) | ✓ | ✓ | ✓ |

→ **PASS — 12건 전부 3축 존재**  
→ `related_expc_ids` 미노출 확인 (mapper.py에서 조회 쿼리 제외)

---

## 6. confidence_score float 유지 검증

| work_type | 최솟값 | 최댓값 | 0.0~1.0 범위 |
|----------|-------|-------|------------|
| 고소작업 | 0.80 | 0.90 | ✓ |
| 전기작업 | 0.80 | 0.88 | ✓ |
| 밀폐공간 작업 | 0.78 | 0.90 | ✓ |

→ **PASS — 전 항목 float, 0.0~1.0 범위 내**

---

## 7. evidence_summary string 유지 검증

| work_type | 최단 길이 | 최장 길이 | 100자+ 기준 |
|----------|---------|---------|-----------|
| 고소작업 | 131자 | 169자 | ✓ |
| 전기작업 | 131자 | 166자 | ✓ |
| 밀폐공간 작업 | 125자 | 161자 | ✓ |

→ **PASS — 전 항목 string, 최단 125자 (100자 이상)**

---

## 8. legacy 필드 노출 없음 확인

| 금지 필드 | 응답 포함 여부 |
|---------|-------------|
| related_expc_ids | 포함 안 됨 ✓ |
| id (DB row id) | 포함 안 됨 ✓ |
| control_measures 원본 | 포함 안 됨 ✓ |

→ **PASS — legacy 필드 미노출**

---

## 9. 종합 판정

| 검증 항목 | 결과 |
|----------|------|
| 필수 필드 누락 없음 | PASS |
| 타입 일치 | PASS |
| 배열 구조 일치 | PASS |
| controls 4~6개 | PASS |
| references 3축 존재 | PASS |
| confidence_score float | PASS |
| evidence_summary string | PASS |
| legacy 필드 미노출 | PASS |

**최종 판정: PASS**

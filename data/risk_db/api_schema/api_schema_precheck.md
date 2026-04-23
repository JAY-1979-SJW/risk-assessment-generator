# API 스키마 설계 사전 확인 (api_schema_precheck)

기준일: 2026-04-23  
기준 소스: `engine/kras_connector/mapper.py :: build_risk_assessment()`

---

## 1. build_risk_assessment() 반환 구조

```python
{
    "work_type": str,          # 입력값 그대로 반환 (정규화 후)
    "hazards": list[dict]      # confidence_score DESC 정렬, 빈 배열 가능
}
```

hazards 배열 내부 각 원소:
```python
{
    "hazard": str,             # risk_mapping_core.hazard
    "controls": list[str],     # control_measures['measures'] 파싱 결과
    "references": {
        "law_ids":        list[int],   # related_law_ids
        "moel_expc_ids":  list[int],   # related_moel_expc_ids (related_expc_ids 금지)
        "kosha_ids":      list[int],   # related_kosha_ids
    },
    "confidence_score": float, # 0.0~1.0 (DB: NUMERIC → Python float 변환)
    "evidence_summary": str,   # 공백 가능 (WARN 로그 발화 조건: 100자 미만)
}
```

---

## 2. hazards 배열 내부 필드 구성

| 필드 | Python 타입 | 필수 여부 | 비고 |
|------|-----------|---------|------|
| hazard | str | 필수 | None이면 해당 row 스킵 |
| controls | list[str] | 필수 | 비어있으면 WARN, 빈 배열로 반환 |
| references | dict | 필수 | 하위 3개 키 항상 존재 |
| confidence_score | float | 필수 | 파싱 실패 시 0.0 |
| evidence_summary | str | 필수 | 빈 문자열 가능 |

---

## 3. references 하위 구조

| 키 | 타입 | DB 원본 컬럼 | 금지 컬럼 |
|----|------|------------|---------|
| law_ids | list[int] | related_law_ids | — |
| moel_expc_ids | list[int] | related_moel_expc_ids | related_expc_ids |
| kosha_ids | list[int] | related_kosha_ids | — |

→ **`related_expc_ids` 절대 노출 금지** — legacy 컬럼, API 응답에서 완전 배제

---

## 4. confidence_score / evidence_summary 타입

| 필드 | DB 타입 | Python 타입 | JSON 타입 | 범위 |
|------|--------|-----------|---------|------|
| confidence_score | NUMERIC(3,2) | float | number | 0.00~1.00 |
| evidence_summary | TEXT | str | string | 최소 100자 (현재 DB) |

---

## 5. 필수/선택 필드 구분

### 엔진 출력 → API 응답 매핑

| 엔진 필드 | API 응답 필드 | 필수/선택 | 기본값 |
|---------|------------|---------|------|
| work_type | work_type | 필수 | — |
| hazards | hazards | 필수 | [] (미등록 시) |
| hazard | hazard | 필수 | — |
| controls | controls | 필수 | [] |
| references.law_ids | references.law_ids | 필수 | [] |
| references.moel_expc_ids | references.moel_expc_ids | 필수 | [] |
| references.kosha_ids | references.kosha_ids | 필수 | [] |
| confidence_score | confidence_score | 필수 | 0.0 |
| evidence_summary | evidence_summary | 필수 | "" |

### 엔진 내부 전용 (API 노출 금지)

| 엔진 내부 | 이유 |
|---------|------|
| id (DB row id) | 내부 식별자 |
| related_expc_ids | legacy 컬럼 |
| control_measures 원본 JSONB | 가공 전 원시 데이터 |

---

## 6. 미등록 work_type 처리 정책

엔진 현재 동작:
```python
if not rows:
    return {'work_type': wt, 'hazards': []}  # 빈 배열 반환, 예외 없음
```

API 계약 정책:
- `hazards` 배열이 비어있으면 **404 UNKNOWN_WORK_TYPE** 반환
- 엔진 내부에서 빈 배열로 반환해도 API 계층에서 404로 변환
- 엔진 코드 수정 없이 API 라우터에서 처리

---

## 7. 확정 사항

- 필드명: 엔진 출력과 완전 동일 (`snake_case` 유지)
- 추가 필드: 없음 (이번 단계)
- reserved 필드: `top_k` (향후 필터용, 현재 미구현)
- 정규화: 없음 (엄격 일치 — work_type 대소문자 구분)

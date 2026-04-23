# POST /api/v1/risk-assessment/build — Request v2 확장 계약

**상태**: v2 설계 (AI 미연동, 정규화 선택형 입력만 처리)
**기준 버전**: v1 (`openapi_draft.yaml`)
**하위호환**: 100% (work_type 단독 요청 = v1 응답과 의미 동일)

---

## 1. 요청 바디 필드

| 필드 | 타입 | 필수 | v1/v2 | 제약 |
|------|------|------|-------|------|
| `work_type` | string | ✓ | v1 | 등록된 10개 작업 유형과 완전 일치 |
| `equipment` | string[] | — | **v2 신규** | 허용값 whitelist 준수, 빈 문자열 금지, 중복 제거 |
| `location` | string[] | — | **v2 신규** | 허용값 whitelist 준수, 빈 문자열 금지, 중복 제거 |
| `conditions` | string[] | — | **v2 신규** | 허용값 whitelist 준수, 빈 문자열 금지, 중복 제거 |

### 1.1 work_type (v1 유지)

- v1 정책 동일. 등록된 10개 작업 유형과 완전 일치(대소문자/공백 차이 없음).
- 미등록 → 404 `UNKNOWN_WORK_TYPE`.
- 누락 → 400 `MISSING_WORK_TYPE`, 빈값 → 400 `EMPTY_WORK_TYPE`.

### 1.2 equipment / location / conditions (v2 신규)

- 세 필드 모두 **optional**. 생략 시 v1 동작과 동일.
- 타입: JSON array of string. `null` 허용 금지.
- 각 원소:
  - 비어있지 않은 문자열 (trim 후 길이 ≥ 1)
  - `input_option_catalog.json`의 해당 카테고리 whitelist에 존재해야 함
- 배열 내부 중복은 서버 측 **자동 dedupe** (순서 보존, WARN 없음)
- 배열 자체가 `[]` (빈 배열)인 경우: 생략과 동일 취급 (규칙 미적용)
- 대소문자 및 NFC 정규화 적용 (`_clean` 함수 재사용)

---

## 2. 입력 검증 순서 (라우터 내부)

```
1. body is dict? → else 400 MISSING_WORK_TYPE (v1 유지)
2. work_type 존재 / 빈값 검증 → 400 MISSING/EMPTY (v1 유지)
3. equipment/location/conditions 각 필드:
   a. 필드 존재 + None 아님 → array 타입 검증
   b. 원소별 공백/빈값 검증 → 400 INVALID_INPUT_OPTION
   c. 원소별 whitelist 검증  → 400 INVALID_INPUT_OPTION
   d. dedupe (순서 보존)
4. work_type → 기본 결과 조회 (mapper.build_risk_assessment)
5. 결과 없음 → 404 UNKNOWN_WORK_TYPE (v1 유지)
6. enrichment 규칙 적용 (equipment/location/conditions → hazard 보강)
7. 응답에 input_context 필드 부가
```

---

## 3. 응답 확장

### 3.1 새 필드: `input_context` (optional)

- **노출 조건**: equipment/location/conditions 중 1개 이상 전달된 경우에만 응답에 포함
- work_type 단독 요청: `input_context` 필드 **미포함** → v1 응답과 바이트 단위로 동일
- 구조:
  ```json
  {
    "input_context": {
      "equipment":  ["사다리"],
      "location":   ["옥상"],
      "conditions": ["활선근접"]
    }
  }
  ```
- dedupe 및 whitelist 통과한 정규화 결과를 그대로 반환
- 빈 배열 필드는 포함되나 `[]` 값으로 반환

### 3.2 hazards 구조 (v1 유지)

- `hazard`, `controls`, `references{law_ids, moel_expc_ids, kosha_ids}`, `confidence_score`, `evidence_summary` 모두 **v1 그대로**.
- enrichment는 아래만 수정 가능:
  - `controls` 리스트 말미에 규칙 기반 조치 추가 (hazard당 최대 2개)
  - `confidence_score` 상향 조정 (+0.05, 상한 1.0 — rulebook 기록 사항만)
  - `evidence_summary` 말미에 `" [조건 반영: {사유}]"` 구문 추가 (선택)
  - hazards 배열 재정렬 (confidence 변경 후 DESC 재정렬)
  - hazards 신규 추가 (최대 1개 / hazard당 최대 2 controls)
- **금지**:
  - 기존 hazard 제거/수정
  - 기존 controls 삭제
  - references ID 추가/삭제 (이번 단계는 DB 참조 불변)
  - related_expc_ids 노출

---

## 4. 하위호환 보장

| 시나리오 | v1 응답 | v2 응답 | 동일 여부 |
|---------|---------|---------|----------|
| `{"work_type":"전기작업"}` | hazards 배열 | hazards 배열 (input_context 미포함) | ✓ 바이트 동일 |
| `{"work_type":"전기작업","equipment":[]}` | — | hazards 배열 (input_context 미포함) | ✓ 의미 동일 |
| `{"work_type":"전기작업","equipment":["사다리"]}` | — | hazards + input_context + 보강 | v2 전용 |

> **규칙**: v2 신규 3개 필드가 모두 `None` 또는 `[]`인 경우, 라우터는 v1 경로와 동일하게 동작하고 응답도 v1과 동일하게 생성한다 (`input_context` 미부가).

---

## 5. 에러 코드 목록 (v2 확장)

| code | HTTP | 의미 | v1/v2 |
|------|------|------|-------|
| `MISSING_WORK_TYPE` | 400 | work_type 누락 | v1 |
| `EMPTY_WORK_TYPE` | 400 | work_type 빈값 | v1 |
| `UNKNOWN_WORK_TYPE` | 404 | 미등록 작업유형 | v1 |
| `INVALID_INPUT_OPTION` | 400 | equipment/location/conditions 허용값 위반 | **v2 신규** |
| `INTERNAL_ERROR` | 500 | 내부 오류 | v1 |

### INVALID_INPUT_OPTION 응답 규격

```json
{
  "error": {
    "code": "INVALID_INPUT_OPTION",
    "message": "입력 옵션이 허용되지 않은 값입니다.",
    "details": {
      "field": "equipment",
      "value": "없는장비",
      "allowed_values": ["사다리","이동식비계","고소작업대","전동공구","절단기","용접기","크레인","굴착기"]
    }
  }
}
```

- `field`: 위반 필드명 (`equipment` | `location` | `conditions`)
- `value`: 위반 원소 값 (빈 문자열이면 `""`)
- `allowed_values`: 해당 카테고리 전체 허용값 (참조용)

---

## 6. 금지 사항 재확인

- mapper.py 기본 조회 로직 수정 금지
- risk_mapping_core DB 스키마 변경 금지
- related_expc_ids 노출 금지
- AI 연동 금지
- 자유문장 해석 금지 (whitelist 불일치 → 400)

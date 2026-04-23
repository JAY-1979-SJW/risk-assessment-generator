# 위험도 산정 규칙 (Risk Scoring Rule) — v1

**대상**: `engine/kras_connector/table_builder.py`
**용도**: v2 API 결과 → 현장 제출용 위험성평가표 row 변환 시 위험도 계산
**원칙**: 임의 계산 금지. 규칙 기반 결정론적 변환만 수행.

---

## 1. current_risk — confidence_score → 3단계

| confidence_score 범위 | current_risk |
|---------------------|-------------|
| ≥ 0.90 | **High** |
| 0.80 ~ 0.8999 | **Medium** |
| < 0.80 | **Low** |

경계 처리: `>=` 기준. 정확히 0.90 → High. 정확히 0.80 → Medium.

### 근거

- v2 risk_mapping_core의 `confidence_score`는 해당 hazard가 work_type에 대해 매핑된 **신뢰도/적합도**를 의미.
- 고신뢰(0.9+)는 산안기준규칙에 직접 명시된 조문으로 뒷받침되는 고빈도·고중대성 위험요인.
- 중신뢰(0.8~0.89)는 법령·해석례·KOSHA 자료로 간접 뒷받침되는 위험요인.
- 저신뢰(<0.8)는 부가적·상황 의존적 위험요인.

산업안전보건법상 위험성평가는 가능성×중대성 방식이 일반적이나, 본 1차 구현은 **DB의 confidence_score 하나만** 신뢰 가능한 축으로 삼아 결정론적으로 변환. 가능성/중대성 분리는 후속 단계(v3)에서 도입 예정.

---

## 2. residual_risk — 조치 후 1단계 감소

| current_risk | residual_risk |
|-------------|---------------|
| High | Medium |
| Medium | Low |
| Low | Low |

### 근거

- 표준 위험성평가 관행: 법령에서 요구하는 필수 안전조치를 적용하면 **한 단계** 위험이 감소한다고 가정.
- v2 API는 모든 hazard에 대해 최소 1개 이상 control_measures를 반환하므로 "조치 적용됨" 가정 성립.
- control 개수·품질에 따라 감소 폭을 달리하는 로직은 본 버전에서 **도입하지 않음** (임의 계산 금지 원칙).

### 특수 케이스

- hazard의 `controls`가 비어 있는 경우 → residual_risk = current_risk (감소 없음).
  - 현 v2 DB 상 발생하지 않음. 엔진 측 안전장치로만 유지.

---

## 3. control_measures — 상위 N개 제한

- **N = 7** (스키마상 `maxItems: 7`).
- API가 반환한 `controls` 배열 순서를 **보존**하여 앞에서부터 N개만 잘라 낸다.
- 순서에는 의미가 있음:
  - 원본(risk_mapping_core)이 중요도 순 또는 법령 순으로 정렬된 상태.
  - v2 enrichment가 조건 기반 조치를 **말미에 append**.
- N개를 초과하는 경우 enrichment 조치가 잘려 나갈 수 있으나, v2 규칙 제약상 enrichment 추가 controls는 hazard당 최대 2개이며 원본이 5~6개 수준이라 실질 손실은 드묾.

### 절삭 시 표기

- 별도 "..외 N건" 주석 없음. 단순 절삭. 필요 시 후속 버전에서 추가.

---

## 4. process — 작업 세부 단계

- 1차 구현: **`process = work_type`** (API가 sub-process를 제공하지 않음).
- 모든 row가 동일 process 값을 갖더라도 표 구조 일관성 유지.
- v2 input_context(equipment/location/conditions)는 **process에 포함하지 않음** — 표 헤더 레벨 정보로 응용 계층에서 별도 표기.
- 향후 API가 process/sub_work를 반환하는 시점(`/api/v1/ra/draft` 등)에 세분화.

---

## 5. references_summary — 근거 축약

입력 재료:
- `evidence_summary` (문자열, 대개 1~3 문장)
- `references.{law_ids, moel_expc_ids, kosha_ids}` (정수 배열)

### 생성 규칙

1. `evidence_summary` 앞부분에서 **첫 온전한 문장**을 추출 (40~140자 범위, `". "` 또는 `".\n"`를 경계로).
2. 140자 초과 시 하드 절삭 + `…`.
3. 문장이 비어 있으면 빈 문자열.
4. 말미에 `" [법령 N건 · 해석례 N건 · KOSHA N건]"` 형식의 3축 건수 요약 부착.
   - 세 개 모두 0건이면 `" [참조 없음]"`.
5. enrichment가 추가한 `" [조건 반영: ...]"` 태그는 **첫 문장 추출 과정에서 자연 탈락** (1차 문장 이후에 위치).

### 예시

입력 evidence:
```
산안기준규칙 제321조(충전전로에서의 전기작업), 제302조(접지), 제304조(누전차단기) 직접 명시. moel_expc: 고압전선 전기재해 예방시설 안전관리비 해석례(24363). KOSHA 건물관리업 사고사망재해 사례집(35222). [조건 반영: 활선근접 조건]
```
references:
```
law_ids: [17109, 17088, 17090]
moel_expc_ids: [24363, 28709, 28708]
kosha_ids: [35222, 35237, 1726]
```

출력:
```
산안기준규칙 제321조(충전전로에서의 전기작업), 제302조(접지), 제304조(누전차단기) 직접 명시. [법령 3건 · 해석례 3건 · KOSHA 3건]
```

---

## 6. 데이터 왜곡 방지 체크리스트

- hazard 명을 변경하지 않는다.
- controls 문자열을 수정하지 않는다 (절삭만 허용).
- references ID 값을 가공하지 않는다 (건수만 요약에 사용).
- confidence_score → level 변환은 위 표 외 어떤 스무딩·보간도 수행하지 않는다.

---

## 7. 버전

- v1 (본 문서) — 2026-04-23 1차 도입. 3단계 risk level.
- 향후: 가능성·중대성 2축 세분화, controls 품질 가중치 기반 residual 세분화.

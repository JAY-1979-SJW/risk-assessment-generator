# Risk Assessment Table Builder — Validation Report

**대상**: `engine/kras_connector/table_builder.py`
**입력 기반**: `docs/sample_output_context_4cases.json` (v2 API 실서버 응답 스냅샷)
**출력**: `docs/sample_table_output.json`
**검증 시점**: 2026-04-23

---

## 1. 검증 매트릭스 (4 케이스 자동 체크)

| 케이스 | hazards→rows | 순서 보존 | confidence DESC | controls ≤ 7 | controls 비어있지 않음 | refs_summary 존재 | current_risk 매핑 | residual_risk 매핑 |
|--------|------------|---------|---------------|-------------|-------------------|----------------|-----------------|------------------|
| 1. 전기+사다리+옥상+활선근접 | 4→4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 2. 밀폐+맨홀+밀폐공간 | 4→4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3-대체. 굴착+굴착기+외부+우천 | 4→4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 4. 고소 legacy 단독 | 4→4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## 2. 샘플 출력 품질 리뷰

### 2.1 CASE 1 (전기작업 + 사다리 + 옥상 + 활선근접)

```
process=전기작업
rows:
  감전          current=High   residual=Medium  controls=7
  추락          current=High   residual=Medium  controls=7
  아크·화재     current=Medium residual=Low     controls=5
  협착          current=Medium residual=Low     controls=5
```

- 감전 controls 7건 = 원본 5건 + enrichment R001 2건 (상한 도달) ✓
- 추락 controls 7건 = 원본 5건 + enrichment R002/R003 2건 (상한 도달) ✓
- 원본에 없던 hazard 신규 생성 0건 → 데이터 왜곡 없음 ✓
- references_summary 첫 문장에 법령 조문명 명시 → 현장 제출 적합 ✓

### 2.2 CASE 2 (밀폐공간 작업 + 맨홀 + 밀폐공간)

```
rows:
  질식          current=High   residual=Medium  controls=7
  중독          current=Medium residual=Low     controls=5
  화재·폭발     current=Medium residual=Low     controls=5
  구조지연      current=Low    residual=Low     controls=5
```

- 질식 confidence 1.00 (cap) → High → residual Medium ✓
- 구조지연 confidence 0.78 → Low → residual Low (감소 없음) — 규칙 표와 일치 ✓

### 2.3 CASE 4 (고소작업 legacy 단독)

```
rows:
  추락     current=High   residual=Medium  controls=5
  낙하물   current=Medium residual=Low     controls=5
  전도     current=Medium residual=Low     controls=5
  협착     current=Medium residual=Low     controls=5
```

- API 응답에 `input_context` 없음 → table 출력도 process=work_type으로 단일 ✓
- enrichment 미적용 확인: controls=5 (원본 그대로) ✓

---

## 3. 불변식 및 정합성

| 불변식 | 결과 |
|-------|------|
| 모든 hazard가 row에 반영됨 (누락 없음) | ✓ 4개 케이스 전부 매칭 |
| hazard 문자열 원본 보존 | ✓ 비교 일치 |
| controls 문자열 변경 없음 (절삭만 허용) | ✓ MAX=7 이내 |
| references ID 건수 요약만 사용 (원본 값 노출 없음) | ✓ `[법령 N건 · 해석례 N건 · KOSHA N건]` 형식 |
| 정렬: confidence_score DESC → row 순서 유지 | ✓ 4케이스 전부 |
| input_context가 있어도 table 출력 구조 확장 없음 (schema 고정) | ✓ keys=[work_type, rows] |

---

## 4. 위험도 계산 일관성

| confidence_score | 기대 level | 샘플 관측 |
|-----------------|-----------|----------|
| 1.00 (CASE2 질식) | High | High ✓ |
| 0.93 (CASE1 감전) | High | High ✓ |
| 0.92 (CASE1 추락) | High | High ✓ |
| 0.90 (CASE4 추락) | High | High ✓ |
| 0.88 (CASE4 낙하물) | Medium | Medium ✓ |
| 0.85 (CASE4 전도) | Medium | Medium ✓ |
| 0.80 (CASE1 협착) | Medium | Medium ✓ |
| 0.78 (CASE2 구조지연) | Low | Low ✓ |

residual: High→Medium, Medium→Low, Low→Low — 100% 일치.

---

## 5. API 결과와의 의미 정합

| 항목 | API 결과 필드 | 표 필드 | 일치 여부 |
|------|-------------|--------|---------|
| 작업 유형 | `work_type` | `work_type`, `process` | ✓ 동일 값 |
| 위험요인 명 | `hazards[].hazard` | `rows[].hazard` | ✓ 동일 |
| 안전조치 | `hazards[].controls` | `rows[].control_measures` | ✓ 상위 N개 절삭, 순서 보존 |
| 법적 근거 | `hazards[].evidence_summary` + `references` | `rows[].references_summary` | ✓ 요약 + 건수 표기 |
| 신뢰도 | `hazards[].confidence_score` (수치) | `rows[].current_risk` (High/Medium/Low) | ✓ 결정론적 변환 |

**의미 왜곡 없음** — 표 변환은 순수 함수로, API 결과가 동일하면 항상 동일한 표가 생성됨.

---

## 6. 한계 및 후속 작업

- `process`가 `work_type` 그대로 → 모든 row가 동일 값. 실제 위험성평가표는 작업 세부 단계(sub_work) 분해가 필요하나 현 API 미제공.
- `residual_risk`는 단순 1단계 감소. control 개수·품질 기반 세분화 미구현.
- `references_summary` 내 첫 문장 추출은 `". "` 경계 기준 — Korean 구조체에서 대체로 작동하나 예외 케이스(괄호 내 period 등) 존재 가능성.

---

## 7. 최종 판정

**PASS** — 표 구조·위험도 계산·4 케이스 출력 모두 자연스러움 및 정합성 확보. 데이터 왜곡 없음.

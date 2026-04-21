# recommend / recalculate 출력 안정화 (14단계)

## 목적

운영 연결 전 추천 엔진 출력 기준선 고정.  
동일 입력에 동일 결과, generic-law fallback 후순위 고정, hazard/control evidence 역할 분리.

---

## 안정화 전 문제 요약

| 문제 | 설명 |
|------|------|
| non-deterministic tie-break | 동점 law가 있을 때 dict 삽입 순서에 의존 → 이론상 불안정 |
| generic-law top 점유 가능 | worktype-only law가 control-specific law보다 먼저 나올 수 있었음 |
| recalculate max_laws 불일치 | `recalculate`가 `max_laws_per_row=3` 하드코딩, 요청 옵션 무시 |
| hazard/control evidence 미분리 | evidence_paths 필드 존재했으나 정렬 반영 안 됨 |
| RecalculateOptions 누락 필드 | `max_laws_per_row` 없어 클라이언트가 조절 불가 |

---

## 출력 기준 고정 내용

### A. evidence type 우선순위 (정렬 tier)

| tier | 조건 | 설명 |
|------|------|------|
| 0 | `evidence_paths`에 `control_law` 포함 | control-specific (가장 관련성 높음) |
| 1 | `hazard_law` 포함, `control_law` 없음 | hazard-specific |
| 2 | `worktype_law`만 존재 | generic fallback |

### B. deterministic 정렬 키

```python
candidates.sort(key=lambda x: (_ev_priority(x["evidence_paths"]), -x["law_score"], x["law_id"]))
```

우선순위: evidence tier ASC → score DESC → law_id ASC (알파벳 tie-break, 완전 stable)

### C. generic-law cap

| 상황 | 최대 generic-law 수 |
|------|---------------------|
| specific law 존재 (tier 0/1) | 1개 |
| specific law 없음 (fallback) | 2개 |

### D. row당 law 수 기준

- `recommend`: `RecommendOptions.max_laws_per_row` (기본 3, 최대 10)
- `recalculate`: `RecalculateOptions.max_laws_per_row` (기본 3, 최대 10) ← 신규 추가

### E. recommend / recalculate 기준 통합

`recalculate`에 `max_laws_per_row` 파라미터 추가, 라우터에서 옵션 전달.  
두 경로 모두 동일한 `_merge_law_evidence()` 함수를 동일 정렬 기준으로 호출.

---

## hazard / control evidence 분리 기준

- `control_law` path = 특정 control_code와 직접 매핑된 근거 → control evidence
- `hazard_law` path = 위험 유형 자체와 매핑된 근거 → hazard evidence
- `worktype_law` path = 작업 유형 수준 근거 → generic fallback

정렬 순서가 이 역할 분리를 자동으로 구현: control evidence가 앞, generic이 뒤.

---

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/services/risk_assessment_engine.py` | `_merge_law_evidence` 정렬 기준 고정, generic cap 추가, recalculate 파라미터 정렬 |
| `backend/schemas/risk_assessment_draft.py` | `RecalculateOptions.max_laws_per_row` 추가 |
| `backend/routers/risk_assessment_draft.py` | recalculate 호출에 `max_laws_per_row` 전달 |
| `engine/kras_connector/tests/test_regression_stability.py` | 회귀 테스트 22개 신규 추가 |

프론트엔드 미수정 / DB migration 없음 / response schema 무변경 (LawInfo 필드 동일)

---

## 전체 안정화 지표

| 지표 | 결과 |
|------|------|
| 반복 호출 일치율 (3회) | **100%** |
| recommend / recalculate 일치율 | **100%** |
| generic-law top1 점유율 | **0%** (전 worktype) |
| 회귀 테스트 | **22/22 PASS** |

---

## worktype별 지표 (max_laws=3, max_hazards=5)

| worktype | rows | ctrl/row | law/row | control-specific% | generic% |
|----------|------|----------|---------|-------------------|----------|
| ELEC_LIVE | 1 | 3.0 | 3.0 | 67% | 0% |
| TEMP_SCAFF | 3 | 3.0 | 3.0 | 56% | 0% |
| LIFT_RIGGING | 3 | 3.0 | 3.0 | 67% | 0% |
| WELD_ARC | 3 | 3.0 | 3.0 | 67% | 0% |
| CIVIL_EXCAV | 1 | 3.0 | 3.0 | 33% | 0% |
| STEEL_LIFT | 1 | 3.0 | 3.0 | 67% | 0% |

CIVIL_EXCAV의 33% — 해당 hazard에 control_law 매핑이 적어 hazard-only law 비중이 높음. fallback 없이 hazard evidence로 채워진 것이므로 정상.

---

## 회귀 테스트 시나리오 목록

| 테스트 | 검증 항목 | 결과 |
|--------|-----------|------|
| repeat × 4 worktypes | 3회 반복 law 순서 동일 | PASS |
| recommend/recalculate align × 3 | 동일 입력 결과 일치 | PASS |
| generic_not_top1 × 3 | specific 있을 때 top1 non-generic | PASS |
| generic_cap_with_specific | max 1 generic when specific exist | PASS |
| control_before_hazard × 2 | control-specific → hazard → generic 순서 | PASS |
| law_count_cap × 3 | max_laws_per_row 상한 준수 | PASS |
| fallback_generic | specific 없을 때 generic 최대 2 | PASS |
| recalculate_max_laws | max_laws_per_row=2 recalculate 적용 | PASS |
| hazard_rows_generated × 4 | 최소 row 수 생성 | PASS |

---

## 남은 한계

- `law_category=expc` (해석례) 비율이 높은 hazard (FALL, ELEC)에서 해석례가 판례 대신 근거로 등장할 수 있음 — 법령 source 품질 문제로 15단계 보강 대상
- DUST / FIRE / EXPLO 일부 hazard는 control_law 매핑이 없어 control-specific 비율 낮음
- `hazard_law` path만 있는 경우 hazard evidence인지 control evidence인지 UI에서 구분 불가 (내부 tier는 구분되나 LawInfo 필드에 미노출 — 필요 시 15단계에서 `evidence_type` 필드 추가 검토)

---

## 15단계 운영 연결 전 체크포인트

- [ ] DUST / FIRE / EXPLO control_law 매핑 보강
- [ ] law_category별 신뢰도 weight 조정 검토
- [ ] LawInfo에 `evidence_type` 노출 여부 결정
- [ ] 운영 서버 배포 전 동일 테스트 재실행

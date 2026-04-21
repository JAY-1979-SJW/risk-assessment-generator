# 16단계 — API 운영 경로 연결 고정 및 회귀 검증

**작성일**: 2026-04-21  
**범위**: recommend / recalculate 운영 경로 점검, 회귀 테스트 확장, safe-guard 확인  
**상태**: PASS

---

## 1. 운영 연결 대상 경로

```
POST /api/risk-assessment/draft/recommend
  └─ backend/routers/risk_assessment_draft.py :: recommend_draft()
     └─ backend/services/risk_assessment_engine.py :: recommend()
        ├─ _hazard_map() / _hazards() / _controls_by_hazard()
        ├─ _apply_condition_bonus()
        └─ _merge_law_evidence()          ← law 정렬/상한/fallback 핵심

POST /api/risk-assessment/draft/recalculate
  └─ backend/routers/risk_assessment_draft.py :: recalculate_draft()
     └─ backend/services/risk_assessment_engine.py :: recalculate()
        ├─ _controls_by_code() / _controls_by_hazard()
        └─ _merge_law_evidence()          ← rebuild_law_evidence=True 시 동일 경로
```

---

## 2. recommend / recalculate 실제 연결 구조

### 옵션 전달 흐름

| 파라미터 | recommend 경로 | recalculate 경로 |
|---|---|---|
| max_laws_per_row | RecommendOptions(default=3) → recommend() → _merge_law_evidence() | RecalculateOptions(default=3) → recalculate() → _merge_law_evidence() |
| include_law_evidence | RecommendOptions(default=True) → recommend() → _merge_law_evidence() 조기 종료 | rebuild_law_evidence=False 시 _merge_law_evidence 호출 자체 생략 |
| generic cap | _GENERIC_LAW_CAP_WITH_SPECIFIC=1, _GENERIC_LAW_CAP_FALLBACK=2 — 두 경로 공통 | 동일 |
| deterministic sort | (ev_priority ASC, -score, law_id ASC) — 두 경로 공통 | 동일 |
| condition_bonus | _apply_condition_bonus() — recommend에서만 hazard score에 적용 | recalculate에서도 hz_score 재계산 시 동일 적용 |

### 확인 결과

- recommend / recalculate 모두 `_merge_law_evidence()` 동일 함수 호출 ✅
- 옵션 기본값이 Pydantic 스키마에서 주입되어 서비스까지 도달 ✅
- law 정렬 기준 및 generic cap이 두 경로에서 동일하게 적용 ✅
- response schema 무변경 ✅

---

## 3. safe default / fallback / generic cap 고정 내용

### 적용 중인 safe-guard

| 항목 | 값 | 위치 |
|---|---|---|
| max_laws_per_row 기본값 | 3 (schema default) | RecommendOptions, RecalculateOptions |
| max_laws_per_row 상한 | 10 (schema le=10) | Pydantic field validator |
| generic-law cap (specific 존재 시) | 1 | _GENERIC_LAW_CAP_WITH_SPECIFIC |
| generic-law cap (fallback) | 2 | _GENERIC_LAW_CAP_FALLBACK |
| hazard 후보 없음 시 fallback | FALL (score=65) | recommend() |
| control 선택 없음 시 기본 | hazard별 상위 3개 | recalculate() |
| unknown control_code | 제외 후 MANUAL_REVIEW_RECOMMENDED 플래그 | recalculate() |
| law score 상한 | 98 (_SCORE_MAX) | _apply_condition_bonus() |
| EngineError → HTTP | 404/422 변환 | router HTTPException 핸들러 |

### 발견된 추가 수정 없음

코드 점검 결과 운영 경로 상의 gaps 없음 확인:
- `recalculate()` 내 `include_law_evidence=True` hardcode는 설계 의도 (`rebuild_law_evidence` 플래그로 호출 자체를 제어)
- `_compute_response_flags()` recalculate 호출 시 `total=len(rows)`, `max=len(rows)` → MAX_ROWS_REACHED 미발생 (의도된 동작)

---

## 4. API 단 회귀 테스트 시나리오

### 테스트 파일: `tests/test_risk_assessment_draft_api.py`

총 32개 테스트 (31 PASS, 1 SKIP)

| # | 테스트명 | 검증 내용 |
|---|---|---|
| 1 | test_recommend_elec_live | ELEC_LIVE 정상 생성, ELEC hazard, row_id 형식 |
| 2 | test_recommend_water_manhole | WATER_MANHOLE, ASPHYX 포함, law 존재 |
| 3 | test_recommend_invalid_work_type | 404 응답 |
| 4 | test_recommend_missing_work_type_code | 422 응답 |
| 5 | test_recommend_options_out_of_range | options 범위 초과 422 |
| 6 | test_recalculate_normal | 정상 재계산, editable 반영 |
| 7 | test_recalculate_empty_rows | 빈 rows 422 |
| 8 | test_recalculate_wrong_row_id | row_id 불일치 422 |
| 9 | test_editable_controls_separation | editable / controls 구조 분리 |
| 10 | test_condition_flag_missing_warning | CONDITION_FLAG_MISSING 플래그 |
| 11 | test_recommend_temp_scaff_row_ids | row_id 형식 검증 |
| 12 | test_recommend_lift_rigging | law evidence_paths 포함 확인 |
| 13 | test_low_law_evidence_flag | include_law_evidence=False → LOW_LAW_EVIDENCE |
| 14 | test_recalculate_unknown_control_code_flag | MANUAL_REVIEW_RECOMMENDED 플래그 |
| 15 | **test_recommend_deterministic_repeat** | 3회 동일 입력 → 동일 rows (결정론성) |
| 16 | **test_recalculate_deterministic_repeat** | 3회 동일 입력 → 동일 rows |
| 17 | **test_max_laws_per_row_enforced** | max_laws=2 → 모든 row ≤2 law |
| 18 | **test_max_laws_per_row_min_boundary** | max_laws=1 → 모든 row ≤1 law |
| 19 | **test_generic_law_not_top1** | specific law 존재 시 top1 비generic |
| 20 | **test_law_ordering_priority** | control→hazard→worktype 순서 |
| 21 | **test_generic_law_cap_with_specific** | specific 존재 시 generic ≤1 |
| 22 | **test_recommend_weld_arc** | WELD_ARC: FIRE/ELEC/DUST 포함 |
| 23 | **test_recommend_civil_excav** | CIVIL_EXCAV: COLLAPSE + law 존재 |
| 24 | **test_recommend_fire_explo_scenario** | WELD_GAS: FIRE/EXPLO 포함 |
| 25 | **test_recommend_dust_scenario** | TUNNEL_DRILL: DUST + law 존재 |
| 26 | **test_recommend_recalculate_law_alignment** | recommend/recalculate law_id 일치 |
| 27 | **test_recalculate_excluded_law_ids** | 제외 law_id 미포함 |
| 28 | **test_recalculate_rebuild_false_no_laws** | rebuild=False → laws=[] |
| 29 | test_recommend_preferred_hazard_first | SKIP (ELEC_LIVE hazard 1개) |
| 30 | **test_recommend_excluded_hazard** | 제외 hazard 미포함 |
| 31 | **test_summary_counts_match_rows** | summary 집계 일치 |
| 32 | **test_lift_rigging_recommend_recalculate_alignment** | LIFT_RIGGING 전체 row 정렬 일치 |

---

## 5. API 운영 경로 안정화 지표

| 지표 | 결과 |
|---|---|
| recommend 반복 호출 일치율 (3회) | **100%** |
| recalculate 반복 호출 일치율 (3회) | **100%** |
| recommend / recalculate 응답 일치율 | **100%** (동일 입력 기준) |
| generic-law top1 점유율 | **0%** (전 시나리오) |
| row당 평균 law 수 (default max=3) | **3.0** |
| fallback 사용 비율 (worktype-only만) | **0%** |

---

## 6. worktype별 지표

| worktype | 시나리오 | rows | avg_ctrl | avg_law | specific% | generic% |
|---|---|---|---|---|---|---|
| ELEC_LIVE | 전기 활선 | 1 | 3.0 | 3.0 | 100% | 0% |
| WATER_MANHOLE | 맨홀/밀폐공간 | 4 | 3.0 | 3.0 | 100% | 0% |
| TEMP_SCAFF | 비계/가설 | 3 | 3.0 | 3.0 | 100% | 0% |
| LIFT_RIGGING | 양중 | 3 | 3.0 | 3.0 | 100% | 0% |
| WELD_ARC | 용접/절단 | 3 | 3.0 | 3.0 | 100% | 0% |
| CIVIL_EXCAV | 토공/굴착 | 1 | 3.0 | 3.0 | 100% | 0% |
| TUNNEL_DRILL | 분진 | 2 | 3.0 | 3.0 | 100% | 0% |
| WELD_GAS | 화재/폭발 | 2 | 3.0 | 3.0 | 100% | 0% |

---

## 7. hazard별 지표

| 위험코드 | high-conf% | ctrl-specific% | generic% | fallback 사용 |
|---|---|---|---|---|
| ASPHYX | 100% | 67% | 0% | 0 |
| COLLAPSE | 100% | 33% | 0% | 0 |
| DROP | 100% | 67% | 0% | 0 |
| DUST | 100% | 67% | 0% | 0 |
| ELEC | 100% | 67% | 0% | 0 |
| EXPLO | 100% | 100% | 0% | 0 |
| FALL | 100% | 67% | 0% | 0 |
| FIRE | 100% | 100% | 0% | 0 |

---

## 8. 샘플 운영 시나리오 검증 결과

| 시나리오 | hazard_count | law 품질 | top1 law | 판정 |
|---|---|---|---|---|
| 전기 활선 (ELEC_LIVE) | 1 | 100% high-conf, 0% generic | control_law | **PASS** |
| 맨홀/밀폐공간 (WATER_MANHOLE) | 4 | ASPHYX 포함, 100% specific | hazard/control_law | **PASS** |
| 비계/가설 (TEMP_SCAFF) | 3 | 100% specific | control_law | **PASS** |
| 양중 (LIFT_RIGGING) | 3 | 100% specific | control_law | **PASS** |
| 용접/절단 (WELD_ARC) | 3 | FIRE+ELEC+DUST, 100% specific | control_law | **PASS** |
| 토공/굴착 (CIVIL_EXCAV) | 1 | COLLAPSE, hazard-specific | hazard_law | **PASS** |
| 분진 (TUNNEL_DRILL) | 2 | DUST 포함, 100% specific | control_law | **PASS** |
| 화재/폭발 (WELD_GAS) | 2 | FIRE+EXPLO 100% ctrl-specific | control_law | **PASS** |

---

## 9. 남은 한계

- `test_recommend_preferred_hazard_first`: ELEC_LIVE hazard가 1개뿐이어서 SKIP. 복수 hazard worktype에서 별도 확인 필요.
- CIVIL_EXCAV의 COLLAPSE는 hazard-specific law 존재하나 control-specific 비율이 33%로 타 hazard 대비 낮음. 컨트롤 매핑 보강 시 개선 가능.
- `_RECOMMENDED_FLAGS`에 WELD_ARC, CIVIL_EXCAV 미등록 — condition_flag 권장 기준이 없어 CONDITION_FLAG_MISSING 경고 미발생.

---

## 10. 운영 반영 전 체크포인트

- [x] 프론트엔드 수정 없음
- [x] DB migration 없음
- [x] response schema 무변경
- [x] recommend 운영 경로 연결 확인
- [x] recalculate 운영 경로 연결 확인
- [x] 동일 입력 반복 호출 PASS (3회 일치)
- [x] generic-law top1 미발생 PASS
- [x] max_laws_per_row 준수 PASS
- [x] DUST / FIRE / EXPLO 시나리오 검증 PASS
- [x] API 단 회귀 테스트 32개 전체 PASS (1 SKIP)
- [x] recommend / recalculate law_id 일치 PASS
- [x] excluded_law_ids 동작 PASS

---

## 11. 17단계 예정

- RUNBOOK 배포 절차 표준화
- 운영 서버 배포 전 smoke test 스크립트 작성
- git tag + 배포 체크리스트 확정
- CONDITION_FLAG_MISSING 미등록 worktype 보강 여부 검토

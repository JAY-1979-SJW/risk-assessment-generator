# 추천 엔진 설계 규칙

생성일: 2026-04-21
단계: 7단계 (4축 통합 추천 엔진 설계)

---

## 입력 파일

| 구분 | 경로 |
|---|---|
| 작업유형 | `data/risk_db/work_taxonomy/work_types.json` |
| 위험요인 | `data/risk_db/hazard_action/hazards.json` |
| control | `data/risk_db/hazard_action_normalized/controls_normalized.json` |
| 법령 | `data/risk_db/law_normalized/safety_laws_normalized.json` |
| worktype↔hazard | `data/risk_db/work_taxonomy/work_hazards_map.json` |
| hazard↔law | `data/risk_db/law_mapping/law_hazard_map.json` |
| worktype↔law | `data/risk_db/law_mapping/law_worktype_map.json` |
| control↔law | `data/risk_db/law_mapping/law_control_map.json` |

---

## 추천 파이프라인 (7단계)

| 단계 | 함수 | 설명 |
|---|---|---|
| 1 | resolve_worktype | work_types.json에서 메타 조회 |
| 2 | collect_hazard_candidates | work_hazards_map 조회 → 없으면 trade 기반 rule_based_inference |
| 3 | score_hazards | base(freq×20+sev×10) + condition_flag 가점 → 상위 5건 |
| 4 | collect_control_candidates | controls_normalized에서 hazard_code 기준 조회 |
| 5 | score_controls | control_type × priority 점수표 → 상위 3건 |
| 6 | merge_law_evidence | 3개 경로 병합, law_id dedupe, path weighted score |
| 7 | assemble_rows | hazard 기준 row 조립 |

---

## hazard_score 점수 규칙

| 조건 | 점수 |
|---|---|
| work_hazards_map 직접 연결 | freq×20 + sev×10 (max: 3×20+3×10=90) |
| rule_based_inference | 65 (기본) |
| condition_flag 가점 | high_place→FALL+15, confined_space→ASPHYX+15, live_electric→ELEC+15 등 |
| severity_class=high 보정 | score<80 이면 +5 |
| 최대 상한 | 98 |

condition_flag 가점 전체 테이블은 `build_recommendation_engine_schema.py` `CONDITION_BONUS` 참조.

---

## control_score 점수 규칙

| control_type | priority=1 | priority=2 |
|---|---|---|
| engineering | 90 | 80 |
| admin | 85 | 75 |
| ppe | 80 | 72 |

---

## law_score 경로 가중치

| evidence_path | 가중치 |
|---|---|
| control_law | 1.0 |
| hazard_law | 0.9 |
| worktype_law | 0.8 |

최종 law_score = max(해당 경로들의 가중 점수)

---

## dedupe 규칙

| 대상 | 기준 |
|---|---|
| hazard | hazard_code 기준, 동일 코드 점수 병합 |
| control | control_code 기준, 상위 점수 유지 |
| law | law_id 기준, evidence_paths 합집합 + best_score 갱신 |

---

## 출력 제한 규칙

| 항목 | 기본 | 최대 |
|---|---|---|
| hazard per worktype | 5 | 7 |
| control per hazard | 3 | 5 |
| law per row | 3 | 5 |

---

## 샘플 생성 대상

| work_type_code | condition_flags |
|---|---|
| ELEC_LIVE (활선 작업) | live_electric, high_place |
| TEMP_SCAFF (비계 설치) | high_place |
| WATER_MANHOLE (맨홀 내부) | confined_space |
| LIFT_RIGGING (리깅·줄걸이) | high_place |
| DEMO_ASBESTOS (석면 해체) | chemical_use |

---

## trade 기반 hazard 추론 규칙

work_hazards_map에 없는 worktype은 trade_code 기반 인퍼런스 적용:
- LIFT → DROP(3,3), COLLIDE(2,3), FALL(2,3)
- DEMO → DUST(3,3), COLLAPSE(2,3), ASPHYX(2,3), POISON(2,3), CHEM(1,3)

---

## 현재 한계

- worktype_hazard: 30/132 work_types만 직접 연결, 나머지 102개는 rule_based_inference
- 법령: 전체가 statute:273603 또는 statute:276853으로 집중 (조문 수준 없음)
- condition_flags 자동 감지 로직 미구현 (사용자 입력 필요)
- work_sub_type_code 연계 점수 가산 미구현
- CHEM/POISON control이 2건뿐 (MAX_CONTROL=3 미충족)

---

## API 반영 전 보완 항목

1. worktype_hazard 커버리지 102개 보강
2. condition_flags 자동 감지 로직 (작업 설명→flag 추출)
3. work_sub_type_code 연계 score 가산 로직
4. law 조문 수준 세분화 (조문 단위 ID 도입)
5. CHEM/POISON control 항목 보강
6. 실시간 law detail_link 유효성 검증

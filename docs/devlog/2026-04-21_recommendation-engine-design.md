# 7단계 — 4축 통합 추천 엔진 설계

- 작업일시: 2026-04-21
- 작업자: JAY-1979-SJW
- 관련 브랜치: master
- 관련 커밋: (커밋 후 기재)

## 목표

3~6단계에서 구축한 worktype/hazard/control/law 4축 링크를 통합하여
위험성평가표 초안을 조립할 수 있는 추천 엔진 구조를 설계하고
5개 worktype에 대해 실제 매핑 DB 기반 샘플 추천 결과를 생성.

## 수정 파일

- `scripts/design/build_recommendation_engine_schema.py` — 신규: 엔진 설계 및 샘플 생성 스크립트
- `data/risk_db/engine_design/recommendation_engine_schema.json` — 신규: 엔진 구조 정의
- `data/risk_db/engine_design/recommendation_engine_samples.json` — 신규: 5개 worktype 샘플
- `data/risk_db/engine_design/recommendation_engine_review_notes.json` — 신규: 검토 메모 5건
- `docs/devlog/recommendation_engine_rules.md` — 신규: 운영 규칙 문서

## 변경 이유

3~6단계 매핑 데이터가 각각 독립된 파일로 존재하여 통합 활용 로직이 없었음.
추천 엔진이 어떤 순서로 어떤 데이터를 조합하는지 구조를 먼저 확정하지 않으면
API 반영 시 설계 충돌 발생 가능.
7단계에서 파이프라인과 점수 규칙을 한 파일에 정의하고 샘플로 검증.

## 시도/실패 내용

### 시도 1 — 단순 hazard 목록 나열 방식 (폐기)

work_hazards_map에서 hazard를 가져와 controls를 그냥 붙이는 단순 조합.
→ condition_flags 가점, rule_based_inference, 법령 경로 병합이 없어
LIFT_RIGGING, DEMO_ASBESTOS처럼 work_hazards_map 미등록 worktype에서 빈 결과 발생.
→ **폐기**.

### 시도 2 — 7단계 파이프라인 + 3경로 law 병합 (채택)

1. work_hazards_map 직접 조회 → 없으면 trade 기반 rule_based_inference
2. condition_flags 가점으로 실제 작업 위험 반영
3. worktype_law + hazard_law + control_law 3경로 법령 병합 + dedupe
4. evidence_paths로 경로 출처 추적 가능
→ ELEC_LIVE ~ DEMO_ASBESTOS 5개 worktype 모두 정상 결과 생성. **채택**.

## 최종 적용 내용

| 항목 | 값 |
|---|---|
| 추천 파이프라인 단계 | 7단계 (resolve→hazard→score→control→score→law→assemble) |
| 샘플 worktype 수 | 5개 |
| 총 row 수 | 14건 |
| row당 평균 control | 2.9건 |
| row당 평균 law | 2.9건 |
| review notes | 5건 (MEDIUM 1, LOW 2, INFO 2) |

**샘플 결과:**
- ELEC_LIVE: ELEC(98) → 3 controls + 2 laws
- TEMP_SCAFF: FALL(98)/DROP(80)/COLLAPSE(75) → 각 3 controls + 3 laws
- WATER_MANHOLE: ASPHYX(98)/EXPLO(80) → 각 3 controls + 3 laws
- LIFT_RIGGING: DROP(80)/FALL(80)/COLLIDE(70) → 각 3 controls + 3 laws
- DEMO_ASBESTOS: POISON(82)/CHEM(82)/DUST(71)/COLLAPSE(70)/ASPHYX(70) → 각 2-3 controls + 3 laws

**법령 evidence_paths 예시 (statute:273603, TEMP_SCAFF/FALL):**
- evidence_paths: ["worktype_law", "hazard_law", "control_law"] — 3경로 모두 확인

## 검증 결과

- 5개 worktype 샘플 결과 생성 완료
- work_hazards_map 미등록 LIFT_RIGGING, DEMO_ASBESTOS → rule_based_inference 정상 동작
- condition_flags 가점 적용 확인 (ELEC_LIVE: ELEC=90+15(live_electric)→98 capped)
- law dedupe 확인 (statute:273603이 3경로 병합되어 evidence_paths=['worktype_law','hazard_law','control_law'])
- 보호 파일 (`backend/routers/engine_results.py`, `risk-assessment-web-baseline-v1.md`) 수정 없음
- 기존 매핑 JSON 수정 없음
- DB migration / 운영 insert 없음
- API 연결 없음
- 최종 판정: **PASS**

## 영향 범위

- `data/risk_db/engine_design/` 신규 디렉토리 생성 (읽기 전용 설계 초안)
- 기존 매핑 파일 변경 없음

## 한계

- worktype_hazard 30/132 커버 → 미등록 102개는 rule_based_inference
- 법령이 statute:273603/276853 2개로 집중 (조문 수준 세분화 불가)
- condition_flags 자동 감지 로직 미구현
- work_sub_type_code 연계 가산 미구현
- CHEM/POISON control 2건 (MAX_CONTROL=3 기준 미충족)

## 다음 단계

8단계 — 추천 엔진 API 반영 또는 worktype_hazard 커버리지 보강

API 반영 전 선행 조건:
1. condition_flags 자동 감지 로직 설계
2. worktype_hazard 102개 보강 계획
3. 실서비스 RAG 엔진과의 통합 지점 검토

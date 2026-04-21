# law_hazard_map 매핑 규칙

생성일: 2026-04-21  
단계: 3단계 (법령 ↔ 위험요인 초안 매핑)

---

## 입력 파일

| 구분 | 경로 |
|---|---|
| hazard 기준 | `data/risk_db/hazard_action/hazards.json` |
| law 기준 | `data/risk_db/law_normalized/safety_laws_normalized.json` |

---

## 출력 파일

| 파일 | 설명 |
|---|---|
| `data/risk_db/law_mapping/law_hazard_map.json` | draft 매핑 (score ≥ 60) |
| `data/risk_db/law_mapping/law_hazard_map_review_needed.json` | 검토 필요 후보 |
| `scripts/mapping/build_law_hazard_map.py` | 생성 스크립트 |

---

## source 우선순위

1. `statute` (법률/명령)
2. `admin_rule` (고시)
3. `licbyl` (별표·서식)
4. `interpretation` (해석례) — 보조 근거만

---

## 매핑 방식 3계층

### 1. manual_seed (최우선)
`산업안전보건기준에 관한 규칙` (raw_id: 273603)을 모든 위험요인의 1순위 법령으로 고정.  
근거: `hazards.json`의 각 위험요인 `source` 필드에 조문 번호 명시됨.  
score: 85~95 (위험요인 직접성에 따라 차등)

### 2. rule_based_inference (보조)
- `산업안전보건법` (276853): 모든 위험요인 상위 의무 규정 → score 80
- `건설업 산업안전보건관리비 계상 및 사용기준` (2100000254546):  
  건설 관련 위험요인(FALL, DROP, COLLAPSE, COLLIDE)만 → score 65

### 3. exact_keyword / partial_keyword (해석례 전용)
해석례 제목에서 위험요인 키워드가 2개 이상 → score 82 (exact)  
1개 → score 68 (partial, review_needed 후보)

---

## 위험요인별 시드 키워드

| code | 대표 키워드 |
|---|---|
| FALL | 추락방지, 안전난간, 작업발판 |
| DROP | 낙하물, 낙하물 방지망 |
| ELEC | 전기, 전로, 충전, 접지 |
| ASPHYX | 산소결핍, 밀폐공간, 유해가스 |
| FIRE | 인화성, 화기, 가연물 |
| EXPLO | 폭발, 가연성 가스, 압력 |
| COLLIDE | 충돌, 차량계 건설기계 |
| COLLAPSE | 붕괴, 흙막이, 동바리 |
| ENTRAP | 협착, 끼임, 회전체 |
| CUT | 절단, 회전날 |
| POISON | 화학물질, 흡입 |
| DUST | 분진, 용접흄, 석면 |
| NOISE | 소음 |
| CHEM | 화학물질, 누출 |
| TRIP | 전도, 미끄러짐 |
| BURN | 화상, 화기취급, 고온 |
| FLYBY | 비래, 파편 |

---

## score 규칙

| 구간 | 판정 |
|---|---|
| 90~100 | 매우 강함 (manual_seed 직접 규정) |
| 75~89 | 강함 (해석례 keyword match, 부모법 inference) |
| 60~74 | draft 후보 (건설업관리비, partial keyword) |
| 59 이하 | review_needed |

---

## review_needed 분리 기준

- score < 60
- partial_keyword 1개만 매칭된 해석례
- `사업장 위험성평가에 관한 지침` (위험성평가 방법론, 특정 위험요인 근거 약함)
- draft 5건 제한 초과분

---

## 결과 요약 (실행 기준: 2026-04-21)

| 항목 | 수치 |
|---|---|
| 총 hazard 수 | 17 |
| 총 law 수 | 52 |
| draft 매핑 | 42건 |
| review_needed | 3건 |
| hazard당 평균 draft | 2.47건 |

source 분포: statute 34, admin_rule 4, interpretation 4  
score 분포: 90-100점 11건 / 75-89점 24건 / 60-74점 7건

---

## 이번 단계의 한계

- law title에 직접 hazard keyword가 없는 경우 → manual_seed로 고정 처리
- `산업안전보건기준에 관한 규칙` 내 조문(제4절, 제619조 등)은 ID가 없어 조문 레벨 연결 불가 → 법령 전체 단위로만 연결
- 해석례 29건 중 대부분이 절차적 사항 → 직접 hazard 근거로 활용하기 어려움
- KOSHA 가이드 DB(guide_raw)는 이번 단계에서 미사용 → 4단계 이후 보강 가능

---

## 다음 단계

4단계 — `law_worktype_map` 초안 생성  
(작업유형별 법령 연결 매핑, `work_types.json` 기준)

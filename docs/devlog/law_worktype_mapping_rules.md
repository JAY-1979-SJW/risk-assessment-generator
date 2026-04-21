# law_worktype_map 매핑 규칙

생성일: 2026-04-21  
단계: 4단계 (작업유형 ↔ 법령 초안 매핑)

---

## 입력 파일

| 구분 | 경로 |
|---|---|
| work_type 기준 | `data/risk_db/work_taxonomy/work_types.json` |
| work_sub_type 참조 | `data/risk_db/work_taxonomy/work_sub_types.json` |
| law 기준 | `data/risk_db/law_normalized/safety_laws_normalized.json` |

work_sub_types는 score 보정 및 keywords 결정에만 참조 (매핑 단위는 work_type).

---

## 출력 파일

| 파일 | 설명 |
|---|---|
| `data/risk_db/law_mapping/law_worktype_map.json` | draft 매핑 (score ≥ 60) |
| `data/risk_db/law_mapping/law_worktype_map_review_needed.json` | 검토 필요 후보 |
| `scripts/mapping/build_law_worktype_map.py` | 생성 스크립트 |

---

## source 우선순위

1. `statute` (법률/명령)
2. `admin_rule` (고시)
3. `licbyl` (별표·서식) — 이번 단계 미사용
4. `interpretation` (해석례) — 보조만

---

## 매핑 방식 3계층

### 1. manual_seed (최우선)
`work_type_code`별 override 또는 `trade_code`별 seed로 `산업안전보건기준에 관한 규칙`(273603)을 고정 연결.  
work_sub_types.json의 source 필드(조문 번호)를 근거로 score 설정.

### 2. rule_based_inference (보조)
- `산업안전보건법`(276853): risk_level=3 작업유형 → score 78, 그 외 → review_needed
- `건설업 산업안전보건관리비 계상 및 사용기준`(2100000254546): 건설 직종 risk_level=3만 → score 63

### 3. exact/partial_keyword (해석례 전용)
해석례 제목에서 작업유형별 키워드 검색.  
2개 이상 일치 → score 80, 1개 → score 65

---

## 작업유형 개별 override 목록

| work_type_code | 법령 | score | 근거 |
|---|---|---|---|
| DEMO_ASBESTOS | 산안법 276853 | 92 | 산안법 제122조 (석면해체·제거) |
| ENV_ASBESTOS | 산안법 276853 | 92 | 산안법 제122조 |
| ELEC_LIVE | 안전보건규칙 273603 | 95 | 제301조 (활선작업) |
| WATER_MANHOLE | 안전보건규칙 273603 | 95 | 제619조 (밀폐공간) |
| MECH_CRANE | 안전보건규칙 273603 | 93 | 제140~149조 |
| MECH_FORKLIFT | 안전보건규칙 273603 | 90 | 제177조 |
| WELD_GAS | 안전보건규칙 273603 | 92 | 제232조 (가스용접) |
| STEEL_LIFT | 안전보건규칙 273603 | 92 | 제153조 (인양) |
| LIFT_RIGGING | 안전보건규칙 273603 | 93 | 제153조 (줄걸이) |
| ELEC_PANEL | 안전보건규칙 273603 | 92 | 제303조 (분전반) |
| TEMP_SCAFF | 안전보건규칙 273603 | 93 | 제59조 (비계) |
| TEMP_OPEN | 안전보건규칙 273603 | 93 | 제42조 (개구부) |
| PAINT_SPRAY | 안전보건규칙 273603 | 88 | 제616조 (유기화합물) |
| TUNNEL_DRILL | 안전보건규칙 273603 | 92 | 제619조+밀폐공간 |

---

## trade별 시드 키워드 (주요)

| trade_code | 키워드 |
|---|---|
| CIVIL | 굴착, 흙막이, 사면 |
| RC | 거푸집, 동바리, 콘크리트 |
| STEEL | 철골, 양중, 고소 |
| TEMP | 비계, 작업발판, 사다리, 개구부 |
| ELEC | 전기, 전로, 감전 |
| WELD | 용접, 화기, 절단, 가스 |
| WATER | 밀폐공간, 산소결핍, 맨홀 |
| MECH | 크레인, 양중, 지게차 |
| LIFT | 양중, 크레인, 줄걸이 |
| ENVIRON | 석면, 분진 |

---

## score 규칙

| 구간 | 판정 |
|---|---|
| 90~100 | 매우 강함 (override/seed 직접 규정) |
| 75~89 | 강함 (trade seed, 해석례 keyword, 부모법) |
| 60~74 | draft 후보 (건설업관리비, 해석례 partial) |
| 59 이하 | review_needed |

risk_level 보정: risk_level=3 → 기본, risk_level=2 → -5, risk_level=1 → -15

---

## review_needed 분리 기준

- score < 60
- risk_level=1 작업유형의 산안법 inference
- risk_level=2 작업유형의 산안법 inference (score 52)
- draft 5건 제한 초과분

---

## 결과 요약 (실행 기준: 2026-04-21)

| 항목 | 수치 |
|---|---|
| 총 work_type 수 | 132 |
| 총 law 수 | 52 |
| draft 매핑 | 268건 |
| review_needed | 82건 |
| work_type당 평균 draft | 2.03건 |

source 분포: statute 194건 / admin_rule 57건 / interpretation 17건  
score 분포: 90-100점 31건 / 75-89점 136건 / 60-74점 101건

---

## 이번 단계의 한계

- work_sub_type 단위 매핑 미수행 (work_type 단위만 생성)
  → 85개 sub_type에 대한 세부 매핑은 후속 4.1단계에서 수행 가능
- 안전보건규칙 내 조문 번호 수준의 ID 없음 → 법령 전체 단위 연결
- 화약류관리법(터널 발파) 등 DB 미수록 법령 연결 불가
- KOSHA 가이드 DB 미사용

---

## 다음 단계

5단계 — `law_control_map` 또는 worktype/hazard/control 통합 연결 설계

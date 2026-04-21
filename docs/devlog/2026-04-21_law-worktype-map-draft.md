# 4단계 — law_worktype_map 초안 생성

- 작업일시: 2026-04-21
- 작업자: JAY-1979-SJW
- 관련 브랜치: master
- 관련 커밋: (커밋 후 기재)

## 목표

`safety_laws_normalized.json`(52건)과 `work_types.json`(132개)을 연결하는
작업유형-법령 매핑 초안 파일(`law_worktype_map.json`) 생성.
UI/엔진 연결 없이 검토 가능한 초안 데이터만 생성.

## 수정 파일

- `scripts/mapping/build_law_worktype_map.py` — 신규: 매핑 생성 스크립트
- `data/risk_db/law_mapping/law_worktype_map.json` — 신규: draft 매핑 268건
- `data/risk_db/law_mapping/law_worktype_map_review_needed.json` — 신규: review 후보 82건
- `docs/devlog/law_worktype_mapping_rules.md` — 신규: 매핑 운영 규칙 문서

## 변경 이유

평가표 생성 시 "작업 선택 → 관련 법령 자동 필터링" 축이 필요함.
3단계(hazard ↔ law)와 함께 작업유형별 법령 연결 축을 구성하여
추후 추천 엔진의 법령 근거 제시에 활용 예정.

## 시도/실패 내용

### 시도 1 — 3단계 hazard 방식 그대로 적용 (폐기)

3단계와 동일하게 trade별 단일 시드 키워드만 적용하면
작업유형별 특성 구분 없이 trade 단위로만 동일한 연결 생성됨.
예: CIVIL 소속 CIVIL_EXCAV(터파기, risk_level=3)와
CIVIL_FILL(성토, risk_level=2)가 동일 score 처리됨.
→ risk_level 보정이 없으면 저위험 작업에도 고점 부여되어
법령 연결의 실질 의미가 약해짐. **폐기**.

### 시도 2 — 2계층 구조 (trade seed + risk_level 보정 + work_type override) (채택)

- **WORKTYPE_OVERRIDE**: 특정 work_type에 조문 수준 근거가 있는 경우 개별 설정  
  예: ELEC_LIVE → 안전보건규칙 제301조 (score 95)  
  예: DEMO_ASBESTOS → 산안법 제122조 (score 92)
- **TRADE_SEED_MAP**: trade별 산업안전보건기준에 관한 규칙을 base score로 연결  
  risk_level=3: 기본, risk_level=2: -5, risk_level=1: -15
- **rule_based_inference**: 산안법(부모법)은 risk_level=3만 score 78, 건설업관리비 score 63
- **interpretation keyword**: 해석례 제목에서 작업유형별 키워드 검색

결과: draft 268건(avg 2.03건/work_type), review_needed 82건. 분포 적절.

## 최종 적용 내용

| 항목 | 값 |
|---|---|
| work_type 수 | 132 |
| law 수 (normalized) | 52 |
| draft 매핑 | 268건 |
| review_needed | 82건 |
| work_type당 평균 draft | 2.03건 |

**score 분포**: 90-100점 31건 / 75-89점 136건 / 60-74점 101건  
**source 분포**: statute 194건 / admin_rule 57건 / interpretation 17건

주요 매핑 예시:
- ELEC_LIVE → 안전보건규칙 제301조 (score 95, manual_seed)
- WATER_MANHOLE → 안전보건규칙 제619조 (score 95, manual_seed)
- TEMP_SCAFF → 안전보건규칙 제59조 (score 93) + 추락 해석례 313846 (score 80)
- DEMO_ASBESTOS → 산안법 제122조 (score 92) + 안전보건규칙 (score 88)
- LIFT_RIGGING → 안전보건규칙 줄걸이 (score 93, manual_seed)

## 검증 결과

- 보호 파일 (`backend/routers/engine_results.py`, `risk-assessment-web-baseline-v1.md`) 수정 없음
- `law_hazard_map.json` 수정 없음
- DB migration / 운영 insert 없음
- 추천 엔진 연결 없음
- 최종 판정: **PASS**

## 영향 범위

- 읽기 전용 초안 데이터 파일만 생성 (운영 영향 없음)
- `data/risk_db/law_mapping/` 디렉토리 파일 추가

## 한계

- work_sub_type 단위 매핑 미수행 (work_type 단위만 처리)
- 화약류관리법 등 DB 미수록 법령 연결 불가
- KOSHA 가이드 DB 미사용

## 다음 단계

5단계 — `law_control_map` 또는 worktype/hazard/control 통합 연결 설계

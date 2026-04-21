# 3단계 — law_hazard_map 초안 생성

- 작업일시: 2026-04-21
- 작업자: JAY-1979-SJW
- 관련 브랜치: master
- 관련 커밋: (커밋 후 기재)

## 목표

`safety_laws_normalized.json`(52건)과 `hazards.json`(17개)을 연결하는
위험요인-법령 매핑 초안 파일(`law_hazard_map.json`) 생성.
UI/엔진 연결 없이 검토 가능한 초안 데이터만 생성.

## 수정 파일

- `scripts/mapping/build_law_hazard_map.py` — 신규: 매핑 생성 스크립트
- `data/risk_db/law_mapping/law_hazard_map.json` — 신규: draft 매핑 42건
- `data/risk_db/law_mapping/law_hazard_map_review_needed.json` — 신규: review 후보 3건
- `docs/devlog/law_hazard_mapping_rules.md` — 신규: 매핑 운영 규칙 문서

## 변경 이유

RAG 엔진이 위험요인 추천 시 법령 근거를 제시하려면
`hazard_code ↔ law_id` 연결 테이블이 필요함.
2단계에서 정규화된 법령 DB를 기반으로 1차 초안 생성.

## 시도/실패 내용

### 시도 1 — 법령 제목 키워드 검색 방식 (실패)

`title_ko`에 위험요인 키워드 포함 여부로 스코어링 시도.  
문제: 법령 제목이 "산업안전보건기준에 관한 규칙" 같은 일반 명칭이어서  
"추락", "감전" 등 위험요인 핵심어가 제목에 없음 → 전부 score 0 처리됨.  
결과: 74건 생성되었으나 전부 `rule_based_inference` score 75로 평탄화,  
핵심 법령과 일반 법령 간 점수 차이 없음. **폐기**.

### 시도 2 — 3계층 스코어링 방식 (채택)

- **Layer 1 (manual_seed)**: `hazards.json` source 필드에 명시된 조문 번호 기반으로  
  `산업안전보건기준에 관한 규칙`(273603)을 위험요인별 직접 근거 법령으로 고정.  
  score 85~95 (위험요인 직접성 차등).
- **Layer 2 (rule_based_inference)**: `산업안전보건법`(276853) 전 위험요인 상위법 score 80.  
  건설업 관리비 고시는 건설 4개 위험요인만 score 65.
- **Layer 3 (keyword)**: 해석례 제목에서만 키워드 검색. licbyl 서식은 제외.

결과: draft 42건, review_needed 3건. source·score 분포 적절.

## 최종 적용 내용

| 항목 | 값 |
|---|---|
| hazard 수 | 17 |
| law 수 (normalized) | 52 |
| draft 매핑 | 42건 |
| review_needed | 3건 |
| hazard당 평균 draft | 2.47건 |

**score 분포**: 90-100점 11건 / 75-89점 24건 / 60-74점 7건  
**source 분포**: statute 34건 / admin_rule 4건 / interpretation 4건

주요 매핑 예시:
- FALL → 산업안전보건기준에 관한 규칙 (score 95, manual_seed)
- FALL → 추락·안전난간 해석례 313846 (score 82, exact_keyword)
- ELEC → 산업안전보건기준에 관한 규칙 (score 95, manual_seed)
- COLLAPSE → 건설업 산업안전보건관리비 기준 (score 65, rule_based_inference)

## 검증 결과

- 보호 파일(`backend/routers/engine_results.py`, `risk-assessment-web-baseline-v1.md`) 수정 없음
- DB migration / 운영 insert 없음
- 추천 엔진 연결 없음
- `law_worktype_map`, `law_control_map` 미생성
- 최종 판정: **PASS**

## 영향 범위

- 읽기 전용 초안 데이터 파일만 생성 (운영 영향 없음)
- `scripts/mapping/` 디렉토리 신규 생성
- `data/risk_db/law_mapping/` 디렉토리 신규 생성

## 다음 단계

4단계 — `law_worktype_map` 초안 생성  
(`work_types.json` 기준으로 작업유형 ↔ 법령 매핑)

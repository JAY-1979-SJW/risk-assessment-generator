# 6단계 — law_control_map 초안 생성

- 작업일시: 2026-04-21
- 작업자: JAY-1979-SJW
- 관련 브랜치: master
- 관련 커밋: (커밋 후 기재)

## 목표

5.5단계에서 정규화 완료된 control 90건과 normalized law 52건을 연결하여
control ↔ law 매핑 초안(law_control_map.json)을 생성.
6단계 완료 시 worktype/hazard/control/law 4축 연결 설계의 마지막 축이 확보됨.

## 수정 파일

- `scripts/mapping/build_law_control_map.py` — 신규: 매핑 생성 스크립트
- `data/risk_db/law_mapping/law_control_map.json` — 신규: draft 92건
- `data/risk_db/law_mapping/law_control_map_review_needed.json` — 신규: 0건
- `docs/devlog/law_control_mapping_rules.md` — 신규: 운영 규칙 문서

## 변경 이유

5.5단계에서 control_code 확정 + law_id 정규화가 완료됨.
`prelinked_law_id` 방식으로 5.5단계 결과를 그대로 사용하면
추가 키워드 매칭 없이 안정적인 매핑 초안 생성 가능.
4축 링크 설계 완성을 위한 마지막 매핑 단계.

## 시도/실패 내용

### 시도 1 — law 제목 키워드 검색 방식 (폐기)

법령 제목에서 control 명칭 키워드(예: "LOTO", "안전난간", "방진")를 검색.
→ normalized law 52건의 제목 대부분이 "산업안전보건기준에 관한 규칙" 한 건으로 귀결.
→ 제목 검색으로 score 차별화 불가. **폐기**.

### 시도 2 — prelinked_law_id 1순위 + secondary 탐색 (채택)

5.5단계 controls_normalized.json의 law_ids를 1순위 기준으로 사용.
priority + control_type + 참조 조문 수준에 따라 score 차별화 적용.
FALL 안전난간 관련 controls에만 interpretation:313846 보조 secondary 추가.
→ 90건 prelinked + 2건 secondary = 92건 draft. **채택**.

## 최종 적용 내용

| 항목 | 값 |
|---|---|
| 총 control 수 | 90건 |
| 총 law 수 (normalized) | 52건 |
| draft 매핑 | 92건 |
| review_needed | 0건 |
| control당 평균 | 1.02건 |

**source 분포**: statute 90건 / interpretation 2건  
**match_type 분포**: prelinked_law_id 90건 / related_law_match 2건  
**score 분포**: 90-100점 36건 / 75-89점 54건 / 60-74점 2건

주요 예시:
- FALL_C01 → 안전난간 설치 → statute:273603(score=92) + interpretation:313846(score=72)
- ELEC_C02 → LOTO 설치 → statute:273603 (score=92)
- ASPHYX_C01 → 산소농도 측정 → statute:273603 (score=88)
- POISON_C01 → MSDS 숙지 → statute:276853 (score=80)
- DROP_C01 → 낙하물방지망 → statute:273603 (score=88, 절 수준 -4 적용)

## 검증 결과

- `law_control_map.json`: 92건 / FALL_C01 2건(primary+secondary) 확인
- `law_control_map_review_needed.json`: 0건 확인
- POISON/CHEM → statute:276853(제114조) score=80 확인
- DROP 제14절 참조 → score 패널티(-4) 적용 확인
- 보호 파일 (`backend/routers/engine_results.py`, `risk-assessment-web-baseline-v1.md`) 수정 없음
- `law_hazard_map.json`, `law_worktype_map.json` 수정 없음
- DB migration / 운영 insert 없음
- 추천 엔진 연결 없음
- 최종 판정: **PASS**

## 영향 범위

- `data/risk_db/law_mapping/law_control_map.json` 신규 생성 (읽기 전용 초안)
- `data/risk_db/law_mapping/law_control_map_review_needed.json` 신규 생성
- 기존 파일 변경 없음

## 한계

- 모든 control이 statute:273603 또는 statute:276853 2개 법령으로만 수렴
  (법령 전체 단위 매핑 — 조문 수준 세분화 불가)
- admin_rule, licbyl 연결 없음 (직접 control 근거 해당 없음)
- interpretation 보조 연결 2건 외 확장 불가
- worktype_hazard 커버리지 30/132 한계는 별도 개선 필요

## 다음 단계

4축 링크 완성:
- worktype_hazard 커버리지 보강 (미연결 102 work_types)
- 또는 4축 통합 링크를 RAG 추천 엔진에 반영

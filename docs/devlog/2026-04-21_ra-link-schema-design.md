# 5단계 — ra_link_schema 4축 통합 연결 설계

- 작업일시: 2026-04-21
- 작업자: JAY-1979-SJW
- 관련 브랜치: master
- 관련 커밋: (커밋 후 기재)

## 목표

worktype / hazard / control / law 4개 축을 연결하는 통합 스키마 설계.
6단계(law_control_map) 착수 전 엔티티 기준 키·관계 종류·현황 공백을 명확히 정의.
UI/엔진 연결 없이 설계 문서와 샘플 데이터만 생성.

## 수정 파일

- `scripts/design/build_ra_link_schema.py` — 신규: 스키마 설계 생성 스크립트
- `data/risk_db/link_design/ra_link_schema.json` — 신규: 4축 엔티티·관계 정의
- `data/risk_db/link_design/ra_link_samples.json` — 신규: 검증용 샘플 (worktype_hazard 10건, hazard_control 10건, control_law 5건)
- `data/risk_db/link_design/ra_link_review_notes.json` — 신규: 후속 단계 검토 메모 7건
- `docs/devlog/ra_link_schema_rules.md` — 신규: 스키마 설계 운영 규칙 문서

## 변경 이유

3단계(hazard↔law)·4단계(worktype↔law)에서 개별 매핑은 완성되었으나
worktype→hazard→control→law 전체 흐름에서 기준 키와 관계 종류가 명확히 정의되지 않았음.
6단계 착수 전 control_code 파생 규칙·law_ref 정규화 방법·관계 커버리지 공백을 확인하기 위해
통합 스키마 설계를 별도 단계로 수행.

## 시도/실패 내용

### 시도 1 — hazard_controls.json에서 control_code 직접 추출 (폐기)

`hazard_controls.json`에 `control_code` 필드가 없어 직접 추출 불가.
law_ref도 자유 텍스트로 law_id로 변환 없이는 관계 연결 불가.
→ control_code 파생 규칙(`{hazard_code}_C{nn:02d}`)과 law_ref 변환 함수를 스크립트 내 정의하여 처리.

### 시도 2 — worktype_hazard 전체 커버 설계 (일부 유보)

work_hazards_map.json이 30/132 work_types만 커버.
미연결 102개를 스크립트 내에서 자동 추론하면 부정확한 연결이 다수 생성될 위험.
→ 현재 커버된 30개만 샘플에 포함, 미연결 102개는 review_notes에 MEDIUM 항목으로 기록하여 후속 보강 과제로 유보.

## 최종 적용 내용

| 항목 | 값 |
|---|---|
| 엔티티 수 | 4 (worktype 132 / hazard 17 / control 90파생 / law 52) |
| 관계 종류 | 5 (worktype_hazard / hazard_control / worktype_law / hazard_law / control_law) |
| worktype_hazard | 48건 (30/132 wt) |
| hazard_control | 90건 (17/17 hz) |
| worktype_law | 268건 (전체) |
| hazard_law | 42건 (전체) |
| control_law | 설계 전용 5건 샘플 |

**review_notes 심각도 분포**: HIGH 2건 / MEDIUM 2건 / LOW 2건 / INFO 1건

주요 HIGH 항목:
- `missing_control_code`: hazard_controls.json에 control_code 필드 없음 → 파생 규칙(`{hazard_code}_C{nn:02d}`) 확정 필요
- `law_ref_text_not_id`: law_ref 자유 텍스트 → law_id 정규화 필요

엔진 흐름 6단계 정의:
1. 작업유형 입력 → 2. 위험요인 목록 → 3. 제어조치 목록
4. 관련 법령 필터 → 5. 위험요인별 법령 근거 → 6. 제어조치별 조문 근거

## 검증 결과

- `ra_link_schema.json`: 4엔티티 / 5관계 / 6단계 엔진흐름 정의 확인
- `ra_link_samples.json`: worktype_hazard 10건 / hazard_control 10건 / control_law 5건 확인
- `ra_link_review_notes.json`: 7건 (HIGH 2 / MEDIUM 2 / LOW 2 / INFO 1) 확인
- 보호 파일 (`backend/routers/engine_results.py`, `risk-assessment-web-baseline-v1.md`) 수정 없음
- `law_hazard_map.json`, `law_worktype_map.json` 수정 없음
- DB migration / 운영 insert 없음
- 추천 엔진 연결 없음
- 최종 판정: **PASS**

## 영향 범위

- 읽기 전용 설계 데이터 파일만 생성 (`data/risk_db/link_design/`) — 운영 영향 없음
- 기존 매핑 파일 변경 없음

## 한계

- control_code가 파생 값이므로 hazard_controls.json 순서 변경 시 불일치 발생 가능
- worktype_hazard 30/132 커버만 설계됨 (미연결 102개 미처리)
- control_law는 샘플 5건만 생성 (전체 매핑은 6단계에서 수행)

## 다음 단계

6단계 — `law_control_map` 초안 생성

전제조건 확인 후 착수:
1. control_code 파생 규칙 확정
2. hazard_controls.json의 law_ref → law_id 정규화

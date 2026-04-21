# 5.5단계 — control_code 기준 확정 및 law_ref → law_id 정규화

- 작업일시: 2026-04-21
- 작업자: JAY-1979-SJW
- 관련 브랜치: master
- 관련 커밋: (커밋 후 기재)

## 목표

6단계(law_control_map) 착수 전
control 식별키(`control_code`)를 흔들리지 않는 공식 기준으로 확정하고,
`hazard_controls.json`의 자유 텍스트 `law_ref`를
normalized law 고유키(`law_id`)로 정규화.

## 수정 파일

- `scripts/normalize/normalize_control_refs.py` — 신규: 정규화 스크립트
- `data/risk_db/hazard_action_normalized/controls_normalized.json` — 신규: 90건 정규화 완료본
- `data/risk_db/hazard_action_normalized/controls_review_needed.json` — 신규: 0건
- `data/risk_db/law_mapping/control_law_ref_candidates.json` — 신규: 90건 후보 매칭 기록
- `docs/devlog/control_reference_normalization_rules.md` — 신규: 운영 규칙 문서

## 변경 이유

5단계 ra_link_review_notes에서 두 가지 HIGH 항목 확인:
1. `missing_control_code`: hazard_controls.json에 control_code 필드 없어 law_control_map 생성 불가
2. `law_ref_text_not_id`: law_ref 자유 텍스트로 관계 연결 불가

이 두 항목을 해소하지 않으면 6단계에서 control 기준 없이 매핑을 시작하게 되어
이후 수정 비용이 크게 증가.

## 시도/실패 내용

### 시도 1 — law_standard/law_control_map.json 재활용 검토 (폐기)

기존 `data/risk_db/law_standard/law_control_map.json`(10건)에
`CTL-FALL-001` 형식의 control_code와 `OSHA-R-42` 형식의 law_code 존재.
→ 이는 normalized law_id 체계(`statute:273603`)와 다른 구 형식.
→ 52건 normalized law 체계와 호환되지 않아 재활용 불가. **폐기**.

### 시도 2 — 방식 C(slug 기반 코드 신설) 검토 (폐기)

`CTRL_FALL_GUARDRAIL` 형식으로 신규 코드 체계 설계 검토.
→ 5단계에서 이미 `FALL_C01` 방식 사용됨.
→ 두 체계가 혼재되면 6단계 통합 시 혼란 발생.
→ **폐기** 후 방식 B(`{hazard_code}_C{nn:02d}`) 유지.

### 시도 3 — 방식 B 공식 확정 (채택)

5단계 파생 규칙을 공식 표준으로 승격.
`hazard_controls.json` 항목 순서를 기준으로 순번 부여.
law_ref 패턴 매칭으로 2개 법령에 대한 완전 매칭 확인.

## 최종 적용 내용

| 항목 | 값 |
|---|---|
| control_code 방식 | B — `{hazard_code}_C{nn:02d}` |
| 총 control 수 | 90건 (17 hazard) |
| 정규화 완료(normalized) | 90건 |
| normalized_without_law | 0건 |
| review_needed | 0건 |
| duplicate_merged | 0건 |
| law_ref → law_id 매칭 | 90건 (matched 100%) |

**law_id 분포**: statute:273603 → 86건 / statute:276853 → 4건(POISON/CHEM)

주요 예시:
- FALL_C01 → 안전난간 설치 → statute:273603 (안전보건규칙 제43조 근거)
- ELEC_C01 → 잠금장치(LOTO) 설치 → statute:273603 (제301조 근거)
- ASPHYX_C01 → 밀폐공간 작업 전 산소 측정 → statute:273603 (제619조 근거)
- POISON_C01 → 화학물질 MSDS 관리 → statute:276853 (산안법 제114조 근거)

## 검증 결과

- `controls_normalized.json`: 90건 / normalization_status=normalized 90건 확인
- `controls_review_needed.json`: 0건 확인
- `control_law_ref_candidates.json`: 90건 / status=matched 90건 확인
- 보호 파일 (`backend/routers/engine_results.py`, `risk-assessment-web-baseline-v1.md`) 수정 없음
- `law_hazard_map.json`, `law_worktype_map.json` 수정 없음
- DB migration / 운영 insert 없음
- 추천 엔진 연결 없음
- `law_control_map.json` 생성 없음
- 최종 판정: **PASS**

## 영향 범위

- `data/risk_db/hazard_action_normalized/` 신규 디렉토리 생성 (읽기 전용 결과물)
- `data/risk_db/law_mapping/control_law_ref_candidates.json` 추가
- 기존 파일 변경 없음

## 한계

- 모든 law_ref가 2개 법령(`statute:273603`, `statute:276853`)으로만 수렴
  → 조문 수준 세분화는 현재 normalized law 체계에서 불가 (법령 전체 단위만 지원)
- hazard_controls.json 항목 순서 변경 시 control_code 재생성 필요
  → 순서 고정 원칙 준수 필요

## 다음 단계

6단계 — `law_control_map` 초안 생성

착수 조건 모두 충족:
- control_code 공식 확정 완료
- law_id 정규화 완료 (90건 매칭)
- controls_normalized.json 기준 파일 준비 완료

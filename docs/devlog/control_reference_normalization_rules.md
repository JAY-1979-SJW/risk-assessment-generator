# control_code 기준 확정 및 law_ref 정규화 규칙

생성일: 2026-04-21
단계: 5.5단계

---

## 입력 파일

| 구분 | 경로 |
|---|---|
| control 기준 | `data/risk_db/hazard_action/hazard_controls.json` (90건) |
| hazard 기준 | `data/risk_db/hazard_action/hazards.json` (17건) |
| law 기준 | `data/risk_db/law_normalized/safety_laws_normalized.json` (52건) |

---

## 출력 파일

| 파일 | 설명 |
|---|---|
| `data/risk_db/hazard_action_normalized/controls_normalized.json` | 90건 정규화 완료 |
| `data/risk_db/hazard_action_normalized/controls_review_needed.json` | 0건 (검토 항목 없음) |
| `data/risk_db/law_mapping/control_law_ref_candidates.json` | 90건 후보 매칭 기록 |

---

## control_code 방식: 방식 B 선택

`{hazard_code}_C{nn:02d}` — hazard 내 입력 순서 기준 순번

```
FALL_C01, FALL_C02, ..., FALL_C11
ELEC_C01, ..., ELEC_C07
ASPHYX_C01, ..., ASPHYX_C07
```

선택 이유:
- 5단계 ra_link_schema에서 이미 사용한 기준과 동일
- 기존 hazard_controls.json에 control_code 필드 없어 방식 A 불가
- hazard별 그룹 관리에 최적
- 입력 순서 고정 필요 → hazard_controls.json 항목 순서를 공식 기준으로 확정

**주의**: hazard_controls.json 항목 순서가 변경되면 control_code 재생성 필요.
순서 변경 금지 원칙 준수.

---

## law_id 정규화 규칙

| law_ref 패턴 | 변환 law_id | 대상 법령명 |
|---|---|---|
| "기준에 관한 규칙" 포함 또는 "안전보건기준" 포함 | `statute:273603` | 산업안전보건기준에 관한 규칙 |
| "산업안전보건법" 포함 이면서 "기준" · "규칙" 미포함 | `statute:276853` | 산업안전보건법 |
| 위 두 패턴 미해당 | 매칭 실패 → review_needed |

결과:
- statute:273603 연결: 86건
- statute:276853 연결: 4건 (POISON_C01~C02, CHEM_C01~C02)
- 미매칭: 0건

---

## 후보 매칭 (control_law_ref_candidates.json)

law_ref 있는 모든 90건에 대해 후보 기록.

| status | 건수 |
|---|---|
| matched | 90 |
| multiple_candidates | 0 |
| no_match | 0 |

confidence: matched → 95, multiple_candidates → 70

---

## review_needed 분리 기준

아래에 해당하면 controls_review_needed.json 이동:
- control_code 생성 방식 애매 (순서 불명확 등)
- 동일 control 중복이면서 대표 코드 불명확
- law_ref 있으나 law_id 확정 불가 (패턴 미해당)
- 후보 law_id 2개 이상이나 우열 불분명
- control 문구 추상적이어서 그룹화 불가

이번 실행: 0건 (모든 law_ref가 2개 패턴 중 하나에 명확 해당)

---

## dedupe 기준

dedupe key: `hazard_code + control_text` 정규화
- 완전 중복 → duplicate_merged (하나 유지, 나머지 제거)
- hazard 다르고 의미 유사 → review 후보

이번 실행: 중복 0건

---

## normalization_status 분포

| status | 건수 | 설명 |
|---|---|---|
| normalized | 90 | control_code + law_id 모두 확정 |
| normalized_without_law | 0 | control은 정규화됐으나 law 연결 없음 |
| review_needed | 0 | 검토 필요 |
| duplicate_merged | 0 | 중복 통합 |

---

## 6단계(law_control_map) 착수 조건

필요 조건 | 상태
---|---
control_code 공식 확정 | **완료** (방식 B, 90건)
law_ref → law_id 정규화 | **완료** (90건 matched)
controls_normalized.json 생성 | **완료**
review_needed 처리 | **완료** (0건)
hazard_controls.json 순서 고정 원칙 | 확인 필요 (파일 수정 금지)

**판정: 6단계 착수 가능**

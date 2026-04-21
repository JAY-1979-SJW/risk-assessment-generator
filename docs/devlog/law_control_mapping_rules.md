# law_control_map 매핑 규칙

생성일: 2026-04-21
단계: 6단계 (control ↔ law 초안 매핑)

---

## 입력 파일

| 구분 | 경로 |
|---|---|
| control 기준 | `data/risk_db/hazard_action_normalized/controls_normalized.json` (90건) |
| law 기준 | `data/risk_db/law_normalized/safety_laws_normalized.json` (52건) |

---

## 출력 파일

| 파일 | 설명 |
|---|---|
| `data/risk_db/law_mapping/law_control_map.json` | draft 92건 |
| `data/risk_db/law_mapping/law_control_map_review_needed.json` | 0건 |

---

## source 우선순위

1. `statute` (법률/고용노동부령)
2. `admin_rule` (고시)
3. `licbyl` (별표·서식)
4. `interpretation` (해석례 — 보조만)

---

## match_type 정의

| match_type | 설명 |
|---|---|
| `prelinked_law_id` | 5.5단계 정규화 law_id 직접 사용 (1순위) |
| `related_law_match` | 동일 hazard 관련 해석례 보조 연결 |
| `exact_keyword` | control 명칭과 법령 제목 핵심어 직접 일치 |
| `partial_keyword` | 일부 키워드 일치 |
| `rule_based_inference` | hazard/control 규칙 기반 |

이번 단계에서 실제 사용: `prelinked_law_id` (90건), `related_law_match` (2건)

---

## score 규칙

### statute:273603 (안전보건기준에 관한 규칙)

| control_type | priority=1 | priority=2 |
|---|---|---|
| engineering | 92 | 82 |
| admin | 88 | 80 |
| ppe | 85 | 80 |

**절(section) 수준 참조 패널티**: -4 (조문이 아닌 절 참조: DROP 제14절, FLYBY 제14절)

### statute:276853 (산업안전보건법, 부모법)

| 조건 | score |
|---|---|
| 모든 유형 | 80 |

### interpretation (해석례, 보조 secondary)

| 조건 | score |
|---|---|
| FALL 안전난간 관련 | 72 |

### score 판정 기준

| 구간 | 판정 |
|---|---|
| 90~100 | 매우 강함 |
| 75~89 | 강함 |
| 60~74 | draft 후보 |
| 59 이하 | review_needed |

---

## prelinked law_id 처리 원칙

- `controls_normalized.json`의 `law_ids` 필드를 1순위로 사용
- 정규화 상태(`normalization_status=normalized`)인 항목만 대상
- prelinked score가 DRAFT_THRESHOLD(60) 미만이면 review_needed로 분리

---

## secondary 연결 원칙

- control 1건당 기본 최대 2건, 강한 근거 있을 때만 최대 3건
- secondary 연결 허용 대상:
  - FALL_C01, FALL_C11: `interpretation:313846` (추락·안전난간 해석례, score=72)
- 그 외 해석례: 해당 없음 (DB 내 나머지 29개 해석례가 직접 제어조치 근거와 무관)

---

## review_needed 분리 기준

아래는 review_needed로 분리:
- score < 60
- 동일 control에 3건 초과 후보
- 상위 일반법만 반복 연결 (direct 근거 없음)
- multiple candidate 간 우열 불분명
- interpretation만 있고 상위 법규 없음

이번 실행: 0건 (모든 prelinked 연결이 조건 충족)

---

## 이번 단계 한계

- 모든 control이 2개 법령(`statute:273603`, `statute:276853`)으로만 수렴
  → 조문 수준 매핑 불가 (현 law 체계가 법령 전체 단위)
- 안전보건규칙 내 세부 조문별 law_id가 없어 조문별 세분화 불가
- admin_rule, licbyl 연결 없음 (직접 control 근거 해당 없음)
- interpretation 연결 2건 외 확장 불가 (DB 내 해석례가 control 직접 근거와 무관)

---

## 다음 단계

7단계 — worktype/hazard/control/law 4축 통합 연결 적용 또는 RAG 엔진 통합

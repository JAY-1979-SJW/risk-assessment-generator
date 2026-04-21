# 위험성평가표 초안 라우터 구현 (9단계)

생성일: 2026-04-21
상태: 초안 구현 완료 (운영 미반영)

---

## 1. 라우터 경로

| Method | Path | 역할 |
|--------|------|------|
| POST | `/api/risk-assessment/draft/recommend` | worktype 기준 평가표 초안 생성 |
| POST | `/api/risk-assessment/draft/recalculate` | 사용자 수정 row 기반 재조립 |

기존 운영 라우터와 경로 충돌 없음. `draft` 네임스페이스 분리.

---

## 2. 파일 위치

| 역할 | 경로 |
|------|------|
| 라우터 | `backend/routers/risk_assessment_draft.py` |
| 스키마 | `backend/schemas/risk_assessment_draft.py` |
| 서비스 | `backend/services/risk_assessment_engine.py` |
| 테스트 | `tests/test_risk_assessment_draft_api.py` |

---

## 3. request/response 핵심 구조

### recommend 요청 필수 필드
```
work.work_type_code  (str, required)
```

### recalculate 요청 필수 필드
```
draft_context.work_type_code  (str, required)
rows[].row_id                  (str, required)
rows[].hazard_code             (str, required)
rows 최소 1건
```

### 응답 공통 구조
```
request_id, generated_at
work.{work_type_code, work_sub_type_code, work_name}
summary.{hazard_count, control_count, law_count}
rows[].{row_id, hazard, controls, laws, editable, row_flags}
review_flags[]
engine_meta.{pipeline_version, sources_used}
```

---

## 4. 에러 처리 규칙

| 조건 | HTTP |
|------|------|
| work_type_code 없음 / 빈 문자열 | 422 |
| 존재하지 않는 work_type_code | 404 |
| row_id 형식 불일치 (worktype/hazard_code) | 422 |
| rows 빈 배열 | 422 |
| max_hazards 범위 초과 (1~10) | 422 |
| invalid condition_flags | 422 |

---

## 5. row_id 규칙

형식: `{work_type_code}_{hazard_code}_{seq:03d}`

- seq: hazard_score 내림차순 기준 1-based
- recalculate 수신 시 `{work_type_code}_{hazard_code}_` prefix 검증
- 불일치 시 422 반환

---

## 6. review_flags 처리 규칙

| Flag | 판정 기준 |
|------|----------|
| `LOW_LAW_EVIDENCE` | law ≤1건 AND 모든 law_score < 55 |
| `CONTROL_ONLY_GENERAL_PPE` | 모든 control이 ppe 타입 |
| `HAZARD_SCORE_LOW` | hazard_score < 60 |
| `MANUAL_REVIEW_RECOMMENDED` | hazard_reason = rule_based_inference |
| `CONDITION_FLAG_MISSING` | worktype별 권장 flag 미입력 |
| `MAX_ROWS_REACHED` | 후보 > max_hazards |
| `DUPLICATE_CONTROL_ACROSS_ROWS` | 동일 control_code 복수 row 존재 |

---

## 7. editable / 원본 분리

- `controls[]`: 엔진 추천 원본 (control_code, control_name, control_score, reason)
- `editable.control_texts`: 사용자 수정용 str list (초기값 = control_name 복사)
- recalculate 시 custom_control_texts가 있으면 editable.control_texts에 반영

규칙: 두 필드를 절대 혼합 저장 금지. 저장 API 구현 시 별도 컬럼 사용.

---

## 8. 테스트 결과

12개 테스트 전체 PASS (2.41s)

| # | 테스트명 | 결과 |
|---|---------|------|
| 1 | recommend ELEC_LIVE 정상 | PASS |
| 2 | recommend WATER_MANHOLE 정상 | PASS |
| 3 | 존재하지 않는 work_type_code | PASS |
| 4 | work_type_code 누락 | PASS |
| 5 | options 범위 초과 | PASS |
| 6 | recalculate 정상 | PASS |
| 7 | 빈 rows recalculate | PASS |
| 8 | row_id 불일치 | PASS |
| 9 | editable/controls 분리 구조 검증 | PASS |
| 10 | CONDITION_FLAG_MISSING warning | PASS |
| 11 | TEMP_SCAFF row_id 형식 | PASS |
| 12 | LIFT_RIGGING row/control/law 포함 | PASS |

---

## 9. 운영 라우터로 전환 시 주의점

1. `backend/main.py` 라우터 등록은 이미 완료 — 운영 배포 전 경로 확인 필요
2. 저장 API 연결 시 assessor_id, project_id, status, version 필드 추가
3. `editable`과 `controls`를 DB에서 반드시 별도 컬럼으로 저장
4. 서비스 데이터 파일 경로: 로컬=`data/risk_db/`, 컨테이너=`/app/data/risk_db/` 자동 전환
5. `detail_link`는 현재 law_hazard_map의 실제 URL을 사용 (null 아님)
6. 운영 전 인증 미들웨어 적용 (현재 미적용)

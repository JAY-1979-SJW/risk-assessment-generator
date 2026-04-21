# 위험성평가표 생성 API 계약 규칙

생성일: 2026-04-21
버전: 1.0
상태: 설계 초안 (운영 미반영)

---

## 1. 엔드포인트

| ID | Method | Path | 역할 |
|----|--------|------|------|
| recommend_draft | POST | `/api/risk-assessment/recommend-draft` | worktype 기준 평가표 초안 생성 |
| recalculate_draft | POST | `/api/risk-assessment/recalculate-draft` | 사용자 수정 기반 control/law 재조립 |

---

## 2. 엔진과 API의 책임 분리

- **엔진**: hazard/control/law 후보 계산 및 점수 산출. HTTP 구조 미인식.
- **API**: 입력 검증 + 엔진 호출 + 응답 조립. 법령 매핑 로직 직접 구현 금지.

위반 금지:
- 엔진이 request/response JSON을 직접 파싱하는 구조 금지
- API가 `law_hazard_map.json`을 직접 읽어 매핑을 재구현하는 구조 금지

---

## 3. request 구조 요약

### recommend_draft

```
site_context.condition_flags  array[str]  optional  enum 5종
work.work_type_code            str         required
work.work_sub_type_code        str         optional
options.*                      int/bool    optional  서버 상한 적용
user_inputs.*                  array/str   optional
```

### recalculate_draft

```
draft_context.work_type_code      str         required
rows[].row_id                     str         required  원본 row_id
rows[].hazard_code                str         required
rows[].selected_control_codes     array[str]  optional
rows[].custom_control_texts       array[str]  optional
rows[].excluded_law_ids           array[str]  optional
options.rebuild_law_evidence      bool        default true
options.rescore_controls          bool        default true
```

---

## 4. response 구조 요약

```
request_id          UUID
work.*              worktype 메타
summary.*           hazard/control/law 건수
rows[]              hazard 기준 행 배열
  row_id            str  식별자
  hazard.*          코드, 이름, 점수, 이유
  controls[]        코드, 이름, 점수, 이유
  laws[]            id, title, score, evidence_paths, detail_link
  editable.*        사용자 수정 가능 필드 (엔진 원본과 분리)
  row_flags[]       행 수준 review flag
review_flags[]      전체 응답 수준 flag
engine_meta.*       파이프라인 버전, 사용 소스
```

---

## 5. row_id 규칙

형식: `{work_type_code}_{hazard_code}_{seq:03d}`

예시: `ELEC_LIVE_ELEC_001`, `TEMP_SCAFF_FALL_001`

- seq는 hazard_score 내림차순 기준 1-based
- recalculate_draft에서 동일 row_id로 재식별 가능해야 함
- 단순 배열 index 사용 금지

---

## 6. review_flags 규칙

| Flag | 조건 |
|------|------|
| `LOW_LAW_EVIDENCE` | 법령 근거 1건 미만 row 존재 |
| `CONTROL_ONLY_GENERAL_PPE` | 대책이 일반 PPE만 포함된 row |
| `HAZARD_SCORE_LOW` | hazard_score 60 미만 row |
| `MANUAL_REVIEW_RECOMMENDED` | rule_based_inference hazard 포함 |
| `CONDITION_FLAG_MISSING` | condition_flags 없이 생성 |
| `MAX_ROWS_REACHED` | max_hazards 상한 도달 |
| `DUPLICATE_CONTROL_ACROSS_ROWS` | 동일 control_code 2개 이상 row 중복 |

---

## 7. 샘플 대상 worktype

| code | 이름 | hazard 수 | 주요 condition_flag |
|------|------|-----------|---------------------|
| ELEC_LIVE | 활선 작업 | 1 | live_electric, high_place |
| TEMP_SCAFF | 비계 설치 | 3 | high_place |
| WATER_MANHOLE | 맨홀 내부 작업 | 2 | confined_space |
| LIFT_RIGGING | 리깅·줄걸이 | 3 | high_place |
| DEMO_ASBESTOS | 석면 해체 | 5 | chemical_use |

---

## 8. 현재 한계

- `detail_link` 미구현 (law_id → 법령 URL 매핑 미정)
- `CONDITION_FLAG_MISSING` flag 산출 조건 오류 (NOTE_009)
- recalculate_draft row_id 불일치 시 처리 규칙 미정
- 저장 API 연결 필드(assessor_id, project_id, status, version) 미포함

---

## 9. 다음 단계(9단계) 구현 시 보완점

1. 엔진 호출을 동기 함수로 먼저 구현, 지연 시 async 전환
2. options 서버 하드 상한 적용 (max_hazards ≤ 10)
3. request_id UUID4 생성 + 로그 기록
4. `CONDITION_FLAG_MISSING` flag 조건 수정
5. recalculate_draft row_id 불일치 시 400 에러 반환
6. law_title_short 필드 추가 또는 프론트 처리 결정
7. 저장 API 연결 필드 스키마 확정

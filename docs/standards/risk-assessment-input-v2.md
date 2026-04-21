# 위험성 평가 입력 구조 v2

## 개요

RAG Risk Engine v1.2 기반 위에 현장 조건 필드를 선택 입력으로 추가한 입력 스키마.
기존 v1 입력(process, sub_work, risk_situation)은 완전 유지되며, v2 필드는 있을 때만 엔진에 반영된다.

- 기존 엔진 로직 변경 없음 — BM25 쿼리 보강 방식으로만 반영
- v1 입력만 있어도 v1.2 결과와 동일하게 동작 (하위 호환)
- DB 마이그레이션: additive only (`002_assessment_input_v2.sql`)

---

## 필드 정의

### 필수 필드 (v1 유지)

| 필드 | 타입 | 설명 |
|------|------|------|
| `process` | string | 공정명 |
| `sub_work` | string | 세부작업명 |
| `risk_situation` | string | 위험상황 설명 |

### 선택 필드 — v1 (기존)

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `risk_category` | string \| null | null |
| `risk_detail` | string \| null | null |
| `current_measures` | string \| null | null |
| `legal_basis_hint` | string \| null | null |
| `top_k` | int (1–50) | 10 |

### 선택 필드 — v2 핵심 (현장 조건)

| 필드 | 타입 | 허용값 | 기본값 | 설명 |
|------|------|--------|--------|------|
| `height_m` | float \| null | >= 0 | null | 작업 높이(m) |
| `worker_count` | int \| null | >= 1 | null | 작업 인원 수 |
| `work_environment` | string \| null | indoor / outdoor / mixed | null | 작업 환경 |
| `night_work` | bool | true / false | false | 야간작업 여부 |
| `confined_space` | bool | true / false | false | 밀폐공간 여부 |
| `hot_work` | bool | true / false | false | 화기작업 여부 |
| `electrical_work` | bool | true / false | false | 전기작업 여부 |
| `heavy_equipment` | bool | true / false | false | 중장비 사용 여부 |
| `work_at_height` | bool | true / false | false | 고소작업 여부 (height_m과 독립 플래그) |

### 선택 필드 — v2 보조

| 필드 | 타입 | 허용값 | 기본값 | 설명 |
|------|------|--------|--------|------|
| `surface_condition` | string \| null | normal / wet / slippery / uneven | null | 바닥 상태 |
| `weather` | string \| null | clear / rain / snow / wind / extreme | null | 기상 조건 |
| `simultaneous_work` | bool | true / false | false | 동시작업 여부 |
| `hazard_priority_hint` | string \| null | (자유 텍스트) | null | 위험 우선순위 힌트 |

---

## Enum 정의

```python
WORK_ENVIRONMENT_VALUES = {'indoor', 'outdoor', 'mixed'}
SURFACE_CONDITION_VALUES = {'normal', 'wet', 'slippery', 'uneven'}
WEATHER_VALUES           = {'clear', 'rain', 'snow', 'wind', 'extreme'}
```

---

## Validation 규칙

### Error 조건 (ValueError — 엔진 실행 차단)

| 조건 | 설명 |
|------|------|
| `process` 빈 값 | 필수 필드 누락 |
| `sub_work` 빈 값 | 필수 필드 누락 |
| `risk_situation` 빈 값 | 필수 필드 누락 — 엔진 실행 금지 |
| `top_k` 범위 이탈 (1~50 아님) | 정수 범위 오류 |

### Warning 조건 (logger.warning — 실행 계속)

| 조건 | 처리 |
|------|------|
| enum 값 허용 범위 외 | None으로 처리, warning 로그 |
| `height_m` 음수 | None으로 처리, warning 로그 |
| `worker_count` < 1 | None으로 처리, warning 로그 |
| boolean coercion fallback | False로 처리, warning 로그 |

### Boolean Coercion 규칙

| 입력값 | 결과 |
|--------|------|
| `True`, `1`, `"true"`, `"yes"`, `"1"` | `True` |
| `False`, `0`, `"false"`, `"no"`, `""` | `False` |
| 기타 | `False` + warning |

---

## 엔진 반영 방식

v2 필드는 BM25 쿼리 문자열에 키워드 클러스터를 추가하는 방식으로 반영된다.
어셈블러나 청크 데이터를 직접 수정하지 않으며, 새 콘텐츠를 생성하지 않는다.

| 조건 | 추가 쿼리 토큰 | 의도 hazard 강화 |
|------|---------------|-----------------|
| `confined_space=True` | `밀폐공간 질식 산소결핍 환기` | 질식 |
| `hot_work=True` | `화기작업 화재 폭발 불꽃` | 화재 / 폭발 |
| `electrical_work=True` | `전기작업 감전 활선 절연` | 감전 |
| `work_at_height=True` 또는 `height_m > 2` | `고소작업 추락 안전대 안전난간` | 추락 |
| `heavy_equipment=True` | `중장비 충돌 낙하 신호수` | 충돌 / 낙하 |
| `night_work=True` | `야간작업 조명 시야` | 조명 부족 |
| `simultaneous_work=True` | `동시작업 협착 충돌 신호수` | 협착 / 충돌 |
| `hazard_priority_hint` 있음 | hint 텍스트 그대로 추가 | 자유 지정 |

---

## v1 → v2 호환 정책

- v2 필드가 없는 v1 입력은 v1.2 결과와 완전히 동일하게 동작
- v2 필드는 DB row에 컬럼이 없으면 mapper가 건너뜀 (`'height_m' in row` 체크)
- `project_assessments`에 v2 컬럼이 없는 레거시 DB도 오류 없이 동작
- v2 입력 시 confidence 하락 없음 (추가 보정만, 결과 제거 없음)

---

## DB 마이그레이션

파일: `engine/kras_connector/migrations/002_assessment_input_v2.sql`

```sql
ALTER TABLE project_assessments
    ADD COLUMN IF NOT EXISTS height_m          FLOAT,
    ADD COLUMN IF NOT EXISTS worker_count      INTEGER,
    ADD COLUMN IF NOT EXISTS work_environment  VARCHAR(20),
    ADD COLUMN IF NOT EXISTS night_work        BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS confined_space    BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS hot_work          BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS electrical_work   BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS heavy_equipment   BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS work_at_height    BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS surface_condition VARCHAR(20),
    ADD COLUMN IF NOT EXISTS weather           VARCHAR(20),
    ADD COLUMN IF NOT EXISTS simultaneous_work BOOLEAN NOT NULL DEFAULT FALSE;
```

전략: `ADD COLUMN IF NOT EXISTS` — 멱등, 기존 데이터 영향 없음.

---

## 수정된 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `engine/rag_risk_engine/schema.py` | RagInput v2 필드 추가, validate_input() 확장 |
| `engine/kras_connector/mapper.py` | v2 컬럼 선택적 매핑, enum/bool/number 검증 |
| `engine/rag_risk_engine/engine.py` | `_build_query()` — v2 플래그 기반 쿼리 보강 |
| `engine/kras_connector/migrations/002_assessment_input_v2.sql` | 신규 생성 |
| `engine/rag_risk_engine/tests/test_engine.py` | v2 테스트 8건 추가 (Test 25–32) |
| `engine/kras_connector/tests/test_service.py` | mapper v2 테스트 8건 추가 |

### 수정 금지 파일 (변경 없음)

| 파일 | 상태 |
|------|------|
| `status/**` | 미변경 |
| `backend/routers/engine_results.py` | 미변경 |
| `docs/standards/risk-assessment-web-baseline-v1.md` | 미변경 |

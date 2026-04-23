# form_builder v1 Spec Lock

**상태**: LOCKED — v1 기간 중 스키마/필드/규칙 변경 금지
**고정일**: 2026-04-23
**대상 파일**: `engine/kras_connector/form_builder.py`
**준거 스키마**: `data/risk_db/api_schema/kras_standard_form_v1.json`
**헤더 실증**: 공식 본표 4개 서식 (F1 KRAS 12컬럼 축약 + F2/F3/F4 공문기반 16컬럼) 검증 완료

---

## 1. 함수 시그니처 고정

```python
def build_risk_assessment_form(
    table_data: dict,
    header_input: dict,
    optional_input: dict | None = None,
) -> dict
```

### 입력

#### `table_data`
`engine.kras_connector.table_builder.build_risk_table_from_result()` 의 출력.
필수 키: `work_type`, `rows[]` (각 row 에 `process`, `hazard`, `current_risk`, `control_measures`, `residual_risk`, `references_summary`).

#### `header_input`
사용자 제공 상단 메타. 누락된 키는 `null` 유지 (자동 생성 금지).
허용 키:
- `company_name`, `site_name`, `industry`, `representative`, `assessment_type`, `assessment_date`, `work_type`

#### `optional_input` (선택)
운영 필드 사용자 입력. 두 가지 경로 지원:
- Flat: `{"sub_work": "...", "target_date": "...", ...}` — 모든 row 에 동일 적용
- Per-row: `{"rows": [{"sub_work": "..."}, ...]}` — 인덱스 기반 덮어쓰기
- Per-row 우선, Flat 대체.
- 허용 키: `sub_work`, `target_date`, `completion_date`, `responsible_person`.

### 출력

`kras_standard_form_v1` 스키마 준수 JSON 딕셔너리 (`form_version`, `header`, `scale_definition`, `rows`).

---

## 2. 계층 구조 고정 (헤더 실증 기반)

| 축 | 계층 | 필드 |
|----|------|------|
| **작업 계층** | 2단 | `process` (공정명) → `sub_work` (세부작업명) |
| **위험도 계층** | 3축 | `probability` (가능성/빈도) × `severity` (중대성/강도) = `risk_level` (1~9) + `risk_band` (low/medium/high/critical) |
| **조치 계층** | 3단 | `current_measures` (현재 안전보건조치) → `control_measures` (위험성 감소대책) → `residual_*` (개선후 위험성 4축) |
| **운영 필드** | 3개 | `target_date` (개선 예정일), `completion_date` (완료일), `responsible_person` (담당자) |
| **분류 필드** | 2단 | `hazard_category_major` (위험분류 대) / `hazard_category_minor` (위험분류 중) — 엔진 자동 생성 금지, null 유지 |

### 2.1 공종(work_category) 미포함 — 정책 고정

- 공식 본표 4개 서식(F1-F4) 모두 **공종 컬럼 없음**. 상단 메타에 `업종(industry)` 만 존재.
- v1 에서 공종 필드 **신규 추가 금지**. 공공공사 PQ 대응은 v1.2 에서 별도 승인 후 도입.

### 2.2 헤더 라벨 일치 (실증 확인)

| v1 필드 | 공식 본표 헤더 라벨 | 일치 |
|--------|----------------|------|
| `probability` | 가능성(빈도) | ✓ |
| `severity` | 중대성(강도) | ✓ |
| `risk_level` | 위험성 | ✓ |
| `control_measures` | 위험성 감소대책 | ✓ |
| `current_measures` | 현재의 안전보건조치 | ✓ |
| `process` | 공정명 (F2-F4) / 공정/작업명 (F1) | ✓ |
| `sub_work` | 세부작업명 (F2-F4) | ✓ (F1 축약형은 `process` 와 통합) |
| `legal_basis` | 관련근거(법적기준) | ✓ |

---

## 3. 자동 채움 / 사용자 입력 구분 (v1 정책)

| 필드 | 채움 주체 | 소스 | 비고 |
|------|---------|------|------|
| `no` | 엔진 | 행 인덱스 | 정렬 후 재부여 |
| `process` | 엔진 | `table_data.rows[].process` | |
| `hazard` | 엔진 | `table_data.rows[].hazard` | |
| `probability` / `severity` / `risk_level` / `risk_band` | 엔진 | `current_risk` 역산 (§ form_risk_mapping_rule) | |
| `control_measures` | 엔진 | `table_data.rows[].control_measures` | 원문 유지, 최대 7 |
| `residual_probability` / `residual_severity` / `residual_risk_level` / `residual_risk_band` | 엔진 | 역산 규칙 | |
| `risk_scale` | 엔진 | 상수 `"3x3"` | |
| `legal_basis` | 엔진 | `references_summary` 에서 카운트 주석 제거한 첫 문장 | |
| `references_detail` | 엔진 | `null` 유지 (table_builder 가 3축 ID 미전달) | v1.1에서 확장 |
| `sub_work` | 사용자 | `optional_input.sub_work` 또는 `optional_input.rows[i].sub_work` | 미입력 시 `null` |
| `target_date` / `completion_date` / `responsible_person` | 사용자 | `optional_input` (Flat 또는 per-row) | 미입력 시 `null` |
| `hazard_category_major` / `hazard_category_minor` | — | 항상 `null` | 자동 생성·사용자 입력 **모두 금지** |
| `current_measures` | — | 항상 `null` | 자동 생성 금지, v1 는 사용자 입력 슬롯도 미오픈 |
| `header.*` | 사용자 | `header_input.*` | 누락 시 `null` |

> 주의: `hazard_category_*` 와 `current_measures` 는 v1 에서 **엔진·사용자 입력 양쪽 모두 막는다**. 감사 대응용 수기 입력은 form_builder 호출 이후 상위 레이어에서 보강.

---

## 4. 정렬 및 번호 재부여

- 출력 row 는 `risk_level` DESC → `probability` DESC → `severity` DESC 순으로 정렬.
- 정렬 후 `no` 를 1 부터 재부여.
- 입력 table_data 의 row 순서(엔진 `confidence_score` DESC)는 본 form 단계에서 risk_level 기반으로 재계산되므로 동일하지 않을 수 있음.

---

## 5. 금지 사항 재확인

- 공종(work_category) 필드 추가 금지.
- `hazard_category_major/minor`, `current_measures` 자동 생성 금지.
- `references_detail` 에 임의 ID 삽입 금지.
- 공식 서식 4개에 없는 임의 컬럼 추가 금지.
- table_builder 출력에 없는 값(예: 날짜, 담당자, 실제 현장조치) 을 엔진이 창작하는 행위 금지.
- mapper.py / enrichment.py / API 라우터 수정 금지.

---

## 6. 호출 예시 (참고용)

```python
from engine.kras_connector.table_builder import build_risk_table_from_result
from engine.kras_connector.form_builder import build_risk_assessment_form

# 1) API 호출 → build API 결과 획득 (별도 경로)
# 2) table_builder 로 1차 변환
table = build_risk_table_from_result(api_result)

# 3) 본표 생성
form = build_risk_assessment_form(
    table_data=table,
    header_input={
        "company_name": "(주)해한 AI",
        "site_name": "OO 건설현장 A동 3층",
        "industry": "전문소방시설공사업",
        "representative": "홍길동",
        "assessment_type": "수시평가",
        "assessment_date": "2026-04-23",
    },
    optional_input={
        "rows": [
            {"sub_work": "옥상 간선 포설", "target_date": "2026-05-10", "responsible_person": "김안전"},
            {"sub_work": "옥상 간선 포설", "target_date": "2026-05-10", "responsible_person": "김안전"},
        ]
    },
)
```

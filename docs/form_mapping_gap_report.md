# table_builder ↔ KRAS 표준 본표 매핑 Gap 분석 (v1)

**목적**: 현재 `engine/kras_connector/table_builder.py` 가 생성하는 테이블 구조와 `kras_standard_form_v1.json` 본표 스키마 간 차이를 정리하고 보완 경로를 고정.
**작성일**: 2026-04-23

---

## 1. 현재 table_builder 출력 복습

```json
{
  "work_type": "전기작업",
  "rows": [
    {
      "process": "전기작업",
      "hazard": "감전",
      "current_risk": "High",       // 3단계 enum
      "control_measures": [...],    // 최대 7건
      "residual_risk": "Medium",    // 3단계 enum
      "references_summary": "..."   // 1문장 + [법령 N건 · 해석례 N건 · KOSHA N건]
    }
  ]
}
```

표준 본표 목표:

```json
{
  "form_version": "kras-standard-v1",
  "header":           { ... },
  "scale_definition": { "notation": "3x3", ... },
  "rows": [
    {
      "no": 1,
      "process":    "...",
      "sub_work":   null,
      "hazard_category_major": null,
      "hazard_category_minor": null,
      "hazard":     "...",
      "legal_basis": "...",
      "current_measures": null,
      "risk_scale": "3x3",
      "probability": 2,             // 1~3 정수
      "severity":    3,             // 1~3 정수
      "risk_level":  6,             // 곱
      "risk_band":   "high",
      "control_measures": [...],
      "residual_probability": 1,
      "residual_severity":    3,
      "residual_risk_level":  3,
      "residual_risk_band":  "medium",
      "target_date":        null,
      "completion_date":    null,
      "responsible_person": null,
      "references_detail":  { ... }  // 내부 (표시 금지)
    }
  ]
}
```

---

## 2. 필드별 Gap

| 본표 필드 | 현재 table_builder | Gap 유형 | 보완 경로 |
|----------|-----------------|---------|---------|
| `form_version` | — | **누락** | 변환 함수에서 상수 부여 |
| `header.*` | — | **누락** | 사용자 입력 파라미터로 주입 (엔진은 빈 슬롯만 제공) |
| `scale_definition` | — | **누락** | 고정값(3x3) 부여 |
| `no` | — | **누락** | row 인덱스로 자동 부여 |
| `process` | ✓ 있음 | 일치 | — |
| `sub_work` | — | **누락** | v1은 null 유지. API가 sub_work 반환하는 시점에 연결 |
| `hazard_category_major` | — | **누락** | 후속 매핑 테이블(분류 사전) 기반 유도. v1은 null 허용 |
| `hazard_category_minor` | — | **누락** | 동상 |
| `hazard` | ✓ 있음 | 일치 | — |
| `legal_basis` | △ `references_summary` 내부에 포함 | **형태 불일치** | `references_summary` 의 첫 문장 추출 → `legal_basis` 에 복사. 내부 `references_detail` 는 엔진 API의 `references` 필드 그대로 전달 |
| `current_measures` | — | **개념 불일치** | 본표의 "현재 조치" 는 현장 이미 적용 상태. 엔진은 모름. v1 은 null 로 두고 사용자 입력 |
| `risk_scale` | — | **누락** | 고정값 "3x3" |
| `probability` / `severity` | △ `current_risk` 단일 level | **정보 손실** | 변환 규칙 §3 (아래) |
| `risk_level` | — | **누락** | probability × severity 로 계산 |
| `risk_band` | △ `current_risk` 로 부분 대응 | 명칭·범위 불일치 | risk_level 기반 재부여 |
| `control_measures` | ✓ 있음 | 일치 | — |
| `residual_probability/severity/level/band` | △ `residual_risk` 단일 | **정보 손실** | 변환 규칙 §3 |
| `target_date` / `completion_date` / `responsible_person` | — | **누락** | v1 은 null. 운영 필드는 사용자 입력 |
| `references_detail` | △ API 응답의 `references` 를 전달하면 됨 | **전달 필요** | table_builder 입력을 API 원본으로 확장 |

---

## 3. 핵심: 3단계 level → probability × severity 변환

### 3.1 문제

현재 엔진 출력은 `confidence_score`(0~1)를 3단계 level 로 변환한 상태. 본표는 **가능성(1~3)×중대성(1~3)** 의 2축 분해를 요구.

정보 손실: 3단계 level → 2축 분해는 일의적으로 결정되지 않는다 (예: Medium=4 는 2×2, 4×1, 1×4 모두 가능).

### 3.2 v1 결정 (보수적 규칙)

3단계 level 을 "**안전측** 2축 분해" 로 매핑한다. "안전측" = 등급이 동일하거나 한 단계 더 보수적인 값.

| current_risk (현재 엔진 출력) | 본표 probability | 본표 severity | 본표 risk_level | 본표 risk_band |
|--------------------------|---------------|------------|---------------|--------------|
| `High` | 3 | 3 | 9 | critical |
| `Medium` | 2 | 3 | 6 | high |
| `Low` | 2 | 2 | 4 | medium |

> **근거**: 본 엔진의 `confidence_score ≥ 0.9 → High` 는 DB 가 법령 직접 명시 + 중대성 고위험으로 태깅한 hazard. 본표 전환 시 실무상 9(critical)로 취급해야 실제 현장 조치가 강화됨.
> **주의**: 이 매핑은 "법적으로 올바른 정규 분해" 가 아니며 감독관이 조사 시 각 축의 근거를 물을 수 있다. → v1.1 에서 DB 에 `probability_hint`, `severity_hint` 를 별도 저장해 분해 근거 보강 예정.

### 3.3 residual 매핑

현재 엔진은 `residual_risk` = level 1단계 감소(High→Medium→Low→Low).

| residual_risk | residual_probability | residual_severity | residual_risk_level | residual_risk_band |
|-------------|-------------------|-----------------|-------------------|------------------|
| Medium | 1 | 3 | 3 | medium |
| Low | 1 | 2 | 2 | low |

**원칙**: 중대성(severity) 은 조치로 감소하지 않는다고 본다 (사고 발생 시 중대성은 물리적 속성). 감소는 주로 가능성(probability) 에서 발생한다. → residual 은 probability 만 낮춘 결과로 구성.

---

## 4. 적시 출력 가능 여부

| 구분 | 상태 |
|------|------|
| **즉시 출력 가능** | 본표 row 법적 필수 컬럼(process, hazard, probability, severity, risk_level, control_measures) 전부 — 단, probability/severity 분해 규칙은 §3의 보수적 매핑 사용 |
| **즉시 출력 가능(권장 포함)** | legal_basis(`references_summary` 첫문장 분리), residual 3축, risk_band |
| **엔진 미제공 — null 유지** | header 메타(사용자 입력 슬롯), sub_work, hazard_category_*, current_measures, target_date/completion_date/responsible_person |

**결론**: **법적 필수·실무 권장 컬럼 14개 중 11개** 는 현재 엔진 단계에서 채울 수 있고, 3개(세부작업·위험분류·현재조치)는 v1 에서 null 로 두고 사용자/운영 입력으로 보강해야 한다.

---

## 5. 즉시 구현 가능한 변환 함수 개요 (아직 구현 금지 — 설계만)

```python
# engine/kras_connector/form_builder.py  (v1.1 이후 구현 예정)

def build_kras_form(
    api_result: dict,           # POST /api/v1/risk-assessment/build 응답
    header: dict,               # 사용자 제공 메타 (company_name, site_name, ...)
) -> dict:
    """
    KRAS 표준 본표(kras_standard_form_v1) 출력.

    내부 단계:
    1. header.work_type ← api_result.work_type  (공정명 기본값 원천)
    2. hazards 순회 → probability/severity 역산 (§3.2)
    3. control_measures 상위 7개 절삭
    4. legal_basis ← evidence_summary 첫 문장
    5. residual 역산 (§3.3)
    6. references_detail ← api_result.hazards[].references (내부 전달)
    7. risk_level DESC 재정렬
    """
```

> 본 문서는 **설계 확정** 까지만 포함. 구현 단계는 v1.1(명시적 사용자 승인 후) 이후.

---

## 6. 후속 작업 목록

| # | 작업 | 우선순위 |
|---|------|--------|
| 1 | `form_builder.py` 구현 (v1.1) | 높음 |
| 2 | hazard → 대분류/중분류 매핑 사전 구축 | 중 |
| 3 | DB에 `probability_hint`/`severity_hint` 컬럼 추가 (mapping 데이터 세분화) | 중 |
| 4 | XLSX 실제 렌더 (`export/` 기존 템플릿 활용) | 중 |
| 5 | 사용자 입력 슬롯 UI (header/운영필드) | 낮음 — UI 단계 |

---

## 7. 판정

**즉시 출력 가능 수준** — 법적 필수 9개, 실무 권장 6개, 건설 특화 1개 중 **13~14개 필드** 를 엔진 출력 + 보수적 변환만으로 채울 수 있다. 나머지는 사용자 입력 슬롯으로 null 유지해 양식 제출 가능성을 저해하지 않는다.

# KRAS 표준 위험성평가표 본표 출력 양식 v1

**상태**: LOCKED — v1 기간 중 스키마 변경 금지
**시행일**: 2026-04-23
**스키마 파일**: `data/risk_db/api_schema/kras_standard_form_v1.json`
**준거**:
- 산업안전보건법 제36조
- 산업안전보건법 시행규칙 제37조
- 고용노동부고시 제2023-19호 (사업장 위험성평가에 관한 지침)
- 고용노동부 건설업 위험성평가 활용가이드
- 공문기반 본표 양식 v2 (`export/위험성평가표_공문기반_20250114_v2.xlsx`)

---

## 1. 양식 범위

본 문서는 **본표(위험성평가실시표) 1종** 만 정의한다.

- 공문기반 서식 16컬럼(Full) 과 KRAS 축약 12컬럼(Compact) 양쪽 수용.
- 시트 1~4(방침·조직·기준·회의)는 이 v1 에서 **생성 대상 아님**. 상단 메타(`header`)만 고정 슬롯 제공.

---

## 2. 최상위 구조

```
{
  "form_version": "kras-standard-v1",
  "header":            { ... },          # 상단 메타
  "scale_definition":  { ... },          # 위험성 추정 방식 (기본 3x3)
  "rows":              [ { ... }, ... ], # 본표 행 — hazard 1건 = row 1행
  "input_context":     { ... }?          # v2 API enrichment echo
}
```

---

## 3. 상단 메타 (`header`)

| 필드 | 필수 | 타입 | 소스 | 설명 |
|------|------|------|------|------|
| `company_name` | △ | string | 사용자 입력 | 회사명 |
| `site_name` | △ | string | 사용자 입력 | 현장명/사업장명 |
| `industry` | △ | string | 사용자 입력 | 업종 |
| `representative` | △ | string | 사용자 입력 | 대표자 |
| `assessment_type` | ✓ | enum | 사용자 입력 | `최초평가` / `정기평가` / `수시평가` / `상시평가` |
| `assessment_date` | ✓ | date | 사용자 입력 | YYYY-MM-DD |
| `work_type` | — | string | 엔진 | KRAS build API 입력 원본 |

△ 표기: 법적 필수(시행규칙 §37)이나 엔진은 사용자 입력을 기다림. 비어 있어도 스키마 검증은 통과(후속 단계에서 강제화 예정).

---

## 4. 위험성 추정 방식 (`scale_definition`)

v1 고정값: **3×3 곱셈식** (고용노동부 표준).

| 항목 | 값 |
|------|----|
| notation | `"3x3"` |
| 가능성(빈도) | 1(하) / 2(중) / 3(상) |
| 중대성(강도) | 1(소) / 2(중) / 3(대) |
| 위험성 | 가능성 × 중대성 (1~9) |
| 등급 | 1~2 low / 3~4 medium / 6 high / 9 critical |

고시 §7 허용 다른 방식(4×4, 체크리스트) 은 v2+ 에서 도입.

---

## 5. 본표 행 (`rows[].*`)

### 5.1 법적 필수 컬럼

| 필드 | 법적 근거 | 설명 |
|------|---------|------|
| `no` | — | 행 번호 1부터 |
| `process` | §37-1호 | 공정명 |
| `hazard` | §37-1호 | 유해위험요인 서술 |
| `current_measures` | §37-3호(현행 조치 포함) | 현재 안전보건조치 (미입력 시 null 허용) |
| `probability` | §37-2호 | 가능성 1~3 |
| `severity` | §37-2호 | 중대성 1~3 |
| `risk_level` | §37-2호 | probability × severity |
| `risk_band` | — | 등급 (low/medium/high/critical) |
| `control_measures` | §37-3호 | 감소대책 배열 (1~7건) |

### 5.2 실무 권장 컬럼

| 필드 | 근거 | 설명 |
|------|------|------|
| `hazard_category_major` | KOSHA 분류 | 대분류 (추락/감전/화재 등) |
| `hazard_category_minor` | KOSHA 분류 | 중분류 |
| `legal_basis` | 고시 §8 | 관련 조문 |
| `risk_scale` | 고시 §7 | 평가척도 (기본 "3x3") |
| `residual_probability` | 고시 §12 | 개선후 가능성 |
| `residual_severity` | 고시 §12 | 개선후 중대성 |
| `residual_risk_level` | 고시 §12 | residual_probability × residual_severity |
| `residual_risk_band` | — | 개선후 등급 |
| `target_date` | 고시 §13 | 개선 예정일 |
| `completion_date` | 고시 §13 | 완료일 |
| `responsible_person` | 고시 §13 | 담당자 |

### 5.3 건설업 특화

| 필드 | 근거 | 설명 |
|------|------|------|
| `sub_work` | 건설업 활용가이드 — 단위작업 원칙 | 세부작업명 |

### 5.4 내부(비표시) 필드

| 필드 | 설명 |
|------|------|
| `references_detail.{law_ids, moel_expc_ids, kosha_ids}` | 엔진이 출력한 3축 참조 ID. **표 컬럼에 노출 금지**. 내부 추적 용도. |

---

## 6. 정렬 규칙

- `rows[]` 는 `risk_level` **DESC** 정렬을 기본값으로 한다.
- 동값인 경우 `probability` DESC → `severity` DESC 순.
- 엔진 출력 정렬(`confidence_score` DESC)은 위험도 계산 후 재정렬된다.

---

## 7. 금지 사항

- v1 스키마 외 임의 필드 추가 금지 (`additionalProperties: false`).
- `related_expc_ids` 또는 기타 내부 DB 컬럼명 노출 금지.
- `references_detail` 은 **응답 구조에 포함 가능**하나 **표(render) 출력 컬럼으로 노출 금지**.
- 위험성 수치(1~9) 외 임의 지표(예: 5점 척도) 혼합 금지.

---

## 8. 후속 버전 계획

| 버전 | 변경 |
|------|------|
| v1 (현재) | 본표 단독, 3×3 고정 |
| v1.1 | XLSX 실제 출력 (본 스키마 → `openpyxl` 렌더) |
| v1.2 | 등록부 scheme 확장 |
| v2 | 4×4 / 체크리스트 척도 지원, 회의록·조직구성 fillable |

---

## 9. 매핑 시 주의 (table_builder → 본표)

`engine/kras_connector/table_builder.py` 의 3단계 risk level(`High/Medium/Low`) 출력은 본표의 2축(probability/severity)과 **정보 손실 없이 양방향 변환이 불가능**하다.

- 현재 table_builder 출력을 본표로 옮기려면 **probability/severity 역산 규칙**이 필요.
- 이 규칙은 `form_mapping_gap_report.md` 에서 정의한다.

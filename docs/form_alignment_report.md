# form_builder ↔ 공식 본표 정합성 보고 (v1)

**대상**: `engine/kras_connector/form_builder.py`
**검증 기준**: 공식 본표 4개 서식 (F1 KRAS 축약 12컬럼, F2/F3/F4 공문기반 16컬럼)
**샘플 출력**: `docs/sample_form_output_3cases.json`

---

## 1. 공식 헤더 라벨 매핑

| 공식 헤더 (F2/F3/F4 16컬럼) | form_builder 출력 필드 | 일치 |
|------------------------|--------------------|------|
| 공정명 | `rows[].process` | ✓ |
| 세부작업명 | `rows[].sub_work` (optional_input) | ✓ (사용자 입력) |
| 위험분류 (대) | `rows[].hazard_category_major` | ✓ 컬럼 존재, 값은 null (v1 정책) |
| 위험분류 (중) | `rows[].hazard_category_minor` | ✓ 컬럼 존재, 값은 null (v1 정책) |
| 유해위험요인 (서술) | `rows[].hazard` | ✓ |
| 관련근거 (법적기준) | `rows[].legal_basis` | ✓ (references_summary 1문장 추출) |
| 현재의 안전보건조치 | `rows[].current_measures` | ✓ 컬럼 존재, 값은 null (v1 정책) |
| 평가척도 | `rows[].risk_scale` | ✓ 고정 `"3x3"` |
| **가능성(빈도)** | `rows[].probability` | ✓ 정수 1~3 |
| **중대성(강도)** | `rows[].severity` | ✓ 정수 1~3 |
| 위험성 | `rows[].risk_level` | ✓ p × s (1~9) |
| 위험성 감소대책 | `rows[].control_measures` | ✓ 배열 (최대 7) |
| 개선후 위험성 | `rows[].residual_risk_level` + `residual_probability`/`severity`/`risk_band` | ✓ 4축 분해 |
| 개선 예정일 | `rows[].target_date` | ✓ (optional_input) |
| 완료일 | `rows[].completion_date` | ✓ (optional_input) |
| 담당자 | `rows[].responsible_person` | ✓ (optional_input) |

### F1 KRAS 축약 12컬럼과의 매핑

F1 은 16컬럼에서 `위험분류(대/중)`, `평가척도`, `개선 예정일` 을 생략한 축약형. form_builder 출력은 상위집합이므로 **F1 도 수용 가능** (불필요 컬럼을 필터링해서 출력하면 됨).

---

## 2. 계층 구조 검증

| 축 | 공식 서식 | form_builder | 일치 |
|----|---------|-------------|------|
| 작업 계층 (2단) | 공정명 → 세부작업명 | `process` → `sub_work` | ✓ |
| **공종 (work_category)** | **공식 4개 서식 모두 부재** | **미추가** (v1 정책) | ✓ |
| 위험도 3축 | 가능성 × 중대성 = 위험성 | `probability`×`severity`=`risk_level` | ✓ |
| 조치 3단 | 현재조치 / 감소대책 / 개선후 | `current_measures` / `control_measures` / `residual_*` | ✓ |
| 운영 3필드 | 개선예정일 / 완료일 / 담당자 | `target_date`/`completion_date`/`responsible_person` | ✓ |

---

## 3. 자동채움 / 사용자 입력 구분 (v1)

| 필드 | 자동/수동 | 샘플 실측 |
|------|---------|---------|
| `no` | 자동 | CASE1 1-4, CASE2 1-4, CASE3 1-4 — 정렬 후 재부여 ✓ |
| `process` | 자동 | `table_data.work_type` 값 ✓ |
| `hazard` | 자동 | 엔진 hazard 원문 ✓ |
| `probability`/`severity`/`risk_level`/`risk_band` | 자동 | 역산 규칙 일치 ✓ |
| `control_measures` | 자동 | 엔진 원문 보존 (최대 7) ✓ |
| `residual_*` (4축) | 자동 | 역산 규칙 일치 ✓ |
| `risk_scale` | 자동 | 고정 `"3x3"` ✓ |
| `legal_basis` | 자동 | `references_summary` 첫 문장 추출 (카운트 주석 제거) ✓ |
| `references_detail` | 자동 | null (v1: table_builder 가 3축 ID 미전달) |
| **`sub_work`** | **수동** (optional_input) | CASE1/2: "옥상 전기간선 포설…"/"맨홀 진입…" 반영, CASE3: null ✓ |
| **`target_date`** | **수동** | CASE1/2: "2026-05-10"/"2026-05-05", CASE3: null ✓ |
| **`completion_date`** | **수동** | 전 케이스 미입력 → null ✓ |
| **`responsible_person`** | **수동** | CASE1/2: "김안전/이철수", CASE3: null ✓ |
| **`hazard_category_major/minor`** | **강제 null** | 3 케이스 전부 null ✓ |
| **`current_measures`** | **강제 null** | 3 케이스 전부 null ✓ |
| `header.*` | **수동** | 3 케이스 모두 사용자 입력 반영 ✓ |

---

## 4. 위험도 역산 규칙 검증 (3 케이스 전체)

### CASE 1 (전기)
| hazard | 입력 current | 입력 residual | 출력 p×s=level (band) | 출력 res_p×res_s=res_level (band) | 판정 |
|--------|-----------|--------------|---------------------|----------------------------------|------|
| 감전 | High | Medium | 3×3=9 (critical) | 2×3=6 (high) | ✓ |
| 추락 | High | Medium | 3×3=9 (critical) | 2×3=6 (high) | ✓ |
| 아크·화재 | Medium | Low | 2×3=6 (high) | 1×3=3 (medium) | ✓ |
| 협착 | Medium | Low | 2×3=6 (high) | 1×3=3 (medium) | ✓ |

### CASE 2 (밀폐공간)
| hazard | 입력 current | 출력 p×s=level | 출력 res_p×res_s=res_level | 판정 |
|--------|-----------|---------------|---------------------------|------|
| 질식 | High | 3×3=9 (critical) | 2×3=6 (high) | ✓ |
| 중독 | Medium | 2×3=6 (high) | 1×3=3 (medium) | ✓ |
| 화재·폭발 | Medium | 2×3=6 (high) | 1×3=3 (medium) | ✓ |
| 구조지연 | **Low** | 2×2=4 (medium) | **2×2=4 (medium) — 변화 없음** | ✓ (Low→Low 규칙) |

### CASE 3 (고소 legacy)
| hazard | 입력 current | 출력 p×s=level | 출력 res_p×res_s=res_level | 판정 |
|--------|-----------|---------------|---------------------------|------|
| 추락 | High | 3×3=9 (critical) | 2×3=6 (high) | ✓ |
| 낙하물 | Medium | 2×3=6 (high) | 1×3=3 (medium) | ✓ |
| 전도 | Medium | 2×3=6 (high) | 1×3=3 (medium) | ✓ |
| 협착 | Medium | 2×3=6 (high) | 1×3=3 (medium) | ✓ |

**모든 케이스 `form_risk_mapping_rule.md` 규칙과 100% 일치.**

---

## 5. 공종(work_category) 미포함 정책 검증

```
>>> any('work_category' in r for r in form['rows'])
False  # 3 케이스 전부

>>> 'work_category' in form['header']
False  # 3 케이스 전부

>>> 'work_category' in form
False  # 3 케이스 전부
```

**공종 필드는 출력 어디에도 존재하지 않음.** 정책 준수 확인.

---

## 6. 빈도 / 강도 / 대책 라벨 일치 확인

| 항목 | 공식 헤더 | 스키마 `label` (required_fields_matrix.json) | form_builder 키 | 일치 |
|------|---------|-------------------------------------------|---------------|------|
| 빈도 | 가능성(빈도) | `"가능성 (빈도)"` | `probability` | ✓ 개념·의미 일치 |
| 강도 | 중대성(강도) | `"중대성 (강도)"` | `severity` | ✓ |
| 대책 | 위험성 감소대책 | `"위험성 감소대책"` | `control_measures` | ✓ |

> 필드 키는 영문(probability/severity/control_measures)이나, 공식 서식 렌더링 단계(v1.1 XLSX 출력)에서 한글 라벨로 대응 표기된다.

---

## 7. 판정

| 항목 | 결과 |
|------|------|
| 공정명 + 세부작업명 2단 구조 | ✓ PASS |
| 공종(work_category) 미추가 | ✓ PASS (3 케이스 모두 필드 부재) |
| 빈도/강도/위험성 감소대책 라벨 일치 | ✓ PASS |
| 위험도 역산 규칙 적용 | ✓ PASS (8 hazard 전부) |
| residual 역산 (Low→Low 포함) | ✓ PASS |
| 자동채움/사용자입력 구분 | ✓ PASS |
| hazard_category_*/current_measures null 유지 | ✓ PASS |
| 헤더 실증과 v1 정책 정합 | ✓ PASS |

**최종: PASS**

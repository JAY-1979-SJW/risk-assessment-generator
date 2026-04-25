# 안전서류 마스터 카탈로그 v1.0

**작성일**: 2026-04-24  
**기준**: legal_required_forms_inventory.md + legal_form_gap_matrix.md + form_authority_matrix.md v4 + legal_form_autofill_matrix.md  
**입력 문서 수**: 기준 자료 7종  
**총 개설 서류**: 23건 (EXCLUDED 3건 포함)

---

## 범례

| 컬럼 | 설명 |
|------|------|
| `doc_id` | 고유 식별자 (카테고리 접두사 + 순번) |
| `obligation_type` | 작성/비치/보존/제출 (복수 가능) |
| `legal_form_exists` | 법정 별지/별표 존재 여부 |
| `source_authority` | A_OFFICIAL / B_GUIDE / C_FIELD / GEN_INTERNAL |
| `current_status` | DONE / PARTIAL / TODO / EXCLUDED |
| `builder_exists` | builder 파일 존재 여부 |
| `api_exists` | registry 등록 + export API 연결 완료 여부 |
| `source_file_exists` | source_map.csv 수집 여부 |
| `autofill_ratio` | 자동 채움 가능 항목 비율 (legal_form_autofill_matrix 기준) |
| `priority` | P0 완료 / P1~P4 구현 순위 |

---

## 전체 카탈로그

### 위험성평가 (RISK)

| doc_id | doc_name_ko | category_lv1 | category_lv2 | legal_basis | obligation_type | legal_form_exists | source_authority | current_status | builder_exists | api_exists | source_file_exists | autofill_ratio | user_input_ratio | priority | note |
|--------|-------------|-------------|-------------|------------|----------------|:-----------------:|:----------------:|:--------------:|:-------------:|:---------:|:-----------------:|:-------------:|:---------------:|:-------:|------|
| RISK-001 | 위험성평가표 (실시표) | 위험성평가 | 본표 | 산안법 제36조, 고시 제2023-19호 | 작성·보존 | ✗ (고시 예시) | A_OFFICIAL | **DONE** | Y | Y | Y | 39% | 61% | P0 | kras_standard_form_v1 기준. form_type: risk_assessment |
| RISK-002 | 위험성평가 자체점검표 | 위험성평가 | 점검표 | 고시 제2023-19호 제11조 | 작성·비치 | ✗ | B_GUIDE | TODO | N | N | △ (B등급) | - | - | P4 | B등급 자율점검표류 임시 활용 |

---

### 교육기록 (EDU)

| doc_id | doc_name_ko | category_lv1 | category_lv2 | legal_basis | obligation_type | legal_form_exists | source_authority | current_status | builder_exists | api_exists | source_file_exists | autofill_ratio | user_input_ratio | priority | note |
|--------|-------------|-------------|-------------|------------|----------------|:-----------------:|:----------------:|:--------------:|:-------------:|:---------:|:-----------------:|:-------------:|:---------------:|:-------:|------|
| EDU-001 | 안전보건교육일지 | 교육기록 | 교육일지 | 산안법 제29조, 시행규칙 제32조 | 작성·보존(3년) | ○ 별지 제52호의2 | GEN_INTERNAL | **DONE** | Y | Y | △ (B등급) | 56% | 44% | P0 | 별지 원본 미수집, B등급 임시. form_type: education_log |
| EDU-002 | 교육훈련 기록부 (교육대장) | 교육기록 | 기록부 | 시행규칙 제28조 | 작성·보존(3년) | ✗ | GEN_INTERNAL | TODO | N | N | N | - | - | P4 | 교육일지와 이중 기록 구조, 통합 검토 필요 |

---

### 작업계획서 (WP)

| doc_id | doc_name_ko | category_lv1 | category_lv2 | legal_basis | obligation_type | legal_form_exists | source_authority | current_status | builder_exists | api_exists | source_file_exists | autofill_ratio | user_input_ratio | priority | note |
|--------|-------------|-------------|-------------|------------|----------------|:-----------------:|:----------------:|:--------------:|:-------------:|:---------:|:-----------------:|:-------------:|:---------------:|:-------:|------|
| WP-001 | 굴착 작업계획서 | 작업계획서 | 토공 | 기준규칙 제38조·제82조 | 작성·비치 | ✗ | GEN_INTERNAL | **DONE** | Y | Y | N | 47% | 53% | P0 | 굴착면 2m 이상. form_type: excavation_workplan |
| WP-002 | 차량계 건설기계 작업계획서 | 작업계획서 | 기계류 | 기준규칙 제38조·제170조 | 작성·비치 | ✗ | GEN_INTERNAL | TODO | N | N | N | 65% | 35% | **P1** | workplan_builder 패턴 재사용 |
| WP-003 | 차량계 하역운반기계 작업계획서 | 작업계획서 | 기계류 | 기준규칙 제38조 제1항 제2호 | 작성·비치 | ✗ | GEN_INTERNAL | TODO | N | N | N | 63% | 37% | **P1** | 지게차 포함, 제조·물류 공통 |
| WP-004 | 타워크레인 작업계획서 | 작업계획서 | 양중 | 기준규칙 제38조 제1항 제1호 | 작성·비치 | ✗ | GEN_INTERNAL | TODO | N | N | N | - | - | P2 | 중대재해 다발 고위험 |
| WP-005 | 중량물 취급 작업계획서 | 작업계획서 | 중량물 | 기준규칙 제38조 제1항 제11호 | 작성·비치 | ✗ | GEN_INTERNAL | TODO | N | N | N | - | - | P2 | 제조·물류·건설 광범위 |
| WP-006 | 터널 굴착 작업계획서 | 작업계획서 | 토공 | 기준규칙 제38조 제1항 제7호 | 작성·비치 | ✗ | GEN_INTERNAL | TODO | N | N | N | - | - | P3 | 터널공사 한정 |
| WP-007 | 건축물 해체 작업계획서 | 작업계획서 | 해체 | 기준규칙 제38조 제1항 제10호 | 작성·비치 | ✗ | GEN_INTERNAL | TODO | N | N | N | - | - | P3 | 해체공사 한정 |
| WP-008 | 화학설비 작업계획서 | 작업계획서 | 화학 | 기준규칙 제38조 제1항 제4호 | 작성·비치 | ✗ | GEN_INTERNAL | TODO | N | N | N | - | - | P4 | 화학·석유화학 한정 |
| WP-009 | 거푸집동바리 작업계획서 | 작업계획서 | 건설 | 기준규칙 제38조 제1항 제13호 | 작성·비치 | ✗ | GEN_INTERNAL | TODO | N | N | N | - | - | P4 | 건설 한정 |
| WP-010 | 교량 건설 작업계획서 | 작업계획서 | 건설 | 기준규칙 제38조 제1항 제8호 | 작성·비치 | ✗ | GEN_INTERNAL | TODO | N | N | N | - | - | P4 | 대형건설 한정 |

---

### 재해보고 (ACC)

| doc_id | doc_name_ko | category_lv1 | category_lv2 | legal_basis | obligation_type | legal_form_exists | source_authority | current_status | builder_exists | api_exists | source_file_exists | autofill_ratio | user_input_ratio | priority | note |
|--------|-------------|-------------|-------------|------------|----------------|:-----------------:|:----------------:|:--------------:|:-------------:|:---------:|:-----------------:|:-------------:|:---------------:|:-------:|------|
| ACC-001 | 산업재해조사표 | 재해보고 | 조사표 | 산안법 제57조, 시행규칙 제73조 | 제출(1개월 이내)·보존(3년) | ○ 별지 제30호 | A_OFFICIAL | TODO | N | N | Y (A등급) | 21% | 79% | **P2** | 과태료 1,500만원. 별지 수집 완료 |

---

### 회의록 (MTG)

| doc_id | doc_name_ko | category_lv1 | category_lv2 | legal_basis | obligation_type | legal_form_exists | source_authority | current_status | builder_exists | api_exists | source_file_exists | autofill_ratio | user_input_ratio | priority | note |
|--------|-------------|-------------|-------------|------------|----------------|:-----------------:|:----------------:|:--------------:|:-------------:|:---------:|:-----------------:|:-------------:|:---------------:|:-------:|------|
| MTG-001 | 산업안전보건위원회 회의록 | 회의록 | 위원회 | 산안법 제24조, 시행규칙 별표 2의2 | 작성·보존(2년) | ○ 별표 제2의2 | A_OFFICIAL | TODO | N | N | Y (A등급) | 64% | 36% | **P2** | 100인 이상 사업장. 별지 수집 완료 |
| MTG-002 | 노사협의체 회의록 | 회의록 | 협의체 | 산안법 제75조, 시행규칙 제79조 | 작성·보존(2년) | ○ 별표 31의2 | A_OFFICIAL | TODO | N | N | N | - | - | P3 | 건설 120억 이상 한정. 별표 미수집 |

---

### 도급관리 (CON)

| doc_id | doc_name_ko | category_lv1 | category_lv2 | legal_basis | obligation_type | legal_form_exists | source_authority | current_status | builder_exists | api_exists | source_file_exists | autofill_ratio | user_input_ratio | priority | note |
|--------|-------------|-------------|-------------|------------|----------------|:-----------------:|:----------------:|:--------------:|:-------------:|:---------:|:-----------------:|:-------------:|:---------------:|:-------:|------|
| CON-001 | 유해·위험작업 도급승인 신청서 | 도급관리 | 승인신청 | 산안법 제59조, 시행규칙 별지 제31호 | 제출(도급 전) | ○ 별지 제31호 | A_OFFICIAL | TODO | N | N | Y (A등급) | 64% | 36% | P3 | 도금·수은 등 유해위험 도급 한정. 별지 31·32·33·34호 수집 완료 |

---

### 유해위험방지 (HRP)

| doc_id | doc_name_ko | category_lv1 | category_lv2 | legal_basis | obligation_type | legal_form_exists | source_authority | current_status | builder_exists | api_exists | source_file_exists | autofill_ratio | user_input_ratio | priority | note |
|--------|-------------|-------------|-------------|------------|----------------|:-----------------:|:----------------:|:--------------:|:-------------:|:---------:|:-----------------:|:-------------:|:---------------:|:-------:|------|
| HRP-001 | 제조업 유해위험방지계획서 | 유해위험방지 | 제조업 | 산안법 제42조, 시행규칙 별지 제16호 | 제출(착공 전 공단 심사) | ○ 별지 제16·18·19호 | A_OFFICIAL | TODO | N | N | Y (A등급) | 60% | 40% | P3 | 미심사 시 설치·운전 금지. 첨부 多 |
| HRP-002 | 건설공사 유해위험방지계획서 | 유해위험방지 | 건설업 | 산안법 제42조, 시행규칙 별지 제17호 | 제출(착공 전 공단 심사) | ○ 별지 제17·22·103호 | A_OFFICIAL | TODO | N | N | Y (A등급) | 60% | 40% | P3 | 공사금액 50억 이상. 미제출 시 착공 금지 |

---

### 범위 외 (EXCLUDED)

| doc_id | doc_name_ko | category_lv1 | category_lv2 | legal_basis | obligation_type | legal_form_exists | source_authority | current_status | builder_exists | api_exists | source_file_exists | autofill_ratio | user_input_ratio | priority | note |
|--------|-------------|-------------|-------------|------------|----------------|:-----------------:|:----------------:|:--------------:|:-------------:|:---------:|:-----------------:|:-------------:|:---------------:|:-------:|------|
| PSM-001 | 공정안전보고서 (PSM) | PSM | 보고서 | 산안법 제44조 | 제출(착공 전) | ○ | A_OFFICIAL | **EXCLUDED** | N | N | N | - | - | - | 대규모 화학·석유화학 한정, 수백 페이지 보고서 |
| REG-001 | 안전보건관리규정 | 안전관리비 | 규정집 | 산안법 제25조 | 작성·비치 | △ 별표 2·3 | A_OFFICIAL | **EXCLUDED** | N | N | Y | - | - | - | 규정집 형태, builder 부적합 |
| TBM-001 | TBM(Tool Box Meeting) 일지 | 회의록 | TBM | 법정 의무 없음 | - | ✗ | B_GUIDE | **EXCLUDED** | N | N | △ (B등급) | - | - | - | 법정 의무 아님, 자유 형식 |

---

## 집계 요약

### 개설 서류 수

| 구분 | 건수 |
|------|------|
| 전체 개설 | **23건** |
| EXCLUDED 제외 감사 대상 | **20건** |

### 카테고리별 수

| category_lv1 | 감사 대상 | DONE | TODO |
|-------------|:--------:|:----:|:----:|
| 위험성평가 | 2 | 1 | 1 |
| 교육기록 | 2 | 1 | 1 |
| 작업계획서 | 10 | 1 | 9 |
| 재해보고 | 1 | 0 | 1 |
| 회의록 | 2 | 0 | 2 |
| 도급관리 | 1 | 0 | 1 |
| 유해위험방지 | 2 | 0 | 2 |
| **합계** | **20** | **3** | **17** |

### 구현 상태 분포

| 판정 | 건수 | 비율 |
|------|:----:|:----:|
| DONE | 3 | 15% |
| TODO | 17 | 85% |
| EXCLUDED | 3 | — |

### source_authority 분포 (감사 대상 20건)

| 등급 | 건수 | 설명 |
|------|:----:|------|
| A_OFFICIAL | 9 | 법정 별지/별표 수집됨 (builder 연결은 별개) |
| GEN_INTERNAL | 11 | 법정 별지 없음 — 시스템 자체 생성 표준 |

### 법정 별지 수집 현황

| 구분 | 건수 |
|------|:----:|
| A등급 별지 수집 완료 | 9건 |
| 미수집 (법정 별지 없음) | 11건 |

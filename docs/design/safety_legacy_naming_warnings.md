# 안전서류 evidence legacy 명명 WARN 정리표

작성일: 2026-04-26
최근 보완:
- 2026-04-26 (정합성 1차 수정 — WARN 수 vs 파일 수 분리, 예측 수치 회수)
- 2026-04-26 (WP-015 evidence 정규화 배치 완료 — 분류 B 4건 표준명 전환)
- 2026-04-26 (G-02 / G-03 evidence 정규화 배치 완료 — 분류 A 중 HM 연결 2건 표준명 전환)
- 2026-04-26 (stale 검증 헬퍼 정리 — `verify_safety_law_refs.py` G-02/G-03 하드코딩을 표준명으로 갱신, one-shot legacy helper 표기)
작성자: lint_safety_naming.py 보강 단계
출처 가드 스크립트: `scripts/lint_safety_naming.py`

> **본 문서의 분류 B (WP-015) 4파일은 2026-04-26 정규화 배치로 표준명 전환 완료.**
> 표준명 적용 후 lint 결과 재산정 수치는 본 문서 9절 "정규화 배치 결과" 참고.

---

## 0. 용어 정의 (정합성 기준)

본 문서와 lint 보고서에서 다음 용어를 엄격히 구분한다.

| 용어 | 정의 | 현재 값 |
|------|------|--------|
| `warning_count` | lint 가 출력한 WARN **메시지 수** (한 파일이 여러 메시지를 동시 유발 가능) | 12 |
| `affected_evidence_files` | 1개 이상의 WARN 을 발생시킨 evidence 파일 **distinct 수** | 8 |
| `legacy_warning_count` | WARN 메시지 중 legacy 분류 수 | 12 |
| `standard_warning_count` | WARN 메시지 중 표준 명명 분류 수 | 0 |
| `future_blocking_errors` | 정규화 배치 시 즉시 FAIL 로 승격될 후보 메시지 수 | 4 |

> **혼동 주의**: "evidence 12건" 같은 표현은 **사용 금지**.
> 정확히는 "lint WARN 메시지 12건, 영향 파일 8건" 으로 표기한다.

---

## 1. 배경

`scripts/lint_safety_naming.py` 신규 도입 시점에 evidence 디렉토리
(`data/evidence/safety_law_refs/`) 를 전수 검사한 결과,
표준 명명 규칙

```
{DOC_ID}-{TYPE}{N}_{snake_case}.json
  DOC_ID  ∈  {WP|EQ|RA|ED|PTW|DL|CL|PPE|CM|HM|EM|TS|SP}-NNN
  TYPE    ∈  L | K | M | P
  COMMON  ∈  ELEC-001 | FIRE-001 | LIFT-001 | HEIGHT-001 | CONFINED-001
```

을 따르지 않는 legacy 파일이 검출되었다 (WARN 메시지 12건 / 영향 파일 8건).
**이 파일들은 신규 builder 구현 단계 이전부터 존재했던 자료이며,
실제 builder · 추천엔진 · catalog evidence_file 참조와의 정합성은 별도로 유지되고 있다.**

본 문서는 lint 가 WARN 으로 분류한 파일을 **언제 어떻게 정규화할지** 추적하기 위한 정리표다.
**현재 단계에서는 rename / 이동을 수행하지 않는다.** (정책: 실제 파일 이동 금지)

---

## 2. WARN 분류 요약

| # | 분류 | 영향 파일 수 | WARN 메시지 수 | 처리 방침 |
|---|------|------------|----------------|----------|
| A | 구 item_no 체계 (DOC_ID 미준수) — `C-06` / `E-06` / `G-02` / `G-03` | 4 | 4 (파일당 1건) | 보존 — catalog 가 `item_no` 로 별도 참조 / G-02·G-03 는 정규화 배치 검토 |
| B | TYPE/N 누락 + evidence_id 와 head 불일치 (WP-015) | 4 | 8 (파일당 2건) | 다음 정규화 배치에서 일괄 rename |
| **합계** |  | **8** | **12** |  |

> 본 표의 "영향 파일 수 합 (8)" 은 lint 의 `affected_evidence_files=8` 과 일치한다.
> "WARN 메시지 수 합 (12)" 은 lint 의 `warning_count=12` 와 일치한다.

---

## 3. 분류 A — 구 item_no 체계 evidence (영향 파일 4건 / WARN 4건)

### 3.1 목록

| 현재 파일명 | 내부 evidence_id | 내부 document_id | 내부 item_no | 예상 표준 파일명 | 참조 영향 |
|------------|------------------|------------------|---------------|-----------------|----------|
| `C-06_industrial_safety_health_act_article_31.json` | (없음) | `EDU_CONSTRUCTION_BASIC` | `C-06` | (해당 없음 — 별도 카탈로그) | catalog 외부 자료 |
| `E-06_worker_license_refs.json`                      | (없음) | `worker_licenses.yml`     | `E-06` | (해당 없음 — 별도 자료)     | 라이선스 참조용 |
| `G-02_industrial_safety_health_act_article_125.json` | (없음) | `HM-001`                  | `G-02` | `HM-001-L1_industrial_safety_health_act_article_125.json` | catalog HM-001 evidence_id="G-02" 로 직접 참조 |
| `G-03_industrial_safety_health_act_article_130.json` | (없음) | `HM-002`                  | `G-03` | `HM-002-L1_industrial_safety_health_act_article_130.json` | catalog HM-002 evidence_id="G-03" 로 직접 참조 |

### 3.2 처리 방침

- **현재 단계에서 rename 보류.**
- C-06 / E-06: catalog 90종 안전서류 외 보조자료 (기초안전보건교육 / 면허 참조) — DOC_ID 체계와 다른 별도 코드체계로 운영. lint 는 단순 WARN 만.
- **G-02 / G-03 (HM-001 / HM-002 evidence) 은 catalog 의 `evidence_id` 가 `"G-02"` / `"G-03"` 으로 박혀 있다.**
  - 단순 파일 rename 만으로는 부족. catalog evidence_id 값과 evidence_file 경로 양쪽을 동시에 갱신해야 함.
  - 갱신 시 builder · validate_form_registry · audit_safety_90_completion · validate_document_recommender 모두 영향 가능 — 회귀 위험 존재.
- 결론: **별도 "evidence 정규화 배치" 단계에서 함께 수행한다.** 이번 lint 보강 단계에서는 추적표 작성까지만.

---

## 4. 분류 B — WP-015 evidence (영향 파일 4건 / WARN 8건 — 파일당 2건씩)

### 4.1 목록

| 현재 파일명 | 내부 evidence_id | 내부 document_id | 예상 표준 파일명 | 참조 영향 |
|------------|------------------|------------------|-----------------|----------|
| `WP-015_safety_rule_article_38.json`           | `WP-015-L1` | `WP-015` | `WP-015-L1_safety_rule_article_38.json` | catalog WP-015 evidence_file 참조 |
| `WP-015_safety_rule_article_39.json`           | `WP-015-L2` | `WP-015` | `WP-015-L2_safety_rule_article_39.json` | catalog WP-015 evidence_file 참조 |
| `WP-015_safety_rule_article_331.json`          | `WP-015-L3` | `WP-015` | `WP-015-L3_safety_rule_article_331.json` | catalog WP-015 evidence_file 참조 |
| `WP-015_safety_rule_articles_328_337.json`     | `WP-015-L4` | `WP-015` | `WP-015-L4_safety_rule_articles_328_337.json` | catalog WP-015 evidence_file 참조 |

### 4.2 처리 방침

- **내부 `evidence_id` 는 표준 (`WP-015-L1~L4`) 이지만 파일명에 TYPE/N 이 빠져 있다.**
- 따라서 lint 는 1파일당 WARN 2개를 기록한다.
  - WARN-1: "legacy 명명 (TYPE/N 누락)"
  - WARN-2: "legacy evidence_id 불일치 (파일명 head ≠ evidence_id)"
- 표준 파일명으로 rename 할 경우 다음 위치도 동시 수정해야 한다.
  - `data/masters/safety/documents/document_catalog.yml` 의 WP-015 `evidence_file` 4건 (현재 파일명 그대로 박혀 있음).
  - 향후 추가될 수 있는 builder 의 evidence reference (현재 builder 는 파일명 직접 의존하지 않음 — 확인 완료).
- 결론: **catalog evidence_file 4건 동시 갱신 + 파일 4건 rename 을 한 트랜잭션으로 처리.**
  본 단계에서는 정책상 rename 금지이므로 다음 evidence 정규화 배치에서 수행.

---

## 5. 추후 정규화 배치 체크리스트

evidence 정규화 배치 단계에서 수행할 작업 (별도 PR 권장):

- [ ] WP-015 evidence 4파일 rename → 표준명 적용
- [ ] catalog WP-015 `evidence_file` 4건 갱신 (rename 과 동일 커밋)
- [ ] G-02 → `HM-001-L1`, G-03 → `HM-002-L1` rename 검토 (catalog evidence_id 값 변경 동반)
- [ ] C-06 / E-06 별도 자료 위치로 이동 검토 (evidence/safety_law_refs 외부)
- [ ] rename 후 `python scripts/lint_safety_naming.py` 결과 재산정
- [ ] 회귀 검증: lint 1종 WARN (`lint_safety_naming`), readiness audit 1종 WARN (`audit_safety_90_completion`), 기능 회귀 검증 5종 PASS (`validate_form_registry` / `smoke_test_p1_forms` / `validate_document_recommender` / `audit_safety_gap` / `validate_safety_platform_skeleton`) 유지

### 5.1 정규화 후 예상 WARN 수치

> **예측 수치는 본 문서에 명시하지 않는다.** dry-run 또는 별도 스크립트로 사전 계산한 근거가 없는 상태에서 "12 → N" 식의 단정적 수치를 박아두면 다음 단계 보고서에서 또 다른 정합성 충돌을 유발할 수 있다.
>
> 정규화 배치를 실제로 수행한 직후, 그 시점의 lint 결과로 **재산정** 한다.
> (재산정 명령: `python scripts/lint_safety_naming.py`)

---

## 6. 본 단계 (2026-04-26) rename 보류 사유

1. **정책**: 본 lint 보강 단계의 작업 범위는 "lint 검사 범위와 legacy WARN 추적성 보강"으로 한정.
   실제 evidence 파일 rename · catalog 상태 변경은 명시적으로 금지됨.
2. **회귀 위험 분리**: rename 은 catalog evidence_id / evidence_file 동시 갱신을 동반하므로
   smoke test 회귀 위험을 분리하기 위해 별도 배치로 미룬다.
3. **추적성 우선**: 본 문서로 추적표를 남겨 두면 향후 어떤 시점이든 정규화 배치 진입 가능.

---

## 7. 향후 lint 회귀 동작

`scripts/lint_safety_naming.py` 는 본 항목들을 WARN 으로 분류하며,
**legacy 항목이 정규화되어 PASS 영역으로 이동하면 자동으로 WARN 카운트가 감소**한다.
신규 evidence 가 표준명을 위반할 경우 `kind ∈ {standard, common_pack, extended}` 분기에서 즉시 FAIL 처리된다 (Rule 4/5/7).

---

## 8. 보조 메모 (정합성 보강 시점 추가)

### 8.1 `engine/output/builders/` 디렉토리 미존재는 정상 상태

lint 결과의 `checked_recursive_paths` 에서
`engine_output_builders_subdir → matched=0` 항목이 표시된다.
이는 **현 시점 builders/ 서브디렉토리가 도입되어 있지 않음**을 의미하며 오류가 아니다.
모든 builder 는 현재 `engine/output/` 직하에 평면 배치되어 있고,
lint 는 추후 builders/ 도입 시점에 자동 인식하기 위한 사전 등록 상태일 뿐이다.

→ lint 출력에서는 `[INFO/NOT_PRESENT]` 태그로 노출된다 (FAIL 아님).

### 8.2 `audit_safety_90_completion.py` PASS 와 HM-001 / HM-002 `TEST_MISSING` 의 관계

- `audit_safety_90_completion.py` 의 최종 판정 **PASS** 는 "감사 스크립트 자체가 정상 실행되어 현황표를 산출했음" 을 의미한다.
  카탈로그 90종 전체가 release 가능한 상태라는 뜻이 아니다.
- 본 감사는 final_readiness 분포를 표시하며, 그 중
  - `HM-001` (작업환경측정 실시 및 결과 관리대장)
  - `HM-002` (특수건강진단 대상자 및 결과 관리대장)
  2건이 **`TEST_MISSING`** 상태 (evidence VERIFIED + builder DONE 이지만 smoke_test 미작성).
- 본 단계 lint 보강 작업은 `TEST_MISSING` 을 해소하지 않는다 (lint 와 무관한 별 트랙).
- **release-strict 기준** (예: `final_readiness ∈ {READY}` 만 출하 허용) 을 적용할 경우
  `HM-001` / `HM-002` 의 `TEST_MISSING` 은 **FAIL 후보**로 간주될 수 있다.
  현재 audit 의 PASS 는 release-strict 기준이 아닌 **"실행 성공 + 현황 감사 PASS"** 로 해석해야 한다.
- HM smoke test 작성은 본 lint 정합성 보강과 독립된 후속 작업으로 트래킹.

---

## 9. 정규화 배치 결과 (2026-04-26 — 분류 B 적용)

### 9.1 처리 항목

WP-015 evidence 4파일을 표준 명명 규칙으로 일괄 rename 했다 (한 트랜잭션).

| 변경 전 | 변경 후 |
|---------|---------|
| `WP-015_safety_rule_article_38.json`        | `WP-015-L1_safety_rule_article_38.json` |
| `WP-015_safety_rule_article_39.json`        | `WP-015-L2_safety_rule_article_39.json` |
| `WP-015_safety_rule_article_331.json`       | `WP-015-L3_safety_rule_article_331.json` |
| `WP-015_safety_rule_articles_328_337.json`  | `WP-015-L4_safety_rule_articles_328_337.json` |

내부 `evidence_id` 값 (`WP-015-L1` ~ `WP-015-L4`) 은 변경하지 않았다 (이미 표준).
내부 `evidence_file` 필드만 새 파일명에 맞춰 갱신.

### 9.2 동시 갱신 항목 (한 트랜잭션)

- `data/masters/safety/documents/document_catalog.yml` WP-015 `evidence_file` 4건 — 새 파일명으로 갱신
- `scripts/smoke_test_p1_forms.py` `WP015_EXPECTED_EVIDENCE_FILES` 4건 — 새 파일명으로 갱신
- `data/evidence/safety_law_refs/CL-002-L1/L2/L3` 의 `related_evidence` 문서 cross-reference 문자열 — 새 파일명으로 갱신
- 4개 WP-015 evidence JSON 파일의 내부 `evidence_file` 필드 — 새 파일명으로 갱신

### 9.3 변경하지 않은 항목 (정책상 분리)

- `C-06`, `E-06` (분류 A) — 90종 catalog 외 보조자료, 별도 트랙
- `G-02`, `G-03` (분류 A, HM-001 / HM-002 evidence) — catalog `evidence_id` 값 변경을 동반하므로 회귀 위험 분리 차원에서 별 트랙

### 9.4 lint 재산정 수치

`scripts/lint_safety_naming.py` 실행 결과 기반 (배치 직후).

| 지표 | 배치 전 | 배치 후 |
|------|--------|--------|
| `errors` | 0 | **0** |
| `warning_count` | 12 | **4** |
| `legacy_warning_count` | 12 | **4** |
| `affected_evidence_files` | 8 | **4** |
| `future_blocking_errors` | 4 | **0** |

남은 4건은 모두 분류 A (`C-06` / `E-06` / `G-02` / `G-03`) — 분류 B 는 0건.

### 9.5 후속 트랙

- 분류 A (G-02 / G-03) — HM-001 / HM-002 catalog `evidence_id` 변경을 동반하는 별 트랙 정규화. **→ 10절에서 완료.**
- 분류 A (C-06 / E-06) — 별도 자료 위치로 이동 검토. 본 lint 정합성과 별개 트랙.

---

## 10. 정규화 배치 결과 (2026-04-26 — 분류 A 중 HM 연결 2건 적용)

### 10.1 처리 항목

G-02 / G-03 evidence 2파일을 표준 명명 규칙으로 rename 하고, catalog `evidence_id` 값을 `"G-02"` / `"G-03"` → `"HM-001-L1"` / `"HM-002-L1"` 로 동시 갱신했다 (한 트랜잭션).

| 변경 전 파일명 | 변경 후 파일명 | catalog evidence_id (변경 전 → 변경 후) |
|---------------|---------------|----------------------------------------|
| `G-02_industrial_safety_health_act_article_125.json` | `HM-001-L1_industrial_safety_health_act_article_125.json` | `"G-02"` → `"HM-001-L1"` |
| `G-03_industrial_safety_health_act_article_130.json` | `HM-002-L1_industrial_safety_health_act_article_130.json` | `"G-03"` → `"HM-002-L1"` |

### 10.2 동시 갱신 항목 (한 트랜잭션)

- evidence 파일 2건 rename
- 각 evidence JSON 에 `evidence_id` 필드 신규 추가 (`"HM-001-L1"` / `"HM-002-L1"`)
- 각 evidence JSON 의 내부 `evidence_file` 필드 갱신 (legacy 그대로였던 것을 새 파일명으로)
- `data/masters/safety/documents/document_catalog.yml`:
  - HM 카테고리 헤더 코멘트 (1줄)
  - HM-001 `evidence_id` / `evidence_file` / `notes` 3줄
  - HM-002 `evidence_id` / `evidence_file` / `notes` 3줄
- `scripts/smoke_test_p1_forms.py`:
  - HM-001 / HM-002 섹션 헤더 코멘트 (2줄)
  - `HM001_EXPECTED_EVIDENCE_IDS` / `HM001_EXPECTED_EVIDENCE_FILES` (4줄)
  - `HM002_EXPECTED_EVIDENCE_IDS` / `HM002_EXPECTED_EVIDENCE_FILES` (4줄)

### 10.3 보존 (변경하지 않음)

- evidence 내부 `item_no` 필드 — 역사적 추적용 메타데이터로 보존 (`G-02` / `G-03` 그대로)
- `docs/design/safety_gap_audit_report.md`, `safety_gap_matrix.md`, `docs/reports/safety_collection_coverage_audit.md` — 시점별 audit 기록물이므로 회고적으로 수정하지 않음
- `scripts/verify_safety_law_refs.py` — P0 1회성 검증 헬퍼 스크립트로, 7종 검증 파이프라인에 포함되지 않으므로 본 배치 범위 외. 재실행 시점에 별도 갱신 필요 (남은 WARN 절 참고)
- C-06 / E-06 — 사용자 정책상 본 단계 변경 금지

### 10.4 lint 재산정 수치

`scripts/lint_safety_naming.py` 실행 결과 기반 (배치 직후).

| 지표 | 분류 B 배치 후 (직전) | 분류 A-HM 배치 후 (현재) |
|------|----------------------|--------------------------|
| `errors` | 0 | **0** |
| `warning_count` | 4 | **2** |
| `legacy_warning_count` | 4 | **2** |
| `affected_evidence_files` | 4 | **2** |
| `future_blocking_errors` | 0 | **0** |

남은 WARN 2건은 정확히 분류 A 잔여 (`C-06` / `E-06`) — 분류 A 중 HM 연결 2건 (`G-02` / `G-03`) 은 0건.

---

## 11. stale 검증 헬퍼 정리 및 잔여 WARN 보존 기준선 (2026-04-26)

### 11.1 stale 하드코딩 정리

`scripts/verify_safety_law_refs.py` 내부 G-02 / G-03 항목의 `evidence_file` 하드코딩이 9·10절 정규화 배치 이후에도 구 파일명을 가리키는 상태였다 (`G-02_industrial_safety_health_act_article_125.json` / `G-03_industrial_safety_health_act_article_130.json`). 구 파일은 디스크에서 제거된 상태이므로, 헬퍼를 재실행할 경우 stale 파일을 재생성하여 lint WARN 회귀를 유발할 위험이 있었다.

본 단계에서 다음을 수행했다.

- `verify_safety_law_refs.py` G-02 / G-03 `evidence_file` 값을 표준명 (`HM-001-L1_*` / `HM-002-L1_*`) 으로 갱신
- 동 스크립트 상단 docstring 에 **ONE-SHOT LEGACY HELPER** 명시 (정기 회귀 7종 파이프라인 외부 헬퍼임을 분명히 표기)
- 내부 `item_no` 메타데이터 (`"G-02"` / `"G-03"`) 는 9·10절 보존 정책에 따라 변경하지 않음 (역사적 추적용)

### 11.2 변경하지 않은 항목 (정책상 분리)

- `data/masters/safety/documents/document_catalog.yml` — 변경 없음
- `engine/output/form_registry.py` / builder / `engine/recommendation/document_recommender.py` — 변경 없음
- `data/evidence/safety_law_refs/C-06_*.json` / `E-06_*.json` — 변경 없음 (분류 A 잔여 2건)

### 11.3 잔여 WARN 2건 보존 사유 (기준선 고정)

| evidence 파일 | 내부 식별자 | 보존 사유 |
|---------------|-------------|----------|
| `C-06_industrial_safety_health_act_article_31.json` | `EDU_CONSTRUCTION_BASIC` (training) | 기초안전보건교육 보조자료. 90종 catalog 외 자료 — DOC_ID 체계가 아닌 별도 코드체계 (`training_code`) 로 운영 |
| `E-06_worker_license_refs.json`                      | `worker_licenses.yml`              | 운전원 자격/면허 참조. 90종 catalog 외 자료 — `license_id` 코드체계로 운영 |

두 파일 모두 다음 특성을 공유한다.
- `data/masters/safety/documents/document_catalog.yml` 의 `evidence_file` 필드에서 직접 참조하지 않음
- builder / form_registry / document_recommender 어디서도 파일명에 직접 의존하지 않음
- catalog 90종 안전서류 외 보조자료 (교육과정·자격면허 메타) 로 별도 트랙

따라서 두 파일은 lint WARN 카테고리 A 잔여로 **현 상태로 보존**한다. 이동·rename 시 별도 코드체계 마이그레이션이 동반되므로 별 트랙으로 분리한다.

### 11.4 lint 재산정 수치 (기준선)

`scripts/lint_safety_naming.py` 실행 결과 (stale 헬퍼 정리 직후).

| 지표 | 분류 A-HM 배치 후 (직전) | stale 헬퍼 정리 후 (현재 기준선) |
|------|--------------------------|----------------------------------|
| `errors` | 0 | **0** |
| `warning_count` | 2 | **2** |
| `legacy_warning_count` | 2 | **2** |
| `affected_evidence_files` | 2 | **2** |
| `future_blocking_errors` | 0 | **0** |

본 단계에서는 lint 입력(evidence 파일·catalog) 변경이 없으므로 수치는 직전과 동일하다. **이 수치를 PASS-with-warnings 기준선**으로 고정한다.

기준선 검증 7종의 카테고리 분류:

| 분류 | 스크립트 | 본 기준선에서의 판정 |
|------|---------|---------------------|
| lint (1종) | `lint_safety_naming` | **WARN** (PASS-with-warnings, exit=0; legacy WARN 2건 보존) |
| readiness audit (1종) | `audit_safety_90_completion` | **WARN** (READY=18, TEST_MISSING=0, EVIDENCE_MISSING=15, TODO=57, OUT=3) |
| 기능 회귀 검증 (5종) | `validate_form_registry` / `smoke_test_p1_forms` / `validate_document_recommender` / `audit_safety_gap` / `validate_safety_platform_skeleton` | **PASS** (5종 모두) |

기준선 표기: **lint 1종 WARN, readiness audit 1종 WARN, 기능 회귀 검증 5종 PASS 유지.**

### 11.5 후속 트랙 (본 단계 외)

- C-06 / E-06 별도 자료 위치로 이동 (예: `data/evidence/training_refs/`, `data/evidence/license_refs/`) — 별 트랙 정규화 배치 사항. 본 단계 정책상 금지.
- `verify_safety_law_refs.py` 의 `apply_verified()` 내 catalog/training/license 마스터 패치 로직 — 7종 파이프라인 외부 동작이며, 마스터 변경이 필요한 시점에만 별도 검증·승인 후 사용.

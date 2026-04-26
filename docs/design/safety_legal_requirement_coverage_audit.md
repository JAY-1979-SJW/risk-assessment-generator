# 법령·지침 의무 누락 감사 설계
# safety_legal_requirement_coverage_audit.md
# 버전: 1.0 | 작성일: 2026-04-26 | 기준선: READY 36/90 = 40.0%

---

## 1. 설계 원칙

| 원칙 | 내용 |
|------|------|
| source of truth | 법령·고시·지침 원문 (DRF API 조회 또는 KOSHA/국토부 원문 파일) |
| AI 역할 | 후보 분류 및 설명 보조만. 의무 확정 불가 |
| 최종 판정 | rule matrix + 검증 스크립트 |
| 법정/실무 분리 | `legal_status=legal` vs `practical` 반드시 구분 |
| 교육 기준 | 장비 대수 기준 금지. 근로자/작업내용/위험작업 기준으로 판정 |
| 장비 대수 기준 | 점검·검사·반입·운전원 배치에서만 처리 |

---

## 2. 현재 catalog 커버리지 분석

### 2-1. 문서 현황 (93종)

| category_code | 카테고리명 | 전체 | legal | practical | optional |
|---|---|---|---|---|---|
| WP | 법정 작업계획서 | 15 | 15 | 0 | 0 |
| EQ | 장비 사용계획서 | 16 | 8 | 7 | 1 |
| RA | 위험성평가 관련 | 6 | 2 | 4 | 0 |
| ED | 안전보건교육 관련 | 5 | 4 | 1 | 0 |
| PTW | 작업허가서 | 8 | 1 | 7 | 0 |
| DL | 일일 안전관리 | 5 | 0 | 5 | 0 |
| CL | 점검표 | 10 | 4 | 6 | 0 |
| PPE | 보호구 관리 | 4 | 2 | 2 | 0 |
| CM | 협력업체 관리 | 7 | 4 | 3 | 0 |
| EM | 사고 비상대응 | 6 | 4 | 2 | 0 |
| TS | 공종별 특화 | 5 | 5 | 0 | 0 |
| SP | 실무 보강 | 4 | 0 | 2 | 2 |
| HM | 보건관리 | 2 | 2 | 0 | 0 |
| **합계** | | **93** | **51** | **39** | **3** |

### 2-2. 구현 현황 (READY 36/90)

- implementation_status=DONE : 36종
- evidence 커버 document_id : 39종 (일부 미완성 포함)
- compliance_clauses 수록 : 28조항 (requirement_type 필드 미입력 상태)
- mappings 수록 :
  - equipment_document_requirements : 8건 (장비 31종 대비 부족)
  - equipment_training_requirements : 7건
  - equipment_inspection_requirements : 9건
  - work_document_requirements : 8건
  - work_training_requirements : 7건

### 2-3. 핵심 갭 — 누락 의무 유형

현재 catalog·compliance·mappings 어디에도 아래 의무 유형이 체계적으로 분류되지 않음:

| 누락 의무 유형 | 현황 | 근거 법령 예시 |
|---|---|---|
| 자격·면허 (qualification) | E-06 evidence만 존재, catalog 미연결 | 건설기계관리법, 산안법 시행령 별표 1 |
| 안전검사 (safety_inspection) | CC-028만 존재, 장비별 매핑 없음 | 산안법 제93조, 시행령 별표 22 |
| 설치 전 점검 (pre_installation_check) | CL-001/002만 존재 | 산안규칙 제57조, 제328조 |
| 사용 전 검사 (pre_use_inspection) | 매핑 없음 | 산안규칙 제146조 (크레인 작업 전) |
| 기록 보존 (record_retention) | 증거 없음 | 산안법 제164조, 산안규칙 제4조 |
| 안전관리비 (safety_cost) | TS-004만 존재, 계산 로직 없음 | 건설기술진흥법 시행규칙 별표 8 |
| 도급 승인 (subcontract_approval) | CM-002만 존재 | 산안법 제58조~제61조 |
| 보건관리자 선임 (health_manager) | HM 카테고리, 선임 기준 매핑 없음 | 산안법 제22조, 시행령 별표 5 |

---

## 3. 의무 유형 분류 체계

### 3-1. 10개 의무 유형 정의

```yaml
obligation_types:

  document_required:
    description: 작업 전 작성·보존해야 하는 서류
    primary_basis: 산안규칙 제38조 (작업계획서), 산안법 제36조 (위험성평가)
    catalog_codes: [WP, EQ, RA, ED, PTW, DL, TS]
    trigger: work_type, equipment_code, trade_id
    legal_marker: legal_status=legal

  education_required:
    description: 정기·채용 시·작업내용 변경 시 교육 (시간·횟수 기준)
    primary_basis: 산안법 제29조, 시행규칙 별표 4
    catalog_codes: [ED]
    trigger: worker_count, worker_type (일용/상용), work_content_change
    note: 장비 대수 기준 아님 — 근로자 고용 형태·작업내용 기준

  special_education_required:
    description: 유해·위험 작업 특별교육 (별표 5)
    primary_basis: 산안법 제29조 제3항, 시행규칙 별표 5
    catalog_codes: [ED-003]
    trigger: work_type (별표 5 해당 여부), equipment_type (별표 5 해당 여부)
    note: work_training_requirements.yml + equipment_training_requirements.yml 참조

  qualification_required:
    description: 법정 면허·자격·신호수·관리감독자 배치
    primary_basis: 건설기계관리법, 산안법 시행령 별표 1, 산안규칙 각조
    catalog_codes: [] # 현재 catalog 미수록 → 신규 추가 필요
    trigger: equipment_code (운전원 자격), work_type (관리감독자)
    note: E-06 evidence 있으나 catalog 미연결 → PPE 또는 신규 QF 카테고리

  inspection_required:
    description: 작업 중·정기 점검 (일상점검, 월정기, 연자체검사)
    primary_basis: 산안규칙 제140조, 제146조, 제172조, 제180조
    catalog_codes: [CL]
    trigger: equipment_code
    note: equipment_inspection_requirements.yml 참조. inspection_type별 주기 분리

  installation_inspection_required:
    description: 비계·동바리·거푸집 등 설치 완료 후 점검
    primary_basis: 산안규칙 제57조, 제328조~제337조
    catalog_codes: [CL-001, CL-002]
    trigger: trade_id (비계/동바리 설치 공종)
    note: 설치 후 사용 전에 별도 점검 의무. inspection_required와 구분

  pre_use_inspection_required:
    description: 장비 작업 시작 전 사전점검 (매 작업일)
    primary_basis: 산안규칙 제146조, 제172조, 제180조
    catalog_codes: [CL-003]
    trigger: equipment_code (차량계, 크레인, 지게차 등)
    note: INSP_DAILY_PRE_WORK → equipment_inspection_requirements.yml

  permit_required:
    description: 작업 허가서 발급 의무 (PTW)
    primary_basis: 산안규칙 제619조 (밀폐공간), 화재예방법 (화기작업)
    catalog_codes: [PTW]
    trigger: work_type (밀폐공간, 화기, 전기, 고소 등)
    note: legal vs practical 구분 필수. PTW-001만 법정 확인됨

  record_retention_required:
    description: 법정 보존 기간 있는 기록 (3년/5년/영구)
    primary_basis: 산안법 제164조, 산안규칙 제4조
    catalog_codes: [ED-001, WP, RA-001, HM-001, HM-002]
    trigger: document_id (보존 기간 지정 문서)
    note: catalog에 retention_years 필드 추가 필요

  safety_cost_required:
    description: 산업안전보건관리비 계상·사용 의무
    primary_basis: 건설기술진흥법 시행규칙 별표 8, 고용노동부 고시
    catalog_codes: [TS-004]
    trigger: project_type=건설, contract_amount (계상 기준 이상)
    note: 계상률·사용 항목·실적 보고 → TS-004 builder에 반영 필요
```

---

## 4. 장비·작업·공종별 의무 매트릭스 스키마

### 4-1. 매트릭스 개념

```
axis_1: equipment_code / work_type_code / trade_id  (행)
axis_2: obligation_type                              (열)
cell:   {required: bool, source_type: law/practical/kosha,
         verification_status: confirmed/NEEDS_VERIFICATION,
         catalog_doc_ids: [...], legal_basis: "..."}
```

### 4-2. 현재 매핑 파일과 obligation_type 대응

| 현재 매핑 파일 | 커버하는 obligation_type | 커버 범위 |
|---|---|---|
| equipment_document_requirements.yml | document_required | 8/31 장비 |
| equipment_training_requirements.yml | special_education_required | 7/31 장비 |
| equipment_inspection_requirements.yml | inspection_required, pre_use_inspection_required | 9/31 장비 |
| work_document_requirements.yml | document_required | 8/~30 작업유형 |
| work_training_requirements.yml | education_required, special_education_required | 7/~30 작업유형 |
| trade_document_mapping.yml | document_required | 공종별 |
| trade_training_mapping.yml | education_required, special_education_required | 공종별 |
| trade_permit_mapping.yml | permit_required | 공종별 |

### 4-3. 신규 추가 필요한 매핑 파일

| 파일명 | obligation_type | 우선순위 |
|---|---|---|
| equipment_qualification_requirements.yml | qualification_required | P1 |
| equipment_safety_inspection_requirements.yml | safety_inspection (산안법 93조) | P1 |
| work_permit_requirements.yml | permit_required | P1 |
| document_retention_policy.yml | record_retention_required | P2 |
| trade_safety_cost_items.yml | safety_cost_required | P2 |
| work_installation_inspection_requirements.yml | installation_inspection_required | P2 |

### 4-4. obligation_type 필드 추가 — catalog 및 compliance_clauses

현재 `compliance_clauses.yml`에 `requirement_type` 필드가 존재하나 모두 미입력.  
감사 스크립트 실행 전에 28개 조항에 위 10개 유형 중 해당 유형을 입력해야 함.

---

## 5. 누락 판정 로직

### 5-1. 판정 규칙 (Rule Set)

```python
# Rule R01 — 장비 있는데 작업계획서 없음
if equipment_code in project.equipment
   and not any(doc in project.docs
               for doc in equipment_document_requirements[equipment_code]
               if source_type == "law"):
    gap(R01, equipment_code, "document_required")

# Rule R02 — 장비 있는데 일상점검표 없음
if equipment_code in project.equipment
   and INSP_DAILY_PRE_WORK in equipment_inspection_requirements[equipment_code]
   and CL-003 not in project.docs:
    gap(R02, equipment_code, "pre_use_inspection_required")

# Rule R03 — 장비 있는데 법정 자격 확인 없음
if equipment_code in equipment_qualification_requirements
   and qualification_doc not in project.docs:
    gap(R03, equipment_code, "qualification_required")

# Rule R04 — 특별교육 대상 작업인데 ED-003 없음
if work_type in work_training_requirements
   and EDU_SPECIAL_16H in [r.training_code for r in work_training_requirements[work_type]]
   and ED-003 not in project.docs:
    gap(R04, work_type, "special_education_required")

# Rule R05 — 밀폐공간 작업인데 PTW-001 없음
if WT_CONFINED_SPACE in project.work_types
   and PTW-001 not in project.docs:
    gap(R05, "WT_CONFINED_SPACE", "permit_required", severity="법정")

# Rule R06 — 비계·동바리 공종인데 CL-001 없음
if trade_id in ["SCAFFOLD_ERECT", "FORMWORK_INSTALL", ...]
   and CL-001 not in project.docs:
    gap(R06, trade_id, "installation_inspection_required")

# Rule R07 — 타워크레인 있는데 CL-006 없음
if EQ_CRANE_TOWER in project.equipment
   and CL-006 not in project.docs:
    gap(R07, "EQ_CRANE_TOWER", "inspection_required")

# Rule R08 — 건설현장인데 TS-004 없음
if project_type == "construction"
   and contract_amount >= safety_cost_threshold
   and TS-004 not in project.docs:
    gap(R08, "project", "safety_cost_required")

# Rule R09 — 유해화학물질 공종인데 MSDS 확인 없음
if trade_id uses hazardous_chemicals
   and PPE-004 not in project.docs:
    gap(R09, trade_id, "document_required", sub="MSDS")

# Rule R10 — DONE builder 있는데 evidence 없음 (현재 audit_safety_90_completion.py 담당)
# → 별도 처리 유지
```

### 5-2. severity 등급

| severity | 기준 |
|---|---|
| 법정_강제 | legal_status=legal + source_type=law + verification_status=confirmed |
| 법정_미확인 | legal_status=legal + verification_status=NEEDS_VERIFICATION |
| 실무_권장 | legal_status=practical |
| 선택 | legal_status=optional |

감사 리포트에서 `법정_강제`만 FAIL로 처리. 나머지는 WARN.

---

## 6. 감사 스크립트 설계

### 6-1. 파일 위치

```
scripts/audit_safety_legal_requirement_coverage.py
```

### 6-2. 입력 데이터

```
data/masters/safety/documents/document_catalog.yml
data/masters/safety/compliance/compliance_clauses.yml
data/masters/safety/compliance/compliance_links.yml
data/masters/safety/mappings/equipment_document_requirements.yml
data/masters/safety/mappings/equipment_training_requirements.yml
data/masters/safety/mappings/equipment_inspection_requirements.yml
data/masters/safety/mappings/work_document_requirements.yml
data/masters/safety/mappings/work_training_requirements.yml
data/masters/safety/mappings/trade_document_mapping.yml
data/masters/safety/mappings/trade_training_mapping.yml
data/masters/safety/mappings/trade_permit_mapping.yml
data/masters/safety/equipment/equipment_types.yml
data/masters/safety/training/training_types.yml
data/masters/safety/inspection/inspection_types.yml
data/masters/safety/work_types.yml
```

### 6-3. 출력 구조

```
[1] OBLIGATION TYPE COVERAGE
  의무 유형 10종 × catalog 연결 현황
  FAIL: catalog 연결 0건인 의무 유형 목록

[2] MAPPING COVERAGE
  장비 31종 × obligation_type별 매핑 현황 (confirmed/NEEDS_VERIFICATION/MISSING)
  작업유형 ~30종 × obligation_type별 현황

[3] COMPLIANCE CLAUSE GAP
  compliance_clauses 28조항 × requirement_type 입력 현황
  requirement_type 미입력 조항 목록

[4] DOCUMENT GAP BY OBLIGATION TYPE
  obligation_type별 legal 문서 중 implementation_status≠DONE 목록
  severity별 집계

[5] RULE-BASED GAP (R01~R10)
  각 규칙 × 위반 케이스 수 (현재 master 기준)

[6] SUMMARY
  total_obligations_audited
  covered_confirmed / covered_needs_verification / missing
  legal_강제_missing: N  ← FAIL 판정 기준
  legal_미확인_missing: N ← WARN
  실무_권장_missing: N    ← INFO

[7] 최종 판정
  PASS: legal_강제_missing == 0
  WARN: legal_강제_missing == 0 but legal_미확인_missing > 0
  FAIL: legal_강제_missing > 0
```

### 6-4. 스크립트 구현 전 선행 작업 (BLOCKER)

아래가 완료되지 않으면 스크립트가 의미 있는 결과를 출력할 수 없음:

| # | 선행 작업 | 담당 파일 |
|---|---|---|
| B1 | compliance_clauses.yml 28조항에 requirement_type 입력 | compliance_clauses.yml |
| B2 | equipment_qualification_requirements.yml 신규 작성 | mappings/ |
| B3 | work_permit_requirements.yml 신규 작성 | mappings/ |
| B4 | catalog 문서에 `retention_years` 필드 추가 (보존 의무 문서 대상) | document_catalog.yml |
| B5 | equipment_document_requirements.yml — 31종 전수 검토 완성 | mappings/ |

---

## 7. 출력 리포트 설계

### 7-1. 파일 위치

```
docs/reports/safety_legal_requirement_coverage_gap.md
```

### 7-2. 리포트 섹션 구성

```markdown
# 법령·지침 의무 커버리지 갭 리포트
생성일: {date} | 기준선: READY {n}/90 = {pct}%

## Executive Summary
| 구분 | 건수 |
| 법정_강제 누락 | N |
| 법정_미확인 누락 | N |
| NEEDS_VERIFICATION 조항 | N |

## 1. 의무 유형별 커버리지
(10종 × legal/practical 구분 테이블)

## 2. 장비별 누락 매트릭스
(장비코드 × obligation_type 매트릭스)

## 3. 작업유형별 누락 매트릭스

## 4. 공종별 누락 매트릭스

## 5. 규칙 위반 케이스 (R01~R10)

## 6. 우선 보강 대상 (severity 법정_강제 기준)

## 7. NEEDS_VERIFICATION 조항 목록 (원문 확인 필요)

## Appendix: 감사 기준 및 rule matrix
```

---

## 8. 우선 보강 대상 예상

아래는 현재 master 상태 기준으로 법정 의무이면서 catalog·mappings 미비가 명확한 항목.  
원문 확인 전까지 `예상`으로 표시.

### P1 — 법정_강제 예상 (즉시 보강 대상)

| 항목 | 근거 법령 | 현재 갭 |
|---|---|---|
| 자격·면허 확인 (운전원) | 건설기계관리법 제26조, 산안규칙 각조 | qualification_required 매핑 전무 |
| 타워크레인 안전검사 | 산안법 제93조, 시행령 별표 22 | CC-028만 존재, 장비별 매핑 없음 |
| 밀폐공간 PTW 법정 여부 | 산안규칙 제619조 | PTW-001 NEEDS_VERIFICATION |
| 비계 설치 점검 (CL-001) | 산안규칙 제57조 | trade → CL-001 매핑 없음 |
| 특별교육 대상 작업 全수록 | 시행규칙 별표 5 (35개 호) | 현재 7건만 매핑 |
| 안전보건교육 대장 (ED-001) | 산안법 제29조, 시행규칙 별표 4 | builder DONE, trade 매핑 없음 |
| 산업재해조사표 (EM-001) | 산안법 제57조 | TODO 상태 |

### P2 — 법정_미확인 또는 실무_권장 (차순위)

| 항목 | 현재 갭 |
|---|---|
| 기록 보존 기간 (retention_years) | catalog 필드 없음 |
| 안전관리비 계상 기준 (TS-004) | builder TODO, 계상률 로직 없음 |
| 도급 승인 서류 (CM-002) | TODO |
| 건강관리수첩 확인 (HM-002) | DONE이나 trade 매핑 없음 |

---

## 9. 구현 순서 제안

```
Step 1. compliance_clauses.yml → requirement_type 28개 입력         [B1]
Step 2. equipment_qualification_requirements.yml 작성               [B2]
Step 3. work_permit_requirements.yml 작성                           [B3]
Step 4. equipment_document_requirements.yml 31종 전수 완성          [B5]
Step 5. scripts/audit_safety_legal_requirement_coverage.py 구현
Step 6. 초회 실행 → FAIL 목록 확정
Step 7. catalog 신규 문서 추가 (qualification, retention 필드)
Step 8. docs/reports/ 자동 생성 연동
```

---

## 10. 감사 스크립트 실행 성공 기준 (목표 상태)

```
legal_강제_missing     = 0     → PASS
legal_미확인_missing   ≤ 5     → WARN (원문 확인 진행 중)
NEEDS_VERIFICATION 조항 ≤ 3    → WARN (잔여 법령 조회 필요)
mapping_coverage       ≥ 80%   → 장비 31종 × P1 의무 유형 5종 기준
```

---

*이 설계 문서는 구현 시작 전 사용자 검토·승인 후 스크립트 구현 단계로 진행한다.*

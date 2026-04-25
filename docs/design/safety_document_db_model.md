# 안전서류 93종 catalog / 90종 effective DB 논리 모델 설계

> 기준일: 2026-04-25 (정합성 보정 반영)  
> 목적: 93종 catalog (90종 effective + 3종 OUT) 운영 데이터를 DB로 정규화할 때의 테이블·관계 사전 확정  
> 범위: 논리 모델 + 우선순위 / 물리 DDL은 별도 산출물  
> 현 상태: YAML 마스터 기반 운영. DB 도입은 단계적 진행 (본 문서는 설계만)

## 0. 기준 수치 (정합성 보정)

| 지표 | 값 | 비고 |
|------|---:|------|
| catalog_total | 93 | safety_document_catalog 적재 대상 (OUT 포함) |
| out_total | 3 | TS-001~003 — implementation_status='OUT'으로 적재 |
| effective_total | 90 | 운영 발행 대상 |
| done_count | 33 | implementation_status='DONE' |
| builder_file_count | 29 | safety_form_builder 적재 대상 |
| form_spec_count | 29 | builder_file과 1:1 매핑 |
| ready_document_count | 16 | audit final_readiness='READY' |

---

## 1. 설계 원칙

| 원칙 | 내용 |
|------|------|
| YAML 단일 진실 소스 유지 | 카탈로그·매핑·법령 evidence는 YAML/JSON이 마스터. DB는 운영 추적용 |
| YAML → DB 단방향 동기화 | DB는 read-only 캐시 + 발행/감사 이력만 기록 |
| 카테고리/패키지는 마스터 코드 테이블화 | 신규 카테고리 추가 시 코드만 등록 |
| 조항 정규화 분리 | evidence JSON은 raw, DB는 정규화된 조항 단위 record |
| 발행 인스턴스 vs 양식 정의 분리 | safety_form_schema (정의) vs safety_required_document_instance (발행본) |
| audit 결과 이력 보존 | 감사 시점별 readiness 변화를 추적 가능 |

---

## 2. 테이블 일람 (13종 + 1개 연결 = 14개)

| # | 테이블명 | 목적 | 운영 DB 도입 우선순위 |
|---|---------|------|:--------------------:|
| 1 | safety_document_category | 13개 카테고리 마스터 | **P1** |
| 2 | safety_document_catalog | 93종 문서 마스터 (OUT 포함) | **P1** |
| 3 | safety_form_builder | builder 등록 정보 (29종) | **P1** |
| 4 | safety_legal_reference | 법령 조항 정규화 | **P1** |
| 5 | safety_document_evidence | evidence 메타 + 법령 매핑 | **P1** |
| 6 | safety_work_package | 작업 패키지 (hot_work 등) | P2 |
| 7 | safety_package_document | 패키지 ↔ 문서 매핑 | P2 |
| 8 | safety_document_relation | related_documents 양방향 그래프 | P2 |
| 9 | safety_form_schema | 필드 스키마 (form_data 검증) | P2 |
| 10 | safety_project_work_activity | 프로젝트 작업 활동 (발행 트리거) | P2 |
| 11 | safety_required_document_instance | 실제 발행 인스턴스 | **P1** (운영 시) |
| 12 | safety_document_output | 생성 파일 추적 | **P1** (운영 시) |
| 13 | safety_document_audit_result | 감사 결과 이력 | P3 |
| 5.1 | safety_evidence_legal_link | evidence ↔ legal_reference 연결 | P1 |

**테이블 합계: 13개 + 연결 테이블 1개 = 14개**

---

## 3. 테이블 상세

### 3.1 safety_document_category

**목적**: 13개 카테고리 (WP, EQ, RA, ED, PTW, DL, CL, PPE, CM, HM, EM, TS, SP) 마스터 코드.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| category_code | VARCHAR(5) PK | WP, PTW, CL... |
| category_name_ko | VARCHAR(50) | 한글명 (작업계획서) |
| category_name_en | VARCHAR(50) | Work Plan |
| description | TEXT | 정의 |
| sort_order | SMALLINT | UI 표시 순서 |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

- **PK**: category_code
- **YAML 관계**: `document_catalog.yml`의 `category_code` 필드 = 본 테이블 PK
- **운영 DB**: 도입 — 신규 카테고리 추가 시 단일 진입점

---

### 3.2 safety_document_catalog

**목적**: 90종 문서 마스터. document_catalog.yml의 1:1 미러.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| document_id | VARCHAR(20) PK | WP-001, CL-005... |
| category_code | VARCHAR(5) FK | → safety_document_category |
| document_name | VARCHAR(100) | 한글 정식 명칭 |
| legal_status | VARCHAR(20) | legal / practical / optional |
| implementation_status | VARCHAR(20) | DONE / TODO / OUT |
| priority | VARCHAR(10) | DONE / P1 / P2 / P3 / OUT |
| form_type | VARCHAR(80) FK NULL | → safety_form_builder.form_type |
| evidence_status | VARCHAR(30) | VERIFIED / PARTIAL_VERIFIED / NEEDS_VERIFICATION |
| legal_basis_text | TEXT | "산안규칙 제236조 등" |
| retention_years | SMALLINT NULL | 3, 5, ... |
| engine_coverage | VARCHAR(10) | YES / NO |
| notes | TEXT | |
| created_at, updated_at | TIMESTAMP | |

- **PK**: document_id
- **FK 후보**: category_code → safety_document_category
- **YAML 관계**: `document_catalog.yml`의 documents[] 1:1 미러 (form_type, evidence_id 등은 별도 테이블로 정규화)
- **운영 DB**: 도입 — 모든 발행/감사의 anchor

---

### 3.3 safety_form_builder

**목적**: form_registry.py의 등록 builder를 DB로 추적.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| form_type | VARCHAR(80) PK | hot_work_permit, ... |
| display_name | VARCHAR(100) | 한글 표시명 |
| version | VARCHAR(10) | "1.0" |
| builder_module | VARCHAR(200) | engine.output.fire_prevention_checklist_builder |
| builder_function | VARCHAR(80) | build_fire_prevention_checklist_excel |
| required_fields_json | JSONB | form_data required 필드 목록 |
| optional_fields_json | JSONB | optional 필드 목록 |
| repeat_field | VARCHAR(50) NULL | 반복 행 필드명 |
| max_repeat_rows | SMALLINT NULL | |
| extra_list_fields_json | JSONB | list 필드 목록 |
| registered_at | TIMESTAMP | |

- **PK**: form_type
- **FK 후보**: 없음 (참조됨: catalog.form_type)
- **YAML 관계**: form_registry.py의 _SUPPORTED_FORMS dict와 1:1
- **운영 DB**: 도입 — 신규 builder 추가 시 자동 sync

---

### 3.4 safety_legal_reference

**목적**: 법령 조항을 정규화. 한 조항(제241조)이 여러 evidence에서 참조될 수 있음.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| legal_ref_id | BIGSERIAL PK | |
| law_name | VARCHAR(100) | 산업안전보건기준에 관한 규칙 |
| law_mst | VARCHAR(20) | 273603 (law.go.kr MST) |
| article_no | VARCHAR(30) | 제236조, 제241조의2 |
| article_title | VARCHAR(200) | 화재 위험이 있는 작업의 장소 등 |
| article_summary | TEXT | 조문 요약 |
| article_full_text | TEXT NULL | law.go.kr API 원문 |
| effective_date | DATE NULL | 시행일 |
| verification_result | VARCHAR(30) | VERIFIED / PARTIAL_VERIFIED / NEEDS_VERIFICATION |
| collected_at | DATE | |
| source_url | VARCHAR(500) | |

- **PK**: legal_ref_id
- **UNIQUE**: (law_mst, article_no) — 중복 조항 방지
- **YAML 관계**: 각 evidence JSON의 `legal_basis[]` 항목을 정규화하여 적재
- **운영 DB**: 도입 — 법령 개정 추적용

---

### 3.5 safety_document_evidence

**목적**: 문서별 evidence 메타. 한 문서가 여러 evidence를 가질 수 있고, 한 evidence는 여러 법령 조항을 참조할 수 있음.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| evidence_id | VARCHAR(40) PK | PTW-002-L1, CL-005-P1 |
| document_id | VARCHAR(20) FK | → safety_document_catalog |
| evidence_type | VARCHAR(20) | LAW / KOSHA / MOEL / PRACTICAL |
| source | VARCHAR(200) | "law.go.kr" / "KOSHA P-94-2021" |
| collection_method | TEXT | |
| verification_result | VARCHAR(30) | |
| evidence_file_path | VARCHAR(300) | data/evidence/safety_law_refs/... |
| reused_from_json | JSONB | ["PTW-002-L1", ...] (재사용 evidence ID) |
| collected_at | DATE | |

- **PK**: evidence_id
- **FK**: document_id → safety_document_catalog
- **연결 테이블**: safety_evidence_legal_link (evidence ↔ legal_reference N:N)
- **YAML 관계**: `data/evidence/safety_law_refs/*.json` 1:1
- **운영 DB**: 도입 — evidence 추적

#### 3.5.1 safety_evidence_legal_link (연결 테이블)

| 컬럼 | 타입 | 비고 |
|------|------|------|
| evidence_id | VARCHAR(40) FK | → safety_document_evidence |
| legal_ref_id | BIGINT FK | → safety_legal_reference |
| section_mapping | VARCHAR(200) | "섹션 4 (가연물 제거)" |
| PRIMARY KEY (evidence_id, legal_ref_id) | | |

---

### 3.6 safety_work_package

**목적**: 작업 패키지 마스터 (hot_work, work_at_height 등). `_V11_PACKAGE_RULES` 외부화.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| package_code | VARCHAR(30) PK | hot_work, work_at_height |
| package_name_ko | VARCHAR(50) | 화기작업, 고소작업 |
| work_type_codes_json | JSONB | ["hot_work"] (해당 work_type) |
| description | TEXT | |
| sort_order | SMALLINT | |

- **PK**: package_code
- **YAML 관계**: 신규 도입 시 `data/masters/safety/packages/work_packages.yml` 외부화
- **운영 DB**: P2 — 패키지 5개 초과 또는 외부화 시점

---

### 3.7 safety_package_document

**목적**: 패키지 ↔ 문서 매핑 (required / conditional_required / optional).

| 컬럼 | 타입 | 비고 |
|------|------|------|
| package_doc_id | BIGSERIAL PK | |
| package_code | VARCHAR(30) FK | → safety_work_package |
| document_id | VARCHAR(20) FK | → safety_document_catalog |
| requirement_level | VARCHAR(20) | required / conditional_required / optional |
| sort_order | SMALLINT | |
| notes | TEXT | |

- **PK**: package_doc_id
- **UNIQUE**: (package_code, document_id, requirement_level)
- **YAML 관계**: `_V11_PACKAGE_RULES`의 `required` / `conditional_required` / `optional` 배열을 row 단위로 정규화
- **운영 DB**: P2

---

### 3.8 safety_document_relation

**목적**: related_documents 양방향 그래프. PTW-002 ↔ CL-005 같은 연계 관계.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| relation_id | BIGSERIAL PK | |
| source_document_id | VARCHAR(20) FK | → safety_document_catalog |
| target_document_id | VARCHAR(20) FK | → safety_document_catalog |
| relation_type | VARCHAR(30) | linked / prerequisite / supersedes |
| direction | VARCHAR(10) | bidirectional / forward |
| notes | TEXT | |

- **PK**: relation_id
- **UNIQUE**: (source_document_id, target_document_id, relation_type)
- **YAML 관계**: catalog의 `related_documents[]` 필드
- **운영 DB**: P2 — 추천 엔진 그래프 탐색 도입 시

---

### 3.9 safety_form_schema

**목적**: 필드 단위 스키마. form_data 검증·UI 자동 생성.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| schema_id | BIGSERIAL PK | |
| form_type | VARCHAR(80) FK | → safety_form_builder |
| field_name | VARCHAR(80) | site_name, work_date |
| field_label_ko | VARCHAR(100) | 현장명, 작업일 |
| field_type | VARCHAR(30) | text / date / list / dict |
| is_required | BOOLEAN | |
| is_repeat | BOOLEAN | |
| max_repeat_rows | SMALLINT NULL | |
| validation_rule | VARCHAR(200) NULL | |
| sort_order | SMALLINT | |

- **PK**: schema_id
- **UNIQUE**: (form_type, field_name)
- **YAML 관계**: builder Python의 required_fields/optional_fields/extra_list_fields tuple
- **운영 DB**: P2 — UI 자동 생성 도입 시

---

### 3.10 safety_project_work_activity

**목적**: 프로젝트 단위 작업 활동(예: "3F 용접 작업 2026-04-25")을 기록. 활동의 work_type이 패키지 매핑을 통해 필요 문서를 트리거.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| activity_id | UUID PK | |
| project_id | UUID FK | 외부 project 테이블 |
| activity_name | VARCHAR(200) | "3F 슬래브 용접 작업" |
| work_type_code | VARCHAR(30) | hot_work, work_at_height, ... (work_type 식별) |
| package_code | VARCHAR(30) FK NULL | → safety_work_package (자동 매핑) |
| planned_start_date | DATE | |
| planned_end_date | DATE NULL | |
| actual_start_date | DATE NULL | |
| actual_end_date | DATE NULL | |
| location | VARCHAR(200) | "3층 동측 구조부" |
| supervisor | VARCHAR(100) | |
| trade | VARCHAR(50) NULL | architecture / civil 등 |
| status | VARCHAR(20) | planned / in_progress / completed / canceled |
| created_at, updated_at | TIMESTAMP | |

- **PK**: activity_id
- **FK**: project_id (외부), package_code → safety_work_package
- **YAML 관계**: 없음 (운영 데이터)
- **연계**: 활동 등록 시 package_code 자동 매핑 → safety_package_document 조회 → 필요 문서 instance 생성 트리거
- **운영 DB**: P2 — 패키지 자동 발행 도입 시 필수

---

### 3.11 safety_required_document_instance

**목적**: 실제 발행한 문서 인스턴스. 현장·일자별 1건. activity_id로 트리거 활동과 연결.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| instance_id | UUID PK | |
| document_id | VARCHAR(20) FK | → safety_document_catalog |
| form_type | VARCHAR(80) FK | → safety_form_builder |
| activity_id | UUID FK NULL | → safety_project_work_activity (트리거 활동) |
| site_id | UUID FK NULL | 외부 site 테이블 |
| project_name | VARCHAR(200) | |
| issue_date | DATE | |
| permit_no | VARCHAR(50) NULL | PTW-002-2026-001 |
| form_data_json | JSONB | builder 입력 form_data 전체 |
| status | VARCHAR(20) | draft / issued / closed / void |
| issued_by | VARCHAR(100) | |
| approved_by | VARCHAR(100) NULL | |
| created_at, updated_at | TIMESTAMP | |

- **PK**: instance_id
- **FK**: document_id, form_type, activity_id
- **YAML 관계**: 없음 (운영 데이터)
- **운영 DB**: 도입 — 운영 시작 시 필수

---

### 3.12 safety_document_output

**목적**: 생성된 파일(xlsx, PDF) 추적.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| output_id | UUID PK | |
| instance_id | UUID FK | → safety_required_document_instance |
| file_format | VARCHAR(10) | xlsx / pdf / hwp |
| file_path | VARCHAR(500) | export/forms/PTW/PTW-002/2026-04-25/... |
| file_size_bytes | BIGINT | |
| sha256_hash | VARCHAR(64) | 무결성 체크 |
| generated_at | TIMESTAMP | |
| generated_by | VARCHAR(100) | |
| download_count | INT DEFAULT 0 | |
| archived_at | TIMESTAMP NULL | 보존기간 초과 시 archive |

- **PK**: output_id
- **FK**: instance_id
- **YAML 관계**: 없음 (운영 데이터)
- **운영 DB**: 도입 — 발행 추적 필수

---

### 3.13 safety_document_audit_result

**목적**: audit_safety_90_completion.py 결과 이력. readiness 변화 추적.

| 컬럼 | 타입 | 비고 |
|------|------|------|
| audit_id | BIGSERIAL PK | |
| document_id | VARCHAR(20) FK | → safety_document_catalog |
| audit_date | DATE | |
| builder_exists | BOOLEAN | |
| catalog_done | BOOLEAN | |
| evidence_exists | BOOLEAN | |
| evidence_status | VARCHAR(30) | |
| smoke_test_exists | BOOLEAN | |
| recommender_connected | BOOLEAN | |
| related_documents_count | SMALLINT | |
| final_readiness | VARCHAR(30) | READY/TEST_MISSING/EVIDENCE_MISSING/... |
| audit_runner | VARCHAR(50) | github-actions / manual |

- **PK**: audit_id
- **FK**: document_id
- **YAML 관계**: 없음 (audit_safety_90_completion.py 출력 누적)
- **운영 DB**: P3 — 감사 자동화 도입 시

---

## 4. 핵심 관계 다이어그램 (논리)

```
safety_document_category (13)
    │ 1
    │
    │ N
safety_document_catalog (93 = 90 effective + 3 OUT) ─── form_type ───→ safety_form_builder (29)
    │                                                          │
    │ 1                                                        │ 1
    │                                                          │
    │ N                                                        │ N
safety_document_evidence (67+) ←─→ safety_evidence_legal_link ←─→ safety_legal_reference
    │
    │
    │
safety_project_work_activity (운영) ──→ safety_required_document_instance (운영) ──→ safety_document_output (운영)
    │
    │ FK: package_code
    ↓
safety_work_package (7) ──N:N── safety_document_catalog
    via safety_package_document


safety_document_catalog ──N:N── safety_document_catalog
    via safety_document_relation (related_documents)


safety_document_catalog ──1:N── safety_document_audit_result (감사 시점별 누적)
```

---

## 5. 우선 도입 테이블 vs 후순위

### 5.1 P1 — 즉시 도입 권장 (마스터 + 운영 핵심) — 7개

| 테이블 | 사유 |
|--------|------|
| safety_document_category | 13개 카테고리 코드 표준화. 신규 카테고리 진입점 |
| safety_document_catalog | 93종 마스터 (90 effective + 3 OUT). 모든 발행의 anchor |
| safety_form_builder | 29개 builder 메타. registry와 sync |
| safety_legal_reference | 법령 정규화. evidence 재사용 효율화 |
| safety_document_evidence | 67개 evidence 메타 + safety_evidence_legal_link |
| safety_required_document_instance | 발행 인스턴스. 운영 시작 시 필수 |
| safety_document_output | 파일 추적. 보존기간 관리 |

### 5.2 P2 — 패키지·관계 외부화 시 — 5개

| 테이블 | 도입 시점 |
|--------|---------|
| safety_work_package | `_V11_PACKAGE_RULES` 외부화 시 |
| safety_package_document | 패키지 추가 시 |
| safety_document_relation | 추천 엔진 그래프 확장 시 |
| safety_form_schema | UI 자동 생성·field 검증 도입 시 |
| **safety_project_work_activity** | 프로젝트 활동 기반 자동 발행 도입 시 |

### 5.3 P3 — 감사 자동화 시 — 1개

| 테이블 | 도입 시점 |
|--------|---------|
| safety_document_audit_result | audit 자동 실행·이력 추적 도입 시 (CI 통합) |

### 5.4 합계 검증

| 우선순위 | 개수 | 누적 |
|---------|----:|----:|
| P1 | 7 | 7 |
| P2 | 5 | 12 |
| P3 | 1 | 13 |
| **합계** | **13** | — |
| (+ 연결 테이블) | 1 | 14 |

---

## 6. YAML ↔ DB 동기화 전략

| YAML/JSON | DB 테이블 | 동기화 방식 |
|-----------|----------|---------|
| `document_catalog.yml` (93종, OUT 포함) | safety_document_catalog | 매 마스터 변경 시 일괄 UPSERT |
| `document_catalog.yml.documents[].related_documents` | safety_document_relation | 동일 변경 시점 |
| `data/evidence/safety_law_refs/*.json` | safety_document_evidence + safety_legal_reference | 파일 추가/수정 시 |
| `engine/output/form_registry.py` _SUPPORTED_FORMS (29종) | safety_form_builder | builder 추가 시 (CI hook) |
| `_V11_PACKAGE_RULES` (recommender) | safety_work_package + safety_package_document | 패키지 변경 시 |
| 프로젝트 활동 등록 (POST /activities) | safety_project_work_activity | 활동 시점 INSERT |
| 운영 발행 (POST /forms/...) | safety_required_document_instance + safety_document_output | 발행 시점 INSERT |

**원칙**: YAML이 진실. DB는 캐시 + 운영 데이터.

---

## 7. 인덱스 전략 (참고)

| 테이블 | 인덱스 |
|--------|--------|
| safety_document_catalog | category_code, implementation_status |
| safety_document_evidence | document_id, verification_result |
| safety_legal_reference | (law_mst, article_no) UNIQUE, verification_result |
| safety_project_work_activity | (project_id, planned_start_date), work_type_code, status |
| safety_required_document_instance | (document_id, issue_date), site_id, activity_id, status |
| safety_document_output | instance_id, file_format, generated_at |
| safety_document_audit_result | (document_id, audit_date) |

---

## 8. 결론

- **13개 테이블 + 1개 연결 테이블 = 14개**로 93종 catalog (90 effective + 3 OUT) 운영 가능
- P1 **7종**은 운영 시작 전 도입 필수
- P2 **5종** (safety_project_work_activity 추가)은 패키지·관계·활동 외부화 시점에 도입
- P3 **1종**은 CI 자동 감사 도입 시
- YAML 마스터 → DB 단방향 동기화 원칙 유지
- 본 설계는 **물리 DDL 작성 전 논리 모델만 확정** — DDL은 별도 산출물

---

*생성: 2026-04-25 / 연계: `safety_directory_architecture.md`, `safety_directory_migration_plan.md`*

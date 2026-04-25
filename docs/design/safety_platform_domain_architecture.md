# Safety Platform 도메인 아키텍처

**버전**: 1.0  
**작성일**: 2026-04-24  
**목적**: 안전서류 90종, 장비, 근로자, 관리자, 교육, 자격, 점검, 법령/KOSHA를 연결하는 전체 골격 확정  
**단계**: 설계 확정 단계 — 이번 단계에서 DB 적용, UI 개발, 서류 템플릿 구현 없음

---

## 1. 전체 도메인 구조

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Safety Platform                               │
│                                                                       │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────────────┐ │
│  │  Project    │───▶│  WorkItem    │───▶│  DocumentInstance        │ │
│  │  (현장/공사) │    │  (작업 항목) │    │  (생성된 서류)            │ │
│  └──────┬──────┘    └──────┬───────┘    └──────────────────────────┘ │
│         │                  │                                          │
│         ▼                  ▼                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────────────┐ │
│  │  Worker     │    │  Equipment   │───▶│  InspectionRecord        │ │
│  │  (근로자)    │    │  (장비 인스턴스)│    │  (점검 기록)             │ │
│  └──────┬──────┘    └──────┬───────┘    └──────────────────────────┘ │
│         │                  │                                          │
│         ▼                  ▼                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────────────┐ │
│  │  Training   │    │  Permit      │───▶│  ComplianceLink          │ │
│  │  (교육 이력) │    │  (작업허가서) │    │  (법령 근거 연결)         │ │
│  └─────────────┘    └──────────────┘    └──────────────────────────┘ │
│                                                                       │
│  ────────────── Knowledge DB (기존, 변경 없음) ──────────────────────  │
│  documents  │  hazards  │  work_types  │  equipment(코드)  │  법령DB  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. 8개 핵심 도메인

### 2.1 Project (현장/공사)
- 단위: 공사 현장 또는 사업장 1개
- 핵심 필드: project_code, name, address, industry_type, start_date, end_date
- 연결: WorkItem(1:N), Worker(1:N via assignment), Equipment(1:N via assignment)

### 2.2 Work (작업 항목)
- 단위: 현장 내 개별 작업 (굴착, 양중, 밀폐공간 진입 등)
- work_type_code → Knowledge DB의 work_types 참조
- 연결: DocumentInstance(N:M via requirements), Training(N:M via requirements)

### 2.3 Worker (근로자/관리자)
- 단위: 개인 근로자 또는 안전관리자
- 역할(worker_roles): 근로자, 안전관리자, 보건관리자, 관리감독자, 도급업체 근로자
- 자격/면허(worker_licenses): 자격증 종류, 취득일, 만료일
- 연결: TrainingSession(N:M via history), WorkItem(N:M via assignment)

### 2.4 Equipment (장비)
- 단위: 현장 배치된 장비 1대 (인스턴스)
- equipment_code → Knowledge DB의 equipment 참조 (코드/명칭/법령)
- 연결: InspectionRecord(1:N), DocumentInstance(N:M via requirements), TrainingRequirement(N:M)

### 2.5 Training (교육)
- training_types: 정기안전교육, 채용시 교육, 작업변경 교육, 특별교육, TBM, MSDS, 밀폐공간 교육 등
- training_requirements: 작업유형별 / 장비별 필수 교육 매핑
- training_sessions: 실시 기록 (일시, 강사, 수강자, 교육 내용)
- worker_training_history: 개인별 이수 이력

### 2.6 Document (서류)
- sp_document_catalog: 90종 서류 마스터 (doc_id, 명칭, 법령근거, 의무유형, 구현상태)
- sp_document_templates: 빌더 연결 정보 (form_type → form_registry.py)
- sp_document_instances: 실제 생성/보존되는 서류 인스턴스

### 2.7 Inspection (점검)
- inspection_types: 점검 유형 (일상점검, 정기점검, 특별점검, 자체검사)
- inspection_records: 실시 기록 (장비별, 작업 전/정기)
- permit_types: 허가서 유형 (작업허가서, 밀폐공간 허가서 등)
- permit_records: 발행 이력

### 2.8 Compliance (법령/근거)
- compliance_sources: 법령/고시/KOSHA GUIDE 출처 목록
- compliance_clauses: 조항 단위 항목 (law_id + article_no)
- compliance_links: 서류/교육/점검과 조항의 N:M 연결

---

## 3. 핵심 연결 흐름

```
장비 배치
  │
  ├─► sp_equipment_training_requirements
  │       → 필요 교육 유형 목록 (예: 타워크레인 → 특별교육 16시간)
  │       → 필요 자격/면허 목록 (예: 이동식크레인 → 크레인 운전기능사)
  │
  ├─► sp_equipment_document_requirements
  │       → 필요 서류 목록 (예: 타워크레인 → WP-004, 자체검사 기록)
  │
  └─► sp_equipment_inspection_requirements
          → 필요 점검 유형/주기 (예: 타워크레인 → 월 1회 정기점검)

작업 항목 추가
  │
  ├─► sp_work_document_requirements
  │       → 필요 서류 (예: 굴착 2m 이상 → WP-001)
  │
  └─► sp_work_training_requirements
          → 필요 교육 (예: 밀폐공간 작업 → 특별교육 16시간)

위험요인 식별
  │
  ├─► sp_hazard_document_requirements
  │       → 관련 서류 (예: 산소결핍 위험 → 밀폐공간 허가서 PTW-001)
  │
  └─► sp_hazard_training_requirements
          → 관련 교육 (예: 추락 위험 → 안전대 사용 교육)
```

---

## 4. 기존 구현과의 연결

### 4.1 Knowledge DB (변경 없음)
| 기존 테이블 | 역할 | 신규 연결 |
|------------|------|----------|
| `documents` | KOSHA/법령 원문 본체 | compliance_sources 참조 원본 |
| `hazards` | 위험요인 코드 | sp_hazard_document_requirements FK |
| `work_types` | 작업유형 코드 | sp_work_document_requirements FK |
| `equipment` | 장비 코드 | sp_equipment_types.knowledge_equipment_code 참조 |
| `law_meta` | 법령 메타 | compliance_clauses 생성 원본 |

### 4.2 Form Registry (변경 없음)
| form_type | doc_id | 상태 |
|-----------|--------|------|
| risk_assessment | RISK-001 | DONE |
| education_log | EDU-001 | DONE |
| excavation_workplan | WP-001 | DONE |
| vehicle_construction_workplan | WP-002 | DONE |
| material_handling_workplan | WP-003 | DONE |
| tower_crane_workplan | WP-004 | DONE |
| mobile_crane_workplan | WP-005 | DONE |
| confined_space_workplan | WP-014 | DONE |
| tbm_log | RA-004 | DONE |
| confined_space_permit | PTW-001 | DONE |
| confined_space_checklist | CL-010 | DONE |

sp_document_templates.form_type → form_registry.py의 form_type 문자열로 직접 연결.

### 4.3 신규 Safety Platform 테이블 (sp_ prefix)
- 기존 테이블명과 충돌 없음
- 모든 신규 테이블은 `sp_` prefix 사용
- 기존 코드 테이블(hazards, work_types, equipment)을 FK로 참조 (수정 없음)

---

## 5. 90종 서류 카테고리 구조

```
안전서류 90종 (목표)
├── 위험성평가 (RISK): 2종 (카탈로그 기준, 추가 예정)
├── 교육기록 (EDU): 2종
├── 작업계획서 (WP): 10종
├── 재해보고 (ACC): 1종
├── 회의록 (MTG): 2종
├── 도급관리 (CON): 1종
├── 유해위험방지 (HRP): 2종
├── 작업허가서 (PTW): NEEDS_VERIFICATION — 밀폐공간 외 추가 종류 미확정
├── 안전점검표 (CL): NEEDS_VERIFICATION — 장비별 체크리스트 종류 미확정
├── 자격/면허 관리 (LIC): NEEDS_VERIFICATION — 서류 형태 여부 미확정
├── 물질안전보건자료 (MSDS): NEEDS_VERIFICATION — 서류 종류/범위 미확정
└── 기타: NEEDS_VERIFICATION
```

현재 카탈로그 확정: 23종 (DONE 3, TODO 17, EXCLUDED 3)  
목표: 90종 — 추가 종류는 법령 검토 후 카탈로그에 순차 등록  

---

## 6. 법령/KOSHA 근거 연결 방식

```
compliance_sources (출처 목록)
  ├── source_type: law     → law_meta.law_id 참조
  ├── source_type: kosha   → documents.source_id 참조 (source_type='kosha')
  ├── source_type: moel    → moel_expc_meta 참조
  └── source_type: internal → 내부 실무 기준 (법령 근거 없음)

compliance_clauses (조항)
  └── law_id + article_no + paragraph_no → 구체적 조항 단위

compliance_links (N:M 연결)
  ├── target_type: document → sp_document_catalog.doc_id
  ├── target_type: training → sp_training_types.training_code
  ├── target_type: inspection → sp_inspection_types.inspection_code
  └── target_type: license  → sp_worker_licenses.license_type
```

**source_type 값 정의**:
- `law`: 산업안전보건법, 기준규칙 등 상위 법령
- `kosha`: KOSHA GUIDE / 기술지침
- `moel`: 고용노동부 고시 / 해석례
- `practical`: 법령 근거 없는 실무 관행
- `internal`: 시스템 내부 기준
- `NEEDS_VERIFICATION`: 근거 미확인 항목

---

## 7. 이번 단계 범위 외 (구현하지 않음)

| 항목 | 이유 |
|------|------|
| 실제 DB migrate 실행 | 설계 확정 단계. 별도 마이그레이션 단계에서 수행 |
| UI 개발 | 골격 설계 우선 |
| 서류 템플릿 추가 | 기존 builder 동작 보존 우선 |
| 교육 자동판정 엔진 | 매핑 데이터 충분히 확보 후 구현 |
| 근로자/장비 CRUD API | 스키마 확정 후 별도 단계 |
| 90종 전체 매핑 완성 | 법령 검토 병행 필요, 단계적 추가 |

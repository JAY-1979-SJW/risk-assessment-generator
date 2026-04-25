# 안전서류 93종 catalog / 90종 effective 디렉토리·분류 표준 설계

> 기준일: 2026-04-25 (정합성 보정 반영)  
> 목적: 90종 effective 문서가 뒤섞이지 않도록 디렉토리·문서ID·evidence·builder·출력물 구조를 사전 확정  
> 범위: 신규 builder 구현 X / 기존 파일 이동 X / 설계 문서 + 명명 규칙만 확정

## 0. 기준 수치 (정합성 보정)

| 지표 | 값 | 비고 |
|------|---:|------|
| **catalog_total** | 93 | document_catalog.yml의 documents[] 전체 |
| **out_total** | 3 | TS-001, TS-002, TS-003 (유해위험방지계획서·PSM) |
| **effective_total** | 90 | 구현 대상 (catalog_total - out_total) |
| **done_count** | 33 | implementation_status == DONE |
| **builder_file_count** | 29 | `engine/output/*_builder.py` 실제 파일 수 |
| **form_spec_count** | 29 | form_registry.py 등록된 form_type 수 (1:1) |
| **ready_document_count** | 16 | audit final_readiness == READY |

> ※ done_count(33) > form_spec_count(29) — EQ-001~004는 WP form_type 공유로 builder 1개를 N개 문서가 사용

---

## 1. 현재 구조 조사 결과

### 1.1 위치 매핑

| 항목 | 현재 경로 | 비고 |
|------|----------|------|
| 문서 카탈로그 | `data/masters/safety/documents/document_catalog.yml` | 93종 단일 파일 |
| safety mappings | `data/masters/safety/mappings/*.yml` | 9개 mapping YAML |
| evidence JSON | `data/evidence/safety_law_refs/*.json` | 67개 평면 디렉토리 |
| builder 파일 | `engine/output/*_builder.py` | 30개 평면 디렉토리 |
| form_registry | `engine/output/form_registry.py` | 단일 파일 (29 form_type 등록) |
| 추천 엔진 | `engine/recommendation/document_recommender.py` | `_V11_PACKAGE_RULES` 내장 |
| smoke test | `scripts/smoke_test_p1_forms.py` | 4845줄 단일 파일 |
| audit script | `scripts/audit_safety_*.py` | 평면 |
| generated output | `export/` | xlsx 직접 저장 (테스트용) |

### 1.2 현재 구조의 문제점

| # | 문제 | 영향 |
|---|------|------|
| 1 | `engine/output/`가 평면 — builder 30개 카테고리 구분 없음 | 90종 확장 시 60+ 파일 누적, 탐색 곤란 |
| 2 | `data/evidence/safety_law_refs/`가 평면 — 67개 → 200+ 예상 | 문서별 evidence 묶음 식별 어려움 |
| 3 | smoke_test 단일 파일 4845줄 | 90종 확장 시 1만줄 초과 예상, 머지 충돌 위험 |
| 4 | `export/` 임시 산출물과 운영 산출물 미구분 | 테스트 파일과 실제 발행물 혼재 |
| 5 | document_catalog.yml 단일 파일 93종 | 카테고리별 부분 수정 시 전체 충돌 위험 |
| 6 | 문서ID·파일명 규칙 미문서화 | 신규 추가 시 명명 일관성 부재 |

---

## 2. 93종 catalog / 90종 effective 분류 체계 확정

### 2.1 13개 카테고리 정의

| 코드 | 카테고리 | 정의 | catalog | OUT | effective |
|------|---------|------|--------:|----:|---------:|
| **WP** | 작업계획서 (Work Plan) | 산안규칙 의무 작업계획서 | 15 | 0 | 15 |
| **EQ** | 장비특화 작업계획서 (Equipment) | 장비별 사용·작업계획서 | 16 | 0 | 16 |
| **RA** | 위험성평가 (Risk Assessment) | 평가표·등록부·회의록 | 6 | 0 | 6 |
| **ED** | 교육 (Education) | 일반/특별/직무 교육 일지 | 5 | 0 | 5 |
| **PTW** | 작업허가서 (Permit-to-Work) | 고위험작업 허가서 | 8 | 0 | 8 |
| **DL** | 일지 (Daily Log) | 일일 안전관리 기록 | 5 | 0 | 5 |
| **CL** | 점검표 (Checklist) | 설비·작업 점검 양식 | 10 | 0 | 10 |
| **PPE** | 보호구·자재 (PPE & Material) | 보호구·MSDS 관리 | 4 | 0 | 4 |
| **CM** | 관리·행정 (Compliance Mgmt) | 협력업체·인사 행정 | 7 | 0 | 7 |
| **HM** | 건강관리 (Health Mgmt) | 작업환경측정·건강진단 | 2 | 0 | 2 |
| **EM** | 비상·사고 (Emergency) | 재해보고·아차사고 | 6 | 0 | 6 |
| **TS** | 특수계획 (Special) | 유해위험방지·PSM·석면 | 5 | **3** | 2 |
| **SP** | 안전문화 (Safety Promo) | 방침·우수사례·문화활동 | 4 | 0 | 4 |
| | **합계** | | **93** | **3** | **90** |

### 2.2 문서별 분류 매트릭스 (effective 90종 기준)

각 문서는 다음 7개 필드로 분류한다.

| 필드 | 가능 값 |
|------|---------|
| document_id | `{CAT}-{NNN}` 형식 (WP-001, CL-005 등) |
| category | 위 13개 코드 |
| document_name | 한글 정식 명칭 |
| priority | DONE / P1 / P2 / P3 / OUT |
| legal_or_practical | legal / practical / optional |
| **builder_type** | **custom / generic / external** |
| **evidence_group** | **A_law / B_kosha / C_moel / D_practical / NONE** |
| **package_group** | hot_work / work_at_height / heavy_lifting / vehicle / electrical / confined / hazmat / general / NONE |
| **output_folder** | `/export/forms/{category}/{doc_id}/` |

#### 2.2.1 builder_type 정의

| 타입 | 정의 | 적용 대상 | 예시 |
|------|------|---------|------|
| **custom** | 문서별 전용 builder. 13~15섹션 복잡 구조 | 모든 PTW, 핵심 WP, 핵심 CL | hot_work_permit, fire_prevention_checklist |
| **generic** | 공통 템플릿 builder (3~5섹션 단순 양식) | DL, CM, EM, SP, 단순 RA | safety_log, compliance_record |
| **external** | 전문기관 제출, 자체 생성 불가 | TS-001~003 (방지계획서·PSM) | OUT 처리 |

#### 2.2.2 evidence_group 정의

| 그룹 | 출처 | 식별자 접두 | 적용 |
|------|------|-----------|------|
| **A_law** | 산안법·산안규칙 (law.go.kr) | `L1`, `L2`... | 모든 legal 문서 |
| **B_kosha** | KOSHA GUIDE | `K1`, `K2`... | 안전관리 보조 자료 |
| **C_moel** | 노동부 고시·별지 서식 | `M1`, `M2`... | 행정 신고 양식 |
| **D_practical** | 실무 표준 (KOSHA·업계) | `P1`, `P2`... | practical checklist |
| **NONE** | evidence 없음 (단순 양식) | — | DL, SP 일부 |

#### 2.2.3 package_group 정의

| 패키지 | 연계 work_type | 핵심 문서 |
|--------|---------------|---------|
| **hot_work** | hot_work | PTW-002, CL-005, EQ-014, PPE-004 |
| **work_at_height** | work_at_height | PTW-003, CL-007, CL-001, EQ-005 |
| **heavy_lifting** | heavy_lifting | WP-005, PTW-007, CL-003 |
| **vehicle** | vehicle_construction, material_handling | WP-008, WP-009, EQ-001, EQ-002, EQ-007 |
| **electrical** | electrical_work | WP-011, PTW-004, CL-004, EQ-013, PTW-008 |
| **confined** | confined_space | WP-014, PTW-001, CL-010 |
| **excavation** | (신규) | WP-001, PTW-005 |
| **hazmat** | (신규) | WP-013, CL-009, PPE-004 |
| **general** | 패키지 무관 공통 | RA-*, ED-*, DL-*, CM-*, EM-*, SP-* |
| **NONE** | 패키지 외 | TS-001~003 (OUT) |

### 2.3 분류 통계 요약

| 카테고리 | builder_type 분포 | evidence_group 주요 |
|---------|------------------|------------------|
| WP (15) | custom 9, generic 5, OUT 0 → 추정 P1 | A_law 13, NONE 2 |
| EQ (16) | generic 12, custom 4 (DONE) | A_law 8, NONE 8 |
| RA (6) | custom 2 (DONE), generic 4 | A_law 2, D_practical 4 |
| ED (5) | custom 3 (DONE), generic 2 | A_law 4, NONE 1 |
| PTW (8) | custom 4 (DONE), custom 4 (TODO) | A_law 5, D_practical 3 |
| DL (5) | generic 5 | NONE 5 |
| CL (10) | custom 8 (DONE+신규), generic 2 | A_law 4, D_practical 6 |
| PPE (4) | generic 4 | A_law 2, D_practical 2 |
| CM (7) | generic 7 | C_moel 4, D_practical 3 |
| HM (2) | custom 2 (DONE) | A_law 2 |
| EM (6) | generic 6 | C_moel 3, D_practical 3 |
| TS (5) | external 3 (OUT), generic 2 | A_law 5 |
| SP (4) | generic 4 | NONE 2, D_practical 2 |

---

## 3. 권장 디렉토리 구조

### 3.1 유지할 경로 (변경 금지)

| 경로 | 이유 |
|------|------|
| `data/masters/safety/documents/document_catalog.yml` | 단일 진실 소스. 분할 금지 (90종 한 파일 유지) |
| `data/masters/safety/mappings/*.yml` | mapping 9개 분리는 이미 적정. 추가 파일만 허용 |
| `engine/output/form_registry.py` | 단일 dispatcher 유지 |
| `engine/recommendation/document_recommender.py` | 단일 추천 엔진 유지 |
| `data/evidence/safety_law_refs/{DOC_ID}-{TYPE}{N}_*.json` | 파일명 규칙 유지 (현 67개 명명 일관성 보장) |
| `scripts/audit_safety_90_completion.py` | 단일 audit script |

### 3.2 신규 도입할 경로 (effective 90종 확장 대비)

| 경로 | 목적 | 도입 시점 |
|------|------|---------|
| `engine/output/builders/{category}/` | builder 카테고리별 분리 (예: `wp/`, `cl/`, `ptw/`) | **신규 builder부터 즉시 적용 권장** (정책 3.5 참조) |
| `engine/output/builders/_common/` | generic builder 공통 모듈 | generic 첫 구현 시 |
| `data/evidence/safety_law_refs/{category}/` | evidence 카테고리별 폴더 | **신규 evidence부터 즉시 적용 권장** (정책 3.5 참조) |
| `scripts/smoke_tests/{category}/` | smoke test 카테고리별 분리 | smoke_test 1만줄 도달 시 |
| `export/forms/{category}/{doc_id}/{YYYYMMDD}/` | 운영 산출물 표준 경로 | export API 구축 시 |
| `data/masters/safety/packages/work_packages.yml` | `_V11_PACKAGE_RULES` 외부화 | 패키지 10개 도달 시 |
| `docs/design/builders/{doc_id}_design.md` | builder별 설계 문서 | 신규 builder 구현 시 |

### 3.3 금지할 경로

| 경로 | 금지 사유 |
|------|---------|
| `engine/output/{doc_id}_builder.py` 평면 추가 | 50개 초과 시 탐색 어려움. **카테고리별 폴더 강제** |
| `data/evidence/{doc_id}/` 형태 | 기존 `safety_law_refs/{doc_id}-*` 명명 규칙 유지 |
| `export/` 직접 xlsx 저장 (영구) | 테스트 외에는 `/export/forms/` 경로 사용 |
| `scripts/smoke_test_p2_forms.py` 등 단계 분할 | smoke_test는 카테고리 분할만 허용 |
| `engine/output/builders/{doc_id}.py` (단수 폴더 미사용) | 카테고리 폴더 누락 금지 |

### 3.5 신규 builder/evidence 경로 정책 (정합성 보정)

**원칙: 기존 평면 파일은 이동하지 않음. 신규 항목부터 카테고리 표준 경로 적용.**

| 항목 | 기존 (이동 X) | 신규 (즉시 적용) |
|------|--------------|----------------|
| builder | `engine/output/{form_type}_builder.py` | **`engine/output/builders/{cat}/{form_type}_builder.py`** |
| evidence | `data/evidence/safety_law_refs/{evidence_id}_*.json` | **`data/evidence/safety_law_refs/{cat}/{evidence_id}_*.json`** |

#### 3.5.1 신규 builder 구현 시 import 정책

**form_registry.py는 평면 + 카테고리 폴더 양쪽 import 모두 허용**:

```python
# 기존 builder (평면 — 이동하지 않음)
from engine.output.fire_prevention_checklist_builder import build_fire_prevention_checklist_excel

# 신규 builder (즉시 카테고리 폴더 사용)
from engine.output.builders.cl.new_checklist_builder import build_new_checklist_excel
```

- 평면 파일과 카테고리 폴더가 **공존**하는 과도기 상태로 진입
- 양쪽 import는 **shim 없이 직접** form_registry.py에 등록
- 신규 builder가 `engine/output/builders/{cat}/`에 위치할 때 `engine/output/builders/__init__.py`와 `engine/output/builders/{cat}/__init__.py`는 빈 파일로 생성 (Python 패키지 인식 목적만)

#### 3.5.2 신규 evidence 작성 시 경로 정책

**카테고리 폴더 우선 적용. audit script는 재귀 glob로 양쪽 모두 스캔**:

```python
# scripts/audit_safety_90_completion.py에서 신규 evidence 추가 후 1줄만 변경
import glob
EV_DIR = "data/evidence/safety_law_refs"
# Before: for fname in os.listdir(EV_DIR): ...
# After:  for fpath in glob.glob(f"{EV_DIR}/**/*.json", recursive=True): ...
```

- audit script 변경은 **신규 evidence를 카테고리 폴더에 처음 저장하는 시점**에 동시 적용
- 변경 후 검증: `python scripts/audit_safety_90_completion.py` — evidence 카운트 동일해야 함

#### 3.5.3 정책 적용 시점

| 시점 | 액션 |
|------|------|
| 본 보정 직후 | 정책만 확정. 코드 변경 없음 |
| 신규 builder 1번째 추가 시 | `engine/output/builders/{cat}/` 디렉토리 생성 + 신규 builder 저장 + form_registry.py에 직접 import 추가 |
| 신규 evidence 1번째 추가 시 | `data/evidence/safety_law_refs/{cat}/` 디렉토리 생성 + 신규 evidence 저장 + audit script glob 변경 |
| 기존 평면 파일 일괄 이동 | M1/M2 임계점 도달 시 (Phase 1-A / 1-B) — `safety_directory_migration_plan.md` 참조 |

### 3.4 권장 최종 구조 (장기)

```
data/
├── masters/safety/
│   ├── documents/
│   │   └── document_catalog.yml          # 단일 진실 소스 (93종)
│   ├── mappings/                          # 현재 9개 + 추가 가능
│   │   ├── trade_document_mapping.yml
│   │   ├── trade_equipment_mapping.yml
│   │   └── ...
│   └── packages/                          # 신규 (선택)
│       └── work_packages.yml              # 추천 엔진 RULES 외부화
│
└── evidence/safety_law_refs/              # 현재 평면 유지 (67개)
    ├── PTW-002-L1_*.json                  # 100개 초과 시 카테고리 분할 검토
    ├── CL-005-P1_*.json
    └── (장기) ptw/, cl/, wp/ 분할

engine/
├── output/                                # 현재 평면
│   ├── form_registry.py                   # 단일 dispatcher 유지
│   ├── form_excel_builder.py              # RA-001 전용 (legacy)
│   ├── *_builder.py                       # 현재 30개 (50개 초과 시 분할)
│   └── (장기) builders/{category}/        # 50개 초과 시 도입
│       ├── wp/excavation_workplan.py
│       ├── ptw/hot_work_permit.py
│       ├── cl/fire_prevention_checklist.py
│       └── _common/                       # generic builder 공통
│
└── recommendation/
    └── document_recommender.py            # 단일 엔진 유지

scripts/
├── audit_safety_90_completion.py
├── smoke_test_p1_forms.py                 # 현재 단일 (1만줄 초과 시 분할)
└── (장기) smoke_tests/{category}/

export/                                    # 테스트용
└── (장기) forms/{category}/{doc_id}/{date}/  # 운영 산출물

docs/design/
├── safety_directory_architecture.md       # 본 문서
├── safety_document_db_model.md            # DB 논리 모델
├── safety_directory_migration_plan.md     # 마이그레이션 계획
└── (장기) builders/{doc_id}_design.md     # builder별 설계 문서
```

---

## 4. 명명 규칙

### 4.1 document_id 규칙

```
형식: {CAT}-{NNN}
예시: WP-001, PTW-002, CL-005, EQ-014

규칙:
- CAT: 13개 카테고리 코드 중 하나 (대문자)
- NNN: 카테고리 내 순번 (3자리, 0 패딩)
- 결번 허용 (예: WP-002 미사용 가능)
- ID는 **변경 불가** (재사용·재배치 금지)
- 신규 추가: 카테고리 내 최대 번호 + 1
```

### 4.2 evidence_id 규칙

```
형식: {DOC_ID}-{TYPE}{N}
예시: PTW-002-L1, CL-005-P1, ED-003-K2

TYPE 코드:
- L: Law (산안법·산안규칙 등 법령 조항)
- K: KOSHA GUIDE
- M: MOEL (노동부 별지·고시)
- P: Practical (실무 표준)

N: 같은 TYPE 내 순번 (1부터)

복합 evidence (한 문서에 여러 출처):
- PTW-002-L1, PTW-002-L2, ..., PTW-002-K1, PTW-002-K2 (순서 유지)
```

### 4.3 evidence 파일명 규칙

```
형식: {evidence_id}_{snake_case_summary}.json
예시:
  PTW-002-L1_safety_rule_article_236_fire_risk_work.json
  CL-005-P1_fire_prevention_checklist_practical.json

규칙:
- 파일명 첫 토큰은 evidence_id (정확히 일치)
- 두 번째 토큰부터는 snake_case 영문 요약
- 한글 미사용 (DB 인덱싱 호환성)
- 파일명 길이 80자 이하 권장
```

### 4.4 builder 파일명 규칙

```
형식: {form_type}_builder.py
예시:
  hot_work_permit_builder.py            (form_type = hot_work_permit)
  fire_prevention_checklist_builder.py  (form_type = fire_prevention_checklist)

규칙:
- form_type은 카탈로그 form_type 필드와 정확히 일치
- snake_case
- 핸들러 함수명: build_{form_type}_excel
- 1 builder = 1 파일 (절대 합치지 않음)
- 카테고리 폴더 도입 시: engine/output/builders/{cat}/{form_type}_builder.py
```

### 4.5 form_type 명명 규칙

```
규칙:
- snake_case 영문
- 명사형 (~_workplan, ~_permit, ~_checklist, ~_log, ~_record)
- document_id와 1:N 가능 (EQ-001~004는 WP form_type 공유)
- form_registry.py docstring에 등록 필수
```

### 4.6 generated output 저장 규칙

```
형식: export/forms/{category}/{doc_id}/{YYYY-MM-DD}/{site}_{seq}.xlsx
예시:
  export/forms/PTW/PTW-002/2026-04-25/테스트현장_001.xlsx
  export/forms/CL/CL-005/2026-04-25/테스트현장_001.xlsx

규칙:
- 영구 저장은 운영 DB의 safety_document_output 레코드와 동기화
- 파일명에 PII(주민번호, 연락처) 포함 금지
- 테스트용은 export/test/ 별도 분리
- xlsx 외에 PDF·HWP는 다음 단계에서 정의
```

### 4.7 smoke_test 함수 규칙

```
형식: run_{doc_id_lower}_smoke_test()
예시:
  run_cl005_smoke_test()
  run_ptw002_smoke_test()

규칙:
- 함수 단독 import·호출 가능 (메인 진입과 독립)
- list[tuple[str, str, str]] 반환 (verdict, name, detail)
- run_smoke_test()에 results.extend() 방식으로 통합
- 카테고리별 분할 도입 시: scripts/smoke_tests/{cat}/test_{doc_id}.py
```

---

## 5. 작업 산출물 폴더 표준 (확장)

### 5.1 카테고리별 output 경로 매핑

| 카테고리 | output 경로 | 보관 기간 |
|---------|-----------|---------|
| WP | `export/forms/WP/{doc_id}/{date}/` | 3년 |
| PTW | `export/forms/PTW/{doc_id}/{date}/` | 3년 (산안법 제164조) |
| CL | `export/forms/CL/{doc_id}/{date}/` | 3년 |
| RA | `export/forms/RA/{doc_id}/{date}/` | 3년 (산안법 제36조) |
| ED | `export/forms/ED/{doc_id}/{date}/` | 3년 (산안법 제29조) |
| HM | `export/forms/HM/{doc_id}/{date}/` | 5년 (작업환경측정 제125조) |
| EM | `export/forms/EM/{doc_id}/{date}/` | 5년 (산업재해 제57조) |
| 기타 | `export/forms/{cat}/{doc_id}/{date}/` | 카테고리별 정책 |

### 5.2 보관 기간 vs 파일 보존

- 운영 DB `safety_document_output`은 메타데이터만 보관 (영구)
- 실제 파일은 발행일 + 보관 기간 후 archived/ 이동 (선택)
- xlsx 외 추가 포맷(PDF, HWP)은 동일 디렉토리, 확장자만 분리

---

## 6. 향후 변경 시 검토 체크리스트

### 6.1 신규 builder 추가 시

- [ ] document_catalog.yml에 항목 존재 확인
- [ ] form_type이 snake_case이며 docstring 등록
- [ ] builder 파일명이 `{form_type}_builder.py`
- [ ] evidence_id 명명 규칙 준수 (`{DOC_ID}-{TYPE}{N}`)
- [ ] evidence 파일명 snake_case
- [ ] smoke_test 함수명 `run_{docidlower}_smoke_test()`
- [ ] 추천 엔진 연결 필요 시 mapping/recommender 업데이트
- [ ] related_documents 양방향 연결 (예: PTW-002 ↔ CL-005)

### 6.2 신규 카테고리 추가 시 (긴급 시)

- [ ] 13개 카테고리로 분류 불가 사유 검토
- [ ] 추가 시 코드 2자리 (예: HM, SP) 또는 3자리 (예: PTW)
- [ ] document_catalog.yml의 category_code 필드와 일치
- [ ] 본 문서의 카테고리 표 업데이트

### 6.3 디렉토리 구조 변경 시

- [ ] safety_directory_migration_plan.md 절차 준수
- [ ] import 경로 변경 → re-export 또는 alias 적용
- [ ] form_registry.py docstring 동기화
- [ ] 모든 검증 스크립트 PASS 유지

---

## 7. 결론

- 본 설계는 **현재 구조 변경 없이** effective 90종 확장을 위한 **표준만 사전 확정**
- 실제 디렉토리 분할(기존 파일 일괄 이동)은 다음 임계점 도달 시 적용:
  - **Phase 1-A**: builder 50개 초과 → `engine/output/builders/{cat}/` 일괄 이동
  - **Phase 1-B**: evidence 100개 초과 → `data/evidence/safety_law_refs/{cat}/` 일괄 이동
  - Phase 2: smoke_test 1만줄 초과 → `scripts/smoke_tests/{cat}/` 분할
  - Phase 3: 패키지 10개 초과 → `_V11_PACKAGE_RULES` yaml 외부화
- **신규 추가 항목은 카테고리 표준 경로 즉시 적용** (정책 3.5)
- 명명 규칙은 **즉시 적용** — 신규 추가 항목부터 본 문서 준수
- 임계점 미도달 항목은 현행 평면 구조 유지 → 기존 import·검증 스크립트 영향 없음

---

*생성: 2026-04-25 / 연계: `safety_document_db_model.md`, `safety_directory_migration_plan.md`*

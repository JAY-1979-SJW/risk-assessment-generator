# V1.1 Stage 0 — 현재 앱 구조 및 문서 생성 엔진 현황 점검

**작성일**: 2026-04-29  
**점검자**: Claude Code (Haiku)  
**범위**: 신축공사 V1.1 구현 착수 전 현황 파악  
**상태**: READ-ONLY (코드 수정 금지)

---

## 1. 현황 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| **백엔드 프레임워크** | ✓ FastAPI | backend/main.py |
| **문서 생성 엔진** | ✓ 90종 form_registry + 10종 supplementary | engine/output/ |
| **기존 form export API** | ✓ 존재 | backend/routers/form_export.py |
| **프론트엔드** | ✓ React 18+ | frontend/src/ |
| **DB** | ✓ PostgreSQL | backend/db.py, psycopg2 |
| **기존 Project 모델** | ✓ 부분 존재 | backend/routers/projects.py |
| **테스트/Audit** | ✓ 존재 | scripts/audit_*.py, tests/ |
| **배포** | ✗ docker-compose 없음 | Dockerfile만 존재 |

---

## 2. 프로젝트 구조

```
.
├── backend/               ← FastAPI 앱
│   ├── main.py           (FastAPI 앱 진입점)
│   ├── routers/          (14개 라우터)
│   │   ├── form_export.py    (✓ form export API)
│   │   ├── projects.py       (✓ 기존 project CRUD)
│   │   └── ...
│   ├── schemas/          (2개: risk_assessment_draft, risk_assessment_build)
│   ├── services/
│   ├── db.py             (PostgreSQL 연결)
│   └── requirements.txt
├── engine/
│   ├── output/           (90 form_builders + 10 supplementary_builders)
│   │   ├── form_registry.py          (87 FormSpec 등록)
│   │   ├── supplementary_registry.py (10 SupplementalSpec 등록)
│   │   └── *_builder.py (102개 파일)
│   └── 기타 (kras_connector, rag_risk_engine, rule_selector 등)
├── frontend/             ← React
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── app/                  (부차적 API, Flask?)
│   ├── api/
│   └── __init__.py
├── scripts/              (60+개 검증/수집 스크립트)
│   ├── audit_*.py        (audit 스크립트)
│   ├── smoke_test_*.py   (smoke test)
│   └── validate_*.py     (validation 스크립트)
├── tests/                (pytest 기반)
│   └── test_risk_assessment_draft_api.py
├── data/                 (마스터 데이터)
│   ├── masters/
│   └── law_db/
├── docs/
│   ├── design/           (설계 문서)
│   │   └── new_construction_v1_1_implementation_backlog.md (최신)
│   └── reports/          (현황 보고서)
└── infra/                (인프라 설정)
```

---

## 3. 백엔드 구조

### 3-1. FastAPI 프레임워크

- **진입점**: `backend/main.py`
- **라우터 등록**: 14개 라우터 (`backend/routers/`)
  - assessments.py
  - **form_export.py** ← ⭐ form registry 사용
  - projects.py ← ⭐ 기존 project CRUD
  - company.py
  - organization.py
  - engine_results.py
  - export.py
  - forms.py
  - recommend.py
  - risk_assessment.py
  - risk_assessment_build.py
  - risk_assessment_draft.py
  - templates.py
- **미들웨어**: CORS 설정
- **인증**: API Key 기반 (보안 설정됨)
- **실행 명령**: `uvicorn backend.main:app --reload`

### 3-2. 데이터베이스

- **DB**: PostgreSQL
- **ORM**: SQLAlchemy 미사용, psycopg2 직접 사용
- **마이그레이션**: Alembic 미사용 (수동 SQL)
- **연결**: `backend/db.py` (fetchone, fetchall, execute 헬퍼)
- **기존 테이블**:
  - `projects` (id, title, status, created_at, updated_at)
  - `project_company_info` (project_id FK)
  - 기타 (risk_assessment_draft, 등등)

### 3-3. 스키마 정의

- **위치**: `backend/schemas/`
- **현황**:
  - `risk_assessment_draft.py` — SiteContext (부분적 정의)
  - `risk_assessment_build.py` — 평가 빌드용

---

## 4. 문서 생성 엔진 구조

### 4-1. Form Registry

**파일**: `engine/output/form_registry.py`  
**상태**: ✓ 정상  
**등록 수**: **87개 FormSpec**

구조:
```python
@dataclass
class FormSpec:
    form_type: str          # "education_log", "risk_assessment", ...
    display_name: str       # 한글명
    document_id: str        # "ED-001", "RA-001", ...
    builder: Callable       # build_*_excel 함수
    # ... 기타 필드
```

**API**:
```python
from engine.output.form_registry import build_form_excel, get_form_spec, list_supported_forms

build_form_excel("education_log", form_data) → bytes (xlsx)
get_form_spec("education_log") → FormSpec dict
list_supported_forms() → list[dict]
```

**등록된 form_type 예시**:
- education_log, special_education_log, manager_job_training_record
- risk_assessment, risk_assessment_register, risk_assessment_meeting_minutes
- excavation_workplan, vehicle_construction_workplan, tower_crane_workplan
- confined_space_permit, hot_work_permit, work_at_height_permit
- scaffold_installation_checklist, fall_protection_checklist
- ... (총 87개)

### 4-2. Supplementary Registry

**파일**: `engine/output/supplementary_registry.py`  
**상태**: ✓ 정상  
**등록 수**: **10개 SupplementalSpec**

구조:
```python
@dataclass
class SupplementalSpec:
    supplemental_type: str       # "attendance_roster", "photo_attachment_sheet", ...
    display_name: str
    parent_form_types: Tuple     # 연결 가능 핵심서류
    output_builder: Callable
```

**등록된 10가지**:
1. attendance_roster (참석자 명부)
2. photo_attachment_sheet (사진대지)
3. document_attachment_list (첨부서류 목록표)
4. confined_space_gas_measurement (산소·가스농도 측정기록표)
5. work_completion_confirmation (작업 종료 확인서)
6. improvement_completion_check (개선조치 완료 확인서)
7. equipment_operator_qualification_check (운전원 자격 확인표)
8. watchman_assignment_confirmation (감시인 배치 확인서)
9. education_makeup_confirmation (미참석자 추가교육 확인서)
10. ppe_receipt_confirmation (보호구 수령 확인서)

### 4-3. Builder 파일

**위치**: `engine/output/`  
**파일 수**: 102개 (form 90 + supplementary 10 + 기타 2)

예시:
- `education_log_builder.py` → `build_education_log_excel(form_data) → Workbook`
- `risk_assessment_register_builder.py` → `build_risk_assessment_register_excel(...) → Workbook`
- `attendance_roster_builder.py` → `build_attendance_roster_excel(...) → Workbook`

---

## 5. 기존 API 구조

### 5-1. Form Export API

**라우터**: `backend/routers/form_export.py`  
**엔드포인트**:

```
GET  /api/forms/types               — 지원 form_type 목록
POST /api/forms/export              — Excel 생성 & 다운로드
GET  /api/forms/specs/{form_type}   — form_type 스펙 조회
```

**사용 예**:

```bash
# form_type 목록
GET /api/forms/types
→ { "forms": [{ "form_type": "education_log", "display_name": "교육일지" }, ...] }

# Excel 생성
POST /api/forms/export
{
  "form_type": "education_log",
  "form_data": { "company_name": "OO건설", ... }
}
→ 200, xlsx bytes (Content-Disposition: attachment)
```

**구현 방식**:
- form_registry.build_form_excel() 호출
- 응답: StreamingResponse (xlsx 바이너리)
- 파일명: "{form_type}_{timestamp}.xlsx" (한글 지원)

### 5-2. 기존 Projects API

**라우터**: `backend/routers/projects.py`

```
GET    /api/projects              — 공사 목록
POST   /api/projects              — 공사 생성
GET    /api/projects/{pid}        — 공사 상세
PUT    /api/projects/{pid}        — 공사 수정
DELETE /api/projects/{pid}        — 공사 삭제
```

**현황**:
- DB: `projects` 테이블 (id, title, status, created_at, updated_at)
- 스키마: ProjectCreate, ProjectUpdate (Pydantic)
- 지원: 기본 CRUD만
- **미지원**: 신축공사 관련 필드 (공사명, 위치, 발주자, 착공일 등)

### 5-3. 기타 라우터

- **export.py**: 위험성평가 export
- **engine_results.py**: 엔진 결과 조회
- **recommend.py**: 서류 추천
- **risk_assessment_build.py**: 평가 빌드 API
- **risk_assessment_draft.py**: 평가 임시저장

---

## 6. 프론트엔드 구조

### 6-1. React 프로젝트

**프레임워크**: React 18+  
**빌드 도구**: Vite  
**구조**:

```
frontend/src/
├── pages/           (페이지 컴포넌트)
├── components/      (공유 컴포넌트)
├── api/             (API 호출 함수)
├── App.jsx          (메인 앱)
├── main.jsx         (진입점)
└── devlog/          (개발로그)
```

**라우팅**: React Router v6 (추정)  
**상태관리**: Context API 또는 Zustand (미확인)  
**스타일**: CSS Modules 또는 Tailwind (미확인)

### 6-2. 기존 화면 현황

- 위험성평가 작성 화면 ✓
- 임시저장/조회 화면 ✓
- 결과 조회 화면 ✓
- **신축공사 전용 화면**: ❌ 없음

---

## 7. 테스트/검증 구조

### 7-1. Pytest 테스트

**위치**: `tests/`  
**파일**: test_risk_assessment_draft_api.py (1개)  
**상태**: 기본 테스트만 존재

### 7-2. Audit 스크립트

**위치**: `scripts/`  
**스크립트**:

| 스크립트 | 용도 |
|---------|------|
| `audit_excel_layout_quality.py` | ✓ Excel A4 레이아웃 감사 |
| `audit_safety_90_completion.py` | ✓ 90종 완성도 감사 |
| `audit_safety_gap.py` | ✓ 갭 분석 |
| `validate_excel_builders.py` | ✓ builder 검증 |
| `smoke_test_p0_forms.py` | ✓ P0 형식 smoke 테스트 |
| `smoke_test_p1_forms.py` | ✓ P1 형식 smoke 테스트 |
| `validate_form_registry.py` | ✓ registry 검증 |

**상태**: 모두 실행 가능 (read-only)

### 7-3. 검증 결과 (기존)

- form_registry: 87건 로드 가능 ✓
- supplementary_registry: 10건 로드 가능 ✓
- Excel syntax: 모두 정상 ✓
- A4 레이아웃 QA: PASS (WARN 1건 허용) ✓

---

## 8. 데이터/DB 구조

### 8-1. 기존 테이블

현재 DB에 존재하는 테이블:

| 테이블 | 목적 | Stage 1에서 필요? |
|--------|------|---------|
| `projects` | 프로젝트 관리 | ⭐ 확장 필요 |
| `project_company_info` | 공사 기본정보 | ⭐ 확장 필요 |
| `risk_assessment_draft` | 평가 임시저장 | — (기존 용도 유지) |
| `users` | 사용자 | ✓ 참조만 |

### 8-2. 신축공사 V1.1에 필요한 모델

| 모델 | 상태 | 비고 |
|------|------|------|
| Project (공사 기본정보) | 부분 존재 | 필드 확장 필요 |
| Site (현장 정보) | ❌ 없음 | 신규 생성 |
| Contractor (협력업체) | ❌ 없음 | 신규 생성 |
| Worker (근로자) | ❌ 없음 | 신규 생성 |
| Equipment (장비) | ❌ 없음 | 신규 생성 |
| WorkSchedule (공종 일정) | ❌ 없음 | 신규 생성 |
| DocumentGenerationJob | ❌ 없음 | 신규 생성 |
| GeneratedDocumentPackage | ❌ 없음 | 신규 생성 |

---

## 9. 운영/배포 구조

### 9-1. Docker

**상태**: ⚠️ 부분적

- `backend/Dockerfile` ✓
- `frontend/Dockerfile` ✓
- `docker-compose.yml` ❌ 없음
- `infra/` 디렉토리 존재 (설정 추정)

### 9-2. 환경변수

**파일**:
- `backend/.env`
- `backend/requirements.txt`
- `scripts/.env.example`

**주요 변수**:
- `DATABASE_URL` (PostgreSQL)
- `INTERNAL_API_KEY` (API 보안)
- `LOG_DIR`, `DEVLOG_DIR` (로깅)

---

## 10. V1.1 구현 관점의 갭 분석

### 10-1. 이미 존재

✓ **백엔드 기반**
- FastAPI 프레임워크
- form registry (90종 완성)
- supplementary registry (10종 완성)
- form export API (`/api/forms/export`)
- PostgreSQL + psycopg2
- CORS, API Key 보안

✓ **프론트엔드 기반**
- React 18+ 앱
- Vite 빌드 시스템
- 기본 라우팅 구조

✓ **테스트/검증**
- Pytest 기반 테스트
- Audit 스크립트 (audit_excel_layout_quality 등)
- Smoke test 스크립트

### 10-2. 일부 존재

⚠️ **Project 모델**
- 기본 CRUD 존재 (projects.py)
- **필드 부족**: 공사 유형, 위치, 발주자, 시공사, 예정 착공/준공일, 안전관리자, Phase 등 신축공사 필드 없음

⚠️ **API 구조**
- form export API 존재
- **확장 필요**: project 기본정보 API, 공종 일정 API, 근로자 API, 자동생성 Rule API

⚠️ **프론트엔드**
- 기본 UI 화면 존재
- **없음**: 신축공사 공사 관리, 공종 등록, 근로자 관리, 서류 생성 마법사 화면

### 10-3. 없음

❌ **신축공사 데이터 모델**
- Site, Contractor, Worker, Equipment, WorkSchedule
- DocumentGenerationJob, GeneratedDocumentPackage

❌ **자동생성 규칙 엔진**
- Rule 기반 서류 추천 로직
- Trigger 감지 (근로자 등록, 공종 선택, 장비 등록 등)

❌ **배포 자동화**
- docker-compose.yml
- CI/CD 파이프라인 (GitHub Actions 추정되지만 확인 미필)

❌ **프론트엔드 UI**
- 공사 등록/수정 폼
- 공종 일정 입력 화면
- 근로자 관리 화면
- 장비 관리 화면
- 서류 생성 마법사
- 오늘 할 일 대시보드
- 누락 서류 체크리스트

### 10-4. 확인 불가

? **ORM 사용 여부**
- SQLAlchemy 미사용 (직접 SQL)
- Alembic 마이그레이션 미사용
- 모델 클래스 정의 확인 필요

? **상태관리 도구**
- Redux, Zustand, Context API 중 어느 것 사용?

? **프론트엔드 스타일링**
- Tailwind CSS, CSS Modules, styled-components 중 어느 것?

---

## 11. Stage 1 데이터 모델 설계 시 확인 사항

### 11-1. Project 모델 확장

**현재**:
```python
class ProjectCreate(BaseModel):
    title: str = "새 위험성평가"

# DB columns: id, title, status, created_at, updated_at
```

**필요한 추가 필드**:
- project_type: enum [신축건축, 신축토목, 신축기타]
- location: string (공사 위치)
- client_name: string (발주자)
- contractor_name: string (시공사)
- contract_amount: decimal (공사 금액)
- safety_manager_id: FK to users
- planned_start_date, planned_end_date: date
- actual_start_date, actual_end_date: date (nullable)
- phase: enum [등록, 착공전준비, 착공, 진행중, 준공]
- phase_updated_at: timestamp

### 11-2. 신규 모델 (Alembic migration 필요)

```
CREATE TABLE sites (
  site_id UUID PRIMARY KEY,
  project_id UUID NOT NULL FK,
  site_name VARCHAR,
  site_address VARCHAR,
  site_manager_id FK to users,
  phone_number VARCHAR,
  emergency_contact VARCHAR,
  status ENUM,
  total_workers INT,
  total_subcontractors INT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE contractors (...);
CREATE TABLE workers (...);
CREATE TABLE equipment (...);
CREATE TABLE work_schedules (...);
CREATE TABLE document_generation_jobs (...);
CREATE TABLE generated_document_packages (...);
```

### 11-3. ORM 선택

**권장**: SQLAlchemy + Alembic
- 장점: type-safe, migration 자동화, relation 관리 용이
- 변경비: 현재 psycopg2 직접 사용에서 ORM으로 전환 필요

**또는**: 현재 psycopg2 유지 (수동 마이그레이션)
- 장점: 최소 변경
- 단점: SQL 관리 부담

---

## 12. 리스크 및 권장 진행 순서

### 12-1. 식별된 리스크

| 리스크 | 영향 | 완화 방안 |
|--------|------|---------|
| ORM 미사용 | migration 관리 어려움 | SQLAlchemy 도입 검토 |
| docker-compose 없음 | 로컬 개발 환경 설정 복잡 | Stage 2 이전에 작성 |
| Project 모델 기존 사용 | 기존 코드와 충돌 가능 | 필드 확장 vs 신규 테이블 검토 |
| 프론트엔드 UI 완전 신규 | 개발 기간 길어질 가능성 | 우선순위 높게 설정 |

### 12-2. 권장 Stage 0 ~ 1 진행 순서

```
1. Stage 0 현황 점검 ✓ (본 문서)
   └→ ORM 선택 결정 (SQLAlchemy vs psycopg2)

2. Stage 1 데이터 모델 설계
   ├─ Project 모델 확장 스키마 작성
   ├─ Site, Contractor, Worker, Equipment, WorkSchedule 스키마 작성
   ├─ DocumentGenerationJob, GeneratedDocumentPackage 스키마 작성
   └─ Alembic migration 파일 준비

3. (병렬) docker-compose.yml 작성
   └─ PostgreSQL, Redis, FastAPI 서비스 정의

4. (병렬) Project API 확장
   ├─ Project.fields 추가
   ├─ Site CRUD API
   └─ Contractor CRUD API
```

---

## 13. 검증 결과 요약

### 13-1. Git Status

```
✓ Clean working tree (수정 없음)
✓ 87 커밋 ahead of origin/master
```

### 13-2. Registry 로드

```
✓ form_registry.py: syntax OK, 87 FormSpec
✓ supplementary_registry.py: syntax OK, 10 SupplementalSpec
```

### 13-3. Code Changed

```
✓ 코드 수정 없음 (read-only)
✓ 신규 파일 생성: docs/reports/v1_1_stage0_current_architecture.md (본 파일)
```

### 13-4. Catalog/Registry/Supplementary 변경

```
✓ document_catalog.yml: 변경 없음
✓ form_registry.py: 변경 없음
✓ supplementary_registry.py: 변경 없음
```

---

## 최종 판정

✅ **PASS**

### 검증 완료 사항

1. ✓ FastAPI 백엔드 구조 확인
2. ✓ form_registry 87건 정상 로드
3. ✓ supplementary_registry 10건 정상 로드
4. ✓ form export API 확인 (backend/routers/form_export.py)
5. ✓ PostgreSQL DB 사용 확인
6. ✓ React 프론트엔드 구조 확인
7. ✓ 기존 Project 모델 부분 존재 확인
8. ✓ 테스트/Audit 스크립트 확인
9. ✓ 코드 수정 없음 확인
10. ✓ git working tree clean

### 다음 단계

**Stage 1 데이터 모델 설계 진행 가능**

- Project 모델 확장 필드 리스트 작성
- Site, Contractor, Worker, Equipment, WorkSchedule 스키마 설계
- Alembic migration 파일 준비
- ORM (SQLAlchemy) 도입 검토

---

**Stage 0 현황 점검 완료**  
**상태**: READY FOR STAGE 1

# 신축공사 웹 자동생성 V1.1 구현 백로그

**작성일**: 2026-04-29  
**기준**: new_construction_web_generation_flow.md (V1.0 설계)  
**범위**: 신축공사 MVP (착공~준공)  
**목표**: 공사 등록 → 일정 선택 → 자동생성 → Excel 다운로드

---

## 목차

1. [현재 기준선 요약](#1-현재-기준선-요약)
2. [V1.1 MVP 범위](#2-v11-mvp-범위)
3. [Stage별 구현 계획](#3-stage별-구현-계획)
4. [P0 작업 (우선순위 높음)](#4-p0-작업-우선순위-높음)
5. [작업량 예상](#5-작업량-예상)
6. [Stage 0 상세 계획 및 지시문](#6-stage-0-상세-계획-및-지시문)

---

## 1. 현재 기준선 요약

### 1-1. 핵심서류 현황

| 항목 | 수량 | 상태 |
|------|------|------|
| form_registry 등록 | 87건 | ✓ DONE |
| document_catalog DONE | 90종 | ✓ DONE |
| Excel builder | 90종 | ✓ 완성 |
| A4 레이아웃 QA | 96/97 PASS | ✓ PASS |

### 1-2. 부대서류 현황

| 항목 | 수량 | 상태 |
|------|------|------|
| supplementary_registry | 10종 | ✓ LIVE |
| attendance_roster | 1 | ✓ |
| photo_attachment_sheet | 1 | ✓ |
| document_attachment_list | 1 | ✓ |
| confined_space_gas_measurement | 1 | ✓ |
| work_completion_confirmation | 1 | ✓ |
| improvement_completion_check | 1 | ✓ |
| equipment_operator_qualification_check | 1 | ✓ |
| watchman_assignment_confirmation | 1 | ✓ |
| education_makeup_confirmation | 1 | ✓ |
| ppe_receipt_confirmation | 1 | ✓ |

### 1-3. 설계 문서 현황

| 항목 | 상태 |
|------|------|
| new_construction_web_generation_flow.md | ✓ 완성 |
| new_construction_safety_schedule_matrix.md | ✓ 완성 |
| UI 모형 (6개 화면) | ✓ 정의 |
| API 설계 (REST) | ✓ 정의 |
| 자동생성 Rule (10개) | ✓ 정의 |
| 데이터 모델 (9개 엔티티) | ✓ 정의 |

### 1-4. 기술 스택 기반

- **백엔드**: Python 3.10+, FastAPI, PostgreSQL
- **프론트엔드**: React 18+, TypeScript, Tailwind CSS
- **문서 생성**: openpyxl (Excel 90종 완성)
- **인프라**: Docker, S3, Redis, GitHub Actions

---

## 2. V1.1 MVP 범위

### 2-1. 포함 항목

✅ **공사 관리**
- 신축공사 공사 등록 (Project 생성)
- 공사 기본정보 입력 (공사명, 위치, 발주자, 시공사)
- 예정 착공/준공 일정 입력
- 안전관리자 지정
- 공사 Phase 자동/수동 관리

✅ **현장 정보**
- 현장소장, 안전관리자 배치
- 근로자 예정 수 통계
- 협력업체 기본 정보

✅ **공종 일정**
- 공종 목록 (7가지: 토공, 파일, 거푸집, 비계, 양중, 전기, 설비)
- 공종별 착수 예정일 입력
- 위험도 자동 추천 또는 수동 입력

✅ **근로자 관리**
- 근로자 기본정보 입력 (이름, 유형, 역할)
- 투입 예정일 입력
- 자격증 정보 (선택)

✅ **장비 관리**
- 장비 종류 선택
- 운전원 정보 입력
- 반입 예정일 입력
- 보험·검사 정보 입력

✅ **자동생성 Rule MVP (최소 3개)**
- **Rule-01**: 신규 근로자 등록 시 (교육일지, 서약서, 보호구)
- **Rule-02**: 공종 착수 전 (공종별 PTW)
- **Rule-03**: 매일 작업 전 (TBM, 안전점검)
- (추가 가능: 장비반입, 착공전 기본체계, 준공 전 최종)

✅ **오늘 할 일 대시보드**
- 자동 제안 서류 목록
- 마감 임박 경고
- Rule 기반 추천

✅ **문서 생성 & 다운로드**
- 자동 제안 서류 선택/확인
- Excel 형식 일괄 생성 (openpyxl 활용)
- ZIP 패키지 압축
- 개별 파일 다운로드
- (선택) 이메일 전송

✅ **문서 패키지 관리**
- 생성된 패키지 목록 조회
- 재생성 기능
- 생성 이력 보관

### 2-2. 제외 항목

❌ 리모델링, 개보수, 철거·해체
❌ 외국인 근로자 다국어 서류
❌ 소방감리 전용 서류
❌ PDF 출력 (V2.0)
❌ 전자서명, 결재 워크플로우
❌ 모바일 앱
❌ 클라우드 협업 편집
❌ AI 자동 추천

---

## 3. Stage별 구현 계획

### Stage 0 — 현황 점검 (확인만, 수정 금지)

**목표**: 기존 backend/frontend 구조 및 API 현황 파악

**선행 조건**:
- 기존 프로젝트 구조 확인 가능
- 기존 form export API 확인 가능

**확인 대상**:
1. 기존 FastAPI 또는 Flask 백엔드 구조
2. 기존 form export 엔드포인트 확인
3. form_registry.py 및 supplementary_registry.py 로드 확인
4. 기존 React 프론트엔드 라우팅
5. 데이터베이스 스키마 (User, Project 등 기존 테이블)

**검증 명령**:
```bash
# 백엔드 구조
ls -la src/ app/ engine/

# Registry 로드 확인
python -c "from engine.output.form_registry import list_form_types; print(len(list_form_types()))"
python -c "from engine.output.supplementary_registry import list_supplemental_types; print(len(list_supplemental_types()))"

# API 확인
grep -r "form_type\|export" src/ app/ | head -20

# 기존 DB 마이그레이션
ls -la alembic/versions/ | tail -10
```

**PASS 기준**:
- form_registry 87건 정상 로드
- supplementary_registry 10건 정상 로드
- 기존 export API 또는 form builder 호출 방식 확인
- 기존 React 라우팅 구조 확인

**FAIL 기준**:
- Registry 로드 실패
- Export API 없음

**금지 사항**:
- ❌ 코드 수정 금지
- ❌ 파일 생성 금지
- ❌ 기존 API 변경 금지

**예상 리스크**:
- 기존 구조와 신규 구현의 연결점 불명확
- DB 스키마 변경 필요 여부 불명

**참고 문서**:
- CLAUDE.md (프로젝트 규칙)
- README.md (프로젝트 구조)

---

### Stage 1 — Project/Site 기본 모델 설계

**목표**: 신축공사 공사 정보 데이터 구조 정의 및 기존 DB 연결 방식 확인

**선행 조건**:
- Stage 0 완료 (기존 구조 파악)
- 기존 DB 사용자 테이블 확인 가능

**수정 대상 파일 후보**:
- `alembic/versions/` — 신규 migration 생성 (또는 기존 활용)
- `src/models/` 또는 `app/models/` — SQLAlchemy 모델 추가
  - Project (공사 기본정보)
  - Site (현장 정보)
  - Contractor (협력업체)
  - Worker (근로자)
  - Equipment (장비)
  - WorkSchedule (공종 일정)

**금지 사항**:
- ❌ 기존 User, Auth 관련 테이블 수정
- ❌ 기존 테이블 삭제
- ❌ form_registry, supplementary_registry 수정
- ❌ document_catalog.yml 수정

**구현 범위**:
1. Project 모델 설계 (project_id, name, type, location, status, phase, dates)
2. Site 모델 (site_id, project_id FK, address, manager_id)
3. Contractor 모델 (company_name, status, safety_level)
4. Worker 모델 (name, type, role, entry_date)
5. Equipment 모델 (type, serial, entry_date, operator_id)
6. WorkSchedule 모델 (work_type, dates, contractor_id, risk_level)

**검증 명령**:
```bash
# SQLAlchemy 모델 파싱 (정문법 확인)
python -c "from sqlalchemy import inspect; from app.models import Project; print(inspect(Project).columns.keys())"

# DB 마이그레이션 dry-run
alembic upgrade --sql
```

**PASS 기준**:
- 6개 모델 모두 정의 완료
- foreign key 관계 정의 완료
- 기존 User와의 연결 확인

**FAIL 기준**:
- 모델 정문법 오류
- FK 순환 참조

**예상 리스크**:
- 기존 User.id와 Project.created_by의 연결 방식
- 다중 Site 지원 필요 여부 불명

---

### Stage 2 — 공사 등록 API

**목표**: Project/Site/Contractor 생성, 조회, 수정 REST API 구현

**선행 조건**:
- Stage 1 완료 (모델 정의)
- 기존 FastAPI 라우터 구조 확인

**수정 대상 파일 후보**:
- `src/routers/projects.py` 또는 `app/routes/projects.py` (신규 생성)

**금지 사항**:
- ❌ 신규 builder 생성
- ❌ registry 수정
- ❌ document_catalog.yml 수정

**구현 범위**:
1. POST /api/v1/projects — 공사 생성
   - Request: { name, type, location, client_name, contractor_name, planned_start, planned_end }
   - Response: { project_id, status, phase, created_at }
2. GET /api/v1/projects — 공사 목록 (사용자별 필터)
3. GET /api/v1/projects/{project_id} — 공사 상세
4. PUT /api/v1/projects/{project_id} — 공사 정보 수정
5. PATCH /api/v1/projects/{project_id}/phase — Phase 변경 (수동)
6. POST /api/v1/projects/{project_id}/sites — Site 생성
7. POST /api/v1/projects/{project_id}/contractors — Contractor 등록

**검증 명령**:
```bash
# API 테스트
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"신축A","type":"신축건축","location":"서울시"}'

# 응답: { project_id: "uuid", status: "등록", phase: "Phase 0" }
```

**PASS 기준**:
- 모든 엔드포인트 응답 200 OK
- project_id 자동 생성
- phase 자동 설정 (Phase 0)

**FAIL 기준**:
- 엔드포인트 오류 (500, 404)
- 응답 스키마 불일치

**예상 리스크**:
- 기존 권한 검증 (auth) 통합 필요
- 동시성 제어 (concurrent update) 미지원

---

### Stage 3 — 신축공사 일정 Phase 0~12 API

**목표**: 공종 일정 관리 및 Phase별 필요서류 조회 API

**선행 조건**:
- Stage 2 완료 (Project 기본 API)

**수정 대상 파일 후보**:
- `src/routers/work_schedules.py` (신규)
- `src/services/phase_rules.py` (신규, Phase/공종별 Rule 매핑)

**금지 사항**:
- ❌ registry/catalog 수정

**구현 범위**:
1. POST /api/v1/projects/{project_id}/work-schedules — 공종 착수일 등록
2. GET /api/v1/projects/{project_id}/work-schedules — 공종 일정 목록
3. GET /api/v1/projects/{project_id}/phases — Phase 진행상황 조회
4. GET /api/v1/projects/{project_id}/phases/{phase}/required-documents — Phase별 필수 서류 목록

**Phase 정의** (new_construction_safety_schedule_matrix.md 기준):
- Phase 0: 공사 등록/계약 직후
- Phase 1: 착공 전 기본체계
- Phase 2: 착공계 제출
- Phase 3: 근로자 투입 전
- Phase 4: 장비 반입 전
- Phase 5: 공종별 착수 전 (5-1~5-7)
- Phase 6: 매일 작업 전
- Phase 7: 작업 중 / 종료
- Phase 8: 주간 반복
- Phase 9: 월간 반복
- Phase 10: 이벤트 발생 (사고 등)
- Phase 11: 준공 2~4주 전
- Phase 12: 준공 시 / 후 보존

**검증 명령**:
```bash
# Phase별 서류 조회
curl http://localhost:8000/api/v1/projects/PRJ001/phases/6/required-documents

# 응답: { phase: "6", forms: [tbm_log, pre_work_safety_check, ...] }
```

**PASS 기준**:
- Phase별 폼 목록 반환 (form_type 기준)
- 공종별 조건부 폼 추가

**예상 리스크**:
- Phase 자동 진행 로직 복잡도
- 사용자 수동 Phase 변경 지원 필요

---

### Stage 4 — 자동생성 Rule MVP (최소 3개)

**목표**: 최소 3개 Rule 기반 자동생성 로직 구현

**선행 조건**:
- Stage 2, 3 완료 (Project, WorkSchedule API)
- form_registry 정상 로드 확인

**수정 대상 파일 후보**:
- `src/services/generation_engine.py` (신규, Rule 엔진)
- `src/routers/documents.py` (신규, 생성 API)

**금지 사항**:
- ❌ registry 수정
- ❌ builder 수정

**MVP 3가지 Rule** (new_construction_safety_schedule_matrix.md 기준):

#### Rule-01: 신규 근로자 등록 시
```
트리거: POST /api/v1/projects/{project_id}/workers
조건: worker.entry_date >= today
자동 생성 제안:
  - education_log (교육일지, 채용 시 8시간)
  - new_worker_safety_pledge (서약서)
  - ppe_issue_register (보호구 지급대장)
  - ppe_management_checklist (보호구 점검표)
  부대서류:
  - attendance_roster
  - ppe_receipt_confirmation
```

#### Rule-02: 공종 착수 전 (착수 D-3)
```
트리거: WorkSchedule.planned_start_date 입력, work_type 선택
조건: work_schedule.planned_start_date - 3days <= today
자동 생성 제안 (공종별):
  - 토공굴착: excavation_workplan, excavation_work_permit, risk_assessment, fall_protection_checklist
  - 기초파일: piling_workplan, piling_use_workplan
  - 거푸집: formwork_shoring_workplan, formwork_shoring_installation_checklist
  부대서류:
  - attendance_roster
  - work_completion_confirmation
  - improvement_completion_check
```

#### Rule-03: 매일 작업 전
```
트리거: project.status == "진행중", 매일 오전 (또는 사용자 버튼)
자동 생성 제안:
  - tbm_log (TBM 안전점검)
  - pre_work_safety_check (작업 전 안전 확인)
  - safety_management_log (안전관리 일지)
  부대서류:
  - attendance_roster
  - photo_attachment_sheet
```

**구현 범위**:
1. Rule 엔진 클래스 (rules.py)
   - TriggerType (근로자, 공종, 장비, 매일)
   - Rule class (trigger_type, condition, generated_forms)
2. 자동생성 감지 로직
   - 근로자 등록 후크
   - WorkSchedule 작성 감지
   - 일일 스케줄러 (APScheduler)
3. 문서 생성 API
   - POST /api/v1/projects/{project_id}/documents/generate
   - Request: { trigger_type, trigger_detail, manual_override? }
   - Response: { job_id, proposed_forms: [...] }

**검증 명령**:
```bash
# 근로자 등록 시 자동생성 제안
curl -X POST http://localhost:8000/api/v1/projects/PRJ001/workers \
  -d '{"name":"홍길동","entry_date":"2026-05-01"}'

# 응답: { worker_id: "W001", proposed_documents: [education_log, new_worker_safety_pledge, ...] }

# 서류 생성
curl -X POST http://localhost:8000/api/v1/projects/PRJ001/documents/generate \
  -d '{
    "trigger_type": "new_worker",
    "trigger_detail": "worker_id=W001",
    "selected_forms": ["education_log", "new_worker_safety_pledge"]
  }'

# 응답: { job_id: "JOB001", status: "completed", generated_files: [...] }
```

**PASS 기준**:
- 3가지 Rule 모두 동작
- 자동 제안 리스트 반환
- 사용자 선택 후 생성 성공

**FAIL 기준**:
- Rule 엔진 오류
- 폼 생성 실패

**예상 리스크**:
- 부대서류 자동 포함 로직 복잡
- 사용자 선택 폼 UI 설계 필요

---

### Stage 5 — 문서 패키지 생성

**목표**: 핵심서류 + 부대서류 묶음 생성 및 ZIP 패키지 제공

**선행 조건**:
- Stage 4 완료 (자동생성 Rule)
- openpyxl Excel 생성 API 확인 가능

**수정 대상 파일 후보**:
- `src/services/document_export.py` (신규)
- `src/routers/packages.py` (신규)

**금지 사항**:
- ❌ registry 수정
- ❌ builder 수정

**구현 범위**:
1. 문서 생성 (openpyxl 기반)
   - 각 form_type에 대해 build_form_excel() 호출
   - 필수 필드만 채운 빈 폼 생성 (또는 기본값 입력)
2. 부대서류 자동 포함
   - Rule별로 필요한 supplementary_type 추가
   - 예: Rule-01 → attendance_roster, ppe_receipt_confirmation
3. 폴더 구조 생성
   ```
   신축공사_2026-04-29/
   ├── Phase_0/
   │   └── 안전관리자_선임_보고서.xlsx
   ├── Phase_1/
   │   ├── 안전보건_방침및목표_게시문.xlsx
   │   └── ...
   ├── Phase_3/
   │   ├── 안전보건교육_교육일지.xlsx
   │   ├── 신규근로자_안전보건_서약서.xlsx
   │   └── ...
   ├── 부대서류/
   │   ├── 참석자_명부.xlsx
   │   ├── 사진_첨부_대지.xlsx
   │   └── ...
   └── README.txt (패키지 설명)
   ```
4. ZIP 압축 및 다운로드
   - POST /api/v1/projects/{project_id}/packages/generate
   - GET /api/v1/packages/{package_id}/download

**검증 명령**:
```bash
# 패키지 생성
curl -X POST http://localhost:8000/api/v1/projects/PRJ001/packages/generate \
  -d '{"format": "zip", "include_supplementary": true}'

# 응답: { package_id: "PKG001", download_url: "...", generated_count: 15 }

# 다운로드
curl -O http://localhost:8000/api/v1/packages/PKG001/download
```

**PASS 기준**:
- ZIP 파일 생성 성공
- 모든 xlsx 파일 정상 포함
- 폴더 구조 유지

**FAIL 기준**:
- ZIP 생성 오류
- xlsx 생성 실패

**예상 리스크**:
- 파일명 인코딩 (한글 + 특수문자)
- 임시 폴더 정리 로직 필요

---

### Stage 6 — 웹 UI 1차 (React 프론트엔드)

**목표**: 공사 관리, 공종 등록, 서류 생성 기본 화면 구현

**선행 조건**:
- Stage 2~5 완료 (API 완성)
- 기존 React 라우팅 및 컴포넌트 구조 파악

**수정 대상 파일 후보**:
- `src/components/projects/` (신규)
  - ProjectList.tsx — 공사 목록
  - ProjectDetail.tsx — 공사 상세
  - ProjectForm.tsx — 공사 등록/수정 폼
- `src/components/documents/` (신규)
  - DocumentGenerator.tsx — 자동생성 마법사
  - DocumentList.tsx — 생성된 문서 목록
  - PackageDownload.tsx — 패키지 다운로드
- `src/pages/` 
  - /projects (공사 목록)
  - /projects/:id (공사 상세)
  - /projects/:id/documents (서류 생성)

**금지 사항**:
- ❌ 기존 컴포넌트 수정
- ❌ builder 수정

**구현 범위**:
1. 공사 목록 화면
   - 사용자의 모든 공사 표시
   - 상태별 필터 (등록, 진행중, 준공)
   - [신규 공사] 버튼
2. 공사 등록 폼
   - 공사명, 위치, 발주자, 시공사, 예정 착공/준공
   - 안전관리자 선택
   - 제출 → Project 생성
3. 공사 상세 페이지
   - 기본정보 탭
   - 공종일정 탭 (공종 추가)
   - 근로자 관리 탭 (근로자 추가)
   - 장비 관리 탭 (장비 추가)
   - 서류 생성 탭
4. 오늘 할 일 (Today's Tasks)
   - Rule 기반 자동 제안 서류
   - [작성 시작] 버튼
5. 서류 생성 마법사
   - Step 1: 생성 유형 선택 (자동 제안 / 특정 선택)
   - Step 2: 서류 확인 (필수/선택 구분)
   - Step 3: 출력 형식 선택 (Excel / ZIP)
   - Step 4: 생성 & 다운로드 시작
6. 누락 서류 체크 (선택)
   - Phase별 완성도 표시
   - 미작성 서류 경고

**검증 명령**:
```bash
# 프론트엔드 빌드
npm run build

# 개발 서버 실행
npm run dev

# Playwright E2E 테스트 (선택)
npm run test:e2e
```

**PASS 기준**:
- 모든 화면 로드 성공
- API 연결 성공
- 폼 제출 후 데이터 저장 확인
- 서류 다운로드 링크 동작

**FAIL 기준**:
- API 연결 실패 (404, 500)
- 폼 제출 오류
- 레이아웃 깨짐 (모바일 제외, V1.1은 PC 중심)

**예상 리스크**:
- 상태 관리 (Zustand, Context) 구조 선택
- API 응답 캐싱 (SWR, React Query)
- 폼 검증 로직 (react-hook-form)

---

### Stage 7 — 검증

**목표**: 통합 테스트, 회귀 테스트, Smoke 테스트

**선행 조건**:
- Stage 6 완료 (UI 완성)

**검증 시나리오**:
1. **Happy Path (행복한 경로)**
   ```
   신규 공사 등록 → 공종 입력 → 근로자 등록 → 자동생성 제안 → 서류 생성 → ZIP 다운로드
   ```

2. **API 테스트** (smoke test)
   ```bash
   # 공사 생성
   POST /api/v1/projects { name: "신축A", ... } → 200, project_id

   # 공사 조회
   GET /api/v1/projects/{project_id} → 200, 정보 일치

   # 공종 등록
   POST /api/v1/projects/{project_id}/work-schedules { work_type: "토공굴착", ... } → 200

   # 자동생성 제안
   GET /api/v1/projects/{project_id}/documents/pending → 200, forms list

   # 패키지 생성
   POST /api/v1/projects/{project_id}/packages/generate → 200, zip URL

   # ZIP 다운로드
   GET /api/v1/packages/{package_id}/download → 200, binary
   ```

3. **문서 생성 Smoke 테스트** (5개 표본)
   - Rule-01 (근로자 등록) → education_log + new_worker_safety_pledge 생성
   - Rule-02 (공종 착수) → excavation_workplan 생성
   - Rule-03 (매일 작업) → tbm_log 생성
   - 부대서류 → attendance_roster, photo_attachment_sheet 생성
   - ZIP 압축 → 파일 무결성 확인

4. **기존 90+10 Builder 회귀 테스트**
   - 기존 form export API가 여전히 작동하는지 확인
   - registry 87건 모두 로드 가능한지 확인
   - supplementary 10건 모두 로드 가능한지 확인

5. **Excel 다운로드 확인**
   - ZIP 파일 내 xlsx 파일들이 정상인지 확인
   - 파일명 (한글) 인코딩 정상인지 확인
   - xlsx 파일을 Excel로 열 때 오류 없는지 수동 확인

**검증 명령**:
```bash
# 통합 테스트 (pytest)
pytest tests/integration/test_new_construction.py -v

# API 회귀 테스트
pytest tests/api/test_form_export.py -v

# UI 테스트 (Playwright)
npx playwright test --headed

# 문서 생성 smoke test
python -m scripts.test_document_generation --sample 5

# Excel 무결성 확인
python -m scripts.validate_xlsx tests/samples/*.xlsx
```

**PASS 기준**:
- 통합 테스트 성공률 100%
- API 응답 시간 < 2초
- ZIP 파일 생성 성공률 100%
- 기존 90+10 builder 회귀 테스트 0 실패

**FAIL 기준**:
- 테스트 실패율 > 5%
- 성능 저하 (응답시간 > 5초)
- ZIP 손상

**예상 리스크**:
- 동시 다중 요청에 대한 Thread safety
- 파일 시스템 권한 (S3 upload)

---

### Stage 8 — 사용자 테스트 준비

**목표**: 대표 현장에서의 실제 운영 테스트를 위한 준비

**선행 조건**:
- Stage 7 검증 완료 (모든 기능 정상)

**구현 범위**:
1. **테스트 현장 선정**
   - 신축공사 진행 중인 현장 1개 이상
   - 안전관리자 1명, 현장소장 1명 선정

2. **테스트 시나리오 작성**
   - Day 1: 공사 등록 (안전관리자)
   - Day 2: 근로자 1명 등록 → 자동생성 확인
   - Day 3: 공종 "굴착" 착수 예정일 입력 → 자동생성 확인
   - Day 4: 매일 TBM 작성 (3일 반복)
   - Day 5: 패키지 다운로드 & Excel 확인

3. **피드백 체크리스트**
   - UI/UX 사용성 (버튼 위치, 텍스트 명확성)
   - 자동생성 규칙 정확성
   - 문서 내용 (필드 채우기, 부대서류)
   - 성능 (로딩 속도, 다운로드 시간)
   - 오류 (에러 메시지, 복구 방법)

4. **수정 우선순위 기준**
   - **P0** (즉시 수정): 기능 불작동 (API 오류, 파일 손상)
   - **P1** (1주일): 사용자 혼동 (텍스트, UI 배치)
   - **P2** (2주일): 성능 개선 (응답시간 > 3초)
   - **P3** (V1.2 이후): 기능 추가 요청

5. **Go-Live 체크리스트**
   - ✓ 모든 P0 결함 해결
   - ✓ 사용자 교육 완료 (10분)
   - ✓ 데이터 백업 및 복구 프로세스 확인
   - ✓ 모니터링 대시보드 구성 (에러 로그, 사용 현황)
   - ✓ 24/7 지원 연락처 안내

---

## 4. P0 작업 (우선순위 높음)

**반드시 먼저 해야 할 것** (Stage 0~3)

| # | 작업 | Stage | 예상 기간 | 담당 |
|---|------|-------|---------|------|
| 1 | 기존 구조 파악 (Stage 0) | 0 | 2h | Backend |
| 2 | 데이터 모델 설계 (Stage 1) | 1 | 8h | Backend |
| 3 | Project/Site API (Stage 2) | 2 | 16h | Backend |
| 4 | Phase/WorkSchedule API (Stage 3) | 3 | 16h | Backend |
| 5 | 자동생성 Rule MVP (Stage 4) | 4 | 24h | Backend |
| 6 | 문서 생성 & ZIP (Stage 5) | 5 | 16h | Backend |
| 7 | 프론트엔드 UI (Stage 6) | 6 | 32h | Frontend |
| 8 | 통합 테스트 (Stage 7) | 7 | 12h | QA |

**V1.1 MVP 필수 (Stage 4 이상 포함)**

| # | 기능 | Stage | 검증 |
|---|------|-------|------|
| 1 | 공사 등록 | 2 | API 200 OK |
| 2 | 자동생성 제안 | 4 | 3 Rule 동작 |
| 3 | 서류 생성 | 5 | ZIP 다운로드 OK |
| 4 | 웹 화면 | 6 | 모든 페이지 로드 |

---

## 5. 작업량 예상

### 기간 추정 (Backend + Frontend)

| Stage | 내용 | Backend | Frontend | QA | 합계 |
|-------|------|---------|----------|-----|------|
| 0 | 현황 점검 | 2h | — | — | 2h |
| 1 | 모델 설계 | 8h | — | 2h | 10h |
| 2 | 공사 API | 16h | 8h | 4h | 28h |
| 3 | Phase API | 16h | 4h | 4h | 24h |
| 4 | Rule MVP | 24h | 8h | 6h | 38h |
| 5 | 패키지 생성 | 16h | 4h | 4h | 24h |
| 6 | UI 1차 | 8h | 32h | 8h | 48h |
| 7 | 통합 검증 | 8h | 8h | 12h | 28h |
| **합계** | | **98h** | **64h** | **40h** | **202h** |

**소요 기간 (1명 기준)**:
- 월 160시간 작업 (주 40시간 × 4주)
- Stage 0~7: 총 202시간 ≈ **1.3개월** (1명 집중 투입)

**병렬 진행 (분담)**:
- Backend (1명) + Frontend (1명) 병렬 → **3주 (Stage 0~7)**
- 추가 QA 지원 시 → **2주 (고품질)**

### 예상 일정

```
Week 1:  Stage 0~1 (현황 파악 + 모델 설계)
Week 2:  Stage 2~3 (API 기본 구현)
Week 3:  Stage 4~5 (자동생성 + 패키지)
Week 4:  Stage 6 (UI 개발, 병렬로 진행)
Week 5:  Stage 7 (테스트 + 수정)
Week 6:  Stage 8 (사용자 테스트 준비)

Go-Live: Week 7 (프로덕션 배포)
```

---

## 6. Stage 0 상세 계획 및 지시문

### 6-1. Stage 0 개요

**목표**: 기존 프로젝트 구조 파악 후 Stage 1 설계 입력 자료 수집

**예상 기간**: 2시간

**담당**: Backend 개발자 1명

**산출물**: Stage0_current_architecture.md (현황 보고서)

### 6-2. 확인 체크리스트

#### 6-2-1. 백엔드 프레임워크 확인

- [ ] FastAPI 사용 여부 (또는 Flask, Django)
- [ ] 루트 프로젝트 구조: `src/` vs `app/` vs 기타
- [ ] 라우터 구조: `routers/`, `routes/`, `api/` 위치
- [ ] 모델 구조: `models/`, `schemas/` 위치
- [ ] 기존 실행 명령: `uvicorn`, `flask run` 등

**확인 명령**:
```bash
ls -la
cat pyproject.toml | grep -i "fastapi\|flask\|django"
cat requirements.txt | grep -i "fastapi\|flask\|django"
find . -name "main.py" -o -name "app.py" | head -5
```

#### 6-2-2. 데이터베이스 및 ORM 확인

- [ ] PostgreSQL, MySQL, SQLite 중 사용 DB
- [ ] SQLAlchemy ORM 사용 여부
- [ ] 기존 마이그레이션 도구: Alembic, Flask-Migrate 등
- [ ] 기존 User, Auth 관련 테이블 확인

**확인 명령**:
```bash
cat src/config.py | grep -i "database\|sqlalchemy"
ls -la alembic/versions/ | wc -l  # 마이그레이션 수
python -c "from sqlalchemy import inspect; from app.models import User; print(inspect(User).columns.keys())" 2>/dev/null || echo "User 모델 미확인"
```

#### 6-2-3. Form Export API 확인

- [ ] 기존 form export 엔드포인트 존재 여부
- [ ] Registry 로드 방식 (Python import vs JSON load)
- [ ] Excel 생성 라이브러리: openpyxl, xlsxwriter 등

**확인 명령**:
```bash
grep -r "form_type\|export" src/ app/ | grep -i "def\|endpoint" | head -10
python -c "from engine.output.form_registry import list_form_types; print(f'Registry: {len(list_form_types())} forms')"
python -c "import openpyxl; print(f'openpyxl: {openpyxl.__version__}')"
```

#### 6-2-4. 프론트엔드 라우팅 확인

- [ ] React Router 사용 여부
- [ ] 기존 페이지 구조: `/pages/`, `/components/`, `/routes/` 위치
- [ ] 상태 관리: Redux, Zustand, Context API 등

**확인 명령**:
```bash
ls -la src/pages/ src/components/ src/
cat package.json | grep -i "react\|next\|webpack"
grep -r "useRouter\|Routes\|BrowserRouter" src/ | head -5
```

#### 6-2-5. 기존 User/Auth 시스템 확인

- [ ] User 모델 존재 여부
- [ ] JWT, Session 기반 인증
- [ ] 권한 검증 미들웨어

**확인 명령**:
```bash
python -c "from app.models import User; u = User(); print(u.__table__.columns.keys())" 2>/dev/null || echo "User 모델 확인 필요"
grep -r "jwt\|Bearer\|Session" src/ app/ | grep -i "auth\|middleware" | head -5
```

### 6-3. Stage 0 보고서 템플릿

`docs/design/stage0_current_architecture.md` 작성:

```markdown
# Stage 0 — 현황 점검 보고서

작성일: 2026-04-29
검증자: [개발자명]

## 1. 백엔드 구조

- 프레임워크: FastAPI / Flask / 기타
- 프로젝트 루트: src/ / app/ / 기타
- 라우터 위치: src/routers/ / app/routes/
- 모델 위치: src/models/ / app/models/
- 실행 명령: uvicorn main:app --reload

## 2. 데이터베이스

- DB 종류: PostgreSQL / MySQL / SQLite
- ORM: SQLAlchemy / Peewee
- 마이그레이션 도구: Alembic / Flask-Migrate
- 기존 테이블:
  - User (columns: id, email, name, ...)
  - 기타: [...]

## 3. Form Export API

- 기존 export 엔드포인트: GET /api/v1/forms/export/{form_type}
- Registry 로드 방식: from engine.output.form_registry import ...
- 로드 검증: list_form_types() → 87건 정상
- Excel 생성 라이브러리: openpyxl 1.3+

## 4. 프론트엔드 구조

- 프레임워크: React 18+
- 라우팅: React Router v6
- 상태 관리: Zustand / Context API
- 컴포넌트 위치: src/components/
- 페이지 위치: src/pages/

## 5. 인증 시스템

- 인증 방식: JWT / Session
- User 모델: ✓ 존재 (columns: id, email, name, role, created_at, ...)
- 권한 검증: @require_auth / middleware

## 6. 다음 단계 제안

Stage 1 모델 설계 시 활용:
- User.id → Project.created_by FK
- 기존 User.role → Project.creator_role (참고용)
- [...]

## 7. 제약 사항 및 주의사항

- 기존 User 테이블 수정 금지
- Registry 수정 금지
- Document_catalog.yml 수정 금지

---

검증 완료: ✓ PASS
```

### 6-4. Stage 0 실행 흐름

```
1. 프로젝트 디렉토리 구조 확인
   ├─ ls -la / tree
   └─ README.md, CLAUDE.md 읽기

2. 백엔드 실행 및 기본 API 테스트
   ├─ python -m uvicorn app.main:app --reload
   ├─ curl http://localhost:8000/docs  (Swagger UI)
   └─ curl http://localhost:8000/api/v1/health

3. Registry 로드 확인
   ├─ python -c "from engine.output.form_registry import list_form_types; ..."
   ├─ python -c "from engine.output.supplementary_registry import list_supplemental_types; ..."
   └─ 87건, 10건 확인

4. 기존 form export API 확인
   ├─ grep -r "form_type.*export" src/
   ├─ curl http://localhost:8000/api/v1/forms/export/risk_assessment
   └─ xlsx 다운로드 확인

5. 프론트엔드 구조 확인
   ├─ ls -la src/pages/ src/components/
   └─ npm run dev 실행

6. 보고서 작성 및 제출
   └─ docs/design/stage0_current_architecture.md
```

### 6-5. Stage 0 최종 체크리스트

완료 전 필수 확인:

- [ ] Registry 87 + 10 정상 로드 확인
- [ ] 기존 form export API 작동 확인
- [ ] User 모델 구조 파악
- [ ] FastAPI / Flask 실행 명령 확인
- [ ] React 라우팅 구조 파악
- [ ] 보고서 작성 완료
- [ ] **코드 수정 없음 확인** (Stage 0은 확인만)

---

## 마무리

본 백로그는 new_construction_web_generation_flow.md V1.0 설계를 기준으로,  
실제 개발 가능한 단계별 구현 계획을 정의하였습니다.

**핵심 원칙**:
- 기존 90종 + 10종 완성 자산 활용
- 신규 builder 생성 금지
- 설계 → 백로그 변환만 수행 (코드 수정 금지)
- 단계별 1개씩 실행 → 검증 → 보고 → 자동 다음 단계

**예상 일정**: 6주 (양질의 검증 포함)  
**소요 인력**: Backend 1명 + Frontend 1명 (병렬)

이 백로그를 기준으로 Stage 0부터 실제 개발 지시문을 반복하면 됩니다.

---

**백로그 생성일**: 2026-04-29  
**기준 문서**: new_construction_web_generation_flow.md v1.0  
**상태**: READY FOR DEVELOPMENT

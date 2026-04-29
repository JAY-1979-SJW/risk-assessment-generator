# V1.1 Stage 2B-2E — 서버 격리 DB Migration Dry-Run 재실행 보고서

작성일: 2026-04-29 (KST)
대상: V1.1 migrations 0013 ~ 0023 (0018 충돌 수정 후 재실행)
판정: **PASS**
선행 보고서: `docs/reports/v1_1_stage2b2e_server_isolated_dry_run.md` (FAIL)

---

## 1. 0018 충돌 수정 내역

운영 DB의 기존 `equipment` 마스터 테이블과의 이름 충돌을 해소하기 위해 V1.1 측 테이블을 `project_equipment` 로 일괄 리네이밍.

| 변경 파일 | 변경 내용 |
|---|---|
| `0018_create_equipment.sql` → `0018_create_project_equipment.sql` | 파일명 변경, 테이블명 `equipment` → `project_equipment`, 인덱스 prefix `idx_equipment_*` → `idx_project_equipment_*`, 헤더 코멘트 보강 |
| `0020_create_safety_events.sql` | 주석 내 source_type 추적 대상 표기 `equipment` → `project_equipment`, 허용값 주석도 동기화 |
| `0023_create_generated_document_files_and_indexes.sql` | 복합 인덱스 `idx_equipment_project_status` → `idx_project_equipment_project_status`, 트리거 TODO 대상 테이블 목록도 동기화 |

운영 DB 기존 `equipment` (마스터) 테이블·`document_equipment_map` FK 등은 **전혀 손대지 않음**.

## 2. 실행 환경

- 위치: 앱서버 `1.201.176.236` / `risk-assessment-db` 컨테이너
- 운영 DB: `kras` (변경 없음)
- 격리 DB: `kras_v11_dryrun_20260429` (이전 dry-run DB DROP 후 TEMPLATE 재클론)
- migration 파일 주입 경로: 컨테이너 `/tmp/v11_migrations/` (운영 앱 디렉터리 무변경)

## 3. Migration 적용 결과 (0013 ~ 0023)

| 파일 | 결과 |
|---|---|
| 0013_create_users_table | ✅ |
| 0014_add_projects_v1_1_fields | ✅ |
| 0015_create_sites | ✅ |
| 0016_create_contractors | ✅ |
| 0017_create_workers | ✅ |
| 0018_create_project_equipment | ✅ (수정 후) |
| 0019_create_work_schedules | ✅ |
| 0020_create_safety_events | ✅ |
| 0021_create_document_generation_jobs | ✅ |
| 0022_create_generated_document_packages | ✅ |
| 0023_create_generated_document_files_and_indexes | ✅ (NOTICE: idx_projects_manager_id 재선언 skip — 정상) |

전 11개 마이그레이션 `ON_ERROR_STOP=1` 로 적용, ERROR 없음.

## 4. 검증 결과

### 4.1 신규 테이블 (10/10)
`contractors, document_generation_jobs, generated_document_files, generated_document_packages, project_equipment, safety_events, sites, users, work_schedules, workers`

### 4.2 projects 확장 컬럼 (18/18) ✅

### 4.3 FK 제약 (21건) ✅
- projects → users (manager_id)
- sites/contractors/workers/project_equipment/work_schedules/safety_events/document_generation_jobs/generated_document_packages/generated_document_files → projects
- workers/project_equipment → contractors
- safety_events → sites
- safety_events/document_generation_jobs/generated_document_packages → users / safety_events
- generated_document_files → generated_document_packages / document_generation_jobs
- generated_document_packages → document_generation_jobs

### 4.4 인덱스 카운트 (테이블별)
users 2 / sites 3 / contractors 5 / workers 7 / project_equipment 7 / work_schedules 6 / safety_events 8 / document_generation_jobs 8 / generated_document_packages 8 / generated_document_files 8

### 4.5 기존 projects 호환성 ✅
- 베이스 컬럼 보존: id, title, status, created_at, updated_at
- 기존 FK 참조(project_assessments, project_company_info, project_forms, project_org_members 등) 유지

### 4.6 운영 DB 무변경 ✅
- public 테이블 수: 30 (변동 없음)
- 운영 `equipment` 컬럼: equipment_code, equipment_name, sort_order, is_active (변동 없음)
- staging DB: 미접근

## 5. 테스트 DB 처리

- `kras_v11_dryrun_20260429` 유지 (사용자 승인 없이 미삭제)
- 권장: Stage 2B-3 진행 직전 또는 다음 변경 시 `DROP DATABASE` 로 정리

## 6. Stage 2B-3 진행 가능 여부

**✅ 진행 가능.** 마이그레이션 0013~0023 격리 DB 적용·검증 통과.
이후 단계에서 API/UI 구현 시 코드의 `equipment` 참조는 V1.1 측을 `project_equipment` 로 사용해야 함에 유의.

## 7. 변경 산출물

- 변경된 마이그레이션: 0018(이름·내용), 0020(주석), 0023(인덱스명·주석)
- 신규 보고서: `docs/reports/v1_1_stage2b2e_server_isolated_dry_run_rerun.md`
- 운영 DB / staging DB / 운영 앱 디렉터리: 변경 없음

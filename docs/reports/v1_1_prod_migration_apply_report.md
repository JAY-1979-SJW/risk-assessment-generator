# V1.1 PROD-MIG-2 — 운영 DB Migration 0013~0023 적용 보고서

작성: 2026-04-29 16:00 KST
대상: 운영 DB `kras` (컨테이너 `risk-assessment-db`, 앱서버 1.201.176.236)
HEAD (로컬): 6585da0
서버 HEAD 적용 후: 6585da0 (git pull --ff-only 완료)

---

## 1. 승인 확인

| 항목 | 내용 |
|---|---|
| 승인 문구 | "PROD-MIG-2 적용 승인" |
| 승인 시각 | 2026-04-29 (KST) |
| 실행 여부 | 실행됨 |

---

## 2. 백업 재확인 결과

| 항목 | 값 |
|---|---|
| backup file | `/home/ubuntu/apps/risk-assessment-app/backups/kras_before_v1_1_20260429_1536.dump` |
| size | 15,501,392 bytes (≈ 14.78 MiB) |
| sha256 | `3f840901f8fbd665bac33d7ad2d5d18b2bbc4b0dc5d71969c8c64f964d2320b7` |
| 기대 sha256 | `3f840901f8fbd665bac33d7ad2d5d18b2bbc4b0dc5d71969c8c64f964d2320b7` |
| 일치 여부 | ✅ MATCH |
| pg_restore list | TOC 233 entries, custom/gzip, PG 16.13 |

migration 적용 전 백업 무결성 확인 완료. 서버 코드 동기화:
- git pull --ff-only 완료 (로컬 HEAD 6585da0과 일치)
- migration 파일 11개 서버 배포 확인됨

---

## 3. 적용 대상 Migration 목록

```
data/risk_db/schema/migrations/0013_create_users_table.sql
data/risk_db/schema/migrations/0014_add_projects_v1_1_fields.sql
data/risk_db/schema/migrations/0015_create_sites.sql
data/risk_db/schema/migrations/0016_create_contractors.sql
data/risk_db/schema/migrations/0017_create_workers.sql
data/risk_db/schema/migrations/0018_create_project_equipment.sql
data/risk_db/schema/migrations/0019_create_work_schedules.sql
data/risk_db/schema/migrations/0020_create_safety_events.sql
data/risk_db/schema/migrations/0021_create_document_generation_jobs.sql
data/risk_db/schema/migrations/0022_create_generated_document_packages.sql
data/risk_db/schema/migrations/0023_create_generated_document_files_and_indexes.sql
```

적용 방식: `cat <file> | docker exec -i risk-assessment-db psql -U kras -d kras -v ON_ERROR_STOP=1`

---

## 4. 파일별 적용 결과

| 파일 | 결과 | 비고 |
|---|---|---|
| 0013_create_users_table.sql | ✅ COMMIT | CREATE FUNCTION / CREATE TABLE / CREATE INDEX / CREATE TRIGGER. NOTICE: trigger 미존재 → DROP IF EXISTS 정상 처리 |
| 0014_add_projects_v1_1_fields.sql | ✅ COMMIT | ALTER TABLE × 18, DO (FK 조건부), CREATE INDEX × 4 |
| 0015_create_sites.sql | ✅ COMMIT | CREATE TABLE + CREATE INDEX × 2 |
| 0016_create_contractors.sql | ✅ COMMIT | CREATE TABLE + CREATE INDEX × 4 |
| 0017_create_workers.sql | ✅ COMMIT | CREATE TABLE + CREATE INDEX × 5 |
| 0018_create_project_equipment.sql | ✅ COMMIT | CREATE TABLE + CREATE INDEX × 5. exit code 255는 파이프 체인의 이전 실패(잘못된 IP 접속 시도) 잔여값; to_regclass 확인으로 생성 검증됨 |
| 0019_create_work_schedules.sql | ✅ COMMIT | CREATE TABLE + CREATE INDEX × 5 |
| 0020_create_safety_events.sql | ✅ COMMIT | CREATE TABLE + CREATE INDEX × 6 |
| 0021_create_document_generation_jobs.sql | ✅ COMMIT | CREATE TABLE + CREATE INDEX × 6 |
| 0022_create_generated_document_packages.sql | ✅ COMMIT | CREATE TABLE + CREATE INDEX × 6 |
| 0023_create_generated_document_files_and_indexes.sql | ✅ COMMIT | CREATE TABLE + CREATE INDEX × 13. NOTICE: idx_projects_manager_id already exists, skipping — 0014에서 선행 생성됨, 정상 |

---

## 5. 생성 테이블 확인 (적용 후 read-only)

| 테이블 | 존재 여부 |
|---|---|
| users | ✅ |
| sites | ✅ |
| contractors | ✅ |
| workers | ✅ |
| project_equipment | ✅ |
| work_schedules | ✅ |
| safety_events | ✅ |
| document_generation_jobs | ✅ |
| generated_document_packages | ✅ |
| generated_document_files | ✅ |

public 테이블 수: **30 → 40** (신규 10개 생성)

---

## 6. projects 확장 컬럼 확인

0014 적용 후 `projects` 테이블 최종 컬럼 (23개):
```
id, title, status, created_at, updated_at             ← 기존 5개 (보존)
construction_type, project_status, start_date, end_date
client_name, prime_contractor_name
site_address, site_manager_name, safety_manager_name
total_floor_count, basement_floor_count, excavation_depth_m
has_tower_crane, has_pile_driver, has_scaffold_over_31m, safety_plan_required
risk_level, manager_id                                 ← V1.1 신규 18개
```

V1.1 확장 컬럼 18개 모두 존재 확인 ✅

---

## 7. FK 제약 확인

| FK | 참조 테이블 |
|---|---|
| contractors_project_id_fkey | projects |
| document_generation_jobs_project_id_fkey | projects |
| document_generation_jobs_requested_by_user_id_fkey | users |
| document_generation_jobs_safety_event_id_fkey | safety_events |
| generated_document_files_generation_job_id_fkey | document_generation_jobs |
| generated_document_files_package_id_fkey | generated_document_packages |
| generated_document_files_project_id_fkey | projects |
| generated_document_packages_created_by_user_id_fkey | users |
| generated_document_packages_generation_job_id_fkey | document_generation_jobs |
| generated_document_packages_project_id_fkey | projects |
| generated_document_packages_safety_event_id_fkey | safety_events |
| project_equipment_contractor_id_fkey | contractors |
| project_equipment_project_id_fkey | projects |
| safety_events_created_by_user_id_fkey | users |
| safety_events_project_id_fkey | projects |
| safety_events_site_id_fkey | sites |
| sites_project_id_fkey | projects |
| work_schedules_project_id_fkey | projects |
| workers_contractor_id_fkey | contractors |
| workers_project_id_fkey | projects |

FK 20개 생성 확인 ✅

인덱스: 각 테이블 CREATE INDEX 출력 및 0023 부가 인덱스 생성 확인 ✅ (NOTICE: idx_projects_manager_id 중복 skip은 정상)

---

## 8. 기존 equipment 마스터 무변경 확인

| 항목 | 결과 |
|---|---|
| `to_regclass('public.equipment')` | `equipment` (존재, 무변경) |
| 주요 컬럼 | equipment_code, equipment_name, sort_order, is_active (기존 구조 유지) |
| V1.1 migration의 equipment 직접 수정 | 없음 (0018은 `project_equipment` 별도 테이블로 생성) |

---

## 9. 기존 projects 호환성 확인

| 항목 | 결과 |
|---|---|
| 기존 row 수 | 1건 (마이그레이션 전후 동일) |
| 기존 컬럼 보존 | id, title, status, created_at, updated_at — 모두 유지 |
| 기존 row 조회 | `[PW테스트] 동작점검_011444 / draft / 2026-04-19 16:14:47` — 정상 조회 |

---

## 10. 실패/경고 사항

- **WARN**: 0018 파이프 명령에서 exit code 255가 출력됨.
  - 원인: 동일 Bash 라인에서 잘못된 IP(1.201.176.226)로의 선행 SSH 실패가 `$?`에 잔류.
  - 0018 자체는 COMMIT 출력 + `to_regclass` 검증으로 정상 생성 확인됨.
  - migration 적용 자체에는 영향 없음.
- **NOTICE**: `trg_users_updated_at` trigger DROP IF EXISTS → 미존재로 skip. 정상.
- **NOTICE**: `idx_projects_manager_id` already exists, skipping. 0014에서 선행 생성, 0023 중복 skip 정상.

---

## 11. PROD-MIG-3 진행 가능 여부

**가능**

- migration 11개 모두 COMMIT
- 신규 테이블 10개 생성 완료
- projects 확장 컬럼 18개 확인
- FK 20개 / 인덱스 정상 생성
- equipment 마스터 무변경
- 기존 projects row 정상 조회
- 백업 보존 (sha256 일치)
- 코드/migration 파일 변경 없음

---

## 검증 체크리스트

- 코드 변경: ❌ 없음
- migration 파일 변경: ❌ 없음 (sha256 최초 기록값과 동일)
- registry/catalog/supplementary 변경: ❌ 없음
- 백업 파일 Git 포함: ❌ 미포함 (서버 로컬에만 존재)
- git diff: 본 보고서 1개만

# V1.1 Stage 2B-2E — 서버 격리 DB Migration Dry-Run 보고서

작성일: 2026-04-29 (KST)
대상: V1.1 migrations 0013 ~ 0023
판정: **FAIL (0018 충돌, Stage 2B-3 진행 불가)**

---

## 1. 실행 환경

- 실행 위치: 앱서버 `1.201.176.236` → `risk-assessment-db` 컨테이너 (PostgreSQL)
- 운영 DB: `kras` (POSTGRES_USER=kras, superuser)
- 운영 DB public 테이블 수: 30
- 격리 테스트 DB명: `kras_v11_dryrun_20260429`
- 로컬 git HEAD: `bb54c9d` (V1.1 migrations 포함)
- 앱서버 git HEAD: `3ebf657` (V1.1 미반영, dry-run을 위해 git pull 미수행)
- migration 파일은 `/tmp/v11_migrations/` 로 scp 후 `docker cp` 로 컨테이너 `/tmp/v11_migrations/` 에 주입 (운영 앱 디렉터리 무변경)

## 2. 운영 DB 무변경 확인

- 운영 DB(`kras`)에 DDL 미실행
- 운영 DB public 테이블 수 변동 없음 (30 → 30)
- 운영 `equipment` 테이블 컬럼 변동 없음: `equipment_code, equipment_name, sort_order, is_active`
- staging DB 변경 없음 (해당 환경에 접근 안 함)

## 3. 격리 DB 생성 방식

- 명령: `CREATE DATABASE kras_v11_dryrun_20260429 TEMPLATE kras;`
- 결과: **성공** (운영 DB의 활성 연결에도 불구하고 PG가 허용 — 운영 DB는 영향 없음)
- 우선순위 1번(TEMPLATE 클론) 적용으로 STOP 조건 해당 없음

## 4. Migration 적용 결과

| 파일 | 결과 |
|---|---|
| 0013_create_users_table.sql | ✅ 성공 (users 신규 생성, trigger 포함) |
| 0014_add_projects_v1_1_fields.sql | ✅ 성공 (projects ALTER 14건 + index 4건) |
| 0015_create_sites.sql | ✅ 성공 |
| 0016_create_contractors.sql | ✅ 성공 |
| 0017_create_workers.sql | ✅ 성공 |
| **0018_create_equipment.sql** | ❌ **FAIL** — `ERROR: column "project_id" does not exist` |
| 0019 ~ 0023 | ⏸ 미적용 (0018 실패로 STOP) |

### 4.1 0018 실패 원인 분석 (핵심 발견사항)

운영 DB(`kras`)에 이미 동일한 이름의 `equipment` 테이블이 **다른 스키마**로 존재한다.

| 구분 | 기존 운영 `equipment` | V1.1 0018 `equipment` |
|---|---|---|
| 용도 | 장비 마스터/룩업 테이블 | 프로젝트 장비 인스턴스 |
| PK | `equipment_code VARCHAR(50)` | `id SERIAL` |
| 주요 컬럼 | equipment_code, equipment_name, sort_order, is_active | project_id FK, contractor_id FK, equipment_name, equipment_type, entry/exit_date, operator_name, … |
| 참조 | `document_equipment_map.equipment_code` 가 FK로 사용 중 | (project_id, contractor_id 등) |

`CREATE TABLE IF NOT EXISTS equipment` 가 기존 마스터 테이블 때문에 silently skip → 이어진 `CREATE INDEX idx_equipment_project_id ON equipment(project_id)` 가 컬럼 미존재로 실패.

## 5. 검증 결과 (격리 DB 한정)

### 5.1 신규 테이블 생성

| 테이블 | 생성 여부 |
|---|---|
| users | ✅ |
| sites | ✅ |
| contractors | ✅ |
| workers | ✅ |
| equipment | ⚠️ V1.1 스키마 아님 (기존 마스터 테이블 잔존) |
| work_schedules | ❌ 미생성 |
| safety_events | ❌ 미생성 |
| document_generation_jobs | ❌ 미생성 |
| generated_document_packages | ❌ 미생성 |
| generated_document_files | ❌ 미생성 |

### 5.2 projects 확장 컬럼 (18건)

✅ 18/18 추가 확인
`construction_type, project_status, start_date, end_date, client_name, prime_contractor_name, site_address, site_manager_name, safety_manager_name, total_floor_count, basement_floor_count, excavation_depth_m, has_tower_crane, has_pile_driver, has_scaffold_over_31m, safety_plan_required, risk_level, manager_id`

### 5.3 FK 제약

- ✅ `projects.manager_id → users.id`
- ✅ `sites.project_id → projects.id`
- ✅ `contractors.project_id → projects.id`
- ✅ `workers.project_id → projects.id`
- ⏸ contractors/safety_events/document_generation_jobs/generated_document_packages 참조 FK는 미적용 마이그레이션 영향으로 검증 불가

### 5.4 인덱스

- ✅ projects: idx_projects_construction_type / project_status / risk_level / manager_id
- ✅ 0015~0017 신규 테이블의 project_id / status 계열 인덱스
- ⏸ 0018 이후 인덱스 미적용

### 5.5 기존 projects 호환성

- ✅ 기존 컬럼(id, title, status, created_at, updated_at) 유지
- ✅ SELECT 가능
- ✅ 기존 FK 참조(contractors, project_assessments, project_company_info, project_forms, project_org_members, sites, workers) 유지

### 5.6 운영 DB 무변경

- ✅ 운영 DB `kras` 의 schema/데이터 변경 없음 (모든 DDL 은 격리 DB `kras_v11_dryrun_20260429` 에서만 수행)

## 6. 실패/경고 사항

### 6.1 [BLOCKER] equipment 테이블명 충돌

운영 DB에 동명의 마스터 테이블 존재. V1.1 의 프로젝트 장비 인스턴스 테이블과 의미·스키마가 완전히 다름. 추가로 `document_equipment_map.fk_dem_equipment` 외래키가 기존 마스터 테이블을 참조 중이라 단순 DROP/RENAME 으로 해결 불가.

**권장 해결 옵션:**
1. **(권장) V1.1 신규 테이블명을 `project_equipment` 로 변경** — 0018 마이그레이션과 모든 후속 참조(0019~0023, registry/builder/API)를 일괄 수정. 운영 영향 0.
2. 기존 마스터 테이블을 `equipment_master` 로 RENAME + `document_equipment_map` FK 재배선 — 운영 영향 있음, 별도 마이그레이션 필요.
3. 기존 마스터 사용 여부를 코드 전수 조사 → 미사용 시 deprecate 후 V1.1 이름 점유.

### 6.2 [INFO] 0019~0023 미검증

0018 STOP 으로 후속 5개 마이그레이션은 격리 DB에서 검증되지 못함. 0018 해결 후 재실행 필요.

## 7. 테스트 DB 처리

- 현재 상태: `kras_v11_dryrun_20260429` 격리 DB **유지 중** (0017 까지의 적용 상태)
- 사용자 승인 없이 삭제하지 않음
- **권장 조치**: 0018 충돌 해결 후 재dry-run 시 다음 명령으로 재생성
  ```sql
  DROP DATABASE kras_v11_dryrun_20260429;
  CREATE DATABASE kras_v11_dryrun_20260429 TEMPLATE kras;
  ```

## 8. Stage 2B-3 진행 가능 여부

**❌ 진행 불가.** 다음 선결 조건 필요:
1. 0018 equipment 충돌 해결 방안 결정 및 마이그레이션 파일 수정
2. 수정된 0018~0023 격리 DB 재dry-run 통과
3. registry/builder/scripts 의 `equipment` 참조와의 일치 확인

## 9. 부수 산출물

- 보고서: `docs/reports/v1_1_stage2b2e_server_isolated_dry_run.md`
- 운영 변경: 없음
- 코드 변경: 없음
- 마이그레이션 파일 수정: 없음

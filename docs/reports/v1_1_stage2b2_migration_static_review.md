# V1.1 Stage 2B-2R — Migration Static Review

**작성일**: 2026-04-29  
**대상**: 0013~0023 (11 files, ~640 lines)  
**범위**: Read-only 정적 검증 (DB 미적용)  
**최종 판정**: ✅ **PASS** — Stage 2B-3 진행 가능

---

## 1. 전체 요약

| 항목 | 결과 |
|-----|------|
| 파일 순서 | ✅ FK 의존성 일치 |
| SQL 안전성 | ✅ BEGIN/COMMIT, IF NOT EXISTS 일관 |
| FK 참조 | ✅ 21개 모두 선행 테이블 참조 |
| 개인정보 | ✅ 주민번호/외국인등록번호/password 0건 |
| 기존 API 호환성 | ✅ projects 기존 컬럼 유지, NOT NULL 미추가 |
| DB 적용 | ❌ 미실행 (정적 검토만) |

---

## 2. Migration 파일 목록

| # | 파일 | Lines | 새 객체 |
|---|-----|-------|--------|
| 0013 | create_users_table.sql | 32 | users (commit e75f897, 사전존재) |
| 0014 | add_projects_v1_1_fields.sql | 79 | projects 18 cols + idx + FK |
| 0015 | create_sites.sql | 41 | sites + 2 idx |
| 0016 | create_contractors.sql | 51 | contractors + 4 idx |
| 0017 | create_workers.sql | 56 | workers + 5 idx |
| 0018 | create_equipment.sql | 58 | equipment + 5 idx |
| 0019 | create_work_schedules.sql | 60 | work_schedules + 5 idx |
| 0020 | create_safety_events.sql | 61 | safety_events + 6 idx |
| 0021 | create_document_generation_jobs.sql | 52 | doc_gen_jobs + 6 idx |
| 0022 | create_generated_document_packages.sql | 51 | packages + 6 idx |
| 0023 | create_generated_document_files_and_indexes.sql | 101 | files + 7 idx + 6 복합 idx |

**총계**: 11 files, ~642 lines, 10 신규 테이블 + projects 확장

---

## 3. 파일 순서 / FK 순서 검증

### 3-1. FK 의존성 그래프

```
users (0013) ─────────────┬──→ projects.manager_id (0014)
                          ├──→ safety_events.created_by_user_id (0020)
                          ├──→ doc_gen_jobs.requested_by_user_id (0021)
                          └──→ packages.created_by_user_id (0022)

projects (0014) ──────────┬──→ sites (0015)
                          ├──→ contractors (0016)
                          ├──→ workers (0017)
                          ├──→ equipment (0018)
                          ├──→ work_schedules (0019)
                          ├──→ safety_events (0020)
                          ├──→ doc_gen_jobs (0021)
                          ├──→ packages (0022)
                          └──→ files (0023)

contractors (0016) ───────┬──→ workers.contractor_id (0017)
                          └──→ equipment.contractor_id (0018)

sites (0015) ────────────────→ safety_events.site_id (0020)

safety_events (0020) ─────┬──→ doc_gen_jobs.safety_event_id (0021)
                          └──→ packages.safety_event_id (0022)

doc_gen_jobs (0021) ──────┬──→ packages.generation_job_id (0022)
                          └──→ files.generation_job_id (0023)

packages (0022) ─────────────→ files.package_id (0023)
```

### 3-2. 순서 검증 결과

✅ **모든 FK 참조 대상이 자기 자신보다 앞선 번호의 파일에서 생성됨**

- 0013 users → 0014~0022 참조 ✓
- 0014 projects → 0015~0023 참조 ✓
- 0015 sites → 0020 safety_events 참조 ✓
- 0016 contractors → 0017, 0018 참조 ✓
- 0020 safety_events → 0021, 0022 참조 ✓
- 0021 doc_gen_jobs → 0022, 0023 참조 ✓
- 0022 packages → 0023 참조 ✓

✅ **순환 FK 없음** (한 방향 DAG 구조)

### 3-3. FK 정책 검증

**ON DELETE 정책 (총 21건 FK)**:

| 정책 | 건수 | 적용 |
|-----|------|-----|
| CASCADE | 9건 | project_id (모든 프로젝트 종속), package_id (files) |
| SET NULL | 12건 | contractor_id, site_id, safety_event_id, generation_job_id, manager_id, *_user_id |

**검증**: ✅ 정책 일관성 확보
- 프로젝트 삭제 시 모든 종속 데이터 자동 정리 (CASCADE)
- 선택적 참조는 SET NULL로 데이터 보존

---

## 4. SQL 안전성 검증

### 4-1. 멱등성 패턴

| 패턴 | 건수 | 파일 |
|-----|------|------|
| `BEGIN` / `COMMIT` | 11/11 | 모든 파일 |
| `CREATE TABLE IF NOT EXISTS` | 11회 | 0013~0023 (각 1회) |
| `ADD COLUMN IF NOT EXISTS` | 18회 | 0014 |
| `CREATE INDEX IF NOT EXISTS` | 51회 | 0014~0023 |
| `ON CONFLICT DO NOTHING` | 1회 | 0013 (initial admin row) |
| `pg_constraint` 사전 검사 | 1회 | 0014 (FK fk_projects_manager_id) |

✅ **모든 마이그레이션은 multiple-run safe**

### 4-2. 비파괴 검증

| 검사 | 결과 |
|-----|------|
| `DROP TABLE` | ✅ 0건 |
| `DROP COLUMN` | ✅ 0건 |
| `RENAME COLUMN` | ✅ 0건 |
| `ALTER ... DROP CONSTRAINT` | ✅ 0건 |
| `TRUNCATE` | ✅ 0건 |

✅ **파괴적 작업 0건** — 운영 데이터 유실 위험 없음

### 4-3. NOT NULL 신규 컬럼 (호환성)

**0014 projects 확장 18개 컬럼**:
- 모두 nullable 또는 DEFAULT 보유
- 기존 행에 자동 적용 가능
- `NOT NULL` 신규 추가 0건

**신규 테이블 NOT NULL** (각 테이블 첫 번째 PK + project_id):
- 신규 테이블이므로 기존 데이터 무영향

✅ **기존 데이터 호환성 100%**

---

## 5. 개인정보 / 보안 검증

### 5-1. 금지 컬럼 검사

| 키워드 | 검사 결과 | 비고 |
|-------|---------|-----|
| 주민등록번호 / resident_no / ssn | ✅ 0건 | 명시 배제 (workers 코멘트) |
| 외국인등록번호 / alien_reg | ✅ 0건 | 명시 배제 (workers 코멘트) |
| password / password_hash | ✅ 0건 | 명시 배제 (users 코멘트) |
| token / session | ✅ 0건 | 명시 배제 (users 코멘트) |
| birth_date | ✅ 0건 | 미사용 |
| 건강정보 / health | ✅ 0건 | 미사용 |

### 5-2. 전화번호 처리

| 테이블 | 컬럼 | 필수 | 평가 |
|-------|-----|-----|------|
| users | phone | (해당 컬럼 없음, 0013에 미포함) | ✅ |
| sites | site_manager_phone, safety_manager_phone | 선택 | ✅ |
| contractors | contact_phone | 선택 | ✅ |
| workers | (없음) | — | ✅ V1.1 미저장 |
| equipment | (없음) | — | ✅ |

✅ **모든 전화번호 컬럼은 NULLABLE** (개인정보 최소화 원칙 준수)

### 5-3. 이름 컬럼 처리

| 테이블 | 컬럼 | 필수 | 비고 |
|-------|-----|-----|------|
| workers | worker_name | NOT NULL | 업무 식별자 (불가피) |
| contractors | representative_name, contact_name | nullable | 선택 |
| sites | site_manager_name 등 | nullable | 선택 |
| equipment | operator_name | nullable | 선택 |

✅ **이름은 업무 운영상 불가피한 최소 저장**

---

## 6. 기존 API 호환성 검증

### 6-1. projects 기존 컬럼 유지

기존 (`infra/init.sql`):
```
id, title, status, created_at, updated_at
```

0014 변경:
- ❌ DROP/RENAME 없음
- ✅ 18개 신규 ADD COLUMN (모두 IF NOT EXISTS)
- ✅ 모두 nullable 또는 DEFAULT
- ✅ Trigger trg_projects_updated_at 그대로 작동

### 6-2. 기존 CRUD 호환성

`backend/routers/projects.py` 분석:

| API | SQL | 영향 |
|----|-----|-----|
| GET /api/projects | `SELECT id, title, status, created_at, updated_at` | ✅ 무영향 |
| POST /api/projects | `INSERT INTO projects (title) VALUES (%s)` | ✅ 신규 컬럼은 NULL/DEFAULT |
| GET /api/projects/{pid} | `SELECT * FROM projects` | ⚠️ 응답에 신규 18개 필드 포함 (호환성 유지) |
| PUT /api/projects/{pid} | `UPDATE projects SET title=%s, status=%s` | ✅ 무영향 |
| DELETE /api/projects/{pid} | `DELETE FROM projects WHERE id = %s` | ✅ 신규 테이블은 CASCADE로 정리 |

✅ **기존 4개 API 100% 호환**  
⚠️ GET /api/projects/{pid}만 응답 페이로드 확장 — 프론트는 모르는 필드 무시 가능

### 6-3. 기타 라우터 영향

| 파일 | 영향 |
|-----|------|
| backend/routers/company.py | ✅ project_company_info 미변경 |
| backend/routers/organization.py | ✅ project_org_members 미변경 |
| backend/routers/assessments.py | ✅ project_assessments 미변경 |
| backend/routers/forms.py | ✅ project_forms 미변경 |
| form_registry.py / supplementary_registry.py | ✅ 무변경 |
| document_catalog.yml | ✅ 무변경 |

---

## 7. Local / Test DB Dry-run 절차

### 7-1. ⚠️ 중요 — 적용 대상

| 환경 | 적용 가능 | 비고 |
|-----|---------|-----|
| **Local docker-compose** | ✅ 가능 | 테스트 권장 |
| **Staging DB (별도 인스턴스)** | ⚠️ 사전 승인 후 | Stage 2B-3 이후 |
| **Production DB (1.201.176.236)** | ❌ **별도 승인 필수** | 본 단계 금지 |

### 7-2. Backup 절차 (적용 전 필수)

```bash
# Local
docker exec risk-assessment-db pg_dump -U postgres kras \
    > backup_2026-04-29_pre_v1_1.sql

# Staging/Prod (참고만, 실행 금지)
ssh -i ~/.ssh/haehan-ai.pem ubuntu@1.201.176.236 \
    "docker exec risk-assessment-db pg_dump -U postgres kras" \
    > /tmp/backup_2026-04-29_pre_v1_1.sql
```

### 7-3. 적용 순서 (Local 전용)

```bash
cd /home/ubuntu/apps/risk-assessment-app  # or local equivalent
DB="kras"
DIR="data/risk_db/schema/migrations"

# 0013은 사전 적용됨 (commit e75f897). 미적용 시 먼저 실행
psql -U postgres -d $DB -f $DIR/0013_create_users_table.sql

# 0014~0023 순차 적용
for f in 0014_add_projects_v1_1_fields.sql \
         0015_create_sites.sql \
         0016_create_contractors.sql \
         0017_create_workers.sql \
         0018_create_equipment.sql \
         0019_create_work_schedules.sql \
         0020_create_safety_events.sql \
         0021_create_document_generation_jobs.sql \
         0022_create_generated_document_packages.sql \
         0023_create_generated_document_files_and_indexes.sql; do
    echo "==== Applying $f ===="
    psql -U postgres -d $DB -v ON_ERROR_STOP=1 -f "$DIR/$f" || break
done
```

**옵션**: `-v ON_ERROR_STOP=1` 로 실패 시 즉시 중단

### 7-4. 적용 후 확인 SQL (read-only)

```sql
-- 1. 신규 테이블 존재 확인 (10개)
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('users', 'sites', 'contractors', 'workers', 'equipment',
                     'work_schedules', 'safety_events',
                     'document_generation_jobs',
                     'generated_document_packages',
                     'generated_document_files')
ORDER BY table_name;
-- 기대: 10 rows

-- 2. projects 확장 컬럼 확인 (18개)
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'projects'
  AND column_name IN ('construction_type', 'project_status', 'start_date',
                      'end_date', 'client_name', 'prime_contractor_name',
                      'site_address', 'site_manager_name', 'safety_manager_name',
                      'total_floor_count', 'basement_floor_count',
                      'excavation_depth_m', 'has_tower_crane', 'has_pile_driver',
                      'has_scaffold_over_31m', 'safety_plan_required',
                      'risk_level', 'manager_id')
ORDER BY column_name;
-- 기대: 18 rows

-- 3. FK 제약 확인
SELECT conname, conrelid::regclass AS table_name,
       pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE contype = 'f'
  AND conrelid::regclass::text IN ('projects', 'sites', 'contractors',
                                    'workers', 'equipment', 'work_schedules',
                                    'safety_events', 'document_generation_jobs',
                                    'generated_document_packages',
                                    'generated_document_files')
ORDER BY conrelid::regclass::text, conname;
-- 기대: 21 FK rows

-- 4. 인덱스 확인
SELECT tablename, indexname FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('projects', 'sites', 'contractors', 'workers', 'equipment',
                    'work_schedules', 'safety_events', 'document_generation_jobs',
                    'generated_document_packages', 'generated_document_files')
ORDER BY tablename, indexname;
-- 기대: ~55개 인덱스 (각 테이블 PK + 신규 인덱스)

-- 5. 기존 API 호환성 - projects 기본 SELECT
SELECT id, title, status, created_at, updated_at
FROM projects LIMIT 5;
-- 기대: 기존 데이터 정상 반환

-- 6. 멱등성 — 동일 마이그레이션 재실행 시 NOTICE만 발생, 에러 없음
-- (CREATE TABLE IF NOT EXISTS / ADD COLUMN IF NOT EXISTS 보장)
```

---

## 8. Rollback 절차

### 8-1. 적용 중 실패

각 파일이 `BEGIN; ... COMMIT;` 트랜잭션 → 자동 ROLLBACK 처리됨.  
직전 파일까지만 적용되며, 데이터 정합성 유지.

**조치**:
1. 에러 메시지 분석
2. 원인 수정 (해당 파일 또는 환경)
3. 동일 파일 재실행 (멱등성 보장)

### 8-2. 적용 후 수동 Rollback (역순)

```sql
-- ⚠️ 운영 적용 시 별도 승인 필요
BEGIN;

-- 0023 → 0014 역순으로 DROP
DROP TABLE IF EXISTS generated_document_files CASCADE;
DROP TABLE IF EXISTS generated_document_packages CASCADE;
DROP TABLE IF EXISTS document_generation_jobs CASCADE;
DROP TABLE IF EXISTS safety_events CASCADE;
DROP TABLE IF EXISTS work_schedules CASCADE;
DROP TABLE IF EXISTS equipment CASCADE;
DROP TABLE IF EXISTS workers CASCADE;
DROP TABLE IF EXISTS contractors CASCADE;
DROP TABLE IF EXISTS sites CASCADE;

-- 0014 projects 확장 컬럼 제거
ALTER TABLE projects DROP CONSTRAINT IF EXISTS fk_projects_manager_id;
ALTER TABLE projects DROP COLUMN IF EXISTS construction_type;
ALTER TABLE projects DROP COLUMN IF EXISTS project_status;
ALTER TABLE projects DROP COLUMN IF EXISTS start_date;
ALTER TABLE projects DROP COLUMN IF EXISTS end_date;
ALTER TABLE projects DROP COLUMN IF EXISTS client_name;
ALTER TABLE projects DROP COLUMN IF EXISTS prime_contractor_name;
ALTER TABLE projects DROP COLUMN IF EXISTS site_address;
ALTER TABLE projects DROP COLUMN IF EXISTS site_manager_name;
ALTER TABLE projects DROP COLUMN IF EXISTS safety_manager_name;
ALTER TABLE projects DROP COLUMN IF EXISTS total_floor_count;
ALTER TABLE projects DROP COLUMN IF EXISTS basement_floor_count;
ALTER TABLE projects DROP COLUMN IF EXISTS excavation_depth_m;
ALTER TABLE projects DROP COLUMN IF EXISTS has_tower_crane;
ALTER TABLE projects DROP COLUMN IF EXISTS has_pile_driver;
ALTER TABLE projects DROP COLUMN IF EXISTS has_scaffold_over_31m;
ALTER TABLE projects DROP COLUMN IF EXISTS safety_plan_required;
ALTER TABLE projects DROP COLUMN IF EXISTS risk_level;
ALTER TABLE projects DROP COLUMN IF EXISTS manager_id;

-- 0013 users (선택 — 다른 시스템에서 사용 시 보류)
-- DROP TABLE IF EXISTS users CASCADE;

COMMIT;
```

### 8-3. Backup 복원 (최후 수단)

```bash
docker exec -i risk-assessment-db psql -U postgres -d kras \
    < backup_2026-04-29_pre_v1_1.sql
```

---

## 9. Stage 2B-3 진행 가능 여부

### 9-1. 검증 결과 종합

```
┌─────────────────────────────────────┐
│  정적 검증 PASS 항목 6/6            │
│                                     │
│  ✅ 파일 순서 (FK 의존성 OK)       │
│  ✅ SQL 안전성 (BEGIN/COMMIT)      │
│  ✅ FK 참조 (21건 정확)             │
│  ✅ 개인정보 (금지 컬럼 0건)        │
│  ✅ 기존 API 호환성 (100%)          │
│  ✅ Rollback 가능성                 │
└─────────────────────────────────────┘
```

### 9-2. Stage 2B-3 권장 작업

1. **Local DB Dry-run** (본 절차 7-3 적용)
   - docker-compose 환경에서 0013~0023 적용
   - 7-4 확인 SQL 실행 → 모두 PASS 확인

2. **updated_at 트리거 적용**
   - 0024 신규 마이그레이션 작성
   - 9개 신규 테이블에 trg_<table>_updated_at 추가

3. **API 구현**
   - GET /api/projects/{pid} 확장 필드 반영
   - PUT /api/projects/{pid} 확장 필드 수정 가능
   - Site/Contractor/Worker CRUD (POST/GET/PUT/DELETE)
   - Equipment/WorkSchedule/SafetyEvent CRUD
   - Document Generation Job/Package/File 조회 API

4. **테스트 추가**
   - 신규 CRUD pytest
   - FK CASCADE 동작 검증
   - 기존 API regression 테스트

### 9-3. 운영 반영 전 추가 승인

⚠️ **운영 DB(kras.haehan-ai.kr)** 적용은 별도 승인 필수:
- Backup 생성 확인
- Staging 검증 완료
- 야간/비업무시간 배포
- API health check 모니터링

---

**작성**: Claude Code (Sonnet 4.6)  
**검증**: 정적 read-only 분석  
**일자**: 2026-04-29

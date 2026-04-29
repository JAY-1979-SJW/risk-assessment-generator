# V1.1 PROD-MIG-0 — 운영 DB Migration 적용 전 승인 게이트 보고서

작성일: 2026-04-29 (KST)
대상 HEAD: `bb66aa2` (Stage 2B-6 백엔드 E2E closure 직후)
판정: **PASS — 운영 DB migration 적용 승인 요청 단계.** 본 보고서는 read-only 점검과 적용 절차 확정만 수행하며 실제 DDL 은 별도 명시 승인 후 다음 단계에서 집행한다.

---

## 1. 전체 요약

| 항목 | 상태 |
|---|---|
| migration 정적 검증 (Stage 2B-2) | PASS (`v1_1_stage2b2_migration_static_review.md`) |
| 격리 DB dry-run (Stage 2B-2D / 2B-2E rerun) | PASS (`v1_1_stage2b2e_server_isolated_dry_run_rerun.md` — `kras_v11_dryrun_20260429`) |
| 백엔드 E2E (Stage 2B-6) | PASS (`v1_1_stage2b6_backend_e2e_closure.md` — 격리 DB 기준 3 Rule × preview→generate→run-excel→build-zip→download-zip 정상) |
| 운영 DB(`kras`) V1.1 적용 | **미적용** (public 30 테이블, `to_regclass('public.project_equipment')=NULL`, `to_regclass('public.generated_document_files')=NULL`) |
| 운영 컨테이너 restart / DDL 이력 | 없음 |
| 본 단계 코드/DB 변경 | 없음 (보고서 1건 추가만) |

본 단계는 **승인 게이트** 이며, DDL/migration/서비스 재시작은 일체 수행하지 않았다.

---

## 2. 현재 완료 상태

| 영역 | 결과 | 출처 |
|---|---|---|
| backend E2E | PASS — API 10/10, Rule 3/3 (preview→generate→run-excel→build-zip→download), jobs 3/3 completed, packages 3/3 ready, files 15/15 ready, ZIP 무결성 OK | Stage 2B-6 |
| isolated DB dry-run | PASS — 0013~0023 11개 마이그레이션 격리 DB(`kras_v11_dryrun_20260429`) 적용 후 DDL 오류 0건, 인덱스/FK 정상 생성 | Stage 2B-2D / 2B-2E (rerun) |
| static review | PASS — 모든 DDL `IF NOT EXISTS`, `DROP TABLE`/`TRUNCATE`/`ALTER … RENAME` 없음, 0013 의 `DROP TRIGGER IF EXISTS` 는 idempotent 보호 | Stage 2B-2 |
| prod DB migration | **미적용** — 본 단계 승인 후 별도 단계에서 집행 | (현 단계) |

---

## 3. 적용 대상 Migration

| 파일 | 신규 테이블 | 기존 테이블 변경 |
|---|---|---|
| `0013_create_users_table.sql` | `users` | (없음, 트리거 idempotent 재생성) |
| `0014_add_projects_v1_1_fields.sql` | (없음) | `projects` +18 컬럼 (모두 nullable / DEFAULT 안전) |
| `0015_create_sites.sql` | `sites` | — |
| `0016_create_contractors.sql` | `contractors` | — |
| `0017_create_workers.sql` | `workers` | — |
| `0018_create_project_equipment.sql` | `project_equipment` (운영 `equipment` 마스터와 충돌 회피) | — |
| `0019_create_work_schedules.sql` | `work_schedules` | — |
| `0020_create_safety_events.sql` | `safety_events` | — |
| `0021_create_document_generation_jobs.sql` | `document_generation_jobs` | — |
| `0022_create_generated_document_packages.sql` | `generated_document_packages` | — |
| `0023_create_generated_document_files_and_indexes.sql` | `generated_document_files` + cross-table 인덱스 | (조합 인덱스만 추가, 컬럼 변경 없음) |

요약:

- migrations: **11**개 (0013~0023, 누락/중복 없음)
- 신규 테이블: **10**개 (users, sites, contractors, workers, project_equipment, work_schedules, safety_events, document_generation_jobs, generated_document_packages, generated_document_files)
- projects 신규 컬럼: **18**개 (모두 NULLABLE, BOOLEAN 류는 DEFAULT FALSE, `construction_type` DEFAULT `'new_construction'`)

`projects` 18 컬럼 (참고): `construction_type, project_status, start_date, end_date, client_name, prime_contractor_name, site_address, site_manager_name, safety_manager_name, total_floor_count, basement_floor_count, excavation_depth_m, has_tower_crane, has_pile_driver, has_scaffold_over_31m, safety_plan_required, risk_level, manager_id`.

---

## 4. 운영 DB 영향 범위

| 항목 | 영향 |
|---|---|
| 기존 테이블 변경 | `projects` 만, 모두 nullable 컬럼 추가 (기존 INSERT/SELECT 동작 호환) |
| 기존 `equipment` 마스터 | **미변경** (V1.1 은 별도 `project_equipment` 사용) |
| 기존 `/api/projects` | 응답에 신규 컬럼이 노출될 수 있으나 누락 시 NULL — 기존 클라이언트 호환 |
| 기존 안전서류 builder / form_registry / supplementary_registry | 변경 없음 (V1.1 builder 수정 0건, registry 87/10 유지) |
| 기존 risk_assessment 흐름 | 변경 없음 (별도 테이블) |
| 외래키 신규 생성 | sites/contractors/workers/project_equipment/work_schedules/safety_events/document_generation_jobs/generated_document_packages/generated_document_files 의 `project_id`, FK 일부 `users.id` (created_by_user_id 등). 모두 `ON DELETE` 명시 |
| 인덱스 추가 | 각 테이블별 단일/복합 인덱스 + 0023 cross-table 인덱스 (대용량 lock 위험 없음 — 신규 빈 테이블) |
| 트리거 / 함수 | 0013 에 `users.updated_at` 트리거 (idempotent: `DROP TRIGGER IF EXISTS … ON users; CREATE TRIGGER …`) |
| 파괴적 DDL (DROP/TRUNCATE/RENAME) | 없음 |

---

## 5. 적용 전 체크리스트

| # | 항목 | 담당 / 비고 |
|---|---|---|
| 1 | 운영 DB 백업(`pg_dump kras`) 정상 완료 | DBA — 적용 직전 1시간 이내 |
| 2 | 백업 파일 별도 호스트 복제 + sha256 기록 | DBA |
| 3 | 운영 DB 활성 트랜잭션 / long-running query 모니터 | DBA |
| 4 | 적용 윈도우 (저트래픽 시간대) 합의 | 사용자 결정 |
| 5 | 운영 컨테이너 restart 미수행 합의 (DDL 만, 코드 무배포) | 사용자 결정 |
| 6 | psql `--set ON_ERROR_STOP=1` 단일 트랜잭션 적용 (가능 단위) | 적용자 |
| 7 | 적용 후 즉시 read-only sanity (`\dt`, `to_regclass`) | 적용자 |
| 8 | E2E 운영 smoke 시나리오 사전 동봉 | (Stage 2B-6 보고서 5장 재사용) |
| 9 | rollback 스크립트 (선언형) 작성·검증 | DBA — 8장 참조 |
| 10 | 비밀값/connection string 로그 미출력 | 적용자 |

---

## 6. 백업 계획

```
# 적용 직전 1회, 운영 DB 서버에서 실행 (예시 — 비밀값 미포함)
ts="$(date +%Y%m%d_%H%M%S)"
pg_dump -h localhost -U kras -d kras --format=custom \
        --no-owner --no-privileges \
        --file="/var/backups/kras_pre_v11_${ts}.dump"
sha256sum "/var/backups/kras_pre_v11_${ts}.dump" > "/var/backups/kras_pre_v11_${ts}.sha256"
ls -lh "/var/backups/kras_pre_v11_${ts}".*
```

- 형식: `pg_dump --format=custom` (선택적 복원 지원)
- 보관: 운영 DB 서버 + 별도 호스트 1부 복제, 보관 기간 30일 권고
- 검증: `pg_restore --list` 로 헤더 검증 후 적용 진행

---

## 7. 적용 절차 (집행은 별도 승인 단계)

```
# 운영 DB 서버에서 (DB 컨테이너 외부에서 psql 단일 세션)
PGOPTIONS='-c statement_timeout=600000 -c lock_timeout=10000' \
psql -h localhost -U kras -d kras -v ON_ERROR_STOP=1 -1 \
     -f data/risk_db/schema/migrations/0013_create_users_table.sql

# 위 패턴을 0014~0023 순서대로 동일하게 반복
# 각 파일은 IF NOT EXISTS 라 재실행에 안전하나, 실패 시 즉시 STOP 정책 유지
```

원칙:

1. **순서 고정**: 0013(users) → 0014(projects ALTER) → 0015~0017 → **0018(project_equipment, 마스터 `equipment` 와 분리)** → 0019~0023.
2. **단일 파일 단일 트랜잭션** (`-1` + `ON_ERROR_STOP=1`).
3. 코드 배포 / 컨테이너 restart 동반 없음 — DDL only.
4. 적용 직후 `\dt`, `to_regclass('public.project_equipment')`, `to_regclass('public.generated_document_files')` 등 read-only 검증.
5. 운영 데이터 변경 (INSERT/UPDATE/DELETE) 본 단계에서 일체 없음.

---

## 8. Rollback 전략

| 상황 | 절차 |
|---|---|
| 신규 테이블만 적용된 상태에서 중단 | `DROP TABLE IF EXISTS generated_document_files, generated_document_packages, document_generation_jobs, safety_events, work_schedules, project_equipment, workers, contractors, sites, users CASCADE;` (역순). 운영 데이터가 미존재한 신규 테이블이라 안전. |
| 0014 projects ALTER 까지 적용된 상태에서 중단 | 신규 컬럼이 모두 NULLABLE 라 기능적 영향 없음. **자동 롤백 없음** — 컬럼 제거는 별도 승인. 권장: 잠정 유지 후 차기 사이클에 정리. |
| 심각 장애 (데이터 손상 의심) | `pg_restore --clean --if-exists --no-owner -d kras /var/backups/kras_pre_v11_*.dump` — DBA 입회 하 수동 복원. **자동화 없음.** |
| 트리거 / 인덱스만 잘못된 상태 | `DROP TRIGGER`, `DROP INDEX` 핀포인트 제거 후 재적용 |

원칙: 신규 테이블 DROP 은 자동화 가능, **`projects` 컬럼 제거 / `pg_restore` 복원은 자동화 금지** (각 건별 명시 승인 필요).

---

## 9. 적용 후 운영 Smoke 계획 (예정)

Stage 2B-6 보고서 §5 와 동일 시나리오를 운영 DB 에 대해 1회 재현:

1. read-only sanity: `\dt` 39 → 49, `to_regclass` 신규 10 테이블 not null
2. project profile / 신규 listing (sites/contractors/workers/equipment/...) GET 200 확인 (빈 리스트 정상)
3. 시드 1건 (테스트용 worker 1, project_equipment 1) 생성
4. RULE_NEW_WORKER preview/generate → run-excel → build-zip → download-zip
5. ZIP 내부 xlsx openpyxl 적재 확인
6. 시드 + 생성 산출물 정리(roll-back of test data 만, 스키마 유지)

운영 smoke 시 절대 금지: 다른 프로젝트 데이터 mutation, 운영 사용자 계정 데이터 접근, 운영 컨테이너 restart.

---

## 10. 승인 요청 항목

사용자 승인이 필요한 결정 4건:

1. **운영 DB migration 적용 승인** — 0013~0023 일괄 적용 여부.
2. **백업 생성 승인** — 적용 직전 `pg_dump` 1회 실행 및 `/var/backups` 저장 여부.
3. **적용 시간대** — 저트래픽 윈도우 (예: KST 03:00~05:00) 또는 사용자 지정 시각.
4. **적용 후 운영 smoke 수행 승인** — 9장 시나리오 (테스트 시드 1건 포함) 즉시 실행 여부.

각 항목은 본 보고서에 대한 회신 또는 별도 지시로 명시 승인이 필요하다. 본 단계에서는 어떤 DDL/INSERT/UPDATE 도 수행하지 않았다.

---

## 11. 검증 (본 단계 변경 없음)

| 항목 | 결과 |
|---|---|
| 코드 변경 | 없음 ✅ |
| DB 변경 | 없음 (운영 DB / 격리 DB / staging 모두 무변경) ✅ |
| migration 적용 | 없음 ✅ |
| migration 파일 수정 | 없음 ✅ |
| `document_catalog.yml` / `form_registry.py` / `supplementary_registry.py` | 변경 없음 ✅ |
| `git diff` | 본 보고서 1건만 ✅ |
| 비밀값 / connection string | 보고서 미포함 ✅ |

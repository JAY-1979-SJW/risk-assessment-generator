# V1.1 PROD-MIG-1 — 운영 DB 백업 생성 및 Migration 적용 직전 최종 점검

작성: 2026-04-29 15:36 KST
대상: 운영 DB `kras` (컨테이너 `risk-assessment-db`, 앱서버 1.201.176.236)
HEAD: f3a38d8 (docs(product): add V1.1 production migration gate report)

---

## 1. 전체 요약

운영 DB `kras`에 V1.1 migration 0013~0023 적용 직전 단계로,
운영 DB 백업(pg_dump custom format)을 생성하고 read-only 점검을 수행하였다.

- 백업 파일 1건 생성 완료, sha256 / pg_restore --list 검증 통과
- 운영 DB 현재 상태: V1.1 신규 테이블(`project_equipment`, `generated_document_files`, `users` 등) 미존재 확인
- 운영 `equipment` 마스터 테이블 존재 확인 (V1.1 migration이 건드리지 않음)
- migration 파일 11개 모두 idempotent 확인 (CREATE/ALTER ... IF NOT EXISTS), DROP/TRUNCATE/RENAME 없음
- DDL 미실행, migration 미적용, 코드/registry 변경 없음

판정: **PASS** — PROD-MIG-2 단계(실제 migration 적용) 진행 가능.

---

## 2. 운영 DB 현재 상태

| 항목 | 값 |
|---|---|
| database | kras |
| schema | public |
| PostgreSQL 버전 | 16.13 |
| public 테이블 수 | 30 |
| `to_regclass('public.project_equipment')` | NULL (미존재) ✅ |
| `to_regclass('public.generated_document_files')` | NULL (미존재) ✅ |
| `to_regclass('public.users')` | NULL (미존재) ✅ |
| `to_regclass('public.equipment')` | equipment (존재 — 마스터, 보존 대상) |
| `to_regclass('public.projects')` | projects (존재 — 0014에서 ADD COLUMN IF NOT EXISTS로 확장 예정) |

운영 public 테이블 목록 (30):
```
assessment_engine_results, collection_runs, controls,
document_control_map, document_equipment_map, document_hazard_map,
document_law_map, document_work_type_map, documents, equipment,
expc_meta, hazards, kosha_meta, law_meta, moel_expc_meta,
normalization_runs, project_assessments, project_company_info,
project_form_attendees, project_forms, project_org_members, projects,
risk_assessment_results, risk_mapping_core, rule_sets, rules,
sentence_labels, sentence_normalization, v_classified_documents, work_types
```

---

## 3. 백업 파일 정보

| 항목 | 값 |
|---|---|
| backup file | `/home/ubuntu/apps/risk-assessment-app/backups/kras_before_v1_1_20260429_1536.dump` |
| format | PostgreSQL custom (`pg_dump -Fc`) |
| size | 15,501,392 bytes (≈ 14.78 MiB) |
| sha256 | `3f840901f8fbd665bac33d7ad2d5d18b2bbc4b0dc5d71969c8c64f964d2320b7` |
| 생성 명령 | `docker exec risk-assessment-db pg_dump -U kras -d kras -Fc > <host-path>` |
| Archive 시각 | 2026-04-29 06:36:37 UTC (= 2026-04-29 15:36 KST) |
| 호스트 위치 | 앱서버 1.201.176.236 (DB 컨테이너에는 backups 마운트 없음 → 호스트로 직접 파이프) |
| Git 포함 여부 | 미포함 (백업 파일은 서버 로컬에만 존재) |

비밀번호/credential은 명령 및 로그에서 출력되지 않았다 (DB 컨테이너 내부 peer 인증 사용).

---

## 4. 백업 검증 결과

`pg_restore --list` 헤더 정상:
```
; Archive created at 2026-04-29 06:36:37 UTC
;     dbname: kras
;     TOC Entries: 233
;     Compression: gzip
;     Format: CUSTOM
;     Dumped from database version: 16.13
;     Dumped by pg_dump version: 16.13
```
- TOC 엔트리: 233개 (테이블/시퀀스/인덱스/함수 등 정상 포함)
- 30개 public 테이블 모두 백업에 포함됨 (assessment_engine_results, equipment, projects 등 헤드 25줄에서 확인)
- 손상/truncated 징후 없음, sha256 안정적으로 산출됨

---

## 5. Migration 적용 준비 상태

대상 파일 (data/risk_db/schema/migrations/, sha256):
```
87d7e073...  0013_create_users_table.sql
d9ab79b5...  0014_add_projects_v1_1_fields.sql
cd4db76d...  0015_create_sites.sql
a2690972...  0016_create_contractors.sql
c6f20f60...  0017_create_workers.sql
40b5e655...  0018_create_project_equipment.sql       ← project_equipment 명명 (운영 equipment 충돌 회피)
fd691e20...  0019_create_work_schedules.sql
a611295a...  0020_create_safety_events.sql
449aead4...  0021_create_document_generation_jobs.sql
1de72250...  0022_create_generated_document_packages.sql
f1319f56...  0023_create_generated_document_files_and_indexes.sql
```

마지막 변경 커밋:
- `f8b2d96 fix(db): rename V1.1 equipment to project_equipment to avoid prod collision`
- `94002dc feat(product): add V1.1 database migrations`
- `e75f897 feat(db): add users table migration (0013)`

이후 변경 없음 → PROD-MIG-GATE 검증 시점과 동일.

| 점검 항목 | 결과 |
|---|---|
| 0013 users 생성 파일 존재 | ✅ |
| 0014 projects 확장 파일 존재 | ✅ |
| 0018이 `project_equipment` 사용 (equipment 아님) | ✅ |
| `CREATE TABLE IF NOT EXISTS` 사용 | ✅ (0013, 0015~0023) |
| `ALTER TABLE ADD COLUMN IF NOT EXISTS` 사용 | ✅ (0014) |
| `DROP TABLE` / `TRUNCATE` / `RENAME` / `DROP COLUMN` | ✅ 없음 (grep 0건) |
| 운영 `equipment` 마스터 테이블을 건드리는 SQL | ✅ 없음 |

---

## 6. 적용 명령 초안 (PROD-MIG-2에서 실행 — 본 단계에서는 실행 금지)

```bash
# 앱서버에서 컨테이너 내부 psql로 순서대로 적용
ssh -i ~/.ssh/haehan-ai.pem ubuntu@1.201.176.236
cd /home/ubuntu/apps/risk-assessment-app/app

for f in data/risk_db/schema/migrations/0013_create_users_table.sql \
         data/risk_db/schema/migrations/0014_add_projects_v1_1_fields.sql \
         data/risk_db/schema/migrations/0015_create_sites.sql \
         data/risk_db/schema/migrations/0016_create_contractors.sql \
         data/risk_db/schema/migrations/0017_create_workers.sql \
         data/risk_db/schema/migrations/0018_create_project_equipment.sql \
         data/risk_db/schema/migrations/0019_create_work_schedules.sql \
         data/risk_db/schema/migrations/0020_create_safety_events.sql \
         data/risk_db/schema/migrations/0021_create_document_generation_jobs.sql \
         data/risk_db/schema/migrations/0022_create_generated_document_packages.sql \
         data/risk_db/schema/migrations/0023_create_generated_document_files_and_indexes.sql ; do
  echo "=== applying $f ==="
  docker exec -i risk-assessment-db psql -U kras -d kras -v ON_ERROR_STOP=1 < "$f" || break
done
```

각 파일 적용 후 `to_regclass(...)` 로 신규 테이블 생성 여부 확인.

---

## 7. Rollback 기준

PROD-MIG-2 적용 중 실패 시 롤백 기준:

1. `psql -v ON_ERROR_STOP=1` 실패 시 즉시 중단 — 후속 파일 적용 금지
2. 회복 명령 (필요 시):
   ```bash
   docker exec -i risk-assessment-db pg_restore -U kras -d kras --clean --if-exists \
       < /home/ubuntu/apps/risk-assessment-app/backups/kras_before_v1_1_20260429_1536.dump
   ```
3. 백업 sha256 사전 검증 후에만 복원:
   `sha256sum kras_before_v1_1_20260429_1536.dump` → `3f840901f8fbd665bac33d7ad2d5d18b2bbc4b0dc5d71969c8c64f964d2320b7`
4. 모든 migration이 idempotent이므로 부분 적용 후 재시도도 안전 (단, 중단된 파일의 중간 상태 검증 필요).

---

## 8. PROD-MIG-2 진행 가능 여부

**가능 (조건부)**

조건:
- 운영 `equipment` 마스터 테이블에 영향 없음 확인됨
- 백업 파일 무결성 확보 및 sha256 기록됨
- migration 파일 변경 없음 (HEAD f3a38d8 시점과 동일 sha256)

---

## 9. 승인 필요 항목

PROD-MIG-2 단계 진행에 사용자 승인이 필요하다.

- [ ] 운영 DB `kras`에 11개 migration 순차 적용 승인
- [ ] 적용 직후 신규 테이블 7종(users, sites, contractors, workers, project_equipment, work_schedules, safety_events, document_generation_jobs, generated_document_packages, generated_document_files) 생성 검증 수행 승인
- [ ] 적용 시간대 (서비스 영향 최소 시점) 확정

---

## 검증 체크리스트

- 운영 DB DDL: ❌ 없음 (read-only SELECT만 수행)
- migration 적용: ❌ 없음
- 코드 변경: ❌ 없음
- migration / registry / catalog / supplementary 파일 변경: ❌ 없음
- 백업 파일 Git 포함: ❌ 미포함 (서버 로컬에만 존재)
- git diff: 본 보고서 1개만

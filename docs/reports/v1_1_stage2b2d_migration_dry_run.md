# V1.1 Stage 2B-2D — Local/Test DB Migration Dry-run 결과

**작성일**: 2026-04-29  
**대상**: 0013~0023 (11 files)  
**최종 판정**: ⚠️ **WARN — Dry-run 환경 없음 (STOP)**

> **요약**: 본 작업 환경(Windows local)에는 docker, docker-compose, psql 클라이언트가 모두 설치되어 있지 않으며, 사용 가능한 DB는 운영 서버(1.201.176.236) 및 DB 서버(1.201.177.67)뿐입니다. 운영/Staging DB 적용은 사양상 금지되므로 본 단계에서는 **DB 적용을 수행하지 않고 STOP**합니다. Stage 2B-3 진행은 별도 환경 준비 후 가능합니다.

---

## 1. dry-run 환경 점검

### 1-1. 사전 확인 결과

| 항목 | 결과 | 세부 |
|-----|------|------|
| `git status --short` | ✅ clean | 작업 트리 깨끗함 |
| HEAD | 9c0debf | docs(product): add V1.1 migration static review |
| 브랜치 | master | (40+ commits ahead of origin) |
| `docker --version` | ❌ not found | 로컬 Windows에 docker 미설치 |
| `docker ps` | ❌ N/A | docker daemon 없음 |
| `which psql` | ❌ not in PATH | PostgreSQL 클라이언트 미설치 |
| `docker-compose.yml` (root) | ❌ 없음 | 루트에 없음 |
| `infra/docker-compose.yml` | ⚠️ 서버용 | Linux 절대경로(`/home/ubuntu/apps/...`), 외부 볼륨 `risk-assessment-pgdata: external: true` → 운영 서버 전용 |
| `backend/.env` | ✅ 존재 | (시크릿 — 표시 안 함) |
| `.env` (root) | ✅ 존재 | (시크릿 — 표시 안 함) |

### 1-2. 가용 DB 인스턴스 매트릭스

| DB | 위치 | 본 작업 사용 가능 | 사유 |
|----|-----|---------------|-----|
| Local PostgreSQL (Windows) | — | ❌ | 미설치 (psql/docker 모두 없음) |
| Local docker-compose DB | — | ❌ | docker 미설치 + 컴포즈 파일이 서버 경로 사용 |
| **Production (kras.haehan-ai.kr / 1.201.176.236)** | 앱 서버 | ❌ | **사양상 금지** |
| **DB 서버 common_data (1.201.177.67)** | DB 서버 | ❌ | **운영 서버, 본 마이그레이션 대상 아님** |
| Staging | — | ❌ | 별도 인스턴스 없음, 사양상 금지 |
| Test container | — | ❌ | 미준비 |

### 1-3. infra/docker-compose.yml 검토

본 파일은 **서버 전용 구성**으로, 로컬에서는 실행 불가:

```yaml
# 운영 서버 절대 경로 (Linux only)
- /home/ubuntu/apps/risk-assessment-app/logs:/app/logs
- /home/ubuntu/apps/risk-assessment-app/data:/app/data
- /home/ubuntu/apps/risk-assessment-app/backups:/app/backups

# 외부 볼륨 (이미 존재해야 함)
volumes:
  risk_assessment_pgdata:
    name: risk-assessment-pgdata
    external: true   # ← 로컬에는 없음
```

→ Windows local에서 `docker compose up` 시도해도 볼륨 없음 + 경로 부재로 실패.

---

## 2. 운영 DB 미사용 확인

✅ **DDL 실행 0건**:
- `psql -f` 미실행
- `docker exec ... psql` 미실행
- 운영 `DATABASE_URL` 사용 0건
- SSH 터널 미개설
- 어떤 DB에도 연결 시도 없음

✅ **변경된 파일 0건** (보고서 1개 제외):
- `0013~0023*.sql` 무수정
- registry/catalog/supplementary 무수정
- 코드/UI 무수정

---

## 3. Migration 적용 결과

| 파일 | 적용 결과 | 비고 |
|-----|---------|-----|
| 0013_create_users_table.sql | ⏸️ **미실행** | dry-run 환경 없음 |
| 0014_add_projects_v1_1_fields.sql | ⏸️ **미실행** | 동일 |
| 0015_create_sites.sql | ⏸️ **미실행** | 동일 |
| 0016_create_contractors.sql | ⏸️ **미실행** | 동일 |
| 0017_create_workers.sql | ⏸️ **미실행** | 동일 |
| 0018_create_equipment.sql | ⏸️ **미실행** | 동일 |
| 0019_create_work_schedules.sql | ⏸️ **미실행** | 동일 |
| 0020_create_safety_events.sql | ⏸️ **미실행** | 동일 |
| 0021_create_document_generation_jobs.sql | ⏸️ **미실행** | 동일 |
| 0022_create_generated_document_packages.sql | ⏸️ **미실행** | 동일 |
| 0023_create_generated_document_files_and_indexes.sql | ⏸️ **미실행** | 동일 |

**실패 여부**: 적용 자체를 시도하지 않음 → 실패/성공 측정 불가.

---

## 4. 검증 결과 (실측 불가 항목)

| 항목 | 상태 | 사유 |
|-----|------|------|
| 신규 10개 테이블 존재 | ⏸️ 미확인 | DB 적용 없음 |
| projects 18개 신규 컬럼 | ⏸️ 미확인 | DB 적용 없음 |
| FK 21건 | ⏸️ 미확인 | DB 적용 없음 |
| 인덱스 ~55개 | ⏸️ 미확인 | DB 적용 없음 |
| 기존 projects CRUD 호환성 | ⏸️ 미확인 | DB 적용 없음 |
| 운영 DB 변경 | ✅ 0건 | 적용 시도 없음 |
| Staging DB 변경 | ✅ 0건 | 적용 시도 없음 |
| 코드 변경 | ✅ 0건 | 보고서 1개만 |

> 정적 검증은 직전 단계(Stage 2B-2R, `v1_1_stage2b2_migration_static_review.md`)에서 PASS 판정 완료. 본 단계는 **실 DB 검증** 단계였으나 환경 부재로 SKIP.

---

## 5. Stage 2B-3 진행 가능 여부

### 5-1. 옵션

#### Option A — 환경 준비 후 dry-run 재시도 (권장)

**필요 사항** (택일):
1. **로컬 PostgreSQL 설치** (Windows)
   - PostgreSQL 16 installer → psql 클라이언트 포함
   - 별도 테스트 DB 생성: `kras_test`
   - `infra/init.sql` 적용 후 0013~0023 순차 적용

2. **Docker Desktop 설치** (Windows)
   - 별도 `docker-compose.local.yml` 작성 (외부 볼륨/서버 경로 제거)
   - 로컬 컨테이너로 격리 검증

3. **앱 서버에 격리 테스트 DB 추가**
   - 운영 컨테이너와 분리된 별도 PostgreSQL 컨테이너
   - `docker exec`로만 접근, 운영 DB 미접촉
   - 사용자의 명시적 승인 필요

**예상 소요**: 30~60분 (환경 설치) + 10분 (dry-run 실행)

#### Option B — 환경 준비 보류, Stage 2B-3 정적 진행

- 정적 검증(2B-2R) 결과만으로 API 구현 진행
- 실 DB 검증은 사용자가 서버 측에서 직접 실행 후 결과 회신
- **위험**: 환경/DB 차이로 인한 미발견 이슈 가능

#### Option C — 사용자가 운영 서버 dry-run 직접 실행

사용자가 SSH로 앱 서버 접속 후 별도 테스트 DB(`CREATE DATABASE kras_test`)에서 직접 적용. 본 에이전트는 운영 권한이 없으므로 이 옵션이 가장 안전.

```bash
# 사용자 직접 실행 (참고용 명령)
ssh -i ~/.ssh/haehan-ai.pem ubuntu@1.201.176.236

# 컨테이너에 들어가서 별도 테스트 DB 생성
docker exec -it risk-assessment-db psql -U postgres -c "CREATE DATABASE kras_test TEMPLATE kras"

# 별도 테스트 DB에 마이그레이션 적용
for f in 0013_create_users_table.sql \
         0014_add_projects_v1_1_fields.sql \
         ... \
         0023_create_generated_document_files_and_indexes.sql; do
    docker exec -i risk-assessment-db \
        psql -U postgres -d kras_test -v ON_ERROR_STOP=1 \
        < /home/ubuntu/apps/risk-assessment-app/data/risk_db/schema/migrations/$f
done

# 정리
docker exec -it risk-assessment-db psql -U postgres -c "DROP DATABASE kras_test"
```

### 5-2. 권장

```
권장: Option C (사용자 직접 server-side 격리 dry-run)
이유: 
  • 본 에이전트는 운영 서버 DDL 권한이 없음
  • 로컬 Windows 환경 부재
  • 별도 환경 구축은 30~60분 추가 소요
  • Option C는 운영 DB 무영향 (별도 test DB 사용)
대안: Option B (Stage 2B-3 정적 진행) 가능, 단 Stage 2B-3 종료 직전에 dry-run 실행 필요
```

---

## 6. 실패/경고 사항

| 분류 | 내용 |
|-----|-----|
| **WARN** | 로컬 dry-run 환경 부재로 실 DB 검증 불가 |
| **WARN** | infra/docker-compose.yml은 서버 전용으로 로컬 사용 불가 |
| **NOTE** | 정적 검증(2B-2R)은 이미 PASS 완료 |
| **NOTE** | Backup 명령(`pg_dump`)도 실행 환경 부재로 미수행 — 실 적용 시점에 별도 수행 필요 |

---

## 7. Rollback 절차 (참고용 — 미실행)

본 단계에서 적용된 마이그레이션이 없으므로 rollback도 불필요.  
실제 적용 후 rollback이 필요한 경우 절차는 `v1_1_stage2b2_migration_static_review.md` §8 참고.

---

## 8. 최종 판정

```
┌──────────────────────────────────────────────────┐
│  Stage 2B-2D: ⚠️  WARN — 환경 없음 STOP          │
│                                                  │
│  ✅ 운영 DB 미접촉 (사양 준수)                   │
│  ✅ Staging DB 미접촉 (사양 준수)                │
│  ✅ 코드/migration/registry 무변경               │
│  ⏸️  Local dry-run 미수행 (환경 부재)            │
│                                                  │
│  📌 Stage 2B-3 진행:                             │
│    옵션 C 권장 — 사용자 server-side 격리 dry-run │
│    또는 옵션 B — 정적 결과만으로 API 구현 진행   │
└──────────────────────────────────────────────────┘
```

---

**작성**: Claude Code (Sonnet 4.6)  
**검증**: 환경 사전 점검 (read-only)  
**일자**: 2026-04-29

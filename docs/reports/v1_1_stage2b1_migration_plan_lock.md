# V1.1 Stage 2B-1 — Migration Plan Lock

**작성일**: 2026-04-29  
**목적**: Stage 2B migration 실제 작성 전, users 테이블 필요성 판단 및 migration 순서 확정  
**범위**: Read-only 평가 (DB/코드/migration 생성 금지)  
**최종 판정**: ✅ PASS → Stage 2B-2 실제 migration 작성 진행 가능

---

## 목차

1. [users 테이블 현황](#1-users-테이블-현황)
2. [users 선행 필요성 판단](#2-users-선행-필요성-판단)
3. [V1.1 FK 전략](#3-v11-fk-전략)
4. [Migration 파일 순서 확정](#4-migration-파일-순서-확정)
5. [ID 전략 (SERIAL vs UUID)](#5-id-전략-serial-vs-uuid)
6. [Rollback 전략](#6-rollback-전략)
7. [Stage 2B-2 지시 기준](#7-stage-2b-2-지시-기준)

---

## 1. users 테이블 현황

### 1-1. 현재 상태

**결과**: ❌ 없음

| 항목 | 상태 | 확인 |
|-----|------|------|
| **users 테이블** | ❌ 미존재 | infra/init.sql, migrations/ 모두 미포함 |
| **user/auth 라우터** | ❌ 미존재 | backend/routers/ 에 user/auth 파일 없음 |
| **users FK 참조** | ❌ 미존재 | backend/routers/projects.py에서 user_id 참조 없음 |
| **manager 필드** | ✅ 있음 (VARCHAR) | project_assessments.manager = VARCHAR(100) |
| **created_by/updated_by** | ✅ 설계 (VARCHAR) | Stage 1 설계에서 VARCHAR(50)로 정의 |
| **sp_workers** | ✅ draft (다른 용도) | safety_platform_core_schema.sql에만 있음 (프로젝트 근로자용) |

### 1-2. Stage 1 설계에서 기대하는 users FK

**projects 테이블**:
```
safety_manager_id VARCHAR(50) → FK to users(id) (nullable)
created_by VARCHAR(50) → FK to users(id)? (명시되지 않음)
updated_by VARCHAR(50) → FK to users(id)? (명시되지 않음)
```

**sites 테이블**:
```
site_manager_id VARCHAR(50) → FK to users(id) (nullable)
safety_manager_id VARCHAR(50) → FK to users(id) (nullable)
```

**contractors 테이블**:
```
supervisor_id VARCHAR(50) → FK to users(id) (nullable)
safety_contact_id VARCHAR(50) → FK to users(id) (nullable)
```

**workers 테이블**:
```
supervisor_id VARCHAR(50) → FK to users(id) (nullable)
```

**equipment 테이블**:
```
operator_id VARCHAR(50) → FK to workers(id) (nullable)
```

### 1-3. 기존 프로젝트와의 연결

**현황**:
- projects API는 user 인증 미필수
- project_company_info.ceo_name, project_org_members.name 등은 사람 이름만 저장
- 사용자 세션/권한 관리 시스템 미존재

**결론**: users 테이블 필수 생성 (Stage 2B-2)

---

## 2. users 선행 필요성 판단

### 2-1. Option A: users 테이블 선행 생성 (권장) ✅

**필요한 필드** (최소):
```sql
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,           
    user_name VARCHAR(255) NOT NULL,           
    role VARCHAR(50),                          
    email VARCHAR(100),                        
    phone VARCHAR(20),                         
    status VARCHAR(20) DEFAULT 'active',       
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**장점**:
- ✅ Stage 1 설계의 FK 즉시 사용 가능
- ✅ 참조 무결성 강제 가능
- ✅ 사용자 조회/관리 API 확장 용이

**권장**: ✅ **선행 생성** (Stage 2B-2 맨 앞에)

### 2-2. Option B: users FK 없이 VARCHAR(50) nullable (비권장) ❌

**단점**:
- ❌ 참조 무결성 미보장
- ❌ 데이터 정합성 문제
- ❌ 향후 FK 추가 시 마이그레이션 복잡

**권장**: ❌ **비권장**

### 2-3. 최종 결정

```
✅ Option A 선택: users 테이블 선행 생성
시점: Stage 2B-2, migration 0013
```

---

## 3. V1.1 FK 전략

### 3-1. FK 정책 결정

#### Policy 1: 모든 manager_id FK 강제 (권장)

- ✅ 모든 manager_id가 FK로 강제
- ✅ nullable인 경우 ON DELETE SET NULL
- ✅ created_by (필수)는 ON DELETE RESTRICT

**특징**:
- 참조 무결성 완벽 보장
- DB 차원의 데이터 검증

### 3-2. 최종 결정

```
✅ Policy 1: 모든 manager_id FK 강제
+ created_by ON DELETE RESTRICT
+ nullable manager_id: ON DELETE SET NULL
단, users 초기 데이터 필수로드
```

---

## 4. Migration 파일 순서 확정

### 4-1. 확정된 순서 (11개 파일)

```
0013_create_users_minimal.sql          (users 테이블)
0014_add_projects_v1_1_fields.sql      (projects 확장 + FK)
0015_create_sites.sql                  (sites 테이블)
0016_create_contractors.sql            (contractors 테이블)
0017_create_workers.sql                (workers 테이블)
0018_create_equipment.sql              (equipment 테이블)
0019_create_work_schedules.sql         (work_schedules 테이블)
0020_create_safety_events.sql          (safety_events 테이블)
0021_create_document_generation_jobs.sql (document job 테이블)
0022_create_generated_document_packages.sql (document package 테이블)
0023_create_generated_document_files.sql (document files 테이블)
```

### 4-2. 실행 순서 의존성

```
0013 (users) → 0014 (projects FK to users)
0014 (projects) → 0015-0023 (all tables FK to projects)
0016 (contractors) → 0017 (workers FK to contractors)
0017 (workers) → 0018 (equipment FK to workers)
0018 (equipment) → 0020 (safety_events FK to equipment)
0019 (work_schedules) → 0020 (safety_events FK to schedules)
0021 (doc jobs) → 0022 (doc packages FK to jobs)
0022 (doc packages) → 0023 (doc files FK to packages)
```

### 4-3. 각 마이그레이션 기본 구조

```sql
-- File: 0013_create_users_minimal.sql
-- Purpose: Create minimal users table for V1.1 FK targets
-- Idempotent: YES

BEGIN;

CREATE TABLE IF NOT EXISTS users (
    user_id         VARCHAR(50) PRIMARY KEY,
    user_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(50),
    email           VARCHAR(100),
    phone           VARCHAR(20),
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

INSERT INTO users (user_id, user_name, role, status) VALUES
    ('admin', '시스템관리자', 'admin', 'active'),
    ('sample_manager', '샘플안전관리자', 'safety_manager', 'active')
ON CONFLICT (user_id) DO NOTHING;

COMMIT;
```

---

## 5. ID 전략 (SERIAL vs UUID)

### 5-1. 결정

| 항목 | 결정 | 이유 |
|-----|------|------|
| **users** | VARCHAR(50) PK | 자연 PK (user_id) |
| **projects** | SERIAL (기존) | 호환성 유지 |
| **sites** | SERIAL | 일관성 (UUID 미사용) |
| **contractors** | SERIAL | 일관성 |
| **workers** | SERIAL | 일관성 |
| **equipment** | SERIAL | 일관성 |
| **기타** | SERIAL/BIGSERIAL | 일관성 |

### 5-2. 최종 결정

```
✅ SERIAL/BIGSERIAL 통일 (UUID 미사용)

이유:
• 기존 프로젝트 관례와 일치
• 성능 최적화 (순차적 인덱싱)
• 분산 시스템은 V3.0 이후 고려
```

---

## 6. Rollback 전략

### 6-1. 배포 중 실패

- Transaction 내에서 자동 ROLLBACK
- 모든 변경 원위치
- 파일 다시 실행

### 6-2. 배포 후 문제

**부분 Rollback** (권장):
```sql
-- 역순 DROP (CASCADE 주의)
DROP TABLE IF EXISTS generated_document_files CASCADE;
DROP TABLE IF EXISTS generated_document_packages CASCADE;
DROP TABLE IF EXISTS document_generation_jobs CASCADE;
...
```

### 6-3. 배포 전 필수 절차

1. ✅ Local 테스트 (docker-compose)
2. ✅ Backup 생성 (pg_dump)
3. ✅ Staging 배포 및 검증
4. ✅ Production 배포 (야간/주말)

---

## 7. Stage 2B-2 지시 기준

### 7-1. 구현 직전 체크리스트

- [ ] users 테이블 설계 확정
- [ ] FK 제약 확정 (Policy 1)
- [ ] Migration 파일 템플릿 준비
- [ ] Stage 1 설계와의 매핑 확인
- [ ] 기존 API 호환성 확인

### 7-2. 구현 지시사항

**작성할 파일**:
- 0013: users 테이블 (50~100 lines)
- 0014: projects 확장 (80~120 lines)
- 0015-0023: 나머지 테이블 (각 40~80 lines)

**총 규모**: 11개 파일, 약 700~900 lines

### 7-3. 후속 단계

- Stage 2B-3: API 구현
- Stage 2B-4: 테스트
- Stage 2B-5: 배포

---

## 최종 판정

```
✅ PASS — Stage 2B-2 구현 준비 완료

✅ 확정 사항:
  • users 테이블 선행 필수 (0013)
  • FK Policy 1: 모든 manager_id FK 강제
  • ID 전략: SERIAL 통일 (UUID 미사용)
  • Migration 파일: 11개 (0013~0023)
  • Rollback: Transaction + Backup

⚠️ 주의 사항:
  • users 초기 데이터 필수 (최소 admin user)
  • FK 제약 ON DELETE 옵션 신중히 선택
  • 기존 API 호환성 유지 필수
  • Backup 생성 후 배포 진행

👉 추천: Stage 2B-2 즉시 migration 파일 작성 진행
```

---

**작성**: Claude Code (Sonnet 4.6)  
**검증**: Read-only 확인  
**일자**: 2026-04-29


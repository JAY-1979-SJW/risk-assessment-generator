# V1.1 File Storage Persistence Plan

**일시**: 2026-04-29 (KST)  
**작업**: FILE-STORAGE-1 — 생성 문서 영속 저장 경로 설계 및 적용 전 점검  
**검증자**: Claude Sonnet 4.6 (자동)

---

## 1. 현재 문제 요약

V1.1 run-excel / build-zip 으로 생성된 xlsx·zip 파일이 컨테이너 내 `/tmp` 에 저장된다.  
`/tmp` 는 컨테이너 재기동 시 초기화(ephemeral)되므로, 재기동 후 기존 package 의 `download-zip` 호출이 실패한다.

| 증상 | 상세 |
|------|------|
| 재기동 후 download-zip | `{"detail":"ZIP file is missing on disk"}` |
| 재기동 후 build-zip | `{"detail":{"message":"Some files are missing on disk","missing":[...]}}` |
| 회피책 | run-excel → build-zip 재실행 (번거롭고 job 재실행 제약 있음) |

---

## 2. 현재 저장 경로

### 2.1 기본값 (환경변수 미설정 시)

| 파일 | 경로 | 기본값 |
|------|------|--------|
| `new_construction_excel_runner.py` | `_DEFAULT_BASE_DIR` | `/tmp/risk_assessment_generated_documents` |
| `new_construction_zip_builder.py` | `_DEFAULT_BASE_DIR` | `/tmp/risk_assessment_generated_documents` |
| `new_construction_downloads.py` | `_DEFAULT_BASE_DIR` | `/tmp/risk_assessment_generated_documents` |

세 파일 모두 동일 패턴:
```python
raw = os.getenv("GENERATED_DOCUMENTS_DIR") or _DEFAULT_BASE_DIR
```

→ `GENERATED_DOCUMENTS_DIR` 환경변수만 주입하면 경로 전환 가능. **코드 수정 불필요.**

### 2.2 현재 운영 컨테이너 상태

```
GENERATED_DOCUMENTS_DIR = (미설정)
실제 저장 경로: /tmp/risk_assessment_generated_documents
```

---

## 3. 생성 파일 현황

운영 smoke 생성 파일 (현재 컨테이너 /tmp 내):

```
/tmp/risk_assessment_generated_documents/
└── project_4/
    └── package_4/
        ├── 16_TBM_일지.xlsx           (smoke 테스트 파일)
        ├── 17_작업_전_안전_확인서.xlsx (smoke 테스트 파일)
        ├── 18_출근부.xlsx              (smoke 테스트 파일)
        ├── 19_사진_첨부_시트.xlsx      (smoke 테스트 파일)
        └── package_4.zip               (smoke 테스트 파일)
```

**판단**: 위 파일은 모두 smoke 테스트 목적으로 생성된 파일(project_id=4, V1_1_SMOKE_20260429).  
운영 실사용 데이터 아님. 별도 정리 지시에서 처리 예정.

---

## 4. 영속 저장 경로 후보 비교

### 후보 A: `/home/ubuntu/apps/risk-assessment-app/generated_documents`

| 항목 | 평가 |
|------|------|
| git 추적 대상 | ✅ 아님 (앱 repo 외부, `risk-assessment-app/app/` 밖) |
| 소유자 | ubuntu:ubuntu (직접 생성 시) |
| 컨테이너 쓰기 | ✅ root(uid=0) 실행이므로 어떤 소유자든 쓰기 가능 |
| 백업 대상 | ✅ `backups/` 와 동일 레벨 → 기존 백업 스크립트 확장 가능 |
| 기존 구조와 일관성 | ✅ `logs/`, `backups/`, `data/` 와 동일 레벨 |
| compose 볼륨 마운트 | ✅ `../` 상대경로 없이 절대경로 사용 (기존 `logs`, `backups` 방식 동일) |
| 용량 관리 | ✅ 독립 디렉토리 → du/rm 으로 명확히 관리 |
| 디스크 여유 | ✅ 127 GB 여유 (35% 사용) |

### 후보 B: `/home/ubuntu/apps/risk-assessment-app/data/generated_documents`

| 항목 | 평가 |
|------|------|
| git 추적 대상 | ✅ 아님 |
| 소유자 | ⚠️ `data/` 하위 일부 디렉토리가 root 소유 (evidence, masters, raw, risk_db) |
| 컨테이너 쓰기 | ✅ root 실행이므로 가능 |
| 백업 포함 여부 | ⚠️ data/ 는 KOSHA 수집 데이터 등 혼재 — 생성 문서와 구분 어려움 |
| 기존 compose volume | ⚠️ `data/` 전체가 이미 마운트됨 — 별도 마운트 필요 없으나 경계 불명확 |
| 용량 관리 | ⚠️ data/ 내 혼재로 분리 어려움 |

**추천: 후보 A** — `/home/ubuntu/apps/risk-assessment-app/generated_documents`

---

## 5. 추천 경로

| 항목 | 값 |
|------|-----|
| 호스트 경로 | `/home/ubuntu/apps/risk-assessment-app/generated_documents` |
| 컨테이너 경로 | `/app/generated_documents` |
| 환경변수 | `GENERATED_DOCUMENTS_DIR=/app/generated_documents` |
| 볼륨 마운트 (compose) | `/home/ubuntu/apps/risk-assessment-app/generated_documents:/app/generated_documents` |

### 파일 구조 (생성 후 예상)

```
/home/ubuntu/apps/risk-assessment-app/generated_documents/
└── project_{id}/
    └── package_{id}/
        ├── {n}_{form_name}.xlsx
        └── package_{id}.zip
```

컨테이너 내에서는 동일 구조가 `/app/generated_documents/` 에 생성됨.

---

## 6. docker-compose 변경 예정 내용

`infra/docker-compose.yml` 의 `api:` 서비스에 아래 2개 항목을 추가한다.

### 6.1 environment 추가

```yaml
environment:
  # ... 기존 항목 유지 ...
  GENERATED_DOCUMENTS_DIR: /app/generated_documents   # ← 신규 추가
```

### 6.2 volumes 추가

```yaml
volumes:
  # ... 기존 항목 유지 ...
  - /home/ubuntu/apps/risk-assessment-app/generated_documents:/app/generated_documents  # ← 신규 추가
```

### 6.3 변경 후 api service 전체 (참고용)

```yaml
api:
  build:
    context: ../backend
    dockerfile: Dockerfile
  container_name: risk-assessment-api
  restart: unless-stopped
  environment:
    POSTGRES_DB: ${POSTGRES_DB}
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@risk-assessment-db:5432/${POSTGRES_DB}
    COMMON_DATA_URL: ${COMMON_DATA_URL}
    OPENAI_API_KEY: ${OPENAI_API_KEY}
    OPENAI_MODEL: ${OPENAI_MODEL:-gpt-4o-mini}
    DEVLOG_DIR: /app/docs/devlog
    CHANGE_HISTORY_PATH: /app/logs/change_history.jsonl
    INTERNAL_API_KEY: ${INTERNAL_API_KEY}
    CORS_ORIGINS: ${CORS_ORIGINS:-https://kras.haehan-ai.kr}
    KOSHA_ID: ${KOSHA_ID:-}
    KOSHA_PW: ${KOSHA_PW:-}
    GENERATED_DOCUMENTS_DIR: /app/generated_documents    # ← 신규
  volumes:
    - ../docs:/app/docs:ro
    - ../app:/app/app:ro
    - ../engine:/app/engine:ro
    - ../scripts:/app/scripts:ro
    - /home/ubuntu/apps/risk-assessment-app/logs:/app/logs
    - /home/ubuntu/apps/risk-assessment-app/data:/app/data
    - ../data/risk_db/mapping:/app/data/risk_db/mapping:ro
    - ../data/risk_db/api_schema:/app/data/risk_db/api_schema:ro
    - ../data/risk_db/rules:/app/data/risk_db/rules:ro
    - /home/ubuntu/apps/risk-assessment-app/backups:/app/backups
    - ../scraper/logs:/app/scraper_logs:ro
    - ../data/masters:/app/data/masters:ro
    - ../data/evidence:/app/data/evidence:ro
    - /home/ubuntu/apps/risk-assessment-app/generated_documents:/app/generated_documents  # ← 신규
```

---

## 7. 권한 / 소유자 계획

| 항목 | 값 |
|------|-----|
| 호스트 디렉토리 생성 | `mkdir -p /home/ubuntu/apps/risk-assessment-app/generated_documents` |
| 소유자 | ubuntu:ubuntu (생성 시 자동) |
| 권한 | 755 (기존 `logs/`, `backups/` 와 동일) |
| 컨테이너 실행 uid | root(0) — 어떤 소유자든 쓰기 가능, 별도 chown 불필요 |
| 생성 파일 소유자 | root (컨테이너 내 생성) — 호스트에서 `ls -la` 시 root 표시됨 |

> **참고**: 기존 `logs/` 마운트에서도 root 소유 파일이 혼재(`ai_generate.jsonl` 등)하며 정상 동작 중. 동일 패턴.

---

## 8. 적용 절차

### 전제 조건
- 로컬에서 compose 파일 수정 후 git push
- 서버에서 git pull --ff-only

### 단계별 절차

**Step 1 — 호스트 경로 생성 (서버)**
```bash
mkdir -p /home/ubuntu/apps/risk-assessment-app/generated_documents
ls -la /home/ubuntu/apps/risk-assessment-app/generated_documents
```

**Step 2 — compose 파일 수정 (로컬)**
- `infra/docker-compose.yml` 의 api service 에 environment + volumes 추가 (§6 참조)
- 커밋 & git push

**Step 3 — 서버 git pull**
```bash
cd /home/ubuntu/apps/risk-assessment-app/app
git pull --ff-only origin master
```

**Step 4 — API 컨테이너 재기동 (api만)**
```bash
docker compose -f infra/docker-compose.yml up -d api
```

**Step 5 — 환경변수 주입 확인**
```bash
docker exec risk-assessment-api env | grep GENERATED_DOCUMENTS_DIR
# 예상: GENERATED_DOCUMENTS_DIR=/app/generated_documents
```

---

## 9. 검증 절차

### 9.1 환경변수 확인

```bash
docker exec risk-assessment-api env | grep GENERATED_DOCUMENTS_DIR
# → GENERATED_DOCUMENTS_DIR=/app/generated_documents
```

### 9.2 run-excel 생성 파일 경로 확인

```bash
# 신규 package generate 후 run-excel
curl -X POST http://localhost:8100/api/v1/new-construction/projects/4/rules/RULE_DAILY_TBM/generate \
  -H 'Content-Type: application/json' -d '{"target_date": "2026-04-30"}'
# → job_id 확인

curl -X POST http://localhost:8100/api/v1/new-construction/document-jobs/{job_id}/run-excel
# → file_path 가 /app/generated_documents/... 인지 확인

# 호스트에서 파일 존재 확인
ls -la /home/ubuntu/apps/risk-assessment-app/generated_documents/project_4/
```

### 9.3 재기동 후 파일 유지 확인

```bash
# 컨테이너 재기동
docker compose -f infra/docker-compose.yml up -d api

# 재기동 후 파일 확인
ls -la /home/ubuntu/apps/risk-assessment-app/generated_documents/project_4/
# → 파일 유지됨 (호스트 경로이므로)

# download-zip 재호출
curl -s -I http://localhost:8100/api/v1/new-construction/document-packages/{package_id}/download-zip
# → Content-Type: application/zip (파일 소실 없음)
```

### 9.4 기존 /tmp 파일 접근 여부 확인

```bash
docker exec risk-assessment-api ls /tmp/risk_assessment_generated_documents 2>/dev/null || echo 'expected: 없음'
# → 재기동 후 /tmp 는 비어있음 (정상)
```

---

## 10. Rollback 절차

환경변수 하나와 볼륨 마운트 한 줄이 변경 전부이므로 rollback 은 단순하다.

```yaml
# compose 에서 아래 2줄 제거
GENERATED_DOCUMENTS_DIR: /app/generated_documents
- /home/ubuntu/apps/risk-assessment-app/generated_documents:/app/generated_documents
```

```bash
git revert <commit>  # compose 변경 커밋 revert
git push origin master
# 서버: git pull --ff-only && docker compose -f infra/docker-compose.yml up -d api
```

Rollback 후 동작:
- 환경변수 미설정 → 다시 `/tmp` 기본값으로 복귀
- 호스트 경로(`generated_documents/`)에 남은 파일은 영향 없음 (컨테이너 미마운트 상태)
- 호스트 경로 디렉토리는 수동 삭제 가능 (DB row 는 file_path 가 남아 있으나 서빙 불가 상태)

---

## 11. 다음 Stage 지시 기준

| 조건 | 판단 |
|------|------|
| Step 5 환경변수 확인 OK | 계속 진행 |
| Step 5 환경변수 미적용 | STOP — compose 수정 확인 |
| run-excel file_path 가 `/tmp` 로 시작 | STOP — 환경변수 미적용, compose 재확인 |
| run-excel file_path 가 `/app/generated_documents` 로 시작 | PASS |
| 재기동 후 download-zip 200 & application/zip | PASS |
| 재기동 후 download-zip 404 / "missing on disk" | FAIL — rollback 후 원인 분석 |

---

## 검증 요약

| 항목 | 결과 |
|------|------|
| 코드 변경 | 없음 |
| compose 변경 | 없음 (이번 단계는 설계만) |
| DB 변경 | 없음 |
| 컨테이너 재기동 | 없음 |
| 파일 삭제 | 없음 |
| git diff | 보고서 1개 (v1_1_file_storage_persistence_plan.md) |

---

**최종 판정: PASS** (설계 완료, 적용 준비 완료)  
*다음 Stage(FILE-STORAGE-2)에서 compose 수정 → 서버 적용 → 검증 수행*

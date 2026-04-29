# V1.1 Production API Deploy Report

**일시**: 2026-04-29 (KST)  
**작업**: PROD-DEPLOY-1 — 운영 API 컨테이너 V1.1 코드 반영  
**검증자**: Claude Sonnet 4.6 (자동)

---

## 1. 배포 전 상태

| 항목 | 값 |
|------|-----|
| 서버 HEAD (배포 전) | 6585da0 docs(product): add V1.1 production backup readiness report |
| working tree | clean |
| API 컨테이너 | Up 16 hours (이전 이미지, V1.1 코드 미반영) |
| DB migration 상태 | 39개 테이블, V1.1 신규 10개, projects 23컬럼 — 정상 |
| health (배포 전) | status: ok, db: connected |
| V1.1 API paths (배포 전) | 0개 (운영 포트 기준) |

---

## 2. git pull 결과

```
git pull --ff-only origin master
Fast-forward: 6585da0 → 3470c50
추가 파일:
  - docs/reports/v1_1_prod_api_smoke_report.md
  - docs/reports/v1_1_prod_migration_apply_report.md
```

서버 HEAD: **3470c50** docs(product): add V1.1 production API smoke report

### 필수 커밋 포함 확인

| 커밋 | 내용 | 포함 |
|------|------|------|
| 2ab633a | feat: add V1.1 ZIP download API | ✓ |
| bb66aa2 | docs: add V1.1 backend E2E closure report | ✓ |
| 939e707 | docs: add V1.1 production migration apply report | ✓ |
| 3470c50 | docs: add V1.1 production API smoke report | ✓ |

---

## 3. build 결과

```
docker compose -f infra/docker-compose.yml build api
```

| 항목 | 결과 |
|------|------|
| requirements.txt 설치 | CACHED |
| COPY . . | DONE 0.1s |
| 새 이미지 SHA | sha256:8ac53125b434… |
| 이미지 태그 | infra-api:latest |
| build 결과 | **SUCCESS** |

---

## 4. API 컨테이너 재기동 결과

```
docker compose -f infra/docker-compose.yml up -d api
```

| 항목 | 결과 |
|------|------|
| Recreate | risk-assessment-api Recreated |
| DB dependency | risk-assessment-db Healthy (대기 후 통과) |
| Started | risk-assessment-api Started |
| StartedAt (UTC) | 2026-04-29T07:16:31Z (KST 16:16:31) |
| 재기동 대상 | risk-assessment-api만 (DB 등 타 컨테이너 무변경) |

---

## 5. health 결과

```json
{
  "status": "ok",
  "api": "up",
  "db": "connected",
  "kosha_db": "connected"
}
```

| 항목 | 결과 |
|------|------|
| health status | ok |
| db | connected |
| V1.1 API paths | **25개** 등록 확인 |

---

## 6. Smoke 결과 (운영 포트 8100)

### 6.1 기존 API 호환성

| API | HTTP | 결과 |
|-----|------|------|
| GET /api/projects | 200 | PASS |

### 6.2 V1.1 Rules

| API | HTTP | 결과 |
|-----|------|------|
| GET /api/v1/new-construction/rules | 200 | PASS — 3개 (RULE_NEW_WORKER, RULE_EQUIPMENT_INTAKE, RULE_DAILY_TBM) |

### 6.3 V1.1 List APIs (project_id=4, V1_1_SMOKE_20260429)

| Endpoint | HTTP | 결과 |
|----------|------|------|
| GET .../profile | 200 | PASS |
| GET .../sites | 200 | PASS |
| GET .../contractors | 200 | PASS |
| GET .../workers | 200 | PASS |
| GET .../equipment | 200 | PASS |
| GET .../work-schedules | 200 | PASS |
| GET .../safety-events | 200 | PASS |
| GET .../document-packages | 200 | PASS — 3개 |

### 6.4 E2E 흐름 (generate → run-excel → build-zip → download-zip)

컨테이너 재기동으로 /tmp 초기화 → 기존 package_id=1 파일 소실.  
신규 package (RULE_DAILY_TBM)로 E2E 재검증.

| 단계 | 결과 |
|------|------|
| generate RULE_DAILY_TBM | PASS — package_id=4, job_id=4, status: pending |
| run-excel (job_id=4) | PASS — status: completed, generated: 4, failed: 0 |
| build-zip (package_id=4) | PASS — status: ready, zip_size: 29,116 bytes |
| download-zip | PASS — Content-Type: application/zip, 29,116 bytes |
| ZIP 시그니처 | PASS — PK (0x504b0304) |
| ZIP 내 xlsx openpyxl 로드 | PASS — 4개 모두 정상 |

ZIP 내 파일:
```
TBM_일지.xlsx           → ['TBM안전점검일지']
작업_전_안전_확인서.xlsx → ['작업전안전확인서']
출근부.xlsx              → ['참석자명부']
사진_첨부_시트.xlsx      → ['사진대지']
```

---

## 7. 로그 확인 결과

```
ERROR/CRITICAL/Traceback: 0건
500 응답: 0건
```

로그에서 발견된 유일한 4xx:
- `HEAD /api/v1/new-construction/document-packages/4/download-zip HTTP/1.1 405`  
  → download-zip은 GET 전용, HEAD 미지원 — **정상 동작**

모든 운영 요청 로그 정상 (200 OK).

---

## 8. DB 변경 없음 확인

| 항목 | 결과 |
|------|------|
| DB DDL 실행 | 없음 |
| migration 추가 적용 | 없음 |
| V1.1 테이블 (39개) | 유지 |
| equipment 마스터 (18건) | 유지 |
| 컨테이너 재기동 대상 | risk-assessment-api만 (DB 컨테이너 무변경) |

---

## 9. Accepted WARN

### WARN-1: /tmp 파일 경로 — 컨테이너 재기동 시 생성 파일 소실

| 항목 | 내용 |
|------|------|
| 현상 | 생성 xlsx/zip 파일이 컨테이너 내 /tmp에 저장되어 재기동 시 초기화 |
| 영향 | 재기동 후 기존 package의 download-zip 호출 시 "ZIP file is missing on disk" 반환 |
| 회피 방법 | run-excel → build-zip 재실행으로 파일 재생성 가능 |
| 판정 | **WARN** — 별도 Stage에서 볼륨 마운트 또는 영구 스토리지로 해결 권장 |

### WARN-2: safety_events PATCH title 400

이전 smoke 보고서(v1_1_prod_api_smoke_report.md)에서 기록된 accepted WARN.  
title 필드가 화이트리스트 미포함으로 400 반환. 이번 단계에서 수정 없음.  
UI에서 title 필드 필요 확정 시 별도 Stage로 처리.

---

## 10. 다음 단계 제안

1. **WARN-1 해결**: 생성 파일 저장 경로를 볼륨 마운트된 경로(예: `/app/data/generated/`)로 변경하여 재기동 후에도 파일 유지
2. **WARN-2 해결**: safety_events PATCH whitelist에 `title` 필드 추가 (UI 요구사항 확정 후)
3. **V1.1 UI 연동**: 운영 API 정상화에 따라 프론트엔드에서 V1.1 API 엔드포인트 연결

---

## 검증 요약

| 항목 | 결과 |
|------|------|
| DB DDL | 없음 |
| migration 추가 적용 | 없음 |
| API 컨테이너 외 재기동 | 없음 |
| builder/catalog/registry 변경 | 없음 |
| 운영 API health | ok |
| V1.1 rules endpoint | 200, 3개 |
| 기존 /api/projects | 200 |
| E2E 흐름 (generate → download-zip) | PASS |
| 로그 오류 | 없음 |

---

**최종 판정: PASS (WARN 2건)**
- WARN-1: 생성 파일 /tmp 저장 (재기동 시 소실)
- WARN-2: safety_events PATCH title 400 (이전 accepted WARN 유지)

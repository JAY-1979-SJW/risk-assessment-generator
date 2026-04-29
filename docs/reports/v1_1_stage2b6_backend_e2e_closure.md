# V1.1 Stage 2B-6 — Backend End-to-End 통합 마감 검증 보고서

작성일: 2026-04-29 (KST)
대상 HEAD: `2ab633a` (Stage 2B-5D ZIP 다운로드 직후, 본 단계는 코드 무수정)
판정: **PASS** — 격리 DB(`kras_v11_dryrun_20260429`) 기준 API 10종 + 3 Rule × (preview → generate → run-excel → build-zip → download-zip) E2E 모두 정상, 운영 DB 무변경, 기존 핵심 파일 무수정.

---

## 1. 전체 요약

| 영역 | 결과 |
|---|---|
| API smoke (10 listing + rules) | 10/10 200 ✅ |
| Rules registry | 3/3 (`RULE_NEW_WORKER`, `RULE_EQUIPMENT_INTAKE`, `RULE_DAILY_TBM`) ✅ |
| Rule E2E preview→generate→run-excel→build-zip→download-zip | 3/3 모두 PASS ✅ |
| 최종 status 전이 | jobs 3/3 `completed`, packages 3/3 `ready`, files 15/15 `ready` ✅ |
| ZIP 무결성 | 3/3 `testzip()=None`, 항목 path-safe ✅ |
| 내부 xlsx openpyxl | 15/15 OK ✅ |
| 운영 DB(`kras`) 변경 | 없음 (public 30 유지, V1.1 테이블 미존재 그대로) ✅ |
| 기존 equipment 마스터 접근 | 없음 (소스 grep 0건) ✅ |
| builder / catalog / registry 변경 | 없음 ✅ |
| migration / DDL 실행 | 없음 ✅ |

---

## 2. Stage 2B 진행 이력

| 단계 | 커밋 | 내용 |
|---|---|---|
| 2A 설계/락 | `1685ebf` → `b3bfa15` | 데이터 모델, 마이그레이션 plan lock |
| 2B-1/2 마이그레이션 | `e75f897`, `94002dc`, `9c0debf`, `bb54c9d`, `95875a3`, `f8b2d96` | `0013`~`0023` 작성, 정적·드라이런 검토, `equipment` → `project_equipment` 리네임 |
| 2B-3 API | `d068519`, `27dd848`, `0551dee`, `c18a220`, `3979cc4` | 프로젝트/사이트/계약자/근로자/장비/일정/안전이벤트/문서메타 API |
| 2B-3F live smoke | `631a3ce` | 격리 DB API 라이브 smoke |
| 2B-4 Rule MVP | `2bfaa7b`, `cd19c83` | rule MVP 설계 + metadata generate API |
| 2B-5A Excel runner | `c86fe15`, `a74a7d5` | Excel 생성 runner + 라이브 smoke |
| 2B-5B 품질검토 + Fix | `91dc8fd`, `4e8d525` | openpyxl 자동 검토 → 6 builder paperSize=9 보정 |
| 2B-5C ZIP builder | `31f4a39` | 패키지 ZIP 생성 API |
| 2B-5D ZIP 다운로드 | `2ab633a` | ZIP 다운로드 API + path-safety helper |
| **2B-6 마감 검증** | (본 보고서) | 격리 DB 기준 백엔드 E2E 통합 점검 |

---

## 3. 구현된 V1.1 API 목록 (`/api/v1/new-construction`)

| 분류 | 메서드/경로 |
|---|---|
| 프로젝트 프로필 | `GET /projects/{id}/profile`, `PATCH /projects/{id}/profile` |
| 사이트 | `GET/POST /projects/{id}/sites`, `PATCH/DELETE /sites/{sid}` |
| 계약자 | `GET/POST /projects/{id}/contractors`, `PATCH/DELETE /contractors/{cid}` |
| 근로자 | `GET/POST /projects/{id}/workers`, `PATCH/DELETE /workers/{wid}` |
| 프로젝트 장비 (project_equipment) | `GET/POST /projects/{id}/equipment`, `PATCH/DELETE /equipment/{eid}` |
| 작업 일정 | `GET/POST /projects/{id}/work-schedules`, `PATCH/DELETE /work-schedules/{sid}` |
| 안전 이벤트 | `GET/POST /projects/{id}/safety-events`, `PATCH/DELETE /safety-events/{eid}` |
| 문서 작업 | `GET/POST /projects/{id}/document-jobs`, `GET/PATCH /document-jobs/{jid}` |
| 문서 패키지 | `GET/POST /projects/{id}/document-packages`, `GET/PATCH /document-packages/{pid}` |
| 문서 파일 | `GET/POST /document-packages/{pid}/files`, `GET/PATCH /document-files/{fid}` |
| Rule | `GET /rules`, `POST /projects/{id}/rules/{rid}/preview`, `POST /projects/{id}/rules/{rid}/generate` |
| Excel/ZIP | `POST /document-jobs/{jid}/run-excel`, `POST /document-packages/{pid}/build-zip`, `GET /document-packages/{pid}/download-zip` |

---

## 4. Migration 상태 (운영 DB 미적용)

| 파일 | 내용 |
|---|---|
| `data/risk_db/schema/migrations/0013_create_users_table.sql` | users 테이블 + idempotent 트리거 (`DROP TRIGGER IF EXISTS … ON users; CREATE …`) |
| `0014_add_projects_v1_1_fields.sql` | projects 컬럼 보강 |
| `0015_create_sites.sql` | sites |
| `0016_create_contractors.sql` | contractors |
| `0017_create_workers.sql` | workers |
| `0018_create_project_equipment.sql` | **project_equipment** (운영 `equipment` 마스터와 충돌 회피) |
| `0019_create_work_schedules.sql` | work_schedules |
| `0020_create_safety_events.sql` | safety_events |
| `0021_create_document_generation_jobs.sql` | document_generation_jobs |
| `0022_create_generated_document_packages.sql` | generated_document_packages (zip_file_path / storage_key 포함) |
| `0023_create_generated_document_files_and_indexes.sql` | generated_document_files + 인덱스 |

위험 SQL 점검: `DROP TABLE` / `TRUNCATE` / `ALTER … RENAME` 없음. `0013` 의 `DROP TRIGGER IF EXISTS` 는 동일 이름 트리거 재생성 직전의 idempotent 보호로, 안전.

운영 DB(`kras`) public 테이블 수: **30** (V1.1 미적용 상태 그대로). `to_regclass('public.project_equipment')` / `to_regclass('public.generated_document_files')` 모두 NULL → V1.1 테이블 미존재 확인.

---

## 5. End-to-End 검증 결과 (격리 DB + TestClient)

- 위치: 앱서버 `risk-assessment-api` 컨테이너
- DB: 격리 dry-run `kras_v11_dryrun_20260429`
- 환경변수: `DATABASE_URL` 격리 DB 직결, `GENERATED_DOCUMENTS_DIR=/tmp/v11_2b6_out`, `PYTHONPATH=/tmp/v11app/backend:/tmp/v11app:/app`
- 사전: 기존 generated_document_* / document_generation_jobs 행을 `project_id=1` 범위에서 DELETE 하여 fresh slate 보장. workers / project_equipment 시드 1건씩 보장 후 진행.

### 5.1 API smoke (read-only listings)

| Endpoint | HTTP |
|---|---|
| `GET /projects/1/profile` | 200 |
| `GET /projects/1/sites` | 200 |
| `GET /projects/1/contractors` | 200 |
| `GET /projects/1/workers` | 200 |
| `GET /projects/1/equipment` | 200 |
| `GET /projects/1/work-schedules` | 200 |
| `GET /projects/1/safety-events` | 200 |
| `GET /projects/1/document-jobs` | 200 |
| `GET /projects/1/document-packages` | 200 |
| `GET /rules` | 200 (3 rule 모두 포함) |

### 5.2 Rule 3개 — preview/generate/run-excel/build-zip/download-zip

| Rule | preview | generate | run-excel | build-zip | download | expected files | zip entries | content-type | testzip | xlsx open |
|---|---|---|---|---|---|---|---|---|---|---|
| RULE_NEW_WORKER       | 200 | 201 | 200 | 200 | 200 | 5 | 5 ✅ | application/zip | None ✅ | 5/5 ✅ |
| RULE_EQUIPMENT_INTAKE | 200 | 201 | 200 | 200 | 200 | 6 | 6 ✅ | application/zip | None ✅ | 6/6 ✅ |
| RULE_DAILY_TBM        | 200 | 201 | 200 | 200 | 200 | 4 | 4 ✅ | application/zip | None ✅ | 4/4 ✅ |

### 5.3 status 전이 (최종 상태)

| 항목 | 결과 |
|---|---|
| `document_generation_jobs` | 3/3 `completed` |
| `generated_document_packages` | 3/3 `ready`, `zip_file_path` 모두 `${GENERATED_DOCUMENTS_DIR}` 하위 |
| `generated_document_files` | total=15, status='ready'=15 |
| 전이 흐름 | generate(`pending` 생성) → run-excel(`running`→`completed`/`pending`→`ready`) → build-zip(`pending`→`ready`) ✅ |

### 5.4 에러 케이스 sanity

- 존재하지 않는 `package_id=99999` → `download-zip` **404** (router 의 `package_not_found`).

---

## 6. 보안 / Guard 검증

| 항목 | 결과 |
|---|---|
| 운영 DB(`kras`) DDL / 컨테이너 restart | 없음 ✅ |
| 운영 DB 직접 접속 | 없음 (smoke 는 격리 DB 만, TestClient in-process) ✅ |
| 기존 `equipment` 마스터 read/write (`grep` `FROM/UPDATE/INSERT INTO equipment`) | 0건, `project_equipment` 만 사용 ✅ |
| `document_catalog.yml` / `engine/output/form_registry.py` / `engine/output/supplementary_registry.py` | 변경 없음 ✅ |
| 개별 builder 파일 변경 | 없음 ✅ |
| `backend/main.py` / `backend/db.py` / `backend/routers/projects.py` / `backend/routers/form_export.py` | 변경 없음 ✅ |
| `download-zip` 에서 ZIP 재생성 / `build_zip` 재호출 | 없음 (path-safety 후 `FileResponse` 만) ✅ |
| `run-excel` 외 builder 실행 경로 | 없음 ✅ |
| Rule generate 에서 Excel 생성 | 없음 (metadata 단계만 — 실제 xlsx 는 `run-excel` 에서) ✅ |
| worker / equipment POST 시 자동 Rule 실행 | 없음 (명시 호출만) ✅ |
| ZIP 다운로드 path traversal | 차단 — segment `..` 검사 + `Path.resolve()` + `relative_to(base)` + `.zip` 강제 + `is_file()` 검증 ✅ |
| 민감정보 필드 (주민/외국인등록번호·전화·건강정보) | 스키마/응답에 미포함 ✅ |
| `form_registry.list_supported_forms()` | 87 (변동 없음) ✅ |
| `supplementary_registry.list_supplemental_types()` | 10 (변동 없음) ✅ |

---

## 7. 운영 DB 적용 전 남은 사항

1. **운영 DB migration**: `0013`~`0023` 을 운영 `kras` DB 에 적용 (별도 게이트, 다운타임/잠금 시간 사전 합의 필요).
2. **운영 smoke**: migration 적용 직후 동일 E2E (preview→generate→run-excel→build-zip→download) 를 운영 환경에서 1회 재현.
3. **인증/인가**: download-zip 에 project 멤버십 기반 접근 제어 게이트 연결 — 현재는 인증 미연결 상태로 라우터 노출.
4. **다운로드 감사 로깅**: append-only 감사 테이블 또는 별도 로그 채널 권장.
5. **UI**: 신축공사 흐름 UI 미구현. 백엔드 안정 후 별도 phase.
6. **격리 DRY-RUN DB**: `kras_v11_dryrun_20260429` 잔존 데이터(project_id=1 기준 packages 3 / files 15 / zip 3) — 다음 dry-run 시 TEMPLATE 재클론 또는 사용자 승인 후 DROP 권고.

---

## 8. 다음 단계 제안

| 단계 | 내용 |
|---|---|
| 2C: 운영 DB migration 적용 | 0013~0023 일괄 적용, 사전 백업, 장애대비 롤백 시나리오 동봉 |
| 2D: 운영 E2E smoke | 본 보고서 5장과 동일한 플로우 재실행, 결과 보고 |
| 2E: 인증/감사 강화 | download-zip 권한 + 감사 로깅 |
| 3: UI | 신축공사 wizard / 다운로드 / 패키지 관리 화면 |

---

## 9. 검증 (본 단계 변경 없음)

| 항목 | 결과 |
|---|---|
| 코드 변경 | 없음 (보고서 1건 추가) ✅ |
| DB DDL | 없음 ✅ |
| 운영 DB 변경 | 없음 ✅ |
| migration 파일 변경 | 없음 ✅ |
| registry / catalog / supplementary 변경 | 없음 ✅ |
| `git diff` | 본 보고서 1건만 ✅ |
| 비밀값 / connection string | 보고서 미포함 ✅ |
| 임시 산출물 | `/tmp/v11app`, `/tmp/v11_2b6_out`, `/tmp/smoke_e2e.py`, `/tmp/v11_2b6_e2e.json` (호스트·컨테이너) 모두 정리 ✅ |

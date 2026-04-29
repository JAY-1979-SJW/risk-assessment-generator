# V1.1 Stage 2B-3F — 격리 DB 라이브 Smoke 검증 보고서

작성일: 2026-04-29 (KST)
대상 HEAD: `3979cc4` (Stage 2B-3E 완료 시점)
판정: **PASS**

---

## 1. 실행 환경

- 위치: 앱서버 `1.201.176.236`
- 방법: `risk-assessment-api` 컨테이너에 V1.1 백엔드 코드를 `/tmp/v11app` 으로 오버레이 후 FastAPI `TestClient` 로 in-process 호출 (외부 포트 바인딩 없음, nohup/백그라운드 없음)
- DB: 격리 dry-run DB `kras_v11_dryrun_20260429` (운영 DB 아님)
- 연결: 컨테이너 내 `DATABASE_URL` 환경변수만 덮어 격리 DB 직결, 비밀번호 등 시크릿은 로그 미출력
- 운영 컨테이너: restart/config 변경 없음 (실행 중 uvicorn 별도, 본 smoke와 격리)
- 실행 후 `/tmp/v11app`, `/tmp/v11_backend`, `/tmp/smoke_v11.py` 모두 정리 완료

## 2. 격리 DB 사용 확인

- 운영 DB(`kras`): public 테이블 수 30 그대로, `equipment` 마스터 컬럼 (`equipment_code, equipment_name, sort_order, is_active`) 변동 없음, **`project_equipment` 테이블 부재** (V1.1 미적용 상태 그대로)
- 격리 DB: smoke 호출 후 신규 V1.1 테이블 9개에 각 1건씩 row 생성 확인 (sites/contractors/workers/project_equipment/work_schedules/safety_events/document_generation_jobs/generated_document_packages/generated_document_files = 1/1/1/1/1/1/1/1/1)

## 3. 운영 DB 무변경 확인

| 항목 | 운영 DB 상태 |
|---|---|
| public 테이블 수 | 30 (변동 없음) |
| equipment 마스터 | 컬럼 4개 그대로 |
| project_equipment | 미존재 (V1.1 미적용) |
| DDL 실행 | 없음 |

## 4. API 그룹별 Smoke 결과 (총 40건, 40/40 OK)

| # | 그룹 | 결과 |
|---|---|---|
| A | Project Profile | GET 200, PATCH 200, 404 가드 200 — ✅ 3/3 |
| B | Sites | GET 200, POST 201, PATCH 200, DELETE 204 (soft), 잘못된 project 404 — ✅ 5/5 |
| C | Contractors | POST 201, GET 200, PATCH 200, **빈 PATCH 400** — ✅ 4/4 |
| D | Workers | POST 201, PATCH 200, DELETE 204, **contractor_id ↔ project guard 400** — ✅ 4/4 |
| E | Project Equipment (URL `/equipment`, table `project_equipment`) | POST 201, GET 200, PATCH 200, DELETE 204 — ✅ 4/4 |
| F | Work Schedules | POST 201, GET 200, PATCH 200, DELETE 204 (status='cancelled'), **planned_end_date < planned_start_date 422** — ✅ 5/5 |
| G | Safety Events | POST 201, GET 200, PATCH 200, **event_type whitelist 422** — ✅ 4/4 |
| H | Document Jobs | POST 201, GET list 200, GET by id 200, PATCH 200 — ✅ 4/4 |
| I | Document Packages | POST 201, GET 200, PATCH 200 — ✅ 3/3 |
| J | Document Files | POST 201, GET list 200, GET by id 200, PATCH 200 — ✅ 4/4 |

## 5. 생성/수정/Soft Delete 검증

- POST: 모든 자식 리소스 201 + 자동 채워진 `id`/`created_at`/`updated_at` 응답 확인
- PATCH: whitelist UPDATE 후 변경 컬럼 반영 + `updated_at` 자동 갱신 확인
- DELETE: 실제 DELETE 미수행, `status` 컬럼만 변경
  - sites/contractors/workers/project_equipment → `inactive`
  - work_schedules/safety_events → `cancelled`
- 빈 PATCH payload: contractors 등 신규 엔드포인트에서 `400 No fields to update` 정상

## 6. JSONB 검증

- `safety_events.payload_json`: dict `{"worker_id":123,"tags":["smoke","v1.1"],"n":5}` 라운드트립 일치 ✅
- `document_generation_jobs.input_snapshot_json`: dict 입력 후 GET 시 dict로 복원 ✅
- psycopg2 `Json()` 어댑터 적용으로 정상 직렬화/역직렬화

## 7. project_equipment Guard 결과

- API URL `/equipment` 사용 시 SQL은 모두 `project_equipment` 테이블만 조회 (운영 마스터 `equipment` 미접근)
- 운영 DB의 `equipment` 마스터(4컬럼) 그대로 유지 — POST `/equipment` 으로 생성된 row는 격리 DB의 `project_equipment` 에만 적재
- repository/router 코드의 `equipment` 단어는 **혼동 금지 주석에서만** 등장

## 8. 추가 가드 검증

| 검증 | 결과 |
|---|---|
| project_id가 존재하지 않을 때 children POST → 404 | ✅ (sites 케이스 확인) |
| contractor_id가 다른 project 소속일 때 POST → 400 | ✅ (workers 케이스 확인, 999999 unknown 으로 검증) |
| safety_events 생성 시 잘못된 event_type → 422 | ✅ Literal whitelist |
| work_schedules planned_end < planned_start → 422 | ✅ pydantic model_validator |

## 9. 실패/경고 사항

없음. 40/40 의도된 상태코드 일치.

## 10. Stage 2B-4 진행 가능 여부

**✅ 진행 가능.** V1.1 메타 CRUD 11개 리소스 라이브 동작 확인 완료. 다음 단계로 자동생성 Rule 실행/Excel builder 연결/패키지 ZIP 생성 등을 별도 단계로 분리 추진 가능.

## 11. 후속 권장 조치

- 격리 DB `kras_v11_dryrun_20260429`: 사용자 승인 후 DROP 권장 (smoke 데이터 1행씩 잔존). 다음 dry-run 시 TEMPLATE 재클론.
- 운영 DB에 0013~0023 마이그레이션을 적용하는 단계는 별도 게이트(Stage 2B-4 또는 2C)로 분리.
- API 인증 미적용 상태이므로 외부 노출 전에 일괄 적용 단계 추가 필요.

---

## 12. 검증

- 코드 변경: 없음
- DB DDL: 없음
- 운영 DB 변경: 없음
- migration 파일 변경: 없음
- registry/catalog/supplementary 변경: 없음
- git diff: 본 보고서 1개

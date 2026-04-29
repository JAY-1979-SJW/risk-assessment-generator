# V1.1 Stage 2B-5D — Document Package ZIP 다운로드 라이브 Smoke 보고서

작성일: 2026-04-29 (KST)
대상 HEAD: `31f4a39` (Stage 2B-5C ZIP builder 직후)
판정: **PASS** — 3 Rule 모두 다운로드 200 OK / `application/zip` / 안전 파일명, 5종 에러 케이스 모두 의도된 코드 반환, 운영 DB 무변경.

---

## 1. 다운로드 API 요약

`GET /api/v1/new-construction/document-packages/{package_id}/download-zip`

| 코드 | 조건 |
|---|---|
| 200 (FileResponse, `application/zip`) | 다운로드 성공 |
| 404 `package_not_found` | package 없음 |
| 409 `package_not_ready` | `package.status ≠ 'ready'` (응답에 `current_status`) |
| 400 `zip_not_built` | `zip_file_path` 비어있음 |
| 400 `unsafe_path` | 경로가 base_dir 밖 / `..` 포함 / `.zip` 아님 |
| 404 `zip_file_missing` | 경로는 안전하지만 디스크상 파일 없음 |

응답 헤더:
- `Content-Type: application/zip`
- `Content-Disposition: attachment; filename="package_{id}.zip"; filename*=UTF-8''<percent-encoded UTF-8>`
   - ASCII fallback 으로 항상 `package_{id}.zip` 제공, 비-ASCII 패키지명은 RFC 5987 `filename*` 로 별도 전달

DB 상태 변경 없음. ZIP 재생성 / Excel builder 실행 / status 갱신 없음.

---

## 2. Download Safety

`backend/services/new_construction_downloads.py` 신규 helper.

| 항목 | 동작 |
|---|---|
| base_dir | `Path(${GENERATED_DOCUMENTS_DIR or /tmp/risk_assessment_generated_documents}).resolve()` |
| path safety | 1) 경로 segment 에 `..` 포함 차단, 2) `Path(...).resolve()` 후 `relative_to(base)` 검사로 traversal/absolute escape 차단, 3) 확장자 `.zip` 강제, 4) `is_file()` 확인 |
| filename | `package_name` 이 있으면 `[^0-9A-Za-z가-힣._-]+` → `_`, `..` 제거, 80자 cap, 비면 `package_{id}.zip` 으로 fallback |
| status guard | repo `get_document_package` 후 `status != 'ready'` → 409 |
| DB trust | `zip_file_path` 를 그대로 사용하지 않고 위 safety 통과한 resolved Path 만 FileResponse 에 전달 |
| 부수효과 | 없음 (ZIP 재생성 / status 변경 / build_zip 호출 없음) |

---

## 3. 라이브 Smoke 결과

- 위치: 앱서버 `risk-assessment-api` 컨테이너 + 격리 DB `kras_v11_dryrun_20260429`
- 방법: V1.1 overlay `/tmp/v11app` docker cp → 격리 DB 상태 리셋 → run-excel·build-zip 으로 ZIP 사전 준비 → FastAPI `TestClient` 로 신축 라우터만 mount(`prefix="/api"`)하여 `download-zip` 호출
- 환경변수: `DATABASE_URL=…/kras_v11_dryrun_20260429`, `GENERATED_DOCUMENTS_DIR=/tmp/v11_2b5d_out`

| Rule | HTTP | Content-Type | Content-Disposition | entries | expected | testzip | xlsx open |
|---|---|---|---|---|---|---|---|
| RULE_NEW_WORKER       | 200 | application/zip | `attachment; filename="package_5.zip"; filename*=UTF-8''package_5.zip` | 5 | 5 ✅ | None (OK) | 5/5 ✅ |
| RULE_EQUIPMENT_INTAKE | 200 | application/zip | `attachment; filename="package_6.zip"; filename*=UTF-8''package_6.zip` | 6 | 6 ✅ | None (OK) | 6/6 ✅ |
| RULE_DAILY_TBM        | 200 | application/zip | `attachment; filename="package_7.zip"; filename*=UTF-8''package_7.zip` | 4 | 4 ✅ | None (OK) | 4/4 ✅ |

> `package_name` 이 격리 DB 시드에서 비어 있어 fallback 인 `package_{id}.zip` 으로 표기됨. `package_name` 이 채워지면 sanitize 결과가 들어간다(safe filename 헬퍼 검증).

ZIP 항목 path-safety: 모든 항목에 `/`, `\\`, `..` 미포함, `.xlsx` 확장자만 — 3/3 ZIP `entries_safe=True`.

---

## 4. 에러 케이스

| 케이스 | 전제 | 응답 |
|---|---|---|
| unknown_package | 존재하지 않는 `package_id=99999` | **404** `Document package not found` |
| not_ready | 해당 package 의 `status='pending'` 으로 일시 변경 | **409** `Package is not ready for download` (`current_status='pending'`) |
| zip_not_built | `zip_file_path = NULL` | **400** `ZIP has not been built for this package` |
| unsafe_path | `zip_file_path = '/etc/passwd'` (base_dir 밖) | **400** `Unsafe ZIP file path` |
| zip_file_missing | `zip_file_path` 가 base_dir 하위·`.zip` 이지만 파일 없음 | **404** `ZIP file is missing on disk` |

> 테스트 종료 후 해당 package 의 `zip_file_path` 는 실제 zip 경로로 복원했고, `status` 도 `ready` 로 되돌렸다. 격리 DB 외부 영향 없음.

---

## 5. 운영 DB / 격리 보장

| 항목 | 결과 |
|---|---|
| 운영 DB(`kras`) public 테이블 수 | 30 (V1.1 미적용 그대로) ✅ |
| 운영 DB DDL / 컨테이너 restart | 없음 ✅ |
| 격리 dry-run DB 외부 접속 | 없음 (TestClient 는 in-process) ✅ |
| 컨테이너·서버 임시 산출물 | `/tmp/v11app`, `/tmp/v11_2b5d_out`, `/tmp/smoke_download.py`, `/tmp/v11_2b5d_smoke.json`, 이전 단계 잔존물 모두 정리 ✅ |
| 비밀값 / connection string 노출 | 없음 ✅ |

---

## 6. 검증

| # | 항목 | 결과 |
|---|---|---|
| 1 | `git status --short` 시작 시 | clean ✅ |
| 2 | py_compile `new_construction_downloads.py` | OK ✅ |
| 3 | py_compile `new_construction.py` (routers) | OK ✅ |
| 4 | py_compile `new_construction_repository.py` | OK ✅ |
| 5 | py_compile `new_construction.py` (schemas) | OK ✅ (변경 없음, 기존 컴파일 통과) |
| 6 | `form_registry.list_supported_forms()` | 87 ✅ |
| 7 | `supplementary_registry.list_supplemental_types()` | 10 ✅ |
| 8 | builder 파일 변경 | 없음 ✅ |
| 9 | `document_catalog.yml` / `form_registry.py` / `supplementary_registry.py` | 변경 없음 ✅ |
| 10 | `zip_builder.build_zip` / `excel_runner.run_excel` 신규 호출 | 없음 (download endpoint 본문에서 import·호출 0건) ✅ |
| 11 | Excel builder 실행 코드 추가 | 없음 ✅ |
| 12 | equipment 마스터 (`FROM equipment` / `INSERT INTO equipment` / `UPDATE equipment`) 접근 | 없음 ✅ |
| 13 | UI / frontend / `main.py` / `db.py` / `projects.py` / `form_export.py` 변경 | 없음 ✅ |
| 14 | background worker / cron / scheduler | 없음 ✅ |
| 15 | StreamingResponse 사용 | 없음 (불필요 — `FileResponse` 만) ✅ |

---

## 7. 변경 파일

- 신규: `backend/services/new_construction_downloads.py` (path safety + filename sanitize helper)
- 수정: `backend/routers/new_construction.py` (FastAPI `FileResponse` import, `urllib.parse.quote` import, `GET …/document-packages/{id}/download-zip` 엔드포인트 추가)
- 신규(보고서): `docs/reports/v1_1_stage2b5d_zip_download_live_smoke.md`

스키마(`backend/schemas/new_construction.py`)와 repository(`backend/repositories/new_construction_repository.py`) 는 기존 `get_document_package` 만 재사용하여 변경하지 않았다.

migration / catalog / registry / 개별 builder / `main.py` / `db.py` / `projects.py` / `form_export.py`: **변경 없음**.

---

## 8. 다음 단계 제안

- 인증·권한 (project 소속자만 다운로드 허용) 게이트는 별도 단계에서 기존 인증 dependency 와 연결.
- 다운로드 감사 로깅 (project_id, user_id, package_id, ts) 추가 가능 — 운영 DB DDL 영향 없는 append-only 테이블 권장.
- 운영 DB 0013~0023 마이그레이션 적용은 별도 게이트 유지.
- 격리 DB `kras_v11_dryrun_20260429` 는 추후 dry-run 시 TEMPLATE 재클론 또는 사용자 승인 후 DROP 권고.

# V1.1 Stage 2B-5C — Document Package ZIP Builder 라이브 Smoke 보고서

작성일: 2026-04-29 (KST)
대상 HEAD: `4e8d525` (Stage 2B-5B-Fix paperSize 보정 직후)
판정: **PASS** — 3 Rule × (run-excel + build-zip) 모두 정상, 15 xlsx → 3 zip 생성, 모든 ZIP 항목 path-safe / openpyxl load OK / 운영 DB 무변경.

---

## 1. 구현 API

`POST /api/v1/new-construction/document-packages/{package_id}/build-zip`

| 코드 | 조건 |
|---|---|
| 200 (`DocumentPackageZipBuildResponse`) | ZIP 생성 성공 |
| 404 `package_not_found` | package 없음 |
| 400 `no_files` | 패키지 내 파일 0건 |
| 409 `invalid_status` | package.status ∉ {ready, created} |
| 400 `files_not_ready` | 일부 file.status ≠ 'ready' (응답에 not_ready_file_ids) |
| 400 `file_missing` | file_path 비었거나 디스크상 파일 없음 (응답에 missing 목록) |

응답 필드: `package_id, project_id, status, file_count, zip_file_path, zip_file_size`.

실패 시 package.status 는 변경하지 않고 400/409 만 응답한다 (사양 명시: `failed` 로 자동 강등 금지).

---

## 2. ZIP Builder 동작

| 항목 | 동작 |
|---|---|
| storage | `${GENERATED_DOCUMENTS_DIR or /tmp/risk_assessment_generated_documents}/project_{project_id}/package_{package_id}/package_{package_id}.zip` (resolve 후 base 외부 차단) |
| 임시 파일 | `*.zip.tmp` 로 쓰고 `os.replace` 로 원자적 교체 (실패 시 tmp 정리) |
| 압축 | `zipfile.ZIP_DEFLATED` |
| 내부 파일명 | `{display_name}.xlsx` 기본, 중복 시 `{file_id}_{display_name}.xlsx`. 한글 허용, `[^0-9A-Za-z가-힣._-]` → `_`, `..` 제거, 80자 cap |
| path safety | base traversal 차단 (`relative_to(base)`), arcname 디렉터리 분리자 / `..` 미포함 보장 |
| zip validation | ZIP 생성 후 `ZipFile.testzip()` + `openpyxl.load_workbook(BytesIO)` 로 각 xlsx 적재 검증(테스트에서) |

**금지 항목 준수**: `StreamingResponse` / `FileResponse` 미사용, 다운로드 endpoint 미추가, background worker 없음, equipment 마스터 테이블 미접근, builder/registry/catalog 무수정.

---

## 3. Repository 추가

`backend/repositories/new_construction_repository.py`

- `update_document_package_zip_ready(package_id, zip_file_path, storage_key=None)` — `status='ready'`, `zip_file_path`, optional `storage_key`, `updated_at=NOW()` SET.
- 기존 함수 재사용: `get_document_package`, `list_files_for_package`, `get_project_profile`.

---

## 4. Schema 추가

`backend/schemas/new_construction.py`

```python
class DocumentPackageZipBuildResponse(BaseModel):
    package_id: int
    project_id: int
    status: str
    file_count: int
    zip_file_path: str
    zip_file_size: int
```

---

## 5. 라이브 Smoke 결과

- 위치: 앱서버 `risk-assessment-api` 컨테이너 + 격리 DB `kras_v11_dryrun_20260429`
- 방법: V1.1 overlay (`backend/`+`engine/`) 를 `/tmp/v11app` 으로 docker cp, `services.new_construction_excel_runner.run_excel` → `services.new_construction_zip_builder.build_zip` 직접 호출
- 환경변수: `DATABASE_URL=…/kras_v11_dryrun_20260429`, `GENERATED_DOCUMENTS_DIR=/tmp/v11_2b5c_out`
- 사전 작업: `document_generation_jobs.status='pending'`, `generated_document_packages.status='pending', zip_file_path=NULL`, `generated_document_files.status='pending'` 으로 리셋

| Rule | run-excel generated/failed | zip entries | zip size (B) | path-safe | openpyxl all OK | package.status | zip_file_path 저장 |
|---|---|---|---|---|---|---|---|
| RULE_NEW_WORKER       | 5/0 | 5 | 35,655 | ✅ | 5/5 | ready | `/tmp/v11_2b5c_out/project_1/package_5/package_5.zip` |
| RULE_EQUIPMENT_INTAKE | 6/0 | 6 | 47,183 | ✅ | 6/6 | ready | `/tmp/v11_2b5c_out/project_1/package_6/package_6.zip` |
| RULE_DAILY_TBM        | 4/0 | 4 | 29,117 | ✅ | 4/4 | ready | `/tmp/v11_2b5c_out/project_1/package_7/package_7.zip` |

ZIP 내부 파일명 (path separator / `..` / 비-xlsx 0건 — 모두 safe):

- RULE_NEW_WORKER: `안전보건교육_교육일지.xlsx`, `보호구_지급_대장.xlsx`, `출근부_배치부.xlsx`, `보호구_수령_확인서.xlsx`, `문서_첨부_리스트.xlsx`
- RULE_EQUIPMENT_INTAKE: `건설_장비_반입_신청서.xlsx`, `건설_장비_보험_정기검사증_확인서.xlsx`, `건설_장비_일일_사전_점검표.xlsx`, `운전원_자격증_확인서.xlsx`, `문서_첨부_리스트.xlsx`, `사진_첨부_시트.xlsx`
- RULE_DAILY_TBM: `TBM_일지.xlsx`, `작업_전_안전_확인서.xlsx`, `출근부.xlsx`, `사진_첨부_시트.xlsx`

`ZipFile.testzip()` 결과: 3/3 zip 모두 `None` (CRC 무결성 OK).

종료 후 `/tmp/v11app`, `/tmp/v11_2b5c_out`, `/tmp/smoke_zip.py`, `/tmp/v11_2b5c_smoke.json` (호스트·컨테이너 양쪽) 모두 정리.

---

## 6. 검증

| # | 항목 | 결과 |
|---|---|---|
| 1 | `git status --short` 시작 시 | clean ✅ |
| 2 | py_compile `new_construction_zip_builder.py` | OK ✅ |
| 3 | py_compile `new_construction_repository.py` | OK ✅ |
| 4 | py_compile `new_construction.py` (schemas) | OK ✅ |
| 5 | py_compile `new_construction.py` (routers) | OK ✅ |
| 6 | `form_registry.list_supported_forms()` | 87 ✅ |
| 7 | `supplementary_registry.list_supplemental_types()` | 10 ✅ |
| 8 | builder 파일 변경 | 없음 (Stage 2B-5B-Fix 이후 git diff 0건) ✅ |
| 9 | `document_catalog.yml` / `form_registry.py` / `supplementary_registry.py` | 변경 없음 ✅ |
| 10 | `StreamingResponse` / `FileResponse` import / 사용 | 없음 (`grep` 0건) ✅ |
| 11 | 다운로드 API (`/download`) 추가 | 없음 ✅ |
| 12 | equipment 마스터 (`FROM equipment` / `INSERT INTO equipment` / `UPDATE equipment`) 접근 | 없음, `project_equipment` 만 사용 ✅ |
| 13 | 운영 DB(`kras`) public 테이블 수 | 30 (V1.1 미적용 그대로) ✅ |
| 14 | 운영 DB DDL / 컨테이너 restart | 없음 ✅ |
| 15 | UI / frontend 변경 | 없음 ✅ |
| 16 | background worker / cron / scheduler | 없음 ✅ |
| 17 | 비밀값 / connection string 노출 | 없음 ✅ |

---

## 7. 변경 파일

- 신규: `backend/services/new_construction_zip_builder.py`
- 수정: `backend/repositories/new_construction_repository.py` (+`update_document_package_zip_ready`)
- 수정: `backend/schemas/new_construction.py` (+`DocumentPackageZipBuildResponse`)
- 수정: `backend/routers/new_construction.py` (+`POST …/document-packages/{package_id}/build-zip`)
- 신규(보고서): `docs/reports/v1_1_stage2b5c_zip_builder_live_smoke.md`

migration / catalog / registry / 개별 builder / `main.py` / `db.py` / `projects.py` / `form_export.py`: **변경 없음**.

---

## 8. 후속 권장

- 다운로드 endpoint (`StreamingResponse` 또는 사전서명 URL) 는 별도 단계 (Stage 2B-5D 또는 2B-6) 에서 권한·감사 로깅 포함하여 추진.
- 운영 DB 0013~0023 마이그레이션 적용은 별도 게이트 유지.
- 격리 DB `kras_v11_dryrun_20260429`: smoke 데이터 ready 상태 유지. 다음 dry-run 시 TEMPLATE 재클론 또는 사용자 승인 후 DROP 권고.

# V1.1 Stage 2B-5A — Excel Runner 격리 DB 라이브 Smoke 보고서

작성일: 2026-04-29 (KST)
대상 HEAD: `c86fe15` (Stage 2B-5A — Excel runner 추가)
판정: **PASS**

---

## 1. 실행 환경

- 위치: 앱서버 `1.201.176.236`
- 방법: `risk-assessment-api` 컨테이너에 V1.1 신규 코드를 `/tmp/v11app` 으로 오버레이 후 FastAPI `TestClient` 로 in-process 호출
- DB: 격리 dry-run DB `kras_v11_dryrun_20260429` (`risk-assessment-db` 컨테이너 내부, 운영 DB 아님)
- 환경변수: `DATABASE_URL` 격리 DB 직결, `PYTHONPATH=/tmp/v11app/backend:/tmp/v11app`, `GENERATED_DOCUMENTS_DIR=/tmp/v11_smoke_out`
- 운영 컨테이너: restart/config 변경 없음
- 종료 후 `/tmp/v11app`, `/tmp/v11_smoke_out`, `/tmp/v11_smoke.tgz` 모두 정리 완료

## 2. 운영 DB 무변경 확인

| 항목 | 운영 DB(`kras`) 상태 |
|---|---|
| public 테이블 수 | 29 (Stage 2B-5A 진행 전후 동일, 본 단계에서 DDL 미실행) |
| `project_equipment` | 미존재 (V1.1 미적용) |
| `generated_document_files` | 미존재 (V1.1 미적용) |
| DDL 실행 | 없음 |
| 운영 컨테이너 restart | 없음 |

## 3. 격리 DB Smoke 결과 (3 Rules)

| Rule | expected file_count | generate file_count | run-excel status | ready / failed | DB job.status | DB package.status |
|---|---|---|---|---|---|---|
| RULE_NEW_WORKER       | 5 | 5 | completed | 5 / 0 | completed | ready |
| RULE_EQUIPMENT_INTAKE | 6 | 6 | completed | 6 / 0 | completed | ready |
| RULE_DAILY_TBM        | 4 | 4 | completed | 4 / 0 | completed | ready |

총 15 파일 생성, 0건 실패.

## 4. 산출물 검증

- 저장 위치: `/tmp/v11_smoke_out/project_1/package_{5,6,7}/{file_id}_{display_name}.xlsx` 15건 — 격리 디렉터리 외부 누설 없음
- 파일명 sanitize: 한글/영숫자/`._-` 외 문자 제거, 길이 80자 이내
- mime_type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` 일관 적용
- file_size: 모두 > 0 (각 파일별 builder 출력 크기 그대로 기록)
- openpyxl 열림 검증: 각 패키지 상위 2건 read_only 모드 로드 성공 (총 6건)

## 5. Builder 호출 기준

- 핵심서류 (`form_type` 보유): `engine.output.form_registry.build_form_excel(form_type, form_data)` 호출
  - `get_form_spec` 의 `required_fields` 누락 항목은 빈 문자열, `repeat_field` / `extra_list_fields` 누락 항목은 빈 list 로 사전 보충
- 부대서류 (`supplemental_type` 보유): `engine.output.supplementary_registry.build_supplemental_excel` 호출
  - 동일하게 `required_fields` / `repeat_field` 빈값 보충
- form_data 공통 키: `project_id, project_name, title, site_name, construction_type, site_address, site_manager_name, safety_manager_name, rule_id, package_id, document_display_name, generated_at`
- subject 추가 키: worker(`worker_name, trade, first_work_date`) / equipment(`equipment_name, equipment_type, entry_date`) / date(`target_date`)
- 개인정보 미포함: 주민/외국인등록번호·전화번호·건강정보 없음

## 6. Repository 추가 함수

- `get_package_for_job(job_id)`
- `list_files_for_package(package_id)` — `list_document_files` 위임
- `update_document_file_ready(file_id, file_path, file_size, mime_type, file_name=None)`
- `update_document_file_failed(file_id, error_message)` — files 테이블에 `error_message` 컬럼 부재 → status='failed' 만 갱신, 사유는 router 응답 / job.error_message 에 보관
- `update_document_job_status(job_id, status, *, started=False, finished=False, error_message=None)`
- `update_document_package_status(package_id, status)`

## 7. Schema 추가

- `DocumentFileRunResult` — file_id / status / form_type / supplemental_type / file_path / file_size / error_message
- `DocumentJobRunResponse` — job_id / package_id / status / generated_count / failed_count / files

## 8. Router 추가

- `POST /api/v1/new-construction/document-jobs/{job_id}/run-excel`
- 오류 코드:
  - 404: job_not_found / package_not_found
  - 400: no_files
  - 409: invalid_status (이미 completed/running 등) — 응답에 `current_status` 포함
- builder 실패 시 500 미반환, `status='failed'` + 상세는 `error_message` 로 응답

## 9. 정적 검증 (12항목)

| # | 검증 | 결과 |
|---|---|---|
| 1 | git status --short | clean (smoke 종료 후) ✅ |
| 2 | py_compile new_construction_excel_runner.py | OK ✅ |
| 3 | py_compile new_construction_repository.py | OK ✅ |
| 4 | py_compile new_construction.py (schemas) | OK ✅ |
| 5 | py_compile new_construction.py (routers) | OK ✅ |
| 6 | form_registry 87건 로드 | 87 ✅ |
| 7 | supplementary_registry 10건 로드 | 10 ✅ |
| 8 | rule generate 기존 smoke 유지 | 3 rules 정상 동작 ✅ |
| 9 | zip/download guard (zipfile / StreamingResponse / FileResponse 미도입) | 신규 코드에 import 없음 ✅ |
| 10 | UI 변경 없음 | 신규 코드 변경 없음 ✅ |
| 11 | document_catalog.yml / form_registry.py / supplementary_registry.py 변경 없음 | git diff 없음 ✅ |
| 12 | 기존 /api/projects 변경 없음 / 운영 equipment 마스터 미접근 | 신규 코드는 `project_equipment` 만 조회 ✅ |

## 10. 후속 권장

- 격리 DB `kras_v11_dryrun_20260429`: smoke 데이터 잔존 (project_id=1 기준 packages 7, files 31). 다음 dry-run 시 TEMPLATE 재클론 또는 사용자 승인 후 DROP.
- ZIP 패키징 및 다운로드 endpoint 는 후속 단계(Stage 2B-5B 또는 2B-6)에서 분리 추진.
- 운영 DB 에 0013~0023 마이그레이션 적용 단계는 별도 게이트 유지.

---

## 11. 변경 파일

- 신규: `backend/services/new_construction_excel_runner.py`
- 수정: `backend/repositories/new_construction_repository.py`
- 수정: `backend/schemas/new_construction.py`
- 수정: `backend/routers/new_construction.py`
- migration / catalog / registry / 개별 builder / main.py / db.py / projects.py / form_export.py: 변경 없음

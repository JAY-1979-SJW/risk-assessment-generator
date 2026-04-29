# V1.1 Stage 2B-5B — Rule 패키지 Excel 자동 품질검토 보고서

작성일: 2026-04-29 (KST)
대상 HEAD: `a74a7d5` (Stage 2B-5A 보고서 직후, 코드 변경 없음)
대상 DB: 격리 dry-run `kras_v11_dryrun_20260429` (운영 DB 무관)
점검 도구: openpyxl 3.1.5 (`risk-assessment-api` 컨테이너 내부)
판정: **PASS (with WARN)** — 15/15 파일 모두 출력 가능, 6건 paperSize 미명시·8건 의도된 6pt 간격행만 권고사항.

---

## 1. 전체 요약

| 항목 | 값 |
|---|---|
| 대상 파일 | 15 |
| PASS | 9 |
| WARN | 6 |
| FAIL | 0 |
| openpyxl load 실패 | 0 |
| DB metadata 불일치 | 0 |
| 빈 시트 / 빈 문서 | 0 |
| 파일 누락 | 0 |
| 운영 DB 변경 | 없음 (테이블 30개 유지, `generated_document_files` / `project_equipment` 미존재 그대로) |

Rule별 결과:

| Rule | 기대 / 실제 | PASS | WARN | FAIL |
|---|---|---|---|---|
| RULE_NEW_WORKER       | 5 / 5 | 3 | 2 | 0 |
| RULE_EQUIPMENT_INTAKE | 6 / 6 | 4 | 2 | 0 |
| RULE_DAILY_TBM        | 4 / 4 | 2 | 2 | 0 |

> WARN 사유는 동일 builder 6종에서 `paperSize` 가 빈 값(엑셀 기본값)으로 저장된 점, 그리고 8개 파일에서 6pt 짜리 간격행이 반복되는 점이며 모두 출력 자체는 가능하다(상세 4·5·6장).

---

## 2. Rule별 파일 목록

### RULE_NEW_WORKER (package_id=5, job_id=5, status=ready/completed)

| file_id | display_name | form_type / supp | file_path | size | 판정 |
|---|---|---|---|---|---|
| 17 | 안전보건교육 교육일지 | form: education_log | `/tmp/v11_2b5b_out/project_1/package_5/17_안전보건교육_교육일지.xlsx` | 7,642 | WARN |
| 18 | 보호구 지급 대장 | form: ppe_issuance_ledger | `…/18_보호구_지급_대장.xlsx` | 6,847 | WARN |
| 19 | 출근부/배치부 | supp: attendance_roster | `…/19_출근부_배치부.xlsx` | 7,522 | PASS |
| 20 | 보호구 수령 확인서 | supp: ppe_receipt_confirmation | `…/20_보호구_수령_확인서.xlsx` | 8,254 | PASS |
| 21 | 문서 첨부 리스트 | supp: document_attachment_list | `…/21_문서_첨부_리스트.xlsx` | 8,395 | PASS |

### RULE_EQUIPMENT_INTAKE (package_id=6, job_id=6, status=ready/completed)

| file_id | display_name | form_type / supp | file_path | size | 판정 |
|---|---|---|---|---|---|
| 22 | 건설 장비 반입 신청서 | form: construction_equipment_entry_request | `…/22_건설_장비_반입_신청서.xlsx` | 6,873 | WARN |
| 23 | 건설 장비 보험·정기검사증 확인서 | form: equipment_insurance_inspection_check | `…/23_건설_장비_보험_정기검사증_확인서.xlsx` | 9,493 | WARN |
| 24 | 건설 장비 일일 사전 점검표 | form: construction_equipment_daily_checklist | `…/24_건설_장비_일일_사전_점검표.xlsx` | 9,767 | PASS |
| 25 | 운전원 자격증 확인서 | supp: equipment_operator_qualification_check | `…/25_운전원_자격증_확인서.xlsx` | 8,039 | PASS |
| 26 | 문서 첨부 리스트 | supp: document_attachment_list | `…/26_문서_첨부_리스트.xlsx` | 8,395 | PASS |
| 27 | 사진 첨부 시트 | supp: photo_attachment_sheet | `…/27_사진_첨부_시트.xlsx` | 7,787 | PASS |

### RULE_DAILY_TBM (package_id=7, job_id=7, status=ready/completed)

| file_id | display_name | form_type / supp | file_path | size | 판정 |
|---|---|---|---|---|---|
| 28 | TBM 일지 | form: tbm_log | `…/28_TBM_일지.xlsx` | 6,792 | WARN |
| 29 | 작업 전 안전 확인서 | form: pre_work_safety_check | `…/29_작업_전_안전_확인서.xlsx` | 9,368 | WARN |
| 30 | 출근부 | supp: attendance_roster | `…/30_출근부.xlsx` | 7,522 | PASS |
| 31 | 사진 첨부 시트 | supp: photo_attachment_sheet | `…/31_사진_첨부_시트.xlsx` | 7,787 | PASS |

> 주의: Stage 2B-5A 종료 시 `/tmp/v11_smoke_out` 가 정리되어 본 단계는 격리 DB 의 동일 패키지(jobs/packages/files 행) 를 `pending` 으로 리셋한 뒤 동일 builder 로 재생성하여 검토했다. 재생성 후 file_size·status·mime_type 모두 Stage 2B-5A 보고서와 동일하게 일치했다. 본 단계 종료 후 `/tmp/v11_2b5b_out`, 컨테이너 내 overlay, audit JSON 모두 삭제 완료.

---

## 3. 품질 점검 결과 (15/15)

| 점검 | 결과 |
|---|---|
| 파일 존재 / `.xlsx` 확장자 / size > 0 | 15/15 ✅ |
| openpyxl `load_workbook(read_only=False)` | 15/15 ✅ |
| 시트 ≥ 1 (모두 단일 시트) | 15/15 ✅ |
| `generated_document_files.status='ready'` | 15/15 ✅ |
| DB `file_size` ↔ 실제 stat 일치 | 15/15 ✅ |
| `mime_type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | 15/15 ✅ |
| `generated_document_packages.status='ready'` | 3/3 ✅ |
| `document_generation_jobs.status='completed'` | 3/3 ✅ |
| 빈 시트 / 완전 빈 문서 | 0건 ✅ |
| 긴 텍스트(>30자) `wrap_text` 미설정 | 0건 ✅ |
| 좁은 컬럼(width<4) | 0건 ✅ |
| `orientation` 설정 | 15/15 ✅ (모두 portrait) |
| `fitToWidth=1` (페이지 가로 1장) | 15/15 ✅ |
| 반복 헤더 `print_title_rows` | 14/15 (file 22 만 미설정) |
| `paperSize=9 (A4)` 명시 | 9/15 (나머지 6건은 `fitToPage=true` 만 설정) |
| `print_area` 명시 | 0/15 (모두 미지정 — fitToPage 동작에는 영향 없음) |

---

## 4. 문제 파일 상세 (WARN 6건)

공통 패턴: 핵심서류 builder 6종이 `page_setup.fitToWidth=1` + `sheet_properties.pageSetUpPr.fitToPage=true` 조합으로 페이지 폭을 강제하지만 `page_setup.paperSize` 자체는 비어 있다. 이 경우 Excel 은 사용자 환경 기본 용지(국내 일반: A4) 로 출력되므로 실제 인쇄에는 보통 문제 없으나, 한국어 office 가 아닌 환경 또는 PDF 변환 시 Letter 로 떨어질 위험이 있다.

| file_id | builder | 증상 | 권장 조치 |
|---|---|---|---|
| 17 | education_log | paperSize 미설정 (fitToPage=true) | builder 의 `page_setup.paperSize = 9` 추가 (별도 단계) |
| 18 | ppe_issuance_ledger | paperSize 미설정 | 동일 |
| 22 | construction_equipment_entry_request | paperSize 미설정, `print_title_rows` 도 없음 | paperSize=9 + 반복 헤더 1~N행 지정 |
| 23 | equipment_insurance_inspection_check | paperSize 미설정 (`print_title_rows=$1:$2` 만 있음) | paperSize=9 |
| 28 | tbm_log | paperSize 미설정 | paperSize=9 |
| 29 | pre_work_safety_check | paperSize 미설정 | paperSize=9 |

부수 점검:
- 8개 부대서류 파일(19/20/21/25/26/27/30/31) 의 row_height 6pt 행은 row 3·7·11·15… 패턴으로 정확히 반복되어 시각적 간격행(spacer) 의도가 명확하다. 빈 셀 영역에만 적용되며 텍스트가 들어간 행은 모두 정상 높이 → **결함 아님 (의도된 디자인)**.
- 병합셀 수는 24~170 범위로 양식별로 적절. 긴 문구가 들어간 셀은 모두 wrap_text 적용됨.

---

## 5. 사람이 직접 다운로드해서 볼 대표 샘플 (risk_assessment 제외)

> 양식 폭/구성/서명·반복부 모두 다른 6건을 추천한다. 각 builder 카테고리(form/supp) 와 페이지 설정(완전 A4 vs fitToPage) 을 골고루 포함.

1. **file_id 17 — 안전보건교육 교육일지** (`education_log`, RULE_NEW_WORKER) — 기본정보 + 교육내용 + 명단 반복부 검증용
2. **file_id 22 — 건설 장비 반입 신청서** (`construction_equipment_entry_request`, RULE_EQUIPMENT_INTAKE) — 신청부 / paperSize 미설정 영향 육안 확인
3. **file_id 24 — 건설 장비 일일 사전 점검표** (`construction_equipment_daily_checklist`, RULE_EQUIPMENT_INTAKE) — merged 170건·세로 항목 다수 양식 가독성 확인
4. **file_id 27 — 사진 첨부 시트** (`photo_attachment_sheet`, RULE_EQUIPMENT_INTAKE) — 사진 슬롯 레이아웃·간격행 시각 확인
5. **file_id 20 — 보호구 수령 확인서** (`ppe_receipt_confirmation`, RULE_NEW_WORKER) — 서명란 row_height 적정성 확인
6. **file_id 28 — TBM 일지** (`tbm_log`, RULE_DAILY_TBM) — 일자/현장 컨텍스트 채움 확인
7. (선택) **file_id 21 — 문서 첨부 리스트** (`document_attachment_list`) — 첨부 항목 텍스트 길이/줄바꿈 확인

---

## 6. 다음 단계 제안

| 항목 | 권고 |
|---|---|
| ZIP 생성 전 보정 | **권장**. 위 6개 builder 에 `page_setup.paperSize = 9` 한 줄 추가하면 모든 파일이 환경 무관하게 A4 로 떨어진다. file 22 는 `print_title_rows` 도 지정 권장. (별도 작업 단계로 분리 — 본 단계는 검토만) |
| 다운로드 API 진행 | **가능**. 현재 출력 품질로도 다운로드/공유는 결함 없음. paperSize 보정과 병행/후행 둘 다 안전. |
| builder 개별 수정 | 위 6종만 minimal patch. 부대서류(supp) 6종은 모두 `paperSize=9` 이미 명시되어 변경 불필요. |
| 격리 DB | `kras_v11_dryrun_20260429` 그대로 유지. 추후 dry-run 시 TEMPLATE 재클론 또는 사용자 승인 후 DROP 권고. |
| 운영 DB 마이그레이션 | 별도 게이트 유지 — 본 단계 무관. |

---

## 7. 검증 (변경 없음)

| 항목 | 결과 |
|---|---|
| 코드 변경 | 없음 ✅ |
| builder 변경 | 없음 ✅ |
| API 변경 | 없음 ✅ |
| migration / DDL | 없음 ✅ |
| `document_catalog.yml` / `form_registry.py` / `supplementary_registry.py` | 변경 없음 ✅ |
| 운영 DB(`kras`) | public 테이블 30 유지, V1.1 테이블 미존재 그대로 ✅ |
| 운영 컨테이너 restart | 없음 ✅ |
| `git diff --stat` | 본 보고서 1건만 추가 예정 ✅ |
| 비밀값 / connection string | 보고서 미포함 ✅ |
| 임시 산출물 | 컨테이너·서버 측 overlay/audit JSON/xlsx 모두 정리 완료 ✅ |

---

## 8. 부록 — 점검 절차

1. `/tmp/v11app` overlay (backend + engine, V1.1 코드) 를 `risk-assessment-api` 컨테이너에 docker cp.
2. 격리 DB `kras_v11_dryrun_20260429` 의 `document_generation_jobs` / `generated_document_packages` / `generated_document_files` 행 3·3·15 건을 `pending` 으로 리셋(file_path/file_size NULL).
3. `services.new_construction_excel_runner.run_excel(job_id)` 를 컨테이너 내부에서 직접 호출하여 동일 builder 로 15 파일 재생성.
4. `openpyxl.load_workbook` 으로 각 파일을 read/write 모드 로드 후 page_setup, page_margins, print_area, print_title_rows, merged_cells, row/column dimensions, cell value/wrap_text, 본문 키워드, sheet 비어있음 여부를 수집.
5. DB `file_size` ↔ 실제 stat, status, mime_type 교차 검증.
6. 결과 JSON 을 컨테이너 → 호스트 → 로컬로 회수 후 본 보고서 작성. 컨테이너·서버·로컬 임시파일 전부 삭제.

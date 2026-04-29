# V1.1 Stage 2B-5B-Fix — Excel paperSize A4 명시 보정 보고서

작성일: 2026-04-29 (KST)
대상 HEAD: `91dc8fd` (Stage 2B-5B 보고서 직후) → 본 단계로 +6 line patch.
판정: **PASS** — 6/6 핵심서류 builder 의 `page_setup.paperSize` 가 9(A4) 로 명시되어 Stage 2B-5B 의 paperSize WARN 6건이 0건으로 해소되었다.

---

## 1. 보정 대상 (Stage 2B-5B WARN 6건)

| # | form_type | 수정 파일 | 수정 위치 |
|---|---|---|---|
| 1 | education_log                          | `engine/output/education_log_builder.py`                          | line 338 (`# 인쇄 설정` 블록) |
| 2 | ppe_issuance_ledger                    | `engine/output/ppe_issuance_ledger_builder.py`                    | line 152 (`_finalize_sheet`) |
| 3 | construction_equipment_entry_request   | `engine/output/construction_equipment_entry_request_builder.py`   | line 159 (`_finalize_sheet`) |
| 4 | equipment_insurance_inspection_check   | `engine/output/equipment_insurance_inspection_check_builder.py`   | line 199 (`_apply_print_settings`) |
| 5 | tbm_log                                | `engine/output/tbm_log_builder.py`                                | line 232 (페이지 설정 블록) |
| 6 | pre_work_safety_check                  | `engine/output/pre_work_safety_check_builder.py`                  | line 230 (`_apply_print_settings`) |

각 builder 가 독립 page_setup 블록을 갖는 구조라 공통 helper 도입 없이 파일별 1줄씩만 추가했다.

---

## 2. 수정 내용

- 추가된 한 줄: `ws.page_setup.paperSize = 9  # A4`
- 위치: 기존 `ws.page_setup.orientation = "portrait"` 직전.
- **변경하지 않은 항목**: orientation, fitToPage, fitToWidth, fitToHeight, page_margins, print_area, print_title_rows, row_height, column_width, 병합셀, 문구, 데이터 구조, 서식.
- 합계 변경: 6 파일 / +6 라인 / -0 라인.

```diff
+    ws.page_setup.paperSize  = 9  # A4
     ws.page_setup.orientation = "portrait"
     ws.page_setup.fitToPage   = True
     ws.page_setup.fitToWidth  = 1
```

---

## 3. 재검토 결과

검증 방법: 수정된 6개 builder 를 직접 호출(`build_form_excel`) → 반환 bytes 를 `openpyxl.load_workbook` 로 적재 → `ws.page_setup.paperSize` 확인.

| form_type | paperSize | A4(=9) | fitToWidth | orientation | load |
|---|---|---|---|---|---|
| education_log                        | 9 | ✅ | 1 | portrait | OK |
| ppe_issuance_ledger                  | 9 | ✅ | 1 | portrait | OK |
| construction_equipment_entry_request | 9 | ✅ | 1 | portrait | OK |
| equipment_insurance_inspection_check | 9 | ✅ | 1 | portrait | OK |
| tbm_log                              | 9 | ✅ | 1 | portrait | OK |
| pre_work_safety_check                | 9 | ✅ | 1 | portrait | OK |

이전 Stage 2B-5B 에서 PASS 였던 9개 부대서류 builder 는 본 단계에서 변경 없음 (이미 paperSize=9 명시되어 있음).

| 항목 | Stage 2B-5B | Stage 2B-5B-Fix |
|---|---|---|
| total | 15 | 15 |
| PASS | 9 | **15** |
| WARN | 6 | **0** |
| FAIL | 0 | 0 |
| paperSize WARN | 6 | **0** |
| openpyxl load | 15/15 | 15/15 (수정 6건 + 미변경 9건) |

> 격리 DB 전체 재실행은 본 단계에서 생략 가능 — runner 는 builder 가 반환한 xlsx bytes 를 그대로 디스크/DB 에 저장하므로, builder 단위 결과가 바뀌면 runner 출력도 동일하게 바뀐다 (Stage 2B-5B 에서 runner 무결성 이미 검증 완료, file_size·mime·status 일치 확인).

---

## 4. 검증

| 항목 | 결과 |
|---|---|
| `py_compile` 6개 builder | OK ✅ |
| `form_registry.list_supported_forms()` | 87 ✅ |
| `supplementary_registry.list_supplemental_types()` | 10 ✅ |
| API 변경 (`backend/routers/`, `backend/services/`, `backend/schemas/`, `backend/repositories/`) | 변경 없음 ✅ (`git diff --stat` 에 backend 0건) |
| DB DDL / migration | 없음 ✅ |
| 운영 DB(`kras`) | public 테이블 30 유지, V1.1 테이블 미존재 그대로 ✅ |
| ZIP / download guard (`zipfile`, `StreamingResponse`, `FileResponse` 추가) | 없음 ✅ |
| `document_catalog.yml` / `form_registry.py` / `supplementary_registry.py` | 변경 없음 ✅ |
| UI / frontend | 변경 없음 ✅ |
| `git diff --stat` | 6 builder, +6/-0 (다른 파일 0건) ✅ |
| 비밀값 / connection string 노출 | 없음 ✅ |

---

## 5. 다음 단계 제안

- ZIP 패키징 / 다운로드 endpoint 진행 가능 — 출력 품질 PASS 이므로 builder 추가 보정 필요 없음.
- 운영 DB 0013~0023 마이그레이션 적용은 별도 게이트 유지.
- 격리 DB `kras_v11_dryrun_20260429` 는 추후 dry-run 시 TEMPLATE 재클론 또는 사용자 승인 후 DROP 권고 (기존 정책 유지).

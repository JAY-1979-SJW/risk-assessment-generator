# 굴착 작업계획서 Builder 구현 계획 v1

**작성일**: 2026-04-24  
**근거**: `docs/design/workplan_excel_layout_lock.md`  
**대상 파일**: `engine/output/workplan_builder.py`

---

## 1. 레이아웃 잠금 문서 재확인

### 1.1 기본 상수

| 항목 | 확정값 |
|------|-------|
| SHEET_NAME | `작업계획서` |
| SHEET_HEADING | `굴착 작업계획서` |
| SHEET_SUBTITLE | `「산업안전보건기준에 관한 규칙」 제38조·제82조에 따른 작업계획서` |
| TOTAL_COLS | 8 |
| MAX_STEPS | 10 |
| 인쇄영역 | A1:H29 |

### 1.2 열 너비

| 열 | 너비 |
|----|------|
| A | 14 |
| B~G | 12 |
| H | 10 |

### 1.3 Row 구조 확인

| 행 범위 | 내용 | 높이 |
|--------|------|------|
| Row 1 | 제목 (A1:H1) | 28pt |
| Row 2 | 부제 (A2:H2) | 16pt |
| Row 3 | 사업장명/현장명 | 20pt |
| Row 4 | 작업위치 (전폭) | 20pt |
| Row 5 | 작업일자/작업책임자 | 20pt |
| Row 6 | 도급업체/작성일 | 20pt |
| Row 7 | 섹션헤더 (법정기재사항) | 18pt |
| Row 8 | 굴착의 방법 | 40pt |
| Row 9 | 흙막이 지보공 및 방호망 | 40pt |
| Row 10 | 사용 기계 종류 및 능력 | 30pt |
| Row 11 | 토석 처리 방법 | 30pt |
| Row 12 | 용수 처리 방법 | 30pt |
| Row 13 | 작업 방법 | 40pt |
| Row 14 | 긴급조치 계획 | 40pt |
| Row 15 | 섹션헤더 (작업단계별 안전조치) | 18pt |
| Row 16 | 표 헤더 | 18pt |
| Row 17~26 | 안전조치 10행 | 30pt |
| Row 27 | 섹션헤더 (확인및서명) | 18pt |
| Row 28 | 서명 라벨행 | 20pt |
| Row 29 | 서명 공란 / 작성일 | 40pt |

---

## 2. form_data 필드 매핑

### 2.1 메타 영역 (Row 3~6)

| form_data 필드 | 라벨 | 위치 | 비고 |
|--------------|------|------|------|
| `site_name` | 사업장명 | Row 3 좌: A3 라벨, B3:D3 값 | [관행] |
| `project_name` | 현장명 | Row 3 우: E3 라벨, F3:H3 값 | [관행] (lock의 work_type 위치) |
| `work_location` | 작업 위치 | Row 4: A4 라벨, B4:H4 값 (전폭) | [관행] |
| `work_date` | 작업 일자 | Row 5 좌: A5 라벨, B5:D5 값 | [관행] (단일 날짜 또는 기간 문자열) |
| `supervisor` | 작업 책임자 | Row 5 우: E5 라벨, F5:H5 값 | [관행] |
| `contractor` | 도급업체 | Row 6 좌: A6 라벨, B6:D6 값 | [관행] |
| — | 작성일 | Row 6 우: E6 라벨, F6:H6 값 | 공란 (수기 기입용) |

> lock.md의 `work_type`→`project_name`, `prepared_by`→`contractor`, `work_date_start~end`→`work_date` 단일 필드로 변경

### 2.2 법정 기재 사항 (Row 8~14)

| form_data 필드 | 라벨 | 위치 | 법조 |
|--------------|------|------|------|
| `excavation_method` | 굴착의 방법 | Row 8: A8 라벨, B8:H8 값 | 제82조 제1항 제1호 |
| `earth_retaining` | 흙막이 지보공 및 방호망 | Row 9: A9 라벨, B9:H9 값 | 제82조 제1항 제2호 |
| `excavation_machine` | 사용 기계 종류 및 능력 | Row 10: A10 라벨, B10:H10 값 | 제82조 제1항 제3호 |
| `soil_disposal` | 토석 처리 방법 | Row 11: A11 라벨, B11:H11 값 | 제82조 제1항 제4호 |
| `water_disposal` | 용수 처리 방법 | Row 12: A12 라벨, B12:H12 값 | 제82조 제1항 제5호 |
| `work_method` | 작업 방법 | Row 13: A13 라벨, B13:H13 값 | 제38조 제2항 |
| `emergency_measure` | 긴급조치 계획 | Row 14: A14 라벨, B14:H14 값 | 제38조 제2항 |

### 2.3 안전조치 반복행 (Row 17~26)

| safety_steps 필드 | 열 위치 | 렌더링 |
|-----------------|--------|-------|
| `step_no` | A (AUTO 채번) | ✓ |
| `task_step` | B:C (작업 단계) | ✓ |
| `hazard` | D:F (위험 요인) | ✓ |
| `safety_measure` | G:H (안전 조치) | ✓ |
| `responsible_person` | — | **미렌더링** (레이아웃 칼럼 없음) |
| `note` | — | **미렌더링** (레이아웃 칼럼 없음) |

> `responsible_person` · `note` 는 입력은 허용하되 출력 없음 (4칼럼 레이아웃 제약)

### 2.4 서명 영역 (Row 28~29)

| 위치 | 내용 | 비고 |
|------|------|------|
| A28:B28 | 라벨 "작성자" | 배경색 적용 |
| C28:D28 | 공란 | 수기 서명 |
| E28:F28 | 라벨 "검토자/확인자" | 배경색 적용 |
| G28:H28 | 공란 | 수기 서명 |
| A29:B29 | 공란 | 서명 공간 |
| C29:D29 | 공란 | 서명 공간 |
| E29:F29 | 공란 | 서명 공간 |
| G29 | 라벨 "작성일" | 배경색 적용 |
| H29 | `sign_date` 값 (없으면 공란) | — |

---

## 3. 함수 설계

```
build_excavation_workplan_excel(form_data) -> bytes
  └─ render_excavation_workplan_sheet(ws, form_data) -> None
       ├─ _apply_col_widths(ws)
       ├─ _write_title(ws, row) -> int          # Row 1~2 → returns 3
       ├─ _write_meta_block(ws, row, data) -> int   # Row 3~6 → returns 7
       ├─ _write_legal_items(ws, row, data) -> int  # Row 7~14 → returns 15
       ├─ _write_step_table(ws, row, steps) -> int  # Row 15~26 → returns 27
       └─ _write_confirmation(ws, row, data) -> int # Row 27~29
```

---

## 4. 제한 사항

| 항목 | 제한 |
|------|------|
| 최대 안전조치 행 | 10행 고정. safety_steps > 10 시 10개까지만 렌더링 (나머지 무시) |
| `responsible_person` | 입력 허용, 출력 없음 (레이아웃 제약) |
| `note` | 입력 허용, 출력 없음 (레이아웃 제약) |
| 작업 유형 | 굴착 1종만 구현 (차량계·터널·해체·중량물 제외) |
| 서명란 | 항상 공란 (수기 서명 전용) |
| 작성일 (Row 6) | 항상 공란 (form_data 대응 필드 없음, 수기 기입용) |
| `sign_date` | 입력 시 H29에 표시; 없으면 공란 |

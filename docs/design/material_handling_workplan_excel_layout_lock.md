# 차량계 하역운반기계 작업계획서 Excel 레이아웃 확정 (LOCK) — 4단계

**작성일**: 2026-04-24  
**상태**: LOCKED — builder 구현은 이 문서 기준으로만 수행  
**경로**: GEN_INTERNAL — 원본 파일 없음, 조문 기반 설계 + 차량계 건설기계 builder 구조 응용  
**근거**: `material_handling_workplan_source_audit.md`, `material_handling_workplan_law_mapping.md`, `material_handling_workplan_raw_layout_inspection.md`, `workplan_field_matrix.md`  
**법적 근거**: 산업안전보건기준에 관한 규칙 제38조 제1항 제2호 + 제38조 제2항 + 제179조·제180조·제182조

---

## 1. 기본 설정

| 항목 | 확정값 |
|------|-------|
| 시트명 | `차량계하역운반기계작업계획서` |
| 제목 | `차량계 하역운반기계 작업계획서` |
| 부제 | `「산업안전보건기준에 관한 규칙」 제38조 제1항 제2호에 따른 작업계획서` |
| 총 열 수 | **8열 (A~H)** |
| 총 행 수 | **51행** (기본 hazard_items=10, pre_check_items=8 기준) |
| 인쇄 설정 | portrait, fitToWidth=1 |
| 여백 (인치) | left=0.5, right=0.5, top=0.75, bottom=0.75 |
| print_area | A1:H51 |

> 건설기계(49행)보다 2행 증가: 보행자 동선 분리 필드(Row 26) + 지게차 전용 점검 안내행(Row 38)

---

## 2. 열 너비 확정

| 열 | 컬럼 | 너비 | 용도 |
|----|------|------|------|
| A | 1 | **14** | 법정항목 라벨 / 순번 |
| B | 2 | **12** | 값 |
| C | 3 | **12** | 값 |
| D | 4 | **12** | 값 |
| E | 5 | **12** | 값 |
| F | 6 | **12** | 값 / 이상유무 |
| G | 7 | **12** | 값 / 이상유무 |
| H | 8 | **10** | 값 / 비고 |

---

## 3. 셀 단위 행 레이아웃

### 블록 A — 제목 (Row 1~2)

| 행 | 병합 범위 | 내용 | 높이 | 스타일 |
|----|---------|------|------|-------|
| Row 1 | A1:H1 | `차량계 하역운반기계 작업계획서` | 28pt | Font 14pt Bold, 가운데 정렬 |
| Row 2 | A2:H2 | `「산업안전보건기준에 관한 규칙」 제38조 제1항 제2호에 따른 작업계획서` | 16pt | Font 9pt Italic, 가운데 정렬 |

### 블록 B — 메타 영역 (Row 3~6)

**2분할 라벨-값 구조**: 좌(A라벨, B:D값) / 우(E라벨, F:H값)

| 행 | 좌측 라벨 (A) | 좌측 값 (B:D) | 우측 라벨 (E) | 우측 값 (F:H) | 높이 |
|----|------------|------------|------------|------------|------|
| Row 3 | `사업장명` | `site_name` | `현장명` | `project_name` | 20pt |
| Row 4 | `작업 위치` | `work_location` (B:H 전폭) | — | — | 20pt |
| Row 5 | `작업 기간` | `work_date` | `작업 책임자` | `supervisor` | 20pt |
| Row 6 | `도급업체` | `contractor` | `작성자` | `prepared_by` | 20pt |

> Row 4 작업 위치: 라벨 A4, 값 B4:H4 (전폭 병합)

### 블록 C — 법정 기재 사항 (Row 7~14)

**전폭 라벨-값 구조**: 라벨 A, 값 B:H

| 행 | 라벨 (A) | 값 (B:H) | 높이 | 법적 성격 | 근거 조항 |
|----|---------|---------|------|---------|---------|
| Row 7 | [섹션 헤더 A7:H7] `법정 기재 사항 (기준규칙 제38조 제1항 제2호)` | — | 18pt | — | — |
| Row 8 | `기계의 종류` | `machine_type` | 30pt | **LAW** | 제38조 제2항 |
| Row 9 | `기계의 최대 하중` | `machine_max_load` | 30pt | **LAW** | 제38조 제2항 |
| Row 10 | `작업방법` | `work_method` | 40pt | **LAW** | 제38조 제2항 |
| Row 11 | `운전자 성명` | `operator_name` (B:D) / `운전자 자격·면허` 라벨(E) / `operator_license` (F:H) | 20pt | PRAC/EVID | 제80조 |
| Row 12 | `유도자 배치 여부 및 방법` | `guide_worker_required` | 30pt | PRAC | 제182조 |
| Row 13 | `안전속도 제한` | `speed_limit` (B:D) / `기계 수량` 라벨(E) / `machine_count` (F:H) | 20pt | LAW/PRAC | 제180조 |
| Row 14 | `지형·지반 사전조사` | `ground_survey` | 30pt | PRAC | 제38조 제1항 |

> Row 11: A=라벨, B:D=운전자성명, E=라벨, F:H=자격면허 (2분할)  
> Row 13: A=라벨, B:D=속도제한값, E=라벨, F:H=기계수량 (2분할) — 건설기계의 work_radius 대신 machine_count

### 블록 D — 운행경로 (Row 15~22)

**운행경로는 법정 필수 (제38조 제2항) — 텍스트 + 스케치 박스 분리**

| 행 | 내용 | 높이 |
|----|------|------|
| Row 15 | [섹션 헤더 A15:H15] `운행경로 (기준규칙 제38조 제1항 제2호 법정 기재사항)` | 18pt |
| Row 16 | 라벨 A=`운행경로 기술`, 값 B:H=`travel_route_text` | 60pt |
| Row 17 | [스케치 헤더 A17:H17] `운행경로 스케치/개략도 ※ 아래 공간에 수기 기재` | 16pt |
| Row 18~22 | 스케치 박스 (A:H 전폭, 병합 없음, 셀 테두리만, 빈 영역) 각 행 | 30pt 각 |

> Row 18~22: 5행 × 8열. 병합 없이 테두리만. 인쇄 후 수기 도면 작성 가능

### 블록 E — 출입통제·유도자·비상연락망 (Row 23~26)

| 행 | 내용 | 높이 |
|----|------|------|
| Row 23 | [섹션 헤더 A23:H23] `출입통제 · 보행자 동선 · 비상연락망` | 18pt |
| Row 24 | 라벨 A=`출입통제 방법`, 값 B:H=`access_control` | 30pt |
| Row 25 | 라벨 A=`비상연락망`, 값 B:D=`emergency_contact` / 라벨 E=`비상조치`, 값 F:H=`emergency_measure` | 20pt |
| Row 26 | 라벨 A=`보행자 동선 분리`, 값 B:H=`pedestrian_separation` | 30pt |

> Row 26: 건설기계 builder 대비 추가된 행 — 지게차·하역운반기계 사고 다발 원인(보행자 충돌) 대응

### 블록 F — 위험요소 및 안전조치 표 (Row 27~39)

| 행 | 내용 | 높이 |
|----|------|------|
| Row 27 | [섹션 헤더 A27:H27] `위험요소 및 안전조치` | 18pt |
| Row 28 | [표 헤더] A=`순번`, B:D=`위험 요소`, E:H=`안전 조치` | 18pt |
| Row 29~38 | 데이터행 × 10행 (MAX_HAZARD=10) | 30pt 각 |

**표 헤더 셀 범위**:
- `A28` — 순번
- `B28:D28` — 위험 요소 (3열 병합)
- `E28:H28` — 안전 조치 (4열 병합)

**데이터행 (Row 29~38)**:
- `A29` — 순번 (AUTO 채번, 가운데 정렬)
- `B29:D29` — `hazard_items[i].hazard`
- `E29:H29` — `hazard_items[i].safety_measure`

### 블록 G — 작업 전 점검 사항 (Row 39~49)

| 행 | 내용 | 높이 |
|----|------|------|
| Row 39 | [섹션 헤더 A39:H39] `작업 전 점검 사항 (기준규칙 제179조)` | 18pt |
| Row 40 | [표 헤더] A=`순번`, B:E=`점검 항목`, F:G=`이상유무`, H=`비고` | 18pt |
| Row 41~48 | 데이터행 × 8행 (MAX_CHECKS=8) | 25pt 각 |

**표 헤더 셀 범위**:
- `A40` — 순번
- `B40:E40` — 점검 항목 (4열 병합)
- `F40:G40` — 이상유무 (2열 병합)
- `H40` — 비고

**데이터행 (Row 41~48)**:
- `A41` — 순번 (AUTO 채번)
- `B41:E41` — `pre_check_items[i].check_item`
- `F41:G41` — `pre_check_items[i].result`
- `H41` — `pre_check_items[i].note`

**기본 제공 점검 항목 (제179조 기반)**:

| 순번 | 점검 항목 | 근거 |
|------|---------|------|
| 1 | 제동장치 및 조종장치 기능 이상 유무 | 제179조 제1항 제1호 |
| 2 | 하역장치 및 유압장치 기능 이상 유무 | 제179조 제1항 제2호 |
| 3 | 바퀴의 이상 유무 | 제179조 제1항 제3호 |
| 4 | 전조등·후미등·방향지시기 및 경음기 기능 | 제179조 제1항 제4호 |
| 5 | 헤드가드 이상 유무 | 제179조 제1항 제5호 |
| 6 | 백레스트 이상 유무 | 제179조 제1항 제6호 |
| 7 | 안전벨트 착용 상태 | 실무 (지게차 전복 시 안전) |
| 8 | 적재물 고정 상태 | 실무 (낙하 방지) |

### 블록 H — 확인 및 서명 (Row 49~51)

| 행 | 내용 | 높이 |
|----|------|------|
| Row 49 | [섹션 헤더 A49:H49] `확인 및 서명` | 18pt |
| Row 50 | 서명 라벨행 | 20pt |
| Row 51 | 서명 공란 / 작성일 | 36pt |

**Row 50 셀 구조**:
- `A50:B50` — 라벨 "작성자 서명" (Bold, 배경색 F2F2F2)
- `C50:D50` — 공란 (수기 서명)
- `E50:F50` — 라벨 "작업책임자 서명" (Bold)
- `G50` — 라벨 "작성일" (Bold)
- `H50` — `sign_date` 값

**Row 51 셀 구조**:
- `A51:D51` — 서명 공란
- `E51:H51` — 서명 공란

---

## 4. 행 번호 요약표

| 행 범위 | 내용 | 높이 |
|--------|------|------|
| Row 1 | 제목 | 28pt |
| Row 2 | 부제 | 16pt |
| Row 3 | 사업장명 / 현장명 | 20pt |
| Row 4 | 작업위치 | 20pt |
| Row 5 | 작업기간 / 작업책임자 | 20pt |
| Row 6 | 도급업체 / 작성자 | 20pt |
| Row 7 | 섹션헤더: 법정기재사항 [LAW] | 18pt |
| Row 8 | 기계의 종류 [LAW] | 30pt |
| Row 9 | 기계의 최대 하중 [LAW] | 30pt |
| Row 10 | 작업방법 [LAW] | 40pt |
| Row 11 | 운전자 성명 / 운전자 자격·면허 | 20pt |
| Row 12 | 유도자 배치 여부 및 방법 [PRAC/제182조] | 30pt |
| Row 13 | 안전속도 제한 [LAW/제180조] / 기계 수량 | 20pt |
| Row 14 | 지형·지반 사전조사 | 30pt |
| Row 15 | 섹션헤더: 운행경로 [LAW] | 18pt |
| Row 16 | 운행경로 텍스트 기술 [LAW] | 60pt |
| Row 17 | 스케치 박스 헤더 | 16pt |
| Row 18~22 | 운행경로 스케치 박스 (5행) | 30pt 각 |
| Row 23 | 섹션헤더: 출입통제·보행자·비상연락망 | 18pt |
| Row 24 | 출입통제 방법 | 30pt |
| Row 25 | 비상연락망 / 비상조치 | 20pt |
| Row 26 | 보행자 동선 분리 [PRAC, 하역운반기계 특성] | 30pt |
| Row 27 | 섹션헤더: 위험요소 및 안전조치 | 18pt |
| Row 28 | 표 헤더 | 18pt |
| Row 29~38 | 위험요소/안전조치 데이터행 × 10 | 30pt 각 |
| Row 39 | 섹션헤더: 작업전점검사항 [제179조] | 18pt |
| Row 40 | 표 헤더 | 18pt |
| Row 41~48 | 작업전점검 데이터행 × 8 | 25pt 각 |
| Row 49 | 섹션헤더: 확인및서명 | 18pt |
| Row 50 | 서명 라벨 / 작성일 | 20pt |
| Row 51 | 서명 공란 | 36pt |
| **합계** | **51행** | |

---

## 5. 병합셀 전체 목록

| 셀 주소 | 병합 범위 | 내용 |
|--------|---------|------|
| A1:H1 | 8열 | 제목 |
| A2:H2 | 8열 | 부제 |
| B3:D3 | 3열 | site_name |
| F3:H3 | 3열 | project_name |
| B4:H4 | 7열 | work_location |
| B5:D5 | 3열 | work_date |
| F5:H5 | 3열 | supervisor |
| B6:D6 | 3열 | contractor |
| F6:H6 | 3열 | prepared_by |
| A7:H7 | 8열 | 섹션헤더 (법정기재사항) |
| B8:H8 | 7열 | machine_type |
| B9:H9 | 7열 | machine_max_load |
| B10:H10 | 7열 | work_method |
| B11:D11 | 3열 | operator_name |
| F11:H11 | 3열 | operator_license |
| B12:H12 | 7열 | guide_worker_required |
| B13:D13 | 3열 | speed_limit |
| F13:H13 | 3열 | machine_count |
| B14:H14 | 7열 | ground_survey |
| A15:H15 | 8열 | 섹션헤더 (운행경로) |
| B16:H16 | 7열 | travel_route_text |
| A17:H17 | 8열 | 스케치 박스 헤더 |
| (Row 18~22) | 병합 없음 | 스케치 박스 빈 영역 |
| A23:H23 | 8열 | 섹션헤더 (출입통제) |
| B24:H24 | 7열 | access_control |
| B25:D25 | 3열 | emergency_contact |
| F25:H25 | 3열 | emergency_measure |
| B26:H26 | 7열 | pedestrian_separation |
| A27:H27 | 8열 | 섹션헤더 (위험요소) |
| B28:D28 | 3열 | 표헤더: 위험요소 |
| E28:H28 | 4열 | 표헤더: 안전조치 |
| B29:D29 ~ B38:D38 | 각 행 3열 | hazard |
| E29:H29 ~ E38:H38 | 각 행 4열 | safety_measure |
| A39:H39 | 8열 | 섹션헤더 (작업전점검) |
| B40:E40 | 4열 | 표헤더: 점검항목 |
| F40:G40 | 2열 | 표헤더: 이상유무 |
| B41:E41 ~ B48:E48 | 각 행 4열 | check_item |
| F41:G41 ~ F48:G48 | 각 행 2열 | result |
| A49:H49 | 8열 | 섹션헤더 (서명) |
| A50:B50 | 2열 | "작성자 서명" 라벨 |
| C50:D50 | 2열 | 서명 공란 |
| E50:F50 | 2열 | "작업책임자 서명" 라벨 |
| A51:D51 | 4열 | 서명 공란 |
| E51:H51 | 4열 | 서명 공란 |

---

## 6. 스타일 확정

| 요소 | 스타일 |
|------|-------|
| 제목 폰트 | 맑은 고딕 14pt Bold |
| 부제 폰트 | 맑은 고딕 9pt Italic |
| 라벨 폰트 | 맑은 고딕 10pt Bold |
| 값 폰트 | 맑은 고딕 10pt |
| 라벨 배경색 | F2F2F2 (회색) |
| 섹션 헤더 배경색 | D9E1F2 (연파랑) |
| 표 헤더 배경색 | E2EFDA (연녹색) |
| 스케치 박스 배경색 | FFFFFF (흰색, 테두리만) |
| 스케치 헤더 배경색 | FFF2CC (연노랑) |
| 테두리 | thin, color=808080 전체 |
| 라벨 정렬 | 가운데 |
| 값 정렬 | 좌측, wrap_text=True |
| 서명란 정렬 | 가운데 |

---

## 7. form_data 스키마 (전체 필드 정의)

```python
form_data = {
    # ── 기본정보 (메타 블록) ─────────────────────────
    "site_name":       str|None,  # 사업장명 [PRAC][AUTO]
    "project_name":    str|None,  # 현장명 [PRAC][AUTO]
    "work_location":   str|None,  # 작업위치 [PRAC][USER]
    "work_date":       str|None,  # 작업기간 [PRAC][USER]
    "supervisor":      str|None,  # 작업책임자 성명 [PRAC][EVID]
    "contractor":      str|None,  # 도급업체 [PRAC]
    "prepared_by":     str|None,  # 작성자 [PRAC]

    # ── 장비정보 [LAW] 제38조 제2항 ─────────────────
    "machine_type":      str|None,  # 기계의 종류 [LAW][USER]
    "machine_max_load":  str|None,  # 기계의 최대 하중 [LAW][USER]  ← 건설기계의 machine_capacity와 다름
    "machine_count":     str|None,  # 기계 수량 [PRAC]
    "operator_name":     str|None,  # 운전자 성명 [PRAC][USER]
    "operator_license":  str|None,  # 운전자 자격·면허 [PRAC][EVID]

    # ── 작업조건 ─────────────────────────────────────
    "work_method":            str|None,  # 작업방법 [LAW] 제38조 제2항
    "guide_worker_required":  str|None,  # 유도자 배치 여부 및 방법 [PRAC] 제182조
    "speed_limit":            str|None,  # 안전속도 제한 [LAW] 제180조
    "ground_survey":          str|None,  # 지형·지반 사전조사 [PRAC]

    # ── 운행경로 [LAW] 제38조 제2항 ─────────────────
    "travel_route_text":         str|None,  # 운행경로 텍스트 기술 [LAW][USER]
    "travel_route_sketch_note":  str|None,  # 스케치 박스 안내문구 (기본값 자동 적용)

    # ── 출입통제/보행자/비상연락망 ───────────────────
    "access_control":          str|None,  # 출입통제 방법 [PRAC]
    "emergency_contact":       str|None,  # 비상연락망 [PRAC]
    "emergency_measure":       str|None,  # 비상조치 [LAW] 제38조 제2항
    "pedestrian_separation":   str|None,  # 보행자 동선 분리 [PRAC] ← 건설기계 builder에 없음

    # ── 위험요소/안전조치 표 ──────────────────────────
    "hazard_items": [               # list[dict], MAX_HAZARD=10
        {
            "hazard":          str|None,  # 위험 요소
            "safety_measure":  str|None,  # 안전 조치
        }
    ],

    # ── 작업 전 점검 사항 (제179조 기반) ──────────────
    "pre_check_items": [            # list[dict], MAX_CHECKS=8
        {
            "check_item": str|None,  # 점검 항목 (기본값: 제179조 6개 항목)
            "result":     str|None,  # 이상유무
            "note":       str|None,  # 비고
        }
    ],

    # ── 서명/확인 ────────────────────────────────────
    "sign_date":  str|None,  # 작성일 [PRAC][EVID][AUTO]
}
```

---

## 8. 건설기계 builder 대비 차이점 요약

| 항목 | 차량계 건설기계 | 차량계 하역운반기계 | 비고 |
|------|--------------|------------------|------|
| 시트명 | 차량계건설기계작업계획서 | **차량계하역운반기계작업계획서** | |
| 법적 근거 조항 | 제38조 제1항 제3호 + **제170조** | **제38조 제1항 제2호** (제170조 없음) | 핵심 차이 |
| 부제 | 제38조·제170조 | **제38조 제1항 제2호** | |
| 총 행 수 | 49행 | **51행** (+2행) | |
| 기계 성능 필드 | machine_capacity (성능·최대작업능력) | **machine_max_load (최대 하중)** | 하역운반기계 특성 |
| 기계 수량 | — | **machine_count** (Row 13 우측) | 추가 |
| 보행자 동선 분리 | — | **pedestrian_separation** (Row 26) | 추가 |
| 점검 섹션 헤더 | 제175조 | **제179조** | |
| 기본 점검항목 | 없음 | **제179조 6개 항목 기본 제공** | |
| print_area | A1:H49 | **A1:H51** | |

---

## 9. 법정 라벨 목록 (검증 스크립트용)

```python
LEGAL_LABELS = [
    "기계의 종류",
    "기계의 최대 하중",
    "작업방법",
    "운행경로 기술",
    "유도자 배치 여부 및 방법",
    "안전속도 제한",
    "출입통제 방법",
    "비상연락망",
    "비상조치",
    "보행자 동선 분리",
    "지형·지반 사전조사",
]
```

---

## 10. LOCK 선언

이 문서가 확정된 이후:
- 셀 주소·병합 범위는 builder 구현 전 변경 금지
- 행 순서 변경 금지
- 열 너비는 ±2 범위 내 허용 (스타일 조정)
- form_data 구조 변경 시 이 문서 동시 업데이트 필수
- 운행경로 텍스트(Row 16)와 스케치 박스(Row 18~22)는 별개 영역으로 유지
- `machine_max_load`와 `machine_capacity`는 동일 필드가 아님 — 절대 혼용 금지
- `pedestrian_separation` (Row 26)은 건설기계 builder에 없는 하역운반기계 전용 필드 — 삭제 금지

# 차량계 건설기계 작업계획서 Excel Builder 구현 계획

**작성일**: 2026-04-24  
**상태**: LOCKED — builder 구현은 이 문서 기준으로만 수행  
**근거**: `legal_form_field_inventory.md` §4, `legal_form_field_classification.md` §4, `workplan_field_matrix.md`  
**법적 근거**: 산업안전보건기준에 관한 규칙 제38조 제1항 제3호, 제170조

---

## 1. 기본 설정

| 항목 | 확정값 |
|------|-------|
| 시트명 | `차량계건설기계작업계획서` |
| 제목 | `차량계 건설기계 작업계획서` |
| 부제 | `「산업안전보건기준에 관한 규칙」 제38조·제170조에 따른 작업계획서` |
| 총 열 수 | **8열 (A~H)** |
| 총 행 수 | **49행** (기본 hazard_items=10, pre_check_items=8 기준) |
| 인쇄 설정 | portrait, fitToWidth=1 |
| 여백 (인치) | left=0.5, right=0.5, top=0.75, bottom=0.75 |

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
| Row 1 | A1:H1 | `차량계 건설기계 작업계획서` | 28pt | Font 14pt Bold, 가운데 정렬 |
| Row 2 | A2:H2 | `「산업안전보건기준에 관한 규칙」 제38조·제170조에 따른 작업계획서` | 16pt | Font 9pt Italic, 가운데 정렬 |

### 블록 B — 메타 영역 (Row 3~6)

**2분할 라벨-값 구조**: 좌(A라벨, B:D값) / 우(E라벨, F:H값)

| 행 | 좌측 라벨 (A) | 좌측 값 (B:D) | 우측 라벨 (E) | 우측 값 (F:H) | 높이 |
|----|------------|------------|------------|------------|------|
| Row 3 | `사업장명` | `site_name` | `현장명` | `project_name` | 20pt |
| Row 4 | `작업 위치` | `work_location` (B:H 전폭) | — | — | 20pt |
| Row 5 | `작업 기간` | `work_date` | `작업 책임자` | `supervisor` | 20pt |
| Row 6 | `도급업체` | `contractor` | `작성자` | `prepared_by` | 20pt |

> Row 4 작업 위치: 라벨 A4, 값 B4:H4 (전폭 병합, E열 라벨 없음)

### 블록 C — 법정 기재 사항 (Row 7~14)

**전폭 라벨-값 구조**: 라벨 A, 값 B:H

| 행 | 라벨 (A) | 값 (B:H) | 높이 | 법적 성격 | 근거 조항 |
|----|---------|---------|------|---------|---------|
| Row 7 | [섹션 헤더 A7:H7] `법정 기재 사항 (기준규칙 제38조·제170조)` | — | 18pt | — | — |
| Row 8 | `기계의 종류` | `machine_type` | 30pt | **LAW** | 제170조 제1호 |
| Row 9 | `기계의 성능·최대작업능력` | `machine_capacity` | 30pt | **LAW** | 제170조 제1호 |
| Row 10 | `작업방법` | `work_method` | 40pt | **LAW** | 제170조 제3호 |
| Row 11 | `운전자 성명` | `operator_name` (B:D) / `운전자 자격·면허` 라벨(E) / `operator_license` (F:H) | 20pt | PRAC/EVID | 제80조 |
| Row 12 | `유도자 배치 여부 및 방법` | `guide_worker_required` | 30pt | PRAC | 제172조 |
| Row 13 | `안전속도 제한` | `speed_limit` (B:D) / `작업반경` 라벨(E) / `work_radius` (F:H) | 20pt | PRAC | 제175조 |
| Row 14 | `지형·지반 사전조사` | `ground_survey` | 30pt | PRAC | 제171조 |

> Row 11: A=라벨, B:D=운전자성명, E=라벨, F:H=자격면허 (2분할)  
> Row 13: A=라벨, B:D=속도제한값, E=라벨, F:H=작업반경값 (2분할)

### 블록 D — 운행경로 (Row 15~22)

**운행경로는 법정 필수 (제170조 제2호) — 텍스트 + 스케치 박스 분리**

| 행 | 내용 | 높이 |
|----|------|------|
| Row 15 | [섹션 헤더 A15:H15] `운행경로 (기준규칙 제170조 제2호 법정 기재사항)` | 18pt |
| Row 16 | 라벨 A=`운행경로 기술`, 값 B:H=`travel_route_text` | 60pt |
| Row 17 | [스케치 헤더 A17:H17] `운행경로 스케치/개략도 ※ 아래 공간에 수기 기재` | 16pt |
| Row 18~22 | 스케치 박스 (A:H 전폭 병합 없음, 셀 테두리만, 빈 영역) 각 행 | 30pt 각 |

> Row 16: travel_route_text — 운행경로 진입로·구내동선·반출경로 텍스트 기술  
> Row 18~22: 스케치 박스 — 5행 × 8열. 병합 없이 테두리만. 사용자가 인쇄 후 수기 도면 작성 가능  
> sketch_placeholder 값이 있으면 Row 17 헤더 옆 안내문구에 반영

### 블록 E — 출입통제·유도자·비상연락망 (Row 23~26)

| 행 | 내용 | 높이 |
|----|------|------|
| Row 23 | [섹션 헤더 A23:H23] `출입통제 · 유도자 · 비상연락망` | 18pt |
| Row 24 | 라벨 A=`출입통제 방법`, 값 B:H=`access_control` | 30pt |
| Row 25 | 라벨 A=`비상연락망`, 값 B:D=`emergency_contact` / 라벨 E=`비상조치`, 값 F:H=`emergency_measure` | 20pt |
| Row 26 | — *(비어 있음, 행 높이만 예약)* | 0pt *(Row 수 고정을 위해 skip)* |

> Row 26 제거 → Row 23~25만 사용. 합계 3행.

### 블록 F — 위험요소 및 안전조치 표 (Row 26~38)

| 행 | 내용 | 높이 |
|----|------|------|
| Row 26 | [섹션 헤더 A26:H26] `위험요소 및 안전조치` | 18pt |
| Row 27 | [표 헤더] A=`순번`, B:D=`위험 요소`, E:H=`안전 조치` | 18pt |
| Row 28~37 | 데이터행 × 10행 (MAX_HAZARD=10) | 30pt 각 |

**표 헤더 셀 범위**:
- `A27` — 순번 (병합 없음)
- `B27:D27` — 위험 요소 (3열 병합)
- `E27:H27` — 안전 조치 (4열 병합)

**데이터행 (Row 28~37)**:
- `A28` — 순번 (정수, AUTO 채번, 가운데 정렬)
- `B28:D28` — `hazard_items[i].hazard`
- `E28:H28` — `hazard_items[i].safety_measure`

> 기본 10행 고정. hazard_items 없으면 공란. 10개 초과 시 행 추가 (동적 확장).

### 블록 G — 작업 전 점검 사항 (Row 38~48)

| 행 | 내용 | 높이 |
|----|------|------|
| Row 38 | [섹션 헤더 A38:H38] `작업 전 점검 사항 (기준규칙 제175조)` | 18pt |
| Row 39 | [표 헤더] A=`순번`, B:E=`점검 항목`, F:G=`이상유무`, H=`비고` | 18pt |
| Row 40~47 | 데이터행 × 8행 (MAX_CHECKS=8) | 25pt 각 |

**표 헤더 셀 범위**:
- `A39` — 순번 (병합 없음)
- `B39:E39` — 점검 항목 (4열 병합)
- `F39:G39` — 이상유무 (2열 병합)
- `H39` — 비고

**데이터행 (Row 40~47)**:
- `A40` — 순번 (정수, AUTO 채번, 가운데 정렬)
- `B40:E40` — `pre_check_items[i].check_item`
- `F40:G40` — `pre_check_items[i].result`
- `H40` — `pre_check_items[i].note`

### 블록 H — 확인 및 서명 (Row 48~49)

| 행 | 내용 | 높이 |
|----|------|------|
| Row 48 | [섹션 헤더 A48:H48] `확인 및 서명` | 18pt |
| Row 49 | 서명 라벨+공란 / 작성일 | 36pt |

**Row 49 셀 구조**:
- `A49:B49` — 라벨 "작성자 서명" (Bold, 배경색 F2F2F2)
- `C49:D49` — 공란 (수기 서명)
- `E49:F49` — 라벨 "작업책임자 서명" (Bold, 배경색)
- `G49` — 라벨 "작성일" (Bold, 배경색)
- `H49` — `sign_date` 값

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
| Row 7 | 섹션헤더: 법정기재사항 | 18pt |
| Row 8 | 기계의 종류 [LAW] | 30pt |
| Row 9 | 기계의 성능·최대작업능력 [LAW] | 30pt |
| Row 10 | 작업방법 [LAW] | 40pt |
| Row 11 | 운전자 성명 / 운전자 자격·면허 | 20pt |
| Row 12 | 유도자 배치 여부 및 방법 | 30pt |
| Row 13 | 안전속도 제한 / 작업반경 | 20pt |
| Row 14 | 지형·지반 사전조사 | 30pt |
| Row 15 | 섹션헤더: 운행경로 [LAW] | 18pt |
| Row 16 | 운행경로 텍스트 기술 [LAW] | 60pt |
| Row 17 | 스케치 박스 헤더 | 16pt |
| Row 18~22 | 운행경로 스케치 박스 (5행) | 30pt 각 |
| Row 23 | 섹션헤더: 출입통제·유도자·비상연락망 | 18pt |
| Row 24 | 출입통제 방법 | 30pt |
| Row 25 | 비상연락망 / 비상조치 | 20pt |
| Row 26 | 섹션헤더: 위험요소 및 안전조치 | 18pt |
| Row 27 | 표 헤더 | 18pt |
| Row 28~37 | 위험요소/안전조치 데이터행 × 10 | 30pt 각 |
| Row 38 | 섹션헤더: 작업전점검사항 | 18pt |
| Row 39 | 표 헤더 | 18pt |
| Row 40~47 | 작업전점검 데이터행 × 8 | 25pt 각 |
| Row 48 | 섹션헤더: 확인및서명 | 18pt |
| Row 49 | 서명 / 작성일 | 36pt |
| **합계** | **49행** | |

---

## 5. 병합셀 전체 목록

| 셀 주소 | 병합 범위 | 내용 |
|--------|---------|------|
| A1:H1 | 8열 병합 | 제목 |
| A2:H2 | 8열 병합 | 부제 |
| B3:D3 | 3열 병합 | site_name |
| F3:H3 | 3열 병합 | project_name |
| B4:H4 | 7열 병합 | work_location |
| B5:D5 | 3열 병합 | work_date |
| F5:H5 | 3열 병합 | supervisor |
| B6:D6 | 3열 병합 | contractor |
| F6:H6 | 3열 병합 | prepared_by |
| A7:H7 | 8열 병합 | 섹션헤더 |
| B8:H8 | 7열 병합 | machine_type |
| B9:H9 | 7열 병합 | machine_capacity |
| B10:H10 | 7열 병합 | work_method |
| B11:D11 | 3열 병합 | operator_name |
| F11:H11 | 3열 병합 | operator_license |
| B12:H12 | 7열 병합 | guide_worker_required |
| B13:D13 | 3열 병합 | speed_limit |
| F13:H13 | 3열 병합 | work_radius |
| B14:H14 | 7열 병합 | ground_survey |
| A15:H15 | 8열 병합 | 섹션헤더 (운행경로) |
| B16:H16 | 7열 병합 | travel_route_text |
| A17:H17 | 8열 병합 | 스케치 박스 헤더 |
| (Row 18~22) | 각 행 병합 없음 | 스케치 박스 빈 영역 |
| A23:H23 | 8열 병합 | 섹션헤더 (출입통제) |
| B24:H24 | 7열 병합 | access_control |
| B25:D25 | 3열 병합 | emergency_contact |
| F25:H25 | 3열 병합 | emergency_measure |
| A26:H26 | 8열 병합 | 섹션헤더 (위험요소) |
| B27:D27 | 3열 병합 | 표헤더: 위험요소 |
| E27:H27 | 4열 병합 | 표헤더: 안전조치 |
| B28:D28 ~ B37:D37 | 각 행 3열 | hazard |
| E28:H28 ~ E37:H37 | 각 행 4열 | safety_measure |
| A38:H38 | 8열 병합 | 섹션헤더 (작업전점검) |
| B39:E39 | 4열 병합 | 표헤더: 점검항목 |
| F39:G39 | 2열 병합 | 표헤더: 이상유무 |
| B40:E40 ~ B47:E47 | 각 행 4열 | check_item |
| F40:G40 ~ F47:G47 | 각 행 2열 | result |
| A48:H48 | 8열 병합 | 섹션헤더 (서명) |
| A49:B49 | 2열 병합 | "작성자 서명" 라벨 |
| C49:D49 | 2열 병합 | 서명 공란 |
| E49:F49 | 2열 병합 | "작업책임자 서명" 라벨 |

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
| 스케치 헤더 배경색 | FFF2CC (연노랑, 안내문구) |
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

    # ── 장비정보 [LAW] 제170조 제1호 ─────────────────
    "machine_type":     str|None, # 기계의 종류 [LAW][USER]
    "machine_capacity": str|None, # 기계의 성능·최대작업능력 [LAW][USER]
    "operator_name":    str|None, # 운전자 성명 [PRAC][USER]
    "operator_license": str|None, # 운전자 자격·면허 [PRAC][EVID]

    # ── 작업조건 ─────────────────────────────────────
    "work_method":     str|None,  # 작업방법 [LAW][USER] 제170조 제3호
    "guide_worker_required": str|None,  # 유도자 배치 여부 및 방법 [PRAC] 제172조
    "speed_limit":     str|None,  # 안전속도 제한 [PRAC] 제175조
    "work_radius":     str|None,  # 작업반경 [PRAC]
    "ground_survey":   str|None,  # 지형·지반 사전조사 [PRAC] 제171조

    # ── 운행경로 [LAW] 제170조 제2호 ─────────────────
    "travel_route_text":         str|None,  # 운행경로 텍스트 기술 [LAW][USER]
    "travel_route_sketch_note":  str|None,  # 스케치 박스 안내문구 (기본값 자동 적용)

    # ── 출입통제/유도자/비상연락망 ───────────────────
    "access_control":    str|None, # 출입통제 방법 [PRAC]
    "emergency_contact": str|None, # 비상연락망 [PRAC]
    "emergency_measure": str|None, # 비상조치 [PRAC]

    # ── 위험요소/안전조치 표 ──────────────────────────
    "hazard_items": [               # list[dict], MAX_HAZARD=10
        {
            "hazard":          str|None,  # 위험 요소
            "safety_measure":  str|None,  # 안전 조치
        }
    ],

    # ── 작업 전 점검 사항 ─────────────────────────────
    "pre_check_items": [            # list[dict], MAX_CHECKS=8
        {
            "check_item": str|None,  # 점검 항목
            "result":     str|None,  # 이상유무
            "note":       str|None,  # 비고
        }
    ],

    # ── 서명/확인 ────────────────────────────────────
    "sign_date":  str|None,  # 작성일 [PRAC][EVID][AUTO]
}
```

### 법정 필수(LAW) vs 사용자 입력 구분

| field_key | 성격 | 미입력 시 처리 |
|-----------|------|-------------|
| `machine_type` | LAW+USER | 공란 렌더링 |
| `machine_capacity` | LAW+USER | 공란 렌더링 |
| `travel_route_text` | LAW+USER | 공란 렌더링 |
| `work_method` | LAW+USER | 공란 렌더링 |
| `guide_worker_required` | PRAC | 공란 렌더링 |
| `access_control` | PRAC | 공란 렌더링 |
| `emergency_contact` | PRAC | 공란 렌더링 |
| `emergency_measure` | PRAC | 공란 렌더링 |
| `operator_license` | PRAC+EVID | 공란 렌더링 |

> builder는 미입력 시 공란 유지. 검증은 `validate_vehicle_workplan_builder.py`에서 수행.

---

## 8. 법정 라벨 목록 (검증 스크립트 재사용)

```python
LEGAL_LABELS = [
    "기계의 종류",
    "기계의 성능·최대작업능력",
    "작업방법",
    "운행경로 기술",
    "유도자 배치 여부 및 방법",
    "출입통제 방법",
    "비상연락망",
    "비상조치",
    "지형·지반 사전조사",
]
```

---

## 9. LOCK 선언

이 문서가 확정된 이후:
- 셀 주소·병합 범위는 builder 구현 전 변경 금지
- 행 순서 변경 금지
- 열 너비는 ±2 범위 내 허용 (스타일 조정)
- form_data 구조 변경 시 이 문서 동시 업데이트 필수
- 운행경로 텍스트(Row 16)와 스케치 박스(Row 18~22)는 별개 영역으로 유지

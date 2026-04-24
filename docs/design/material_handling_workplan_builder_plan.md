# 차량계 하역운반기계 작업계획서 Builder 구현 계획 — 1단계

**작성일**: 2026-04-24  
**상태**: CONFIRMED — builder 구현 착수 기준 문서  
**기반**: material_handling_workplan_excel_layout_lock.md (LOCKED)  
**참조 구현**: engine/output/vehicle_workplan_builder.py (건설기계 builder)

---

## 1. 시트 기본값

| 항목 | 값 |
|------|---|
| 시트명 | `차량계하역운반기계작업계획서` |
| 제목 | `차량계 하역운반기계 작업계획서` |
| 부제 | `「산업안전보건기준에 관한 규칙」 제38조 제1항 제2호에 따른 작업계획서` |
| 총 행 수 | 51행 |
| 총 열 수 | 8열 (A~H) |
| print_area | `A1:H51` |
| 인쇄 방향 | portrait, fitToWidth=1 |
| 여백 (인치) | left=0.5, right=0.5, top=0.75, bottom=0.75 |

---

## 2. 열 너비

| 열 | 너비 |
|----|------|
| A  | 14   |
| B~G | 12  |
| H  | 10   |

---

## 3. 행 구조 요약

| 행 범위 | 블록 | 내용 | 높이 |
|--------|------|------|------|
| Row 1 | A — 제목 | 제목 (A1:H1) | 28pt |
| Row 2 | A — 제목 | 부제 (A2:H2) | 16pt |
| Row 3 | B — 메타 | 사업장명 / 현장명 | 20pt |
| Row 4 | B — 메타 | 작업위치 (A4 라벨, B4:H4 전폭) | 20pt |
| Row 5 | B — 메타 | 작업기간 / 작업책임자 | 20pt |
| Row 6 | B — 메타 | 도급업체 / 작성자 | 20pt |
| Row 7 | C — 법정 | 섹션헤더 (A7:H7) | 18pt |
| Row 8 | C — 법정 | 기계의 종류 [LAW] (A8 라벨, B8:H8 값) | 30pt |
| Row 9 | C — 법정 | 기계의 최대 하중 [LAW] (A9 라벨, B9:H9 값) | 30pt |
| Row 10 | C — 법정 | 작업방법 [LAW] (A10 라벨, B10:H10 값) | 40pt |
| Row 11 | C — 법정 | 운전자성명(A,B:D) / 운전자 자격·면허(E,F:H) | 20pt |
| Row 12 | C — 법정 | 유도자 배치 여부 및 방법 (A12 라벨, B12:H12 값) | 30pt |
| Row 13 | C — 법정 | 안전속도 제한(A,B:D) / 기계 수량(E,F:H) | 20pt |
| Row 14 | C — 법정 | 지형·지반 사전조사 (A14 라벨, B14:H14 값) | 30pt |
| Row 15 | D — 운행경로 | 섹션헤더 [LAW] (A15:H15) | 18pt |
| Row 16 | D — 운행경로 | 운행경로 텍스트 기술 (A16 라벨, B16:H16 값) | 60pt |
| Row 17 | D — 운행경로 | 스케치 박스 헤더 (A17:H17) | 16pt |
| Row 18~22 | D — 운행경로 | 스케치 박스 (병합 없음, 테두리만, 5행) | 30pt 각 |
| Row 23 | E — 출입통제 | 섹션헤더 (A23:H23) | 18pt |
| Row 24 | E — 출입통제 | 출입통제 방법 (A24 라벨, B24:H24 값) | 30pt |
| Row 25 | E — 출입통제 | 비상연락망(A,B:D) / 비상조치(E,F:H) | 20pt |
| Row 26 | E — 출입통제 | 보행자 동선 분리 [PRAC] (A26 라벨, B26:H26 값) | 30pt |
| Row 27 | F — 위험요소 | 섹션헤더 (A27:H27) | 18pt |
| Row 28 | F — 위험요소 | 표 헤더 (순번/위험요소/안전조치) | 18pt |
| Row 29~38 | F — 위험요소 | 데이터행 × 10 (MAX_HAZARD=10) | 30pt 각 |
| Row 39 | G — 점검 | 섹션헤더 제179조 (A39:H39) | 18pt |
| Row 40 | G — 점검 | 표 헤더 (순번/점검항목/이상유무/비고) | 18pt |
| Row 41~48 | G — 점검 | 데이터행 × 8 (MAX_CHECKS=8) | 25pt 각 |
| Row 49 | H — 서명 | 섹션헤더 (A49:H49) | 18pt |
| Row 50 | H — 서명 | 서명 라벨행 | 20pt |
| Row 51 | H — 서명 | 서명 공란 (A51:D51 / E51:H51) | 36pt |
| **합계** | | **51행** | |

---

## 4. 주요 병합셀 범위

| 범위 | 내용 |
|------|------|
| A1:H1 | 제목 |
| A2:H2 | 부제 |
| B3:D3, F3:H3 | 사업장명/현장명 |
| B4:H4 | 작업위치 |
| B5:D5, F5:H5 | 작업기간/작업책임자 |
| B6:D6, F6:H6 | 도급업체/작성자 |
| A7:H7 | 법정 섹션헤더 |
| B8:H8 | machine_type |
| B9:H9 | machine_max_load |
| B10:H10 | work_method |
| B11:D11, F11:H11 | operator_name/license |
| B12:H12 | guide_worker_required |
| B13:D13, F13:H13 | speed_limit/machine_count |
| B14:H14 | ground_survey |
| A15:H15 | 운행경로 섹션헤더 |
| B16:H16 | travel_route_text |
| A17:H17 | 스케치 헤더 |
| Row 18~22: 병합 없음 | 스케치 박스 |
| A23:H23 | 출입통제 섹션헤더 |
| B24:H24 | access_control |
| B25:D25, F25:H25 | emergency_contact/measure |
| B26:H26 | pedestrian_separation |
| A27:H27, B28:D28, E28:H28 | 위험요소 헤더 |
| B29:D29~B38:D38 | hazard (각 행) |
| E29:H29~E38:H38 | safety_measure (각 행) |
| A39:H39, B40:E40, F40:G40 | 점검 헤더 |
| B41:E41~B48:E48 | check_item (각 행) |
| F41:G41~F48:G48 | result (각 행) |
| A49:H49 | 서명 섹션헤더 |
| A50:B50, C50:D50, E50:F50 | 서명 라벨행 |
| A51:D51, E51:H51 | 서명 공란 |

---

## 5. 법정 필수항목 위치

| 필드 | 행 | 근거 |
|------|----|------|
| machine_type | Row 8 | 제38조 제2항 |
| machine_max_load | Row 9 | 제38조 제2항 |
| work_method | Row 10 | 제38조 제2항 |
| travel_route_text | Row 16 | 제38조 제2항 |
| emergency_measure | Row 25 우측 | 제38조 제2항 |
| speed_limit | Row 13 좌측 | 제180조 |

---

## 6. 기본 제공 점검 항목 (제179조 기반, MAX_CHECKS=8)

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

---

## 7. 건설기계 builder 대비 차이점

| 항목 | vehicle_workplan_builder.py | material_handling_workplan_builder.py |
|------|---------------------------|--------------------------------------|
| 시트명 | 차량계건설기계작업계획서 | **차량계하역운반기계작업계획서** |
| 부제 조항 | 제38조·제170조 | **제38조 제1항 제2호** |
| 총 행 수 | 49행 | **51행** |
| 기계 성능 필드 | machine_capacity | **machine_max_load** |
| Row 13 우측 | work_radius | **machine_count** |
| Row 26 | 없음 | **pedestrian_separation** (추가) |
| Row 50~51 | 1행 서명란 | **2행 서명란 (라벨행+공란행)** |
| 점검 섹션 헤더 | 제175조 | **제179조** |
| 기본 점검항목 | 없음 | **8개 기본 제공** |
| print_area | A1:H49 (동적) | **A1:H51 (고정)** |

---

## 8. 공개 함수

```python
def build_material_handling_workplan_excel(form_data: Dict[str, Any]) -> bytes
def render_material_handling_workplan_sheet(ws, form_data: Dict[str, Any]) -> None
```

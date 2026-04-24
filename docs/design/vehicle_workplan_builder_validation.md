# 차량계 건설기계 작업계획서 Builder 검증 결과

**검증일**: 2026-04-24  
**스크립트**: `scripts/validate_vehicle_workplan_builder.py`  
**대상**: `engine/output/vehicle_workplan_builder.py`

---

## 검증 결과 요약

| 구분 | 결과 |
|------|------|
| 총 검증 항목 | 77개 |
| PASS | **77개** |
| FAIL | 0개 |
| **최종 판정** | **PASS** |

---

## 검증 항목별 결과

### 샘플 데이터 검증 (31개 항목)

| # | 항목 | 결과 |
|---|------|------|
| 1 | xlsx bytes 정상 생성 (9,197 bytes) | PASS |
| 2 | openpyxl 재오픈 성공 | PASS |
| 3 | 시트명 == '차량계건설기계작업계획서' | PASS |
| 4 | 제목(A1) == '차량계 건설기계 작업계획서' | PASS |
| 5 | 부제(A2) == SHEET_SUBTITLE | PASS |
| 6 | 법정항목 라벨 존재: '기계의 종류' | PASS |
| 7 | 법정항목 라벨 존재: '기계의 성능·최대작업능력' | PASS |
| 8 | 법정항목 라벨 존재: '작업방법' | PASS |
| 9 | 법정항목 라벨 존재: '운행경로 기술' | PASS |
| 10 | 법정항목 라벨 존재: '유도자 배치 여부 및 방법' | PASS |
| 11 | 법정항목 라벨 존재: '출입통제 방법' | PASS |
| 12 | 법정항목 라벨 존재: '비상연락망' | PASS |
| 13 | 법정항목 라벨 존재: '비상조치' | PASS |
| 14 | 법정항목 라벨 존재: '지형·지반 사전조사' | PASS |
| 15 | 운행경로 텍스트 영역 라벨 ('운행경로 기술') 존재 | PASS |
| 16 | 운행경로 스케치 박스 헤더 존재 | PASS |
| 17 | 유도자 배치 여부 및 방법 라벨 존재 | PASS |
| 18 | 출입통제 방법 라벨 존재 | PASS |
| 19 | 비상연락망 라벨 존재 | PASS |
| 20 | 위험요소/안전조치 표 헤더 존재 | PASS |
| 21 | 작업 전 점검 사항 표 헤더 존재 | PASS |
| 22 | print_area 설정 존재 (A1:H49) | PASS |
| 23~32 | 주요 병합셀 10종 존재 | PASS (전체) |

### 샘플 값 렌더링 검증 (12개 항목)

| # | 항목 | 결과 |
|---|------|------|
| 1 | site_name 렌더링 | PASS |
| 2 | project_name 렌더링 | PASS |
| 3 | machine_type 렌더링 | PASS |
| 4 | work_radius 포함 텍스트 렌더링 | PASS |
| 5 | guide_worker_required 포함 텍스트 렌더링 | PASS |
| 6 | travel_route_text 포함 텍스트 렌더링 | PASS |
| 7 | access_control 포함 텍스트 렌더링 | PASS |
| 8 | emergency_contact 포함 텍스트 렌더링 | PASS |
| 9 | sign_date 렌더링 | PASS |
| 10 | hazard_items[0].hazard 렌더링 | PASS |
| 11 | hazard_items[0].safety_measure 렌더링 | PASS |
| 12 | pre_check_items[0].check_item 렌더링 | PASS |

### 빈 form_data 검증 (33개 항목)

| # | 항목 | 결과 |
|---|------|------|
| 1~31 | 샘플 검증과 동일 구조 검증 (빈 form_data) | PASS (전체) |
| 32 | 빈 form_data 공란 유지 확인 | PASS |
| 비고 | 비공란 비헤더 값: 없음 | — |

---

## 주요 확인 사항

### 운행경로 처리

- **텍스트 영역** (Row 16): `travel_route_text` 필드를 별도 행에 렌더링. 라벨 "운행경로 기술", 값 B:H 병합
- **스케치 박스** (Row 17~22): 스케치 헤더(연노랑 배경) + 빈 영역 5행(테두리만). 수기 도면 작성 공간
- 두 영역이 완전히 분리되어 있음 확인

### 법정 필수항목 반영

| 조항 | 항목 | 라벨 | 확인 |
|------|------|------|------|
| 제170조 제1호 | 기계의 종류 | `기계의 종류` | ✓ |
| 제170조 제1호 | 기계의 성능·최대작업능력 | `기계의 성능·최대작업능력` | ✓ |
| 제170조 제2호 | 운행경로 | `운행경로 기술` | ✓ |
| 제170조 제3호 | 작업방법 | `작업방법` | ✓ |

### 세부 필드 노출

| 필드 | 라벨 | 확인 |
|------|------|------|
| `guide_worker_required` | 유도자 배치 여부 및 방법 | ✓ |
| `access_control` | 출입통제 방법 | ✓ |
| `emergency_contact` | 비상연락망 | ✓ |
| `emergency_measure` | 비상조치 | ✓ |
| `operator_license` | 운전자 자격·면허 | ✓ |
| `work_radius` | 작업반경 | ✓ |
| `speed_limit` | 안전속도 제한 | ✓ |
| `ground_survey` | 지형·지반 사전조사 | ✓ |

---

## 제한 사항

- form_registry 미등록 (별도 단계에서 수행)
- export API 미연결 (별도 단계에서 수행)
- 운행경로 스케치 박스는 빈 영역으로만 제공, 실제 도면 자동 생성 불가
- `hazard_items > 10`, `pre_check_items > 8` 초과분 무시 (기본 행 수 고정)

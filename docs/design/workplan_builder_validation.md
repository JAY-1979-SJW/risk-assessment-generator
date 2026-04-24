# 굴착 작업계획서 Excel Builder 검증 결과

**작성일**: 2026-04-24  
**대상**: `engine/output/workplan_builder.py` v1  
**검증 스크립트**: `scripts/validate_workplan_builder.py`  
**최종 판정**: **PASS (61/61)**

---

## 1. 검증 항목 및 결과

### 샘플 데이터 검증 (30항목)

| 항목 | 결과 |
|------|------|
| xlsx bytes 정상 생성 (7,713 bytes) | PASS |
| openpyxl 재오픈 성공 | PASS |
| 시트명 == '작업계획서' | PASS |
| 제목(A1) == '굴착 작업계획서' | PASS |
| 부제(A2) == SHEET_SUBTITLE | PASS |
| 법정항목 라벨: 굴착의 방법 | PASS |
| 법정항목 라벨: 흙막이 지보공 및 방호망 | PASS |
| 법정항목 라벨: 사용 기계 종류 및 능력 | PASS |
| 법정항목 라벨: 토석 처리 방법 | PASS |
| 법정항목 라벨: 용수 처리 방법 | PASS |
| 법정항목 라벨: 작업 방법 | PASS |
| 법정항목 라벨: 긴급조치 계획 | PASS |
| 안전조치표 10행(순번 1~10) 존재 | PASS |
| 인쇄영역 == 'A1:H29' | PASS |
| 병합셀: A1:H1 (제목) | PASS |
| 병합셀: A2:H2 (부제) | PASS |
| 병합셀: B3:D3 (site_name) | PASS |
| 병합셀: F3:H3 (project_name) | PASS |
| 병합셀: B4:H4 (work_location) | PASS |
| 병합셀: B5:D5 (work_date) | PASS |
| 병합셀: F5:H5 (supervisor) | PASS |
| 병합셀: A7:H7 (섹션헤더-법정) | PASS |
| 병합셀: B8:H8 (excavation_method) | PASS |
| 병합셀: A15:H15 (섹션헤더-안전조치) | PASS |
| 병합셀: B16:C16 (표헤더-작업단계) | PASS |
| 병합셀: D16:F16 (표헤더-위험요인) | PASS |
| 병합셀: G16:H16 (표헤더-안전조치) | PASS |
| 병합셀: A27:H27 (섹션헤더-서명) | PASS |
| 병합셀: A28:B28 (작성자 라벨) | PASS |
| 병합셀: E28:F28 (검토자 라벨) | PASS |

### 빈 form_data 검증 (30항목)

샘플 데이터 검증과 동일한 30항목 — 전항목 PASS  
xlsx bytes: 6,959 bytes (샘플 대비 –754 bytes, 데이터 없음으로 정상)

### 공란 유지 검증 (1항목)

| 항목 | 결과 |
|------|------|
| 모든 값 필드 공란 유지 (비공란 비헤더 값 없음) | PASS |

---

## 2. xlsx 파일 크기

| 케이스 | 크기 |
|--------|------|
| 빈 form_data | 6,959 bytes |
| 샘플 데이터 (3 steps) | 7,713 bytes |

---

## 3. 확인된 제한 사항

| 항목 | 내용 |
|------|------|
| safety_steps > 10 | 초과분 무시, 10행 고정 출력 |
| responsible_person · note | 입력 허용, 출력 없음 (레이아웃 제약) |
| Row 6 우측 작성일 | 항상 공란 (form_data 필드 없음, 수기 기입) |
| 서명란 | 항상 공란 (수기 서명 전용) |
| 굴착 외 작업유형 | v1 미구현 (차량계·터널·해체·중량물) |
| 작업계획도 영역 | Excel 범위 외 (수기 도면용) |

---

## 4. 주요 트리비아

- `ws.print_area` openpyxl 반환값은 시트명 포함 형식: `"'작업계획서'!$A$1:$H$29"`
  → 검증 스크립트에서 `$` 제거 + `!` 뒤 취득으로 정규화 비교 처리.

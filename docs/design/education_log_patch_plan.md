# 교육일지 Builder v1.1 패치 계획

**작성일**: 2026-04-24  
**근거**: `education_log_layout_diff.md`, `education_log_law_validation.md`, `education_log_usability_check.md`  
**제약**: builder 재작성 금지 / 함수 시그니처 변경 금지 / form_data 구조 변경 금지 / 최대 5개 이내

---

## 패치 목록 (4건)

### P1 — 법적 근거 부제 추가

| 항목 | 내용 |
|------|------|
| 대상 함수 | `_write_title(ws, row)` |
| 변경 내용 | 제목 행(Row 1) 아래에 부제 행 추가: "「산업안전보건법」 제29조에 따른 안전보건교육" |
| 행 높이 | 부제 행: 16pt, 맑은 고딕 9pt italic, 가운데 정렬 |
| 반환값 변경 | `row + 1` → `row + 2` (부제 행 포함) |
| 함수 시그니처 | 변경 없음 |
| form_data | 변경 없음 |
| 검증 영향 | validate_empty: header_texts에 부제 텍스트 추가 필요 |

### P2 — 교육 내용 행 높이 20 → 30pt

| 항목 | 내용 |
|------|------|
| 대상 함수 | `_write_subject_table` 내 데이터 행 |
| 변경 내용 | `ws.row_dimensions[r].height = 20` → `30` |
| 사유 | 교육 내용 요약 기재 공간 확보 |
| 함수 시그니처 | 변경 없음 |
| form_data | 변경 없음 |

### P3 — 수강자 행 높이 18 → 22pt

| 항목 | 내용 |
|------|------|
| 대상 함수 | `_write_attendee_table` 내 수강자 반복 행 |
| 변경 내용 | `ws.row_dimensions[r].height = 18` → `22` |
| 사유 | 손글씨 서명 최소 공간 확보 (≥ 7mm) |
| 함수 시그니처 | 변경 없음 |
| form_data | 변경 없음 |

### P4 — 확인자 서명 행 높이 30 → 40pt

| 항목 | 내용 |
|------|------|
| 대상 함수 | `_write_confirmation` 내 서명란 행 |
| 변경 내용 | `ws.row_dimensions[r].height = 30` → `40` |
| 사유 | 직인/인감 날인 공간 확보 (≥ 14mm) |
| 함수 시그니처 | 변경 없음 |
| form_data | 변경 없음 |

---

## 연동 수정 (패치 카운트 외)

| 대상 | 수정 내용 |
|------|---------|
| `scripts/validate_education_log_builder.py` | `validate_empty` 의 `header_texts`에 부제 텍스트 추가 (P1 부제 반영) |
| `docs/design/form_requirements_spec.md` | 정기교육 시간 "매분기" → "매반기" 오탈자 수정 |

---

## 변경 요약

| 패치 | 유형 | 위험도 |
|------|------|-------|
| P1 부제 행 | 행 추가 (title 함수 내) | 낮음 — 행 오프셋 +1 |
| P2 높이 20→30 | 스타일 숫자 변경 | 없음 |
| P3 높이 18→22 | 스타일 숫자 변경 | 없음 |
| P4 높이 30→40 | 스타일 숫자 변경 | 없음 |

**validate 재실행 후 25/25 PASS 유지 목표**

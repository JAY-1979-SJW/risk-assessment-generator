---
title: 굴착 작업계획서 누락 3필드 보완 패치 계획
date: 2026-04-24
status: APPROVED
---

# 굴착 작업계획서 누락 3필드 보완 계획

## 1. 패치 범위

| 파일 | 변경 유형 |
|------|---------|
| `engine/output/workplan_builder.py` | 최소 수정 (legal_rows 3행 추가, print_area 갱신) |
| `engine/output/form_registry.py` | optional_fields 3개 추가 |
| `scripts/validate_form_registry.py` | 샘플 3필드 추가 |
| `scripts/validate_export_api.py` | 샘플 3필드 추가 |

## 2. 누락 3필드 법적 근거

| field_key | 한국어 라벨 | 법적 근거 | 분류 |
|-----------|-----------|---------|------|
| `guide_worker_required` | 유도자 배치 | 기준규칙 제172조, 제38조 제2항 | LAW |
| `access_control` | 출입통제 방법 | 기준규칙 제38조 제1항 제6호 | LAW |
| `emergency_contact` | 비상연락망 | 기준규칙 제38조 제2항 (긴급조치 세부) | PRAC |

## 3. 레이아웃 변경 계획

### 현재 (29행, A1:H29)

```
Row 1 : 제목 (굴착 작업계획서)
Row 2 : 부제
Row 3 : 사업장명 | 현장명
Row 4 : 작업위치
Row 5 : 작업일자 | 작업책임자
Row 6 : 도급업체 | 작성일
Row 7 : [섹션] 법정 기재 사항 (제82조)
Row 8 : 굴착의 방법
Row 9 : 흙막이 지보공 및 방호망
Row 10: 사용 기계 종류 및 능력
Row 11: 토석 처리 방법
Row 12: 용수 처리 방법
Row 13: 작업 방법
Row 14: 긴급조치 계획
Row 15: [섹션] 작업단계별 안전조치
Row 16: [표헤더] 순번 | 작업단계 | 위험요인 | 안전조치
Row 17~26: 데이터 10행
Row 27: [섹션] 확인 및 서명
Row 28: 작성자 | 검토자/확인자
Row 29: 서명공란 | 작성일
```

### 변경 후 (32행, A1:H32)

```
Row 1 : 제목 (변경 없음)
Row 2 : 부제 (변경 없음)
Row 3~6 : 메타 블록 (변경 없음)
Row 7 : [섹션] 법정 기재 사항 (제38조·제82조)  ← 라벨 소폭 수정
Row 8~14: 기존 법정 7항목 (변경 없음)
Row 15: 유도자 배치           ← NEW
Row 16: 출입통제 방법          ← NEW
Row 17: 비상연락망             ← NEW
Row 18: [섹션] 작업단계별 안전조치  (Row 15→18)
Row 19: [표헤더]                   (Row 16→19)
Row 20~29: 데이터 10행             (Row 17-26→20-29)
Row 30: [섹션] 확인 및 서명         (Row 27→30)
Row 31: 작성자 | 검토자/확인자      (Row 28→31)
Row 32: 서명공란 | 작성일           (Row 29→32)
```

**확장**: +3행 (29→32), print_area `A1:H29` → `A1:H32`

## 4. 구현 원칙

- 기존 meta 블록(Row 3~6), step table(10행 고정), 서명란 구조 유지
- `_write_legal_items()` 내 `legal_rows` 리스트에 3개 tuple 추가만 수행
- 행 높이: 기존 법정항목과 동일 30px
- 값 없으면 빈 셀 (기존 `_v()` 헬퍼 재사용)
- 섹션 헤더 라벨: `"법정 기재 사항 (산업안전보건기준에 관한 규칙 제38조·제82조)"`

## 5. form_registry.py 변경

`excavation_workplan` FormSpec의 `optional_fields`에 3개 추가:

```python
optional_fields=(
    "site_name", "project_name", "work_location", "work_date",
    "supervisor", "contractor",
    "guide_worker_required",   # ← NEW
    "access_control",          # ← NEW
    "emergency_contact",       # ← NEW
    "safety_steps",
    "sign_date",
),
```

## 6. 위험 분석

| 위험 | 대응 |
|------|------|
| 기존 xlsx bytes 크기 변화 | +3행으로 파일 크기 소폭 증가 — 검증 스크립트 `> 5000` 조건 유지 |
| print_area 변경 | `A1:H32` 로 명시 수정 — 기존 29행 이하 셀은 영향 없음 |
| education_log builder 영향 | 없음 (독립 파일) |
| risk_assessment builder 영향 | 없음 (독립 파일) |
| export API 계약 변경 | optional_fields만 추가, required_fields 불변 → 기존 클라이언트 영향 없음 |

## 7. 검증 기준

| 체크 | 기준 |
|------|------|
| xlsx 생성 성공 | build_form_excel('excavation_workplan', sample) → bytes > 0 |
| 신규 3필드 라벨 존재 | openpyxl 재열기 후 셀 값 확인 |
| 기존 법정 7항목 유지 | LEGAL_LABELS 7개 모두 존재 |
| 빈 form_data 허용 | build_form_excel('excavation_workplan', {}) → bytes > 0 |
| 회귀 없음 | validate_form_registry / validate_export_api 전 케이스 PASS |

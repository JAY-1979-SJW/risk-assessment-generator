# 교육일지 Excel Builder 구현 계획 v1

**작성일**: 2026-04-24
**근거**: `docs/design/form_schema_from_law.md §2`, `docs/design/form_generation_lock.md §3`
**대상 파일**: `engine/output/education_log_builder.py`

---

## 1. 필드 분류 확정

### 1.1 자동 채움 필드 (AUTO)

| 필드명 | 내용 | 생성 방법 |
|--------|------|----------|
| `subject_no` | 교육 과목 순번 | 1부터 자동 채번 |
| `attendee_no` | 수강자 순번 | 1부터 자동 채번 |
| `education_duration_hours` | 교육 시간 합계 | 입력값 그대로 표시 (호출자가 계산해 넘김) |
| `confirm_date` | 확인 일자 | 입력값 그대로 표시 (호출자가 채워 넘김, 없으면 공란) |

### 1.2 사용자 입력 필드 (USER → 값 없으면 공란 유지)

**메타 영역:**
| 필드명 | 한글명 | 법정 여부 |
|--------|--------|----------|
| `site_name` | 사업장명 | 관행 |
| `site_address` | 사업장 소재지 | 관행 |
| `education_type` | 교육 종류 | 법정 |
| `education_date` | 교육 일시 | 법정 |
| `education_location` | 교육 장소 | 법정 |
| `education_target_job` | 교육 대상 (직종·작업) | 법정 |

**강사 정보:**
| 필드명 | 한글명 | 법정 여부 |
|--------|--------|----------|
| `instructor_name` | 강사명 | 법정 |
| `instructor_qualification` | 강사 자격 | 법정 |

**교육 내용 (subjects 배열 각 항목):**
| 필드명 | 한글명 | 법정 여부 |
|--------|--------|----------|
| `subject_name` | 교육 과목명 | 법정 |
| `subject_content` | 교육 내용 요약 | 법정 |
| `subject_hours` | 해당 과목 시간 | 법정 |

**수강자 명단 (attendees 배열 각 항목):**
| 필드명 | 한글명 | 법정 여부 |
|--------|--------|----------|
| `attendee_name` | 성명 | 법정 |
| `attendee_job_type` | 직종(직위) | 법정 |

**확인 서명:**
| 필드명 | 한글명 | 법정 여부 |
|--------|--------|----------|
| `confirmer_name` | 확인자 성명 | 법정 |
| `confirmer_role` | 확인자 직위 | 법정 |

### 1.3 수강자 반복 행 (REPEAT)

- 최대 30행 고정 출력 (입력 수강자 수 ≤ 30)
- 입력된 수강자 데이터 이후 행: 공란 유지
- 수강자 서명란(`attendee_signature`): **항상 공란** (Excel에서 서명 입력 불가 → 출력 후 수기 서명)

### 1.4 강제 공란 필드

| 필드명 | 사유 |
|--------|------|
| `attendee_signature` | 수기 서명 전용 — Excel 생성 시 절대 채우지 않음 |
| 수강자 행 초과분 (31행~) | 미사용 행 — 공란 출력 |

---

## 2. 시트 레이아웃 (8컬럼 A-H)

### 2.1 컬럼 너비

| 컬럼 | 용도 | 너비 |
|------|------|------|
| A | 번호/레이블 | 6 |
| B | 성명/값 | 16 |
| C | 값 | 14 |
| D | 직종/값 | 12 |
| E | 레이블 | 10 |
| F | 서명/값 | 14 |
| G | 값 | 14 |
| H | 값 | 14 |

### 2.2 행 구조

```
Row 1   : 제목 "안전보건교육일지" (A:H 병합, 제목 스타일)
Row 2   : [사업장명 라벨:A] [site_name:B-D] [사업장 소재지:E] [site_address:F-H]
Row 3   : [교육 종류:A] [education_type:B-D] [교육 장소:E] [education_location:F-H]
Row 4   : [교육 일시:A] [education_date:B-D] [교육 시간:E] [education_duration_hours:F-H]
Row 5   : [교육 대상:A] [education_target_job:B-H]
Row 6   : [강사명:A] [instructor_name:B-D] [강사 자격:E] [instructor_qualification:F-H]
Row 7   : 섹션 헤더 "교육 내용" (A:H 병합)
Row 8   : 표 헤더 (순번|교육 과목명|교육 내용 요약|시간)
Row 9+  : subject 반복 행 (기본 3행, 입력에 따라 확장)
Row X   : 섹션 헤더 "수강자 명단" (A:H 병합)
Row X+1 : 표 헤더 (번호|성명|직종(직위)|서명 또는 날인)
Row X+2 : 수강자 행 × 30 (최대)
Row Y   : [확인자 성명:A] [confirmer_name:B-D] [확인자 직위:E] [confirmer_role:F-H]
Row Y+1 : [서명란:A] [공란:B-D] [확인 일자:E] [confirm_date:F-H]
```

### 2.3 컬럼 스팬 정의

**메타/강사 2분할 라벨-값:**
- 왼쪽: 라벨=A, 값=B:D (3컬럼)
- 오른쪽: 라벨=E, 값=F:H (3컬럼)

**교육 대상 (전체 폭 값):**
- 라벨=A, 값=B:H (7컬럼)

**교육 내용 표 헤더:**
- 순번=A, 교육 과목명=B:D, 교육 내용 요약=E:G, 시간(h)=H

**수강자 명단 표 헤더:**
- 번호=A, 성명=B:C, 직종(직위)=D:E, 서명 또는 날인=F:H

---

## 3. 함수 설계

```
build_education_log_excel(form_data: dict) -> bytes
  └─ render_education_log_sheet(ws, form_data) -> None
       ├─ _apply_col_widths(ws)
       ├─ _write_title(ws, row) -> int
       ├─ _write_meta_block(ws, row, form_data) -> int
       ├─ _write_subject_table(ws, row, subjects) -> int
       ├─ _write_attendee_table(ws, row, attendees) -> int
       └─ _write_confirmation(ws, row, form_data) -> int
```

---

## 4. 입력 스키마 (form_data dict)

```python
{
    "site_name": str | None,
    "site_address": str | None,
    "education_type": str | None,         # 정기교육 / 특별교육 / ...
    "education_date": str | None,
    "education_location": str | None,
    "education_duration_hours": str | float | None,
    "education_target_job": str | None,
    "instructor_name": str | None,
    "instructor_qualification": str | None,
    "subjects": [                          # 생략 시 빈 행 3개
        {
            "subject_name": str | None,
            "subject_content": str | None,
            "subject_hours": str | float | None,
        }
    ],
    "attendees": [                         # 생략 시 30행 공란
        {
            "attendee_name": str | None,
            "attendee_job_type": str | None,
        }
    ],
    "confirmer_name": str | None,
    "confirmer_role": str | None,
    "confirm_date": str | None,
}
```

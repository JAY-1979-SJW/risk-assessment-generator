# KRAS 표준 위험성평가표 본표 — Excel 레이아웃 스펙 v1

**상태**: LOCKED (v1 기간 중 컬럼 의미/순서 변경 금지)
**시행일**: 2026-04-23
**대상 모듈**: `engine/output/form_excel_builder.py`
**입력 스키마**: `data/risk_db/api_schema/kras_standard_form_v1.json` (form_builder 출력)
**준거**:
- 산업안전보건법 시행규칙 §37
- 고용노동부고시 제2023-19호 §7~§13
- 공문기반 본표 양식 v2 (`export/위험성평가표_공문기반_20250114_v2.xlsx`)
- `docs/standards/kras_standard_form_v1.md`

---

## 1. 시트 구성

1개 워크북, 1개 시트.

| 영역 | 위치 | 내용 |
|------|------|------|
| 제목 | 1행 | "위험성평가표 (실시표)" — 전체 컬럼 병합 |
| 메타 | 2~5행 | `header` 필드 (회사명, 현장명, 업종, 대표자, 평가종류, 평가일자, 작업유형) |
| 공백 | 6행 | 메타와 본문 구분 |
| 헤더 | 7행 | 본표 17컬럼 컬럼명 (1행 단일 헤더) |
| 본문 | 8행~ | `rows[]` 각 row = 1행 |

> 공식 서식은 2단 병합 헤더(대/중/소)를 쓰지만, v1 은 가독성과 DB 기반 재생성 용이성을 위해 **1행 단일 헤더**로 단순화한다. 컬럼 의미·순서는 공식 서식과 일치해야 한다.

---

## 2. 본표 17컬럼 (헤더 순서 고정)

| # | 컬럼명 | form_data 경로 | 타입 | 비고 |
|---|--------|----------------|------|------|
| 1 | 번호 | `rows[i].no` | int | 1부터 |
| 2 | 공정명 | `rows[i].process` | string | work_type 기반 |
| 3 | 세부작업명 | `rows[i].sub_work` | string? | null 허용, 건설업 특화 |
| 4 | 위험분류(대) | `rows[i].hazard_category_major` | string? | v1 에서는 항상 null → 빈칸 |
| 5 | 위험분류(중) | `rows[i].hazard_category_minor` | string? | v1 에서는 항상 null → 빈칸 |
| 6 | 유해위험요인 | `rows[i].hazard` | string | 필수 |
| 7 | 관련근거(법적기준) | `rows[i].legal_basis` | string? | `references_summary` 카운트 주석 제거값 |
| 8 | 현재의 안전보건조치 | `rows[i].current_measures` | string? | v1 에서는 항상 null → 빈칸 (사용자 입력 슬롯) |
| 9 | 평가척도 | `rows[i].risk_scale` | string | 기본 `"3x3"` |
| 10 | 가능성(빈도) | `rows[i].probability` | int | 1~3 |
| 11 | 중대성(강도) | `rows[i].severity` | int | 1~3 |
| 12 | 위험성 | `rows[i].risk_level` | int | 1~9 (= prob × sev) |
| 13 | 위험성 감소대책 | `rows[i].control_measures` | string[] | 줄바꿈(`\n`) join 으로 셀에 렌더 |
| 14 | 개선후 위험성 | `rows[i].residual_risk_level` | int | 1~9 |
| 15 | 개선 예정일 | `rows[i].target_date` | string? (YYYY-MM-DD) | null → 빈칸 |
| 16 | 완료일 | `rows[i].completion_date` | string? (YYYY-MM-DD) | null → 빈칸 |
| 17 | 담당자 | `rows[i].responsible_person` | string? | null → 빈칸 |

> **공종(work_category) 컬럼은 추가하지 않는다.** (form_builder_spec_lock.md 의 고정 정책)

---

## 3. 메타 영역 (2~5행)

2열 레이블 + 값 구조 (4행 × 2그룹 = 총 8슬롯).

```
[2행]  회사명 : {header.company_name}      │  업종       : {header.industry}
[3행]  현장명 : {header.site_name}         │  대표자     : {header.representative}
[4행]  평가종류: {header.assessment_type}   │  평가일자   : {header.assessment_date}
[5행]  작업유형: {header.work_type}         │  (빈칸)
```

- 값이 null/빈 문자열이면 빈 셀 유지.
- 레이블 셀은 옅은 배경색(회색), 값 셀은 기본 배경.

---

## 4. 렌더링 규칙

| 항목 | 규칙 |
|------|------|
| 글꼴 | "맑은 고딕" 10pt (제목 14pt bold, 헤더 10pt bold) |
| 한글 | 워크북 기본 인코딩 UTF-8 — 깨지지 않음 |
| 줄바꿈 | `control_measures` 는 `"\n".join(...)` 후 `wrap_text=True` |
| 정렬 | 숫자열(번호, 가능성, 중대성, 위험성, 개선후 위험성) = center / 나머지 = left top |
| 높이 | 본문 행 기본 auto. 최소 24px |
| 컬럼 폭 | 번호 6, 공정명 14, 세부작업명 20, 위험분류(대·중) 각 12, 유해위험요인 20, 관련근거 32, 현재조치 24, 평가척도 8, 가능성 8, 중대성 8, 위험성 8, 감소대책 40, 개선후 위험성 10, 개선예정일 12, 완료일 12, 담당자 16 |
| 테두리 | 헤더·본문 모든 셀 thin 실선 |
| 헤더 배경 | 옅은 회색 (`#D9E1F2`) |
| null 처리 | 모든 null/None → 빈 문자열("") 출력. 임의 값 생성 금지 |

---

## 5. 시트 출력 금지 필드

| 필드 | 사유 |
|------|------|
| `rows[i].references_detail` | `kras_standard_form_v1.md` §5.4 — 내부 추적 전용, 표 노출 금지 |
| `rows[i].risk_band` / `residual_risk_band` | 등급은 숫자(위험성) 컬럼으로 표현, 별도 문자열 컬럼 없음 |
| `scale_definition` | 내부 정의. 평가척도 컬럼에는 `risk_scale` 문자열만 표시 |
| `input_context` | v2 API enrichment echo. 시트 비출력 |

---

## 6. 파일 출력

- 반환값: `bytes` (in-memory xlsx 바이너리)
- 이유: API 응답 / 저장 로직과 분리. 샘플 파일 생성 시에만 파일로 저장.
- 파일명 규칙(샘플): `risk_form_sample_{case_tag}.xlsx`

---

## 7. 변경 이력

| 버전 | 날짜 | 변경 |
|------|------|------|
| v1 | 2026-04-23 | 최초 작성 — 17컬럼 고정, 공종 제외, 1행 단일 헤더 |

# Excel 본표 렌더링 품질 검증 보고서 v1

**생성일**: 2026-04-23
**대상 모듈**: `engine/output/form_excel_builder.py`
**입력 샘플**: `docs/sample_form_output_3cases.json` (form_builder 출력 3케이스)
**출력 파일**: `samples/risk_form_sample_3cases.xlsx` (3개 시트, 각 케이스 1개 시트)
**레이아웃 스펙**: `docs/standards/excel_layout_spec.md`

---

## 1. 검증 방법

1. `docs/sample_form_output_3cases.json` 3케이스 `form_output` 을 `render_form_sheet()` 로 각 시트에 렌더링.
2. 생성된 xlsx 를 `openpyxl.load_workbook` 로 재로드.
3. 각 케이스에 대해 아래 체크를 프로그램 기반으로 수행 (정적 수동 검토 아님).

---

## 2. 검증 항목별 결과

| # | 검증 항목 | CASE1 (전기) | CASE2 (밀폐) | CASE3 (고소) |
|---|-----------|:------------:|:------------:|:------------:|
| 1 | 공식 헤더 순서·라벨 일치 (17컬럼) | ✅ | ✅ | ✅ |
| 2 | 공종(work_category) 컬럼 없음 | ✅ | ✅ | ✅ |
| 3 | 행 수 = rows 수 | ✅ (4) | ✅ (4) | ✅ (4) |
| 4 | 공정명/세부작업명 2단 유지 | ✅ | ✅ | ✅ (sub_work=null → 빈칸) |
| 5 | 위험분류(대) 항상 빈칸 (v1 정책) | ✅ | ✅ | ✅ |
| 6 | 위험분류(중) 항상 빈칸 (v1 정책) | ✅ | ✅ | ✅ |
| 7 | 현재의 안전보건조치 빈칸 (사용자 입력 슬롯) | ✅ | ✅ | ✅ |
| 8 | 가능성/중대성/위험성 값 원본과 일치 | ✅ | ✅ | ✅ |
| 9 | 개선후 위험성 값 원본과 일치 | ✅ | ✅ | ✅ |
| 10 | 위험성 감소대책 다줄 렌더링 (`\n` 조인) | ✅ | ✅ | ✅ |
| 11 | references_detail 시트 미노출 | ✅ | ✅ | ✅ |
| 12 | 자동/수동 입력 필드 구분 (null 은 빈칸) | ✅ | ✅ | ✅ |

---

## 3. 헤더 검증 세부

확인된 헤더 라벨 순서 (7행):

```
번호 | 공정명 | 세부작업명 | 위험분류(대) | 위험분류(중) | 유해위험요인 |
관련근거(법적기준) | 현재의 안전보건조치 | 평가척도 | 가능성(빈도) | 중대성(강도) | 위험성 |
위험성 감소대책 | 개선후 위험성 | 개선 예정일 | 완료일 | 담당자
```

- 총 17 컬럼.
- 공종(work_category) 컬럼 **미포함** (form_builder_spec_lock 정책 준수).
- 컬럼 순서·라벨 `docs/standards/excel_layout_spec.md` §2 와 완전 일치.

---

## 4. 메타 영역 검증 (2~5행)

| 케이스 | 회사명 | 현장명 | 업종 | 대표자 | 평가종류 | 평가일자 | 작업유형 |
|--------|--------|--------|------|--------|----------|----------|----------|
| CASE1 | (주)해한 AI | OO빌딩 신축공사 옥상 전기설비 | 전기공사업 | 홍길동 | 수시평가 | 2026-04-23 | 전기작업 |
| CASE2 | (주)해한 AI | OO 하수처리장 맨홀 점검 | 환경설비공사업 | 홍길동 | 최초평가 | 2026-04-23 | 밀폐공간 작업 |
| CASE3 | (주)해한 AI | OO 공장 구조물 점검 | 건설업 | 홍길동 | 정기평가 | 2026-04-23 | 고소작업 |

- 7개 header 필드 모두 렌더링 확인.
- CASE3 은 optional_input 전체 null → 본문 담당자/개선 예정일/완료일 모두 빈칸.

---

## 5. 빈칸/null 처리

- `rows[i].sub_work` (CASE3), `target_date`, `completion_date`, `responsible_person` null → 빈 셀로 출력.
- `hazard_category_major/minor`, `current_measures` 는 v1 에서 항상 null → 빈 셀.
- 임의 값 생성 없음 (form_builder 출력 그대로 렌더).

---

## 6. 가독성

- `control_measures` 배열 → `\n` 조인, `wrap_text=True` 로 셀 내 줄바꿈.
- CASE1 1행 감소대책 7건(v1 최대치) 모두 1셀 내 7줄 줄바꿈으로 정상 렌더.
- 숫자 컬럼(번호, 가능성, 중대성, 위험성, 개선후 위험성) center 정렬.
- 텍스트 컬럼 left-top 정렬 + wrap_text.
- 한글 깨짐 없음 (UTF-8 기반 openpyxl 기본 저장).

---

## 7. 미출력 필드 확인

시트 컬럼 목록에 아래 필드는 **존재하지 않음** (의도 준수):

- `references_detail.law_ids` / `moel_expc_ids` / `kosha_ids`
- `risk_band`, `residual_risk_band` (등급 문자열 — 숫자 컬럼으로 대체 표현)
- `scale_definition` 전체
- `input_context`
- `work_category` (공종)

---

## 8. 최종 판정

**PASS**

- 3케이스 모두 공식 17컬럼 헤더 순서·라벨 일치
- 공종 컬럼 미혼입
- 값 누락·왜곡 없음
- references_detail 미노출
- 자동(v1 정책) 빈칸 vs 사용자 미입력(optional) 빈칸의 동작 일관

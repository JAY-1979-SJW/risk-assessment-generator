# 서식 수집 실행 로그 v2

**최초 실행**: 2026-04-23 (v1, 로컬 112건 이전)
**확장 실행**: 2026-04-23 (v2, 외부 P1 격차 보강 수집)
**스크립트**:
- v1 로컬 이전: `scripts/collect_forms_to_repository.py`
- v2 licbyl 확장: `scripts/collect_licbyl_gap_forms.py`
- v2 KOSHA/MOEL/법령: `scripts/collect_kosha_external_forms.py`
- v2 권위뷰 ingest: `scripts/ingest_new_forms_to_repository.py`

**근거**: `docs/standards/form_repository_layout.md`, `docs/standards/form_priority_queue.md`

---

## v2 확장 요약 (2026-04-23 P1 격차 보강)

### 신규 수집 출처

| 출처 | 방식 | 신규 확보 |
|------|------|-----------|
| 국가법령정보 licbyl OpenAPI (data.go.kr) | 8 키워드 확장 검색 후 산업안전보건 관련만 유지 | **12** 별지/별표 (hwp+pdf 쌍 24 파일) |
| KOSHA Guide (oshri.kosha.or.kr/extappKosha) | 직접 URL 다운로드 | **9** PDF (C-102, C-39, E-154, H-80, X-68, P-94, Z-5, Z-47, ebook 2건) |
| KOSHA 자료실 (oshri.kosha.or.kr/kosha/data) | articleNo/attachNo 직접 다운로드 | **3** 파일 (조선업 작업계획서, 고소작업대, 밀폐공간) |
| MOEL 지방청 (moel.go.kr/local/uijeongbu) | 직접 URL + 세션 재시도 | **1** hwp (안전보건교육일지) |
| 법령정보센터 LSW (law.go.kr/LSW/flDownload) | 세션 재시도 | **1** PDF ([별표 2의2] 산업안전보건위원회 회의록 양식) |

**합계 신규 38 행** (source_map.csv 기준), 실제 물리 파일은 licbyl 12×2 + 외부 15 = 39 파일, 이 중 중복 해시 1건 제외하여 v2 ingest 38행.

### 누적 수집 현황 (v1 + v2 최종)

| 항목 | v1 | v2 추가 | 최종 |
|------|-----|---------|------|
| 총 파일 (forms/ 권위 뷰) | 112 | +39 | **151** |
| 권위 A | 43 | +25 | **68** |
| 권위 B | 64 | +14 | **78** |
| 권위 C | 5 | 0 | **5** |
| LAW 출처 | 34 | +25 | **59** |
| MOEL 출처 | 68 | +1 | **69** |
| KOSHA 출처 | 1 | +13 | **14** |
| INTERNAL 출처 | 9 | 0 | **9** |
| hwp | 51 | +14 | **65** |
| hwpx | 51 | 0 | **51** |
| pdf | 0 | +24 | **24** |
| xlsx/xls/docx/doc | 10 | +1 | **11** |

### doc_type 최종 분포

| doc_type | 건수 | 비고 |
|----------|------|------|
| 별지 | 46 | licbyl 32 + v2 확장 14 (제1, 9, 11, 13, 14, 30, 55호 등) |
| 별표 | 18 | v1 8 + v2 10 (교육시간/대상·교육기관 기준·산업재해발생률 등) |
| 자율점검표 | 24 | MOEL 업종별 |
| 가이드 | 22 | |
| 작업계획서 | 10 | **v2 신규** — 조선업·중량물·전기·굴착·고소작업대 2·밀폐공간 2·용접·안전작업절차 |
| 표준모델 | 6 | |
| 테스트 | 5 | |
| TBM | 4 | v1 2 + v2 2 (Z-5-2022 작업전 안전회의, TBM 실행 시나리오·회의록) |
| 안내서 | 4 | |
| 계획서 | 4 | 유해위험방지계획서 (v1) |
| 본표 | 2 | |
| 표준안 | 1 | KRAS 경비 |
| 본표_축약 | 1 | KRAS 12컬럼 |
| 규정 | 1 | 표준실시규정 |
| 안전작업매뉴얼 | 1 | **v2 신규** — 밀폐공간 |
| 교육일지 | 1 | **v2 신규** — MOEL 의정부지청 |
| 회의록 | 1 | **v2 신규** — 산업안전보건위원회 법정 별표 2의2 |

### P1 핵심 확보 체크

| 우선 서식 | 요구 | 확보 | 파일 위치 |
|-----------|------|------|-----------|
| **작업계획서 (3종 이상)** | 3 | **10** ✅ | `data/forms/B_semi_official/kosha_form/KOSHA__작업계획서__*.pdf` |
| **산업재해조사표 (별지 30호)** | 1 | **1** ✅ | `data/forms/A_official/licbyl/LAW__별지__산업재해조사표_제30호서식__N_A.hwp(+pdf)` |
| **교육일지/TBM (1종 이상)** | 1 | **5** ✅ | 교육일지 1 + TBM 4 |
| **산업안전보건위원회 회의록** | 1 | **1** ✅ | `data/forms/A_official/licbyl/LAW__회의록__별표_2의2_산업안전보건위원회_회의록_양식_법정_별표__N_A.pdf` |

### v2 수집 실패/한계

| 항목 | 사유 | 조치 |
|------|------|------|
| licbyl 확장 첫 실행시 802 HTTP 502 | data.go.kr API 간헐 장애 | 필터를 산업안전보건 전용으로 좁혀 재실행. 잘못 받은 792개 폴더는 정리 후 스킵. |
| `www.kosha.or.kr` 서브도메인 직접 다운로드 | 1993B HTML 페이지 응답 — 미로그인 가드 | `oshri.kosha.or.kr` 미러로 치환하여 성공 |
| `edu.kosha.or.kr` 교육일지 URL | 301 → 홈 리다이렉트 (dead link) | MOEL 의정부지청 URL로 대체 확보 |
| 굴착작업 전용 작업계획서 (별도 단일 양식) | 법정 별지 없음. KOSHA C-39-2023(지침) + C-104 기술지침 확보로 대체 | 구조 분석 단계에서 실측 |

---

## v1 요약 (기보유 로컬 수집본 이전)

- 복사 성공: **112**
- 스킵: **277**
- 실패: **0**
- 총 처리 대상 (스크립트 스캔 범위): **389**

### 권위 분류 (source_map.csv 기준)

| 등급 | 건수 |
|------|------|
| A (법정·공단 공식) | 43 |
| B (준공식·MOEL/KOSHA 배포) | 64 |
| C (내부·테스트) | 5 |
| **합계** | **112** |

### 출처 분류

| 출처 | 건수 |
|------|------|
| LAW (licbyl 법령 별지·별표) | 34 |
| MOEL (정책자료실 배포) | 68 |
| INTERNAL (내부) | 9 |
| KOSHA (참조자료 xls) | 1 |
| **합계** | **112** |

### 형식 분류

| 형식 | 건수 |
|------|------|
| hwp | 51 |
| hwpx | 51 |
| xlsx | 8 |
| xls | 1 |
| docx | 1 |
| **합계** | **112** |

### 문서 유형 분류

| doc_type | 건수 | 비고 |
|----------|------|------|
| 별지 | 32 | licbyl 13 + 별표 재분류 2 + MOEL 재배포 6 등 |
| 별표 | 8 | |
| 자율점검표 | 24 | 업종별 MOEL 점검표 |
| 가이드 | 22 | MOEL 업종 가이드 |
| 표준모델 | 6 | MOEL 위험성평가 표준모델 |
| 안내서 | 4 | |
| 계획서 | 4 | "계획서" 키워드 매치 (실제 작업계획서 원본 아님 — §격차 참조) |
| TBM | 2 | MOEL 지침문서 (회의록 템플릿 아님) |
| 테스트 | 5 | 개발 샘플 |
| 본표 | 2 | 공문기반 v1/v2 |
| 규정 | 1 | 표준실시규정.docx |
| 표준안 | 1 | 경비 xls |
| 본표_축약 | 1 | KRAS 12컬럼 |

---

## 의도적 제외 범위 (본 스크립트 스캔 대상 외)

1. **`scraper/kosha_files/` KOSHA OPS 2,382 PDF + 400 zip + 기타** — 대부분 교재·안내서·포스터이며 "편집형 서식 템플릿"이 아니므로 `docs/standards/form_repository_layout.md` §5 규정대로 **권위 뷰 진입 제외**. 본 레포 내 `scraper/kosha_files/` 그대로 보존.
2. **`scraper/kosha_files/**/*.hwp` 5건** — Step 4 분류 시 개별 열람 후 편집형 서식으로 확인되면 `B_semi_official/kosha_form`으로 추가 진입 예정.
3. **`data/raw/kosha/`, `data/raw/kosha_forms/` JSON 메타** — 바이너리 원본 아님. Step 3 대상 아님.
4. **MOEL 정책자료실 서식 비관련 277건** — "개정법률", "옴부즈만", "공고문" 등 법 개정문/조직 발표문. 본 스크립트는 서식성 키워드가 없는 파일을 자동 스킵.

---

## 스크립트 자동 스킵 사유 (277건)

- 전건 사유: **"서식성 키워드 미포함"**
- 판정 규칙: `scripts/collect_forms_to_repository.py` 의 `doc_type_of_moel()` 함수 — (`점검표` / `자율점검표` / `표준모델` / `표준안` / `안내서` / `가이드` / `별지` + `서식` / `계획서` / `TBM` / `교육` / `실시규정` / `중대재해` + `서식`) 중 **어느 하나라도 포함해야 진입**.
- 향후 추가 진입이 필요한 특수 파일은 `INTERNAL_RULES` 또는 키워드 세트를 확장하여 재실행.

---

## 격차 (외부 수집이 필요하나 이번 실행에서 확보 못함)

본 실행은 **로컬 수집본 재정리**만 수행. 아래 항목은 외부 공공 포털에서의 추가 다운로드가 필요하며, 현 세션에서 웹 접근성 한계로 실제 파일 저장은 보류한다.

| 격차 | 상태 | 다음 조치 |
|------|------|-----------|
| 작업계획서 표준양식 (산안법 시행규칙과 별개 "기준규칙" 제38·39·40·42·49·54조 기반) | **미확보 (0건)** | ① `kosha.or.kr` 기술자료실 "작업계획서" 검색, ② MOEL 업종 가이드 부록 발췌 — 별도 세션에서 수동/자동 다운로드 필요 |
| TBM 회의록·일지 템플릿 | **미확보** (현존 2건은 정책문서) | KOSHA 안전보건 참고자료 검색 |
| 교육일지 (시행규칙 별지 제52호의2서식 추정) | **미확보** | licbyl API에 해당 lawId 추가 수집 |
| 산업재해조사표 (시행규칙 별지 제30호서식) | **미확보** | licbyl API 추가 |
| 산업안전보건기준에 관한 규칙 별지 전체 | **미확보** (본 수집은 시행규칙만 커버) | licbyl API에 기준규칙 lawId 추가 |
| 유해위험방지계획서 첨부 세부양식 | **부분 확보** (별지 19·22 본표만) | 첨부 서식은 KOSHA 기술자료실 |

---

## 상세 (최초 500건)

| # | action | source | detail |
|---|--------|--------|--------|
| 1 | copied | `data/raw/law_api/licbyl/files/17853601/[별표 2] 안전보건관리규정을 작성해야 할 사업의 .hwp` | LAW__별표__안전보건관리규정을_작성해야_할_사업의_2__N_A.hwp |
| 2 | copied | `data/raw/law_api/licbyl/files/17853601/[별표 2] 안전보건관리규정을 작성해야 할 사업의 .hwpx` | LAW__별표__안전보건관리규정을_작성해야_할_사업의_2__N_A.hwpx |
| 3 | copied | `data/raw/law_api/licbyl/files/17853603/[별표 3] 안전보건관리규정의 세부 내용(제25조제2항.hwp` | LAW__별표__안전보건관리규정의_세부_내용_제25조제2항_3__N_A.hwp |
| 4 | copied | `data/raw/law_api/licbyl/files/17853603/[별표 3] 안전보건관리규정의 세부 내용(제25조제2항.hwpx` | LAW__별표__안전보건관리규정의_세부_내용_제25조제2항_3__N_A.hwpx |
| 5 | copied | `data/raw/law_api/licbyl/files/17853655/[별지 제2호서식] 안전관리자ㆍ보건관리자ㆍ산업�.hwp` | LAW__별지__안전관리자_보건관리자_산업_제2호서식__N_A.hwp |
| 6 | copied | `data/raw/law_api/licbyl/files/17853655/[별지 제2호서식] 안전관리자ㆍ보건관리자ㆍ산업�.hwpx` | LAW__별지__안전관리자_보건관리자_산업_제2호서식__N_A.hwpx |
| 7 | copied | `data/raw/law_api/licbyl/files/17853657/[별지 제3호서식] 안전관리자ㆍ보건관리자ㆍ산업�.hwp` | LAW__별지__안전관리자_보건관리자_산업_제3호서식__N_A.hwp |
| 8 | copied | `data/raw/law_api/licbyl/files/17853657/[별지 제3호서식] 안전관리자ㆍ보건관리자ㆍ산업�.hwpx` | LAW__별지__안전관리자_보건관리자_산업_제3호서식__N_A.hwpx |
| 9 | copied | `data/raw/law_api/licbyl/files/17853659/[별지 제3호의2서식] 안전관리자ㆍ보건관리자ㆍ산%E.hwp` | LAW__별지__안전관리자_보건관리자_산E_제3호의2서식__N_A.hwp |
| 10 | copied | `data/raw/law_api/licbyl/files/17853659/[별지 제3호의2서식] 안전관리자ㆍ보건관리자ㆍ산%E.hwpx` | LAW__별지__안전관리자_보건관리자_산E_제3호의2서식__N_A.hwpx |
| 11 | copied | `data/raw/law_api/licbyl/files/17853663/[별지 제5호서식] 안전ㆍ보건관리 업무계약서(산�.hwp` | LAW__별지__안전_보건관리_업무계약서_산_제5호서식__N_A.hwp |
| 12 | copied | `data/raw/law_api/licbyl/files/17853663/[별지 제5호서식] 안전ㆍ보건관리 업무계약서(산�.hwpx` | LAW__별지__안전_보건관리_업무계약서_산_제5호서식__N_A.hwpx |
| 13 | copied | `data/raw/law_api/licbyl/files/17853665/[별지 제6호서식] 지정신청서(법인 등 신청용)(안�.hwp` | LAW__별지__지정신청서_법인_등_신청용_안_제6호서식__N_A.hwp |
| 14 | copied | `data/raw/law_api/licbyl/files/17853665/[별지 제6호서식] 지정신청서(법인 등 신청용)(안�.hwpx` | LAW__별지__지정신청서_법인_등_신청용_안_제6호서식__N_A.hwpx |
| 15 | copied | `data/raw/law_api/licbyl/files/17853667/[별지 제6호의2서식] (안전관리전문기관¸ 보건관�%A.hwp` | LAW__별지__안전관리전문기관_보건관A_제6호의2서식__N_A.hwp |
| 16 | copied | `data/raw/law_api/licbyl/files/17853667/[별지 제6호의2서식] (안전관리전문기관¸ 보건관�%A.hwpx` | LAW__별지__안전관리전문기관_보건관A_제6호의2서식__N_A.hwpx |
| 17 | copied | `data/raw/law_api/licbyl/files/17853671/[별지 제7호의2서식] 지정서(산업안전ㆍ보건지도�%A.hwp` | LAW__별지__지정서_산업안전_보건지도A_제7호의2서식__N_A.hwp |
| 18 | copied | `data/raw/law_api/licbyl/files/17853671/[별지 제7호의2서식] 지정서(산업안전ㆍ보건지도�%A.hwpx` | LAW__별지__지정서_산업안전_보건지도A_제7호의2서식__N_A.hwpx |
| 19 | copied | `data/raw/law_api/licbyl/files/17853673/[별지 제8호서식] 변경신청서(법인 등 신청용)(안�.hwp` | LAW__별지__변경신청서_법인_등_신청용_안_제8호서식__N_A.hwp |
| 20 | copied | `data/raw/law_api/licbyl/files/17853673/[별지 제8호서식] 변경신청서(법인 등 신청용)(안�.hwpx` | LAW__별지__변경신청서_법인_등_신청용_안_제8호서식__N_A.hwpx |
| 21 | copied | `data/raw/law_api/licbyl/files/17853675/[별지 제8호의2서식] (안전관리전문기관¸ 보건관�%A.hwp` | LAW__별지__안전관리전문기관_보건관A_제8호의2서식__N_A.hwp |
| 22 | copied | `data/raw/law_api/licbyl/files/17853675/[별지 제8호의2서식] (안전관리전문기관¸ 보건관�%A.hwpx` | LAW__별지__안전관리전문기관_보건관A_제8호의2서식__N_A.hwpx |
| 23 | copied | `data/raw/law_api/licbyl/files/17853697/[별지 제19호서식] 유해위험방지계획서 산업안전�%8.hwp` | LAW__별지__유해위험방지계획서_산업안전8_제19호서식__N_A.hwp |
| 24 | copied | `data/raw/law_api/licbyl/files/17853697/[별지 제19호서식] 유해위험방지계획서 산업안전�%8.hwpx` | LAW__별지__유해위험방지계획서_산업안전8_제19호서식__N_A.hwpx |
| 25 | copied | `data/raw/law_api/licbyl/files/17853703/[별지 제22호서식] 유해위험방지계획서 산업안전�%8.hwp` | LAW__별지__유해위험방지계획서_산업안전8_제22호서식__N_A.hwp |
| 26 | copied | `data/raw/law_api/licbyl/files/17853703/[별지 제22호서식] 유해위험방지계획서 산업안전�%8.hwpx` | LAW__별지__유해위험방지계획서_산업안전8_제22호서식__N_A.hwpx |
| 27 | copied | `data/raw/law_api/licbyl/files/17853867/[별지 제102호서식] 산업안전보건관리비 사용계획�%.hwp` | LAW__별지__산업안전보건관리비_사용계획_제102호서식__N_A.hwp |
| 28 | copied | `data/raw/law_api/licbyl/files/17853867/[별지 제102호서식] 산업안전보건관리비 사용계획�%.hwpx` | LAW__별지__산업안전보건관리비_사용계획_제102호서식__N_A.hwpx |
| 29 | copied | `data/raw/law_api/licbyl/files/17973935/[별지 제240호서식] 산업안전지도사ㆍ산업보건지도%.hwp` | LAW__별지__산업안전지도사_산업보건지도_제240호서식__N_A.hwp |
| 30 | copied | `data/raw/law_api/licbyl/files/17973935/[별지 제240호서식] 산업안전지도사ㆍ산업보건지도%.hwpx` | LAW__별지__산업안전지도사_산업보건지도_제240호서식__N_A.hwpx |
| 31 | copied | `data/raw/law_api/licbyl/files/18014263/[별표 2] 안전보건관리책임자를 두어야 하는 사업�.hwp` | LAW__별표__안전보건관리책임자를_두어야_하는_사업_2__N_A.hwp |
| 32 | copied | `data/raw/law_api/licbyl/files/18014263/[별표 2] 안전보건관리책임자를 두어야 하는 사업�.hwpx` | LAW__별표__안전보건관리책임자를_두어야_하는_사업_2__N_A.hwpx |
| 33 | copied | `data/raw/law_api/licbyl/files/18014277/[별표 9] 산업안전보건위원회를 구성해야 할 사업�.hwp` | LAW__별표__산업안전보건위원회를_구성해야_할_사업_9__N_A.hwp |
| 34 | copied | `data/raw/law_api/licbyl/files/18014277/[별표 9] 산업안전보건위원회를 구성해야 할 사업�.hwpx` | LAW__별표__산업안전보건위원회를_구성해야_할_사업_9__N_A.hwpx |
| 35 | skipped | `data/raw/moel_forms/policy_data/files/1159169249136/「산업안전보건 옴부즈만」개요(홍보팀).hwp` | 서식성 키워드 미포함 |
| 36 | skipped | `data/raw/moel_forms/policy_data/files/1159169249136/「산업안전보건 옴부즈만」개요(홍보팀).hwpx` | 서식성 키워드 미포함 |
| 37 | skipped | `data/raw/moel_forms/policy_data/files/1159169249136/「산업안전보건 옴부즈만」명단(최종, 종서식).hwp` | 서식성 키워드 미포함 |
| 38 | skipped | `data/raw/moel_forms/policy_data/files/1159169249136/「산업안전보건 옴부즈만」명단(최종, 종서식).hwpx` | 서식성 키워드 미포함 |
| 39 | skipped | `data/raw/moel_forms/policy_data/files/1159174095649/산업안전보건법 개정법률.hwp` | 서식성 키워드 미포함 |
| 40 | skipped | `data/raw/moel_forms/policy_data/files/1159174095649/산업안전보건법 개정법률.hwpx` | 서식성 키워드 미포함 |
| 41 | skipped | `data/raw/moel_forms/policy_data/files/1159174418317/산업안전보건법시행령 일부개정령.hwp` | 서식성 키워드 미포함 |
| 42 | skipped | `data/raw/moel_forms/policy_data/files/1159174418317/산업안전보건법시행령 일부개정령.hwpx` | 서식성 키워드 미포함 |
| 43 | skipped | `data/raw/moel_forms/policy_data/files/1159176690167/산업안전보건법시행규칙 일부개정령.hwp` | 서식성 키워드 미포함 |
| 44 | skipped | `data/raw/moel_forms/policy_data/files/1159176690167/산업안전보건법시행규칙 일부개정령.hwpx` | 서식성 키워드 미포함 |
| 45 | skipped | `data/raw/moel_forms/policy_data/files/1159252440998/200606산재현황인터넷.hwp` | 서식성 키워드 미포함 |
| 46 | skipped | `data/raw/moel_forms/policy_data/files/1159252440998/200606산재현황인터넷.hwpx` | 서식성 키워드 미포함 |
| 47 | skipped | `data/raw/moel_forms/policy_data/files/1160358928661/산업안전보건법시행령 일부개정령.hwp` | 서식성 키워드 미포함 |
| 48 | skipped | `data/raw/moel_forms/policy_data/files/1160358928661/산업안전보건법시행령 일부개정령.hwpx` | 서식성 키워드 미포함 |
| 49 | skipped | `data/raw/moel_forms/policy_data/files/1160358928661/산업안전보건위 설치안내문2.hwp` | 서식성 키워드 미포함 |
| 50 | skipped | `data/raw/moel_forms/policy_data/files/1160358928661/산업안전보건위 설치안내문2.hwpx` | 서식성 키워드 미포함 |
| 51 | skipped | `data/raw/moel_forms/policy_data/files/1166595887102/200609산재현황인터넷.hwp` | 서식성 키워드 미포함 |
| 52 | skipped | `data/raw/moel_forms/policy_data/files/1166595887102/200609산재현황인터넷.hwpx` | 서식성 키워드 미포함 |
| 53 | skipped | `data/raw/moel_forms/policy_data/files/1172040037133/(0)정책자료(고시개정내용).hwp` | 서식성 키워드 미포함 |
| 54 | skipped | `data/raw/moel_forms/policy_data/files/1172040037133/(0)정책자료(고시개정내용).hwpx` | 서식성 키워드 미포함 |
| 55 | skipped | `data/raw/moel_forms/policy_data/files/1175231275779/'06년도결산보고서 최종-전체.hwp` | 서식성 키워드 미포함 |
| 56 | skipped | `data/raw/moel_forms/policy_data/files/1175231275779/'06년도결산보고서 최종-전체.hwpx` | 서식성 키워드 미포함 |
| 57 | skipped | `data/raw/moel_forms/policy_data/files/1176107161442/(0)출장소운영처리지침.hwp` | 서식성 키워드 미포함 |
| 58 | skipped | `data/raw/moel_forms/policy_data/files/1176107161442/(0)출장소운영처리지침.hwpx` | 서식성 키워드 미포함 |
| 59 | skipped | `data/raw/moel_forms/policy_data/files/1176277674668/(0)조선업 안전관리 평가표(최종).hwp` | 서식성 키워드 미포함 |
| 60 | skipped | `data/raw/moel_forms/policy_data/files/1176277674668/(0)조선업 안전관리 평가표(최종).hwpx` | 서식성 키워드 미포함 |
| 61 | skipped | `data/raw/moel_forms/policy_data/files/1176363407267/(3)2006산재현황(인터넷).hwp` | 서식성 키워드 미포함 |
| 62 | skipped | `data/raw/moel_forms/policy_data/files/1176363407267/(3)2006산재현황(인터넷).hwpx` | 서식성 키워드 미포함 |
| 63 | skipped | `data/raw/moel_forms/policy_data/files/1176795143992/0416 국제근로감독협 보도자료(최종).hwp` | 서식성 키워드 미포함 |
| 64 | skipped | `data/raw/moel_forms/policy_data/files/1176795143992/0416 국제근로감독협 보도자료(최종).hwpx` | 서식성 키워드 미포함 |
| 65 | skipped | `data/raw/moel_forms/policy_data/files/1178674517282/'06산재현황(최종수정-인터넷).hwp` | 서식성 키워드 미포함 |
| 66 | skipped | `data/raw/moel_forms/policy_data/files/1178674517282/'06산재현황(최종수정-인터넷).hwpx` | 서식성 키워드 미포함 |
| 67 | skipped | `data/raw/moel_forms/policy_data/files/1182412032964/(0)'0703재현황(인터넷).hwp` | 서식성 키워드 미포함 |
| 68 | skipped | `data/raw/moel_forms/policy_data/files/1182412032964/(0)'0703재현황(인터넷).hwpx` | 서식성 키워드 미포함 |
| 69 | skipped | `data/raw/moel_forms/policy_data/files/1188197073939/(0)관리책임자 등 선임보고서.hwp` | 서식성 키워드 미포함 |
| 70 | skipped | `data/raw/moel_forms/policy_data/files/1188197073939/(0)관리책임자 등 선임보고서.hwpx` | 서식성 키워드 미포함 |
| 71 | skipped | `data/raw/moel_forms/policy_data/files/1188454402763/'0706재현황(인터넷).hwp` | 서식성 키워드 미포함 |
| 72 | skipped | `data/raw/moel_forms/policy_data/files/1188454402763/'0706재현황(인터넷).hwpx` | 서식성 키워드 미포함 |
| 73 | skipped | `data/raw/moel_forms/policy_data/files/1193041486256/(0)산업안전보건법 시행규칙 개정안.hwp` | 서식성 키워드 미포함 |
| 74 | skipped | `data/raw/moel_forms/policy_data/files/1193041486256/(0)산업안전보건법 시행규칙 개정안.hwpx` | 서식성 키워드 미포함 |
| 75 | skipped | `data/raw/moel_forms/policy_data/files/1197014864091/'0709재해현황(인터넷).hwp` | 서식성 키워드 미포함 |
| 76 | skipped | `data/raw/moel_forms/policy_data/files/1197014864091/'0709재해현황(인터넷).hwpx` | 서식성 키워드 미포함 |
| 77 | skipped | `data/raw/moel_forms/policy_data/files/1204869444394/'0712재해현황(인터넷-최종).hwp` | 서식성 키워드 미포함 |
| 78 | skipped | `data/raw/moel_forms/policy_data/files/1204869444394/'0712재해현황(인터넷-최종).hwpx` | 서식성 키워드 미포함 |
| 79 | skipped | `data/raw/moel_forms/policy_data/files/1206522110994/(0)'07회계연도 산업재해보상보험및예방기금 결산보고서(최종).hwp` | 서식성 키워드 미포함 |
| 80 | skipped | `data/raw/moel_forms/policy_data/files/1206522110994/(0)'07회계연도 산업재해보상보험및예방기금 결산보고서(최종).hwpx` | 서식성 키워드 미포함 |
| 81 | skipped | `data/raw/moel_forms/policy_data/files/1213229982792/'0803재해현황(인터넷).hwp` | 서식성 키워드 미포함 |
| 82 | skipped | `data/raw/moel_forms/policy_data/files/1213229982792/'0803재해현황(인터넷).hwpx` | 서식성 키워드 미포함 |
| 83 | skipped | `data/raw/moel_forms/policy_data/files/1217899380679/0804 08년 상반기 산재통계.hwp` | 서식성 키워드 미포함 |
| 84 | skipped | `data/raw/moel_forms/policy_data/files/1217899380679/0804 08년 상반기 산재통계.hwpx` | 서식성 키워드 미포함 |
| 85 | skipped | `data/raw/moel_forms/policy_data/files/1220573461362/080904 산업안전 통계(7월최종).hwp` | 서식성 키워드 미포함 |
| 86 | skipped | `data/raw/moel_forms/policy_data/files/1220573461362/080904 산업안전 통계(7월최종).hwpx` | 서식성 키워드 미포함 |
| 87 | skipped | `data/raw/moel_forms/policy_data/files/1223856043364/08년 8월말 산재통계.hwp` | 서식성 키워드 미포함 |
| 88 | skipped | `data/raw/moel_forms/policy_data/files/1223856043364/08년 8월말 산재통계.hwpx` | 서식성 키워드 미포함 |
| 89 | skipped | `data/raw/moel_forms/policy_data/files/1225847275903/08년 9월말 산재통계.hwp` | 서식성 키워드 미포함 |
| 90 | skipped | `data/raw/moel_forms/policy_data/files/1225847275903/08년 9월말 산재통계.hwpx` | 서식성 키워드 미포함 |
| 91 | skipped | `data/raw/moel_forms/policy_data/files/1228704123852/08년 10월말 산재통계(최종).hwp` | 서식성 키워드 미포함 |
| 92 | skipped | `data/raw/moel_forms/policy_data/files/1228704123852/08년 10월말 산재통계(최종).hwpx` | 서식성 키워드 미포함 |
| 93 | skipped | `data/raw/moel_forms/policy_data/files/1230614312846/(0)지정교육기관 현황_안전보건정책과_090102.hwp` | 서식성 키워드 미포함 |
| 94 | skipped | `data/raw/moel_forms/policy_data/files/1230614312846/(0)지정교육기관 현황_안전보건정책과_090102.hwpx` | 서식성 키워드 미포함 |
| 95 | skipped | `data/raw/moel_forms/policy_data/files/1230618966058/(1)안전관리대행기관(86개소).hwp` | 서식성 키워드 미포함 |
| 96 | skipped | `data/raw/moel_forms/policy_data/files/1230618966058/(1)안전관리대행기관(86개소).hwpx` | 서식성 키워드 미포함 |
| 97 | skipped | `data/raw/moel_forms/policy_data/files/1230710488412/운반작업 안전관리(1230).hwp` | 서식성 키워드 미포함 |
| 98 | skipped | `data/raw/moel_forms/policy_data/files/1230710488412/운반작업 안전관리(1230).hwpx` | 서식성 키워드 미포함 |
| 99 | skipped | `data/raw/moel_forms/policy_data/files/1231393907294/08년 11월말 산재통계(최종).hwp` | 서식성 키워드 미포함 |
| 100 | skipped | `data/raw/moel_forms/policy_data/files/1231393907294/08년 11월말 산재통계(최종).hwpx` | 서식성 키워드 미포함 |
| 101 | skipped | `data/raw/moel_forms/policy_data/files/1233887095516/08년_산재통계_외국인수정.hwp` | 서식성 키워드 미포함 |
| 102 | skipped | `data/raw/moel_forms/policy_data/files/1233887095516/08년_산재통계_외국인수정.hwpx` | 서식성 키워드 미포함 |
| 103 | skipped | `data/raw/moel_forms/policy_data/files/1237286825463/08산업재해보상보험및예방기금결산서(유인).hwp` | 서식성 키워드 미포함 |
| 104 | skipped | `data/raw/moel_forms/policy_data/files/1237286825463/08산업재해보상보험및예방기금결산서(유인).hwpx` | 서식성 키워드 미포함 |
| 105 | skipped | `data/raw/moel_forms/policy_data/files/1267056611219/(0)0912월_산재통계(인터넷).hwp` | 서식성 키워드 미포함 |
| 106 | skipped | `data/raw/moel_forms/policy_data/files/1267056611219/(0)0912월_산재통계(인터넷).hwpx` | 서식성 키워드 미포함 |
| 107 | skipped | `data/raw/moel_forms/policy_data/files/1274148449703/1003월_산재통계.hwp` | 서식성 키워드 미포함 |
| 108 | skipped | `data/raw/moel_forms/policy_data/files/1274148449703/1003월_산재통계.hwpx` | 서식성 키워드 미포함 |
| 109 | skipped | `data/raw/moel_forms/policy_data/files/1290406595344/(0)100122_재해예방전문지도기관_평가결과.hwp` | 서식성 키워드 미포함 |
| 110 | skipped | `data/raw/moel_forms/policy_data/files/1290406595344/(0)100122_재해예방전문지도기관_평가결과.hwpx` | 서식성 키워드 미포함 |
| 111 | copied | `data/raw/moel_forms/policy_data/files/1291083677148/(2)2010년 동절기 안전보건 가이드라인.hwp` | MOEL__가이드__2_2010년_동절기_안전보건_가이드라인__N_A.hwp |
| 112 | copied | `data/raw/moel_forms/policy_data/files/1291083677148/(2)2010년 동절기 안전보건 가이드라인.hwpx` | MOEL__가이드__2_2010년_동절기_안전보건_가이드라인__N_A.hwpx |
| 113 | skipped | `data/raw/moel_forms/policy_data/files/1296094157064/1012월_산재통계.hwp` | 서식성 키워드 미포함 |
| 114 | skipped | `data/raw/moel_forms/policy_data/files/1296094157064/1012월_산재통계.hwpx` | 서식성 키워드 미포함 |
| 115 | skipped | `data/raw/moel_forms/policy_data/files/1298286186517/(0)1012월_산재통계(최종).hwp` | 서식성 키워드 미포함 |
| 116 | skipped | `data/raw/moel_forms/policy_data/files/1298286186517/(0)1012월_산재통계(최종).hwpx` | 서식성 키워드 미포함 |
| 117 | copied | `data/raw/moel_forms/policy_data/files/1298358950349/(13)해빙기 건설현장 안전보건 가이드라인(11년).hwp` | MOEL__가이드__13_해빙기_건설현장_안전보건_가이드라인_11년__N_A.hwp |
| 118 | copied | `data/raw/moel_forms/policy_data/files/1298358950349/(13)해빙기 건설현장 안전보건 가이드라인(11년).hwpx` | MOEL__가이드__13_해빙기_건설현장_안전보건_가이드라인_11년__N_A.hwpx |
| 119 | skipped | `data/raw/moel_forms/policy_data/files/1298364989651/재해예방전문지도기관_평가결과_홈페이지게시용(2010년).hwp` | 서식성 키워드 미포함 |
| 120 | skipped | `data/raw/moel_forms/policy_data/files/1298364989651/재해예방전문지도기관_평가결과_홈페이지게시용(2010년).hwpx` | 서식성 키워드 미포함 |
| 121 | skipped | `data/raw/moel_forms/policy_data/files/1304317188239/(1)즉시 과태료부과 세부내용1.hwp` | 서식성 키워드 미포함 |
| 122 | skipped | `data/raw/moel_forms/policy_data/files/1304317188239/(1)즉시 과태료부과 세부내용1.hwpx` | 서식성 키워드 미포함 |
| 123 | copied | `data/raw/moel_forms/policy_data/files/1305786985178/장마철_건설현장_안전보건_가이드라인.hwp` | MOEL__가이드__장마철_건설현장_안전보건_가이드라인__N_A.hwp |
| 124 | copied | `data/raw/moel_forms/policy_data/files/1305786985178/장마철_건설현장_안전보건_가이드라인.hwpx` | MOEL__가이드__장마철_건설현장_안전보건_가이드라인__N_A.hwpx |
| 125 | skipped | `data/raw/moel_forms/policy_data/files/1309857279165/(0)산업안전보건규칙개정전문(최종).hwp` | 서식성 키워드 미포함 |
| 126 | skipped | `data/raw/moel_forms/policy_data/files/1309857279165/(0)산업안전보건규칙개정전문(최종).hwpx` | 서식성 키워드 미포함 |
| 127 | skipped | `data/raw/moel_forms/policy_data/files/1309857279165/(0)산업안전보건규칙주요개정내용해설(홈페이지등재).hwp` | 서식성 키워드 미포함 |
| 128 | skipped | `data/raw/moel_forms/policy_data/files/1309857279165/(0)산업안전보건규칙주요개정내용해설(홈페이지등재).hwpx` | 서식성 키워드 미포함 |
| 129 | skipped | `data/raw/moel_forms/policy_data/files/1313989933841/1106월_산재통계.hwp` | 서식성 키워드 미포함 |
| 130 | skipped | `data/raw/moel_forms/policy_data/files/1313989933841/1106월_산재통계.hwpx` | 서식성 키워드 미포함 |
| 131 | skipped | `data/raw/moel_forms/policy_data/files/1325738414849/(5)안전보건진단기관현황(전국).hwp` | 서식성 키워드 미포함 |
| 132 | skipped | `data/raw/moel_forms/policy_data/files/1325738414849/(5)안전보건진단기관현황(전국).hwpx` | 서식성 키워드 미포함 |
| 133 | copied | `data/raw/moel_forms/policy_data/files/1327993088630/고시전문_방지계획서.hwp` | MOEL__계획서__고시전문_방지계획서__N_A.hwp |
| 134 | copied | `data/raw/moel_forms/policy_data/files/1327993088630/고시전문_방지계획서.hwpx` | MOEL__계획서__고시전문_방지계획서__N_A.hwpx |
| 135 | copied | `data/raw/moel_forms/policy_data/files/1327993088630/유해위험방지계획서 제도 설명.hwp` | MOEL__계획서__유해위험방지계획서_제도_설명__N_A.hwp |
| 136 | copied | `data/raw/moel_forms/policy_data/files/1327993088630/유해위험방지계획서 제도 설명.hwpx` | MOEL__계획서__유해위험방지계획서_제도_설명__N_A.hwpx |
| 137 | copied | `data/raw/moel_forms/policy_data/files/1329300460863/해빙기_건설현장_안전보건_가이드라인.hwp` | MOEL__가이드__해빙기_건설현장_안전보건_가이드라인__N_A.hwp |
| 138 | copied | `data/raw/moel_forms/policy_data/files/1329300460863/해빙기_건설현장_안전보건_가이드라인.hwpx` | MOEL__가이드__해빙기_건설현장_안전보건_가이드라인__N_A.hwpx |
| 139 | skipped | `data/raw/moel_forms/policy_data/files/1329702958686/(0)1112월_산재통계.hwp` | 서식성 키워드 미포함 |
| 140 | skipped | `data/raw/moel_forms/policy_data/files/1329702958686/(0)1112월_산재통계.hwpx` | 서식성 키워드 미포함 |
| 141 | skipped | `data/raw/moel_forms/policy_data/files/1337817061760/(2)건설업 기초안전보건교육 관련 FAQ.hwp` | 서식성 키워드 미포함 |
| 142 | skipped | `data/raw/moel_forms/policy_data/files/1337817061760/(2)건설업 기초안전보건교육 관련 FAQ.hwpx` | 서식성 키워드 미포함 |
| 143 | copied | `data/raw/moel_forms/policy_data/files/1337909045554/(7)120516_장마철_건설현장_안전보건_가이드라인(2012년).hwp` | MOEL__가이드__7_120516_장마철_건설현장_안전보건_가이드라인_2012년__N_A.hwp |
| 144 | copied | `data/raw/moel_forms/policy_data/files/1337909045554/(7)120516_장마철_건설현장_안전보건_가이드라인(2012년).hwpx` | MOEL__가이드__7_120516_장마철_건설현장_안전보건_가이드라인_2012년__N_A.hwpx |
| 145 | skipped | `data/raw/moel_forms/policy_data/files/1340342851038/(9)안전보건진단기관현황(전국).hwp` | 서식성 키워드 미포함 |
| 146 | skipped | `data/raw/moel_forms/policy_data/files/1340342851038/(9)안전보건진단기관현황(전국).hwpx` | 서식성 키워드 미포함 |
| 147 | copied | `data/raw/moel_forms/policy_data/files/1352453506951/121109 동절기 안전보건 가이드라인.hwp` | MOEL__가이드__동절기_안전보건_가이드라인__20121109.hwp |
| 148 | copied | `data/raw/moel_forms/policy_data/files/1352453506951/121109 동절기 안전보건 가이드라인.hwpx` | MOEL__가이드__동절기_안전보건_가이드라인__20121109.hwpx |
| 149 | skipped | `data/raw/moel_forms/policy_data/files/1359452172340/13년도 건설현장 자율안전컨설팅 추진계획(홈페이지 게시).hwp` | 서식성 키워드 미포함 |
| 150 | skipped | `data/raw/moel_forms/policy_data/files/1359452172340/13년도 건설현장 자율안전컨설팅 추진계획(홈페이지 게시).hwpx` | 서식성 키워드 미포함 |
| 151 | skipped | `data/raw/moel_forms/policy_data/files/1359594423530/(2)재해예방전문 지도기관 업무수행능력 평가결과 및 전체명단.hwp` | 서식성 키워드 미포함 |
| 152 | skipped | `data/raw/moel_forms/policy_data/files/1359594423530/(2)재해예방전문 지도기관 업무수행능력 평가결과 및 전체명단.hwpx` | 서식성 키워드 미포함 |
| 153 | copied | `data/raw/moel_forms/policy_data/files/1360822329859/[붙임] 해빙기 건설현장 안전보건 가이드라인.hwp` | MOEL__가이드__붙임_해빙기_건설현장_안전보건_가이드라인__N_A.hwp |
| 154 | copied | `data/raw/moel_forms/policy_data/files/1360822329859/[붙임] 해빙기 건설현장 안전보건 가이드라인.hwpx` | MOEL__가이드__붙임_해빙기_건설현장_안전보건_가이드라인__N_A.hwpx |
| 155 | skipped | `data/raw/moel_forms/policy_data/files/1363340431206/(0)(2013.03.15.)건설업기초교육기관 현황.hwp` | 서식성 키워드 미포함 |
| 156 | skipped | `data/raw/moel_forms/policy_data/files/1363340431206/(0)(2013.03.15.)건설업기초교육기관 현황.hwpx` | 서식성 키워드 미포함 |
| 157 | copied | `data/raw/moel_forms/policy_data/files/1370587541154/장마철 건설현장 안전보건 가이드라인(최종).hwp` | MOEL__가이드__장마철_건설현장_안전보건_가이드라인_최종__N_A.hwp |
| 158 | copied | `data/raw/moel_forms/policy_data/files/1370587541154/장마철 건설현장 안전보건 가이드라인(최종).hwpx` | MOEL__가이드__장마철_건설현장_안전보건_가이드라인_최종__N_A.hwpx |
| 159 | skipped | `data/raw/moel_forms/policy_data/files/1371544651072/130902_안전보건진단기관 현황(홈페이지).hwp` | 서식성 키워드 미포함 |
| 160 | skipped | `data/raw/moel_forms/policy_data/files/1371544651072/130902_안전보건진단기관 현황(홈페이지).hwpx` | 서식성 키워드 미포함 |
| 161 | copied | `data/raw/moel_forms/policy_data/files/1372384586591/교육서비스위험성평가 표준모델(실험실).hwp` | MOEL__표준모델__교육서비스위험성평가_표준모델_실험실__N_A.hwp |
| 162 | copied | `data/raw/moel_forms/policy_data/files/1372384586591/교육서비스위험성평가 표준모델(실험실).hwpx` | MOEL__표준모델__교육서비스위험성평가_표준모델_실험실__N_A.hwpx |
| 163 | skipped | `data/raw/moel_forms/policy_data/files/1377681409212/직무교육_위탁기관_현황(0828).hwp` | 서식성 키워드 미포함 |
| 164 | skipped | `data/raw/moel_forms/policy_data/files/1377681409212/직무교육_위탁기관_현황(0828).hwpx` | 서식성 키워드 미포함 |
| 165 | skipped | `data/raw/moel_forms/policy_data/files/1377748928455/산업재해예방_필수_안전수칙(외부기관용).hwp` | 서식성 키워드 미포함 |
| 166 | skipped | `data/raw/moel_forms/policy_data/files/1377748928455/산업재해예방_필수_안전수칙(외부기관용).hwpx` | 서식성 키워드 미포함 |
| 167 | copied | `data/raw/moel_forms/policy_data/files/1378181181811/교육서비스위험성평가 표준모델(단체급식).hwp` | MOEL__표준모델__교육서비스위험성평가_표준모델_단체급식__N_A.hwp |
| 168 | copied | `data/raw/moel_forms/policy_data/files/1378181181811/교육서비스위험성평가 표준모델(단체급식).hwpx` | MOEL__표준모델__교육서비스위험성평가_표준모델_단체급식__N_A.hwpx |
| 169 | skipped | `data/raw/moel_forms/policy_data/files/1378347117872/0528지방자치단체 공무원 안전보건교육교재(고용부수정).hwp` | 서식성 키워드 미포함 |
| 170 | skipped | `data/raw/moel_forms/policy_data/files/1378347117872/0528지방자치단체 공무원 안전보건교육교재(고용부수정).hwpx` | 서식성 키워드 미포함 |
| 171 | skipped | `data/raw/moel_forms/policy_data/files/1383891157882/(2013년 11월)건설업기초교육기관 현황.hwp` | 서식성 키워드 미포함 |
| 172 | skipped | `data/raw/moel_forms/policy_data/files/1383891157882/(2013년 11월)건설업기초교육기관 현황.hwpx` | 서식성 키워드 미포함 |
| 173 | skipped | `data/raw/moel_forms/policy_data/files/1390820211562/14년_건설업 자율안전보건컨설팅 추진계획.hwp` | 서식성 키워드 미포함 |
| 174 | skipped | `data/raw/moel_forms/policy_data/files/1390820211562/14년_건설업 자율안전보건컨설팅 추진계획.hwpx` | 서식성 키워드 미포함 |
| 175 | skipped | `data/raw/moel_forms/policy_data/files/1396314630946/1312월_산재통계_인터넷.hwp` | 서식성 키워드 미포함 |
| 176 | skipped | `data/raw/moel_forms/policy_data/files/1396314630946/1312월_산재통계_인터넷.hwpx` | 서식성 키워드 미포함 |
| 177 | skipped | `data/raw/moel_forms/policy_data/files/1401238940638/(5)안전보건진단기관_현황(140523_현재).hwp` | 서식성 키워드 미포함 |
| 178 | skipped | `data/raw/moel_forms/policy_data/files/1401238940638/(5)안전보건진단기관_현황(140523_현재).hwpx` | 서식성 키워드 미포함 |
| 179 | copied | `data/raw/moel_forms/policy_data/files/1413866229120/산안법_시행규칙_별지_제1호의2(1_2)_서식_안전관리자ㆍ보건관리자ㆍ산업보건의__3ccc7b13.hwp` | MOEL__별지__산안법_시행규칙_별지_제1호의2_1_2_서식_안전관리자__N_A.hwp |
| 180 | copied | `data/raw/moel_forms/policy_data/files/1413866229120/산안법_시행규칙_별지_제1호의2(1_2)_서식_안전관리자ㆍ보건관리자ㆍ산업보건의__3ccc7b13.hwpx` | MOEL__별지__산안법_시행규칙_별지_제1호의2_1_2_서식_안전관리자__N_A.hwpx |
| 181 | skipped | `data/raw/moel_forms/policy_data/files/1419847960548/산재보험기금 자산운용지침.hwp` | 서식성 키워드 미포함 |
| 182 | skipped | `data/raw/moel_forms/policy_data/files/1419847960548/산재보험기금 자산운용지침.hwpx` | 서식성 키워드 미포함 |
| 183 | skipped | `data/raw/moel_forms/policy_data/files/1457496484144/1512월_산재통계(사고사망_예규기준).hwp` | 서식성 키워드 미포함 |
| 184 | skipped | `data/raw/moel_forms/policy_data/files/1457496484144/1512월_산재통계(사고사망_예규기준).hwpx` | 서식성 키워드 미포함 |
| 185 | copied | `data/raw/moel_forms/policy_data/files/1475831008865/위험성평가 및 우수 사업장 인정 개요.hwp` | MOEL__표준모델__위험성평가_및_우수_사업장_인정_개요__N_A.hwp |
| 186 | copied | `data/raw/moel_forms/policy_data/files/1475831008865/위험성평가 및 우수 사업장 인정 개요.hwpx` | MOEL__표준모델__위험성평가_및_우수_사업장_인정_개요__N_A.hwpx |
| 187 | skipped | `data/raw/moel_forms/policy_data/files/1482997761128/(0)참고_교육자료이용방법.hwp` | 서식성 키워드 미포함 |
| 188 | skipped | `data/raw/moel_forms/policy_data/files/1482997761128/(0)참고_교육자료이용방법.hwpx` | 서식성 키워드 미포함 |
| 189 | skipped | `data/raw/moel_forms/policy_data/files/1482997761128/(1)참고_강사기준등_질의답변.hwp` | 서식성 키워드 미포함 |
| 190 | skipped | `data/raw/moel_forms/policy_data/files/1482997761128/(1)참고_강사기준등_질의답변.hwpx` | 서식성 키워드 미포함 |
| 191 | skipped | `data/raw/moel_forms/policy_data/files/1482997761128/(보도자료)★8.1_50인미만_도매_숙박_음식업_안전보건교육_실시_의무화.hwp` | 서식성 키워드 미포함 |
| 192 | skipped | `data/raw/moel_forms/policy_data/files/1482997761128/(보도자료)★8.1_50인미만_도매_숙박_음식업_안전보건교육_실시_의무화.hwpx` | 서식성 키워드 미포함 |
| 193 | skipped | `data/raw/moel_forms/policy_data/files/1483332742887/(0)[별표 8의2] 교육대상별 교육내용.hwp` | 서식성 키워드 미포함 |
| 194 | skipped | `data/raw/moel_forms/policy_data/files/1483332742887/(0)[별표 8의2] 교육대상별 교육내용.hwpx` | 서식성 키워드 미포함 |
| 195 | skipped | `data/raw/moel_forms/policy_data/files/1483332742887/[별표 8] 산업안전ㆍ보건 관련 교육과정별 교육시간.hwp` | 서식성 키워드 미포함 |
| 196 | skipped | `data/raw/moel_forms/policy_data/files/1483332742887/[별표 8] 산업안전ㆍ보건 관련 교육과정별 교육시간.hwpx` | 서식성 키워드 미포함 |
| 197 | skipped | `data/raw/moel_forms/policy_data/files/1489104927663/1612월_산재통계_인터넷.hwp` | 서식성 키워드 미포함 |
| 198 | skipped | `data/raw/moel_forms/policy_data/files/1489104927663/1612월_산재통계_인터넷.hwpx` | 서식성 키워드 미포함 |
| 199 | skipped | `data/raw/moel_forms/policy_data/files/1508387392120/(0)산업재해조사표_모범사례(1차).hwp` | 서식성 키워드 미포함 |
| 200 | skipped | `data/raw/moel_forms/policy_data/files/1508387392120/(0)산업재해조사표_모범사례(1차).hwpx` | 서식성 키워드 미포함 |
| 201 | skipped | `data/raw/moel_forms/policy_data/files/1508387392120/(0)산업재해조사표_모범사례(2차).hwp` | 서식성 키워드 미포함 |
| 202 | skipped | `data/raw/moel_forms/policy_data/files/1508387392120/(0)산업재해조사표_모범사례(2차).hwpx` | 서식성 키워드 미포함 |
| 203 | skipped | `data/raw/moel_forms/policy_data/files/1508387392120/(0)산업재해조사표_모범사례(3차).hwp` | 서식성 키워드 미포함 |
| 204 | skipped | `data/raw/moel_forms/policy_data/files/1508387392120/(0)산업재해조사표_모범사례(3차).hwpx` | 서식성 키워드 미포함 |
| 205 | skipped | `data/raw/moel_forms/policy_data/files/20180300599/원하청 산업재해 통합관리제도.hwp` | 서식성 키워드 미포함 |
| 206 | skipped | `data/raw/moel_forms/policy_data/files/20180300599/원하청 산업재해 통합관리제도.hwpx` | 서식성 키워드 미포함 |
| 207 | skipped | `data/raw/moel_forms/policy_data/files/20180400725/1712월_산재통계_인터넷.hwp` | 서식성 키워드 미포함 |
| 208 | skipped | `data/raw/moel_forms/policy_data/files/20180400725/1712월_산재통계_인터넷.hwpx` | 서식성 키워드 미포함 |
| 209 | skipped | `data/raw/moel_forms/policy_data/files/20180500716/1803월_산재통계_인터넷.hwp` | 서식성 키워드 미포함 |
| 210 | skipped | `data/raw/moel_forms/policy_data/files/20180500716/1803월_산재통계_인터넷.hwpx` | 서식성 키워드 미포함 |
| 211 | skipped | `data/raw/moel_forms/policy_data/files/20180800735/1806월_산재통계_인터넷.hwp` | 서식성 키워드 미포함 |
| 212 | skipped | `data/raw/moel_forms/policy_data/files/20180800735/1806월_산재통계_인터넷.hwpx` | 서식성 키워드 미포함 |
| 213 | skipped | `data/raw/moel_forms/policy_data/files/20190500060/1812월_산재통계_인터넷.hwp` | 서식성 키워드 미포함 |
| 214 | skipped | `data/raw/moel_forms/policy_data/files/20190500060/1812월_산재통계_인터넷.hwpx` | 서식성 키워드 미포함 |
| 215 | skipped | `data/raw/moel_forms/policy_data/files/20200300434/2019년 민간재해예방기관 평가결과(최종).hwp` | 서식성 키워드 미포함 |
| 216 | skipped | `data/raw/moel_forms/policy_data/files/20200300434/2019년 민간재해예방기관 평가결과(최종).hwpx` | 서식성 키워드 미포함 |
| 217 | skipped | `data/raw/moel_forms/policy_data/files/20200400135/★200331 도급시 산업재해예방 운영지침.hwp` | 서식성 키워드 미포함 |
| 218 | skipped | `data/raw/moel_forms/policy_data/files/20200400135/★200331 도급시 산업재해예방 운영지침.hwpx` | 서식성 키워드 미포함 |
| 219 | skipped | `data/raw/moel_forms/policy_data/files/20210100654/기술지도기관 평가결과.hwp` | 서식성 키워드 미포함 |
| 220 | skipped | `data/raw/moel_forms/policy_data/files/20210100654/기술지도기관 평가결과.hwpx` | 서식성 키워드 미포함 |
| 221 | skipped | `data/raw/moel_forms/policy_data/files/20210200761/[붙임] 2020년 민간재해예방기관 평가 결과_최종.hwp` | 서식성 키워드 미포함 |
| 222 | skipped | `data/raw/moel_forms/policy_data/files/20210200761/[붙임] 2020년 민간재해예방기관 평가 결과_최종.hwpx` | 서식성 키워드 미포함 |
| 223 | skipped | `data/raw/moel_forms/policy_data/files/20210901248/안전보건관리체계 자율진단표.hwp` | 서식성 키워드 미포함 |
| 224 | skipped | `data/raw/moel_forms/policy_data/files/20210901248/안전보건관리체계 자율진단표.hwpx` | 서식성 키워드 미포함 |
| 225 | copied | `data/raw/moel_forms/policy_data/files/20211000975/안전보건관리체계 자율점검표(산재예방지원과)_211130.hwp` | MOEL__자율점검표__안전보건관리체계_자율점검표_산재예방지원과_211130__N_A.hwp |
| 226 | copied | `data/raw/moel_forms/policy_data/files/20211000975/안전보건관리체계 자율점검표(산재예방지원과)_211130.hwpx` | MOEL__자율점검표__안전보건관리체계_자율점검표_산재예방지원과_211130__N_A.hwpx |
| 227 | skipped | `data/raw/moel_forms/policy_data/files/20211101668/(최종)자율(점검)표_안전보건관리체계_창고 및 운수업.hwp` | 서식성 키워드 미포함 |
| 228 | skipped | `data/raw/moel_forms/policy_data/files/20211101668/(최종)자율(점검)표_안전보건관리체계_창고 및 운수업.hwpx` | 서식성 키워드 미포함 |
| 229 | skipped | `data/raw/moel_forms/policy_data/files/20211101668/(최종)자율(점검)표_안전보건관리체계_폐기물처리업.hwp` | 서식성 키워드 미포함 |
| 230 | skipped | `data/raw/moel_forms/policy_data/files/20211101668/(최종)자율(점검)표_안전보건관리체계_폐기물처리업.hwpx` | 서식성 키워드 미포함 |
| 231 | copied | `data/raw/moel_forms/policy_data/files/20211201729/12.21_건설업_중대산업재해_예방을_위한_자율점검표(첨부_건설산재예방정책과).hwp` | MOEL__자율점검표__1221_건설업_중대산업재해_예방을_위한_자율점검표_첨부_건설산재예방정책과__N_A.hwp |
| 232 | copied | `data/raw/moel_forms/policy_data/files/20211201729/12.21_건설업_중대산업재해_예방을_위한_자율점검표(첨부_건설산재예방정책과).hwpx` | MOEL__자율점검표__1221_건설업_중대산업재해_예방을_위한_자율점검표_첨부_건설산재예방정책과__N_A.hwpx |
| 233 | skipped | `data/raw/moel_forms/policy_data/files/20211201729/붙임1 21. 12월 건설현장 주요 사망사고 사례.hwp` | 서식성 키워드 미포함 |
| 234 | skipped | `data/raw/moel_forms/policy_data/files/20211201729/붙임1 21. 12월 건설현장 주요 사망사고 사례.hwpx` | 서식성 키워드 미포함 |
| 235 | copied | `data/raw/moel_forms/policy_data/files/20220100395/화학업종 중소기업을 위한 안전보건관리 자율점검표.hwp` | MOEL__자율점검표__화학업종_중소기업을_위한_안전보건관리_자율점검표__N_A.hwp |
| 236 | copied | `data/raw/moel_forms/policy_data/files/20220100395/화학업종 중소기업을 위한 안전보건관리 자율점검표.hwpx` | MOEL__자율점검표__화학업종_중소기업을_위한_안전보건관리_자율점검표__N_A.hwpx |
| 237 | skipped | `data/raw/moel_forms/policy_data/files/20220100720/220118_안전보건관리체계 자율진단표_임업.hwp` | 서식성 키워드 미포함 |
| 238 | skipped | `data/raw/moel_forms/policy_data/files/20220100720/220118_안전보건관리체계 자율진단표_임업.hwpx` | 서식성 키워드 미포함 |
| 239 | copied | `data/raw/moel_forms/policy_data/files/20220100720/220118_중소기업을 위한 안전보건관리 자율점검표_임업.hwp` | MOEL__자율점검표__중소기업을_위한_안전보건관리_자율점검표_임업__20220118.hwp |
| 240 | copied | `data/raw/moel_forms/policy_data/files/20220100720/220118_중소기업을 위한 안전보건관리 자율점검표_임업.hwpx` | MOEL__자율점검표__중소기업을_위한_안전보건관리_자율점검표_임업__20220118.hwpx |
| 241 | copied | `data/raw/moel_forms/policy_data/files/20220200959/중소기업을 위한 안전보건관리 자율점검표_사업시설관리업(최종).hwp` | MOEL__자율점검표__중소기업을_위한_안전보건관리_자율점검표_사업시설관리업_최종__N_A.hwp |
| 242 | copied | `data/raw/moel_forms/policy_data/files/20220200959/중소기업을 위한 안전보건관리 자율점검표_사업시설관리업(최종).hwpx` | MOEL__자율점검표__중소기업을_위한_안전보건관리_자율점검표_사업시설관리업_최종__N_A.hwpx |
| 243 | copied | `data/raw/moel_forms/policy_data/files/20220200966/2022년 안전보건교육안내서.hwp` | MOEL__가이드__2022년_안전보건교육안내서__N_A.hwp |
| 244 | copied | `data/raw/moel_forms/policy_data/files/20220200966/2022년 안전보건교육안내서.hwpx` | MOEL__가이드__2022년_안전보건교육안내서__N_A.hwpx |
| 245 | copied | `data/raw/moel_forms/policy_data/files/20220300558/220310 채석업종을 위한 안전보건관리체계 자율점검표.hwp` | MOEL__자율점검표__채석업종을_위한_안전보건관리체계_자율점검표__20220310.hwp |
| 246 | copied | `data/raw/moel_forms/policy_data/files/20220300558/220310 채석업종을 위한 안전보건관리체계 자율점검표.hwpx` | MOEL__자율점검표__채석업종을_위한_안전보건관리체계_자율점검표__20220310.hwpx |
| 247 | copied | `data/raw/moel_forms/policy_data/files/20220300830/활용 서식 모음_'중대재해처벌법 따라하기' 안내서.hwp` | MOEL__가이드__활용_서식_모음_중대재해처벌법_따라하기_안내서__N_A.hwp |
| 248 | copied | `data/raw/moel_forms/policy_data/files/20220300830/활용 서식 모음_'중대재해처벌법 따라하기' 안내서.hwpx` | MOEL__가이드__활용_서식_모음_중대재해처벌법_따라하기_안내서__N_A.hwpx |
| 249 | skipped | `data/raw/moel_forms/policy_data/files/20220300930/미디어 현장배송 사용법.hwp` | 서식성 키워드 미포함 |
| 250 | skipped | `data/raw/moel_forms/policy_data/files/20220300930/미디어 현장배송 사용법.hwpx` | 서식성 키워드 미포함 |
| 251 | skipped | `data/raw/moel_forms/policy_data/files/20220400203/안전보건관리체계 구축 컨설팅 매뉴얼(최종본).hwp` | 서식성 키워드 미포함 |
| 252 | skipped | `data/raw/moel_forms/policy_data/files/20220400203/안전보건관리체계 구축 컨설팅 매뉴얼(최종본).hwpx` | 서식성 키워드 미포함 |
| 253 | copied | `data/raw/moel_forms/policy_data/files/20220401598/물질안전보건자료(MSDS) 이행실태 자율점검표.hwp` | MOEL__자율점검표__물질안전보건자료_MSDS_이행실태_자율점검표__N_A.hwp |
| 254 | copied | `data/raw/moel_forms/policy_data/files/20220401598/물질안전보건자료(MSDS) 이행실태 자율점검표.hwpx` | MOEL__자율점검표__물질안전보건자료_MSDS_이행실태_자율점검표__N_A.hwpx |
| 255 | skipped | `data/raw/moel_forms/policy_data/files/20220501265/[인쇄본] 안전보건관리비_해설집 - 수정.hwp` | 서식성 키워드 미포함 |
| 256 | skipped | `data/raw/moel_forms/policy_data/files/20220501265/[인쇄본] 안전보건관리비_해설집 - 수정.hwpx` | 서식성 키워드 미포함 |
| 257 | copied | `data/raw/moel_forms/policy_data/files/20220600492/[인쇄본] 중소 건설현장을 위한 사망사고 기인물 자율점검표 - 편집.hwp` | MOEL__자율점검표__인쇄본_중소_건설현장을_위한_사망사고_기인물_자율점검표_-__N_A.hwp |
| 258 | copied | `data/raw/moel_forms/policy_data/files/20220600492/[인쇄본] 중소 건설현장을 위한 사망사고 기인물 자율점검표 - 편집.hwpx` | MOEL__자율점검표__인쇄본_중소_건설현장을_위한_사망사고_기인물_자율점검표_-__N_A.hwpx |
| 259 | copied | `data/raw/moel_forms/policy_data/files/20220601094/안전보건 의무 이행점검 및 평가개선 점검표.hwp` | MOEL__자율점검표__안전보건_의무_이행점검_및_평가개선_점검표__N_A.hwp |
| 260 | copied | `data/raw/moel_forms/policy_data/files/20220601094/안전보건 의무 이행점검 및 평가개선 점검표.hwpx` | MOEL__자율점검표__안전보건_의무_이행점검_및_평가개선_점검표__N_A.hwpx |
| 261 | skipped | `data/raw/moel_forms/policy_data/files/20220800481/220907 건설재해예방 지도계약 안내_발주자 대상.hwp` | 서식성 키워드 미포함 |
| 262 | skipped | `data/raw/moel_forms/policy_data/files/20220800481/220907 건설재해예방 지도계약 안내_발주자 대상.hwpx` | 서식성 키워드 미포함 |
| 263 | copied | `data/raw/moel_forms/policy_data/files/20221100163/식품가공용 기계 자율안전점검표.hwp` | MOEL__자율점검표__식품가공용_기계_자율안전점검표__N_A.hwp |
| 264 | copied | `data/raw/moel_forms/policy_data/files/20221100163/식품가공용 기계 자율안전점검표.hwpx` | MOEL__자율점검표__식품가공용_기계_자율안전점검표__N_A.hwpx |
| 265 | skipped | `data/raw/moel_forms/policy_data/files/20230200712/2022년 민간재해예방기관 평가 결과(수정).hwp` | 서식성 키워드 미포함 |
| 266 | skipped | `data/raw/moel_forms/policy_data/files/20230200712/2022년 민간재해예방기관 평가 결과(수정).hwpx` | 서식성 키워드 미포함 |
| 267 | skipped | `data/raw/moel_forms/policy_data/files/20230201264/[붙임1]2023년 안전보건관리체계구축 컨설팅 자율 신청 안내_공고문.hwp` | 서식성 키워드 미포함 |
| 268 | skipped | `data/raw/moel_forms/policy_data/files/20230201264/[붙임1]2023년 안전보건관리체계구축 컨설팅 자율 신청 안내_공고문.hwpx` | 서식성 키워드 미포함 |
| 269 | skipped | `data/raw/moel_forms/policy_data/files/20230201451/[붙임]2022년_건설재해예방전문지도기관_평가_결과.hwp` | 서식성 키워드 미포함 |
| 270 | skipped | `data/raw/moel_forms/policy_data/files/20230201451/[붙임]2022년_건설재해예방전문지도기관_평가_결과.hwpx` | 서식성 키워드 미포함 |
| 271 | skipped | `data/raw/moel_forms/policy_data/files/20230201608/[붙임1]대중소기업 상생협력사업 공고문.hwp` | 서식성 키워드 미포함 |
| 272 | skipped | `data/raw/moel_forms/policy_data/files/20230201608/[붙임1]대중소기업 상생협력사업 공고문.hwpx` | 서식성 키워드 미포함 |
| 273 | skipped | `data/raw/moel_forms/policy_data/files/20230301869/붙임_2023년 대중소기업 상생협력사업 2차 공고문.hwp` | 서식성 키워드 미포함 |
| 274 | skipped | `data/raw/moel_forms/policy_data/files/20230301869/붙임_2023년 대중소기업 상생협력사업 2차 공고문.hwpx` | 서식성 키워드 미포함 |
| 275 | copied | `data/raw/moel_forms/policy_data/files/20230401190/2. 위험요인별 점검표.hwp` | MOEL__자율점검표__2_위험요인별_점검표__N_A.hwp |
| 276 | copied | `data/raw/moel_forms/policy_data/files/20230401190/2. 위험요인별 점검표.hwpx` | MOEL__자율점검표__2_위험요인별_점검표__N_A.hwpx |
| 277 | copied | `data/raw/moel_forms/policy_data/files/20230600668/★ 건설현장 사망사고 핵심 위험요인 자율점검표.hwp` | MOEL__자율점검표__건설현장_사망사고_핵심_위험요인_자율점검표__N_A.hwp |
| 278 | copied | `data/raw/moel_forms/policy_data/files/20230600668/★ 건설현장 사망사고 핵심 위험요인 자율점검표.hwpx` | MOEL__자율점검표__건설현장_사망사고_핵심_위험요인_자율점검표__N_A.hwpx |
| 279 | copied | `data/raw/moel_forms/policy_data/files/20230900922/230918 소규모 사업장을 위한 위험성평가 안내서(최종).hwp` | MOEL__안내서__소규모_사업장을_위한_위험성평가_안내서_최종__20230918.hwp |
| 280 | copied | `data/raw/moel_forms/policy_data/files/20230900922/230918 소규모 사업장을 위한 위험성평가 안내서(최종).hwpx` | MOEL__안내서__소규모_사업장을_위한_위험성평가_안내서_최종__20230918.hwpx |
| 281 | skipped | `data/raw/moel_forms/policy_data/files/20230901623/230926_MSDS_대체자료_연계개선_제도변경_안내(게시용).hwp` | 서식성 키워드 미포함 |
| 282 | skipped | `data/raw/moel_forms/policy_data/files/20230901623/230926_MSDS_대체자료_연계개선_제도변경_안내(게시용).hwpx` | 서식성 키워드 미포함 |
| 283 | skipped | `data/raw/moel_forms/policy_data/files/20231200149/[붙임2] 2024년 대중소기업 상생협력사업 공고문.hwp` | 서식성 키워드 미포함 |
| 284 | skipped | `data/raw/moel_forms/policy_data/files/20231200149/[붙임2] 2024년 대중소기업 상생협력사업 공고문.hwpx` | 서식성 키워드 미포함 |
| 285 | skipped | `data/raw/moel_forms/policy_data/files/20240301162/산업안전 대진단 자가진단표(오프라인)_송부용_최종.hwp` | 서식성 키워드 미포함 |
| 286 | skipped | `data/raw/moel_forms/policy_data/files/20240301162/산업안전 대진단 자가진단표(오프라인)_송부용_최종.hwpx` | 서식성 키워드 미포함 |
| 287 | skipped | `data/raw/moel_forms/policy_data/files/20240400771/'24년도 위험성평가 우수사례 발표대회 공고문.hwp` | 서식성 키워드 미포함 |
| 288 | skipped | `data/raw/moel_forms/policy_data/files/20240400771/'24년도 위험성평가 우수사례 발표대회 공고문.hwpx` | 서식성 키워드 미포함 |
| 289 | copied | `data/raw/moel_forms/policy_data/files/20240400787/[붙임2]_[별지 제31호서식] 유해ㆍ위험작업 도급승인 신청서(산업안전보건법 시행규칙).hwp` | MOEL__별지__붙임2_별지_제31호서식_유해_위험작업_도급승인_신청서_산업안전보건법__N_A.hwp |
| 290 | copied | `data/raw/moel_forms/policy_data/files/20240400787/[붙임2]_[별지 제31호서식] 유해ㆍ위험작업 도급승인 신청서(산업안전보건법 시행규칙).hwpx` | MOEL__별지__붙임2_별지_제31호서식_유해_위험작업_도급승인_신청서_산업안전보건법__N_A.hwpx |
| 291 | copied | `data/raw/moel_forms/policy_data/files/20240400787/[붙임3]_[별지 제33호서식] 유해ㆍ위험작업 도급승인 변경신청서(산업안전보건법_0d91499c.hwp` | MOEL__별지__붙임3_별지_제33호서식_유해_위험작업_도급승인_변경신청서_산업안전보건법__N_A.hwp |
| 292 | copied | `data/raw/moel_forms/policy_data/files/20240400787/[붙임3]_[별지 제33호서식] 유해ㆍ위험작업 도급승인 변경신청서(산업안전보건법_0d91499c.hwpx` | MOEL__별지__붙임3_별지_제33호서식_유해_위험작업_도급승인_변경신청서_산업안전보건법__N_A.hwpx |
| 293 | copied | `data/raw/moel_forms/policy_data/files/20240401662/작업 전 안전점검회의(TBM)의 안전보건 정기교육 시간 인정에 관한 지침.hwp` | MOEL__TBM__작업_전_안전점검회의_TBM_의_안전보건_정기교육_시간__N_A.hwp |
| 294 | copied | `data/raw/moel_forms/policy_data/files/20240401662/작업 전 안전점검회의(TBM)의 안전보건 정기교육 시간 인정에 관한 지침.hwpx` | MOEL__TBM__작업_전_안전점검회의_TBM_의_안전보건_정기교육_시간__N_A.hwpx |
| 295 | copied | `data/raw/moel_forms/policy_data/files/20260300895/발파·해체공법 중심 해체공사 안전작업 가이드(배포용).hwp` | MOEL__가이드__발파_해체공법_중심_해체공사_안전작업_가이드_배포용__N_A.hwp |
| 296 | copied | `data/raw/moel_forms/policy_data/files/20260300895/발파·해체공법 중심 해체공사 안전작업 가이드(배포용).hwpx` | MOEL__가이드__발파_해체공법_중심_해체공사_안전작업_가이드_배포용__N_A.hwpx |
| 297 | skipped | `data/raw/moel_forms/policy_data/files/5246/공단사업계획.hwp` | 서식성 키워드 미포함 |
| 298 | skipped | `data/raw/moel_forms/policy_data/files/5246/공단사업계획.hwpx` | 서식성 키워드 미포함 |
| 299 | skipped | `data/raw/moel_forms/policy_data/files/5247/워크숍계획.hwp` | 서식성 키워드 미포함 |
| 300 | skipped | `data/raw/moel_forms/policy_data/files/5247/워크숍계획.hwpx` | 서식성 키워드 미포함 |
| 301 | skipped | `data/raw/moel_forms/policy_data/files/5263/한국산업안전공단 직제개편 추진계획.hwp` | 서식성 키워드 미포함 |
| 302 | skipped | `data/raw/moel_forms/policy_data/files/5263/한국산업안전공단 직제개편 추진계획.hwpx` | 서식성 키워드 미포함 |
| 303 | skipped | `data/raw/moel_forms/policy_data/files/5319/재해예방전문지도기관현황.hwp` | 서식성 키워드 미포함 |
| 304 | skipped | `data/raw/moel_forms/policy_data/files/5560/실험(1).hwp` | 서식성 키워드 미포함 |
| 305 | skipped | `data/raw/moel_forms/policy_data/files/5786/조선업재해예방대책-한글97.hwp` | 서식성 키워드 미포함 |
| 306 | skipped | `data/raw/moel_forms/policy_data/files/5789/accident_statistics(2001).hwp` | 서식성 키워드 미포함 |
| 307 | skipped | `data/raw/moel_forms/policy_data/files/5914/밀폐공간작업으로인한건강장해예방조치(12-2).hwp` | 서식성 키워드 미포함 |
| 308 | skipped | `data/raw/moel_forms/policy_data/files/5972/신822.hwp` | 서식성 키워드 미포함 |
| 309 | skipped | `data/raw/moel_forms/policy_data/files/5972/신832.hwp` | 서식성 키워드 미포함 |
| 310 | skipped | `data/raw/moel_forms/policy_data/files/5973/신851.hwp` | 서식성 키워드 미포함 |
| 311 | skipped | `data/raw/moel_forms/policy_data/files/5973/신861.hwp` | 서식성 키워드 미포함 |
| 312 | skipped | `data/raw/moel_forms/policy_data/files/5974/신(1987).hwp` | 서식성 키워드 미포함 |
| 313 | skipped | `data/raw/moel_forms/policy_data/files/5974/신(1988).hwp` | 서식성 키워드 미포함 |
| 314 | skipped | `data/raw/moel_forms/policy_data/files/5975/신(1989).hwp` | 서식성 키워드 미포함 |
| 315 | skipped | `data/raw/moel_forms/policy_data/files/5975/신(1990).hwp` | 서식성 키워드 미포함 |
| 316 | skipped | `data/raw/moel_forms/policy_data/files/5976/신(1991).hwp` | 서식성 키워드 미포함 |
| 317 | skipped | `data/raw/moel_forms/policy_data/files/5976/신(1992).hwp` | 서식성 키워드 미포함 |
| 318 | skipped | `data/raw/moel_forms/policy_data/files/5977/신(1993).hwp` | 서식성 키워드 미포함 |
| 319 | skipped | `data/raw/moel_forms/policy_data/files/5977/신(1994).hwp` | 서식성 키워드 미포함 |
| 320 | skipped | `data/raw/moel_forms/policy_data/files/5978/신(1995).hwp` | 서식성 키워드 미포함 |
| 321 | skipped | `data/raw/moel_forms/policy_data/files/5978/신(1996).hwp` | 서식성 키워드 미포함 |
| 322 | skipped | `data/raw/moel_forms/policy_data/files/5979/신(1997).hwp` | 서식성 키워드 미포함 |
| 323 | skipped | `data/raw/moel_forms/policy_data/files/5979/신(1998).hwp` | 서식성 키워드 미포함 |
| 324 | skipped | `data/raw/moel_forms/policy_data/files/5980/신(1999).hwp` | 서식성 키워드 미포함 |
| 325 | skipped | `data/raw/moel_forms/policy_data/files/5980/신(2000).hwp` | 서식성 키워드 미포함 |
| 326 | skipped | `data/raw/moel_forms/policy_data/files/6009/산재기금 결산.hwp` | 서식성 키워드 미포함 |
| 327 | skipped | `data/raw/moel_forms/policy_data/files/6010/산재보험기금 적립금결산(02).hwp` | 서식성 키워드 미포함 |
| 328 | skipped | `data/raw/moel_forms/policy_data/files/6023/환경산업보건실습래포트.hwp` | 서식성 키워드 미포함 |
| 329 | skipped | `data/raw/moel_forms/policy_data/files/6024/(05-2)제5장(6)2.hwp` | 서식성 키워드 미포함 |
| 330 | skipped | `data/raw/moel_forms/policy_data/files/6025/(03-1)제3장(3-01)B41.hwp` | 서식성 키워드 미포함 |
| 331 | skipped | `data/raw/moel_forms/policy_data/files/6025/(03-2)제3장(3-자)B41.hwp` | 서식성 키워드 미포함 |
| 332 | skipped | `data/raw/moel_forms/policy_data/files/6025/(04)제4장1.hwp` | 서식성 키워드 미포함 |
| 333 | skipped | `data/raw/moel_forms/policy_data/files/6025/(05)제5장1.hwp` | 서식성 키워드 미포함 |
| 334 | skipped | `data/raw/moel_forms/policy_data/files/6025/(05-1)제5장(횡)1.hwp` | 서식성 키워드 미포함 |
| 335 | skipped | `data/raw/moel_forms/policy_data/files/6026/(01)제1장4.hwp` | 서식성 키워드 미포함 |
| 336 | skipped | `data/raw/moel_forms/policy_data/files/6026/(02)제2장3.hwp` | 서식성 키워드 미포함 |
| 337 | skipped | `data/raw/moel_forms/policy_data/files/6026/(02-1)제2장(2-02)B43.hwp` | 서식성 키워드 미포함 |
| 338 | skipped | `data/raw/moel_forms/policy_data/files/6026/(02-2)제2장(2-11)B43.hwp` | 서식성 키워드 미포함 |
| 339 | skipped | `data/raw/moel_forms/policy_data/files/6026/(03)제3장3.hwp` | 서식성 키워드 미포함 |
| 340 | skipped | `data/raw/moel_forms/policy_data/files/6067/밀폐공간작업지침.hwp` | 서식성 키워드 미포함 |
| 341 | skipped | `data/raw/moel_forms/policy_data/files/6089/미국의 산업안전보건 관련법의 변천과정[1].hwp` | 서식성 키워드 미포함 |
| 342 | skipped | `data/raw/moel_forms/policy_data/files/6089/미국의 산업안전보건 관련법의 변천과정[1].hwpx` | 서식성 키워드 미포함 |
| 343 | skipped | `data/raw/moel_forms/policy_data/files/6162/보험요율결정방식(0319).hwp` | 서식성 키워드 미포함 |
| 344 | skipped | `data/raw/moel_forms/policy_data/files/6162/보험요율결정방식(0319).hwpx` | 서식성 키워드 미포함 |
| 345 | skipped | `data/raw/moel_forms/policy_data/files/6190/미국산안법2.hwp` | 서식성 키워드 미포함 |
| 346 | skipped | `data/raw/moel_forms/policy_data/files/6190/미국산안법2.hwpx` | 서식성 키워드 미포함 |
| 347 | skipped | `data/raw/moel_forms/policy_data/files/6191/선진국 산안법체계.hwp` | 서식성 키워드 미포함 |
| 348 | skipped | `data/raw/moel_forms/policy_data/files/6191/선진국 산안법체계.hwpx` | 서식성 키워드 미포함 |
| 349 | skipped | `data/raw/moel_forms/policy_data/files/6232/MSDS팜플렛.hwp` | 서식성 키워드 미포함 |
| 350 | skipped | `data/raw/moel_forms/policy_data/files/6255/매뉴얼(석면해체제거작업)2.hwp` | 서식성 키워드 미포함 |
| 351 | skipped | `data/raw/moel_forms/policy_data/files/6255/매뉴얼(석면해체제거작업)2.hwpx` | 서식성 키워드 미포함 |
| 352 | skipped | `data/raw/moel_forms/policy_data/files/6284/산업안전보건위원회 운영 요령.hwp` | 서식성 키워드 미포함 |
| 353 | skipped | `data/raw/moel_forms/policy_data/files/6284/산업안전보건위원회 운영 요령.hwpx` | 서식성 키워드 미포함 |
| 354 | skipped | `data/raw/moel_forms/policy_data/files/6330/0409재해현황인터넷.hwp` | 서식성 키워드 미포함 |
| 355 | skipped | `data/raw/moel_forms/policy_data/files/6330/0409재해현황인터넷.hwpx` | 서식성 키워드 미포함 |
| 356 | skipped | `data/raw/moel_forms/policy_data/files/6450/5개년계획1223(최종).hwp` | 서식성 키워드 미포함 |
| 357 | skipped | `data/raw/moel_forms/policy_data/files/6450/5개년계획1223(최종).hwpx` | 서식성 키워드 미포함 |
| 358 | skipped | `data/raw/moel_forms/policy_data/files/6450/5개년계획요약1223(최종).hwp` | 서식성 키워드 미포함 |
| 359 | skipped | `data/raw/moel_forms/policy_data/files/6450/5개년계획요약1223(최종).hwpx` | 서식성 키워드 미포함 |
| 360 | skipped | `data/raw/moel_forms/policy_data/files/6560/04재해현황인터넷.hwp` | 서식성 키워드 미포함 |
| 361 | skipped | `data/raw/moel_forms/policy_data/files/6560/04재해현황인터넷.hwpx` | 서식성 키워드 미포함 |
| 362 | skipped | `data/raw/moel_forms/policy_data/files/6572/04년도결산보고서(산재기금).hwp` | 서식성 키워드 미포함 |
| 363 | skipped | `data/raw/moel_forms/policy_data/files/6572/04년도결산보고서(산재기금).hwpx` | 서식성 키워드 미포함 |
| 364 | skipped | `data/raw/moel_forms/policy_data/files/6875/0503재해현황인터넷.hwp` | 서식성 키워드 미포함 |
| 365 | skipped | `data/raw/moel_forms/policy_data/files/6875/0503재해현황인터넷.hwpx` | 서식성 키워드 미포함 |
| 366 | copied | `data/raw/moel_forms/policy_data/files/7589/건설업 위험성평가 활용가이드.hwp` | MOEL__안내서__건설업_위험성평가_활용가이드__N_A.hwp |
| 367 | copied | `data/raw/moel_forms/policy_data/files/7589/건설업 위험성평가 활용가이드.hwpx` | MOEL__안내서__건설업_위험성평가_활용가이드__N_A.hwpx |
| 368 | skipped | `data/raw/moel_forms/policy_data/files/7591/05올해의산안감독관포상계획[51122].hwp` | 서식성 키워드 미포함 |
| 369 | skipped | `data/raw/moel_forms/policy_data/files/7591/05올해의산안감독관포상계획[51122].hwpx` | 서식성 키워드 미포함 |
| 370 | skipped | `data/raw/moel_forms/policy_data/files/7626/06산재예방유공자포상계획.hwp` | 서식성 키워드 미포함 |
| 371 | skipped | `data/raw/moel_forms/policy_data/files/7626/06산재예방유공자포상계획.hwpx` | 서식성 키워드 미포함 |
| 372 | skipped | `data/raw/moel_forms/policy_data/files/7808/노사정 합동 미국 산업안전보건시찰 결과 보고서[1].hwp` | 서식성 키워드 미포함 |
| 373 | skipped | `data/raw/moel_forms/policy_data/files/7808/노사정 합동 미국 산업안전보건시찰 결과 보고서[1].hwpx` | 서식성 키워드 미포함 |
| 374 | skipped | `data/raw/moel_forms/policy_data/files/7811/0512산재통계(확정)1.hwp` | 서식성 키워드 미포함 |
| 375 | skipped | `data/raw/moel_forms/policy_data/files/7811/0512산재통계(확정)1.hwpx` | 서식성 키워드 미포함 |
| 376 | skipped | `data/raw/moel_forms/policy_data/files/7832/출장결과보고서.hwp` | 서식성 키워드 미포함 |
| 377 | skipped | `data/raw/moel_forms/policy_data/files/7832/출장결과보고서.hwpx` | 서식성 키워드 미포함 |
| 378 | skipped | `data/raw/moel_forms/policy_data/files/8054/관리책임자 등 선임보고서.hwp` | 서식성 키워드 미포함 |
| 379 | skipped | `data/raw/moel_forms/policy_data/files/8054/관리책임자 등 선임보고서.hwpx` | 서식성 키워드 미포함 |
| 380 | copied | `참조자료/위험성평가 표준안(경비).xls` | KOSHA__표준안__위험성평가_표준안_경비__N_A.xls |
| 381 | copied | `참조자료/표준실시규정.docx` | INTERNAL__규정__표준실시규정__N_A.docx |
| 382 | copied | `export/위험성평가표_공문기반_20250114_v2.xlsx` | INTERNAL__본표__위험성평가표_공문기반_20250114_v2__20250114.xlsx |
| 383 | copied | `export/위험성평가표_공문기반_20250114.xlsx` | INTERNAL__본표__위험성평가표_공문기반_20250114__20250114.xlsx |
| 384 | copied | `export/위험성평가표_표준양식_테스트.xlsx` | INTERNAL__본표_축약__위험성평가표_표준양식_테스트__N_A.xlsx |
| 385 | copied | `export/위험성평가표_최종.xlsx` | INTERNAL__테스트__위험성평가표_최종__N_A.xlsx |
| 386 | copied | `export/test.xlsx` | INTERNAL__테스트__test__N_A.xlsx |
| 387 | copied | `test_output.xlsx` | INTERNAL__테스트__test_output__N_A.xlsx |
| 388 | copied | `test_output_v2.xlsx` | INTERNAL__테스트__test_output_v2__N_A.xlsx |
| 389 | copied | `test_output_final.xlsx` | INTERNAL__테스트__test_output_final__N_A.xlsx |
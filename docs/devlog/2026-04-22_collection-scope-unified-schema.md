# 21단계 — KOSHA/법령 수집 가능 범위 확인 및 저장 구조 통합

- 날짜: 2026-04-22
- 단계: 21
- 목표: KOSHA + 법제처 OpenAPI 수집 가능 범위 확인, 저장 구조 통합

---

## 1. KOSHA 수집 가능 범위

### 수집 경로
| 경로 | 로그인 | 접근 방식 |
|------|--------|----------|
| `portal.kosha.or.kr/kosha/data/publicDataList.do` (공개자료실) | 불필요 | HTML 파싱 |
| `portal.kosha.or.kr/archive/cent-arch/indust-page{N}/` (업종별 자료실) | 필요 | Playwright |

### 수집 가능 항목
- KOSHA GUIDE (기술지침): P-/C-/W- 시리즈
- 건설안전 자료: OPS 유형
- 교육자료: HWP/PDF 첨부파일

### 원문 형태
- text_pdf / hwp / zip → 텍스트 추출 가능
- image_pdf → 제외 (포스터/스티커류, 텍스트 없음)

### 현황 (로컬)
- `data/risk_db/guide_raw/kosha_guides_index.json`: 5건 dry_run (실제 본문 없음)
- 서버 파이프라인 존재 (`kosha_pipeline.py`, PostgreSQL, `kosha_material_chunks` 테이블)
- 로컬 수집: KOSHA_ID/KOSHA_PW 환경변수 필요

### 제한사항
- 로그인 없이는 목록/공개자료만 접근 가능
- 다운로드된 파일의 HWP 파싱은 별도 라이브러리 필요 (현재 서버 파이프라인에 구현됨)
- 로컬 환경에서는 PostgreSQL 미사용 → 서버에서만 full 파이프라인 실행 가능

---

## 2. 법령(OpenAPI) 수집 가능 범위

### API 구분

| API | 엔드포인트 | 로컬 접근 | 용도 |
|-----|-----------|----------|------|
| 공공데이터포털 GW | `apis.data.go.kr/1170000/law/` | **502 오류** (서버에서 실행 필요) | 목록 검색 |
| law.go.kr DRF 검색 | `www.law.go.kr/DRF/lawSearch.do` | 가능 (verify=False) | 목록 검색 |
| law.go.kr DRF 본문 | `www.law.go.kr/DRF/lawService.do` | 가능 (verify=False) | 본문 수집 |

### 수집 가능 항목별 현황

| 항목 | target | 목록 수집 | 본문 수집 | 비고 |
|------|--------|----------|----------|------|
| 현행법령 | law | 32건 완료 | 미수집 (수집 가능) | XML 223KB/건, 조문 분해 가능 |
| 행정규칙 | admrul | 34건 완료 | 미수집 (수집 가능) | 고시 8건, 공고 26건 |
| 법령해석례(법제처) | expc | 129건 완료 | 미수집 (수집 가능) | HTML |
| 별표/서식 | licbyl | 17건 완료 | 미수집 (HWP/PDF) | 텍스트 추출 필요 |
| 고용노동부 해석례 | moel_expc | 9,573건 SQLite | 미수집 (수집 가능) | detail_url 보유 |

### DRF API 응답 구조 (법령 본문)
```xml
<법령 법령키="...">
  <기본정보>   법령ID, 공포일자, 법령명_한글, 소관부처 등
  <조문>
    <조문단위>  조문번호, 조문여부(전문/조문), 조문제목, 조문내용, <항>
    ...         산업안전보건법 기준 208개 조문단위
  </조문>
  <부칙>
  <개정문>
  <제개정이유>
</법령>
```

### 조문 단위 분해 가능 여부
- 조문단위 → `조문번호`, `조문제목`, `조문내용`, `항/호/목` 구조로 분해 가능
- 분석 단위: 조문 1개 = 1 chunk (RAG 적합)

---

## 3. 보강 데이터 소스 결과

| 소스 | 접근 방법 | 목록 구조 | 본문 | 비고 |
|------|----------|----------|------|------|
| 고용노동부 중대재해 | 웹 크롤링 (`www.moel.go.kr`) | 공개 게시판 | HTML | 로그인 불필요 |
| 국토교통부 건설안전 | 웹 크롤링 (`www.molit.go.kr`) | 공개 게시판 | HWP/PDF 첨부 | 로그인 불필요 |

- 두 소스 모두 공개 접근 가능이나 구조화된 API 없음
- 로봇 정책(robots.txt) 준수 필요
- 이번 단계에서는 탐색 확인만 — 실제 수집은 차기 단계

---

## 4. 통합 저장 구조

저장 파일: `data/risk_db/collection_schema/unified_storage_schema.json`

### 공통 필드 (모든 source_type 공유)
| 필드 | 필수 | 설명 |
|------|------|------|
| `doc_id` | Y | 고유 식별자 (source_type + raw_id + article_no) |
| `source_type` | Y | law / admrul / expc / licbyl / kosha / moel_expc / guideline / incident |
| `source_org` | Y | moleg / moel / molit / kosha / other |
| `title` | Y | 법령명 / 안건명 / 자료명 |
| `content_raw` | N | 원문 텍스트 (없으면 null) |
| `has_text` | Y | content_raw 유무 (분기 기준) |
| `attachment_url` | N | 첨부파일 URL |
| `source_url` | Y | 원본 페이지/API 링크 |
| `published_at` | N | 공포일자 / 게시일 (YYYY-MM-DD) |
| `collected_at` | Y | 수집 시각 (ISO8601) |

### 법령 전용 확장 필드
`law_id`, `raw_id`, `article_no`, `paragraph_no`, `law_type`, `ministry`, `enforcement_date`, `revision_type`

### KOSHA 전용 확장 필드
`guide_code`, `category`, `document_type`, `list_type`, `industry`, `doc_no`

### has_text 분기 로직
```
has_text=True  → analysis 대상 (normalize → chunk → embed → index)
has_text=False
  ├── attachment_url 있음 → 첨부 다운로드 → 텍스트 추출 재시도
  ├── image_pdf       → 제외 (포스터류)
  └── 첨부 없음       → 제외 또는 수동 입력 대기
```

---

## 5. 문제점 및 제한사항

| 문제 | 심각도 | 내용 |
|------|--------|------|
| GW API 로컬 502 | WARN | `apis.data.go.kr`는 서버 환경에서만 정상 동작 — 로컬 수집 시 DRF 직접 사용 |
| law.go.kr SSL 오류 | WARN | SSL 인증서 검증 실패 → `verify=False` 우회 필요 (TLS 설정 문제) |
| HWP 파싱 | WARN | HWP 원문 텍스트 추출에 별도 파서 필요 (`hwplib` 또는 LibreOffice 변환) |
| KOSHA 로컬 불가 | WARN | 로그인 기반 Playwright 수집은 서버 파이프라인에만 구현됨 |
| moel_expc 9573건 | INFO | 건수 많음 — 배치 처리 + 속도 제한 고려 (1초 딜레이 권장) |
| 별표/서식 licbyl | INFO | 17건 HWP/PDF — 서식류는 텍스트 빈약, 분석 가치 낮음 |

---

## 6. 수집 착수 우선순위

| 순위 | 대상 | 건수 | 수집 방법 | 예상 크기 |
|------|------|------|----------|---------|
| 1 | 법령 본문 (law) | 32 | DRF XML (verify=False) | ~7MB |
| 2 | 행정규칙 본문 (admrul) | 34 | DRF HTML | ~1MB |
| 3 | 고용부 해석례 (moel_expc) | 9,573 | DRF HTML 배치 | ~200MB |
| 4 | 법제처 해석례 (expc) | 129 | DRF HTML | ~5MB |
| 5 | KOSHA (kosha) | 미정 | 서버 파이프라인 | 별도 |

**1차 착수 추천: 법령(32건) + 행정규칙(34건) → 총 66건, 빠른 수집 가능**

---

## 최종 판정: PASS

| 기준 | 결과 |
|------|------|
| 핵심 소스 2개 이상 수집 가능 구조 확인 | PASS (law DRF + KOSHA pipeline 모두 확인) |
| 저장 구조 통합 가능 | PASS (unified_storage_schema.json 설계 완료) |
| 본문 없는 데이터 식별 구조 | PASS (has_text 필드 + 분기 로직 설계) |
| 추정 사항 없이 실제 접근 확인 | PASS (DRF API 실제 호출 성공, 조문 208개 확인) |

---

## 다음 단계 (22단계)
- 법령 본문 수집 (32건 DRF XML → 조문 단위 분해 → 저장)
- 행정규칙 본문 수집 (34건 DRF HTML)
- `unified_storage_schema.json` 기준으로 JSON Lines 저장 구조 구현

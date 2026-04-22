# 위험성평가표 DB 데이터 딕셔너리 (v1.0 초안)

- 대상 DBMS : PostgreSQL 14+
- 작성일   : 2026-04-22
- 범위     : 위험성평가표 자동생성기 운영 DB 1차 설계 (KOSHA / law / expc / video 확장 대비)
- 원천 참조 : `data/risk_db/schema/kosha_document_schema.json`,
            `data/normalized/kosha/*.json`,
            `data/risk_db/laws/law_moel_expc.json`

---

## 설계 개요

### documents 가 공통 본체인 이유
- KOSHA / law / expc / video 모두 **“제목·본문·원천 식별자·수집시점”** 이라는 공통 성질을 가진다.
- 공통 본체를 분리하면:
  - 검색·정렬·중복 제거를 한 쿼리로 처리할 수 있다.
  - 소스가 추가되어도(예: video) 새 테이블 없이 `source_type` 값만 늘리면 된다.
  - 매핑 테이블(`document_*_map`)이 단일 FK로 끝나므로 운영이 단순해진다.

### source_type 별 상세 메타를 분리한 이유
- `documents` 에 모든 메타(법령 조문, 해석례 기관, KOSHA 업종 등)를 평면화하면 NULL 컬럼이 폭증한다.
- 소스별로 **서로 다른 필드 집합**을 가진다:
  - KOSHA : 업종, 태그
  - law   : 법령명·조문·소관부처·시행일
  - expc  : 의안번호·질의·회시·회시일
- 1:1 확장 테이블(`kosha_meta` / `law_meta` / `expc_meta`) 로 나눠서
  공통 본체를 깔끔하게 유지하고, 소스별 인덱스도 각각 최적화한다.
- 향후 `video_meta` 도 같은 패턴으로 추가하면 된다.

### document_*_map 을 별도 테이블로 둔 이유
- 현재 JSON 은 `hazards: []`, `work_types: []`, `equipment: []` 처럼 배열을 갖는다.
- 배열 컬럼/JSONB 를 그대로 두면:
  - **“비계 작업의 모든 문서”** 같은 역방향 조회 성능이 나쁘다.
  - 코드 이름이 바뀌면 모든 문서를 다시 써야 한다.
- 정규화된 N:M 매핑 테이블 + 표준 코드 테이블(`hazards`, `work_types`, `equipment`) 구조로 두면:
  - 표준 코드 변경을 한 곳에서만 관리한다.
  - 위험요인/작업유형/장비 기준 역색인을 모두 인덱스로 지원한다.

### risk_assessment_results 를 캐시/로그성 테이블로 둔 이유
- 이 테이블은 formatter(`format_risk_assessment`) 의 **출력 결과**를 그대로 저장한다.
- 언제든 같은 질의로 재생성 가능한 파생 데이터이므로,
  - **정규화 대상이 아니다.** JSONB 로 한 번에 저장한다.
  - 재실행/A/B 비교/감사 로그 용도로 append-only 성격을 가진다.
- 공통 본체와 연결이 **직접적이지 않기 때문에** FK 를 의도적으로 두지 않았다.
  (결과에는 여러 document_id 가 섞여 들어가며, document 삭제 시 결과까지 지울 필요는 없다.)

---

## 테이블별 상세

### 1) documents
- **목적** : 모든 소스의 공통 문서 본체. 검색/정렬/중복의 기준 테이블.
- **PK** : `id` (BIGSERIAL)
- **Unique** : `(source_type, source_id)` — 원천 내에서 중복 방지
- **주요 컬럼**
  - `source_type` : kosha / law / expc / video
  - `source_id` : 원천 ID (medSeq, lawId, expcId 등)
  - `doc_category` : kosha_opl / kosha_guide / law_statute / law_admrul / law_expc …
  - `title`, `title_normalized`, `body_text`
  - `has_text`, `content_length`
  - `url`, `file_url`, `pdf_path`, `file_sha256`
  - `language`, `status`
  - `published_at`, `collected_at`, `created_at`, `updated_at`
- **JSON 대응**
  - KOSHA normalized : `source` → `source_type`, `source_id`, `doc_category`,
    `title`, `title_normalized`, `body_text`, `has_text`, `content_length`,
    `url`, `file_url`, `pdf_path`, `file_sha256`, `published_at`, `collected_at`,
    `language`, `status` 와 1:1 매핑.
  - law normalized (`law_moel_expc.json`) : `law_id` → `source_id`,
    `law_type`/카테고리 → `doc_category`, `title*` → `title*`,
    `promulgation_date` → `published_at`.

### 2) hazards
- **목적** : 위험요인 표준 코드 마스터.
- **PK** : `hazard_code`
- **주요 컬럼** : `hazard_name`, `sort_order`, `is_active`
- **JSON 대응** : normalized JSON 의 `hazards[]` 원소 값이 `hazard_code` 에 해당.

### 3) work_types
- **목적** : 작업유형 표준 코드 마스터.
- **PK** : `work_type_code`
- **JSON 대응** : `work_types[]` 원소.

### 4) equipment
- **목적** : 장비/설비 표준 코드 마스터.
- **PK** : `equipment_code`
- **JSON 대응** : `equipment[]` 원소.

### 5) document_hazard_map
- **목적** : 문서 ↔ 위험요인 N:M 매핑.
- **PK** : `(document_id, hazard_code)`
- **FK**
  - `document_id` → `documents(id)` (ON DELETE CASCADE)
  - `hazard_code` → `hazards(hazard_code)` (ON DELETE RESTRICT)
- **기타** : `is_primary` — 대표 위험요인 플래그(옵션).
- **JSON 대응** : `hazards[]` 배열의 각 원소가 한 행이 된다.

### 6) document_work_type_map
- **목적** : 문서 ↔ 작업유형 N:M 매핑.
- **PK** : `(document_id, work_type_code)`
- **FK** : `documents(id)` CASCADE / `work_types(work_type_code)` RESTRICT
- **JSON 대응** : `work_types[]` 배열.

### 7) document_equipment_map
- **목적** : 문서 ↔ 장비 N:M 매핑.
- **PK** : `(document_id, equipment_code)`
- **FK** : `documents(id)` CASCADE / `equipment(equipment_code)` RESTRICT
- **JSON 대응** : `equipment[]` 배열.

### 8) kosha_meta
- **목적** : KOSHA 고유 속성 확장.
- **PK / FK** : `document_id` (1:1, documents(id) CASCADE)
- **주요 컬럼**
  - `industry` — 업종(제조업/건설업 등)
  - `tags` JSONB — 자유 태그
- **JSON 대응** : normalized JSON 의 `industry`, `tags` 필드.

### 9) law_meta
- **목적** : 법령/행정규칙/해석례의 법조문 계열 속성.
- **PK / FK** : `document_id` (1:1, documents(id) CASCADE)
- **주요 컬럼** : `law_name`, `law_id`, `article_no`, `promulgation_date`,
  `effective_date`, `ministry`, `extra` JSONB
- **JSON 대응**
  - law 파일의 `title` → `law_name`
  - `law_id` → `law_id`
  - `promulgation_date` → `promulgation_date`
  - `enforcement_date` → `effective_date`
  - `ministry_name` / `authority` → `ministry`
  - `keywords` 등 기타 메타는 `extra` JSONB 로.

### 10) expc_meta
- **목적** : 해석례(expc) 전용 질의/회시 속성.
- **PK / FK** : `document_id` (1:1, documents(id) CASCADE)
- **주요 컬럼** : `agenda_no`, `agency_question`, `agency_answer`, `reply_date`,
  `question_summary`, `answer_summary`, `reason_text`, `extra` JSONB
- **JSON 대응**
  - 해석례 JSON 의 `reference_no` 등 의안번호 → `agenda_no`
  - `inquire_org` → `agency_question`
  - `authority` → `agency_answer`
  - `issued_at` → `reply_date`
  - 질의/회시/이유 요약은 normalize 단계에서 추출하여 매핑.

### 11) risk_assessment_results
- **목적** : formatter 출력물(위험성평가표 JSON)을 그대로 보관.
- **PK** : `id`
- **주요 컬럼**
  - `query` — 원 검색어/작업명
  - `representative_work_type`, `main_hazard`
  - `sub_hazards`, `risk_factors`, `controls`,
    `legal_basis`, `reference_cases` (모두 JSONB)
  - `source_summary`, `meta` (JSONB)
- **FK** : 없음 (의도적으로 비정규화, 캐시/감사성 테이블)
- **JSON 대응** : `format_risk_assessment` 함수가 반환하는 dict 의 상위 키 구조와 1:1.

### 12) collection_runs
- **목적** : 원천 수집기의 실행 이력.
- **PK** : `id`
- **주요 컬럼** : `source_type`, `run_date`, `status`,
  `total_count`, `success_count`, `fail_count`, `note`,
  `started_at`, `finished_at`, `created_at`
- **JSON 대응** : 기존 로그(`scraper/reports/*`, `kosha_dl*.log`)를 요약한 메타 레벨.

### 13) normalization_runs
- **목적** : 정규화 스크립트(`scripts/normalize/*`)의 실행 이력.
- 구조는 `collection_runs` 와 동일.

---

## JSON ↔ DB 대응 요약표

| normalized JSON 필드 | 저장 테이블 / 컬럼 |
|---|---|
| source | documents.source_type |
| source_id | documents.source_id |
| doc_category | documents.doc_category |
| title | documents.title |
| title_normalized | documents.title_normalized |
| body_text | documents.body_text |
| has_text | documents.has_text |
| content_length | documents.content_length |
| url | documents.url |
| file_url | documents.file_url |
| pdf_path | documents.pdf_path |
| file_sha256 | documents.file_sha256 |
| language | documents.language |
| status | documents.status |
| published_at | documents.published_at |
| collected_at | documents.collected_at |
| hazards[] | document_hazard_map + hazards |
| work_types[] | document_work_type_map + work_types |
| equipment[] | document_equipment_map + equipment |
| industry | kosha_meta.industry |
| tags | kosha_meta.tags |
| law 관련 필드 | law_meta.* |
| 해석례 질의/회시 | expc_meta.* |

---

## 확장 여지

- **video 추가** : `source_type='video'` + `video_meta` 1:1 테이블 신설만으로 확장.
- **전문검색** : `documents.title`, `documents.body_text` 에 GIN 인덱스(trigram 또는 tsvector)를 추가하면 `ILIKE %...%` 대비 수십 배 이상 가속 기대.
- **enum 타입** : `source_type`, `status` 등은 운영 안정화 후 CHECK 또는 ENUM 으로 고정.

# 산업안전보건 전체 데이터 수집·분류 커버리지 전수 감사

**버전**: 1.0  
**작성일**: 2026-04-25 KST  
**기준**: audit_safety_gap.py v3.0 / document_catalog v2.1 (92종) / kosha_context_index v1.0

---

## 1. KOSHA 현재 기준선 (고정값)

| 항목 | 수치 |
|------|------|
| classification source (parse_status=success) | 2,047건 |
| kosha_context_index total rows | 4,797건 |
| indexed materials (distinct) | 1,928건 |
| indexed chunks (distinct) | 4,755건 |
| fallback 행 (chunk 없는 자료) | 42건 |
| construction indexed | 1,028건 |
| UNKNOWN indexed (태그 전무) | 686건 |
| hazard 태그 행 | 3,971건 |
| work_type 태그 행 | 3,433건 |
| equipment 태그 행 | 1,411건 |
| 검색 검증 10개 케이스 | 10/10 OK |

**분류 현황 (kosha_material_classifications)**

| 항목 | 수치 |
|------|------|
| 전체 분류 완료 | 2,047건 |
| KOSHA Guide 번호 추출 | 290건 |
| UNKNOWN (태그 전무) | 245건 (12.0%) |
| 건설업 classified | 324건 |
| 건설업 중 hazard_tags 있음 | 289건 (89.2%) |

**KOSHA raw 전체 현황 (kosha_material_files)**

| parse_status | 건수 |
|--------------|------|
| success | 2,047 |
| image_pdf | 2,434 |
| duplicate | 1,621 |
| excluded_foreign | 8,957 |
| excluded_mixed | 367 |
| extracted (zip 내부) | 476 |
| failed | 64 |
| failed_unzip | 111 |
| pending (hwp/media 등) | 329 |
| unsupported | 49 |
| **합계** | **~16,455** |

---

## 2. 전체 출처별 수집·파싱·분류·인덱싱 현황

### 2-1. 데이터베이스 (PostgreSQL common_data)

| 테이블명 | 행 수 | 용도 |
|----------|-------|------|
| kosha_materials | ~6,900 | KOSHA 자료 메타 |
| kosha_material_files | ~16,455 | KOSHA 파일별 상태 |
| kosha_material_chunks | 4,907 | KOSHA 청크 |
| kosha_chunk_tags | 4,907 | 청크 태그 |
| kosha_material_classifications | 2,047 | KOSHA 세부 분류 |
| kosha_context_index | 4,797 | 검색용 인덱스 |

> ⚠️ 법령·고용노동부·내부마스터 데이터는 PostgreSQL에 적재되지 않음. 파일 기반 관리 중.

### 2-2. 파일 기반 원시 데이터

| 출처분류 | source_count | downloaded | parsed | classified | indexed | 비고 |
|---------|-------------|-----------|--------|-----------|---------|------|
| LAW (법령 원문) | 1 folder | 1 index JSON | ✗ DB 없음 | ✗ | ✗ | data/raw/law_api/law/ |
| ENFORCEMENT_DECREE (시행령) | 포함 | 포함 | ✗ | ✗ | ✗ | law 폴더 내 포함 |
| ENFORCEMENT_RULE (시행규칙) | 포함 | 포함 | ✗ | ✗ | ✗ | law 폴더 내 포함 |
| SAFETY_HEALTH_RULE (안전보건기준규칙) | 포함 | 포함 | ✗ | ✗ | ✗ | law 폴더 내 포함 |
| ADMIN_RULE (행정규칙/고시) | 1 folder | 1 index JSON | ✗ | ✗ | ✗ | data/raw/law_api/admrul/ |
| LAW_FORM (별표/서식) | 80+ PDF | 80+ PDF 수집 | ✗ | ✗ | ✗ | data/raw/law_api/licbyl/files/ |
| LAW_INTERPRETATION (법령해석례) | 1 folder | 1 index JSON | ✗ | ✗ | ✗ | data/raw/law_api/expc/ |
| MOEL_QA (질의회시) | ~346 | 346 | ✗ DB 없음 | ✗ | ✗ | data/raw/moel_forms/, data/law_db/moel_expc.db (SQLite) |
| MOEL_GUIDE (고용부 지침) | ~346 | 346 | ✗ | ✗ | ✗ | data/raw/moel_forms/ |
| KOSHA_GUIDE | 포함 | 2,047 success | ✓ | ✓ 290건 | ✓ | DB 적재 완료 |
| KOSHA_OPS (교육자료) | 포함 | 포함 | ✓ | ✓ | ✓ | DB 적재 완료 |
| KOSHA_CHECKLIST | 포함 | 포함 | ✓ | ✓ | ✓ | DB 적재 완료 |
| KOSHA_EXTERNAL | 17 | 17 | ✗ 미처리 | ✗ | ✗ | data/raw/kosha_external/ |
| KOSHA_FORMS | 8 | 8 | ✗ 미처리 | ✗ | ✗ | data/raw/kosha_forms/ |
| PRACTICAL_FORM (실무서식) | 174 | 174 | ✗ 미분류 | ✗ | ✗ | data/forms/ (A/B/C 분류) |
| INTERNAL_MASTER (마스터) | 15 YAML | 15 | N/A | N/A | ✗ | data/masters/safety/ |
| FORM_BUILDER (서식생성기) | 10종 | N/A | N/A | N/A | engine/ | engine/output/ 구현체 |
| ENGINE (판정엔진) | 4종 | N/A | N/A | N/A | engine/ | rag, rule_selector, safety_decision, kras_connector |

---

## 3. 문서군별 커버리지 (92종 기준)

범례: ✓=완료 △=부분 ✗=없음

| 문서군 | 총종수 | DONE | 법령근거 | 시행규칙 | 고시 | 별표서식 | 고용부자료 | KOSHA자료 | 실무서식 | evidence | form_builder | engine연결 | context_index |
|--------|--------|------|---------|---------|------|---------|----------|---------|---------|---------|------------|----------|-------------|
| WP 작업계획서 | 14 | 6 | ✓ | ✓ | △ | △ | △ | ✓ | △ | ✗ | 6종 ✓ | ✓ 6건 | ✓ |
| EQ 장비사용계획서 | 16 | 2 | ✓ | ✓ | △ | ✗ | △ | ✓ | △ | ✗ | 2종 △ | △ | ✓ |
| RA 위험성평가 | 6 | 2 | ✓ | ✓ | ✓ | △ | ✓ | ✓ | ✓ | ✗ | 2종 △ | ✓ 2건 | ✓ |
| ED 안전보건교육 | 5 | 1 | ✓ | ✓ | △ | ✓ | ✓ | ✓ | ✓ | ✓ C-06 | 1종 △ | ✓ 1건 | ✓ |
| PTW 작업허가서 | 8 | 1 | ✓ | ✓ | △ | ✗ | △ | ✓ | ✓ | ✗ | 1종 △ | ✓ 1건 | ✓ |
| DL 일일안전관리 | 5 | 0 | ✓ | ✓ | △ | ✗ | △ | △ | △ | ✗ | ✗ | ✗ | △ |
| CL 점검표 | 10 | 1 | ✓ | ✓ | △ | △ | ✓ | ✓ | ✓ | ✗ | 1종 △ | △ | ✓ |
| PPE 보호구관리 | 4 | 0 | ✓ | ✓ | △ | △ | △ | ✓ | △ | ✗ | ✗ | ✗ | △ |
| HM 보건관리 | 2 | 0 | ✓ | ✓ | △ | △ | ✓ | ✓ | △ | ✓ G-02/G-03 | ✗ **P0** | ✗ | ✓ |
| CHEM 화학물질 | (HM/PPE 포함) | — | ✓ | ✓ | ✓ | △ | ✓ | ✓ | △ | ✗ | ✗ | ✗ | ✓ |
| CM 협력업체관리 | 7 | 0 | ✓ | ✓ | △ | △ | △ | △ | △ | ✗ | ✗ | ✗ | △ |
| EM 사고비상대응 | 6 | 0 | ✓ | ✓ | △ | ✓ EM-001 | △ | △ | △ | ✗ | ✗ | ✗ | △ |
| TS 공종별특화 | 5 | 0(3 OUT) | ✓ | ✓ | △ | ✓ | △ | △ | △ | ✗ | ✗ | ✗ | △ |
| SP 실무보강 | 4 | 0 | ✓ | ✓ | △ | ✗ | △ | △ | △ | ✗ | ✗ | ✗ | △ |

**form_builder 구현 현황 요약**

| 구현체 (engine/output/) | 대상 ID |
|------------------------|---------|
| workplan_builder.py | WP-001 (굴착) |
| tower_crane_workplan_builder.py | WP-006 |
| mobile_crane_workplan_builder.py | WP-007 |
| vehicle_workplan_builder.py | WP-008 |
| material_handling_workplan_builder.py | WP-009, EQ-001 |
| confined_space_workplan_builder.py | WP-014 |
| confined_space_permit_builder.py | PTW-001 |
| confined_space_checklist_builder.py | CL-010 |
| education_log_builder.py | ED-001 |
| tbm_log_builder.py | RA-004 |
| **미구현 P0** | EQ-003, EQ-004, HM-001, HM-002 |

---

## 4. 추가 수집·보강 필요 목록

### 4-A. 아직 수집 대상 목록도 없는 것

| 항목 | 규모 추정 | 비고 |
|------|----------|------|
| 고용노동부 질의회시 DB화 | 수백건 | data/law_db/moel_expc.db에 있으나 PostgreSQL 미적재 |
| 산업안전보건기준규칙 조문별 조회 인덱스 | 700조+ | law_api 인덱스만, 조문 파싱 미구현 |
| 중대재해처벌법 시행령 체계도 | 15조 | document_catalog 근거로만 사용, 원문 미파싱 |
| KOSHA_EXTERNAL 17건 분류 적재 | 17건 | data/raw/kosha_external/ 미처리 |
| KOSHA_FORMS 8건 분류 적재 | 8건 | data/raw/kosha_forms/ 미처리 |

### 4-B. 목록은 있으나 다운로드 안 된 것

| 항목 | 현황 | 비고 |
|------|------|------|
| 법제처 별표/서식 전체 | 80+ PDF 수집됨, DB 미적재 | data/raw/law_api/licbyl/files/ |
| 고용부 고시·예규 전체 | index 1건만, 전문 미수집 | data/raw/law_api/admrul/ |
| 법령해석례 전체 | index 1건만, 전문 미수집 | data/raw/law_api/expc/ |

### 4-C. 다운로드됐으나 파싱 실패

| 항목 | 건수 | 비고 |
|------|------|------|
| failed_unzip | 111건 | zip 압축 해제 실패 |
| text_pdf failed | 64건 | PDF 텍스트 추출 실패 |
| hwp pending | 9건 | HWP 파서 미처리 |
| MOEL forms 파싱 | 346건 | 다운로드 완료, DB 미적재 |
| LAW_FORM PDF 파싱 | 80+건 | 수집 완료, DB 미적재 |

### 4-D. 파싱됐으나 분류 안 된 것

| 항목 | 건수 | 비고 |
|------|------|------|
| KOSHA UNKNOWN (태그 전무) | 686행 (인덱스 기준) | 키워드 미매칭 |
| KOSHA UNKNOWN (classifications 기준) | 245건 | Guide번호 미추출 + 태그 없음 |
| MOEL forms | 346건 | 파싱 자체 미완 |

### 4-E. 분류됐으나 문서 카탈로그와 연결 안 된 것

| 항목 | 현황 | 비고 |
|------|------|------|
| kosha_context_index ↔ document_catalog 매핑 | 미구현 | context_index에 document_id 컬럼 없음 |
| MOEL 자료 ↔ document_catalog 매핑 | 미구현 | |
| 실무서식(data/forms/) ↔ document_catalog | source_map.csv 존재, DB 미적재 | |

### 4-F. 법령 evidence가 없는 것

| 항목 | 현황 | 비고 |
|------|------|------|
| evidence 파일 보유 | 4건 (C-06, E-06, G-02, G-03) | |
| evidence 없는 document_catalog 항목 | 88건 (92 - 4) | |
| 우선 확보 필요: HM-001, HM-002 | catalog_only, evidence VERIFIED 표기만 | 법령 원문 연결 파일 미생성 |
| 우선 확보 필요: RA-001 | 산안법 제36조, 고용노동부고시 제2023-19호 | |
| 우선 확보 필요: WP-001~WP-014 | 산안기준규칙 제38조 각호 | |

### 4-G. form_builder가 없는 것 (우선순위순)

| 우선순위 | ID | 항목 | 연계 builder |
|---------|----|----- |------------|
| P0 | EQ-003 | 타워크레인 작업계획서 (장비특화) | WP-006 재사용 가능 |
| P0 | EQ-004 | 이동식 크레인 작업계획서 (장비특화) | WP-007 재사용 가능 |
| P0 | HM-001 | 작업환경측정 결과보고서 | 신규 구현 필요 |
| P0 | HM-002 | 특수건강진단 결과 관리 대장 | 신규 구현 필요 |
| P1 | PTW-002 | 화기작업 허가서 | 신규 |
| P1 | PTW-003 | 고소작업 허가서 | 신규 |
| P1 | PTW-007 | 중량물 인양 작업 허가서 | 신규 |
| P1 | ED-003 | 특별안전보건교육 일지 | ED-001 파생 |
| P1 | WP-002 | 터널 굴착 작업계획서 | WP-001 파생 |
| P1 | WP-003 | 건축물 해체 작업계획서 | 신규 |
| P1 | WP-005 | 중량물 취급 작업계획서 | 신규 |
| P1 | WP-010 | 항타기·항발기 작업계획서 | 신규 |
| P1 | WP-011 | 전기 작업계획서 | 신규 |
| P1 | CL-001 | 비계·동바리 설치 점검표 | 신규 |
| P1 | CL-003 | 건설 장비 일일 사전 점검표 | 신규 |
| P1 | DL-001 | 안전관리 일지 | 신규 |
| P1 | A-15 | 거푸집·동바리 WP-015 | 법령 확인 후 |

### 4-H. engine 연결이 없는 것

| 현황 | 건수 |
|------|------|
| engine_coverage=YES | 20건 |
| engine_coverage=PARTIAL | 3건 |
| engine_coverage=NO | 87건 |
| engine 연결 보류 사유 | context_index read-only 연결 단계 미진행 |

---

## 5. 추가 수집 우선순위

### P0 — 즉시 조치 (법정 의무 + form_builder 병목)

| 번호 | 항목 | 이유 | 조치 |
|------|------|------|------|
| P0-1 | HM-001 form_builder 구현 | evidence VERIFIED, P0, builder 미구현 | 산안법 제125조 기반 서식 구현 |
| P0-2 | HM-002 form_builder 구현 | evidence VERIFIED, P0, builder 미구현 | 산안법 제130조 기반 서식 구현 |
| P0-3 | EQ-003 form_builder 구현 | P0, WP-006 builder 재사용으로 신속 완료 가능 | tower_crane_workplan_builder 래핑 |
| P0-4 | EQ-004 form_builder 구현 | P0, WP-007 builder 재사용으로 신속 완료 가능 | mobile_crane_workplan_builder 래핑 |

### P1 — 단기 보강 (법령 근거 있음, 노동부 점검 대응 필요)

| 번호 | 항목 | 이유 |
|------|------|------|
| P1-1 | 거푸집·동바리 WP-015 등록 | 법령 원문 확인 후 document_catalog 등록 |
| P1-2 | evidence 파일 확장 | WP/RA/ED 핵심 항목 법령 원문 연결 |
| P1-3 | PTW-002/003/007 form_builder | 화기·고소·중량물 허가서 현장 필수 |
| P1-4 | ED-003 특별안전보건교육 form_builder | 별표5 39개 작업 대상 법정 |
| P1-5 | MOEL forms PostgreSQL 적재 | 질의회시·지침 346건 DB화 |
| P1-6 | 고용부 고시·예규 전문 수집 | admrul 인덱스만 있음 |
| P1-7 | 안전관리자/보건관리자 직무교육 | D축 MISSING P1 |
| P1-8 | 비계 조립 후 점검 INSP_SCAFF | E축 MISSING P1 |
| P1-9 | 유해인자 노출 근로자 관리 대장 | G축 MISSING P1 |
| P1-10 | DL-001 안전관리 일지 form_builder | 매일 작성 실무 핵심 |

### P2 — 중기 보강

| 번호 | 항목 |
|------|------|
| P2-1 | failed_unzip 111건 재처리 |
| P2-2 | text_pdf failed 64건 재처리 |
| P2-3 | hwp pending 9건 처리 |
| P2-4 | KOSHA UNKNOWN 245건 키워드 사전 보강 후 재분류 |
| P2-5 | kosha_context_index ↔ document_catalog 매핑 테이블 |
| P2-6 | 법제처 별표/서식 80+건 파싱 및 DB 적재 |
| P2-7 | CL/EM/CM form_builder 순차 구현 |
| P2-8 | context_score 임계값 기반 엔진 필터링 설계 |

### P3 — 장기 과제

| 번호 | 항목 |
|------|------|
| P3-1 | image_pdf 2,434건 OCR 처리 |
| P3-2 | SP/TS(OUT 제외) form_builder |
| P3-3 | 안전문화 자료 선택형 서식 |
| P3-4 | KOSHA_EXTERNAL/FORMS 25건 적재 |

---

## 6. 통합 인덱스 설계안 (safety_context_index, 이번 단계 생성 안 함)

### 설계 목적

현재 `kosha_context_index`는 KOSHA 전용이다.  
법령·고용노동부·내부마스터·실무서식이 통합되면 `safety_context_index`로 확장한다.

### 테이블 설계안

#### safety_source_documents
법령·KOSHA·MOEL·내부 모든 원본 문서의 통합 레지스트리.

| 필드 | 설명 |
|------|------|
| id | bigserial PK |
| source_type | LAW / KOSHA / MOEL / PRACTICAL / INTERNAL |
| source_id | 원본 시스템 ID (kosha material_id, law 조문번호 등) |
| title | 문서명 |
| doc_category | 문서 분류 |
| legal_ref | 법령 근거 (조문번호) |
| raw_path | 파일 경로 |
| parse_status | pending / success / failed |
| lang | ko / en |
| created_at | |

#### safety_source_classifications
출처별 세부 분류 (현재 kosha_material_classifications의 일반화).

| 필드 | 설명 |
|------|------|
| id | bigserial PK |
| source_doc_id | safety_source_documents.id FK |
| primary_industry | construction / manufacturing / ... |
| safety_domain | fall / electric / ... |
| document_type | guide / checklist / form / ... |
| hazard_tags | jsonb |
| work_type_tags | jsonb |
| equipment_tags | jsonb |
| confidence | numeric |
| classifier_version | |

#### safety_source_evidence_links
법령 원문과 document_catalog 항목 간 연결.

| 필드 | 설명 |
|------|------|
| id | bigserial PK |
| document_id | document_catalog의 id (예: WP-001) |
| source_doc_id | safety_source_documents.id FK |
| law_article | 법령 조문 (예: 산안법 제36조) |
| evidence_status | VERIFIED / NEEDS_VERIFICATION |
| verified_at | |

#### safety_document_requirement_map
document_catalog 92종과 출처·형성기·엔진 간의 연결 매핑.

| 필드 | 설명 |
|------|------|
| id | serial PK |
| document_id | document_catalog id |
| form_builder | engine/output/ 모듈명 |
| source_type | 주 출처 분류 |
| engine_coverage | YES / PARTIAL / NO |
| context_index_linked | boolean |
| evidence_count | 연결 evidence 파일 수 |

#### safety_context_index
(현재 kosha_context_index의 확장판)  
kosha_context_index와 동일 스키마 + source_type, document_id 컬럼 추가.

| 추가 필드 | 설명 |
|----------|------|
| source_type | KOSHA / LAW / MOEL / PRACTICAL |
| document_id | document_catalog.id (NULL 가능) |
| law_article | 법령 조문 직접 인덱싱 |

---

## 7. 다음 실행 계획

### 즉시 (P0, 이번 단계 완료 후)
1. EQ-003 form_builder — WP-006 builder 래핑, 1일 내 완료 가능
2. EQ-004 form_builder — WP-007 builder 래핑, 1일 내 완료 가능
3. HM-001 form_builder — 산안법 제125조 기반, 신규 구현 3~5일
4. HM-002 form_builder — 산안법 제130조 기반, 신규 구현 3~5일

### 단기 (P1, 1~2주)
5. MOEL forms 346건 PostgreSQL 적재 스키마 설계 및 적재
6. evidence 파일 확장 (핵심 WP/RA/ED 항목)
7. PTW-002/003/007 form_builder
8. KOSHA UNKNOWN 재분류 키워드 사전 강화

### 중기 (P2, 2~4주)
9. failed_unzip 111 / hwp 9 / text_pdf failed 64 재처리
10. 법제처 별표/서식 파싱 및 DB 적재
11. kosha_context_index ↔ document_catalog 매핑
12. 위험성평가 엔진 kosha_context_index read-only 연결

### 장기 (P3)
13. image_pdf OCR
14. safety_context_index 통합 확장

---

## 8. 집계 기준 SQL

```sql
-- KOSHA 수집 현황
SELECT parse_status, file_type, COUNT(*) FROM kosha_material_files
GROUP BY parse_status, file_type ORDER BY parse_status, file_type;

-- 분류 완료
SELECT COUNT(*) FROM kosha_material_classifications;

-- context_index
SELECT COUNT(*), COUNT(DISTINCT material_id), COUNT(DISTINCT chunk_id)
FROM kosha_context_index;

-- UNKNOWN
SELECT COUNT(*) FROM kosha_context_index
WHERE kosha_guide_code IS NULL AND hazard_tags='[]'::jsonb AND work_type_tags='[]'::jsonb;

-- 건설업
SELECT COUNT(*) FROM kosha_context_index WHERE primary_industry='construction';
```

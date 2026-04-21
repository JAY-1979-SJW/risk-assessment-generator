# Risk Data Roadmap — v1.0

## 1. 목적

RAG Risk Engine v1.2 의 검색 품질을 향상시키기 위해 체계적인 위험성 평가 데이터 자산을 구축한다.  
엔진 자체는 수정하지 않으며, 데이터 레이어만 확장한다.

---

## 2. 데이터 구조 (5개 축)

```
data/risk_db/
├── work_taxonomy/          # 공종·작업유형 분류
│   ├── work_trades.json
│   ├── work_types.json
│   └── work_hazards_map.json
├── hazard_action/          # 위험유형·통제수단·PPE
│   ├── hazards.json
│   ├── hazard_controls.json
│   └── hazard_ppe.json
├── equipment/              # 장비·위험·통제
│   ├── equipment_master.json
│   ├── equipment_hazards.json
│   └── equipment_controls.json
├── real_cases/             # 실제 사례 기반 평가
│   └── real_assessment_cases.json
└── law_standard/           # 법령·기준 참조
    ├── safety_laws.json
    └── law_hazard_map.json
```

---

## 3. 파일별 현황

| 파일 | 레코드 수 | 소스 |
|------|-----------|------|
| work_trades.json | 25 trades | 건설기술진흥법 시행령 별표 |
| work_types.json | ~75 types | KOSHA 안전보건교육 + sample_chunks |
| work_hazards_map.json | 48 mappings | sample_chunks 직접 추출 + 규칙 기반 |
| hazards.json | 14 hazard types | hazard_classifier.py 분류체계 |
| hazard_controls.json | 50+ entries | sample_chunks ids 1-33 + 법령 |
| hazard_ppe.json | 35+ entries | sample_chunks + 규칙 제32조 |
| equipment_master.json | 22 items | 규칙 크레인·비계·리프트 조항 |
| equipment_hazards.json | 42 mappings | 규칙 + sample_chunks |
| equipment_controls.json | 53 entries | 규칙 장비별 안전기준 + sample_chunks |
| real_assessment_cases.json | 15 cases | sample_chunks ids 1-22, 29-33 |
| safety_laws.json | 33 laws | sample_chunks law_ref + 국가법령정보센터 |
| law_hazard_map.json | 56 mappings | safety_laws → hazard 직접 매핑 |

**총 데이터 자산: 12개 파일, 450+ 레코드**

---

## 4. DB 스키마 (rd_ prefix — 003_risk_data_schema.sql)

```sql
-- 공종 분류
rd_work_trades       (trade_code PK, trade_name_ko, risk_level, law_ref)
rd_work_types        (type_code PK, trade_code FK, type_name_ko, risk_level)
rd_work_hazards_map  (id PK, work_type_code, hazard_code, frequency, severity)

-- 위험유형·통제
rd_hazards           (hazard_code PK, hazard_name_ko, severity_default)
rd_hazard_scenarios  (id PK, hazard_code, scenario_desc, trigger_condition)
rd_hazard_controls   (id PK, hazard_code, control_type, control_desc)
rd_hazard_ppe        (id PK, hazard_code, ppe_name_ko, ppe_standard)

-- 장비
rd_equipment_master  (equipment_code PK, name_ko, equipment_type, law_ref)
rd_equipment_hazards (id PK, equipment_code, hazard_code, condition_desc)
rd_equipment_controls(id PK, equipment_code, hazard_code, control_type, control_desc)

-- 실사례
rd_real_cases        (case_id PK, trade_code, work_type_code, hazard_codes, ...)

-- 법령
rd_safety_laws       (law_code PK, law_title_ko, article_number, law_ref_url)
rd_law_hazard_map    (id PK, law_code FK, hazard_code, applicability)
```

---

## 5. 엔진 연계 포인트 (Step 10 — 미구현, 정의만)

엔진은 현재 **BM25 텍스트 검색** 기반이다. 데이터 자산과의 연계는 아래 3가지 방식으로 계획한다.

### 5.1 쿼리 부스팅 (현재 v2에서 일부 구현됨)
- 입력의 `work_type`, `equipment` 필드 → `work_hazards_map` 조회 → 고위험 hazard 키워드를 `_build_query()`에 추가
- 현재: `confined_space`, `hot_work`, `electrical_work`, `work_at_height`, `heavy_equipment`, `night_work`, `simultaneous_work` 플래그 기반

### 5.2 사후 필터링 (미구현)
- `engine.query()` 결과의 각 청크를 `rd_work_hazards_map`에서 연관성 점수로 재순위(re-rank)
- 입력의 `trade_code` → `rd_work_types` → 관련 `work_type_code` 필터링

### 5.3 법령 메타데이터 주입 (미구현)
- 결과 청크의 `law_ref` 필드 → `rd_safety_laws` 조회 → 실제 법령 전문 링크 추가
- `rd_law_hazard_map` → 관련 hazard 교차 검증

### 5.4 실사례 매핑 (미구현)
- 입력의 `work_type_code` → `rd_real_cases` 조회 → 유사 사례 상위 3건 부록으로 첨부

---

## 6. 데이터 품질 원칙

| 원칙 | 내용 |
|------|------|
| 추적 가능 소스 | 모든 레코드에 `source` 필드 (sample_chunks id 또는 법령 조항) |
| 임의 생성 금지 | sample_chunks.json + 법령 + hazard_classifier.py 규칙만 허용 |
| 분리 보호 | rd_ 접두어 테이블 — 기존 KRAS 테이블과 완전 격리 |
| 증분 갱신 | KOSHA 지식DB 수집 확장 시 JSON → SQL 변환 파이프라인으로 추가 |

---

## 7. 다음 단계 (백로그)

| 우선순위 | 작업 | 기대 효과 |
|----------|------|-----------|
| P1 | sample_chunks → rd_real_cases 전체 이식 (현재 15건 → 목표 100건+) | 실사례 검색 커버리지 향상 |
| P1 | rd_work_hazards_map BM25 쿼리 자동 부스팅 구현 | work_type 기반 정밀도 향상 |
| P2 | KOSHA 스크랩 신규 청크 → hazard_controls 자동 추출 | 통제수단 DB 확장 |
| P2 | rd_safety_laws URL 실제 국가법령정보센터 링크 채워넣기 | 법령 참조 완결성 |
| P3 | rd_equipment_master ↔ 입력 equipment 필드 연동 | 장비 기반 위험 자동 추가 |

---

## 8. 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-20 | 초기 생성 — 12개 JSON 파일, 003_risk_data_schema.sql |

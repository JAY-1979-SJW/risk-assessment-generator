# Legal Source Registry 구축 보고서

**작성일**: 2026-04-26  
**검증 결과**: PASS (ERRORS: 0, WARNINGS: 0)

---

## 1. 총 source 수

| 구분 | 수량 | 비고 |
|------|------|------|
| registry 등록 source | 23 | 원래 22개 후보에서 시행령/규칙 분리로 23개 |
| collect queue 항목 | 19 | Q-001 ~ Q-019 |
| evidence 매핑 (registry 기준) | 85 | PRACTICAL 3개 + E-06 1개 미매핑 |

> 원래 22개 source 후보에서 "건설기계관리법 시행령/시행규칙"(1 → 2)와 "소방시설공사업법 시행령/시행규칙"(1 → 2)를 각각 DECREE·RULE로 분리하여 23개가 됨.

---

## 2. collection_status별 count

| 상태 | 건수 | source_code |
|------|------|-------------|
| COLLECTED_VERIFIED | 4 | MOEL_OSH_ACT, MOEL_OSH_ACT_ENFORCEMENT_RULE, MOEL_OSH_STANDARD_RULE, MOEL_RISK_ASSESSMENT_GUIDELINE_2023_19 |
| COLLECTED_PARTIAL | 1 | KOSHA_GUIDE (8개 수집, 5개 미수집) |
| REFERENCED_ONLY | 3 | MOLIT_CONSTRUCTION_TECH_PROMOTION_ACT, MOTIE_ELECTRIC_CONSTRUCTION_BUSINESS_ACT, MOTIE_ELECTRIC_EQUIPMENT_TECH_STANDARD |
| SCRIPT_EXISTS_NOT_COLLECTED | 6 | MOLIT_CONSTRUCTION_MACHINERY_MANAGEMENT_ACT/DECREE/RULE, NFA_FIRE_FACILITY_BUSINESS_ACT/DECREE/RULE |
| NOT_COLLECTED | 7 | MOEL_OSH_ACT_ENFORCEMENT_DECREE, MOLIT_CONSTRUCTION_TECH_PROMOTION_DECREE/RULE, MSIT_TELECOM_CONSTRUCTION_BUSINESS_ACT, KOSHA_SIF_CASES, KALIS_CSI_ACCIDENT_DATA, MOTIE_ELECTRIC_CONSTRUCTION_BUSINESS_ACT |
| UNKNOWN | 2 | UNKNOWN_CONSTRUCTION_SAFETY_COST_STANDARD, UNKNOWN_CONSTRUCTION_SAFETY_MANAGEMENT_GUIDELINE |

---

## 3. collection_action별 count

| action | 건수 |
|--------|------|
| SKIP_ALREADY_COLLECTED | 4 |
| COLLECT_BY_EXISTING_SCRIPT | 6 |
| COLLECT_BY_LAW_API | 6 |
| COLLECT_BY_NEW_CONNECTOR | 4 |
| NEEDS_OFFICIAL_NAME_CONFIRMATION | 2 |
| WATCH_ONLY | 2 |

---

## 4. priority별 count

| priority | 건수 | 내용 |
|----------|------|------|
| P0 | 5 | 핵심 법령 (위험성평가 필수) |
| P1 | 9 | 건설현장 준수 필수 |
| P2 | 7 | 특정 공종 필요 |
| P3 | 2 | 참고 데이터 |

---

## 5. 즉시 수집 가능 source (enabled: true)

### Group 1: 기존 스크립트 실행만으로 수집 (6건)

| queue_id | source_code | 스크립트 | MST |
|----------|-------------|----------|-----|
| Q-001 | MOLIT_CONSTRUCTION_MACHINERY_MANAGEMENT_ACT | law_statutes.py | 283763 |
| Q-002 | MOLIT_CONSTRUCTION_MACHINERY_MANAGEMENT_DECREE | law_statutes.py | 285023 |
| Q-003 | MOLIT_CONSTRUCTION_MACHINERY_MANAGEMENT_RULE | collect_missing_laws.py | TBD |
| Q-004 | NFA_FIRE_FACILITY_BUSINESS_ACT | collect_missing_laws.py | 259473 |
| Q-005 | NFA_FIRE_FACILITY_BUSINESS_DECREE | collect_missing_laws.py | 284779 |
| Q-006 | NFA_FIRE_FACILITY_BUSINESS_RULE | collect_missing_laws.py | 282735 |

### Group 2: law.go.kr API MST 조회 후 수집 (5건 enabled)

| queue_id | source_code | MST 상태 |
|----------|-------------|----------|
| Q-007 | MOEL_OSH_ACT_ENFORCEMENT_DECREE | MST 조회 필요 |
| Q-008 | MOLIT_CONSTRUCTION_TECH_PROMOTION_ACT | MST 조회 필요 |
| Q-011 | MOTIE_ELECTRIC_CONSTRUCTION_BUSINESS_ACT | 명칭 확인 필요 |
| Q-012 | MSIT_TELECOM_CONSTRUCTION_BUSINESS_ACT | MST 조회 필요 |
| Q-017 | KOSHA_GUIDE (잔여 5건) | kosha_guides.py |

---

## 6. 공식 명칭 확인 필요 source (2건)

| queue_id | source_code | 후보 명칭 |
|----------|-------------|----------|
| Q-013 | UNKNOWN_CONSTRUCTION_SAFETY_COST_STANDARD | 건설업 산업안전보건관리비 계상 및 사용기준 (고용부 또는 국토부) |
| Q-014 | UNKNOWN_CONSTRUCTION_SAFETY_MANAGEMENT_GUIDELINE | 건설공사 안전관리 업무수행 지침 (국토부 또는 공단) |

---

## 7. 중복 수집 금지 source (4건)

| source_code | 이유 | evidence 수 |
|-------------|------|-------------|
| MOEL_OSH_ACT | 완전 수집 완료 | 8 |
| MOEL_OSH_ACT_ENFORCEMENT_RULE | 완전 수집 완료 | 6 |
| MOEL_OSH_STANDARD_RULE | 완전 수집 완료 (가장 많음) | 62 |
| MOEL_RISK_ASSESSMENT_GUIDELINE_2023_19 | 완전 수집 완료 | 2 |

---

## 8. 다음 수집 순서 (권장)

```
PHASE 1 (즉시, 기존 스크립트):
  1. Q-001: python scripts/collect/law_statutes.py  (건설기계관리법, MST=283763)
  2. Q-004: python scripts/collect/collect_missing_laws.py  (소방시설공사업법, MST=259473)
  3. Q-002, Q-003, Q-005, Q-006: 연계 시행령/규칙 수집

PHASE 2 (MST 조회 후, law API):
  4. Q-007: 산업안전보건법 시행령 (P0, MST 조회 필요)
  5. Q-008: 건설기술진흥법 (MST 조회 필요)
  6. Q-011: 전기공사업법 (명칭 확인 선행)
  7. Q-012: 정보통신공사업법

PHASE 3 (명칭 확인 후):
  8. Q-013, Q-014: UNKNOWN 2건 공식 명칭 확정

PHASE 4 (커넥터 개발):
  9. Q-015: NFA_NFTC (소방청 NFTC)
  10. Q-016: MOTIE_ELECTRIC_EQUIPMENT_TECH_STANDARD
  11. Q-017: KOSHA_GUIDE 잔여 5건

PHASE 5 (선택, 참고용):
  12. Q-018, Q-019: KOSHA SIF, KALIS CSI (enabled: false, 필요시 활성화)
```

---

## 9. 생성 파일 목록

| 파일 | 용도 |
|------|------|
| `docs/design/legal_source_classification_schema.md` | 분류 스키마 정의 (source_type, domain, authority, status, action, priority) |
| `data/masters/safety/legal_sources_registry.yml` | 23개 source 전체 registry |
| `data/masters/safety/legal_evidence_registry.yml` | 85개 evidence → source_code 매핑 |
| `data/masters/safety/legal_collection_queue.yml` | 19개 수집 대기 큐 |
| `scripts/safety/validate_legal_source_registry.py` | registry 정합성 검증 스크립트 |
| `docs/reports/legal_source_registry_build_report.md` | 본 보고서 |

---

## 10. 검증 결과

```
python scripts/safety/validate_legal_source_registry.py
→ ERRORS: 0 / WARNINGS: 0 / [최종 결과] PASS
```

검증 항목:
- [OK] registry 파일 존재
- [OK] source_code 중복 없음 (23개)
- [OK] source 수 일치 (23개)
- [OK] collection_status enum 전체 정상
- [OK] collection_action enum 전체 정상
- [OK] COLLECTED_VERIFIED 4건 evidence_count > 0
- [OK] 중복 수집 금지 4건 SKIP_ALREADY_COLLECTED 설정
- [OK] UNKNOWN 2건 enabled=false + NEEDS_OFFICIAL_NAME_CONFIRMATION 설정
- [OK] queue에 SKIP_ALREADY_COLLECTED 항목 없음
- [OK] queue source_code 전체 registry에 존재
- [OK] queue_id 중복 없음 (19개)

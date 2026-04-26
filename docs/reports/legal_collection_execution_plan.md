# Legal Source 수집 실행 계획

**작성일**: 2026-04-26  
**기준**: legal_collection_queue.yml Q-001 ~ Q-019 (19건)  
**전제**: COLLECTED_VERIFIED 4건은 수집 제외 (SKIP_ALREADY_COLLECTED)

---

## 1. 그룹별 재분류 (19건 전수)

### A. SKIP_ALREADY_COLLECTED — 재수집 금지 (registry에만 존재, queue 미등록)

| source_code | 법령명 | evidence 수 |
|-------------|--------|-------------|
| MOEL_OSH_ACT | 산업안전보건법 | 8 |
| MOEL_OSH_ACT_ENFORCEMENT_RULE | 산업안전보건법 시행규칙 | 6 |
| MOEL_OSH_STANDARD_RULE | 산업안전보건기준에 관한 규칙 | 62 |
| MOEL_RISK_ASSESSMENT_GUIDELINE_2023_19 | 위험성평가 지침 (고용노동부고시 2023-19호) | 2 |

> 총 78개 evidence 확보됨. 이 4건은 collect queue에 등록되지 않는다.

---

### B. COLLECT_NOW_EXISTING_SCRIPT — 기존 스크립트 즉시 실행 가능 (6건)

| queue_id | source_code | 법령명 | 스크립트 | MST | 차단 |
|----------|-------------|--------|----------|-----|------|
| Q-001 | MOLIT_CONSTRUCTION_MACHINERY_MANAGEMENT_ACT | 건설기계관리법 | law_statutes.py | 283763 | 없음 |
| Q-002 | MOLIT_CONSTRUCTION_MACHINERY_MANAGEMENT_DECREE | 건설기계관리법 시행령 | law_statutes.py | 285023 | Q-001 후 |
| Q-003 | MOLIT_CONSTRUCTION_MACHINERY_MANAGEMENT_RULE | 건설기계관리법 시행규칙 | collect_missing_laws.py | TBD | Q-001 후 |
| Q-004 | NFA_FIRE_FACILITY_BUSINESS_ACT | 소방시설공사업법 | collect_missing_laws.py | 259473 | 없음 |
| Q-005 | NFA_FIRE_FACILITY_BUSINESS_DECREE | 소방시설공사업법 시행령 | collect_missing_laws.py | 284779 | Q-004 후 |
| Q-006 | NFA_FIRE_FACILITY_BUSINESS_RULE | 소방시설공사업법 시행규칙 | collect_missing_laws.py | 282735 | Q-004 후 |

**실행 명령 (예시)**:
```bash
# Q-001: 건설기계관리법 (MST 확인 완료)
python scripts/collect/law_statutes.py --mst 283763

# Q-004: 소방시설공사업법 (MST 확인 완료)  
python scripts/collect/collect_missing_laws.py --mst 259473
```

---

### C. COLLECT_NOW_LAW_API — MST 조회 후 law.go.kr API 수집 (8건)

| queue_id | source_code | 법령명 | authority | 고시번호 | MST | 우선순위 | 차단 |
|----------|-------------|--------|-----------|----------|-----|----------|------|
| Q-007 | MOEL_OSH_ACT_ENFORCEMENT_DECREE | 산업안전보건법 시행령 | MOEL | — | 미확인 | P0 | 없음 |
| Q-008 | MOLIT_CONSTRUCTION_TECH_PROMOTION_ACT | 건설기술진흥법 | MOLIT | — | 미확인 | P1 | 없음 |
| Q-011 | MOTIE_ELECTRIC_CONSTRUCTION_BUSINESS_ACT | 전기공사업법 | MOTIE | — | 미확인 | P1 | 없음 |
| Q-013 | MOEL_CONSTRUCTION_SAFETY_HEALTH_COST_STANDARD | 건설업 산업안전보건관리비 계상 및 사용기준 | MOEL | 제2025-11호 | 미확인 | P2 | 없음 |
| Q-012 | MSIT_TELECOM_CONSTRUCTION_BUSINESS_ACT | 정보통신공사업법 | MSIT | — | 미확인 | P2 | 없음 |
| Q-009 | MOLIT_CONSTRUCTION_TECH_PROMOTION_DECREE | 건설기술진흥법 시행령 | MOLIT | — | 미확인 | P2 | Q-008 후 |
| Q-010 | MOLIT_CONSTRUCTION_TECH_PROMOTION_RULE | 건설기술진흥법 시행규칙 | MOLIT | — | 미확인 | P2 | Q-008 후 |
| Q-014 | MOLIT_CONSTRUCTION_SAFETY_MANAGEMENT_GUIDELINE | 건설공사 안전관리 업무수행 지침 | MOLIT | 제2022-791호 | 미확인 | P3 | 없음 |

**MST 조회 방법**:
```bash
# law.go.kr DRF API로 MST 조회 (.env의 LAW_GO_KR_OC 사용)
GET /DRF/lawSearch.do?OC={OC}&target=law&query={법령명}&type=JSON
# 응답 lsInfoDt[0].lsiSeq 값이 MST
```

---

### D. CONFIRM_OFFICIAL_NAME_THEN_COLLECT — 명칭 확인 후 수집 (0건)

> Q-013/Q-014는 2026-04-26 발행처 확인 완료로 그룹 C로 이동됨.  
> Q-011은 전기공사업법 명칭 확인 완료(2026-04-26)로 그룹 C 유지.  
> **현재 이 그룹에 해당하는 항목 없음.**

---

### E. NEW_CONNECTOR_REQUIRED — 전용 커넥터 개발 필요 (3건)

| queue_id | source_code | 법령명 | 이유 | 우선순위 |
|----------|-------------|--------|------|----------|
| Q-015 | NFA_NFTC | 화재안전기술기준 (NFTC) | 소방청 NFTC 전용 사이트, law.go.kr 미수록 | P1 |
| Q-016 | MOTIE_ELECTRIC_EQUIPMENT_TECH_STANDARD | 전기설비기술기준 | 산업부 행정규칙, 별도 파서 필요 | P2 |
| Q-017 | KOSHA_GUIDE | KOSHA GUIDE 잔여 5건 | KOSHA 홈페이지 PDF, kosha_guides.py 활용 | P2 |

> Q-015/Q-016은 enabled=false (커넥터 개발 선행 필요).  
> Q-017은 enabled=true, kosha_guides.py 활용 가능.

---

### F. WATCH_ONLY — 수집 보류, 참고용 (2건)

| queue_id | source_code | 법령명 | 이유 |
|----------|-------------|--------|------|
| Q-018 | KOSHA_SIF_CASES | KOSHA SIF 사고사례 | 위험성평가표 생성 미필수, 스크립트 미존재 |
| Q-019 | KALIS_CSI_ACCIDENT_DATA | 국토안전관리원 CSI 사고자료 | 위험성평가표 생성 미필수, 스크립트 미존재 |

---

## 2. 즉시 수집 가능 대상 (Enabled=true, 차단 없음)

### 2-1. 단독 실행 가능 (차단 없음)

| queue_id | 법령명 | 실행 방법 | 예상 산출 경로 |
|----------|--------|-----------|----------------|
| Q-001 | 건설기계관리법 | `python scripts/collect/law_statutes.py --mst 283763` | data/evidence/safety_law_refs/건설기계관리법_*.json |
| Q-004 | 소방시설공사업법 | `python scripts/collect/collect_missing_laws.py --mst 259473` | data/evidence/safety_law_refs/소방시설공사업법_*.json |
| Q-007 | 산업안전보건법 시행령 | MST 조회 후 law_statutes.py | data/evidence/safety_law_refs/산업안전보건법시행령_*.json |
| Q-008 | 건설기술진흥법 | MST 조회 후 law_statutes.py | data/evidence/safety_law_refs/건설기술진흥법_*.json |
| Q-011 | 전기공사업법 | MST 조회 후 law_statutes.py | data/evidence/safety_law_refs/전기공사업법_*.json |
| Q-013 | 건설업 산안관리비 계상 및 사용기준 | MST 조회 후 law_statutes.py | data/evidence/safety_law_refs/산안관리비_*.json |
| Q-012 | 정보통신공사업법 | MST 조회 후 law_statutes.py | data/evidence/safety_law_refs/정보통신공사업법_*.json |
| Q-017 | KOSHA GUIDE 잔여 5건 | `python scripts/collect/kosha_guides.py` | data/evidence/safety_law_refs/KOSHA_GUIDE_*.json |

### 2-2. 상위 수집 완료 후 실행 (차단 있음)

| queue_id | 법령명 | 차단 조건 |
|----------|--------|-----------|
| Q-002 | 건설기계관리법 시행령 | Q-001 완료 후 |
| Q-003 | 건설기계관리법 시행규칙 | Q-001 완료 후 |
| Q-005 | 소방시설공사업법 시행령 | Q-004 완료 후 |
| Q-006 | 소방시설공사업법 시행규칙 | Q-004 완료 후 |
| Q-009 | 건설기술진흥법 시행령 | Q-008 완료 후 (enabled=false, 활성화 필요) |
| Q-010 | 건설기술진흥법 시행규칙 | Q-008 완료 후 (enabled=false, 활성화 필요) |
| Q-014 | 건설공사 안전관리 업무수행 지침 | 없음 (MST 조회만 선행 필요) |

---

## 3. 보류 대상 요약

| queue_id | 사유 | 해제 조건 |
|----------|------|-----------|
| Q-009 | enabled=false | Q-008 완료 후 enabled=true 변경 |
| Q-010 | enabled=false | Q-008 완료 후 enabled=true 변경 |
| Q-015 | NFTC 커넥터 미개발 | nfsc.go.kr 파서 개발 완료 후 |
| Q-016 | 전기설비기술기준 커넥터 미개발 | 산업부 고시 파서 또는 law.go.kr 행정규칙 경로 확인 후 |
| Q-018 | WATCH_ONLY | 필요 시 스크립트 개발 후 재검토 |
| Q-019 | WATCH_ONLY | 필요 시 스크립트 개발 후 재검토 |

---

## 4. 수집 실행 순서 (권장)

```
PHASE 1 — 즉시 실행 가능 (기존 스크립트, MST 확보)
  Step 1: Q-001  건설기계관리법 (law_statutes.py, MST=283763)
  Step 2: Q-004  소방시설공사업법 (collect_missing_laws.py, MST=259473)
  Step 3: Q-002  건설기계관리법 시행령 (MST=285023, Q-001 완료 후)
  Step 4: Q-003  건설기계관리법 시행규칙 (MST 조회 필요, Q-001 완료 후)
  Step 5: Q-005  소방시설공사업법 시행령 (MST=284779, Q-004 완료 후)
  Step 6: Q-006  소방시설공사업법 시행규칙 (MST=282735, Q-004 완료 후)

PHASE 2 — MST 조회 후 실행 (P0/P1 우선)
  Step 7: Q-007  산업안전보건법 시행령 (P0, MST 조회 필요)
  Step 8: Q-008  건설기술진흥법 (P1, MST 조회 필요)
  Step 9: Q-011  전기공사업법 (P1, MST 조회 필요)
  Step 10: Q-013 건설업 산안관리비 계상 및 사용기준 (P2)
  Step 11: Q-012 정보통신공사업법 (P2)
  Step 12: Q-014 건설공사 안전관리 업무수행 지침 (P3)
  (Q-009, Q-010: Q-008 완료 후 enabled=true 변경 후 실행)

PHASE 3 — 커넥터/스크립트 개발 후 실행
  Step 13: Q-017 KOSHA GUIDE 잔여 5건 (kosha_guides.py, duplicate 체크 필수)
  Step 14: Q-015 NFA_NFTC (커넥터 개발 후)
  Step 15: Q-016 전기설비기술기준 (커넥터 개발 후)

PHASE 4 — 선택 수집 (참고용, 현재 보류)
  Q-018: KOSHA SIF 사고사례
  Q-019: KALIS CSI 사고자료
```

---

## 5. 수집 후 필수 처리

각 source 수집 완료 후 아래 작업을 수행한다:

1. **legal_sources_registry.yml 갱신**
   - `collection_status` → `COLLECTED_VERIFIED` 또는 `COLLECTED_PARTIAL`
   - `collected_evidence_count` → 실제 evidence 수
   - `effective_date` → 수집된 법령의 시행일

2. **legal_evidence_registry.yml 확장**
   - 신규 evidence를 해당 `source_code`에 매핑

3. **legal_collection_queue.yml 갱신**
   - `enabled: false` (수집 완료 표시)
   - `notes`에 완료 날짜 기재

4. **검증 실행**
   ```bash
   python scripts/safety/validate_legal_source_registry.py
   python scripts/lint_safety_naming.py
   python scripts/smoke_test_p1_forms.py
   ```

5. **commit / push / 서버 동기화**

---

## 6. 중복 수집 방지 체크리스트

수집 실행 전 반드시 확인:

- [ ] `duplicate_collection_risk: true` 항목이 queue에 없는지 확인
- [ ] KOSHA GUIDE(Q-017): evidence_id `PTW-002-K*`, `PTW-003-K*`, `PTW-007-K*` 재수집 금지
- [ ] 산업안전보건기준에 관한 규칙: 62개 evidence ID 중복 확인
- [ ] validate_legal_source_registry.py PASS 확인 후 수집 시작

---

**작성 완료**: 2026-04-26  
**다음 단계**: PHASE 1 (Q-001, Q-004) 실행 승인 후 진행

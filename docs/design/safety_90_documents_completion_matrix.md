# 안전서류 90종 구현 완료 매트릭스

> 기준일: 2026-04-25  
> 감사 스크립트: `scripts/audit_safety_90_completion.py`  
> 총 93종 (OUT 3종 제외 실효 90종)

---

## 1. 전체 현황 요약

| 구분 | 건수 | 비율 |
|------|-----:|-----:|
| ✅ READY (완전 구현) | 16 | 17.8% |
| ⚠️ TEST_MISSING (evidence 있으나 smoke test 없음) | 2 | 2.2% |
| ⚠️ EVIDENCE_MISSING (DONE builder 있으나 evidence 없음) | 15 | 16.7% |
| 🔲 TODO (미착수) | 57 | 63.3% |
| ➖ OUT (범위 외) | 3 | — |
| **합계 (실효)** | **90** | |

**READY 비율: 17.8% (16/90)**

---

## 2. final_readiness 판정 기준

| 상태 | 정의 |
|------|------|
| **READY** | catalog DONE + form_registry 등록 + evidence 파일 존재 + smoke_test 포함 |
| **TEST_MISSING** | catalog DONE + builder + evidence 있으나 smoke_test 미포함 |
| **EVIDENCE_MISSING** | catalog DONE + builder 등록됨 + evidence 파일 없음 |
| **BUILDER_ONLY** | builder 등록됨 + catalog NOT DONE (현재 0건) |
| **TODO** | catalog TODO, builder 없음 |
| **OUT** | 범위 외 제외 (TS-001~003: 유해위험방지계획서·PSM) |

---

## 3. 카테고리별 현황

| 카테고리 | 총계 | READY | TEST_MISS | EV_MISS | TODO | OUT |
|---------|-----:|------:|----------:|--------:|-----:|----:|
| WP (작업계획서) | 15 | 3 | 0 | 6 | 6 | 0 |
| EQ (장비특화 계획서) | 16 | 0 | 0 | 4 | 12 | 0 |
| RA (위험성평가) | 6 | 0 | 0 | 2 | 4 | 0 |
| ED (교육) | 5 | 2 | 0 | 1 | 2 | 0 |
| PTW (작업허가서) | 8 | 4 | 0 | 1 | 3 | 0 |
| DL (일지) | 5 | 0 | 0 | 0 | 5 | 0 |
| CL (점검표) | 10 | 7 | 0 | 1 | 2 | 0 |
| PPE (보호구·장비) | 4 | 0 | 0 | 0 | 4 | 0 |
| CM (관리·행정) | 7 | 0 | 0 | 0 | 7 | 0 |
| EM (비상·사고) | 6 | 0 | 0 | 0 | 6 | 0 |
| TS (특수·PSM) | 5 | 0 | 0 | 0 | 2 | 3 |
| SP (안전문화) | 4 | 0 | 0 | 0 | 4 | 0 |
| HM (건강관리) | 2 | 0 | 2 | 0 | 0 | 0 |
| **합계** | **93** | **16** | **2** | **15** | **57** | **3** |

---

## 4. 핵심 패키지 READY 현황

| 패키지 | 상태 | required | conditional | advisory |
|--------|------|---------|-------------|---------|
| 고소작업 (work_at_height) | ✅ READY | RA-001, RA-004, PTW-003 | CL-007, CL-001 | PPE-001 |
| 중량물 인양 (heavy_lifting) | ✅ READY | RA-001, RA-004, WP-005, PTW-007 | CL-003 | PPE-001 |
| 차량계 건설기계 (vehicle_construction) | ✅ READY | RA-001, RA-004, WP-008 | CL-003, EQ-002 | PPE-001 |
| 차량계 하역운반 (material_handling) | ✅ READY | RA-001, RA-004, WP-009 | CL-003, EQ-001 | PPE-001 |
| 화기작업 (hot_work) | ✅ READY | RA-001, RA-004, PTW-002 | CL-005 | PPE-001 |
| 전기작업 (electrical_work) | ✅ READY | RA-001, RA-004, WP-011 | PTW-004, CL-004 | PPE-001 |
| 밀폐공간 (confined_space) | ✅ READY | RA-001, RA-004, WP-014, PTW-001 | CL-010 | PPE-001 |

> PPE-001, PPE-004, EQ-014는 advisory/missing_builders로 분류. 패키지 READY 판정에 영향 없음.

---

## 5. 전체 문서 완료 매트릭스

범례: ✓ = 있음/완료  ✗ = 없음/미완료  - = 해당없음  
EV: VERF=VERIFIED, PART=PARTIAL_VERIFIED, NEED=NEEDS_VERIFICATION, -= NONE

| ID | 서식명 | CAT | Done | Builder | EV | EV상태 | Test | Rec | 최종판정 |
|-----|--------|-----|:----:|:-------:|:--:|:------:|:----:|:---:|---------|
| WP-001 | 굴착 작업계획서 | WP | ✓ | ✓ | ✗ | - | ✗ | ✓ | **EVIDENCE_MISSING** |
| WP-002 | 터널 굴착 작업계획서 | WP | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| WP-003 | 건축물 해체 작업계획서 | WP | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| WP-004 | 교량 설치·해체·변경 작업계획서 | WP | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| **WP-005** | **중량물 취급 작업계획서** | WP | ✓ | ✓ | ✓ | VERF | ✓ | ✓ | ✅ **READY** |
| WP-006 | 타워크레인 작업계획서 | WP | ✓ | ✓ | ✗ | - | ✗ | ✗ | **EVIDENCE_MISSING** |
| WP-007 | 이동식 크레인 작업계획서 | WP | ✓ | ✓ | ✗ | - | ✗ | ✓ | **EVIDENCE_MISSING** |
| WP-008 | 차량계 건설기계 작업계획서 | WP | ✓ | ✓ | ✗ | - | ✗ | ✓ | **EVIDENCE_MISSING** |
| WP-009 | 차량계 하역운반기계 작업계획서 | WP | ✓ | ✓ | ✗ | - | ✗ | ✓ | **EVIDENCE_MISSING** |
| WP-010 | 항타기·항발기 사용 작업계획서 | WP | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| **WP-011** | **전기 작업계획서** | WP | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| WP-012 | 궤도 작업계획서 | WP | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| WP-013 | 화학설비·부속설비 작업계획서 | WP | ✗ | ✗ | ✗ | - | ✗ | ✓ | TODO |
| WP-014 | 밀폐공간 작업계획서 | WP | ✓ | ✓ | ✗ | - | ✗ | ✓ | **EVIDENCE_MISSING** |
| **WP-015** | **거푸집·동바리 작업계획서** | WP | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| EQ-001 | 차량계 하역운반기계 계획서 (장비특화) | EQ | ✓ | ✓ | ✗ | - | ✗ | ✓ | **EVIDENCE_MISSING** |
| EQ-002 | 차량계 건설기계 계획서 (장비특화) | EQ | ✓ | ✓ | ✗ | - | ✗ | ✓ | **EVIDENCE_MISSING** |
| EQ-003 | 타워크레인 계획서 (장비특화) | EQ | ✓ | ✓ | ✗ | - | ✗ | ✗ | **EVIDENCE_MISSING** |
| EQ-004 | 이동식 크레인 계획서 (장비특화) | EQ | ✓ | ✓ | ✗ | - | ✗ | ✓ | **EVIDENCE_MISSING** |
| EQ-005 | 고소작업대 사용계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EQ-006 | 펌프카 작업계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EQ-007 | 굴착기·로더 사용계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✓ | TODO |
| EQ-008 | 덤프·롤러·불도저 사용계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EQ-009 | 항타기·항발기·천공기 사용계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EQ-010 | 리프트·곤돌라 사용계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EQ-011 | 양중기·호이스트·윈치 작업계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EQ-012 | 중량물 취급 계획서 (장비특화) | EQ | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EQ-013 | 임시전기·발전기 사용계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✓ | TODO |
| EQ-014 | 용접·용단·화기작업 계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✓ | TODO (advisory) |
| EQ-015 | 콤프레샤·공압장비 사용계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EQ-016 | 사다리·말비계·작업발판 사용계획서 | EQ | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| RA-001 | 위험성평가표 | RA | ✓ | ✓ | ✗ | - | ✓ | ✓ | **EVIDENCE_MISSING** |
| RA-002 | 위험성평가 관리 등록부 | RA | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| RA-003 | 위험성평가 참여 회의록 | RA | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| RA-004 | TBM 안전점검 일지 | RA | ✓ | ✓ | ✗ | - | ✓ | ✓ | **EVIDENCE_MISSING** |
| RA-005 | 위험성평가 실시 규정 | RA | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| RA-006 | 위험성평가 결과 근로자 공지문 | RA | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| ED-001 | 안전보건교육 교육일지 | ED | ✓ | ✓ | ✗ | - | ✗ | ✗ | **EVIDENCE_MISSING** |
| ED-002 | 연간 안전보건교육 계획서 | ED | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| **ED-003** | **특별 안전보건교육 교육일지** | ED | ✓ | ✓ | ✓ | VERF | ✓ | ✓ | ✅ **READY** |
| **ED-004** | **안전보건관리자 직무교육 이수 확인서** | ED | ✓ | ✓ | ✓ | PART | ✓ | ✗ | ✅ **READY** |
| ED-005 | 안전보건협의체 회의록 | ED | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| PTW-001 | 밀폐공간 작업 허가서 | PTW | ✓ | ✓ | ✗ | - | ✓ | ✓ | **EVIDENCE_MISSING** |
| **PTW-002** | **화기작업 허가서** | PTW | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| **PTW-003** | **고소작업 허가서** | PTW | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| **PTW-004** | **전기작업 허가서** | PTW | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| PTW-005 | 굴착 작업 허가서 | PTW | ✗ | ✗ | ✗ | - | ✗ | ✓ | TODO |
| PTW-006 | 방사선 투과검사 작업 허가서 | PTW | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| **PTW-007** | **중량물 인양·중장비사용 작업 허가서** | PTW | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| PTW-008 | 임시전기 설치·연결 허가서 | PTW | ✗ | ✗ | ✗ | - | ✗ | ✓ | TODO |
| DL-001 | 안전관리 일지 | DL | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| DL-002 | 관리감독자 안전보건 업무 일지 | DL | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| DL-003 | 안전순찰 점검 일지 | DL | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| DL-004 | 기상 조건 기록 일지 | DL | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| DL-005 | 작업 전 안전 확인서 | DL | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| **CL-001** | **비계·동바리 설치 점검표** | CL | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| **CL-002** | **거푸집 및 동바리 설치 점검표** | CL | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| **CL-003** | **건설장비 일일 사전점검표** | CL | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| **CL-004** | **전기설비 정기 점검표** | CL | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| **CL-005** | **화재 예방 점검표** | CL | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| **CL-006** | **타워크레인 자체 점검표** | CL | ✓ | ✓ | ✓ | PART | ✓ | ✗ | ✅ **READY** |
| **CL-007** | **추락 방호 설비 점검표** | CL | ✓ | ✓ | ✓ | PART | ✓ | ✓ | ✅ **READY** |
| CL-008 | 보호구 지급 및 관리 점검표 | CL | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| CL-009 | 유해화학물질 취급 점검표 | CL | ✗ | ✗ | ✗ | - | ✗ | ✓ | TODO |
| CL-010 | 밀폐공간 사전 안전 점검표 | CL | ✓ | ✓ | ✗ | - | ✗ | ✓ | **EVIDENCE_MISSING** |
| PPE-001 | 보호구 지급 대장 | PPE | ✗ | ✗ | ✗ | - | ✗ | ✓ | TODO (advisory) |
| PPE-002 | 건설 장비 반입 신청서 | PPE | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| PPE-003 | 건설 장비 보험·정기검사증 확인서 | PPE | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| PPE-004 | MSDS 비치 및 교육 확인서 | PPE | ✗ | ✗ | ✗ | - | ✗ | ✓ | TODO (advisory) |
| CM-001 | 협력업체 안전보건 관련 서류 확인서 | CM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| CM-002 | 도급·용역 안전보건 협의서 | CM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| CM-003 | 근로자 건강진단 결과 확인서 | CM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| CM-004 | 안전보건관리자 선임 신고서 | CM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| CM-005 | 신규 근로자 안전보건 서약서 | CM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| CM-006 | 외국인 근로자 안전보건 교육 확인서 | CM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| CM-007 | 산업재해 발생 현황 관리 대장 | CM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EM-001 | 산업재해조사표 | EM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EM-002 | 아차사고 보고서 | EM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EM-003 | 비상 연락망 및 대피 계획서 | EM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EM-004 | 중대재해 발생 즉시 보고서 | EM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EM-005 | 재해 원인 분석 및 재발 방지 보고서 | EM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| EM-006 | 응급조치 실시 기록서 | EM | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| TS-001 | 유해위험방지계획서 (건설업) | TS | ✗ | ✗ | ✗ | - | ✗ | ✗ | OUT |
| TS-002 | 유해위험방지계획서 (제조업) | TS | ✗ | ✗ | ✗ | - | ✗ | ✗ | OUT |
| TS-003 | 공정안전보고서 (PSM) | TS | ✗ | ✗ | ✗ | - | ✗ | ✗ | OUT |
| TS-004 | 산업안전보건관리비 사용계획서 | TS | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| TS-005 | 석면 해체·제거 작업 계획서 | TS | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| SP-001 | 안전보건 방침 및 목표 게시문 | SP | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| SP-002 | 협력업체 안전보건 수준 평가표 | SP | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| SP-003 | 위험성평가 우수 사례 보고서 | SP | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| SP-004 | 안전문화 활동 기록부 | SP | ✗ | ✗ | ✗ | - | ✗ | ✗ | TODO |
| ⚠️ HM-001 | 작업환경측정 실시 및 결과 관리대장 | HM | ✓ | ✓ | ✓ | VERF | ✗ | ✗ | **TEST_MISSING** |
| ⚠️ HM-002 | 특수건강진단 대상자 및 결과 관리대장 | HM | ✓ | ✓ | ✓ | VERF | ✗ | ✗ | **TEST_MISSING** |

---

## 6. builder 파일 ↔ catalog 매핑 (29종 form_type)

| form_type | 카탈로그 문서 |
|-----------|-------------|
| risk_assessment | RA-001 |
| tbm_log | RA-004 |
| education_log | ED-001 |
| special_education_log | ED-003 |
| manager_job_training_record | ED-004 |
| confined_space_permit | PTW-001 |
| hot_work_permit | PTW-002 |
| work_at_height_permit | PTW-003 |
| electrical_work_permit | PTW-004 |
| lifting_work_permit | PTW-007 |
| scaffold_installation_checklist | CL-001 |
| formwork_shoring_installation_checklist | CL-002 |
| construction_equipment_daily_checklist | CL-003 |
| electrical_facility_checklist | CL-004 |
| fire_prevention_checklist | CL-005 |
| tower_crane_self_inspection_checklist | CL-006 |
| fall_protection_checklist | CL-007 |
| confined_space_checklist | CL-010 |
| excavation_workplan | WP-001 |
| heavy_lifting_workplan | WP-005 / EQ-012 |
| tower_crane_workplan | WP-006 / EQ-003 |
| mobile_crane_workplan | WP-007 / EQ-004 |
| vehicle_construction_workplan | WP-008 / EQ-002 |
| material_handling_workplan | WP-009 / EQ-001 |
| electrical_workplan | WP-011 |
| confined_space_workplan | WP-014 |
| formwork_shoring_workplan | WP-015 |
| work_environment_measurement | HM-001 |
| special_health_examination | HM-002 |

---

*생성: 2026-04-25 / 다음 감사: `python scripts/audit_safety_90_completion.py`*

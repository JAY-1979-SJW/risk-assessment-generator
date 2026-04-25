# Safety Platform 안전관리 갭 매트릭스

**버전**: 3.3  
**작성일**: 2026-04-24 / 갱신: 2026-04-25 (EQ-003/EQ-004 builder DONE 처리)  
**생성 기준**: scripts/audit_safety_gap.py 실행 결과 + scripts/verify_safety_law_refs.py 법령 검증 + 수동 상세 필드 보강  
**기준 마스터**: document_catalog v2.1 (92종) / training_types v1.1 (10종) / worker_licenses v1.0 (7종) / inspection_types v1.0 (8종) / work_types v1.0 (7종) / compliance_clauses v1.0 (28건)  
**목적**: 12개 안전관리 축별 전수 감사 — 연결 ID 및 엔진 커버리지 포함  
**주의**: 감사 결과 기록 전용. 마스터 수정은 별도 단계에서 진행.

---

## 전체 집계 요약

| 상태 | 건수 | 비율 |
|---|---|---|
| COVERED | 20 | 18% |
| PARTIAL | 60 | 55% |
| MISSING | 27 | 25% |
| NEEDS_VERIFICATION | 3 | 3% |
| **합계** | **110** | |

> v3.1→3.2: audit_safety_gap.py 실행값 기준 갱신. C-06/E-06 COVERED 승격, G-02/G-03 PARTIAL 유지(evidence VERIFIED, builder 미구현).

> v3.2→3.3: EQ-003(타워크레인 장비특화)/EQ-004(이동식크레인 장비특화) implementation_status DONE 처리. WP-006/WP-007 builder 재사용. audit 수치 변동 없음(COVERED 20 / PARTIAL 60 / MISSING 27 / NV 3). P0 잔여 2건(G-02/G-03) 유지. HM-001/HM-002 form_builder 및 E-06 자격/면허 5종 PARTIAL_VERIFIED는 후속 단계.

> NEEDS_VERIFICATION: 마스터에 등록됐으나 적용 범위·법령 근거가 불명확한 항목

---

## 컬럼 정의

| 컬럼 | 설명 |
|---|---|
| no | 감사 번호 (축코드-순번) |
| audit_axis | 감사 축 (A~L) |
| item_name | 감사 항목명 |
| current_status | COVERED / PARTIAL / MISSING / NEEDS_VERIFICATION |
| missing_type | 누락 유형 (복수 가능, 쉼표 구분) |
| related_document_id | document_catalog doc_id (없으면 NOT_DEFINED) |
| related_training_id | training_types training_code (없으면 NOT_DEFINED) |
| related_inspection_id | inspection_types inspection_code (없으면 NOT_DEFINED) |
| related_equipment_id | equipment_types code (없으면 NOT_DEFINED) |
| related_work_type_code | work_types code (없으면 NOT_DEFINED) |
| related_compliance_id | compliance_clauses id (근거 불확실이면 NEEDS_VERIFICATION) |
| engine_coverage | YES / NO / PARTIAL / NOT_APPLICABLE |
| required_action | 필요 조치 (한 줄) |
| priority | P0 / P1 / P2 / P3 |
| evidence_status | VERIFIED / NEEDS_VERIFICATION / PRACTICAL / OUT_OF_SCOPE |
| notes | 비고 |

---

## A축 — 법정 작업계획서

> 기준: 산업안전보건기준에 관한 규칙 제38조 제1항 각호

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-01 | A | 굴착 작업계획서 | COVERED | NONE | WP-001 | EDU_SPECIAL_16H | INSP_DAILY_PRE_WORK | EQ_EXCAV | WT_EXCAVATION | CC-006,CC-007 | YES | — | — | VERIFIED | builder DONE. 규칙 제38조 제1항 제6호 |
| A-02 | A | 타워크레인 작업계획서 | COVERED | NONE | WP-006 | EDU_SPECIAL_16H | INSP_DAILY_PRE_WORK,INSP_MONTHLY | EQ_CRANE_TOWER | WT_CRANE_LIFTING | CC-006,CC-009 | YES | — | — | VERIFIED | builder DONE. 규칙 제38조 제1항 제1호 |
| A-03 | A | 이동식 크레인 작업계획서 | COVERED | NONE | WP-007 | EDU_SPECIAL_16H | INSP_DAILY_PRE_WORK | EQ_CRANE_MOB | WT_CRANE_LIFTING | CC-008 | PARTIAL | — | — | VERIFIED | builder DONE. 제38조 제1항 제14호 |
| A-04 | A | 차량계 건설기계 작업계획서 | COVERED | NONE | WP-008 | EDU_SPECIAL_16H | INSP_DAILY_PRE_WORK | EQ_EXCAV,EQ_BULLDOZER | NOT_DEFINED | CC-010 | YES | — | — | VERIFIED | builder DONE. 제38조 제1항 제3호 |
| A-05 | A | 차량계 하역운반기계 작업계획서 | COVERED | NONE | WP-009 | EDU_SPECIAL_16H | INSP_DAILY_PRE_WORK | EQ_FORKLIFT | WT_MATERIAL_HANDLING | CC-011 | YES | — | — | VERIFIED | builder DONE. 제38조 제1항 제2호 |
| A-06 | A | 밀폐공간 작업계획서 | COVERED | NONE | WP-014 | EDU_CONFINED_SPACE | INSP_CONFINED_SPACE_GAS | EQ_MANHOLE_BLOWER | WT_CONFINED_SPACE | CC-015 | YES | — | — | VERIFIED | builder DONE. 제619조~제626조 |
| A-07 | A | 터널 굴착 작업계획서 | PARTIAL | FORM_BUILDER_MISSING | WP-002 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P1 | VERIFIED | 제38조 제1항 제7호. 터널공사 현장 한정 |
| A-08 | A | 건축물 해체 작업계획서 | PARTIAL | FORM_BUILDER_MISSING | WP-003 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P1 | VERIFIED | 제38조 제1항 제9호. 해체공사 한정 |
| A-09 | A | 중량물 취급 작업계획서 | PARTIAL | FORM_BUILDER_MISSING,MAPPING_MISSING | WP-005 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | WT_HEAVY_LOAD | NEEDS_VERIFICATION | PARTIAL | builder 구현. 적용 조건 법령 확인 | P1 | NEEDS_VERIFICATION | 제38조 제1항 제10호. 100kg이상 추정 |
| A-10 | A | 항타기·항발기 작업계획서 | PARTIAL | FORM_BUILDER_MISSING | WP-010 | NOT_DEFINED | INSP_WEEKLY | EQ_PILEDRIVER | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P1 | VERIFIED | 제38조 제1항 제12호 |
| A-11 | A | 전기 작업계획서 | PARTIAL | FORM_BUILDER_MISSING,COMPLIANCE_MISSING | WP-011 | NOT_DEFINED | INSP_INSULATION_MONTHLY | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 제38조 해당 여부 법령 확인 후 builder | P1 | NEEDS_VERIFICATION | 제38조 적용 여부 미확인 |
| A-12 | A | 화학설비 작업계획서 | PARTIAL | FORM_BUILDER_MISSING | WP-013 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | CC-012 | NO | builder 구현 | P2 | VERIFIED | 제38조 제1항 제4호 |
| A-13 | A | 교량 작업계획서 | PARTIAL | FORM_BUILDER_MISSING | WP-004 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | VERIFIED | 제38조 제1항 제8호 |
| A-14 | A | 궤도 작업계획서 | PARTIAL | FORM_BUILDER_MISSING | WP-012 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | VERIFIED | 제38조 제1항 제11호. 철도현장 한정 |
| A-15 | A | 거푸집·동바리 작업계획서 | MISSING | DOCUMENT_MISSING,FORM_BUILDER_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 법령 원문 확인 후 document_catalog 등록 | P1 | NEEDS_VERIFICATION | 제38조 제13호 추정. WP-015 후보 |

---

## B축 — 위험성평가

> 기준: 산업안전보건법 제36조, 시행규칙 제37조, 고용노동부고시 제2023-19호

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B-01 | B | 위험성평가표 | COVERED | NONE | RA-001 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-001,CC-017,CC-019 | YES | — | — | VERIFIED | builder DONE |
| B-02 | B | TBM 안전점검 일지 | COVERED | NONE | RA-004 | EDU_TBM | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-024 | YES | — | — | PRACTICAL | builder DONE |
| B-03 | B | 위험성평가 관리 등록부 (3년 보존) | PARTIAL | FORM_BUILDER_MISSING | RA-002 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-017 | NO | builder 구현 | P1 | VERIFIED | 기록 보존 의무 |
| B-04 | B | 위험성평가 참여 회의록 | PARTIAL | FORM_BUILDER_MISSING | RA-003 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-001 | NO | builder 구현 | P2 | VERIFIED | 근로자 참여 증빙 |
| B-05 | B | 위험성평가 결과 근로자 공지문 | PARTIAL | FORM_BUILDER_MISSING | RA-006 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | PRACTICAL | 게시용 |
| B-06 | B | 위험성평가 실시 규정 | PARTIAL | FORM_BUILDER_MISSING | RA-005 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-019 | NO | builder 구현 | P3 | PRACTICAL | 고시 제2023-19호 권고 |
| B-07 | B | 위험성평가 유형 구분 (최초/수시/정기) | PARTIAL | MAPPING_MISSING | RA-001 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-001,CC-019 | PARTIAL | RA 분류 필드 추가 검토 | P1 | NEEDS_VERIFICATION | 고시에서 유형 구분 명시 |
| B-08 | B | 잔여위험 관리 기록 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 등록 여부 법령 검토 | P2 | NEEDS_VERIFICATION | 감소 후 잔류 위험 관리 |

---

## C축 — 근로자 교육

> 기준: 산업안전보건법 제29조~제31조, 시행규칙 별표4~5

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C-01 | C | 안전보건교육 일지 | COVERED | NONE | ED-001 | EDU_REG_WORKER_HALFYEAR | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002,CC-018 | YES | — | — | VERIFIED | builder DONE |
| C-02 | C | 근로자 정기안전보건교육 (매반기) | COVERED | NONE | ED-001 | EDU_REG_WORKER_HALFYEAR | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | YES | — | — | VERIFIED | 매반기 6h |
| C-03 | C | 채용 시 안전보건교육 | COVERED | NONE | ED-001 | EDU_ONBOARD_WORKER | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | YES | — | — | VERIFIED | 채용 시 8h |
| C-04 | C | 작업변경 시 안전보건교육 | COVERED | NONE | ED-001 | EDU_TASK_CHANGE | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | YES | — | — | VERIFIED | 변경 시 2h |
| C-05 | C | 특별안전보건교육 (16h) | COVERED | NONE | ED-003 | EDU_SPECIAL_16H | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | YES | — | — | VERIFIED | 별표5 대상 작업 |
| C-06 | C | 건설업 기초안전보건교육 | **COVERED** | NONE | ED-001 | EDU_CONSTRUCTION_BASIC | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | NO | — | — | **VERIFIED** | EDU_CONSTRUCTION_BASIC 등록 + 산안법 제31조 원문 확인(2026-04-24). 교육이수확인서 서식 연계 P1. |
| C-07 | C | 특별안전보건교육 일지 (ED-003) | PARTIAL | FORM_BUILDER_MISSING | ED-003 | EDU_SPECIAL_16H | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | PARTIAL | builder 구현 (ED-001과 분리) | P1 | VERIFIED | 별표5 39종 작업 기록 |
| C-08 | C | 일용근로자 교육 (별도 유형) | PARTIAL | TRAINING_MISSING | ED-001 | EDU_ONBOARD_WORKER | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | PARTIAL | training_types 별도 유형 등록 검토 | P1 | VERIFIED | 채용교육 내 1h 구분 필요 추정 |
| C-09 | C | 외국인 근로자 안전교육 | PARTIAL | TRAINING_MISSING | CM-006 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | NO | training_types 등록 | P2 | PRACTICAL | 다국어 교육 필요 |
| C-10 | C | 특별교육 별표5 work_type 전수 매핑 | PARTIAL | MAPPING_MISSING | NOT_DEFINED | EDU_SPECIAL_16H | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | PARTIAL | 별표5 39종 work_training_requirements 완성 | P1 | NEEDS_VERIFICATION | 현재 5/7종만 매핑 |

---

## D축 — 관리자/직무교육

> 기준: 산업안전보건법 제15조~제19조, 제32조

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D-01 | D | 관리감독자 정기교육 (매분기) | COVERED | NONE | ED-001 | EDU_REG_MANAGER_QUARTERLY | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | YES | — | — | VERIFIED | 매분기 8h |
| D-02 | D | 안전관리자 직무교육 | MISSING | TRAINING_MISSING | ED-004 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 산안법 제17조 확인 후 training_types 등록 | P1 | NEEDS_VERIFICATION | 신규 선임 시 + 능력향상교육 |
| D-03 | D | 보건관리자 직무교육 | MISSING | TRAINING_MISSING | ED-004 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 산안법 제18조 확인 후 training_types 등록 | P1 | NEEDS_VERIFICATION | 신규 선임 시 + 능력향상교육 |
| D-04 | D | 안전보건관리책임자 교육 | MISSING | TRAINING_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 산안법 제15조 확인 후 training_types 등록 | P1 | NEEDS_VERIFICATION | 선임 후 교육 의무 추정 |
| D-05 | D | 안전보건관리자 직무교육 이수 확인서 | PARTIAL | FORM_BUILDER_MISSING | ED-004 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | VERIFIED | 이수 증빙 서류 |
| D-06 | D | 안전보건관리담당자 교육 | MISSING | TRAINING_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 적용 조건 확인 후 등록 | P2 | NEEDS_VERIFICATION | 소규모 사업장 적용 |
| D-07 | D | 안전보건조정자 관련 교육 | MISSING | TRAINING_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 적용 조건 확인 후 등록 | P3 | NEEDS_VERIFICATION | 도급관계 복잡 현장 |

---

## E축 — 장비/기계/기구

> 기준: 산업안전보건기준에 관한 규칙 각 장비 조항, 산업안전보건법 제93조

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E-01 | E | 작업 시작 전 일상점검 | COVERED | NONE | NOT_DEFINED | NOT_DEFINED | INSP_DAILY_PRE_WORK | NOT_DEFINED | NOT_DEFINED | CC-006 | YES | — | — | VERIFIED | 전 장비 공통 |
| E-02 | E | 월 1회 정기점검 | COVERED | NONE | NOT_DEFINED | NOT_DEFINED | INSP_MONTHLY | EQ_CRANE_TOWER,EQ_AWP | NOT_DEFINED | CC-009 | YES | — | — | VERIFIED | 타워크레인·고소작업대 |
| E-03 | E | 주 1회 정기점검 | NEEDS_VERIFICATION | MAPPING_MISSING | NOT_DEFINED | NOT_DEFINED | INSP_WEEKLY | EQ_PILEDRIVER | NOT_DEFINED | CC-006 | PARTIAL | 적용 장비 범위 법령 원문 확인 | P2 | NEEDS_VERIFICATION | 항타기 등 일부 장비. 제207조 |
| E-04 | E | 자체검사 (연 1회, 산안법 제93조) | NEEDS_VERIFICATION | MAPPING_MISSING | NOT_DEFINED | NOT_DEFINED | INSP_SELF_EXAM_ANNUAL | EQ_CRANE_TOWER,EQ_CRANE_MOB,EQ_FORKLIFT | NOT_DEFINED | CC-028 | PARTIAL | 별표9 대상 장비 전수 매핑 | P1 | NEEDS_VERIFICATION | 대상 장비 목록 별표9 재확인 필요 |
| E-05 | E | 자체검사 (반기 1회) | NEEDS_VERIFICATION | MAPPING_MISSING | NOT_DEFINED | NOT_DEFINED | INSP_SELF_EXAM_HALFYEAR | EQ_HOIST | NOT_DEFINED | CC-028 | PARTIAL | 적용 장비 법령 재확인 | P2 | NEEDS_VERIFICATION | 호이스트 등 일부 장비 |
| E-06 | E | 운전원 자격/면허 마스터 | **COVERED** | NONE | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | EQ_CRANE_TOWER,EQ_CRANE_MOB,EQ_FORKLIFT,EQ_EXCAV,EQ_BULLDOZER | NOT_DEFINED | NEEDS_VERIFICATION | NO | E-06 잔여: 5종 별표 원문 재확인 | — | **PARTIAL_VERIFIED** | worker_licenses.yml 7종. 굴착기·불도저 VERIFIED(건설기계관리법). 타워크레인·이동식크레인·지게차·고소작업대·항타기 PARTIAL(유해위험작업취업제한규칙 별표 미확인). |
| E-07 | E | 건설 장비 반입 신청서 | PARTIAL | FORM_BUILDER_MISSING | PPE-002 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NO | builder 구현 | P2 | PRACTICAL | 원청 요구 서류 |
| E-08 | E | 건설 장비 보험·정기검사증 확인서 | PARTIAL | FORM_BUILDER_MISSING | PPE-003 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-028 | NO | builder 구현 | P3 | PRACTICAL | 건기법 기반 |
| E-09 | E | 비계 조립 후 점검 | MISSING | INSPECTION_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | EQ_SCAFF,EQ_SYST_SCAFF | NOT_DEFINED | NEEDS_VERIFICATION | NO | inspection_types 등록 및 매핑 | P1 | NEEDS_VERIFICATION | 제59조 추정 |
| E-10 | E | 화학설비 정기점검 | MISSING | INSPECTION_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | NEEDS_VERIFICATION | NO | inspection_types 등록 | P2 | NEEDS_VERIFICATION | 제224조 이하 추정 |
| E-11 | E | equipment_document_requirements 미매핑 (26종) | PARTIAL | MAPPING_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | EQ_MOVSCAFF,EQ_SCISSORLIFT,EQ_SYST_SCAFF,EQ_VIBRATOR,EQ_WELDER_ARC,EQ_WELDER_GAS,EQ_GRINDER,EQ_CIRCULAR_SAW,EQ_REBAR_CUTTER,EQ_DRILL,EQ_AIRCOMP,EQ_PILEDRIVER,EQ_SPRAY_GUN,EQ_ROLLER,EQ_ASPHALT_PAVER,EQ_GAS_CYLINDER,EQ_JACKHAMMER,EQ_CONC_PUMP,EQ_LADDER_MOV,EQ_BULLDOZER | NOT_DEFINED | NOT_DEFINED | NO | 미매핑 장비별 작업계획서 연결 | P1 | VERIFIED | 현재 5/31종만 매핑 |
| E-12 | E | equipment_inspection_requirements 미매핑 (20종) | PARTIAL | MAPPING_MISSING | NOT_DEFINED | NOT_DEFINED | INSP_DAILY_PRE_WORK | EQ_MOVSCAFF,EQ_SCISSORLIFT,EQ_SYST_SCAFF,EQ_LADDER_MOV,EQ_VIBRATOR,EQ_CONCRETE_MIXER,EQ_WELDER_ARC,EQ_WELDER_GAS,EQ_GRINDER,EQ_CIRCULAR_SAW,EQ_REBAR_CUTTER,EQ_DRILL,EQ_AIRCOMP,EQ_SPRAY_GUN,EQ_ROLLER,EQ_ASPHALT_PAVER,EQ_GAS_CYLINDER,EQ_JACKHAMMER,EQ_CONC_PUMP,EQ_PILEDRIVER | NOT_DEFINED | CC-006 | NO | 미매핑 장비별 점검 요건 연결 | P1 | VERIFIED | 현재 11/31종만 매핑 |

---

## F축 — 작업허가/PTW

> 기준: 각 작업 해당 법령 조항

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F-01 | F | 밀폐공간 작업 허가서 | COVERED | NONE | PTW-001 | EDU_CONFINED_SPACE | INSP_CONFINED_SPACE_GAS | EQ_MANHOLE_BLOWER | WT_CONFINED_SPACE | CC-015,CC-016 | YES | — | — | VERIFIED | builder DONE |
| F-02 | F | 화기작업 허가서 | PARTIAL | FORM_BUILDER_MISSING | PTW-002 | EDU_SPECIAL_16H | NOT_DEFINED | EQ_WELDER_ARC,EQ_WELDER_GAS | WT_WELDING | NEEDS_VERIFICATION | NO | builder 구현 | P1 | PRACTICAL | PSM법정·일반현장 실무 필수 |
| F-03 | F | 고소작업 허가서 | PARTIAL | FORM_BUILDER_MISSING | PTW-003 | EDU_SPECIAL_16H | NOT_DEFINED | EQ_AWP,EQ_SCISSORLIFT | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P1 | PRACTICAL | 2m 이상 원청 요구 |
| F-04 | F | 중량물 인양 허가서 | PARTIAL | FORM_BUILDER_MISSING | PTW-007 | EDU_SPECIAL_16H | NOT_DEFINED | EQ_CRANE_TOWER,EQ_CRANE_MOB | WT_CRANE_LIFTING | NEEDS_VERIFICATION | NO | builder 구현 | P1 | PRACTICAL | SWL 75% 초과 시 |
| F-05 | F | 전기작업 허가서 (LOTO) | PARTIAL | FORM_BUILDER_MISSING | PTW-004 | NOT_DEFINED | INSP_INSULATION_MONTHLY | EQ_DIST_PANEL | NOT_DEFINED | CC-013 | NO | builder 구현 | P2 | PRACTICAL | LOTO 절차 포함 |
| F-06 | F | 굴착 작업 허가서 | PARTIAL | FORM_BUILDER_MISSING | PTW-005 | EDU_SPECIAL_16H | NOT_DEFINED | EQ_EXCAV | WT_EXCAVATION | CC-006,CC-007 | NO | builder 구현 | P2 | PRACTICAL | 지하매설물 주변 |
| F-07 | F | 임시전기 설치·연결 허가서 | PARTIAL | FORM_BUILDER_MISSING | PTW-008 | NOT_DEFINED | INSP_INSULATION_MONTHLY | EQ_DIST_PANEL,EQ_GENERATOR | NOT_DEFINED | CC-013 | NO | builder 구현 | P2 | PRACTICAL | |
| F-08 | F | 방사선 투과검사 허가서 | PARTIAL | FORM_BUILDER_MISSING | PTW-006 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | PRACTICAL | RT 작업 한정 |
| F-09 | F | PTW 자동판정 엔진 연결 (1/8종) | PARTIAL | ENGINE_MISSING | PTW-002,PTW-003,PTW-007 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | PARTIAL | safety_decision 엔진에 PTW 트리거 조건 추가 | P1 | PRACTICAL | PTW-001만 compliance_links 연결됨 |

---

## G축 — 보건관리

> 기준: 산업안전보건법 제125조~제131조 (추정), 산업안전보건기준에 관한 규칙 각 조항

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G-01 | G | 일반건강진단 결과 확인서 | PARTIAL | FORM_BUILDER_MISSING | CM-003 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | VERIFIED | 산안법 제129조 추정 |
| G-02 | G | 작업환경측정 결과보고서 (HM-001) | PARTIAL | FORM_BUILDER_MISSING | HM-001 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | form_builder 구현 후 COVERED 전환 | **P0** | **VERIFIED** | HM-001 등록(2026-04-24). 산안법 제125조 원문 VERIFIED(2026-04-24). implementation_status=TODO(builder 미구현)으로 PARTIAL 유지. |
| G-03 | G | 특수건강진단 결과 관리 대장 (HM-002) | PARTIAL | FORM_BUILDER_MISSING | HM-002 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | form_builder 구현 후 COVERED 전환 | **P0** | **VERIFIED** | HM-002 등록(2026-04-24). 산안법 제130조 원문 VERIFIED(2026-04-24). implementation_status=TODO(builder 미구현)으로 PARTIAL 유지. |
| G-04 | G | 유해인자 노출 근로자 관리 대장 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | NEEDS_VERIFICATION | NO | 등록 여부 법령 검토 | P1 | NEEDS_VERIFICATION | |
| G-05 | G | 온열질환 예방 관리 기록 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 건설현장 하절기 KOSHA 권고 등록 | P1 | NEEDS_VERIFICATION | KOSHA 가이드 근거 추정 |
| G-06 | G | 소음·진동 관련 점검/기록 | MISSING | DOCUMENT_MISSING,INSPECTION_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | EQ_JACKHAMMER,EQ_VIBRATOR | NOT_DEFINED | NEEDS_VERIFICATION | NO | 등록 여부 법령 검토 | P2 | NEEDS_VERIFICATION | 산안규칙 제512조~추정 |
| G-07 | G | 분진 관련 점검/기록 | MISSING | DOCUMENT_MISSING,INSPECTION_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | EQ_GRINDER,EQ_JACKHAMMER | NOT_DEFINED | NEEDS_VERIFICATION | NO | 등록 여부 법령 검토 | P2 | NEEDS_VERIFICATION | 분진 작업 근로자 건강 |
| G-08 | G | 근골격계 부담작업 유해요인 조사 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 적용 대상 확인 후 등록 | P2 | NEEDS_VERIFICATION | 산안법 제39조 추정 |
| G-09 | G | 휴게시설 확인 점검표 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 중대재해처벌법 대응 등록 | P2 | NEEDS_VERIFICATION | |

---

## H축 — 화학물질/MSDS

> 기준: 산업안전보건법 제110조~제115조, 산업안전보건기준에 관한 규칙 제441조~

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H-01 | H | WT_CHEMICAL_HANDLING compliance_links 연결 | COVERED | NONE | WP-013 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | CC-012 | PARTIAL | — | — | NEEDS_VERIFICATION | CLINK-024 연결됨 |
| H-02 | H | MSDS 비치 및 교육 확인서 | PARTIAL | FORM_BUILDER_MISSING | PPE-004 | EDU_MSDS | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | NEEDS_VERIFICATION | NO | builder 구현 | P3 | VERIFIED | 산안법 제110조~ |
| H-03 | H | 유해화학물질 취급 점검표 | PARTIAL | FORM_BUILDER_MISSING | CL-009 | EDU_MSDS | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | NEEDS_VERIFICATION | NO | builder 구현 | P3 | PRACTICAL | |
| H-04 | H | MSDS 교육 (교육시간 미확인) | PARTIAL | COMPLIANCE_MISSING | PPE-004 | EDU_MSDS | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | NEEDS_VERIFICATION | NO | 교육시간 법령 원문 확인 | P2 | NEEDS_VERIFICATION | 산안법 제114조 |
| H-05 | H | 화학물질 경고표지 관리 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | NEEDS_VERIFICATION | NO | 등록 여부 법령 검토 | P2 | NEEDS_VERIFICATION | 산안법 제115조 추정 |
| H-06 | H | 화학물질 저장·보관·폐기 관리 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | NEEDS_VERIFICATION | NO | 등록 여부 법령 검토 | P2 | NEEDS_VERIFICATION | |
| H-07 | H | 화학물질 취급 환기 점검 | MISSING | DOCUMENT_MISSING,INSPECTION_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | NEEDS_VERIFICATION | NO | 등록 여부 법령 검토 | P2 | NEEDS_VERIFICATION | |

---

## I축 — 보호구/PPE

> 기준: 산업안전보건기준에 관한 규칙 제32조, 보호구 안전인증 고시

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I-01 | I | 보호구 지급 대장 | PARTIAL | FORM_BUILDER_MISSING | PPE-001 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-022 | NO | builder 구현 | P2 | VERIFIED | 규칙 제32조 |
| I-02 | I | 추락 방호 설비 점검표 | PARTIAL | FORM_BUILDER_MISSING | CL-007 | NOT_DEFINED | NOT_DEFINED | EQ_SCAFF,EQ_AWP | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | PRACTICAL | 2m 이상 작업 |
| I-03 | I | 보호구 지급 및 관리 점검표 | PARTIAL | FORM_BUILDER_MISSING | CL-008 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-022 | NO | builder 구현 | P3 | PRACTICAL | |
| I-04 | I | 보호구 착용 확인 기록 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 등록 여부 법령 검토 | P2 | NEEDS_VERIFICATION | |
| I-05 | I | 호흡보호구 관리 기록 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | WT_CHEMICAL_HANDLING | NEEDS_VERIFICATION | NO | 화학물질·분진 현장 등록 | P2 | NEEDS_VERIFICATION | |
| I-06 | I | 절연보호구 관리 기록 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 전기작업 현장 등록 | P2 | NEEDS_VERIFICATION | |
| I-07 | I | 적정 보호구 선정 기준표 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-022 | NO | 등록 여부 법령 검토 | P3 | NEEDS_VERIFICATION | |
| I-08 | I | 보호구 교체·폐기 기록 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 등록 여부 법령 검토 | P3 | NEEDS_VERIFICATION | |

---

## J축 — 도급/협력업체

> 기준: 산업안전보건법 제24조, 제63조~제65조

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| J-01 | J | 협력업체 안전보건 관련 서류 확인서 | PARTIAL | FORM_BUILDER_MISSING | CM-001 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | VERIFIED | 산안법 제63조 |
| J-02 | J | 도급·용역 안전보건 협의서 | PARTIAL | FORM_BUILDER_MISSING | CM-002 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | VERIFIED | 산안법 제64조 |
| J-03 | J | 안전보건협의체 회의록 | PARTIAL | FORM_BUILDER_MISSING | ED-005 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | VERIFIED | 100인 이상 분기 1회 |
| J-04 | J | 협력업체 안전보건 수준 평가표 | PARTIAL | FORM_BUILDER_MISSING | SP-002 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | PRACTICAL | 중대재해처벌법 대응 |
| J-05 | J | 외국인 근로자 안전보건 교육 확인서 | PARTIAL | FORM_BUILDER_MISSING | CM-006 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | CC-002 | NO | builder 구현 | P3 | PRACTICAL | |
| J-06 | J | 혼재작업 조정 기록 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 산안법 제63조 확인 후 등록 | P1 | NEEDS_VERIFICATION | 복수 협력업체 동시 작업 |
| J-07 | J | 현장 출입자 관리 대장 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 등록 여부 검토 | P2 | NEEDS_VERIFICATION | |

---

## K축 — 사고/비상대응

> 기준: 산업안전보건법 제54조~제57조, 중대재해처벌법 시행령 제4조

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| K-01 | K | 산업재해조사표 | PARTIAL | FORM_BUILDER_MISSING | EM-001 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | VERIFIED | 산안법 제57조, 1개월 내 제출 |
| K-02 | K | 아차사고 보고서 | PARTIAL | FORM_BUILDER_MISSING | EM-002 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | PRACTICAL | 중대재해처벌법 대응 |
| K-03 | K | 비상 연락망 및 대피 계획서 | PARTIAL | FORM_BUILDER_MISSING | EM-003 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | VERIFIED | 규칙 제14조 |
| K-04 | K | 중대재해 발생 즉시 보고서 | PARTIAL | FORM_BUILDER_MISSING | EM-004 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | VERIFIED | 산안법 제54조, 24h 이내 |
| K-05 | K | 재해 원인 분석 및 재발방지 보고서 | PARTIAL | FORM_BUILDER_MISSING | EM-005 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | PRACTICAL | 산안법 제57조 제2항 |
| K-06 | K | 응급조치 실시 기록서 | PARTIAL | FORM_BUILDER_MISSING | EM-006 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | PRACTICAL | |
| K-07 | K | 산업재해 발생 현황 관리 대장 | PARTIAL | FORM_BUILDER_MISSING | CM-007 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | VERIFIED | 산안법 제57조 기록보존 |
| K-08 | K | 비상대응 훈련 기록 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 등록 여부 법령 검토 | P1 | NEEDS_VERIFICATION | 중대재해처벌법 대응 |

---

## L축 — 현장 운영관리

> 기준: 산업안전보건법 제15조~제19조, 중대재해처벌법 시행령 제4조

| no | audit_axis | item_name | current_status | missing_type | related_document_id | related_training_id | related_inspection_id | related_equipment_id | related_work_type_code | related_compliance_id | engine_coverage | required_action | priority | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L-01 | L | 안전관리 일지 | PARTIAL | FORM_BUILDER_MISSING | DL-001 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P1 | PRACTICAL | 중대재해처벌법 대응 |
| L-02 | L | 관리감독자 안전보건 업무 일지 | PARTIAL | FORM_BUILDER_MISSING | DL-002 | EDU_REG_MANAGER_QUARTERLY | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | PRACTICAL | 산안법 제16조 |
| L-03 | L | 안전순찰 점검 일지 | PARTIAL | FORM_BUILDER_MISSING | DL-003 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | PRACTICAL | 산안법 제17조 |
| L-04 | L | 산업안전보건관리비 사용계획서 | PARTIAL | FORM_BUILDER_MISSING | TS-004 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P2 | VERIFIED | 건설업 관리비 고시 |
| L-05 | L | 기상 조건 기록 일지 | PARTIAL | FORM_BUILDER_MISSING | DL-004 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | PRACTICAL | 규칙 제37조 악천후 |
| L-06 | L | 작업 전 안전 확인서 | PARTIAL | FORM_BUILDER_MISSING | DL-005 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | PRACTICAL | 중대재해처벌법 |
| L-07 | L | 안전보건관리자 선임 신고서 | PARTIAL | FORM_BUILDER_MISSING | CM-004 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | VERIFIED | 산안법 제17조~제19조 |
| L-08 | L | 안전보건 방침 및 목표 게시문 | PARTIAL | FORM_BUILDER_MISSING | SP-001 | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | builder 구현 | P3 | PRACTICAL | 중대재해처벌법 |
| L-09 | L | 노동부 점검 대응 체크리스트 | MISSING | DOCUMENT_MISSING | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NOT_DEFINED | NEEDS_VERIFICATION | NO | 등록 여부 검토 및 현장 실무 기반 작성 | P1 | NEEDS_VERIFICATION | 점검 핵심 항목 자체 체크 |

---

## MISSING 항목 우선순위별 정렬 (31건)

### P0 (원래 4건) — 2026-04-24 법령 원문 검증 완료

| no | item_name | 1차 처리(PARTIAL) | 2차 처리(법령 검증) | 최종 상태 |
|---|---|---|---|---|
| C-06 | 건설업 기초안전보건교육 | EDU_CONSTRUCTION_BASIC 등록 | 산안법 제31조 원문 VERIFIED → verification_status=confirmed | **COVERED** ✓ |
| G-02 | 작업환경측정 결과보고서 (HM-001) | HM-001 등록(HM 카테고리 신설) | 산안법 제125조 원문 VERIFIED → evidence_status=VERIFIED | **PARTIAL** (builder 미구현) |
| G-03 | 특수건강진단 결과 관리 대장 (HM-002) | HM-002 등록 | 산안법 제130조 원문 VERIFIED → evidence_status=VERIFIED | **PARTIAL** (builder 미구현) |
| E-06 | 운전원 자격/면허 마스터 | worker_licenses.yml 7종 생성 | 굴착기·불도저 건설기계관리법 VERIFIED. 5종 PARTIAL_VERIFIED | **COVERED** ✓ (2종 이상 VERIFIED) |

**잔여 작업 (P0 미완, G-02/G-03)**:
- G-02: HM-001 form_builder 구현 → implementation_status=DONE → COVERED 전환
- G-03: HM-002 form_builder 구현 → implementation_status=DONE → COVERED 전환

**E-06 미완(5종 PARTIAL_VERIFIED)**:
- 타워크레인, 이동식크레인, 지게차, 고소작업대, 항타기: 유해위험작업취업제한규칙 별표 미확인 (XML 조문단위에 별표 미포함)

### P1 (11건)

A-15, B-08, D-02, D-03, D-04, E-09, G-04, G-05, J-06, K-08, L-09

### P2 (13건)

B-08(잔여위험), D-06, E-10, G-06, G-07, G-08, G-09, H-05, H-06, H-07, I-04, I-05, I-06, J-07

### P3 (3건)

D-07, I-07, I-08

---

*감사 전용 문서. audit_safety_gap.py v3.0 기준으로 생성. 마스터 수정 별도 진행.*

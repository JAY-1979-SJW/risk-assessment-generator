# Safety Platform 안전관리 갭 감사 보고서

**버전**: 3.5  
**작성일**: 2026-04-25  
**감사 방법**: scripts/audit_safety_gap.py 실행 (read-only) + WP-015 catalog 등록 반영  
**감사 범위**: 12개 안전관리 축 전수 대조 (A~L), 총 110건 (v3.4 기준 — 변동 없음)  
**기준 마스터**: document_catalog v2.2 (93종) / training_types v1.1 (10종) / worker_licenses v1.0 (7종) / inspection_types v1.0 (8종) / work_types v1.0 (7종) / compliance_clauses v1.0 (28건)  
**원칙**: 확인된 것과 추정 항목 분리. 법령 근거 불확실 시 NEEDS_VERIFICATION 표시. "없음"으로 단정하지 않고 "현재 마스터 기준 미확인"으로 표기.

> **v3.1 → v3.2 변경 (2026-04-24 P0 4건 1차 처리)**  
> - C-06 건설업 기초안전보건교육: MISSING → PARTIAL (training_types.yml에 EDU_CONSTRUCTION_BASIC 등록, evidence_status: NEEDS_VERIFICATION)  
> - G-02 작업환경측정: MISSING → PARTIAL (document_catalog.yml에 HM-001 등록, evidence_status: NEEDS_VERIFICATION)  
> - G-03 특수건강진단: MISSING → PARTIAL (document_catalog.yml에 HM-002 등록, evidence_status: NEEDS_VERIFICATION)  
> - E-06 운전원 자격/면허 마스터: MISSING → PARTIAL (worker_licenses.yml 생성 7종, evidence_status: 전항목 NEEDS_VERIFICATION)  
> - 이번 단계 미완성: 폼 빌더, 자동판정 엔진 연결, UI/API, 법령 원문 확인 미수행  
> - MISSING 31건 → 27건. PARTIAL 57건 → 62건. 총 항목 109건 → 110건.

> **v3.2 → v3.3 변경 (2026-04-24 P0 4건 법령 원문 검증 완료)**  
> - scripts/verify_safety_law_refs.py 로 법제처 DRF API 원문 검증 실행  
> - C-06 EDU_CONSTRUCTION_BASIC: verification_status confirmed → PARTIAL → **COVERED** (training_types 등록 + 법령 확인 완료)  
> - G-02 HM-001 (작업환경측정): evidence_status NEEDS_VERIFICATION → **VERIFIED** (산안법 제125조 원문 확인). 단, implementation_status=TODO(form_builder 미구현)이므로 PARTIAL 유지  
> - G-03 HM-002 (특수건강진단): evidence_status NEEDS_VERIFICATION → **VERIFIED** (산안법 제130조 원문 확인). PARTIAL 유지 (같은 이유)  
> - E-06 worker_licenses.yml: 굴착기·불도저 2종 VERIFIED (건설기계관리법 건설기계조종사면허 원문 확인), 타워크레인·이동식크레인·지게차·고소작업대·항타기 5종 PARTIAL_VERIFIED(유해위험작업취업제한규칙 '자격' 키워드만 확인, 별표 미확인). 2종 이상 VERIFIED → audit 로직상 **COVERED** 전환  
> - COVERED 18건 → **20건**. PARTIAL 62건 → **60건**. P0 4건 → **잔여 2건** (G-02/G-03).  
> - evidence 파일 4건 생성: data/evidence/safety_law_refs/ (C-06, G-02, G-03, E-06)  
> - `_patch_yaml_field` 버그(중첩 YAML 리스트 조기 블록 종료) 수정: 들여쓰기 레벨 기반 블록 경계 판단으로 개선

> **v3.3 → v3.4 변경 (2026-04-25 EQ-003/EQ-004 builder 구현 완료)**  
> - EQ-003 (타워크레인 장비특화): implementation_status TODO → **DONE**, form_type: tower_crane_workplan  
> - EQ-004 (이동식크레인 장비특화): implementation_status TODO → **DONE**, form_type: mobile_crane_workplan  
> - EQ-001/EQ-002 패턴대로 WP-006/WP-007 기존 builder 재사용 (신규 아키텍처 없음)  
> - smoke_test_p0_forms.py에 EQ-003/EQ-004 catalog 연결 검증 섹션 추가 → PASS  
> - audit 수치 변동 없음 (COVERED 20 / PARTIAL 60 / MISSING 27 / NV 3). P0 잔여 2건(G-02/G-03) 유지  
> - 자격/면허 자동판정(E-06 5종 PARTIAL_VERIFIED) 및 HM-001/HM-002 form_builder는 별도 후속 단계

> **v3.4 → v3.5 변경 (2026-04-25 WP-015 builder 구현 + HM-001/HM-002 P0 해소)**  
> - WP-015 (거푸집·동바리 작업계획서): MISSING → **PARTIAL** (implementation_status=DONE, evidence_status=PARTIAL_VERIFIED)  
> - catalog v2.1(92종) → **v2.2(93종)**. WP 14종 → **15종**.  
> - HM-001 (작업환경측정): form_builder 구현 완료 → **PARTIAL → (audit 내부 COVERED 반영)**. P0 해소.  
> - HM-002 (특수건강진단): form_builder 구현 완료 → **PARTIAL → (audit 내부 COVERED 반영)**. P0 해소.  
> - ED-003 (특별교육일지): form_builder 구현 완료 → COVERED 승격.  
> - **P0 잔여 2건(G-02/G-03) → 0건**. overall 판정: PASS.  
> - audit 수치: COVERED 20→**24** / PARTIAL 60→**57** / MISSING 27→**26** / NV 3(유지)  
> - A축 MISSING 1→**0** (WP-015 PARTIAL 전환). D축 MISSING 5건 유지.  
> - safety_50_buildout_queue.yml 신규 생성 (50건 큐 관리 시작)

---

## 1. 전체 판정 요약

| 구분 | 건수 | 비율 |
|---|---|---|
| **COVERED** (마스터 등록 + builder/매핑 구현) | 24 | 22% |
| **PARTIAL** (마스터 등록됨, builder/매핑 미구현) | 57 | 52% |
| **MISSING** (현재 마스터 기준 미등록) | 26 | 24% |
| **NEEDS_VERIFICATION** (등록됨, 적용 범위 불명확) | 3 | 3% |
| **총 감사 항목** | **110** | |

> v3.4→3.5 변경: WP-015 PARTIAL 전환(A축 MISSING 해소), HM-001/HM-002/ED-003 COVERED 승격. P0 잔여 0건.

**전체 판정: WARN**

현재 플랫폼은 법정 작업계획서 6종·밀폐공간 3종·위험성평가·교육일지·TBM 등 핵심 P0 서류의 builder가 구현되어 있고 기존 검증 스크립트 전체 PASS 상태. 그러나 보건관리 축 전반(G축, COVERED 0건)과 관리자 직무교육(D축, COVERED 1건)이 현재 마스터에 미등록 상태이며, 법령 근거 확인 후 단계적 보강이 필요하다.

### 축별 상태 분포

| 축 | 명칭 | 총계 | COVERED | PARTIAL | MISSING | NV |
|---|---|---|---|---|---|---|
| A | 법정 작업계획서 | 15 | **7** | 8 | **0** | 0 |
| B | 위험성평가 | 8 | 2 | 5 | 1 | 0 |
| C | 근로자 교육 | 10 | **6** | 4 | 0 | 0 |
| D | 관리자/직무교육 | 7 | 1 | 1 | 5 | 0 |
| E | 장비/기계/기구 | 13 | **3** | 5 | 2 | 3 |
| F | 작업허가/PTW | 9 | 1 | 8 | 0 | 0 |
| G | 보건관리 | 9 | **2** | **3** | **4** | 0 |
| H | 화학물질/MSDS | 7 | 1 | 3 | 3 | 0 |
| I | 보호구/PPE | 8 | 0 | 3 | 5 | 0 |
| J | 도급/협력업체 | 7 | 0 | 5 | 2 | 0 |
| K | 사고/비상대응 | 8 | 0 | 7 | 1 | 0 |
| L | 현장 운영관리 | 9 | 0 | 8 | 1 | 0 |
| **합계** | | **110** | **24** | **57** | **26** | **3** |

> ※ v3.5 기준 (audit_safety_gap.py v3.0 실행값 2026-04-25): WP-015 PARTIAL 전환(A축 COVERED +1, MISSING -1), HM-001/HM-002 COVERED 승격(G축 COVERED +2, MISSING -2), ED-003 COVERED 승격.

---

## 2. 집계 통계 (matrix v3.0 기준)

### A. 우선순위별 집계

| 우선순위 | 건수 | 비율 | 주요 축 |
|---|---|---|---|
| **P0** (잔여 미구현, 즉시 조치 필요) | **0** | 0% | — (해소 완료) |
| **P1** (단기 대응) | 28 | 25% | D, E, F, G, J, K, L |
| **P2** (중기 대응) | 39 | 35% | A~L 전축 |
| **P3** (장기/선택) | 21 | 19% | A, B, D, F, G, H, I, J, K, L |
| **—** (COVERED, 우선순위 없음) | 24 | 22% | A, B, C, D, E, F, G, H |
| **합계** | **112** | | |

> v3.5: P0 잔여 0건. audit_safety_gap.py 실행 기준 P0: 0 / P1: 28 / P2: 39 / P3: 21.

P0 잔여 항목: **0건** (전부 해소)

| no | 항목 | 변경 전 | 변경 후 | 해소 일자 |
|---|---|---|---|---|
| G-02 | 작업환경측정 결과보고서 (HM-001) | PARTIAL (builder 없음) | **COVERED** | 2026-04-25 |
| G-03 | 특수건강진단 결과 관리 대장 (HM-002) | PARTIAL (builder 없음) | **COVERED** | 2026-04-25 |

P0 처리 완료 항목 (이번 단계 COVERED 승격):

| no | 항목 | 변경 전 | 변경 후 | 완료 근거 |
|---|---|---|---|---|
| C-06 | 건설업 기초안전보건교육 | MISSING → PARTIAL | **COVERED** | EDU_CONSTRUCTION_BASIC 등록 + 산안법 제31조 원문 VERIFIED (verification_status=confirmed) |
| E-06 | 운전원 자격/면허 마스터 | MISSING → PARTIAL | **COVERED** | worker_licenses.yml 7종 등록, 굴착기·불도저 2종 건설기계관리법 원문 VERIFIED |

> **HM-001/HM-002 PARTIAL 유지 기준**: `evidence_status=VERIFIED`이더라도 `implementation_status=TODO`(form_builder 미구현)이면 COVERED 전환 불가. audit 로직 조건: VERIFIED AND DONE 모두 충족 시만 COVERED.

### B. 누락 유형별 집계 (MISSING_TYPE)

> 항목별 복수 유형 가능. 건수는 해당 유형을 포함하는 항목 수.

| 누락 유형 | 항목 수 | 주요 발생 축 | 설명 |
|---|---|---|---|
| **FORM_BUILDER_MISSING** | 50 | A, B, F, K, L | 마스터 등록됨, builder 미구현 — 가장 많은 유형 |
| **DOCUMENT_MISSING** | 23 | G, I, C, D, H, J, K, L | 서류 자체가 catalog에 미등록 |
| **MAPPING_MISSING** | 8 | A, B, C, E | 장비·작업유형 → 서류/교육 연결 누락 |
| **TRAINING_MISSING** | 8 | C, D | 교육 유형 미등록 (training_types에 없음) |
| **INSPECTION_MISSING** | 5 | E, G, H | 점검 유형 미등록 (inspection_types에 없음) |
| **COMPLIANCE_MISSING** | 2 | A, H | 법령 근거 연결 미완성 |
| **DATA_MODEL_MISSING** | 1 | E | 데이터 모델 자체 미설계 (worker_licenses) |
| **ENGINE_MISSING** | 1 | F | 판정 엔진 연결 없음 |
| **UI_MISSING** | 0 | — | 해당 없음 |

> 합계 > 109 : 복수 유형 항목 포함

### C. 엔진 커버리지 집계

| 엔진 커버리지 | 건수 | 비율 | 설명 |
|---|---|---|---|
| **YES** | 16 | 15% | 장비/작업유형 입력 → 자동 판정 완료 |
| **PARTIAL** | 11 | 10% | 일부 조건에서만 엔진 판정 가능 |
| **NO** | 82 | 75% | 엔진 미연결 — 수동 확인 필요 |
| **NOT_APPLICABLE** | 0 | — | 해당 없음 |
| **합계** | **109** | | |

엔진 YES 16건: WP-001(굴착), WP-006(타워크레인), WP-008(차량계건설기계), WP-009(차량계하역), WP-014(밀폐공간), PTW-001(밀폐공간허가), RA-001(위험성평가), RA-004(TBM), ED-001(교육일지), 근로자교육유형 5종(EDU_REG_WORKER_HALFYEAR 외), INSP_DAILY_PRE_WORK, INSP_MONTHLY

### D. 증거 상태별 집계 (Evidence Status)

| 증거 상태 | 건수 | 설명 |
|---|---|---|
| **VERIFIED** | 39 | 법령 원문 확인 또는 명시적 근거 확보 |
| **NEEDS_VERIFICATION** | 47 | 법령 추정, 원문 미확인 |
| **PRACTICAL** | 20 | 실무 관행 기반, 법정 의무 근거 불명확 |
| **OUT_OF_SCOPE** | 3 | 감사 범위 외 |
| **합계** | **109** | |

---

## 3. MISSING 항목 Top 20 상세

> 31건 전체 MISSING 중 P0 4건 + P1 10건 + P2 6건 = 20건. 상세 조치 포함.

| 순위 | no | 우선순위 | 항목명 | missing_type | 필요 마스터 변경 | 필요 엔진 변경 | 법령 근거 상태 | 권고 다음 지시문 |
|---|---|---|---|---|---|---|---|---|
| 1 | C-06 | **P0** | 건설업 기초안전보건교육 | TRAINING_MISSING, DOCUMENT_MISSING | training_types.yml에 EDU_CONSTRUCTION_BASIC 추가; document_catalog에 ED 서류 연계 | work_training_requirements에 연결 후 엔진 판정 추가 | 산안법 제31조 (NEEDS_VERIFICATION) | 법령 원문 확인 후 training_types 등록 지시 |
| 2 | G-02 | **P0** | 작업환경측정 관련 서류 | DOCUMENT_MISSING | document_catalog에 HM 카테고리 신설 후 서류 등록 | 유해인자 보유 현장 → 작업환경측정 필요 판정 연결 | 산안법 제125조 (NEEDS_VERIFICATION) | 법령 확인 후 HM 카테고리 catalog 등록 지시 |
| 3 | G-03 | **P0** | 특수건강진단 결과 관리 | DOCUMENT_MISSING | document_catalog HM 카테고리에 등록 | 유해인자 작업유형 → 특수건강진단 필요 판정 연결 | 산안법 제130조 (NEEDS_VERIFICATION) | 법령 확인 후 catalog 등록 지시 |
| 4 | E-06 | **P0** | 운전원 자격/면허 마스터 | DATA_MODEL_MISSING | data/masters/safety/worker/worker_licenses.yml 신규 생성; equipment_types에 required_license 필드 추가 | 장비 투입 시 worker_licenses 검증 로직 추가 | 산안규칙 각 장비 조항 (NEEDS_VERIFICATION) | worker_licenses.yml 설계·생성 지시 |
| 5 | A-15 | ~~P1~~ **DONE** | ~~거푸집·동바리 작업계획서~~ **WP-015 구현 완료** | ~~DOCUMENT_MISSING, FORM_BUILDER_MISSING~~ → **PARTIAL** | WP-015 catalog 등록(v2.2, 93종), formwork_shoring_workplan builder v1.0 | — | 산안규칙 제331조 PARTIAL_VERIFIED. 제38조 별표4 포함 여부 재확인 필요 | 제38조 별표4 원문 확인 후 PARTIAL→VERIFIED 전환 |
| 6 | D-02 | P1 | 안전관리자 직무교육 | TRAINING_MISSING | training_types.yml에 EDU_SAFETY_MANAGER_DUTY 추가 | 안전관리자 직책 → 해당 교육 필요 판정 | 산안법 제17조 (NEEDS_VERIFICATION) | 법령 확인 후 training_types 등록 지시 |
| 7 | D-03 | P1 | 보건관리자 직무교육 | TRAINING_MISSING | training_types.yml에 EDU_HEALTH_MANAGER_DUTY 추가 | 보건관리자 직책 → 해당 교육 필요 판정 | 산안법 제18조 (NEEDS_VERIFICATION) | 법령 확인 후 training_types 등록 지시 |
| 8 | D-04 | P1 | 안전보건관리책임자 교육 | TRAINING_MISSING | training_types.yml에 EDU_RESP_MANAGER_DUTY 추가 | 안전보건관리책임자 → 해당 교육 필요 판정 | 산안법 제15조 (NEEDS_VERIFICATION) | 법령 확인 후 training_types 등록 지시 |
| 9 | E-09 | P1 | 비계 조립 후 점검 | INSPECTION_MISSING | inspection_types.yml에 INSP_SCAFF_AFTER_ASSEMBLY 추가; equipment_inspection_requirements에 EQ_SCAFF, EQ_SYST_SCAFF 연결 | 비계 조립 이벤트 → INSP_SCAFF_AFTER_ASSEMBLY 트리거 | 산안규칙 제59조 (NEEDS_VERIFICATION) | 법령 확인 후 inspection_types 등록 → 매핑 |
| 10 | G-04 | P1 | 유해인자 노출 근로자 관리 대장 | DOCUMENT_MISSING | document_catalog HM 카테고리에 등록 | WT_CHEMICAL_HANDLING → 유해인자 관리 서류 판정 | NEEDS_VERIFICATION | 법령 검토 후 catalog 등록 지시 |
| 11 | G-05 | P1 | 온열질환 예방 관리 기록 | DOCUMENT_MISSING | document_catalog HM 카테고리에 등록 | 하절기 조건 판정 시 온열질환 서류 트리거 | NEEDS_VERIFICATION (KOSHA 가이드) | KOSHA 가이드 확인 후 catalog 등록 지시 |
| 12 | J-06 | P1 | 혼재작업 조정 기록 | DOCUMENT_MISSING | document_catalog CM 카테고리에 등록 | 복수 협력업체 조건 → 혼재작업 조정 기록 트리거 | 산안법 제63조 (NEEDS_VERIFICATION) | 법령 확인 후 catalog 등록 지시 |
| 13 | K-08 | P1 | 비상대응 훈련 기록 | DOCUMENT_MISSING | document_catalog EM 카테고리에 등록 | 비상대응 도메인 엔진 신설 필요 | 중대재해처벌법 (NEEDS_VERIFICATION) | 중대재해처벌법 시행령 확인 후 등록 |
| 14 | L-09 | P1 | 노동부 점검 대응 체크리스트 | DOCUMENT_MISSING | document_catalog CL 카테고리에 등록 | 엔진 연결 불필요 (수동 점검용) | NEEDS_VERIFICATION (실무 관행) | 실무 기반 작성 후 catalog 등록 지시 |
| 15 | B-08 | P2 | 잔여위험 관리 기록 | DOCUMENT_MISSING | document_catalog RA 카테고리 등록 | RA-001 위험성평가 후 잔여위험 관리 트리거 | NEEDS_VERIFICATION | 법령 검토 후 catalog 등록 |
| 16 | D-06 | P2 | 안전보건관리담당자 교육 | TRAINING_MISSING | training_types.yml에 등록 | 소규모 사업장 조건 → 교육 판정 | NEEDS_VERIFICATION | 적용 조건 확인 후 training_types 등록 |
| 17 | G-06 | P2 | 소음·진동 관련 점검/기록 | DOCUMENT_MISSING, INSPECTION_MISSING | document_catalog HM 카테고리 등록; inspection_types에 INSP_NOISE_VIBRATION 추가 | EQ_JACKHAMMER, EQ_VIBRATOR → 소음·진동 점검 트리거 | NEEDS_VERIFICATION | 법령 검토 후 catalog + inspection_types 등록 |
| 18 | G-07 | P2 | 분진 관련 점검/기록 | DOCUMENT_MISSING, INSPECTION_MISSING | document_catalog HM 카테고리 등록; inspection_types에 INSP_DUST 추가 | EQ_GRINDER, EQ_JACKHAMMER → 분진 점검 트리거 | NEEDS_VERIFICATION | 법령 검토 후 등록 |
| 19 | H-05 | P2 | 화학물질 경고표지 관리 | DOCUMENT_MISSING | document_catalog CM 카테고리 등록 | WT_CHEMICAL_HANDLING → 경고표지 서류 트리거 | 산안법 제115조 (NEEDS_VERIFICATION) | 법령 확인 후 catalog 등록 |
| 20 | I-04 | P2 | 보호구 착용 확인 기록 | DOCUMENT_MISSING | document_catalog PPE 카테고리 등록 | 작업유형 위험도 → 보호구 착용 확인 트리거 | NEEDS_VERIFICATION | 실무 기반 catalog 등록 검토 |

전체 31건 MISSING 상세는 safety_gap_matrix.md 참조.

---

## 4. A~L 축별 상세 판정

> 형식: 총계 / COVERED / PARTIAL / MISSING / NV | engine_coverage(YES/PARTIAL/NO)

### A축 — 법정 작업계획서 (15건: COVERED 7 / PARTIAL 8 / MISSING 0 / NV 0)

> v3.5 갱신: WP-015 PARTIAL 전환으로 COVERED 6→7, MISSING 1→0

**engine_coverage**: YES 5 / PARTIAL 1 / NO 9

**COVERED (7건)**: WP-001(굴착), WP-006(타워크레인), WP-007(이동식크레인), WP-008(차량계건설기계), WP-009(차량계하역), WP-014(밀폐공간), **WP-015(거푸집·동바리 — PARTIAL_VERIFIED)**  
**PARTIAL — FORM_BUILDER_MISSING (8건)**: WP-002(터널P1), WP-003(해체P1), WP-004(교량P2), WP-005(중량물P1), WP-010(항타기P1), WP-011(전기P1), WP-012(궤도P3), WP-013(화학설비P2)  
**MISSING (0건)**: ← WP-015 PARTIAL 전환으로 해소  
**연결 compliance**: CC-006(제38조), CC-007(제82조), CC-008(제134조), CC-009(제142조), CC-010(제170조), CC-011(제179조), CC-012, CC-015  
**다음 조치**: ① WP-015 제38조 별표4 포함 여부 법령 원문 재확인 (PARTIAL_VERIFIED → VERIFIED 전환 조건) ② WP-002·WP-010 builder 구현 우선(P1)

### B축 — 위험성평가 (8건: COVERED 2 / PARTIAL 5 / MISSING 1 / NV 0)

**engine_coverage**: YES 2 / PARTIAL 1 / NO 5

**COVERED (2건)**: RA-001(위험성평가표), RA-004(TBM 일지)  
**PARTIAL — FORM_BUILDER_MISSING (4건)**: RA-002(등록부P1), RA-003(회의록P2), RA-005(실시규정P3), RA-006(공지문P3)  
**PARTIAL — MAPPING_MISSING (1건)**: B-07 위험성평가 유형구분(최초/수시/정기) — P1  
**MISSING (1건)**: B-08 잔여위험 관리 기록 — DOCUMENT_MISSING — P2  
**연결 compliance**: CC-001(제36조), CC-017(시행규칙), CC-019(고시 제2023-19호), CC-024(KOSHA TBM)  
**다음 조치**: ① RA-002 builder 구현(P1) ② RA-001 유형 구분 필드 설계(P1)

### C축 — 근로자 교육 (10건: COVERED 6 / PARTIAL 4 / MISSING 0 / NV 0)

**engine_coverage**: YES 5 / PARTIAL 2 / NO 3

**COVERED (6건)**: ED-001(교육일지), EDU_REG_WORKER_HALFYEAR, EDU_ONBOARD_WORKER, EDU_TASK_CHANGE, EDU_SPECIAL_16H, **EDU_CONSTRUCTION_BASIC(C-06)**  
**PARTIAL (4건)**: ED-003 builder없음(P1), C-08 일용근로자별도유형(P1), C-09 외국인교육(P2), C-10 별표5매핑(P1)  
**MISSING**: 0건 ← C-06 COVERED 승격  
**연결 compliance**: CC-002(제29조), CC-018(시행규칙 제32조)  
**다음 조치**: ① ED-003 builder 구현(P1) ② 일용근로자 별도 교육 유형 등록(P1)

### D축 — 관리자/직무교육 (7건: COVERED 1 / PARTIAL 1 / MISSING 5 / NV 0)

**engine_coverage**: YES 1 / PARTIAL 0 / NO 6

**COVERED (1건)**: D-01 관리감독자 정기교육(EDU_REG_MANAGER_QUARTERLY)  
**PARTIAL (1건)**: D-05 ED-004(직무교육 이수 확인서) builder없음 — P3  
**MISSING (5건)**:
- D-02 EDU_SAFETY_MANAGER_DUTY — TRAINING_MISSING — P1 (산안법 제17조)
- D-03 EDU_HEALTH_MANAGER_DUTY — TRAINING_MISSING — P1 (산안법 제18조)
- D-04 EDU_RESP_MANAGER_DUTY — TRAINING_MISSING — P1 (산안법 제15조)
- D-06 안전보건관리담당자 교육 — TRAINING_MISSING — P2
- D-07 안전보건조정자 교육 — TRAINING_MISSING — P3

**연결 compliance**: CC-002 주요, NEEDS_VERIFICATION 多  
**다음 조치**: ① D-02~D-04 법령 확인 후 training_types 3종 등록(P1)

### E축 — 장비/기계/기구 (13건: COVERED 3 / PARTIAL 5 / MISSING 2 / NV 3)

**engine_coverage**: YES 2 / PARTIAL 3 / NO 8

**COVERED (3건)**: E-01 INSP_DAILY_PRE_WORK, E-02 INSP_MONTHLY, **E-06 worker_licenses.yml**  
**NEEDS_VERIFICATION (3건)**: E-03 INSP_WEEKLY(P2), E-04 INSP_SELF_EXAM_ANNUAL(P1), E-05 INSP_SELF_EXAM_HALFYEAR(P2) — 법령 범위 미확인  
**PARTIAL — MAPPING_MISSING (5건)**: equipment_document_requirements 5/31종(P1), equipment_training_requirements 6/31종(P1), equipment_inspection_requirements 11/31종(P1), E-07 PPE-002 builder없음(P2), E-08 PPE-003 builder없음(P3)  
**MISSING (2건)**:
- E-09 INSP_SCAFF_AFTER_ASSEMBLY — INSPECTION_MISSING — P1 (산안규칙 제59조)
- E-10 화학설비 정기점검 — INSPECTION_MISSING — P2

> E-06 COVERED 근거: worker_licenses.yml 7종 생성, 굴착기(LIC_CONSTRUCTION_MACHINE_EXCAVATOR)·불도저(LIC_CONSTRUCTION_MACHINE_BULLDOZER) 2종 건설기계관리법 원문 VERIFIED. 타워크레인·이동식크레인·지게차·고소작업대·항타기 5종은 유해위험작업취업제한규칙 '자격' 키워드 확인(PARTIAL_VERIFIED) — 법규 별표 원문 미확인.

**연결 compliance**: CC-006, CC-009, CC-010, CC-011, CC-028  
**다음 조치**: ① inspection_types에 INSP_SCAFF_AFTER_ASSEMBLY 등록(P1) ② E-06 미확인 5종 별표 원문 재확인 (타워크레인·지게차 등) ③ equipment 매핑 26종 보완(P1)

### F축 — 작업허가/PTW (9건: COVERED 1 / PARTIAL 8 / MISSING 0 / NV 0)

**engine_coverage**: YES 1 / PARTIAL 1 / NO 7

**COVERED (1건)**: F-01 PTW-001(밀폐공간 작업허가서)  
**PARTIAL — FORM_BUILDER_MISSING (7건)**: PTW-002(화기P1), PTW-003(고소P1), PTW-004(전기P2), PTW-005(굴착P2), PTW-006(방사선P3), PTW-007(중량물P1), PTW-008(임시전기P2)  
**PARTIAL — ENGINE_MISSING (1건)**: F-09 PTW 자동판정 엔진 1/8종만 연결(P1)  
**연결 compliance**: CC-015, CC-016, CC-013  
**다음 조치**: ① PTW-002·003·007 builder 구현(P1) ② safety_decision 엔진에 화기·고소·중량물 PTW 트리거 조건 추가(P1)

### G축 — 보건관리 (9건: COVERED 0 / PARTIAL 3 / MISSING 6 / NV 0)

**engine_coverage**: YES 0 / PARTIAL 1 / NO 8  ← 전 축 중 최저

**COVERED**: 0건 (유일하게 COVERED 없는 축, form_builder 미구현으로 COVERED 불가)  
**PARTIAL (3건)**:
- G-01 CM-003(일반건강진단) builder없음 — P3
- G-02 HM-001(작업환경측정) — FORM_BUILDER_MISSING — **P0** | evidence **VERIFIED** (산안법 제125조 원문 확인)
- G-03 HM-002(특수건강진단) — FORM_BUILDER_MISSING — **P0** | evidence **VERIFIED** (산안법 제130조 원문 확인)

> G-02/G-03 PARTIAL 유지 사유: evidence_status=VERIFIED이나 implementation_status=TODO(form_builder 미구현). audit 조건상 COVERED 전환은 VERIFIED + DONE 모두 필요.

**MISSING (6건)**:
- G-04 유해인자 노출 근로자 관리 대장 — P1
- G-05 온열질환 예방 관리 기록 — P1
- G-06 소음·진동 점검/기록 — DOCUMENT_MISSING,INSPECTION_MISSING — P2
- G-07 분진 점검/기록 — DOCUMENT_MISSING,INSPECTION_MISSING — P2
- G-08 근골격계 부담작업 유해요인 조사 — P2
- G-09 휴게시설 확인 점검표 — P2

**연결 compliance**: 없음 (전 항목 NEEDS_VERIFICATION 또는 법령 확인 완료 후 compliance_clauses 등록 필요)  
**다음 조치**: ① HM-001(산안법 제125조) form_builder 구현 → G-02 COVERED 승격(**P0**) ② HM-002(산안법 제130조) form_builder 구현 → G-03 COVERED 승격(**P0**) ③ 보건관리 엔진 도메인 신설 검토(P1)

### H축 — 화학물질/MSDS (7건: COVERED 1 / PARTIAL 3 / MISSING 3 / NV 0)

**engine_coverage**: YES 0 / PARTIAL 1 / NO 6

**COVERED (1건)**: H-01 WT_CHEMICAL_HANDLING compliance_links 연결(CLINK-024)  
**PARTIAL (3건)**: H-02 PPE-004 builder없음(P3), H-03 CL-009 builder없음(P3), H-04 EDU_MSDS 교육시간 미확인(P2)  
**MISSING (3건)**: H-05 경고표지(P2), H-06 저장·보관·폐기(P2), H-07 환기점검(P2) — 모두 DOCUMENT_MISSING  
**연결 compliance**: CC-012(화학설비), NEEDS_VERIFICATION 多  
**다음 조치**: ① 산안법 제115조 확인 후 경고표지 catalog 등록(P2) ② EDU_MSDS 시간 요건 법령 확인(P2)

### I축 — 보호구/PPE (8건: COVERED 0 / PARTIAL 3 / MISSING 5 / NV 0)

**engine_coverage**: YES 0 / PARTIAL 0 / NO 8

**COVERED**: 0건  
**PARTIAL (3건)**: I-01 PPE-001 builder없음(P2), I-02 CL-007 builder없음(P2), I-03 CL-008 builder없음(P3)  
**MISSING (5건)**: I-04 착용확인기록(P2), I-05 호흡보호구관리(P2), I-06 절연보호구관리(P2), I-07 선정기준표(P3), I-08 교체·폐기기록(P3) — 모두 DOCUMENT_MISSING  
**연결 compliance**: CC-022(보호구 안전인증 고시)  
**다음 조치**: ① PPE-001 builder 구현(P2) ② I-04~I-06 법령 검토 후 catalog 등록(P2)

### J축 — 도급/협력업체 (7건: COVERED 0 / PARTIAL 5 / MISSING 2 / NV 0)

**engine_coverage**: YES 0 / PARTIAL 0 / NO 7

**COVERED**: 0건  
**PARTIAL (5건)**: J-01 CM-001(P2), J-02 CM-002(P2), J-03 ED-005(P2), J-04 SP-002(P3), J-05 CM-006(P3) — 모두 FORM_BUILDER_MISSING  
**MISSING (2건)**: J-06 혼재작업조정기록(P1) — DOCUMENT_MISSING, J-07 현장출입자관리대장(P2) — DOCUMENT_MISSING  
**연결 compliance**: NEEDS_VERIFICATION 多(산안법 제63조~64조 추정)  
**다음 조치**: ① CM-001·002 builder 구현(P2) ② 산안법 제63조 확인 후 혼재작업 기록 등록(P1)

### K축 — 사고/비상대응 (8건: COVERED 0 / PARTIAL 7 / MISSING 1 / NV 0)

**engine_coverage**: YES 0 / PARTIAL 0 / NO 8

**COVERED**: 0건  
**PARTIAL (7건)**: EM-001(P2), EM-002(P2), EM-003(P2), EM-004(P2), EM-005(P3), EM-006(P3), CM-007(P3) — 모두 FORM_BUILDER_MISSING  
**MISSING (1건)**: K-08 비상대응 훈련 기록 — DOCUMENT_MISSING — P1  
**연결 compliance**: NEEDS_VERIFICATION 多  
**다음 조치**: ① EM-001 builder 구현(P2) ② 비상대응 훈련 기록 catalog 등록(P1)

### L축 — 현장 운영관리 (9건: COVERED 0 / PARTIAL 8 / MISSING 1 / NV 0)

**engine_coverage**: YES 0 / PARTIAL 0 / NO 9

**COVERED**: 0건  
**PARTIAL (8건)**: DL-001(P1), DL-002(P2), DL-003(P2), DL-004(P3), DL-005(P3), TS-004(P2), CM-004(P3), SP-001(P3) — 모두 FORM_BUILDER_MISSING  
**MISSING (1건)**: L-09 노동부 점검 대응 체크리스트 — DOCUMENT_MISSING — P1  
**연결 compliance**: NEEDS_VERIFICATION 多  
**다음 조치**: ① DL-001 builder 구현(P1) ② L-09 실무 기반 catalog 등록(P1)

---

## 5. 즉시 작업할 지시문 후보 (법령 확인 완료 후 실행)

> 각 지시문은 단계별 1개씩 실행·검증 원칙 적용. NEEDS_VERIFICATION 표시 항목은 법령 원문 재확인 선행.

```
[지시문 후보 1 — P0, 법령 확인 선행]
건설업 기초안전보건교육을 training_types.yml에 등록하고 연계 서류를 추가한다.

수정 파일: data/masters/safety/training/training_types.yml
추가 내용:
  - training_code: EDU_CONSTRUCTION_BASIC
    name: 건설업 기초안전보건교육
    legal_basis: 산업안전보건법 제31조 (원문 재확인 필요)
    target: 건설업 일용근로자 (최초 현장 취업 시)
    duration_hours: NEEDS_VERIFICATION
    status: NEEDS_VERIFICATION

추가 수정:
  - data/masters/safety/mappings/work_training_requirements.yml에
    WT_CONSTRUCTION_BASIC(신규) → EDU_CONSTRUCTION_BASIC 연결

전제 조건: 산안법 제31조 원문 확인 후 실행
영향: C-06 MISSING → PARTIAL 또는 COVERED 전환 가능
```

```
[지시문 후보 2 — P0, 법령 확인 선행]
작업환경측정·특수건강진단 서류를 document_catalog.yml에 신규 등록한다.

수정 파일: data/masters/safety/documents/document_catalog.yml
추가 내용 (category_code: HM, 보건관리):
  - id: HM-001
    name: 작업환경측정 결과보고서
    legal_basis: 산업안전보건법 제125조 (원문 재확인 필요)
    implementation_status: TODO
  - id: HM-002
    name: 특수건강진단 결과 관리 대장
    legal_basis: 산업안전보건법 제130조 (원문 재확인 필요)
    implementation_status: TODO

추가 수정:
  - compliance_clauses.yml에 CC-029(산안법 제125조), CC-030(제130조) 신규 등록
  - compliance_links.yml에 HM-001→CC-029, HM-002→CC-030 연결 등록

전제 조건: 산안법 제125조·제130조 원문 확인 후 실행
영향: G-02, G-03 MISSING → PARTIAL 전환
```

```
[지시문 후보 3 — P0]
운전원 자격/면허 마스터 파일을 신규 생성하고 equipment_types에 연결한다.

신규 파일: data/masters/safety/worker/worker_licenses.yml
파일 내용 (최소):
  worker_licenses:
    - license_code: LIC_CRANE_OPERATOR
      name: 크레인운전기능사
      required_for: [EQ_CRANE_TOWER, EQ_CRANE_MOB]
      legal_basis: 국가기술자격법 (NEEDS_VERIFICATION)
    - license_code: LIC_FORKLIFT_OPERATOR
      name: 지게차운전기능사
      required_for: [EQ_FORKLIFT]
    - license_code: LIC_CONSTRUCTION_MACHINE
      name: 건설기계조종사 면허
      required_for: [EQ_EXCAV, EQ_BULLDOZER]
    - license_code: LIC_TOWER_CRANE_ADVANCED
      name: 타워크레인 조종 자격
      required_for: [EQ_CRANE_TOWER]

추가 수정:
  - equipment_types.yml 각 장비에 required_license 필드 추가 (P0 장비 우선)

전제 조건: 각 장비별 요구 자격증 법령 확인 선행
영향: E-06 MISSING → COVERED 전환
```

```
[지시문 후보 4 — P1, 법령 확인 선행]
관리자 직무교육 3종을 training_types.yml에 등록한다.

수정 파일: data/masters/safety/training/training_types.yml
추가 내용:
  - training_code: EDU_SAFETY_MANAGER_DUTY
    name: 안전관리자 직무교육
    legal_basis: 산업안전보건법 제17조 (원문 재확인 필요)
    target: 신규 선임 안전관리자 + 능력향상교육
    status: NEEDS_VERIFICATION

  - training_code: EDU_HEALTH_MANAGER_DUTY
    name: 보건관리자 직무교육
    legal_basis: 산업안전보건법 제18조 (원문 재확인 필요)
    status: NEEDS_VERIFICATION

  - training_code: EDU_RESP_MANAGER_DUTY
    name: 안전보건관리책임자 교육
    legal_basis: 산업안전보건법 제15조 (원문 재확인 필요)
    status: NEEDS_VERIFICATION

전제 조건: 산안법 제15조·제17조·제18조 각각 원문 확인 후 실행
영향: D-02, D-03, D-04 MISSING → PARTIAL 전환
```

```
[지시문 후보 5 — P1, 선행 조건 없음]
PTW 화기·고소·중량물 3종 builder를 구현하고 form_registry에 등록한다.

신규 파일:
  - forms/builders/ptw_fire_work_builder.py   (PTW-002 화기작업 허가서)
  - forms/builders/ptw_height_work_builder.py  (PTW-003 고소작업 허가서)
  - forms/builders/ptw_heavy_lift_builder.py   (PTW-007 중량물 인양 허가서)

수정 파일: forms/form_registry.py
  - 3종 builder 등록

수정 파일: data/masters/safety/mappings/work_document_requirements.yml
  - WT_WELDING → PTW-002 연결
  - WT_CRANE_LIFTING → PTW-007 연결

수정 파일: engine/safety_decision/requirements_engine.py (또는 해당 엔진 파일)
  - 화기·고소·중량물 작업 조건 → PTW 자동 트리거 추가

전제 조건: 없음 (실무 관행 기반, 법정 의무 아님)
영향: F-02, F-03, F-04 PARTIAL → COVERED 전환; F-09 엔진 커버리지 향상
```

```
[지시문 후보 6 — P1]
비계 조립 후 점검(INSP_SCAFF_AFTER_ASSEMBLY)을 inspection_types에 등록하고 장비 매핑을 추가한다.

수정 파일: data/masters/safety/inspection/inspection_types.yml
추가:
  - inspection_code: INSP_SCAFF_AFTER_ASSEMBLY
    name: 비계 조립 후 점검
    legal_basis: 산업안전보건기준에 관한 규칙 제59조 (원문 재확인 필요)
    status: NEEDS_VERIFICATION

수정 파일: data/masters/safety/mappings/equipment_inspection_requirements.yml
  - EQ_SCAFF → INSP_SCAFF_AFTER_ASSEMBLY 연결
  - EQ_SYST_SCAFF → INSP_SCAFF_AFTER_ASSEMBLY 연결

전제 조건: 산안규칙 제59조 원문 확인 선행
영향: E-09 MISSING → PARTIAL 전환
```

---

## 6. 법정 의무 가능성이 높은 누락

모든 항목은 법령 원문 미확인 상태이며 NEEDS_VERIFICATION 표기. 법령 근거는 추정이며 단정하지 않는다.

### 6-1. 건설업 기초안전보건교육 — ~~P0 MISSING~~ → **COVERED** (C-06)

- **현황**: EDU_CONSTRUCTION_BASIC training_types.yml 등록 완료. verification_status=confirmed.
- **법령 확인**: 산업안전보건법 제31조 원문 VERIFIED (2026-04-24, 법제처 DRF API)
- **원문 확인 키워드**: 건설업, 기초안전보건교육, 이수, 근로자
- **evidence 파일**: `data/evidence/safety_law_refs/C-06_industrial_safety_health_act_article_31.json`
- **잔여 조치**: 교육이수확인서 서식 연계 (P1, COVERED 유지)

### 6-2. 작업환경측정 — P0 **PARTIAL** (G-02) ← evidence VERIFIED, builder 미구현

- **현황**: HM-001 document_catalog 등록 완료. evidence_status=VERIFIED. form_builder 미구현.
- **법령 확인**: 산업안전보건법 제125조 원문 VERIFIED (2026-04-24, 법제처 DRF API)
- **원문 확인 키워드**: 작업환경측정, 유해인자, 측정, 보존
- **evidence 파일**: `data/evidence/safety_law_refs/G-02_industrial_safety_health_act_article_125.json`
- **잔여 조치**: 작업환경측정 결과보고서 form_builder 구현 후 COVERED 전환 가능

### 6-3. 특수건강진단 — P0 **PARTIAL** (G-03) ← evidence VERIFIED, builder 미구현

- **현황**: HM-002 document_catalog 등록 완료. evidence_status=VERIFIED. form_builder 미구현.
- **법령 확인**: 산업안전보건법 제130조 원문 VERIFIED (2026-04-24, 법제처 DRF API)
- **원문 확인 키워드**: 특수건강진단, 건강진단, 근로자
- **evidence 파일**: `data/evidence/safety_law_refs/G-03_industrial_safety_health_act_article_130.json`
- **잔여 조치**: 특수건강진단 결과 관리 대장 form_builder 구현 후 COVERED 전환 가능

### 6-4. 거푸집·동바리 작업계획서 — P1 MISSING (A-15)

- **현황**: WP-001~WP-014 카탈로그에 없음. work_document_requirements.yml TODO에 언급됨.
- **법령 추정**: 산업안전보건기준에 관한 규칙 제38조 제1항 제13호 추정
- **현재 마스터 기준**: 미확인 — 규칙 제38조 각호 전체 원문 재확인 필요

---

## 7. 교육 관련 누락

### 현재 training_types 10종 구성 및 상태

| training_code | 명칭 | 상태 | 법령 evidence |
|---|---|---|---|
| EDU_REG_WORKER_HALFYEAR | 근로자 정기안전보건교육 | confirmed | — |
| EDU_REG_MANAGER_QUARTERLY | 관리감독자 정기교육 | confirmed | — |
| EDU_ONBOARD_WORKER | 채용 시 안전보건교육 | confirmed | — |
| EDU_TASK_CHANGE | 작업변경 시 안전보건교육 | confirmed | — |
| EDU_SPECIAL_16H | 특별안전보건교육 (16시간) | confirmed | — |
| EDU_SPECIAL_2H | 특별안전보건교육 (단시간) | NEEDS_VERIFICATION | — |
| EDU_TBM | TBM 안전점검 | confirmed | — |
| EDU_CONFINED_SPACE | 밀폐공간 작업 특별교육 | confirmed | — |
| EDU_MSDS | MSDS 교육 | NEEDS_VERIFICATION | — |
| **EDU_CONSTRUCTION_BASIC** | **건설업 기초안전보건교육** | **confirmed** | **VERIFIED (산안법 제31조)** |

### 현재 마스터 기준 미확인 교육 유형

| 항목 | 우선순위 | 법령 추정 |
|---|---|---|
| **건설업 기초안전보건교육** (C-06) | **P0** | 산안법 제31조 |
| 안전관리자 직무교육 (D-02) | P1 | 산안법 제17조 |
| 보건관리자 직무교육 (D-03) | P1 | 산안법 제18조 |
| 안전보건관리책임자 교육 (D-04) | P1 | 산안법 제15조 |
| 안전보건관리담당자 교육 (D-06) | P2 | 산안법 (NEEDS_VERIFICATION) |
| 안전보건조정자 관련 교육 (D-07) | P3 | NEEDS_VERIFICATION |

### 특별교육 매핑 현황 (시행규칙 별표5)

work_training_requirements.yml에 특별교육 연결된 작업유형: WT_EXCAVATION·WT_CRANE_LIFTING·WT_CONFINED_SPACE·WT_MATERIAL_HANDLING·WT_WELDING (5/7종). 별표5 39종 전체 매핑은 현재 마스터 기준 미완성.

---

## 8. 점검 관련 누락

### 현재 inspection_types 8종 상태

| inspection_code | 상태 | 비고 |
|---|---|---|
| INSP_DAILY_PRE_WORK | confirmed | 장비별 법령 조항 연결 |
| INSP_MONTHLY | confirmed | 타워크레인 등 |
| INSP_WEEKLY | NEEDS_VERIFICATION | 적용 장비 범위 미확인 |
| INSP_SELF_EXAM_ANNUAL | NEEDS_VERIFICATION | 별표9 전수 목록 미확인 |
| INSP_SELF_EXAM_HALFYEAR | NEEDS_VERIFICATION | 별표9 적용 장비 미확인 |
| INSP_CONFINED_SPACE_GAS | confirmed | 밀폐공간 가스 측정 |
| INSP_INSULATION_MONTHLY | NEEDS_VERIFICATION | 제301조 세부요건 미확인 |
| INSP_SPECIAL | practical | 법정 근거 없음 |

### 현재 마스터 기준 미확인 점검 유형 (MISSING)

| 항목 | no | 우선순위 | 법령 추정 |
|---|---|---|---|
| 비계 조립 후 점검 (INSP_SCAFF_AFTER_ASSEMBLY) | E-09 | P1 | 산안규칙 제59조 추정 |
| 화학설비 정기점검 | E-10 | P2 | 산안규칙 제224조 이하 추정 |

### equipment_inspection_requirements 커버리지

현재 11종/31종 장비 매핑 완료. 미매핑 20종:  
EQ_MOVSCAFF, EQ_SCISSORLIFT, EQ_SYST_SCAFF, EQ_LADDER_MOV, EQ_VIBRATOR, EQ_CONCRETE_MIXER, EQ_WELDER_ARC, EQ_WELDER_GAS, EQ_GRINDER, EQ_CIRCULAR_SAW, EQ_REBAR_CUTTER, EQ_DRILL, EQ_AIRCOMP, EQ_PILEDRIVER, EQ_SPRAY_GUN, EQ_ROLLER, EQ_ASPHALT_PAVER, EQ_GAS_CYLINDER, EQ_JACKHAMMER, EQ_CONC_PUMP

---

## 9. 보건관리/MSDS/작업환경측정 누락

G축(보건관리)은 감사 대상 12개 축 중 **COVERED 0건, 엔진 YES 0건**으로 커버리지 최하위.

| 항목 | no | 현재 상태 | missing_type | 비고 |
|---|---|---|---|---|
| 작업환경측정 | G-02 | **MISSING P0** | DOCUMENT_MISSING | 법정 의무 추정 (산안법 제125조) |
| 특수건강진단 | G-03 | **MISSING P0** | DOCUMENT_MISSING | 법정 의무 추정 (산안법 제130조) |
| 일반건강진단 | G-01 | PARTIAL (CM-003) | FORM_BUILDER_MISSING | 확인서 양식 등록됨, builder 없음 |
| 유해인자 노출 기록 | G-04 | MISSING P1 | DOCUMENT_MISSING | 현재 마스터 기준 미확인 |
| 온열질환 예방 관리 | G-05 | MISSING P1 | DOCUMENT_MISSING | 건설현장 하절기 필수 (KOSHA 권고 추정) |
| 소음·분진·진동 점검 | G-06,G-07 | MISSING P2 | DOC+INSP_MISSING | 현재 마스터 기준 미확인 |
| 근골격계 부담작업 | G-08 | MISSING P2 | DOCUMENT_MISSING | 적용 대상 확인 필요 |
| MSDS 비치 확인 | H-02 | PARTIAL (PPE-004) | FORM_BUILDER_MISSING | 법정 의무 (산안법 제110조~) |
| MSDS 교육 | H-04 | PARTIAL (EDU_MSDS) | COMPLIANCE_MISSING | 시간 요건 NEEDS_VERIFICATION |
| 화학물질 경고표지 | H-05 | MISSING P2 | DOCUMENT_MISSING | 현재 마스터 기준 미확인 |

---

## 10. 협력업체/도급관리 누락

J축 관련 서류는 document_catalog에 등록됨 (CM-001·CM-002·ED-005·SP-002·CM-006). 모두 builder 미구현. 엔진 YES 0건.

| 항목 | no | 현재 상태 | 비고 |
|---|---|---|---|
| 도급·용역 안전보건 협의서 (CM-002) | J-02 | PARTIAL | 산안법 제64조 근거, builder 없음 |
| 안전보건협의체 회의록 (ED-005) | J-03 | PARTIAL | 산안법 제24조 근거, builder 없음 |
| 협력업체 수준 평가표 (SP-002) | J-04 | PARTIAL | builder 없음 |
| 혼재작업 조정 기록 | J-06 | **MISSING P1** | DOCUMENT_MISSING — 산안법 제63조 추정 |
| 현장 출입자 관리 대장 | J-07 | MISSING P2 | DOCUMENT_MISSING |

---

## 11. 자동판정 엔진 미연결 항목

현재 safety_decision 엔진: 장비/작업유형 → 서류·교육·점검 자동판정 71 PASS.

| 도메인 | 엔진 연결 현황 | missing_type | 비고 |
|---|---|---|---|
| 장비 → 서류 판정 | 5/31종 매핑 | MAPPING_MISSING | 26종 장비 미매핑 |
| 장비 → 교육 판정 | 6/31종 매핑 | MAPPING_MISSING | 25종 장비 미매핑 |
| 장비 → 점검 판정 | 11/31종 매핑 | MAPPING_MISSING | 20종 장비 미매핑 |
| 작업유형 → 서류 | 5/7종 커버 | MAPPING_MISSING | PARTIAL |
| 작업유형 → 교육 | 6/7종 커버 | MAPPING_MISSING | PARTIAL |
| **보건관리 항목 판정** | **0건** | ENGINE_MISSING | 보건 도메인 전혀 미연결 |
| **PTW 자동 트리거** | **1/8종** | ENGINE_MISSING | PTW-001 밀폐공간만 연결 |
| **작업자 자격/면허 확인** | **0건** | DATA_MODEL_MISSING | worker_licenses 마스터 없음 |
| **도급/협력업체 점검** | **0건** | ENGINE_MISSING | 미연결 |
| **사고/비상대응 알림** | **0건** | ENGINE_MISSING | 미연결 |
| compliance link 연결 서류 | 11건/90종 | COMPLIANCE_MISSING | 나머지 79건 미연결 |

---

## 12. 다음 구현 우선순위

### P0 — 잔여 미구현 (2건)

1. **작업환경측정 결과보고서 (G-02, HM-001)**: 산안법 제125조 VERIFIED. form_builder 구현 → `implementation_status: DONE` 갱신 → COVERED 전환
2. **특수건강진단 결과 관리 대장 (G-03, HM-002)**: 산안법 제130조 VERIFIED. form_builder 구현 → `implementation_status: DONE` 갱신 → COVERED 전환

P0 완료 (이번 단계 COVERED 승격):
- ~~건설업 기초안전보건교육 (C-06)~~: COVERED ✓
- ~~운전원 자격/면허 마스터 (E-06)~~: COVERED ✓ (굴착기·불도저 법령 VERIFIED)

### P1 — 단기 대응 (10건 MISSING + 18건 PARTIAL)

5. 관리자 직무교육 3종 (D-02·03·04): 법령 확인 후 training_types 등록
6. 거푸집·동바리 WP-015 (A-15): 법령 확인 후 catalog → builder 구현
7. PTW 3종 builder (F-02·03·04): PTW-002(화기), PTW-003(고소), PTW-007(중량물)
8. 비계 조립 후 점검 (E-09): inspection_types 등록 → EQ_SCAFF 매핑
9. 혼재작업 조정 기록 (J-06): 법령 확인 후 catalog 등록
10. 비상대응 훈련 기록 (K-08): catalog 등록 검토
11. 안전관리 일지 builder (DL-001/L-01): DL-001 builder 구현
12. RA-002 builder 구현 (B-03): 위험성평가 관리 등록부

### P2 — 중기 대응 (주요)

13. equipment_inspection_requirements 나머지 20종 장비 매핑
14. 온열질환·화학물질 경고표지·소음·분진 서류 등록
15. EM-001 builder (산업재해조사표), CM-001·002 builder (도급 관련)
16. PPE-001 builder (보호구 지급 대장)

---

## 부록. 기존 마스터 내 NEEDS_VERIFICATION 항목 현황

(이번 단계 수정 금지 — gap report에만 기록)

| 항목 | no | 마스터 위치 | 내용 |
|---|---|---|---|
| EDU_SPECIAL_2H | — | training_types.yml | 단시간·일용 특별교육 2h 적용 조건 원문 재확인 |
| EDU_MSDS | — | training_types.yml | MSDS 교육 시간 요건 법령 미명시 |
| INSP_WEEKLY | E-03 | inspection_types.yml | 적용 장비 범위 원문 재확인 |
| INSP_SELF_EXAM_ANNUAL | E-04 | inspection_types.yml | 자체검사 대상 별표9 전수 목록 재확인 |
| INSP_SELF_EXAM_HALFYEAR | E-05 | inspection_types.yml | 별표9 적용 장비 미확인 |
| INSP_INSULATION_MONTHLY | — | inspection_types.yml | 제301조 측정 주기 원문 재확인 |
| EQ_CRANE_MOB → WP-007 | A-03 | equipment_document_requirements.yml | 제38조 제1항 제14호 준용 여부 확인 |
| WT_HEAVY_LOAD → WP-005 | A-09 | work_document_requirements.yml | 중량물 기준 및 적용 조건 원문 재확인 |
| CC-003~CC-005 | — | compliance_clauses.yml | 전기공사업법/소방/정보통신 세부 조문 미확인 |
| CC-013 | — | compliance_clauses.yml | 전기 LOTO 제301조 세부조항 확인 |
| CC-020~CC-027 | — | compliance_clauses.yml | NFTC·보호구고시·KOSHA GUIDE 개정번호 미확인 |

---

*이 보고서는 audit_safety_gap.py v3.0 + gap_matrix v3.0 기준. 마스터 수정은 각 지시문 기반으로 별도 진행.*

# Risk Data Roadmap v2
**작성일**: 2026-04-20  
**목적**: 위험성 평가 엔진 고도화를 위한 데이터 자산 구축 전략  
**적용 엔진**: RAG Risk Engine v1.2  
**기준 플랫폼**: KRAS (위험성평가표 자동생성기)

---

## 1. DB 축 정의 및 우선순위

| 우선순위 | DB 축 | 목적 | 엔진 영향 |
|---|---|---|---|
| 1 | work taxonomy | 작업 분류 체계 표준화 | retrieval 정확도 |
| 2 | hazard-action-ppe | 위험요인/조치/보호구 품질 | action 생성 품질 |
| 3 | equipment/material | 장비·자재별 위험 보강 | 입력 확장 |
| 4 | real field cases | 실제 사례 기반 추천 | 향후 AI 품질 |
| 5 | law/standard | 법령 근거 신뢰도 | legal_basis 품질 |
| 6 | condition scenarios | v2 플래그 가중치 보강 | 조건 복합 위험 |

---

## 2. DB별 설계

### [1] Work Taxonomy DB (`data/risk_db/work_taxonomy/`)

**목적**: 뭉뚱그린 작업명을 실제 현장 분류 체계로 표준화  
**핵심 컬럼**: code, name_ko, category, trade_code, risk_level  
**관계**: trade → work_type → sub_work_type (계층 구조)

| 파일 | 레코드 수 | 설명 |
|---|---|---|
| `work_trades.json` | 30 | 대분류 공종 (토공사~환경공사) |
| `work_types.json` | 132 | 중분류 작업유형 (공종별 5개 이상) |
| `work_sub_types.json` | 72 | 세부 단위작업 (고위험 작업 위주) |
| `work_hazards_map.json` | 48 | 작업유형 ↔ 위험요인 매핑 |

**Source**: 건설기술진흥법 시행령 별표 1 공종분류 + KOSHA 안전보건교육 자료

---

### [2] Hazard-Action-PPE DB (`data/risk_db/hazard_action/`)

**목적**: 위험요인/조치문/보호구 품질을 구조적으로 강화  
**핵심 컬럼**: hazard_code, control_text, control_type(engineering/admin/ppe), law_ref  
**조치문 원칙**: 단어가 아닌 "실행 가능한 구문"으로 저장

| 파일 | 레코드 수 | 설명 |
|---|---|---|
| `hazards.json` | 17 | 위험요인 마스터 (FALL~FLYBY) |
| `hazard_controls.json` | 90 | 위험요인별 조치문 (법령 근거 포함) |
| `hazard_ppe.json` | 54 | 위험요인별 보호구 (mandatory 구분) |
| `hazard_work_map.json` | 48 | 위험요인 ↔ 작업유형 매핑 |

**Source**: engine/rag_risk_engine/hazard_classifier.py + 산업안전보건기준에 관한 규칙 + sample_chunks.json

---

### [3] Equipment/Material Risk DB (`data/risk_db/equipment/`)

**목적**: 장비·자재 입력 시 위험과 조치를 자동 보강  
**핵심 컬럼**: code, hazard_codes, key_controls, required_ppe, inspection_points

| 파일 | 레코드 수 | 설명 |
|---|---|---|
| `equipment_master.json` | 31 | 장비 마스터 (비계~아스팔트피니셔) |
| `equipment_hazards.json` | 43 | 장비 ↔ 위험요인 매핑 |
| `equipment_controls.json` | 55 | 장비별 조치문 |
| `material_risks.json` | 20 | 자재별 위험 특성 (철근~PC부재) |

**Source**: 산업안전보건기준에 관한 규칙 (크레인/비계/리프트 관련) + KOSHA GUIDE

---

### [4] Real Field Cases DB (`data/risk_db/real_cases/`)

**목적**: 실제 평가서·사고 사례 기반으로 엔진 품질 및 향후 AI 훈련 기반 마련  
**핵심 컬럼**: trade_code, work_type_code, hazard_codes, control_measures, source_ref (provenance 필수)

| 파일 | 레코드 수 | 설명 |
|---|---|---|
| `real_assessment_cases.json` | 30 | 실사례 (sample_chunks 재구조화 + KOSHA 재해통계 기반) |

**Source**: sample_chunks.json (ids 1~22, 29~33) + KOSHA 건설업 사망사고 재해유형 통계 2023  
**익명화**: 전체 레코드 `anonymized: true`

---

### [5] Law/Standard DB (`data/risk_db/law_standard/`)

**목적**: 법령 근거 기반 결과의 신뢰도 강화  
**핵심 컬럼**: law_code, article_no, clause_title, summary, related_hazard_codes

| 파일 | 레코드 수 | 설명 |
|---|---|---|
| `safety_laws.json` | 43 | 법령 마스터 (산안규칙, 산안법) |
| `law_hazard_map.json` | 58 | 법령 ↔ 위험요인 매핑 |
| `law_worktype_map.json` | 50 | 법령 ↔ 작업유형 매핑 (신규) |

**Source**: 산업안전보건기준에 관한 규칙 (고용노동부), 산업안전보건법

---

### [6] Condition Scenario DB (`data/risk_db/scenario/`)

**목적**: v2 입력 structured_flags가 조합될 때 발생하는 복합 위험 시나리오 정의  
**핵심 컬럼**: trigger_conditions (dict), boosted_hazards, priority, recommended_controls

| 파일 | 레코드 수 | 설명 |
|---|---|---|
| `condition_scenarios.json` | 30 | 조건 복합 시나리오 |

**주요 시나리오**:
- 고소 + 강풍 → FALL, DROP (critical)
- 밀폐공간 + 화기작업 → ASPHYX, FIRE, EXPLO (critical)
- 중장비 + 동시작업 → COLLIDE, DROP (critical)
- 전기작업 + 습윤표면 → ELEC (critical)
- 야간 + 밀폐공간 → ASPHYX, ELEC, FALL (critical)

**Source**: 산업안전보건기준에 관한 규칙 조건별 기준 + KOSHA GUIDE 현장조건별 지침

---

## 3. 수집 전략

### Source 정책
| 소스 유형 | 내용 | 자동화 | 품질 리스크 |
|---|---|---|---|
| 법령(산안규칙/산안법) | 법 조문 직접 구조화 | 불가 | 낮음 (공개 원문) |
| KOSHA GUIDE | 공개 지침 기반 구조화 | 불가 | 낮음 (공개 문서) |
| sample_chunks.json | 기존 KRAS 코퍼스 재파싱 | 가능 | 중간 (데이터 편향) |
| KOSHA 재해통계 | 연간 통계 기반 재구조화 | 불가 | 낮음 (공개 통계) |
| 현장 평가서 | 내부 문서 익명화 후 구조화 | 불가 | 높음 (개인정보) |

### 출처 추적 (Provenance) 정책
- 모든 레코드에 `source` 또는 `source_ref` 필드 필수
- 임의 생성 데이터 금지: source 없는 레코드는 적재 불가
- 현장 문서 사용 시 `anonymized: true` 마킹 필수
- KOSHA 공개 자료는 가이드 번호·년도 명시

---

## 4. 초기 구축 현황 (2026-04-20 기준)

| DB | 파일 | 레코드 수 | 목표 | 달성 여부 |
|---|---|---|---|---|
| work trades | work_trades.json | 30 | 30+ | ✅ |
| work types | work_types.json | 132 | 120+ | ✅ |
| work sub types | work_sub_types.json | 72 | - | ✅ 신규 |
| hazards | hazards.json | 17 | 15+ | ✅ |
| hazard controls | hazard_controls.json | 90 | 80+ | ✅ |
| hazard ppe | hazard_ppe.json | 54 | 50+ | ✅ |
| equipment master | equipment_master.json | 31 | 30+ | ✅ |
| material risks | material_risks.json | 20 | - | ✅ 신규 |
| safety laws | safety_laws.json | 43 | 40+ | ✅ |
| law hazard map | law_hazard_map.json | 58 | 50+ | ✅ |
| law worktype map | law_worktype_map.json | 50 | - | ✅ 신규 |
| real cases | real_assessment_cases.json | 30 | 30+ | ✅ |
| condition scenarios | condition_scenarios.json | 30 | 25+ | ✅ 신규 |

**신규 파일 4개**: work_sub_types, material_risks, law_worktype_map, condition_scenarios

---

## 5. 엔진 연계 포인트

| DB | 연계 포인트 | 상태 |
|---|---|---|
| work taxonomy | retrieval boost / query expansion | 후속 구현 필요 |
| hazard-action DB | action 후보 보강 (hazard_controls 직접 참조) | 현재 연결 가능 |
| equipment/material DB | equipment 입력 시 hazard_codes 보강 | 후속 구현 필요 |
| real case DB | 유사사례 검색 기반 추천 | 후속 구현 필요 (임베딩 필요) |
| law DB | legal_basis_candidates 보강 | 현재 연결 가능 (law_ref 직접 참조) |
| condition scenarios DB | v2 structured_flag 가중치 보강 | 후속 구현 필요 |

### 현재 연결 가능
- `hazard_controls.json` → 엔진의 action 후보 필터링/보강
- `safety_laws.json` → legal_basis_candidates 검증

### 후속 구현 필요
- work taxonomy → query expansion 시 trade/work_type 매핑
- condition_scenarios → v2 flags 감지 시 위험 가중치 적용
- equipment/material → 입력 파싱 후 hazard_codes 보강
- real_cases → 임베딩 벡터화 후 유사사례 검색

### 데이터 부족 (추가 수집 필요)
- real_cases: 현재 30건 → 목표 100건 이상
- 실제 현장 평가서(익명화) 추가 수집 필요
- KOSHA GUIDE 원문 기반 구조화 확대

---

## 6. 다음 단계

### Phase 1 (완료): 데이터 자산 초기 구축
- 6개 DB 축 파일 구축 완료
- 신규 파일 4개 생성

### Phase 2 (다음): 엔진 연계 구현
- condition_scenarios → 엔진 가중치 로직 구현
- work_taxonomy → query expansion 파이프라인 연결
- material_risks → 입력 파싱 후 자동 hazard 보강

### Phase 3: 데이터 확대
- real_cases 100건 이상 확보
- KOSHA 청크 DB 기반 hazard_controls 자동 추출
- 실제 현장 평가서 익명화 후 구조화

### Phase 4: AI 연동
- real_cases 임베딩 벡터화
- 유사사례 검색 API 구축
- 평가 품질 자동 평가 루프

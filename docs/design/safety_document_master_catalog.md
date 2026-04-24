# 안전 관련 법적·실무 서류 마스터 카탈로그

**작성일**: 2026-04-24  
**법령 기준**: 산업안전보건법(이하 "법"), 산업안전보건기준에 관한 규칙(이하 "기준규칙"), 산업안전보건법 시행규칙(이하 "시행규칙"), 중대재해처벌법  
**원칙**: 법정 의무와 실무 서류 명확히 분리 / 장비 사용계획서는 별도 파일(equipment_workplan_master_catalog.md) 관리

---

## 범례

| 코드 | 의미 |
|------|------|
| `[법정]` | 법령·고시에서 작성·보존 의무 명시 |
| `[실무필수]` | 법령 명시 없으나 현장 관행·원청 요구로 사실상 필수 |
| `[선택]` | 선택적 보강 서류 |
| `DONE` | builder 구현 완료 |
| `P0` | 다음 구현 1순위 |
| `P1` | 단기 구현 (3개월) |
| `P2` | 중기 구현 (6개월) |
| `P3` | 장기 구현 (1년+) |
| `OUT` | 현 범위 외 (복잡도/분량 초과) |

---

## 현황 요약

| 대분류 | 코드 접두 | 문서 수 | 법정 의무 | 실무 필수 | 구현 완료 |
|--------|----------|--------|----------|---------|---------|
| 1. 법정 작업계획서 | WP | 14 | 14 | 0 | 3 |
| 2. 장비 사용계획서 | EQ | → 별도 파일 | | | 2 |
| 3. 위험성평가 관련 | RA | 6 | 2 | 4 | 1 |
| 4. 안전보건교육 관련 | ED | 5 | 3 | 2 | 1 |
| 5. 작업허가서/PTW | PTW | 8 | 3 | 5 | 0 |
| 6. 일일 안전관리 | DL | 5 | 1 | 4 | 0 |
| 7. 점검표/체크리스트 | CL | 10 | 2 | 8 | 0 |
| 8. 보호구/장비 반입 | PPE | 4 | 1 | 3 | 0 |
| 9. 협력업체/근로자 관리 | CM | 7 | 3 | 4 | 0 |
| 10. 사고/비상대응 | EM | 6 | 3 | 3 | 0 |
| 11. 공종별 특화 | TS | 5 | 4 | 1 | 0 |
| 12. 실무 보강 | SP | 4 | 0 | 4 | 0 |
| **합계** | | **74** | **36** | **38** | **7** |

---

## 대분류 1. 법정 작업계획서

**근거**: 기준규칙 제38조 제1항 별표4 — 사업주는 다음 각 호의 작업 전 사전조사 후 작업계획서 작성 의무

### WP-001: 굴착 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-001 |
| document_name | 굴착 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 굴착·지반 작업 |
| minor_category | 일반 굴착 (2m 이상) |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제6호, 제82조 제1항 |
| target_work | 굴착면 높이 2m 이상 굴착 작업 |
| target_equipment | 굴착기, 백호, 포클레인 |
| required_fields | excavation_method, earth_retaining, excavation_machine, soil_disposal, water_disposal, work_method, emergency_measure |
| inspection_items | 굴착면 상태, 흙막이 지보공 변형 여부, 용수 처리 현황, 장비 이동 경로 |
| route_or_drawing_required | true (굴착 범위 도면) |
| signature_required | true |
| builder_priority | DONE |
| implementation_status | **DONE** (excavation_workplan) |

---

### WP-002: 터널 굴착 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-002 |
| document_name | 터널 굴착 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 굴착·지반 작업 |
| minor_category | 터널 굴착 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제7호, 제46조 이하 |
| target_work | 터널 굴착 작업 전반 |
| target_equipment | TBM, NATM 장비, 발파 장비 |
| required_fields | tunnel_method, tunnel_support, tunnel_water, tunnel_ventilation, work_method, emergency_measure |
| inspection_items | 지보공 상태, 용수 처리, 환기량, 가스 농도, 조명 상태 |
| route_or_drawing_required | true (터널 단면도, 지보공 배치도) |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### WP-003: 건축물 해체 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-003 |
| document_name | 건축물 등의 해체 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 해체·철거 작업 |
| minor_category | 건축물·구조물 해체 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제9호, 제52조~제55조 |
| target_work | 건축물·교량·콘크리트 구조물 해체 |
| target_equipment | 해체기, 압쇄기, 크레인 |
| required_fields | demolition_method, demolition_order, protective_facilities, site_contact, waste_handling, dust_control, emergency_measure |
| inspection_items | 해체 순서 준수, 방호망 설치 상태, 비산먼지 대책, 유해물질(석면) 여부 |
| route_or_drawing_required | true (해체 순서 도면) |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### WP-004: 교량 설치·해체·변경 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-004 |
| document_name | 교량 설치·해체·변경 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 구조물 설치·해체 |
| minor_category | 교량 공사 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제8호 |
| target_work | 교량 상부·하부 구조물 설치·해체·변경 |
| target_equipment | 크레인, 가이드레인, 가설 구조물 |
| required_fields | bridge_structure, work_method, work_sequence, safety_measures, emergency_measure |
| inspection_items | 구조물 안전성, 작업 순서, 추락 방지, 비계 설치 상태 |
| route_or_drawing_required | true (교량 구조도, 작업 순서도) |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### WP-005: 중량물 취급 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-005 |
| document_name | 중량물 취급 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 중량물·양중 작업 |
| minor_category | 중량물 취급 (100kg 이상) |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제10호, 제39조 |
| target_work | 총 중량 100kg 이상 물체를 2인 이상 취급하는 작업 |
| target_equipment | 지게차, 이동식크레인, 호이스트, 윈치 |
| required_fields | lifting_machine, lifting_sequence, load_weight, fall_prevention, ground_settlement, emergency_measure |
| inspection_items | 줄걸이 상태, 와이어로프 마모, 지반 침하, 인양 경로 장애물 |
| route_or_drawing_required | true (인양 경로 도면) |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### WP-006: 타워크레인 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-006 |
| document_name | 타워크레인 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 양중·크레인 작업 |
| minor_category | 타워크레인 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제1호, 제142조 이하 |
| target_work | 타워크레인을 사용하는 모든 작업 |
| target_equipment | 타워크레인 (고정식·이동식·클라이밍) |
| required_fields | crane_type, crane_capacity, work_method, work_sequence, travel_route, safety_measures, guide_worker, emergency_measure |
| inspection_items | 설치·해체 계획, 작업반경, 충돌 방지, 과부하 방지 장치, 기상 조건 |
| route_or_drawing_required | true (작업반경도, 충돌 방지 구역도) |
| signature_required | true |
| builder_priority | P0 |
| implementation_status | PENDING |

---

### WP-007: 이동식 크레인 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-007 |
| document_name | 이동식 크레인 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 양중·크레인 작업 |
| minor_category | 이동식크레인·카고크레인 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제14호, 제134조 이하 |
| target_work | 이동식 크레인(카고크레인 포함) 사용 작업 |
| target_equipment | 유압식 이동크레인, 카고크레인, 트럭크레인 |
| required_fields | crane_type, crane_capacity, load_weight, work_method, travel_route, outrigger_setup, ground_condition, emergency_measure |
| inspection_items | 아웃트리거 설치 상태, 지반 지지력, 작업반경 내 장애물, 줄걸이 방법, 신호수 배치 |
| route_or_drawing_required | true (이동 경로, 작업반경도) |
| signature_required | true |
| builder_priority | P0 |
| implementation_status | PENDING |

---

### WP-008: 차량계 건설기계 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-008 |
| document_name | 차량계 건설기계 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 차량계 건설기계 |
| minor_category | 건설기계 일반 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제3호, 제170조 이하 |
| target_work | 차량계 건설기계를 사용하는 작업 |
| target_equipment | 불도저, 굴착기, 로더, 롤러, 모터그레이더, 스크레이퍼 |
| required_fields | machine_type, machine_capacity, work_method, travel_route_text, speed_limit, guide_worker_required, emergency_measure |
| inspection_items | 운행경로 장애물, 유도자 배치, 제한속도 표지, 후방경보 장치 |
| route_or_drawing_required | true (운행경로도) |
| signature_required | true |
| builder_priority | DONE |
| implementation_status | **DONE** (vehicle_construction_workplan) |

---

### WP-009: 차량계 하역운반기계 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-009 |
| document_name | 차량계 하역운반기계 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 차량계 하역운반기계 |
| minor_category | 하역운반기계 일반 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제2호, 제2항, 제179조~제182조 |
| target_work | 차량계 하역운반기계(지게차, 구내운반차, 화물자동차 포함)를 사용하는 작업 |
| target_equipment | 지게차, 구내운반차, 화물자동차, 컨베이어 |
| required_fields | machine_type, machine_max_load, work_method, travel_route_text, speed_limit, pedestrian_separation, guide_worker_required, emergency_measure |
| inspection_items | 운행경로 보행자 분리, 제한속도 준수, 작업 전 점검 8개 항목(제179조), 유도자 배치 |
| route_or_drawing_required | true (운행경로도) |
| signature_required | true |
| builder_priority | DONE |
| implementation_status | **DONE** (material_handling_workplan) |

---

### WP-010: 항타기·항발기 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-010 |
| document_name | 항타기·항발기 사용 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 기초·말뚝 공사 |
| minor_category | 항타기·항발기·천공기 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제12호, 제186조 이하 |
| target_work | 항타기·항발기·천공기를 사용하는 작업 |
| target_equipment | 항타기, 항발기, 어스오거, 천공기 |
| required_fields | machine_type, machine_capacity, work_method, pile_sequence, guide_worker_required, emergency_measure |
| inspection_items | 기계 설치 상태, 와이어로프 마모, 과부하 방지, 말뚝 박기 순서 |
| route_or_drawing_required | true (항타 위치도) |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### WP-011: 전기 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-011 |
| document_name | 전기 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 전기·전력 작업 |
| minor_category | 고압·저압 전기 작업 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항, 제301조 이하 |
| target_work | 전기설비 설치·수리·점검 등 전기 작업 |
| target_equipment | 변압기, 배전반, 전선로 |
| required_fields | voltage_class, work_method, isolation_method, lockout_tagout, ppe_required, emergency_measure |
| inspection_items | 전원 차단 확인, LOTO 적용 여부, 절연 보호구 착용, 잔류 전하 방전 |
| route_or_drawing_required | true (단선도, 전기 계통도) |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### WP-012: 궤도 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-012 |
| document_name | 궤도 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 궤도·철도 작업 |
| minor_category | 궤도 부설·유지보수 |
| legal_required | true |
| practical_required | false |
| legal_basis | 기준규칙 제38조 제1항 제11호 |
| target_work | 궤도(레일) 부설·유지보수 작업 |
| target_equipment | 궤도작업차, 레일 설치 장비 |
| required_fields | track_section, work_method, train_passage_plan, signal_system, emergency_measure |
| inspection_items | 열차 접근 경보, 작업 구간 신호, 궤도 안정성 |
| route_or_drawing_required | true (궤도 배치도) |
| signature_required | true |
| builder_priority | P3 |
| implementation_status | PENDING |

---

### WP-013: 화학설비 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-013 |
| document_name | 화학설비·부속설비 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 화학·위험물 작업 |
| minor_category | 화학설비 정비·내부 청소 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제4호, 제224조 이하 |
| target_work | 화학설비 및 그 부속설비에서 위험물질을 다루거나 내부 청소하는 작업 |
| target_equipment | 반응기, 저장탱크, 배관설비 |
| required_fields | facility_name, hazmat_list, work_method, purge_method, gas_detection, ppe_required, emergency_measure |
| inspection_items | 잔류 위험물 제거, 가스 농도 측정, 환기 확보, 화기 통제 |
| route_or_drawing_required | true (P&ID, 설비 배치도) |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### WP-014: 밀폐공간 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | WP-014 |
| document_name | 밀폐공간 작업계획서 |
| major_category | 법정 작업계획서 |
| middle_category | 밀폐공간 작업 |
| minor_category | 맨홀·탱크·피트 등 밀폐공간 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제619조~제626조 (밀폐공간 작업 프로그램), 제38조 참조 |
| target_work | 산소결핍·유해가스 위험이 있는 밀폐공간 작업 |
| target_equipment | 환기 장비, 가스 감지기, 구조용 로프 |
| required_fields | confined_space_location, gas_types, ventilation_method, entry_permit_no, emergency_rescue, ppe_required, emergency_measure |
| inspection_items | 산소 농도(18% 이상), 유해가스 농도, 환기 상태, 감시인 배치, 구조 장비 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P0 |
| implementation_status | PENDING |

---

## 대분류 3. 위험성평가 관련 서류

**근거**: 법 제36조, 시행규칙 제37조, 고용노동부고시 제2023-19호

### RA-001: 위험성평가표 (본표)

| 항목 | 내용 |
|------|------|
| document_id | RA-001 |
| document_name | 위험성평가표 (실시표) |
| major_category | 위험성평가 관련 |
| middle_category | 위험성평가 기록 |
| minor_category | 평가 결과 본표 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제36조, 시행규칙 제37조, 고용노동부고시 제2023-19호 |
| target_work | 모든 사업장 전 작업 공정 |
| target_equipment | 해당 없음 |
| required_fields | company_name, assessment_type, assessment_date, work_type, hazard_type, hazard_detail, current_measure, possibility, severity, risk_level, improvement |
| inspection_items | 유해·위험요인 식별, 위험성 결정, 감소 대책, 실시 주기 준수 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | DONE |
| implementation_status | **DONE** (risk_assessment) |

---

### RA-002: 위험성평가 등록부

| 항목 | 내용 |
|------|------|
| document_id | RA-002 |
| document_name | 위험성평가 관리 등록부 |
| major_category | 위험성평가 관련 |
| middle_category | 위험성평가 관리 |
| minor_category | 평가 이력 관리 |
| legal_required | false |
| practical_required | true |
| legal_basis | 시행규칙 제37조 (기록 보존 3년) — 등록부 형식은 관행 |
| target_work | 모든 공정 평가 이력 집계 |
| target_equipment | 해당 없음 |
| required_fields | eval_no, eval_date, eval_type, process_name, risk_level_summary, improvement_status, manager, due_date |
| inspection_items | 평가 주기 준수, 수시 평가 트리거 사유, 개선 조치 완료 여부 |
| route_or_drawing_required | false |
| signature_required | false |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### RA-003: 위험성평가 회의록

| 항목 | 내용 |
|------|------|
| document_id | RA-003 |
| document_name | 위험성평가 참여 회의록 |
| major_category | 위험성평가 관련 |
| middle_category | 위험성평가 기록 |
| minor_category | 근로자 참여 기록 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제36조 제3항 (근로자 참여 보장) |
| target_work | 위험성평가 실시 시점 |
| target_equipment | 해당 없음 |
| required_fields | meeting_date, meeting_location, attendees, agenda, worker_opinion, reflection_result |
| inspection_items | 참석자 서명, 근로자 의견 반영 여부, 본표와의 세트 보관 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### RA-004: TBM (작업 전 안전점검) 일지

| 항목 | 내용 |
|------|------|
| document_id | RA-004 |
| document_name | TBM (Tool Box Meeting) 일지 |
| major_category | 위험성평가 관련 |
| middle_category | 일일 위험성평가 |
| minor_category | 작업 전 안전점검회의 |
| legal_required | false |
| practical_required | true |
| legal_basis | 고용노동부고시 제2023-19호 (상시평가 실시 권고), 중대재해처벌법 시행령 제4조 |
| target_work | 건설·제조·서비스업 일일 작업 개시 전 |
| target_equipment | 해당 없음 |
| required_fields | tbm_date, tbm_time, work_location, today_work, hazard_points, safety_instructions, special_notes, attendees |
| inspection_items | 기상 조건, 당일 위험요인, 안전수칙 공유, 출석 서명 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P0 |
| implementation_status | PENDING |

---

### RA-005: 위험성평가 실시규정

| 항목 | 내용 |
|------|------|
| document_id | RA-005 |
| document_name | 위험성평가 실시 규정 |
| major_category | 위험성평가 관련 |
| middle_category | 위험성평가 관리 |
| minor_category | 운영 규정 문서 |
| legal_required | false |
| practical_required | true |
| legal_basis | 고용노동부고시 제2023-19호 제9조 (실시규정 작성 권고) |
| target_work | 사업장 전체 위험성평가 관리 |
| target_equipment | 해당 없음 |
| required_fields | purpose, scope, responsible_persons, evaluation_method, frequency, preservation_period |
| inspection_items | 평가 주기·절차·담당자 명시 여부 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P3 |
| implementation_status | PENDING |

---

### RA-006: 위험성평가 결과 공지문

| 항목 | 내용 |
|------|------|
| document_id | RA-006 |
| document_name | 위험성평가 결과 근로자 공지문 |
| major_category | 위험성평가 관련 |
| middle_category | 위험성평가 공지 |
| minor_category | 게시용 요약본 |
| legal_required | false |
| practical_required | true |
| legal_basis | 고용노동부고시 제2023-19호 (공지 권고) |
| target_work | 위험성평가 완료 후 현장 게시 |
| target_equipment | 해당 없음 |
| required_fields | process_name, main_hazards, safety_rules, posting_date |
| inspection_items | 근로자 접근 가능 위치 게시 여부 |
| route_or_drawing_required | false |
| signature_required | false |
| builder_priority | P3 |
| implementation_status | PENDING |

---

## 대분류 4. 안전보건교육 관련 서류

**근거**: 법 제29조~제31조, 시행규칙 제26조~제33조, 별표4~별표5

### ED-001: 안전보건교육 교육일지

| 항목 | 내용 |
|------|------|
| document_id | ED-001 |
| document_name | 안전보건교육 교육일지 |
| major_category | 안전보건교육 관련 |
| middle_category | 정기·특별 교육 |
| minor_category | 교육 실시 기록 |
| legal_required | true |
| practical_required | true |
| legal_basis | 시행규칙 제32조, 별지 제52호의2서식 |
| target_work | 정기교육·채용 시 교육·작업내용 변경 시 교육·특별교육 |
| target_equipment | 해당 없음 |
| required_fields | education_type, education_date, education_location, education_duration_hours, education_target_job, instructor_name, instructor_qualification, subjects, attendees, confirmer_name, confirmer_role |
| inspection_items | 법정 시간 준수, 강사 자격, 수강자 서명, 교육 내용 법정 과목 포함 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | DONE |
| implementation_status | **DONE** (education_log) |

---

### ED-002: 안전보건교육 계획서

| 항목 | 내용 |
|------|------|
| document_id | ED-002 |
| document_name | 연간 안전보건교육 계획서 |
| major_category | 안전보건교육 관련 |
| middle_category | 교육 계획 |
| minor_category | 연간 계획 |
| legal_required | false |
| practical_required | true |
| legal_basis | 법 제29조 (교육 의무), 시행규칙 별표4 (교육 시간·내용) |
| target_work | 연초 교육 계획 수립 |
| target_equipment | 해당 없음 |
| required_fields | year, education_schedule, education_types, target_persons, instructor_plan, budget |
| inspection_items | 법정 교육 유형 전체 포함 여부, 시간 계획 적정성 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### ED-003: 특별교육 교육일지

| 항목 | 내용 |
|------|------|
| document_id | ED-003 |
| document_name | 특별 안전보건교육 교육일지 |
| major_category | 안전보건교육 관련 |
| middle_category | 특별 교육 |
| minor_category | 고위험 작업 특별교육 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제29조 제3항, 시행규칙 별표5 (특별교육 대상 및 내용) |
| target_work | 별표5 지정 39개 고위험 작업 종사자 |
| target_equipment | 해당 없음 |
| required_fields | education_type, target_work_type, education_date, education_location, education_duration_hours, instructor_name, attendees, confirmer_name |
| inspection_items | 특별교육 대상 작업 해당 여부, 16시간 이상 교육 시간, 강사 자격 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### ED-004: 안전보건관리자 교육 이수 확인서

| 항목 | 내용 |
|------|------|
| document_id | ED-004 |
| document_name | 안전보건관리자 직무교육 이수 확인서 |
| major_category | 안전보건교육 관련 |
| middle_category | 관리자 교육 |
| minor_category | 직무교육 이수 증빙 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제32조, 시행규칙 제40조 |
| target_work | 안전보건관리자 선임 후 3개월 내 직무교육 |
| target_equipment | 해당 없음 |
| required_fields | manager_name, manager_role, training_institution, training_period, training_hours, certificate_no |
| inspection_items | 이수 기간(3개월 내), 교육 기관 인가 여부, 주기적 보수교육 |
| route_or_drawing_required | false |
| signature_required | false |
| builder_priority | P3 |
| implementation_status | PENDING |

---

### ED-005: 안전보건협의체 회의록

| 항목 | 내용 |
|------|------|
| document_id | ED-005 |
| document_name | 안전보건협의체(안전보건위원회) 회의록 |
| major_category | 안전보건교육 관련 |
| middle_category | 안전보건위원회 |
| minor_category | 분기 회의 기록 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제24조, 시행규칙 제37조 이하 |
| target_work | 상시근로자 100인 이상 사업장 분기 1회 |
| target_equipment | 해당 없음 |
| required_fields | meeting_date, attendees, agenda, resolution, next_action |
| inspection_items | 분기 개최 여부, 근로자위원 참여, 의결 사항 이행 여부 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

## 대분류 5. 작업허가서 / PTW (Permit to Work)

**근거**: PSM(공정안전보고서) 필수 요소, 건설업 원청 관행, 밀폐공간·화기 법정 근거

### PTW-001: 밀폐공간 작업 허가서

| 항목 | 내용 |
|------|------|
| document_id | PTW-001 |
| document_name | 밀폐공간 작업 허가서 |
| major_category | 작업허가서/PTW |
| middle_category | 밀폐공간 |
| minor_category | 산소결핍·유해가스 위험 공간 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제619조~제626조 |
| target_work | 맨홀·탱크·피트·하수도·저장고 내부 작업 |
| required_fields | space_location, gas_measurement_result, ventilation_confirm, monitor_assigned, rescue_equipment, entry_time, exit_time, permit_issuer |
| inspection_items | 산소 18% 이상, 유해가스 허용기준 이하, 환기 장치 가동, 감시인 배치, 구조 장비 비치 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P0 |
| implementation_status | PENDING |

---

### PTW-002: 화기작업 허가서

| 항목 | 내용 |
|------|------|
| document_id | PTW-002 |
| document_name | 화기작업 허가서 (Hot Work Permit) |
| major_category | 작업허가서/PTW |
| middle_category | 화기·용접 작업 |
| minor_category | 용접·용단·그라인딩 등 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제241조~제252조 (화재·폭발 예방), PSM 안전운전계획 필수 요소 |
| target_work | 인화성·가연성 물질 주변 용접·용단·절단·가열 작업 |
| required_fields | work_location, fire_hazard_check, fire_extinguisher_confirm, flammable_clearance, work_duration, fire_watch_assigned, permit_issuer |
| inspection_items | 가연성 물질 제거(반경 10m), 소화기 비치, 불꽃 비산 방지, 화재 감시자 배치 30분 이상 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### PTW-003: 고소작업 허가서

| 항목 | 내용 |
|------|------|
| document_id | PTW-003 |
| document_name | 고소작업 허가서 |
| major_category | 작업허가서/PTW |
| middle_category | 고소·추락 위험 작업 |
| minor_category | 2m 이상 고소 작업 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제42조 (추락 방호조치), PSM 요소 |
| target_work | 높이 2m 이상 작업 (비계, 사다리, 고소작업대 포함) |
| required_fields | work_location, work_height, fall_protection_method, ppe_confirmed, scaffold_inspection, permit_issuer |
| inspection_items | 안전난간·안전망 설치 여부, 안전대 착용 확인, 비계 점검 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### PTW-004: 전기작업 허가서

| 항목 | 내용 |
|------|------|
| document_id | PTW-004 |
| document_name | 전기작업 허가서 (LOTO) |
| major_category | 작업허가서/PTW |
| middle_category | 전기 작업 |
| minor_category | 전원 차단·LOTO 작업 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제316조 이하 (LOTO), 전기작업 계획서와 연계 |
| target_work | 활선 전기설비 점검·수리 또는 전원 차단 후 작업 |
| required_fields | equipment_name, voltage, isolation_point, loto_confirmed, residual_charge_check, ppe_confirmed, permit_issuer |
| inspection_items | 전원 완전 차단 확인, LOTO 태그 부착, 잔류 전하 방전, 절연 장갑 착용 |
| route_or_drawing_required | true (단선도) |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### PTW-005: 굴착·굴삭 작업 허가서

| 항목 | 내용 |
|------|------|
| document_id | PTW-005 |
| document_name | 굴착 작업 허가서 |
| major_category | 작업허가서/PTW |
| middle_category | 굴착·지반 작업 |
| minor_category | 지하매설물 확인 후 굴착 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제38조, 제82조 이하 (지하매설물 확인 의무) |
| target_work | 매설 배관·전선 주변 굴착 작업 |
| required_fields | excavation_location, underground_utilities_check, excavation_depth, shoring_plan, permit_issuer |
| inspection_items | 지하매설물 탐사 완료 여부, 흙막이 설치 계획, 인접 구조물 영향 |
| route_or_drawing_required | true (지하매설물 도면) |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### PTW-006: 방사선 작업 허가서

| 항목 | 내용 |
|------|------|
| document_id | PTW-006 |
| document_name | 방사선 투과검사 작업 허가서 |
| major_category | 작업허가서/PTW |
| middle_category | 방사선·비파괴 검사 |
| minor_category | 방사선 투과검사 (RT) |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제573조 이하, 원자력안전법 관련 |
| target_work | 용접부 방사선 투과검사 |
| required_fields | work_location, radiation_source, controlled_area, exposure_time, dosimeter_check, evacuation_plan, permit_issuer |
| inspection_items | 통제구역 설정·표시, 선량계 착용, 비작업자 대피 확인 |
| route_or_drawing_required | true (통제구역도) |
| signature_required | true |
| builder_priority | P3 |
| implementation_status | PENDING |

---

### PTW-007: 중량물 인양 허가서

| 항목 | 내용 |
|------|------|
| document_id | PTW-007 |
| document_name | 중량물 인양 작업 허가서 (Lift Permit) |
| major_category | 작업허가서/PTW |
| middle_category | 중량물·크레인 인양 |
| minor_category | Critical Lift (복합 인양 포함) |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제135조 이하, WP-005·WP-007 계획서와 연계 |
| target_work | 크레인을 사용한 중량물 인양 (특히 Critical Lift) |
| required_fields | load_weight, crane_type, crane_capacity, rigging_method, lift_radius, ground_condition, signal_person, permit_issuer |
| inspection_items | SWL 준수, 줄걸이 상태, 지반 지지력, 신호수 배치, 위험 구역 통제 |
| route_or_drawing_required | true (리프팅 계획도) |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### PTW-008: 임시전기 연결 허가서

| 항목 | 내용 |
|------|------|
| document_id | PTW-008 |
| document_name | 임시전기 설치·연결 허가서 |
| major_category | 작업허가서/PTW |
| middle_category | 임시전기·전력 |
| minor_category | 건설 현장 임시전기 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제301조 이하, 건설 현장 임시전기 가이드라인 |
| target_work | 건설 현장 임시 배전반·전선 설치 작업 |
| required_fields | installation_location, voltage, circuit_type, grounding_check, overload_protection, inspector_name, permit_issuer |
| inspection_items | 접지 설치, 누전차단기 설치, 방수·방호 처리, 과부하 보호 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

## 대분류 6. 일일 안전관리 서류

### DL-001: 안전관리 일지

| 항목 | 내용 |
|------|------|
| document_id | DL-001 |
| document_name | 안전관리 일지 (현장 일일 점검 기록) |
| major_category | 일일 안전관리 |
| middle_category | 현장 안전 일지 |
| minor_category | 일일 점검 기록 |
| legal_required | false |
| practical_required | true |
| legal_basis | 중대재해처벌법 시행령 제4조 (안전보건관리체계 구축 의무) |
| target_work | 건설·제조 현장 매일 |
| required_fields | date, weather, site_manager, today_work_summary, hazard_noted, corrective_action, special_notes |
| inspection_items | 위험 요인 기록, 즉시 조치 사항, 다음날 예정 작업 위험 예고 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### DL-002: 관리감독자 업무 일지

| 항목 | 내용 |
|------|------|
| document_id | DL-002 |
| document_name | 관리감독자 안전보건 업무 일지 |
| major_category | 일일 안전관리 |
| middle_category | 관리감독자 기록 |
| minor_category | 감독 이행 증빙 |
| legal_required | false |
| practical_required | true |
| legal_basis | 법 제16조 (관리감독자 직무), 중대재해처벌법 시행령 제4조 |
| target_work | 매일 작업 지휘 및 점검 |
| required_fields | date, supervisor_name, work_location, work_type, safety_check_items, unsafe_condition_noted, action_taken |
| inspection_items | 작업 지시 내용, 위험 발견 즉시 조치, TBM 실시 확인 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### DL-003: 안전순찰 점검 일지

| 항목 | 내용 |
|------|------|
| document_id | DL-003 |
| document_name | 안전순찰 점검 일지 |
| major_category | 일일 안전관리 |
| middle_category | 현장 순찰 기록 |
| minor_category | 정기 순찰 |
| legal_required | false |
| practical_required | true |
| legal_basis | 법 제17조 (안전관리자 직무) |
| target_work | 현장 순찰 (1일 1회 이상) |
| required_fields | patrol_date, patrol_time, patrol_route, deficiency_found, correction_required, corrected_by |
| inspection_items | 순찰 구간, 미시정 사항 이월 관리 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### DL-004: 기상 조건 기록 일지

| 항목 | 내용 |
|------|------|
| document_id | DL-004 |
| document_name | 기상 조건 기록 일지 |
| major_category | 일일 안전관리 |
| middle_category | 기상·환경 기록 |
| minor_category | 악천후 작업 중지 기록 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제37조 (악천후 시 작업 중지 의무) |
| target_work | 기상 조건에 따른 작업 가능 여부 판단 |
| required_fields | date, wind_speed, precipitation, temperature, visibility, work_status, stop_reason |
| inspection_items | 10m/s 이상 강풍, 강설·강우, 안개 조건 기록 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P3 |
| implementation_status | PENDING |

---

### DL-005: 작업 전 안전 확인서 (Safety Observation)

| 항목 | 내용 |
|------|------|
| document_id | DL-005 |
| document_name | 작업 전 안전 확인서 |
| major_category | 일일 안전관리 |
| middle_category | 작업 전 확인 |
| minor_category | 개인별 작업 전 확인 |
| legal_required | false |
| practical_required | true |
| legal_basis | 중대재해처벌법 시행령 제4조, 원청 안전관리 요구사항 |
| target_work | 작업자 개인 작업 개시 전 자가 점검 |
| required_fields | worker_name, date, work_type, ppe_confirmed, hazard_check, supervisor_briefing |
| inspection_items | PPE 착용, 위험 요인 인지, 작업 지시 수령 확인 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P3 |
| implementation_status | PENDING |

---

## 대분류 7. 점검표 / 체크리스트

### CL-001: 비계·동바리 설치 점검표

| 항목 | 내용 |
|------|------|
| document_id | CL-001 |
| document_name | 비계·동바리 설치 점검표 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제57조~제75조, 제88조~제94조 |
| required_fields | scaffold_type, installation_date, inspector, connection_state, guard_rail, toe_board, loading_test |
| builder_priority | P1 |
| implementation_status | PENDING |

### CL-002: 거푸집 동바리 안전 점검표

| 항목 | 내용 |
|------|------|
| document_id | CL-002 |
| document_name | 거푸집 동바리 설치 점검표 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제337조~제347조 |
| required_fields | formwork_type, support_spacing, cross_bracing, loading_condition, inspector |
| builder_priority | P2 |
| implementation_status | PENDING |

### CL-003: 건설 장비 일일 점검표

| 항목 | 내용 |
|------|------|
| document_id | CL-003 |
| document_name | 건설 장비 일일 사전 점검표 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제171조 (차량계 건설기계 사전점검), 제179조 (하역운반기계 사전점검) |
| required_fields | equipment_type, equipment_no, inspection_date, brake, lighting, horn, tires, hydraulic, operator_name |
| builder_priority | P1 |
| implementation_status | PENDING |

### CL-004: 전기설비 점검표

| 항목 | 내용 |
|------|------|
| document_id | CL-004 |
| document_name | 전기설비 정기 점검표 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제303조 이하 |
| required_fields | panel_location, grounding_check, rcd_test, insulation_resistance, overload_protection |
| builder_priority | P2 |
| implementation_status | PENDING |

### CL-005: 화재 예방 점검표

| 항목 | 내용 |
|------|------|
| document_id | CL-005 |
| document_name | 화재 예방 점검표 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제241조 이하, 소방시설 설치 및 관리에 관한 법률 |
| required_fields | fire_extinguisher_location, expiry_check, flammable_storage, smoking_restriction, fire_exit |
| builder_priority | P2 |
| implementation_status | PENDING |

### CL-006: 타워크레인·양중 장비 점검표

| 항목 | 내용 |
|------|------|
| document_id | CL-006 |
| document_name | 타워크레인 자체 점검표 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제143조~제148조 (타워크레인 점검 의무) |
| required_fields | crane_no, inspection_date, wire_rope, hook, overload_limiter, anemometer, slewing_brake |
| builder_priority | P1 |
| implementation_status | PENDING |

### CL-007: 추락 방호 설비 점검표

| 항목 | 내용 |
|------|------|
| document_id | CL-007 |
| document_name | 추락 방호 설비 점검표 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제42조~제44조 |
| required_fields | location, guard_rail_height, safety_net_condition, safety_harness_anchors |
| builder_priority | P2 |
| implementation_status | PENDING |

### CL-008: 보호구 지급·관리 점검표

| 항목 | 내용 |
|------|------|
| document_id | CL-008 |
| document_name | 보호구 지급 및 관리 점검표 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제32조 (보호구 지급 의무) |
| required_fields | ppe_type, quantity, issue_date, condition_check, replacement_date |
| builder_priority | P3 |
| implementation_status | PENDING |

### CL-009: 유해화학물질 취급 점검표

| 항목 | 내용 |
|------|------|
| document_id | CL-009 |
| document_name | 유해화학물질 취급 점검표 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제441조 이하, 화학물질관리법 |
| required_fields | chemical_name, msds_confirmed, storage_condition, ppe_required, spill_kit_location |
| builder_priority | P3 |
| implementation_status | PENDING |

### CL-010: 밀폐공간 사전 안전 점검표

| 항목 | 내용 |
|------|------|
| document_id | CL-010 |
| document_name | 밀폐공간 사전 안전 점검표 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제622조~제625조 |
| required_fields | space_type, oxygen_level, co_level, h2s_level, ventilation_ok, monitor_person, rescue_equipment |
| builder_priority | P0 |
| implementation_status | PENDING |

---

## 대분류 8. 보호구 / 장비 반입 서류

### PPE-001: 보호구 지급 대장

| 항목 | 내용 |
|------|------|
| document_id | PPE-001 |
| document_name | 보호구 지급 대장 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제32조 |
| required_fields | worker_name, ppe_type, issue_date, size, quantity, signature |
| builder_priority | P2 |
| implementation_status | PENDING |

### PPE-002: 장비 반입 신청서

| 항목 | 내용 |
|------|------|
| document_id | PPE-002 |
| document_name | 건설 장비 반입 신청서 |
| legal_required | false |
| practical_required | true |
| legal_basis | 원청 안전 관리 규정 (법정 서식 아님) |
| required_fields | equipment_type, manufacturer, model, license_no, operator_name, license_copy, inspection_certificate |
| builder_priority | P2 |
| implementation_status | PENDING |

### PPE-003: 장비 보험·검사증 확인서

| 항목 | 내용 |
|------|------|
| document_id | PPE-003 |
| document_name | 건설 장비 보험·정기검사증 확인서 |
| legal_required | false |
| practical_required | true |
| legal_basis | 건설기계관리법, 산업안전보건법 제93조 (검사 의무) |
| required_fields | equipment_no, inspection_expiry, insurance_expiry, operator_license, confirm_date |
| builder_priority | P3 |
| implementation_status | PENDING |

### PPE-004: MSDS (물질안전보건자료) 비치 확인서

| 항목 | 내용 |
|------|------|
| document_id | PPE-004 |
| document_name | MSDS 비치 및 교육 확인서 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제110조~제115조 |
| required_fields | chemical_name, msds_version, posting_location, training_date, trainer_name, worker_signature |
| builder_priority | P3 |
| implementation_status | PENDING |

---

## 대분류 9. 협력업체 / 근로자 관리 서류

### CM-001: 협력업체 안전보건 서류 확인서

| 항목 | 내용 |
|------|------|
| document_id | CM-001 |
| document_name | 협력업체 안전보건 관련 서류 확인서 |
| legal_required | false |
| practical_required | true |
| legal_basis | 법 제63조 (도급인 안전보건 조치 의무) |
| required_fields | contractor_name, business_no, safety_manager_name, safety_plan_confirmed, insurance_confirmed, equipment_inspection_confirmed |
| builder_priority | P2 |
| implementation_status | PENDING |

### CM-002: 도급·용역 안전보건 협의서

| 항목 | 내용 |
|------|------|
| document_id | CM-002 |
| document_name | 도급·용역 안전보건 협의서 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제64조 (도급인·수급인 협의체 구성) |
| required_fields | meeting_date, attendees, safety_agenda, agreed_measures, next_meeting_date |
| builder_priority | P2 |
| implementation_status | PENDING |

### CM-003: 근로자 건강진단 결과 확인서

| 항목 | 내용 |
|------|------|
| document_id | CM-003 |
| document_name | 근로자 건강진단 결과 확인서 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제129조~제131조, 시행규칙 제97조 |
| required_fields | worker_name, examination_date, examination_type, result_code, follow_up_action |
| builder_priority | P3 |
| implementation_status | PENDING |

### CM-004: 안전보건관리자 선임 신고서

| 항목 | 내용 |
|------|------|
| document_id | CM-004 |
| document_name | 안전보건관리자 선임 신고서 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제17조~제19조, 시행규칙 제16조 별지서식 |
| required_fields | company_name, manager_name, qualification, appointment_date, submit_date |
| builder_priority | P3 |
| implementation_status | PENDING |

### CM-005: 신규 근로자 안전보건 서약서

| 항목 | 내용 |
|------|------|
| document_id | CM-005 |
| document_name | 신규 근로자 안전보건 서약서 |
| legal_required | false |
| practical_required | true |
| legal_basis | 중대재해처벌법 시행령 제4조 (안전보건 의무 부여) |
| required_fields | worker_name, join_date, safety_rules_confirmed, ppe_usage_confirmed, signature |
| builder_priority | P3 |
| implementation_status | PENDING |

### CM-006: 외국인 근로자 안전보건 확인서

| 항목 | 내용 |
|------|------|
| document_id | CM-006 |
| document_name | 외국인 근로자 안전보건 교육 확인서 |
| legal_required | false |
| practical_required | true |
| legal_basis | 법 제29조 (외국인 포함 교육 의무) |
| required_fields | worker_name, nationality, language, interpreter_provided, safety_briefing_confirmed, signature |
| builder_priority | P3 |
| implementation_status | PENDING |

### CM-007: 산업재해 발생 현황 대장

| 항목 | 내용 |
|------|------|
| document_id | CM-007 |
| document_name | 산업재해 발생 현황 관리 대장 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제57조 (산업재해 기록·보존 의무), 시행규칙 제73조 |
| required_fields | accident_date, worker_name, accident_type, injury_type, lost_days, cause, prevention_measures |
| builder_priority | P3 |
| implementation_status | PENDING |

---

## 대분류 10. 사고 / 비상대응 서류

### EM-001: 산업재해조사표

| 항목 | 내용 |
|------|------|
| document_id | EM-001 |
| document_name | 산업재해조사표 (별지 제30호서식) |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제57조, 시행규칙 제73조 별지 제30호서식 |
| target_work | 중대재해 또는 사망 사고 발생 시 |
| required_fields | company_name, accident_date, accident_location, worker_name, injury_type, accident_cause, prevention_measures |
| inspection_items | 발생 후 1개월 이내 관할 노동청 제출 의무 (중대재해: 즉시 보고) |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

### EM-002: 아차사고 보고서

| 항목 | 내용 |
|------|------|
| document_id | EM-002 |
| document_name | 아차사고 (Near Miss) 보고서 |
| legal_required | false |
| practical_required | true |
| legal_basis | 중대재해처벌법 시행령 제4조 (안전보건 개선 의무) |
| required_fields | incident_date, reporter_name, location, description, potential_harm, corrective_action, follow_up |
| builder_priority | P2 |
| implementation_status | PENDING |

### EM-003: 비상 연락망 및 대피 계획서

| 항목 | 내용 |
|------|------|
| document_id | EM-003 |
| document_name | 비상 연락망 및 대피 계획서 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제14조 (비상구 및 대피), 밀폐공간 구조계획 (제622조) |
| required_fields | emergency_contacts, evacuation_routes, assembly_point, rescue_team, fire_extinguisher_locations |
| builder_priority | P2 |
| implementation_status | PENDING |

### EM-004: 중대재해 발생 즉시 보고서

| 항목 | 내용 |
|------|------|
| document_id | EM-004 |
| document_name | 중대재해 발생 즉시 보고서 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제54조 (중대재해 발생 시 즉시 보고 의무) |
| required_fields | accident_datetime, location, victim_name, accident_type, immediate_measure, reporter_name, contact |
| inspection_items | 발생 후 24시간 이내 관할 노동청 보고 |
| builder_priority | P2 |
| implementation_status | PENDING |

### EM-005: 재해 원인 분석 보고서

| 항목 | 내용 |
|------|------|
| document_id | EM-005 |
| document_name | 재해 원인 분석 및 재발 방지 보고서 |
| legal_required | false |
| practical_required | true |
| legal_basis | 법 제57조 제2항 (재발 방지 대책 수립 의무) |
| required_fields | accident_summary, direct_cause, indirect_cause, root_cause, prevention_measures, implementation_schedule |
| builder_priority | P3 |
| implementation_status | PENDING |

### EM-006: 응급조치 기록서

| 항목 | 내용 |
|------|------|
| document_id | EM-006 |
| document_name | 응급조치 실시 기록서 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제14조, 응급의료에 관한 법률 |
| required_fields | incident_time, patient_name, symptom, first_aid_given, hospital_transfer, first_aider_name |
| builder_priority | P3 |
| implementation_status | PENDING |

---

## 대분류 11. 공종별 특화 서류

### TS-001: 유해위험방지계획서 (건설업)

| 항목 | 내용 |
|------|------|
| document_id | TS-001 |
| document_name | 유해위험방지계획서 (건설업, 별지 제22호서식) |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제42조, 시행규칙 제42조~제52조, 별지 제22호서식 |
| target_work | 1억원 이상 건설 공사 착공 전 |
| required_fields | project_name, project_cost, construction_method, hazard_analysis, safety_plan, emergency_plan |
| builder_priority | OUT |
| implementation_status | OUT (복합 문서, 별도 설계 필요) |

### TS-002: 유해위험방지계획서 (제조업)

| 항목 | 내용 |
|------|------|
| document_id | TS-002 |
| document_name | 유해위험방지계획서 (제조업, 별지 제19호서식) |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제42조, 시행규칙 제42조, 별지 제19호서식 |
| target_work | 유해위험설비 설치·이전·변경 시 |
| required_fields | facility_name, hazard_equipment, installation_method, safety_measures |
| builder_priority | OUT |
| implementation_status | OUT |

### TS-003: 공정안전보고서 (PSM)

| 항목 | 내용 |
|------|------|
| document_id | TS-003 |
| document_name | 공정안전보고서 (PSM 4요소) |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제44조, 시행규칙 제50조 이하 |
| target_work | PSM 대상 사업장 (유해위험물질 규정량 이상 취급) |
| builder_priority | OUT |
| implementation_status | OUT (복합 패키지, Excel 단독 불가) |

### TS-004: 산업안전보건관리비 사용계획서

| 항목 | 내용 |
|------|------|
| document_id | TS-004 |
| document_name | 산업안전보건관리비 사용계획서 (별지 제102호서식) |
| legal_required | true |
| practical_required | true |
| legal_basis | 건설업 산업안전보건관리비 계상 및 사용기준 고시, 별지 제102호서식 |
| target_work | 건설 현장 안전보건관리비 집행 계획 및 정산 |
| required_fields | project_name, contract_amount, safety_cost_rate, planned_amount, actual_amount, expenditure_items |
| builder_priority | P2 |
| implementation_status | PENDING |

### TS-005: 석면 해체·제거 작업 계획서

| 항목 | 내용 |
|------|------|
| document_id | TS-005 |
| document_name | 석면 해체·제거 작업 계획서 |
| legal_required | true |
| practical_required | true |
| legal_basis | 법 제119조, 시행규칙 제175조 이하 |
| target_work | 건축물 철거 시 석면 함유 자재 제거 |
| required_fields | building_address, asbestos_type, quantity, removal_method, ppe_required, disposal_plan, air_monitoring |
| builder_priority | P2 |
| implementation_status | PENDING |

---

## 대분류 12. 실무 보강 서류

### SP-001: 안전보건 방침 및 목표 게시문

| 항목 | 내용 |
|------|------|
| document_id | SP-001 |
| document_name | 안전보건 방침 및 목표 게시문 |
| legal_required | false |
| practical_required | true |
| legal_basis | 중대재해처벌법 시행령 제4조 제1호 (안전보건 목표·경영 방침 수립 의무) |
| required_fields | policy_statement, safety_goals, ceo_signature, posting_date |
| builder_priority | P3 |
| implementation_status | PENDING |

### SP-002: 협력업체 안전보건 수준 평가표

| 항목 | 내용 |
|------|------|
| document_id | SP-002 |
| document_name | 협력업체 안전보건 수준 평가표 |
| legal_required | false |
| practical_required | true |
| legal_basis | 법 제63조, 중대재해처벌법 시행령 제4조 제9호 (협력업체 안전관리 역량 평가 의무) |
| required_fields | contractor_name, evaluation_date, safety_management_score, accident_history, training_status, equipment_status |
| builder_priority | P3 |
| implementation_status | PENDING |

### SP-003: 위험성평가 우수 사례 보고서

| 항목 | 내용 |
|------|------|
| document_id | SP-003 |
| document_name | 위험성평가 우수 사례 보고서 |
| legal_required | false |
| practical_required | false |
| legal_basis | 고용노동부 위험성평가 우수 사업장 인정 제도 |
| required_fields | company_name, improvement_case, before_risk, after_risk, economic_benefit |
| builder_priority | P3 |
| implementation_status | PENDING |

### SP-004: 안전문화 활동 기록부

| 항목 | 내용 |
|------|------|
| document_id | SP-004 |
| document_name | 안전문화 활동 기록부 |
| legal_required | false |
| practical_required | false |
| legal_basis | 중대재해처벌법 시행령 제4조 (안전보건관리체계 구축) |
| required_fields | activity_name, date, participants, outcome |
| builder_priority | P3 |
| implementation_status | PENDING |

---

## 제38조 별표4 대상 작업 누락 여부 검증

| 별표4 작업 | 대응 문서 ID | 구현 상태 |
|-----------|------------|---------|
| 타워크레인 사용 작업 | WP-006 | PENDING (P0) |
| 차량계 하역운반기계 사용 작업 | WP-009 + EQ-002 | **DONE** |
| 차량계 건설기계 사용 작업 | WP-008 + EQ-003~EQ-006 | **DONE** |
| 화학설비·부속설비 작업 | WP-013 | PENDING (P2) |
| 굴착 작업 (2m 이상) | WP-001 | **DONE** |
| 터널 굴착 작업 | WP-002 | PENDING (P1) |
| 교량 설치·해체·변경 작업 | WP-004 | PENDING (P2) |
| 건축물 등의 해체 작업 | WP-003 | PENDING (P1) |
| 중량물 취급 작업 | WP-005 | PENDING (P1) |
| 궤도 작업 | WP-012 | PENDING (P3) |
| 항타기·항발기 사용 작업 | WP-010 + EQ-009 | PENDING (P1) |
| 이동식 크레인 사용 작업 | WP-007 + EQ-004 | PENDING (P0) |
| 밀폐공간 작업 | WP-014 + PTW-001 | PENDING (P0) |

> **누락 없음** — 별표4 전체 대상 작업 목록이 카탈로그에 포함됨.

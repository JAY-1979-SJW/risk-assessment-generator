# 장비 사용계획서 마스터 카탈로그

**작성일**: 2026-04-24  
**법령 기준**: 산업안전보건기준에 관한 규칙 제38조, 건설기계관리법, 크레인·양중 관련 고시  
**원칙**: 법정 작업계획서(별표4)와 실무 장비 사용계획서를 명확히 구분  
**연관 파일**: `safety_document_master_catalog.md` (WP-006~WP-014)

---

## 범례

| 코드 | 의미 |
|------|------|
| `법정` | 기준규칙 제38조 별표4 직접 의무 대상 |
| `실무필수` | 법정 의무는 아니나 현장 관행·원청 요구로 사실상 필수 |
| `선택` | 사업장 자율 적용 |
| `DONE` | builder 구현 완료 |
| `P0~P3` | 구현 우선순위 |

---

## 중분류별 장비 사용계획서 목록 (16종 중분류)

| 중분류 | 문서 ID | 문서명 | 법정/실무 | 구현 상태 |
|--------|---------|--------|----------|---------|
| 차량계 하역운반기계 | EQ-001 | 차량계 하역운반기계 작업계획서 | **법정** | **DONE** |
| 차량계 건설기계 | EQ-002 | 차량계 건설기계 작업계획서 | **법정** | **DONE** |
| 타워크레인 | EQ-003 | 타워크레인 작업계획서 | **법정** | P0 |
| 이동식크레인·카고크레인 | EQ-004 | 이동식 크레인 작업계획서 | **법정** | P0 |
| 고소작업대 | EQ-005 | 고소작업대 사용계획서 | 실무필수 | P1 |
| 펌프카 | EQ-006 | 펌프카 작업계획서 | 실무필수 | P1 |
| 굴착기·로더 | EQ-007 | 굴착기·로더 사용계획서 | 법정 (차량계 건설기계 하위) | P1 |
| 덤프·롤러·불도저 | EQ-008 | 덤프·롤러·불도저 사용계획서 | 법정 (차량계 건설기계 하위) | P2 |
| 항타기·항발기·천공기 | EQ-009 | 항타기·항발기 사용계획서 | **법정** | P1 |
| 리프트·곤돌라 | EQ-010 | 리프트·곤돌라 사용계획서 | 실무필수 | P2 |
| 양중기·호이스트·윈치 | EQ-011 | 양중기·호이스트 작업계획서 | 실무필수 | P1 |
| 중량물 취급 | EQ-012 | 중량물 취급 작업계획서 | **법정** | P1 |
| 임시전기·발전기 | EQ-013 | 임시전기·발전기 사용계획서 | 실무필수 | P2 |
| 용접·용단·화기작업 | EQ-014 | 화기작업 계획서 | 실무필수 | P1 |
| 콤프레샤·공압장비 | EQ-015 | 콤프레샤·공압장비 사용계획서 | 선택 | P3 |
| 사다리·말비계·작업발판 | EQ-016 | 사다리·말비계 사용계획서 | 실무필수 | P2 |

---

## 상세 명세

---

### EQ-001: 차량계 하역운반기계 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-001 |
| document_name | 차량계 하역운반기계 작업계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 차량계 하역운반기계 |
| minor_category | 지게차·구내운반차·화물자동차 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제2호, 제2항 / 제179조 (작업 전 점검) / 제180조 (제한속도) / 제182조 (유도자) |
| target_work | 지게차·구내운반차·화물자동차·고소작업대를 이용한 하역·운반 작업 |
| target_equipment | 지게차 (포크리프트), 구내운반차, 전동 파렛트 트럭, 화물자동차 |
| required_fields | machine_type, machine_max_load, work_location, work_method, travel_route_text, speed_limit, guide_worker_required, pedestrian_separation, emergency_contact, emergency_measure |
| inspection_items | 제동·조종장치, 하역·유압장치, 바퀴 이상 유무, 전조등·경음기, 헤드가드, 백레스트, 안전벨트, 적재물 고정 (제179조 기준 8개 항목) |
| route_or_drawing_required | true (운행경로 개략도, 스케치 박스) |
| signature_required | true |
| builder_priority | DONE |
| implementation_status | **DONE** — `material_handling_workplan` builder, registry v1.0 |
| notes | machine_max_load ≠ machine_capacity (건설기계와 혼용 금지) / pre_check_items 미제공 시 제179조 기본 8개 자동 적용 |

---

### EQ-002: 차량계 건설기계 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-002 |
| document_name | 차량계 건설기계 작업계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 차량계 건설기계 |
| minor_category | 건설기계 일반 (불도저·굴착기·로더·롤러 등) |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제3호 / 제170조 (기계 종류·성능·작업방법·운행경로) / 제171조 (작업 전 점검) |
| target_work | 차량계 건설기계를 사용하는 모든 건설 작업 |
| target_equipment | 불도저, 굴착기(백호), 로더, 모터그레이더, 롤러, 스크레이퍼, 덤프트럭 |
| required_fields | machine_type, machine_capacity, work_method, travel_route_text, speed_limit, work_radius, guide_worker_required, ground_survey, emergency_contact, emergency_measure |
| inspection_items | 브레이크·조향장치, 전조등·경음기, 유압계통, 타이어·트랙, 후방경보장치 (제171조 기준) |
| route_or_drawing_required | true (운행경로도) |
| signature_required | true |
| builder_priority | DONE |
| implementation_status | **DONE** — `vehicle_construction_workplan` builder, registry v1.0 |
| notes | machine_capacity = 최대작업능력 (하역운반기계의 machine_max_load와 다름) |

---

### EQ-003: 타워크레인 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-003 |
| document_name | 타워크레인 작업계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 타워크레인 |
| minor_category | 고정식·이동식·클라이밍 타워크레인 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제1호 / 제142조~제148조 (타워크레인 설치·사용) |
| target_work | 타워크레인을 사용하는 모든 인양·설치·해체 작업 |
| target_equipment | 타워크레인 (고정식, 클라이밍, 셀프이렉팅) |
| required_fields | crane_type, crane_model, crane_capacity_max, work_radius, work_method, travel_route_text, collision_prevention, guide_worker_required, anemometer_check, emergency_measure |
| inspection_items | 과부하방지장치, 권과방지장치, 비상정지장치, 풍속계(anemometer), 클라이밍 고정 상태, 줄걸이 방법, 작업반경 내 장애물 |
| route_or_drawing_required | true (작업반경도, 인접 크레인 충돌 방지 구역도) |
| signature_required | true |
| builder_priority | P0 |
| implementation_status | PENDING |
| notes | 타워크레인 2대 이상 → 충돌 방지 계획 별도 수립 / 풍속 15m/s 이상 작업 중지 기준 명시 필요 |

---

### EQ-004: 이동식 크레인·카고크레인 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-004 |
| document_name | 이동식 크레인·카고크레인 작업계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 이동식크레인·카고크레인 |
| minor_category | 유압식 이동크레인·카고크레인·트럭크레인 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제14호 / 제134조~제141조 (이동식 크레인 사용) |
| target_work | 이동식 크레인을 사용하는 인양·설치 작업 |
| target_equipment | 유압식 이동크레인, 카고크레인, 트럭크레인, 크롤러크레인 |
| required_fields | crane_type, crane_capacity, load_weight, work_radius, ground_condition, outrigger_setup, rigging_method, signal_person, travel_route_text, emergency_measure |
| inspection_items | 아웃트리거 설치 및 지반 지지력, 와이어로프 상태, 과부하방지장치, 신호수 배치, 줄걸이 방법 및 SWL |
| route_or_drawing_required | true (인양 위치도, 이동 경로, 작업반경도) |
| signature_required | true |
| builder_priority | P0 |
| implementation_status | PENDING |
| notes | Critical Lift (SWL 75% 초과 or 복합 인양) 시 PTW-007 추가 발행 필요 |

---

### EQ-005: 고소작업대 사용계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-005 |
| document_name | 고소작업대 사용계획서 (스카이·렌탈 장비 포함) |
| major_category | 장비 사용계획서 |
| middle_category | 고소작업대 |
| minor_category | 스카이차·붐리프트·시저리프트·렌탈 고소장비 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제86조 이하 (고소작업대), 건설기계관리법 (고소작업차 검사 의무) |
| target_work | 건축물 외벽 마감, 고가 설비 점검·수리, 가로등·신호등 작업 |
| target_equipment | 스카이차 (붐트럭), 붐리프트, 시저리프트, 마스트클라이밍 플랫폼 |
| required_fields | equipment_type, max_height, working_height, platform_load, ground_level_check, outrigger_required, travel_route_text, wind_speed_limit, guide_worker_required, emergency_measure |
| inspection_items | 전도 방지(지반 평탄·하중 분산), 과부하 방지, 안전난간 상태, 안전대 앵커 설치, 풍속 제한 준수 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### EQ-006: 펌프카 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-006 |
| document_name | 콘크리트 펌프카 작업계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 펌프카 |
| minor_category | 콘크리트 펌프카 (붐타입·이동식) |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제170조 이하 (차량계 건설기계 준용), 건설기계관리법 |
| target_work | 콘크리트 타설 작업 |
| target_equipment | 붐타입 펌프카, 이동식 콘크리트 펌프 |
| required_fields | pump_type, boom_length, max_pressure, work_location, ground_condition, outrigger_setup, travel_route_text, pipe_installation_plan, emergency_measure |
| inspection_items | 아웃트리거 설치 및 지반 지지력, 붐 전개 범위 내 장애물(전선 등), 압력 관리, 배관 고정 상태 |
| route_or_drawing_required | true (붐 전개 반경도) |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |
| notes | 고압 배관 파열 시 콘크리트 비산 위험 — 비상조치 항목 필수 |

---

### EQ-007: 굴착기·로더 사용계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-007 |
| document_name | 굴착기·로더 특화 사용계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 굴착기·로더 |
| minor_category | 백호·굴착기·로더·스키드로더 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제3호 (차량계 건설기계), 제170조~제174조 |
| target_work | 토공·굴착·상차 작업 |
| target_equipment | 굴착기(백호), 미니굴착기, 로더, 스키드스티어로더 |
| required_fields | machine_type, machine_capacity, work_method, travel_route_text, excavation_depth, underground_utility_check, swing_radius, guide_worker_required, emergency_measure |
| inspection_items | 후방 사각지대 확인, 스윙 반경 내 근로자 접근 통제, 버켓 상태, 유압 호스 누유, 지하매설물 손상 방지 |
| route_or_drawing_required | true (굴착 범위·운행경로) |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |
| notes | EQ-002 차량계 건설기계 계획서의 세부 특화본. 지하매설물 사전 탐사 확인 필드 추가 |

---

### EQ-008: 덤프·롤러·불도저 사용계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-008 |
| document_name | 덤프·롤러·불도저 사용계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 덤프·롤러·불도저 |
| minor_category | 덤프트럭·진동롤러·불도저·모터그레이더 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제3호 (차량계 건설기계), 제170조 |
| target_work | 토공 운반, 노면 다짐, 성토·절토 작업 |
| target_equipment | 덤프트럭(15톤·25톤), 진동롤러, 불도저, 모터그레이더 |
| required_fields | machine_type, machine_capacity, payload_capacity, work_method, travel_route_text, speed_limit, guide_worker_required, emergency_measure |
| inspection_items | 덤프박스 상승 잠금 확인, 적재 과적 여부, 운행 경로 경사도, 롤러 진동 충격 영향 반경 |
| route_or_drawing_required | true (운반 경로도) |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### EQ-009: 항타기·항발기·천공기 사용계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-009 |
| document_name | 항타기·항발기·천공기 사용계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 항타기·항발기·천공기 |
| minor_category | 유압해머·디젤해머·어스오거·회전천공기 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제12호 / 제186조~제197조 (항타기·항발기 사용) |
| target_work | 말뚝 박기·뽑기, 지반 천공 작업 |
| target_equipment | 유압해머, 디젤해머, 어스오거, 회전식 천공기(CFA·RCD) |
| required_fields | machine_type, machine_capacity, pile_type, pile_depth, work_method, pile_sequence, guide_worker_required, ground_survey, vibration_impact, emergency_measure |
| inspection_items | 기계 수직 설치 확인, 와이어로프 마모·이탈, 과부하 방지 장치, 인접 구조물 진동 영향, 소음·진동 민원 대책 |
| route_or_drawing_required | true (항타 위치도, 순서도) |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |
| notes | 소음·진동 영향 평가 및 인접 건물 균열 모니터링 항목 권고 |

---

### EQ-010: 리프트·곤돌라 사용계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-010 |
| document_name | 건설용 리프트·곤돌라 사용계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 리프트·곤돌라 |
| minor_category | 건설용 리프트·달비계·곤돌라 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제133조~제148조 (리프트), 제63조~제68조 (달비계·곤돌라) |
| target_work | 자재·인원 수직 이송, 외벽 도장·청소 작업 |
| target_equipment | 건설용 리프트, 이동식 비계 리프트, 곤돌라, 달비계 |
| required_fields | equipment_type, rated_load, lift_height, installation_plan, wire_rope_condition, overload_protection, emergency_stop, emergency_measure |
| inspection_items | 권과방지장치, 과부하방지장치, 와이어로프 마모 기준 초과 여부, 비상정지 작동 확인 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### EQ-011: 양중기·호이스트·윈치 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-011 |
| document_name | 양중기·호이스트·윈치 작업계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 양중기·호이스트·윈치 |
| minor_category | 전동호이스트·체인블록·윈치·달기체인 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제132조~제141조 (호이스트·양중 장비) |
| target_work | 소형 자재 인양, 기계·장비 이동 |
| target_equipment | 전동 호이스트, 체인블록, 모노레일 호이스트, 윈치 |
| required_fields | equipment_type, rated_load, load_weight, rigging_method, hook_safety_latch, wire_rope_condition, emergency_measure |
| inspection_items | 훅 해지 장치 (safety latch), 와이어로프·체인 마모 기준, 과부하 방지, 줄걸이 용구 상태 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |

---

### EQ-012: 중량물 취급 작업계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-012 |
| document_name | 중량물 취급 작업계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 중량물 취급 |
| minor_category | 100kg 이상 중량물 2인 이상 취급 |
| legal_required | true |
| practical_required | true |
| legal_basis | 기준규칙 제38조 제1항 제10호, 제39조 (중량물 취급) |
| target_work | 중량물(100kg 이상) 인력 또는 기계를 이용한 취급·이동·설치 |
| target_equipment | 지게차, 이동식크레인, 호이스트, 윈치, 수동 핸드 팔렛트 |
| required_fields | load_name, load_weight, load_dimensions, handling_equipment, lifting_method, sequence, fall_prevention, tip_over_prevention, ground_load_check, signal_person, emergency_measure |
| inspection_items | SWL 초과 여부, 줄걸이 각도(60° 이하 권장), 지반 침하, 낙하·전도 방지 조치, 작업 구역 통제 |
| route_or_drawing_required | true (인양 경로, 하치 위치) |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |
| notes | Critical Lift(SWL 75% 초과) 판단 기준 명시 / 계산서 첨부 권고 |

---

### EQ-013: 임시전기·발전기 사용계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-013 |
| document_name | 임시전기 설치·발전기 사용계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 임시전기·발전기 |
| minor_category | 건설 현장 임시 배전·발전기 운영 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제301조~제330조 (전기 작업 안전), 건설 현장 임시전기 지침 |
| target_work | 건설 현장 임시전기 설치·운영, 발전기 사용 작업 |
| target_equipment | 이동식 발전기, 임시 분전반, 가설 전선 |
| required_fields | installation_location, voltage_class, installed_capacity, grounding_method, rcd_installed, weatherproof_protection, cable_routing, fuel_storage, emergency_measure |
| inspection_items | 접지(제3종 이상), 누전차단기(30mA 이하), 방수·방호 처리, 케이블 손상, 발전기 연료 누출, 배기 가스 환기 |
| route_or_drawing_required | true (임시전기 배선도) |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |

---

### EQ-014: 용접·용단·화기작업 계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-014 |
| document_name | 용접·용단·화기작업 안전계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 용접·용단·화기작업 |
| minor_category | 아크용접·가스용단·브레이징·그라인딩 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제241조~제252조 (화재·폭발 예방) / PTW-002 화기작업허가서와 연계 |
| target_work | 용접·용단·가스절단·금속 가열 등 화기 발생 작업 |
| target_equipment | 아크용접기, 가스용단기, 그라인더, 가스 토치 |
| required_fields | work_type, work_location, flammable_clearance, fire_extinguisher_type, fire_extinguisher_location, fire_watch_name, gas_cylinder_storage, ventilation_method, emergency_measure |
| inspection_items | 가연성 물질 제거(반경 10m), 소화기 적합성, 환기 확보, 화재 감시자 배치·30분 이상 잔류, 가스 실린더 고정·전도 방지, 역화 방지 장치 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P1 |
| implementation_status | PENDING |
| notes | 밀폐 공간·유해가스 환경에서는 WP-014 밀폐공간 작업계획서 동시 발행 |

---

### EQ-015: 콤프레샤·공압장비 사용계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-015 |
| document_name | 콤프레샤·공압장비 사용계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 콤프레샤·공압장비 |
| minor_category | 공기압축기·공압 공구·압력 용기 |
| legal_required | false |
| practical_required | false |
| legal_basis | 기준규칙 제261조~제276조 (압력 용기 안전), 산업안전보건법 제93조 (안전검사) |
| target_work | 공압 도구 사용 작업, 분사 도장, 콘크리트 파쇄 |
| target_equipment | 공기압축기, 공압 그라인더, 임팩트 렌치, 스프레이건 |
| required_fields | equipment_type, max_pressure, relief_valve_check, inspection_certificate, hose_condition, emergency_pressure_release |
| inspection_items | 안전밸브 작동 확인, 압력 게이지 정상 여부, 호스 접속부 이탈 방지 클램프, 정기검사 유효 기간 |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P3 |
| implementation_status | PENDING |

---

### EQ-016: 사다리·말비계·작업발판 사용계획서

| 항목 | 내용 |
|------|------|
| document_id | EQ-016 |
| document_name | 사다리·말비계·이동식 작업발판 사용계획서 |
| major_category | 장비 사용계획서 |
| middle_category | 사다리·말비계·작업발판 |
| minor_category | 이동식 사다리·말비계·조립식 발판 |
| legal_required | false |
| practical_required | true |
| legal_basis | 기준규칙 제24조~제31조 (사다리), 제57조~제75조 (비계) |
| target_work | 소규모 고소 작업 (사다리·말비계·발판 사용) |
| target_equipment | A형 사다리, 연장 사다리, 말비계(A형 이동 비계), 알루미늄 작업발판 |
| required_fields | equipment_type, work_height, ladder_angle_check, anti_slip_confirmed, top_cap_usage_prohibited, two_person_rule, ppe_confirmed, emergency_measure |
| inspection_items | 사다리 75° 각도, 미끄럼 방지, 최상단 발판 사용 금지, 2인 이상 동시 사용 금지, 고정 확인 (상하단) |
| route_or_drawing_required | false |
| signature_required | true |
| builder_priority | P2 |
| implementation_status | PENDING |
| notes | 이동식 비계(롤링 비계)는 CL-001 비계 점검표 함께 발행 |

---

## 장비 사용계획서 — 법정/실무/선택 분류표

| 중분류 | 문서 ID | 법정 여부 | 법적 근거 (핵심) | 연관 작업계획서 |
|--------|---------|----------|-----------------|--------------|
| 차량계 하역운반기계 | EQ-001 | **법정** | 기준규칙 제38조 제2항 | WP-009 |
| 차량계 건설기계 | EQ-002 | **법정** | 기준규칙 제38조 제1항 제3호, 제170조 | WP-008 |
| 타워크레인 | EQ-003 | **법정** | 기준규칙 제38조 제1항 제1호, 제142조 | WP-006 |
| 이동식크레인·카고 | EQ-004 | **법정** | 기준규칙 제38조 제1항 제14호, 제134조 | WP-007 |
| 고소작업대 | EQ-005 | 실무필수 | 기준규칙 제86조 이하 | — |
| 펌프카 | EQ-006 | 실무필수 | 기준규칙 제170조 준용 | — |
| 굴착기·로더 | EQ-007 | **법정** | 기준규칙 제38조 제1항 제3호 (건설기계 하위) | WP-008 |
| 덤프·롤러·불도저 | EQ-008 | **법정** | 기준규칙 제38조 제1항 제3호 (건설기계 하위) | WP-008 |
| 항타기·항발기·천공기 | EQ-009 | **법정** | 기준규칙 제38조 제1항 제12호, 제186조 | WP-010 |
| 리프트·곤돌라 | EQ-010 | 실무필수 | 기준규칙 제133조 이하 | — |
| 양중기·호이스트·윈치 | EQ-011 | 실무필수 | 기준규칙 제132조 이하 | — |
| 중량물 취급 | EQ-012 | **법정** | 기준규칙 제38조 제1항 제10호, 제39조 | WP-005 |
| 임시전기·발전기 | EQ-013 | 실무필수 | 기준규칙 제301조 이하 | — |
| 용접·용단·화기작업 | EQ-014 | 실무필수 | 기준규칙 제241조 이하 | PTW-002 |
| 콤프레샤·공압장비 | EQ-015 | 선택 | 기준규칙 제261조 이하 | — |
| 사다리·말비계·발판 | EQ-016 | 실무필수 | 기준규칙 제24조, 제57조 | CL-001 |

---

## 장비별 주요 점검 항목 비교표

| 장비 | 작업 전 점검 핵심 3개 | 운행경로 도면 필요 | 유도자(신호수) 의무 |
|------|--------------------|-----------------|-----------------|
| 지게차 | 제동장치·하역장치·바퀴 | 필요 | **법정** (제182조) |
| 굴착기 | 브레이크·유압·타이어 | 필요 | 법정 (제173조) |
| 타워크레인 | 과부하방지·권과방지·풍속계 | 필요 (반경도) | 법정 (신호수) |
| 이동식크레인 | 아웃트리거·와이어로프·줄걸이 | 필요 | 법정 (신호수) |
| 고소작업대 | 지반·아웃트리거·안전난간 | 불필요 | 권장 |
| 펌프카 | 아웃트리거·붐·배관 고정 | 필요 (반경도) | 권장 |
| 항타기 | 수직 설치·와이어로프·과부하방지 | 필요 (위치도) | 법정 |
| 리프트 | 권과방지·과부하방지·비상정지 | 불필요 | 불필요 |
| 호이스트 | 훅 해지장치·체인·과부하방지 | 불필요 | 권장 |
| 용접기 | 환기·소화기·화재감시자 | 불필요 | 불필요 |

---

## 현황 요약

| 구분 | 문서 수 | 법정 의무 | 구현 완료 | 구현 대기 |
|------|--------|----------|---------|---------|
| 장비 사용계획서 전체 | 16 | 8 | 2 | 14 |
| 법정 미구현 | 6 | 6 | 0 | 6 |
| 실무필수 미구현 | 7 | 0 | 0 | 7 |
| 선택 미구현 | 1 | 0 | 0 | 1 |

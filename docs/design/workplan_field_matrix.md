# 작업계획서 계열 세부 필드 매트릭스

**작성일**: 2026-04-24  
**대상**: 굴착 작업계획서 / 차량계 건설기계 작업계획서 / 차량계 하역운반기계 작업계획서  
**목적**: 3종 작업계획서의 공통·차별 필드를 11개 카테고리로 세분화하여 builder 설계 기반 마련

---

## 분석 대상 3종

| 문서 | form_type | 법적 근거 | builder 현황 |
|------|----------|---------|------------|
| 굴착 작업계획서 | `excavation_workplan` | 기준 규칙 제38조·제82조 | ✓ 구현 완료 |
| 차량계 건설기계 작업계획서 | *(미등록)* | 기준 규칙 제38조·제170조 | ✗ 미구현 |
| 차량계 하역운반기계 작업계획서 | *(미등록)* | 기준 규칙 제38조 제1항 제2호 | ✗ 미구현 |

---

## 카테고리별 필드 매트릭스

### 1. 기계 종류/성능

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 기계 종류 | LAW | `excavation_machine` (종류 포함) | `machine_type` | `machine_type` |
| 기계 모델명 | PRAC | — | `machine_model` | `machine_model` |
| 기계 성능 (최대 작업능력) | LAW | `excavation_machine` (성능 포함) | `machine_capacity` | — |
| 최대 하중 | LAW | — | — | `machine_max_load` |
| 기계 수량 | PRAC | — | `machine_count` | `machine_count` |
| 제조사/연식 | PRAC | — | `machine_manufacturer` | `machine_manufacturer` |

**비고**:
- 굴착 작업계획서: `excavation_machine` 단일 필드에 종류+성능 통합 기술
- 차량계 건설기계: 종류(`machine_type`)와 성능(`machine_capacity`)을 분리하여 제170조 제1호 완족
- 차량계 하역운반기계: 종류(`machine_type`)와 최대 하중(`machine_max_load`)이 법정 필수

---

### 2. 운행경로

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 운행경로 (문자 기술) | LAW | — | `travel_route` | `travel_route` |
| 진입로 위치 | PRAC | — | `entry_point` | `entry_point` |
| 구내 동선 | PRAC | — | `internal_route` | `internal_route` |
| 반출경로 (토석) | LAW | `soil_disposal` (적재장소 포함) | — | — |
| 속도제한 구간 | PRAC | — | `speed_zones` | `speed_zones` |
| 보행자 교차 지점 | PRAC | — | `pedestrian_crossing` | `pedestrian_crossing` |

**비고**:
- 굴착은 운행경로 대신 토석 반출경로(`soil_disposal`)가 법정 필수
- 차량계 건설기계·하역운반기계: 운행경로(`travel_route`)가 제170조/제38조 명시 법정 필수
- 하역운반기계는 **보행자 동선 분리**가 사고 다발 원인으로 특히 중요

---

### 3. 작업방법

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 작업방법 (전체) | LAW | `work_method` | `work_method` | `work_method` |
| 굴착 방법 | LAW | `excavation_method` | — | — |
| 흙막이 지보공 방법 | LAW | `earth_retaining` | — | — |
| 작업순서·절차 | PRAC | `safety_steps[].task_step` | `work_sequence` | `work_sequence` |
| 하역·운반 방법 | PRAC | — | — | `unloading_method` |
| 신호 방법 | PRAC | — | `signal_method` | `signal_method` |

**비고**:
- 굴착은 방법 필드가 세분화 (굴착방법, 흙막이, 작업방법 각각 별도)
- 차량계 계열은 `work_method` 1개 필드로 법정 의무 충족 가능
- 하역운반기계는 하역 방법(`unloading_method`)과 신호 방법(`signal_method`)이 실무 핵심

---

### 4. 지형/지반 상태

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 지형·지반 사전조사 결과 | PRAC(제38조) | *(미정의)* | `ground_survey` | `ground_survey` |
| 지하매설물 현황 | LAW | `excavation_method` 내 포함 | `underground_facilities` | — |
| 지반 지지력 | PRAC | *(굴착 전 조사 필수)* | `bearing_capacity` | — |
| 용수 현황 | LAW | `water_disposal` | — | — |
| 경사도/구배 | PRAC | — | `slope_grade` | `slope_grade` |

**비고**:
- 기준 규칙 제38조 제1항: 3종 모두 **사전조사 의무** 있음 (지형·지반·지층 상태)
- 굴착은 용수 처리(`water_disposal`)가 제82조 법정 필수이나, 차량계 계열은 미규정
- 차량계 건설기계는 제171조에서 지형 등 조사 명시 (PRAC → 실무상 준법정)

---

### 5. 위험예방대책

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 위험요인 목록 | PRAC | `safety_steps[].hazard` | `hazard_list` | `hazard_list` |
| 안전조치 내용 | PRAC | `safety_steps[].safety_measure` | `safety_measures` | `safety_measures` |
| 위험성평가 연계 | PRAC | — | `risk_assessment_ref` | `risk_assessment_ref` |
| 추락 방지 조치 | PRAC | *(굴착면 추락)* | *(운전석 이탈 시)* | — |
| 협착 방지 조치 | PRAC | — | `crush_prevention` | `crush_prevention` |
| 충돌 방지 조치 | PRAC | — | `collision_prevention` | `collision_prevention` |

---

### 6. 출입통제

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 출입통제 범위 | PRAC | *(미정의)* | `access_control` | `access_control` |
| 출입통제 방법 | PRAC | *(미정의)* | `barrier_type` | `barrier_type` |
| 출입금지 표지 설치 | PRAC | — | `warning_signs` | `warning_signs` |
| 출입 통제 담당자 | PRAC | — | `access_controller` | `access_controller` |
| 보행자 분리 동선 | PRAC | — | — | `pedestrian_separation` |

**비고**:
- 굴착 작업계획서 현재 구현에는 출입통제 필드 **미정의** — 감독 시 지적 가능
- 차량계 건설기계: 작업반경 내 출입 금지는 제172조 유도자 규정과 연계
- 차량계 하역운반기계: **보행자 동선 분리**가 사고 다발 원인 → 별도 필드 권장

---

### 7. 유도자

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 유도자 배치 여부 | PRAC(제172조) | *(미정의)* | `guide_worker_required` | `guide_worker_required` |
| 유도자 배치 위치 | PRAC | *(미정의)* | `guide_worker_position` | `guide_worker_position` |
| 유도자 성명·연락처 | PRAC | *(미정의)* | `guide_worker_name` | `guide_worker_name` |
| 신호 방법 (유도자) | PRAC | *(미정의)* | `guide_signal_method` | `guide_signal_method` |

**비고**:
- 기준 규칙 제172조: 유도자가 필요한 경우 — 이 경우 작업계획서에 포함 권고
- 3종 모두 유도자 관련 필드가 현재 **미정의** 상태
- 법적으로는 작업계획서 기재 의무 없으나 중대재해 발생 시 계획서 부재가 위험 증거

---

### 8. 작업반경

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 최대 작업반경 (m) | PRAC | — | `work_radius` | — |
| 출입금지 범위 (작업반경 기준) | PRAC | — | `exclusion_zone` | — |
| 굴착 심도 (m) | PRAC | *(work_method 내 기술)* | — | — |
| 선회 반경 | PRAC | — | `swing_radius` | — |
| 최대 인양 높이 | PRAC | — | `max_lift_height` | — |

**비고**:
- 굴착은 작업반경 대신 굴착 심도·범위가 핵심 — 현재 work_method 내 자유 기술
- 차량계 건설기계는 작업반경(`work_radius`)이 출입통제 범위의 기준 → 별도 필드 필요

---

### 9. 비상조치

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 긴급조치 계획 (전반) | LAW | `emergency_measure` | `emergency_measure` | `emergency_measure` |
| 비상 연락망 | PRAC | *(미정의)* | `emergency_contact` | `emergency_contact` |
| 대피 경로 | PRAC | *(emergency_measure 내)* | `evacuation_route` | `evacuation_route` |
| 붕괴 시 조치 | PRAC | *(emergency_measure 내)* | — | — |
| 전도 시 조치 | PRAC | — | `overturn_response` | `overturn_response` |
| 충돌·협착 시 조치 | PRAC | — | `collision_response` | `collision_response` |

**비고**:
- 굴착: `emergency_measure` 단일 필드에 전반 기술 (제38조 제2항 법정 필수)
- 차량계 계열: 법정 필수 필드(`emergency_measure`) + PRAC 세분화 권장
- 비상 연락망 필드는 현재 **3종 모두 미정의** → 중대재해 대응 시 필수 항목

---

### 10. 점검항목

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 작업 전 점검 체크리스트 | PRAC | *(미정의)* | `pre_check_items` | `pre_check_items` |
| 흙막이 지보공 점검 | PRAC | *(earth_retaining 내)* | — | — |
| 기계 이상 여부 확인 | PRAC | — | `machine_inspection` | `machine_inspection` |
| 제동장치·조향장치 | PRAC | — | `brake_steering_check` | `brake_steering_check` |
| 헤드가드·백레스트 (지게차) | PRAC | — | — | `forklift_guard_check` |
| 안전벨트 착용 | PRAC | — | `seatbelt_check` | `seatbelt_check` |

**비고**:
- 점검항목은 3종 모두 현재 builder에 **미정의** 상태
- 차량계 건설기계: 기준 규칙 제175조 준수를 위한 점검 기록
- 차량계 하역운반기계(지게차): 헤드가드·백레스트·조작장치 점검은 제179조 필수 점검

---

### 11. 서명/확인

| 항목 | 법적 성격 | 굴착 | 차량계 건설기계 | 차량계 하역운반기계 |
|------|---------|:---:|:------------:|:----------------:|
| 작성일 | PRAC/EVID | `sign_date` | `sign_date` | `sign_date` |
| 작성자 서명란 | EVID | *(수기 공란)* | *(수기 공란)* | *(수기 공란)* |
| 작업 책임자·서명 | PRAC/EVID | `supervisor` | `supervisor` | `supervisor` |
| 운전자 서명 | PRAC/EVID | — | *(수기 공란)* | *(수기 공란)* |
| 유도자 서명 | PRAC/EVID | — | *(수기 공란)* | *(수기 공란)* |
| 안전담당자 확인 | PRAC/EVID | — | *(수기 공란)* | *(수기 공란)* |

**비고**:
- 서명란은 3종 모두 **수기 서명 전용** — builder에서 빈 셀로 출력
- `supervisor` 필드: 굴착에만 구현됨, 차량계 2종은 미정의

---

## 현행 builder 구현 대비 누락 필드 요약

### 굴착 작업계획서 — 현행 구현 대비 누락

| 카테고리 | 누락 필드 | 중요도 |
|---------|---------|------|
| 출입통제 | `access_control`, `barrier_type` | ★★★★☆ |
| 유도자 | `guide_worker_required`, `guide_worker_position` | ★★★★☆ |
| 지형·지반 | 사전조사 결과 (`ground_survey`) | ★★★☆☆ |
| 비상조치 | `emergency_contact` (비상 연락망) | ★★★☆☆ |
| 점검항목 | `pre_check_items` | ★★★☆☆ |

### 차량계 건설기계 — 신규 구현 시 필수 정의

| 카테고리 | 필드명 | 법적 성격 |
|---------|--------|---------|
| 기계 | `machine_type`, `machine_capacity` | LAW |
| 운행경로 | `travel_route` | LAW |
| 작업방법 | `work_method` | LAW |
| 지형조사 | `ground_survey` | PRAC |
| 유도자 | `guide_worker_required`, `guide_worker_position` | PRAC |
| 출입통제 | `access_control`, `work_radius` | PRAC |
| 비상조치 | `emergency_measure`, `emergency_contact` | LAW/PRAC |
| 운전자 | `operator_license` | PRAC/EVID |
| 서명 | `supervisor`, `sign_date` | PRAC/EVID |

### 차량계 하역운반기계 — 신규 구현 시 필수 정의

| 카테고리 | 필드명 | 법적 성격 |
|---------|--------|---------|
| 기계 | `machine_type`, `machine_max_load` | LAW |
| 운행경로 | `travel_route` | LAW |
| 작업방법 | `work_method` | LAW |
| 보행자 분리 | `pedestrian_separation` | PRAC |
| 유도자 | `guide_worker_required`, `guide_worker_position` | PRAC |
| 출입통제 | `access_control` | PRAC |
| 속도제한 | `speed_limit` | PRAC |
| 점검 | `pre_check_items`, `forklift_guard_check` | PRAC |
| 비상조치 | `emergency_measure`, `emergency_contact` | LAW/PRAC |
| 운전자 | `operator_license` | PRAC/EVID |
| 서명 | `supervisor`, `sign_date` | PRAC/EVID |

---

## 공통 구조 설계 권고

차량계 건설기계·하역운반기계 builder를 신규 구현할 때 굴착 작업계획서(`workplan_builder.py`)의 구조를 재사용 가능:

```
form_data 공통 구조 (안):
  # 표두 (공통)
  site_name          str|None  사업장명
  project_name       str|None  현장명
  work_location      str|None  작업위치
  work_date          str|None  작업기간
  supervisor         str|None  작업책임자
  sign_date          str|None  작성일

  # 법정 필수 (형식별 차별화)
  machine_type       str|None  기계 종류
  machine_capacity   str|None  기계 성능 (건설기계용)
  machine_max_load   str|None  최대 하중 (하역운반기계용)
  travel_route       str|None  운행경로
  work_method        str|None  작업방법
  emergency_measure  str|None  긴급조치 계획

  # 실무 보강 (공통)
  ground_survey      str|None  지형·지반 사전조사
  guide_worker_plan  str|None  유도자 배치 계획
  access_control     str|None  출입통제 방법
  work_radius        str|None  작업반경
  operator_license   str|None  운전자 자격/면허
  emergency_contact  str|None  비상 연락망
  pre_check_items    str|None  작업 전 점검사항

  # 반복 행 (굴착과 동일 패턴)
  safety_steps       list[dict] 작업단계별 안전조치 (task_step, hazard, safety_measure)
```

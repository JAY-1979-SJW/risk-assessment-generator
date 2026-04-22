# noise 복구 규칙 + 자연어 렌더링 보강

> v2 기준 descriptive_noise 재검토 및 control_code → 위험성평가표 감소대책 문장 렌더링 템플릿.

---

## 1. descriptive_noise 복구 점검

### 1.1 현황 (v2 800 샘플)

- `descriptive_noise`: 327 건
- 그 중 control 신호 의심(키워드 hit) : 23 건 → **복구 후보 약 7%**

### 1.2 복구 후보 대표 사례

| sample_id | 원문 (발췌) | 현 라벨 | 복구 제안 |
|---|---|---|---|
| S0409 | "작업지휘자를 지정하여 운전자와 무선으로 연락을 취하면서 모든 상황을 직접 보면서 지휘 및 통제" | descriptive_noise | `requirement` + `supervision_control` / `ctrl_work_leader_designation` |
| S0434 / S0435 | "송풍기 시험 작업장소의 작업 관계자외 출입통제" | descriptive_noise | `requirement` + `administrative_control` / `ctrl_access_restriction` |
| S0445 | "장비간 근접작업 시 유도자 배치" | descriptive_noise | `requirement` + `traffic_control` / `ctrl_traffic_guide_assignment` |
| S0451 | "옹벽 등 붕괴 우려 장소 출입통제" | descriptive_noise | `requirement` + `administrative_control` / `ctrl_access_restriction` |
| S0480 | "작업지휘자나 유도자의 지휘에 따르고…" | descriptive_noise | `procedure` + `supervision_control` / `ctrl_work_leader_designation` |
| S0488 | "전원 미차단 및 감시인 미배치" | descriptive_noise | `prohibition`(부정 서술) → hazard condition 후보 (`ctrl_standby_person_assignment` 의 반면교사 케이스) |
| S0492 | "안전작업계획서작성및작업지휘자(유도자) 배치" | descriptive_noise | `requirement` + `document_control` + `supervision_control` (1 sentence : N controls) |
| S0493 | "후진경보기와 경광등을 갖춘 지게차를 자격 보유자가 조종하는가?" | descriptive_noise | `inspection_rule` + `ctrl_backup_alarm_use` |

### 1.3 복구 규칙

아래 신호가 **단독**이 아니라 **행위/의무 결합**으로 등장하면 noise 에서 해당 rule 타입으로 복구한다.

| 신호 keyword | 복구 대상 |
|---|---|
| `보호구 + 착용/지급` | `ppe_rule` |
| `환기 + 실시/가동/확인` | `equipment_rule`(engineering) |
| `저장 + 분리/보관/격리` | `equipment_rule`(chemical_storage_segregation) |
| `점검 + 주기어(매일/매월/…)` | `inspection_rule` |
| `측정 + 값/기준/주기` | `inspection_rule` |
| `대피 + 경로/집결지` | `emergency_rule` |
| `허가 + 작업/진입/발급` | `document_rule` + permit |
| `감시인 + 배치/지정` | `requirement` + supervision |
| `차량 + 유도/분리/제한속도` | `requirement` + traffic |
| `출입 + 금지/통제/제한` | `requirement` + administrative |

### 1.4 noise 유지 규칙 (복구 제외)

아래는 신호 단어가 있어도 그대로 noise 로 둔다.

| 패턴 | 예시 | 이유 |
|---|---|---|
| 물성·성분 서술 | "본 물질은 황색 액체이다" | 대책 아님 |
| 배경·일반론 | "산업안전은 매우 중요하다" | 대책 아님 |
| 참고 안내 | "자세한 사항은 MSDS 참고" | 대책 본문 아님 |
| 단순 질의 평가문 | "…인가?", "…하는가?" (체크리스트 질문 형식) | 본질은 checklist_verification 이지만 **질문 원문**은 대책 문장으로 쓰기 어려움 → 원문 그대로 대책으로 쓰지 말고 `ctrl_checklist_verification` template 렌더링으로 대체 |

### 1.5 조치 권고

- 본 단계에서는 자동 재라벨링하지 않음. reviewer 시트에 **복구 후보 플래그** 추가를 다음 단계에서 수행.
- 지금은 문서화만 하고 법령 단계에서 법·admrul 문장에 동일 복구 규칙을 적용해 noise 율을 낮춘다.

---

## 2. 자연어 렌더링 템플릿

### 2.1 원칙
- "적절히 조치한다", "관리한다"처럼 **공허한 표현 금지**.
- 문장 끝은 평서형 종결(`~한다`) 로 통일.
- 현장 대책 문서에 들어가도 어색하지 않도록 주어·대상·동작이 모두 살아있는 문장으로.
- category · control 단위로 2 개 이상 변형 예시를 둔다(위험 상황별 재활용).

### 2.2 category 별 렌더링 예 (2개씩)

#### engineering_control
- `ctrl_fall_protection_install`
  1. "추락 위험이 있는 작업 구간에 안전난간·작업발판·개구부 덮개를 설치하고 매일 상태를 확인한다."
  2. "고소작업 구간에는 안전방망 또는 추락방호망을 설치하고 손상 여부를 작업 전 점검한다."
- `ctrl_guard_installation`
  1. "회전·절단부를 갖는 기계에는 방호장치(덮개·인터록 등)를 설치하고 임의 탈거를 금지한다."
  2. "과부하방지장치가 정상 작동하도록 유지·점검한다."
- `ctrl_machine_emergency_stop`
  1. "회전기계에 비상정지장치(e-stop)를 설치하고 작업 전 동작을 확인한다."
- `ctrl_dust_suppression`
  1. "분진 발생 구간에는 살수·이동식 집진기·방진망을 설치·운영하여 비산을 억제한다."
- `ctrl_chemical_storage_segregation`
  1. "인화성·산화성 물질은 성상별로 분리 저장하고 누출방지 방유제를 갖춘다."
- `ctrl_excavation_shoring`
  1. "굴착 구간에는 지반조건에 맞는 흙막이 지보공(토류판·어스앵커 등)을 설치한다."

#### ppe_control
- `ctrl_ppe_wear`
  1. "해당 작업에 적합한 보호구(안전모·안전대·보안경 등)를 전원 착용한다."
  2. "소음 85dB 이상 구간에서는 귀마개 또는 귀덮개를 착용한다."

#### training_control
- `ctrl_special_training`
  1. "해당 유해·위험작업 근로자에게 특별안전보건교육을 실시하고 이수대장을 작성한다."
- `ctrl_pre_work_briefing`
  1. "작업 전 TBM 을 실시하여 위험요인·작업순서·보호구를 주지시킨다."

#### inspection_control
- `ctrl_periodic_inspection`
  1. "대상 설비의 방호장치·과부하장치를 정해진 주기(매일/매월/6개월 등)로 점검하고 기록을 유지한다."
- `ctrl_pre_work_inspection`
  1. "작업 시작 전 설비와 작업환경의 이상 유무를 점검하고 이상 시 즉시 조치한다."
- `ctrl_atmospheric_measurement`
  1. "밀폐공간 진입 전 산소·유해가스 농도를 측정하고 기준값을 초과하면 진입을 금지한다."
- `ctrl_lifting_equipment_inspection`
  1. "크레인·호이스트·와이어로프 등 양중기는 작업 전 점검하고 이상 시 사용하지 아니한다."
- `ctrl_electrical_equipment_inspection`
  1. "전동공구·분전반·누전차단기의 절연저항과 접지 상태를 정기 점검한다."

#### document_control
- `ctrl_msds_posting`
  1. "취급 물질의 MSDS 와 경고표지를 작업장 잘 보이는 곳에 게시하고 비치한다."
- `ctrl_work_plan_preparation`
  1. "해당 작업의 작업계획서를 작성하고 근로자에게 교육·주지한다."
- `ctrl_lifting_work_plan`
  1. "양중작업 전 인양계획서(하중·장비·신호체계)를 작성하여 승인을 받는다."

#### supervision_control
- `ctrl_supervisor_assignment`
  1. "해당 작업에 관리감독자를 지정하여 작업을 직접 지휘하게 한다."
- `ctrl_signalman_assignment`
  1. "중량물 인양·차량계 건설기계 작업에 신호수를 배치하고 정해진 신호체계로 작업을 지휘한다."
- `ctrl_standby_person_assignment`
  1. "밀폐공간 등 고위험 작업 외부에 감시인을 상시 배치하고 이상 시 즉시 작업을 중단시킨다."
- `ctrl_fire_watch_assignment`
  1. "화기작업 중 화재감시인을 배치하고 작업 종료 후 최소 30분 이상 잔류시켜 잔불을 확인한다."
- `ctrl_work_leader_designation`
  1. "차량계 건설기계·차량계 하역운반기계 등의 작업에는 작업지휘자를 지정하여 직접 지휘하게 한다."

#### permit_control
- `ctrl_work_permit_issue`
  1. "해당 작업에 대해 작업허가서(PTW) 를 발행하고 승인 후 착수하며 작업 종료 시 종결 처리한다."
- `ctrl_confined_space_permit`
  1. "밀폐공간 진입 전 작업허가서·가스농도·환기 상태를 확인한다."
- `ctrl_hot_work_permit`
  1. "용접·용단 등 화기작업은 화기작업 허가서를 발행하고 주변 가연물을 제거한 후 실시한다."
- `ctrl_excavation_permit`
  1. "굴착 전 지하매설물과 주변 구조물을 확인하고 굴착작업 허가서를 발행한다."
- `ctrl_height_work_permit`
  1. "2m 이상 고소작업 착수 전 고소작업 허가서를 발행하고 추락방호 조치를 확인한다."

#### administrative_control
- `ctrl_access_restriction`
  1. "위험구역에는 출입금지 표지와 차단 설비를 설치하고 관계자 외 출입을 통제한다."
- `ctrl_work_area_demarcation`
  1. "작업구역 경계를 라바콘·안전선·표시띠로 물리적으로 명확히 표시한다."
- `ctrl_work_hour_restriction`
  1. "폭염·한파·야간 등 위험 시간대에는 작업을 제한하고 추가 휴식시간을 부여한다."

#### emergency_control
- `ctrl_emergency_evacuation`
  1. "비상 시 대피 경로·집결지·비상연락체계를 수립하고 근로자에게 주지한다."
- `ctrl_fire_extinguisher_setup`
  1. "작업 구간에 소화기·소화전 등 소화설비를 비치하고 사용법을 주지한다."

#### health_control
- `ctrl_special_health_check`
  1. "유해인자 노출 근로자에게 특수건강진단·배치전건강진단을 실시한다."
- `ctrl_heat_stress_management`
  1. "폭염 시 그늘막·냉방·수분공급·휴식을 제공하여 온열질환을 예방한다."

#### housekeeping_control
- `ctrl_housekeeping_cleanup`
  1. "작업장과 통로의 자재 적치·누유·분진을 정리하여 안전 통로를 확보한다."
- `ctrl_hot_work_area_clear`
  1. "용접·용단 작업 전 주변 10m 이내 가연물을 제거하거나 격리한다."

#### traffic_control
- `ctrl_traffic_guide_assignment`
  1. "중장비·차량 이동 구간에 유도자를 배치하고 반사조끼·신호봉으로 유도한다."
- `ctrl_backup_alarm_use`
  1. "후진 작업 시 후진경보와 후방감지기를 정상 동작 상태로 사용한다."
- `ctrl_vehicle_path_separation`
  1. "차량 주행로와 보행자 통로를 물리적으로 분리한다."
- `ctrl_speed_limit`
  1. "사업장 내 차량·중장비의 제한속도를 지정하고 서행을 준수한다."

---

## 3. 금지 표현 (렌더링 단계 검증)

| 금지 표현 | 대체 |
|---|---|
| "적절히 조치한다" | 구체 행위 동사로 교체 |
| "관리한다" 단독 | 대상·기준·주기 결합 |
| "주의한다" 단독 | 구체 제어 조치로 교체 |
| "한다" 주체 불명 | "사업주는 …" / "근로자는 …" 주체 명시 |

## 4. 향후 확장 지점

- category·control 별 렌더링 예시를 control master CSV 의 `description` 컬럼과 별도 관리.
- 향후 운영 DB 반영 시 `controls` 테이블에 `render_template_ko` 컬럼 추가 검토.
- 법령 문장 매핑 단계에서는 법조문 원문을 `law_ref` 로 묶고, 렌더링 문장은 현장 수용형으로 변환.

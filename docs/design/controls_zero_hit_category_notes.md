# zero-hit category 보강 메모

> v1 (400 샘플) 에서 sentence hit 이 0 건이었던 4 category 를 v2 (800 샘플) 에서 어떻게 해소했는지 기록.

---

## 해소 결과 요약

| category | v1 hit | v2 hit | 보강된 대표 control |
|---|---|---|---|
| `supervision_control` | 0 | 20 | `ctrl_work_leader_designation`(11), `ctrl_signalman_assignment`(4), `ctrl_supervisor_assignment`(3), etc. |
| `permit_control` | 0 | 12 | `ctrl_work_permit_issue`(12), `ctrl_confined_space_permit`, `ctrl_hot_work_permit` |
| `administrative_control` | 0 | 26 | `ctrl_access_restriction`(26), 기타 신규 |
| `traffic_control` | 0 | 7 | `ctrl_traffic_guide_assignment`, `ctrl_vehicle_path_separation` |

모든 zero-hit category 가 최소 7 hit 이상으로 활성화. `supervision_control` · `administrative_control` 은 20 hit 이상으로 충분한 샘플 확보.

---

## 1. supervision_control

### 대표 문장 패턴 (10+ 선별)
1. "…에 관리감독자를 지정하여 직접 작업을 지휘하도록 하여야 한다"
2. "작업을 지휘하는 자를 배치하고 작업을 지휘하게 하여야 한다"
3. "밀폐공간에서 근로자가 작업을 하는 동안 감시인을 지정하여 외부에 배치한다"
4. "중량물 인양 작업 시 신호수를 지정하여 신호체계를 준수한다"
5. "화기작업 중 화재감시인을 배치하고 작업 후 30분 이상 잔류시킨다"
6. "크레인 작업 시 미리 정한 신호방법에 따라 신호수가 수신호로 작업을 지시한다"
7. "차량계 건설기계의 운행에 유도자를 배치한다"
8. "작업지휘자는 작업순서를 결정하고 작업자를 직접 지휘한다"
9. "안전관리자는 작업장을 수시 순회하여 안전상태를 점검한다"
10. "조도·가스농도 이상 발생 시 감시인이 즉시 작업을 중단시킨다"

### 대표 키워드 / 동의어
- 관리감독자 ≡ 안전보건관리책임자
- 작업지휘자 ≡ 작업 지휘자 ≡ 작업을 지휘 ≡ 직접 지휘
- 신호수 ≡ 유도자 ≡ 유도원 ≡ 수신호
- 감시인 ≡ 감시자 ≡ 외부 감시 ≡ 입회자 ≡ standby
- 화재감시인 ≡ 화기감시 ≡ 화재감시자 ≡ fire watch

### 오탐 위험 문장
- `감시카메라를 설치한다` → engineering_control 이지 supervision 아님.
- `감시가 필요하다` 단독 → context_required.
- `입회 없이` → 부정문. 문장 구조상 금지(`prohibition`)로 분류.

### control_type 점검
- `ctrl_supervisor_assignment` : 관리감독자 배치 → 범용. `ctrl_work_leader_designation` 과 구분(차량계·하역기계 등 직접 지휘 대상).
- `ctrl_crane_signal_rule` : 크레인 신호체계 유지. `ctrl_signalman_assignment` 과 구분(신호수 배치 vs 신호체계 운영).

---

## 2. permit_control

### 대표 문장 패턴
1. "밀폐공간에서 작업 시 작업허가서를 발급받은 후 작업을 실시한다"
2. "화기작업을 하기 전에 화기작업 허가서를 발행하고 승인받는다"
3. "2m 이상 고소작업 시 고소작업 허가서를 발행하고 추락방호 확인 후 착수한다"
4. "굴착공사 착수 전 지하매설물 확인을 거쳐 굴착작업 허가를 발행한다"
5. "사업주는 작업 전 작업허가서(PTW)를 작성하여 승인을 얻어야 한다"
6. "허가증 없이 위험구역에 출입하여서는 아니 된다"
7. "작업허가 발행 내역을 기록하고 작업 종료 후 종결 처리한다"
8. "허가된 시간 외 작업은 금지된다"
9. "밀폐공간 진입허가를 받은 자만 진입할 수 있다"
10. "화기 허가가 없는 장소에서는 용접·용단을 해서는 아니 된다"

### 대표 키워드 / 동의어
- 작업허가서 ≡ 작업 허가 ≡ PTW ≡ permit to work ≡ 허가증
- 밀폐공간 작업허가 ≡ 밀폐공간 진입허가 ≡ confined space permit
- 화기작업 허가 ≡ 화기 허가 ≡ hot work permit
- 굴착작업 허가 ≡ 굴착 허가 ≡ 굴착 승인
- 고소작업 허가 ≡ 고소 허가

### 오탐 위험 문장
- `허가를 받는다` (단순 행정 표현 · 작업허가 아님) → context_required.
- `허가 번호 123456` 같은 메타정보 → descriptive_noise.
- `영업허가`·`건축허가` → permit_control 아님. 주체가 사업주/작업자 안전 허가가 아니면 제외.

### control_type 점검
- 세분 4종(밀폐/화기/굴착/고소)이 명시적 키워드 hit 시 범용(`ctrl_work_permit_issue`) 보다 우선.
- 모두 master 상위 정렬(길이 긴 keyword set) 로 자동 충족.

---

## 3. administrative_control

### 대표 문장 패턴
1. "위험구역에 관계자 외 출입을 금지하는 표지를 부착한다"
2. "작업구역에 안전펜스·바리케이드를 설치하여 외부인의 접근을 차단한다"
3. "혼재작업 시 안전보건협의체를 구성하여 작업을 조정한다"
4. "작업구역을 명확히 분리하고 동시작업 시 위험요인을 사전에 조정한다"
5. "작업구역 경계에 라바콘과 안전선으로 물리적 경계를 표시한다"
6. "폭염경보 발령 시 옥외작업을 제한하고 시간당 10분 이상 휴식을 부여한다"
7. "한파 시 옥외작업을 제한하거나 작업시간을 단축한다"
8. "야간작업 제한 시간 내에서 위험작업을 금지한다"
9. "출입통제 구간은 출입대장을 비치하고 관계자만 접근한다"
10. "작업시간 제한을 준수하여 근로자 피로도를 관리한다"

### 대표 키워드 / 동의어
- 출입금지 ≡ 출입통제 ≡ 출입 제한 ≡ 관계자 외 출입 ≡ 접근금지
- 안전선 ≡ 안전펜스 ≡ 바리케이드
- 작업구역 분리 ≡ 혼재작업 구역 ≡ 구역 분리
- 경계 표시 ≡ 라바콘 ≡ 표시띠 ≡ 구획 표시 ≡ 차단 라인
- 야간작업 제한 ≡ 폭염 휴식 ≡ 한파 휴식 ≡ 작업시간 제한 ≡ 근무시간 제한

### 오탐 위험 문장
- `출입금지 표지를 부착한다` → `ctrl_access_restriction`(admin) 이 맞지만, `부착`만 보면 document_control(`ctrl_safety_sign_posting`) 과 경쟁. master 정렬에서 `출입금지` 구체 keyword 가 우선이 되도록 보장됨.
- `입장이 금지된다` → 문장구조가 prohibition. hazard condition 문맥이면 administrative 아님.

### control_type 점검
- `ctrl_access_restriction` 이 단독으로 26 hit 을 차지 — 과잉 가능성 있음. reviewer 단계에서 split 고려.

---

## 4. traffic_control

### 대표 문장 패턴
1. "차량계 건설기계의 운행 경로에 유도자를 배치한다"
2. "후진 시 후진경보 또는 유도자로 충돌을 방지한다"
3. "작업장 내 차량 제한속도를 지정하고 서행하도록 한다"
4. "보행자 동선과 차량 주행로를 물리적으로 분리한다"
5. "중장비 이동 구간에서는 사람과 장비의 동선을 분리한다"
6. "장비 유도 시 유도자는 주황색 조끼를 착용한다"
7. "유도요원은 장비 운전자와 시야를 주고받을 수 있는 위치에 선다"
8. "야간 작업 시 유도자는 신호봉과 반사조끼를 사용한다"
9. "사업장 내 제한속도(20km/h 등)를 준수한다"
10. "후방감지기·후진경보가 정상 동작하는지 작업 전 점검한다"

### 대표 키워드 / 동의어
- 유도자 ≡ 유도원 ≡ 유도요원 ≡ 차량 유도 ≡ 장비 유도
- 후진경보 ≡ 후진 시 경보 ≡ 후진 경고음 ≡ 후방감지기
- 차량 동선 ≡ 보행자 동선 ≡ 주행로 ≡ 보행로 분리
- 제한속도 ≡ 서행 ≡ 시속 ≡ 속도 제한

### 오탐 위험 문장
- `유도자` 는 supervision(`ctrl_signalman_assignment`) 과 겹침.
  - 중량물·양중 맥락 → supervision
  - 차량·건설기계 맥락 → traffic
  - 중립 문맥이면 traffic 쪽으로 기본. master 정렬에서 traffic keyword set 이 더 구체(후진경보/차량 동선/주행로 포함)이므로 차량 맥락 자동 우선.
- `도로교통법` 참조 문장 → 작업안전 traffic 이 아님 → legal_reference 로 분류.

### control_type 점검
- `ctrl_vehicle_path_separation` / `ctrl_speed_limit` 는 v2 신규. 현재 7 hit 으로 최소 활성화.
- 양중 신호수(`ctrl_signalman_assignment`) 와 traffic 유도자(`ctrl_traffic_guide_assignment`) 의 분리가 reviewer 검토 포인트.

---

## 종합 판단

- 4 category 모두 샘플 hit 이 확보되어 reviewer 검토 라인에 들어감.
- `ctrl_access_restriction` · `ctrl_work_permit_issue` 는 과잉 hit 경향 → 정답셋 확정 시 일부 reject/split 예상.
- `traffic_control` 은 신규 control 2개에 대한 hit 이 아직 소규모 — 법령 단계 진입 후 정책법(차량계 건설기계 안전조치) 문장으로 추가 확장 가능.

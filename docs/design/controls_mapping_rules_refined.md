# 문장 → control 반자동 매핑 규칙 정밀화 (v0.2)

> v0.1 초안(`controls_mapping_rules_draft.md`) 뒤를 잇는 정밀화 버전.
> 기반: `controls_master_draft_v2.csv` (63 controls, 12 category).
> 적용 대상: 800 샘플(`sentence_control_mapping_sample_v2.csv`).

---

## 0. v0.1 대비 변경 요약

| 영역 | v0.1 | v0.2 |
|---|---|---|
| controls 수 | 47 | 63 (+16 신규) |
| zero-hit category | supervision/permit/administrative/traffic | 전부 해소 |
| 샘플 수 | 400 | 800 (400 kosha 확장) |
| 단일 토큰 규칙 | 구분만 표기 | 단일 토큰 차단 set 으로 고정 |
| 매칭 정렬 | 수동 나열 | master 의 `typical_keywords` 평균 길이 내림차순 |
| confidence 계산 | 1회 hit=medium, 2회+=high | 4글자↑ 키워드 1회 hit 도 high 승격 |

---

## 1. 1차 category 분류 규칙

### 변경 없음
- engineering / ppe / training / inspection / document / emergency / health / housekeeping
  → v0.1 규칙을 그대로 유지하되 키워드 alias 를 typical_keywords 에 녹여서 규칙을 단일 소스(master) 로 통합.

### 보강

#### supervision_control
- hit 동사: `배치`, `지정`, `입회`, `감시`, `지휘`, `상주`
- 명사 signal:
  - `관리감독자`, `안전보건관리책임자`
  - `작업지휘자`, `작업 지휘자`, `작업을 지휘`, `직접 지휘`
  - `신호수`, `유도자`, `유도원`, `수신호`, `신호체계`
  - `감시인`, `감시자`, `외부 감시`, `standby`, `입회자`
  - `화재감시인`, `화기감시`, `화재감시자`, `fire watch`
- ⚠️ context_required: `감시` 단독은 hazard condition 으로 오인될 수 있음 → 주체/대상 명사 결합 시에만 확정.

#### permit_control
- hit 동사: `허가`, `승인`, `발행`, `발급`
- 명사 signal:
  - 범용: `작업허가서`, `작업 허가`, `PTW`, `permit to work`, `허가증`
  - 세분: `밀폐공간 작업허가`, `밀폐공간 진입허가`
  - 화기: `화기작업 허가`, `화기 허가`, `hot work permit`
  - 굴착: `굴착작업 허가`, `굴착 허가`, `굴착 승인`
  - 고소: `고소작업 허가`, `고소 허가`
- 규칙: 세분 허가(밀폐/화기/굴착/고소) 키워드가 있으면 범용 `ctrl_work_permit_issue` 대신 세분 control 로 할당.

#### administrative_control
- hit 동사: `통제`, `금지`, `제한`, `설정`, `분리`, `조정`, `표시`, `부여`
- 명사 signal:
  - `출입금지`, `출입통제`, `출입 제한`, `관계자 외 출입`, `접근금지`, `안전선`, `안전펜스`, `바리케이드`
  - `작업구역 분리`, `혼재작업`, `안전보건협의체`, `합동 안전점검`
  - `경계 표시`, `라바콘`, `표시띠`, `구획 표시`, `차단 라인`
  - `야간작업 제한`, `폭염 휴식`, `한파 휴식`, `작업시간 제한`, `근무시간 제한`
- ⚠️ 부정 규칙:
  - `금지한다` 단독 + 문장 타입=`prohibition` → administrative 아님.
  - `제한한다` 단독 + 숫자 임계값 → `condition_trigger` 일 수 있으므로 hazard/condition 후보로 재분류.

#### traffic_control
- hit 동사: `배치`, `유도`, `분리`, `구분`, `준수`
- 명사 signal:
  - `유도자`, `신호수`, `차량 유도`, `장비 유도`, `유도원`, `유도요원`
  - `후진경보`, `후진 시 경보`, `후진 경고음`, `후방감지기`
  - `차량 동선`, `보행자 동선`, `주행로`, `보행로 분리`, `차량과 보행자`
  - `제한속도`, `서행`, `시속`, `속도 제한`
- ⚠️ `유도자` 는 supervision_control(`ctrl_signalman_assignment`) 과 traffic(`ctrl_traffic_guide_assignment`) 에서 겹침.
  - 차량·중장비 맥락이면 traffic.
  - 중량물 양중 맥락이면 supervision.
  - 맥락 없으면 **traffic 우선** (본 버전 선택: traffic rule 을 master 정렬에서 뒤로 두어 supervision 이 우선 승리).

---

## 2. 2차 control_type 세부 매핑 규칙

v0.1 대비 추가된 control_type 만 표기:

| sentence_type / 키워드 결합 | → control_type |
|---|---|
| equipment_rule + `흙막이`/`지보공`/`토류판`/`어스앵커` | `ctrl_excavation_shoring` |
| equipment_rule + `시스템 비계`/`쌍줄비계`/`연결재` | `ctrl_scaffold_install_std` |
| equipment_rule + `비상정지`/`e-stop`/`emergency stop` | `ctrl_machine_emergency_stop` |
| equipment_rule + `살수`/`비산먼지`/`이동식 집진기` | `ctrl_dust_suppression` |
| equipment_rule + `분리 저장`/`방유제`/`저장탱크` | `ctrl_chemical_storage_segregation` |
| inspection_rule + `크레인 점검`/`와이어로프` | `ctrl_lifting_equipment_inspection` |
| inspection_rule + `누전차단기`/`절연저항`/`분전반 점검` | `ctrl_electrical_equipment_inspection` |
| document_rule + `양중작업 계획`/`인양계획` | `ctrl_lifting_work_plan` |
| requirement + `작업지휘자 지정`/`작업을 지휘` | `ctrl_work_leader_designation` |
| permit + `굴착작업 허가` | `ctrl_excavation_permit` |
| permit + `고소작업 허가` | `ctrl_height_work_permit` |
| requirement + `경계 표시`/`라바콘` | `ctrl_work_area_demarcation` |
| requirement + `작업시간 제한`/`야간작업 제한`/`폭염 휴식` | `ctrl_work_hour_restriction` |
| requirement + `차량 동선`/`보행자 동선`/`주행로` | `ctrl_vehicle_path_separation` |
| requirement + `제한속도`/`서행` | `ctrl_speed_limit` |
| requirement + `폭염`/`열사병`/`온열질환`/`냉방` | `ctrl_heat_stress_management` |

---

## 3. 단일 토큰 확정 금지 (고정 차단 set)

```
SINGLE_TOKEN_BLOCK = {
    "관리", "조치", "확인", "준수", "주의",
    "실시", "부착", "설치",
}
```

- 이 토큰들이 keyword 배열에 포함되어 있더라도 **길이 2 글자 이하일 때는** hit 으로 치지 않음.
- 이유:
  - `관리/조치/확인` = v0.1 에서 이미 context_required 로 분류됨.
  - `실시/부착/설치` = 의무 조동사와 결합되는 흔한 본동사 → 단독이면 category 확정 불가.
- 적용 범위: `scripts/rules/build_controls_v2.py::SINGLE_TOKEN_BLOCK`.

---

## 4. context_required (문맥 결합 필수)

| 표현 | 확정 조건 |
|---|---|
| `감시` | 주체(감시인/감시자/화재감시인) 또는 대상(밀폐공간/화기) 결합 |
| `신호` | `신호체계`/`수신호`/`신호수` 또는 장비(크레인) 결합 |
| `허가` | `작업허가서`/`작업 허가` 같은 명사구 결합 |
| `유도` | `유도자`/`차량 유도`/`장비 유도` 결합 |
| `배치` | 주체(관리감독자·감시인·신호수·유도자) 결합 |
| `제한` | 대상(출입/속도/시간) 결합 |
| `표시` | 대상(안전보건표지/경계/구획) 결합 |

---

## 5. risk_overfit 경고

master 정렬 후에도 과잉 매칭이 우려되는 control:

| control | 우려 | 대응 |
|---|---|---|
| `ctrl_incident_report` | `보고`/`신고` 단독 hit 으로 법정 보고 조항까지 대거 끌려옴 | reviewer 단계에서 split 후보 — 중대재해/재해 원인 보고 구분 |
| `ctrl_guard_installation` | `방호장치` 가 너무 범용 | 세분 control(`ctrl_machine_emergency_stop`) 을 master 상위 정렬에 두어 먼저 매칭 |
| `ctrl_access_restriction` | `출입금지/통제` 가 긴 법조문에 자주 출현 | zero-hit 해소 목적은 달성 — confidence medium 이상은 reviewer 검토 |
| `ctrl_work_permit_issue` | `허가` 단어만으로도 매칭 | 세분 permit control(밀폐/화기/굴착/고소) 이 master 상위 정렬 |

---

## 6. negative rules (이 표현이면 해당 control 금지)

| 문장 특성 | 금지 대상 control |
|---|---|
| `~제외한다`/`~적용하지 아니한다` (scope_exclusion) | 모든 control |
| `~이란 …을 말한다` (definition) | 모든 control |
| `제○○조에 따라` 만 포함 (legal_reference) | 모든 control |
| 부정문 `~해서는 아니 된다` | 해당 동작의 engineering/administrative control 금지. prohibition 으로만 유지. |
| `지급한다` + `보호구 지급` 명사 부재 | `ctrl_ppe_provision` 금지 (ppe_wear 와 혼동) |

---

## 7. confidence 계산(v0.2)

```
1. 매칭된 keyword 수 = N
2. 4자 이상 구체 keyword hit 이 1개 이상 → has_specific = True
3. conf = "high"    if N >= 2 or has_specific
         "medium"  otherwise
4. eligible sentence_type 이 아니면 conf = "low" + code 공란
```

- v0.1 대비 변화: 4자↑ 구체 keyword 1회 hit 만으로도 high 승격 (예: `밀폐공간 작업허가`).

---

## 8. 동의어·alias (master 통합)

v0.2 부터는 동의어 테이블을 별도 문서에 두지 않고 master `typical_keywords` 파이프 구분으로 단일화.

예시 — 이미 master 에 반영됨:
- 보호구 ≡ 개인보호구 ≡ PPE
- 국소배기장치 ≡ 국소배기 ≡ 배기설비 ≡ 환기장치 ≡ 후드 ≡ LEV
- 안전난간 ≡ 안전난간대 ≡ 가드레일 (일부)
- 유도자 ≡ 유도원 ≡ 유도요원
- 출입금지 ≡ 출입통제 ≡ 출입 제한 ≡ 접근금지 ≡ 안전선 ≡ 안전펜스 ≡ 바리케이드

---

## 9. 반영 지점

- 규칙 로직: `scripts/rules/build_controls_v2.py`
- master 출처: `data/risk_db/master/controls_master_draft_v2.csv`
- 샘플 확장: `data/risk_db/master/sentence_labeling_sample_v2.csv`
- 결과 매핑: `data/risk_db/master/sentence_control_mapping_sample_v2.csv`
- reviewer 검토용: `data/risk_db/master/sentence_control_review_sheet.csv` (v1 72 hit 기반 · v2 분 별도 검토 시 확장 필요)

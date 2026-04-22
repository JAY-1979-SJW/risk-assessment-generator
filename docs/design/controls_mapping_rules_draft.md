# 문장 → control 반자동 매핑 규칙 초안 (v0.1)

> 대상: 반자동 분류기 입력용 규칙. 400 샘플 CSV 기반.
> **오탐 가능성 큰 규칙**은 `⚠️ risk_overfit` 표기.
> **단일 토큰**으로 확정하는 규칙은 `⚠️ context_required` 표기.

---

## 1. category-level 매핑 규칙 (1차 필터)

### engineering_control
- **hit 동사**: `설치`, `부착`, `고정`, `차단`, `밀폐`, `방호`, `격리`
- **명사 signal**: `안전난간`, `방호장치`, `가드`, `국소배기장치`, `환기장치`, `인터록`, `덮개`
- AND sentence_type ∈ {`requirement`, `equipment_rule`}

### ppe_control
- **hit 동사**: `착용`, `지급`, `사용하게`, `교체`
- **명사 signal**: `보호구`, `안전모`, `안전대`, `안전화`, `방진마스크`, `호흡보호구`, `내화학장갑`, `보안경`, `보호복`
- 부정어 결합 시 → `ppe_wear_prohibit` 별도 (현 초안 미포함)

### training_control
- **hit 동사**: `실시`, `주지`, `숙지`
- **명사 signal**: `교육`, `특별교육`, `안전보건교육`, `안전교육`, `훈련`, `TBM`, `작업 전 교육`
- ⚠️ `교육자료`·`교육미디어` 단독은 `descriptive_noise` — context_required

### inspection_control
- **hit 동사**: `점검`, `측정`, `시험`, `검사`, `확인`
- **주기어**: `매일`, `매월`, `6개월마다`, `연 1회`, `작업 전`, `작업 시작 전`
- AND sentence_type ∈ {`inspection_rule`, `requirement`}

### document_control
- **hit 동사**: `작성`, `비치`, `게시`, `보존`, `기록`, `부착`(표지)
- **명사 signal**: `MSDS`, `물질안전보건자료`, `경고표지`, `관리대장`, `보고서`, `안전보건규정`
- ⚠️ `부착` 은 engineering_control 과 중복 가능 — 명사로 구분

### supervision_control
- **hit 동사**: `배치`, `지정`, `입회`, `감시`
- **명사 signal**: `관리감독자`, `작업지휘자`, `신호수`, `감시인`, `화재감시인`, `안전관리자`

### permit_control
- **hit 동사**: `허가`, `승인`, `발행`
- **명사 signal**: `작업허가서`, `밀폐공간 작업허가`, `화기작업 허가`, `고소작업 허가`

### administrative_control
- **hit 동사**: `통제`, `금지`, `제한`, `설정`
- **명사 signal**: `출입금지`, `출입통제`, `작업구역`, `안전표지`, `작업계획서`
- ⚠️ `금지한다` 만 있는 문장 ≠ administrative_control. sentence_type=`prohibition` 과 구분 필요.

### emergency_control
- **hit 동사**: `대피`, `응급조치`, `구조`, `신고`, `통보`
- **명사 signal**: `비상대응계획`, `비상연락망`, `대피로`, `집결지`, `화재`, `소화기`

### health_control
- **hit 동사**: `실시`(건강진단), `관리`, `노출`
- **명사 signal**: `특수건강진단`, `배치전검진`, `작업환경측정` (→ inspection 과 중복)
- ⚠️ 대부분 inspection/document 와 overlap — 1순위는 그쪽, 2순위로 health

### housekeeping_control
- **hit 동사**: `정리`, `청소`, `제거`, `배수`
- **명사 signal**: `적치`, `통로`, `미끄럼`, `누유`, `분진 정리`

### traffic_control
- **hit 동사**: `유도`, `분리`, `차단`
- **명사 signal**: `차량 동선`, `중장비 유도`, `작업구역 분리`, `출입구 통제`(차량)

---

## 2. type-level 세부 매핑 규칙 (2차 확정)

| sentence_type / 키워드 결합 | → control_type |
|---|---|
| equipment_rule + `안전난간`/`개구부 덮개`/`작업발판` | `ctrl_fall_protection_install` |
| equipment_rule + `국소배기`/`환기장치` | `ctrl_local_ventilation_install` |
| equipment_rule + `방호장치`/`가드`/`회전부` | `ctrl_guard_installation` |
| equipment_rule + `기동장치 잠`/`LOTO` | `ctrl_lockout_tagout` |
| ppe_rule + action=`wear` | `ctrl_ppe_wear` |
| ppe_rule + action=`provide` | `ctrl_ppe_provision` |
| education_rule + `특별교육` | `ctrl_special_training` |
| education_rule + `작업 전 교육`/`TBM` | `ctrl_pre_work_briefing` |
| inspection_rule + 주기어(`매일`·`매월`·`6개월마다`) | `ctrl_periodic_inspection` |
| inspection_rule + `밀폐공간`/`산소농도` | `ctrl_atmospheric_measurement` |
| inspection_rule + `체크리스트`/`점검표` | `ctrl_checklist_verification` |
| document_rule + `MSDS`/`경고표지` | `ctrl_msds_posting` |
| document_rule + `보존`/`기록` | `ctrl_record_retention` |
| emergency_rule + `대피`/`비상연락` | `ctrl_emergency_evacuation` |
| supervision_control + `화재감시인` | `ctrl_fire_watch_assignment` |
| supervision_control + `감시인`(밀폐공간) | `ctrl_standby_person_assignment` |
| housekeeping + `정리`/`적치`/`통로` | `ctrl_housekeeping_cleanup` |
| traffic + `신호수`/`유도` | `ctrl_traffic_guide_assignment` |
| administrative + `출입금지`/`출입통제` | `ctrl_access_restriction` |
| permit + `작업허가서` | `ctrl_work_permit_issue` |

---

## 3. 동의어·유사어 테이블

| 대표 | 동의어 (같은 control 로 묶음) |
|------|---|
| `보호구` | 개인보호구 / PPE |
| `안전난간` | 안전난간대 / 가드레일 |
| `국소배기장치` | 국소배기 / 배기설비 / LEV |
| `방호장치` | 가드 / 안전덮개 / 인터록 |
| `특별교육` | 특별안전교육 / 특별안전보건교육 |
| `작업 전 교육` | TBM / 툴박스미팅 / 조회 |
| `작업환경측정` | 환경측정 / 유해인자 측정 |
| `경고표지` | 주의표지 / 안전보건표지 |
| `작업허가서` | 작업허가 / PTW |
| `감시인` | 감시자 / 스탠바이 |

---

## 4. 구분이 필요한 유사어

| 표현 A | 표현 B | 구분 기준 |
|--------|--------|----------|
| `점검` (장비) | `측정` (환경) | 측정은 정량값 산출 (dB·ppm·lx 등) |
| `차단` (에너지) | `격리` (공간) | 에너지 흐름 vs 작업 구역 |
| `부착` (표지) | `부착` (장비 고정) | document_control vs engineering_control |
| `금지` (문장 구조) | `금지구역 설정` | sentence_type=prohibition vs administrative_control |
| `대피` | `피난` | 동일 (emergency_evacuation 으로 통합) |

---

## 5. 문맥이 없으면 판단 금지 (context_required)

| 표현 | 이유 |
|------|------|
| `관리` 단독 | 너무 광범위 — 관리 주체·대상에 따라 category 달라짐 |
| `조치` 단독 | 의미 공허 — 구체 동사 결합 필요 |
| `확인` 단독 | inspection 일 수도, document 일 수도 |
| `준수` 단독 | 규정 이행의 일반 서술 — control 아님 |
| `주의` 단독 | caution 이지 control 이 아님 |

---

## 6. control 이 **아닌** 표현 (hazard/condition 으로 재분류)

| 표현 | 실제 분류 |
|------|----------|
| `추락 위험이 있는` | condition (`height_work`) 또는 hazard (`추락`) |
| `유해물질에 노출` | hazard 노출, condition=`hazardous_substance` |
| `밀폐공간` | condition=`confined_space` |
| `용접·용단` 작업 | condition=`hot_work` + work_type 매핑 |
| `중량물 취급` | hazard (`중량물`) |
| `2m 이상의 고소` | condition=`height_work`, quantity_threshold 병행 |

---

## 7. confidence 지침

| confidence | 조건 |
|-----------|------|
| `high` | category + type 둘 다 확정 키워드 hit + 반례 없음 |
| `medium` | category 는 확정, type 은 키워드 overlap 있음 (reviewer 확정 필요) |
| `low` | context_required 표기 항목만 hit, 또는 2 개 이상 type 후보 경쟁 |

---

## 8. 오탐 위험 표기

| 규칙 | 표기 | 비고 |
|------|-----|------|
| "점검 실시" 만 hit → inspection | `⚠️ risk_overfit` | 실제 대상(설비/환경)에 따라 type 달라짐 |
| "작성" 단독 → document_rule | `⚠️ context_required` | 보고서·계획서·점검표 구분 |
| "부착" 단독 → engineering | `⚠️ context_required` | 표지 부착은 document |
| "관리" 단독 | `⚠️ context_required` | 대부분 noise |
| "확인" 단독 | `⚠️ context_required` | 절차적 확인 vs 점검 구분 |

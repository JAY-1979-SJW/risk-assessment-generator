# 문장 분류 규칙 초안 (v0.1)

> 대상: 반자동 분류기 입력용. 샘플 CSV 에 `*_candidate` 를 채우는 규칙.
> **단일 키워드만으로 확정하는 규칙에는 `⚠️ context_required` 표기**.

---

## 1. sentence_type 규칙

### requirement
- **hit 패턴**: `하여야 한다`, `해야 한다`, `설치하여야`, `비치하여야`, `갖추어야`, `지급하여야`, `실시하여야`, `마련하여야`, `확인하여야`
- obligation_level → `mandatory`
- 반례: `할 수 있다` (허용, 의무 아님) → `recommended`

### prohibition
- **hit 패턴**: `해서는 아니 된다`, `해서는 안 된다`, `금지한다`, `출입하지 아니하도록`, `하여서는 안`
- obligation_level → `prohibited`

### caution
- **hit 패턴**: `주의`, `유의`, `조심`, `신중히`
- ⚠️ "주의" 단독은 context_required (물성 설명의 "주의" 도 있음)

### procedure
- **hit 패턴**: `작업 순서`, `작업방법`, `다음 순서`, `① ② ③`, `첫째`, `둘째`, `셋째`
- ⚠️ 순서 표기만 있고 단일 항목이면 개별 항목으로 재분할 대상

### condition_trigger
- **hit 패턴**: `~인 경우`, `~할 때`, `~시`, `~이상`, `~이하`, `~때에는`
- 같은 문장에 `requirement` 신호도 있으면 **양쪽 병기** 가능 (sentence_type 은 1순위만 저장, reviewer_note 기록)

### equipment_rule
- **hit 패턴 (장비/설비)**: `안전난간`, `방호장치`, `과부하방지장치`, `이동식 크레인`, `고소작업대`, `리프트`, `승강기`, `비계`, `국소배기장치`, `환기장치`, `용접기`
- AND (`requirement` | `inspection_rule` | `prohibition` 신호 결합)
- 장비 명만 있고 설명이면 noise 혹은 `descriptive_noise`

### ppe_rule
- **hit 패턴**: `보호구`, `안전모`, `안전대`, `안전화`, `방진마스크`, `호흡보호구`, `내화학장갑`, `보안경`, `귀마개`, `보호복`
- action = `wear` | `provide`
- 자주 오는 동사: `착용`, `지급`, `비치`

### inspection_rule
- **hit 패턴**: `점검`, `측정`, `검사`, `확인하여야`, `주기`, `매일`, `매주`, `매월`, `6개월마다`, `연 1회`
- action = `inspect` | `measure`

### education_rule
- **hit 패턴**: `교육`, `특별교육`, `안전보건교육`, `안전교육`, `훈련`, `이수`, `교육시간`
- action = `train`
- ⚠️ `교육자료`, `교육미디어` 는 자료 참조 → `descriptive_noise` 가능

### document_rule
- **hit 패턴**: `작성`, `게시`, `비치`, `보존`, `기록`, `MSDS`, `물질안전보건자료`, `경고표지`, `기록·보존`, `보고서`
- action = `prepare` | `post` | `provide` | `record` | `report`
- ⚠️ 보고서 "작성" 은 해당 / 일반 "작성" 은 보류

### emergency_rule
- **hit 패턴**: `비상`, `대피`, `응급`, `구조`, `피난`, `화재 발생 시`
- condition_type = `incident_emergency`

### legal_reference
- **hit 패턴**: `제○조`, `별표`, `고시 제`, `같은 법`, `이 규칙`, `산업안전보건법`
- 본문 실체 규정이면 참조 + 다른 타입 병기

### scope_exclusion
- **hit 패턴**: `제외한다`, `적용하지 아니한다`, `다만`, `예외`
- obligation_level = `exception`

### definition
- **hit 패턴**: `"○○"이란 …을 말한다`, `의미한다`, `정의한다`, `○○란`
- action_type = `none` 고정

### descriptive_noise
- 아래 **noise 규칙** 섹션 참조.

---

## 2. obligation_level 매핑 규칙 (요약)

| 신호 | level |
|------|-------|
| 하여야 / 해야 | mandatory |
| 해서는 아니 | prohibited |
| 하도록 권고 / 바람직 | recommended |
| 주의 / 유의 | cautionary |
| (신호 없음) | informative |
| 다만 / 제외 | exception |

---

## 3. subject_type 매핑 규칙

| 신호 (문장 주어부) | subject |
|---------------|---------|
| 사업주는 / 사업주가 | employer |
| 관리감독자는 / 작업지휘자는 | supervisor |
| 안전관리자는 / 보건관리자는 | safety_manager |
| 근로자는 / 근로자가 | worker |
| 도급인은 / 수급인은 | contractor |
| (장비 주어 — "크레인은 …을 갖춘다") | equipment |
| 사업장에는 / 작업장에는 | workplace |
| MSDS / 경고표지 / 관리대장 | document |
| 그 외 | mixed_or_unknown |

⚠️ 한국어는 주어 생략이 잦음. 생략 시 인근 조문 주어 맥락 참조 (context_required).

---

## 4. action_type 매핑 규칙

| 동사 어근 | action |
|-----------|--------|
| 설치 | install |
| 점검 / 검사 | inspect |
| 측정 | measure |
| 착용 | wear |
| 지급 / 비치 | provide |
| 교육 / 훈련 | train |
| 게시 | post |
| 작성 / 준비 | prepare |
| 기록 | record |
| 보고 / 신고 | report |
| 격리 / 차단 / 폐쇄 | isolate |
| 환기 | ventilate |
| 청소 / 제거 | clean |
| 보관 / 저장 | store |
| 출입금지 | prohibit_access |
| 감시 / 모니터링 | monitor |
| 유지 / 정비 | maintain |

---

## 5. condition_type 규칙

| 신호 | condition |
|------|-----------|
| `N명 이상`, `N톤 이상`, `N미터 이상` | quantity_threshold |
| `크레인`, `리프트`, `고소작업대` + "사용" | equipment_presence |
| `관리대상`, `특별관리`, `유해·위험물질` | hazardous_substance |
| `밀폐공간`, `산소결핍` | confined_space |
| `고소`, `추락 우려`, `2m 이상` | height_work |
| `양중`, `인양`, `들어올리는` | lifting_operation |
| `전기`, `충전전로`, `활선` | electrical_work |
| `용접`, `용단`, `화기작업` | hot_work |
| `강풍`, `폭염`, `우천`, `한랭` | weather_environment |
| `혼재작업`, `동시작업`, `복수 사업주` | simultaneous_work |
| `매일`, `매월`, `○개월마다` | periodic_schedule |
| `작업 시작 전`, `작업 종료 후` | before_after_work |
| `재해 발생 시`, `사고 발생 시` | incident_emergency |
| `○○명 이상 사업장` | legal_scope |
| — | none_or_unknown |

---

## 6. noise 규칙 (descriptive_noise 판정)

아래 조건이 **모두** 충족되면 noise:
1. `requirement` / `prohibition` / `caution` 신호 없음
2. 아래 "단독 noise 어휘" 중 하나 이상 포함
3. 숫자 조건 임계값 없음

### 단독 noise 어휘
`참고`, `정보`, `특성`, `증상`, `질병`, `사실`, `설명`, `안내`,
`보건기준`(단독), `일반정보`, `물리화학적 특성`, `배경`, `개요`,
`교육미디어`, `교육자료`(단독), `제외 근로자`, `지급되고`(단독)

### 단, 아래 signal 과 결합되면 noise 가 아니다
- 보호구 (`ppe_rule` 복구)
- 환기·국소배기 (`equipment_rule`)
- 저장·보관 + 위험물질 (`equipment_rule` + `store`)
- 측정·점검 주기 (`inspection_rule`)
- MSDS 의무 ("작성·게시·비치" 결합) (`document_rule`)

### MSDS 상투 문장
- "경고표지 예방조치 문구를 참고하세요." → `descriptive_noise` (단, 같은 문장에 의무 신호 없을 때)
- "해당 물질은 물리화학적 특성에 따라 …" → noise
- "자세한 내용은 별지 참고" → noise

---

## 7. confidence 지침

| confidence | 조건 |
|-----------|------|
| `high` | 확정 키워드 단일 hit + 반례 없음 |
| `medium` | 키워드 hit 있으나 context_required 표시된 항목 |
| `low` | 신호 미미 / 여러 축 충돌 / reviewer 판단 권장 |

---

## 8. 미정의 축 (다음 단계 이관)

| 축 | 상태 | 비고 |
|----|------|------|
| `controls` master | 미존재 | 실제 현장 대응조치(예: "안전난간 설치", "LOTO", "출입통제") 코드화 필요. 본 분류의 `action_type` 과 별도 master. |
| `trigger → result` 연결 | 부분 | 조건 문장과 결과 문장을 link 하는 joint schema 는 후속 단계. |
| 판례/재해사례 연결 | 미정 | KOSHA 중대재해사례 문장은 `descriptive_noise` 가 아니라 별도 `incident_case` 타입 도입 검토. |

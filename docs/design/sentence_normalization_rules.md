# 문장 정제 규칙 (v0.1)

> 대상: 자동 정제기 입력용 규칙 모음.
> 본 규칙은 `sentence_labeling_sample_v2.csv` (800 샘플)을 1차 적용 대상으로 하며,
> 결과는 `sentence_normalization_sample_v1.csv` 로 내보낸다.
>
> 원칙
> - 원문 보존, 정제는 별도 필드.
> - subject/object 자동 확정 금지(후보만).
> - noise → rule 복구는 **행위 결합**이 명확할 때만.
> - split 은 의미 손실 없는 범위 내에서만.

---

## 1. 적용 순서 (파이프라인)

입력 문장 1건에 대해 다음 순서로 규칙을 적용한다.

```
1) header_strip        — 조문 번호/장절 헤더 제거
2) incomplete_check    — 항/절 단편(Q11) 판정 → sentence_role=metadata 로 조기 분기
3) evidence_check      — 참조만 있는 문장(Q08) 판정 → sentence_role=evidence
4) noise_check         — descriptive_noise / MSDS 상투(Q05/Q09) 판정
   4-1) noise_recover   — 복구 신호 결합 시 rule 복귀
5) split_decide        — Q01/Q06/Q07 분해 수행
6) vague_normalize     — Q04 추상 수식어 정규화
7) subject_infer       — Q02 주어 후보 복원
8) object_infer        — Q03 대상 후보 복원
9) role_assign         — sentence_role 최종 결정
10) flag_set           — ambiguity / context_required / duplicate 후보 flag
11) confidence_set     — confidence 산정
```

---

## 2. header_strip (조문 번호/장절 헤더 제거)

### 제거 대상
문장 **시작부**에서 아래 토큰을 제거한다(문장 중간은 그대로 유지).

- `제\s*\d+\s*조\s*\([^)]+\)\s*` : "제5조(고용관리 책임자)"
- `제\s*\d+\s*조의?\s*\d*\s*` : "제7조의2"
- `①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮` 문두 연속 1~3회
- `제\s*\d+\s*항\s*` : "제1항"
- `<개정\s*\d{4}\.\d{1,2}\.\d{1,2}(,\s*\d{4}\.\d{1,2}\.\d{1,2})*>` : "<개정 2010.6.4>"
- `<신설\s*\d{4}\.\d{1,2}\.\d{1,2}>` : "<신설 2011.7.25>"
- `\d+\.\s*` 선행 번호(문두에 한함, 전체 문장 길이가 짧지 않을 때만)

### 주의
- 조문 번호 텍스트는 `evidence_candidate` 에 기록한다. (예: "산안법 제29조")
- `header_strip` 수행 시 `normalization_type` 에 `header_strip` 추가.

---

## 3. incomplete_check (Q11)

### 판정
아래 중 하나 이상 충족 시 `sentence_role = metadata` 로 고정, 이후 규칙은 건너뜀.

- 원문 어절 수 ≤ 3 이면서 종결어미(`~한다`, `~이다`) 없음
- 토큰이 `나.`, `다.`, `3.`, `가.`, `④` 등 단독 항 번호만 있음
- 조문 헤더만 있고 본문 없음 (header_strip 후 남은 텍스트 길이 < 4 글자)

결과:
- `sentence_role = metadata`
- `noise_flag = 1` (rule 대상 아님)
- `quality_issue_codes = Q11`
- `normalization_type = header_strip`

---

## 4. evidence_check (Q08)

### 판정
아래 패턴 + 실체 의무 동사 없음 → `sentence_role = evidence`.

- `제\s*\d+\s*조(에 따라|에 의하여|의 규정에 따라)`
- `별표\s*\d+` 단독
- `같은 법\s*제\s*\d+\s*조`
- `이 규칙\s*제\s*\d+\s*조`
- `(고시|훈령)\s*제\s*\d+\s*호`

### 실체 의무 동사
다음 동사 어근이 **결합**되어 있으면 evidence_only 가 아니라 rule_core 후보.
- 설치 / 점검 / 측정 / 착용 / 지급 / 교육 / 작성 / 게시 / 비치 / 신고 / 보고 / 허가 / 대피

결과:
- `sentence_role = evidence`
- `evidence_candidate` 에 참조 토큰 기록
- `control_candidate` 비움
- `noise_flag = 0`
- `quality_issue_codes = Q08`

---

## 5. noise_check (Q05/Q09)

### 5.1 noise 판정 조건 (**모두 충족**)

1. 의무·금지·주의 신호 어휘 없음:
   - 없음 셋: `하여야 한다`, `해야 한다`, `금지`, `해서는 아니`, `지급`, `착용`, `설치`, `점검`, `측정`, `교육`, `게시`, `비치`, `허가`, `대피`, `감시`, `출입통제`, `작성`
2. 숫자 임계값(수량/높이/면적/농도) 없음
3. 아래 "noise 단독 어휘" 중 하나 이상 포함
   - `참고하세요`, `자세한 내용`, `일반정보`, `설명`, `배경`, `개요`
   - `증상`, `질병`, `본 물질은`, `특성`, `물리화학적`
   - `중요하다`, `바람직하다` (단독)
   - `교육미디어`, `교육자료`(단독), `OPL 참고`
   - `다음과 같다` (서술적 나열 도입)

결과:
- `noise_flag = 1`
- `sentence_role = explanation`
- `quality_issue_codes = Q05` (MSDS 상투 추가 시 `Q05,Q09`)
- `normalization_type = noise_mark`

### 5.2 noise_recover (복구 후보)

noise 로 판정된 문장 중 아래 **행위 결합 신호**가 있으면 `noise_recovery_candidate = 1` 로 남기고
정제 문장을 `sentence_role = rule_core` 로 바꾸되 `confidence = low`.

| 신호 조합 | 복구 대상 role/action |
|-----------|------------------------|
| `보호구` + (`착용`\|`지급`) | rule_core / wear or provide |
| `환기` + (`실시`\|`가동`\|`확인`) | rule_core / ventilate |
| `저장` + (`분리`\|`보관`\|`격리`) | rule_core / store |
| `점검` + (매일\|매월\|`주기`\|`6개월`\|연 1회) | rule_core / inspect |
| `측정` + (`값`\|`기준`\|`주기`) | rule_core / measure |
| `대피` + (`경로`\|`집결지`) | rule_core / mixed(emergency) |
| `허가` + (`작업`\|`진입`\|`발급`) | rule_core / prepare |
| `감시인` + (`배치`\|`지정`) | rule_core / monitor |
| `차량` + (`유도`\|`분리`\|`제한속도`) | rule_core / mixed(traffic) |
| `출입` + (`금지`\|`통제`\|`제한`) | rule_core / prohibit_access |
| `작업지휘자` + (`지정`\|`배치`) | rule_core / monitor |

`normalization_type = noise_recover` 추가.

### 5.3 noise 유지(복구 제외)

- 물성·성분 서술 (`본 물질은`, `~이다`)
- 참고 안내 (`자세한 내용은`, `참고하세요`)
- 단순 질의문 (`~인가?`, `~하는가?`): 본질은 점검·확인이지만 원문을 그대로 대책으로 쓰지 말 것.
  `sentence_role = explanation` 유지 + `reviewer_note = question_form`.

---

## 6. split_decide (Q01/Q06/Q07)

### 6.1 split 가능 패턴 (우선 분해)

| 패턴 | 예시 | split 결과 |
|------|------|------------|
| A하고 B하여야 한다 | "국소배기장치를 설치하고 정기적으로 점검하여야 한다." | ①설치, ②점검 |
| A·B·C 를 … 한다 (열거) | "안전모·안전대·보안경을 지급하여야 한다." | ①안전모 지급, ②안전대 지급, ③보안경 지급 |
| A 및 B, A 또는 B | "작성 및 게시하여야 한다." | ①작성, ②게시 |
| A인 경우 B 한다 (Q06) | "높이 2m 이상에서 작업하는 경우 안전대를 착용한다." | ①condition: 2m 이상 작업, ②rule_core: 안전대 착용 |
| ~전/후 A 한다 | "작업 시작 전 산소농도를 측정한다." | split 하지 않음(조건절과 rule 이 일체) |

### 6.2 split 금지 패턴 (분해 불가)

| 패턴 | 이유 |
|------|------|
| 단일 동사 종결 | 굳이 쪼갤 여지 없음 |
| 같은 행위를 부연 | "정기적으로, 즉 6개월마다 점검한다." |
| 법령 단일 정의문 | definition 문장 |
| 조건 다단 중첩 | "A이면서 B인 경우 C 한다" — 조건 다단은 하나로 유지(condition_candidate 주요 1개만 기록) |
| 분리하면 주어·대상이 붕괴 | "설치·운영하여 성능을 유지한다" (단일 행위 묶음) |

### 6.3 상속 규칙

split 수행 시 각 분해 단위에 공통으로 상속:
- `source_sentence_id`, `source_type`, `document_id`, `document_title`
- `subject_candidate` (원문에서 확정적으로 복원 가능할 때만)
- `evidence_candidate` (조문 참조)
- `condition_candidate` (조건절이 앞쪽에 있고 공통 적용 시)

개별 산정:
- `action_candidate`, `object_candidate`
- `hazard_candidate`, `equipment_candidate`, `control_candidate`
- `sentence_role`

### 6.4 split 후 의미 손실 위험 사례

- "설치·운영": 하나로 유지(복합행위 control 로 취급)
- "작성·게시·비치": 3개로 분해(document_rule 별 action 이 다름)
- "관리·감독": 하나로 유지(추상 수식에 가까움 — ambiguity_flag)
- "지급·착용": 2개로 분해(주체가 다름: 사업주 지급 / 근로자 착용 → subject_candidate 다르게 상속)

---

## 7. vague_normalize (Q04 추상 표현 정규화)

### 7.1 삭제 대상(의미 손실 적음)

정규화 규칙: 다음 수식어를 문장에서 제거하고 `normalization_note: vague=<원어>` 로 기록.

- `적절한`, `적절히`, `적절하게`
- `충분한`, `충분히`
- `안전하게`, `확실히`, `철저히`
- `신속히`, `즉시`, `지체 없이` (rule 문장에서 제거 — 시간 조건이 아닌 부사적 사용일 때)

예:
- "적절한 보호구를 착용하여야 한다" → "보호구를 착용하여야 한다" + `normalization_type=vague_remove`, `normalization_note=vague=적절한`

### 7.2 플래그 대상(의미 손실 큼)

아래는 삭제 시 의미가 붕괴되므로 원형 유지 + `ambiguity_flag = 1`, `normalization_type = vague_flag`.

- "필요한 조치를 하여야 한다" (무엇의 조치인지 불명)
- "이상이 없도록 하여야 한다" (무엇의 이상?)
- "노력하여야 한다" (의무 강도 모호)
- `관리한다`, `조치한다` 단독 (대상·기준·주기 결여)

### 7.3 control 매핑 시 low_weight 처리

- `ambiguity_flag = 1` 레코드는 control_candidate 가 붙어도 `confidence = low` 고정.

---

## 8. subject_infer (Q02 주어 보정)

### 8.1 주어 사전

- `사업주`, `관리감독자`, `안전관리자`, `보건관리자`, `근로자`, `작업자`,
  `도급인`, `수급인`, `원수급인`, `하수급인`
- 장비 주어(설비 자체): `크레인`, `리프트`, `고소작업대`, `국소배기장치` 등
- 문서 주어: `MSDS`, `경고표지`, `관리대장`

### 8.2 보정 규칙

1. 문장 시작이 위 주어 사전 + 조사(`는/가/이/은`) 로 시작 → `subject_candidate` 고정.
2. 시작이 번호/기호/부사로 시작 → 직전 **같은 document_id** 의 문장에서
   마지막으로 등장한 주어를 **상속 후보** 로 가져옴. 그러나:
   - 직전 문장이 설명·정의이면 상속 **금지**.
   - 동일 조항(문서 제목에 같은 조 번호)일 때만 상속.
3. 복원 불가 시 `subject_candidate = ""` 유지. 자동으로 "사업주" 라고 쓰지 않는다.
4. 복수 주어(예: "원수급인과 수급인") → `subject_candidate = mixed_or_unknown`.

### 8.3 기록

- 상속 수행 시 `normalization_type = subject_infer`.
- 상속 근거는 `normalization_note: subject_from=S0032` 등.

### 8.4 임의 확정 금지 사유

- 한국어 법령·KOSHA 문체는 주어 생략이 많으나, 조문 경계를 넘어가면 주어가 달라질 수 있음.
- 잘못된 주어 확정은 이후 sentence_type ↔ subject_type 조합 판정을 오염시킨다.

---

## 9. object_infer (Q03 대상 보정)

### 9.1 보정 우선순위

**object 복원이 subject 복원보다 엔진 기여도가 크다.** (control 매핑에 직접 쓰임)

1. 문장 내 "목적어 + 동사" 구조가 있으면 그 목적어를 object_candidate 로 저장.
   - 예: "국소배기장치를 설치" → object=국소배기장치
2. 문장 내 목적어가 없으면, 같은 문장 앞쪽 명사구(조건절 포함)에서 후보 추출.
   - 예: "지정하고 이를 고용노동부장관에게 신고" → object=고용관리 책임자 (앞 문맥에서)
3. 복원 불가 시 `object_candidate = ""`.

### 9.2 대상 사전 (예시)

- 장비/설비: 안전난간, 작업발판, 국소배기장치, 방호장치, 비계, 크레인, 호이스트, 분전반, 누전차단기 등
- 보호구: 안전모, 안전대, 보안경, 방진마스크, 내화학장갑 등
- 문서: 작업계획서, MSDS, 경고표지, 관리대장, 점검표, 허가서
- 행위 노무: 특별안전보건교육, TBM, 작업지휘자 지정

### 9.3 기록

- 상속 수행 시 `normalization_type = object_infer`.

---

## 10. role_assign (sentence_role 최종 결정)

각 정제 문장에 대해 다음 기준으로 role 을 부여한다.

| 조건 | sentence_role |
|------|---------------|
| 의무/금지 동사 + 구체 대상 결합 | rule_core |
| 조건절만 있고 rule 없음 (split 후 조건 단위) | condition |
| 참조만 있음 (Q08) | evidence |
| 설명/배경 (Q05/Q09) noise | explanation |
| 위험요인만 서술 | hazard_statement |
| 대책만 서술 (rule 없이 control 서술만) | control_statement |
| 제외·예외 (scope_exclusion) | exception |
| 조문/장절/항 번호 | metadata |
| 자동 판정 곤란 | unresolved |

주의: `sentence_type`(기존 분류)과 `sentence_role`(정제 역할)은 별개 축.

---

## 11. flag_set (플래그 부여)

| 플래그 | 조건 |
|--------|------|
| `ambiguity_flag` | 추상 수식어 정규화 대상인데 삭제 시 의미 손실(§ 7.2) |
| `context_required_flag` | 문장 내 지시어(`이 경우`, `그 밖에`, `같은 조`, `해당`) 포함 및 subject/object 복원 실패 |
| `noise_flag` | § 5.1 충족 |
| `noise_recovery_candidate` | § 5.2 충족 |

### duplicate_flag (Q10)
- 같은 `document_id` 내에서 `action_candidate + object_candidate` 동일한 레코드 쌍 탐지 시 `normalization_note: possible_duplicate_of=<id>` 기록.
- 자동 통합은 **금지**. reviewer 확인용 후보 플래그만.

---

## 12. confidence_set

| confidence | 조건 |
|-----------|------|
| high | split 성공 + subject·object 둘 다 복원 + ambiguity=0 + evidence/noise 아님 |
| medium | 일부 후보 비었거나 split 경계 일부 모호. 그러나 sentence_role 확정. |
| low | noise_recover / ambiguity=1 / context_required=1 / 어느 rule 후보도 확정 못함 |

---

## 13. 파이프라인 구현 경계

본 단계에서 자동화 가능 범위:
- header_strip, incomplete_check, evidence_check, noise_check, noise_recover, split_decide,
  vague_normalize, object_infer, role_assign, flag_set, confidence_set

부분 자동화(추후 정밀화 필요):
- subject_infer (문맥 상속)
- duplicate_flag (같은 문서 내 비교만, 문서 간 중복 미검출)

자동화 금지:
- subject/object 임의 확정
- noise 자동 삭제(원문 보존)
- 운영 DB 반영

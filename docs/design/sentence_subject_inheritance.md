# 주어 상속/복원 설계 (v0.2)

> 목적: `sentence_normalization_sample_v1.csv` 기준 Q02(주어 결손) 484건 / rule_core 기준 239건을
> **상속·사전 확장·문법 패턴 보강**으로 실질적으로 완화한다.
>
> 연계: `sentence_normalization_rules_v2.md`, `sentence_normalization_schema.md` § 2.3.
>
> 원칙
> - **임의 확정 금지**. 후보(candidate) 만 채운다.
> - 상속은 "보수적 기본값"이 아니라 "근거가 있는 상속"만 허용한다.
> - 상속 출처(`inherited_subject_from`) 를 반드시 기록한다.
> - 복수 주체 충돌 시 `subject_candidate = mixed_or_unknown` + `ambiguity_flag = 1`.

---

## 1. v1 진단

v1 로직:
- 문장 선두에 `{주어}{는/은/이/가/에게/에서}` 매칭 시 direct 고정
- 매칭 실패 시 직전 문장의 주어가 있으면 같은 `document_id` 에서 상속 시도

v1 한계(800 샘플 실측):
- **사전 협소**: `경영책임자등`, `법무부장관`, `법원`, `국토교통부장관`, `이사장`, `이사회` 등 법령 주체가 누락
- **조사 매칭 실패**: "사업주 또는 경영책임자등은" 같은 복수 주체 결합 패턴을 잡지 못함
- **kosha 상속 부재**: kosha 문서의 `작업자`/`근로자`/`관리자` 기본 주체 상속 없음
- **상속 경계 모호**: 동일 `document_id` 전체에서 상속 → 조항 경계를 넘어도 상속되는 위험

결과: Q02(주어 결손) 484건, rule_core 기준 239건(kosha 196 / law 34 / licbyl 6 / expc 3).

---

## 2. v2 복원/상속 4단계 우선순위

주어 후보는 다음 순서로 검사하여 **처음 성공한 단계**로 확정 후보를 정한다.
각 단계의 성공 여부는 `subject_candidate_confidence` 에 반영한다.

### 2.1 P1 — 같은 문장 내 직접 탐지(direct)

- 문장 어느 위치든 `{주어명}(은|는|이|가|에게|에서)` 패턴이 있으면 direct.
- 문두 선행은 가산점. 문중 출현은 candidate 로 채우되 `direct_pos = mid`.
- **복수 주체 결합 패턴**(v2 신설):
  - `A 또는 B(은|는|이|가)` → 첫 단일 주체와 두번째 주체를 모두 확인, 같은 범주(예: 사업주·경영책임자등 → `employer`)면 단일 code 채택.
  - 범주가 다르면 `mixed_or_unknown` + `ambiguity_flag = 1`.

→ `subject_candidate_direct` 에 저장, `subject_candidate_confidence = direct_high`.

### 2.2 P2 — 같은 split_group 안 선행 문장 상속

- 원문 1건을 split 한 경우, **같은 `split_group_id`** 의 order 1 문장에서 direct 로 확정된 주어가 있으면 후행 piece 에 상속.
- 상속 근거: `inherited_subject_from = split_group:order=1`.
- split 이 없을 때는 skip.

→ `subject_candidate_inherited`, `subject_candidate_confidence = inherited_split`.

### 2.3 P3 — 같은 조항/같은 document_title 내 직전 direct 주어 상속

- **조항 경계**: 같은 `document_id` **그리고** 같은 `document_title` 의 연속 문장에서
  직전 direct 주어가 있으면 상속.
  - v1 의 "같은 document_id 전체" 상속보다 좁혀서 오상속을 줄인다.
- 상속 금지:
  - 직전 문장이 `definition` / `explanation` / `metadata` 면 상속 금지.
  - 직전 문장과 의무 방향이 상이(예: 직전 `prohibition` + 현재 `requirement`) 해도 상속 금지하지 않음(주체는 상속해도 무방). 단, 주체 자체가 `equipment/document/workplace` 면 상속 금지.
- 상속 근거: `inherited_subject_from = prev:{prev_sample_id}`.

→ `subject_candidate_confidence = inherited_prev`.

### 2.4 P4 — source_type 별 default 주체

- P1~P3 모두 실패하고 sentence_role 이 `rule_core | control_statement` 일 때만 적용.
- `subject_candidate_inherited` 에 default code 를 채우고 confidence 는 낮게 표시.
- default 주체는 "**가장 보수적인 추정**"이며 reviewer 검토 대상으로 남긴다.

| source_type | default subject | 적용 조건 |
|-------------|------------------|-----------|
| law / admrul / licbyl | (없음, 공란 유지) | 법령 문장은 주체 혼동 위험이 크므로 default 를 강제하지 않는다 |
| expc | (없음, 공란 유지) | 해석례는 주체 명시 부재 시 reviewer 큐 |
| kosha | `worker` | KOSHA 안전 자료는 작업자 수행 지침 비중이 높음(보수적 추정) |

- kosha default 는 `subject_candidate_confidence = default_kosha_worker` 로 표시.
- reviewer 는 `employer`/`supervisor` 로 승격 여부를 확인.

### 2.5 어느 단계에서도 복원 실패

- `subject_candidate` 공란 유지. `ambiguity_flag` 는 부여하지 않는다(Q02 자체가 결손 코드이기 때문).
- `subject_candidate_confidence = unresolved`.

---

## 3. 주체 사전 확장 (v2)

### 3.1 법령 주체 (law / admrul / licbyl / expc)

**기존** (v1):
원수급인 / 하수급인 / 도급인 / 수급인 / 사업주 / 관리감독자 / 작업지휘자 / 안전관리자 / 보건관리자 / 근로자 / 작업자 / 고용노동부장관 / 사업장 / 작업장.

**추가** (v2):
- `경영책임자등` → `employer` (중대재해처벌법 주체; 사업주와 같은 범주로 취급)
- `법인 또는 기관의 경영책임자등` → `employer`
- `사업주 또는 경영책임자등` → `employer` (복수 결합)
- `법무부장관`, `국토교통부장관`, `고용노동부장관` → `authority`
- `법원`, `검사`, `피고인`, `변호인` → `judicial`
- `이사회`, `이사장` → `board`
- `건설근로자공제회` → `authority`
- `공제회`, `공단`, `협회`, `공제조합`, `사업주단체` → `authority`
- `정부` → `authority`
- `소방본부장`, `소방서장` → `authority`
- `지방자치단체의 장` → `authority`
- `관할청`, `관계 행정기관의 장` → `authority`

### 3.2 KOSHA 주체

- `작업자` → `worker`
- `관리자`, `안전관리자`, `보건관리자`, `현장소장` → `supervisor`
- `사용부서`, `점검자`, `운전자` → `worker`
- `회사`, `사업장` → `workplace` (조직 주체)

### 3.3 장비/문서 주체 (기존 유지)

- 크레인·리프트·국소배기장치 등 → `equipment`
- MSDS·경고표지·관리대장 등 → `document`

---

## 4. 문법 패턴 보강

### 4.1 "A 또는 B" 복수 주체 결합

- `(사업주|도급인) 또는 경영책임자등(은|는|이|가)` → `employer` (단일)
- `원수급인 또는 하수급인` → `contractor`
- `고용노동부장관 또는 [기관장]` → `authority`
- 범주 다른 결합 → `mixed_or_unknown` + `ambiguity_flag = 1`

### 4.2 "A 및 B" 결합 주어

- `사업주 및 근로자` → `mixed_or_unknown` (주체 방향 상이)
- `원수급인과 수급인` → `contractor` (같은 범주)

### 4.3 문두 괄호 보정

- "( ) 사업주는" 처럼 여는 괄호 뒤 주어 → 괄호 내부를 무시하고 주어 매칭.

---

## 5. 저장 필드 (v2)

v2 에서 다음 컬럼을 추가한다(v1 의 `subject_candidate` 는 유지).

| 필드 | 설명 |
|------|------|
| `subject_candidate_direct` | P1 성공 시 채움 |
| `subject_candidate_inherited` | P2/P3/P4 성공 시 채움 |
| `subject_candidate` | direct 우선, 없으면 inherited (호환용) |
| `subject_candidate_confidence` | `direct_high` / `direct_mid` / `inherited_split` / `inherited_prev` / `default_kosha_worker` / `unresolved` |
| `inherited_subject_from` | 상속 근거 문자열 (예: `split_group:order=1`, `prev:S0120-01`) |

---

## 6. 상속 금지 케이스 (명시)

다음의 경우 상속 자체를 시도하지 않는다.

- 직전 문장의 `sentence_role` ∈ {`definition`, `explanation`, `metadata`}
- 직전 문장의 `subject_candidate` 가 `equipment` | `document` | `workplace`
- 현재 문장의 `sentence_role` ∈ {`metadata`, `evidence`, `exception`}
- 현재 문장이 단편(Q11) 으로 이미 metadata 로 분기됨
- 현재 문장에서 P1 (direct) 가 실패했으나 `subject_candidate` 가 장비/문서/작업장일 가능성이 큰 어휘(예: "크레인", "MSDS") 를 주어 위치에 가진 경우

---

## 7. Ambiguity / 반례

| 상황 | 처리 |
|------|------|
| "관리감독자 또는 안전관리자는" | supervisor · safety_manager 범주 상이 → `mixed_or_unknown` + `ambiguity_flag = 1` |
| "도급인 및 수급인은" | 모두 `contractor` → `contractor` 단일 |
| "사업주(법인인 경우에는 대표자를 말한다)" | `employer` + 괄호 내용은 정의 |
| P3 상속 중 문서 제목이 바뀜 | 상속 중단, unresolved |
| P4 kosha 기본 `worker` 후 실체 주어가 "관리자" 로 확정 | `subject_candidate` 를 `supervisor` 로 교체하며 `override_note` 에 `replaced_default` 기록 |

---

## 8. 기대 효과 (800 샘플 기준 목표)

- Q02(주어 결손) 484건 → **목표 ≤ 200건** (약 -60%)
- rule_core 중 주어 결손 239건 → **목표 ≤ 80건**
- default_kosha_worker 가 과다하게 붙지 않도록 확인
  - rule_core 가 아닌 문장(explanation 등)에는 default 미적용
- 상속 경계 과확장 방지
  - 같은 document_title 조항 내에서만 상속 허용

검증 지표는 `sentence_normalization_sample_v2.csv` 와 `sentence_normalization_diff_v1_v2.csv` 에서 확인한다.

# 문장 정제(normalization) 스키마 (v0.1)

> 목적: 원문 문장을 "엔진이 판단 가능한 최소 단위"로 분해·정규화한 결과를
> 저장할 구조를 정의한다.
>
> **원문은 보존**하고, 정제 결과는 별도 레코드로 둔다. 한 원문 문장은
> **여러 정제 문장**(split_group) 으로 확장될 수 있다.
>
> 연계:
> - 품질 이슈 유형: `docs/design/sentence_quality_issue_taxonomy.md`
> - 정제 규칙: `docs/design/sentence_normalization_rules.md`
> - 샘플 산출: `data/risk_db/master/sentence_normalization_sample_v1.csv`

---

## 1. 설계 원칙

1. 원문은 **read-only**. 정제는 새 레코드에 기록한다.
2. 원문 1건 → 정제 N건(N ≥ 1) 관계를 허용한다. N=1 인 경우도 split_group_id 는 발급한다.
3. 정제는 "요약"이 아니라 **분해/정규화/구조화**이다.
   - split: 복합문 분해
   - normalize: 추상 표현 정규화, 주어/대상 복원 후보
   - role: rule_core/condition/evidence/explanation/… 구분
4. 확정값과 후보값을 구분한다.
   - `*_candidate` 는 자동 추정치. 확정 아님.
   - `normalization_status` 로 자동/재검토/수동 구분.
5. control/hazard/condition/evidence 를 같은 필드에 섞지 않는다.
6. sentence_type (원문 분류 축) 과 sentence_role (정제 후 역할) 은 별개로 운용한다.

---

## 2. 레코드 필드 정의

정제 결과 한 행(row)은 **정제 문장 단위**이다.

### 2.1 식별자 / 출처

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `normalized_sentence_id` | string | Y | 정제 문장 고유 ID. 예: `N0001-01` (원문 S0001 의 split 1번) |
| `source_sentence_id` | string | Y | 원문 sample_id (예: S0001) |
| `source_type` | string | Y | law / admrul / licbyl / expc / kosha |
| `document_id` | int | Y | 원문 문서 id |
| `document_title` | string | N | 원문 문서 제목 |

### 2.2 원문/정제문

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `raw_sentence_text` | text | Y | 원문 문장. **삭제/수정 금지** |
| `normalized_sentence_text` | text | Y | 정제 결과 문장. split 시 분해 단위 |
| `normalization_status` | enum | Y | `auto` / `auto_flagged` / `needs_review` / `manual` |
| `split_group_id` | string | Y | 원문 단위 그룹 키(= source_sentence_id) |
| `split_order` | int | Y | split 순번. split 없을 때 1 |
| `was_split` | bool | Y | split 수행 여부(0/1) |
| `normalization_type` | string | Y | 적용된 정규화 유형. 쉼표로 다중 기록. 값은 § 3. 참조 |

### 2.3 역할·후보 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `sentence_role` | enum | Y | `rule_core` / `condition` / `evidence` / `explanation` / `hazard_statement` / `control_statement` / `exception` / `metadata` / `unresolved` |
| `obligation_level_candidate` | enum | N | mandatory / prohibited / recommended / cautionary / informative / exception |
| `subject_candidate` | string | N | 복원된 주어 후보(employer/worker/contractor/supervisor/…/mixed_or_unknown) |
| `object_candidate` | string | N | 복원된 대상 후보(장비/문서/행위 노무) |
| `action_candidate` | string | N | install/inspect/measure/wear/provide/train/post/prepare/record/report/isolate/ventilate/clean/store/prohibit_access/monitor/maintain/mixed_or_unknown |
| `condition_candidate` | string | N | quantity_threshold/height_work/confined_space/… (sentence_classification_schema § 2.5) |
| `hazard_candidate` | string | N | 추락/낙하/감전/질식/끼임/화재 등 |
| `equipment_candidate` | string | N | 기존 equipment master code (예: EQ_SCAFF) |
| `control_candidate` | string | N | 기존 controls_master_draft_v2 의 control_code (예: ctrl_fall_protection_install) |
| `evidence_candidate` | string | N | 참조 법조문 표기(예: "산안법 제29조", "별표 4") |

### 2.4 플래그·노트

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `noise_flag` | bool | Y | 설명·배경·상투문 여부 |
| `noise_recovery_candidate` | bool | Y | noise 이나 제어 신호 결합으로 복구 후보 |
| `ambiguity_flag` | bool | Y | 추상 표현 등으로 확정 곤란 |
| `context_required_flag` | bool | Y | 인접 문맥 필요 |
| `quality_issue_codes` | string | Y | Q01..Q12 중 적용된 코드(쉼표 구분) |
| `confidence` | enum | Y | high / medium / low |
| `normalization_note` | text | N | 적용한 규칙·상속·삭제·이유 기록 |
| `reviewer_note` | text | N | 사람 검토 의견 |

---

## 3. normalization_type 허용값

여러 값이 동시에 적용될 수 있고 쉼표로 나열한다.

| 값 | 의미 |
|----|------|
| `no_change` | 변경 없음(split 없음, 정규화 없음) |
| `split_action` | 복합 행위 split 수행 |
| `split_condition` | 조건/rule split 수행 |
| `split_enum` | 열거(·,및,또는) split 수행 |
| `vague_remove` | 추상 수식어 삭제 |
| `vague_flag` | 추상 표현 정규화 불가 → flag |
| `subject_infer` | 주어 후보 복원 |
| `object_infer` | 대상 후보 복원 |
| `noise_mark` | noise 로 분기 |
| `noise_recover` | noise 에서 rule 복구 |
| `header_strip` | 조문 번호/장절 헤더 제거 |
| `evidence_isolate` | 법조문 참조만 남은 문장으로 분리 |
| `duplicate_flag` | 중복 의미 탐지 flag |
| `manual_override` | 사람 검토 수동 확정 |

---

## 4. sentence_type ↔ sentence_role 관계

- `sentence_type` (기존 sentence_classification_schema 의 축) 은 **원문 분류**에 쓴다.
- `sentence_role` 은 **정제 후 역할**에 쓴다.
- 매핑 예:

| 원문 sentence_type | 정제 후 sentence_role 주요 값 |
|--------------------|----------------------------------|
| requirement / prohibition / equipment_rule / ppe_rule / inspection_rule / education_rule / document_rule / emergency_rule | rule_core (+ 일부 control_statement) |
| condition_trigger | condition |
| legal_reference | evidence |
| definition / descriptive_noise | explanation |
| scope_exclusion | exception |
| procedure | rule_core (split 후 개별 행위) |
| caution | rule_core (단, 약한 의무) |

- 한 원문에서 split 된 문장은 **서로 다른 role** 을 가질 수 있다.
  예: 조건문(condition) + 의무문(rule_core).

---

## 5. ID 규칙

- 정제 문장 ID: `{sample_id}-{split_order:02d}` (예: `S0123-01`, `S0123-02`)
- split 이 없어도 `-01` 을 부여한다.
- `split_group_id` = `sample_id`. split 은 항상 같은 원문 안에서 번호를 이어 붙인다.

---

## 6. 상속 규칙 (split 시)

split 수행 시 다음 속성은 기본적으로 **상속**한다.
- `source_sentence_id`, `source_type`, `document_id`, `document_title`
- `subject_candidate` (원문에서 복원 가능한 경우에 한해)
- `condition_candidate` (선행 조건절에서 상속)
- `evidence_candidate` (조문 참조)

다음은 split 단위로 **개별 산정**한다.
- `action_candidate`, `object_candidate`
- `hazard_candidate`, `equipment_candidate`, `control_candidate`
- `obligation_level_candidate`
- `sentence_role`
- `quality_issue_codes`
- `confidence`

---

## 7. 품질 이슈 코드 매핑 (quality_issue_codes)

`sentence_quality_issue_taxonomy.md` 의 Q01..Q12 코드를 쓴다.
한 정제 문장에 복수 코드 적용 가능(쉼표 구분).

예:
- `Q01,Q04` — 복합 행위 + 추상 수식어
- `Q06,Q02` — 조건/의무 혼합 + 주어 생략
- `Q05,Q09` — noise(MSDS 상투)

---

## 8. 저장 포맷

- **CSV(샘플 산출)**: `data/risk_db/master/sentence_normalization_sample_v1.csv`
  - 컬럼 순서는 § 2 의 정의 순서와 동일.
- **diff 산출**: `data/risk_db/master/sentence_normalization_diff_sample.csv`
  - raw vs normalized 비교 / 주요 변경 요약.

---

## 9. 다음 단계 연결 (controls / 법령)

정제 결과는 다음 단계의 입력으로 사용된다.

1. **controls 정밀화**
   - `control_candidate` 만 추린 집합 → 기존 `sentence_control_mapping_sample_v2` 와 병합
   - `sentence_role = rule_core | control_statement` 만 매핑 대상
2. **법령 조문 구조 분해**
   - `source_type ∈ {law, admrul, licbyl}` + `normalization_status != metadata`
   - condition_candidate + rule_core 쌍으로 조문 단위 trigger→rule 그래프 구성
3. **위험성평가표 감소대책 문장 렌더링**
   - rule_core 중 `control_candidate` 존재 + `ambiguity_flag = 0` 만 1차 대상
   - `controls_noise_and_rendering.md` § 2 템플릿으로 렌더

---

## 10. 운영 반영 원칙

- 본 단계는 **설계·샘플 산출**까지만 수행하고 운영 DB 반영은 금지한다.
- 향후 반영 시에는 별도 테이블(예: `sentence_normalized`)을 만들고 원문 테이블과 1:N 외래키로 연결한다.
- 현재 DB 스키마(`risk_assessment_db_schema.sql`)는 이 단계에서 수정하지 않는다.

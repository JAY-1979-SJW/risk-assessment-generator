# 중복 의미(duplicate semantics) 탐지 설계 (v0.1)

> 목적: 표현은 다르지만 의미가 같은 문장(Q10)을 자동 플래그한다.
> 자동 통합/삭제는 금지하고, reviewer 판단용 **canonical 후보**만 지정한다.
>
> 연계: `sentence_normalization_rules_v2.md`, `sentence_quality_issue_taxonomy.md` § Q10.

---

## 1. 중복 탐지 원칙

- 자동 삭제 금지. duplicate_flag 만 부여.
- canonical 지정은 후보(`canonical_candidate`). reviewer 가 최종 확정.
- 문서 간 중복은 보수적으로(같은 control_candidate + action + object 일치 시에만).
- 서로 다른 `source_type` 간에는 canonical 을 강제 결합하지 않는다(법령 vs KOSHA).

---

## 2. 중복 유형 4종

### 2.1 `exact_duplicate`

- **정의**: 공백·구두점을 제외한 `normalized_sentence_text` 가 완전히 일치.
- **판별**: `normalize_for_compare(text)` 가 동일.
- **예시**: 같은 KOSHA 문서 안에서 같은 경고 문구가 반복.

### 2.2 `near_duplicate`

- **정의**: 텍스트 Jaccard 유사도가 높은 문장 쌍(토큰 기준).
- **판별**:
  - 한국어 토큰(어절 기반) 집합 Jaccard ≥ 0.8
  - 길이 차 ≤ 25%
  - 같은 `document_id` 내부에서만 비교(기본)
- **예시**: "안전모를 착용한다" vs "안전모를 반드시 착용한다."

### 2.3 `same_control_variant`

- **정의**: 다른 표현이지만 같은 control 을 가리키는 문장 쌍.
- **판별**:
  - `control_candidate` 동일
  - `action_candidate` 동일
  - `object_candidate` 동일 또는 alias 동일
  - `sentence_role` 동일(rule_core|control_statement)
  - 같은 `document_id` 내
- **예시**:
  - "안전난간을 설치한다." / "추락방지 안전난간을 갖춘다." — 둘 다 `ctrl_fall_protection_install` / install / 안전난간.

### 2.4 `same_rule_different_surface`

- **정의**: control 까지 동일하지 않아도, 의무 구조가 동일(`action + object + obligation_level + role`).
- **판별**:
  - `action_candidate` 동일
  - `object_candidate` 동일 또는 alias
  - `obligation_level_candidate` 동일
  - `sentence_role` 동일
  - 같은 `document_id` 내
  - Jaccard ≥ 0.5

---

## 3. object alias 사전

중복 판정에 쓰는 alias 그룹(기본 셋):

| 대표 object | alias |
|---|---|
| 안전모 | 안전모, 헬멧 |
| 안전대 | 안전대, 안전벨트, 안전그네 |
| 안전화 | 안전화, 작업화 |
| 보안경 | 보안경, 고글, 보호안경 |
| 보호구 | 보호구, 개인보호구, PPE |
| 안전난간 | 안전난간, 안전난간대, 난간 |
| 작업발판 | 작업발판, 발판 |
| 국소배기장치 | 국소배기장치, LEV, 국소배기, 후드 |
| 방호장치 | 방호장치, 가드, 안전덮개, 인터록 |
| 작업계획서 | 작업계획서, 작업계획, 작업순서서 |
| MSDS | MSDS, 물질안전보건자료, 안전보건자료 |
| 경고표지 | 경고표지, 경고표시 |
| 작업허가서 | 작업허가서, 허가서, PTW |
| 특별안전보건교육 | 특별안전보건교육, 특별교육, 안전교육 |

같은 그룹에 속하면 object 동일로 간주.

---

## 4. 비교 범위

- **기본**: 같은 `document_id` 내부.
- **확장** (옵션): 같은 `source_type` 내에서 `control_candidate` 가 동일한 그룹만.
- **금지**: `source_type` 이 서로 다른 문장 간 canonical 연결.

---

## 5. canonical 후보 선정 규칙

같은 중복 그룹에서 아래 우선순위로 `canonical_candidate = 1` 을 부여한다.

1. `subject_candidate` 가 direct(`direct_high`) 인 문장
2. `ambiguity_flag = 0`
3. `noise_flag = 0`
4. `normalized_sentence_text` 길이가 **가장 짧은** 문장(잔여 잡음 적음)
5. 위 조건 동점 시 `normalized_sentence_id` 오름차순 첫 번째

canonical 외 문장에는 `canonical_candidate = 0` 과 `duplicate_of = {canonical_id}`, `duplicate_type = {exact_duplicate|near_duplicate|same_control_variant|same_rule_different_surface}` 을 기록한다.

---

## 6. 저장 필드 (v2)

| 필드 | 설명 |
|------|------|
| `duplicate_flag` | 0/1. 중복 그룹에 속하면 1 |
| `duplicate_type` | 위 4종 중 하나 |
| `canonical_candidate` | 0/1 |
| `duplicate_of` | canonical 문장의 `normalized_sentence_id` |
| `duplicate_group_id` | 같은 그룹의 공통 id(예: `DG0001`) |

---

## 7. 탐지 우선 대상

`sentence_labeling_sample_v2.csv` 와 v1 결과에서 중복이 자주 관찰된 카테고리:

- **착용** 계열: "안전모·안전대·보안경을 착용한다" 반복
- **설치** 계열: "방호장치·안전난간을 설치한다" 반복(특히 KOSHA 문서)
- **점검** 계열: "작업 전 점검한다" 반복
- **게시/비치/작성** 계열: "MSDS·경고표지 게시·비치" 반복
- **교육** 계열: "안전보건교육·특별교육 실시" 반복

v1 에서 같은 `document_id + action + object` 쌍을 공유하는 잠재 중복 rows 25건 / groups 10개를 실측으로 확인.

---

## 8. 처리 금지

- 자동 삭제 금지. duplicate 문장도 정제 결과 테이블에 전부 유지.
- canonical 이 아닌 문장의 `control_candidate` 를 지우지 않는다(집계에서 dedupe 는 다운스트림에서 수행).
- `source_type` 경계 넘는 canonical 지정 금지.
- `sentence_role = metadata | evidence | explanation` 문장은 중복 탐지 대상에서 제외.

---

## 9. 한계

- Jaccard 기반 near-duplicate 는 표현 변형에 약함 — 향후 임베딩 기반 확장 여지.
- alias 사전이 협소하므로 v2 단계에서 누락 그룹이 있을 수 있음.
- `same_rule_different_surface` 는 의미 일치이지만 실제 제어가 달라질 수 있어 `canonical_candidate` 취소 여지가 큼 → reviewer 필수.

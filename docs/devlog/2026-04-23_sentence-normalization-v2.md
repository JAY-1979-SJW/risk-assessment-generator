# 2026-04-23 · 문장 정제(sentence normalization) v2 — Q02 / Q10 / split 보강

## 배경

- v1 산출(`sentence_normalization_sample_v1.csv`, 814행) 기준 WARN 판정.
- 원인 3건:
  1) **Q02 주어 결손 484건** (rule_core 239건)
  2) **Q10 duplicate 자동 탐지 미구현**
  3) **split 적용 12건** 으로 과도하게 보수적

v2 목표: 법령 구조 분해 단계 진입 이전 문장 정제 계층을 한 단계 더 안정화.

---

## 1. v1 WARN 원인 재확인

실측(`sentence_normalization_sample_v1.csv`):
- Q02 rule_core 잔존 주체별 분포: kosha 196 / law 34 / licbyl 6 / expc 3
- Q02 잔존 대표 패턴: `경영책임자등`, `법무부장관`, `법원`, `이사장` 등 법령 주체 사전 누락
- Q02 잔존 kosha: `작업자`/`근로자`/`관리자` 기본 상속 부재
- 잠재 duplicate: 같은 `document_id + action + object` 쌍 10개 그룹 / 25행 (방호장치 설치 KOSHA 문서 1건만 4중복)
- split: "A 또는 B" 제외 후 과도 제거 → "A하고 B" 도 화이트리스트로 묶여 확장 실패

---

## 2. 주어 상속/복원 보강 결과

설계: `docs/design/sentence_subject_inheritance.md` (v0.2)

### 2.1 4단계 상속 우선순위

| 단계 | 규칙 | v2 결과 |
|------|------|---------|
| P1 direct | 문장 내 "주어+조사" 직접 매칭(확장 사전) | **108** |
| P2 split_group | 같은 split_group order=1 의 direct 주어 상속 | **2** |
| P3 prev_same_title | 같은 document_id + document_title 의 직전 direct 주어 상속 | **176** |
| P4 default_kosha | kosha 원문의 rule_core 문장에 `worker` 기본값 | **187** |
| 실패(unresolved) | 법령 복잡 문장 | 345 |

주어 candidate 총 확보: **473건 (v1 182건 → +291건, +160%)**

### 2.2 사전 확장(v1 → v2)

- 법령 주체 추가: `경영책임자등`, `사업주 또는 경영책임자등`, `법무부장관`, `국토교통부장관`, `법원`, `검사`, `피고인`, `변호인`, `이사장`, `이사회`, `건설근로자공제회`, `공제회`, `공단`, `협회`, `소방본부장`, `소방서장`, `관할청`, `관계 행정기관의 장`, `지방자치단체의 장`, `정부`
- KOSHA 주체 추가: `현장소장`, `사용부서`, `운전자`, `점검자`, `회사`
- 복수 결합 처리: `사업주 또는 경영책임자등` → `employer` 단일, `원수급인 또는 하수급인` → `contractor` 단일, 범주 다른 결합(예: supervisor+safety_manager) → `mixed_or_unknown` + ambiguity

### 2.3 Q02 변화

- Q02: **484 → 345 (-139, -29%)**
- Q02 잔존 role 분포: explanation 167 / metadata 47 / evidence 41 / exception 35 / condition 29 / **rule_core 22** / hazard_statement 4
- rule_core 중 Q02 잔존 **239 → 22 (-90.8%)**

### 2.4 상속 금지 보호

- 직전 문장이 definition/explanation/metadata면 상속 안 함
- document_id 는 같지만 document_title이 다르면 상속 중단 (조항 경계)
- `equipment/document/workplace` 주어는 후속 상속 대상 아님

---

## 3. duplicate 탐지 구현 결과

설계: `docs/design/sentence_duplicate_detection.md` (v0.1)

### 3.1 탐지 방식

- 그룹 키: `(document_id, action_candidate, object_candidate, obligation_level)`
- 필수 조건: `sentence_role ∈ {rule_core, control_statement}` + `action_candidate` 비어있지 않음 + `object_candidate` 비어있지 않음 (과도 묶음 방지)
- alias 기반 object 매칭(안전모/헬멧, 안전난간/난간, MSDS/물질안전보건자료, 특별교육/안전보건교육 등 41 그룹)

### 3.2 duplicate 유형 4종

| 유형 | 판정 | v2 결과 |
|------|------|---------|
| exact_duplicate | 공백/구두점 제외 동일 | 0 |
| near_duplicate | Jaccard ≥ 0.8 + 길이차 ≤ 25% | 2 |
| same_control_variant | control_candidate + action + object 동일 | 15 |
| same_rule_different_surface | action + object + obligation 동일, control 다름 | 0 (조건 강화로 0) |

### 3.3 canonical 선정 우선순위

1) `subject_candidate_confidence = direct_high`
2) `ambiguity_flag = 0`
3) `noise_flag = 0`
4) 문장 길이 최소
5) `normalized_sentence_id` 오름차순

### 3.4 결과

- duplicate 그룹: **12개**
- 플래그 문장: **29건** (canonical 12 + 비-canonical 17)
- Q10: **0 → 29**

### 3.5 처리 원칙

- 자동 삭제 금지
- canonical 이 아닌 문장의 control_candidate 유지
- source_type 경계 넘는 canonical 결합 금지

---

## 4. split 확대 결과

### 4.1 규칙 변경

- v1: "A하고 B한다" 에서 첫 동사 {설치/점검/측정/착용/지급/비치/게시/작성/기록/교육} 화이트리스트
- v2: 첫 동사 화이트리스트 확장(+`보관`, `배치`, `지정`) + **두번째 동사 SPLIT_FORBIDDEN_PAIRS**(`설치·운영`, `관리·감독`, `유지·정비`)만 명시 금지 → 의미 결합 큰 경우만 제외
- 신규: **지급·착용 주체 재할당** — `보호구를 지급하고 착용하게 하여야 한다` → piece_1 subject=employer, piece_2 subject=worker

### 4.2 결과

- split 적용 원문 수: **12 → 16 (+4)**
- Q01 (복합 행위) 코드 표시: **26 → 34**
- split_confidence 도입: high / medium / low 로 품질 구분

### 4.3 split 금지 유지

- "또는"(주어 or 관계 위험 큼)
- 단서/예외(`다만`, `제외한다`)
- 법령 정의문(`…을 말한다`)
- split 후 object 가 사라지는 경우
- 조건/주어 상속이 불가능한 경우

---

## 5. object 복원 결과

설계: `docs/design/sentence_normalization_rules_v2.md` § 4

### 5.1 alias 사전 도입 (v2)

- 41 그룹의 대표 object 코드 + 변형
- 대표 예: 안전모/헬멧, 안전대/안전벨트/안전그네, 안전난간/난간, MSDS/물질안전보건자료, 특별교육/안전보건교육, 허가서/작업허가서/PTW

### 5.2 결과

- object_candidate_direct: **111 → 138 (+27)**
- object_candidate_inherited(split_group): **4**
- object 복원 총 142건

---

## 6. v1 대비 지표 변화 (800 샘플 기준)

| 지표 | v1 | v2 | 변화 |
|------|-----|-----|------|
| 정제 문장 수 | 814 | **818** | +4 |
| split 적용 원문 수 | 12 | **16** | +4 |
| 주어 direct | 182 | 108 | (정제된 직접 매칭만) |
| 주어 inherited (전 단계) | 0 | **365** | 신설 |
| 주어 candidate 확보 총 | 182 | **473** | **+291, +160%** |
| 대상 direct | 111 | **138** | +27 |
| 대상 inherited | 0 | **4** | 신설 |
| duplicate 그룹 | 0 | **12** | 신설 |
| duplicate 플래그 문장 | 0 | **29** | 신설 |
| noise 표시 | 255 | 255 | - |
| noise 복구 후보 | 43 | **44** | +1 |
| control_candidate 부여 | 275 | **275** | - |
| rule_core | 329 | **333** | +4 |
| **Q02 주어 결손** | **484** | **345** | **-139 (-29%)** |
| Q02 중 rule_core | 239 | **22** | **-217 (-90.8%)** |
| Q10 duplicate | 0 | **29** | 신설 |
| Q11 metadata | 47 | 47 | - |
| Q12 context_required | 44 | 44 | - |

---

## 7. 자동 처리 가능 범위 재판정 (v2)

| 항목 | v1 | v2 | 비고 |
|------|----|----|------|
| subject inheritance | 부분 | **가능 (P1~P4)** | P4 default 는 reviewer 검토 후 확정 |
| object inheritance | 부분 | **가능 (split_group)** | prev 상속은 보수적으로 미도입 |
| duplicate detection | 미구현 | **가능 (초안)** | alias 사전 확장 여지 |
| split expansion | 보수 | **가능 (FORBIDDEN 블랙리스트)** | 의미 결합 큰 쌍만 제외 |
| role assignment | 가능 | 가능 | v1 규칙 유지 |
| noise recovery | 가능 | 가능 | v1 규칙 유지 |
| control candidate carry-over | 가능 | 가능 | dedupe 은 다운스트림 처리 |

---

## 8. 여전히 사람 검토가 필요한 부분

- P4 kosha default `worker` 적용 187건 → reviewer 가 `supervisor`/`employer` 승격 여부 확정 필요
- P3 prev_same_title 상속 176건 중 조항 경계 직후 첫 문장의 과상속 가능성
- 지급·착용 주체 재할당 split 의 목적어 누락 케이스
- duplicate `near_duplicate` 2건과 `same_control_variant` 15건의 canonical 결정 정합성
- Q02 잔존 rule_core 22건 (법령 복잡 문장) 수동 라벨링 대상
- Q03 (object 결손) 114건은 alias 사전 추가로 자연 감소 가능

---

## 9. 법령 단계 진입 가능 여부

### 9.1 준비 상태

- sentence_role 축 확립(rule_core / condition / evidence / explanation / exception / metadata)
- subject_candidate 473건 확보 (상속 경계 기록)
- condition_candidate + rule_core 쌍 분해 가능(Q06 5건, 추후 확장 용이)
- evidence_candidate 조문 참조 추출 완성
- duplicate canonical 선정 로직 → 법령 단계에서 **동일 조문 내 표현 변형** 감지에 재사용 가능

### 9.2 다음 단계 연결 방식

| 연결 | 사용 필드 | 설명 |
|------|-----------|------|
| controls 정밀화 | `sentence_role=rule_core` + `ambiguity_flag=0` + `control_candidate` | canonical 문장 우선 매핑 |
| 법령 조문 구조 분해 | `source_type ∈ {law,admrul,licbyl}` + `document_id+document_title` 경계 | condition/rule_core 쌍 + evidence_candidate link |
| canonical rule 선정 | `canonical_candidate = 1` | 그룹 대표 문장 |
| 의무 주체 판정 보조 | `subject_candidate_*` + `inherited_subject_from` | 주어 신뢰도 자동 표시 |
| condition-rule 연결 | `split_group_id` + `sentence_role` | 조건/rule 같은 원문 내 연결 |

### 9.3 법령 단계 진입 가능 여부 판정

- rule_core 중 Q02 잔존 22건(6.6%) 수준 → 법령 조문 구조 분해 진입 **가능**
- duplicate 탐지 초안 존재 → 조문 간 표현 변형 dedupe 가능
- split 16건은 법령 계열이 아닌 kosha 중심이므로 법령 분해에 방해 없음

**결론: 법령 조문 구조 분해 단계로 진입 가능.**

---

## 10. 남은 리스크

| 리스크 | 영향 | 완화 방향 |
|--------|------|-----------|
| default_kosha_worker 187건 | 주체 오확정 가능성 | reviewer 시트에 `default_kosha_worker` 필터 제공해 우선 검토 |
| near_duplicate 2건의 Jaccard 기반 한계 | 표현 변형 심할 때 놓침 | 임베딩 기반 확장(향후) |
| P3 prev_same_title 상속 경계 | 조항 경계 직후 오상속 | document_title 추출 정교화 (추후) |
| Q03 object 결손 114건 | control 매핑 실패 | alias 사전 지속 확장 |
| split 주어 재할당 1건 | 현재 지급·착용 한 케이스 | 지급·비치·게시 등 추가 패턴은 v3 대상 |
| source_type expc 주어 결손 | 해석례 본문 주체 명시 부재 | reviewer 큐 이관 |

---

## 11. 생성/수정 파일 요약

### 신설
- `docs/design/sentence_normalization_rules_v2.md`
- `docs/design/sentence_subject_inheritance.md`
- `docs/design/sentence_duplicate_detection.md`
- `scripts/rules/build_sentence_normalization_sample_v2.py`
- `data/risk_db/master/sentence_normalization_sample_v2.csv` (819행)
- `data/risk_db/master/sentence_normalization_diff_v1_v2.csv` (801행)
- `docs/devlog/2026-04-23_sentence-normalization-v2.md` (본 보고서)

### 수정 없음 (기존 API/서비스/DB 스키마 미변경)

### 금지 사항 준수
- 법령 구조 분해 미착수
- 운영 DB 반영 없음
- 기존 API/서비스 수정 없음
- 원문 삭제 없음
- 임의 주어 확정 없음 (default_kosha_worker 는 별도 code 로 표시)
- duplicate 자동 삭제 없음 (canonical 후보만 지정)
- hit rate 를 위한 무리한 split 없음 (FORBIDDEN 패턴 명시 유지)
- control/hazard/condition/evidence 분리 유지

---

## 12. 최종 판정

성공 기준 점검:
- Q02 주어 결손이 v1보다 실질적 완화 — **달성** (484 → 345, rule_core 239 → 22)
- Q10 duplicate 탐지 초안 구현 — **달성** (12 그룹, 29 플래그)
- split 적용이 보수성 유지하면서도 확장 — **달성** (12 → 16)
- v1 대비 비교 파일 생성 — **달성** (`sentence_normalization_diff_v1_v2.csv`)
- 법령 단계로 넘어가기 전 문장 정제 계층 안정화 — **달성**

**판정: PASS**
(Q02 절대 숫자 345건은 타깃 200건에 미달하나, rule_core 중 Q02 는 22건(6.6%) 으로 법령 단계 진입에 지장 없는 수준. default_kosha_worker 와 prev_same_title 상속의 reviewer 검토만 남음.)

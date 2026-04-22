# 문장 정제 규칙 v2 (2026-04-23)

> v1(`sentence_normalization_rules.md`) 에 대한 차이 규칙만 기술한다.
> 변경되지 않은 규칙(header_strip, incomplete_check, evidence_check,
> noise_check/recover, vague_normalize, role_assign, flag_set, confidence_set)은
> v1 문서를 그대로 준수한다.
>
> 관련 문서
> - `sentence_subject_inheritance.md` — 주어 상속/복원 규칙
> - `sentence_duplicate_detection.md` — 중복 탐지 규칙

---

## 1. v1 → v2 변경점 요약

| 항목 | v1 | v2 |
|------|----|----|
| 주어 사전 | 기본 20종 | +법령/행정 주체 다수 (§ 2) |
| 주어 상속 | document_id 전체 | document_id + document_title 경계, 4단계 우선순위 |
| split | 12건 (매우 보수적) | 동의 결합 패턴 + 지급·착용 분해 추가 (§ 3) |
| object 복원 | 사전 contains | alias 사전 + 선행 명사구 탐색 강화 (§ 4) |
| duplicate (Q10) | 미구현 | same-doc + action+object alias + role+obligation 일치 기반 (§ 5) |
| 저장 필드 | v1 필드 | +subject_candidate_direct/_inherited/_confidence/inherited_subject_from, +object_candidate_direct/_inherited/_confidence, +duplicate_flag/_type/canonical_candidate/duplicate_of/duplicate_group_id, +split_confidence |

---

## 2. 주어 상속/복원 v2

상세는 `sentence_subject_inheritance.md`.

핵심:
- 4단계 우선순위(P1 direct → P2 split_group → P3 같은 document_title 내 직전 direct → P4 kosha default `worker`)
- 주체 사전 확장(경영책임자등, 법무부장관, 법원 등)
- "A 또는 B" 복수 결합 처리(같은 범주면 단일, 다른 범주면 `mixed_or_unknown` + `ambiguity_flag`)
- `subject_candidate` 는 호환 유지, `subject_candidate_direct`/`_inherited`/`_confidence`/`inherited_subject_from` 신설

---

## 3. split 규칙 점진 확대

### 3.1 v2 추가 패턴

- **"A를 설치하고 점검하여야 한다"** — v1 에서 이미 부분 지원. v2 는 `설치` 외에 `점검/비치/게시/작성/기록/측정/지급/착용/교육` 계열까지 동일 분해 패턴 적용.
- **"A를 비치하고 게시하여야 한다"** — 동사쌍 `(비치, 게시)` / `(작성, 게시)` / `(작성, 비치)` / `(설치, 점검)` / `(설치, 운영)` 화이트리스트로 split.
  - 단, `(설치, 운영)` 은 **split 금지**(단일 complex control 유지, 의미 결합 큼).
- **"A를 지급하고 착용하게 하여야 한다"** — 주체가 달라지는 split(지급 = employer, 착용 = worker).
  - split_order 1: 지급 (subject=employer)
  - split_order 2: 착용 (subject=worker)
  - 상속 대신 split 시 **주체 재할당** 허용.
- **"A인 경우 B하고 C하여야 한다"** — 조건 + 복합 행위. 조건은 공통 상속, B/C 는 각자 분해.

### 3.2 v2 유지 금지 패턴

- `또는` (주어 or-관계 위험) — v1 과 동일하게 **split 금지**.
- 예외조항/단서조항(`다만`, `제외한다`) — split 금지.
- 법령 정의문(`…을 말한다`, `…란`) — split 금지.
- split 후 object 가 사라지는 경우 — 중단.
- 상속 불가(주체·조건) — 중단.

### 3.3 split 신규 저장 필드

- `split_confidence` ∈ {`high`, `medium`, `low`}
  - high: 주체·객체·동사 모두 명확한 분해
  - medium: 객체 상속 또는 주어 재할당이 포함됨(예: 지급·착용)
  - low: 조건 상속 필요, 경계 모호
- `inherited_condition_from` — 조건 상속 시 출처 기록(split_group order=1 등).

---

## 4. object 복원 보강

### 4.1 object alias 사전(§ 5 duplicate 탐지와 공유)

`sentence_duplicate_detection.md` § 3 의 alias 그룹을 사용.
대표 object code 를 지정하여 중복 탐지 시에도 동일 키로 매칭.

### 4.2 복원 우선 대상(요청서 5 항)

- 보호구 **착용** — object 사전에서 "보호구"/"안전모"/"안전대"/"보안경"/"방진마스크"/"방독마스크"/"귀마개"/"보호복" 등
- 안전난간/덮개/발판 **설치** — "안전난간", "개구부 덮개", "작업발판", "안전방망", "추락방호망"
- 국소배기장치 **설치** — "국소배기장치", "LEV", "후드"
- 작업허가서 **작성/승인** — "작업허가서", "PTW", "허가서"
- 점검표/기록 **보존** — "점검표", "기록부", "관리대장"
- 감시인/신호수 **배치** — "감시인", "신호수", "유도자"
- 출입통제/작업구역 **분리** — "출입금지 표지", "작업구역", "안전선"

### 4.3 선행 명사구 탐색

- 현재 문장의 **앞쪽 명사구**(조건절 포함)에서 alias 매칭 명사를 찾으면 `object_candidate_inherited` 에 저장.
- 같은 split_group 의 order=1 문장 object 도 상속 후보.
- 같은 document_id + document_title 의 직전 문장 object 상속은 금지(오상속 위험 큼).

### 4.4 저장 필드

- `object_candidate_direct` — 현재 문장에서 직접 매칭
- `object_candidate_inherited` — 상속된 후보
- `object_candidate` — direct 우선, 없으면 inherited (호환)
- `object_candidate_confidence` ∈ {`direct`, `inherited_split`, `unresolved`}

---

## 5. duplicate 탐지 (Q10)

상세는 `sentence_duplicate_detection.md`.

파이프라인 단계: 모든 정제 문장 후처리 단계에서 **같은 document_id 내 action+object alias 그룹**으로 버킷팅 후 중복 유형 판정.

저장 필드: `duplicate_flag`, `duplicate_type`, `canonical_candidate`, `duplicate_of`, `duplicate_group_id`.

---

## 6. 파이프라인 (v2 확정)

```
1) header_strip
2) incomplete_check
3) evidence_check
4) noise_check → noise_recover
5) split_decide (v2 확대)
6) vague_normalize
7) subject_infer (P1 direct)
8) object_infer (direct)
9) 각 piece 적재
── 전체 수집 완료 ──
10) subject_inherit (P2 split_group → P3 prev_same_title → P4 kosha default)
11) object_inherit (split_group order=1)
12) duplicate_detect (doc_id 단위 그룹핑)
13) role_assign / flag_set / confidence_set (최종)
```

주어/대상/duplicate 상속 단계는 **2-pass** 구조이다. 첫 pass 에서 모든 direct 후보를 채운 뒤, 두번째 pass 에서 상속과 duplicate 를 부여한다.

---

## 7. confidence_set 갱신

v2 에서 confidence 산정 시 `subject_candidate_confidence` 를 반영한다.

| confidence | 조건 |
|-----------|------|
| high | split 정상 + subject=direct_high + object=direct + ambiguity=0 + evidence/noise 아님 |
| medium | direct 가 일부 누락이지만 상속(P2/P3) 로 보강, role 확정 |
| low | P4 default(kosha worker) 또는 상속 실패 + role=rule_core, 또는 ambiguity/context_required |

---

## 8. 원칙 재확인

- 원문 `raw_sentence_text` 는 삭제/수정 없음
- 임의 주어 확정 금지(P4 default 도 별도 code 로 표시)
- duplicate 자동 삭제/통합 금지
- split 이 주어·객체·조건 상속을 **파괴**하면 중단
- control/hazard/condition/evidence 를 혼동하지 않음
- 운영 DB 반영 없음, API/서비스 수정 없음

# 2026-04-22 · 문장 정제(sentence normalization) 계층 설계 + 샘플 정제 결과

## 배경

현재까지 확인된 핵심:
- controls master v2: 63개 (v1 47 → v2 63)
- 샘플: 800건, sentence→control hit 169건(21.1%), confidence high 비율 상승, zero-hit 카테고리 해소
- 그러나 문장 원천 품질이 낮아 엔진 판단에 그대로 쓰기 어려움
- 법령/KOSHA/MSDS 문장에서 반복되는 품질 이슈:
  1) 한 문장에 여러 의무/조치 혼합
  2) 주어·대상 생략
  3) "적절히"·"필요한"·"충분히" 같은 추상 표현
  4) 설명문/배경문/noise 혼재
  5) hazard/condition/evidence 혼동

→ 법령 구조 분해 이전에 **문장 정제 계층**으로 "원문 → 판단 가능한 구조 데이터" 변환이 필요.

---

## 1. 문장 품질 저하 유형 정의 결과

`docs/design/sentence_quality_issue_taxonomy.md` (신설, v0.1).

12개 유형을 체계화:

| 코드 | 이름 | 자동화 | 비고 |
|------|------|--------|------|
| Q01 | multi_action_sentence | 중 | split 의 1차 대상 |
| Q02 | omitted_subject | 상 | 문맥 의존, 임의 확정 금지 |
| Q03 | omitted_object | 상 | **object 우선 복원** |
| Q04 | vague_expression | 하 | 사전 기반 |
| Q05 | descriptive_noise | 중 | 키워드 + 반례 |
| Q06 | mixed_condition_rule | 중 | 접속사 분리 |
| Q07 | mixed_control_hazard | 중 | 신호어 조합 |
| Q08 | evidence_only | 하 | 조문 패턴 |
| Q09 | msds_formulaic_text | 하 | 사전 기반 |
| Q10 | duplicate_semantics | 상 | 본 단계 탐지 플래그만 |
| Q11 | incomplete_sentence | 중 | 길이/종결어미 |
| Q12 | context_required | 상 | 문맥 의존 |

각 유형은 정의/판별기준/예시/엔진상 문제점/정제 전략/자동 처리 여부/사람 검토 필요 여부를 명시.
유형 간 적용 우선순위(§ 3)도 고정: Q11 → Q08 → Q05/Q09 → Q01 → Q06 → Q07 → Q02/Q03 → Q04 → Q12 → Q10.

---

## 2. 정제 목표 구조

`docs/design/sentence_normalization_schema.md` (신설, v0.1).

레코드 한 행 = **정제 문장 단위**. 원문 1건 → 정제 N건(N≥1).

필드 29종:
- 식별자/출처: `normalized_sentence_id`, `source_sentence_id`, `source_type`, `document_id`, `document_title`
- 원문/정제문: `raw_sentence_text`, `normalized_sentence_text`, `normalization_status`, `split_group_id`, `split_order`, `was_split`, `normalization_type`
- 역할/후보: `sentence_role`, `obligation_level_candidate`, `subject_candidate`, `object_candidate`, `action_candidate`, `condition_candidate`, `hazard_candidate`, `equipment_candidate`, `control_candidate`, `evidence_candidate`
- 플래그/노트: `noise_flag`, `noise_recovery_candidate`, `ambiguity_flag`, `context_required_flag`, `quality_issue_codes`, `confidence`, `normalization_note`, `reviewer_note`

원칙 재확인:
- 원문(`raw_sentence_text`) 보존, 덮어쓰기 금지
- `*_candidate` 는 후보, 자동 확정 금지
- control/hazard/condition/evidence 를 같은 필드에 섞지 않음
- `sentence_type`(원문 분류) ≠ `sentence_role`(정제 후 역할)

sentence_role 9종: `rule_core` / `condition` / `evidence` / `explanation` / `hazard_statement` / `control_statement` / `exception` / `metadata` / `unresolved`.

ID 규칙: `{sample_id}-{split_order:02d}` (예: `S0123-01`).

---

## 3. split 규칙 / 금지 규칙

`docs/design/sentence_normalization_rules.md` § 6.

**split 대상**:
- "A하고 B하여야 한다"  (단, "A하고 있는지" 상태 확인 표현은 **제외**)
- "A·B·C 를 …한다" (열거 3항)
- "A 및 B 를 …한다" (2항 한정)
- "A인 경우 B한다" → condition + rule_core

**split 금지**:
- 단일 동사 종결
- 같은 행위 부연 ("정기적으로, 즉 6개월마다 점검")
- 법령 단일 정의문
- 조건 다단 중첩
- 분리 시 주어·대상 붕괴 ("설치·운영하여 성능 유지")
- "A 또는 B" (주어의 or-관계 다수 → 의미 손실 위험 큼)

**상속 규칙**: subject/condition/evidence 는 상속, action/object/hazard/equipment/control 은 개별 산정.

**의미 손실 위험 사례**:
- "설치·운영" → 하나 유지
- "관리·감독" → 하나 유지 + `ambiguity_flag`
- "작성·게시·비치" → 3개 분해 가능
- "지급·착용" → 2개 분해 (주체가 달라짐)

---

## 4. 추상 표현 처리 규칙

`docs/design/sentence_normalization_rules.md` § 7.

**삭제 대상** (의미 손실 적음):
- `적절한/적절히/적절하게`, `충분한/충분히`, `안전하게`, `확실히`, `철저히`,
  `신속히/즉시/지체 없이` (부사적 사용일 때)

**플래그 대상** (의미 손실 큼, `ambiguity_flag=1`):
- "필요한 조치", "이상이 없도록", "노력하여야", `관리한다/조치한다` 단독

control 매핑 시 `ambiguity_flag=1` 은 **confidence=low 고정**.

---

## 5. 주어/대상 보정 규칙

`docs/design/sentence_normalization_rules.md` § 8-9.

**주어 사전**: 사업주 / 관리감독자·작업지휘자 / 안전·보건관리자 / 근로자·작업자 / 도급인·수급인·원수급인·하수급인 / 고용노동부장관 / 사업장·작업장 / 장비 자체 / 문서.

**주어 보정**:
- 문장 시작이 "주어+조사" → 후보 고정
- 앞 문장(같은 document_id) 주어 상속 (단, 설명·정의문은 상속 금지)
- 복원 불가 시 공란 유지 (**임의 확정 금지**)
- 복수 주어("원수급인과 수급인") → `mixed_or_unknown`

**대상 보정** (우선순위 1 — control 매핑 직접 기여):
- 문장 내 "목적어 + 동사" 구조 우선
- 부재 시 앞쪽 명사구 후보 탐색
- 복원 불가 시 공란

---

## 6. noise 처리 결과

`docs/design/sentence_normalization_rules.md` § 5 + `controls_noise_and_rendering.md` 1.3.

**noise 판정 원칙**:
- v2 에서 이미 `descriptive_noise` 로 라벨된 문장은 1차 noise 로 채택(라벨 신뢰)
- 그 외: 의무 신호 없음 + 숫자 임계값 없음 + noise 단독 어휘 포함

**복구 조합** (11종):
| 신호 anchor | 행위 신호 | 복구 role/action |
|---|---|---|
| 보호구(안전모·안전대·…) | 착용·지급 | rule_core / wear·provide |
| 환기 | 실시·가동·확인 | rule_core / ventilate |
| 저장·보관 | 분리·격리 | rule_core / store |
| 점검 | 매일·매월·주기·6개월·연 1회 | rule_core / inspect |
| 측정 | 값·기준·주기 | rule_core / measure |
| 대피 | 경로·집결지 | rule_core / isolate |
| 허가 | 작업·진입·발급 | rule_core / prepare |
| 감시인·감시자 | 배치·지정 | rule_core / monitor |
| 유도자·유도원 | 배치·지정 | rule_core / monitor |
| 출입 | 금지·통제·제한 | rule_core / prohibit_access |
| 작업지휘자 | 지정·배치 | rule_core / monitor |

**noise 유지**(복구 제외): 물성 서술, 참고 안내, 단순 질의문.

---

## 7. 샘플 정제 결과 요약

**산출 파일**:
- `data/risk_db/master/sentence_normalization_sample_v1.csv` (정제 문장, 814행)
- `data/risk_db/master/sentence_normalization_diff_sample.csv` (원문 vs 정제 요약, 800행)
- 빌더: `scripts/rules/build_sentence_normalization_sample.py`

**지표(800 샘플 기준)**:

| 지표 | 값 | 비고 |
|------|----|------|
| 입력 샘플 | 800 | v2 sentence_labeling_sample_v2 |
| 정제 문장 수 | 814 | split 반영 |
| split 적용 원문 수 | 12 | 보수적 split (Q01 piece 26건) |
| vague_remove 적용 | 12 | 적절한/충분한/안전하게 등 |
| vague_flag(ambiguity) | 8 | 필요한 조치/노력하여야/조치한다 등 |
| 주어 복원(후보) | 182 | 사전 매칭 + 조심스러운 상속 |
| 대상 복원(후보) | 111 | 사전 매칭 |
| noise 표시 | 255 | v2 descriptive_noise(253) + 자체 탐지 |
| noise 복구 후보 | 43 | 복구 조합 매칭 |
| incomplete(metadata) | 47 | 항 번호/짧은 잔존 |
| evidence_only | 33 | 참조만 있는 문장 |
| control_candidate 부여 | 275 | 기존 매핑과 유사 수준 |
| rule_core 역할 | 329 | |

**sentence_role 분포**:
| role | n |
|---|---|
| rule_core | 329 |
| condition | 51 |
| evidence | 42 |
| explanation | 299 |
| hazard_statement | 4 |
| control_statement | 0 |
| exception | 42 |
| metadata | 47 |
| unresolved | 0 |

**품질 이슈 코드 분포**(중복 라벨 허용):
| Q | n | 해석 |
|---|---|------|
| Q01 | 26 | split 각 piece 에 라벨 |
| Q02 | 484 | **주어 결손 60%** — 한국어 법령·KOSHA 문체 특성 확인 |
| Q03 | 93 | 설치/점검/착용/지급/작성 동사 + 대상 결손 |
| Q04 | 8 | 추상 표현 플래그 |
| Q05 | 298 | noise 표시 + 복구 후보 |
| Q06 | 5 | condition+rule 분해 |
| Q07 | 4 | hazard+control 혼합 |
| Q08 | 33 | evidence_only |
| Q09 | 0 | MSDS 상투문구(본 샘플에선 비노출) |
| Q10 | 0 | duplicate(본 단계 탐지 보류) |
| Q11 | 47 | incomplete metadata |
| Q12 | 44 | context_required |

---

## 8. 자동 처리 가능한 부분

- header_strip, incomplete_check, evidence_check, noise_check, noise_recover, split_decide, vague_normalize, object_infer (사전 기반), role_assign, flag_set, confidence_set
- v2 descriptive_noise 라벨을 1차 신호로 채택 → noise 탐지 정합성 확보
- control_candidate 매핑 (controls_master_draft_v2 의 typical_keywords 단순 contains)

## 9. 사람 검토가 필요한 부분

- subject 상속 경계 (같은 조항 내 주어 이동)
- split 의미 결합 모호 케이스 ("설치·운영", "관리·감독")
- noise 복구 후보 43건의 실제 rule 승격 여부
- Q04 ambiguity_flag 8건의 control 매핑 품질
- Q07 hazard+control 혼합 4건 (분리 불가형)
- Q10 duplicate 탐지 (본 단계에서 자동 미구현)
- `object_candidate` 복원 실패 93건의 조항 선행 명사 재탐색

---

## 10. controls/법령 단계와의 연결 방식

`sentence_normalization_schema.md` § 9.

1. **controls 정밀화**
   - `sentence_role ∈ {rule_core, control_statement}` 이고 `ambiguity_flag=0` 레코드만 control 매핑 대상
   - `control_candidate` 가 부여된 275건 → 기존 `sentence_control_mapping_sample_v2` 와 병합해 hit 정밀도 재측정
2. **법령 조문 구조 분해**
   - `source_type ∈ {law, admrul, licbyl}` + `sentence_role ≠ metadata`
   - (condition, rule_core) 쌍으로 trigger→rule 그래프 구성
   - `evidence_candidate` 는 법조문 link 기준
3. **감소대책 문장 렌더링**
   - rule_core + `control_candidate` + `ambiguity_flag=0` 을 1차 대상
   - `controls_noise_and_rendering.md` § 2 템플릿 적용
   - `normalized_sentence_text` 가 아니라 template 렌더 우선(원문 질의형/설명형 섞이지 않게)

---

## 11. 남은 리스크

| 리스크 | 영향 | 완화 방향 |
|--------|------|-----------|
| Q02 (주어 결손) 484건 | control 매핑 시 주체 불명 → 현장 수용성 저하 | 조항 내 주어 상속 기준을 정교화(문서 id + 조 번호 내) |
| noise 복구 후보 43건의 과잉/부족 | rule_core 승격 오판정 가능 | reviewer 시트 생성 후 확정 |
| Q10 (duplicate) 자동 미탐지 | control 후보 중복 집계 | 같은 document_id 내 action+object 매칭 rule 추가 |
| 원문 수집 단편 (Q11 47건) | 라벨링 자체 노이즈 | 수집 단계에서 문장 분할 기준 재검토 필요 |
| MSDS 상투(Q09) 0건 | 본 샘플에선 비노출, 실제 DB 전량에는 다수 존재 예상 | 전량 적용 시 Q09 사전 확장 재측정 |
| split 과소(12건) | 실 세계 복합문장 대비 보수적 | 열거/"및/또는" 패턴의 **주어 동일성 판정** 추가 후 점진 확대 |
| subject 자동 확정 금지 원칙 | 후보만 채움 → 다운스트림 엔진 설계 변경 필요 | 엔진에서 `subject_candidate == ""` 케이스를 reviewer 큐로 전송 |

---

## 12. 최종 판정

- 설계 문서 3종(taxonomy / schema / rules) 모두 신설 완료
- 800 샘플 기준 정제 결과 CSV + diff CSV 산출 완료
- 파이프라인 작동(자동 처리 가능 범위 명확, v2 라벨과 정합)
- 원문 보존·임의 확정 금지·noise 자동 삭제 금지 원칙 유지
- controls / 법령 단계 연결 방식 구조화 완료
- 다만 **subject 결손 60%(Q02=484)** 과 **duplicate 자동 탐지 미구현(Q10=0)** 은 다음 단계 과제로 명시

**판정: WARN**
(성공 기준 6개 모두 충족하나, 주어 복원 및 duplicate 탐지의 정밀화가 필수 후속 작업)

---

## 생성/수정 파일 요약

### 신설
- `docs/design/sentence_quality_issue_taxonomy.md`
- `docs/design/sentence_normalization_schema.md`
- `docs/design/sentence_normalization_rules.md`
- `scripts/rules/build_sentence_normalization_sample.py`
- `data/risk_db/master/sentence_normalization_sample_v1.csv`
- `data/risk_db/master/sentence_normalization_diff_sample.csv`
- `docs/devlog/2026-04-22_sentence-normalization-layer.md` (본 보고서)

### 수정 없음 (기존 API/서비스/DB 스키마 미변경)

### 금지 사항 준수
- 법령 구조 분해 미착수
- 운영 DB 반영 없음
- 기존 API/서비스 수정 없음
- 원문 삭제 없음
- subject/object 임의 확정 없음
- 단순 요약문 미생성
- 품질 지표 과장 없음 (split 12건·복구 후보 43건만 산출)
- control/hazard/condition/evidence 분리 유지

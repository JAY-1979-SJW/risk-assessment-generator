# 위험성 평가 웹 표준 기준선 v1

> 확정일: 2026-04-20  
> 상태: LOCKED — 이 문서의 규칙은 명시적 버전업(v2) 없이 임의 변경 금지

---

## 1. 목적

이 문서는 `risk-assessment-app` 운영 상태 대시보드(`risk-assessment.html`)의 화면 구성·상태 로직·fixture·assertion 기준을 고정한다.

이 문서는 위험성 평가 화면에 국한하지 않고, 이 프로젝트에서 운영형 상태 웹 화면을 추가할 때 따라야 할 **표준 운영형 웹 기준선 v1**로 기능한다. 이후 신규 화면은 이 기준을 상속하거나 명시적으로 분기해야 한다.

---

## 2. 적용 대상

### 현재 적용 파일

| 역할 | 파일 경로 |
|------|-----------|
| 대시보드 HTML | `status/risk-assessment/risk-assessment.html` |
| 브라우저 fixture | `status/risk-assessment/fixture-test.html` |
| Node.js assertion runner | `status/risk-assessment/fixture-assertions.js` |

### 향후 적용 범위

이 기준을 따라야 하는 화면: 동일 프로젝트 내 운영 상태를 표시하는 모든 HTML 대시보드.  
예외 적용 시 별도 버전 기준선 문서 필수.

---

## 3. 화면 구성 고정 항목

아래 블록은 **삭제 금지**이며 위치·역할이 고정된다.

| 블록 ID | 마크업 id | 역할 | 삭제 금지 | 위치 고정 | 수정 허용 범위 | 구조 변경 금지 |
|---------|-----------|------|-----------|-----------|----------------|----------------|
| overall | `#card-overall`, `#overall-content` | 전체 상태(HEALTHY/DEGRADED/INCIDENT) 표시 | YES | 최상단, wide | 내부 텍스트·카운트 | 위치 이동, id 변경 |
| action | `#card-action`, `#action-content` | Action Recommendation 표시 | YES | overall 직하, wide | 내부 텍스트 | 위치 이동, id 변경 |
| git | `#git-content` | git_guard 최신 verdict | YES | 현재 상태 좌상 | 내부 row | id 변경 |
| self | `#self-content` | self_check 최신 verdict | YES | 현재 상태 우상 | 내부 row | id 변경 |
| backup | `#backup-content` | backup_check 최신 verdict | YES | 현재 상태 좌하 | 내부 row | id 변경 |
| restore | `#restore-content` | restore_rehearsal 최신 verdict | YES | 현재 상태 우하 | 내부 row | id 변경 |
| svc | `#svc-content` | 서비스 live 상태 | YES | wide 단독 | 내부 row | id 변경 |
| h24 | `#h24-content` | 최근 24시간 요약 | YES | 이력 블록 A | 내부 카운트 | id 변경 |
| d7 | `#d7-content` | 최근 7일 마지막 실행 | YES | 이력 블록 B | 내부 시각 | id 변경 |
| events | `#events-content` | 최근 이벤트 10개 (normalized) | YES | 이력 블록 C | 내부 row | id 변경 |

**재갱신 주기 고정값**: 현재 상태 5s / 이력(overall·action·h24·d7·events) 60s — 임의 변경 금지.

---

## 4. 상태 / Action 규칙

### 4-1. Overall Status 판정 순서

1. INCIDENT: 아래 중 하나라도 해당
   - `self_check` / `backup_check` / `restore_rehearsal` 중 하나가 최근 2회 연속 FAIL (normalized)
   - 서로 다른 source 2개 이상이 24h 내 각 2회 이상 FAIL (normalized)
2. DEGRADED: 아래 중 하나라도 해당
   - `git_guard` 24h 내 FAIL 1회 이상 (normalized)
   - `self_check` / `backup_check` / `restore_rehearsal` 연속 FAIL (normalized)
   - 24h WARN 5회 이상 누적
   - 실제 FAIL 1회 이상 (다른 DEGRADED 조건 없을 때)
3. HEALTHY: 위 조건 미해당

### 4-2. Action Recommendation 매핑 규칙 (고정)

| action class | 발동 조건 | actionIds | priority | approval | nextTemplate |
|-------------|-----------|-----------|----------|----------|--------------|
| OBSERVE | INCIDENT/DEGRADED 조건 미해당 | OBS-001, OBS-002, OBS-003 | low | false | null |
| AUTO-RECOVERY-CANDIDATE | `self_check` 최근 2회 연속 FAIL (normalized), APR 조건 미해당 | ARC-001, ARC-002, ARC-003 | medium | false | 서비스 이상 대응 템플릿 (§ B) |
| APPROVAL-REQUIRED | 아래 조건 중 하나 이상 해당 | 조건별 APR 집합 (최대 4개) | high | true | § A 또는 § C (조건별) |

**APPROVAL-REQUIRED 조건별 actionId 매핑 (고정)**:

| 조건 | 추가 IDs |
|------|----------|
| `restore_rehearsal` 최근 2회 중 1회 이상 FAIL | APR-003, APR-004 |
| `git_guard` 최근 3회 중 content dirty FAIL (mode_only 제외) | APR-001, APR-004 |
| `backup_check` 최근 2회 모두 FAIL | APR-003, APR-004 |
| 복수 source 24h FAIL ≥ 2 (2개 이상 source) | APR-002, APR-003, APR-004 |

**nextTemplate 조건 매핑 (APPROVAL-REQUIRED 전용)**:

| 조건 | nextTemplate 포함 문구 |
|------|------------------------|
| git content dirty | § A |
| restore_rehearsal FAIL 또는 backup_check FAIL | § C |
| 조건 미매핑 시 fallback | § A / § C 모두 포함 |

**규칙 고정**:
- OBSERVE는 nextTemplate=null — DOM에 `.act-template` 요소 렌더 금지
- AUTO-RECOVERY-CANDIDATE는 § B만 포함 — § A / § C 포함 금지
- APPROVAL-REQUIRED는 § A 또는 § C만 포함 — § B 포함 금지
- actionIds는 Set 기반 중복 제거 후 최대 4개 슬라이스
- approval=true 시 DOM에 `.approval-yes` 요소 필수
- approval=false 시 DOM에 `.approval-yes` 요소 렌더 금지

### 4-3. ACTION_CATALOG 고정값

| ID | 설명 |
|----|------|
| OBS-001 | 상태 추적 유지 |
| OBS-002 | 다음 scheduled check 결과 대기 |
| OBS-003 | recent events 24h 추세 확인 |
| ARC-001 | 최소 범위 재기동 후보 검토 |
| ARC-002 | docker compose ps / health 재확인 |
| ARC-003 | 최근 로그 비교 후 단일 서비스 문제 여부 판단 |
| APR-001 | git 정렬 복구 계획 작성 |
| APR-002 | 데이터 복구 범위 확정 |
| APR-003 | backup/restore 무결성 재확인 |
| APR-004 | 대표님 승인 후 실행 단계로 전환 |

이 테이블의 ID·설명은 임의 변경 금지. 추가 시 APR-005+ / ARC-004+ / OBS-004+ 순번 사용.

---

## 5. priority / 시각 규칙

| priority | 클래스 | 색상 | 추가 스타일 |
|----------|--------|------|-------------|
| low | `.priority-low` | `#22c55e` (초록) | 없음 |
| medium | `.priority-med` | `#f97316` (주황) | 없음 |
| high | `.priority-high` | `#ef4444` (빨강) | `font-weight: bold` 필수 |

**시각 고정 규칙**:
- `high`는 action-class 문자와 priority 색상 모두 빨강+bold — 화면에서 가장 먼저 인지 가능해야 함
- `.act-id-row`에 `flex-wrap: wrap` 필수 — 좁은 폭에서 badge overflow 금지
- `.act-id`에 `white-space: nowrap` 적용 — badge 내 텍스트 분리 금지
- action-banner 오른쪽 div에 `min-width: 0` 필수 — 긴 텍스트 overflow 방지
- 좁은 폭 기준: "텍스트 겹침 없음 + badge 줄바꿈 허용 + priority 색상 식별 가능"이면 PASS

---

## 6. fixture 기준선

아래 3종 fixture가 기준 fixture이며, 회귀 검증 시 반드시 이 구성으로 실행해야 한다.

### 6-1. observe fixture

```
조건: git_guard/self_check/backup_check/restore_rehearsal 전부 최근 이벤트 PASS
기대 overall: HEALTHY
기대 action: OBSERVE
기대 actionIds: ['OBS-001', 'OBS-002', 'OBS-003']
기대 priority: low
기대 nextTemplate: null
기대 approval: false
```

### 6-2. auto-recovery fixture

```
조건: self_check 마지막 2회 FAIL, 나머지 source 전부 PASS
      (git_guard PASS, backup_check PASS, restore_rehearsal PASS)
기대 overall: DEGRADED
기대 action: AUTO-RECOVERY-CANDIDATE
기대 actionIds: ['ARC-001', 'ARC-002', 'ARC-003']
기대 priority: medium
기대 nextTemplate: '서비스 이상 대응 템플릿 (§ B)'
기대 approval: false
```

### 6-3. approval-required fixture

```
조건: restore_rehearsal 마지막 2회 FAIL, 나머지 source 전부 PASS
      (git_guard PASS, self_check PASS, backup_check PASS)
기대 overall: INCIDENT (restore_rehearsal 연속 FAIL 조건)
기대 action: APPROVAL-REQUIRED
기대 actionIds: APR-003 포함, APR-004 포함 (최대 4개)
기대 priority: high
기대 nextTemplate: '데이터 복구 대응 템플릿 (§ C)' 포함
기대 approval: true
```

각 fixture 이벤트 객체 최소 포함 필드:

```json
{ "source": "<source명>", "verdict": "PASS|WARN|FAIL", "ts": "<ISO 8601>", "summary": "" }
```

---

## 7. assertion 기준선

**기준 실행 결과**: `node status/risk-assessment/fixture-assertions.js` → 19/19 PASS

| # | 케이스 | assertion |
|---|--------|-----------|
| 1 | OBSERVE | action === 'OBSERVE' |
| 2 | ARC | action === 'AUTO-RECOVERY-CANDIDATE' |
| 3 | APR | action === 'APPROVAL-REQUIRED' |
| 4 | OBSERVE | actionIds === ['OBS-001','OBS-002','OBS-003'] |
| 5 | ARC | actionIds === ['ARC-001','ARC-002','ARC-003'] |
| 6 | APR | actionIds.includes('APR-003') |
| 7 | APR | actionIds.includes('APR-004') |
| 8 | OBSERVE | priority === 'low' |
| 9 | ARC | priority === 'medium' |
| 10 | APR | priority === 'high' |
| 11 | APR | nextTemplate.includes('§ C') |
| 12 | OBSERVE | nextTemplate === null |
| 13 | ARC | nextTemplate.includes('§ B') |
| 14 | ARC | !nextTemplate.includes('§ A') |
| 15 | ARC | !nextTemplate.includes('§ C') |
| 16 | APR | !nextTemplate.includes('§ B') |
| 17 | APR | approval === true |
| 18 | OBSERVE | approval === false |
| 19 | ARC | approval === false |

**회귀 검사 최소 통과 조건**: 19/19 PASS — 1개라도 FAIL이면 배포 불가.

DOM assertion (fixture-test.html 브라우저 렌더 기준):

| 케이스 | DOM 항목 | 기준 |
|--------|----------|------|
| OBSERVE | `.act-template` 요소 | 존재 금지 |
| ARC / APR | `.act-template` 요소 | 존재 필수 |
| APR | `.approval-yes` 요소 | 존재 필수 |
| OBSERVE / ARC | `.approval-yes` 요소 | 존재 금지 |
| OBSERVE | `.act-id` badge 수 | 정확히 3개 |
| ARC | `.act-id` badge 수 | 정확히 3개 |
| APR | `.act-id` badge 수 | 2개 이상 |

---

## 8. 수정 허용 범위

### 허용

- spacing (padding, margin, gap) 보정
- badge `flex-wrap`, `white-space`, `overflow` 보정
- `min-width: 0` 등 overflow 방지 속성 추가
- null/조건부 렌더 보정 (templateHtml 조건 등)
- fixture 이벤트 추가 (기존 3종 fixture 조건 유지 전제)
- assertion 추가 (기존 19개 assertion 삭제 금지)
- 내부 행(row) 텍스트 라벨 수정
- 폰트 크기 ±0.1rem 범위 조정

### 제한 (사유 명시 후 허용)

- 기존 블록 내부 마크업 구조 부분 조정 (id 유지 전제)
- 카드 배경색·테두리색 변경
- 갱신 주기 변경 (5s/60s 기준)

### 금지

- 전체 레이아웃 재구성 (grid 구조 변경)
- 블록 id 임의 변경 또는 삭제
- ACTION_CATALOG ID 임의 변경 또는 삭제
- action/priority 매핑 규칙 임의 변경
- calcOverall / calcAction 로직 임의 변경 (버그 수정 제외)
- 기존 assertion 삭제 또는 약화
- 기존 3종 fixture 조건 변경
- 엔진 로직(AI 생성 등) 대시보드 HTML에 혼합
- 임시 필드·디버그 코드 프로덕션 잔류
- 전면 리팩토링

---

## 9. 배포 전/후 검증 절차

### 배포 전

| 항목 | 기준 | 판정 |
|------|------|------|
| Node.js assertion | `node fixture-assertions.js` → 19/19 PASS | PASS 필수 |
| 브라우저 fixture 렌더 | fixture-test.html 열어 assertion 요약 PASS 확인 | PASS 필수 |
| JS console error | 0건 | PASS 필수 |
| 기존 블록 10개 id | DOM에 모두 존재 | PASS 필수 |

배포 전 위 4개 항목 중 1개라도 FAIL이면 배포 금지.

### 배포 후

| 항목 | 기준 | 판정 |
|------|------|------|
| 서버 파일 반영 | `git pull --ff-only` 완료 확인 | PASS 필수 |
| 실제 렌더 확인 | 브라우저에서 대시보드 정상 로드 | PASS 필수 |
| JS error | console error 0건 | PASS 필수 |
| 핵심 블록 존재 | overall/action/svc/h24/d7/events 모두 렌더됨 | PASS 필수 |
| action 규칙 일치 | 실제 데이터 기반 action 클래스·priority·nextTemplate 일치 | PASS 필수 |

배포 후 위 5개 항목 중 1개라도 FAIL이면 즉시 롤백.

---

## 10. 완료 정의 (안정화 완료 조건)

아래 6개 조건을 **모두** 만족해야 "안정화 완료"로 판정한다. 하나라도 미달이면 미완료.

| # | 조건 | 판정 방법 |
|---|------|-----------|
| 1 | 기준 fixture 3종 PASS | `fixture-assertions.js` 19/19 PASS |
| 2 | assertion PASS | 19/19 PASS, 회귀 시 동일 결과 |
| 3 | narrow width PASS | 텍스트 겹침 없음, badge wrap 허용, priority 색 식별 가능 |
| 4 | 기존 블록 10개 보존 PASS | DOM에 모든 id 존재 확인 |
| 5 | 상태/action/priority 규칙 일치 PASS | 4절 매핑 테이블과 구현 일치 |
| 6 | 배포 후 반영 확인 PASS | 9절 배포 후 항목 전부 PASS |

현재(2026-04-20) 조건 1~5 충족 완료. 조건 6은 다음 배포 시 확인.

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| v1 | 2026-04-20 | 최초 확정 — fixture 3종 PASS, assertion 19/19 PASS 기준으로 기준선 고정 |

# Risk Assessment Enrichment Rulebook (v2.0)

**대상**: `POST /api/v1/risk-assessment/build` v2 확장
**전제**: 규칙 기반 후처리. AI/자유문장 해석 금지.
**안전 원칙**: 기존 결과를 **제거하지 않는다**. 우선순위 조정·control 추가·hazard 1개 신규만 허용.

---

## 1. 규칙 구조

각 규칙 1건은 아래 필드로 정의한다:

| 필드 | 타입 | 의미 |
|------|------|------|
| `id` | string | 규칙 식별자 (`R001` 형식) |
| `rationale` | string | 규칙 근거 (산안법·KOSHA·현장 상식 중 하나 기준) |
| `when.work_type` | string | 작업 유형 완전 일치 (생략 시 모든 work_type 대상) |
| `when.equipment_any` | string[] | equipment 배열 중 1개 이상 매칭 시 발동 |
| `when.location_any`  | string[] | location 배열 중 1개 이상 매칭 시 발동 |
| `when.conditions_any`| string[] | conditions 배열 중 1개 이상 매칭 시 발동 |
| `effects` | array | 아래 effect 객체의 순차 적용 |

### 1.1 when 결합 방식

- `when` 내부 키는 **AND** 결합.
- 같은 키 내 배열 원소는 **OR** (`_any` 접미사).
- 3개 입력 필드 중 2개 이상의 조건이 걸린 규칙은 모든 필드 조건을 만족해야 발동.

### 1.2 effect 유형

| type | 효과 | 제약 |
|------|------|------|
| `boost_hazard` | 매칭 hazard의 `confidence_score` +`delta` (상한 1.0) | delta ≤ 0.1, hazard 명에 substring 일치 |
| `add_controls` | 매칭 hazard에 controls 추가 (순서: 말미) | hazard당 rule 단위 최대 2개, 기존 controls와 중복 금지 |
| `add_hazard` | hazards 배열에 신규 hazard 1개 추가 | **요청당 최대 1회**, controls ≤ 2개, references = 빈 배열 |
| `tag_evidence` | `evidence_summary` 말미에 `" [조건 반영: {note}]"` 추가 | 1 hazard에 1회만 |

### 1.3 매칭 규칙

- `match_hazard_contains`: hazard 문자열에 부분 포함 검사 (NFC normalize 후 substring).
- 복수 hazard 일치 시 **가장 높은 confidence_score**를 갖는 hazard 1건만 선택.
- 일치하는 hazard가 없으면 `boost_hazard` / `add_controls` / `tag_evidence`는 **no-op** (규칙 자체를 건너뛰지 않고 다음 effect로 이동).

### 1.4 enrichment 적용 순서

1. 입력 허용값 검증 및 dedupe 완료된 상태.
2. `build_risk_assessment(work_type)` → 기본 결과 획득.
3. 규칙 테이블 순회. 매칭된 규칙들을 `id` ASC로 정렬해 결정론적 적용.
4. 각 규칙의 effects 순차 적용:
   - hazard당 추가된 controls 카운터 유지 (2개 한도)
   - `add_hazard` 카운터 (1회 한도)
5. confidence 조정이 있었으면 `hazards` 배열을 `confidence_score DESC`로 재정렬 — v1과 동일한 정렬 불변식 유지.
6. `input_context` 필드 부가.

---

## 2. 규칙 목록 (1차 확정, 20건)

### 전기작업

| ID | when | effects | 근거 |
|----|------|---------|------|
| R001 | work_type=전기작업, conditions_any=[활선근접] | boost `감전` +0.05 / add_controls `감전` +2 | 산안기준규칙 §321 (충전전로 작업) |
| R002 | work_type=전기작업, equipment_any=[사다리] | boost `추락` +0.05 / add_controls `추락` +1 | 사다리 최상부 작업은 KOSHA 지침상 금지 |
| R003 | work_type=전기작업, location_any=[옥상, 천장부] | boost `추락` +0.05 / add_controls `추락` +1 | 옥상/천장부는 추락 고위험 구역 |
| R004 | work_type=전기작업, conditions_any=[우천] | boost `감전` +0.05 / add_controls `감전` +1 | 습윤 상태 누전 위험 급증 |

### 밀폐공간 작업

| ID | when | effects | 근거 |
|----|------|---------|------|
| R010 | work_type=밀폐공간 작업, location_any=[맨홀, PIT] | boost `질식` +0.05 / add_controls `질식` +2 | 산안기준규칙 §619 (밀폐공간 작업 프로그램) |
| R011 | work_type=밀폐공간 작업, conditions_any=[밀폐공간] | boost `질식` +0.05 / add_controls `질식` +1 | 조건 중복 시 감시인·구조 체계 강조 |
| R012 | work_type=밀폐공간 작업, conditions_any=[화기작업] | add_controls `화재` +1 (없으면 add_hazard `화재·폭발`) | 산소농도 변화 + 점화원 동시 존재 |

### 화기작업

| ID | when | effects | 근거 |
|----|------|---------|------|
| R020 | work_type=화기작업, location_any=[실내] | boost `화재` +0.05 / add_controls `화재` +2 | 실내 환기 부족으로 가연성 가스 누적 |
| R021 | work_type=화기작업, equipment_any=[용접기, 절단기] | add_controls `화재` +1 | 아크·스파크 비산 거리 고려 |
| R022 | work_type=화기작업, conditions_any=[비산분진] | boost `화재·폭발` +0.05 / add_controls `화재` +1 | 분진 폭발 (MSDS·KOSHA GUIDE D-15) |

### 고소작업 / 이동식비계 작업 / 고소작업대 작업

| ID | when | effects | 근거 |
|----|------|---------|------|
| R030 | work_type=고소작업, location_any=[옥상, 천장부] | boost `추락` +0.05 / add_controls `추락` +1 | 단부·개구부 주변 |
| R031 | work_type=고소작업, conditions_any=[우천, 야간작업] | boost `추락` +0.05 / add_controls `추락` +1 | 시인성·마찰 저하 |
| R032 | work_type=이동식비계 작업, conditions_any=[추락위험] | boost `추락` +0.05 / add_controls `추락` +1 | 승강 시 2인 작업 원칙 |
| R033 | work_type=고소작업대 작업, conditions_any=[협업작업] | add_controls `협착` +1 | 붐 조작 중 2차 작업 시 협착 |

### 굴착작업 / 중장비 작업

| ID | when | effects | 근거 |
|----|------|---------|------|
| R040 | work_type=굴착작업, equipment_any=[굴착기] | boost `협착` +0.05 / add_controls `협착` +1 / add_controls `전도` +1 | 굴착기 선회반경 및 지반 전도 |
| R041 | work_type=굴착작업, location_any=[외부], conditions_any=[우천] | boost `붕괴` +0.05 / add_controls `붕괴` +1 | 토사붕괴·매몰 위험 상승 |
| R042 | work_type=중장비 작업, conditions_any=[협업작업] | add_controls `충돌` +1 | 신호수·후방경보 체계 |

### 양중작업 / 절단·천공 작업

| ID | when | effects | 근거 |
|----|------|---------|------|
| R050 | work_type=양중작업, equipment_any=[크레인] | boost `낙하` +0.05 / add_controls `낙하` +1 | 인양물 결속·하부 출입통제 |
| R060 | work_type=절단/천공 작업, equipment_any=[절단기] | boost `절단` +0.05 / add_controls `절단` +1 | 회전체 방호덮개 |
| R061 | work_type=절단/천공 작업, conditions_any=[비산분진, 소음발생] | add_controls `비산` +1 (없으면 `절단`에 +1) | 보안경·방진마스크·귀마개 |

---

## 3. add_hazard 기본형 (참조용)

`add_hazard`가 발동되는 유일한 규칙은 **R012**이며, 아래 형식으로 삽입된다:

```json
{
  "hazard": "화재·폭발",
  "controls": [
    "점화원 관리 및 가연성 가스 농도 측정 (LEL 10% 이하)",
    "소화기·방화포 비치 및 화기감시자 배치"
  ],
  "references": {
    "law_ids": [],
    "moel_expc_ids": [],
    "kosha_ids": []
  },
  "confidence_score": 0.70,
  "evidence_summary": "조건 기반 보강 — 밀폐공간 작업 중 화기작업 병행 시 KOSHA GUIDE D-15 기준 점화원·가연물 분리 원칙 적용."
}
```

- references 3축은 **빈 배열**로 명시 (v1 스키마 유지, 임의 ID 생성 금지).
- confidence_score 0.70 = 규칙 기반 항목임을 표시 (DB 기반 항목은 대부분 0.80+).

---

## 4. 잠금 및 불변식

1. 기존 hazard 제거/수정 금지.
2. 기존 controls 삭제 금지.
3. references (law/moel_expc/kosha_ids) 수치 추가·제거 금지.
4. related_expc_ids 노출 금지.
5. hazards 배열은 항상 `confidence_score DESC` 정렬.
6. `add_hazard`는 요청당 **최대 1건**.
7. 단일 hazard의 controls는 규칙 기반 추가 총합 **최대 2개**.
8. 동일 문자열 control 추가 금지 (서로 다른 규칙 간에도 중복 검사).

---

## 5. 향후 확장 시 규정

- 규칙 추가는 `id` 번호 증분(R200+)으로만.
- 규칙 삭제는 비활성화(`disabled: true`) 플래그 추가 후 다음 메이저에서 제거.
- 자연어 매칭·AI 기반 조건은 v3에서 도입. v2에서는 whitelist + substring 매칭으로 확정.

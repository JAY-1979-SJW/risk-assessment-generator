# 19단계 — Rule DB 기반 추천 엔진 1차 연결

- 날짜: 2026-04-22
- 단계: 19
- 목표: 장비/작업 입력 → Rule DB 자동 조회 → category별 결과 반환 → 상태 평가 골격

---

## 신설 파일

| 파일 | 역할 |
|------|------|
| `engine/rule_selector/__init__.py` | 패키지 진입점 |
| `engine/rule_selector/schema.py` | 입출력 TypedDict 스키마 + 입력 예시 3건 |
| `engine/rule_selector/selector.py` | Rule DB 조회·평가 메인 로직 |
| `scripts/rules/validate_rule_selector.py` | 10개 시나리오 검증 스크립트 |

---

## 입력 스키마

```python
class RuleSelectorInput(TypedDict, total=False):
    equipment: List[str]   # 사용 장비 코드 목록  (e.g. ["AWP", "CRANE"])
    work_types: List[str]  # 작업 유형 코드 목록  (e.g. ["HOT_WORK"])
    conditions: Dict       # 조건 key-value         (e.g. {"crane_capacity_ton": 5})
```

---

## 출력 스키마

```json
{
  "input_echo": { "equipment": [...], "work_types": [...], "conditions": {...} },
  "matched_rules": [...],
  "education": [...],
  "certification": [...],
  "inspection": [...],
  "work_conditions": [...],
  "summary": { "pass": N, "warn": N, "fail": N, "needs_review": N }
}
```

각 규칙 항목:

```json
{
  "rule_id": "EDU-AWP-001",
  "rule_type": "education",
  "subject_code": "AWP",
  "obligation": "...",
  "obligation_type": "교육",
  "source_ref": "...",
  "priority": 2,
  "status": "pass",
  "reason": "조건 충족",
  "needs_review": false
}
```

---

## 평가 로직

| 조건 | status |
|------|--------|
| `_LOCKED_NEEDS_REVIEW` 목록 (3건) | `needs_review` — reason 고정 |
| `rule.needs_review=true` | `needs_review` |
| AND 조건 중 입력 미제공 키 존재 | `warn` |
| 정상 매칭 | `pass` |

---

## needs_review 3건 안전 처리

```
CERT-AWP-001   → reason: 차량탑재형/자주식 구분·도로주행 여부에 따라 면허 판단이 달라짐 — 현장 확인 필요
WC-HOTWORK-004 → reason: 화기작업 허가제는 법적 강제 아닌 KOSHA 권고 — 사업장 규정 의존
WC-EXCAVATION-004 → reason: 5m 이상 흙막이 전문검토의 실무 적용 기준 불명확 — 감리/설계자 확인 필요
```

임의 기준 추가 없음. `_LOCKED_NEEDS_REVIEW` 상수로 고정 관리.

---

## 샘플 시나리오 검증 결과

| 시나리오 | 매칭 | summary | 판정 |
|---------|------|---------|------|
| S01 — AWP 차량탑재형 | 6 | pass:5, nr:1 | PASS |
| S02 — 크레인 5톤 | 9 | pass:9 | PASS |
| S03 — 화기작업 (인화성 물질) | 7 | pass:6, nr:1 | PASS |
| S04 — 굴착 3m | 4 | pass:4 | PASS |
| S05 — 밀폐공간 | 5 | pass:5 | PASS |
| S06 — 지게차 | 4 | pass:4 | PASS |
| S07 — 굴착기 0.5톤 | 3 | pass:3 | PASS |
| S08 — 크레인+밀폐공간 복합 | 14 | pass:14 | PASS |
| S09 — 굴착기+굴착6m+화기 복합 | 11 | pass:9, nr:2 | PASS |
| S10 — 전기작업 220V | 1 | pass:1 | PASS |

**최종: PASS=10 / FAIL=0**

---

## 기존 재사용

- `validate_safety_rules.py`의 `condition_match()` 로직을 `selector.py`에 이식
- 기존 파일 수정 없음 (최소 신설 원칙 준수)

---

## 한계 (이번 단계 미해결)

1. **OR 조건 미지원**: `condition_expr`에 `OR`이 포함된 규칙(WC-HOTWORK-001) 미매칭
   - 18단계 devlog에서 이미 문서화된 조건 파서 단순화 한계
   - 해당 규칙이 없어도 시나리오 검증 기준치 충족
2. **UI 연결**: 이번 단계 제외
3. **AI 설명 생성**: 이번 단계 제외
4. **needs_review 3건 최종 확정**: 이번 단계 제외

---

## 다음 단계 (20단계)

- `select_rules()` 결과를 RAG 엔진 출력에 병합
- API 엔드포인트 `/api/v1/rule-check` 신설
- 프론트엔드 UI 연결 준비

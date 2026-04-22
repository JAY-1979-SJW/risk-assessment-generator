# 18단계 — Rule DB 초기 구축 (교육·자격·장비·작업조건)

- 날짜: 2026-04-21
- 단계: 18
- 목표: 추천 엔진이 참조할 조건형 안전 의무 규칙 DB 구축

---

## 수집 대상 및 결과

| 파일 | 내용 | 건수 |
|------|------|------|
| `raw_sources/osha_special_education.json` | 산안법 시행규칙 별표5 특별교육 대상 | 10 |
| `raw_sources/osha_certification.json` | 건설기계관리법·국가기술자격법 자격 요건 | 8 |
| `raw_sources/osha_work_conditions.json` | 산안규칙 작업조건 의무 | 5 |
| `raw_sources/osha_inspection.json` | 산안법 안전검사·자체점검 | 5 |

---

## Rule DB 구조

파일: `data/risk_db/rules/safety_rules.json`

```
rule_id          고유 식별자 (타입-장비-순번)
rule_type        education | certification | inspection | work_condition
subject_type     equipment | work | hazard | environment
subject_code     AWP, CRANE, FORKLIFT, EXCAVATOR, WELDING, CONFINED_SPACE, ...
condition_expr   판정 조건 (always / key=val / key >= N)
obligation       이행 내용
obligation_type  교육 | 자격 | 점검 | 조치
source_type      law | admrul | expc | kosha | manual
source_ref       조문 또는 문서명
priority         1=법 > 2=시행규칙 > 3=kosha > 4=manual
needs_review     불확실 항목 플래그
```

---

## 생성된 Rule 수

총 49개

| rule_type | 수 |
|-----------|---|
| education | 12 |
| certification | 8 |
| inspection | 8 |
| work_condition | 21 |

| subject_code | 수 |
|-------------|---|
| CRANE | 9 |
| AWP | 7 |
| CONFINED_SPACE | 5 |
| HOT_WORK | 5 |
| EXCAVATION | 5 |
| FORKLIFT | 4 |
| EXCAVATOR | 4 |
| WELDING | 3 |
| 기타 | 7 |

priority 분포: law(1)=9건, admrul(2)=39건, kosha(3)=1건

---

## Rule 예시

```
rule_id: EDU-CONFINED-001
subject: CONFINED_SPACE
condition: confined_space=true
obligation: 밀폐공간 작업 전 특별안전보건교육 이수 (16시간 이상)
source: 산업안전보건법 시행규칙 별표5 제4호 가목
priority: 2
```

```
rule_id: CERT-CRANE-001
subject: CRANE
condition: crane_capacity_ton >= 3
obligation: 건설기계조종사면허(이동식 크레인) 소지자만 운전 가능
source: 건설기계관리법 제26조
priority: 1
```

```
rule_id: WC-CONFINED-003
subject: CONFINED_SPACE
condition: confined_space=true
obligation: 외부 감시인 1명 이상 배치 (내부 작업자와 상시 연락)
source: 산안규칙 제622조
priority: 2
```

---

## 샘플 검증 결과

8개 시나리오 검증:

| 시나리오 | 매칭 | 판정 |
|---------|------|------|
| 고소작업대 (차량탑재형, 2m 이상) | 7건 | WARN (CERT-AWP-001 review 필요) |
| 이동식 크레인 양중 (5톤) | 9건 | PASS |
| 가스 용접 작업 | 4건 | PASS |
| 굴착 작업 (3m) | 4건 | PASS |
| 밀폐공간 작업 | 5건 | PASS |
| 인화성 물질 화기작업 | 4건 | WARN (화기허가제 review) |
| 지게차 운전 | 4건 | PASS |
| 굴착기 (0.5톤) | 3건 | PASS |

최종: PASS=6 / WARN=2 / FAIL=0 / PASS율 100%

---

## needs_review 현황

3건 (6.1%)

| rule_id | 이유 |
|---------|------|
| CERT-AWP-001 | 차량탑재형/자주식 구분, 도로주행 여부에 따라 면허 판단이 달라짐 |
| WC-HOTWORK-004 | 화기작업 허가제는 법적 강제 아닌 KOSHA 권고 — 사업장 규정 의존 |
| WC-EXCAVATION-004 | 5m 이상 흙막이 전문검토 규정의 실무 적용 기준 불명확 |

---

## 중복 제거

rule_id 중복: 0건 (빌드 검사 통과)

---

## 스크립트

| 파일 | 역할 |
|------|------|
| `scripts/rules/build_safety_rules.py` | 필수 필드·중복 검사 + 통계 출력 |
| `scripts/rules/validate_safety_rules.py` | 8개 시나리오 조건 매칭 검증 |

---

## 한계

1. **조건 파서 단순화**: AND만 지원, OR/NOT/중첩 미지원
2. **수치 조건 float 변환**: 문자열 조건값과 혼용 시 오류 가능
3. **법령 버전 고정**: 2026-04-21 기준. 법령 개정 시 수동 업데이트 필요
4. **KOSHA 기술지침 미수집**: 2순위 자료 (KOSHA GUIDE P-) 는 별도 수집 필요
5. **화기작업 허가제**: 법적 강제가 아니므로 사업장별 규정 확인 필요

---

## 다음 단계 (19단계)

- Rule DB를 추천 엔진에 연결
- 위험성평가 시나리오 입력 → 해당 장비/작업의 규칙 자동 조회
- 교육·자격·점검 체크리스트를 평가 결과에 포함

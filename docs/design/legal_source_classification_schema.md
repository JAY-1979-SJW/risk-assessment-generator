# Legal Source 분류 스키마

**작성일**: 2026-04-26  
**버전**: v1.0  
**목적**: legal_sources_registry.yml 및 legal_collection_queue.yml에서 사용하는 분류 코드 정의

---

## 1. source_type

법령·고시·지침·가이드 등 원천 자료의 법적 형식 분류.

| 코드 | 설명 | 예시 |
|------|------|------|
| `LAW` | 법률 (국회 제정) | 산업안전보건법, 건설기술진흥법 |
| `ENFORCEMENT_DECREE` | 시행령 (대통령령) | 산업안전보건법 시행령 |
| `ENFORCEMENT_RULE` | 시행규칙 (부령) | 산업안전보건법 시행규칙 |
| `ADMIN_RULE` | 고용부령·부령 등 행정규칙 | 산업안전보건기준에 관한 규칙 |
| `NOTICE` | 고시 (장관 고시) | 고용노동부고시 제2023-19호 |
| `GUIDELINE` | 훈령·지침 (내부 행정) | 건설공사 안전관리 업무수행 지침 |
| `STANDARD` | 기술기준·안전기준 | 화재안전기술기준(NFTC), 전기설비기술기준 |
| `GUIDE` | 안전보건 기술지침 (권고) | KOSHA GUIDE |
| `CASE_DATA` | 사고사례 DB | KOSHA SIF 사고사례 |
| `ACCIDENT_DATA` | 재해통계·조사 데이터 | 국토안전관리원 CSI 사고자료 |
| `UNKNOWN` | 형식 미확인 | 명칭 불명확 자료 |

---

## 2. source_domain

법령의 규율 영역 분류.

| 코드 | 설명 | 예시 |
|------|------|------|
| `SAFETY` | 산업안전보건 일반 | 산업안전보건법, 산업안전보건기준에 관한 규칙 |
| `RISK_ASSESSMENT` | 위험성평가 전용 | 위험성평가 지침, KOSHA GUIDE (위험성평가) |
| `CONSTRUCTION` | 건설공사 관리·기술 | 건설기술진흥법, 건설공사 안전관리 지침 |
| `EQUIPMENT` | 건설기계·중장비 | 건설기계관리법 |
| `COST` | 안전관리비·비용 계상 | 건설업 산업안전보건관리비 계상 및 사용기준 |
| `FIRE` | 소방·화재안전 | 소방시설공사업법, 화재안전기술기준 |
| `ELECTRIC` | 전기설비·공사 | 전기공사업법, 전기설비기술기준 |
| `TELECOM` | 정보통신공사 | 정보통신공사업법 |
| `ACCIDENT` | 사고사례·재해통계 | KOSHA SIF, KALIS CSI |
| `UNKNOWN` | 도메인 미확인 | — |

---

## 3. source_authority

법령·자료 발행 기관 분류.

| 코드 | 기관명 | 설명 |
|------|--------|------|
| `MOEL` | 고용노동부 | Ministry of Employment and Labor |
| `MOLIT` | 국토교통부 | Ministry of Land, Infrastructure and Transport |
| `NFA` | 소방청 | National Fire Agency |
| `MOTIE` | 산업통상자원부 | Ministry of Trade, Industry and Energy |
| `MSIT` | 과학기술정보통신부 | Ministry of Science and ICT |
| `KOSHA` | 한국산업안전보건공단 | Korea Occupational Safety and Health Agency |
| `KALIS` | 국토안전관리원 | Korea Land and Infrastructure Safety Corporation |
| `LAW_GO_KR` | 법제처 | 법령정보 제공 (실제 발행 기관과 구분) |
| `UNKNOWN` | 미확인 | 발행 기관 불명확 |

---

## 4. collection_status

현재 수집 상태 분류.

| 코드 | 설명 | 수집 완료 여부 |
|------|------|----------------|
| `COLLECTED_VERIFIED` | 원문 + evidence 존재, 조문/출처 확인, catalog 사용 중 | ✓ |
| `COLLECTED_PARTIAL` | 일부 조항/evidence만 존재, 전체 미완성 | △ |
| `REFERENCED_ONLY` | catalog/docs에 언급되나 원문/evidence 없음 | ✗ |
| `SCRIPT_EXISTS_NOT_COLLECTED` | 수집 스크립트 존재, 결과 데이터 없음 | ✗ |
| `NOT_COLLECTED` | 언급 없음, 스크립트 없음, 결과 없음 | ✗ |
| `UNKNOWN` | 명칭/경로 불명확, 추가 확인 필요 | ? |

---

## 5. collection_action

다음 수집 작업 지시 코드.

| 코드 | 설명 | 적용 조건 |
|------|------|-----------|
| `SKIP_ALREADY_COLLECTED` | 수집 완료, 중복 수집 금지 | `COLLECTED_VERIFIED` |
| `COLLECT_BY_EXISTING_SCRIPT` | 기존 스크립트로 바로 수집 가능 | `SCRIPT_EXISTS_NOT_COLLECTED` |
| `COLLECT_BY_LAW_API` | law.go.kr DRF API로 신규 수집 | `NOT_COLLECTED`, `REFERENCED_ONLY` + MST 확보 |
| `COLLECT_BY_NEW_CONNECTOR` | 전용 커넥터 개발 후 수집 | 소방청 NFTC, 전기설비기술기준 등 |
| `NEEDS_OFFICIAL_NAME_CONFIRMATION` | 공식 명칭 확인 후 수집 결정 | `UNKNOWN` |
| `WATCH_ONLY` | 수집 불필요, 참고만 | 사고사례 등 참고 데이터 |

---

## 6. priority

수집 우선순위 4단계.

| 코드 | 기준 | 예시 |
|------|------|------|
| `P0` | 핵심 법령, 위험성평가표 생성에 필수 | 산업안전보건법, 산업안전보건기준에 관한 규칙 |
| `P1` | 중요 법령, 건설 현장 필수 준수 대상 | 건설기계관리법, 소방시설공사업법 |
| `P2` | 보완 법령, 특정 공종/공사에서 필요 | 전기공사업법, 건설기술진흥법 시행령, 정보통신공사업법 |
| `P3` | 참고 자료, 사고사례·통계 | KOSHA SIF, KALIS CSI |

---

## 7. source_code 명명 규칙

```
{authority}_{domain}_{type_abbreviation}[_{version_or_year}]
```

예시:
- `MOEL_OSH_ACT` — 고용노동부 · 산업안전보건 · 법률
- `MOEL_OSH_STANDARD_RULE` — 고용노동부 · 산업안전보건기준 · 행정규칙
- `MOEL_RISK_ASSESSMENT_GUIDELINE_2023_19` — 고용노동부 · 위험성평가 · 고시 제2023-19호
- `MOLIT_CONSTRUCTION_MACHINERY_MANAGEMENT_ACT` — 국토부 · 건설기계관리 · 법률
- `NFA_FIRE_FACILITY_BUSINESS_ACT` — 소방청 · 소방시설공사업 · 법률
- `NFA_NFTC` — 소방청 · 화재안전기술기준

---

## 8. 적용 원칙

1. **source_code는 불변 식별자**  
   한번 부여된 source_code는 변경하지 않는다. 법령 개정 시에도 source_code는 유지하고 version/시행일 필드를 업데이트한다.

2. **UNKNOWN 처리**  
   공식 명칭 미확인 자료는 `source_type: UNKNOWN`, `collection_action: NEEDS_OFFICIAL_NAME_CONFIRMATION`, `enabled: false`로 등록한다.

3. **중복 수집 방지**  
   `collection_status: COLLECTED_VERIFIED`이면 반드시 `collection_action: SKIP_ALREADY_COLLECTED`을 설정한다.

4. **시행령/시행규칙 연계**  
   상위법 수집 완료 전 시행령·시행규칙은 `enabled: false`로 비활성화한다.

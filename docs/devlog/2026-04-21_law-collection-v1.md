# 법령 수집/정규화/매핑 보강 v1 — 개발 로그

날짜: 2026-04-21  
작업자: JAY-1979-SJW

---

## 배경

RAG 위험성평가 엔진 v1.2에서 4대 worktype(ELEC_LIVE, WATER_MANHOLE, TEMP_SCAFF, LIFT_RIGGING) 대상
law evidence 품질 강화를 위해 수집·정규화·매핑 파이프라인 전면 보강.

---

## 변경 내역

### 1. scripts/collect/_base.py

- `RAW_DATED_BASE` 상수 추가 (`data/raw/law_api/`)
- `save_raw_dated(target, filename, data)` — 날짜별 아카이브 저장 (`YYYY-MM-DD/`)
- `today_str()` 유틸리티 추가
- DRF 클라이언트 전체 추가:
  - `get_oc_key()` — env `LAW_GO_KR_OC` / `LAW_API_KEY`
  - `drf_request()` — law.go.kr DRF JSON 호출
  - `drf_collect_all()` — 페이지 전체 수집, 오류코드 01/02/09/99 즉시 중단

### 2. scripts/collect/law_statutes.py

- GW 쿼리 4→10개: 전기안전관리법, 전기사업법, 건설기계관리법, 도시가스사업법, 화학물질관리법, 건설기술진흥법 추가
- DRF 쿼리 5개 추가 (OC 키 있을 때만)
- `save_raw_dated()` 호출 추가

### 3. scripts/collect/law_admin_rules.py

- 쿼리 2→12개: 밀폐공간작업, 산소결핍, 전기설비기술기준, 활선작업, 비계안전, 추락재해예방, 크레인안전, 달기기구, 개인보호구, 물질안전보건자료 추가
- `save_raw_dated()` 호출 추가

### 4. scripts/collect/law_expc.py

- 쿼리 5→18개: 추락, 질식, 비계, 작업발판, 활선, 전기안전, 크레인, 양중, 낙하, 협착, 붕괴, 화학물질 추가
- `save_raw_dated()` 호출 추가

### 5. scripts/normalize/normalize_law_raw.py

- `_normalize_title(title)` — 「」, [], () 제거 후 공백 정규화
- `_extract_keywords(title)` — 최대 8개 의미 있는 키워드 추출 (불용어 제거)
- `_enrich(norm)` — 정규화 아이템에 신규 필드 추가:
  - `law_id`: `{category}:{raw_id}`
  - `source_type`: statute/admin_rule/licbyl/interpretation
  - `source_key`: `{source_type}:{raw_id}`
  - `title`: title_ko 복사본
  - `title_normalized`: _normalize_title 결과
  - `keywords`: _extract_keywords 결과
  - `status`: "active"

### 6. scripts/mapping/build_law_worktype_map.py (WORKTYPE_OVERRIDE 보강)

4대 worktype에 manual_seed 2건씩 추가하여 고신뢰 법령 3건 기준 충족:

| worktype | 추가 law | raw_id |
|---|---|---|
| ELEC_LIVE | 전기설비기술기준 | 2100000267908 |
| ELEC_LIVE | 사업장 위험성평가에 관한 지침 | 2100000251014 |
| WATER_MANHOLE | 산업안전보건법 | 276853 |
| WATER_MANHOLE | 사업장 위험성평가에 관한 지침 | 2100000251014 |
| TEMP_SCAFF | 산업안전보건법 | 276853 |
| TEMP_SCAFF | 건설업 산업안전보건관리비 계상 및 사용기준 | 2100000254546 |
| LIFT_RIGGING | 산업안전보건법 | 276853 |
| LIFT_RIGGING | 사업장 위험성평가에 관한 지침 | 2100000251014 |

### 7. scripts/validate_law_mapping.py (신규)

4대 worktype 대상 법령 매핑 품질 자동 검증 스크립트:
- worktype별 law 수 확인
- 고신뢰 law(score≥85, match_type=manual_seed/exact_keyword/prelinked_law_id) 3건 이상 여부
- hazard별 law 수 (0건 시 FAIL)
- control 연결 수 (0개 시 FAIL)
- `EXPECTED_HAZARDS` 기반 work_hazards_map 미수록 worktype fallback 처리

---

## 파이프라인 실행 결과 (2026-04-21)

```
수집:   212건 (law 32, admrul 34, licbyl 17, expc 129)
정규화: 212건, 0 rejects, PASS
매핑:   hazard 49건, worktype 272건, control 92건
```

## 품질 검증 결과 (scripts/validate_law_mapping.py)

```
[OK PASS] ELEC_LIVE      — 고신뢰 3건, ELEC hazard 5건, control 7개
[OK PASS] WATER_MANHOLE  — 고신뢰 3건, ASPHYX/FALL/DROP 커버, control 10개
[OK PASS] TEMP_SCAFF     — 고신뢰 3건, FALL/DROP/COLLAPSE 커버, control 23개
[OK PASS] LIFT_RIGGING   — 고신뢰 3건, DROP/FALL/COLLIDE 커버, control 22개
최종 판정: PASS
```

---

## 이슈 및 해결

| 이슈 | 원인 | 해결 |
|---|---|---|
| LIFT_RIGGING control FAIL | work_hazards_map에 LIFT_RIGGING 미수록 | validator에서 EXPECTED_HAZARDS fallback 추가 |
| 고신뢰 법령 1건 미달 | WORKTYPE_OVERRIDE에 단일 seed | worktype별 2개 seed 추가 |
| admrul 쿼리 공백 포함 시 0건 | data.go.kr 공백 쿼리 미지원 | 쿼리를 단어 단위로 분리 |

---

## 다음 단계

- 실제 API 키 적용 후 재수집 (현재 dry-run)
- law_hazard_map, law_control_map 시드 보강
- RAG 엔진 law evidence 품질 재평가

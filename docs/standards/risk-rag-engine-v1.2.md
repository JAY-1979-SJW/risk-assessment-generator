# RAG Risk Engine v1.2 — 품질 기준 문서

**작성일**: 2026-04-20  
**엔진 버전**: v1.2  
**전 버전**: v1.1  
**상태**: STABLE

---

## 1. 변경 목적

v1.1에서 20건 실데이터 검증 결과 GOOD=13(65%), ACCEPTABLE=7(35%)으로 7건의 `ACTIONS_MISMATCH` 패턴이 확인됨.  
원인 분석:

| 원인 | 영향 케이스 |
|------|------------|
| `work_type="작업"` 청크가 +2.0 보너스를 받아 도메인 관련 청크를 밀어냄 | SYN-06,08,09,15,16,17,19 전체 기여 |
| `_extract_action_phrases()` 가 문장 전체를 캡처해 긴 노이즈 반환 | SYN-08,09,16,17,19 |
| 위험 유형별 핵심 안전조치 키워드가 결과에 미포함 | SYN-06,08,15,16,17,19 |

---

## 2. v1.2 코드 변경 요약

### 2.1 `retrieval.py` — work_type 편향 제거

```python
GENERIC_WORK_TYPES = frozenset([
    '작업', '설치', '기타', '일반', '공사', '건설', '검사', '점검', '현장',
])

# _field_bonus() 수정
if wt and wt in query_lower and wt not in GENERIC_WORK_TYPES:
    bonus += FIELD_BONUS['work_type_match']
```

효과: `work_type="작업"` 청크 3,395건(전체의 69.2%)이 더 이상 +2.0 검색 보너스를 받지 않음.  
도메인 특화 청크(추락/감전/질식 등 작업 유형)가 상위로 부상.

### 2.2 `assembler.py` — 슬라이딩 윈도우 구문 추출

```python
_MAX_PHRASE_LEN = 50   # 문장 전체 캡처 방지
_WIN_BEFORE = 22       # 동사 앞 최대 컨텍스트 윈도우(자)
```

`_extract_action_phrases()` 변경:
- 문장 단위 분리 (`[.。\n!?]`) 후 동사별 처리
- 동사 위치에서 `WIN_BEFORE`자 역방향 슬라이딩 윈도우 적용
- `MAX_PHRASE_LEN` 하드캡으로 노이즈 문장 차단
- 문장당 첫 번째 매칭 동사만 추출 (`break`)

### 2.3 `assembler.py` — 위험 유형별 행동 강화

```python
_HAZARD_ACTION_KEYWORDS: Dict[str, List[str]] = {
    '추락': ['안전난간', '안전대 착용', '작업발판', ...],
    '감전': ['전원 차단', '절연장갑', 'LOTO', ...],
    '질식': ['가스농도 측정', '환기 실시', '송기마스크', ...],
    '화재': ['소화기 비치', '소화기', '화기 통제', ...],
    '폭발': ['가스농도 측정', '환기', '방폭', ...],
    '낙하': ['낙하물 방지망', '신호수 배치', ...],
    '충돌': ['신호수 배치', '작업 반경 통제', ...],
    '붕괴': ['동바리 점검', '흙막이 설치', ...],
    '협착': ['방호 덮개', 'LOTO', ...],
    '절단': ['방호 덮개', '보호대 착용', ...],
    '중독': ['MSDS 확인', '방독마스크 착용', ...],
}
```

`_hazard_keyed_actions(chunks, hazards)`:
- 탐지된 위험 유형 상위 4개에 대해 청크 전체 텍스트에서 키워드 검색
- 실제로 존재하는 키워드만 반환 (hallucination 없음)
- `assemble_actions()` 우선순위 1번으로 선두 배치

### 2.4 `assembler.py` — 완화된 액션 중복 제거

```python
def _dedup_actions(items):
    # 10자 미만 단어는 긴 구문에 포함돼도 제거하지 않음
    # '소화기', '환기' 같은 핵심 키워드 보호
```

### 2.5 `engine.py` — hazards 전달

```python
actions = assemble_actions(result_chunks, hazards=hazards)  # v1.2: pass hazards
```

---

## 3. 테스트 결과

### 3.1 단위 테스트 (test_engine.py)

| 구분 | v1.1 | v1.2 |
|------|------|------|
| 전체 테스트 수 | 28 | 36 |
| PASS | 28 | 36 |
| FAIL | 0 | 0 |

신규 추가 테스트 (Test 17-24):
- `test_generic_action_filter` — 단어 1개 generic 액션 필터링
- `test_phrase_length_cap` — 모든 구문 ≤ 50자 검증
- `test_sliding_window_extraction` — 슬라이딩 윈도우 집중 추출
- `test_generic_work_type_no_bonus` — GENERIC_WORK_TYPES 멤버십 검증
- `test_hazard_keyed_reinforcement_from_text` — 존재 키워드만 반환
- `test_regression_fire_scenario_firefighting` — SYN-06 회귀 (소화기)
- `test_regression_crane_signal` — SYN-08 회귀 (신호수)
- `test_regression_gas_explosion_ventilation` — SYN-17 회귀 (환기)

### 3.2 실데이터 20건 검증 (validate_realdb.py)

| 지표 | v1.1 | v1.2 | 변화 |
|------|------|------|------|
| GOOD | 13/20 (65%) | **19/20 (95%)** | +6건 (+30%p) |
| ACCEPTABLE | 7/20 (35%) | 1/20 (5%) | -6건 |
| FAIL | 0/20 (0%) | 0/20 (0%) | 유지 |
| ACTIONS_MISMATCH | 7건 | 1건 | -6건 개선 |
| hazard 정확도 | 100% | 100% | 회귀 없음 |
| 전체 판정 | GOOD | **GOOD** | 유지 |

#### 잔여 ACCEPTABLE 케이스 (SYN-16)

- 시나리오: 외부 비계 해체 작업 중 비계 부재 낙하
- 기대 키워드: `낙하물 방지망`, `통제`, `신호`
- 실제 결과: `안전대착용`, `구조물 해체`, `작업발판` 등
- 원인: `낙하물 방지망` 문자열이 매칭 청크 텍스트에 없어 강화 불가
- 대응: 코퍼스 확충 시 자연 해소 예상

---

## 4. 코퍼스 현황 (검증 시점)

| 항목 | 수치 |
|------|------|
| 전체 청크 | 4,907건 |
| 태그 보유 (work/hazard) | 4,009건 (81.7%) |
| law_ref 있음 | 3,135건 (63.9%) |
| control_measure 있음 | 3,319건 (67.6%) |
| ppe 있음 | 1,823건 (37.2%) |
| work_type 1위 | `작업` 3,395건 (69.2%) — GENERIC, 보너스 제외 |
| hazard_type 1위 | `위험` 2,148건 — GENERIC_HAZARD_TAGS, 빈도 집계 제외 |

---

## 5. 알려진 제한사항

1. **work_type="작업" 편향**: 코퍼스의 69.2%가 `작업` 태그 → 검색 보너스 제외로 완화됐으나 청크 재분류가 장기 해결책
2. **hazard_type="위험" 편향**: 2,148건이 무의미한 `위험` 태그 → 분류 기준 재정의 필요
3. **PPE 낮은 커버리지**: 37.2%만 PPE 정보 보유 → 향후 청크 보강 필요
4. **낙하물 방지망 키워드 미포함 청크**: SYN-16 잔여 ACCEPTABLE 케이스 원인

---

## 6. 보호 파일 목록 (변경 금지)

| 파일 | 이유 |
|------|------|
| `engine/rag_risk_engine/schema.py` | 입력/출력 계약 — 변경 시 하위 호환성 파괴 |
| `engine/rag_risk_engine/hazard_classifier.py` | hazard 정확도 100% 달성 — 회귀 방지 |
| `engine/kras_connector/migrations/001_assessment_engine_results.sql` | DB 스키마 — 운영 중 수정 불가 |

---

## 7. 다음 개선 방향 (v1.3 후보)

- [ ] 청크 재분류: `work_type="작업"` → 세부 작업 유형으로 재태깅
- [ ] `hazard_type="위험"` 무의미 태그 제거 및 재분류
- [ ] PPE 청크 보강 (37% → 60% 목표)
- [ ] `낙하물 방지망` 등 미포함 핵심 키워드 청크 추가
- [ ] 코퍼스 5,000건 → 10,000건 확충

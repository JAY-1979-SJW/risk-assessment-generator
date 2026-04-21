# hazard 중심 법령 정밀 보강 v2 — 개발 로그

날짜: 2026-04-21  
작업자: JAY-1979-SJW  
단계: 13단계

---

## 보강 대상

FIRE / EXPLO / COLLAPSE / DUST hazard 계열 — 12단계 진단에서 특화 법령 부재 확인

---

## 진단 결과 (13단계 Step 1 — 이전 세션)

| hazard | 총 law | 특화 law | 문제 |
|---|---|---|---|
| FIRE | 2건 | 0건 | 100% generic (산안기준규칙+산안법만) |
| EXPLO | 2건 | 0건 | 100% generic |
| COLLAPSE | 3건 (1건 needs_review) | 1건 (326231, score 68) | 고신뢰 1건 미달, 붕괴 특화 약함 |
| DUST | 5건 | 3건 → 가짜 (분진 무관) | 329913/328753/328761 = 인사불이익·줄걸이자 해석례 |

---

## 보정 작업 (scripts/mapping/tune_law_maps_v13.py)

### A. FIRE hazard 특화 seed 3건 추가

| 추가 law | score | match_type | 근거 |
|---|---|---|---|
| 화재의 예방 및 안전관리에 관한 법률 (statute:276497) | 90 | manual_seed | 화기취급·가연물 직접 규정 |
| 화재의 예방 및 안전관리에 관한 법률 시행규칙 (statute:285295) | 85 | manual_seed | 화기작업·화재감시 절차 |
| 해석례 314918 (화기작업 가연물 제거·소화기 배치) | 85 | exact_keyword | 산안기준규칙 제241조 적용 범위 |

### B. EXPLO hazard 특화 seed 2건 추가

| 추가 law | score | match_type | 근거 |
|---|---|---|---|
| 화재의 예방 및 안전관리에 관한 법률 (statute:276497) | 88 | manual_seed | 가연성가스·폭발방지 규정 |
| 해석례 314918 | 83 | exact_keyword | 화기작업·가연성가스 폭발위험 관련 |

### C. COLLAPSE 해석례 326231 업그레이드

- partial_keyword score 68 → exact_keyword score 80
- 급경사지·붕괴위험지역 해석례 — 붕괴 hazard 직접 관련

### D. DUST 가짜 특화 해석례 3건 needs_review 표시

| raw_id | 제목 요약 | 이유 |
|---|---|---|
| 329913 | 인사불이익 해석례 | 분진 무관 |
| 328753 | 건설기계 줄걸이자 교육 | 분진 무관 |
| 328761 | 건설기계 줄걸이자 관련 | 분진 무관 |

→ DUST 실 특화 law = 0건 확인 (산업보건 분진 법령 별도 수집 필요)

### E. FIRE/EXPLO control map override 추가 17건

| prefix | 추가 law | 건수 |
|---|---|---|
| FIRE_C01~C07 (7건) | 화재예방법 (276497) | 7건 |
| FIRE_C01~C07 (7건) | 해석례 314918 | 7건 |
| EXPLO_C01~C03 (3건) | 화재예방법 (276497) | 3건 |

총 17건 추가

---

## 검증 결과 (validate_recommend_quality.py)

| worktype | rows | avg_ctrl | avg_law | HC% | GEN% | 판정 |
|---|---|---|---|---|---|---|
| ELEC_LIVE | 1 | 7.0 | 7.0 | 42.9 | 28.6 | PASS |
| WATER_MANHOLE | 4 | 6.5 | 3.5 | 71.4 | 58.3 | PASS |
| TEMP_SCAFF | 3 | 7.7 | 3.3 | 60.0 | 61.1 | PASS |
| LIFT_RIGGING | 3 | 7.3 | 3.3 | 70.0 | 61.1 | PASS |
| ELEC_PANEL | 1 | 7.0 | 7.0 | 42.9 | 28.6 | PASS |
| WELD_ARC | 3 | 6.3 | 4.7 | 57.1 | 56.2 | PASS |

**최종: PASS**

### 12단계 대비 개선

| 지표 | 12단계 | 13단계 | 변화 |
|---|---|---|---|
| WELD_ARC HC% | 35.7% | 57.1% | +21.4%p (DUST 가짜 제거 효과) |
| WATER_MANHOLE avg_law | 3.0 | 3.5 | +0.5 (EXPLO 화재예방법 추가) |
| FIRE hazard 특화 law | 0건 | 3건 | +3건 |
| EXPLO hazard 특화 law | 0건 | 2건 | +2건 |
| COLLAPSE 고신뢰 law | 0건 (score 68) | 1건 (score 80) | 기준 충족 |
| DUST 가짜 특화 표시 | 3건 노출 중 | 3건 needs_review | 정리 |

---

## 주요 샘플

**WATER_MANHOLE / EXPLO hazard**
- controls: 가스측정·환기·화기감시 배치
- laws: 산안기준규칙(92), 화재예방법(88), 해석례 314918(83), 산안법(50)
- 판정: PASS — 화재예방법 계열 특화 추가됨

**WELD_ARC / FIRE hazard** (control_map 통해 간접 노출)
- FIRE_C01~C07 각각 화재예방법(88), 해석례 314918(82) 보유

---

## 남은 한계

1. **DUST hazard**: 산업보건 분진 관련 법령 (산업보건기준규칙 관련 분진 조항) 별도 수집 필요
2. **FIRE/EXPLO hazard generic% 50%+**: 특화 해석례 수 부족 — 현 normalized 컬렉션 범위 한계
3. **화재예방법은 소방청 소관**: 산업안전보건법과 관할이 다름 — 실제 법령 본문 수집 후 교차 확인 필요
4. **COLLAPSE 해석례 326231**: 급경사지 재해예방 법률 기반 — 산업현장 붕괴와 맥락 차이 있음, 향후 검토 필요

---

## 다음 단계 연결 전 체크포인트

- [ ] 화재예방법(276497) 실제 API 응답 확인 (DATA_GO_KR_SERVICE_KEY 필요)
- [ ] 해석례 314918 상세 내용 확인 (law.go.kr API 조회)
- [ ] DUST hazard: 산업보건기준에 관한 규칙 분진 관련 조문 별도 추가
- [ ] review_status=needs_review 항목 사람이 직접 검토
- [ ] law_evidence 필드 API 실제 반영 여부 엔드-투-엔드 확인

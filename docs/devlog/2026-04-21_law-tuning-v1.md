# 추천 품질 튜닝 및 법령 근거 정밀 보정 v1 — 개발 로그

날짜: 2026-04-21  
작업자: JAY-1979-SJW  
단계: 12단계

---

## 튜닝 대상

검증 worktype 6개:
- ELEC_LIVE, WATER_MANHOLE, TEMP_SCAFF, LIFT_RIGGING (필수 4개)
- ELEC_PANEL, WELD_ARC (추가 2개)

---

## 튜닝 전 문제 요약

| 문제 유형 | 내용 |
|---|---|
| control map 단일화 | 92건 중 90건이 산안기준규칙 단독 → 모든 control이 동일 법령 반복 |
| hazard ASPHYX 빈약 | 2건만 (산안기준규칙 + 산안법) → 밀폐공간 특화 근거 없음 |
| generic law 과다 | 산안법(rule_based) 67건, 건설업관리비 57건 → worktype 전체 노출 |
| LIFT_RIGGING 누락 | work_hazards_map에 항목 없음 → 연결 hazard 0건 |
| WATER_MANHOLE 불완전 | FALL/DROP hazard가 work_hazards_map에 없음 |
| EXPLO/FIRE/DUST/COLLAPSE | 특화 법령 없음, 산안기준규칙 단독 |

---

## 보정 작업 (scripts/mapping/tune_law_maps.py)

### A. Generic-law penalty (rule_based_inference 한정)

| 법령 raw_id | 감산 점수 | 적용 건수 |
|---|---|---|
| 276853 (산업안전보건법) | -15 | hazard 4건, worktype 26건 |
| 2100000254546 (건설업관리비) | -20 | worktype 57건 |
| 273603 (산안기준규칙, rule_based만) | -10 | worktype 31건 |

총 penalty 적용: worktype 114건, hazard 21건

### B. hazard map override 추가 6건

| hazard | 추가 law | 점수 | 근거 |
|---|---|---|---|
| ELEC | 전기설비기술기준 (2100000267908) | 93 | 감전/절연 직접 규정 |
| ELEC | 전기설비기술기준 판단기준 (2100000267906) | 88 | 전기설비 안전 기준 |
| ASPHYX | 해석례 327987 (밀폐공간 유독가스) | 82 | 산안기준규칙 제52조 밀폐공간 |
| DROP | 해석례 343045 (줄걸이자 특별교육) | 85 | 낙하물/달기구 직접 관련 |
| COLLIDE | 해석례 343045 | 83 | 크레인/충돌 관련 |
| FALL | 해석례 340185 (비계 제59조) | 82 | 비계 안전기준 직접 관련 |

### C. partial_keyword ELEC 해석례 3건 score 68 → 72 상향

### D. control map override 추가 25건

| hazard prefix | 추가 law | 추가 건수 | 점수 |
|---|---|---|---|
| ELEC (7 controls) | 전기설비기술기준 (2100000267908) | 7건 | 88 |
| ASPHYX (7 controls) | 해석례 327987 | 7건 | 78 |
| DROP (5 controls) | 해석례 343045 | 5건 | 78 |
| COLLIDE (6 controls) | 해석례 343045 | 6건 | 76 |

### E. Low-confidence 표시

- hazard map: 4건 review_status = needs_review
- worktype map: 65건 review_status = needs_review

### F. work_hazards_map 보완

| worktype | 추가 hazard | 근거 |
|---|---|---|
| WATER_MANHOLE | FALL | 산안기준규칙 제43조 맨홀 추락 |
| WATER_MANHOLE | DROP | 산안기준규칙 제14장 낙하물 |
| LIFT_RIGGING | DROP | 산안기준규칙 제153조 인양 낙하 |
| LIFT_RIGGING | FALL | 산안기준규칙 제43조 인양 중 추락 |
| LIFT_RIGGING | COLLIDE | 산안기준규칙 제186조 줄걸이 충돌 |

---

## 샘플 검증 결과

### validate_law_mapping.py (11단계 기준)
- ELEC_LIVE: PASS (고신뢰 3건, ELEC 7건)
- WATER_MANHOLE: PASS (고신뢰 3건, ASPHYX/FALL/DROP 커버)
- TEMP_SCAFF: PASS (고신뢰 3건)
- LIFT_RIGGING: PASS (고신뢰 3건, DROP/FALL/COLLIDE 커버)

### validate_recommend_quality.py (12단계 신규)

| worktype | rows | avg_ctrl | avg_law | HC% | GEN% | 판정 |
|---|---|---|---|---|---|---|
| ELEC_LIVE | 1 | 7.0 | 7.0 | 42.9 | 28.6 | PASS |
| WATER_MANHOLE | 4 | 6.5 | 3.0 | 66.7 | 70.8 | PASS |
| TEMP_SCAFF | 3 | 7.7 | 3.3 | 60.0 | 61.1 | PASS |
| LIFT_RIGGING | 3 | 7.3 | 3.3 | 70.0 | 61.1 | PASS |
| ELEC_PANEL | 1 | 7.0 | 7.0 | 42.9 | 28.6 | WARN (고신뢰 1건) |
| WELD_ARC | 3 | 6.3 | 4.7 | 35.7 | 56.2 | WARN (고신뢰 1건) |

### 주요 샘플 row

**ELEC_LIVE / ELEC hazard**
- controls: LOTO 작업허가, 절연장갑, 접지 (공학적+PPE)
- laws: 산안기준규칙(95), 전기설비기술기준(93), 전기설비기술기준 판단기준(88)
- 판정: PASS — 전기설비 특화 law 2건 추가됨

**WATER_MANHOLE / ASPHYX hazard**
- controls: 가스측정, 환기, 감시인 배치 (공학적+관리적)
- laws: 산안기준규칙(95), 밀폐공간 해석례 327987(82), 산안법(65)
- 판정: PASS — 밀폐공간 특화 해석례 추가됨

**LIFT_RIGGING / DROP hazard**
- controls: 낙하방지망, 출입금지 구역, 과부하 방지 (공학적)
- laws: 산안기준규칙(92), 줄걸이자 해석례 343045(85), 산안법(65)
- 판정: PASS — 줄걸이 특화 해석례 추가됨

---

## generic-law 감소 결과

| 지표 | 튜닝 전 | 튜닝 후 |
|---|---|---|
| worktype map 총 아이템 | 272건 | 272건 (점수 조정) |
| needs_review 표시 | 0건 | 65건 |
| hazard map generic% (ELEC) | 60% | 29% |
| hazard map control-specific law | 없음 | ELEC 7건, ASPHYX/DROP/COLLIDE 각 7/5/6건 |

---

## 남은 한계

1. **FIRE/EXPLO hazard**: 산안기준규칙 외 특화 법령 없음 (화재안전기술기준은 소방청 소관 — 산업안전과 구분)
2. **COLLAPSE hazard**: 고신뢰 law 1건 (산안기준규칙만), 붕괴 특화 해석례 부족
3. **DUST hazard**: 산업보건 분진 관련 법령 수집 필요
4. **EXPLO hazard for WATER_MANHOLE**: 화학물질 폭발 관련 특화 law 없음
5. **Generic law % 50-70%**: 특화 해석례 수가 부족해 비율 개선 한계
6. **control text 품질**: controls_normalized.json 기반이라 제어 이름이 긴 형태

---

## 다음 단계 운영 연결 전 체크포인트

- [ ] 실제 API 키(DATA_GO_KR_SERVICE_KEY) 설정 후 법령 재수집 → 실제 법령 본문 포함
- [ ] 산업안전보건기준에 관한 규칙 조문별 매핑 (제43조 추락, 제153조 인양, 제619조 밀폐공간 등)
- [ ] law_evidence 필드가 draft API 응답에 실제 반영되는지 엔드-투-엔드 확인
- [ ] FIRE/EXPLO/COLLAPSE 특화 seed 추가
- [ ] review_status=needs_review 항목 사람이 직접 검토

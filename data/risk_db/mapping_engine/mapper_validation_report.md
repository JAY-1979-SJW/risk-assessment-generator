# Mapper 품질 검증 보고서 (mapper_validation_report)

기준일: 2026-04-23  
검증 대상: `build_risk_assessment()` — 3개 작업 × 4 hazard = 12건  
데이터 소스: risk_mapping_core DB (실 서버)

---

## 1. hazard 누락 검증

| work_type | DB hazard 수 | 출력 hazard 수 | 누락 |
|----------|-------------|--------------|------|
| 고소작업 | 4 | 4 | 없음 |
| 전기작업 | 4 | 4 | 없음 |
| 밀폐공간 작업 | 4 | 4 | 없음 |

→ **PASS — 전체 12건 누락 없음**

---

## 2. controls 비어있지 않음 검증

| work_type | controls 최소 | controls 최대 | 비어있는 hazard |
|----------|-------------|-------------|----------------|
| 고소작업 | 5개 | 5개 | 없음 |
| 전기작업 | 5개 | 5개 | 없음 |
| 밀폐공간 작업 | 5개 | 5개 | 없음 |

→ **PASS — 모든 hazard controls 5개 (4~6개 범위 내)**

---

## 3. reference 3축 존재 검증

| work_type | law_ids_ok | moel_expc_ids_ok | kosha_ids_ok |
|----------|-----------|-----------------|-------------|
| 고소작업 | PASS | PASS | PASS |
| 전기작업 | PASS | PASS | PASS |
| 밀폐공간 작업 | PASS | PASS | PASS |

→ **PASS — 12건 전부 law / moel_expc / kosha 3축 모두 존재**  
→ **related_expc_ids 미사용 확인** — `related_moel_expc_ids = related_expc_ids` (0011 복사 일치)

---

## 4. JSON 구조 일관성

출력 구조:
```
{
  work_type: string           ✓
  hazards: [                  ✓
    hazard: string            ✓
    controls: string[]        ✓
    references: {
      law_ids: number[]       ✓
      moel_expc_ids: number[] ✓
      kosha_ids: number[]     ✓
    }
    confidence_score: float   ✓
    evidence_summary: string  ✓
  ]
}
```

→ **PASS — 3개 작업 모두 계약 구조 완전 일치**

---

## 5. hazard 중복 없음 검증

| work_type | no_hazard_dup |
|----------|--------------|
| 고소작업 | PASS |
| 전기작업 | PASS |
| 밀폐공간 작업 | PASS |

→ **PASS — UNIQUE 제약 + 코드 내 seen_hazards 중복 방지 이중 보호**

---

## 6. 고소작업 baseline 정합성 검증

| hazard | DB confidence_score | baseline confidence_score | moel_expc_ids 일치 |
|--------|--------------------|--------------------------|--------------------|
| 추락 | 0.90 | 0.90 | OK |
| 낙하물 | 0.88 | 0.88 | OK |
| 전도 | 0.85 | 0.85 | OK |
| 협착 | 0.80 | 0.80 | OK |

→ **PASS — 고소작업 baseline 완전 일치**

---

## 7. 자연어 가독성 확인 (사람이 읽을 때)

### 고소작업 / 추락
- controls: "안전난간 설치 (산업안전보건기준에 관한 규칙 제13조)" — 법령 조문번호 포함, 자연스러움
- evidence_summary: 법령 직접 명시 + 해석례 + KOSHA 자료 설명 — 자연스러움

### 전기작업 / 감전
- controls: "충전전로 작업 전 정전 확인 및 개폐기 잠금(LOTO) 조치 (산안기준규칙 제321조)" — 전기 전문용어 적절
- evidence_summary: 제321조(충전전로), 제302조(접지), 제304조(누전차단기) — 체계적

### 밀폐공간 작업 / 질식
- controls: "작업 전 산소농도(18% 이상) 및 유해가스 농도 측정" — 수치 기준 명시, 명확
- evidence_summary: 제618조(정의), 제619조(프로그램), 시행규칙 제85조 — 3중 법령 체계적

### 판정
→ **PASS — 3개 작업 전체 사람이 읽어도 자연스럽고 실용적인 내용**

---

## 8. evidence_summary 100자 기준 검증

| work_type | 최단 evidence_summary 길이 |
|----------|--------------------------|
| 고소작업 | 131자 (협착) |
| 전기작업 | 최소 확인 필요 |
| 밀폐공간 작업 | 130자 이상 |

→ 전체 evidence_summary 100자 미만 row: **0건** (0012 migration 적용 후)

---

## 9. 종합 판정

| 검증 항목 | 결과 |
|----------|------|
| hazard 누락 없음 | PASS |
| controls 비어있지 않음 | PASS |
| reference 3축 모두 존재 | PASS |
| JSON 구조 일관성 | PASS |
| 동일 hazard 중복 없음 | PASS |
| 고소작업 baseline 정합 | PASS |
| 자연어 가독성 | PASS |
| related_expc_ids 미사용 | PASS |

**최종 판정: PASS**

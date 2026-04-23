# API 계약 일치 검증 보고서

## 테스트 환경
- 서버: localhost:8199 (로컬 FastAPI)
- DB: SSH 터널 → risk-assessment-db:5432 (컨테이너 직접 접속)
- 실행일: 2026-04-23

---

## 에러 응답 검증

| 케이스 | 기대 | 실제 | 결과 |
|--------|------|------|------|
| body 없음 | 400 MISSING_WORK_TYPE | 400 MISSING_WORK_TYPE | PASS |
| `{}` (work_type 누락) | 400 MISSING_WORK_TYPE | 400 MISSING_WORK_TYPE | PASS |
| `{"work_type": ""}` | 400 EMPTY_WORK_TYPE | 400 EMPTY_WORK_TYPE | PASS |
| `{"work_type": "도장작업"}` | 404 UNKNOWN_WORK_TYPE | 404 UNKNOWN_WORK_TYPE | PASS |

404 응답에 `supported_work_types` 포함 여부: PASS

---

## 정상 응답 검증

### 고소작업
- HTTP: 200 ✓
- hazards: 4개 (추락/낙하물/전도/협착)
- controls: 각 5개 ✓
- references 3축 (law_ids/moel_expc_ids/kosha_ids): ✓
- confidence_score: 0.90 / 0.88 / 0.85 / 0.80 ✓
- evidence_summary: 문자열 ✓
- related_expc_ids 미노출: ✓

### 전기작업
- HTTP: 200 ✓
- hazards: 4개 (감전/추락/아크·화재/협착)
- controls: 각 5개 ✓
- references 3축: ✓
- confidence_score: 0.88 / 0.82 / 0.80 / 0.80 ✓
- evidence_summary: ✓
- related_expc_ids 미노출: ✓

### 밀폐공간 작업
- HTTP: 200 ✓
- hazards: 4개 (질식/중독/화재·폭발/구조지연)
- controls: 각 5개 ✓
- references 3축: ✓
- confidence_score: 0.90 / 0.87 / 0.83 / 0.78 ✓
- evidence_summary: ✓
- related_expc_ids 미노출: ✓

---

## 종합 결과

**7/7 PASS**

| 항목 | 결과 |
|------|------|
| HTTP 400 에러 정책 | PASS |
| HTTP 404 에러 정책 | PASS |
| 정상 3개 작업 실데이터 | PASS |
| hazards 4개 출력 | PASS |
| controls 5개 유지 | PASS |
| references 3축 존재 | PASS |
| confidence_score 유지 | PASS |
| evidence_summary 유지 | PASS |
| legacy 필드(related_expc_ids) 미노출 | PASS |

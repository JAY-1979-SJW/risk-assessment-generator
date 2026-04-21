# 위험성평가표 프로그램 고도화 v1

**작성일**: 2026-04-20  
**적용 엔진**: RAG Risk Engine v2.0 (기존 v1.2 위에 ADDITIVE)  
**보호 기준선**: 기존 32개 테스트 전원 PASS 유지

---

## 1. 고도화 목표

기존 v1.2 KOSHA BM25 검색 품질을 유지하면서, risk_db 6축 데이터를
엔진에 우선순위대로 연결하여 다음을 달성한다:

- v2 조건 입력(structured flags)이 결과 품질 향상으로 직결
- 위험성평가표 결과의 근거/추적성 강화
- 이후 UI·AI 연동을 위한 구조적 기준선 확립

---

## 2. 연결된 DB 우선순위

| 순위 | DB | 연결 여부 | 품질 영향 | 난이도 |
|------|-----|-----------|-----------|--------|
| 1 | `scenario/condition_scenarios.json` | ✅ 연결 | hazard/action 직접 강화 (조건 조합) | 중 |
| 2 | `hazard_action/hazard_controls.json` | ✅ 연결 | recommended_actions 구체화 | 하 |
| 2 | `hazard_action/hazard_ppe.json` | ✅ 연결 | required_ppe 품질 향상 | 하 |
| 3 | `work_taxonomy/work_types.json` | ✅ 연결 | BM25 query expansion | 하 |
| 3 | `work_taxonomy/work_hazards_map.json` | ✅ 연결 | 예상 hazard 사전 반영 | 하 |
| 4 | `equipment/` | 미연결 | 장비 기반 보강 | 중 |
| 5 | `law_standard/` | 미연결 | 법령 근거 강화 | 중 |
| 6 | `real_cases/` | 미연결 | 유사사례 추천 | 상 |

---

## 3. 연결 규칙 (모두 ADDITIVE ONLY)

### 3-A. condition_scenarios 매칭

v2 입력 플래그 → 30개 시나리오 중 매칭 → controls/law_refs 추가

**지원되는 trigger_conditions 키:**

| 시나리오 키 | v2 입력 매핑 |
|------------|-------------|
| `work_at_height` | `work_at_height=True` OR `height_m > 2` |
| `night_work` | `night_work=True` |
| `confined_space` | `confined_space=True` |
| `hot_work` | `hot_work=True` |
| `electrical_work` | `electrical_work=True` |
| `heavy_equipment` | `heavy_equipment=True` |
| `simultaneous_work` | `simultaneous_work=True` |
| `wet_surface` | `surface_condition` in ('wet', 'slippery') |
| `weather_condition=wind_strong` | `weather` in ('wind', 'extreme') |
| `weather_condition=rain` | `weather` in ('rain', 'snow') |

**지원 불가 (v2 미제공):** `flammable_nearby`, `excavation`, `lifting_operation`, `asbestos_work`

**v2로 매칭 가능한 시나리오:** SC-001~003, SC-005~008, SC-010~012, SC-016~017 (12개)

### 3-B. hazard_controls 연결

KOSHA 검색 기반 hazard 분류 → hazard code 변환 → hazard_controls 조회 → 우선순위=1 조건 우선 추가

**Korean label → hazard_code 매핑:**
```
추락→FALL, 감전→ELEC, 질식→ASPHYX, 화재→FIRE, 폭발→EXPLO
낙하→DROP, 충돌→COLLIDE, 붕괴→COLLAPSE, 협착→ENTRAP
절단→CUT, 중독→POISON, 분진→DUST, 소음→NOISE
```

**우선순위:** KOSHA 검색 결과 > 시나리오 controls > DB controls (strict additive)

### 3-C. hazard_ppe 연결

감지된 hazard codes → hazard_ppe 조회 → mandatory PPE 우선 추가 (기존 미포함 항목만)

### 3-D. work_taxonomy query expansion

`sub_work` 텍스트 → work_types.json name_ko 매칭 → work_hazards_map 조회 → Korean 키워드 클러스터 BM25 쿼리에 추가 (max 3개)

---

## 4. 입력 보강 규칙 (v2 fields → hazard/action boost)

| v2 필드 | 쿼리 토큰 추가 | 조건 경고 | 비고 |
|---------|---------------|-----------|------|
| `work_at_height=True` OR `height_m>2` | 고소작업 추락 안전대 안전난간 | 관련 시나리오 매칭 시 | — |
| `height_m > 10` | — | [입력 경고] 고소 {N}m: 강풍 기준 수립 필요 | 추가 경고 |
| `confined_space=True` | 밀폐공간 질식 산소결핍 환기 | 관련 시나리오 매칭 시 | — |
| `hot_work=True` | 화기작업 화재 폭발 불꽃 | 관련 시나리오 매칭 시 | — |
| `electrical_work=True` | 전기작업 감전 활선 절연 | 관련 시나리오 매칭 시 | — |
| `heavy_equipment=True` | 중장비 충돌 낙하 신호수 | 관련 시나리오 매칭 시 | — |
| `night_work=True` | 야간작업 조명 시야 | 관련 시나리오 매칭 시 | — |
| `simultaneous_work=True` | 동시작업 협착 충돌 신호수 | 관련 시나리오 매칭 시 | — |
| `surface_condition=wet/slippery` | 미끄럼 안전화 바닥 | SC-006 매칭 시 | — |
| `surface_condition=uneven` | — | [입력 경고] 고르지 않은 바닥 | 추가 경고 |
| `weather=rain/snow` | 우천 결빙 미끄럼 | SC-002 매칭 시 | snow→rain 취급 |
| `weather=wind/extreme` | 강풍 악천후 작업중지 | SC-001 매칭 시 | — |
| `weather=snow` | — | [입력 경고] 적설 환경 | 추가 경고 |
| `weather=extreme` | — | [입력 경고] 극한 기상 | 추가 경고 |
| `worker_count >= 10` | — | [입력 경고] 다수 작업자 N명 | 추가 경고 |

---

## 5. 결과 구조 고도화

### 신규 출력 필드

| 필드 | 타입 | 내용 |
|------|------|------|
| `evidence_sources` | `Dict[str, List[str]]` | 출처 분리 추적 |
| `boosted_by_conditions` | `List[str]` | 매칭된 scenario ID 목록 (예: ['SC-001', 'SC-007']) |
| `boosted_by_taxonomy` | `List[str]` | 적용된 work_type code 목록 (예: ['TEMP_SCAFF']) |
| `source_db_refs` | `List[str]` | 참조된 risk_db 레코드 IDs 전체 |

### evidence_sources 구조

```json
{
  "retrieval_actions": ["...", "..."],   // KOSHA BM25 검색 결과
  "scenario_actions":  ["...", "..."],   // condition_scenarios 기반
  "db_actions":        ["...", "..."],   // hazard_controls 기반
  "retrieval_ppe":     ["...", "..."],   // KOSHA BM25 검색 결과
  "db_ppe":            ["...", "..."],   // hazard_ppe 기반
  "retrieval_legal":   ["...", "..."],   // KOSHA BM25 검색 결과
  "db_legal":          ["...", "..."]    // 시나리오 + hazard_controls law_refs
}
```

### 출력 용량 제한

| 필드 | v1.2 기준 | v2 기준 |
|------|-----------|---------|
| `recommended_actions` | 최대 8개 | 최대 10개 (risk_db boost 포함) |
| `required_ppe` | 최대 6개 | 최대 8개 (risk_db boost 포함) |
| `legal_basis_candidates` | 최대 5개 | 최대 6개 (risk_db boost 포함) |
| `warnings` | 가변 | 가변 (조건/입력 경고 추가) |

---

## 6. 저장 구조 영향

### 현재 구조 (migration 001)

```sql
assessment_engine_results (
  engine_version      VARCHAR(20) DEFAULT 'v1.1',
  input_snapshot      JSONB,
  output_json         JSONB,
  source_chunk_ids    INTEGER[],
  confidence          VARCHAR(10),
  warnings            TEXT[]
)
```

### 제안 추가 (migration 004 — additive only)

```sql
-- engine_version 기본값: 'v2.0'으로 변경
-- 신규 nullable 컬럼 추가:
risk_db_ref_ids    TEXT[]  DEFAULT '{}'
boosted_conditions TEXT[]  DEFAULT '{}'
boosted_taxonomy   TEXT[]  DEFAULT '{}'
evidence_sources   JSONB
```

**마이그레이션 위험도**: 낮음 (모두 nullable, 기존 행 영향 없음)  
**파일**: `engine/kras_connector/migrations/004_engine_upgrade_v2.sql`

---

## 7. 품질 검증 결과

### 기존 테스트 (32개)

**결과: 32/32 PASS** (v1.2 기준선 유지)

### v2 조건 입력 케이스 (8개 신규)

| 케이스 | 매칭 시나리오 | actions | ppe | legal | 판정 |
|--------|-------------|---------|-----|-------|------|
| 밀폐+화기 | SC-008 | 10 | 8 | 6 | PASS |
| 중장비+동시작업 | SC-005 | 10 | 8 | 6 | PASS |
| 전기+습윤 | SC-006 | 10 | 8 | 6 | PASS |
| 야간+동시작업 | SC-010 | 10 | 8 | 6 | PASS |
| 고소+동시(수직) | SC-011 | 10 | 8 | 6 | PASS |
| 표면불규칙+눈 | SC-002 | 10 | 7 | 6 | PASS |
| 고높이 경고(25m) | (없음) | 10 | 8 | 6 | PASS |
| 다수작업자+중장비 | SC-005 | 10 | 8 | 6 | PASS |

**종합 판정**: hazard 정확도 후퇴 없음 / FAIL 0 / action GOOD 비율 유지 또는 상승

---

## 8. 프로그램 관점 판정

| 관점 | 상태 | 비고 |
|------|------|------|
| 입력 품질 | ★★★★☆ | v2 flags 10종 완전 반영 |
| 결과 품질 | ★★★★☆ | scenario_controls 구체성 높음 |
| 근거 추적성 | ★★★★★ | evidence_sources + boosted_by_* 신설 |
| 저장/재조회 가능성 | ★★★☆☆ | migration 004 적용 후 ★★★★☆ |
| 향후 UI 연결 용이성 | ★★★★☆ | evidence_sources로 출처 구분 표시 가능 |
| 향후 AI 연동 준비도 | ★★★☆☆ | 구조화됨, embedding 단계는 후속 |

---

## 9. 남은 과제

### 단기 (고도화 2차)

- `equipment/equipment_hazards.json` 연결 → 장비 입력 기반 hazard 보강
- `law_standard/safety_laws.json` 연결 → OSHA-R-* 코드 → 실제 법령명 변환
- `condition_scenarios.json` trigger_conditions 확장 → `flammable_nearby` 등 v2 파생 추론 추가

### 중기 (고도화 3차)

- `real_cases/real_assessment_cases.json` 연결 → 유사 사례 기반 추천
- `work_taxonomy/work_sub_types.json` 연결 → sub_work 분류 정교화
- condition_scenarios 30 → 50+ 확장 (미지원 조건 추가)

### 장기 (AI/UI 단계)

- embedding 기반 semantic search (현재 BM25 보완)
- 위험성평가표 결과 UI 표시: evidence_sources 활용 출처 분리 표기
- assessment_engine_results 재조회 API에 boosted_conditions 필터 추가

---

## 10. 변경 파일 목록

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `engine/rag_risk_engine/risk_db_booster.py` | 신규 생성 | risk_db 연결 핵심 모듈 |
| `engine/rag_risk_engine/engine.py` | 수정 | booster 연결, 신규 출력 필드, query expansion |
| `engine/rag_risk_engine/schema.py` | 수정 | RagOutput에 v2 traceability 필드 추가 |
| `engine/kras_connector/migrations/004_engine_upgrade_v2.sql` | 신규 생성 | DB 추적성 컬럼 additive 추가 |

**보호 파일 (변경 없음):**
- `backend/routers/engine_results.py` — 미변경 ✅
- `docs/standards/risk-assessment-web-baseline-v1.md` — 미변경 ✅

# 매핑 엔진 Read 계약서 (engine_read_contract)

기준일: 2026-04-23  
대상 테이블: `risk_mapping_core`  
소비자: `engine/kras_connector/` — `service.py` → `mapper.py` → `run_engine()`

---

## 1. 조회 인터페이스

### 1-1. 기본 조회 쿼리 (work_type 입력 → hazard 목록)

```sql
SELECT
    id,
    work_type,
    hazard,
    related_law_ids,
    related_moel_expc_ids,
    related_kosha_ids,
    control_measures,
    confidence_score,
    evidence_summary
FROM risk_mapping_core
WHERE work_type = %(work_type)s
ORDER BY confidence_score DESC;
```

**입력**: `work_type` — `RagInput.sub_work` 또는 정규화된 work_type 값  
**출력**: 해당 작업의 hazard-control 매핑 전체 (0~4건)

### 1-2. 단일 hazard 조회 (work_type + hazard)

```sql
SELECT *
FROM risk_mapping_core
WHERE work_type = %(work_type)s
  AND hazard   = %(hazard)s;
```

---

## 2. 필드 매핑 규칙

| risk_mapping_core 컬럼 | 엔진 출력 필드 | 변환 방법 |
|------------------------|--------------|---------|
| `hazard` | `primary_hazards` | 리스트에 append |
| `control_measures->'measures'` | `recommended_actions` | JSON 배열 → 리스트 flatten |
| `related_law_ids` | `legal_basis_candidates` → `source_db_refs` | ID 배열 → law DB JOIN (조문 텍스트 fetch) |
| `related_moel_expc_ids` | `evidence_sources['db_moel_expc']` | ID 배열 → moel_expc DB JOIN |
| `related_kosha_ids` | `evidence_sources['db_kosha']` | ID 배열 → kosha DB JOIN |
| `confidence_score` | `confidence` | 0.85이상→high / 0.70~0.84→medium / 미만→low |
| `evidence_summary` | `reasoning_notes` | append |

---

## 3. control_measures 읽기 규칙

```python
# DB에서 읽을 때: JSONB 오브젝트 구조 주의
cm = row['control_measures']  # dict or str
if isinstance(cm, str):
    cm = json.loads(cm)

measures = cm.get('measures', [])   # 반드시 'measures' 키로 접근
source   = cm.get('source', '')     # 'law+kosha' / 'law' / 'kosha'
```

**주의**: `cm` 자체가 리스트가 아님 — `{"source": "...", "measures": [...]}` 구조

---

## 4. confidence_score → 엔진 confidence 변환

```python
def score_to_level(score: float) -> str:
    if score >= 0.85:
        return 'high'
    elif score >= 0.70:
        return 'medium'
    else:
        return 'low'
```

---

## 5. work_type 정규화 (RagInput.sub_work → DB 조회키)

`project_assessments.sub_work` 값은 자유 텍스트이므로 DB의 `work_type` 값과 정규화 필요.

| 정규화 방법 | 설명 |
|-----------|------|
| 완전 일치 | `sub_work == work_type` → 직접 조회 |
| 키워드 포함 | `'고소' in sub_work` → `'고소작업'` 매핑 |
| 미매핑 | 빈 결과 반환 → RAG 엔진 단독 실행 |

**지원 work_type 10종**:
고소작업, 굴착작업, 양중작업, 이동식비계 작업, 고소작업대 작업,  
밀폐공간 작업, 화기작업, 전기작업, 절단/천공 작업, 중장비 작업

---

## 6. 필드 사용 금지 목록

| 필드 | 사유 |
|------|------|
| `related_expc_ids` | Legacy 컬럼 — 신규 코드에서 읽기·쓰기 금지 (`compat_field_audit.md` 참조) |
| `work_type='고소작업'` 대상 UPDATE | `overwrite_guard_rule.md` 참조 — diff 리포트만 허용 |

---

## 7. 엔진 연결 전 사전 확인 쿼리

```sql
-- 전체 row 수 확인 (예상: 40)
SELECT COUNT(*) FROM risk_mapping_core;

-- work_type별 row 수
SELECT work_type, COUNT(*) as cnt
FROM risk_mapping_core
GROUP BY work_type
ORDER BY cnt DESC;

-- evidence_summary 100자 미만 row (0건 이어야 함 — 0012 migration 후)
SELECT work_type, hazard, LENGTH(evidence_summary) as len
FROM risk_mapping_core
WHERE LENGTH(evidence_summary) < 100;
```

---

## 8. 반환 payload 구조

`sample_engine_payload.json` 참조.

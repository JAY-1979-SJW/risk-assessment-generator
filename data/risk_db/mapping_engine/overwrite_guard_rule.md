# 고소작업 Overwrite 방지 규칙 (overwrite_guard_rule)

기준일: 2026-04-23

---

## 보호 대상

`risk_mapping_core` 테이블에서 `work_type = '고소작업'` 인 4개 row (id: 1~4).

이 row들은 `0009_risk_mapping_core.sql` 에서 최초 생성되고 검증된 PASS 기준 샘플이다.

---

## 위반 이력

| migration | 위반 내용 | 상태 |
|-----------|---------|------|
| `0010_risk_mapping_core_expand.sql` | `evidence_summary` 4건 UPDATE 실행 | 기록됨, 되돌릴 수 없음 |

---

## 보호 규칙

### 규칙 1: migration SQL 작성 시

신규 migration에서 `work_type='고소작업'` 을 대상으로 하는 UPDATE 금지.

```sql
-- 금지 패턴
UPDATE risk_mapping_core SET ... WHERE work_type='고소작업';

-- 허용 패턴 (diff 리포트만)
SELECT * FROM risk_mapping_core WHERE work_type='고소작업';
```

### 규칙 2: Python 코드 작성 시

```python
# 금지
if work_type == '고소작업':
    cursor.execute("UPDATE risk_mapping_core SET ... WHERE work_type=%s", (work_type,))

# 허용 (diff-only)
if work_type == '고소작업':
    # 비교만 수행, UPDATE 금지
    existing = cursor.execute("SELECT ... FROM risk_mapping_core WHERE work_type=%s", (work_type,))
    diff = compare(existing, new_data)
    write_diff_report(diff)
```

### 규칙 3: ON CONFLICT 처리

고소작업 row를 대상으로 ON CONFLICT DO UPDATE 사용 금지.  
신규 작업 insert 시 WHERE 절로 고소작업 제외:

```sql
-- 신규 insert 시 고소작업 row에 영향 없도록 보장
INSERT INTO risk_mapping_core (work_type, hazard, ...)
VALUES (...)
ON CONFLICT (work_type, hazard) DO NOTHING;  -- 고소작업은 DO NOTHING
```

---

## 사전 검증 쿼리 (migration 실행 전 필수 실행)

```sql
-- 고소작업 fingerprint 확인 (변경되지 않았는지 검증)
SELECT
  hazard,
  MD5(related_law_ids::text)         as law_hash,
  MD5(related_moel_expc_ids::text)   as expc_hash,
  MD5(related_kosha_ids::text)       as kosha_hash,
  MD5(control_measures::text)        as ctrl_hash,
  confidence_score
FROM risk_mapping_core
WHERE work_type = '고소작업'
ORDER BY id;
```

### 기준값 (baseline fingerprints)

| hazard | law_hash (MD5) | confidence_score |
|--------|---------------|-----------------|
| 추락 | MD5([16733, 16754, 16767]) | 0.90 |
| 낙하물 | MD5([16734, 16957, 16964]) | 0.88 |
| 전도 | MD5([16767, 16801, 16948]) | 0.85 |
| 협착 | MD5([17237, 15812, 22357]) | 0.80 |

---

## Diff 리포트 생성 규칙

변경이 필요한 경우 UPDATE 대신 diff_report 파일만 생성:

```json
{
  "work_type": "고소작업",
  "hazard": "추락",
  "field": "confidence_score",
  "current": 0.90,
  "proposed": 0.92,
  "reason": "추가 law 조문 2건 발견",
  "action": "PENDING_REVIEW — 수동 검토 필요"
}
```

---

## 자동화 가능 범위

- evidence_summary 100자 미만 WARN 보완: **별도 migration + diff 리포트 필수**
- confidence_score 변경: **불가 — 수동 검토 후 별도 결정**
- 참조 ID 추가: **불가 — 신규 보완 migration 필요**

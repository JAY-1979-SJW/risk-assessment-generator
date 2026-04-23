# 컬럼 호환성 감사 보고서 (compat_field_audit)

기준일: 2026-04-23

---

## 1. 현재 컬럼 상태

| 컬럼명 | 타입 | 상태 | 비고 |
|--------|------|------|------|
| `related_law_ids` | JSONB | 표준 (유지) | source_type='law' |
| `related_expc_ids` | JSONB | **Legacy** | 0009/0010에서 생성된 구 필드명 |
| `related_moel_expc_ids` | JSONB | **표준 (신규)** | 0011에서 추가, related_expc_ids 데이터 복사 완료 |
| `related_kosha_ids` | JSONB | 표준 (유지) | source_type='kosha' |
| `control_measures` | JSONB | 표준 (유지) | `{"source":..., "measures":[...]}` 구조 |
| `confidence_score` | NUMERIC | 표준 (유지) | |
| `evidence_summary` | TEXT | 표준 (유지) | |

### 두 필드의 관계
```
related_expc_ids  ←  legacy (0009~0010 생성, 향후 write 금지)
related_moel_expc_ids  ←  표준 (0011 이후 모든 write 대상)

현재 두 필드의 데이터는 100% 동일 (0011에서 복사 확인)
```

---

## 2. Legacy 참조 위치 요약

| 파일 | 참조 유형 | 처리 방침 |
|------|----------|---------|
| `0009_risk_mapping_core.sql` | 컬럼 생성 + INSERT | 완료된 migration — **수정 불가** (히스토리) |
| `0010_risk_mapping_core_expand.sql` | INSERT/UPDATE SET | 완료된 migration — **수정 불가** (히스토리) |
| `0011_risk_mapping_add_moel_expc_col.sql` | 복사 및 COPY 설명 | 완료된 migration — 하위 호환 주석으로만 존재 |

**결론**: legacy 참조는 전부 완료된 migration 히스토리 파일에만 존재.  
신규 Python 코드, API 코드, 설정 파일에는 `related_expc_ids` 참조 없음.

---

## 3. 표준화 결정 사항

| 구분 | 규칙 |
|------|------|
| **신규 INSERT** | `related_moel_expc_ids` 에만 write |
| **신규 SELECT** | `related_moel_expc_ids` 사용 |
| **legacy 필드 read** | 허용 (하위 호환), 단 새 코드에서는 사용 금지 |
| **legacy 필드 write** | **금지** (0012 migration 이후부터) |
| **legacy 필드 제거** | 향후 데이터 마이그레이션 안정화 후 DROP 예정 |

---

## 4. 향후 제거 절차 (참고용, 아직 실행 금지)

```sql
-- 제거 가능 조건: related_expc_ids = related_moel_expc_ids 100% 확인 후
ALTER TABLE risk_mapping_core DROP COLUMN related_expc_ids;
DROP INDEX idx_rmc_expc_ids;
```

**제거 전 확인 쿼리:**
```sql
SELECT COUNT(*) FROM risk_mapping_core
WHERE related_expc_ids != related_moel_expc_ids;
-- 결과 0이면 제거 가능
```

# 0012 Migration 서버 적용 전 사전 확인 (pre_deploy_check)

기준일: 2026-04-23  
대상 migration: `0012_fix_evidence_summary_min100.sql`

---

## 1. 서버 접속 경로

| 항목 | 값 |
|------|-----|
| 앱서버 | ubuntu@1.201.176.236 |
| DB 컨테이너 | risk-assessment-db |
| DB 사용자 | kras |
| DB 이름 | kras |
| migration 파일 경로 | /home/ubuntu/apps/risk-assessment-app/app/data/risk_db/schema/migrations/0012_fix_evidence_summary_min100.sql |

## 2. migration 파일 존재 확인

`git fetch origin && git checkout origin/master -- data/risk_db/schema/migrations/0012_fix_evidence_summary_min100.sql`  
→ **PASS** (2.4K, 2026-04-23 11:15)

## 3. 대상 row 식별 조건

```sql
WHERE work_type = '이동식비계 작업'
  AND hazard = '낙하물'
  AND work_type != '고소작업'  -- 이중 안전장치
```

## 4. 현재 evidence_summary 사전 확인

| 컬럼 | 현재 값 |
|------|--------|
| work_type | 이동식비계 작업 |
| hazard | 낙하물 |
| LENGTH(evidence_summary) | **99자** |
| evidence_summary | 산안기준규칙 제14조(낙하물에 의한 위험의 방지), 제42조, 제193조(낙하물에 의한 위험방지) 근거. moel_expc: 낙하물 위험방지 조치 해석례(25997) 직접 관련. |

## 5. WHERE 조건 dry-run 결과

```
update_target_count = 1  ← 정확히 1건
gosojakup_count = 4      ← 보호 baseline 유지
total_rows = 40          ← 정상
```

## 6. 판정

| 체크 항목 | 결과 |
|----------|------|
| migration 파일 존재 | PASS |
| 대상 row 식별 | PASS (1건) |
| 고소작업 비접촉 | PASS (WHERE work_type != '고소작업') |
| 총 row 수 정상 | PASS (40건) |
| evidence_summary 현재 99자 | 확인 — 보정 필요 |

**사전 확인 판정: PASS → 2단계 적용 진행**

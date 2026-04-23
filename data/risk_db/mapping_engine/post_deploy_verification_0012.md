# 0012 Migration 서버 적용 후 검증 보고서 (post_deploy_verification)

기준일: 2026-04-23  
대상 migration: `0012_fix_evidence_summary_min100.sql`

---

## 1. 대상 row evidence_summary 길이 재조회

| 컬럼 | 적용 전 | 적용 후 |
|------|--------|--------|
| work_type | 이동식비계 작업 | 이동식비계 작업 |
| hazard | 낙하물 | 낙하물 |
| LENGTH(evidence_summary) | **99자** | **129자** |

→ 100자 이상 기준 **충족**

---

## 2. evidence_summary 변경 내용

**적용 전 (99자)**:
```
산안기준규칙 제14조(낙하물에 의한 위험의 방지), 제42조, 제193조(낙하물에 의한 위험방지) 근거. 
moel_expc: 낙하물 위험방지 조치 해석례(25997) 직접 관련.
```

**적용 후 (129자)**:
```
산안기준규칙 제14조(낙하물에 의한 위험의 방지), 제42조, 제193조(낙하물에 의한 위험방지) 근거. 
moel_expc: 낙하물 위험방지 조치 해석례(25997) 직접 관련. KOSHA OPL(1726) 낙하물 예방 조치 확인.
```

---

## 3. 참조 ID 변경 없음 확인

| 컬럼 | 값 | 변경 여부 |
|------|-----|---------|
| related_law_ids | [16734, 16767, 16957] | 변경 없음 |
| related_moel_expc_ids | [25997, 24497, 31953] | 변경 없음 |
| related_kosha_ids | [1726, 3057, 35368] | 변경 없음 |

---

## 4. control_measures 변경 없음 확인

```json
{"source": "law+kosha", "measures": [
  "비계 작업발판 자재·공구 결속 및 주머니 사용",
  "비계 하부 출입통제 구역 설정 및 경고 표지 (산안기준규칙 제14조)",
  "발끝막이판(토보드) 설치",
  "비계 위 불필요한 자재 적재 금지",
  "낙하물 방지망 설치 (제193조)"
]}
```
→ **변경 없음**

---

## 5. 전체 테이블 무결성 확인

| 체크 항목 | 적용 전 | 적용 후 | 결과 |
|----------|--------|--------|------|
| 총 row 수 | 40 | 40 | PASS |
| 고소작업 row 수 | 4 | 4 | PASS |
| evidence_summary 100자 미만 row | 1건 | **0건** | PASS |

---

## 6. migration 실행 로그 (NOTICE 요약)

```
BEGIN
NOTICE:  고소작업 row 건수 OK: 4
DO
UPDATE 1
NOTICE:  이동식비계/낙하물 evidence_summary 길이 OK: 129자
DO
NOTICE:  고소작업 [추락] evidence_summary 길이: 169자
NOTICE:  고소작업 [낙하물] evidence_summary 길이: 147자
NOTICE:  고소작업 [전도] evidence_summary 길이: 139자
NOTICE:  고소작업 [협착] evidence_summary 길이: 131자
DO
COMMIT
```

→ UPDATE 1건만 실행, 고소작업 row 비접촉, COMMIT 정상

---

## 7. 최종 판정

**PASS** — 모든 검증 기준 충족

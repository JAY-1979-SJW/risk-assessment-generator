# 매핑 엔진 연결 전 안정화 최종 판정 보고서

기준일: 2026-04-23  
대상: risk_mapping_core — 10 work_types × 40 rows  

---

## 7단계 체크리스트

| 단계 | 내용 | 상태 | 산출물 |
|------|------|------|--------|
| 1 | 재검증 (수치 일치) | PASS | — |
| 2 | 컬럼 호환성 감사 | PASS | `compat_field_audit.md`, `legacy_reference_list.txt` |
| 3 | 고소작업 보호 규칙 강제 | PASS | `protected_baseline_gosojakup.json`, `overwrite_guard_rule.md`, `diff_sample_report.json` |
| 4 | evidence_summary 최소 100자 보정 | PENDING_DEPLOY | `0012_fix_evidence_summary_min100.sql` — 서버 적용 대기 |
| 5 | 저신뢰 항목 검토 | PASS | `low_confidence_review.md` |
| 6 | 엔진 Read 계약 정의 | PASS | `engine_read_contract.md`, `sample_engine_payload.json` |

---

## 데이터 현황 요약

| 항목 | 수치 | 상태 |
|------|------|------|
| 총 row 수 | 40 | 정상 |
| work_type 종류 | 10 | 정상 |
| hazard 종류 (unique) | 22 | 정상 |
| confidence_score 0.80 이상 | 35건 | 정상 |
| confidence_score 0.75~0.79 | 5건 | ACCEPTABLE (법령 공백) |
| confidence_score 0.75 미만 | 0건 | 정상 |
| evidence_summary 100자 미만 | 1건 (이동식비계/낙하물) | 0012 migration 적용 후 해소 |

---

## 보호 규칙 준수 현황

| 규칙 | 상태 |
|------|------|
| 고소작업 4 row UPDATE 금지 (`overwrite_guard_rule.md`) | 문서화 완료, 위반 이력 1건 기록 (0010) |
| legacy `related_expc_ids` 신규 write 금지 (`compat_field_audit.md`) | 신규 코드 0건 확인 |
| `related_moel_expc_ids` 표준 사용 | 0011 이후 적용 |
| ON CONFLICT DO NOTHING (고소작업 보호) | 규칙 문서화 완료 |

---

## 최종 판정

```
엔진 연결 허용 조건:
  ✓ 40 rows 데이터 무결성 확인
  ✓ 컬럼 호환성 문서화 완료
  ✓ 보호 규칙 강제 완료
  ✓ 저신뢰 항목 사유 명확히 문서화
  ✓ engine_read_contract.md 계약 정의 완료
  ⚠ 0012 migration 서버 적용 후 evidence_summary 100자 미만 0건 달성 필요

최종 판정: CONDITIONAL PASS
  → 0012 migration 배포 완료 후 FULL PASS 전환
  → 엔진 연결 개발 병행 진행 허용
```

---

## 다음 단계 (엔진 연결)

1. **0012 migration 배포**: git push → 서버 `git pull --ff-only` → `docker exec psql`
2. **engine/kras_connector/mapper.py 수정**: `sub_work` → `work_type` 정규화 로직 추가
3. **risk_mapping_core 조회 함수 추가**: `engine_read_contract.md` § 1-1 쿼리 구현
4. **control_measures['measures'] 파싱**: `engine_read_contract.md` § 3 규칙 적용
5. **RAG 출력에 DB 매핑 결과 병합**: `primary_hazards`, `recommended_actions` 보강

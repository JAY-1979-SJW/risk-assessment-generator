# 작업일지: KOSHA 분류기 v2.0 세부 분류 추가

- **날짜**: 2026-04-19
- **작업자**: JAY-1979-SJW
- **커밋**: `00ef1c9`

---

## 작업명
KOSHA 공종 분류기 v2.0 — 업종별/공종별/세부 분류 항목 추가

## 목표
기존 v1.0에서 `equipment`, `location`, `ppe`, `law_ref` 필드가 모두 비어있는 문제 해결.
위험성평가표 자동생성에 필요한 장비·위치·보호구·법령 정보를 청크 단위로 추출.

## 수정 파일
- `scraper/kosha_classifier.py` — 분류기 핵심 로직 (신규 커밋으로 추가됨)

## 변경 이유

| 항목 | v1.0 상태 | 문제점 |
|------|-----------|--------|
| equipment | 0건 (항상 None) | 장비 추출 로직 없음 |
| location | 0건 (항상 None) | 위치 추출 로직 없음 |
| ppe | 2,215건 (청크 원문 복사) | "보호구" 같은 일반어만 저장 |
| law_ref | 3,655건 (청크 원문 복사) | "조" 같은 무의미한 값 |
| 미분류 청크 | 1,513건 | 태그 없음 |

## 시도 / 실패 내용

- `ON CONFLICT DO NOTHING` → 기존 v1.0 태그를 갱신하지 못함
  - 해결: DB에 `UNIQUE (chunk_id)` 제약 추가 후 `ON CONFLICT DO UPDATE` 방식으로 변경
- `rule_version='v1.0'` 레코드가 남아있어 `run_classify_all()`이 미분류 건만 처리
  - 해결: `run_reclassify_all()` 함수 신규 추가 (전체 대상)

## 최종 적용 내용

```
EQUIPMENT_KW  : 23종 장비 키워드 사전 (크레인/지게차/굴삭기 등)
LOCATION_KW   : 11종 위치 키워드 사전 (고소/지하/밀폐공간 등)
PPE_KW        : 12종 보호구 직접 추출 (안전모/안전대/보안경 등)
LAW_PATTERNS  : 10개 법령 regex (산업안전보건법/중대재해처벌법 등)
rule_version  : v1.0 → v2.0
run_reclassify_all() : 전체 재분류 (--reclassify 플래그)
```

## 검증 결과

```
전체 대상   : 7,142건
equipment   : 1,910건 (27%) — 지게차 482, 리프트 163, 타워크레인 122
location    : 3,383건 (47%) — 고소 1,092, 지하 1,026, 개구부 289
ppe         : 2,536건 (36%)
law_ref     : 1,149건 (16%)
소요 시간   : 10초
```

DB 확인:
```sql
SELECT rule_version, COUNT(*) FROM kosha_chunk_tags GROUP BY rule_version;
-- v2.0 | 7142
```

## 다음 단계
- 위험성평가표 자동생성 API 개발 (`/api/generate`)
- 업종+공종 조합으로 위험 요인/감소 조치 추천 로직
- `candidate_trades` 활용한 복합 공종 처리

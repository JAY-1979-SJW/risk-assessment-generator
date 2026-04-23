# collector 안정화 검증 결과

## 실행 환경

- 실행 일시: 2026-04-24
- 데이터: `data/risk_db/law_raw/laws_index.json` (89건) — 샘플 10건 사용
- 방식: 격리 스텁 (temp 파일 전용 출력, tracked 파일 무변경)
- API 키: 없음 — dry-run 방지를 위해 고정 fixture 사용

## 실행 대상

| 모듈 | 검증 항목 | 방식 |
|------|-----------|------|
| law_statutes.py | `_stable_law_sort_key()` + `save_json()` skip | temp 파일, 고정 fetched_at |
| law_content.py | `done_msts` 로드·dedup + JSONL append 방지 | temp JSONL, 동일 MST 재입력 |

## 1차 실행 결과

| 검증 | 내용 | 결과 |
|------|------|------|
| A1 | 입력 순서 달라도 정렬 순서 동일 (10건 shuffle) | PASS |
| A2 | 1차 save_json → written=True | PASS |
| A3 | 동일 데이터 재호출 → written=False (skip) | PASS |
| B1 | 5건 1차 처리: 처리=5, 중복skip=0 | PASS |
| B2 | 5건 2차 처리 (JSONL에서 done_msts 재로드): 처리=0, skip=7 | PASS |
| C | save_json write→skip→write 패턴 정확 | PASS |

## 2차 실행 결과 (flapping 검증)

| 검증 | 내용 | 결과 |
|------|------|------|
| A | 동일 데이터 2차 save_json → written=False | PASS |
| A | 파일 mtime 미변경 (1차 실행 시점 유지, 41.5초 경과) | PASS |
| B | JSONL 10줄 → 2차 실행 후 10줄 (신규 기록 0줄) | PASS |
| B | done_msts JSONL 재로드: 5건 로드, 재처리 0건 | PASS |

## git 상태

| 시점 | tracked 파일 변경 | 비고 |
|------|-------------------|------|
| 사전 | 0건 | working tree clean |
| 1차 실행 후 | 0건 | temp 파일만 기록됨 |
| 2차 실행 후 | 0건 | 동일 |

## skip/write 발생 패턴

```
1차 실행: save_json → written=True  (최초 기록)
2차 실행: save_json → written=False (동일 내용 → skip)
          JSONL append: 0줄         (done_msts가 전체 skip)
```

## 주의사항 (fetched_at 설계 한계)

- law_statutes.py의 실 수집 시 `fetched_at: now_iso()`로 매번 갱신됨
- `laws_index.json`이 git 추적 중이므로, 실제 수집 실행마다 timestamp로 인해 git diff 발생
- 이는 **items 순서 flapping이 아닌 timestamp 기록**으로 의도된 동작
- 순서 기반 flapping(수집 결과 재정렬로 인한 불필요 write)은 이번 안정화로 차단됨

## 최종 판정

**PASS**

- 동일 데이터 재실행 시 save_json write 0 확인
- items 순서 안정성 (shuffle 입력 → 동일 출력 순서) 확인
- done_msts JSONL 재로드 후 중복 처리 0건 확인
- git tracked 파일 변경 0 확인

# law_content.py 중복 방지 보강 검증 결과

## 검증 환경

- 방식: 인라인 Python fixture (대량 수집 없음, 임시 파일 사용)
- 실행 일시: 2026-04-24

## 케이스별 결과

| 케이스 | 설명 | 결과 |
|--------|------|------|
| 1 | 동일 법령(MST) 2회 입력 → 1회만 처리 | PASS |
| 2 | 기존 JSONL에서 done_msts 로드 → 기존 법령 skip, 신규 처리 | PASS |
| 3 | 입력 순서 달라도 처리 순서 동일 | PASS |
| 4 | 누락 필드/None/int 타입 포함 → 오류 없음 | PASS |
| 5 | save_json() 동일 내용 재호출 → skip (written=False) | PASS |

## 보강 내용 요약

- `done_ids` (doc_id 기준) → `done_msts` (raw_id=MST 기준) 전환
  - set 크기: 조문 수 × 법령 수 → 법령 수만
  - skip 조건: `law_{mst}_0000 in done_ids` → `mst in done_msts`
- `done_msts.add(mst)` API 호출 전 추가 → 동일 실행 내 재처리 방지
- `items = sorted(items, key=_stable_item_sort_key)` 추가 → 처리 순서 안정
- `_stable_item_sort_key()` — `(법령ID, 법령일련번호, 시행일자, 법령명한글)` 튜플, 전부 str 변환

# law_statutes.py 정렬 기준 검증 결과

## 검증 환경

- 방식: 인라인 Python fixture (대량 수집 없음)
- 실행 일시: 2026-04-24

## 케이스별 결과

| 케이스 | 설명 | 결과 |
|--------|------|------|
| 1 | 입력 순서가 다른 동일 데이터 → 출력 순서 동일 | PASS |
| 2 | 필드 누락 데이터 포함 (None, 빈 dict) → 오류 없음 | PASS |
| 3 | 숫자/문자 혼합값 포함 (int + str) → 오류 없음 | PASS |
| 4 | save_json() 동일 내용 재호출 → skip (written=False) | PASS |

## 검증 확인 사항

- `_stable_law_sort_key()`는 모든 값을 `str()` 변환하므로 int/str 혼합 TypeError 없음
- `.get(key) or ""` 패턴으로 None/누락 모두 `""` 처리
- fallback으로 `json.dumps(item, sort_keys=True)` 사용 — 완전 동일 레코드도 안정 정렬
- `save_json()`의 `sort_keys=True` canonical 비교와 충돌 없음
- 동일 내용 재호출 시 mtime 불변 확인

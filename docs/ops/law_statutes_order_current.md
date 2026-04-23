# law_statutes.py 현재 동작 분석

## 데이터 구조

- `all_items: list[dict]` — GW API + DRF API 수집 결과를 순서대로 extend
- `deduped: list[dict]` — 중복 제거 후 순서 그대로 유지 (insertion order)
- `output["items"] = deduped` — save_json() 에 전달

## dedup 처리 위치

`law_statutes.py:110-116`

```python
seen, deduped = set(), []
for item in all_items:
    key = _DEDUP_KEY(item)
    if not key or key in seen:
        continue
    seen.add(key)
    deduped.append(item)
```

`_DEDUP_KEY = lambda item: item.get("법령일련번호") or item.get("법령명한글") or item.get("법령명_한글")`

## save_json() 호출 위치

`law_statutes.py:132`

```python
save_json(OUT_PATH, output)
```

`save_json()`은 `sort_keys=True`로 dict 키를 정렬하지만, items 리스트 내 원소 순서는 정렬하지 않는다.

## 실제 필드명 (laws_index.json 확인)

| 필드명 | 예시 | 타입 |
|--------|------|------|
| 법령ID | "001766" | str |
| 법령일련번호 | "276853" | str |
| 시행일자 | "20251001" | str |
| 법령명한글 | "산업안전보건법" | str |
| 법령약칭명 | "" | str |
| _id | "1" | str |

모든 값이 문자열로 저장됨.

## 문제점

- API 응답 순서가 수집 실행마다 달라질 수 있음
- deduped 순서가 바뀌면 items 배열 순서가 바뀜
- save_json() 비교 시 내용이 달라 보여 불필요한 write 발생 (flapping)
- 현재 정렬 기준: 없음

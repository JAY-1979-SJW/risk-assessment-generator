# law_content.py 현재 동작 분석

## done_ids / 캐시 현황

`law_content.py:167-177`

```python
done_ids: set[str] = set()
if jsonl_path.exists():
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    done_ids.add(json.loads(line)["doc_id"])
                except Exception:
                    pass
```

- 기존 JSONL에서 **모든 `doc_id`** 를 로드
- `doc_id` 형식: `law_{mst}_{seq:04d}` (e.g. `law_276853_0000`, `law_276853_0001`, ...)
- 법령당 조문 수만큼 done_ids에 원소 추가됨 (비효율)

## skip 체크 위치

`law_content.py:189`

```python
if f"law_{mst}_0000" in done_ids:
```

- **첫 번째 조문(seq=0000)** 의 존재만 확인 — 법령 단위 skip
- 처리 후 `done_ids`에 신규 doc_id를 **추가하지 않음**

## 문제점

| 유형 | 내용 |
|------|------|
| 동일 실행 내 중복 | `items`에 같은 `법령일련번호`가 두 번 등장 시, 첫 처리 후 `done_ids` 미갱신 → 재처리 발생 |
| 정렬 없음 | `items` 순회 순서가 API 응답 순서 그대로 → 실행마다 처리 순서 다를 수 있음 |
| done_ids 부하 | 조문 수만큼 원소를 set에 유지 (법령당 수십~수백 개) |

## 파일명 생성 기준

- JSONL: `data/raw/law_content/law/YYYY-MM-DD/law_content.jsonl`
- meta:  `data/raw/law_content/law/YYYY-MM-DD/law_content_meta.json`
- `today_str()` (UTC 기준 날짜) 로 디렉토리 결정

## save_json() 호출 위치

`law_content.py:229`

```python
save_json(meta_path, summary)
```

- meta JSON 저장 시에만 사용
- JSONL은 `open(..., "a")` 직접 append

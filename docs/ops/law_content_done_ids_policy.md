# law_content.py 중복 방지 보강 정책

## 핵심 전환: done_ids → done_msts

| 항목 | 기존 | 변경 후 |
|------|------|---------|
| 키 타입 | `doc_id` (조문 단위) | `raw_id` = MST (법령 단위) |
| set 크기 | 조문 수 × 법령 수 | 법령 수만 |
| 읽는 필드 | `doc_id` | `raw_id` |
| skip 조건 | `law_{mst}_0000 in done_ids` | `mst in done_msts` |

## done_msts 구축

기존 JSONL에서 `raw_id` 필드(= MST)를 읽어 set 구성:

```python
done_msts: set[str] = set()
if jsonl_path.exists():
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    done_msts.add(json.loads(line)["raw_id"])
                except Exception:
                    pass
```

## 동일 실행 내 중복 방지

skip 체크 통과 직후, API 호출 **전** 에 추가:

```python
if mst in done_msts:
    ...  # skip
    continue

done_msts.add(mst)   # ← 이후 중복 방지 (API 호출 전)
result = drf_service_get(...)
```

- 실패한 법령도 same-run 재처리 없음 (의도적 — 재시도는 다음 실행에서)
- 성공한 법령도 즉시 marked — JSONL 재오픈 없이 처리

## 입력 정렬

`items` 순회 전 안정 정렬 적용:

```python
def _stable_item_sort_key(item: dict) -> tuple:
    return (
        str(item.get("법령ID") or ""),
        str(item.get("법령일련번호") or ""),
        str(item.get("시행일자") or ""),
        str(item.get("법령명한글") or ""),
    )

items = sorted(items, key=_stable_item_sort_key)
```

- None/누락/숫자 타입 모두 str() 변환으로 안전
- json.dumps fallback 생략 — `법령일련번호`(MST)가 고유 식별자이므로 충분

## save_json() 관계

- meta JSON: `save_json(meta_path, summary)` — 기존 그대로, 수정 없음
- JSONL: append 방식 유지, done_msts로 중복 append 방지

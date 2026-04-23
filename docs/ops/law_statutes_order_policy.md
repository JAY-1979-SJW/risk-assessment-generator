# law_statutes.py 정렬 기준 정책

## 정렬 우선순위

| 순위 | 키 | 실제 필드명 | 이유 |
|------|-----|-------------|------|
| 1 | 법령ID | `법령ID` | 법제처 고정 식별자, 변경 없음 |
| 2 | 법령일련번호 | `법령일련번호` | 개정마다 갱신되는 버전 구분자 |
| 3 | 시행일자 | `시행일자` | 날짜 문자열(YYYYMMDD), 문자 정렬 = 시간 정렬 |
| 4 | 법령명한글 | `법령명한글` | 사람이 읽을 수 있는 이름 |
| 5 | fallback | JSON dump | 위 4개 모두 동일한 드문 경우 대비 |

## 구현 예시

```python
def _stable_law_sort_key(item: dict) -> tuple:
    return (
        str(item.get("법령ID") or ""),
        str(item.get("법령일련번호") or ""),
        str(item.get("시행일자") or ""),
        str(item.get("법령명한글") or ""),
        json.dumps(item, ensure_ascii=False, sort_keys=True),
    )
```

## 안전성 요건

- `None` 또는 키 누락: `.get(key) or ""` → `str("")` 으로 처리
- 숫자/문자 혼합: 모두 `str()` 변환으로 TypeError 방지
- DRF 응답의 `법령명_한글`: run() 내에서 이미 `법령명한글`로 정규화됨 → 별도 처리 불필요

## 적용 위치

`law_statutes.py` — `run()` 함수 내 dedup 직후, `output` dict 생성 직전:

```python
deduped = sorted(deduped, key=_stable_law_sort_key)
```

## 비고

- `save_json()`의 `sort_keys=True`는 dict 키 정렬 담당 → 변경 없음
- items 배열 요소 순서는 `sorted()` 가 담당 → 역할 분리 명확

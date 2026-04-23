# save_json() 현재 동작 분석

분석 대상: `scripts/collect/_base.py` L44–46  
분석 일자: 2026-04-24

## 현재 코드

```python
def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
```

## 항목별 동작

| 항목 | 현재 값 | 문제 여부 |
|------|---------|----------|
| indent | 2 | 정상 |
| ensure_ascii | False (한글 유지) | 정상 |
| sort_keys | **미사용** | **문제** — dict key 삽입 순서에 의존, 동일 데이터라도 key 순서가 달라지면 다른 내용으로 직렬화 |
| 파일 끝 newline | **없음** | **문제** — `json.dumps` 결과에 trailing `\n` 없음, diff 도구 불일치 발생 |
| overwrite 조건 | **무조건 write** | **문제** — 동일 내용이어도 항상 파일 씀, mtime 계속 변경 → write flapping 원인 |
| parent mkdir | `parents=True, exist_ok=True` | 정상 |
| encoding | `utf-8` | 정상 |
| 반환값 | `None` | 중립 (변경 여부 알 수 없음) |

## 핵심 flapping 원인

1. **sort_keys 없음**: 수집기가 dict를 구성하는 순서가 run마다 다를 수 있음 → 내용은 동일하지만 직렬화 결과가 달라져 overwrite 발생
2. **동일 내용 무조건 write**: 변경 없어도 항상 파일을 씀 → mtime이 매 실행마다 갱신 → 상위 프로세스(감시, sync, git)가 변경으로 오탐

## 수정 방향

- `sort_keys=True` 추가로 canonical JSON 보장
- 파일 끝 `\n` 보장
- 기존 파일과 바이트 비교 후 동일하면 write skip
- 반환값을 `bool` 또는 `str("written"/"skipped")`로 변경하여 호출부에서 확인 가능하게

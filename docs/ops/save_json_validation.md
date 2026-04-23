# save_json() 단위 검증 결과

검증 일자: 2026-04-24  
검증 스크립트: `scripts/collect/_test_save_json.py`

## 검증 케이스 결과

| 케이스 | 내용 | 기대 결과 | 실제 결과 | 판정 |
|--------|------|----------|---------|------|
| 1 | 새 파일 저장 | True(write) 반환 + 파일 생성 | True, 파일 생성 | PASS |
| 부가 | 파일 끝 `\n` 보장 | 마지막 문자 `\n` | `\n` 확인 | PASS |
| 부가 | sort_keys 적용 | `"a"` < `"b"` 순서 | 순서 정렬 확인 | PASS |
| 2 | 동일 데이터 재저장 | False(skip) + mtime 불변 | False, mtime 동일 | PASS |
| 3 | key 순서만 다른 동일 dict | False(skip) + mtime 불변 | False, mtime 동일 | PASS |
| 4 | 실제 값 1개 변경 후 저장 | True(write) + mtime 변경 | True, mtime 변경 | PASS |

## 최종 판정: PASS (6/6)

## 실행 명령

```bash
python scripts/collect/_test_save_json.py
```

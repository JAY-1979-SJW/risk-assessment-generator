# save_json() 영향 범위 확인

확인 일자: 2026-04-24

## 호출부 목록 (수집기)

| 파일 | 호출 위치 | 호환성 |
|------|----------|--------|
| `collect/law_statutes.py` | L132 — 목록 인덱스 저장 | 호환 (반환값 미사용) |
| `collect/law_content.py` | L229 — 본문 메타 저장 | 호환 (반환값 미사용) |
| `collect/law_admin_rules.py` | L140 — 행정규칙 목록 저장 | 호환 (반환값 미사용) |
| `collect/law_expc.py` | L108 — 해석례 목록 저장 | 호환 (반환값 미사용) |
| `collect/law_licbyl.py` | L70 — 인허가 목록 저장 | 호환 (반환값 미사용) |
| `collect/law_moel_expc.py` | L125 — 고용부 해석례 저장 | 호환 (반환값 미사용) |
| `collect/admrul_content.py` | L196 — 행정규칙 본문 메타 | 호환 (반환값 미사용) |
| `collect/expc_content.py` | L178 — 해석례 본문 메타 | 호환 (반환값 미사용) |
| `collect/kosha_guides.py` | L318 — KOSHA 안전보건 가이드 저장 | 호환 (반환값 미사용) |
| `collect/_base.py` | L88 — `save_raw_dated()` 내부 | 호환 (반환값 미사용, path 반환) |

## 반환값 사용 여부

- 기존 반환값: `None` (falsy)
- 변경 후 반환값: `bool` (`True`=written, `False`=skipped)
- 모든 호출부에서 반환값 미사용 → 호환성 문제 없음
- `normalize/normalize_moel_expc.py`의 `_save_json()`은 별도 독립 함수 → 영향 없음

## 호환성 판정: 전체 호환

호출부 수정 불필요. 기존 시그니처(`path, data`) 유지.

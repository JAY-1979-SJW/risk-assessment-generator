# fetched_at 패치 검증 결과

검증일: 2026-04-24

## 검증 케이스 및 결과

| # | 케이스 | 결과 |
|---|--------|------|
| 1 | `today_str()` 형식이 YYYY-MM-DD인지 | PASS |
| 2 | `today_str()` 같은 날 2회 호출 시 동일값인지 | PASS |
| 3 | `now_iso()` vs `today_str()` 값이 다른지 (초단위 vs 날짜) | PASS |
| 4 | `save_json()` 동일 내용 재저장 시 mtime 불변(skip)인지 | PASS |
| 5 | pipeline output에 `fetched_at=YYYY-MM-DD` 포함, archive에 미포함 | PASS |
| 6 | 같은 날 2회 실행 시 pipeline.json / archive.json diff 없음 | PASS |
| 7 | `strftime("%Y-%m-%d")` 방식이 `today_str()`과 동일 결과인지 | PASS |
| 8 | `normalize_law_raw.py`: `fetched_at` 누락 시 `collected_at=""` fallback | PASS |
| 9 | `normalize_law_raw.py`: `fetched_at=YYYY-MM-DD` 정상 읽기 | PASS |

## 잔존 now_iso() 위치 (수정 불필요 확인)

| 파일 | 위치 | 저장 경로 | gitignore | 판정 |
|------|------|----------|-----------|------|
| `collect/law_content.py:126,234` | `collected_at` | `data/raw/law_content/` | ✅ 제외됨 | 수정 불필요 |
| `collect/_base.py:63` | `.status` 파일 `run_at` | `logs/` | ✅ 제외됨 | 수정 불필요 |
| `collect_laws_index.py:161` | `.status` 파일 `run_at` | `logs/` | ✅ 제외됨 | 수정 불필요 |
| `collect_kosha_guides.py:168` | `.status` 파일 `run_at` | `logs/` | ✅ 제외됨 | 수정 불필요 |

## 최종 판정: PASS

- 같은 날 반복 실행 시 `fetched_at` 때문에 dirty 발생하지 않음 ✅
- 날짜 아카이브 인덱스(`data/raw/law_api/{date}/*.json`)에 `fetched_at` 없음 ✅
- 파이프라인 인덱스(`data/risk_db/law_raw/*.json`)에 날짜 단위 `fetched_at`만 사용 ✅
- `normalize_law_raw.py` `fetched_at` 누락 시 `""` fallback으로 호환성 유지 ✅

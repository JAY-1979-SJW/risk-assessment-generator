# fetched_at 패치 계획

작성일: 2026-04-24

## 문제 원인

`fetched_at` 필드에 `now_iso()` / `datetime.now().isoformat()` (초 단위 ISO 타임스탬프)를 사용하여  
같은 날 반복 실행 시 Git 추적 메타 파일이 매번 dirty 상태가 됨.

## Git 추적 범위 (문제 파일)

| 경로 | gitignore 규칙 | 비고 |
|------|---------------|------|
| `data/raw/law_api/**/*_index.json` | `!data/raw/law_api/**/*_index.json` (예외 추적) | 날짜 아카이브 |
| `data/risk_db/law_raw/*.json` | 미제외 (추적) | 파이프라인 입력 |
| `data/risk_db/guide_raw/kosha_guides_index.json` | 미제외 (추적) | 파이프라인 입력 |

## 적용 정책

### A안 — data/raw/law_api/{date}/*.json (날짜 아카이브)
- `fetched_at` 필드 완전 제거
- 날짜 폴더명(`YYYY-MM-DD`)이 수집일을 이미 표현하므로 중복 불필요

### C안 — data/risk_db/law_raw/*.json, guide_raw/*.json (파이프라인)
- `fetched_at = today_str()` (YYYY-MM-DD) 로 고정
- 같은 날 반복 실행 시 값 불변 → diff 없음

## 수정 대상 파일

| 파일 | 현재 | 변경 | 영향 경로 |
|------|------|------|----------|
| `scripts/collect/law_statutes.py` | `now_iso()` | C안(pipeline) + A안(archive) | laws_index.json |
| `scripts/collect/law_admin_rules.py` | `now_iso()` | C안(pipeline) + A안(archive) | admin_rules_index.json |
| `scripts/collect/law_expc.py` | `now_iso()` | C안(pipeline) + A안(archive) | expc_index.json |
| `scripts/collect/law_licbyl.py` | `now_iso()` | C안(pipeline only) | licbyl_index.json |
| `scripts/collect/law_moel_expc.py` | `now_iso()` | C안(pipeline only) | moel_expc_index.json |
| `scripts/collect_laws_index.py` | `datetime.now().isoformat()` | C안(strftime) | laws_index.json(legacy) |
| `scripts/collect_kosha_guides.py` | `datetime.now().isoformat()` | C안(strftime) | kosha_guides_index.json |

## normalize 호환성

`scripts/normalize/normalize_law_raw.py:126`:
```python
"collected_at": file_meta.get("fetched_at", ""),
```
`fetched_at` 누락 시 빈 문자열 fallback — **이미 안전 처리됨. 추가 수정 불필요.**

## 수정 방법 요약

- `_base.py` 기반 파일 (`law_statutes`, `law_admin_rules`, `law_expc`):
  - import에 `today_str` 추가
  - `output["fetched_at"] = today_str()` (C안)
  - `save_raw_dated(...)` 호출 시 `{k:v for k,v in output.items() if k != "fetched_at"}` (A안)
- `_base.py` 기반 파일 (`law_licbyl`, `law_moel_expc`):
  - `now_iso()` → `today_str()` (import도 교체)
- 독립 스크립트 (`collect_laws_index`, `collect_kosha_guides`):
  - `datetime.now(timezone.utc).isoformat()` → `datetime.now(timezone.utc).strftime("%Y-%m-%d")`
  - 3개소 각각 수정 (per-item, error-case, output-header)

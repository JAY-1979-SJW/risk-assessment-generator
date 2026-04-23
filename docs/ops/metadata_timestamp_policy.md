---
title: 메타데이터 타임스탬프 정책 비교
date: 2026-04-24
status: DRAFT — 코드 수정 미수행
---

# 메타데이터 타임스탬프 정책 비교

## 1. 현황 요약

`fetched_at: now_iso()` 가 Git-tracked 인덱스 파일에 포함되어  
매 수집 실행마다 git dirty 상태가 발생한다.  
`save_json()` skip 로직은 이 타임스탬프로 인해 항상 무력화된다.

---

## 2. 정책 비교

### A안 — Git 추적 메타에서 fetched_at 제거

**방식**: Git-tracked 인덱스 JSON의 최상단 `fetched_at` 필드를 삭제.  
수집 완료 시각은 `logs/*.status` 파일(이미 존재)에만 기록.

**영향 스크립트**:
- `law_statutes.py`, `law_admin_rules.py`, `law_expc.py`, `law_licbyl.py`, `law_moel_expc.py` — output dict에서 `fetched_at` 삭제
- `collect_laws_index.py`, `collect_kosha_guides.py` — 동일
- `normalize_law_raw.py` — `file_meta.get("fetched_at", "")` 대체 필요 (폴더 날짜 파싱 또는 `""`로 고정)

**장점**:
- `save_json()` skip 완전 복구 → zero dirty (내용이 동일하면 write 없음)
- 정보 손실 없음 — 수집 시각은 `.status` 로그에 보존

**단점**:
- `normalize_law_raw.py` 의 `collected_at` 소스를 바꿔야 함 (폴더 날짜 또는 파일 mtime)
- 수정 스크립트 수: 8개

**적합 대상**: 파이프라인 인덱스 6개 (`data/risk_db/law_raw/`, `guide_raw/`)

---

### B안 — laws_index.json 등을 Git 추적에서 제외

**방식**: `.gitignore` 에서 `!data/raw/law_api/**/*_index.json` 을 삭제하거나  
`data/risk_db/law_raw/` 를 통째로 제외. `git rm --cached` 로 untrack.

**영향**:
- git 이력에서 법령 데이터 변경 추적 불가
- `.gitignore` 수정 + `git rm --cached` 9개 파일

**장점**:
- 코드 변경 없음, 즉시 효과

**단점**:
- 법령 데이터가 언제 갱신됐는지 git 이력으로 추적 불가
- 현재 추적 정책(`!data/raw/law_api/**/*_index.json`)을 역행
- 날짜 아카이브(`data/raw/law_api/{date}/`)는 원래 추적이 목적이었음

**적합 대상**: 없음 — 정보 손실 대비 이익 불균형

---

### C안 — fetched_at 값을 수집일 단위로 고정 (YYYY-MM-DD)

**방식**: `now_iso()` → `today_str()` 로 교체.  
같은 날 재실행 시 `fetched_at` 값이 동일 → `save_json()` skip 작동.

**영향 스크립트**:
- `_base.py` 의 `now_iso()` 를 직접 바꾸면 안 됨 (다른 용도 존재)
- 각 스크립트의 output dict 에서 `fetched_at: now_iso()` → `fetched_at: today_str()` 로 교체 (6–7곳)

**장점**:
- 최소 수정으로 same-day 재실행 dirty 제거
- `normalize_law_raw.py` 변경 불필요 — `collected_at` 이 날짜 정밀도로 기록 (충분)
- 날짜 아카이브의 날짜-폴더와 `fetched_at` 날짜 일치 → 의미 명확

**단점**:
- 새로운 날(첫 실행)에는 여전히 dirty 발생 — 그러나 이는 **정상적인 데이터 갱신**이므로 허용 가능
- `now_iso()` 와 `today_str()` 를 혼용하는 패턴이 생김

**적합 대상**: 파이프라인 인덱스 6개 + 날짜 아카이브 3개

---

## 3. 권장안

**C안 채택 (파이프라인 인덱스) + A안 원칙 병행**

| 파일 그룹 | 권장 | 이유 |
|---|---|---|
| `data/risk_db/law_raw/*.json` (6개) | C안: `fetched_at: today_str()` | 내용 변경 없으면 same-day skip |
| `data/risk_db/guide_raw/kosha_guides_index.json` | C안 동일 | 동일 이유 |
| `data/raw/law_api/{date}/*.json` (3개) | A안: `fetched_at` 삭제 | 날짜가 폴더에 이미 기록됨 — 이중 불필요 |

**기대 효과**:
- 수집 내용이 동일한 한 git dirty 없음
- 새 데이터 수집 시 (법령 갱신 등) 정상적으로 변경 감지
- `normalize_law_raw.py` 수정 범위 최소화

---

## 4. 수정 대상 목록 (코드 미수정 — 참고용)

```
scripts/collect/law_statutes.py        line 136: fetched_at: now_iso()
scripts/collect/law_admin_rules.py     line 131: fetched_at: now_iso()
scripts/collect/law_expc.py            line  99: fetched_at: now_iso()
scripts/collect/law_licbyl.py          line  74: fetched_at: now_iso()
scripts/collect/law_moel_expc.py       line 126: fetched_at: now_iso()
scripts/collect_laws_index.py          line  90,141,147: datetime.now(...).isoformat()
scripts/collect_kosha_guides.py        line 104,148,154: datetime.now(...).isoformat()
```

`data/raw/law_api/` 날짜 아카이브는 `save_raw_dated()` 경유 저장이므로  
`law_statutes.py` 등 각 스크립트의 output dict 수정으로 함께 해결됨.

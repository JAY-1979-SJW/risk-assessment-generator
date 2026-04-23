---
title: fetched_at dirty 원인 분석
date: 2026-04-24
status: DONE
---

# fetched_at 더티 발생 원인 분석

## 1. 문제 정의

수집 스크립트를 실행할 때마다 Git-tracked 인덱스 파일이 변경되어
`git status` 가 항상 dirty 상태를 보인다.  
`save_json()` 의 내용 비교(skip-unchanged) 로직이 있음에도 효과 없음.

**근본 원인**: `fetched_at: now_iso()` — 초 단위 UTC 타임스탬프가  
매 실행마다 달라지므로 내용 비교가 항상 "변경됨"으로 판정된다.

---

## 2. fetched_at 생성 위치 (스크립트)

| 스크립트 | 생성 위치 | 표현식 |
|---|---|---|
| `scripts/collect/law_statutes.py` | 상단 메타 + 항목별 에러 | `now_iso()` |
| `scripts/collect/law_admin_rules.py` | 상단 메타 | `now_iso()` |
| `scripts/collect/law_expc.py` | 상단 메타 | `now_iso()` |
| `scripts/collect/law_licbyl.py` | 상단 메타 | `now_iso()` |
| `scripts/collect/law_moel_expc.py` | 상단 메타 | `now_iso()` |
| `scripts/collect_laws_index.py` | 상단 메타 + 항목별 | `datetime.now(timezone.utc).isoformat()` |
| `scripts/collect_kosha_guides.py` | 상단 메타 + 항목별 | `datetime.now(timezone.utc).isoformat()` |
| `scripts/collect/kosha_forms_scraper.py` | 인덱스 파일 | `time.strftime("%Y-%m-%d %H:%M:%S")` |
| `scripts/collect/moel_forms_scraper.py` | 인덱스 파일 | `time.strftime("%Y-%m-%d %H:%M:%S")` |

모두 실행 시각을 초 단위 이상으로 기록 → 동일 실행으로 간주 불가능.

---

## 3. fetched_at 소비 위치 (읽기)

| 파일 | 용도 |
|---|---|
| `scripts/normalize/normalize_law_raw.py:126` | `file_meta.get("fetched_at", "")` → `collected_at` 필드로 변환 |

**앱/API 레이어에서는 fetched_at을 전혀 사용하지 않는다.**  
검증 로직, 비즈니스 로직에도 사용 없음.

`collected_at` 은 정규화된 레코드의 출처 메타로만 기록되며,  
시각 정밀도(초 단위)가 반드시 필요한 요건이 없다.

---

## 4. Git 추적 대상 파일 (fetched_at 포함, 9개)

### 4-1. 날짜별 아카이브 (data/raw/law_api/)
```
data/raw/law_api/law/2026-04-21/laws_index.json
data/raw/law_api/admrul/2026-04-21/admin_rules_index.json
data/raw/law_api/expc/2026-04-21/expc_index.json
```
- `.gitignore` 에 `!data/raw/law_api/**/*_index.json` 으로 force-include
- 폴더 자체가 날짜(`2026-04-21/`)를 인코딩 → `fetched_at` 이중 기록
- 같은 날 재실행 시 파일 덮어쓰기 + `fetched_at` 변경 → dirty

### 4-2. 파이프라인 현행 인덱스 (data/risk_db/law_raw/, guide_raw/)
```
data/risk_db/law_raw/laws_index.json
data/risk_db/law_raw/admin_rules_index.json
data/risk_db/law_raw/expc_index.json
data/risk_db/law_raw/licbyl_index.json
data/risk_db/law_raw/moel_expc_index.json
data/risk_db/guide_raw/kosha_guides_index.json
```
- 수집 실행 시마다 갱신되는 "현행" 파일
- `save_json()` skip 로직이 있으나 `fetched_at` 때문에 항상 통과

---

## 5. save_json() 스킵 로직이 무력화되는 이유

```python
# scripts/collect/_base.py:44
def save_json(path: Path, data: dict) -> bool:
    canonical = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") == canonical:
            return False   # ← 이 분기에 진입하려면 내용이 동일해야 함
    path.write_text(canonical, encoding="utf-8")
    return True
```

`fetched_at` 값이 `"2026-04-24T03:12:45.123456+00:00"` 처럼 매 실행마다 달라지므로
canonical 문자열이 항상 달라 → 비교 실패 → 매번 write → git dirty.

---

## 6. 영향 파일 요약

| 분류 | 파일 수 | dirty 발생 빈도 |
|---|---|---|
| 날짜 아카이브 (raw/) | 3 | 같은 날 재실행 시마다 |
| 파이프라인 인덱스 (risk_db/) | 6 | 매 수집 실행마다 |

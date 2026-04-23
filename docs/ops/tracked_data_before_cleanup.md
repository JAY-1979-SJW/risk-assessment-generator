# tracked data 백업 목록 (정리 전 스냅샷)

**생성일**: 2026-04-23
**목적**: `data/` 하위의 현재 git tracked 파일 목록을 정리 전에 기록. git-guard cleanup(옵션 B) 수행 후 롤백/감사 기준으로 사용.
**근거**: 사용자 지시 (1단계 "현재 tracked 대용량 백업 목록 생성 (read-only)").
**read-only 단계**: 본 단계에서는 `git ls-files`, 디스크 stat 외 **어떤 파괴적 명령도 수행하지 않음**.

---

## 1. 총괄 집계

| 구분 | count | bytes | 조치 |
|------|-------|-------|------|
| REMOVE: `data/raw/kosha/` | 983 | 4,081,859 | 3단계 `git rm --cached -r` |
| REMOVE: `data/raw/kosha_forms/` | 8 | 277,461 | 3단계 `git rm --cached -r` |
| REMOVE: `data/raw/kosha_external/` | 0 | 0 | 현재 untracked — .gitignore 만으로 충분 |
| REMOVE: `data/forms/` | 0 | 0 | 현재 untracked — .gitignore + `source_map.csv` 예외 |
| REMOVE: `data/normalized/` | 983 | 4,256,576 | 3단계 `git rm --cached -r` |
| KEEP: `data/raw/law_api/` (메타 4건) | 4 | 144,767 | 유지 — `*_index.json`, `rename_map.json` |
| KEEP: `data/risk_db/` | 128 | 6,166,758 | 유지 — 규칙·매핑·yaml/md/csv 메타 |
| KEEP: `data/law_db/` | 0 | 0 | 현재 tracked 없음 |
| **tracked 총합** | **2,106** | **14,927,321 (≈15 MB)** | |

---

## 2. 실제 디스크 용량 (참고)

정리 후에도 **디스크 원본은 보존**. 단지 git index 에서만 제거.

| 디렉토리 | 디스크 용량 | tracked 여부 |
|----------|-------------|---------------|
| `data/raw/moel_forms/` | 930 MB | tracked 0 (이미 제외) |
| `data/forms/` | 700 MB | tracked 0 (이번 세션 신규) |
| `data/risk_db/` | 23 MB | tracked 128 |
| `data/normalized/` | 6.8 MB | tracked 983 |
| `data/raw/kosha/` | 6.5 MB | tracked 983 |
| `data/raw/kosha_external/` | 4.4 MB | tracked 0 |
| `data/law_db/` | 3.4 MB | tracked 0 |
| `data/raw/law_api/` | 4.0 MB | tracked 4 |
| `data/raw/kosha_forms/` | 288 KB | tracked 8 |

---

## 3. REMOVE 대상 상세

### 3.1 `data/raw/kosha/` (983 파일, 4.08 MB)

- 전건: `data/raw/kosha/kosha_kosha_opl_{ID}.json` 패턴
- 수집기: `scripts/collect/kosha_guides.py` (또는 상위 파이프라인) → KOSHA OPL/교재 메타 JSON
- **서버 git-guard flapping 의 주 원인** — 수집기 재저장 시 line ending / key ordering 이 달라지며 Modified 대량 발생
- ID 범위: 샘플 `28763`, `28798`, `28810`, `28868`, `30186` ~ `30217` 등

### 3.2 `data/raw/kosha_forms/` (8 파일, 277 KB)

- 전건 tracked:
  - `api_probe_case_arch.json`
  - `api_probe_master_arch.json`
  - `api_probe_revision_notice.json`
  - `api_probe_safe_data_room.json`
  - `api_probe_safe_health_arch.json`
  - `api_probe_safe_health_form.json`
  - `api_probe_tech_support_all.json`
  - `api_probe_tech_support_industry.json`
- 성격: KOSHA 서식/기술자료 API probe 결과. 수집 스크립트 재실행 시 갱신되므로 제외 대상. 재생성 가능.

### 3.3 `data/normalized/` (983 파일, 4.26 MB)

- 전건: `data/normalized/kosha/kosha_kosha_opl_{ID}.json` — kosha 원본을 정규화한 파이프라인 산출물
- 원본(`data/raw/kosha/`)에서 언제든 재생성 가능 (파이프라인 재실행)

### 3.4 `data/raw/kosha_external/` (tracked 0)

- 이번 세션에서 추가된 KOSHA/MOEL/법령 외부 다운로드 16 파일. 현재 untracked → .gitignore 만으로 차단.

### 3.5 `data/forms/` (tracked 0)

- 이번 세션 신규 권위 뷰 151 파일 (700 MB). 현재 untracked.
- 예외: `data/forms/source_map.csv` 는 **메타로 커밋 유지** (권위뷰 재구축의 핵심 레퍼런스).

---

## 4. KEEP 대상 상세

### 4.1 `data/raw/law_api/` (4 메타 파일)

| 파일 | 성격 |
|------|------|
| `data/raw/law_api/admrul/2026-04-21/admin_rules_index.json` | 행정규칙 수집 인덱스 |
| `data/raw/law_api/expc/2026-04-21/expc_index.json` | 해석례 수집 인덱스 |
| `data/raw/law_api/law/2026-04-21/laws_index.json` | 법령 수집 인덱스 |
| `data/raw/law_api/licbyl/rename_map.json` | licbyl URL-인코딩 파일명 해제 맵 |

모두 인덱스/맵 메타. **유지**.

본 디렉토리 아래 `licbyl/files/**` 원본 hwp/hwpx/pdf 는 tracked 아님 — 현재 .gitignore 에 `*.hwp`, `*.pdf` 는 없지만 지금껏 git add 된 적 없으므로 제외된 상태. 3단계 이후 .gitignore 에 `data/raw/law_api/**/files/**` 를 추가할지 여부는 별도 판단.

### 4.2 `data/risk_db/` (128 파일, 6.17 MB)

형식별:
- json 80 — 규칙·매핑·법령 콘텐츠
- sql 16 — 스키마/시드
- md 14 — 문서
- csv 12 — 매핑 CSV
- bak 3 — 백업 (판단 필요)
- yaml 2 — 설정
- txt 1

전건 **유지**. 3개 `.bak` 파일은 차후 별도 정리 대상으로 기록하되 이번 cleanup 범위 밖.

### 4.3 `data/law_db/` (tracked 0)

디스크엔 3.4 MB 있으나 tracked 없음. 그대로 둠.

---

## 5. 본 목록을 작성한 이유

1. `git rm --cached -r` 는 **index 에서만** 제거하지만, 혹시 실수로 `-r` 로 `data/` 전체를 날리는 경우를 대비해 **무엇을 제거하고 무엇을 살릴지 사전에 고정**.
2. 서버에서 동일 pull 후 dirty 가 해소됐는지 비교할 baseline.
3. KEEP 대상인 `data/risk_db/` 128 파일이 단계 중 실수로 인덱스에서 빠지지 않는지 검증 근거.

---

## 6. 다음 단계

Step 2: `.gitignore` 보강 + `.gitattributes` 신설.
Step 3: 본 REMOVE 목록에 한해 `git rm --cached -r` 수행. KEEP 파일은 건드리지 않음.

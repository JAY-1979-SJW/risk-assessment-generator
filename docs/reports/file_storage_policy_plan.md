# FILE-STORAGE-3: 생성 문서 다운로드/보관/파일명/정리 정책 설계

**일시**: 2026-04-29 (KST)  
**작업**: FILE-STORAGE-3 — 생성 문서 저장/다운로드/보관/정리 정책 설계  
**검증자**: Claude Sonnet 4.6 (자동), read-only 조사 + 보고서 작성만 수행

---

## 1. 목적

V1.1에서 생성 문서 영속 저장소(FILE-STORAGE-2)가 반영된 이후,  
운영 환경에서 안전하고 지속 가능하게 생성 문서를 관리하기 위한 정책을 설계한다.

이 보고서는 설계 문서이며, 구현은 다음 Stage에서 순차적으로 진행한다.

---

## 2. 현재 구현 조사 결과

### 2.1 GENERATED_DOCUMENTS_DIR 사용 위치

| 파일 | 역할 |
|------|------|
| `backend/services/new_construction_excel_runner.py` | xlsx 파일 경로 결정 및 생성 |
| `backend/services/new_construction_zip_builder.py` | ZIP 파일 경로 결정 및 생성 |
| `backend/services/new_construction_downloads.py` | download-zip 경로 검증 |

세 파일 모두 동일 패턴:
```python
_DEFAULT_BASE_DIR = "/tmp/risk_assessment_generated_documents"
raw = os.getenv("GENERATED_DOCUMENTS_DIR") or _DEFAULT_BASE_DIR
return Path(raw).resolve()
```

현재 운영 설정: `GENERATED_DOCUMENTS_DIR=/app/generated_documents` (FILE-STORAGE-2에서 반영)

### 2.2 파일 경로 생성 방식

**xlsx (excel_runner)**:
```python
base / f"project_{project_id}" / f"package_{package_id}" / f"{file_id}_{safe_display_name}.xlsx"
```
- `file_id`: DB `generated_document_files.id` (auto-increment, 글로벌 유니크)
- `safe_display_name`: 한글/영문/숫자/`._-` 허용, 나머지 `_` 치환, 80자 제한

**ZIP (zip_builder)**:
```python
base / f"project_{project_id}" / f"package_{package_id}" / f"package_{package_id}.zip"
```
- 임시 파일 `.tmp` 생성 후 `os.replace()` 로 원자적 교체

### 2.3 현재 디렉터리 구조 (실제)

```
/app/generated_documents/
└── project_4/
    └── package_5/
        ├── 20_TBM_일지.xlsx
        ├── 21_작업_전_안전_확인서.xlsx
        ├── 22_출근부.xlsx
        ├── 23_사진_첨부_시트.xlsx
        └── package_5.zip
```

### 2.4 ZIP 내부 파일명 (실제 확인)

ZIP 내부에서는 `file_id_` 접두어 없이 `display_name.xlsx` 형식만 사용:
```
TBM_일지.xlsx
작업_전_안전_확인서.xlsx
출근부.xlsx
사진_첨부_시트.xlsx
```
→ 서버 저장 파일명과 ZIP 내부 파일명이 다름

### 2.5 download-zip 라우터 동작

```
GET /api/v1/new-construction/document-packages/{package_id}/download-zip
```

1. DB에서 `zip_file_path` 조회
2. `resolve_zip_path()` 로 path safety 검증
3. 검증 통과 시 `FileResponse` 반환 (상태 변경/ZIP 재생성 없음)
4. Content-Disposition 헤더: RFC 5987 방식 (ASCII fallback + UTF-8 인코딩)

### 2.6 API 응답에서 서버 경로 노출 현황

| API | 응답에 노출되는 경로 | 위험도 |
|-----|---------------------|--------|
| `POST /document-jobs/{id}/run-excel` | `DocumentFileRunResult.file_path` = 절대경로 | **WARN** |
| `POST /document-packages/{id}/build-zip` | `DocumentPackageZipBuildResponse.zip_file_path` = 절대경로 | **WARN** |
| `GET /document-packages/{id}/download-zip` | 서버 경로 미노출 (FileResponse만 반환) | PASS |
| `GET /document-packages/`, `GET /document-packages/{id}` | `GeneratedDocumentPackageResponse.zip_file_path` = 절대경로 | **WARN** |
| `GET /document-packages/{id}/files` | `GeneratedDocumentFileResponse.file_path` = 절대경로 | **WARN** |

---

## 3. 현재 리스크 분석

### 3.1 리스크 판정표

| # | 리스크 | 판정 | 근거 |
|---|--------|------|------|
| 1 | 서버 절대 경로가 API 응답에 노출 | **WARN** | `file_path`, `zip_file_path` 필드가 그대로 응답에 포함됨 |
| 2 | 사용자가 임의 path를 넣어 다운로드 가능 | PASS | download-zip은 `package_id`(int)로만 접근, path 직접 입력 불가 |
| 3 | path traversal 가능성 | PASS | `..` split 검사 + `Path.resolve().relative_to(base)` 이중 차단 |
| 4 | generated_documents 밖 파일 접근 차단 | PASS | `candidate.relative_to(base)` 검증으로 차단 |
| 5 | symlink escape 차단 | **WARN** | `Path.resolve()`가 symlink를 실제 경로로 변환하므로 symlink→base_dir 외부 파일은 차단됨. 단, 명시적 `is_symlink()` 검사는 없음 — 현재 구조상 실질 위험 낮음 |
| 6 | 파일명 중복 가능성 | PASS | `file_id`(글로벌 유니크)가 파일명 접두어로 포함되어 중복 없음 |
| 7 | 한글/공백/특수문자 파일명 다운로드 문제 | **WARN** | 서버 저장은 한글 허용(`가-힣`). Windows 브라우저에서 한글 파일명 다운로드는 RFC 5987로 처리하나, 일부 구형 클라이언트 미호환 |
| 8 | smoke/test 파일과 운영 파일 혼재 | **WARN** | 현재 `project_4`(V1_1_SMOKE) 파일이 동일 디렉터리에 존재. 구분 디렉터리 없음 |
| 9 | 오래된 파일 무한 누적 | **WARN** | 정리 정책/스크립트 없음. 현재는 파일 수 적어 문제 없으나 운영 확대 시 용량 증가 |
| 10 | 파일 삭제 기준 부재 | **WARN** | 삭제 트리거, 보관 기간 정의 없음 |

**PASS**: 3건 | **WARN**: 7건 | **FAIL**: 0건

### 3.2 가장 시급한 리스크

1. **서버 절대경로 노출** (리스크 #1): run-excel/build-zip 응답에 `/app/generated_documents/...` 절대경로 포함 → 공격자가 서버 디렉터리 구조 파악 가능
2. **smoke/test 파일 혼재** (리스크 #8): 식별 구조 없으면 cleanup 시 운영 파일 실수 삭제 가능
3. **무한 누적** (리스크 #9): 프로젝트 수 증가 시 디스크 고갈 위험

---

## 4. 권장 디렉터리 구조

### 4.1 현재 구조

```
generated_documents/
└── project_{id}/
    └── package_{id}/
        ├── {file_id}_{display_name}.xlsx
        └── package_{id}.zip
```

### 4.2 권장 구조

```
generated_documents/
├── projects/                          # 운영 프로젝트 생성 문서
│   └── {project_id}/
│       └── packages/
│           └── {package_id}/
│               ├── manifest.json      # 패키지 메타데이터 (§6 참조)
│               ├── xlsx/              # 개별 xlsx 파일
│               │   └── {file_id}_{safe_name}.xlsx
│               └── zip/               # 생성된 ZIP
│                   └── package_{package_id}_{YYYYMMDD}.zip
├── smoke/                             # smoke/test 생성 파일
│   └── project_{id}/
│       └── package_{id}/
│           └── ...
└── archive/                           # 장기 보관 대상 (수동 이동)
    └── ...
```

### 4.3 현재 → 권장 구조 마이그레이션

| 항목 | 판단 |
|------|------|
| 마이그레이션 즉시 필요 여부 | 불필요 — 현재 파일 수 적고 모두 smoke/test 파일 |
| 기존 `project_4/package_5/` 호환 | DB의 `file_path`, `zip_file_path` 컬럼에 절대경로 저장됨 → 경로 이동 시 DB 업데이트 필요 |
| 추천 마이그레이션 시점 | FILE-STORAGE-4에서 신규 생성부터 권장 구조 적용. 기존 smoke 파일은 별도 정리 지시에서 처리 |
| smoke 파일 분리 방식 | `project_id=4`(V1_1_SMOKE_20260429)처럼 테스트 project를 별도 환경변수 `SMOKE_PROJECT_IDS`로 관리하거나, `smoke/` 디렉터리 하위에 생성 |

### 4.4 단기 호환 방식 (FILE-STORAGE-4 구현 전)

신규 생성은 권장 구조를 즉시 적용하고, 기존 경로(`project_{id}/package_{id}/`) 파일은 DB의 `file_path`를 기준으로 계속 서빙. 경로 형식이 혼재되더라도 `resolve_zip_path()` 의 base_dir 검증이 통과하면 동작 가능.

---

## 5. 권장 파일명 표준

### 5.1 xlsx 서버 저장 파일명

**현재**:
```
{file_id}_{safe_display_name}.xlsx
예: 20_TBM_일지.xlsx
```

**권장 (변경 없음 — 현재 방식 유지)**:
```
{file_id}_{safe_display_name}.xlsx
```

| 기준 | 결정 | 이유 |
|------|------|------|
| 한글 파일명 허용 | ✅ 허용 | 리눅스 파일시스템 문제 없음, 사람이 읽기 쉬움 |
| 공백 제거 | ✅ 제거 (`_` 치환) | 쉘 스크립트/경로 처리 안전 |
| 특수문자 치환 | ✅ `_` 치환 (`[^0-9A-Za-z가-힣._-]+`) | 현재 구현 유지 |
| 중복 방지 | ✅ `file_id` 접두어 (글로벌 유니크) | DB `generated_document_files.id` |
| 길이 제한 | 80자 제한 | 현재 구현 유지 |

### 5.2 ZIP 서버 저장 파일명

**현재**:
```
package_{package_id}.zip
예: package_5.zip
```

**권장**:
```
package_{package_id}_{YYYYMMDD_HHMMSS}.zip
예: package_5_20260429_163301.zip
```

변경 이유: 동일 package_id로 ZIP을 재생성할 경우 타임스탬프가 없으면 충돌. 타임스탬프 추가로 이전 ZIP을 `archive/`로 이동 후 새 ZIP 생성 가능.

### 5.3 ZIP 내부 파일명

**현재**: `{safe_display_name}.xlsx` (file_id 없음, 한글 허용)
```
TBM_일지.xlsx, 작업_전_안전_확인서.xlsx, ...
```

**권장 (유지)**: 사용자가 다운로드받는 ZIP이므로 사람이 읽기 쉬운 이름 유지.

| 기준 | 결정 |
|------|------|
| 한글 허용 | ✅ — 현장 사용자가 직접 여는 파일, 한글이 자연스러움 |
| Windows 호환 | ✅ — RFC 5987 Content-Disposition으로 처리 |
| 중복 방지 | ✅ — 동일 display_name 중복 시 `{file_id}_{name}.xlsx` fallback (현재 구현) |

### 5.4 download-zip Content-Disposition 파일명

**현재**:
```
ASCII fallback: package_{package_id}.zip
UTF-8 form: {safe_package_name}.zip (package_name이 없으면 fallback)
```

**권장**: `package_name` 필드를 Rule/프로젝트 기반으로 자동 생성하여 의미있는 파일명 제공.
```
예: 위험성평가_홍길동_20260429.zip
```
구현은 FILE-STORAGE-4에서 처리.

---

## 6. manifest.json 표준

### 6.1 manifest가 필요한 이유

| 이유 | 설명 |
|------|------|
| 파일 추적 | DB 없이도 패키지 내용을 디렉터리만으로 파악 가능 |
| 무결성 검증 | sha256 해시로 파일 손상 감지 |
| cleanup 기준 | manifest의 `generated_at`, `project_id`로 삭제 대상 판정 |
| 다운로드 검증 | DB `zip_file_path`가 없어도 manifest로 파일 존재 확인 가능 |
| 감사 로그 | 언제 누가 어떤 문서를 생성했는지 파일시스템에 기록 |

### 6.2 권장 manifest.json 스키마

```json
{
  "storage_version": "v1",
  "project_id": 4,
  "package_id": 5,
  "rule_id": "RULE_DAILY_TBM",
  "generated_at": "2026-04-29T16:33:01+09:00",
  "generated_by_user_id": null,
  "subject": {
    "kind": "date",
    "target_date": "2026-04-30"
  },
  "documents": [
    {
      "file_id": 20,
      "kind": "form",
      "form_type": "tbm_log",
      "supplemental_type": null,
      "display_name": "TBM 일지",
      "stored_filename": "20_TBM_일지.xlsx",
      "relative_path": "xlsx/20_TBM_일지.xlsx",
      "sha256": "...",
      "file_size": 12345,
      "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "status": "ready"
    }
  ],
  "zip": {
    "stored_filename": "package_5_20260429_163301.zip",
    "relative_path": "zip/package_5_20260429_163301.zip",
    "sha256": "...",
    "file_size": 29122,
    "mime_type": "application/zip",
    "built_at": "2026-04-29T16:33:15+09:00"
  },
  "is_smoke": false,
  "retention_policy": "standard_30d"
}
```

### 6.3 DB 연동 판단

| 질문 | 판단 |
|------|------|
| DB 없이 파일 추적 가능한가 | ✅ manifest만으로 가능 |
| 추후 DB 연동 필요한가 | △ 현재는 불필요. 다운로드 횟수, 사용자별 접근 이력이 필요해지면 DB 연동 고려 |
| manifest로 cleanup 대상 판정 | ✅ `generated_at` + `retention_policy`로 판정 가능 |
| manifest로 다운로드 검증 | ✅ `zip.relative_path`로 파일 존재 확인 가능 (DB `zip_file_path` 백업) |

### 6.4 is_smoke 플래그

`is_smoke: true` — project가 테스트용(`V1_1_SMOKE_*`)인 경우 자동 설정.  
cleanup 스크립트에서 `is_smoke: true` 파일을 우선 정리 대상으로 분류.

---

## 7. 다운로드 보안 정책

### 7.1 현재 구현 보안 수준

| 보안 기준 | 현재 상태 | 판정 |
|-----------|-----------|------|
| absolute path 직접 다운로드 금지 | `package_id`(int)로만 접근 | ✅ PASS |
| base_dir 기준 경로 resolve | `Path.resolve().relative_to(base)` | ✅ PASS |
| `..` path traversal 차단 | split 검사 + relative_to | ✅ PASS |
| symlink escape 차단 | `resolve()`로 실제 경로 변환 후 검증 | ✅ PASS (명시적 is_symlink 없음) |
| 존재하지 않는 파일 404 | `candidate.is_file()` 검사 | ✅ PASS |
| 권한 없는 project 403 | ❌ project_id 기반 접근 제어 없음 | **WARN** |
| 응답에 서버 절대경로 미노출 | ❌ run-excel/build-zip 응답에 file_path 포함 | **WARN** |
| ZIP 생성 실패 명확한 에러 | `zip_not_built` / `zip_file_missing` 에러 코드 | ✅ PASS |

### 7.2 필요한 개선사항 (우선순위순)

**개선 1 — 서버 절대경로 제거 (FILE-STORAGE-4)**

응답 스키마에서 `file_path`, `zip_file_path` 필드를 제거하거나 상대경로로 대체.

```python
# 현재 (WARN)
"file_path": "/app/generated_documents/project_4/package_5/20_TBM_일지.xlsx"

# 권장 (상대경로)
"relative_path": "project_4/package_5/20_TBM_일지.xlsx"
# 또는 완전 제거 (download API에서만 파일 서빙)
```

**개선 2 — 프로젝트 접근 권한 검증 (FILE-STORAGE-4 또는 별도 Stage)**

```python
# download-zip 라우터에서 project_id 검증 추가
pkg = repo.get_document_package(package_id)
# 현재 사용자가 pkg["project_id"]에 접근 권한이 있는지 확인
# (현재 auth 미구현이므로 추후 auth Stage와 연계)
```

**개선 3 — symlink 명시적 차단 (FILE-STORAGE-4)**

```python
if candidate.is_symlink():
    return None, "unsafe_path"
```

**개선 4 — 다운로드 URL 토큰 방식 (장기, 별도 Stage)**

현재는 `package_id`가 공개 식별자. 다운로드 전용 일회성 토큰 발급으로 URL 예측 방지.

---

## 8. 보관 기간 정책

> **주의**: 법정 보존기간은 별도 법령 검토 Stage에서 확정. 이 절은 시스템 운영 정책 초안이다.

### 8.1 파일 유형별 보관 기간 초안

| 파일 유형 | 식별 방법 | 보관 기간 | 비고 |
|-----------|-----------|-----------|------|
| smoke/test 파일 | `is_smoke: true` 또는 project title `SMOKE_*` | **7일** | 검증 후 정리 |
| tmp 중간 파일 (`.tmp`) | 확장자 `.tmp` | **1일** | build-zip 실패 잔재 |
| 일반 생성 파일 | `retention_policy: standard_30d` | **30일** | 기본 정책 |
| 프로젝트 산출물 | `retention_policy: project_1y` | **1년** | 프로젝트 종료 후 기산 |
| 법정 안전서류 | `retention_policy: legal_3y` | **3년 이상** | 별도 법령 검토 필요 |

### 8.2 법정 보존기간 참고 (잠정)

산업안전보건법 및 건설기술진흥법에 따라 안전교육 일지, 작업허가서 등 서류의 보존기간이 규정될 수 있음. 정확한 기간은 법령 검토 Stage에서 확정.

### 8.3 보관 정책 적용 방식

- manifest.json의 `retention_policy` 필드로 각 패키지별 정책 지정
- cleanup 스크립트가 `generated_at` + `retention_policy`로 만료 여부 판정
- 삭제 전 `archive/` 디렉터리로 이동 후 별도 보관 기간 적용 가능

---

## 9. 오래된 파일 정리 정책

### 9.1 설계 원칙

- **초기 정책: delete 금지, dry-run 우선**
- apply 실행 전 반드시 수동 확인 단계 포함
- 운영 자동화는 충분한 운영 기간(최소 3개월) 후 단계적 도입

### 9.2 권장 스크립트 (구현은 FILE-STORAGE-5에서)

```
scripts/storage/cleanup_generated_documents.py --dry-run
scripts/storage/cleanup_generated_documents.py --apply
scripts/storage/cleanup_generated_documents.py --smoke-only --dry-run
```

### 9.3 dry-run 출력 항목

```
[DRY-RUN] 정리 대상 파일 목록
──────────────────────────────────
project_4/package_1/  (smoke, generated_at: 2026-04-29, age: 0d, policy: smoke_7d) → 삭제 예정
project_4/package_2/  (smoke, generated_at: 2026-04-29, age: 0d, policy: smoke_7d) → 삭제 예정
...
──────────────────────────────────
대상: 3 패키지, 15 파일, 총 120 KB
제외: 2 패키지 (retention 미만)
보고: --apply 로 실행하면 위 파일이 삭제됩니다.
```

### 9.4 삭제 후보 판정 기준

| 기준 | 설명 |
|------|------|
| `generated_at` + `retention_policy` 기준 만료 | 주 삭제 트리거 |
| `is_smoke: true` + 7일 초과 | smoke 파일 우선 정리 |
| `.tmp` 파일 + 1일 초과 | 임시 파일 정리 |
| package `status = failed` + 30일 초과 | 실패 패키지 정리 |

### 9.5 삭제 제외 기준

| 기준 | 설명 |
|------|------|
| manifest 없는 파일 | 출처 불명 — 수동 검토 후 결정 |
| `retention_policy: legal_*` | 법정 보존 대상 절대 자동 삭제 금지 |
| `archive/` 하위 파일 | 수동 이동된 파일, cleanup 대상 제외 |
| DB에 `status: ready` 이고 만료 미경과 | 정상 운영 파일 |

### 9.6 manifest 없는 파일 처리

```
[WARN] manifest.json 없는 파일 발견:
  project_4/package_1/  → manifest 없음, dry-run에서 SKIP, 수동 검토 필요
```

manifest 없는 파일은 dry-run에서 목록만 출력하고 삭제하지 않는다.  
FILE-STORAGE-4에서 manifest 생성 구현 후 신규 패키지는 모두 manifest 포함.

### 9.7 apply 실행 전 백업

- `apply` 실행 전 `/app/backups/generated_documents_cleanup_{YYYYMMDD}.tar.gz` 생성 권장
- 용량이 크면 삭제 대상만 선택 백업

### 9.8 운영 자동화 조건

| 조건 | 기준 |
|------|------|
| 수동 dry-run + 확인 횟수 | 3회 이상 |
| 운영 기간 | 3개월 이상 |
| 자동화 범위 | smoke/tmp 파일만 (운영 파일 자동 삭제 금지) |
| 자동화 실행 주기 | 주 1회 (cron, 권장) |

---

## 10. 구현 우선순위

### FILE-STORAGE-4 (다음 Stage)

**manifest.json 생성 + 다운로드 경로 보안 최소 구현**

- run-excel 완료 시 manifest.json 자동 생성
- manifest에 `is_smoke` 자동 판정 (project_title 기반)
- 응답에서 서버 절대경로 제거 (`file_path` → `relative_path` 또는 제거)
- symlink 명시적 차단 추가
- 현재 `project_{id}/package_{id}/` 구조 유지 (마이그레이션 없이)

### FILE-STORAGE-5

**cleanup dry-run 스크립트 구현**

- `scripts/storage/cleanup_generated_documents.py --dry-run`
- manifest 기반 만료 판정
- smoke/tmp 파일 우선 대상

### FILE-STORAGE-6

**운영 적용 및 기존 파일 호환성 검증**

- 현재 smoke 파일 정리
- 신규 manifest 구조 검증
- 권장 디렉터리 구조(`projects/`, `smoke/`) 점진 전환

### FILE-STORAGE-7

**보관기간/법정 보존기간 정책 확정**

- 산업안전보건법 조문 검토
- retention_policy 값 확정
- 법정 보존 대상 문서 유형 목록화

---

## 11. 다음 Stage 제안

```
FILE-STORAGE-4 지시 기준:
- manifest.json 생성 구현 (run-excel 완료 시 자동 생성)
- is_smoke 자동 판정 로직
- API 응답에서 server absolute path 제거
- symlink 명시적 차단
- 최소 코드 변경, 기존 디렉터리 구조 호환 유지
```

---

## 검증 요약

| 항목 | 결과 |
|------|------|
| 코드 변경 | 없음 |
| compose 변경 | 없음 |
| DB 변경 | 없음 |
| 컨테이너 재기동 | 없음 |
| 파일 삭제 | 없음 |
| 생성 파일 | 이 보고서 1개 |

---

**최종 판정: PASS** (설계 완료)  
*다음 Stage: FILE-STORAGE-4 — manifest.json 생성 및 안전한 다운로드 경로 최소 구현*

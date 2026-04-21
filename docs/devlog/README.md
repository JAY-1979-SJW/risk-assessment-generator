# devlog 운영 규칙

위험성평가표 자동생성기 프로젝트의 작업 기록 체계.

---

## 3층 기록 구조

```
1층 — devlog (사람이 읽는 작업일지)
    docs/devlog/YYYY-MM-DD_<slug>.md

2층 — git commit (실제 변경 증거)
    feat(stepNN): ...
    test(stepNN): ...
    docs(stepNN): ...

3층 — index 로그 (기계적 추적)
    docs/devlog/_index.jsonl
```

---

## 1층: devlog 규칙

- 위치: `docs/devlog/YYYY-MM-DD_<slug>.md`
- 단계 완료마다 **반드시 1개** 작성
- 템플릿: `_template.md` 사용
- 반드시 포함: 목표 / 수정 파일 / 검증 결과 / **PASS/WARN/FAIL**

### PASS / WARN / FAIL 기준

| 판정 | 조건 |
|---|---|
| PASS | 테스트 전체 통과 + 핵심 지표 기준선 충족 |
| WARN | 일부 SKIP / 경계 조건 미달 / 데이터 부족 |
| FAIL | 테스트 실패 / 핵심 기준 미달 / 보호 파일 오염 |

---

## 2층: git commit 규칙

### 커밋 메시지 형식

```
<type>(step<NN>): <summary>

<optional body — 핵심 변경 / 검증 결과 요약>
```

### type 목록

| type | 사용 조건 |
|---|---|
| `feat` | 신규 기능 / 라우터 / 서비스 / 엔진 |
| `test` | 테스트 추가 / 회귀 검증 |
| `docs` | devlog / 표준 문서 / README |
| `fix` | 버그 수정 / safe-guard 보정 |
| `data` | law_db / 수집 데이터 / 매핑 파일 |
| `chore` | 기록 체계 / gitignore / 스크립트 |

### 예시

```
feat(step16): draft API operational path verification

- recommend/recalculate both use identical _merge_law_evidence()
- 32 regression tests: 31 PASS, 1 SKIP
- generic-law top1: 0%, repeat call match: 100%
```

### 커밋 금지 대상

- `.env`, `*.secrets` (민감값)
- `frontend/node_modules/`
- `scraper/kosha_files/` (대용량 수집물)
- `*.log` 파일

---

## 3층: `_index.jsonl` 규칙

- 위치: `docs/devlog/_index.jsonl`
- 형식: UTF-8, append-only, 한 줄 = 한 단계
- 단계 완료마다 **반드시 1줄 append**

### 필드 정의

| 필드 | 타입 | 설명 |
|---|---|---|
| `date` | string | 작업 완료일 (YYYY-MM-DD) |
| `step` | int | 단계 번호 |
| `title` | string | 단계 작업명 |
| `result` | string | PASS / WARN / FAIL |
| `devlog_path` | string | devlog 파일 경로 |
| `commit_hash` | string | 단계 커밋 해시 (7자) or "pending" |
| `tests_summary` | string | "N passed, M skipped" 형식 |
| `files_changed_count` | int | 변경 파일 수 |
| `protected_files_changed` | bool | 보호 파일(프론트/DB/스키마) 수정 여부 |
| `notes` | string | 핵심 지표 또는 특이사항 |

### 예시 줄

```jsonl
{"date":"2026-04-21","step":16,"title":"API 운영 경로 연결 고정","result":"PASS","devlog_path":"docs/devlog/2026-04-21_api-operational-connection.md","commit_hash":"abc1234","tests_summary":"31 passed, 1 skipped","files_changed_count":2,"protected_files_changed":false,"notes":"generic-law top1=0%, repeat match=100%"}
```

### append 방법

```bash
# 수동 append
python scripts/devlog_append.py

# 직접 편집
echo '{"date":"...","step":NN,...}' >> docs/devlog/_index.jsonl
```

---

## 단계 완료 절차

```
1. 코드/문서 수정 완료
2. 테스트 실행 → PASS/WARN/FAIL 판정
3. devlog 작성 (_template.md 기반)
4. git add (선택적) + git commit
5. _index.jsonl 1줄 append (commit_hash 포함)
6. 최종 보고
```

---

## 단계 완료 체크리스트

작업 완료 전 반드시 확인:

- [ ] devlog 1개 작성됨
- [ ] 테스트 실행 결과 기록됨
- [ ] PASS / WARN / FAIL 판정 명시됨
- [ ] git commit 완료됨
- [ ] `_index.jsonl` 1줄 append 완료됨
- [ ] 보호 파일 수정 여부 기록됨
- [ ] commit_hash devlog에 기입됨

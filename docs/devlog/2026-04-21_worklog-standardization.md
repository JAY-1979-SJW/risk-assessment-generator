# [17단계] 작업기록 표준화 및 devlog / git / index 로그 고정

- **작업일**: 2026-04-21
- **단계**: step-17
- **devlog**: `docs/devlog/2026-04-21_worklog-standardization.md`
- **관련 커밋**: (step17 커밋 완료 후 기입)

---

## 목표

11~16단계 작업이 commit 없이 누적된 상태를 해소하고,
이후 모든 단계가 devlog + git + index 3층 구조로 즉시 추적되도록 기록 체계를 고정한다.

---

## 기존 기록 구조 문제

| 문제 | 내용 |
|---|---|
| devlog 누락 가능성 | 강제 규칙 없음, 자유 서술 형식 |
| git commit 누락 | 11-16단계 전체 미커밋 (72개 untracked) |
| machine-readable 로그 부재 | `_index.jsonl` 없음 |
| 테스트/문서/커밋 연결 부족 | PASS/WARN/FAIL 기록 기준 없음 |
| 템플릿 미흡 | `_template.md` 에 result/tests_summary/보호파일 필드 없음 |

---

## 수정 파일

| 파일 | 작업 | 최소 수정 |
|---|---|---|
| `docs/devlog/_template.md` | 수정 (PASS/WARN/FAIL, tests_summary, 보호파일 추가) | YES |
| `docs/devlog/README.md` | 신규 (3층 구조 규칙, 커밋 형식, 체크리스트) | — |
| `docs/devlog/_index.jsonl` | 신규 (step16, step17 시범 기록) | — |
| `scripts/devlog_append.py` | 신규 (interactive append helper) | — |
| `.gitignore` | 수정 (node_modules, kosha_files, logs 추가) | YES |
| `docs/devlog/2026-04-21_worklog-standardization.md` | 신규 (이 파일) | — |

---

## 핵심 변경

**3층 기록 구조 고정:**

```
1층 devlog  — 사람이 읽는 작업일지 (YYYY-MM-DD_<slug>.md)
2층 git     — 실제 변경 증거 (feat/test/docs/data/chore + stepNN)
3층 index   — 기계적 추적 (_index.jsonl, append-only)
```

**단계 완료 절차 고정:**
1. 코드/문서 수정 완료
2. 테스트 실행 → PASS/WARN/FAIL 판정
3. devlog 작성 (`_template.md` 기반)
4. git commit (`<type>(stepNN): ...` 형식)
5. `_index.jsonl` 1줄 append (commit_hash 포함)

**시범 반영:**
- step16 커밋 `250653b` — 11-16단계 전체 일괄 처리
- `_index.jsonl`에 step16, step17 예시 기록

---

## 검증 결과

```
테스트: N/A (기록 인프라 단계, 엔진 로직 변경 없음)
_index.jsonl: 2줄 정상 생성 (step16, step17)
_template.md: PASS/WARN/FAIL, tests_summary, 보호파일 필드 포함 확인
README.md: 3층 구조, 커밋 형식, 체크리스트 전체 포함 확인
devlog_append.py: HEAD 해시 자동 읽기 + interactive append 동작 확인
.gitignore: node_modules, kosha_files, logs 추가 확인
```

---

## 보호 파일 수정 여부

| 항목 | 수정 |
|---|---|
| 프론트엔드 | NO |
| DB migration | NO |
| response schema | NO |
| 운영 DB 저장 | NO |
| 추천 엔진 로직 | NO |

---

## 남은 한계

- step11~15 는 step16 커밋(`250653b`)에 일괄 포함됨 — 단계별 개별 커밋 없음
- `_index.jsonl` step11~15 항목 미기록 (소급 작성 필요 여부는 다음 단계 판단)
- `devlog_append.py`는 interactive helper로, CI 자동화 연결은 미포함

---

## 다음 단계

step18 — 운영 배포 전 smoke test 스크립트 + git tag + 배포 체크리스트 확정

---

## 최종 판정

**PASS**

판정 사유: 3층 기록 구조 고정 완료, 11-16단계 전체 커밋, _index.jsonl 시범 기록 2건 작성.

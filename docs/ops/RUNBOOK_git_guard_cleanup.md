# RUNBOOK — git-guard cleanup 서버 반영

**대상 서버**: `ubuntu@1.201.176.236` (앱서버)
**대상 경로**: `/home/ubuntu/apps/risk-assessment-app/app`
**원인 알림**: `git-guard FAIL` (2026-04-23 21:45 KST)
- Modified 815건 (line-ending flapping)
- Untracked 2,650건 (신규 수집분 + `data/normalized/` 파이프라인 산출)

**로컬 사전 작업**: 본 레포에서 옵션 B 정리 완료(커밋 1/커밋 2). push 만 남은 상태.
**적용 방식**: 서버에서 **`git pull --ff-only` 단일 경로만 사용** (CLAUDE.md 배포규칙 준수).

> ⚠️ 본 런북은 서버에서의 파일 **삭제를 수반하지 않는다**. `git rm --cached` 결과는 "인덱스 제거 + working-tree 유지" 이므로 pull 후에도 디스크 원본 JSON 983+8+983 건은 보존된다.

---

## 0. 사전 점검 (서버에서 실행)

```bash
ssh -i ~/.ssh/haehan-ai.pem ubuntu@1.201.176.236
cd /home/ubuntu/apps/risk-assessment-app/app

# 0.1 현재 HEAD/brach 확인
git rev-parse --abbrev-ref HEAD
git rev-parse --short HEAD          # 예상: 659f9791

# 0.2 dirty 규모 파악 (예상: Modified ~815, Untracked ~2,650)
git status --porcelain | awk '{print $1}' | sort | uniq -c

# 0.3 대용량 수집 디렉토리 디스크 용량 (삭제 금지 대상)
du -sh data/raw/kosha data/raw/kosha_forms data/normalized 2>/dev/null

# 0.4 백업 디렉토리 존재 여부 (없으면 생성)
[ -d /home/ubuntu/backup/git_guard_cleanup ] && echo "backup dir OK" || \
  mkdir -p /home/ubuntu/backup/git_guard_cleanup
```

**PASS 기준**: HEAD 가 `659f9791` (또는 이후의 직계 조상). Modified ≠ 0 이면 아래 1장으로 진행.

---

## 1. 서버 Modified 해소 — 인덱스만 리셋, 파일 유지

`git rm --cached` 를 서버에서 직접 수행하지 않는다 (로컬 커밋 1 에 이미 포함됨).
대신 **현 Modified 상태를 해제 (index 를 HEAD 에 맞춤)** 한 뒤 pull.

```bash
cd /home/ubuntu/apps/risk-assessment-app/app

# 1.1 실수 방지: 현재 수정된 파일 목록 백업
git status --porcelain | grep '^ M\|^M ' | awk '{print $2}' \
  > /home/ubuntu/backup/git_guard_cleanup/modified_before_reset_$(date +%Y%m%d_%H%M).txt

# 1.2 Modified 해제 (파일은 그대로, index 만 HEAD 로 맞춤)
git restore --staged .                  # staged 변경 해제
git restore .                           # working tree 변경 해제 (파일 내용은 HEAD 버전으로 복귀)
```

> ⚠️ `git restore .` 은 **working tree 의 추적 중인 파일** 만 건드린다. Untracked 파일(새로 수집된 2,650건)은 영향 없음.
> `data/raw/kosha/*.json` 983건은 현재 tracked 이므로 `git restore` 가 HEAD 의 버전으로 되돌리지만, 이후 pull 로 **index 에서 제거 + working-tree 파일은 그대로** 상태가 된다.

```bash
# 1.3 검증: Modified 0 인지 확인
git status --porcelain | awk '{print $1}' | sort | uniq -c
# 예상: ?? 만 존재 (untracked 2,650건)
```

**PASS 기준**: `M` / `A` / `D` 코드가 0 건.

---

## 2. pull --ff-only

```bash
# 2.1 원격 최신 fetch
git fetch origin

# 2.2 ff 가능한지 사전 확인
git log --oneline HEAD..origin/master | head -10

# 2.3 ff-only pull
git pull --ff-only origin master
```

**예상 변경**:
- `.gitignore` 보강 (large data 제외)
- `.gitattributes` 신규 (line-ending/바이너리 정책)
- `data/raw/kosha/`, `data/raw/kosha_forms/`, `data/normalized/` 아래 1,974 파일이 **index 에서 제거됨**
  - **디스크 파일은 그대로 보존** (working-tree 에 남음, 다만 untracked 로 바뀌고 .gitignore 에 의해 상태 표시에서도 숨김)
- `docs/standards/**`, `docs/ops/**`, `scripts/**` 신규 파일 다수
- `data/forms/source_map.csv`, `data/raw/kosha_external/download_manifest.json`, `data/raw/law_api/licbyl/_cleanup_plan.json` 신규(메타 예외)

**실패 시**: `fatal: Not possible to fast-forward` 발생하면 서버에서 로컬 커밋이 있다는 뜻. 그 경우 아래 대응:
1. `git stash push -u` (로컬 변경 임시 보관)
2. `git fetch origin && git reset origin/master --soft`? **금지** — 사용자 규칙 위반.
3. 대신 사용자에게 서버측 커밋 정체 보고 → 로컬에서 합치는 전략 재수립 후 재시도.

---

## 3. pull 후 검증

```bash
cd /home/ubuntu/apps/risk-assessment-app/app

# 3.1 HEAD 갱신 확인
git rev-parse --short HEAD
# → 로컬 push HEAD 와 동일한 단축 해시여야 함

# 3.2 상태 청결 확인
git status --porcelain | wc -l
# 예상: 0 (작업 트리는 완전 clean; .gitignore 가 대용량 수집본을 숨김)

# 3.3 대용량 tracked 감축 확인
git ls-files data/ | wc -l
# 예상: 132 (이전 2,106 → 감소)

# 3.4 디스크 원본이 삭제되지 않았는지 확인
ls data/raw/kosha/*.json 2>/dev/null | wc -l
# 예상: 983 (삭제되지 않고 보존)

ls data/raw/kosha_forms/*.json 2>/dev/null | wc -l
# 예상: 8

find data/normalized -type f 2>/dev/null | wc -l
# 예상: 983

# 3.5 .gitattributes 가 적용되는지 확인 (아무 JSON 하나에 대해)
git check-attr text eol data/raw/kosha/kosha_kosha_opl_28763.json
# 예상: text: set, eol: lf

# 3.6 ignore 가 의도대로 먹는지 sample 체크
git check-ignore -v data/raw/kosha/kosha_kosha_opl_28763.json
# 예상: .gitignore:XX:data/raw/kosha/**  → ignored

git check-ignore -v data/forms/source_map.csv
# 예상: exit code 1 (ignored 아님 — 예외로 keep)
```

**PASS 기준**:
- git status 0 건
- tracked data 파일 132 건 (±오차)
- 디스크 원본 983 + 8 + 983 = 1,974 건 모두 보존
- .gitattributes text=set/eol=lf 가 JSON 에 적용

---

## 4. git-guard 재실행 확인

```bash
# 4.1 git-guard 로그 경로 (CLAUDE.md 기준)
tail -20 /tmp/kosha_migration.log 2>/dev/null || echo "no guard log"

# 4.2 5분 기다리거나, 수동으로 guard 스크립트 실행 (위치는 운영 환경에 따라)
# 예: /home/ubuntu/bin/git-guard.sh 또는 crontab -l 로 확인
crontab -l | grep -i guard
```

**PASS 기준**: 이후 git-guard 결과가 `PASS` 또는 `CLEAN` 으로 바뀜 (Modified 0, Untracked ≤ 메타 수).

---

## 5. 롤백

본 RUNBOOK 이 실패 또는 부작용이 관측되면:

```bash
# 5.1 현재 HEAD 기억
git rev-parse HEAD > /home/ubuntu/backup/git_guard_cleanup/head_after_pull.txt

# 5.2 pull 이전 HEAD 로 되돌리기 (hard 금지 — soft 사용)
git reset --soft <pre-pull-HEAD>

# 5.3 .gitignore/.gitattributes 파일 자체는 working-tree 에서 editor 로 복원
```

> `git reset --hard` 는 사용자 규칙으로 금지. `--soft` 는 working-tree 보존하므로 허용.

**또는** 더 간단히: 서버에서 변경 없이 로컬에서 revert 커밋을 만들어 push 후 서버 재pull.

---

## 6. 이후 절차 (본 런북 범위 외)

- **수집기 write-flapping 방지**: `docs/ops/collector_write_policy.md` 의 1순위 3개 대상에 대해 별도 PR 진행.
- `data/normalized/` 의 재생성: 파이프라인 (`scripts/normalize/kosha_normalizer.py`) 재실행만으로 복원 가능 (원본 `data/raw/kosha/` 보존되어 있으므로).
- 정기 점검: 매주 `git ls-files data/ | wc -l` 이 132 수준에서 크게 증가하면 수집기 경로 누수 검토.

---

## 7. 체크리스트

| 항목 | 완료 |
|------|------|
| 0. 사전 HEAD/용량 점검 | ☐ |
| 1. Modified 해제 (`git restore`) | ☐ |
| 2. `git pull --ff-only` | ☐ |
| 3. 상태·tracked·디스크 검증 | ☐ |
| 4. git-guard 재실행 | ☐ |
| 5. (문제 발생 시) 롤백 확인 | ☐ |

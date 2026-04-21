# risk-assessment-app 장애 유형별 실행 템플릿

> 실제 복구 전 반드시 `infra/ops_restore_rehearsal.sh` 로 복구 가능 상태를 확인한다.
> 상세 runbook 은 README.md `## risk-assessment-app 장애 대응 / 복구 리허설 Runbook` 참조.

---

## 노이즈(Noise) vs 실제 장애(Incident) 판정 기준

### PASS / WARN / FAIL 과 Overall Status 의 차이

| 개념 | 설명 |
|------|------|
| PASS/WARN/FAIL | 개별 스크립트 1회 실행 결과 |
| HEALTHY | 24시간 기준 실제 FAIL 없음 (noise 포함 FAIL은 제외) |
| DEGRADED | git_guard FAIL 이지만 서비스 정상, 또는 WARN 다수 누적 |
| INCIDENT | self_check/backup/restore 연속 FAIL 2회, 또는 복수 source 동시 FAIL |

### 운영 잡음(Noise) 분류

- **git_guard mode_only**: `chmod` 등 파일 모드 변경만 있는 경우 → raw FAIL이라도 normalized WARN 으로 처리
- **1회성 WARN**: 초기 실행·데이터 부족·예상 가능한 경고 → 즉각 장애 아님
- **연속성 없는 FAIL**: 단발성 외부 요인(네트워크 지연 등) → DEGRADED 판정 전 재확인

### 실제 장애(INCIDENT) 승격 조건

1. `self_check` · `backup_check` · `restore_rehearsal` 중 하나가 연속 2회 FAIL
2. 서로 다른 source 2개 이상이 24시간 내 각 2회 이상 FAIL
3. API health / frontend HTTP 연속 2회 이상 비정상

### 판단 원칙

- **1회 FAIL ≠ 즉시 장애**: 연속성과 핵심 source 동시 실패 여부를 확인한다.
- **git_guard FAIL 단독**: 서비스/health 정상이면 DEGRADED (복구 급하지 않음).
- **mode_only**: `git checkout -- <file>` 로 해소 가능, 긴급 복구 불필요.

---

## A. git 이상 대응 템플릿

### 증상
- `ops_git_guard.sh` verdict FAIL / WARN
- working tree dirty (커밋되지 않은 변경 존재)
- HEAD != upstream (서버 HEAD 가 origin 과 다름)
- deploy 경로 기준 불일치 의심

### 1차 확인
```bash
cd /home/ubuntu/apps/risk-assessment-app/app

infra/ops_git_guard.sh          # git 상태 종합 점검
git status -sb                  # 변경 파일 목록
git rev-parse HEAD              # 서버 현재 커밋
git rev-parse @{u}              # upstream 커밋
git log --oneline -5            # 최근 커밋 흐름 확인
```

### 판정 기준
| 상태 | 판정 |
|------|------|
| `git status` 출력 없음 + HEAD == upstream | PASS |
| working tree dirty (서버 직접 수정 흔적) | WARN → 확인 후 조치 |
| HEAD != upstream (커밋 누락/초과) | WARN → pull 또는 재배포 필요 |
| 경로 자체 없거나 git repo 아님 | FAIL → 초기 clone 필요 |

### 조치 원칙
- 서버 직접 수정 흔적 먼저 확인 (`git diff`, `git status`) — 원인 파악 전 reset 금지
- 백업 없는 `git reset --hard` / `git clean -f` 금지
- 코드 수정은 로컬에서 수행 → `git push` → 서버 `git pull --ff-only` 우선

```bash
# 정상 배포 흐름 (로컬 → 서버)
git pull --ff-only              # 서버에서 실행
```

### 복구 후 검증
```bash
infra/ops_git_guard.sh
infra/ops_self_check.sh
curl http://127.0.0.1:8000/health
curl -o /dev/null -sw "%{http_code}\n" http://127.0.0.1
```

### 금지사항
- 서버에서 코드 직접 수정 금지
- `git reset --hard` / `git clean -f` 사전 확인 없이 실행 금지
- `scp` / `docker cp` 로 코드 배포 금지
- `/home/ubuntu/app/` (다른 앱 공유 디렉토리) 조작 금지

---

## B. 서비스 이상 대응 템플릿

### 증상
- `docker compose ps` 에서 컨테이너 비정상 (Exit / Restarting)
- `curl http://127.0.0.1:8000/health` 실패 또는 200 아님
- frontend HTTP 200 아님

### 1차 확인
```bash
cd /home/ubuntu/apps/risk-assessment-app/app/infra

infra/ops_self_check.sh                         # 경로·권한·스크립트 종합 점검
docker compose ps                               # 컨테이너 상태 전체 확인
docker compose logs --tail=50 risk-assessment-api   # API 오류 로그
docker compose logs --tail=50 risk-assessment-web   # frontend 오류 로그
curl http://127.0.0.1:8000/health               # API health 확인
curl -o /dev/null -sw "%{http_code}\n" http://127.0.0.1  # frontend HTTP 상태
```

### 판정 기준
| 상태 | 판정 |
|------|------|
| 전체 컨테이너 Up + health 200 + frontend 200 | PASS |
| 일부 컨테이너 Restarting / Exit 코드 존재 | WARN → 로그 확인 후 최소 재기동 |
| API health 비정상 + 로그 오류 | WARN → 원인 확인 후 조치 |
| 모든 컨테이너 Down | FAIL → compose up 후 검증 |

### 조치 원칙
- git 이상·경로·권한 문제를 먼저 배제한 뒤 컨테이너 조치
- 무작정 전체 재배포 (`--build`) 금지 — 필요한 서비스만 최소 범위 재기동
- `.env` 파일 존재·권한(600) 먼저 확인

```bash
# 필요한 서비스만 최소 재기동 (예: API 컨테이너만)
docker compose restart risk-assessment-api

# 전체 재기동이 불가피한 경우 (확인 후)
docker compose up -d
```

### 복구 후 검증
```bash
docker compose ps
infra/ops_self_check.sh
curl http://127.0.0.1:8000/health
curl -o /dev/null -sw "%{http_code}\n" http://127.0.0.1
```

### 금지사항
- 컨테이너 내부에서 파일 직접 수정 금지 (`docker exec` 로 코드 교체 금지)
- 원인 미확인 상태에서 `docker compose down && up --build` 금지
- 다른 앱 컨테이너 조작 금지
- `/home/ubuntu/app/` (다른 앱) 컨테이너 재기동 금지

---

## C. 데이터 복구 필요 대응 템플릿

### 증상
- `data/` 경로 손상·누락 의심
- 로그·설정 파일 유실 또는 비정상
- API 오류가 DB / 파일 접근 실패에서 기인하는 것으로 의심

### 1차 확인
```bash
cd /home/ubuntu/apps/risk-assessment-app/app/infra

infra/ops_backup_check.sh       # 백업 파일 존재·접근 점검
infra/ops_restore_rehearsal.sh  # 복구 가능 상태 종합 점검

# 최신 백업 파일 목록 확인
ls -lht /home/ubuntu/apps/risk-assessment-app/backups/data/   | head -5
ls -lht /home/ubuntu/apps/risk-assessment-app/backups/logs/   | head -5
ls -lht /home/ubuntu/apps/risk-assessment-app/backups/config/ | head -5

# 백업 무결성 확인 (압축 해제 금지, 목록만 확인)
tar -tzf /home/ubuntu/apps/risk-assessment-app/backups/data/<파일명>   | head -20
tar -tzf /home/ubuntu/apps/risk-assessment-app/backups/logs/<파일명>   | head -20
tar -tzf /home/ubuntu/apps/risk-assessment-app/backups/config/<파일명> | head -20
```

### 판정 기준
| 상태 | 판정 |
|------|------|
| 최신 백업 3종 존재 + tar 무결성 OK | PASS — 복구 가능 |
| 일부 category 백업 없음 | WARN — 가능한 범위만 복구 |
| 백업 파일 없거나 tar 손상 | FAIL — 대체 수단 확인 필요 |

### 실제 복구 전 준비
```bash
# 1. ops_restore_rehearsal.sh verdict PASS 확인 필수
infra/ops_restore_rehearsal.sh

# 2. 복구 범위 명확화 (data / logs / config 중 어느 범위만 복구할지 결정)

# 3. 현재 파일 임시 백업 (덮어쓰기 전 보존)
cp -a /home/ubuntu/apps/risk-assessment-app/data/ \
  /home/ubuntu/apps/risk-assessment-app/data_bak_$(date +%Y%m%d_%H%M%S)/

# 4. 복구 대상 tar 내부 경로 확인 (실제 압축 해제 전)
tar -tzf /home/ubuntu/apps/risk-assessment-app/backups/data/<파일명> | head -30
```

### 조치 원칙
- 코드는 git 으로만 복원 (`git pull --ff-only`) — 백업본으로 코드 덮어쓰기 금지
- data / logs / config 중 필요한 범위만 최소 복구
- 전체 루트 삭제 후 복구 금지
- tar 압축 해제 전 대상 경로 반드시 확인
- 다른 앱 경로 절대 금지

### 복구 후 검증
```bash
infra/ops_backup_check.sh
infra/ops_restore_rehearsal.sh
infra/ops_self_check.sh
curl http://127.0.0.1:8000/health
curl -o /dev/null -sw "%{http_code}\n" http://127.0.0.1
docker compose ps
```

### 금지사항
- `/home/ubuntu/apps/risk-assessment-app/` 전체 삭제 후 복구 금지
- git 추적 코드를 백업본으로 덮어쓰기 금지
- tar 압축 해제 전 대상 경로 확인 없이 실행 금지
- 다른 앱 디렉토리 침범 금지
- 컨테이너 내부 `docker exec` 로 파일 직접 교체 금지

---

## Action Matrix

> 이 매트릭스는 overall status · normalized verdict · 이벤트 이력을 종합해 **대응 등급**을 결정한다.
> 실제 자동 복구는 수행하지 않으며 대시보드 표시 및 운영자 판단 보조용으로만 사용한다.

### OBSERVE

**해당 조건**
- overall = HEALTHY
- overall = DEGRADED 이지만 noise 중심 (git_guard mode_only, 1회성 WARN)
- dirty_type=mode_only 만 존재
- 초기 백업/리허설 WARN (데이터 부족)
- 서비스 정상 + 반복성 없는 단발 WARN

**기본 대응**
- 상태 추적 유지
- 즉시 조치 없음

| 항목 | 값 |
|------|-----|
| approval needed | no |
| recommended next step | 상태 추적 유지, 즉시 조치 없음 |

---

### AUTO-RECOVERY-CANDIDATE

**해당 조건**
- API health 2회 연속 실패
- frontend HTTP 2회 연속 실패
- 특정 서비스(self_check)만 반복 FAIL (2회 이상)
- 서비스성 문제 반복 — git content 이상·data 손상·restore FAIL 없음

**기본 대응**
- 원인 로그 확인 후 최소 범위 재기동 후보
- 아직 자동 실행 금지 (사람이 판단)

| 항목 | 값 |
|------|-----|
| approval needed | no |
| recommended next step | 원인 확인 후 최소 범위 재기동 후보 |

---

### APPROVAL-REQUIRED

**해당 조건**
- git content dirty (mode_only 제외 실제 파일 변경)
- HEAD != upstream + 배포 불일치 의심
- data 복구 필요 (data 경로 손상·누락)
- backup_check 연속 FAIL 또는 restore_rehearsal FAIL
- 시크릿/권한 이상
- 복수 source(2개 이상) 동시 FAIL

**기본 대응**
- 대표님 승인 후 정렬/복구 절차 진행
- 단독 판단 조치 금지

| 항목 | 값 |
|------|-----|
| approval needed | yes |
| recommended next step | 대표님 승인 후 복구/정렬 절차 진행 |

---

### 우선순위 규칙 (충돌 시)

1. restore FAIL → APPROVAL-REQUIRED 우선
2. git content dirty → APPROVAL-REQUIRED 우선
3. 복수 source 동시 FAIL → APPROVAL-REQUIRED 우선
4. 서비스성 반복 FAIL (git/data 이상 없음) → AUTO-RECOVERY-CANDIDATE
5. mode_only WARN 만 존재 → OBSERVE (APPROVAL-REQUIRED 금지)
6. overall HEALTHY + noise 없음 → OBSERVE

---

## Action Catalog

> 각 Action class에서 다음에 실행할 구체적인 작업 후보 목록.
> 실제 자동 실행 금지 — 운영자 판단 후 수동 실행.

### OBS-001 상태 추적 유지

- **목적**: 현재 운영 상태가 정상 범위임을 기록하고 추이 모니터링 유지
- **사용 조건**: overall HEALTHY, 단발 WARN, mode_only noise
- **1차 확인**: 대시보드 Action Recommendation 카드 → OBSERVE 확인
- **금지사항**: 즉각 조치 시도 금지, 필요 없는 서비스 재기동 금지
- **후속 연결**: (조치 불필요 — 다음 scheduled check 대기)

### OBS-002 다음 scheduled check 결과 대기

- **목적**: 단발 WARN/FAIL 이 반복성 있는 문제인지 추가 데이터로 확인
- **사용 조건**: 1회성 WARN 또는 noise 성 이벤트 직후
- **1차 확인**: 이력 블록 — 24시간 요약 P/W/F 카운트 추세 확인
- **금지사항**: 결과 미확인 상태에서 선제적 재기동 금지
- **후속 연결**: FAIL 반복 확인 시 → ARC-001 또는 APR 계열로 전환

### OBS-003 recent events 24h 추세 확인

- **목적**: 최근 이벤트 10개를 보고 source별 패턴 유무 판단
- **사용 조건**: OBSERVE 중 주기적 리뷰
- **1차 확인**: 대시보드 "최근 이벤트 10개 (normalized)" 블록
- **금지사항**: 패턴 없는 이벤트를 근거로 복구 절차 진입 금지
- **후속 연결**: 반복 패턴 발견 시 → ARC 또는 APR 계열 재평가

---

### ARC-001 최소 범위 재기동 후보 검토

- **목적**: 서비스성 반복 FAIL 원인을 파악하고 최소 범위 재기동 여부 결정
- **사용 조건**: self_check 2회 연속 FAIL, git/data 이상 없음
- **1차 확인**:
  ```bash
  docker compose ps
  docker compose logs --tail=50 risk-assessment-api
  docker compose logs --tail=50 risk-assessment-web
  curl http://127.0.0.1:8000/health
  ```
- **금지사항**: 원인 미확인 상태에서 전체 재배포(`--build`) 금지, 다른 앱 컨테이너 금지
- **후속 연결**: 서비스 이상 대응 템플릿 (§ B)

### ARC-002 docker compose ps / health 재확인

- **목적**: 현재 컨테이너 상태와 API health 를 다시 확인해 FAIL 지속 여부 판단
- **사용 조건**: ARC-001 진행 중 또는 직후
- **1차 확인**:
  ```bash
  docker compose ps
  curl http://127.0.0.1:8000/health
  curl -o /dev/null -sw "%{http_code}\n" http://127.0.0.1
  ```
- **금지사항**: health 재확인 없이 재기동 실행 금지
- **후속 연결**: FAIL 지속 시 → ARC-003 → 단일 서비스 재기동 후보 결정

### ARC-003 최근 로그 비교 후 단일 서비스 문제 여부 판단

- **목적**: 로그에서 반복 오류 패턴 확인 → 재기동 대상 서비스를 최소화
- **사용 조건**: ARC-002 이후 FAIL 지속 확인된 경우
- **1차 확인**:
  ```bash
  docker compose logs --tail=100 risk-assessment-api | grep -i error
  docker compose logs --tail=100 risk-assessment-web | grep -i error
  ```
- **금지사항**: 전체 컨테이너 동시 재기동 금지, 원인 불명 상태에서 `--build` 금지
- **후속 연결**: 단일 서비스 재기동 결정 시 → 서비스 이상 대응 템플릿 (§ B)

---

### APR-001 git 정렬 복구 계획 작성

- **목적**: git content dirty / HEAD 불일치 원인 파악 및 복구 계획 문서화
- **사용 조건**: git content dirty (mode_only 제외), HEAD != upstream 의심
- **1차 확인**:
  ```bash
  git status -sb
  git diff
  git rev-parse HEAD
  git rev-parse @{u}
  git log --oneline -5
  ```
- **금지사항**: 원인 확인 전 `git reset --hard` 금지, 백업 없는 `git clean -f` 금지
- **후속 연결**: git 이상 대응 템플릿 (§ A)

### APR-002 데이터 복구 범위 확정

- **목적**: data 손상·누락 범위를 특정하고 최소 복구 범위를 결정
- **사용 조건**: data 경로 손상 의심, API 오류가 DB/파일 접근 실패에서 기인
- **1차 확인**:
  ```bash
  ls -lh /home/ubuntu/apps/risk-assessment-app/data/
  infra/ops_backup_check.sh
  infra/ops_restore_rehearsal.sh
  ```
- **금지사항**: 전체 루트 삭제 후 복구 금지, git 추적 코드를 백업으로 덮어쓰기 금지
- **후속 연결**: 데이터 복구 대응 템플릿 (§ C)

### APR-003 backup/restore 무결성 재확인

- **목적**: 백업 파일 존재·압축 무결성을 검증해 복구 가능 상태 확인
- **사용 조건**: backup_check FAIL, restore_rehearsal FAIL, 또는 복구 전 사전 검증
- **1차 확인**:
  ```bash
  infra/ops_backup_check.sh
  infra/ops_restore_rehearsal.sh
  ls -lht /home/ubuntu/apps/risk-assessment-app/backups/data/ | head -5
  tar -tzf <최신 백업 파일> | head -20
  ```
- **금지사항**: 무결성 확인 전 실제 tar 압축 해제 금지
- **후속 연결**: 데이터 복구 대응 템플릿 (§ C)

### APR-004 대표님 승인 후 실행 단계로 전환

- **목적**: APPROVAL-REQUIRED 조건에서 복구/정렬 실행 전 승인 획득
- **사용 조건**: APR-001 / APR-002 / APR-003 완료 후 실행 전
- **1차 확인**: 복구 계획 · 범위 · 영향도 정리 → 대표님께 보고
- **금지사항**: 승인 없이 복구·정렬 실행 금지, 다른 앱 범위 포함 금지
- **후속 연결**: 승인 완료 시 → 해당 복구 템플릿 (§ A / § B / § C) 실행

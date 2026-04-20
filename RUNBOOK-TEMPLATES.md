# risk-assessment-app 장애 유형별 실행 템플릿

> 실제 복구 전 반드시 `infra/ops_restore_rehearsal.sh` 로 복구 가능 상태를 확인한다.
> 상세 runbook 은 README.md `## risk-assessment-app 장애 대응 / 복구 리허설 Runbook` 참조.

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

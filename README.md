# 위험성평가표 자동생성기

KRAS 표준 양식 기반 위험성평가표 웹 자동생성 서비스

- 도메인: https://kras.haehan-ai.kr
- 저장소: risk-assessment-generator

## 서비스 구성

| 컨테이너 | 역할 |
|----------|------|
| risk-assessment-api | FastAPI 백엔드 |
| risk-assessment-web | React 프론트엔드 |
| risk-assessment-db  | PostgreSQL |

## risk-assessment-app 운영 표준

- 관리 루트: `/home/ubuntu/apps/risk-assessment-app`
- git 저장소: `/home/ubuntu/apps/risk-assessment-app/app`
- compose 경로: `/home/ubuntu/apps/risk-assessment-app/app/infra`
- 표준 디렉토리: `app/`, `data/`, `logs/`, `backups/`

### 배포 원칙
1. 코드 수정은 로컬에서만 수행한다.
2. 반영은 `git commit` → `git push` → 서버 `git pull --ff-only` 순서로 수행한다.
3. 서버는 작업장이 아니라 배포 결과물로 유지한다.
4. 필요 시 `docker compose` 재기동 후 health 를 확인한다.

### 금지 사항
- 서버에서 코드 직접 수정 금지
- `scp` 금지
- `docker cp` 금지
- 컨테이너 내부 직접 수정 금지

### 주의
- `/home/ubuntu/app/` 는 다른 앱 공유 디렉토리이므로 전체 삭제/수정 금지
- 과거 경로(`/home/ubuntu/app/risk-assessment-generator`, `/mnt/risk-assessment-data`, `/mnt/risk-assessment-logs`)는 현재 운영 표준 경로가 아니다

## 배포 절차

```bash
# 1. 로컬 수정 후 GitHub push
git add .
git commit -m "변경내용"
git push origin master

# 2. 서버 접속
ssh -i ~/.ssh/haehan-ai.pem ubuntu@1.201.176.236

# 3. 서버에서 배포 실행
cd /home/ubuntu/apps/risk-assessment-app/app
bash infra/deploy.sh
```

## 개발 로그 관리 규칙

코드 수정 시 아래 3가지를 함께 관리한다.

| 축 | 위치 | 목적 |
|----|------|------|
| 작업일지 | `docs/devlog/YYYY-MM-DD_작업명.md` | 변경 이유·시도·검증 기록 |
| 변경 이력 | `logs/change_history.jsonl` | 커밋과 작업일지 연결 |
| 실행 로그 | 서버 `~/kosha_scraper/logs/` | 스크립트 실행 결과 |

**작업 절차**

```
1. 기능 수정 전 → docs/devlog/ 에 작업일지 초안 작성
2. 코드 수정 → git commit (커밋 메시지에 목적 명시)
3. 커밋 후 → logs/change_history.jsonl 에 1줄 append
4. 데이터 변환 작업 → 서버 실행 로그 별도 보관 (kosha_scraper/logs/)
```

**change_history.jsonl 항목 형식**

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SS+09:00",
  "task_name": "작업명",
  "changed_files": ["경로1", "경로2"],
  "summary": "한 줄 요약",
  "result": "검증 결과",
  "commit_hash": "git short hash",
  "devlog": "docs/devlog/파일명.md"
}
```

## risk-assessment-app 백업/복구 표준

### 백업 대상
- `/home/ubuntu/apps/risk-assessment-app/data/` — DB 볼륨 및 운영 데이터
- `/home/ubuntu/apps/risk-assessment-app/backups/` — 운영 산출물 (pg_dump 등)
- 운영상 필요한 로그만 선별 백업 (`logs/*.log`, `logs/*.jsonl`)
- `infra/.env` — git 미추적 민감 설정 (별도 보관 필수, 기밀 취급)

### 백업 제외
- git으로 복원 가능한 코드 전체 (`app/`)
- 캐시·빌드 산출물·임시 파일 (`node_modules`, `.venv`, `__pycache__`, `dist/`)
- 중복 백업 파일

### 기본 원칙
1. 코드는 git으로 복원한다.
2. 운영 데이터는 `data/` 중심으로 백업한다.
3. 복구는 전체 삭제가 아니라 필요한 범위만 최소 복구한다.
4. 복구 후 반드시 health / frontend / self-check 로 검증한다.

### 정기 백업 자동화

| 항목 | 내용 |
|------|------|
| 스크립트 | `infra/ops_backup_rotate.sh` |
| 실행 주기 | 매일 08:40 (cron) |
| 로그 | `logs/backup_rotate.log`, `logs/backup_rotate_cron.log` |
| 보관 정책 | data 최근 7개 / logs 최근 14개 / config 최근 7개 |
| 복구 시 | 최신 정상 백업 우선 사용 |

### 수동 백업 명령 예시

```bash
# DB dump (컨테이너 내부 pg_dump → backups/)
BACKUP_DIR=/home/ubuntu/apps/risk-assessment-app/backups
DATE=$(date +%Y%m%d_%H%M%S)
docker exec risk-assessment-db pg_dump -U postgres kras \
  | gzip > "${BACKUP_DIR}/kras_${DATE}.sql.gz"

# data/ 전체 rsync (원격 스토리지 또는 다른 경로)
rsync -a /home/ubuntu/apps/risk-assessment-app/data/ \
  <BACKUP_DEST>/risk-assessment-data/
```

### 복구 전 확인사항
- `docker compose ps` — 컨테이너 상태 확인
- 복구 대상 파일 무결성 확인 (`md5sum`, `gzip -t`)
- 코드 복구는 git 으로만 수행 (`git pull --ff-only`)
- `.env` 파일 존재 여부 확인

### 복구 후 검증 항목
- `docker compose ps` — 전체 컨테이너 Running 확인
- `curl http://127.0.0.1:8000/health` — API health 200
- frontend HTTP 200 확인
- `infra/ops_self_check.sh` 실행 → verdict PASS
- `infra/ops_git_guard.sh` 실행 → verdict PASS
- `infra/ops_backup_check.sh` 실행 → verdict PASS

### 금지사항
- 전체 루트(`/home/ubuntu/apps/risk-assessment-app/`) 삭제 후 복구 금지
- 다른 앱 경로 복구 금지
- git 추적 코드를 백업본으로 덮어쓰기 금지
- 컨테이너 내부 수동 복구 금지 (`docker exec` 로 파일 직접 교체 금지)

---

## 초기 서버 설정 (최초 1회)

```bash
git clone https://github.com/JAY-1979-SJW/risk-assessment-generator.git \
  /home/ubuntu/apps/risk-assessment-app/app
cd /home/ubuntu/apps/risk-assessment-app/app/infra
cp .env.example .env
# .env 파일에서 비밀번호 변경 후 저장
docker compose --env-file .env up -d --build
```

#!/bin/bash
set -euo pipefail

DRY_RUN=true
EXECUTE=false
HOST=""
USER="ubuntu"
APP_DIR="/home/ubuntu/apps/risk-assessment-app"
BRANCH="master"
RESTART=false
HEALTH=false

print_usage() {
  cat <<EOF
usage: server_git_pull_deploy.sh [OPTIONS]

옵션:
  --dry-run              실행할 명령 출력만 수행, 실제 ssh 미실행 (기본값)
  --execute              실제 서버 배포 실행 (필수: --host와 --user)
  --host HOST            배포 대상 서버 호스트 (필수)
  --user USER            서버 접속 사용자 (기본값: ubuntu)
  --app-dir PATH         앱 디렉토리 (기본값: /home/ubuntu/apps/risk-assessment-app)
  --branch BRANCH        git branch (기본값: master)
  --restart              배포 후 docker compose up -d 실행
  --health               배포 후 docker compose ps 실행
  --help                 이 메시지 출력

예시:
  # dry-run: 명령만 출력
  ./scripts/ops/server_git_pull_deploy.sh --dry-run --host 1.201.176.236 --user ubuntu

  # 실제 배포 (--execute 필수)
  ./scripts/ops/server_git_pull_deploy.sh --execute --host 1.201.176.236 --user ubuntu --branch master --restart --health

EOF
}

log_status() {
  echo "[STATUS] $1"
}

log_section() {
  echo ""
  echo "===================================================================="
  echo "[$1]"
  echo "===================================================================="
}

log_pass() {
  echo "  ✓ $1"
}

log_fail() {
  echo "  ✗ $1"
  exit 1
}

log_warn() {
  echo "  ⚠ $1"
}

log_info() {
  echo "  ℹ $1"
}

log_cmd() {
  echo "  $ $1"
}

# 옵션 파싱
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      EXECUTE=false
      shift
      ;;
    --execute)
      EXECUTE=true
      DRY_RUN=false
      shift
      ;;
    --host)
      HOST="$2"
      shift 2
      ;;
    --user)
      USER="$2"
      shift 2
      ;;
    --app-dir)
      APP_DIR="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --restart)
      RESTART=true
      shift
      ;;
    --health)
      HEALTH=true
      shift
      ;;
    --help)
      print_usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      print_usage
      exit 1
      ;;
  esac
done

# 검증
log_section "CONFIGURATION"

if [[ -z "$HOST" ]]; then
  log_fail "--host 필수 (배포 대상 서버)"
fi

log_pass "호스트: $HOST"
log_pass "사용자: $USER"
log_pass "앱 디렉토리: $APP_DIR"
log_pass "브랜치: $BRANCH"

if [[ "$RESTART" == "true" ]]; then
  log_info "docker compose up -d 활성화"
fi

if [[ "$HEALTH" == "true" ]]; then
  log_info "docker compose ps 활성화"
fi

if [[ "$EXECUTE" == "true" ]]; then
  log_warn "실행 모드: 실제 서버에 접속하여 배포 진행"
else
  log_info "dry-run 모드: 실행할 명령만 출력 (실제 ssh 미실행)"
fi

# 서버 명령 구성
log_section "DEPLOY COMMANDS"

# 핵심 명령: git pull --ff-only만 사용
SERVER_COMMANDS=(
  "cd $APP_DIR"
  "git status --short"
  "git fetch origin"
  "git pull --ff-only origin $BRANCH"
  "git rev-parse --short HEAD"
  "docker compose ps"
)

# 선택 명령
if [[ "$RESTART" == "true" ]]; then
  SERVER_COMMANDS+=("docker compose up -d")
fi

log_info "실행할 서버 명령:"
for cmd in "${SERVER_COMMANDS[@]}"; do
  log_cmd "$cmd"
done

# Dry-run 종료
if [[ "$DRY_RUN" == "true" ]]; then
  log_section "DRY-RUN SUMMARY"
  log_pass "명령 구성 완료"
  log_info "실제 배포를 진행하려면:"
  log_info "  ./scripts/ops/server_git_pull_deploy.sh --execute --host $HOST --user $USER --branch $BRANCH"
  if [[ "$RESTART" == "true" ]]; then
    log_info "    --restart"
  fi
  if [[ "$HEALTH" == "true" ]]; then
    log_info "    --health"
  fi
  exit 0
fi

# 실제 ssh 실행
log_section "EXECUTING REMOTE COMMANDS"

# ssh 접속 명령 구성
SSH_USER_HOST="${USER}@${HOST}"
FULL_COMMAND=""

for cmd in "${SERVER_COMMANDS[@]}"; do
  if [[ -z "$FULL_COMMAND" ]]; then
    FULL_COMMAND="$cmd"
  else
    FULL_COMMAND="$FULL_COMMAND; $cmd"
  fi
done

log_info "ssh 접속: ssh $SSH_USER_HOST"
log_info "원격 명령 실행 중..."

# SSH 실행 (에러 처리)
if ssh "$SSH_USER_HOST" bash -c "$FULL_COMMAND"; then
  log_section "RESULT"
  log_pass "서버 배포 완료"
  log_info "호스트: $HOST"
  log_info "브랜치: $BRANCH"
  log_info "앱 디렉토리: $APP_DIR"

  if [[ "$RESTART" == "true" ]]; then
    log_pass "docker compose up -d 실행 완료"
  fi

  if [[ "$HEALTH" == "true" ]]; then
    log_info "docker compose ps 확인 완료"
  fi

  exit 0
else
  log_section "RESULT"
  log_fail "서버 배포 실패 — 위 출력 확인"
fi

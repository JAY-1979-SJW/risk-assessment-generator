#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/ubuntu/apps/risk-assessment-app/app"
LOG_FILE="/home/ubuntu/apps/risk-assessment-app/logs/git_guard.log"
TS=$(date "+%Y-%m-%d %H:%M:%S")

cd "$APP_DIR"

# 상태 수집
BRANCH=$(git branch --show-current)
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "NONE")
HEAD=$(git rev-parse HEAD)
UP_HEAD=$(git rev-parse @{u} 2>/dev/null || echo "NONE")
STATUS=$(git status --porcelain)
AHEAD_BEHIND=$(git status -sb | grep -Eo "\[.*\]" || echo "")

# 판정
VERDICT="PASS"

if [ -n "$STATUS" ]; then
  VERDICT="FAIL"
fi

if [ "$HEAD" != "$UP_HEAD" ]; then
  VERDICT="WARN"
fi

# 로그 기록
mkdir -p "$(dirname "$LOG_FILE")"
echo "[$TS] verdict=$VERDICT branch=$BRANCH head=$HEAD upstream=$UP_HEAD status_len=${#STATUS} $AHEAD_BEHIND" >> "$LOG_FILE"

# 콘솔 출력
echo "verdict=$VERDICT"
echo "branch=$BRANCH"
echo "head=$HEAD"
echo "upstream=$UP_HEAD"

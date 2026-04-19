#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/ubuntu/apps/risk-assessment-app/app"
LOG_FILE="/home/ubuntu/apps/risk-assessment-app/logs/git_guard.log"
STATE_FILE="/home/ubuntu/apps/risk-assessment-app/logs/git_guard.state"
SECRETS_FILE="${HOME}/.config/ops/telegram.secrets"
TS=$(date "+%Y-%m-%d %H:%M:%S")
SUPPRESS_SECS=1800  # 동일 verdict 30분 중복 억제

# ── 텔레그램 전송 ──────────────────────────────────────────────────────────────
_send_telegram() {
  local msg="$1"
  local token chat_id
  token=$(grep '^TELEGRAM_BOT_TOKEN=' "$SECRETS_FILE" 2>/dev/null | cut -d= -f2-)
  chat_id=$(grep '^TELEGRAM_CHAT_ID=' "$SECRETS_FILE" 2>/dev/null | cut -d= -f2-)
  [ -z "$token" ] || [ -z "$chat_id" ] && { echo "[warn] telegram secrets 없음, 전송 생략"; return 0; }
  curl -s -X POST "https://api.telegram.org/bot${token}/sendMessage" \
    -d "chat_id=${chat_id}" \
    --data-urlencode "text=${msg}" \
    >/dev/null 2>&1
}

# ── 중복 억제 판단 ─────────────────────────────────────────────────────────────
# state 파일 형식: "<verdict> <epoch>"
_should_send() {
  local verdict="$1"
  [ "$verdict" = "PASS" ] && return 1  # PASS는 항상 전송 안 함
  if [ -f "$STATE_FILE" ]; then
    local prev_verdict prev_ts now
    prev_verdict=$(awk '{print $1}' "$STATE_FILE" 2>/dev/null || echo "")
    prev_ts=$(awk '{print $2}' "$STATE_FILE" 2>/dev/null || echo "0")
    now=$(date +%s)
    if [ "$prev_verdict" = "$verdict" ] && [ $(( now - prev_ts )) -lt $SUPPRESS_SECS ]; then
      return 1  # 동일 verdict, 30분 미경과 → 억제
    fi
  fi
  return 0  # 전송
}

# ── 테스트 모드 ────────────────────────────────────────────────────────────────
TEST_OVERRIDE=""
if [ "${1:-}" = "--test-warn" ]; then
  TEST_OVERRIDE="WARN"
elif [ "${1:-}" = "--test-fail" ]; then
  TEST_OVERRIDE="FAIL"
fi

# ── git 상태 수집 ──────────────────────────────────────────────────────────────
cd "$APP_DIR"
BRANCH=$(git branch --show-current)
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "NONE")
HEAD=$(git rev-parse HEAD)
UP_HEAD=$(git rev-parse @{u} 2>/dev/null || echo "NONE")
STATUS=$(git status --porcelain)
AHEAD_BEHIND=$(git status -sb | grep -Eo "\[.*\]" || echo "")

# ── 판정 ───────────────────────────────────────────────────────────────────────
VERDICT="PASS"
if [ -n "$STATUS" ]; then
  VERDICT="FAIL"
fi
if [ "$HEAD" != "$UP_HEAD" ]; then
  VERDICT="WARN"
fi

# 테스트 모드 override
if [ -n "$TEST_OVERRIDE" ]; then
  VERDICT="$TEST_OVERRIDE"
fi

# ── 로그 기록 ──────────────────────────────────────────────────────────────────
mkdir -p "$(dirname "$LOG_FILE")"
echo "[$TS] verdict=$VERDICT branch=$BRANCH head=$HEAD upstream=$UP_HEAD status_len=${#STATUS} $AHEAD_BEHIND${TEST_OVERRIDE:+ [TEST]}" >> "$LOG_FILE"

# ── 콘솔 출력 ─────────────────────────────────────────────────────────────────
echo "verdict=$VERDICT"
echo "branch=$BRANCH"
echo "head=$HEAD"
echo "upstream=$UP_HEAD"

# ── 텔레그램 알림 (WARN/FAIL만) ───────────────────────────────────────────────
if _should_send "$VERDICT"; then
  MSG="[risk-assessment-app git-guard ${VERDICT}]
시각: ${TS}
branch: ${BRANCH}
head:   ${HEAD:0:12}
upstream: ${UP_HEAD:0:12}
dirty files: ${#STATUS}자
경로: ${APP_DIR}
${AHEAD_BEHIND}${TEST_OVERRIDE:+
※ TEST MODE}"
  _send_telegram "$MSG"
  echo "$VERDICT $(date +%s)" > "$STATE_FILE"
  echo "telegram: sent"
else
  echo "telegram: suppressed (verdict=$VERDICT)"
fi

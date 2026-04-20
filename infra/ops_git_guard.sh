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

# ── dirty_type 탐지 (content / mode_only / none) ─────────────────────────────
if [ -z "$STATUS" ]; then
  DIRTY_TYPE="none"
else
  # content 변경(줄 추가/삭제)이 있으면 content, 없으면 mode_only
  CONTENT_LINES=$(git diff 2>/dev/null | grep -cE '^[+\-][^+\-]' 2>/dev/null || echo 0)
  if [ "${CONTENT_LINES:-0}" -gt 0 ]; then
    DIRTY_TYPE="content"
  else
    DIRTY_TYPE="mode_only"
  fi
fi

# ── 판정 ───────────────────────────────────────────────────────────────────────
VERDICT="PASS"
if [ -n "$STATUS" ]; then
  # mode-only 변경(chmod 등)은 WARN, content 변경은 FAIL
  if [ "$DIRTY_TYPE" = "mode_only" ]; then
    VERDICT="WARN"
  else
    VERDICT="FAIL"
  fi
fi
if [ "$HEAD" != "$UP_HEAD" ] && [ "$VERDICT" != "FAIL" ]; then
  VERDICT="WARN"
fi

# 테스트 모드 override
if [ -n "$TEST_OVERRIDE" ]; then
  VERDICT="$TEST_OVERRIDE"
fi

# ── 권한 감시 (로그만, 자동 수정 금지) ───────────────────────────────────────
PERM_WARNS=""
_check_perm() {
  local path="$1" expected="$2" label="$3"
  [ -e "$path" ] || return 0
  local actual
  actual=$(stat -c "%a" "$path" 2>/dev/null || echo "")
  if [ "$actual" != "$expected" ]; then
    PERM_WARNS="${PERM_WARNS}perm-warn: ${label} mode=${actual} expected=${expected}; "
  fi
}

_check_perm "${HOME}/.config/ops/telegram.secrets"             "600" "telegram.secrets"
_check_perm "${APP_DIR}/infra/.env"                            "600" "app infra/.env"
_check_perm "/home/ubuntu/app/repo.bak.20260418"               "700" "repo.bak dir"

# .env 파일 권한 체크 (infra 디렉토리 내, .example 제외)
for f in "${APP_DIR}"/infra/.env "${APP_DIR}"/infra/.env.*; do
  [[ "$f" == *.example ]] && continue
  [ -f "$f" ] && _check_perm "$f" "600" "$(basename "$f")"
done

# 권한 이탈 감지 시 WARN 격상
if [ -n "$PERM_WARNS" ] && [ "$VERDICT" = "PASS" ]; then
  VERDICT="WARN"
fi

# ── 로그 기록 ──────────────────────────────────────────────────────────────────
mkdir -p "$(dirname "$LOG_FILE")"
LOG_LINE="[$TS] verdict=$VERDICT branch=$BRANCH head=$HEAD upstream=$UP_HEAD status_len=${#STATUS} $AHEAD_BEHIND${TEST_OVERRIDE:+ [TEST]}${PERM_WARNS:+ | $PERM_WARNS}"
echo "$LOG_LINE" >> "$LOG_FILE"

# ── 대시보드용 .last + history 갱신 ──────────────────────────────────────────
STATUS_DIR="/home/ubuntu/app/nginx/webroot/status/risk-assessment/data"
mkdir -p "$STATUS_DIR"
echo "$LOG_LINE" > "$STATUS_DIR/git_guard.last" 2>/dev/null || true

TS_ISO=$(date +%Y-%m-%dT%H:%M:%S+09:00)
HIST_SUMMARY="branch=${BRANCH} head=${HEAD:0:8} upstream=${UP_HEAD:0:8} dirty_type=${DIRTY_TYPE}"
HIST_FILE="$STATUS_DIR/git_guard.history.jsonl"
printf '{"ts":"%s","source":"git_guard","verdict":"%s","summary":"%s"}\n' \
    "$TS_ISO" "$VERDICT" "$HIST_SUMMARY" >> "$HIST_FILE" 2>/dev/null || true
if [ "$(wc -l < "$HIST_FILE" 2>/dev/null || echo 0)" -gt 1000 ]; then
    tail -n 1000 "$HIST_FILE" > "${HIST_FILE}.tmp" && mv "${HIST_FILE}.tmp" "$HIST_FILE" || true
fi

# ── 콘솔 출력 ─────────────────────────────────────────────────────────────────
echo "verdict=$VERDICT"
echo "branch=$BRANCH"
echo "head=$HEAD"
echo "upstream=$UP_HEAD"
[ -n "$PERM_WARNS" ] && echo "perm-warns: $PERM_WARNS"

# ── 텔레그램 알림 (WARN/FAIL만) ───────────────────────────────────────────────
if _should_send "$VERDICT"; then
  MSG="[risk-assessment-app git-guard ${VERDICT}]
시각: ${TS}
branch: ${BRANCH}
head:   ${HEAD:0:12}
upstream: ${UP_HEAD:0:12}
dirty files: ${#STATUS}자
경로: ${APP_DIR}
${AHEAD_BEHIND}${PERM_WARNS:+
권한경고: ${PERM_WARNS}}${TEST_OVERRIDE:+
※ TEST MODE}"
  _send_telegram "$MSG"
  echo "$VERDICT $(date +%s)" > "$STATE_FILE"
  echo "telegram: sent"
else
  echo "telegram: suppressed (verdict=$VERDICT)"
fi

#!/usr/bin/env bash
set -euo pipefail

# risk-assessment-app 운영 표준 자가점검
# 읽기 전용 — 자동 수정 금지

APP_ROOT="/home/ubuntu/apps/risk-assessment-app"
APP_DIR="${APP_ROOT}/app"
LOG_FILE="${APP_ROOT}/logs/self_check.log"
COMPOSE="${APP_DIR}/infra/docker-compose.yml"
SECRETS_FILE="${HOME}/.config/ops/telegram.secrets"
API_URL="http://localhost:8100"
WEB_URL="http://localhost:8101"
TS=$(date "+%Y-%m-%d %H:%M:%S")

mkdir -p "${APP_ROOT}/logs"

# ── 점검 결과 누적 ─────────────────────────────────────────────────────────────
GIT_R="PASS"; PATH_R="PASS"; PERM_R="PASS"; SVC_R="PASS"; DOCS_R="PASS"
DETAIL=""

_warn()  { local section="$1"; eval "${section}_R=WARN"; DETAIL="${DETAIL} [$section:WARN] $2;"; }
_fail()  { local section="$1"; eval "${section}_R=FAIL"; DETAIL="${DETAIL} [$section:FAIL] $2;"; }
_note()  { DETAIL="${DETAIL} [$1:INFO] $2;"; }

# ── A. git 상태 ────────────────────────────────────────────────────────────────
cd "$APP_DIR"
GIT_STATUS=$(git status --porcelain 2>/dev/null || echo "ERROR")
GIT_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "NONE")
GIT_UP=$(git rev-parse @{u} 2>/dev/null || echo "NONE")

if [ "$GIT_STATUS" = "ERROR" ]; then
  _fail GIT "git 명령 실패"
elif [ -n "$GIT_STATUS" ]; then
  _fail GIT "working tree dirty"
fi

if [ "$GIT_HEAD" != "$GIT_UP" ]; then
  _warn GIT "HEAD != upstream (head=${GIT_HEAD:0:8} up=${GIT_UP:0:8})"
fi

# ── B. 경로 구조 ───────────────────────────────────────────────────────────────
for dir in app data logs backups; do
  if [ ! -d "${APP_ROOT}/${dir}" ]; then
    _fail PATH "${APP_ROOT}/${dir} 없음"
  fi
done

if [ ! -f "$COMPOSE" ]; then
  _fail PATH "compose 파일 없음: $COMPOSE"
fi

# ── C. 권한 ────────────────────────────────────────────────────────────────────
if [ ! -f "$SECRETS_FILE" ]; then
  _fail PERM "telegram.secrets 파일 없음"
else
  PERM=$(stat -c "%a" "$SECRETS_FILE" 2>/dev/null || echo "")
  if [ "$PERM" != "600" ]; then
    _fail PERM "telegram.secrets mode=${PERM} (expected 600)"
  fi
fi

if [ ! -w "${APP_ROOT}/logs" ]; then
  _warn PERM "logs 디렉토리 쓰기 불가"
fi

# ── D. 서비스 상태 ────────────────────────────────────────────────────────────
# docker compose ps — 컨테이너 상태
for svc in risk-assessment-api risk-assessment-db risk-assessment-web; do
  STATE=$(docker ps --filter "name=^${svc}$" --format "{{.Status}}" 2>/dev/null || echo "")
  if [ -z "$STATE" ]; then
    _fail SVC "${svc} 컨테이너 없음"
  elif echo "$STATE" | grep -qiE 'unhealthy|exited|restarting'; then
    _fail SVC "${svc} 비정상: $STATE"
  fi
done

# API health
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${API_URL}/health" 2>/dev/null || echo "000")
if [ "$API_CODE" != "200" ]; then
  _fail SVC "API health HTTP ${API_CODE} (expected 200)"
fi

# frontend
WEB_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${WEB_URL}" 2>/dev/null || echo "000")
if [ "$WEB_CODE" != "200" ]; then
  _warn SVC "frontend HTTP ${WEB_CODE} (expected 200)"
fi

# ── E. 문서 기준 ──────────────────────────────────────────────────────────────
README="${APP_DIR}/README.md"
if [ ! -f "$README" ]; then
  _warn DOCS "README.md 없음"
else
  grep -q '/home/ubuntu/apps/risk-assessment-app' "$README" || _warn DOCS "README에 관리 루트 경로 없음"
  grep -q 'git pull --ff-only' "$README"                    || _warn DOCS "README에 git pull --ff-only 없음"
  grep -qE 'scp 금지|docker cp 금지|scp.*금지|docker cp.*금지' "$README" || _warn DOCS "README에 금지 사항 없음"
fi

# ── 최종 verdict ──────────────────────────────────────────────────────────────
VERDICT="PASS"
for r in "$GIT_R" "$PATH_R" "$PERM_R" "$SVC_R" "$DOCS_R"; do
  [ "$r" = "FAIL" ] && VERDICT="FAIL" && break
  [ "$r" = "WARN" ] && VERDICT="WARN"
done

# ── 로그 기록 ─────────────────────────────────────────────────────────────────
LOG_LINE="[$TS] git=${GIT_R} path=${PATH_R} perms=${PERM_R} services=${SVC_R} docs=${DOCS_R} verdict=${VERDICT}${DETAIL:+ |${DETAIL}}"
echo "$LOG_LINE" >> "$LOG_FILE"

# ── 대시보드용 .last 갱신 ─────────────────────────────────────────────────────
STATUS_DIR="/home/ubuntu/app/nginx/webroot/status/risk-assessment/data"
mkdir -p "$STATUS_DIR"
echo "$LOG_LINE" > "$STATUS_DIR/self_check.last" 2>/dev/null || true

# ── 콘솔 출력 ────────────────────────────────────────────────────────────────
echo "[$TS]"
echo "  git      : $GIT_R"
echo "  path     : $PATH_R"
echo "  perms    : $PERM_R"
echo "  services : $SVC_R"
echo "  docs     : $DOCS_R"
echo "  verdict  : $VERDICT"
[ -n "$DETAIL" ] && echo "  detail   :$DETAIL"

[ "$VERDICT" = "PASS" ] && exit 0 || exit 1

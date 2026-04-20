#!/usr/bin/env bash
set -euo pipefail

# risk-assessment-app 백업 대상 점검
# 읽기/점검 전용 — 자동 백업·자동 삭제 금지

APP_ROOT="/home/ubuntu/apps/risk-assessment-app"
APP_DIR="${APP_ROOT}/app"
BACKUP_DIR="${APP_ROOT}/backups"
DATA_DIR="${APP_ROOT}/data"
LOG_DIR="${APP_ROOT}/logs"
LOG_FILE="${LOG_DIR}/backup_check.log"
COMPOSE="${APP_DIR}/infra/docker-compose.yml"
TS=$(date "+%Y-%m-%d %H:%M:%S")

mkdir -p "${LOG_DIR}"

# ── 결과 변수 ─────────────────────────────────────────────────────────────────
BACKUP_R="PASS"; DATA_R="PASS"; COMPOSE_R="PASS"
SCRIPTS_R="PASS"; RECENT_R="PASS"
DETAIL=""

_warn() { local s="$1"; eval "${s}_R=WARN"; DETAIL="${DETAIL} [${s}:WARN] $2;"; }
_fail() { local s="$1"; eval "${s}_R=FAIL"; DETAIL="${DETAIL} [${s}:FAIL] $2;"; }

# ── A. backups 경로 존재 및 쓰기 가능 ────────────────────────────────────────
if [ ! -d "${BACKUP_DIR}" ]; then
  _fail BACKUP "${BACKUP_DIR} 없음"
elif [ ! -w "${BACKUP_DIR}" ]; then
  _fail BACKUP "${BACKUP_DIR} 쓰기 불가"
fi

# ── B. data 경로 접근 가능 ────────────────────────────────────────────────────
if [ ! -d "${DATA_DIR}" ]; then
  _fail DATA "${DATA_DIR} 없음"
elif [ ! -r "${DATA_DIR}" ]; then
  _fail DATA "${DATA_DIR} 읽기 불가"
fi

# ── C. compose 파일 존재 ─────────────────────────────────────────────────────
if [ ! -f "${COMPOSE}" ]; then
  _fail COMPOSE "compose 파일 없음: ${COMPOSE}"
fi

# ── D. 운영 스크립트 존재 ────────────────────────────────────────────────────
INFRA_DIR="${APP_DIR}/infra"
for script in ops_self_check.sh ops_git_guard.sh; do
  if [ ! -f "${INFRA_DIR}/${script}" ]; then
    _warn SCRIPTS "${script} 없음"
  elif [ ! -x "${INFRA_DIR}/${script}" ]; then
    _warn SCRIPTS "${script} 실행 권한 없음"
  fi
done

# ── E. 최근 백업 파일 확인 ───────────────────────────────────────────────────
echo ""
echo "=== 최근 백업 파일 (최대 10개) ==="
RECENT_COUNT=0
if [ -d "${BACKUP_DIR}" ]; then
  RECENT_COUNT=$(find "${BACKUP_DIR}" -maxdepth 2 -type f | wc -l)
  find "${BACKUP_DIR}" -maxdepth 2 -type f -printf "%T@ %p\n" 2>/dev/null \
    | sort -rn | head -10 | awk '{print $2}' | while read -r f; do
        ls -lh "$f"
      done
fi

if [ "${RECENT_COUNT}" -eq 0 ]; then
  _warn RECENT "backups 에 파일 없음 — 초기 상태이거나 백업 미수행"
fi

# ── F. .env 파일 보안 경고 (git 미추적) ──────────────────────────────────────
ENV_FILE="${INFRA_DIR}/.env"
if [ -f "${ENV_FILE}" ]; then
  ENV_PERM=$(stat -c "%a" "${ENV_FILE}" 2>/dev/null || echo "")
  if [ "${ENV_PERM}" != "600" ]; then
    _warn BACKUP ".env mode=${ENV_PERM} (권장: 600) — 별도 보관 필요"
  fi
else
  _warn BACKUP ".env 파일 없음 — 서버 미배포 또는 분실 위험"
fi

# ── 최종 verdict ──────────────────────────────────────────────────────────────
VERDICT="PASS"
for r in "${BACKUP_R}" "${DATA_R}" "${COMPOSE_R}" "${SCRIPTS_R}" "${RECENT_R}"; do
  [ "$r" = "FAIL" ] && VERDICT="FAIL" && break
  [ "$r" = "WARN" ] && VERDICT="WARN"
done

# ── 로그 기록 ─────────────────────────────────────────────────────────────────
LOG_LINE="[${TS}] backup_path=${BACKUP_R} data=${DATA_R} compose=${COMPOSE_R} scripts=${SCRIPTS_R} recent=${RECENT_R} verdict=${VERDICT}${DETAIL:+ |${DETAIL}}"
echo "${LOG_LINE}" >> "${LOG_FILE}"

# ── 대시보드용 .last 갱신 ─────────────────────────────────────────────────────
STATUS_DIR="/home/ubuntu/apps/risk-assessment-app/logs/status"
mkdir -p "${STATUS_DIR}"
echo "${LOG_LINE}" > "${STATUS_DIR}/backup_check.last" 2>/dev/null || true

# ── 콘솔 출력 ────────────────────────────────────────────────────────────────
echo ""
echo "[${TS}]"
echo "  backup_path : ${BACKUP_R}"
echo "  data        : ${DATA_R}"
echo "  compose     : ${COMPOSE_R}"
echo "  scripts     : ${SCRIPTS_R}"
echo "  recent      : ${RECENT_R}"
echo "  verdict     : ${VERDICT}"
[ -n "${DETAIL}" ] && echo "  detail      :${DETAIL}"

[ "${VERDICT}" = "PASS" ] && exit 0 || exit 1

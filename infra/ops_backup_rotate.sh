#!/usr/bin/env bash
set -euo pipefail

# risk-assessment-app 정기 백업 + 보관 주기 정리
# 생성 → 무결성 검사 → 보관 초과분 정리

APP_ROOT="/home/ubuntu/apps/risk-assessment-app"
APP_DIR="${APP_ROOT}/app"
INFRA_DIR="${APP_DIR}/infra"
BACKUP_ROOT="${APP_ROOT}/backups"
LOG_DIR="${APP_ROOT}/logs"
LOG_FILE="${LOG_DIR}/backup_rotate.log"
TS=$(date "+%Y%m%d_%H%M%S")
DATE=$(date "+%Y-%m-%d %H:%M:%S")

# 보관 개수 정책
KEEP_DATA=7
KEEP_LOGS=14
KEEP_CONFIG=7

mkdir -p "${BACKUP_ROOT}/data" "${BACKUP_ROOT}/logs" "${BACKUP_ROOT}/config"
mkdir -p "${LOG_DIR}"

DATA_R="PASS"; LOGS_R="PASS"; CONFIG_R="PASS"; ROTATE_R="PASS"
DETAIL=""

_warn() { local s="$1"; eval "${s}_R=WARN"; DETAIL="${DETAIL} [${s}:WARN] $2;"; }
_fail() { local s="$1"; eval "${s}_R=FAIL"; DETAIL="${DETAIL} [${s}:FAIL] $2;"; }

# ── A. data 백업 ──────────────────────────────────────────────────────────────
DATA_FILE="${BACKUP_ROOT}/data/risk-assessment-data-${TS}.tar.gz"
if tar -czf "${DATA_FILE}" -C "${APP_ROOT}" data/ 2>/dev/null; then
  if tar -tzf "${DATA_FILE}" > /dev/null 2>&1; then
    DATA_SIZE=$(du -sh "${DATA_FILE}" | cut -f1)
    DETAIL="${DETAIL} [DATA] ${DATA_FILE##*/} (${DATA_SIZE});"
  else
    _fail DATA "tar 무결성 검사 실패"
    rm -f "${DATA_FILE}"
  fi
else
  _fail DATA "tar 생성 실패"
fi

# ── B. logs 백업 ──────────────────────────────────────────────────────────────
LOGS_FILE="${BACKUP_ROOT}/logs/risk-assessment-logs-${TS}.tar.gz"
cd "${LOG_DIR}"
LOG_TARGETS=""
for f in git_guard.log self_check.log backup_check.log \
          git_guard_cron.log self_check_cron.log backup_check_cron.log \
          backup_rotate_cron.log change_history.jsonl; do
  [ -f "${LOG_DIR}/${f}" ] && LOG_TARGETS="${LOG_TARGETS} ${f}"
done

if [ -n "${LOG_TARGETS}" ]; then
  if tar -czf "${LOGS_FILE}" -C "${LOG_DIR}" ${LOG_TARGETS} 2>/dev/null; then
    if tar -tzf "${LOGS_FILE}" > /dev/null 2>&1; then
      LOGS_SIZE=$(du -sh "${LOGS_FILE}" | cut -f1)
      DETAIL="${DETAIL} [LOGS] ${LOGS_FILE##*/} (${LOGS_SIZE});"
    else
      _fail LOGS "tar 무결성 검사 실패"
      rm -f "${LOGS_FILE}"
    fi
  else
    _fail LOGS "tar 생성 실패"
  fi
else
  _warn LOGS "백업할 로그 파일 없음"
fi

# ── C. config 백업 ────────────────────────────────────────────────────────────
CONFIG_FILE="${BACKUP_ROOT}/config/risk-assessment-config-${TS}.tar.gz"
cd "${APP_ROOT}"
CONFIG_TARGETS=""
[ -f "${INFRA_DIR}/.env" ]  && CONFIG_TARGETS="${CONFIG_TARGETS} app/infra/.env"
[ -f "${APP_ROOT}/README.md" ] && CONFIG_TARGETS="${CONFIG_TARGETS} README.md"
[ -f "${APP_ROOT}/paths.env" ] && CONFIG_TARGETS="${CONFIG_TARGETS} paths.env"

if [ -n "${CONFIG_TARGETS}" ]; then
  if tar -czf "${CONFIG_FILE}" --preserve-permissions -C "${APP_ROOT}" ${CONFIG_TARGETS} 2>/dev/null; then
    if tar -tzf "${CONFIG_FILE}" > /dev/null 2>&1; then
      CONFIG_SIZE=$(du -sh "${CONFIG_FILE}" | cut -f1)
      DETAIL="${DETAIL} [CONFIG] ${CONFIG_FILE##*/} (${CONFIG_SIZE});"
    else
      _fail CONFIG "tar 무결성 검사 실패"
      rm -f "${CONFIG_FILE}"
    fi
  else
    _fail CONFIG "tar 생성 실패"
  fi
else
  _warn CONFIG "백업할 config 파일 없음"
fi

# ── D. 보관 주기 정리 (timestamp 정렬, 최신 N개 유지) ────────────────────────
_rotate() {
  local dir="$1" pattern="$2" keep="$3"
  local count
  count=$(find "${dir}" -maxdepth 1 -name "${pattern}" -type f | wc -l)
  if [ "${count}" -gt "${keep}" ]; then
    local to_delete=$(( count - keep ))
    find "${dir}" -maxdepth 1 -name "${pattern}" -type f -printf "%T@ %p\n" \
      | sort -n | head -"${to_delete}" | awk '{print $2}' | while read -r f; do
          rm -f "${f}"
          DETAIL="${DETAIL} [ROTATE:DEL] ${f##*/};"
        done
  fi
}

_rotate "${BACKUP_ROOT}/data"   "risk-assessment-data-*.tar.gz"   "${KEEP_DATA}"
_rotate "${BACKUP_ROOT}/logs"   "risk-assessment-logs-*.tar.gz"   "${KEEP_LOGS}"
_rotate "${BACKUP_ROOT}/config" "risk-assessment-config-*.tar.gz" "${KEEP_CONFIG}"

# 잔여 파일 수 확인
DATA_CNT=$(find "${BACKUP_ROOT}/data"   -name "risk-assessment-data-*.tar.gz"   -type f | wc -l)
LOGS_CNT=$(find "${BACKUP_ROOT}/logs"   -name "risk-assessment-logs-*.tar.gz"   -type f | wc -l)
CFG_CNT=$(find "${BACKUP_ROOT}/config"  -name "risk-assessment-config-*.tar.gz" -type f | wc -l)
DETAIL="${DETAIL} [REMAIN] data=${DATA_CNT} logs=${LOGS_CNT} config=${CFG_CNT};"

# ── 최종 verdict ──────────────────────────────────────────────────────────────
VERDICT="PASS"
for r in "${DATA_R}" "${LOGS_R}" "${CONFIG_R}" "${ROTATE_R}"; do
  [ "$r" = "FAIL" ] && VERDICT="FAIL" && break
  [ "$r" = "WARN" ] && VERDICT="WARN"
done

# ── 로그 기록 ─────────────────────────────────────────────────────────────────
LOG_LINE="[${DATE}] data=${DATA_R} logs=${LOGS_R} config=${CONFIG_R} rotate=${ROTATE_R} verdict=${VERDICT}${DETAIL:+ |${DETAIL}}"
echo "${LOG_LINE}" >> "${LOG_FILE}"

# ── 콘솔 출력 ────────────────────────────────────────────────────────────────
echo "[${DATE}]"
echo "  data   : ${DATA_R}"
echo "  logs   : ${LOGS_R}"
echo "  config : ${CONFIG_R}"
echo "  rotate : ${ROTATE_R}"
echo "  verdict: ${VERDICT}"
[ -n "${DETAIL}" ] && echo "  detail :${DETAIL}"

[ "${VERDICT}" = "PASS" ] && exit 0 || exit 1

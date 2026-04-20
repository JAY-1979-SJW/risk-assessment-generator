#!/usr/bin/env bash
set -euo pipefail

# risk-assessment-app 복구 리허설 점검
# 비파괴(read-only) — 실제 복구·삭제·untar 금지

APP_ROOT="/home/ubuntu/apps/risk-assessment-app"
APP_DIR="${APP_ROOT}/app"
BACKUP_DIR="${APP_ROOT}/backups"
DATA_DIR="${APP_ROOT}/data"
LOG_DIR="${APP_ROOT}/logs"
LOG_FILE="${LOG_DIR}/restore_rehearsal.log"
COMPOSE="${APP_DIR}/infra/docker-compose.yml"
INFRA_DIR="${APP_DIR}/infra"
TS=$(date "+%Y-%m-%d %H:%M:%S")

mkdir -p "${LOG_DIR}"

# ── 결과 변수 ─────────────────────────────────────────────────────────────────
BACKUPS_R="PASS"; COMPOSE_R="PASS"; SCRIPTS_R="PASS"; PATHS_R="PASS"
DETAIL=""

_warn() { local s="$1"; eval "${s}_R=WARN"; DETAIL="${DETAIL} [${s}:WARN] $2;"; }
_fail() { local s="$1"; eval "${s}_R=FAIL"; DETAIL="${DETAIL} [${s}:FAIL] $2;"; }

echo "=== risk-assessment-app 복구 리허설 점검 ==="
echo "[${TS}]"
echo ""

# ── A. 필수 경로 존재 확인 ────────────────────────────────────────────────────
echo "--- [A] 경로 존재 확인 ---"
for dir in "${APP_ROOT}" "${APP_DIR}" "${DATA_DIR}" "${LOG_DIR}" "${BACKUP_DIR}"; do
  if [ -d "${dir}" ]; then
    echo "  PASS  ${dir}"
  else
    echo "  FAIL  ${dir} — 없음"
    _fail PATHS "${dir} 없음"
  fi
done

# ── B. compose 파일 존재 ─────────────────────────────────────────────────────
echo ""
echo "--- [B] compose 파일 ---"
if [ -f "${COMPOSE}" ]; then
  echo "  PASS  ${COMPOSE}"
else
  echo "  FAIL  ${COMPOSE} — 없음"
  _fail COMPOSE "compose 파일 없음"
fi

# ── C. 핵심 운영 스크립트 존재·실행권한 확인 ─────────────────────────────────
echo ""
echo "--- [C] 운영 스크립트 ---"
REQUIRED_SCRIPTS=(
  ops_git_guard.sh
  ops_self_check.sh
  ops_backup_check.sh
  ops_backup_rotate.sh
  ops_restore_rehearsal.sh
)
for script in "${REQUIRED_SCRIPTS[@]}"; do
  SPATH="${INFRA_DIR}/${script}"
  if [ ! -f "${SPATH}" ]; then
    echo "  FAIL  ${script} — 없음"
    _fail SCRIPTS "${script} 없음"
  elif [ ! -x "${SPATH}" ]; then
    echo "  WARN  ${script} — 실행권한 없음"
    _warn SCRIPTS "${script} 실행권한 없음"
  else
    echo "  PASS  ${script}"
  fi
done

# ── D. 백업 파일 탐지 및 tar 무결성 확인 ─────────────────────────────────────
echo ""
echo "--- [D] 백업 파일 탐지 (data / logs / config) ---"

FOUND_DATA=""; FOUND_LOGS=""; FOUND_CONFIG=""
MISS_CATEGORIES=""

if [ -d "${BACKUP_DIR}" ]; then
  FOUND_DATA=$(find "${BACKUP_DIR}" -maxdepth 2 -name "*data*" -type f \
    | sort -r | head -1 2>/dev/null || true)
  FOUND_LOGS=$(find "${BACKUP_DIR}" -maxdepth 2 -name "*logs*" -type f \
    | sort -r | head -1 2>/dev/null || true)
  FOUND_CONFIG=$(find "${BACKUP_DIR}" -maxdepth 2 -name "*config*" -type f \
    | sort -r | head -1 2>/dev/null || true)
fi

_check_backup() {
  local label="$1" file="$2"
  if [ -z "${file}" ]; then
    echo "  WARN  ${label} — 최신 백업 파일 없음"
    MISS_CATEGORIES="${MISS_CATEGORIES} ${label}"
    return
  fi
  echo "  FOUND ${label}: ${file}"

  # tar 무결성 확인 (비파괴)
  if [[ "${file}" == *.tar.gz ]] || [[ "${file}" == *.tgz ]]; then
    if tar -tzf "${file}" > /dev/null 2>&1; then
      echo "        tar integrity: PASS"
    else
      echo "        tar integrity: FAIL — 손상 의심"
      _fail BACKUPS "${label} tar 손상: ${file}"
    fi
  elif [[ "${file}" == *.gz ]]; then
    if gzip -t "${file}" 2>/dev/null; then
      echo "        gzip integrity: PASS"
    else
      echo "        gzip integrity: FAIL — 손상 의심"
      _fail BACKUPS "${label} gzip 손상: ${file}"
    fi
  else
    echo "        integrity check: 지원 포맷 아님 (수동 확인 필요)"
  fi
}

_check_backup "data"   "${FOUND_DATA}"
_check_backup "logs"   "${FOUND_LOGS}"
_check_backup "config" "${FOUND_CONFIG}"

# 백업 판정
if [ -z "${FOUND_DATA}" ] && [ -z "${FOUND_LOGS}" ] && [ -z "${FOUND_CONFIG}" ]; then
  _fail BACKUPS "백업 파일 3종 모두 없음 — 복구 불가 상태"
elif [ -n "${MISS_CATEGORIES}" ]; then
  # BACKUPS_R 이 이미 FAIL 이 아닌 경우에만 WARN 으로 올림
  current="${BACKUPS_R}"
  [ "${current}" != "FAIL" ] && _warn BACKUPS "일부 category 백업 없음:${MISS_CATEGORIES}"
fi

# ── E. 최종 verdict ───────────────────────────────────────────────────────────
VERDICT="PASS"
for r in "${BACKUPS_R}" "${COMPOSE_R}" "${SCRIPTS_R}" "${PATHS_R}"; do
  [ "$r" = "FAIL" ] && VERDICT="FAIL" && break
  [ "$r" = "WARN" ] && VERDICT="WARN"
done

# ── 로그 기록 ─────────────────────────────────────────────────────────────────
LOG_LINE="[${TS}] backups=${BACKUPS_R} compose=${COMPOSE_R} scripts=${SCRIPTS_R} paths=${PATHS_R} verdict=${VERDICT}${DETAIL:+ |${DETAIL}}"
echo "${LOG_LINE}" >> "${LOG_FILE}"

# ── 대시보드용 .last 갱신 ─────────────────────────────────────────────────────
STATUS_DIR="/home/ubuntu/app/nginx/webroot/status/risk-assessment/data"
mkdir -p "${STATUS_DIR}"
echo "${LOG_LINE}" > "${STATUS_DIR}/restore_rehearsal.last" 2>/dev/null || true

TS_ISO=$(date +%Y-%m-%dT%H:%M:%S+09:00)
HIST_SUMMARY="backups=${BACKUPS_R} compose=${COMPOSE_R} scripts=${SCRIPTS_R} paths=${PATHS_R}"
HIST_FILE="${STATUS_DIR}/restore_rehearsal.history.jsonl"
printf '{"ts":"%s","source":"restore_rehearsal","verdict":"%s","summary":"%s"}\n' \
    "$TS_ISO" "$VERDICT" "$HIST_SUMMARY" >> "$HIST_FILE" 2>/dev/null || true
if [ "$(wc -l < "$HIST_FILE" 2>/dev/null || echo 0)" -gt 1000 ]; then
    tail -n 1000 "$HIST_FILE" > "${HIST_FILE}.tmp" && mv "${HIST_FILE}.tmp" "$HIST_FILE" || true
fi

# ── 콘솔 최종 출력 ────────────────────────────────────────────────────────────
echo ""
echo "=== 최종 판정 ==="
echo "  backups : ${BACKUPS_R}"
echo "  compose : ${COMPOSE_R}"
echo "  scripts : ${SCRIPTS_R}"
echo "  paths   : ${PATHS_R}"
echo "  verdict : ${VERDICT}"
[ -n "${DETAIL}" ] && echo "  detail  :${DETAIL}"
echo ""
echo "로그: ${LOG_FILE}"

[ "${VERDICT}" = "PASS" ] && exit 0 || exit 1

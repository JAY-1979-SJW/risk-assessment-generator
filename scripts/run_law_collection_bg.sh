#!/usr/bin/env bash
# 법령/KOSHA 가이드 메타 수집 백그라운드 실행 스크립트
# 사용법: bash scripts/run_law_collection_bg.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

LOG_DIR="$ROOT_DIR/logs/law_collect"
PID_FILE="$LOG_DIR/collect.pid"
LOCK_FILE="$LOG_DIR/collect.lock"
LOG_FILE="$LOG_DIR/run_$(date +%Y%m%d_%H%M%S).log"
STATUS_FILE="$LOG_DIR/last_run.status"

mkdir -p "$LOG_DIR"
mkdir -p "$ROOT_DIR/data/risk_db/law_raw"
mkdir -p "$ROOT_DIR/data/risk_db/guide_raw"

# ── 중복 실행 방지 ──────────────────────────────────────────────────────
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[WARN] 이미 실행 중 (PID=$OLD_PID). 종료합니다."
        exit 1
    else
        echo "[INFO] 이전 PID($OLD_PID) 미실행 확인 — 재실행합니다."
        rm -f "$PID_FILE" "$LOCK_FILE"
    fi
fi

if [ -f "$LOCK_FILE" ]; then
    echo "[WARN] lock 파일 잔류 ($LOCK_FILE) — 정리 후 재실행합니다."
    rm -f "$LOCK_FILE"
fi

touch "$LOCK_FILE"

# ── Python 확인 ─────────────────────────────────────────────────────────
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "")
if [ -z "$PYTHON" ]; then
    echo "[ERROR] python3/python 명령을 찾을 수 없습니다."
    rm -f "$LOCK_FILE"
    exit 2
fi

echo "[INFO] 수집 시작: $(date)" | tee "$LOG_FILE"
echo "[INFO] 로그 파일: $LOG_FILE"
echo "[INFO] Python: $PYTHON"

# ── 백그라운드 실행 ─────────────────────────────────────────────────────
nohup bash -c "
  cd '$ROOT_DIR'
  echo '[INFO] --- 법령 메타 수집 ---' >> '$LOG_FILE' 2>&1
  '$PYTHON' scripts/collect_laws_index.py >> '$LOG_FILE' 2>&1
  LAW_EXIT=\$?

  echo '[INFO] --- KOSHA 가이드 메타 수집 ---' >> '$LOG_FILE' 2>&1
  '$PYTHON' scripts/collect_kosha_guides.py >> '$LOG_FILE' 2>&1
  GUIDE_EXIT=\$?

  if [ \$LAW_EXIT -eq 0 ] && [ \$GUIDE_EXIT -eq 0 ]; then
    STATUS=SUCCESS
  elif [ \$LAW_EXIT -eq 0 ] || [ \$GUIDE_EXIT -eq 0 ]; then
    STATUS=PARTIAL
  else
    STATUS=FAIL
  fi

  printf '%s\nrun_at=%s\nlaw_exit=%s\nguide_exit=%s\nlog=%s\n' \
    \"\$STATUS\" \"\$(date -u +%Y-%m-%dT%H:%M:%SZ)\" \"\$LAW_EXIT\" \"\$GUIDE_EXIT\" \"$LOG_FILE\" \
    > '$STATUS_FILE'

  rm -f '$LOCK_FILE' '$PID_FILE'
  echo \"[INFO] 완료: \$STATUS (\$(date))\" >> '$LOG_FILE' 2>&1
" >> "$LOG_FILE" 2>&1 &

BG_PID=$!
echo $BG_PID > "$PID_FILE"
echo "[INFO] 백그라운드 실행 중 (PID=$BG_PID)"
echo "[INFO] 로그 확인  : tail -f $LOG_FILE"
echo "[INFO] 상태 확인  : bash scripts/check_law_collection_status.sh"

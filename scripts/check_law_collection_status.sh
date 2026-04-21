#!/usr/bin/env bash
# 법령/KOSHA 가이드 수집 상태 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$ROOT_DIR/logs/law_collect"
PID_FILE="$LOG_DIR/collect.pid"
STATUS_FILE="$LOG_DIR/last_run.status"

echo "===== 법령 수집 상태 ====="

# 1. 프로세스 실행 여부
echo ""
echo "--- 프로세스 ---"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "[실행중] PID=$PID"
    else
        echo "[중지됨] PID=$PID"
    fi
else
    echo "[미실행] PID 파일 없음"
fi

# 2. 마지막 실행 상태
echo ""
echo "--- 마지막 실행 상태 ---"
if [ -f "$STATUS_FILE" ]; then
    cat "$STATUS_FILE"
else
    echo "(없음)"
fi

# 3. 최근 로그 (20줄)
echo ""
echo "--- 최근 로그 ---"
LATEST_LOG=$(ls -t "$LOG_DIR"/run_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "파일: $LATEST_LOG"
    tail -20 "$LATEST_LOG"
else
    echo "(로그 없음)"
fi

# 4. staging 산출물
echo ""
echo "--- staging 산출물 ---"
echo "[law_raw]"
ls -lh "$ROOT_DIR/data/risk_db/law_raw/" 2>/dev/null || echo "(없음)"
echo "[guide_raw]"
ls -lh "$ROOT_DIR/data/risk_db/guide_raw/" 2>/dev/null || echo "(없음)"

# 5. 개별 status 파일
echo ""
echo "--- 개별 수집 status ---"
for sfile in "$LOG_DIR"/*.status; do
    [ -f "$sfile" ] || continue
    echo "[$sfile]"
    cat "$sfile"
    echo ""
done

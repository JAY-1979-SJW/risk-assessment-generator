"""
KOSHA 파싱 모니터 데몬
기능:
  1. LogTailer      — tail -f 방식 (inode 추적, 로테이션 대응)
  2. LogParser      — 라인 분류: PROGRESS / ERROR / WARN / COMPLETE / UNKNOWN
  3. ErrorDetector  — 프로세스 사망 / 연속 실패 / 속도 급락 감지
  4. ProcessWatcher — PID 감시 → 자동 재시작 or 승인 대기
  5. MonitorDaemon  — 전체 루프, Ctrl+C 종료

사용법:
  python3 kosha_monitor.py                     # 기본 감시 (자동 재시작)
  python3 kosha_monitor.py --no-restart        # 프로세스 사망 시 승인 대기만
  python3 kosha_monitor.py --log logs/parser.log  # 단일 로그 파일 지정
"""

import os
import re
import sys
import time
import signal
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque

# ── 설정 ────────────────────────────────────────────────────────────────────

SCRAPER_DIR   = Path(__file__).parent
LOGS_DIR      = SCRAPER_DIR / 'logs'

# 감시 대상 로그 파일 (없으면 생략)
WATCH_LOGS = [
    LOGS_DIR / 'run_history.log',
    LOGS_DIR / 'parser.log',
    LOGS_DIR / 'pipeline.log',
    LOGS_DIR / 'scraper.error.log',
    Path('/tmp/kosha_parse.log'),
    Path('/tmp/kosha_parse_inner.log'),
    Path('/tmp/kosha_unzip.log'),
]

# 감시 대상 프로세스 패턴 → (재시작 명령)
WATCH_PROCS = {
    'kosha_parser.py --pending': (
        'cd %s && nohup python3 -u kosha_parser.py --pending '
        '>> /tmp/kosha_parse.log 2>&1 &' % SCRAPER_DIR
    ),
    'parse_inner.py': (
        'nohup python3 -u /tmp/parse_inner.py '
        '>> /tmp/kosha_parse_inner.log 2>&1 &'
    ),
}

POLL_INTERVAL     = 2    # 로그 폴링 간격 (초)
PROC_CHECK_EVERY  = 10   # 프로세스 체크 간격 (초)
STALL_MINUTES     = 15   # N분 이상 진행 없으면 STALL 경고
FAIL_THRESHOLD    = 20   # 연속 실패 N건 → WARN
SPEED_WARN_RATIO  = 0.3  # 초기 속도 대비 30% 미만 → WARN

# ANSI 색상
C = {
    'reset':   '\033[0m',
    'bold':    '\033[1m',
    'red':     '\033[91m',
    'yellow':  '\033[93m',
    'green':   '\033[92m',
    'cyan':    '\033[96m',
    'gray':    '\033[90m',
    'blue':    '\033[94m',
    'magenta': '\033[95m',
}

def color(text, *keys):
    prefix = ''.join(C[k] for k in keys)
    return f'{prefix}{text}{C["reset"]}'


# ── 1. LogTailer ─────────────────────────────────────────────────────────────

class LogTailer:
    """tail -f 방식. 파일 inode 변경(로테이션) 시 재오픈."""

    def __init__(self, path: Path):
        self.path  = path
        self._f    = None
        self._ino  = None
        self._open()

    def _open(self):
        if not self.path.exists():
            return
        try:
            self._f   = open(self.path, 'r', encoding='utf-8', errors='replace')
            self._f.seek(0, 2)          # 파일 끝으로 이동 (기존 내용 스킵)
            self._ino = os.stat(self.path).st_ino
        except OSError:
            self._f = None

    def lines(self) -> list[str]:
        if not self.path.exists():
            self._f = None
            return []
        # inode 변경 감지 → 재오픈
        try:
            cur_ino = os.stat(self.path).st_ino
        except OSError:
            return []
        if self._f is None or cur_ino != self._ino:
            if self._f:
                self._f.close()
            self._open()
        if self._f is None:
            return []
        result = []
        while True:
            line = self._f.readline()
            if not line:
                break
            result.append(line.rstrip('\n'))
        return result

    def close(self):
        if self._f:
            self._f.close()


# ── 2. LogParser ─────────────────────────────────────────────────────────────

# 2026-04-19 22:08:15 [INFO] run.parser_inner | [200/7316] 성공:200 실패:0 ...
_RE_LOG      = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (\S+) \| (.*)')
_RE_PROGRESS = re.compile(r'\[(\d+)/(\d+)\].*성공:(\d+).*실패:(\d+).*청크:(\d+).*(\d+\.\d+)건/s.*잔여:(\d+)분')
_RE_COMPLETE = re.compile(r'(파싱 완료|inner 완료|ZIP 해제 완료|=== 파이프라인 완료)')
_RE_START    = re.compile(r'(파싱 시작|해제 시작|파이프라인 시작).*대상:(\d+)건')

class ParsedLine:
    __slots__ = ('ts', 'level', 'logger', 'msg', 'kind', 'data')

    def __init__(self, raw: str, source: str):
        self.data   = {}
        self.source = source
        m = _RE_LOG.match(raw)
        if m:
            self.ts     = m.group(1)
            self.level  = m.group(2)
            self.logger = m.group(3)
            self.msg    = m.group(4)
        else:
            self.ts     = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.level  = 'INFO'
            self.logger = source
            self.msg    = raw

        self.kind = self._classify()

    def _classify(self):
        if self.level == 'ERROR':
            return 'ERROR'
        if self.level == 'WARNING':
            return 'WARN'
        m = _RE_PROGRESS.search(self.msg)
        if m:
            self.data = {
                'done': int(m.group(1)), 'total': int(m.group(2)),
                'success': int(m.group(3)), 'failed': int(m.group(4)),
                'chunks': int(m.group(5)), 'speed': float(m.group(6)),
                'remain': int(m.group(7)),
            }
            return 'PROGRESS'
        if _RE_COMPLETE.search(self.msg):
            return 'COMPLETE'
        if _RE_START.search(self.msg):
            m2 = _RE_START.search(self.msg)
            self.data = {'total': int(m2.group(2))}
            return 'START'
        return 'INFO'


# ── 3. ErrorDetector ─────────────────────────────────────────────────────────

class ErrorDetector:
    def __init__(self):
        self._last_progress: dict[str, datetime] = {}
        self._last_speed:    dict[str, float]    = {}
        self._fail_streak:   dict[str, int]      = {}
        self._warnings_sent: dict[str, datetime] = {}

    def feed(self, line: ParsedLine) -> list[str]:
        """경고 메시지 목록 반환 (없으면 [])"""
        alerts = []
        src = line.source

        if line.kind == 'PROGRESS':
            self._last_progress[src] = datetime.now()
            speed = line.data.get('speed', 0)
            failed = line.data.get('failed', 0)

            # 초기 속도 기록
            if src not in self._last_speed and speed > 0:
                self._last_speed[src] = speed

            # 속도 급락 감지
            baseline = self._last_speed.get(src, 0)
            if baseline > 0 and speed > 0 and speed < baseline * SPEED_WARN_RATIO:
                key = f'speed_{src}'
                if self._throttle(key, minutes=10):
                    alerts.append(f'속도 급락 [{src}]: {baseline:.1f} → {speed:.1f} 건/s')

            # 연속 실패 감지
            self._fail_streak[src] = failed
            if failed >= FAIL_THRESHOLD:
                key = f'fail_{src}'
                if self._throttle(key, minutes=15):
                    alerts.append(f'실패 누적 [{src}]: {failed}건')

        elif line.kind == 'ERROR':
            alerts.append(f'ERROR [{src}]: {line.msg}')

        return alerts

    def check_stall(self) -> list[str]:
        """진행 없는 소스 목록 반환"""
        alerts = []
        threshold = timedelta(minutes=STALL_MINUTES)
        now = datetime.now()
        for src, last in self._last_progress.items():
            if now - last > threshold:
                key = f'stall_{src}'
                if self._throttle(key, minutes=STALL_MINUTES):
                    alerts.append(f'진행 없음 [{src}]: {int((now-last).seconds/60)}분째 정지')
        return alerts

    def _throttle(self, key: str, minutes: int) -> bool:
        """같은 경고를 N분 내 중복 발송 방지"""
        last = self._warnings_sent.get(key)
        if last and datetime.now() - last < timedelta(minutes=minutes):
            return False
        self._warnings_sent[key] = datetime.now()
        return True


# ── 4. ProcessWatcher ────────────────────────────────────────────────────────

class ProcessWatcher:
    def __init__(self, auto_restart: bool = True):
        self.auto_restart = auto_restart
        self._known_dead:  set[str] = set()
        self._restart_count: dict[str, int] = {}

    def alive_procs(self) -> set[str]:
        """현재 살아있는 감시 프로세스 패턴 집합"""
        try:
            out = subprocess.check_output(
                ['ps', 'aux'], text=True, stderr=subprocess.DEVNULL
            )
        except Exception:
            return set()
        alive = set()
        for pat in WATCH_PROCS:
            if pat in out:
                alive.add(pat)
        return alive

    def check(self) -> list[str]:
        """죽은 프로세스 감지 → 재시작 or 알림 메시지 반환"""
        alerts = []
        alive = self.alive_procs()
        for pat, restart_cmd in WATCH_PROCS.items():
            if pat not in alive and pat not in self._known_dead:
                self._known_dead.add(pat)
                cnt = self._restart_count.get(pat, 0)
                if self.auto_restart and cnt < 3:
                    self._restart_count[pat] = cnt + 1
                    try:
                        subprocess.run(restart_cmd, shell=True, check=False)
                        alerts.append(
                            color(f'[재시작 #{cnt+1}] {pat}', 'yellow')
                        )
                    except Exception as e:
                        alerts.append(
                            color(f'[재시작 실패] {pat}: {e}', 'red')
                        )
                else:
                    alerts.append(
                        color(f'[프로세스 사망] {pat} — 수동 확인 필요', 'red', 'bold')
                    )
            elif pat in alive and pat in self._known_dead:
                self._known_dead.discard(pat)

        return alerts

    def status_line(self) -> str:
        alive = self.alive_procs()
        parts = []
        for pat in WATCH_PROCS:
            name = pat.split('.py')[0].split('/')[-1]
            if pat in alive:
                parts.append(color(f'● {name}', 'green'))
            else:
                parts.append(color(f'○ {name}', 'red'))
        return '  '.join(parts)


# ── 5. 출력 포맷터 ───────────────────────────────────────────────────────────

def fmt_line(line: ParsedLine) -> str | None:
    src_short = line.source.replace('run_history.log', 'run')
    ts = line.ts[11:]  # HH:MM:SS 만

    if line.kind == 'PROGRESS':
        d = line.data
        pct = d['done'] / d['total'] * 100 if d['total'] else 0
        bar_len = 20
        filled  = int(bar_len * pct / 100)
        bar     = '█' * filled + '░' * (bar_len - filled)
        return (
            f"{color(ts, 'gray')} {color(src_short, 'cyan')} "
            f"|{color(bar, 'blue')}| {color(f'{pct:.0f}%', 'bold')} "
            f"{d['done']:,}/{d['total']:,}  "
            f"✓{color(str(d['success']), 'green')} "
            f"✗{color(str(d['failed']), 'red' if d['failed'] else 'gray')} "
            f"chunk={d['chunks']:,}  "
            f"{color(str(round(d['speed'],1))+'/s', 'cyan')}  "
            f"잔여 {color(str(d['remain'])+'분', 'yellow')}"
        )

    elif line.kind == 'COMPLETE':
        return color(f'\n✅ [{ts}] {src_short} | {line.msg}', 'green', 'bold')

    elif line.kind == 'START':
        return color(f'\n🚀 [{ts}] {src_short} | {line.msg}', 'cyan', 'bold')

    elif line.kind == 'ERROR':
        return color(f'🔴 [{ts}] {src_short} | {line.msg}', 'red', 'bold')

    elif line.kind == 'WARN':
        return color(f'⚠️  [{ts}] {src_short} | {line.msg}', 'yellow')

    elif line.kind == 'INFO':
        # scraper.error.log 내용은 항상 출력, 나머지 INFO는 스킵
        if 'error' in line.source.lower():
            return color(f'🔴 [{ts}] {line.msg}', 'red')
        return None

    return None


# ── 6. MonitorDaemon ─────────────────────────────────────────────────────────

class MonitorDaemon:
    def __init__(self, extra_logs: list[Path] = None, auto_restart: bool = True):
        log_paths   = list(WATCH_LOGS)
        if extra_logs:
            log_paths += extra_logs
        self.tailers  = {p: LogTailer(p) for p in log_paths}
        self.parser_  = LogParser()   # 이름 충돌 방지
        self.detector = ErrorDetector()
        self.watcher  = ProcessWatcher(auto_restart=auto_restart)
        self._running = True
        self._last_proc_check = 0
        self._last_status_line = ''
        signal.signal(signal.SIGTERM, self._on_sigterm)
        signal.signal(signal.SIGINT,  self._on_sigterm)

    def _on_sigterm(self, *_):
        self._running = False

    def run(self):
        print(color('\n=== KOSHA 파싱 모니터 시작 ===', 'cyan', 'bold'))
        print(color('  Ctrl+C 로 종료\n', 'gray'))

        while self._running:
            now = time.time()
            any_output = False

            # ① 모든 로그 파일 새 라인 읽기
            for path, tailer in self.tailers.items():
                for raw in tailer.lines():
                    if not raw.strip():
                        continue
                    line = ParsedLine(raw, path.name)
                    formatted = fmt_line(line)
                    if formatted:
                        print(formatted)
                        any_output = True

                    # 에러 감지 피드
                    alerts = self.detector.feed(line)
                    for a in alerts:
                        print(color(f'  ⚠  {a}', 'yellow', 'bold'))

            # ② 진행 정지 감지
            for a in self.detector.check_stall():
                print(color(f'  ⏸  {a}', 'yellow'))
                any_output = True

            # ③ 프로세스 감시 (N초마다)
            if now - self._last_proc_check >= PROC_CHECK_EVERY:
                self._last_proc_check = now
                for a in self.watcher.check():
                    print(a)
                    any_output = True

                # 상태 표시줄 갱신 (변경 시만)
                status = (f'\r  {self.watcher.status_line()}  '
                          f'{color(datetime.now().strftime("%H:%M:%S"), "gray")}  ')
                if status != self._last_status_line:
                    print(status, end='', flush=True)
                    self._last_status_line = status

            time.sleep(POLL_INTERVAL)

        # 종료
        print(color('\n\n=== 모니터 종료 ===', 'gray'))
        for t in self.tailers.values():
            t.close()


class LogParser:
    """ParsedLine 생성 위임 (구조 분리용)"""
    def parse(self, raw: str, source: str) -> ParsedLine:
        return ParsedLine(raw, source)


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import os
    os.chdir(Path(__file__).parent)
    from dotenv import load_dotenv
    load_dotenv()

    ap = argparse.ArgumentParser(description='KOSHA 파싱 모니터')
    ap.add_argument('--no-restart',  action='store_true', help='프로세스 사망 시 자동 재시작 안 함')
    ap.add_argument('--log',         action='append',     help='추가 감시 로그 경로')
    ap.add_argument('--from-start',  action='store_true', help='로그 파일 처음부터 읽기')
    args = ap.parse_args()

    extra = [Path(p) for p in (args.log or [])]

    if args.from_start:
        # 처음부터 읽기 모드: tailer seek(0) 처리
        class _FromStartTailer(LogTailer):
            def _open(self):
                super()._open()
                if self._f:
                    self._f.seek(0)   # 끝 대신 처음으로
        # MonitorDaemon 내부에서 LogTailer 대신 사용
        import kosha_monitor as _self
        _self.LogTailer = _FromStartTailer

    daemon = MonitorDaemon(extra_logs=extra, auto_restart=not args.no_restart)
    daemon.run()

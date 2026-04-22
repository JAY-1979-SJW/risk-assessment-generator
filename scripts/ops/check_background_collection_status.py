"""
백그라운드 수집 상태 요약.

출력
- 실행중 여부 (PID)
- 최근 collection_runs 5건
- 큐 pending / running / done / failed / skipped 개수
- source 별 실패 상위 3
- 최근 오류 5건 (큐 내 last_error 에서)
- 다음 권장 조치

CLI
    python scripts/ops/check_background_collection_status.py
    python scripts/ops/check_background_collection_status.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()

sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ops._queue import counts, master_path, queue_dir, read_all  # noqa: E402


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    for env in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env.exists():
            load_dotenv(env, override=False)


def get_db_connection():
    import psycopg2  # type: ignore
    _load_dotenv()
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    database = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    if not (host and database and user):
        raise RuntimeError("DB 접속 정보 누락")
    return psycopg2.connect(
        host=host, port=int(port), dbname=database, user=user, password=password or ""
    )


def _pid_running(pid_path: Path) -> tuple[bool, int | None]:
    if not pid_path.exists():
        return (False, None)
    try:
        pid = int(pid_path.read_text().strip())
    except Exception:
        return (False, None)
    try:
        os.kill(pid, 0)
        return (True, pid)
    except OSError:
        return (False, pid)


def _recent_runs(limit: int = 5) -> list[dict]:
    try:
        conn = get_db_connection()
    except Exception:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, source_type, run_date, status,
                       total_count, success_count, fail_count,
                       started_at, finished_at,
                       COALESCE(note,'') AS note
                  FROM collection_runs
                 ORDER BY id DESC
                 LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    out: list[dict] = []
    for r in rows:
        out.append({
            "id": r[0], "source_type": r[1], "run_date": str(r[2]),
            "status": r[3], "total": r[4], "success": r[5], "failed": r[6],
            "started_at": str(r[7]) if r[7] else None,
            "finished_at": str(r[8]) if r[8] else None,
            "note": (r[9] or "")[:200],
        })
    return out


def summarize(as_json: bool) -> dict:
    log_path = Path(os.getenv("OPS_LOG_PATH", "/app/logs/background_collection.log"))
    pid_path = Path(os.getenv("OPS_PID_PATH", "/app/logs/background_collection.pid"))
    is_running, pid = _pid_running(pid_path)

    jobs = read_all()
    qc = counts(jobs)

    # source 별 실패 상위
    by_source_fail: dict[str, int] = {}
    recent_errors: list[dict] = []
    for j in jobs:
        if j.get("status") == "failed":
            by_source_fail[j.get("source_type") or "?"] = \
                by_source_fail.get(j.get("source_type") or "?", 0) + 1
            if len(recent_errors) < 5:
                recent_errors.append({
                    "job_id": j.get("job_id"),
                    "retry": j.get("retry_count", 0),
                    "error": (j.get("last_error") or "")[:180],
                })
    fail_top = sorted(by_source_fail.items(), key=lambda kv: -kv[1])[:3]

    runs = _recent_runs(5)

    # 권장 조치
    advice: list[str] = []
    pending = qc.get("pending", 0)
    if pending == 0 and qc.get("failed", 0) == 0:
        advice.append("큐가 비어있거나 모두 처리됨. build_collection_queue.py 재빌드 고려.")
    if pending > 0 and not is_running:
        advice.append("pending 존재하지만 프로세스 미구동. run_background_collection.py --loop 시작 필요.")
    if qc.get("failed", 0) >= 10:
        advice.append("failed 10건 이상. 큐에서 원인 분석 후 retry_count 리셋 고려.")
    if not advice:
        advice.append("정상 동작 중.")

    report = {
        "queue_path": str(master_path()),
        "log_path": str(log_path),
        "pid_path": str(pid_path),
        "running": is_running,
        "pid": pid,
        "queue_counts": qc,
        "failed_by_source_top3": fail_top,
        "recent_errors": recent_errors,
        "recent_runs": runs,
        "advice": advice,
    }

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        _print_human(report)
    return report


def _print_human(r: dict) -> None:
    print("=== Background Collection Status ===")
    print(f"queue : {r['queue_path']}")
    print(f"log   : {r['log_path']}")
    print(f"pid   : {r['pid_path']}  running={r['running']}  pid={r['pid']}")
    print("\n-- queue counts --")
    for k in ("pending", "running", "done", "failed", "skipped"):
        print(f"  {k:<9}: {r['queue_counts'].get(k, 0):,}")
    print("\n-- failed by source (top 3) --")
    for st, n in r["failed_by_source_top3"]:
        print(f"  {st:<12}: {n:,}")
    if r["recent_errors"]:
        print("\n-- recent errors --")
        for e in r["recent_errors"]:
            print(f"  [{e['retry']}] {e['job_id']}  :: {e['error']}")
    print("\n-- recent runs --")
    for run in r["recent_runs"]:
        print(f"  #{run['id']} {run['run_date']} {run['source_type']:<12} "
              f"{run['status']:<8} t={run['total']} ok={run['success']} "
              f"fail={run['failed']} note={run['note']}")
    print("\n-- advice --")
    for a in r["advice"]:
        print(f"  - {a}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    summarize(args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())

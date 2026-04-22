"""
큐 파일 I/O 유틸.

- 마스터 큐: $OPS_QUEUE_DIR/collection_queue.jsonl
- 파생 뷰  : collection_queue_pending.jsonl / _done.jsonl / _failed.jsonl
- 기본 경로: /app/data/ops (컨테이너) == /home/ubuntu/apps/risk-assessment-app/data/ops (호스트)

Job 레코드 스키마 (JSONL, 한 줄 1 job):
    job_id         str  (action:source_type:source_id 혹은 action:range)
    source_type    str
    source_id      str
    action         str  (relink_articles | refresh_hwpx_path | kosha_redownload | ...)
    priority       int  (작을수록 높음. 기본 5)
    status         str  (pending | running | done | failed | skipped)
    retry_count    int  (기본 0)
    last_error     str | None
    updated_at     str  (ISO 8601)
    note           str | None

쓰기는 항상 임시 파일 → os.replace 로 원자 교체.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_QUEUE_DIR = "/app/data/ops"


def queue_dir() -> Path:
    p = Path(os.getenv("OPS_QUEUE_DIR", DEFAULT_QUEUE_DIR))
    p.mkdir(parents=True, exist_ok=True)
    return p


def master_path() -> Path:
    return queue_dir() / "collection_queue.jsonl"


def view_path(status: str) -> Path:
    return queue_dir() / f"collection_queue_{status}.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    cnt = 0
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                cnt += 1
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return cnt


def read_all() -> list[dict]:
    p = master_path()
    if not p.exists():
        return []
    out: list[dict] = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def write_all(jobs: list[dict]) -> None:
    _atomic_write_jsonl(master_path(), jobs)
    for st in ("pending", "done", "failed"):
        _atomic_write_jsonl(view_path(st), [j for j in jobs if j.get("status") == st])


def make_job(
    action: str,
    source_type: str,
    source_id: str,
    priority: int = 5,
    note: str | None = None,
) -> dict:
    return {
        "job_id": f"{action}:{source_type}:{source_id}",
        "source_type": source_type,
        "source_id": source_id,
        "action": action,
        "priority": priority,
        "status": "pending",
        "retry_count": 0,
        "last_error": None,
        "updated_at": now_iso(),
        "note": note,
    }


def counts(jobs: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for j in jobs:
        s = j.get("status") or "?"
        out[s] = out.get(s, 0) + 1
    return out

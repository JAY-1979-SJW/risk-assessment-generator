"""
백그라운드 수집 오케스트레이터.

역할
- 큐(`collection_queue.jsonl`)에서 status='pending' job 을 꺼내
  action 별 핸들러를 호출, 결과를 큐/collection_runs 에 기록한다.
- 기존 수집/매핑 로직 재사용. 새 로직을 쓰지 않는다.
- 한 job 의 예외는 다른 job 에 전파되지 않는다.

CLI
    python scripts/ops/run_background_collection.py
        [--once | --loop]
        [--limit N]           # 한 배치에서 처리할 최대 job 수 (기본 50)
        [--sources a,b,c]     # 특정 source_type 만
        [--actions a,b]       # 특정 action 만
        [--sleep-seconds N]   # --loop 배치 간 휴식 (기본 60)
        [--dry-run]           # 실제 DB 쓰기 없음

재시도 규칙
    - job 실행 시 예외 발생 → retry_count+=1, status=failed
    - retry_count >= 3 → 이후 스킵

액션 핸들러
    relink_articles   — scripts.db.link_forms_to_articles 의 인덱스 재사용
    refresh_hwpx_path — data/raw/** 에서 파일 탐색 후 documents.hwpx_path 갱신

로그/PID
    $OPS_LOG_PATH (기본 /app/logs/background_collection.log)
    $OPS_PID_PATH (기본 /app/logs/background_collection.pid)
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import signal
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()

sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ops._queue import (  # noqa: E402
    counts, master_path, now_iso, queue_dir, read_all, write_all,
)

MAX_RETRY = 3
DEFAULT_LIMIT = 50
DEFAULT_SLEEP = 60


# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

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


def _log_path() -> Path:
    p = Path(os.getenv("OPS_LOG_PATH", "/app/logs/background_collection.log"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _pid_path() -> Path:
    p = Path(os.getenv("OPS_PID_PATH", "/app/logs/background_collection.pid"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _setup_logger() -> logging.Logger:
    lg = logging.getLogger("ops.bg_collect")
    lg.setLevel(logging.INFO)
    if not lg.handlers:
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh = logging.FileHandler(_log_path(), encoding="utf-8")
        fh.setFormatter(fmt)
        lg.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        lg.addHandler(sh)
    return lg


# ---------------------------------------------------------------------------
# 액션 핸들러 팩토리 — 공용 리소스 1회 로드 후 job 단위로 호출
# ---------------------------------------------------------------------------

class ActionContext:
    """배치 시작 시 1회 초기화, 배치 내 모든 job 이 공유."""
    def __init__(self, conn):
        self.conn = conn
        self._art_idx: dict | None = None
        self._law_names_sorted: list[str] | None = None
        self._raw_index: dict[tuple[str, str], Path] | None = None

    def article_index(self) -> dict:
        if self._art_idx is None:
            from scripts.db.link_forms_to_articles import build_article_index
            self._art_idx = build_article_index(self.conn)
            self._law_names_sorted = sorted({ln for (ln, _) in self._art_idx.keys()},
                                            key=lambda s: -len(s))
        return self._art_idx

    def law_names_sorted(self) -> list[str]:
        if self._law_names_sorted is None:
            self.article_index()
        return self._law_names_sorted or []

    def raw_index(self) -> dict[tuple[str, str], Path]:
        """data/raw 아래의 모든 HWPX 를 (source_type, source_id) 로 인덱싱."""
        if self._raw_index is not None:
            return self._raw_index
        idx: dict[tuple[str, str], Path] = {}
        roots = [
            Path(os.getenv("DATA_DIR", "/app/data")) / "raw",
        ]
        # source_id 가 파일명에 포함된 패턴을 허용하기 위해 filename 기반 매핑
        for root in roots:
            if not root.exists():
                continue
            for p in root.rglob("*.hwpx"):
                name = p.stem  # 예: "K12345_xxx"
                # 아주 러프한 매칭: stem 전체를 source_id 후보로
                idx.setdefault(("*", name), p)
        self._raw_index = idx
        return idx


def _resolve_document(conn, source_type: str, source_id: str) -> tuple[int, str, str] | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, COALESCE(title,''), COALESCE(body_text,'') "
            "FROM documents WHERE source_type=%s AND source_id=%s",
            (source_type, source_id),
        )
        r = cur.fetchone()
        return (int(r[0]), r[1], r[2]) if r else None


def action_relink_articles(ctx: ActionContext, job: dict, dry_run: bool) -> tuple[str, str | None]:
    """
    해당 문서 본문에서 법령 article 참조를 추출하여 document_law_map 업서트.
    반환: (status, note)
    """
    from scripts.db.link_forms_to_articles import find_article_refs

    doc = _resolve_document(ctx.conn, job["source_type"], job["source_id"])
    if not doc:
        return ("skipped", "document not found")
    doc_id, title, body = doc
    text = (title or "") + "\n" + (body or "")
    if len(text) < 40:
        return ("skipped", "body too short")

    refs = find_article_refs(text, ctx.law_names_sorted())
    if not refs:
        return ("done", "no article refs")

    art_idx = ctx.article_index()
    inserted = 0
    seen: set[tuple[str, str]] = set()
    with ctx.conn.cursor() as cur:
        for law, art_no in refs:
            if (law, art_no) in seen:
                continue
            seen.add((law, art_no))
            art_doc_id = art_idx.get((law, art_no))
            if not art_doc_id:
                continue
            if dry_run:
                inserted += 1
                continue
            cur.execute(
                """
                INSERT INTO document_law_map (document_id, law_document_id, law_name, match_type)
                VALUES (%s, %s, %s, 'article')
                ON CONFLICT (document_id, law_document_id) DO UPDATE
                   SET match_type = CASE
                        WHEN document_law_map.match_type = 'law_name' THEN 'article'
                        ELSE document_law_map.match_type
                     END
                """,
                (doc_id, art_doc_id, law),
            )
            if cur.rowcount > 0:
                inserted += 1
    if not dry_run:
        ctx.conn.commit()
    return ("done", f"article_refs={len(refs)} inserted={inserted}")


def action_refresh_hwpx_path(ctx: ActionContext, job: dict, dry_run: bool) -> tuple[str, str | None]:
    """
    data/raw 에서 source_id 를 포함하는 HWPX 파일을 찾으면 documents.hwpx_path 갱신.
    찾지 못하면 skipped (재시도 대상 아님).
    """
    doc = _resolve_document(ctx.conn, job["source_type"], job["source_id"])
    if not doc:
        return ("skipped", "document not found")
    doc_id, _title, _body = doc

    raw = ctx.raw_index()
    sid = job["source_id"]
    hit: Path | None = None
    for (_src, stem), p in raw.items():
        if sid and sid in stem:
            hit = p
            break
    if hit is None:
        return ("skipped", "no raw hwpx match")

    if dry_run:
        return ("done", f"would set hwpx_path={hit}")
    with ctx.conn.cursor() as cur:
        cur.execute(
            "UPDATE documents SET hwpx_path=%s, updated_at=now() WHERE id=%s",
            (str(hit), doc_id),
        )
    ctx.conn.commit()
    return ("done", f"hwpx_path={hit}")


def _extract_pdf_text(data: bytes, max_chars: int = 20000) -> str:
    """pypdf 로 텍스트 추출. 실패 시 빈 문자열."""
    try:
        import io as _io
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(_io.BytesIO(data))
        parts: list[str] = []
        total = 0
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            if t:
                parts.append(t)
                total += len(t)
                if total >= max_chars:
                    break
        return ("\n".join(parts))[:max_chars]
    except Exception:
        return ""


def action_kosha_redownload(ctx: ActionContext, job: dict, dry_run: bool) -> tuple[str, str | None]:
    """
    kosha status='draft' 문서를 file_url 로 재다운로드 → PDF 저장 → 텍스트 추출 →
    body_text/pdf_path/file_sha256/content_length/has_text/status='active' 업데이트.

    실패/재시도 정책
      - file_url 없음 → skipped (재시도 대상 아님)
      - HTTP 오류/타임아웃 → 예외 raise → 상위 retry_count 증가
      - PDF 가 아닌 응답 → skipped
      - 텍스트 추출 500자 미만 → 저장은 하되 has_text=False
    """
    import hashlib as _hashlib
    import os as _os
    import requests as _requests  # type: ignore

    src_type = job["source_type"]
    src_id = job["source_id"]
    if src_type != "kosha":
        return ("skipped", f"unsupported source_type={src_type}")

    with ctx.conn.cursor() as cur:
        cur.execute(
            "SELECT id, COALESCE(file_url,''), COALESCE(status,''), "
            "       COALESCE(pdf_path,''), COALESCE(file_sha256,''), "
            "       doc_category "
            "FROM documents WHERE source_type=%s AND source_id=%s",
            (src_type, src_id),
        )
        row = cur.fetchone()
    if not row:
        return ("skipped", "document not found")
    doc_id, file_url, status, existing_pdf_path, existing_sha, doc_category = row

    if status not in ("draft", "pending"):
        # 이미 active/excluded 이면 큐 노이즈 — 재처리 금지
        return ("skipped", f"status={status} (already processed)")
    if not file_url:
        return ("skipped", "file_url missing")

    if dry_run:
        return ("done", f"would GET {file_url[:60]}...")

    ua = _os.getenv("KOSHA_USER_AGENT") or (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    resp = _requests.get(
        file_url, headers={"User-Agent": ua, "Accept-Language": "ko-KR,ko;q=0.9"},
        timeout=(10, 45), allow_redirects=True,
    )
    resp.raise_for_status()
    data = resp.content
    if not data or not data.startswith(b"%PDF"):
        return ("skipped", "response is not PDF")

    sha256 = _hashlib.sha256(data).hexdigest()

    # 이미 동일 SHA 가 반영되어 있으면 no-op
    if existing_sha and existing_sha == sha256 and status == "active":
        return ("done", "identical sha — no update")

    # 저장 경로: /app/data/raw/kosha/pdf/{category or 'misc'}/{source_id}.pdf
    data_dir = Path(_os.getenv("DATA_DIR", "/app/data"))
    category_dir = (doc_category or "misc").replace("/", "_")
    pdf_dir = data_dir / "raw" / "kosha" / "pdf" / category_dir
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{src_id}.pdf"
    pdf_path.write_bytes(data)

    text = _extract_pdf_text(data)
    has_text = bool(text) and len(text) >= 500
    content_length = len(text)

    # status 를 active 로 승격하되, 텍스트가 사실상 없으면 draft 유지
    new_status = "active" if has_text else "draft"

    with ctx.conn.cursor() as cur:
        cur.execute(
            """
            UPDATE documents
               SET body_text      = %s,
                   pdf_path       = %s,
                   file_sha256    = %s,
                   content_length = %s,
                   has_text       = %s,
                   status         = %s,
                   collected_at   = COALESCE(collected_at, now()),
                   updated_at     = now()
             WHERE id = %s
            """,
            (text or None, str(pdf_path), sha256, content_length, has_text, new_status, doc_id),
        )
    ctx.conn.commit()

    note = f"size={len(data)} sha={sha256[:10]} text={content_length} status={new_status}"
    return ("done", note)


ACTIONS = {
    "relink_articles":   action_relink_articles,
    "refresh_hwpx_path": action_refresh_hwpx_path,
    "kosha_redownload":  action_kosha_redownload,
}


# ---------------------------------------------------------------------------
# 배치 실행
# ---------------------------------------------------------------------------

def _insert_collection_run(conn, summary: dict, source_type: str = "ops_mixed") -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO collection_runs
                    (source_type, run_date, status, total_count, success_count, fail_count,
                     note, started_at, finished_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    source_type, summary["run_date"], summary["status"],
                    summary["total"], summary["success"], summary["failed"],
                    summary["note"], summary["started_at"], summary["finished_at"],
                ),
            )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logging.getLogger("ops.bg_collect").warning("collection_runs insert failed: %r", exc)


def process_batch(limit: int, sources: set[str] | None, actions: set[str] | None,
                  dry_run: bool, log: logging.Logger) -> dict:
    started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    jobs = read_all()
    if not jobs:
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0,
                "run_date": date.today(),
                "started_at": started_at, "finished_at": started_at,
                "status": "ok", "note": "queue empty"}

    # 선택 대상: pending 만, 우선순위 낮은값 먼저, retry_count 제한 내
    candidates = [j for j in jobs
                  if j.get("status") == "pending"
                  and j.get("retry_count", 0) < MAX_RETRY
                  and (actions is None or j.get("action") in actions)
                  and (sources is None or j.get("source_type") in sources)]
    candidates.sort(key=lambda j: (j.get("priority", 5), j.get("job_id", "")))
    picks = candidates[:max(1, limit)]

    if not picks:
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0,
                "run_date": date.today(),
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "status": "ok", "note": "no eligible jobs"}

    conn = get_db_connection()
    ctx = ActionContext(conn)

    success = failed = skipped = 0
    notes_failed: list[str] = []

    # in-place 상태 변경을 위해 index
    by_id = {j["job_id"]: j for j in jobs}

    for j in picks:
        handler = ACTIONS.get(j.get("action"))
        if handler is None:
            j["status"] = "skipped"
            j["last_error"] = f"unknown action: {j.get('action')}"
            j["updated_at"] = now_iso()
            skipped += 1
            continue

        j["status"] = "running"
        j["updated_at"] = now_iso()
        try:
            status, note = handler(ctx, j, dry_run)
        except Exception as exc:
            conn.rollback()
            j["retry_count"] = int(j.get("retry_count", 0)) + 1
            j["status"] = "failed"
            j["last_error"] = f"{type(exc).__name__}: {exc}"
            j["updated_at"] = now_iso()
            failed += 1
            msg = f"{j['job_id']} FAILED retry={j['retry_count']} err={j['last_error']}"
            log.error(msg)
            if len(notes_failed) < 10:
                notes_failed.append(msg[:240])
            continue

        j["status"] = status
        j["last_error"] = None
        j["note"] = note
        j["updated_at"] = now_iso()
        if status == "done":
            success += 1
        elif status == "skipped":
            skipped += 1
        else:
            success += 1  # boundary 처리

        log.info("%s %s %s", j["job_id"], status.upper(), note or "")

    try:
        conn.close()
    except Exception:
        pass

    # 큐 저장 — dry-run 에서는 건드리지 않음
    if not dry_run:
        write_all(list(by_id.values()))

    finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
    summary = {
        "run_date": date.today(),
        "started_at": started_at,
        "finished_at": finished_at,
        "total": len(picks),
        "success": success,
        "failed": failed,
        "skipped": skipped,
        "status": "ok" if failed == 0 else "partial",
        "note": ("; ".join(notes_failed))[:480] or None,
    }
    # collection_runs 기록 — dry-run 에서는 생략
    if not dry_run:
        try:
            c2 = get_db_connection()
            _insert_collection_run(c2, summary, source_type="ops_mixed")
            c2.close()
        except Exception as exc:
            log.warning("collection_runs log failed: %r", exc)

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_STOP = False


def _install_signal_handlers(log: logging.Logger) -> None:
    def _h(signum, _frame):
        global _STOP
        _STOP = True
        log.info("signal %d received — stopping after current batch", signum)
    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(s, _h)
        except Exception:
            pass


def _write_pid() -> None:
    try:
        _pid_path().write_text(str(os.getpid()))
    except Exception:
        pass


def _parse_csv(v: str | None) -> set[str] | None:
    if not v:
        return None
    out = {t.strip() for t in v.split(",") if t.strip()}
    return out or None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    ap.add_argument("--sources", type=str, default="")
    ap.add_argument("--actions", type=str, default="")
    ap.add_argument("--sleep-seconds", type=int, default=DEFAULT_SLEEP)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.once and not args.loop:
        args.once = True

    log = _setup_logger()
    _install_signal_handlers(log)
    _write_pid()

    log.info(
        "START pid=%d queue=%s limit=%d sources=%s actions=%s dry_run=%s loop=%s sleep=%d",
        os.getpid(), master_path(), args.limit,
        args.sources or "*", args.actions or "*",
        args.dry_run, args.loop, args.sleep_seconds,
    )

    sources = _parse_csv(args.sources)
    actions = _parse_csv(args.actions)

    try:
        while True:
            summary = process_batch(
                limit=args.limit, sources=sources, actions=actions,
                dry_run=args.dry_run, log=log,
            )
            log.info(
                "BATCH total=%d success=%d failed=%d skipped=%d status=%s",
                summary["total"], summary["success"], summary["failed"],
                summary["skipped"], summary["status"],
            )
            if args.once or _STOP:
                break
            if summary["total"] == 0:
                # pending 없으면 더 길게 쉬자
                time.sleep(max(args.sleep_seconds, 60))
            else:
                time.sleep(max(args.sleep_seconds, 1))
    finally:
        try:
            if _pid_path().exists():
                _pid_path().unlink()
        except Exception:
            pass

    log.info("STOP pid=%d", os.getpid())
    return 0


if __name__ == "__main__":
    sys.exit(main())

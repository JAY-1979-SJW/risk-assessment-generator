import os
import sys
import json
import time
import asyncio
import logging
import textwrap
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Query, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from openai import OpenAI

# ── 경로 설정 ────────────────────────────────────────────────────────────────
DEVLOG_DIR = Path(os.getenv("DEVLOG_DIR", "/app/docs/devlog"))
CHANGE_HISTORY_PATH = Path(os.getenv("CHANGE_HISTORY_PATH", "/app/logs/change_history.jsonl"))
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

SCRAPER_LOGS_DIR = Path(os.getenv("SCRAPER_LOGS_DIR", "/app/scraper_logs"))

# 감시 대상 로그 파일 (우선순위 순)
_WATCH_LOGS = [
    ("run_history", "실행이력"),
    ("parser",      "파서"),
    ("pipeline",    "파이프라인"),
]

# ── 로거 설정 ────────────────────────────────────────────────────────────────
def _make_logger(name: str, filename: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(LOG_DIR / filename, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(sh)
    return logger

access_log = _make_logger("kras.access", "backend_access.log")
error_log  = _make_logger("kras.error",  "backend_error.log")

# ── 인증 ────────────────────────────────────────────────────────────────────
_internal_key_header = APIKeyHeader(name="X-Internal-Key", auto_error=False)


def _require_internal_key(key: str = Security(_internal_key_header)):
    """INTERNAL_API_KEY가 설정된 경우에만 인증 강제. 미설정 시 통과(개발 편의)."""
    if INTERNAL_API_KEY and key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Internal-Key header")

app = FastAPI(title="KRAS API", version="2.0.0")

# ── 라우터 등록 ──────────────────────────────────────────────────────────────
from routers import projects, company, organization, assessments, forms, templates, export, engine_results
app.include_router(projects.router,       prefix="/api")
app.include_router(company.router,        prefix="/api")
app.include_router(organization.router,   prefix="/api")
app.include_router(assessments.router,    prefix="/api")
app.include_router(forms.router,          prefix="/api")
app.include_router(templates.router,      prefix="/api")
app.include_router(export.router,         prefix="/api")
app.include_router(engine_results.router, prefix="/api")

_CORS_ORIGINS = [
    o.strip() for o in
    os.getenv("CORS_ORIGINS", "https://kras.haehan-ai.kr").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    client_ip = request.client.host if request.client else "-"
    try:
        response = await call_next(request)
        elapsed = round((time.monotonic() - start) * 1000)
        access_log.info(json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": elapsed,
            "ip": client_ip,
        }, ensure_ascii=False))
        return response
    except Exception as exc:
        elapsed = round((time.monotonic() - start) * 1000)
        error_log.error(json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "method": request.method,
            "path": request.url.path,
            "error": str(exc),
            "ms": elapsed,
            "ip": client_ip,
        }, ensure_ascii=False))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


DATABASE_URL = os.getenv("DATABASE_URL")
COMMON_DATA_URL = os.getenv("COMMON_DATA_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_CONTEXT_CHARS = 12000

RISK_CATEGORIES = [
    "기계적 요인", "전기적 요인", "화학(물질)적 요인",
    "작업환경 요인", "작업특성 요인", "기타",
]

SYSTEM_PROMPT = textwrap.dedent("""
당신은 산업안전보건 전문가입니다.
제공된 안전보건 자료(raw_text)를 분석하여 위험성평가 항목을 JSON으로 추출합니다.

반드시 다음 JSON 배열 형식으로만 응답하세요. 설명문 없이 JSON만 출력:
[
  {
    "세부작업명": "작업 설명 (20자 이내)",
    "위험분류": "기계적 요인|전기적 요인|화학(물질)적 요인|작업환경 요인|작업특성 요인|기타 중 하나",
    "위험세부분류": "협착|추락|감전|폭발|분진|소음|화재|절단|충돌|기타 중 하나",
    "위험상황": "구체적인 위험 발생 상황과 예상 결과 (50자 이내)",
    "관련근거": "산업안전보건법 또는 안전보건규칙 조항 (없으면 빈 문자열)",
    "현재조치": "현재 시행 중인 안전보건조치 (없으면 빈 문자열)",
    "가능성": 2,
    "중대성": 2,
    "감소대책": "추가 위험 감소 대책 (50자 이내)"
  }
]

가능성/중대성 기준: 3(상)=일상적, 2(중)=가끔, 1(하)=드물게
위험성 = 가능성 × 중대성 (6이상=높음, 3~4=보통, 1~2=낮음)
최대 15개 항목. 실제 자료에 근거한 내용만 작성.
""").strip()


# ── AI 로그 헬퍼 ────────────────────────────────────────────────────────────

ai_log = _make_logger("kras.ai", "ai_generate.log")

def _write_ai_log(record: dict):
    ai_log.info(json.dumps(record, ensure_ascii=False))
    jsonl_path = LOG_DIR / "ai_generate.jsonl"
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── DB 헬퍼 ─────────────────────────────────────────────────────────────────

def _get_conn():
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")
    return psycopg2.connect(DATABASE_URL)


def _get_kosha_conn():
    url = COMMON_DATA_URL or DATABASE_URL
    if not url:
        raise HTTPException(status_code=503, detail="COMMON_DATA_URL not configured")
    return psycopg2.connect(url)


def _db_stats():
    conn = _get_kosha_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM kosha_materials")
        materials = cur.fetchone()[0]
        cur.execute("SELECT parse_status, COUNT(*) FROM kosha_material_files GROUP BY parse_status")
        files = dict(cur.fetchall())
        cur.execute("SELECT COUNT(*) FROM kosha_material_chunks")
        chunks = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM kosha_chunk_tags")
        tags = cur.fetchone()[0]
        return {"materials": materials, "files": files, "chunks": chunks, "tags": tags}
    finally:
        conn.close()


def _fetch_chunks(trade_type: str, work_type: str = None, limit: int = 30) -> list:
    params = [f"%{trade_type}%", f"%{trade_type}%"]
    work_filter = ""
    if work_type:
        work_filter = "AND (kct.work_type ILIKE %s OR kmc.work_type ILIKE %s)"
        params += [f"%{work_type}%", f"%{work_type}%"]
    params.append(limit)

    sql = f"""
        SELECT kmc.raw_text, kct.trade_type, kct.work_type, kct.hazard_type
        FROM kosha_material_chunks kmc
        JOIN kosha_chunk_tags kct ON kct.chunk_id = kmc.id
        WHERE (kct.trade_type ILIKE %s OR kmc.work_type ILIKE %s)
          {work_filter}
          AND kmc.raw_text IS NOT NULL
          AND LENGTH(kmc.raw_text) > 100
        ORDER BY kct.confidence DESC NULLS LAST, kmc.id DESC
        LIMIT %s
    """
    conn = _get_kosha_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── OpenAI 헬퍼 ──────────────────────────────────────────────────────────────

def _normalize_items(items: list, process_name: str) -> list:
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            prob = max(1, min(3, int(item.get("가능성", 2))))
            sev = max(1, min(3, int(item.get("중대성", 2))))
        except (ValueError, TypeError):
            prob, sev = 2, 2

        score = prob * sev
        level = "높음" if score >= 6 else ("보통" if score >= 3 else "낮음")
        cat = item.get("위험분류", "기타")
        if cat not in RISK_CATEGORIES:
            cat = "기타"

        after_prob = max(1, prob - 1)
        after_score = after_prob * sev
        after_level = "높음" if after_score >= 6 else ("보통" if after_score >= 3 else "낮음")

        result.append({
            "공정명": process_name,
            "세부작업명": item.get("세부작업명", ""),
            "위험분류": cat,
            "위험세부분류": item.get("위험세부분류", ""),
            "위험상황": item.get("위험상황", ""),
            "관련근거": item.get("관련근거", ""),
            "현재조치": item.get("현재조치", ""),
            "가능성": prob,
            "중대성": sev,
            "위험성": score,
            "위험등급": level,
            "감소대책": item.get("감소대책", ""),
            "개선후가능성": after_prob,
            "개선후위험성": after_score,
            "개선후위험등급": after_level,
        })
    return result


# ── 엔드포인트 ───────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    result = {"status": "ok", "api": "up"}
    try:
        conn = _get_conn()
        conn.close()
        result["db"] = "connected"
    except Exception as e:
        result["status"] = "degraded"
        result["db"] = "error"
        result["db_error"] = str(e)
        return result
    try:
        result["kosha_db"] = "connected"
        result["kosha"] = _db_stats()
    except Exception as e:
        result["status"] = "degraded"
        result["kosha_db"] = "error"
        result["kosha_db_error"] = str(e)
    return result


@app.get("/admin/kosha/stats")
def kosha_stats():
    """KOSHA 수집 DB 상세 현황."""
    conn = _get_kosha_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT COUNT(*) AS cnt FROM kosha_materials")
        total_materials = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM kosha_material_files")
        total_files = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM kosha_material_chunks")
        total_chunks = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM kosha_chunk_tags")
        total_tags = cur.fetchone()["cnt"]

        cur.execute("""
            SELECT list_type, COUNT(*) AS cnt
            FROM kosha_materials
            GROUP BY list_type ORDER BY cnt DESC
        """)
        by_list_type = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT download_status, parse_status, COUNT(*) AS cnt
            FROM kosha_material_files
            GROUP BY download_status, parse_status ORDER BY cnt DESC
        """)
        by_file_status = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT file_type, COUNT(*) AS cnt
            FROM kosha_material_files
            GROUP BY file_type ORDER BY cnt DESC
        """)
        by_file_type = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT trade_type, COUNT(*) AS cnt
            FROM kosha_chunk_tags
            WHERE trade_type IS NOT NULL
            GROUP BY trade_type ORDER BY cnt DESC LIMIT 20
        """)
        top_trades = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT m.id, m.title, m.list_type, m.created_at::text AS created_at
            FROM kosha_materials m
            ORDER BY m.created_at DESC LIMIT 10
        """)
        recent_materials = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('kosha_materials','kosha_material_files','kosha_material_chunks','kosha_chunk_tags')
            ORDER BY table_name, ordinal_position
        """)
        schema_rows = cur.fetchall()
        schema: dict = {}
        for row in schema_rows:
            pass
        cur.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('kosha_materials','kosha_material_files','kosha_material_chunks','kosha_chunk_tags')
            ORDER BY table_name, ordinal_position
        """)
        schema_full = {}
        for row in cur.fetchall():
            t = row["table_name"]
            schema_full.setdefault(t, []).append({"column": row["column_name"], "type": row["data_type"]})

        return {
            "summary": {
                "materials": total_materials,
                "files": total_files,
                "chunks": total_chunks,
                "tags": total_tags,
            },
            "by_list_type": by_list_type,
            "by_file_status": by_file_status,
            "by_file_type": by_file_type,
            "top_trades": top_trades,
            "recent_materials": recent_materials,
            "schema": schema_full,
        }
    finally:
        conn.close()


@app.get("/admin/kosha/stream")
async def stream_kosha_logs(
    logs: str = Query("run_history,parser", description="쉼표 구분 로그명"),
    tail: int = Query(100, ge=0, le=500, description="초기 전송 최근 N줄"),
):
    """SSE: KOSHA 파서 로그 실시간 스트리밍.
    logs 파라미터: run_history, parser, pipeline (쉼표 구분).
    브라우저 EventSource 재연결 시 자동 재시도."""

    import re
    _ansi = re.compile(r'\x1b\[[0-9;]*m')

    requested = [n.strip() for n in logs.split(',')]
    paths = []
    for name in requested:
        p = SCRAPER_LOGS_DIR / f'{name}.log'
        if p.exists():
            paths.append((name, p))

    async def generate():
        # ── 연결 확인 이벤트
        yield 'event: connected\ndata: {"logs": %s}\n\n' % json.dumps(requested)

        if not paths:
            yield 'event: warn\ndata: {"msg": "로그 파일 없음 — 볼륨 마운트 확인 필요"}\n\n'
            return

        handles: dict[str, object] = {}
        try:
            # ── 초기: 각 파일 마지막 tail줄 전송
            for name, path in paths:
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                    recent = lines[-tail:] if tail else []
                    for line in recent:
                        clean = _ansi.sub('', line.rstrip())
                        if clean:
                            payload = json.dumps({"src": name, "line": clean}, ensure_ascii=False)
                            yield f'data: {payload}\n\n'
                    # 파일 핸들 열어두고 끝으로 이동
                    fh = open(path, 'r', encoding='utf-8', errors='replace')
                    fh.seek(0, 2)
                    handles[name] = fh
                except OSError:
                    pass

            # 구분선 이벤트
            yield 'event: tail_start\ndata: {}\n\n'

            # ── 실시간 tail
            while True:
                any_line = False
                for name, fh in list(handles.items()):
                    try:
                        while True:
                            line = fh.readline()
                            if not line:
                                break
                            clean = _ansi.sub('', line.rstrip())
                            if clean:
                                payload = json.dumps({"src": name, "line": clean}, ensure_ascii=False)
                                yield f'data: {payload}\n\n'
                                any_line = True
                    except OSError:
                        pass

                if not any_line:
                    # keepalive — 프록시/브라우저 연결 유지
                    yield ': keepalive\n\n'
                    await asyncio.sleep(2)

        except asyncio.CancelledError:
            pass
        finally:
            for fh in handles.values():
                try:
                    fh.close()
                except Exception:
                    pass

    return StreamingResponse(
        generate(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@app.get("/trades")
def list_trades(q: Optional[str] = Query(None, description="검색어 (부분 일치)")):
    """공종(trade_type) 목록 반환. q로 필터링 가능."""
    conn = _get_kosha_conn()
    try:
        with conn.cursor() as cur:
            if q:
                cur.execute(
                    "SELECT DISTINCT trade_type FROM kosha_chunk_tags "
                    "WHERE trade_type ILIKE %s ORDER BY trade_type LIMIT 100",
                    (f"%{q}%",),
                )
                return {"trades": [r[0] for r in cur.fetchall()]}
            else:
                cur.execute(
                    "SELECT trade_type, COUNT(*) AS cnt FROM kosha_chunk_tags "
                    "GROUP BY trade_type ORDER BY cnt DESC LIMIT 100"
                )
                return {"trades": [{"trade_type": r[0], "count": r[1]} for r in cur.fetchall()]}
    finally:
        conn.close()


@app.get("/kosha/search")
def search_kosha(
    q: str = Query(..., description="검색 키워드"),
    limit: int = Query(10, ge=1, le=50),
):
    """KOSHA 청크 키워드 검색 (raw_text 미리보기 포함)."""
    conn = _get_kosha_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT kmc.id, kmc.work_type, kmc.hazard_type,
                       LEFT(kmc.raw_text, 300) AS preview,
                       kct.trade_type, kct.confidence
                FROM kosha_material_chunks kmc
                LEFT JOIN kosha_chunk_tags kct ON kct.chunk_id = kmc.id
                WHERE kmc.raw_text ILIKE %s
                  AND LENGTH(kmc.raw_text) > 100
                ORDER BY kct.confidence DESC NULLS LAST
                LIMIT %s
                """,
                (f"%{q}%", limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
        return {"query": q, "count": len(rows), "results": rows}
    finally:
        conn.close()


class GenerateRequest(BaseModel):
    process_name: str
    trade_type: str
    work_type: Optional[str] = ""


@app.post("/generate")
def generate_risk(req: GenerateRequest):
    """KOSHA DB + OpenAI로 위험성평가 항목 자동 생성."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")

    chunks = _fetch_chunks(req.trade_type, req.work_type or None)
    if not chunks:
        raise HTTPException(
            status_code=404,
            detail=f"'{req.trade_type}' 관련 KOSHA 자료를 찾지 못했습니다.",
        )

    raw_texts = [c["raw_text"] for c in chunks if c.get("raw_text")]
    combined = "\n\n---\n\n".join(raw_texts)
    if len(combined) > MAX_CONTEXT_CHARS:
        combined = combined[:MAX_CONTEXT_CHARS] + "\n...(이하 생략)"

    user_msg = (
        f"공정명: {req.process_name}\n"
        f"작업 유형: {req.trade_type} {(req.work_type or '').strip()}\n\n"
        f"=== KOSHA 안전보건 자료 ===\n{combined}"
    )

    ai_start = time.monotonic()
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    ai_ms = round((time.monotonic() - ai_start) * 1000)

    content = response.choices[0].message.content
    parsed = json.loads(content)
    if isinstance(parsed, dict):
        for v in parsed.values():
            if isinstance(v, list):
                parsed = v
                break

    items = _normalize_items(parsed, req.process_name)

    # AI 생성 로그 기록
    _write_ai_log({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "process_name": req.process_name,
        "trade_type": req.trade_type,
        "work_type": req.work_type or "",
        "model": OPENAI_MODEL,
        "chunks_used": len(chunks),
        "context_chars": len(combined),
        "items_generated": len(items),
        "ai_ms": ai_ms,
        "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
        "completion_tokens": response.usage.completion_tokens if response.usage else None,
    })

    return {
        "process_name": req.process_name,
        "trade_type": req.trade_type,
        "chunks_used": len(chunks),
        "count": len(items),
        "items": items,
    }


# ── Internal: devlog (조회 전용) ─────────────────────────────────────────────
# 추후 인증 미들웨어를 붙이려면 이 라우터 그룹에 Depends(verify_token) 추가

@app.get("/internal/devlog", dependencies=[Security(_require_internal_key)])
def list_devlog():
    """docs/devlog/ 내 마크다운 파일 목록 (최신순)."""
    if not DEVLOG_DIR.exists():
        return {"files": []}

    files = sorted(
        [f for f in DEVLOG_DIR.iterdir() if f.suffix == ".md" and not f.name.startswith("_")],
        key=lambda f: f.name,
        reverse=True,
    )
    return {
        "files": [
            {"filename": f.name, "size": f.stat().st_size}
            for f in files
        ]
    }


@app.get("/internal/devlog/{filename}", dependencies=[Security(_require_internal_key)])
def get_devlog(filename: str):
    """특정 devlog 마크다운 파일 내용 반환."""
    if "/" in filename or "\\" in filename or filename.startswith("_"):
        raise HTTPException(status_code=400, detail="Invalid filename")

    path = DEVLOG_DIR / filename
    if not path.exists() or path.suffix != ".md":
        raise HTTPException(status_code=404, detail="Not found")

    return {"filename": filename, "content": path.read_text(encoding="utf-8")}


@app.get("/internal/change-history", dependencies=[Security(_require_internal_key)])
def get_change_history(n: int = Query(20, ge=1, le=200, description="최근 N건")):
    """change_history.jsonl 최근 N건 (timestamp 역순)."""
    if not CHANGE_HISTORY_PATH.exists():
        return {"items": []}

    lines = CHANGE_HISTORY_PATH.read_text(encoding="utf-8").strip().splitlines()
    records = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return {"count": len(records), "items": records[:n]}

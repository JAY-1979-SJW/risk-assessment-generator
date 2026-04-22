"""
작업일보 텍스트 → work_types / equipment / hazards 코드 매핑 엔진 (1차, 규칙 기반).

- DB(hazards, work_types, equipment)에서 code / name 만 조회한다.
- 키워드 포함 여부로 매칭 점수를 산출한다.
- 위험도 계산 / 평가표 생성 / 법 매칭은 수행하지 않는다.

점수 규칙:
    name 완전 포함  : +2
    code 포함       : +1
    부분 포함(단어) : +1  (name 완전 포함이 아닐 때 1회만 가산)

CLI:
    python scripts/engine/map_worklog.py "천장 배관 작업, 사다리 사용"
    echo "천장 작업" | python scripts/engine/map_worklog.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

def _load_dotenv_files() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for env_path in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


def get_db_connection():
    """Return a new psycopg2 connection using project env vars. No hardcoding."""
    import psycopg2
    _load_dotenv_files()

    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)

    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    database = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")

    if not (host and database and user):
        missing = [k for k, v in [("host", host), ("database", database), ("user", user)] if not v]
        raise RuntimeError(f"DB 접속 정보 누락: {missing}")

    return psycopg2.connect(
        host=host, port=int(port), dbname=database, user=user, password=password or ""
    )


# ---------------------------------------------------------------------------
# 매칭 로직
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")

# 부분 매칭에서 제외할 공통 어미·조사. name 에 공통적으로 붙어 과다 매칭을 일으키는 단어만 최소로 추림.
_STOPWORDS = {
    "작업", "공사", "중", "시", "때", "등", "및", "의", "는", "가", "을", "를", "에", "로", "서",
}


def normalize_text(text: str) -> str:
    """소문자화 + 연속 공백 단일화."""
    if not text:
        return ""
    return _WS.sub(" ", text.strip().lower())


def _score_one(norm_text: str, code: str, name: str) -> int:
    code_l = (code or "").strip().lower()
    name_l = (name or "").strip().lower()

    score = 0
    name_full = bool(name_l and name_l in norm_text)
    if name_full:
        score += 2
    if code_l and code_l in norm_text:
        score += 1
    if not name_full:
        tokens = [
            t for t in name_l.split()
            if len(t) >= 2 and t not in _STOPWORDS
        ]
        if any(t in norm_text for t in tokens):
            score += 1
    return score


def match_items(text: str, rows: list[tuple[str, str]]) -> list[dict]:
    """
    text : 원본 작업일보 텍스트
    rows : [(code, name), ...]
    return : [{code, name, score}, ...] score>=1, score 내림차순
    """
    norm = normalize_text(text)
    if not norm:
        return []
    matched: list[dict] = []
    for code, name in rows:
        sc = _score_one(norm, code, name)
        if sc >= 1:
            matched.append({"code": code, "name": name, "score": sc})
    matched.sort(key=lambda r: (-r["score"], r["code"]))
    return matched


# ---------------------------------------------------------------------------
# 엔진
# ---------------------------------------------------------------------------

def _fetch(conn, table: str, code_col: str, name_col: str) -> list[tuple[str, str]]:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {code_col}, {name_col} FROM {table} "
            f"WHERE is_active = TRUE"
        )
        return [(r[0], r[1]) for r in cur.fetchall()]


def map_worklog(text) -> dict:
    """
    입력 : str 또는 {'work_log': str}
    출력 : { input, work_types[], equipment[], hazards[] }
    """
    if isinstance(text, dict):
        text = text.get("work_log", "")
    if not isinstance(text, str):
        raise TypeError("text must be str or dict with 'work_log'")

    conn = get_db_connection()
    try:
        hazards_rows = _fetch(conn, "hazards", "hazard_code", "hazard_name")
        work_rows = _fetch(conn, "work_types", "work_type_code", "work_type_name")
        equip_rows = _fetch(conn, "equipment", "equipment_code", "equipment_name")
    finally:
        conn.close()

    return {
        "input": text,
        "work_types": match_items(text, work_rows),
        "equipment": match_items(text, equip_rows),
        "hazards": match_items(text, hazards_rows),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _read_input_from_argv_or_stdin() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def run() -> int:
    raw = _read_input_from_argv_or_stdin()
    if not raw:
        print(
            "usage: python scripts/engine/map_worklog.py <text>\n"
            "       echo <text> | python scripts/engine/map_worklog.py",
            file=sys.stderr,
        )
        return 2
    try:
        result = map_worklog(raw)
    except Exception as exc:
        print(f"[FAIL] {exc!r}", file=sys.stderr)
        return 3
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(run())

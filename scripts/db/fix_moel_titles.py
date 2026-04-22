"""
MOEL 문서 제목 후처리 수정.

이슈:
    moel_forms_scraper.py 의 detail 파싱이 class="subject" 를 못 찾으면
    페이지 <title>고용노동부</title> 로 fallback 해 제목이 깨짐.

수정 전략:
    data/raw/moel_forms/policy_data/list_all.json 의 "filtered" 항목에는
    리스트 페이지에서 정상 추출된 title 이 있으므로, 이를 이용해
    UPDATE documents SET title = list_title WHERE source_type='moel_form' ...
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIST_JSON = PROJECT_ROOT / "data" / "raw" / "moel_forms" / "policy_data" / "list_all.json"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for p in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if p.exists():
            load_dotenv(p, override=False)


def get_conn():
    import psycopg2
    _load_dotenv()
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    db = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    pw = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    if not (host and db and user):
        raise RuntimeError("DB 접속 정보 누락")
    return psycopg2.connect(host=host, port=int(port), dbname=db, user=user, password=pw or "")


def main() -> int:
    if not LIST_JSON.exists():
        print(f"[FAIL] list_all.json 없음: {LIST_JSON}", file=sys.stderr)
        return 2
    data = json.loads(LIST_JSON.read_text(encoding="utf-8"))
    filtered = data.get("filtered") or []
    print(f"[LOAD] filtered items: {len(filtered)}")

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM documents "
            "WHERE source_type='moel_form' AND "
            "(title IS NULL OR title='고용노동부' OR LENGTH(title) < 10)"
        )
        bad_before = int(cur.fetchone()[0])
    print(f"[BEFORE] 깨진 title: {bad_before}")

    updated = 0
    with conn.cursor() as cur:
        for it in filtered:
            bbs = str(it.get("bbs_seq") or "").strip()
            title = str(it.get("title") or "").strip()
            if not bbs or not title:
                continue
            cur.execute(
                """UPDATE documents
                   SET title = %s, title_normalized = %s, updated_at = NOW()
                   WHERE source_type = 'moel_form'
                     AND source_id = %s
                     AND (title IS NULL OR title = '고용노동부' OR LENGTH(title) < 10)""",
                (title, title, bbs),
            )
            updated += cur.rowcount
    conn.commit()
    print(f"[UPDATED] {updated}")

    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM documents "
            "WHERE source_type='moel_form' AND "
            "(title IS NULL OR title='고용노동부' OR LENGTH(title) < 10)"
        )
        bad_after = int(cur.fetchone()[0])
        cur.execute(
            "SELECT source_id, LEFT(title, 70) FROM documents "
            "WHERE source_type='moel_form' ORDER BY id DESC LIMIT 5"
        )
        samples = cur.fetchall()
    print(f"[AFTER ] 깨진 title: {bad_after}")
    print("[SAMPLE]")
    for r in samples:
        print(f"  {r[0]}: {r[1]}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

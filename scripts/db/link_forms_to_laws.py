"""
서식 ↔ 법령 연결기 (document_law_map).

목적
    서식(kosha_form/moel_form/licbyl) 본문에서 법령명을 추출하여
    law 문서와 매핑한다. 위험성평가 → 법령 근거 → 서식 추천의 골격.

테이블
    document_law_map (자동 생성, IF NOT EXISTS)
        document_id      BIGINT  -- 서식(또는 임의 문서) id
        law_document_id  BIGINT  -- 매핑되는 law 문서 id
        law_name         TEXT    -- 매칭된 법령명
        match_type       VARCHAR(20) DEFAULT 'law_name'
        is_primary       BOOLEAN DEFAULT FALSE
        PRIMARY KEY (document_id, law_document_id)
        FK → documents(id)

매칭 규칙
    - law_meta 의 distinct law_name 전수를 인덱스화 (긴 이름 먼저)
    - 서식 title + body 에서 law_name 문자열 포함 여부
    - law_name 당 대표 law doc:
        1) law_statute (source_type='law' AND doc_category='law_statute' AND title=law_name)
        2) 없으면 그 law_name 의 첫 law_article (ORDER BY id ASC)

원칙
    - ON CONFLICT DO NOTHING
    - 기존 서식 body/metadata 변경 없음
    - 법령 문서 변경 없음
    - 신규 수집 금지
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()


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


FORM_SOURCES = ("kosha_form", "moel_form", "licbyl")

DDL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS document_law_map (
    document_id      BIGINT NOT NULL,
    law_document_id  BIGINT NOT NULL,
    law_name         TEXT NOT NULL,
    match_type       VARCHAR(20) NOT NULL DEFAULT 'law_name',
    is_primary       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (document_id, law_document_id),
    CONSTRAINT fk_dlm_document FOREIGN KEY (document_id)     REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_dlm_law      FOREIGN KEY (law_document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_dlm_law_document ON document_law_map(law_document_id);
CREATE INDEX IF NOT EXISTS ix_dlm_law_name     ON document_law_map(law_name);
"""


# ---------------------------------------------------------------------------
# law_name → representative law doc id
# ---------------------------------------------------------------------------

def _load_law_index(conn) -> list[tuple[str, int]]:
    """(law_name, law_document_id) — 긴 이름 우선."""
    out: list[tuple[str, int]] = []
    with conn.cursor() as cur:
        # 1) law_statute preference
        cur.execute("""
            SELECT DISTINCT lm.law_name, d.id
              FROM law_meta lm
              JOIN documents d ON d.id = lm.document_id
             WHERE lm.law_name IS NOT NULL AND lm.law_name <> ''
               AND d.source_type='law' AND d.doc_category='law_statute'
        """)
        statute = {name: doc_id for name, doc_id in cur.fetchall()}

        # 2) 실제 law 문서(source_type='law')에 연결된 law_name 만.
        #    licbyl/admrul/expc 의 law_meta 엔트리는 법령이 아니므로 제외.
        cur.execute("""
            SELECT lm.law_name, MIN(lm.document_id)
              FROM law_meta lm
              JOIN documents d ON d.id = lm.document_id
             WHERE lm.law_name IS NOT NULL AND lm.law_name <> ''
               AND d.source_type = 'law'
             GROUP BY lm.law_name
        """)
        for name, first_doc_id in cur.fetchall():
            doc_id = statute.get(name, first_doc_id)
            out.append((name, int(doc_id)))

    # 긴 이름 우선으로 정렬 — "산업안전보건법 시행규칙" 이 "산업안전보건법" 보다 먼저 매칭되도록
    out.sort(key=lambda x: -len(x[0]))
    return out


def _compile_law_pattern(law_index: list[tuple[str, int]]):
    # 단일 정규식으로 alternation (긴 이름 먼저). 빠름.
    escaped = [re.escape(name) for name, _ in law_index]
    return re.compile("|".join(escaped))


def run(conn, dry_run: bool, limit: int, min_body_len: int) -> dict:
    stats = {
        "form_docs_scanned": 0,
        "form_docs_with_match": 0,
        "inserts": 0,
        "distinct_laws_touched": 0,
    }
    # 1) 테이블 생성
    with conn.cursor() as cur:
        cur.execute(DDL_CREATE_TABLE)
    conn.commit()

    law_index = _load_law_index(conn)
    print(f"[LAW-INDEX] distinct law_names = {len(law_index)}")
    if not law_index:
        return stats
    # dict for resolving name → id after match
    name_to_id: dict[str, int] = {n: i for n, i in law_index}
    pattern = _compile_law_pattern(law_index)

    distinct_laws_touched: set[int] = set()

    with conn.cursor() as rcur, conn.cursor() as wcur:
        q = f"""
            SELECT id, COALESCE(title,'') || '\n' || COALESCE(body_text,'') AS text
              FROM documents
             WHERE source_type IN ({','.join(['%s'] * len(FORM_SOURCES))})
             ORDER BY id
        """
        params: list = list(FORM_SOURCES)
        if limit > 0:
            q += " LIMIT %s"
            params.append(limit)
        rcur.execute(q, params)

        for doc_id, text in rcur.fetchall():
            stats["form_docs_scanned"] += 1
            if len(text) < min_body_len:
                continue
            names_found = set(pattern.findall(text))
            if not names_found:
                continue
            stats["form_docs_with_match"] += 1

            for name in names_found:
                law_doc_id = name_to_id.get(name)
                if law_doc_id is None:
                    continue
                wcur.execute(
                    """
                    INSERT INTO document_law_map (document_id, law_document_id, law_name, match_type)
                    VALUES (%s, %s, %s, 'law_name')
                    ON CONFLICT DO NOTHING
                    """,
                    (doc_id, law_doc_id, name),
                )
                if wcur.rowcount > 0:
                    stats["inserts"] += 1
                    distinct_laws_touched.add(law_doc_id)

    if dry_run:
        conn.rollback()
    else:
        conn.commit()

    stats["distinct_laws_touched"] = len(distinct_laws_touched)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--min-body-length", type=int, default=40)
    args = ap.parse_args()

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 3
    try:
        stats = run(conn, args.dry_run, args.limit, args.min_body_length)
    finally:
        conn.close()

    print("[RESULT]")
    for k in ("form_docs_scanned", "form_docs_with_match", "inserts", "distinct_laws_touched"):
        print(f"  {k:<22}: {stats[k]:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

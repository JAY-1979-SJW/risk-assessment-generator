"""
서식 → 법령 조문(article) 단위 매칭 (document_law_map, match_type='article').

목적
    link_forms_to_laws.py 는 "법령명" 수준까지만 연결했음.
    본 스크립트는 서식 본문의 "[법령명] 제N조" 패턴을 추출해
    특정 law_article(조문) 문서 ID 와 매칭한다.

테이블
    document_law_map (이미 존재)
        match_type = 'article' 로 삽입

매칭 규칙
    1) law_meta 에서 (law_name, article_no, document_id) 인덱스 구축
       — document 는 source_type='law' AND doc_category='law_article'
    2) 서식 본문에서 pattern:
        <law_name>\s*(?:\(|,|·|및|또는|\s)*제\s*(\d+)\s*조
       법령명과 가까운 거리(40자 이내)에 있는 "제N조" 를 매칭
    3) article_no="제{N}조" 로 정규화 후 lookup 해 article_document_id 획득
    4) INSERT INTO document_law_map (...) match_type='article' ON CONFLICT DO NOTHING

주의
    - (document_id, law_document_id) 가 PK 이므로 동일 form-article 쌍은 1번만.
    - law_name 수준 엔트리(match_type='law_name') 는 건드리지 않음.

CLI
    python scripts/db/link_forms_to_articles.py [--dry-run] [--limit N]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
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


# ---------------------------------------------------------------------------
# law_article 인덱스: (law_name, article_no) → document_id
# ---------------------------------------------------------------------------

def build_article_index(conn) -> dict[tuple[str, str], int]:
    """
    Returns: {(law_name, article_no_normalized): article_doc_id}
    article_no_normalized: "제{N}조" (공백 제거, 가지 번호 제거 전)
    """
    idx: dict[tuple[str, str], int] = {}
    with conn.cursor() as cur:
        cur.execute("""
            SELECT lm.law_name, lm.article_no, lm.document_id
              FROM law_meta lm
              JOIN documents d ON d.id = lm.document_id
             WHERE d.source_type = 'law' AND d.doc_category = 'law_article'
               AND lm.law_name IS NOT NULL AND lm.law_name <> ''
               AND lm.article_no IS NOT NULL AND lm.article_no <> ''
        """)
        for law_name, article_no, doc_id in cur.fetchall():
            key_no = re.sub(r"\s+", "", article_no)  # "제  25 조" → "제25조"
            m = re.match(r"^제(\d+)조", key_no)
            if not m:
                continue
            base_no = f"제{m.group(1)}조"
            idx[(law_name, base_no)] = int(doc_id)
    return idx


# ---------------------------------------------------------------------------
# 서식 본문에서 "[law_name] 제N조" 추출
# ---------------------------------------------------------------------------

# "제 25 조", "제25조", "제25조의3" 모두 N 만 추출
# law_name 과 "제N조" 사이 최대 40자 (구두점·공백·조사 허용)
_ARTICLE_RE_TMPL = r"{law}[^제\d]{{0,40}}?제\s*(\d+)\s*조"


def find_article_refs(
    text: str,
    law_names_sorted: list[str],
) -> list[tuple[str, str]]:
    """
    text 에서 (law_name, 제N조) 쌍을 모두 추출.
    law_names_sorted: 긴 이름 우선 (긴 이름이 짧은 이름 prefix 인 경우 긴 이름이 먼저 매칭되도록)
    """
    found: list[tuple[str, str]] = []
    consumed_spans: list[tuple[int, int]] = []

    for law in law_names_sorted:
        pattern = re.compile(_ARTICLE_RE_TMPL.format(law=re.escape(law)))
        for m in pattern.finditer(text):
            # 겹치는 짧은 이름 매칭 제거: 이미 긴 이름으로 잡힌 범위 안이면 skip
            start, end = m.start(), m.end()
            if any(cs <= start and end <= ce for cs, ce in consumed_spans):
                continue
            consumed_spans.append((start, end))
            n = m.group(1)
            found.append((law, f"제{n}조"))
    return found


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------

def run(conn, dry_run: bool, limit: int) -> dict:
    stats = {
        "forms_scanned": 0,
        "forms_with_article_ref": 0,
        "article_refs_found": 0,
        "article_refs_resolved": 0,
        "inserts": 0,
    }

    # 1) article 인덱스
    art_idx = build_article_index(conn)
    print(f"[ARTICLE-INDEX] (law_name, 제N조) → doc_id : {len(art_idx):,}")

    # law_name 목록 (긴 이름 우선)
    law_names = sorted({ln for (ln, _) in art_idx.keys()}, key=lambda s: -len(s))

    # 2) 서식 스캔
    unresolved_sample: list[tuple[int, str, str]] = []
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
            stats["forms_scanned"] += 1
            refs = find_article_refs(text, law_names)
            if not refs:
                continue
            stats["forms_with_article_ref"] += 1
            stats["article_refs_found"] += len(refs)

            # dedup within the form
            seen: set[tuple[str, str]] = set()
            for law, art_no in refs:
                if (law, art_no) in seen:
                    continue
                seen.add((law, art_no))
                art_doc_id = art_idx.get((law, art_no))
                if not art_doc_id:
                    if len(unresolved_sample) < 20:
                        unresolved_sample.append((doc_id, law, art_no))
                    continue
                stats["article_refs_resolved"] += 1
                wcur.execute(
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
                if wcur.rowcount > 0:
                    stats["inserts"] += wcur.rowcount

    if dry_run:
        conn.rollback()
    else:
        conn.commit()

    stats["_unresolved_sample"] = unresolved_sample
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 3
    try:
        stats = run(conn, args.dry_run, args.limit)
    finally:
        conn.close()

    print("[RESULT]")
    for k in (
        "forms_scanned",
        "forms_with_article_ref",
        "article_refs_found",
        "article_refs_resolved",
        "inserts",
    ):
        print(f"  {k:<25}: {stats[k]:,}")
    unresolved = stats.get("_unresolved_sample") or []
    if unresolved:
        print(f"[unresolved sample] {len(unresolved)} (상위)")
        for doc_id, law, art in unresolved[:10]:
            print(f"  doc={doc_id}  law={law}  article={art}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

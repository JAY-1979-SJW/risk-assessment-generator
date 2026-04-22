"""
위험성평가표 운영 DB 문서 이관기.

입력:
    - law/admrul/expc/licbyl : data/risk_db/law_normalized/safety_laws_normalized.json
    - kosha                 : data/normalized/kosha/*.json  (또는 PROJECT_ROOT/data/normalized/kosha)

대상 테이블:
    - documents                      (본체, UNIQUE(source_type, source_id))
    - law_meta / expc_meta / kosha_meta
    - document_hazard_map / document_work_type_map / document_equipment_map (KOSHA 만)

옵션:
    --source  {law, admrul, expc, licbyl, kosha, all}   (기본: all)
    --dry-run
    --limit   N        (source 당 상한, 기본 0 = 무제한)

원칙:
    - ON CONFLICT (source_type, source_id) DO UPDATE 로 idempotent 하게 동작
    - 에러 레코드는 집계만 하고 계속 진행
    - dry-run 은 실제 INSERT 를 수행하지 않고 예상 건수만 출력 (트랜잭션 ROLLBACK)

실행:
    DATABASE_URL=postgresql://user:pw@host:5432/db \
      python scripts/db/import_documents.py --source all --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 데이터 루트 후보: 저장소 내부 data/ → 형제(server data dir, /home/ubuntu/apps/risk-assessment-app/data)
DATA_ROOT_CANDIDATES = [
    Path(os.environ["KRAS_DATA_ROOT"]) if os.environ.get("KRAS_DATA_ROOT") else None,
    PROJECT_ROOT / "data",
    PROJECT_ROOT.parent / "data",
]
DATA_ROOT_CANDIDATES = [p for p in DATA_ROOT_CANDIDATES if p is not None]


def _first_existing(paths: Iterable[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


LAWS_FILE_CANDIDATES = [
    root / "risk_db" / "law_normalized" / "safety_laws_normalized.json"
    for root in DATA_ROOT_CANDIDATES
]
KOSHA_DIR_CANDIDATES = [
    root / "normalized" / "kosha" for root in DATA_ROOT_CANDIDATES
] + [
    root / "risk_db" / "normalized" / "kosha" for root in DATA_ROOT_CANDIDATES
]

MASTER_HAZARD_FILE = PROJECT_ROOT / "data" / "risk_db" / "mapping" / "hazard_keywords.json"
MASTER_WORKTYPE_FILE = PROJECT_ROOT / "data" / "risk_db" / "mapping" / "work_type_keywords.json"
MASTER_EQUIPMENT_FILE = PROJECT_ROOT / "data" / "risk_db" / "mapping" / "equipment_keywords.json"

LAW_SOURCES = ("law", "admrul", "licbyl")
ALL_SOURCES = ("law", "admrul", "licbyl", "expc", "kosha")

# ---------------------------------------------------------------------------
# DB 접속
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for env_path in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


def get_db_connection():
    import psycopg2
    _load_dotenv()
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        print(f"[DB] 접속: DATABASE_URL")
        return psycopg2.connect(dsn)
    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    database = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    if not (host and database and user):
        missing = [k for k, v in [("host", host), ("database", database), ("user", user)] if not v]
        raise RuntimeError(f"DB 접속 정보 누락: {missing}")
    print(f"[DB] 접속: {user}@{host}:{port}/{database}")
    return psycopg2.connect(host=host, port=int(port), dbname=database, user=user, password=password or "")


# ---------------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------------

def _parse_date(value: Any) -> date | None:
    """YYYY-MM-DD, YYYY.MM.DD, YYYYMMDD 중 어느 포맷이든 date 로 변환. 실패 시 None."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    fmts = ("%Y-%m-%d", "%Y.%m.%d", "%Y%m%d", "%Y/%m/%d")
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        # 2026-04-21T02:58:35.634694+00:00
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        pass
    d = _parse_date(s)
    if d:
        return datetime(d.year, d.month, d.day)
    return None


def _status_or_default(value: Any, default: str = "active") -> str:
    """스키마 허용값 주석: active/excluded/draft/archived. 그 외는 active 로 정규화."""
    if not value:
        return default
    s = str(value).strip().lower()
    allowed = {"active", "excluded", "draft", "archived"}
    if s in allowed:
        return s
    # KOSHA 의 'mapped' 같은 값은 active 로 정규화
    return default


# ---------------------------------------------------------------------------
# 카운터
# ---------------------------------------------------------------------------

class Counter:
    def __init__(self) -> None:
        self.inserted = 0
        self.updated = 0
        self.skipped = 0
        self.failed = 0
        self.mapping_inserted = 0
        self.mapping_skipped = 0
        self.errors: list[tuple[str, str]] = []  # (source_id, error)

    def as_dict(self) -> dict:
        return dict(
            inserted=self.inserted,
            updated=self.updated,
            skipped=self.skipped,
            failed=self.failed,
            mapping_inserted=self.mapping_inserted,
            mapping_skipped=self.mapping_skipped,
        )


# ---------------------------------------------------------------------------
# 마스터 코드 캐시 (mapping 검증용)
# ---------------------------------------------------------------------------

class MasterCache:
    def __init__(self, conn) -> None:
        self.hazards: set[str] = set()
        self.work_types: set[str] = set()
        self.equipment: set[str] = set()
        with conn.cursor() as cur:
            cur.execute("SELECT hazard_code FROM hazards")
            self.hazards = {r[0] for r in cur.fetchall()}
            cur.execute("SELECT work_type_code FROM work_types")
            self.work_types = {r[0] for r in cur.fetchall()}
            cur.execute("SELECT equipment_code FROM equipment")
            self.equipment = {r[0] for r in cur.fetchall()}


# ---------------------------------------------------------------------------
# 문서 본체 upsert
# ---------------------------------------------------------------------------

DOC_UPSERT_SQL = """
INSERT INTO documents (
    source_type, source_id, doc_category,
    title, title_normalized, body_text, has_text, content_length,
    url, file_url, pdf_path, file_sha256,
    language, status, published_at, collected_at,
    created_at, updated_at
) VALUES (
    %(source_type)s, %(source_id)s, %(doc_category)s,
    %(title)s, %(title_normalized)s, %(body_text)s, %(has_text)s, %(content_length)s,
    %(url)s, %(file_url)s, %(pdf_path)s, %(file_sha256)s,
    %(language)s, %(status)s, %(published_at)s, %(collected_at)s,
    NOW(), NOW()
)
ON CONFLICT (source_type, source_id) DO UPDATE SET
    doc_category     = EXCLUDED.doc_category,
    title            = EXCLUDED.title,
    title_normalized = EXCLUDED.title_normalized,
    body_text        = EXCLUDED.body_text,
    has_text         = EXCLUDED.has_text,
    content_length   = EXCLUDED.content_length,
    url              = EXCLUDED.url,
    file_url         = EXCLUDED.file_url,
    pdf_path         = EXCLUDED.pdf_path,
    file_sha256      = EXCLUDED.file_sha256,
    language         = EXCLUDED.language,
    status           = EXCLUDED.status,
    published_at     = EXCLUDED.published_at,
    collected_at     = EXCLUDED.collected_at,
    updated_at       = NOW()
RETURNING id, (xmax = 0) AS inserted;
"""


def upsert_document(cur, row: dict) -> tuple[int, bool]:
    """Return (document_id, inserted?). inserted=False 이면 update 된 것."""
    cur.execute(DOC_UPSERT_SQL, row)
    rec = cur.fetchone()
    return int(rec[0]), bool(rec[1])


# ---------------------------------------------------------------------------
# law/admrul/licbyl/expc 이관
# ---------------------------------------------------------------------------

def _law_doc_category(source_type: str) -> str:
    return {
        "law":    "law_statute",
        "admrul": "law_admrul",
        "licbyl": "law_licbyl",
        "expc":   "law_expc",
    }.get(source_type, "law_other")


def _build_law_doc_row(item: dict) -> dict:
    src = item.get("source_type")
    source_id = str(item.get("raw_id") or "").strip()
    title = (item.get("title") or item.get("title_ko") or "").strip()
    return dict(
        source_type=src,
        source_id=source_id,
        doc_category=_law_doc_category(src),
        title=title,
        title_normalized=(item.get("title_normalized") or title).strip(),
        body_text=None,
        has_text=False,
        content_length=0,
        url=(item.get("detail_link") or "").strip() or None,
        file_url=(item.get("file_link") or item.get("pdf_link") or "").strip() or None,
        pdf_path=None,
        file_sha256=None,
        language="ko",
        status=_status_or_default(item.get("status"), "active"),
        published_at=_parse_date(item.get("promulgation_date")),
        collected_at=_parse_timestamp(item.get("collected_at")),
    )


def upsert_law_meta(cur, document_id: int, item: dict) -> None:
    raw = item.get("raw_payload") or {}
    law_id_long = str(
        raw.get("법령ID") or raw.get("행정규칙ID") or raw.get("별표서식ID") or ""
    ).strip()
    ministry = (item.get("ministry_name") or item.get("authority") or "").strip()
    extra = {
        "category":      item.get("category"),
        "document_type": item.get("document_type"),
        "law_type":      item.get("law_type"),
        "reference_no":  item.get("reference_no"),
        "revision_type": item.get("revision_type"),
        "status_text":   item.get("status_text"),
        "law_id_key":    item.get("law_id"),
        "source_key":    item.get("source_key"),
        "detail_link":   item.get("detail_link"),
        "file_link":     item.get("file_link"),
        "pdf_link":      item.get("pdf_link"),
    }
    cur.execute(
        """
        INSERT INTO law_meta (document_id, law_name, law_id, article_no,
                              promulgation_date, effective_date, ministry, extra)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (document_id) DO UPDATE SET
            law_name          = EXCLUDED.law_name,
            law_id            = EXCLUDED.law_id,
            article_no        = EXCLUDED.article_no,
            promulgation_date = EXCLUDED.promulgation_date,
            effective_date    = EXCLUDED.effective_date,
            ministry          = EXCLUDED.ministry,
            extra             = EXCLUDED.extra
        """,
        (
            document_id,
            (item.get("title") or "").strip()[:1000] or None,
            law_id_long or None,
            None,  # article_no — 조문단위 데이터 없음
            _parse_date(item.get("promulgation_date")),
            _parse_date(item.get("enforcement_date")),
            ministry or None,
            json.dumps(extra, ensure_ascii=False),
        ),
    )


def upsert_expc_meta(cur, document_id: int, item: dict) -> None:
    raw = item.get("raw_payload") or {}
    extra = {
        "document_type":   item.get("document_type"),
        "law_type":        item.get("law_type"),
        "status_text":     item.get("status_text"),
        "revision_type":   item.get("revision_type"),
        "source_key":      item.get("source_key"),
        "detail_link":     item.get("detail_link"),
        "file_link":       item.get("file_link"),
        "pdf_link":        item.get("pdf_link"),
        "raw_payload":     raw,
    }
    cur.execute(
        """
        INSERT INTO expc_meta (document_id, agenda_no, agency_question, agency_answer,
                               reply_date, question_summary, answer_summary, reason_text, extra)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (document_id) DO UPDATE SET
            agenda_no        = EXCLUDED.agenda_no,
            agency_question  = EXCLUDED.agency_question,
            agency_answer    = EXCLUDED.agency_answer,
            reply_date       = EXCLUDED.reply_date,
            question_summary = EXCLUDED.question_summary,
            answer_summary   = EXCLUDED.answer_summary,
            reason_text      = EXCLUDED.reason_text,
            extra            = EXCLUDED.extra
        """,
        (
            document_id,
            (item.get("reference_no") or "").strip() or None,
            (raw.get("질의기관명") or "").strip() or None,
            (raw.get("회신기관명") or item.get("ministry_name") or "").strip() or None,
            _parse_date(item.get("promulgation_date")),
            None,
            None,
            None,
            json.dumps(extra, ensure_ascii=False),
        ),
    )


def load_law_items() -> list[dict]:
    path = _first_existing(LAWS_FILE_CANDIDATES)
    if path is None:
        print(f"[WARN] 법령 정규화 파일 없음. 후보: {[str(p) for p in LAWS_FILE_CANDIDATES]}")
        return []
    print(f"[LOAD] laws file = {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items") or []
    if not isinstance(items, list):
        raise RuntimeError(f"items 배열을 찾을 수 없음: {path}")
    return items


def import_law_bucket(conn, source_type: str, items: list[dict], *, limit: int,
                      dry_run: bool) -> Counter:
    cnt = Counter()
    if not items:
        print(f"[{source_type.upper()}] 대상 0건")
        return cnt

    bucket = [it for it in items if it.get("source_type") == source_type]
    if limit > 0:
        bucket = bucket[:limit]
    print(f"[{source_type.upper()}] 대상 {len(bucket)} 건")

    for idx, item in enumerate(bucket, start=1):
        source_id = str(item.get("raw_id") or "").strip()
        if not source_id:
            cnt.skipped += 1
            cnt.errors.append((f"idx={idx}", "raw_id 비어있음"))
            continue
        try:
            with conn.cursor() as cur:
                row = _build_law_doc_row(item)
                if not row["title"]:
                    cnt.skipped += 1
                    cnt.errors.append((source_id, "title 비어있음"))
                    continue
                doc_id, inserted = upsert_document(cur, row)
                if source_type == "expc":
                    upsert_expc_meta(cur, doc_id, item)
                else:
                    upsert_law_meta(cur, doc_id, item)
                if inserted:
                    cnt.inserted += 1
                else:
                    cnt.updated += 1
            if not dry_run:
                conn.commit()
            else:
                conn.rollback()
        except Exception as exc:
            conn.rollback()
            cnt.failed += 1
            cnt.errors.append((source_id, repr(exc)))
    return cnt


# ---------------------------------------------------------------------------
# KOSHA 이관
# ---------------------------------------------------------------------------

def _kosha_dir() -> Path | None:
    for p in KOSHA_DIR_CANDIDATES:
        if p.exists() and p.is_dir():
            return p
    return None


def _has_kosha_files(p: Path) -> bool:
    return any(p.glob("*.json"))


def _build_kosha_doc_row(item: dict) -> dict:
    source_id = str(item.get("source_id") or "").strip()
    title = (item.get("title") or "").strip()
    body = item.get("body_text") or None
    return dict(
        source_type="kosha",
        source_id=source_id,
        doc_category=(item.get("doc_category") or "kosha").strip() or "kosha",
        title=title,
        title_normalized=(item.get("title_normalized") or title).strip(),
        body_text=body,
        has_text=bool(item.get("has_text")),
        content_length=int(item.get("content_length") or (len(body) if body else 0)),
        url=(item.get("url") or "").strip() or None,
        file_url=(item.get("file_url") or "").strip() or None,
        pdf_path=(item.get("pdf_path") or "").strip() or None,
        file_sha256=(item.get("file_sha256") or "").strip() or None,
        language=(item.get("language") or "ko").strip() or "ko",
        status=_status_or_default(item.get("status"), "active"),
        published_at=_parse_date(item.get("published_at")),
        collected_at=_parse_timestamp(item.get("collected_at")),
    )


def upsert_kosha_meta(cur, document_id: int, item: dict) -> None:
    industry = (item.get("industry") or "").strip() or None
    tags = item.get("tags") or []
    if not isinstance(tags, list):
        tags = [str(tags)]
    cur.execute(
        """
        INSERT INTO kosha_meta (document_id, industry, tags)
        VALUES (%s, %s, %s::jsonb)
        ON CONFLICT (document_id) DO UPDATE SET
            industry = EXCLUDED.industry,
            tags     = EXCLUDED.tags
        """,
        (document_id, industry, json.dumps(tags, ensure_ascii=False)),
    )


def upsert_mapping(cur, table: str, document_id: int, code_col: str, code: str,
                   is_primary: bool = False) -> bool:
    cur.execute(
        f"""
        INSERT INTO {table} (document_id, {code_col}, is_primary)
        VALUES (%s, %s, %s)
        ON CONFLICT (document_id, {code_col}) DO NOTHING
        """,
        (document_id, code, is_primary),
    )
    return cur.rowcount > 0


def import_kosha(conn, *, limit: int, dry_run: bool, master: MasterCache) -> Counter:
    cnt = Counter()
    base = _kosha_dir()
    if base is None:
        print("[KOSHA] 정규화 디렉토리 없음. 후보:", [str(p) for p in KOSHA_DIR_CANDIDATES])
        return cnt

    files = sorted(base.glob("*.json"))
    if limit > 0:
        files = files[:limit]
    print(f"[KOSHA] 대상 {len(files)} 건 (경로: {base})")

    for fp in files:
        source_id = ""
        try:
            with fp.open("r", encoding="utf-8") as f:
                item = json.load(f)
            source_id = str(item.get("source_id") or "").strip()
            if not source_id:
                cnt.skipped += 1
                cnt.errors.append((fp.name, "source_id 비어있음"))
                continue
            title = (item.get("title") or "").strip()
            if not title:
                cnt.skipped += 1
                cnt.errors.append((source_id, "title 비어있음"))
                continue

            with conn.cursor() as cur:
                row = _build_kosha_doc_row(item)
                doc_id, inserted = upsert_document(cur, row)
                upsert_kosha_meta(cur, doc_id, item)

                # 매핑 (마스터에 존재하는 코드만 insert)
                for haz in (item.get("hazards") or []):
                    code = str(haz).strip()
                    if code and code in master.hazards:
                        if upsert_mapping(cur, "document_hazard_map", doc_id, "hazard_code", code):
                            cnt.mapping_inserted += 1
                    else:
                        cnt.mapping_skipped += 1

                for wt in (item.get("work_types") or []):
                    code = str(wt).strip()
                    if code and code in master.work_types:
                        if upsert_mapping(cur, "document_work_type_map", doc_id, "work_type_code", code):
                            cnt.mapping_inserted += 1
                    else:
                        cnt.mapping_skipped += 1

                for eq in (item.get("equipment") or []):
                    code = str(eq).strip()
                    if code and code in master.equipment:
                        if upsert_mapping(cur, "document_equipment_map", doc_id, "equipment_code", code):
                            cnt.mapping_inserted += 1
                    else:
                        cnt.mapping_skipped += 1

                if inserted:
                    cnt.inserted += 1
                else:
                    cnt.updated += 1

            if not dry_run:
                conn.commit()
            else:
                conn.rollback()
        except Exception as exc:
            conn.rollback()
            cnt.failed += 1
            cnt.errors.append((source_id or fp.name, repr(exc)))
    return cnt


# ---------------------------------------------------------------------------
# 보고
# ---------------------------------------------------------------------------

def _fmt_counter(src: str, c: Counter) -> str:
    return (
        f"  - {src:<8} inserted={c.inserted:>6}  updated={c.updated:>6}  "
        f"skipped={c.skipped:>4}  failed={c.failed:>4}  "
        f"map_ins={c.mapping_inserted:>6}  map_skip={c.mapping_skipped:>6}"
    )


def _print_final_counts(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM documents")
        total = int(cur.fetchone()[0])
        cur.execute(
            "SELECT source_type, COUNT(*) FROM documents GROUP BY source_type ORDER BY source_type"
        )
        by_src = list(cur.fetchall())

        cur.execute(
            "SELECT source_type, COUNT(*) FROM documents "
            "WHERE COALESCE(title, '') = '' GROUP BY source_type"
        )
        null_title = dict(cur.fetchall())

        cur.execute(
            "SELECT source_type, COUNT(*) FROM documents "
            "WHERE COALESCE(body_text, '') = '' GROUP BY source_type"
        )
        null_body = dict(cur.fetchall())

        cur.execute(
            "SELECT source_type, source_id, COUNT(*) FROM documents "
            "GROUP BY source_type, source_id HAVING COUNT(*) > 1"
        )
        dups = cur.fetchall()

        maps = {}
        for tbl in ("document_hazard_map", "document_work_type_map", "document_equipment_map"):
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            maps[tbl] = int(cur.fetchone()[0])

        cur.execute("SELECT id, source_type, source_id, LEFT(title, 60) FROM documents ORDER BY id DESC LIMIT 5")
        samples = cur.fetchall()

    print()
    print("[검증 결과]")
    print(f"  전체 documents: {total:,}")
    print("  source_type 별:")
    for st, cc in by_src:
        nt = null_title.get(st, 0)
        nb = null_body.get(st, 0)
        print(f"    - {st:<8} count={cc:>6}  null_title={nt:>4}  null_body={nb:>6}")
    print(f"  중복 (source_type, source_id): {len(dups)} 건")
    print("  매핑 테이블:")
    for tbl, c in maps.items():
        print(f"    - {tbl:<28} {c:>6}")
    print("  샘플 5건 (최신 id 순):")
    for r in samples:
        print(f"    - id={r[0]} [{r[1]}:{r[2]}] {r[3]}")


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------

def run(args) -> int:
    sources = ALL_SOURCES if args.source == "all" else (args.source,)

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 2

    try:
        master = MasterCache(conn)
        print(f"[MASTER] hazards={len(master.hazards)} work_types={len(master.work_types)} "
              f"equipment={len(master.equipment)}")

        law_items: list[dict] = []
        if any(s in LAW_SOURCES + ("expc",) for s in sources):
            law_items = load_law_items()
            print(f"[LOAD] safety_laws items={len(law_items)}")

        results: dict[str, Counter] = {}
        mode = "DRY-RUN" if args.dry_run else "APPLY"
        print(f"[MODE] {mode}  (limit={args.limit})")

        if "law" in sources:
            results["law"] = import_law_bucket(conn, "law", law_items, limit=args.limit, dry_run=args.dry_run)
        if "admrul" in sources:
            results["admrul"] = import_law_bucket(conn, "admrul", law_items, limit=args.limit, dry_run=args.dry_run)
        if "licbyl" in sources:
            results["licbyl"] = import_law_bucket(conn, "licbyl", law_items, limit=args.limit, dry_run=args.dry_run)
        if "expc" in sources:
            results["expc"] = import_law_bucket(conn, "expc", law_items, limit=args.limit, dry_run=args.dry_run)
        if "kosha" in sources:
            results["kosha"] = import_kosha(conn, limit=args.limit, dry_run=args.dry_run, master=master)

        print()
        print(f"[적재 결과 요약]  (mode={mode})")
        for src, c in results.items():
            print(_fmt_counter(src, c))
            if c.errors:
                for sid, err in c.errors[:5]:
                    print(f"      ERR sid={sid}: {err}")
                if len(c.errors) > 5:
                    print(f"      ... (+{len(c.errors) - 5} more)")

        if not args.dry_run:
            _print_final_counts(conn)

        return 0
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=list(ALL_SOURCES) + ["all"], default="all")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="source 당 상한 (0=무제한)")
    args = ap.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())

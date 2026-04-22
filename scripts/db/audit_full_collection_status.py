"""
전수 수집/정규화/적재/분류 현황 진단기 (read-only).

목적
    - 원천(raw) / 정규화(normalized) / 운영 DB / 분류 매핑을
      한 번에 집계하여 source 별로 한 줄 비교표를 출력한다.
    - DB write / 스크래퍼 실행은 일절 하지 않는다.
    - 파일시스템은 로컬 우선, 환경변수 KRAS_DATA_ROOT 로 서버 경로 지정 가능.

실행
    # 로컬 (이 저장소의 data/)
    python scripts/db/audit_full_collection_status.py

    # 서버 (원격 실행 시)
    KRAS_DATA_ROOT=/home/ubuntu/apps/risk-assessment-app/app/data \\
      python scripts/db/audit_full_collection_status.py

DB 접속 우선순위
    1) DATABASE_URL
    2) PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD
    3) .env / infra/.env

절대 규칙
    - SELECT 외 쿼리 금지 (read-only 트랜잭션)
    - 파일 삭제/생성 금지 (이 스크립트는 stdout 출력만)
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()


# ---------------------------------------------------------------------------
# 파일시스템 측정
# ---------------------------------------------------------------------------

def _data_roots() -> list[Path]:
    roots: list[Path] = []
    override = os.environ.get("KRAS_DATA_ROOT")
    if override:
        roots.append(Path(override))
    roots.append(PROJECT_ROOT / "data")
    roots.append(PROJECT_ROOT.parent / "data")
    return [r for r in roots if r.exists()]


def _count_files(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    try:
        return sum(1 for p in path.rglob(pattern) if p.is_file())
    except OSError:
        return 0


def _first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


@dataclass
class FsSummary:
    source: str
    raw_path: str
    raw_count: int
    normalized_path: str
    normalized_count: int


def measure_filesystem(roots: list[Path]) -> list[FsSummary]:
    out: list[FsSummary] = []

    def fs(source, raw_sub, norm_sub, raw_pattern="*"):
        raw_candidates = [r / raw_sub for r in roots]
        norm_candidates = [r / norm_sub for r in roots]
        raw = _first_existing(raw_candidates)
        norm = _first_existing(norm_candidates)
        out.append(FsSummary(
            source=source,
            raw_path=str(raw) if raw else f"(missing) {raw_candidates[0] if raw_candidates else ''}",
            raw_count=_count_files(raw, raw_pattern) if raw else 0,
            normalized_path=str(norm) if norm else f"(missing) {norm_candidates[0] if norm_candidates else ''}",
            normalized_count=_count_files(norm, "*.json") if norm else 0,
        ))

    # law 계열
    fs("law",      "raw/law_content/law",    "normalized/law")
    fs("admrul",   "raw/law_content/admrul", "normalized/admrul")
    fs("expc",     "raw/law_content/expc",   "normalized/expc")
    fs("licbyl",   "raw/law_api/licbyl/files", "normalized/licbyl", raw_pattern="*.hwp*")

    # KOSHA
    fs("kosha",      "raw/kosha",        "normalized/kosha",  raw_pattern="*.json")
    fs("kosha_form", "raw/kosha_forms",  "normalized/kosha_forms")

    # MOEL
    fs("moel_form",  "raw/moel_forms",   "normalized/moel_forms")

    return out


# ---------------------------------------------------------------------------
# DB 측정
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
        missing = [k for k, v in [("host", host), ("database", database), ("user", user)] if not v]
        raise RuntimeError(f"DB 접속 정보 누락: {missing}")
    return psycopg2.connect(host=host, port=int(port), dbname=database, user=user, password=password or "")


SOURCE_ORDER = ["law", "admrul", "expc", "licbyl", "kosha", "kosha_form", "moel_form"]


def fetch_db_snapshot(conn) -> dict:
    out: dict = {
        "by_source": {},    # source -> {total, null_body, has_text, has_pdf, has_hwpx}
        "mapping": {},      # source -> {hazard, work, equip}
        "meta": {},         # law_meta/expc_meta/kosha_meta -> count
        "master": {},       # hazards/work_types/equipment -> count
        "total": 0,
    }
    with conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        cur.execute("SELECT COUNT(*) FROM documents")
        out["total"] = int(cur.fetchone()[0])

        cur.execute("""
            SELECT source_type,
                   COUNT(*) AS total,
                   SUM(CASE WHEN COALESCE(body_text,'')='' THEN 1 ELSE 0 END) AS null_body,
                   SUM(CASE WHEN has_text THEN 1 ELSE 0 END) AS with_text,
                   SUM(CASE WHEN pdf_path IS NOT NULL AND pdf_path<>'' THEN 1 ELSE 0 END) AS has_pdf,
                   SUM(CASE WHEN hwpx_path IS NOT NULL AND hwpx_path<>'' THEN 1 ELSE 0 END) AS has_hwpx
            FROM documents GROUP BY source_type
        """)
        for row in cur.fetchall():
            st, total, null_body, with_text, has_pdf, has_hwpx = row
            out["by_source"][st] = {
                "total": int(total),
                "null_body": int(null_body),
                "with_text": int(with_text),
                "has_pdf": int(has_pdf),
                "has_hwpx": int(has_hwpx),
            }

        cur.execute("""
            SELECT d.source_type,
                   COUNT(DISTINCT h.document_id) AS hazard_mapped,
                   COUNT(DISTINCT w.document_id) AS work_mapped,
                   COUNT(DISTINCT e.document_id) AS equip_mapped
            FROM documents d
            LEFT JOIN document_hazard_map     h ON h.document_id=d.id
            LEFT JOIN document_work_type_map  w ON w.document_id=d.id
            LEFT JOIN document_equipment_map  e ON e.document_id=d.id
            GROUP BY d.source_type
        """)
        for row in cur.fetchall():
            st, hz, wk, eq = row
            out["mapping"][st] = {"hazard": int(hz), "work": int(wk), "equip": int(eq)}

        for meta in ("law_meta", "expc_meta", "kosha_meta"):
            cur.execute(f"SELECT COUNT(*) FROM {meta}")
            out["meta"][meta] = int(cur.fetchone()[0])

        for mst in ("hazards", "work_types", "equipment"):
            cur.execute(f"SELECT COUNT(*) FROM {mst}")
            out["master"][mst] = int(cur.fetchone()[0])

        # law_meta 상세 (law_id / article_no 구분)
        cur.execute("""
            SELECT COUNT(DISTINCT law_id) AS distinct_laws,
                   SUM(CASE WHEN article_no IS NOT NULL AND article_no<>'' THEN 1 ELSE 0 END) AS rows_with_article,
                   COUNT(*)
            FROM law_meta
        """)
        dl, art, total = cur.fetchone()
        out["law_meta_detail"] = {
            "distinct_laws": int(dl or 0),
            "rows_with_article": int(art or 0),
            "total": int(total or 0),
        }

    return out


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------

def _pct(a: int, b: int) -> str:
    if b <= 0:
        return "-"
    return f"{(a * 100.0 / b):.1f}%"


def _judge(raw: int, norm: int, db: int, hazard: int) -> str:
    # PASS : raw>0, norm>0, db>=norm*0.9, 분류 1종 이상 50% 이상
    # WARN : 일부 미완
    # FAIL : raw==0 OR db==0
    if raw <= 0 or db <= 0:
        return "FAIL"
    if norm > 0 and db < norm * 0.5:
        return "FAIL"
    if hazard > 0 and db > 0 and hazard / db >= 0.5 and db >= norm * 0.9:
        return "PASS"
    return "WARN"


def print_report(fs_list: list[FsSummary], db: dict) -> None:
    print()
    print("=" * 110)
    print(" 위험성평가 전수 수집/분류 현황 감사")
    print("=" * 110)
    print()

    # --- 1. source별 요약 표 ---
    hdr = (
        f"{'source':<12}"
        f"{'raw':>10}"
        f"{'norm':>10}"
        f"{'db':>10}"
        f"{'null_body':>12}"
        f"{'has_text':>10}"
        f"{'hwpx':>8}"
        f"{'hazard':>8}"
        f"{'work':>8}"
        f"{'equip':>8}"
        f"{'haz%':>7}"
        f"{'  판정':>8}"
    )
    print(hdr)
    print("-" * len(hdr))

    fs_by_src = {f.source: f for f in fs_list}
    for src in SOURCE_ORDER:
        f = fs_by_src.get(src)
        raw = f.raw_count if f else 0
        norm = f.normalized_count if f else 0
        db_src = db["by_source"].get(src, {})
        db_cnt = db_src.get("total", 0)
        null_body = db_src.get("null_body", 0)
        has_text = db_src.get("with_text", 0)
        has_hwpx = db_src.get("has_hwpx", 0)

        m = db["mapping"].get(src, {})
        hz = m.get("hazard", 0)
        wk = m.get("work", 0)
        eq = m.get("equip", 0)

        verdict = _judge(raw, norm, db_cnt, hz)
        print(
            f"{src:<12}"
            f"{raw:>10,}"
            f"{norm:>10,}"
            f"{db_cnt:>10,}"
            f"{null_body:>12,}"
            f"{has_text:>10,}"
            f"{has_hwpx:>8,}"
            f"{hz:>8,}"
            f"{wk:>8,}"
            f"{eq:>8,}"
            f"{_pct(hz, db_cnt):>7}"
            f"{'  ' + verdict:>8}"
        )

    print()
    print(f"documents total: {db['total']:,}")
    print(f"hazards master : {db['master']['hazards']}")
    print(f"work_types mst : {db['master']['work_types']}")
    print(f"equipment mst  : {db['master']['equipment']}")
    print()

    # --- 2. law 상세 ---
    ld = db.get("law_meta_detail", {})
    print("[law 상세]")
    print(f"- law_meta total         : {ld.get('total', 0)}")
    print(f"- law_meta distinct_laws : {ld.get('distinct_laws', 0)}")
    print(f"- law_meta article rows  : {ld.get('rows_with_article', 0)}")
    fs_law = fs_by_src.get("law")
    print(f"- normalized/law files   : {fs_law.normalized_count if fs_law else 0}")
    print(f"- DB documents(law)      : {db['by_source'].get('law', {}).get('total', 0)}")
    print()

    # --- 3. 분류 상세 ---
    tot = db["total"] or 1
    dh = sum(v.get("hazard", 0) for v in db["mapping"].values())
    dw = sum(v.get("work", 0) for v in db["mapping"].values())
    de = sum(v.get("equip", 0) for v in db["mapping"].values())
    print("[분류 상세 — distinct document_id 기준]")
    print(f"- hazard    : {dh:>6,} / {tot:>6,}  ({_pct(dh, tot)})")
    print(f"- work_type : {dw:>6,} / {tot:>6,}  ({_pct(dw, tot)})")
    print(f"- equipment : {de:>6,} / {tot:>6,}  ({_pct(de, tot)})")
    print()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    roots = _data_roots()
    print(f"[FS] data roots: {[str(r) for r in roots] or '(none found)'}")

    fs_list = measure_filesystem(roots)

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        # FS 만이라도 출력
        fake_db = {
            "total": 0, "by_source": {}, "mapping": {},
            "meta": {}, "master": {"hazards": 0, "work_types": 0, "equipment": 0},
            "law_meta_detail": {},
        }
        print_report(fs_list, fake_db)
        return 2

    try:
        db = fetch_db_snapshot(conn)
    finally:
        conn.close()

    print_report(fs_list, db)
    return 0


if __name__ == "__main__":
    sys.exit(main())

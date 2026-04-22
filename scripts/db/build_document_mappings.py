"""
키워드 기반 문서-분류 매핑 적재기 (hazard / work_type / equipment).

배경
    - KOSHA 정규화 파일은 hazards/work_types/equipment 코드가 사전 주입되어
      `import_documents.py` 에서 그대로 map 테이블에 적재되었다.
    - 반면 law/admrul/expc/licbyl/kosha_form/moel_form 은 해당 배열이 비어 있어
      매핑이 전혀 없다(커버리지 0%).
    - 본 스크립트는 `data/risk_db/mapping/*.json` 의 키워드 사전을 이용해
      DB 의 title + body_text 를 스캔하여 map 테이블에 보충 적재한다.

입력
    - DB: documents (title, body_text)
    - FS: <data_root>/risk_db/mapping/{hazard_keywords,work_type_keywords,equipment_keywords}.json

적재 대상
    document_hazard_map (document_id, hazard_code)
    document_work_type_map (document_id, work_type_code)
    document_equipment_map (document_id, equipment_code)
    (ON CONFLICT DO NOTHING — 기존 매핑 유지)

옵션
    --source TYPE      source_type 지정. 여러 번 전달 가능. (기본: all except kosha)
    --all              전체 source 처리 (kosha 포함)
    --dry-run          실제 INSERT 없이 예상 건수만 집계
    --limit N          source별 상한 (테스트용)
    --min-body-length  매핑 대상 최소 본문 길이 (기본 20. 제목만 있어도 허용하려면 0)
    --data-root P      data 루트 직접 지정

실행
    DATABASE_URL=... python3 scripts/db/build_document_mappings.py --dry-run
    DATABASE_URL=... python3 scripts/db/build_document_mappings.py

원칙
    - 매핑 중복 INSERT 금지 (ON CONFLICT DO NOTHING)
    - 기존 매핑 삭제 금지 (read-only UPDATE 스타일, INSERT 전용)
    - 매핑 코드는 반드시 마스터(hazards/work_types/equipment)에 있는 것만 허용
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()


# ---------------------------------------------------------------------------
# 환경 / 경로
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    for env in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env.exists():
            load_dotenv(env, override=False)


def _data_root_candidates(override: str | None) -> list[Path]:
    roots: list[Path] = []
    if override:
        roots.append(Path(override))
    env = os.environ.get("KRAS_DATA_ROOT")
    if env:
        roots.append(Path(env))
    roots.append(PROJECT_ROOT / "data")
    roots.append(PROJECT_ROOT.parent / "data")
    return [r for r in roots if r.exists()]


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
    return psycopg2.connect(
        host=host, port=int(port), dbname=database, user=user, password=password or ""
    )


# ---------------------------------------------------------------------------
# 키워드 사전
# ---------------------------------------------------------------------------

@dataclass
class KeywordDict:
    # code -> list of keywords (raw strings)
    hazard: dict[str, list[str]]
    work: dict[str, list[str]]
    equip: dict[str, list[str]]


def _load_keywords(root: Path) -> KeywordDict:
    def _load(fname: str, outer_key: str, code_key: str) -> dict[str, list[str]]:
        p = root / "risk_db" / "mapping" / fname
        with p.open(encoding="utf-8") as f:
            data = json.load(f)
        out: dict[str, list[str]] = {}
        for row in data.get(outer_key) or []:
            code = (row.get(code_key) or "").strip()
            kws = [str(k).strip() for k in (row.get("keywords") or []) if str(k).strip()]
            if code and kws:
                out[code] = kws
        return out

    return KeywordDict(
        hazard=_load("hazard_keywords.json", "hazards", "hazard_code"),
        work=_load("work_type_keywords.json", "work_types", "work_type_code"),
        equip=_load("equipment_keywords.json", "equipment", "equipment_code"),
    )


def _compile_patterns(kws: dict[str, list[str]]) -> list[tuple[str, re.Pattern[str]]]:
    """keyword union → alternation regex. 각 code 당 1개 패턴."""
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for code, keywords in kws.items():
        # escape + alternation; 한국어는 word boundary 없이도 충분
        alt = "|".join(re.escape(k) for k in keywords)
        compiled.append((code, re.compile(alt)))
    return compiled


# ---------------------------------------------------------------------------
# 마스터 코드 검증
# ---------------------------------------------------------------------------

def _load_master(conn) -> tuple[set[str], set[str], set[str]]:
    with conn.cursor() as cur:
        cur.execute("SELECT hazard_code FROM hazards")
        hz = {r[0] for r in cur.fetchall()}
        cur.execute("SELECT work_type_code FROM work_types")
        wt = {r[0] for r in cur.fetchall()}
        cur.execute("SELECT equipment_code FROM equipment")
        eq = {r[0] for r in cur.fetchall()}
    return hz, wt, eq


# ---------------------------------------------------------------------------
# 매핑
# ---------------------------------------------------------------------------

DEFAULT_SOURCES = ("law", "admrul", "expc", "licbyl", "kosha_form", "moel_form")


def _extract_codes(text: str, patterns: list[tuple[str, re.Pattern[str]]],
                   allowed: set[str]) -> list[str]:
    found: list[str] = []
    for code, pat in patterns:
        if code not in allowed:
            continue
        if pat.search(text):
            found.append(code)
    return found


def build_for_source(
    conn,
    source_type: str,
    patterns_hz: list[tuple[str, re.Pattern[str]]],
    patterns_wt: list[tuple[str, re.Pattern[str]]],
    patterns_eq: list[tuple[str, re.Pattern[str]]],
    allowed_hz: set[str],
    allowed_wt: set[str],
    allowed_eq: set[str],
    dry_run: bool,
    limit: int,
    min_body_len: int,
) -> dict:
    stats = {
        "source_type": source_type,
        "docs_scanned": 0,
        "docs_matched_any": 0,
        "hazard_inserts": 0,
        "work_inserts": 0,
        "equip_inserts": 0,
    }

    with conn.cursor(name=f"cursor_{source_type}") as cur:  # server-side cursor
        cur.itersize = 500
        q = """
            SELECT id, COALESCE(title,''), COALESCE(body_text,'')
            FROM documents
            WHERE source_type = %s
        """
        params: list = [source_type]
        if limit > 0:
            q += " LIMIT %s"
            params.append(limit)
        cur.execute(q, params)

        with conn.cursor() as wcur:
            for doc_id, title, body in cur:
                stats["docs_scanned"] += 1
                text = f"{title}\n{body}"
                if min_body_len > 0 and len(body) < min_body_len and len(title) < min_body_len:
                    # 제목만 있는 빈본문은 건너뜀(소음 방지)
                    continue

                codes_hz = _extract_codes(text, patterns_hz, allowed_hz)
                codes_wt = _extract_codes(text, patterns_wt, allowed_wt)
                codes_eq = _extract_codes(text, patterns_eq, allowed_eq)
                if not (codes_hz or codes_wt or codes_eq):
                    continue
                stats["docs_matched_any"] += 1

                for code in codes_hz:
                    wcur.execute(
                        "INSERT INTO document_hazard_map (document_id, hazard_code) "
                        "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (doc_id, code),
                    )
                    stats["hazard_inserts"] += wcur.rowcount
                for code in codes_wt:
                    wcur.execute(
                        "INSERT INTO document_work_type_map (document_id, work_type_code) "
                        "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (doc_id, code),
                    )
                    stats["work_inserts"] += wcur.rowcount
                for code in codes_eq:
                    wcur.execute(
                        "INSERT INTO document_equipment_map (document_id, equipment_code) "
                        "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (doc_id, code),
                    )
                    stats["equip_inserts"] += wcur.rowcount

    if dry_run:
        conn.rollback()
    else:
        conn.commit()
    return stats


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", action="append", default=[],
                    help="대상 source_type. 여러 번 지정 가능. 기본: law/admrul/expc/licbyl/kosha_form/moel_form")
    ap.add_argument("--all", action="store_true", help="kosha 포함 전 source")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--min-body-length", type=int, default=20)
    ap.add_argument("--data-root", type=str, default=None)
    args = ap.parse_args()

    roots = _data_root_candidates(args.data_root)
    if not roots:
        print("[FAIL] data_root 를 찾을 수 없다.", file=sys.stderr)
        return 2
    root = roots[0]
    print(f"[FS] data_root = {root}")

    try:
        kw = _load_keywords(root)
    except Exception as exc:
        print(f"[FAIL] 키워드 사전 로드 실패: {exc!r}", file=sys.stderr)
        return 2
    print(f"[KW] hazards={len(kw.hazard)}  work_types={len(kw.work)}  equipment={len(kw.equip)}")

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 3

    try:
        hz_master, wt_master, eq_master = _load_master(conn)
        print(f"[MASTER] hazards={len(hz_master)} work_types={len(wt_master)} equipment={len(eq_master)}")

        # 키워드 사전의 코드가 마스터에 존재하는 것만 사용
        kw_hz = {c: k for c, k in kw.hazard.items() if c in hz_master}
        kw_wt = {c: k for c, k in kw.work.items() if c in wt_master}
        kw_eq = {c: k for c, k in kw.equip.items() if c in eq_master}
        dropped = (
            set(kw.hazard) - hz_master,
            set(kw.work) - wt_master,
            set(kw.equip) - eq_master,
        )
        if any(dropped):
            print(f"[KW] 마스터에 없는 코드 제외: hazard={dropped[0]} work={dropped[1]} equip={dropped[2]}")

        pat_hz = _compile_patterns(kw_hz)
        pat_wt = _compile_patterns(kw_wt)
        pat_eq = _compile_patterns(kw_eq)

        if args.all:
            sources = ("law", "admrul", "expc", "licbyl", "kosha", "kosha_form", "moel_form")
        elif args.source:
            sources = tuple(args.source)
        else:
            sources = DEFAULT_SOURCES

        print(f"[RUN] sources = {sources}  dry_run={args.dry_run}  limit={args.limit}  "
              f"min_body_len={args.min_body_length}")

        total_stats = []
        for src in sources:
            print(f"--- processing source={src} ---")
            stats = build_for_source(
                conn, src,
                pat_hz, pat_wt, pat_eq,
                hz_master, wt_master, eq_master,
                dry_run=args.dry_run,
                limit=args.limit,
                min_body_len=args.min_body_length,
            )
            print(
                f"  scanned={stats['docs_scanned']:,}  matched_any={stats['docs_matched_any']:,}  "
                f"hazard+={stats['hazard_inserts']:,}  work+={stats['work_inserts']:,}  "
                f"equip+={stats['equip_inserts']:,}"
            )
            total_stats.append(stats)

        print()
        print("[SUMMARY]")
        sh = sw = se = dm = ds = 0
        for s in total_stats:
            sh += s["hazard_inserts"]; sw += s["work_inserts"]; se += s["equip_inserts"]
            dm += s["docs_matched_any"]; ds += s["docs_scanned"]
        print(f"  docs_scanned      : {ds:,}")
        print(f"  docs_matched_any  : {dm:,}")
        print(f"  hazard inserts    : {sh:,}")
        print(f"  work   inserts    : {sw:,}")
        print(f"  equip  inserts    : {se:,}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())

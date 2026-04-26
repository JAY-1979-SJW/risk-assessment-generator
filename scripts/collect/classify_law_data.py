"""
classify_law_data.py — 법령 수집 데이터 index/db 분류 및 현황 출력

분류 기준
  index : API 목록·메타 수집 결과 (*_index.json)
          data/risk_db/law_raw/          → 파이프라인 입력 (항상 최신 1건)
          data/raw/law_api/YYYY-MM-DD/   → 날짜별 아카이브

  db    : 조문 본문까지 수집·가공한 실질 DB (*.jsonl)
          data/raw/law_content/law/YYYY-MM-DD/law_content.jsonl
          data/raw/law_content/admrul/YYYY-MM-DD/admrul_content.jsonl

Usage:
    python -m scripts.collect.classify_law_data          # 현황 출력
    python -m scripts.collect.classify_law_data --json   # JSON 출력
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data"


# ── 분류 규칙 ──────────────────────────────────────────────────────────────────
INDEX_DIRS = {
    "pipeline_input": DATA / "risk_db" / "law_raw",
    "archive_law":    DATA / "raw" / "law_api" / "law",
    "archive_admrul": DATA / "raw" / "law_api" / "admrul",
    "archive_expc":   DATA / "raw" / "law_api" / "expc",
    "archive_licbyl": DATA / "raw" / "law_api" / "licbyl",
}

DB_DIRS = {
    "law_content":   DATA / "raw" / "law_content" / "law",
    "admrul_content": DATA / "raw" / "law_content" / "admrul",
}


def _collect_index_files():
    result = {}
    for label, base in INDEX_DIRS.items():
        files = sorted(base.rglob("*.json")) if base.exists() else []
        result[label] = []
        for f in files:
            stat = f.stat()
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                count = data.get("total_count") or len(data.get("items", []))
                status = data.get("status", data.get("result_code", "?"))
                fetched = data.get("fetched_at", "")
            except Exception:
                count, status, fetched = -1, "parse_error", ""
            result[label].append({
                "file": str(f.relative_to(ROOT)),
                "size_kb": round(stat.st_size / 1024, 1),
                "item_count": count,
                "status": status,
                "fetched_at": fetched,
            })
    return result


def _collect_db_files():
    result = {}
    for label, base in DB_DIRS.items():
        files = sorted(base.rglob("*.jsonl")) if base.exists() else []
        result[label] = []
        for f in files:
            stat = f.stat()
            lines = sum(1 for _ in f.open(encoding="utf-8"))
            meta_f = f.with_suffix("").with_name(f.stem + "_meta.json")
            fetched = ""
            if meta_f.exists():
                try:
                    meta = json.loads(meta_f.read_text(encoding="utf-8"))
                    fetched = meta.get("fetched_at", "")
                except Exception:
                    pass
            result[label].append({
                "file": str(f.relative_to(ROOT)),
                "size_kb": round(stat.st_size / 1024, 1),
                "record_count": lines,
                "fetched_at": fetched,
            })
    return result


def report(as_json=False):
    index_data = _collect_index_files()
    db_data = _collect_db_files()

    out = {"index": index_data, "db": db_data}

    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print("=" * 60)
    print("  법령 수집 데이터 분류 현황")
    print("=" * 60)

    print("\n[INDEX] API 목록·메타 수집 결과")
    print("-" * 60)
    for label, files in index_data.items():
        if not files:
            print(f"  {label}: (없음)")
            continue
        print(f"  {label}/")
        for f in files:
            cnt = f["item_count"]
            cnt_str = f"{cnt}건" if cnt >= 0 else "파싱오류"
            print(f"    {Path(f['file']).name:<45} {cnt_str:>6}  {f['fetched_at'][:10] or '?':>10}  {f['size_kb']} KB")

    print("\n[DB] 조문 본문 수집 결과")
    print("-" * 60)
    for label, files in db_data.items():
        if not files:
            print(f"  {label}: (없음)")
            continue
        print(f"  {label}/")
        for f in files:
            print(f"    {Path(f['file']).name:<45} {f['record_count']:>6}건  {f['fetched_at'][:10] or '?':>10}  {f['size_kb']} KB")

    print("\n[분류 기준]")
    print("  index = API 검색 목록·메타만 수집 (*_index.json)")
    print("          파이프라인 입력: data/risk_db/law_raw/")
    print("          날짜 아카이브:   data/raw/law_api/YYYY-MM-DD/")
    print("  db    = 조문 본문까지 수집·가공 (*.jsonl)")
    print("          law_content:     data/raw/law_content/law/YYYY-MM-DD/")
    print("          admrul_content:  data/raw/law_content/admrul/YYYY-MM-DD/")
    print("=" * 60)


if __name__ == "__main__":
    as_json = "--json" in sys.argv
    report(as_json=as_json)

"""
classify_law_data.py — 수집 데이터 전체 분류 현황 출력

분류 체계
  index    : API 목록·메타 수집 (*_index.json)
  db       : 조문·본문 수집·가공 (*.jsonl)
  master   : 운영 마스터 (data/masters/)
  evidence : 법령 근거 개별 파일 (data/evidence/)
  mapping  : 위험-공종-법령 매핑 (risk_db/law_mapping, mappings, mapping)
  schema   : API/스키마 정의 (risk_db/api_schema, schema)
  design   : 설계·리뷰 문서 (risk_db/*_design)
  taxonomy : 공종·위험 분류 체계 (risk_db/work_taxonomy, hazard_action)
  normalized: 정규화 결과 (risk_db/law_normalized, data/normalized)
  raw_kosha: KOSHA 원천 수집 (raw/kosha*, raw/moel_forms)

Usage:
    python -m scripts.collect.classify_law_data           # 전체 현황 출력
    python -m scripts.collect.classify_law_data --json    # JSON 출력
    python -m scripts.collect.classify_law_data --verify  # 미분류 파일 검출
"""
import json
import re
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
    "unified_index":  DATA / "index",
}

DB_DIRS = {
    "law_content":    DATA / "raw" / "law_content" / "law",
    "admrul_content": DATA / "raw" / "law_content" / "admrul",
    "expc_content":   DATA / "raw" / "law_content" / "expc",
}

# ── 추가 분류 디렉토리 ──────────────────────────────────────────────────────────
EXTRA_DIRS: dict[str, list[Path]] = {
    "master": [
        DATA / "masters",
    ],
    "evidence": [
        DATA / "evidence",
    ],
    "mapping": [
        DATA / "risk_db" / "law_mapping",
        DATA / "risk_db" / "mappings",
        DATA / "risk_db" / "mapping",
        DATA / "risk_db" / "mapping_engine",
    ],
    "schema": [
        DATA / "risk_db" / "api_schema",
        DATA / "risk_db" / "collection_schema",
        DATA / "risk_db" / "schema",
    ],
    "design": [
        DATA / "risk_db" / "api_design",
        DATA / "risk_db" / "engine_design",
        DATA / "risk_db" / "link_design",
    ],
    "taxonomy": [
        DATA / "risk_db" / "work_taxonomy",
        DATA / "risk_db" / "hazard_action",
        DATA / "risk_db" / "hazard_action_normalized",
        DATA / "risk_db" / "rules",
        DATA / "risk_db" / "scenario",
    ],
    "normalized": [
        DATA / "risk_db" / "law_normalized",
        DATA / "risk_db" / "law_standard",
        DATA / "normalized",
    ],
    "raw_kosha": [
        DATA / "raw" / "kosha",
        DATA / "raw" / "kosha_external",
        DATA / "raw" / "kosha_forms",
        DATA / "raw" / "moel_forms",
        DATA / "risk_db" / "guide_raw",
        DATA / "risk_db" / "raw_sources",
        DATA / "risk_db" / "real_cases",
        DATA / "risk_db" / "laws",
        DATA / "risk_db" / "equipment",
    ],
}

# 모든 분류된 디렉토리 집합 (미분류 검출용)
_ALL_CLASSIFIED: list[Path] = (
    list(INDEX_DIRS.values())
    + list(DB_DIRS.values())
    + [p for paths in EXTRA_DIRS.values() for p in paths]
)


def _is_dated_archive(f: Path, base: Path) -> bool:
    """날짜 폴더(YYYY-MM-DD) 또는 pipeline_input 루트 파일만 허용. _misc 등 제외."""
    rel_parts = f.relative_to(base).parts
    if len(rel_parts) == 1:
        return True  # pipeline_input 루트
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", rel_parts[0]))


def _collect_index_files():
    result = {}
    for label, base in INDEX_DIRS.items():
        files = sorted(base.rglob("*.json")) if base.exists() else []
        result[label] = []
        for f in files:
            if not _is_dated_archive(f, base):
                continue
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


def _collect_extra_files() -> dict[str, list[dict]]:
    result = {}
    for label, dirs in EXTRA_DIRS.items():
        result[label] = []
        for base in dirs:
            if not base.exists():
                continue
            for f in sorted(base.rglob("*")):
                if not f.is_file() or f.suffix not in (".json", ".jsonl", ".yml", ".yaml"):
                    continue
                stat = f.stat()
                result[label].append({
                    "file": str(f.relative_to(ROOT)),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "ext": f.suffix,
                })
    return result


def _collect_unclassified() -> list[str]:
    """data/ 아래 json/jsonl/yml 파일 중 분류 규칙에 포함되지 않은 것."""
    def _is_classified(f: Path) -> bool:
        for base in _ALL_CLASSIFIED:
            if not base.exists():
                continue
            try:
                f.relative_to(base)
                return True
            except ValueError:
                pass
        return False

    unclassified = []
    for f in sorted(DATA.rglob("*")):
        if not f.is_file() or f.suffix not in (".json", ".jsonl", ".yml", ".yaml"):
            continue
        if not _is_classified(f):
            unclassified.append(str(f.relative_to(ROOT)))
    return unclassified


def report(as_json=False, verify=False):
    index_data = _collect_index_files()
    db_data = _collect_db_files()
    extra_data = _collect_extra_files()
    unclassified = _collect_unclassified() if verify else []

    if as_json:
        out = {"index": index_data, "db": db_data, **extra_data}
        if verify:
            out["unclassified"] = unclassified
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    W = 60
    print("=" * W)
    print("  데이터 전체 분류 현황")
    print("=" * W)

    # ── INDEX ─────────────────────────────────────────────────────────────────
    print("\n[INDEX] API 목록·메타 수집")
    print("-" * W)
    for label, files in index_data.items():
        if not files:
            continue
        print(f"  {label}/")
        for f in files:
            cnt = f["item_count"]
            cnt_str = f"{cnt}건" if cnt >= 0 else "파싱오류"
            print(f"    {Path(f['file']).name:<43} {cnt_str:>6}  {f['fetched_at'][:10] or '?':>10}")

    # ── DB ────────────────────────────────────────────────────────────────────
    print("\n[DB] 조문·본문 수집")
    print("-" * W)
    for label, files in db_data.items():
        if not files:
            continue
        print(f"  {label}/")
        for f in files:
            print(f"    {Path(f['file']).name:<43} {f['record_count']:>6}건  {f['size_kb']:>8} KB")

    # ── EXTRA ─────────────────────────────────────────────────────────────────
    section_names = {
        "master":     "MASTER — 운영 마스터 데이터",
        "evidence":   "EVIDENCE — 법령 근거 개별 파일",
        "mapping":    "MAPPING — 위험·공종·법령 매핑",
        "schema":     "SCHEMA — API·스키마 정의",
        "design":     "DESIGN — 설계·리뷰 문서",
        "taxonomy":   "TAXONOMY — 공종·위험 분류 체계",
        "normalized": "NORMALIZED — 정규화 결과",
        "raw_kosha":  "RAW_KOSHA — KOSHA·MOEL 원천",
    }
    for key, title in section_names.items():
        files = extra_data.get(key, [])
        total_kb = sum(f["size_kb"] for f in files)
        print(f"\n[{title}]  {len(files)}개  {total_kb:.0f} KB")
        print("-" * W)
        # 디렉토리별 그룹 출력
        dir_groups: dict[str, list] = {}
        for f in files:
            parent = str(Path(f["file"]).parent)
            dir_groups.setdefault(parent, []).append(f)
        for dname, dfiles in dir_groups.items():
            print(f"  {dname}/  ({len(dfiles)}개)")
            for f in dfiles[:5]:  # 파일 많을 경우 앞 5개만
                print(f"    {Path(f['file']).name:<50} {f['size_kb']:>7} KB")
            if len(dfiles) > 5:
                print(f"    ... 외 {len(dfiles)-5}개")

    # ── UNCLASSIFIED ──────────────────────────────────────────────────────────
    if verify:
        print(f"\n[UNCLASSIFIED] 미분류 파일  {len(unclassified)}개")
        print("-" * W)
        if not unclassified:
            print("  없음 — 전체 분류 완료")
        for f in unclassified:
            print(f"  {f}")

    print("=" * W)


if __name__ == "__main__":
    report(
        as_json="--json" in sys.argv,
        verify="--verify" in sys.argv,
    )

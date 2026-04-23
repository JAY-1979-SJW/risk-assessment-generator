"""
신규 수집본 → data/forms/ 배치 + source_map.csv append

대상:
    (1) data/raw/law_api/licbyl/files/{new_ids}/**  — 2026-04-23 gap collection
        (이미 원래 수집 17개 외의 12개 safety-new)
    (2) data/raw/kosha_external/**/*  — KOSHA/MOEL/법령정보센터 외부 15개
        categories: work_plan / hoisting / excavation / aerial_lift / confined_space /
                    welding / tbm / education / committee / general

정책:
    - 기존 source_map.csv 에 이미 등재된 checksum은 스킵.
    - 등급 판정:
        licbyl new       → A (법정 별지/별표)
        committee 별표   → A (법정 별표)
        그 외 외부 수집   → B (KOSHA Guide·MOEL 배포 가이드)
    - 재명명: {source}__{doc_type}__{title_slug}__{date}.{ext}
    - 파일 destination:
        licbyl new       → data/forms/A_official/licbyl/
        committee 별표   → data/forms/A_official/licbyl/
        kosha_external   → data/forms/B_semi_official/kosha_form/ (doc_type별 prefix)
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_LICBYL = ROOT / "data" / "raw" / "law_api" / "licbyl" / "files"
RAW_EXT = ROOT / "data" / "raw" / "kosha_external"
EXT_MANIFEST = RAW_EXT / "download_manifest.json"

FORMS = ROOT / "data" / "forms"
SRC_MAP = FORMS / "source_map.csv"

# Original 17 licbyl IDs — 이미 source_map에 등재됨
EXISTING_LICBYL_IDS = {
    "17853601", "17853603", "17853655", "17853657", "17853659",
    "17853663", "17853665", "17853667", "17853671", "17853673",
    "17853675", "17853697", "17853703", "17853867", "17973935",
    "18014263", "18014277",
}


def slugify(t: str, max_tokens: int = 8) -> str:
    t = re.sub(r"[\[\]\(\)【】〔〕「」『』\"'“”‘’《》<>]", " ", t)
    t = re.sub(r"%[0-9A-Fa-f]{2}", "", t)
    t = re.sub(r"[ㆍ·・/\\,、、、¸★☆◈◆◇]", "_", t)
    t = re.sub(r"\s+", "_", t.strip())
    t = re.sub(r"[^0-9A-Za-z가-힣_\-]", "", t)
    t = re.sub(r"_+", "_", t).strip("_")
    if not t:
        return "untitled"
    parts = t.split("_")
    if len(parts) > max_tokens:
        parts = parts[:max_tokens]
    return "_".join(parts)


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_existing_checksums() -> set[str]:
    s: set[str] = set()
    if not SRC_MAP.exists():
        return s
    with SRC_MAP.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            cs = row.get("checksum_sha256", "").strip()
            if cs:
                s.add(cs)
    return s


def append_rows(rows: list[dict]) -> None:
    existed = SRC_MAP.exists()
    fields = [
        "view_path", "source_path", "source_url", "source_code", "source_id",
        "doc_type", "doc_title", "date", "ext", "authority_grade",
        "is_original", "checksum_sha256", "size_bytes", "notes",
    ]
    with SRC_MAP.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not existed:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


# ──────────────────────────────────────────────────────────── licbyl new

def process_licbyl_new() -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    log: list[str] = []
    if not RAW_LICBYL.exists():
        return rows, log
    existing_cs = load_existing_checksums()
    for id_dir in sorted(RAW_LICBYL.iterdir()):
        if not id_dir.is_dir():
            continue
        if id_dir.name in EXISTING_LICBYL_IDS:
            continue  # 이미 등재됨
        for src in sorted(id_dir.iterdir()):
            if not src.is_file():
                continue
            if src.suffix.lower() not in (".hwp", ".hwpx", ".pdf", ".docx", ".xlsx", ".xls"):
                continue
            cs = sha256_of(src)
            if cs in existing_cs:
                log.append(f"skip: duplicate checksum {src.name}")
                continue

            title = src.stem
            # [별지 제N호서식] 제목 (법령).ext / [별표 N] 제목 (법령).ext 패턴
            m = re.match(r"\[(별지|별표)\s*([^]\]]+)\]\s*(.+?)(?:\((.*?)\))?$", title)
            if m:
                bylaw_type, number, rest, law = m.groups()
                doc_type = bylaw_type
                number_slug = slugify(number, max_tokens=4)
                title_slug = slugify(rest, max_tokens=6)
                new_stem = f"LAW__{doc_type}__{title_slug}_{number_slug}__N_A"
            else:
                doc_type = "기타"
                new_stem = f"LAW__{doc_type}__{slugify(title, 8)}__N_A"
            new_name = f"{new_stem}{src.suffix.lower()}"

            dst = FORMS / "A_official" / "licbyl" / new_name
            i = 1
            while dst.exists() and sha256_of(dst) != cs:
                dst = FORMS / "A_official" / "licbyl" / f"{new_stem}__dup{i}{src.suffix.lower()}"
                i += 1
            if dst.exists():
                log.append(f"skip: exists same hash {dst.name}")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            log.append(f"copied: {dst.name}")

            rows.append({
                "view_path": str(dst.relative_to(ROOT)).replace("\\", "/"),
                "source_path": str(src.relative_to(ROOT)).replace("\\", "/"),
                "source_url": f"https://www.law.go.kr/ (licbyl ID {id_dir.name})",
                "source_code": "LAW",
                "source_id": id_dir.name,
                "doc_type": doc_type,
                "doc_title": title,
                "date": "N/A",
                "ext": src.suffix.lower().lstrip("."),
                "authority_grade": "A",
                "is_original": "Y",
                "checksum_sha256": cs,
                "size_bytes": src.stat().st_size,
                "notes": "산업안전보건 법정 별지/별표 (2026-04-23 gap 확장 수집)",
            })
    return rows, log


# ──────────────────────────────────────────────────────── kosha_external

EXT_TARGET_DIR_BY_CAT = {
    "work_plan": FORMS / "B_semi_official" / "kosha_form",
    "hoisting": FORMS / "B_semi_official" / "kosha_form",
    "excavation": FORMS / "B_semi_official" / "kosha_form",
    "aerial_lift": FORMS / "B_semi_official" / "kosha_form",
    "confined_space": FORMS / "B_semi_official" / "kosha_form",
    "welding": FORMS / "B_semi_official" / "kosha_form",
    "tbm": FORMS / "B_semi_official" / "kosha_form",
    "education": FORMS / "B_semi_official" / "kosha_form",
    "general": FORMS / "B_semi_official" / "kosha_form",
    "committee": FORMS / "A_official" / "licbyl",  # 법정 별표
}

EXT_AUTHORITY_BY_CAT = {
    "committee": "A",
    # 나머지는 B
}


def process_kosha_external() -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    log: list[str] = []
    if not EXT_MANIFEST.exists():
        return rows, log
    manifest = json.loads(EXT_MANIFEST.read_text(encoding="utf-8"))
    existing_cs = load_existing_checksums()

    for entry in manifest:
        if not entry.get("local"):
            log.append(f"skip: no local for {entry.get('title')}")
            continue
        src = ROOT / entry["local"]
        if not src.exists():
            log.append(f"skip: local missing {src}")
            continue
        cs = sha256_of(src)
        if cs in existing_cs:
            log.append(f"skip: duplicate checksum {src.name}")
            continue

        cat = entry.get("category", "general")
        doc_type = entry.get("doc_type") or "기타"
        title = entry.get("title", src.stem)
        source_origin = entry.get("origin", "")
        authority = EXT_AUTHORITY_BY_CAT.get(cat, entry.get("authority", "B"))

        # source code: committee(law.go.kr) → LAW; education(moel) → MOEL; kosha → KOSHA
        if cat == "committee":
            source_code = "LAW"
        elif "moel.go.kr" in entry.get("url", ""):
            source_code = "MOEL"
        else:
            source_code = "KOSHA"

        # 날짜 추출 (YYYY-MM-DD 또는 YYYY만)
        date = "N_A"
        m = re.search(r"(\d{4})[-년. ]?(\d{1,2})?[-월. ]?(\d{1,2})?", title)
        if m and m.group(1):
            y = m.group(1)
            if 2000 <= int(y) <= 2030:
                date = y

        title_slug = slugify(title, max_tokens=10)
        new_stem = f"{source_code}__{doc_type}__{title_slug}__{date}"
        new_name = f"{new_stem}{src.suffix.lower()}"

        target = EXT_TARGET_DIR_BY_CAT.get(cat, FORMS / "B_semi_official" / "kosha_form")
        dst = target / new_name
        i = 1
        while dst.exists() and sha256_of(dst) != cs:
            dst = target / f"{new_stem}__dup{i}{src.suffix.lower()}"
            i += 1
        if dst.exists():
            log.append(f"skip: exists same hash {dst.name}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        log.append(f"copied: {dst.name}")

        rows.append({
            "view_path": str(dst.relative_to(ROOT)).replace("\\", "/"),
            "source_path": str(src.relative_to(ROOT)).replace("\\", "/"),
            "source_url": entry.get("url", ""),
            "source_code": source_code,
            "source_id": source_origin[:100],
            "doc_type": doc_type,
            "doc_title": title,
            "date": date.replace("N_A", "N/A"),
            "ext": src.suffix.lower().lstrip("."),
            "authority_grade": authority,
            "is_original": "Y" if authority == "A" else "N",
            "checksum_sha256": cs,
            "size_bytes": src.stat().st_size,
            "notes": f"외부 수집 2026-04-23 ({cat}) — {source_origin}",
        })
    return rows, log


def main() -> int:
    all_rows: list[dict] = []
    all_log: list[str] = []
    for fn in (process_licbyl_new, process_kosha_external):
        rows, log = fn()
        all_rows.extend(rows)
        all_log.extend(log)

    if all_rows:
        append_rows(all_rows)
    print(f"appended {len(all_rows)} rows to source_map.csv")
    print(f"log entries: {len(all_log)}")
    print("--- log ---")
    for line in all_log:
        print(" ", line)
    return 0


if __name__ == "__main__":
    sys.exit(main())

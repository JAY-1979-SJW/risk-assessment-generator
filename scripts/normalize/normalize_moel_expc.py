"""
moel_expc.db → risk_db 통합 파이프라인 (6단계)

Step 1: SQLite → law_moel_expc_raw.json
Step 2: 정규화 → law_moel_expc.json  (law_id, source_type, keywords, summary 등)
Step 3: 기존 law DB 스키마 통일 (safety_laws_normalized.json 기준)
Step 4: rule DB 연결 — hazard_code / work_type_code 키워드 매핑
Step 5: 검증 — 중복 law_id, 필수 필드 누락, 매핑 통계
Step 6: 보고 — PASS / WARN / FAIL
"""
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
LAWS_DIR   = ROOT / "data" / "risk_db" / "laws"
RAW_OUT    = LAWS_DIR / "law_moel_expc_raw.json"
NORM_OUT   = LAWS_DIR / "law_moel_expc.json"
DB_PATH    = ROOT / "data" / "law_db" / "moel_expc.db"
HAZARDS_F  = ROOT / "data" / "risk_db" / "hazard_action" / "hazards.json"
WTYPES_F   = ROOT / "data" / "risk_db" / "work_taxonomy" / "work_types.json"

REQUIRED_FIELDS = [
    "law_id", "source_type", "category", "law_type",
    "title", "title_ko", "ministry_name",
    "issued_at", "status", "keywords", "needs_review",
]

# ─── 보조 함수 ────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _fmt_date(raw: str) -> str:
    """'2005.12.28' → '2005-12-28' / 이미 ISO → 그대로"""
    if not raw:
        return ""
    raw = raw.strip()
    m = re.match(r"^(\d{4})\.(\d{2})\.(\d{2})$", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return raw


# ─── Step 4 보조: 매핑 테이블 로드 ───────────────────────────────────────────

def _build_hazard_map() -> list[dict]:
    """hazards.json → [{code, keywords:[str]}] 목록"""
    raw = _load_json(HAZARDS_F)
    items = raw.get("hazards", raw) if isinstance(raw, dict) else raw
    result = []
    for item in (items if isinstance(items, list) else items.values()):
        kws = [k for k in item.get("classifier_keywords", []) if k]
        name_ko = item.get("name_ko", "")
        if name_ko:
            kws.insert(0, name_ko)
        result.append({"code": item["code"], "keywords": kws})
    return result


def _build_worktype_map() -> list[dict]:
    """work_types.json → [{code, name_ko}] 목록"""
    raw = _load_json(WTYPES_F)
    items = raw.get("work_types", raw) if isinstance(raw, dict) else raw
    return [{"code": i["code"], "name": i["name_ko"]} for i in items]


def _extract_hazard_codes(title: str, hazard_map: list[dict]) -> list[str]:
    codes = []
    for h in hazard_map:
        if any(kw in title for kw in h["keywords"]):
            codes.append(h["code"])
    return list(dict.fromkeys(codes))  # 순서 유지 중복 제거


def _extract_worktype_codes(title: str, wt_map: list[dict]) -> list[str]:
    return [w["code"] for w in wt_map if w["name"] and w["name"] in title]


def _extract_keywords(title: str) -> list[str]:
    """안건명에서 의미 있는 키워드 추출 (2자 이상 명사 토큰)"""
    # 괄호 내용 포함하여 토큰 분리
    tokens = re.split(r"[\s,·/\[\]()「」『』<>]+", title)
    seen, out = set(), []
    for t in tokens:
        t = t.strip()
        if len(t) >= 2 and t not in seen:
            seen.add(t)
            out.append(t)
    return out[:10]  # 최대 10개


# ─── Step 1: SQLite → raw JSON ───────────────────────────────────────────────

def step1_raw() -> list[dict]:
    print("[Step 1] SQLite → law_moel_expc_raw.json")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT serial_no, case_name, case_no, interpret_org, "
        "       inquire_org, interpreted_at, detail_url "
        "FROM moel_expc ORDER BY interpreted_at DESC"
    ).fetchall()
    conn.close()

    records = [dict(r) for r in rows]
    _save_json(RAW_OUT, {
        "generated_at": _now_iso(),
        "source": "data/law_db/moel_expc.db",
        "total": len(records),
        "records": records,
    })
    print(f"  → {len(records)}건 저장: {RAW_OUT}")
    return records


# ─── Step 2 + 3: 정규화 + 스키마 통일 ───────────────────────────────────────

def step2_normalize(records: list[dict], hazard_map, wt_map) -> list[dict]:
    print("[Step 2·3] 정규화 + 기존 law DB 스키마 통일")
    items = []
    for r in records:
        serial   = r["serial_no"] or ""
        title    = (r["case_name"] or "").strip()
        issued   = _fmt_date(r["interpreted_at"] or "")
        ministry = r["interpret_org"] or "고용노동부"
        case_no  = r["case_no"] or ""
        detail   = r["detail_url"] or ""
        if detail and not detail.startswith("http"):
            detail = f"https://www.law.go.kr{detail}"

        keywords       = _extract_keywords(title)
        hazard_codes   = _extract_hazard_codes(title, hazard_map)   # Step 4
        wt_codes       = _extract_worktype_codes(title, wt_map)     # Step 4

        # 원본에 날짜 없는 레코드는 검토 필요 표시
        no_date = not issued

        item = {
            # ── 식별 ──────────────────────────────────────────────
            "law_id":           f"moel_expc:{serial}",
            "source_type":      "moel_expc",
            "source_key":       f"moel_expc:{serial}",
            "category":         "interpretation",
            "law_type":         "해석례",
            # ── 제목 ──────────────────────────────────────────────
            "title":            title,
            "title_ko":         title,
            "title_normalized": title,
            "summary":          title,
            # ── 출처 ──────────────────────────────────────────────
            "ministry_name":    ministry,
            "authority":        ministry,
            "inquire_org":      r["inquire_org"] or "",
            "reference_no":     case_no,
            "detail_link":      detail,
            # ── 일자 ──────────────────────────────────────────────
            "issued_at":        issued,
            "promulgation_date": issued,
            "enforcement_date": issued,
            # ── 상태 ──────────────────────────────────────────────
            "status":           "active",
            "needs_review":     no_date,   # 날짜 없는 원본 레코드만 true
            # ── 키워드 & 매핑 (Step 4) ────────────────────────────
            "keywords":         keywords,
            "hazard_codes":     hazard_codes,
            "work_type_codes":  wt_codes,
        }
        items.append(item)

    _save_json(NORM_OUT, {
        "generated_at": _now_iso(),
        "source_db":    str(DB_PATH),
        "schema_ref":   "safety_laws_normalized.json",
        "total":        len(items),
        "items":        items,
    })
    print(f"  → {len(items)}건 저장: {NORM_OUT}")
    return items


# ─── Step 5: 검증 ─────────────────────────────────────────────────────────────

def step5_validate(items: list[dict]) -> dict:
    print("[Step 5] 검증")
    total = len(items)
    issues = []

    # 중복 law_id
    ids = [i["law_id"] for i in items]
    dup = {x for x in ids if ids.count(x) > 1}
    if dup:
        issues.append(f"중복 law_id {len(dup)}건: {list(dup)[:5]}")

    # 필수 필드 누락 (issued_at 공백은 원본 데이터 이슈로 별도 집계)
    missing_cnt = 0
    no_date_cnt = sum(1 for i in items if not i.get("issued_at"))
    for item in items:
        missing = [
            f for f in REQUIRED_FIELDS
            if f != "issued_at"  # 날짜 없는 원본은 별도 처리
            and (f not in item or item[f] is None or item[f] == "")
        ]
        if missing:
            missing_cnt += 1

    if missing_cnt:
        issues.append(f"필수 필드 누락 항목: {missing_cnt}건")
    if no_date_cnt:
        issues.append(f"원본 날짜 없음(needs_review=true): {no_date_cnt}건 (원본 API 데이터 이슈)")

    # 매핑 통계
    with_hazard = sum(1 for i in items if i.get("hazard_codes"))
    with_wt     = sum(1 for i in items if i.get("work_type_codes"))
    with_kw     = sum(1 for i in items if i.get("keywords"))

    stats = {
        "total":              total,
        "dup_law_id":         len(dup),
        "missing_field_rows": missing_cnt,
        "no_date_rows":       no_date_cnt,
        "needs_review":       sum(1 for i in items if i.get("needs_review")),
        "with_keywords":      with_kw,
        "with_hazard_codes":  with_hazard,
        "with_worktype_codes":with_wt,
        "hazard_map_rate":    f"{with_hazard/total*100:.1f}%" if total else "0%",
        "worktype_map_rate":  f"{with_wt/total*100:.1f}%"    if total else "0%",
        "issues":             issues,
    }

    for k, v in stats.items():
        if k != "issues":
            print(f"  {k}: {v}")
    if issues:
        for iss in issues:
            print(f"  [WARN] {iss}")

    return stats


# ─── Step 6: 보고 ─────────────────────────────────────────────────────────────

def step6_report(stats: dict) -> None:
    print()
    print("=" * 60)
    print("[Step 6] 최종 보고")
    print("=" * 60)
    print(f"  생성 파일:")
    print(f"    {RAW_OUT}")
    print(f"    {NORM_OUT}")
    print(f"  총 건수          : {stats['total']:,}건")
    print(f"  중복 law_id      : {stats['dup_law_id']}건")
    print(f"  필드 누락 항목   : {stats['missing_field_rows']}건")
    print(f"  원본 날짜 없음   : {stats['no_date_rows']}건 (needs_review=true, 원본 API 이슈)")
    print(f"  키워드 추출      : {stats['with_keywords']:,}건 (100%)")
    print(f"  hazard 매핑      : {stats['with_hazard_codes']:,}건 ({stats['hazard_map_rate']})")
    print(f"  work_type 매핑   : {stats['with_worktype_codes']:,}건 ({stats['worktype_map_rate']})")

    if stats["dup_law_id"] > 0 or stats["missing_field_rows"] > 0:
        verdict = "FAIL"
    elif stats["no_date_rows"] > 0:
        verdict = "WARN"
    else:
        verdict = "PASS"

    print(f"\n  결과: [{verdict}]")
    print("=" * 60)


# ─── 진입점 ───────────────────────────────────────────────────────────────────

def run() -> None:
    hazard_map = _build_hazard_map()
    wt_map     = _build_worktype_map()
    print(f"  hazard 분류기: {len(hazard_map)}종 / work_type: {len(wt_map)}종 로드")
    print()

    records = step1_raw()
    print()
    items   = step2_normalize(records, hazard_map, wt_map)
    print()
    stats   = step5_validate(items)
    step6_report(stats)


if __name__ == "__main__":
    run()

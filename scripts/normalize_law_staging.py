"""
법령/KOSHA staging JSON → law_standard 정규화 후보 파이프라인

입력:  data/risk_db/law_raw/laws_index.json
       data/risk_db/guide_raw/kosha_guides_index.json
출력:  data/risk_db/law_standard/safety_laws_normalized_candidates.json
       data/risk_db/law_standard/safety_laws_normalize_report.json
"""

import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
LAW_RAW     = ROOT / "data/risk_db/law_raw/laws_index.json"
GUIDE_RAW   = ROOT / "data/risk_db/guide_raw/kosha_guides_index.json"
LAW_STD     = ROOT / "data/risk_db/law_standard/safety_laws.json"
OUT_CAND    = ROOT / "data/risk_db/law_standard/safety_laws_normalized_candidates.json"
OUT_REPORT  = ROOT / "data/risk_db/law_standard/safety_laws_normalize_report.json"

# ─── 코드 체계 ──────────────────────────────────────────────────────────────
# 기존: OSHA-R-XX (enforcement_rule), OSHA-L-XX (law)
# 신규 후보 prefix: RAW-LAW-, RAW-DEC-, RAW-RULE-, RAW-NOTICE-, RAW-GUIDE-
# KOSHA guide: 원본 guide_code 재사용 (KOSHA-G-CONST-XXX)

TYPE_PREFIX = {
    "law":              "RAW-LAW",
    "enforcement_decree": "RAW-DEC",
    "enforcement_rule": "RAW-RULE",
    "notice":           "RAW-NOTICE",
    "guideline":        "RAW-GUIDE",
    "guide":            "KOSHA-G",
}


def _auto_code(law_type: str, seq: int) -> str:
    prefix = TYPE_PREFIX.get(law_type, "RAW-UNKNOWN")
    return f"{prefix}-{seq:03d}"


def normalize_law(entry: dict, seq: int) -> dict:
    law_type = entry.get("law_type") or "law"
    return {
        "law_code":   _auto_code(law_type, seq),
        "law_name":   entry.get("law_name") or None,
        "law_type":   law_type,
        "article_no": entry.get("article_no") or None,
        "title":      entry.get("title") or None,
        "summary":    entry.get("summary") or None,
        "source":     entry.get("source") or "law.go.kr",
        "source_org": entry.get("source_org") or "고용노동부",
        "raw_url":    entry.get("raw_url") or None,
        "is_active":  True,
        "_staging_status": entry.get("status"),
        "_mst":        entry.get("mst"),
        "_effective_date": entry.get("effective_date"),
    }


def normalize_guide(entry: dict, seq: int) -> dict:
    # KOSHA guide_code가 이미 있으면 그대로 사용
    existing_code = entry.get("guide_code")
    law_code = existing_code if existing_code else _auto_code("guide", seq)
    return {
        "law_code":   law_code,
        "law_name":   entry.get("title") or None,
        "law_type":   "guide",
        "article_no": None,
        "title":      entry.get("title") or None,
        "summary":    None,
        "source":     entry.get("source") or "kosha.or.kr",
        "source_org": entry.get("source_org") or "한국산업안전보건공단",
        "raw_url":    entry.get("raw_url") or None,
        "is_active":  True,
        "_staging_status": entry.get("status"),
        "_category":   entry.get("category"),
    }


# ─── 검증 함수 ───────────────────────────────────────────────────────────────

def validate_candidates(candidates: list, existing_laws: list) -> dict:
    existing_codes = {e["law_code"] for e in existing_laws}
    existing_names = {e["law_name"] for e in existing_laws}

    report = {
        "run_at": datetime.now().isoformat(),
        "total_candidates": len(candidates),

        # A. 코드 충돌
        "code_conflict_with_existing": [],
        "duplicate_code_within_candidates": [],
        "duplicate_name_with_existing": [],

        # B. 필드 누락
        "missing_law_name": [],
        "missing_source": [],
        "missing_law_type": [],
        "missing_raw_url": [],

        # C. 타입 일관성
        "is_active_not_bool": [],
        "article_no_inconsistent": [],

        # D. source 분포
        "source_distribution": {},
        "type_distribution": {},
    }

    seen_codes = {}
    for item in candidates:
        code = item.get("law_code")
        name = item.get("law_name")
        src  = item.get("source", "unknown")
        ltype = item.get("law_type", "unknown")

        # A. 코드 충돌
        if code in existing_codes:
            report["code_conflict_with_existing"].append(code)
        if code in seen_codes:
            report["duplicate_code_within_candidates"].append(code)
        else:
            seen_codes[code] = True
        if name and name in existing_names:
            report["duplicate_name_with_existing"].append({"law_code": code, "law_name": name})

        # B. 필드 누락
        if not name:
            report["missing_law_name"].append(code)
        if not item.get("source"):
            report["missing_source"].append(code)
        if not item.get("law_type"):
            report["missing_law_type"].append(code)
        if not item.get("raw_url"):
            report["missing_raw_url"].append(code)

        # C. 타입 일관성
        if not isinstance(item.get("is_active"), bool):
            report["is_active_not_bool"].append(code)
        art = item.get("article_no")
        if art is not None and not isinstance(art, str):
            report["article_no_inconsistent"].append(code)

        # D. 분포
        report["source_distribution"][src] = report["source_distribution"].get(src, 0) + 1
        report["type_distribution"][ltype] = report["type_distribution"].get(ltype, 0) + 1

    # 판정
    errors = (
        len(report["code_conflict_with_existing"]) +
        len(report["duplicate_code_within_candidates"]) +
        len(report["missing_law_name"]) +
        len(report["is_active_not_bool"])
    )
    warns = (
        len(report["missing_raw_url"]) +
        len(report["duplicate_name_with_existing"])
    )

    if errors > 0:
        report["verdict"] = "FAIL"
    elif warns > 0:
        report["verdict"] = "WARN"
    else:
        report["verdict"] = "PASS"

    report["error_count"] = errors
    report["warn_count"] = warns
    return report


# ─── 메인 ────────────────────────────────────────────────────────────────────

def main():
    # 1. 입력 로드
    with open(LAW_RAW, encoding="utf-8") as f:
        law_data = json.load(f)
    with open(GUIDE_RAW, encoding="utf-8") as f:
        guide_data = json.load(f)
    with open(LAW_STD, encoding="utf-8") as f:
        std_data = json.load(f)

    existing_laws = std_data.get("laws", [])

    print(f"[입력] laws_index:        {len(law_data.get('laws', []))}건")
    print(f"[입력] kosha_guides:      {len(guide_data.get('guides', []))}건")
    print(f"[기존] safety_laws.json:  {len(existing_laws)}건")

    # 2. 정규화
    candidates = []

    for i, entry in enumerate(law_data.get("laws", []), start=1):
        candidates.append(normalize_law(entry, i))

    for i, entry in enumerate(guide_data.get("guides", []), start=1):
        candidates.append(normalize_guide(entry, i))

    print(f"[정규화] 후보 총 {len(candidates)}건 생성")

    # 3. 검증
    report = validate_candidates(candidates, existing_laws)

    # 4. 저장
    out_json = {
        "_meta": {
            "version": "0.1-candidate",
            "note": "law_raw + guide_raw 정규화 후보. 기존 safety_laws.json에 직접 병합 금지.",
            "source_files": [str(LAW_RAW), str(GUIDE_RAW)],
            "created": datetime.now().isoformat(),
        },
        "laws": candidates,
    }
    with open(OUT_CAND, "w", encoding="utf-8") as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)

    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n[산출물] {OUT_CAND}")
    print(f"[리포트] {OUT_REPORT}")

    # 5. 콘솔 요약
    print(f"\n=== 충돌/품질 검증 ===")
    print(f"코드 충돌(기존):      {len(report['code_conflict_with_existing'])}건")
    print(f"코드 중복(후보내):    {len(report['duplicate_code_within_candidates'])}건")
    print(f"법령명 중복(기존):    {len(report['duplicate_name_with_existing'])}건  ← 조항 수준 vs 법령 수준 차이 허용")
    print(f"law_name 누락:       {len(report['missing_law_name'])}건")
    print(f"source 누락:         {len(report['missing_source'])}건")
    print(f"law_type 누락:       {len(report['missing_law_type'])}건")
    print(f"raw_url 누락:        {len(report['missing_raw_url'])}건")
    print(f"is_active 타입 이상: {len(report['is_active_not_bool'])}건")
    print(f"\nsource 분포:  {report['source_distribution']}")
    print(f"type 분포:    {report['type_distribution']}")
    print(f"\n최종 판정: {report['verdict']}  (오류:{report['error_count']}, 경고:{report['warn_count']})")


if __name__ == "__main__":
    main()

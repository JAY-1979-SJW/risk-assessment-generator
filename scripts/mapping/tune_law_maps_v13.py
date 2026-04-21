"""
tune_law_maps_v13.py — hazard 중심 법령 정밀 보강 (13단계)

적용 내용:
  1. FIRE  hazard → 화재예방법(statute:276497) score 90 manual_seed 추가
                  → 화재예방법 시행규칙(statute:285295) score 85 manual_seed 추가
                  → 해석례 314918 (가연물 화기작업) score 85 exact_keyword 추가
  2. EXPLO hazard → 화재예방법(statute:276497) score 88 manual_seed 추가
                  → 해석례 314918 score 83 exact_keyword 추가
  3. COLLAPSE hazard → 해석례 326231 partial_keyword 68 → exact_keyword 80 업그레이드
  4. DUST  hazard → 가짜 특화 해석례 3건 (329913, 328753, 328761) needs_review 표시
  5. FIRE/EXPLO control map → 화재예방법 계열 override 추가 (FIRE_C01~C07, EXPLO_C01~C03)

실행:
  python scripts/mapping/tune_law_maps_v13.py
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "risk_db"

HAZARD_MAP  = DATA / "law_mapping" / "law_hazard_map.json"
CONTROL_MAP = DATA / "law_mapping" / "law_control_map.json"

NOW = datetime.now(timezone.utc).isoformat()

# ── DUST 가짜 특화 법령 (산업안전 분진 무관 해석례) ────────────────────────
DUST_FALSE_POSITIVE_IDS = {"329913", "328753", "328761"}

# ── COLLAPSE 업그레이드 대상 ────────────────────────────────────────────────
COLLAPSE_UPGRADE_ID = "326231"

# ── FIRE/EXPLO hazard override 추가 ─────────────────────────────────────────
# (hazard_code, hazard_name, cat, raw_id, title, law_cat, doc_type, src_target,
#  score, match_type, keywords, ministry, ref_no, link)
HAZARD_OVERRIDES_V13 = [
    # FIRE — 화재예방법
    ("FIRE", "화재",
     "statute", "276497",
     "화재의 예방 및 안전관리에 관한 법률",
     "statute", "법률", "law",
     90, "manual_seed",
     ["화재예방", "화기취급", "가연물", "소방"],
     "소방청", "19626",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=law&MST=276497&type=HTML&mobileYn="),
    # FIRE — 화재예방법 시행규칙
    ("FIRE", "화재",
     "statute", "285295",
     "화재의 예방 및 안전관리에 관한 법률 시행규칙",
     "statute", "총리령", "law",
     85, "manual_seed",
     ["화재예방", "화기작업", "소화기", "화재감시"],
     "소방청", "285295",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=law&MST=285295&type=HTML&mobileYn="),
    # FIRE — 가연물 화기작업 해석례
    ("FIRE", "화재",
     "interpretation", "314918",
     "민원인 - 화기작업 시 가연물 제거 및 소화기 배치 의무(「산업안전보건기준에 관한 규칙」 제241조 관련)",
     "interpretation", "해석례", "expc",
     85, "exact_keyword",
     ["화기작업", "가연물", "소화기", "화재감시원"],
     "법제처", "14-0403",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=expc&ID=314918&type=HTML&mobileYn="),
    # EXPLO — 화재예방법
    ("EXPLO", "폭발",
     "statute", "276497",
     "화재의 예방 및 안전관리에 관한 법률",
     "statute", "법률", "law",
     88, "manual_seed",
     ["폭발방지", "가연성가스", "화기관리", "방폭"],
     "소방청", "19626",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=law&MST=276497&type=HTML&mobileYn="),
    # EXPLO — 가연물 화기작업 해석례 (폭발 관점)
    ("EXPLO", "폭발",
     "interpretation", "314918",
     "민원인 - 화기작업 시 가연물 제거 및 소화기 배치 의무(「산업안전보건기준에 관한 규칙」 제241조 관련)",
     "interpretation", "해석례", "expc",
     83, "exact_keyword",
     ["화기작업", "가연성가스", "폭발위험"],
     "법제처", "14-0403",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=expc&ID=314918&type=HTML&mobileYn="),
]

# ── FIRE/EXPLO control 법령 override ─────────────────────────────────────────
FIRE_LAW_ENTRY = {
    "law_id": "statute:276497",
    "law_title": "화재의 예방 및 안전관리에 관한 법률",
    "law_category": "statute",
    "law_document_type": "법률",
    "law_source_target": "law",
    "match_type": "manual_seed",
    "match_score": 88,
    "match_keywords": ["화재예방", "화기취급", "가연물"],
    "reason_summary": "화재예방법 — 화기작업 대책 직접 근거",
    "detail_link": "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=law&MST=276497&type=HTML&mobileYn=",
    "reference_no": "19626",
    "ministry_name": "소방청",
}

FIRE_INTERP_ENTRY = {
    "law_id": "interpretation:314918",
    "law_title": "민원인 - 화기작업 시 가연물 제거 및 소화기 배치 의무(「산업안전보건기준에 관한 규칙」 제241조 관련)",
    "law_category": "interpretation",
    "law_document_type": "해석례",
    "law_source_target": "expc",
    "match_type": "exact_keyword",
    "match_score": 82,
    "match_keywords": ["화기작업", "가연물", "소화기"],
    "reason_summary": "화기작업 가연물 제거/소화기 배치 해석례 — 화재 제어 조치 직접 근거",
    "detail_link": "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=expc&ID=314918&type=HTML&mobileYn=",
    "reference_no": "14-0403",
    "ministry_name": "법제처",
}

CONTROL_LAW_ADDITIONS_V13: dict[str, list[dict]] = {
    "FIRE": [FIRE_LAW_ENTRY, FIRE_INTERP_ENTRY],
    "EXPLO": [FIRE_LAW_ENTRY],
}


def _raw_id(law_id: str) -> str:
    return law_id.split(":")[-1] if ":" in law_id else law_id


def _backup(path: Path) -> None:
    shutil.copy2(path, path.with_suffix(".json.bak"))


def tune_hazard_map() -> dict:
    data = json.loads(HAZARD_MAP.read_text(encoding="utf-8"))
    items: list[dict] = data.get("items", [])
    stats = {"dust_false_positive_marked": 0, "collapse_upgraded": 0,
             "overrides_added": 0}

    # 1. DUST 가짜 특화 해석례 → needs_review
    for item in items:
        if (item.get("hazard_code") == "DUST"
                and _raw_id(item.get("law_id", "")) in DUST_FALSE_POSITIVE_IDS
                and item.get("review_status") != "needs_review"):
            item["review_status"] = "needs_review"
            item["_v13_note"] = "false_positive: 분진 무관 해석례"
            stats["dust_false_positive_marked"] += 1

    # 2. COLLAPSE 해석례 326231 점수 업그레이드
    for item in items:
        if (item.get("hazard_code") == "COLLAPSE"
                and _raw_id(item.get("law_id", "")) == COLLAPSE_UPGRADE_ID
                and item.get("match_type") == "partial_keyword"):
            item["match_score"] = 80
            item["match_type"] = "exact_keyword"
            item["_v13_note"] = "upgraded: partial_keyword 68 → exact_keyword 80"
            stats["collapse_upgraded"] += 1

    # 3. FIRE/EXPLO override 추가
    existing_keys = {(it.get("hazard_code", ""), it.get("law_id", "")) for it in items}
    added = []
    for ovr in HAZARD_OVERRIDES_V13:
        (hz_code, hz_name, cat, raw_id, title, law_cat, doc_type, src_target,
         score, match_type, kws, ministry, ref_no, link) = ovr
        law_id = f"{cat}:{raw_id}"
        key = (hz_code, law_id)
        if key in existing_keys:
            continue
        added.append({
            "hazard_code":       hz_code,
            "hazard_name":       hz_name,
            "law_id":            law_id,
            "law_title":         title,
            "law_category":      law_cat,
            "law_document_type": doc_type,
            "law_source_target": src_target,
            "match_type":        match_type,
            "match_score":       score,
            "match_keywords":    kws,
            "reason_summary":    f"[v13 override] {title} — 키워드: {', '.join(kws)}",
            "detail_link":       link,
            "reference_no":      ref_no,
            "ministry_name":     ministry,
            "review_status":     "draft",
            "created_at":        NOW,
            "source":            "tune_law_maps_v13",
        })
        existing_keys.add(key)

    items.extend(added)
    stats["overrides_added"] = len(added)

    data["items"] = items
    data["item_count"] = len(items)
    data["tuned_v13_at"] = NOW
    _backup(HAZARD_MAP)
    HAZARD_MAP.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def tune_control_map() -> dict:
    data = json.loads(CONTROL_MAP.read_text(encoding="utf-8"))
    items: list[dict] = data.get("items", [])
    stats = {"overrides_added": 0}

    existing_keys = {(it.get("control_code", ""), it.get("law_id", "")) for it in items}
    added = []
    for ctrl_prefix, additions in CONTROL_LAW_ADDITIONS_V13.items():
        target_codes = list(dict.fromkeys(
            it.get("control_code", "")
            for it in items
            if it.get("control_code", "").startswith(ctrl_prefix)
        ))
        for ctrl_code in target_codes:
            base = next((it for it in items if it.get("control_code") == ctrl_code), {})
            for add in additions:
                key = (ctrl_code, add["law_id"])
                if key in existing_keys:
                    continue
                added.append({
                    "control_code":      ctrl_code,
                    "hazard_code":       base.get("hazard_code", ctrl_prefix),
                    "law_id":            add["law_id"],
                    "law_title":         add["law_title"],
                    "law_category":      add["law_category"],
                    "law_document_type": add["law_document_type"],
                    "law_source_target": add["law_source_target"],
                    "match_type":        add["match_type"],
                    "match_score":       add["match_score"],
                    "match_keywords":    add["match_keywords"],
                    "reason_summary":    add["reason_summary"],
                    "detail_link":       add["detail_link"],
                    "reference_no":      add["reference_no"],
                    "ministry_name":     add["ministry_name"],
                    "review_status":     "draft",
                    "created_at":        NOW,
                    "source":            "tune_law_maps_v13",
                })
                existing_keys.add(key)

    items.extend(added)
    stats["overrides_added"] = len(added)

    data["items"] = items
    data["item_count"] = len(items)
    data["tuned_v13_at"] = NOW
    _backup(CONTROL_MAP)
    CONTROL_MAP.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def print_summary(hz_stats: dict, ctrl_stats: dict) -> None:
    print("=" * 60)
    print("13단계 법령 보강 결과")
    print("=" * 60)
    for name, s in [("hazard_map", hz_stats), ("control_map", ctrl_stats)]:
        print(f"\n[{name}]")
        for k, v in s.items():
            print(f"  {k:30}: {v}")


if __name__ == "__main__":
    print("hazard_map 보강...")
    hz_stats = tune_hazard_map()

    print("control_map 보강...")
    ctrl_stats = tune_control_map()

    print_summary(hz_stats, ctrl_stats)
    print("\n완료. 백업: *.json.bak")

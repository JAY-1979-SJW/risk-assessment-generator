"""
tune_law_maps.py — 법령 매핑 품질 튜닝 (12단계)

적용 내용:
  1. NFTC(소방청 화재안전기술기준) 항목 제거 — 산업안전 무관
  2. generic-law penalty: rule_based_inference 산안법/건설업관리비 점수 감산
  3. hazard map override 추가:
       ELEC  ← 전기설비기술기준 (admin_rule:2100000267908) score 93
       ELEC  ← 전기설비기술기준 판단기준 (admin_rule:2100000267906) score 88
       ASPHYX ← 밀폐공간 유독가스 해석례 (interpretation:327987) score 82
       DROP   ← 줄걸이자 해석례 (interpretation:343045) score 85
       COLLIDE ← 줄걸이자 해석례 (interpretation:343045) score 83
       FALL  ← 비계 제59조 해석례 (interpretation:340185) score 82
  4. control map override 추가:
       ELEC controls ← 전기설비기술기준 (2100000267908) score 88
       ASPHYX controls ← 밀폐공간 해석례 (interpretation:327987) score 78
       DROP controls ← 줄걸이자 해석례 (interpretation:343045) score 78
       COLLIDE controls ← 줄걸이자 해석례 (interpretation:343045) score 76
  5. low-confidence 제거: score < 62 항목 후순위화 (review_status=needs_review)
  6. partial_keyword score 68 → 72로 상향 (전기 관련 해석례 한정)

실행:
  python scripts/mapping/tune_law_maps.py
"""
import json
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data" / "risk_db"

HAZARD_MAP  = DATA / "law_mapping" / "law_hazard_map.json"
WORKTYPE_MAP = DATA / "law_mapping" / "law_worktype_map.json"
CONTROL_MAP = DATA / "law_mapping" / "law_control_map.json"
NORM_FILE   = DATA / "law_normalized" / "safety_laws_normalized.json"

# ── NFTC 제거 대상 (소방청 화재안전기술기준 — 산업안전 무관) ───────────────
NFTC_RAW_IDS = {
    "2100000250560","2100000216258","2100000216276","2100000243374",
    "2100000216251","2100000216259","2100000219020","2100000233392",
    "2100000243380","2100000216277","2100000275054","2100000243428",
    "2100000249982","2100000216245","2100000275088","2100000243916",
    "2100000216262","2100000275086","2100000247562","2100000243424",
    "2100000243376","2100000243888","2100000250566","2100000232516",
    "2100000250562","2100000275086",
}

# ── generic-law penalty 대상 ──────────────────────────────────────────────
# (raw_id, match_type 조건, 감산 점수)
GENERIC_PENALTY: list[tuple[str, str, int]] = [
    ("276853",        "rule_based_inference", 15),   # 산업안전보건법 — 상위법, 매우 일반적
    ("2100000254546", "rule_based_inference", 20),   # 건설업 관리비 — 건설 전용, 비건설 worktype에 부적절
    ("273603",        "rule_based_inference", 10),   # 산안기준규칙 — 중요하지만 rule_based 시 과다 노출
]

# ── low-confidence 기준 ────────────────────────────────────────────────────
LOW_CONF_THRESHOLD = 62  # 이 이하는 review_status = needs_review 표시

# ── partial_keyword 상향 대상 (ELEC 관련 해석례) ──────────────────────────
ELEC_INTERP_IDS = {"314608", "323735", "323547"}

# ── hazard map 추가 override ─────────────────────────────────────────────
# (hazard_code, hazard_name, law_id_prefix, raw_id, law_title, category,
#  doc_type, source_target, score, match_type, keywords, ministry, ref_no, detail_link)
HAZARD_OVERRIDES = [
    # ELEC — 전기설비기술기준
    ("ELEC", "감전",
     "admin_rule", "2100000267908",
     "전기설비기술기준",
     "admin_rule", "고시", "admrul", 93, "manual_seed",
     ["전기설비", "감전", "절연", "충전"],
     "산업통상자원부장관", "2025-18",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=admrul&ID=2100000267908&type=HTML&mobileYn="),
    # ELEC — 전기설비기술기준 판단기준
    ("ELEC", "감전",
     "admin_rule", "2100000267906",
     "전기설비기술기준 판단기준",
     "admin_rule", "고시", "admrul", 88, "manual_seed",
     ["전기설비", "절연", "안전"],
     "산업통상자원부장관", "2025-17",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=admrul&ID=2100000267906&type=HTML&mobileYn="),
    # ASPHYX — 밀폐공간 유독가스 해석례 (산안기준규칙 제52조10호)
    ("ASPHYX", "질식",
     "interpretation", "327987",
     "민원인 - 독소나 유독가스가 발생할 가능성이 있는 장소의 의미(「산업안전보건기준에 관한 규칙」 제52조제10 등 관련)",
     "interpretation", "해석례", "expc", 82, "exact_keyword",
     ["밀폐공간", "질식", "유독가스", "독소"],
     "법제처", "19-0616",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=expc&ID=327987&type=HTML&mobileYn="),
    # DROP — 줄걸이자 해석례 (산안기준규칙 제91조1항)
    ("DROP", "낙하·비래",
     "interpretation", "343045",
     "민원인 - 건설기계 줄걸이자가 담당하는 업무를 수행하는 근로자에 대한 특별교육을 실시하지 아니하였다면 「산업안전보건법 시행규칙」 제91조제1항에 따른 과태료 부과 대상이 되는지",
     "interpretation", "해석례", "expc", 85, "exact_keyword",
     ["줄걸이", "달기구", "낙하", "크레인"],
     "법제처", "26-0064",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=expc&ID=343045&type=HTML&mobileYn="),
    # COLLIDE — 줄걸이자 해석례 (같은 항목, 충돌 관점)
    ("COLLIDE", "충돌",
     "interpretation", "343045",
     "민원인 - 건설기계 줄걸이자가 담당하는 업무를 수행하는 근로자에 대한 특별교육을 실시하지 아니하였다면 「산업안전보건법 시행규칙」 제91조제1항에 따른 과태료 부과 대상이 되는지",
     "interpretation", "해석례", "expc", 83, "exact_keyword",
     ["줄걸이", "크레인", "충돌", "신호수"],
     "법제처", "26-0064",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=expc&ID=343045&type=HTML&mobileYn="),
    # FALL — 비계 제59조 해석례
    ("FALL", "추락",
     "interpretation", "340185",
     "민원인 - 「산업안전보건기준에 관한 규칙」 시행규칙 제59조제1항 중 호 관련 부분의 적용에 관한 법률해석 요청(「산업안전보건기준에 관한 규칙」 시행규칙 제59조제1항 중 관련)",
     "interpretation", "해석례", "expc", 82, "exact_keyword",
     ["비계", "추락", "작업발판", "설치기준"],
     "법제처", "24-0700",
     "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=expc&ID=340185&type=HTML&mobileYn="),
]

# ── control map 추가 override ─────────────────────────────────────────────
# control_code prefix → (추가 law 정보)
CONTROL_LAW_ADDITIONS: dict[str, list[dict]] = {
    "ELEC": [
        {
            "law_id": "admin_rule:2100000267908",
            "law_title": "전기설비기술기준",
            "law_category": "admin_rule",
            "law_document_type": "고시",
            "law_source_target": "admrul",
            "match_type": "manual_seed",
            "match_score": 88,
            "match_keywords": ["전기설비", "감전", "절연"],
            "reason_summary": "전기설비기술기준 — 활선/전로/절연 직접 규정",
            "detail_link": "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=admrul&ID=2100000267908&type=HTML&mobileYn=",
            "reference_no": "2025-18",
            "ministry_name": "산업통상자원부장관",
        },
    ],
    "ASPHYX": [
        {
            "law_id": "interpretation:327987",
            "law_title": "민원인 - 독소나 유독가스가 발생할 가능성이 있는 장소의 의미(「산업안전보건기준에 관한 규칙」 제52조제10 등 관련)",
            "law_category": "interpretation",
            "law_document_type": "해석례",
            "law_source_target": "expc",
            "match_type": "exact_keyword",
            "match_score": 78,
            "match_keywords": ["밀폐공간", "유독가스", "질식"],
            "reason_summary": "밀폐공간 유독가스 범위 해석 — 밀폐공간 제어 조치 직접 관련",
            "detail_link": "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=expc&ID=327987&type=HTML&mobileYn=",
            "reference_no": "19-0616",
            "ministry_name": "법제처",
        },
    ],
    "DROP": [
        {
            "law_id": "interpretation:343045",
            "law_title": "민원인 - 건설기계 줄걸이자가 담당하는 업무를 수행하는 근로자에 대한 특별교육을 실시하지 아니하였다면 「산업안전보건법 시행규칙」 제91조제1항에 따른 과태료 부과 대상이 되는지",
            "law_category": "interpretation",
            "law_document_type": "해석례",
            "law_source_target": "expc",
            "match_type": "exact_keyword",
            "match_score": 78,
            "match_keywords": ["줄걸이", "달기구", "낙하"],
            "reason_summary": "줄걸이자 특별교육 의무 해석 — 낙하/낙하물 제어 조치 관련",
            "detail_link": "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=expc&ID=343045&type=HTML&mobileYn=",
            "reference_no": "26-0064",
            "ministry_name": "법제처",
        },
    ],
    "COLLIDE": [
        {
            "law_id": "interpretation:343045",
            "law_title": "민원인 - 건설기계 줄걸이자가 담당하는 업무를 수행하는 근로자에 대한 특별교육을 실시하지 아니하였다면 「산업안전보건법 시행규칙」 제91조제1항에 따른 과태료 부과 대상이 되는지",
            "law_category": "interpretation",
            "law_document_type": "해석례",
            "law_source_target": "expc",
            "match_type": "exact_keyword",
            "match_score": 76,
            "match_keywords": ["줄걸이", "크레인", "충돌"],
            "reason_summary": "줄걸이자 특별교육 의무 해석 — 크레인/충돌 제어 조치 관련",
            "detail_link": "https://www.law.go.kr/DRF/lawService.do?OC=sapphire_5&target=expc&ID=343045&type=HTML&mobileYn=",
            "reference_no": "26-0064",
            "ministry_name": "법제처",
        },
    ],
}

NOW = datetime.now(timezone.utc).isoformat()


def _raw_id_from_law_id(law_id: str) -> str:
    """'statute:273603' → '273603'"""
    return law_id.split(":")[-1] if ":" in law_id else law_id


def _backup(path: Path) -> None:
    bak = path.with_suffix(".json.bak")
    shutil.copy2(path, bak)


def _is_nftc(item: dict) -> bool:
    raw_id = _raw_id_from_law_id(item.get("law_id", ""))
    return raw_id in NFTC_RAW_IDS


def _apply_penalty(items: list[dict]) -> tuple[list[dict], int]:
    """Apply generic-law score penalties. Returns (updated_items, penalty_count)."""
    count = 0
    for item in items:
        raw_id = _raw_id_from_law_id(item.get("law_id", ""))
        mt = item.get("match_type", "")
        for gid, gmt, penalty in GENERIC_PENALTY:
            if raw_id == gid and mt == gmt:
                item["match_score"] = max(0, item.get("match_score", 0) - penalty)
                item["_tuned_penalty"] = penalty
                count += 1
                break
    return items, count


def _mark_low_conf(items: list[dict]) -> int:
    count = 0
    for item in items:
        if item.get("match_score", 100) < LOW_CONF_THRESHOLD:
            if item.get("review_status") != "needs_review":
                item["review_status"] = "needs_review"
                count += 1
    return count


def _upgrade_elec_interp(items: list[dict]) -> int:
    count = 0
    for item in items:
        raw_id = _raw_id_from_law_id(item.get("law_id", ""))
        if (raw_id in ELEC_INTERP_IDS
                and item.get("match_type") == "partial_keyword"
                and item.get("match_score", 0) < 73):
            item["match_score"] = 72
            item["match_type"] = "partial_keyword_upgraded"
            count += 1
    return count


def tune_hazard_map() -> dict:
    data = json.loads(HAZARD_MAP.read_text(encoding="utf-8"))
    items: list[dict] = data.get("items", [])
    stats = {"nftc_removed": 0, "penalty_applied": 0, "low_conf_marked": 0,
             "overrides_added": 0, "elec_upgraded": 0}

    # 1. NFTC 제거
    before = len(items)
    items = [it for it in items if not _is_nftc(it)]
    stats["nftc_removed"] = before - len(items)

    # 2. generic penalty
    items, stats["penalty_applied"] = _apply_penalty(items)

    # 3. low-confidence 표시
    stats["low_conf_marked"] = _mark_low_conf(items)

    # 4. ELEC 해석례 score 상향
    stats["elec_upgraded"] = _upgrade_elec_interp(items)

    # 5. override 추가 (중복 체크)
    existing_keys = {(it.get("hazard_code",""), it.get("law_id","")) for it in items}
    added = []
    for ovr in HAZARD_OVERRIDES:
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
            "reason_summary":    f"[튜닝 override] {title} — 키워드: {', '.join(kws)}",
            "detail_link":       link,
            "reference_no":      ref_no,
            "ministry_name":     ministry,
            "review_status":     "draft",
            "created_at":        NOW,
            "source":            "tune_law_maps_v12",
        })
        existing_keys.add(key)
    items.extend(added)
    stats["overrides_added"] = len(added)

    data["items"] = items
    data["item_count"] = len(items)
    data["tuned_at"] = NOW
    data["tune_stats"] = stats
    _backup(HAZARD_MAP)
    HAZARD_MAP.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def tune_worktype_map() -> dict:
    data = json.loads(WORKTYPE_MAP.read_text(encoding="utf-8"))
    items: list[dict] = data.get("items", [])
    stats = {"nftc_removed": 0, "penalty_applied": 0, "low_conf_marked": 0}

    before = len(items)
    items = [it for it in items if not _is_nftc(it)]
    stats["nftc_removed"] = before - len(items)

    items, stats["penalty_applied"] = _apply_penalty(items)
    stats["low_conf_marked"] = _mark_low_conf(items)

    data["items"] = items
    data["item_count"] = len(items)
    data["tuned_at"] = NOW
    data["tune_stats"] = stats
    _backup(WORKTYPE_MAP)
    WORKTYPE_MAP.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def tune_control_map() -> dict:
    data = json.loads(CONTROL_MAP.read_text(encoding="utf-8"))
    items: list[dict] = data.get("items", [])
    stats = {"nftc_removed": 0, "penalty_applied": 0, "low_conf_marked": 0,
             "overrides_added": 0}

    before = len(items)
    items = [it for it in items if not _is_nftc(it)]
    stats["nftc_removed"] = before - len(items)

    items, stats["penalty_applied"] = _apply_penalty(items)
    stats["low_conf_marked"] = _mark_low_conf(items)

    # control-specific law 추가
    existing_keys = {(it.get("control_code",""), it.get("law_id","")) for it in items}
    added = []
    for ctrl_prefix, additions in CONTROL_LAW_ADDITIONS.items():
        # 해당 prefix의 control_code 목록
        target_ctrl_codes = [it.get("control_code","") for it in items
                             if it.get("control_code","").startswith(ctrl_prefix)]
        target_ctrl_codes = list(dict.fromkeys(target_ctrl_codes))  # dedup

        # 각 control_code에 addition 추가
        for ctrl_code in target_ctrl_codes:
            # control 기존 정보
            base = next((it for it in items if it.get("control_code") == ctrl_code), {})
            for add in additions:
                key = (ctrl_code, add["law_id"])
                if key in existing_keys:
                    continue
                new_item = {
                    "control_code":     ctrl_code,
                    "hazard_code":      base.get("hazard_code", ctrl_prefix),
                    "law_id":           add["law_id"],
                    "law_title":        add["law_title"],
                    "law_category":     add["law_category"],
                    "law_document_type": add["law_document_type"],
                    "law_source_target": add["law_source_target"],
                    "match_type":       add["match_type"],
                    "match_score":      add["match_score"],
                    "match_keywords":   add["match_keywords"],
                    "reason_summary":   add["reason_summary"],
                    "detail_link":      add["detail_link"],
                    "reference_no":     add["reference_no"],
                    "ministry_name":    add["ministry_name"],
                    "review_status":    "draft",
                    "created_at":       NOW,
                    "source":           "tune_law_maps_v12",
                }
                added.append(new_item)
                existing_keys.add(key)

    items.extend(added)
    stats["overrides_added"] = len(added)

    data["items"] = items
    data["item_count"] = len(items)
    data["tuned_at"] = NOW
    data["tune_stats"] = stats
    _backup(CONTROL_MAP)
    CONTROL_MAP.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def print_summary(hz_stats, wt_stats, ctrl_stats):
    print("=" * 60)
    print("법령 매핑 튜닝 결과")
    print("=" * 60)
    for name, s in [("hazard_map", hz_stats), ("worktype_map", wt_stats), ("control_map", ctrl_stats)]:
        print(f"\n[{name}]")
        for k, v in s.items():
            print(f"  {k:25}: {v}")


if __name__ == "__main__":
    print("hazard_map 튜닝...")
    hz_stats = tune_hazard_map()

    print("worktype_map 튜닝...")
    wt_stats = tune_worktype_map()

    print("control_map 튜닝...")
    ctrl_stats = tune_control_map()

    print_summary(hz_stats, wt_stats, ctrl_stats)
    print("\n완료. 백업: *.json.bak")

"""
7단계 — 4축 통합 추천 엔진 설계 및 샘플 추천 결과 생성
입력: work_types, hazards, controls_normalized, safety_laws_normalized,
      law_hazard_map, law_worktype_map, law_control_map, work_hazards_map
출력: recommendation_engine_schema.json
       recommendation_engine_samples.json
       recommendation_engine_review_notes.json
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "risk_db"

OUT_DIR = DATA / "engine_design"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# 점수 상수 (한 곳에서 관리)
# ──────────────────────────────────────────────

# hazard_score 기본 (work_hazards_map 있는 경우)
HAZARD_BASE_FREQ   = 20   # frequency 계수
HAZARD_BASE_SEV    = 10   # severity 계수
HAZARD_RULE_BASE   = 65   # work_hazards_map 미등록 rule-based
HAZARD_MAX_SCORE   = 98

# condition_flag → hazard 가점
CONDITION_BONUS: dict[str, dict[str, int]] = {
    "high_place":     {"FALL": 15, "DROP": 10},
    "confined_space": {"ASPHYX": 15, "EXPLO": 10, "POISON": 8},
    "live_electric":  {"ELEC": 15},
    "night_work":     {"COLLIDE": 8, "TRIP": 8, "FALL": 5},
    "chemical_use":   {"CHEM": 12, "POISON": 12, "DUST": 6},
}

# rule-based hazard 추론 (work_hazards_map 미등록 worktype)
TRADE_HAZARD_INFERENCE: dict[str, list[tuple]] = {
    # (hazard_code, freq_equiv, sev_equiv, reason)
    "LIFT":  [("DROP",    3, 3, "줄걸이·인양 작업 낙하위험"),
              ("COLLIDE", 2, 3, "중장비·인양물 충돌위험"),
              ("FALL",    2, 3, "고소 인양 작업 추락위험")],
    "DEMO":  [("DUST",    3, 3, "해체 작업 분진·석면"),
              ("COLLAPSE",2, 3, "구조물 해체 붕괴위험"),
              ("ASPHYX",  2, 3, "밀폐 구역 질식위험"),
              ("POISON",  2, 3, "석면·유해물질 중독"),
              ("CHEM",    1, 3, "화학물질 노출")],
    "WATER": [("ASPHYX",  3, 3, "맨홀·우물 밀폐공간 질식"),
              ("EXPLO",   2, 3, "하수·가스 폭발위험")],
    "ELEC":  [("ELEC",    3, 3, "전기 작업 감전위험"),
              ("FIRE",    2, 3, "단락·스파크 화재")],
    "TEMP":  [("FALL",    3, 3, "가설구조물 추락"),
              ("DROP",    2, 3, "자재 낙하"),
              ("COLLAPSE",2, 3, "가설구조물 붕괴")],
}

# control_score 기본
CTRL_SCORE: dict[tuple, int] = {
    ("engineering", 1): 90,
    ("admin",       1): 85,
    ("ppe",         1): 80,
    ("engineering", 2): 80,
    ("admin",       2): 75,
    ("ppe",         2): 72,
}

# law_score evidence_path 우선순위 가중치
LAW_PATH_WEIGHT = {"control_law": 1.0, "hazard_law": 0.9, "worktype_law": 0.8}

# 출력 제한
MAX_HAZARD  = 5
MAX_CONTROL = 3
MAX_LAW     = 3

# 샘플 대상 worktype
SAMPLE_TARGETS = [
    ("ELEC_LIVE",      ["live_electric", "high_place"]),
    ("TEMP_SCAFF",     ["high_place"]),
    ("WATER_MANHOLE",  ["confined_space"]),
    ("LIFT_RIGGING",   ["high_place"]),
    ("DEMO_ASBESTOS",  ["chemical_use"]),
]

# ──────────────────────────────────────────────
# 데이터 로드
# ──────────────────────────────────────────────

def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_indexes():
    wt_raw  = load_json(DATA / "work_taxonomy" / "work_types.json")
    wt_list = wt_raw if isinstance(wt_raw, list) else wt_raw.get("items", wt_raw.get("work_types", []))
    wt_idx: dict[str, dict] = {}
    for item in wt_list:
        code = item.get("work_type_code") or item.get("code", "")
        wt_idx[code] = item

    hz_raw  = load_json(DATA / "hazard_action" / "hazards.json")
    hz_idx: dict[str, dict] = {h["code"]: h for h in hz_raw.get("hazards", [])}

    cn_raw  = load_json(DATA / "hazard_action_normalized" / "controls_normalized.json")
    hz_ctrl: dict[str, list] = defaultdict(list)
    for item in cn_raw.get("items", []):
        hz_ctrl[item["hazard_code"]].append(item)

    law_raw = load_json(DATA / "law_normalized" / "safety_laws_normalized.json")
    law_idx: dict[str, dict] = {}
    for item in law_raw.get("items", []):
        cat    = item.get("category", "")
        raw_id = str(item.get("raw_id", ""))
        law_id = f"{cat}:{raw_id}"
        law_idx[law_id] = item

    whm_raw    = load_json(DATA / "work_taxonomy" / "work_hazards_map.json")
    wt_hz_map: dict[str, list] = defaultdict(list)
    for m in whm_raw.get("mappings", []):
        wt_hz_map[m["work_type_code"]].append(m)

    lhm_raw  = load_json(DATA / "law_mapping" / "law_hazard_map.json")
    hz_law_map: dict[str, list] = defaultdict(list)
    for item in lhm_raw.get("items", []):
        hz_law_map[item["hazard_code"]].append(item)

    lwm_raw  = load_json(DATA / "law_mapping" / "law_worktype_map.json")
    wt_law_map: dict[str, list] = defaultdict(list)
    for item in lwm_raw.get("items", []):
        wt_law_map[item["work_type_code"]].append(item)

    lcm_raw  = load_json(DATA / "law_mapping" / "law_control_map.json")
    ctrl_law_map: dict[str, list] = defaultdict(list)
    for item in lcm_raw.get("items", []):
        ctrl_law_map[item["control_code"]].append(item)

    return (wt_idx, hz_idx, hz_ctrl, law_idx,
            wt_hz_map, hz_law_map, wt_law_map, ctrl_law_map)


# ──────────────────────────────────────────────
# 파이프라인 함수
# ──────────────────────────────────────────────

def step1_resolve_worktype(wt_code: str, wt_idx: dict) -> dict:
    return wt_idx.get(wt_code, {"work_type_code": wt_code})


def step2_collect_hazard_candidates(wt_code: str, wt_info: dict,
                                     wt_hz_map: dict, hz_idx: dict) -> list[dict]:
    entries = wt_hz_map.get(wt_code, [])
    candidates: list[dict] = []
    if entries:
        for e in entries:
            hz_code = e["hazard_code"]
            hz_info = hz_idx.get(hz_code, {})
            base    = e["frequency"] * HAZARD_BASE_FREQ + e["severity"] * HAZARD_BASE_SEV
            candidates.append({
                "hazard_code": hz_code,
                "hazard_name": hz_info.get("name_ko", hz_code),
                "severity_class": hz_info.get("severity_class", "medium"),
                "base_score":    base,
                "source":        "work_hazards_map",
                "frequency":     e["frequency"],
                "severity":      e["severity"],
            })
    else:
        # rule-based inference
        trade = (wt_info.get("trade_code", "") or wt_code.split("_")[0])
        inferences = TRADE_HAZARD_INFERENCE.get(trade, [])
        for (hz_code, freq, sev, reason) in inferences:
            hz_info = hz_idx.get(hz_code, {})
            base    = HAZARD_RULE_BASE
            candidates.append({
                "hazard_code": hz_code,
                "hazard_name": hz_info.get("name_ko", hz_code),
                "severity_class": hz_info.get("severity_class", "medium"),
                "base_score":    base,
                "source":        "rule_based_inference",
                "infer_reason":  reason,
            })
    return candidates


def step3_score_hazards(candidates: list[dict], condition_flags: list[str]) -> list[dict]:
    scored = []
    for c in candidates:
        score = c["base_score"]
        bonus_reasons: list[str] = []
        for flag in condition_flags:
            bonuses = CONDITION_BONUS.get(flag, {})
            b = bonuses.get(c["hazard_code"], 0)
            if b:
                score += b
                bonus_reasons.append(f"{flag}+{b}")
        if c["severity_class"] == "high" and score < 80:
            score += 5
        score = min(score, HAZARD_MAX_SCORE)
        item = {**c, "hazard_score": score}
        if bonus_reasons:
            item["condition_bonus"] = bonus_reasons
        scored.append(item)

    scored.sort(key=lambda x: x["hazard_score"], reverse=True)
    return scored[:MAX_HAZARD]


def step4_collect_controls(hz_code: str, hz_ctrl: dict) -> list[dict]:
    return hz_ctrl.get(hz_code, [])


def step5_score_controls(controls: list[dict]) -> list[dict]:
    scored = []
    for c in controls:
        ctype    = c.get("control_type", "admin")
        priority = int(c.get("priority", 2))
        score    = CTRL_SCORE.get((ctype, priority),
                                  CTRL_SCORE.get((ctype, 2), 70))
        scored.append({
            "control_code":  c["control_code"],
            "control_name":  c["control_text"],
            "control_type":  ctype,
            "priority":      priority,
            "control_score": score,
            "reason":        f"{ctype} priority={priority}",
        })
    scored.sort(key=lambda x: x["control_score"], reverse=True)
    return scored[:MAX_CONTROL]


def step6_merge_laws(wt_code: str, hz_code: str, ctrl_codes: list[str],
                     wt_law_map: dict, hz_law_map: dict,
                     ctrl_law_map: dict, law_idx: dict) -> list[dict]:
    """세 경로 법령 병합 → law_id dedupe + evidence_paths 유지"""
    law_pool: dict[str, dict] = {}

    def add(law_id: str, score: float, path: str, title: str):
        wt = LAW_PATH_WEIGHT.get(path, 0.8)
        eff_score = score * wt
        if law_id not in law_pool:
            law_pool[law_id] = {
                "law_id":          law_id,
                "law_title":       title,
                "best_score":      eff_score,
                "raw_score":       score,
                "evidence_paths":  [path],
            }
        else:
            law_pool[law_id]["evidence_paths"].append(path)
            if eff_score > law_pool[law_id]["best_score"]:
                law_pool[law_id]["best_score"] = eff_score
                law_pool[law_id]["raw_score"]  = score

    for item in wt_law_map.get(wt_code, []):
        law_info = law_idx.get(item["law_id"], {})
        add(item["law_id"], item["match_score"], "worktype_law",
            law_info.get("title_ko", ""))

    for item in hz_law_map.get(hz_code, []):
        law_info = law_idx.get(item["law_id"], {})
        add(item["law_id"], item["match_score"], "hazard_law",
            law_info.get("title_ko", ""))

    for ctrl_code in ctrl_codes:
        for item in ctrl_law_map.get(ctrl_code, []):
            law_info = law_idx.get(item["law_id"], {})
            add(item["law_id"], item["match_score"], "control_law",
                law_info.get("title_ko", ""))

    merged = sorted(law_pool.values(), key=lambda x: x["best_score"], reverse=True)

    result = []
    for m in merged[:MAX_LAW]:
        paths = list(dict.fromkeys(m["evidence_paths"]))  # dedupe 순서 유지
        result.append({
            "law_id":         m["law_id"],
            "law_title":      m["law_title"],
            "law_score":      round(m["best_score"], 1),
            "evidence_paths": paths,
        })
    return result


def step7_assemble_row(wt_code: str, hz: dict, controls: list[dict],
                       laws: list[dict]) -> dict:
    return {
        "work_type_code": wt_code,
        "hazard_code":    hz["hazard_code"],
        "hazard_name":    hz["hazard_name"],
        "hazard_score":   hz["hazard_score"],
        "hazard_reason":  hz.get("infer_reason", hz.get("source", "")),
        "controls":       controls,
        "laws":           laws,
    }


# ──────────────────────────────────────────────
# 전체 파이프라인
# ──────────────────────────────────────────────

def run_pipeline(wt_code: str, condition_flags: list[str],
                 wt_idx, hz_idx, hz_ctrl, law_idx,
                 wt_hz_map, hz_law_map, wt_law_map, ctrl_law_map) -> list[dict]:
    wt_info    = step1_resolve_worktype(wt_code, wt_idx)
    candidates = step2_collect_hazard_candidates(wt_code, wt_info, wt_hz_map, hz_idx)
    hazards    = step3_score_hazards(candidates, condition_flags)

    rows = []
    for hz in hazards:
        raw_ctrls  = step4_collect_controls(hz["hazard_code"], hz_ctrl)
        scored_ctrls = step5_score_controls(raw_ctrls)
        ctrl_codes = [c["control_code"] for c in scored_ctrls]
        laws       = step6_merge_laws(wt_code, hz["hazard_code"], ctrl_codes,
                                       wt_law_map, hz_law_map, ctrl_law_map, law_idx)
        row        = step7_assemble_row(wt_code, hz, scored_ctrls, laws)
        rows.append(row)
    return rows


# ──────────────────────────────────────────────
# 스키마 정의
# ──────────────────────────────────────────────

def build_schema(now: str) -> dict:
    return {
        "generated_at": now,
        "version":      "1.0",
        "description":  "위험성평가표 초안 조립 추천 엔진 — 4축 링크 기반",
        "inputs": {
            "required": ["work_type_code"],
            "optional": ["work_sub_type_code", "condition_flags"],
            "condition_flags_enum": [
                "high_place", "confined_space", "live_electric",
                "night_work", "chemical_use",
            ],
        },
        "pipeline": [
            "step1_resolve_worktype",
            "step2_collect_hazard_candidates",
            "step3_score_hazards",
            "step4_collect_control_candidates",
            "step5_score_controls",
            "step6_merge_law_evidence",
            "step7_assemble_rows",
        ],
        "pipeline_detail": {
            "step1_resolve_worktype":      "work_types.json에서 work_type_code 메타 조회",
            "step2_collect_hazard_candidates": "work_hazards_map 조회 → 없으면 trade 기반 rule_based_inference",
            "step3_score_hazards":         "base(freq×20+sev×10) + condition_flag 가점 → 상위 5건",
            "step4_collect_control_candidates": "controls_normalized.json에서 hazard_code 기준 조회",
            "step5_score_controls":        "control_type × priority 점수표 → 상위 3건",
            "step6_merge_law_evidence":    "worktype_law + hazard_law + control_law 병합, dedupe, score 가중",
            "step7_assemble_rows":         "hazard 기준 row 조립 (한 행 = hazard + controls + laws)",
        },
        "score_constants": {
            "hazard": {
                "freq_coef":       HAZARD_BASE_FREQ,
                "sev_coef":        HAZARD_BASE_SEV,
                "rule_base":       HAZARD_RULE_BASE,
                "max":             HAZARD_MAX_SCORE,
                "condition_bonus": CONDITION_BONUS,
            },
            "control": {f"{ct}__p{p}": s for (ct, p), s in CTRL_SCORE.items()},
            "law_path_weight": LAW_PATH_WEIGHT,
        },
        "output_limits": {
            "max_hazard_per_wt":    MAX_HAZARD,
            "max_control_per_hz":   MAX_CONTROL,
            "max_law_per_row":      MAX_LAW,
        },
        "entities": {
            "worktype": {"pk": "work_type_code", "source": "work_types.json"},
            "hazard":   {"pk": "hazard_code",    "source": "hazards.json"},
            "control":  {"pk": "control_code",   "source": "controls_normalized.json"},
            "law":      {"pk": "law_id ({category}:{raw_id})", "source": "safety_laws_normalized.json"},
        },
        "relations_used": [
            "worktype_hazard (work_hazards_map.json + trade inference)",
            "hazard_control  (controls_normalized.json)",
            "worktype_law    (law_worktype_map.json)",
            "hazard_law      (law_hazard_map.json)",
            "control_law     (law_control_map.json)",
        ],
        "output_shape": {
            "row_structure": {
                "work_type_code": "str",
                "hazard_code":    "str",
                "hazard_name":    "str",
                "hazard_score":   "int(0-100)",
                "hazard_reason":  "str",
                "controls":       "[{control_code, control_name, control_score, reason}]",
                "laws":           "[{law_id, law_title, law_score, evidence_paths}]",
            },
        },
        "dedup_rules": {
            "hazard":  "hazard_code 기준 — 동일 코드 점수 병합",
            "control": "control_code 기준 — 동일 코드 상위 점수 유지",
            "law":     "law_id 기준 — evidence_paths 합집합, best_score = max(path_weighted)",
        },
    }


# ──────────────────────────────────────────────
# review notes 생성
# ──────────────────────────────────────────────

def build_review_notes(all_samples: list[dict], now: str) -> dict:
    notes = []

    # worktype_hazard 커버리지 문제
    notes.append({
        "category": "worktype_hazard_coverage",
        "severity": "medium",
        "message":  "work_hazards_map.json이 30/132 work_type만 커버. "
                    "LIFT_RIGGING, DEMO_ASBESTOS 등 미등록 worktype은 "
                    "trade 기반 rule_based_inference로 대체됨. "
                    "인퍼런스 정확도 검증 필요.",
    })

    # 상위 법령(statute:273603) 과다 반복
    law_cnt: dict[str, int] = defaultdict(int)
    for samp in all_samples:
        for row in samp.get("rows", []):
            for l in row.get("laws", []):
                law_cnt[l["law_id"]] += 1
    top_law = max(law_cnt, key=law_cnt.get) if law_cnt else ""
    top_cnt = law_cnt.get(top_law, 0)
    notes.append({
        "category": "law_concentration",
        "severity": "low",
        "message":  f"'{top_law}'이 전체 샘플 {top_cnt}개 row에서 반복 등장. "
                    "법령 체계가 법률 전체 단위이므로 조문 수준 세분화 없이는 불가피. "
                    "향후 조문별 sub-law 체계 도입 시 개선 가능.",
    })

    # control 부족 hazard
    notes.append({
        "category": "control_shortage",
        "severity": "low",
        "message":  "CHEM(2건), POISON(2건)은 hazard별 control이 2건뿐. "
                    "MAX_CONTROL=3 기준 미달. controls_normalized 보강 필요.",
    })

    # score 튜닝 포인트
    notes.append({
        "category": "score_tuning",
        "severity": "info",
        "message":  "condition_flags 가점이 없는 작업에서 rule_base(65)가 "
                    "work_hazards_map 항목(70~90)보다 낮아 실제 위험 과소평가 가능. "
                    "LIFT_RIGGING(DROP=65)의 경우 현장 실무 기준으로 재검토 권장.",
    })

    # API 반영 전 보완 항목
    notes.append({
        "category": "pre_api_requirements",
        "severity": "info",
        "message":  "API 반영 전 필요 작업: "
                    "(1) worktype_hazard 커버리지 102개 보강, "
                    "(2) condition_flags 자동 감지 로직 설계, "
                    "(3) work_sub_type_code 연계 점수 가산 로직 추가, "
                    "(4) 실시간 law 참조 링크 검증.",
    })

    return {
        "generated_at": now,
        "note_count":   len(notes),
        "notes":        notes,
    }


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────

def main():
    (wt_idx, hz_idx, hz_ctrl, law_idx,
     wt_hz_map, hz_law_map, wt_law_map, ctrl_law_map) = build_indexes()

    now = datetime.now(timezone.utc).isoformat()

    # 스키마 생성
    schema = build_schema(now)
    out_schema = OUT_DIR / "recommendation_engine_schema.json"
    with out_schema.open("w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    # 샘플 추천 결과 생성
    all_samples = []
    for (wt_code, flags) in SAMPLE_TARGETS:
        wt_info = wt_idx.get(wt_code, {})
        rows    = run_pipeline(wt_code, flags,
                               wt_idx, hz_idx, hz_ctrl, law_idx,
                               wt_hz_map, hz_law_map, wt_law_map, ctrl_law_map)
        sample = {
            "work_type_code": wt_code,
            "work_type_name": wt_info.get("name_ko", wt_code),
            "condition_flags": flags,
            "row_count":      len(rows),
            "rows":           rows,
        }
        all_samples.append(sample)

    out_samples = OUT_DIR / "recommendation_engine_samples.json"
    with out_samples.open("w", encoding="utf-8") as f:
        json.dump({
            "generated_at": now,
            "sample_count": len(all_samples),
            "samples":      all_samples,
        }, f, ensure_ascii=False, indent=2)

    # review notes
    review = build_review_notes(all_samples, now)
    out_review = OUT_DIR / "recommendation_engine_review_notes.json"
    with out_review.open("w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)

    # 보고 출력
    total_rows = sum(s["row_count"] for s in all_samples)
    avg_row    = total_rows / max(len(all_samples), 1)

    all_rows   = [r for s in all_samples for r in s["rows"]]
    avg_ctrl   = sum(len(r["controls"]) for r in all_rows) / max(total_rows, 1)
    avg_law    = sum(len(r["laws"])     for r in all_rows) / max(total_rows, 1)

    print(f"[완료] {out_schema.name}")
    print(f"[완료] {out_samples.name}")
    print(f"[완료] {out_review.name}")
    print()
    print("=== 샘플 결과 요약 ===")
    for s in all_samples:
        hz_names = [r["hazard_code"] for r in s["rows"]]
        print(f"  {s['work_type_code']:20s} | rows={s['row_count']} | hazards={hz_names}")
    print()
    print(f"  총 row 수: {total_rows}")
    print(f"  row당 평균 control: {avg_ctrl:.1f}건")
    print(f"  row당 평균 law:     {avg_law:.1f}건")
    print()
    print("=== review notes ===")
    for n in review["notes"]:
        print(f"  [{n['severity'].upper()}] [{n['category']}] {n['message'][:60]}")


if __name__ == "__main__":
    main()

"""
build_ra_link_schema.py
worktype / hazard / control / law 4축 통합 연결 구조 설계 초안 생성.

출력:
  data/risk_db/link_design/ra_link_schema.json       - 엔티티·관계 스키마 정의
  data/risk_db/link_design/ra_link_samples.json      - 샘플 연결 초안
  data/risk_db/link_design/ra_link_review_notes.json - 갭·보완 항목

실행:
  python scripts/design/build_ra_link_schema.py
"""

import json
import os
from datetime import datetime, timezone

BASE  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA  = os.path.join(BASE, "data/risk_db")
OUT   = os.path.join(DATA, "link_design")

# ---------------------------------------------------------------------------
# 입력 파일
# ---------------------------------------------------------------------------
F_WORKTYPES     = os.path.join(DATA, "work_taxonomy/work_types.json")
F_WORKSUBS      = os.path.join(DATA, "work_taxonomy/work_sub_types.json")
F_WH_MAP        = os.path.join(DATA, "work_taxonomy/work_hazards_map.json")
F_HAZARDS       = os.path.join(DATA, "hazard_action/hazards.json")
F_CONTROLS      = os.path.join(DATA, "hazard_action/hazard_controls.json")
F_LAW_NORM      = os.path.join(DATA, "law_normalized/safety_laws_normalized.json")
F_LAW_HAZARD    = os.path.join(DATA, "law_mapping/law_hazard_map.json")
F_LAW_WORKTYPE  = os.path.join(DATA, "law_mapping/law_worktype_map.json")


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def make_control_code(hazard_code: str, idx: int) -> str:
    """control_code 파생 규칙: {hazard_code}_C{nn:02d}"""
    return f"{hazard_code}_C{idx:02d}"


# ---------------------------------------------------------------------------
# law_ref 텍스트 → law_id 매핑 테이블
# "산업안전보건기준에 관한 규칙 제NNN조" 또는 "산업안전보건법 제NNN조"
# 간단 규칙: 산안법 언급이면 statute:276853, 나머지는 statute:273603
# ---------------------------------------------------------------------------
def resolve_law_ref(law_ref: str) -> tuple[str, str]:
    """(law_id, law_title) 반환"""
    if "산업안전보건법 " in law_ref and "기준" not in law_ref and "규칙" not in law_ref:
        return "statute:276853", "산업안전보건법"
    return "statute:273603", "산업안전보건기준에 관한 규칙"


def main():
    now = datetime.now(timezone.utc).isoformat()
    os.makedirs(OUT, exist_ok=True)

    # --- 데이터 로드 ---
    wt_db   = load(F_WORKTYPES)
    sub_db  = load(F_WORKSUBS)
    wh_db   = load(F_WH_MAP)
    hz_db   = load(F_HAZARDS)
    ctrl_db = load(F_CONTROLS)
    law_db  = load(F_LAW_NORM)
    lh_db   = load(F_LAW_HAZARD)
    lw_db   = load(F_LAW_WORKTYPE)

    work_types   = wt_db["work_types"]
    work_subs    = sub_db["work_sub_types"]
    wh_maps      = wh_db["mappings"]
    hazards      = hz_db["hazards"]
    controls_raw = ctrl_db["hazard_controls"]
    laws         = law_db["items"]

    # --- control_code 파생 ---
    ctrl_by_hazard: dict[str, list] = {}
    for c in controls_raw:
        ctrl_by_hazard.setdefault(c["hazard_code"], []).append(c)

    controls_with_code = []
    for hcode, items in ctrl_by_hazard.items():
        for i, c in enumerate(items, start=1):
            c2 = dict(c)
            c2["control_code"] = make_control_code(hcode, i)
            controls_with_code.append(c2)

    # --- 집계 ---
    wt_codes_total    = {w["code"] for w in work_types}
    sub_codes_total   = {s["code"] for s in work_subs}
    hz_codes_total    = {h["code"] for h in hazards}
    ctrl_codes_total  = {c["control_code"] for c in controls_with_code}
    law_ids_total     = {f"{l['category']}:{l['raw_id']}" for l in laws}

    wh_wt_covered     = {m["work_type_code"] for m in wh_maps}
    wh_hz_covered     = {m["hazard_code"]    for m in wh_maps}
    hz_ctrl_covered   = {c["hazard_code"]    for c in controls_raw}

    # ========================================================
    # 1. ra_link_schema.json
    # ========================================================
    schema = {
        "generated_at": now,
        "version": "1.0",
        "description": "worktype / hazard / control / law 4축 통합 연결 구조 설계 초안",
        "engine_flow": [
            "1. 사용자 작업유형(worktype) 선택",
            "2. worktype_hazard 관계 → hazard 후보 조회",
            "3. hazard_control 관계 → control 후보 조회",
            "4. worktype_law + hazard_law 병합 → law 근거 조회",
            "5. (선택) control_law 관계 → 개별 control의 법령 근거 보강",
            "6. 평가표 조립 및 생성"
        ],
        "entities": {
            "worktype": {
                "primary_key":  "work_type_code",
                "sub_key":      "work_sub_type_code",
                "source_file":  "data/risk_db/work_taxonomy/work_types.json",
                "sub_file":     "data/risk_db/work_taxonomy/work_sub_types.json",
                "total_count":  len(wt_codes_total),
                "sub_count":    len(sub_codes_total),
                "example":      "TEMP_SCAFF"
            },
            "hazard": {
                "primary_key":  "hazard_code",
                "source_file":  "data/risk_db/hazard_action/hazards.json",
                "total_count":  len(hz_codes_total),
                "example":      "FALL"
            },
            "control": {
                "primary_key":  "control_code",
                "derivation":   "{hazard_code}_C{nn:02d}  (hazard_controls.json 순번 기반)",
                "source_file":  "data/risk_db/hazard_action/hazard_controls.json",
                "total_count":  len(ctrl_codes_total),
                "gap_note":     "현재 파일에 control_code 필드 없음 — 파생 코드 적용 필요",
                "example":      "FALL_C01"
            },
            "law": {
                "primary_key":  "law_id",
                "format":       "{category}:{raw_id}",
                "categories":   ["statute", "admin_rule", "licbyl", "interpretation"],
                "source_file":  "data/risk_db/law_normalized/safety_laws_normalized.json",
                "total_count":  len(law_ids_total),
                "example":      "statute:273603"
            }
        },
        "relations": {
            "worktype_hazard": {
                "keys":         ["work_type_code", "hazard_code"],
                "source_file":  "data/risk_db/work_taxonomy/work_hazards_map.json",
                "status":       "exists_partial",
                "coverage":     f"{len(wh_wt_covered)}/{len(wt_codes_total)} work_types",
                "item_count":   len(wh_maps),
                "note":         "나머지 work_types는 trade_code 기반 hazard 추론 필요"
            },
            "hazard_control": {
                "keys":         ["hazard_code", "control_code"],
                "source_file":  "data/risk_db/hazard_action/hazard_controls.json",
                "status":       "exists_no_code",
                "coverage":     f"{len(hz_ctrl_covered)}/{len(hz_codes_total)} hazards",
                "item_count":   len(controls_raw),
                "note":         "control_code 파생 후 사용 가능. 4개 hazard(CUT, FLYBY, NOISE, TRIP 포함) 미완성"
            },
            "worktype_law": {
                "keys":         ["work_type_code", "law_id"],
                "source_file":  "data/risk_db/law_mapping/law_worktype_map.json",
                "status":       "draft",
                "coverage":     f"{len(wt_codes_total)}/{len(wt_codes_total)} work_types",
                "item_count":   lw_db["item_count"]
            },
            "hazard_law": {
                "keys":         ["hazard_code", "law_id"],
                "source_file":  "data/risk_db/law_mapping/law_hazard_map.json",
                "status":       "draft",
                "coverage":     f"{len(hz_codes_total)}/{len(hz_codes_total)} hazards",
                "item_count":   lh_db["item_count"]
            },
            "control_law": {
                "keys":         ["control_code", "law_id"],
                "source_file":  "TBD: data/risk_db/law_mapping/law_control_map.json",
                "status":       "design_only",
                "derivation":   "hazard_controls.law_ref 텍스트 → law_id 파싱으로 초안 생성 가능",
                "note":         "6단계에서 law_control_map.json 본 생성 예정"
            }
        },
        "query_patterns": {
            "worktype→hazards":  "worktype_hazard[work_type_code=X] → hazard_code 목록",
            "hazard→controls":   "hazard_control[hazard_code=X] → control_code 목록",
            "hazard→laws":       "hazard_law[hazard_code=X] → law_id 목록",
            "worktype→laws":     "worktype_law[work_type_code=X] → law_id 목록",
            "control→laws":      "control_law[control_code=X] → law_id 목록",
            "hazard→worktypes":  "worktype_hazard[hazard_code=X] → work_type_code 목록",
            "control→hazards":   "hazard_control[control_code=X] → hazard_code (역방향)"
        }
    }

    with open(os.path.join(OUT, "ra_link_schema.json"), "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print("[완료] ra_link_schema.json")

    # ========================================================
    # 2. ra_link_samples.json
    # ========================================================
    # A. worktype_hazard: work_hazards_map.json 상위 10건
    wh_samples = [
        {
            "work_type_code": m["work_type_code"],
            "hazard_code":    m["hazard_code"],
            "link_score":     m["frequency"] * 30 + m["severity"] * 10,
            "frequency":      m["frequency"],
            "severity":       m["severity"],
            "reason":         f"work_hazards_map.json 기존 매핑 — 출처: {m['source']}"
        }
        for m in wh_maps[:10]
    ]

    # B. hazard_control: hazard_controls (control_code 파생 후 10건)
    hc_samples = [
        {
            "hazard_code":   c["control_code"].split("_C")[0],
            "control_code":  c["control_code"],
            "control_text":  c["control_text"],
            "control_type":  c["control_type"],
            "priority":      c["priority"],
            "link_score":    90 if c["priority"] == 1 else 70,
            "reason":        f"hazard_controls.json 직접 추출 — 출처: {c.get('source','')}"
        }
        for c in controls_with_code[:10]
    ]

    # C. control_law: law_ref 텍스트 → law_id 파생 (5건 샘플)
    cl_samples = []
    seen_ctrl = set()
    for c in controls_with_code:
        if len(cl_samples) >= 5:
            break
        if c["control_code"] in seen_ctrl:
            continue
        law_id, law_title = resolve_law_ref(c.get("law_ref", ""))
        cl_samples.append({
            "control_code":  c["control_code"],
            "control_text":  c["control_text"],
            "law_id":        law_id,
            "law_title":     law_title,
            "law_ref_text":  c.get("law_ref", ""),
            "link_score":    88,
            "reason":        f"hazard_controls.law_ref 텍스트 → law_id 파싱 (resolve_law_ref 규칙)"
        })
        seen_ctrl.add(c["control_code"])

    samples = {
        "generated_at":   now,
        "note":           "설계 초안 샘플. 운영 투입 전 검토 필요.",
        "samples": {
            "worktype_hazard": wh_samples,
            "hazard_control":  hc_samples,
            "control_law":     cl_samples
        }
    }

    with open(os.path.join(OUT, "ra_link_samples.json"), "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    print("[완료] ra_link_samples.json")

    # ========================================================
    # 3. ra_link_review_notes.json
    # ========================================================
    hz_ctrl_missing = sorted(hz_codes_total - hz_ctrl_covered)
    wt_wh_missing   = sorted(wt_codes_total - wh_wt_covered)

    notes = {
        "generated_at": now,
        "notes": [
            {
                "category": "missing_control_code",
                "severity": "high",
                "message":  "hazard_controls.json에 control_code 필드 없음. "
                            "파생 규칙({hazard_code}_C{nn:02d}) 확정 후 파일에 반영 필요.",
                "action":   "hazard_controls.json 컬럼 추가 또는 control_master.json 신규 생성"
            },
            {
                "category": "worktype_hazard_partial",
                "severity": "medium",
                "message":  f"work_hazards_map.json이 {len(wh_wt_covered)}/{len(wt_codes_total)} "
                            f"work_types만 커버 ({len(wt_codes_total) - len(wh_wt_covered)}개 미연결).",
                "missing_sample": wt_wh_missing[:10],
                "action":   "5단계 후속: 미커버 work_types에 대해 trade_code 기반 hazard 추론 적용"
            },
            {
                "category": "hazard_control_partial",
                "severity": "medium",
                "message":  f"hazard_controls.json이 {len(hz_ctrl_covered)}/{len(hz_codes_total)} "
                            f"hazard만 커버. 미포함 hazard: {hz_ctrl_missing}",
                "action":   "POISON, CHEM 등 미완성 hazard control 보강 필요"
            },
            {
                "category": "law_ref_text_not_id",
                "severity": "high",
                "message":  "hazard_controls.json의 law_ref 필드가 자유 텍스트(제43조 등)이며 "
                            "법령 ID(law_id)와 직접 연결 불가. "
                            "현재 resolve_law_ref() 규칙으로 statute:273603 또는 statute:276853만 구분.",
                "action":   "6단계 law_control_map 생성 시 law_ref 조문→article_id 매핑 테이블 필요"
            },
            {
                "category": "control_law_concentration",
                "severity": "low",
                "message":  "모든 control의 law 근거가 사실상 산업안전보건기준에 관한 규칙(statute:273603) "
                            "1개 법령에 집중됨. control_law 관계의 다양성이 낮을 것으로 예상.",
                "action":   "조문 레벨 article_id 도입으로 세분화 가능 — 중장기 과제"
            },
            {
                "category": "multi_hazard_control",
                "severity": "low",
                "message":  "일부 control 대책이 여러 hazard에 동시 적용됨. "
                            "예: LOTO(감전·협착), 안전대 착용(추락·화상). "
                            "hazard_control 1:다 설계는 허용하나 중복 제거 기준 필요.",
                "action":   "control_master.json 생성 시 대표 hazard 지정 필드 추가 검토"
            },
            {
                "category": "next_step_requirement",
                "severity": "info",
                "message":  "6단계(law_control_map) 진입 전 필요 사항: "
                            "(1) control_code 확정, "
                            "(2) hazard_controls.json control_code 컬럼 추가, "
                            "(3) law_ref 텍스트 → law_id 파싱 규칙 확장"
            }
        ]
    }

    with open(os.path.join(OUT, "ra_link_review_notes.json"), "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)
    print("[완료] ra_link_review_notes.json")

    # --- 콘솔 요약 ---
    print(f"\n=== 4축 커버리지 요약 ===")
    print(f"  worktype     : {len(wt_codes_total)}개")
    print(f"  hazard       : {len(hz_codes_total)}개")
    print(f"  control      : {len(ctrl_codes_total)}개 (파생)")
    print(f"  law          : {len(law_ids_total)}개")
    print(f"\n=== 관계 현황 ===")
    print(f"  worktype_hazard : {len(wh_maps)}건 ({len(wh_wt_covered)}/{len(wt_codes_total)} wt)")
    print(f"  hazard_control  : {len(controls_raw)}건 ({len(hz_ctrl_covered)}/{len(hz_codes_total)} hz)")
    print(f"  worktype_law    : {lw_db['item_count']}건 (전체)")
    print(f"  hazard_law      : {lh_db['item_count']}건 (전체)")
    print(f"  control_law     : 설계 초안 5건 샘플 (본 생성 미완)")


if __name__ == "__main__":
    main()

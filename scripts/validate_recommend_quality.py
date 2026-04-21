"""
추천 품질 샘플 검증 스크립트 (12단계)

4대 worktype + 2개 추가 유형 대상 매핑 데이터 기반
row/control/law 품질을 사람이 읽기 좋은 표 형식으로 출력.

실행:
  python scripts/validate_recommend_quality.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "risk_db"

WH_MAP      = DATA / "work_taxonomy" / "work_hazards_map.json"
HZ_MAP      = DATA / "law_mapping" / "law_hazard_map.json"
CTRL_MAP    = DATA / "law_mapping" / "law_control_map.json"
WT_MAP      = DATA / "law_mapping" / "law_worktype_map.json"
CTRL_NORM   = DATA / "hazard_action_normalized" / "controls_normalized.json"

TARGET_WORKTYPES = ["ELEC_LIVE", "WATER_MANHOLE", "TEMP_SCAFF", "LIFT_RIGGING",
                    "ELEC_PANEL", "WELD_ARC"]

# generic law raw_ids
GENERIC_IDS = {"273603", "276853", "2100000254546", "2100000251014"}

LOW_CONF = 62
HIGH_CONF = 82


def load(path: Path) -> dict:
    if not path.exists():
        print(f"[MISSING] {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _raw_id(law_id: str) -> str:
    return law_id.split(":")[-1] if ":" in law_id else law_id


def main() -> int:
    wh_data   = load(WH_MAP)
    hz_data   = load(HZ_MAP)
    ctrl_data = load(CTRL_MAP)
    wt_data   = load(WT_MAP)
    cn_data   = load(CTRL_NORM)

    # work → hazard 맵
    work_hazards: dict[str, list[str]] = defaultdict(list)
    for e in wh_data.get("mappings", wh_data.get("items", [])):
        work_hazards[e.get("work_type_code", "")].append(e.get("hazard_code", ""))

    # hazard → law 맵 (active only)
    hz_laws: dict[str, list[dict]] = defaultdict(list)
    for it in hz_data.get("items", []):
        if it.get("review_status") != "needs_review":
            hz_laws[it.get("hazard_code", "")].append(it)

    # control → law 맵
    ctrl_laws: dict[str, list[dict]] = defaultdict(list)
    for it in ctrl_data.get("items", []):
        ctrl_laws[it.get("control_code", "")].append(it)

    # worktype → law 맵
    wt_laws: dict[str, list[dict]] = defaultdict(list)
    for it in wt_data.get("items", []):
        wt_laws[it.get("work_type_code", "")].append(it)

    # control → 상세 정보
    ctrl_detail: dict[str, dict] = {}
    for it in cn_data.get("items", []):
        ctrl_detail[it.get("control_code", "")] = it

    # hazard → controls 맵
    hz_ctrls: dict[str, list[str]] = defaultdict(list)
    for cc, detail in ctrl_detail.items():
        hz = detail.get("hazard_code", "")
        if hz:
            hz_ctrls[hz].append(cc)

    print("=" * 70)
    print("추천 품질 샘플 검증 리포트")
    print("=" * 70)

    all_pass = True
    metrics_table = []

    for wt_code in TARGET_WORKTYPES:
        hazards = work_hazards.get(wt_code, [])
        wt_law_list = wt_laws.get(wt_code, [])

        # worktype 지표
        high_conf_wt = [l for l in wt_law_list
                        if l.get("match_score", 0) >= HIGH_CONF
                        and l.get("match_type") in ("manual_seed","exact_keyword","prelinked_law_id")]
        generic_wt = [l for l in wt_law_list
                      if _raw_id(l.get("law_id","")) in GENERIC_IDS]

        # row: hazard별 대표 law 수집
        rows = []
        for hz_code in hazards:
            laws = hz_laws.get(hz_code, [])
            ctrl_codes = hz_ctrls.get(hz_code, [])
            ctrl_names = [ctrl_detail[cc].get("control_name","")[:30]
                          for cc in ctrl_codes[:4] if cc in ctrl_detail]

            # control별 law 다양성
            ctrl_law_diversity = set()
            for cc in ctrl_codes:
                for cl in ctrl_laws.get(cc, []):
                    ctrl_law_diversity.add(_raw_id(cl.get("law_id","")))

            row_laws = sorted(laws, key=lambda x: -x.get("match_score", 0))
            high_conf_laws = [l for l in row_laws if l.get("match_score",0) >= HIGH_CONF]
            generic_laws = [l for l in row_laws if _raw_id(l.get("law_id","")) in GENERIC_IDS]

            # 공학적/관리적/PPE 구분
            ctrl_types = [ctrl_detail[cc].get("control_type","")
                          for cc in ctrl_codes if cc in ctrl_detail]
            has_eng = "engineering" in ctrl_types
            has_admin = "administrative" in ctrl_types
            has_ppe = "ppe" in ctrl_types

            rows.append({
                "hazard_code": hz_code,
                "ctrl_count": len(ctrl_codes),
                "ctrl_names": ctrl_names,
                "law_count": len(laws),
                "high_conf": len(high_conf_laws),
                "generic_law_ratio": len(generic_laws) / max(len(laws),1),
                "ctrl_law_ids": list(ctrl_law_diversity),
                "has_eng": has_eng,
                "has_admin": has_admin,
                "has_ppe": has_ppe,
                "law_titles": [l.get("law_title","")[:45] for l in row_laws[:3]],
            })

        # 지표 계산
        avg_ctrl = sum(r["ctrl_count"] for r in rows) / max(len(rows), 1)
        avg_law  = sum(r["law_count"]  for r in rows) / max(len(rows), 1)
        hc_ratio = sum(r["high_conf"]  for r in rows) / max(sum(r["law_count"] for r in rows), 1)
        gr_avg   = sum(r["generic_law_ratio"] for r in rows) / max(len(rows), 1)
        overrides_in_wt = sum(1 for l in wt_law_list
                              if l.get("source") == "tune_law_maps_v12")
        wt_override = sum(1 for r in rows
                          for lid in r["ctrl_law_ids"]
                          if lid not in GENERIC_IDS)

        metrics_table.append({
            "wt": wt_code,
            "rows": len(rows),
            "avg_ctrl": round(avg_ctrl, 1),
            "avg_law": round(avg_law, 1),
            "hc_ratio": round(hc_ratio * 100, 1),
            "gr_pct": round(gr_avg * 100, 1),
            "ctrl_diversity": wt_override,
        })

        # 판정
        verdict = "PASS"
        issues = []
        if len(rows) == 0:
            issues.append("worktype → hazard 매핑 없음")
            verdict = "FAIL"
        if len(high_conf_wt) < 2:
            issues.append(f"고신뢰 law {len(high_conf_wt)}건 < 2건 기준 미달")
            verdict = "WARN"
        for r in rows:
            if r["high_conf"] == 0:
                issues.append(f"hazard {r['hazard_code']}: high-conf law 0건")
                verdict = "FAIL"
            if r["ctrl_count"] == 0:
                issues.append(f"hazard {r['hazard_code']}: control 없음")
                verdict = "FAIL"
            if not r["has_eng"]:
                issues.append(f"hazard {r['hazard_code']}: 공학적 대책 없음")
                if verdict == "PASS": verdict = "WARN"

        if verdict == "FAIL":
            all_pass = False

        mark = "OK" if verdict == "PASS" else ("WN" if verdict == "WARN" else "NG")
        print(f"\n[{mark} {verdict}] {wt_code}")
        print(f"  worktype law: {len(wt_law_list)}건  고신뢰: {len(high_conf_wt)}건  "
              f"generic: {len(generic_wt)}건")
        print(f"  연결 hazard: {hazards}")

        for r in rows:
            eng_mark = "O" if r["has_eng"] else "X"
            print(f"\n  hazard: {r['hazard_code']}")
            print(f"    control {r['ctrl_count']}건 [공학:{eng_mark}] | "
                  f"law {r['law_count']}건 (고신뢰:{r['high_conf']}, generic:{r['generic_law_ratio']*100:.0f}%)")
            for cn in r["ctrl_names"][:3]:
                print(f"      ctrl: {cn}")
            for lt in r["law_titles"][:3]:
                print(f"      law:  {lt}")
            ctrl_spec = [lid for lid in r["ctrl_law_ids"] if lid not in GENERIC_IDS]
            if ctrl_spec:
                print(f"    control-specific law ID: {ctrl_spec[:3]}")

        if issues:
            for i in issues:
                print(f"  ISSUE: {i}")

    # 지표 테이블
    print("\n" + "=" * 70)
    print("worktype별 지표")
    print(f"{'worktype':<20} {'rows':>5} {'avg_ctrl':>9} {'avg_law':>8} "
          f"{'HC%':>6} {'GEN%':>6} {'ctrl다양':>8}")
    print("-" * 70)
    for m in metrics_table:
        print(f"{m['wt']:<20} {m['rows']:>5} {m['avg_ctrl']:>9.1f} {m['avg_law']:>8.1f} "
              f"{m['hc_ratio']:>6.1f} {m['gr_pct']:>6.1f} {m['ctrl_diversity']:>8}")

    print("\n" + "=" * 70)
    final = "PASS" if all_pass else "WARN"
    print(f"최종 판정: {final}")
    print("=" * 70)
    return 0 if final == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

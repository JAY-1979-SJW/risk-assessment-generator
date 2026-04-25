"""
공종별 위험성평가 추천 엔진 검증 스크립트

검증 항목:
  - 모든 enabled trade_id 추천 payload 생성 가능
  - 소방설비 10개 / 전기 9개 / 기계설비 9개 / 공통 10개
  - FIRE_PIPE_INSTALL + COMMON_HOT_WORK + COMMON_WORK_AT_HEIGHT merge
  - ELEC_CABLE_TRAY: ELECTRIC_SHOCK 또는 FALL_FROM_HEIGHT 포함
  - MECH_PIPE_INSTALL: HOT_WORK_FIRE 또는 HEAVY_LIFTING 포함
  - 모든 required_documents catalog 존재
  - 모든 required_permits catalog 존재
  - 모든 required_trainings training_types 존재 or warning 처리
  - warnings 필드 항상 존재
  - source_trace 항상 존재
  - source_status_summary 항상 존재
  - source_status 허용 enum 안에 있음

출력 형식:
  [validate_trade_risk_recommender]
  - trades_checked:
  - payloads_generated:
  - warnings:
  - errors:
  - result: PASS/WARN/FAIL
"""

from __future__ import annotations

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import yaml

from engine.recommendation.trade_risk_recommender import (
    build_trade_risk_recommendation,
    get_trade_preset,
    load_trade_risk_masters,
    merge_common_high_risk_presets,
)

_ALLOWED_SOURCE_STATUS = {"VERIFIED", "PARTIAL_VERIFIED", "PRACTICAL", "NEEDS_VERIFICATION"}

_WORK_TYPES_DIR = _REPO_ROOT / "data" / "masters" / "safety" / "work_types"
_DETAIL_FILES = [
    ("firefighting_work_types.yml", "소방설비", 10),
    ("electrical_work_types.yml", "전기", 9),
    ("mechanical_work_types.yml", "기계설비", 9),
    ("common_high_risk_work_types.yml", "공통 고위험작업", 10),
]


def _ok(msg: str, detail: str = "") -> tuple:
    return ("PASS", msg, detail)


def _warn(msg: str, detail: str = "") -> tuple:
    return ("WARN", msg, detail)


def _fail(msg: str, detail: str = "") -> tuple:
    return ("FAIL", msg, detail)


def run_validation() -> None:
    results: list[tuple] = []
    trades_checked: list[str] = []
    payloads_generated = 0
    warn_msgs: list[str] = []
    error_msgs: list[str] = []

    # 마스터 로드
    masters = load_trade_risk_masters()
    if masters["_load_errors"]:
        for e in masters["_load_errors"]:
            results.append(_fail("마스터 로드 오류", e))
            error_msgs.append(e)
    else:
        results.append(_ok("마스터 데이터 로드 성공"))

    valid_doc_ids = masters["valid_doc_ids"]
    valid_training_codes = masters["valid_training_codes"]

    # ── 그룹별 공종 수 및 전체 payload 생성 ──────────────────────────
    for fname, group_name, min_count in _DETAIL_FILES:
        fpath = _WORK_TYPES_DIR / fname
        if not fpath.exists():
            results.append(_fail(f"{fname} 없음"))
            continue
        with open(fpath, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        trades = [t for t in data.get("trades", []) if t.get("enabled", True)]
        group_count = len(trades)

        if group_count >= min_count:
            results.append(_ok(f"{group_name} 공종 수 충족", f"{group_count} ≥ {min_count}"))
        else:
            results.append(_fail(f"{group_name} 공종 수 부족", f"{group_count} < {min_count}"))

        for trade in trades:
            tid = trade["trade_id"]
            trades_checked.append(tid)
            try:
                p = build_trade_risk_recommendation(tid)
                payloads_generated += 1

                # warnings 필드 존재
                if "warnings" not in p:
                    results.append(_fail(f"{tid}: warnings 필드 없음"))
                # source_trace 존재
                if not p.get("source_trace"):
                    results.append(_fail(f"{tid}: source_trace 없음"))
                # source_status_summary 존재
                if "source_status_summary" not in p:
                    results.append(_fail(f"{tid}: source_status_summary 없음"))
                # source_status enum 검증
                for ri in p.get("risk_items", []):
                    ss = ri.get("source_status", "")
                    if ss not in _ALLOWED_SOURCE_STATUS:
                        results.append(_fail(
                            f"{tid}: 허용되지 않는 source_status",
                            f"hazard={ri.get('hazard_id')}, status={ss}"
                        ))
                # required_documents catalog 검증
                for did in p.get("required_documents", []):
                    if valid_doc_ids and did not in valid_doc_ids:
                        results.append(_fail(
                            f"{tid}: required_documents catalog 불일치", did
                        ))
                # required_permits catalog 검증
                for pid in p.get("required_permits", []):
                    if valid_doc_ids and pid not in valid_doc_ids:
                        results.append(_fail(
                            f"{tid}: required_permits catalog 불일치", pid
                        ))
                # required_trainings 검증 (없으면 warning)
                for tcode in p.get("required_trainings", []):
                    if valid_training_codes and tcode not in valid_training_codes:
                        w = f"{tid}: required_trainings 미등록 코드 '{tcode}'"
                        results.append(_warn(w))
                        warn_msgs.append(w)

            except Exception as e:
                msg = f"{tid} 추천 생성 실패: {e}"
                results.append(_fail(msg))
                error_msgs.append(msg)

    results.append(_ok(
        f"전체 enabled trade payload 생성",
        f"{payloads_generated}/{len(trades_checked)}개"
    ))

    # ── 특정 공종 hazard 포함 여부 검증 ──────────────────────────────
    try:
        p_elec = build_trade_risk_recommendation("ELEC_CABLE_TRAY")
        hazard_ids_elec = {ri["hazard_id"] for ri in p_elec.get("risk_items", [])}
        if "ELECTRIC_SHOCK" in hazard_ids_elec or "FALL_FROM_HEIGHT" in hazard_ids_elec:
            results.append(_ok(
                "ELEC_CABLE_TRAY: ELECTRIC_SHOCK 또는 FALL_FROM_HEIGHT 포함",
                str(hazard_ids_elec)
            ))
        else:
            results.append(_fail(
                "ELEC_CABLE_TRAY: ELECTRIC_SHOCK / FALL_FROM_HEIGHT 모두 없음",
                str(hazard_ids_elec)
            ))
    except Exception as e:
        results.append(_fail(f"ELEC_CABLE_TRAY 검증 실패: {e}"))

    try:
        p_mech = build_trade_risk_recommendation("MECH_PIPE_INSTALL")
        hazard_ids_mech = {ri["hazard_id"] for ri in p_mech.get("risk_items", [])}
        if "HOT_WORK_FIRE" in hazard_ids_mech or "HEAVY_LIFTING" in hazard_ids_mech:
            results.append(_ok(
                "MECH_PIPE_INSTALL: HOT_WORK_FIRE 또는 HEAVY_LIFTING 포함",
                str(hazard_ids_mech)
            ))
        else:
            results.append(_fail(
                "MECH_PIPE_INSTALL: HOT_WORK_FIRE / HEAVY_LIFTING 모두 없음",
                str(hazard_ids_mech)
            ))
    except Exception as e:
        results.append(_fail(f"MECH_PIPE_INSTALL 검증 실패: {e}"))

    # ── merge 검증 ────────────────────────────────────────────────────
    try:
        base_trade = get_trade_preset("FIRE_PIPE_INSTALL")
        merged = merge_common_high_risk_presets(
            base_trade, ["COMMON_HOT_WORK", "COMMON_WORK_AT_HEIGHT"]
        )
        source_trace = merged.get("source_trace", [])
        if (
            "FIRE_PIPE_INSTALL" in source_trace
            and "COMMON_HOT_WORK" in source_trace
            and "COMMON_WORK_AT_HEIGHT" in source_trace
        ):
            results.append(_ok(
                "FIRE_PIPE_INSTALL + COMMON_HOT_WORK + COMMON_WORK_AT_HEIGHT merge 성공",
                f"hazards={len(merged['risk_items'])}개, source_trace={source_trace}"
            ))
        else:
            results.append(_fail("merge source_trace 누락", str(source_trace)))

        # merge 중복 제거 검증
        hazard_ids_merged = [ri["hazard_id"] for ri in merged["risk_items"]]
        if len(hazard_ids_merged) == len(set(hazard_ids_merged)):
            results.append(_ok("merge 중복 hazard 없음"))
        else:
            from collections import Counter
            dupes = [h for h, cnt in Counter(hazard_ids_merged).items() if cnt > 1]
            results.append(_fail("merge 중복 hazard 존재", str(dupes)))

        doc_list = merged.get("required_documents", [])
        if len(doc_list) == len(set(doc_list)):
            results.append(_ok("merge required_documents 중복 없음"))
        else:
            results.append(_fail("merge required_documents 중복 존재"))

    except Exception as e:
        msg = f"FIRE_PIPE_INSTALL merge 검증 실패: {e}"
        results.append(_fail(msg))
        error_msgs.append(msg)

    # ── 출력 ─────────────────────────────────────────────────────────
    pass_cnt = sum(1 for r in results if r[0] == "PASS")
    warn_cnt = sum(1 for r in results if r[0] == "WARN")
    fail_cnt = sum(1 for r in results if r[0] == "FAIL")
    overall = "FAIL" if fail_cnt > 0 else ("WARN" if warn_cnt > 0 else "PASS")

    print("\n" + "=" * 68)
    print("  [validate_trade_risk_recommender]")
    print("=" * 68)
    for verdict, name, detail in results:
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}[verdict]
        line = f"  {icon} [{verdict}] {name}"
        if detail:
            line += f" — {detail}"
        print(line)
    print("-" * 68)
    print(f"  trades_checked: {len(trades_checked)}")
    print(f"  payloads_generated: {payloads_generated}")
    print(f"  warnings: {warn_cnt}")
    print(f"  errors: {fail_cnt}")
    print(f"  result: PASS {pass_cnt}  WARN {warn_cnt}  FAIL {fail_cnt}")
    print(f"\n  최종 판정: {overall}")
    print("=" * 68 + "\n")

    sys.exit(0 if overall != "FAIL" else 1)


if __name__ == "__main__":
    run_validation()

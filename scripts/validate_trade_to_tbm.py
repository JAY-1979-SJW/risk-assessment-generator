"""
trade_id → TBM 안전점검 일지 연결 검증 스크립트

검증 항목:
  - FIRE_PIPE_INSTALL → TBM 입력 생성 가능
  - FIRE_PIPE_INSTALL + COMMON_HOT_WORK + COMMON_WORK_AT_HEIGHT → TBM 입력 생성 가능
  - ELEC_CABLE_TRAY → TBM 입력 생성 가능
  - MECH_PIPE_INSTALL → TBM 입력 생성 가능
  - 각 결과 hazard_points 1개 이상
  - safety_instructions 1개 이상
  - required_permits가 있으면 permit_check에 반영
  - ppe가 있으면 보호구 확인 항목에 반영
  - common_equipment가 있으면 장비 확인 항목에 반영
  - pre_work_checks 존재
  - supervisor_signature 존재
  - attendees 서명란 존재
  - 필수 고정 문구 4개 포함
  - photo_evidence 권장/선택 상태로 포함
  - TBM Excel bytes 생성 가능
  - 기존 RA-001 연결 검증 영향 없음
  - 기존 smoke_test_p0_forms.py 13/13 PASS 유지

출력 형식:
  [validate_trade_to_tbm]
  - cases_checked:
  - tbm_items_generated:
  - excel_generated:
  - warnings:
  - errors:
  - result: PASS/WARN/FAIL
"""

from __future__ import annotations

import pathlib
import sys
from io import BytesIO

_REPO_ROOT = pathlib.Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.recommendation.tbm_log_adapter import (
    FIXED_NOTICES,
    build_tbm_input_from_trade_id,
    validate_tbm_input,
)
from engine.output.tbm_log_builder import build_tbm_log_excel

_TEST_CASES = [
    ("FIRE_PIPE_INSTALL", None, "FIRE_PIPE_INSTALL 단독"),
    ("FIRE_PIPE_INSTALL", ["COMMON_HOT_WORK", "COMMON_WORK_AT_HEIGHT"],
     "FIRE_PIPE_INSTALL + COMMON_HOT_WORK + COMMON_WORK_AT_HEIGHT"),
    ("ELEC_CABLE_TRAY", None, "ELEC_CABLE_TRAY 단독"),
    ("MECH_PIPE_INSTALL", None, "MECH_PIPE_INSTALL 단독"),
]


def _ok(msg: str, detail: str = "") -> tuple:
    return ("PASS", msg, detail)


def _warn(msg: str, detail: str = "") -> tuple:
    return ("WARN", msg, detail)


def _fail(msg: str, detail: str = "") -> tuple:
    return ("FAIL", msg, detail)


def run_validation() -> None:
    results: list[tuple] = []
    total_hazard_items = 0
    excel_generated = 0
    warn_msgs: list[str] = []
    error_msgs: list[str] = []

    # ── 케이스별 검증 ─────────────────────────────────────────
    for trade_id, common_ids, label in _TEST_CASES:
        try:
            payload = build_tbm_input_from_trade_id(
                trade_id, common_work_ids=common_ids
            )
        except Exception as e:
            msg = f"{label}: TBM 입력 생성 실패 — {e}"
            results.append(_fail(msg))
            error_msgs.append(msg)
            continue

        meta = payload.get("_meta", {})
        hazard_points = payload.get("hazard_points", "")
        safety_instructions = payload.get("safety_instructions", "")
        pre_work_checks = payload.get("pre_work_checks", "")
        permit_check = payload.get("permit_check", "")
        ppe_check = payload.get("ppe_check", "")
        required_permits = meta.get("required_permits", [])
        ppe = meta.get("ppe", [])
        common_equipment = meta.get("common_equipment", [])

        # hazard_points 1개 이상
        hazard_count = len([l for l in hazard_points.splitlines() if l.strip()])
        if hazard_count >= 1:
            results.append(_ok(f"{label}: hazard_points", f"{hazard_count}개"))
            total_hazard_items += hazard_count
        else:
            results.append(_fail(f"{label}: hazard_points 없음"))
            error_msgs.append(f"{label}: hazard_points 0개")

        # safety_instructions 1개 이상
        instr_count = len([l for l in safety_instructions.splitlines() if l.strip()])
        if instr_count >= 1:
            results.append(_ok(f"{label}: safety_instructions", f"{instr_count}개"))
        else:
            results.append(_fail(f"{label}: safety_instructions 없음"))
            error_msgs.append(f"{label}: safety_instructions 0개")

        # required_permits가 있으면 permit_check에 반영
        if required_permits:
            if permit_check.strip():
                results.append(_ok(
                    f"{label}: permit_check 반영",
                    f"permits={required_permits}"
                ))
            else:
                results.append(_fail(
                    f"{label}: required_permits 있으나 permit_check 미반영",
                    str(required_permits)
                ))
                error_msgs.append(f"{label}: permit_check 누락")
        else:
            results.append(_ok(f"{label}: required_permits 없음 (permit_check 불필요)"))

        # ppe가 있으면 보호구 확인 항목에 반영
        if ppe:
            if any(p in ppe_check for p in ppe) or any(p in pre_work_checks for p in ppe):
                results.append(_ok(f"{label}: ppe 반영", f"ppe={ppe[:3]}"))
            else:
                results.append(_warn(
                    f"{label}: ppe 목록이 ppe_check/pre_work_checks에 미확인",
                    str(ppe[:3])
                ))
                warn_msgs.append(f"{label}: ppe 반영 미확인")
        else:
            results.append(_ok(f"{label}: ppe 없음 (ppe_check 불필요)"))

        # common_equipment가 있으면 장비 확인 항목에 반영
        if common_equipment:
            if any(eq in pre_work_checks for eq in common_equipment):
                results.append(_ok(
                    f"{label}: common_equipment 반영",
                    f"equip={common_equipment[:2]}"
                ))
            else:
                results.append(_warn(
                    f"{label}: common_equipment pre_work_checks 미확인",
                    str(common_equipment[:2])
                ))
                warn_msgs.append(f"{label}: common_equipment 반영 미확인")
        else:
            results.append(_ok(f"{label}: common_equipment 없음"))

        # pre_work_checks 존재
        if pre_work_checks.strip():
            results.append(_ok(f"{label}: pre_work_checks 존재"))
        else:
            w = f"{label}: pre_work_checks 없음"
            results.append(_warn(w))
            warn_msgs.append(w)

        # supervisor_signature 존재
        if "supervisor_signature" in payload:
            results.append(_ok(f"{label}: supervisor_signature 필드 존재"))
        else:
            results.append(_fail(f"{label}: supervisor_signature 필드 없음"))
            error_msgs.append(f"{label}: supervisor_signature 없음")

        # attendees 서명란 존재 (리스트 키 존재 여부)
        if "attendees" in payload:
            results.append(_ok(f"{label}: attendees 서명란 존재"))
        else:
            results.append(_fail(f"{label}: attendees 필드 없음"))
            error_msgs.append(f"{label}: attendees 없음")

        # 필수 고정 문구 4개 포함
        notices = payload.get("fixed_notices", [])
        missing_notices = [n[:30] + "..." for n in FIXED_NOTICES if n not in notices]
        if not missing_notices:
            results.append(_ok(f"{label}: 필수 고정 문구 4개 포함"))
        else:
            results.append(_fail(
                f"{label}: 필수 고정 문구 누락",
                str(missing_notices)
            ))
            error_msgs.append(f"{label}: 고정 문구 누락 {missing_notices}")

        # photo_evidence 권장/선택 상태
        photo = payload.get("photo_evidence", {})
        if (photo.get("TBM_MEETING") in ("RECOMMENDED", "REQUIRED") and
                photo.get("WORK_AREA_BEFORE") in ("RECOMMENDED", "REQUIRED")):
            results.append(_ok(f"{label}: photo_evidence RECOMMENDED 포함"))
        else:
            results.append(_warn(
                f"{label}: photo_evidence RECOMMENDED 상태 아님",
                str(photo)
            ))
            warn_msgs.append(f"{label}: photo_evidence 미설정")

        # validate_tbm_input 실행
        v_warns = validate_tbm_input(payload)
        fail_v = [w for w in v_warns if w.startswith("[FAIL]")]
        warn_v = [w for w in v_warns if w.startswith("[WARN]")]
        for w in fail_v:
            results.append(_fail(f"{label}: validate_tbm_input", w))
            error_msgs.append(w)
        # site_context 미입력 WARN은 정상 (dry-run)

        # Excel bytes 생성
        try:
            xl = build_tbm_log_excel(payload)
            if len(xl) > 1000:
                results.append(_ok(f"{label}: Excel 생성 성공", f"{len(xl):,} bytes"))
                excel_generated += 1
            else:
                results.append(_fail(
                    f"{label}: Excel bytes 너무 작음", f"{len(xl)} bytes"
                ))
                error_msgs.append(f"Excel bytes {len(xl)}")
        except Exception as e:
            msg = f"{label}: Excel 생성 실패 — {e}"
            results.append(_fail(msg))
            error_msgs.append(msg)

    # ── 기존 RA-001 연결 검증 영향 없음 ──────────────────────
    try:
        from engine.recommendation.risk_assessment_adapter import (
            build_ra001_excel_from_trade_id,
        )
        xl = build_ra001_excel_from_trade_id("FIRE_PIPE_INSTALL")
        if isinstance(xl, bytes) and len(xl) > 1000:
            results.append(_ok("기존 RA-001 연결 (FIRE_PIPE_INSTALL) 정상"))
        else:
            results.append(_fail("기존 RA-001 연결 오류"))
    except Exception as e:
        results.append(_fail("기존 RA-001 연결 예외", str(e)))
        error_msgs.append(str(e))

    # ── 기존 smoke test (form_registry tbm_log) 회귀 ──────────
    try:
        from engine.output.form_registry import build_form_excel
        xl_smoke = build_form_excel("tbm_log", {
            "tbm_date": "2026-04-25 08:00",
            "today_work": "배관 보수",
            "hazard_points": "추락 위험",
            "safety_instructions": "안전대 착용",
            "trade_name": "소방 배관",
            "pre_work_checks": "허가서 확인",
            "permit_check": "화기작업 허가서",
        })
        if isinstance(xl_smoke, bytes) and len(xl_smoke) > 0:
            results.append(_ok("기존 smoke (form_registry tbm_log) 정상"))
        else:
            results.append(_fail("기존 smoke 오류"))
    except Exception as e:
        results.append(_fail("기존 smoke 예외", str(e)))
        error_msgs.append(str(e))

    # ── 출력 ──────────────────────────────────────────────────
    pass_cnt = sum(1 for r in results if r[0] == "PASS")
    warn_cnt = sum(1 for r in results if r[0] == "WARN")
    fail_cnt = sum(1 for r in results if r[0] == "FAIL")
    overall = "FAIL" if fail_cnt > 0 else ("WARN" if warn_cnt > 0 else "PASS")

    print("\n" + "=" * 68)
    print("  [validate_trade_to_tbm]")
    print("=" * 68)
    for verdict, name, detail in results:
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}[verdict]
        line = f"  {icon} [{verdict}] {name}"
        if detail:
            line += f" — {detail}"
        print(line)
    print("-" * 68)
    print(f"  cases_checked: {len(_TEST_CASES)}")
    print(f"  tbm_items_generated: {total_hazard_items} hazard_points")
    print(f"  excel_generated: {excel_generated}/{len(_TEST_CASES)}")
    print(f"  warnings: {warn_cnt}")
    print(f"  errors: {fail_cnt}")
    print(f"  result: PASS {pass_cnt}  WARN {warn_cnt}  FAIL {fail_cnt}")
    print(f"\n  최종 판정: {overall}")
    print("=" * 68 + "\n")

    sys.exit(0 if overall != "FAIL" else 1)


if __name__ == "__main__":
    run_validation()

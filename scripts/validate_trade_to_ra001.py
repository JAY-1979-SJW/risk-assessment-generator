"""
trade_id → RA-001 위험성평가표 연결 검증 스크립트

검증 항목:
  - FIRE_PIPE_INSTALL → RA-001 입력 생성 가능
  - FIRE_PIPE_INSTALL + COMMON_HOT_WORK + COMMON_WORK_AT_HEIGHT → RA-001 입력 생성 가능
  - ELEC_CABLE_TRAY → RA-001 입력 생성 가능
  - MECH_PIPE_INSTALL → RA-001 입력 생성 가능
  - 각 결과 risk_rows 1개 이상
  - 위험요인명/위험상황/감소대책 누락 없음
  - required_documents catalog 존재
  - required_trainings training_types 존재
  - required_permits catalog 존재
  - Excel bytes 생성 가능 (> 1000 bytes)
  - 필수 고정 문구 3개 포함
  - 기존 RA-001 smoke test(P0) 영향 없음

출력 형식:
  [validate_trade_to_ra001]
  - cases_checked:
  - risk_rows_generated:
  - excel_generated:
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

from engine.recommendation.risk_assessment_adapter import (
    _DISCLAIMERS,
    build_ra001_excel_from_trade_id,
    build_ra001_input_from_trade_id,
    validate_ra001_input,
)
from engine.recommendation.trade_risk_recommender import load_trade_risk_masters

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
    total_rows = 0
    excel_generated = 0
    warn_msgs: list[str] = []
    error_msgs: list[str] = []

    masters = load_trade_risk_masters()
    valid_doc_ids = masters["valid_doc_ids"]
    valid_training_codes = masters["valid_training_codes"]

    if masters["_load_errors"]:
        for e in masters["_load_errors"]:
            results.append(_fail("마스터 로드 오류", e))
            error_msgs.append(e)
    else:
        results.append(_ok("마스터 데이터 로드 성공"))

    # ── 케이스별 검증 ────────────────────────────────────────
    for trade_id, common_ids, label in _TEST_CASES:
        try:
            payload = build_ra001_input_from_trade_id(trade_id, common_work_ids=common_ids)
        except Exception as e:
            msg = f"{label}: RA-001 입력 생성 실패 — {e}"
            results.append(_fail(msg))
            error_msgs.append(msg)
            continue

        rows = payload.get("rows", [])
        meta = payload.get("_meta", {})

        # rows 1개 이상
        if rows:
            results.append(_ok(f"{label}: rows 생성", f"{len(rows)}행"))
            total_rows += len(rows)
        else:
            results.append(_fail(f"{label}: rows 0행"))
            error_msgs.append(f"{label}: rows 0행")
            continue

        # 위험요인명/위험상황/감소대책 누락
        row_issues = []
        for i, row in enumerate(rows, start=1):
            if not row.get("hazard_category_minor"):
                row_issues.append(f"행{i}: 위험요인명 누락")
            if not row.get("hazard"):
                row_issues.append(f"행{i}: 위험상황 누락")
            if not row.get("control_measures"):
                row_issues.append(f"행{i}: 감소대책 누락")
        if row_issues:
            for issue in row_issues:
                results.append(_fail(f"{label}: {issue}"))
                error_msgs.append(issue)
        else:
            results.append(_ok(f"{label}: 모든 행 필수 필드 존재"))

        # required_documents catalog 검증
        doc_issues = [d for d in meta.get("required_documents", []) if valid_doc_ids and d not in valid_doc_ids]
        if doc_issues:
            results.append(_fail(f"{label}: required_documents catalog 불일치", str(doc_issues)))
            error_msgs.extend(doc_issues)
        else:
            results.append(_ok(f"{label}: required_documents catalog 일치"))

        # required_permits catalog 검증
        permit_issues = [p for p in meta.get("required_permits", []) if valid_doc_ids and p not in valid_doc_ids]
        if permit_issues:
            results.append(_fail(f"{label}: required_permits catalog 불일치", str(permit_issues)))
            error_msgs.extend(permit_issues)
        else:
            results.append(_ok(f"{label}: required_permits catalog 일치"))

        # required_trainings 검증
        train_issues = [t for t in meta.get("required_trainings", []) if valid_training_codes and t not in valid_training_codes]
        if train_issues:
            w = f"{label}: required_trainings 미등록 코드 {train_issues}"
            results.append(_warn(w))
            warn_msgs.append(w)
        else:
            results.append(_ok(f"{label}: required_trainings 코드 일치"))

        # disclaimers 3개 포함
        disc_in_meta = meta.get("disclaimers", [])
        missing_disc = [d[:30] for d in _DISCLAIMERS if d not in disc_in_meta]
        if missing_disc:
            results.append(_fail(f"{label}: 필수 고정 문구 누락", str(missing_disc)))
            error_msgs.append(f"disclaimers 누락: {missing_disc}")
        else:
            results.append(_ok(f"{label}: 필수 고정 문구 3개 포함"))

        # validate_ra001_input 경고 수집
        input_warnings = validate_ra001_input(payload)
        site_warns = [w for w in input_warnings if "[SITE_INFO]" in w]
        other_warns = [w for w in input_warnings if "[SITE_INFO]" not in w]
        if other_warns:
            for w in other_warns:
                results.append(_warn(f"{label}: {w}"))
                warn_msgs.append(w)

        # Excel bytes 생성
        try:
            xl = build_ra001_excel_from_trade_id(trade_id, common_work_ids=common_ids)
            if len(xl) > 1000:
                results.append(_ok(f"{label}: Excel 생성 성공", f"{len(xl):,} bytes"))
                excel_generated += 1
            else:
                results.append(_fail(f"{label}: Excel bytes 너무 작음", f"{len(xl)} bytes"))
                error_msgs.append(f"Excel bytes {len(xl)}")
        except Exception as e:
            msg = f"{label}: Excel 생성 실패 — {e}"
            results.append(_fail(msg))
            error_msgs.append(msg)

    # ── 기존 smoke test 영향 확인 ────────────────────────────
    try:
        from engine.output.form_registry import build_form_excel
        xl_smoke = build_form_excel("risk_assessment", {
            "company_name": "테스트건설(주)",
            "assessment_type": "최초평가",
            "assessment_date": "2026-04-25",
            "rows": [{"hazard_category": "추락", "risk_level": "중"}],
        })
        if isinstance(xl_smoke, bytes) and len(xl_smoke) > 0:
            results.append(_ok("기존 RA-001 smoke (form_registry) 정상"))
        else:
            results.append(_fail("기존 RA-001 smoke 오류"))
    except Exception as e:
        results.append(_fail("기존 RA-001 smoke 예외", str(e)))
        error_msgs.append(str(e))

    # ── 출력 ─────────────────────────────────────────────────
    pass_cnt = sum(1 for r in results if r[0] == "PASS")
    warn_cnt = sum(1 for r in results if r[0] == "WARN")
    fail_cnt = sum(1 for r in results if r[0] == "FAIL")
    overall = "FAIL" if fail_cnt > 0 else ("WARN" if warn_cnt > 0 else "PASS")

    print("\n" + "=" * 68)
    print("  [validate_trade_to_ra001]")
    print("=" * 68)
    for verdict, name, detail in results:
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}[verdict]
        line = f"  {icon} [{verdict}] {name}"
        if detail:
            line += f" — {detail}"
        print(line)
    print("-" * 68)
    print(f"  cases_checked: {len(_TEST_CASES)}")
    print(f"  risk_rows_generated: {total_rows}")
    print(f"  excel_generated: {excel_generated}/{len(_TEST_CASES)}")
    print(f"  warnings: {warn_cnt}")
    print(f"  errors: {fail_cnt}")
    print(f"  result: PASS {pass_cnt}  WARN {warn_cnt}  FAIL {fail_cnt}")
    print(f"\n  최종 판정: {overall}")
    print("=" * 68 + "\n")

    sys.exit(0 if overall != "FAIL" else 1)


if __name__ == "__main__":
    run_validation()

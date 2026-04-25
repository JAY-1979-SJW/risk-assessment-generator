"""
trade_id → TBM 안전점검 일지 dry-run CLI

사용법:
    python scripts/dry_run_trade_to_tbm.py --trade-id FIRE_PIPE_INSTALL
    python scripts/dry_run_trade_to_tbm.py \
        --trade-id FIRE_PIPE_INSTALL \
        --common-work COMMON_HOT_WORK --common-work COMMON_WORK_AT_HEIGHT \
        --site-name "테스트 현장" --work-location "지하1층"
    python scripts/dry_run_trade_to_tbm.py \
        --trade-id ELEC_CABLE_TRAY \
        --output-json /tmp/tbm_elec.json \
        --output-xlsx /tmp/tbm_elec.xlsx
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.recommendation.tbm_log_adapter import (
    build_tbm_input_from_trade_id,
    validate_tbm_input,
)
from engine.output.tbm_log_builder import build_tbm_log_excel


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="trade_id → TBM 안전점검 일지 (dry-run)"
    )
    p.add_argument("--trade-id", required=True, help="공종 ID (예: FIRE_PIPE_INSTALL)")
    p.add_argument("--common-work", action="append", default=[],
                   dest="common_work", metavar="COMMON_ID",
                   help="공통 고위험작업 ID (여러 개 허용, 예: COMMON_HOT_WORK)")
    p.add_argument("--site-name", default=None, dest="site_name", help="사업장명")
    p.add_argument("--work-location", default=None, dest="work_location", help="작업 장소")
    p.add_argument("--work-date", default=None, dest="work_date", help="작업 일자 (YYYY-MM-DD)")
    p.add_argument("--workers-count", default=None, type=int, dest="workers_count", help="작업 인원")
    p.add_argument("--work-description", default=None, dest="work_description",
                   help="오늘의 작업 내용 (미입력 시 공종명 기반 자동 생성)")
    p.add_argument("--output-json", default=None, dest="output_json",
                   metavar="PATH", help="TBM 입력 payload JSON 저장 경로")
    p.add_argument("--output-xlsx", default=None, dest="output_xlsx",
                   metavar="PATH", help="TBM Excel 저장 경로")
    return p.parse_args()


def _print_section(title: str, content: str, indent: int = 4) -> None:
    pad = " " * indent
    print(f"\n  ── {title} ──")
    for line in (content or "(없음)").splitlines():
        print(f"{pad}{line}")


def main() -> None:
    args = _parse_args()

    site_context: dict | None = None
    ctx_parts = {
        "site_name": args.site_name,
        "work_location": args.work_location,
        "work_date": args.work_date,
        "workers_count": args.workers_count,
        "work_description": args.work_description,
    }
    non_none = {k: v for k, v in ctx_parts.items() if v is not None}
    if non_none:
        site_context = non_none

    print(f"\n{'='*64}")
    print(f"  TBM dry-run: {args.trade_id}")
    if args.common_work:
        print(f"  + common works: {args.common_work}")
    print(f"{'='*64}")

    # ── TBM 입력 생성 ─────────────────────────────────────────
    try:
        payload = build_tbm_input_from_trade_id(
            args.trade_id,
            common_work_ids=args.common_work or None,
            site_context=site_context,
        )
    except ValueError as e:
        print(f"\n  ❌ [FAIL] TBM 입력 생성 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ❌ [FAIL] 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    meta = payload.get("_meta", {})

    # ── 결과 출력 ─────────────────────────────────────────────
    print(f"\n  trade_id  : {meta.get('trade_id')}")
    print(f"  trade_name: {meta.get('trade_name')}")
    print(f"  trade_group: {meta.get('trade_group')}")
    print(f"  risk_items: {meta.get('risk_items_count')}개")
    print(f"  source_trace: {meta.get('source_trace')}")

    _print_section("오늘의 작업 내용", payload.get("today_work", ""))
    _print_section("위험요인", payload.get("hazard_points", ""))
    _print_section("안전수칙", payload.get("safety_instructions", ""))
    _print_section("작업 전 확인사항", payload.get("pre_work_checks", ""))
    _print_section("작업허가서 확인", payload.get("permit_check", ""))
    _print_section("보호구 확인", payload.get("ppe_check", ""))
    _print_section("교육 확인사항", payload.get("training_notes", ""))

    photo = payload.get("photo_evidence", {})
    print(f"\n  ── 사진 증빙 정책 ──")
    for k, v in photo.items():
        print(f"    {k}: {v}")

    print(f"\n  ── 고정 문구 ({len(payload.get('fixed_notices', []))}개) ──")
    for i, notice in enumerate(payload.get("fixed_notices", []), start=1):
        print(f"    [{i}] {notice[:80]}")

    # ── 검증 ──────────────────────────────────────────────────
    validation_warnings = validate_tbm_input(payload)
    fail_warns = [w for w in validation_warnings if w.startswith("[FAIL]")]
    warn_warns = [w for w in validation_warnings if w.startswith("[WARN]")]
    other_warns = [w for w in validation_warnings
                   if not w.startswith("[FAIL]") and not w.startswith("[WARN]")]

    print(f"\n  ── 검증 결과 ──")
    if not validation_warnings:
        print("    ✅ 검증 경고 없음")
    else:
        for w in fail_warns:
            print(f"    ❌ {w}")
        for w in warn_warns:
            print(f"    ⚠️  {w}")
        for w in other_warns:
            print(f"    ℹ️  {w}")

    if meta.get("warnings"):
        print(f"\n  ── 추천 엔진 경고 ({len(meta['warnings'])}건) ──")
        for w in meta["warnings"][:5]:
            print(f"    ⚠️  {w}")
        if len(meta["warnings"]) > 5:
            print(f"    ... 외 {len(meta['warnings']) - 5}건")

    # ── JSON 저장 ──────────────────────────────────────────────
    if args.output_json:
        out_path = pathlib.Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # _meta 포함, 직렬화 가능한 형태로 저장
        serializable = {k: v for k, v in payload.items()}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)
        print(f"\n  📄 JSON 저장: {out_path}")

    # ── Excel 생성 ─────────────────────────────────────────────
    if args.output_xlsx:
        out_path = pathlib.Path(args.output_xlsx)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            xlsx_bytes = build_tbm_log_excel(payload)
            with open(out_path, "wb") as f:
                f.write(xlsx_bytes)
            print(f"  📊 Excel 저장: {out_path} ({len(xlsx_bytes):,} bytes)")
        except Exception as e:
            print(f"\n  ❌ [FAIL] Excel 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # ── 판정 ──────────────────────────────────────────────────
    if fail_warns:
        verdict = "FAIL"
    elif warn_warns or other_warns:
        verdict = "WARN"
    else:
        verdict = "PASS"

    print(f"\n{'─'*64}")
    icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}[verdict]
    print(f"  {icon} 최종 판정: {verdict}")
    print(f"{'='*64}\n")

    sys.exit(0 if verdict != "FAIL" else 1)


if __name__ == "__main__":
    main()

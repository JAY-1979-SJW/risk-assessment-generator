"""
trade_id → RA-001 위험성평가표 Excel 생성 CLI dry-run

사용 예:
  python scripts/dry_run_trade_to_ra001.py --trade-id FIRE_PIPE_INSTALL
  python scripts/dry_run_trade_to_ra001.py \\
      --trade-id FIRE_PIPE_INSTALL \\
      --common-work COMMON_HOT_WORK --common-work COMMON_WORK_AT_HEIGHT \\
      --site-name "테스트 현장" --work-location "지하1층"
  python scripts/dry_run_trade_to_ra001.py \\
      --trade-id ELEC_CABLE_TRAY \\
      --output-json /tmp/ra001_elec.json \\
      --output-xlsx /tmp/ra001_elec.xlsx
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.recommendation.risk_assessment_adapter import (
    build_ra001_excel_from_trade_id,
    build_ra001_input_from_trade_id,
    validate_ra001_input,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="trade_id → RA-001 위험성평가표 Excel 생성 dry-run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--trade-id", required=True, metavar="TRADE_ID")
    parser.add_argument(
        "--common-work", action="append", default=[], dest="common_works", metavar="COMMON_ID"
    )
    parser.add_argument("--site-name", default=None)
    parser.add_argument("--work-location", default=None)
    parser.add_argument("--work-date", default=None)
    parser.add_argument("--workers-count", default=None, type=int)
    parser.add_argument("--output-json", default=None, metavar="FILE")
    parser.add_argument("--output-xlsx", default=None, metavar="FILE")
    return parser.parse_args()


def _json_serializable(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Not serializable: {type(obj)}")


def _print_summary(payload: dict, warnings: list[str]) -> None:
    meta = payload.get("_meta", {})
    print(f"\n{'='*62}")
    print(f"  [RA-001 생성 요약]")
    print(f"  공종: {meta.get('trade_id')} ({meta.get('trade_name')})")
    print(f"  출처: {' + '.join(meta.get('source_trace', []))}")
    print(f"  위험요인 행 수: {meta.get('risk_items_count', 0)}행")
    print(f"  필수서류: {meta.get('required_documents', [])}")
    print(f"  필수허가서: {meta.get('required_permits', [])}")
    print(f"  필수교육: {meta.get('required_trainings', [])}")
    print(f"  source_status: {meta.get('source_status_summary', {})}")
    if warnings:
        print(f"  경고 ({len(warnings)}개):")
        for w in warnings:
            print(f"    ⚠  {w}")
    else:
        print("  경고: 없음")
    print(f"{'='*62}\n")


def main() -> None:
    args = _parse_args()

    site_context: dict | None = None
    if any([args.site_name, args.work_location, args.work_date, args.workers_count]):
        site_context = {
            "site_name": args.site_name,
            "work_location": args.work_location,
            "work_date": args.work_date,
            "workers_count": args.workers_count,
            "equipment_used": [],
        }

    # RA-001 입력 생성
    try:
        payload = build_ra001_input_from_trade_id(
            args.trade_id,
            common_work_ids=args.common_works or None,
            site_context=site_context,
        )
    except ValueError as e:
        print(f"[오류] {e}", file=sys.stderr)
        sys.exit(1)

    warnings = validate_ra001_input(payload)
    _print_summary(payload, warnings)

    # JSON 저장
    if args.output_json:
        out_path = pathlib.Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # _meta._meta fields만 직렬화 (rows 포함)
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=_json_serializable),
            encoding="utf-8",
        )
        print(f"[JSON 저장] {out_path}")

    # Excel 생성
    try:
        xl_bytes = build_ra001_excel_from_trade_id(
            args.trade_id,
            common_work_ids=args.common_works or None,
            site_context=site_context,
        )
        print(f"[Excel 생성] {len(xl_bytes):,} bytes")

        if args.output_xlsx:
            out_xlsx = pathlib.Path(args.output_xlsx)
            out_xlsx.parent.mkdir(parents=True, exist_ok=True)
            out_xlsx.write_bytes(xl_bytes)
            print(f"[Excel 저장] {out_xlsx}")
        else:
            print("  (--output-xlsx 미지정: 파일 저장 생략)")

    except Exception as e:
        print(f"[FAIL] Excel 생성 실패: {e}", file=sys.stderr)
        sys.exit(1)

    if any("FAIL" in w for w in warnings):
        sys.exit(1)


if __name__ == "__main__":
    main()

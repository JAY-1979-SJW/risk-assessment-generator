"""
공종별 위험성평가 추천 엔진 CLI dry-run

사용 예:
  python scripts/dry_run_trade_risk_recommendation.py --trade-id FIRE_PIPE_INSTALL
  python scripts/dry_run_trade_risk_recommendation.py \\
      --trade-id FIRE_PIPE_INSTALL \\
      --common-work COMMON_HOT_WORK --common-work COMMON_WORK_AT_HEIGHT
  python scripts/dry_run_trade_risk_recommendation.py \\
      --trade-id ELEC_CABLE_TRAY --site-name "테스트 현장" --work-location "지하1층"
  python scripts/dry_run_trade_risk_recommendation.py \\
      --trade-id MECH_PIPE_INSTALL --output result.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

# 프로젝트 루트를 sys.path에 추가
_REPO_ROOT = pathlib.Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.recommendation.trade_risk_recommender import (
    build_trade_risk_recommendation,
    get_trade_preset,
    merge_common_high_risk_presets,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="공종별 위험성평가 프리셋 추천 엔진 dry-run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--trade-id",
        required=True,
        metavar="TRADE_ID",
        help="공종 ID (예: FIRE_PIPE_INSTALL, ELEC_CABLE_TRAY)",
    )
    parser.add_argument(
        "--common-work",
        action="append",
        default=[],
        metavar="COMMON_TRADE_ID",
        dest="common_works",
        help="병합할 공통 고위험작업 ID (여러 개 지정 가능)",
    )
    parser.add_argument("--site-name", default=None, metavar="NAME", help="현장명")
    parser.add_argument("--work-location", default=None, metavar="LOC", help="작업 위치")
    parser.add_argument("--work-date", default=None, metavar="DATE", help="작업 일자 (YYYY-MM-DD)")
    parser.add_argument(
        "--workers-count",
        default=None,
        type=int,
        metavar="N",
        help="작업 인원 수",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="결과를 저장할 JSON 파일 경로 (없으면 stdout 출력)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="compact JSON 출력 (들여쓰기 없음)",
    )
    return parser.parse_args()


def _print_summary(payload: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  공종: {payload['trade_id']} ({payload['trade_name']})")
    print(f"  그룹: {payload['trade_group']}")
    print(f"  출처: {' + '.join(payload['source_trace'])}")
    print(f"  위험요인 수: {len(payload['risk_items'])}개")
    print(f"  필수서류: {payload['required_documents']}")
    print(f"  필수허가서: {payload['required_permits']}")
    print(f"  필수교육: {payload['required_trainings']}")
    print(f"  source_status: {payload['source_status_summary']}")
    if payload["warnings"]:
        print(f"  경고 ({len(payload['warnings'])}개):")
        for w in payload["warnings"]:
            print(f"    ⚠️  {w}")
    else:
        print("  경고: 없음")
    ctx = payload["site_context"]
    if any(v for v in ctx.values() if v):
        print(f"  현장정보: {ctx}")
    print(f"{'='*60}\n")


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

    # 기본 추천 생성
    try:
        payload = build_trade_risk_recommendation(args.trade_id, site_context=site_context)
    except ValueError as e:
        print(f"[오류] {e}", file=sys.stderr)
        sys.exit(1)

    # 공통 고위험작업 merge
    if args.common_works:
        trade_preset = get_trade_preset(args.trade_id)
        payload = merge_common_high_risk_presets(trade_preset, args.common_works)
        payload["site_context"] = site_context or payload["site_context"]

    # 요약 출력
    _print_summary(payload)

    # JSON 직렬화
    indent = None if args.compact else 2
    json_str = json.dumps(payload, ensure_ascii=False, indent=indent)

    if args.output:
        out_path = pathlib.Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_str, encoding="utf-8")
        print(f"[저장] {out_path}")
    else:
        print(json_str)


if __name__ == "__main__":
    main()

"""
샘플 위험성평가표 본표 xlsx 생성 스크립트.

입력: docs/sample_form_output_3cases.json  (form_builder 출력 실증값)
출력: samples/risk_form_sample_3cases.xlsx — 3개 케이스를 시트 3개로 병렬 출력

1개 워크북/3개 시트 구조 사용 이유:
- build_form_excel(form_data) -> bytes 계약은 유지.
- 샘플 검증 목적상 3케이스를 한 파일에서 한 번에 열어 비교하기 위함.
- 실제 export API 는 단일 form_data → 단일 시트 bytes 를 반환.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# 프로젝트 루트 import path 등록
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from openpyxl import Workbook

from engine.output.form_excel_builder import render_form_sheet  # noqa: E402


SOURCE = ROOT / "docs" / "sample_form_output_3cases.json"
TARGET = ROOT / "samples" / "risk_form_sample_3cases.xlsx"


_SHEET_NAME_TAGS = {
    "CASE 1": "CASE1_전기작업",
    "CASE 2": "CASE2_밀폐공간",
    "CASE 3": "CASE3_고소작업",
}


def _sheet_name(case_key: str) -> str:
    """
    Excel 시트명 규칙: 31자 이하, 일부 특수문자 금지.
    케이스 키에서 'CASE N' 접두만 보고 한글 태그를 매핑.
    """
    for prefix, tag in _SHEET_NAME_TAGS.items():
        if case_key.startswith(prefix):
            return tag
    # fallback: 특수문자 제거 후 31자 절단
    safe = re.sub(r"[\\/*?:\[\]]", "_", case_key)
    return safe[:31]


def main() -> int:
    if not SOURCE.exists():
        print(f"[ERR] source not found: {SOURCE}", file=sys.stderr)
        return 1

    with SOURCE.open("r", encoding="utf-8") as f:
        cases = json.load(f)

    TARGET.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    # 기본 시트 제거
    default_ws = wb.active
    wb.remove(default_ws)

    for case_key, case in cases.items():
        form_data = case.get("form_output")
        if not isinstance(form_data, dict):
            print(f"[WARN] skip {case_key}: no form_output")
            continue
        ws = wb.create_sheet(title=_sheet_name(case_key))
        render_form_sheet(ws, form_data)
        print(f"[OK] rendered {case_key} -> {ws.title} ({len(form_data.get('rows', []))} rows)")

    wb.save(TARGET)
    print(f"[DONE] wrote {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

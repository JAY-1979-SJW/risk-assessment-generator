"""
위험성평가표 생성 API 계약 빌드 스크립트 (8단계)
입력: engine_design/, law_mapping/ JSON
출력: api_design/ 3종 + docs/devlog/ 문서
용도: 설계 재생성 및 검증용 (운영 구현체 아님)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = ROOT / "data/risk_db/engine_design"
API_DIR = ROOT / "data/risk_db/api_design"
DOCS_DIR = ROOT / "docs/devlog"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_inputs() -> bool:
    required = [
        ENGINE_DIR / "recommendation_engine_schema.json",
        ENGINE_DIR / "recommendation_engine_samples.json",
        ENGINE_DIR / "recommendation_engine_review_notes.json",
    ]
    missing = [p for p in required if not p.exists()]
    if missing:
        print("ERROR: 입력 파일 누락:")
        for p in missing:
            print(f"  {p}")
        return False
    return True


def check_output_files() -> dict:
    outputs = {
        "schema": API_DIR / "risk_assessment_api_schema.json",
        "samples": API_DIR / "risk_assessment_api_samples.json",
        "review_notes": API_DIR / "risk_assessment_api_review_notes.json",
        "doc": DOCS_DIR / "risk_assessment_api_contract_rules.md",
    }
    result = {}
    for key, path in outputs.items():
        result[key] = {"path": str(path), "exists": path.exists()}
    return result


def validate_schema(schema: dict) -> list[str]:
    errors = []
    if "endpoints" not in schema:
        errors.append("schema: endpoints 필드 없음")
    else:
        endpoint_ids = {e["id"] for e in schema["endpoints"]}
        for required_id in ("recommend_draft", "recalculate_draft"):
            if required_id not in endpoint_ids:
                errors.append(f"schema: endpoint {required_id} 없음")
    if "row_id_rules" not in schema:
        errors.append("schema: row_id_rules 없음")
    if "review_flags_enum" not in schema:
        errors.append("schema: review_flags_enum 없음")
    if "responsibility_boundary" not in schema:
        errors.append("schema: responsibility_boundary 없음")
    return errors


def validate_samples(samples: dict) -> list[str]:
    errors = []
    required_wt = {"ELEC_LIVE", "TEMP_SCAFF", "WATER_MANHOLE", "LIFT_RIGGING", "DEMO_ASBESTOS"}
    found_wt = {s["work_type_code"] for s in samples.get("samples", [])}
    missing_wt = required_wt - found_wt
    if missing_wt:
        errors.append(f"samples: worktype 누락 {missing_wt}")
    for s in samples.get("samples", []):
        wt = s.get("work_type_code", "?")
        if "request" not in s:
            errors.append(f"samples[{wt}]: request 없음")
        if "response" not in s:
            errors.append(f"samples[{wt}]: response 없음")
            continue
        resp = s["response"]
        for field in ("request_id", "rows", "review_flags", "engine_meta"):
            if field not in resp:
                errors.append(f"samples[{wt}].response: {field} 없음")
        for row in resp.get("rows", []):
            row_id = row.get("row_id", "?")
            if "_" not in row_id or not row_id.split("_")[-1].isdigit():
                errors.append(f"samples[{wt}].row_id 형식 오류: {row_id}")
            for field in ("hazard", "controls", "laws", "editable"):
                if field not in row:
                    errors.append(f"samples[{wt}][{row_id}]: {field} 없음")
    return errors


def report(label: str, errors: list[str]) -> bool:
    if errors:
        print(f"FAIL [{label}]")
        for e in errors:
            print(f"  - {e}")
        return False
    print(f"PASS [{label}]")
    return True


def main():
    print("=== 8단계 API 계약 검증 ===\n")

    if not validate_inputs():
        sys.exit(1)

    output_status = check_output_files()
    print("출력 파일 상태:")
    all_exist = True
    for key, info in output_status.items():
        status = "OK" if info["exists"] else "MISSING"
        print(f"  [{status}] {info['path']}")
        if not info["exists"]:
            all_exist = False

    if not all_exist:
        print("\nERROR: 출력 파일 일부 누락. 먼저 파일 생성 필요.")
        sys.exit(1)

    print()
    schema = load_json(API_DIR / "risk_assessment_api_schema.json")
    samples = load_json(API_DIR / "risk_assessment_api_samples.json")
    review = load_json(API_DIR / "risk_assessment_api_review_notes.json")

    schema_ok = report("schema", validate_schema(schema))
    samples_ok = report("samples", validate_samples(samples))
    review_ok = report("review_notes", [] if "notes" in review else ["notes 필드 없음"])

    endpoint_count = len(schema.get("endpoints", []))
    sample_count = len(samples.get("samples", []))
    flag_count = len(schema.get("review_flags_enum", {}))
    note_count = len(review.get("notes", []))
    critical_count = sum(1 for n in review.get("notes", []) if n.get("severity") == "CRITICAL")

    print(f"\n--- 결과 요약 ---")
    print(f"엔드포인트 정의: {endpoint_count}개")
    print(f"샘플 worktype: {sample_count}개")
    print(f"review_flags 정의: {flag_count}종")
    print(f"review_notes: {note_count}건 (CRITICAL {critical_count}건)")

    print()
    if schema_ok and samples_ok and review_ok:
        print("최종 판정: PASS")
    else:
        print("최종 판정: FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()

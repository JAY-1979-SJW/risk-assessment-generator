"""
POST /api/v1/risk-assessment/build 계약 검증 스크립트.
Usage: python scripts/test_build_api.py [--base http://127.0.0.1:8199]
"""
import json
import sys
import argparse
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8199"


def post(path: str, body=None) -> tuple[int, dict]:
    url = BASE + path
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else b""
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def check(label, status, body, expected_status, expected_code=None, checks=None):
    ok = status == expected_status
    code_ok = (expected_code is None) or (
        body.get("error", {}).get("code") == expected_code
    )
    extra = []
    if checks:
        for fn, desc in checks:
            result = fn(body)
            if not result:
                extra.append(f"FAIL: {desc}")
    result_str = "PASS" if (ok and code_ok and not extra) else "FAIL"
    print(f"[{result_str}] {label}")
    if not ok:
        print(f"       status: expected={expected_status}, got={status}")
    if not code_ok:
        print(f"       code: expected={expected_code}, got={body.get('error',{}).get('code')}")
    for e in extra:
        print(f"       {e}")
    return result_str == "PASS"


def run():
    results = []
    EP = "/api/v1/risk-assessment/build"

    print("\n=== 에러 응답 검증 ===")
    # 1. body 없음
    s, b = post(EP, None)
    results.append(check("body 없음 → 400 MISSING_WORK_TYPE", s, b, 400, "MISSING_WORK_TYPE"))

    # 2. work_type 누락 ({})
    s, b = post(EP, {})
    results.append(check("work_type 누락 → 400 MISSING_WORK_TYPE", s, b, 400, "MISSING_WORK_TYPE"))

    # 3. 빈 문자열
    s, b = post(EP, {"work_type": ""})
    results.append(check("빈 문자열 → 400 EMPTY_WORK_TYPE", s, b, 400, "EMPTY_WORK_TYPE"))

    # 4. 미등록 작업명
    s, b = post(EP, {"work_type": "도장작업"})
    results.append(check(
        "미등록 작업명 → 404 UNKNOWN_WORK_TYPE",
        s, b, 404, "UNKNOWN_WORK_TYPE",
        checks=[(lambda x: "supported_work_types" in x.get("error", {}).get("details", {}),
                 "supported_work_types 포함")]
    ))

    print("\n=== 정상 응답 검증 (3개 작업) ===")
    for work_type in ["고소작업", "전기작업", "밀폐공간 작업"]:
        s, b = post(EP, {"work_type": work_type})

        def make_checks(body):
            hazards = body.get("hazards", [])
            checks = [
                (lambda _: s == 200, "HTTP 200"),
                (lambda _: len(hazards) >= 1, f"hazards >= 1 (got {len(hazards)})"),
            ]
            for i, h in enumerate(hazards):
                checks += [
                    (lambda _, h=h: len(h.get("controls", [])) >= 1,
                     f"hazard[{i}] controls >= 1 (got {len(h.get('controls',[]))})"),
                    (lambda _, h=h: "law_ids" in h.get("references", {}),
                     f"hazard[{i}] references.law_ids 존재"),
                    (lambda _, h=h: "moel_expc_ids" in h.get("references", {}),
                     f"hazard[{i}] references.moel_expc_ids 존재"),
                    (lambda _, h=h: "kosha_ids" in h.get("references", {}),
                     f"hazard[{i}] references.kosha_ids 존재"),
                    (lambda _, h=h: isinstance(h.get("confidence_score"), (int, float)),
                     f"hazard[{i}] confidence_score 숫자"),
                    (lambda _, h=h: isinstance(h.get("evidence_summary"), str),
                     f"hazard[{i}] evidence_summary 문자열"),
                    (lambda _, h=h: "related_expc_ids" not in h,
                     f"hazard[{i}] related_expc_ids 미노출"),
                    (lambda _, h=h: "related_expc_ids" not in h.get("references", {}),
                     f"hazard[{i}] references에 related_expc_ids 미노출"),
                ]
            return checks

        extra_checks = make_checks(b)
        passed = check(
            f"{work_type} → 200",
            s, b, 200,
            checks=[(fn, desc) for fn, desc in extra_checks],
        )
        results.append(passed)

        if s == 200:
            hazards = b.get("hazards", [])
            print(f"       work_type={b.get('work_type')}, hazards={len(hazards)}개")
            for h in hazards:
                print(f"         hazard={h['hazard']}, controls={len(h['controls'])}개, "
                      f"score={h['confidence_score']:.2f}")

    # 최종 판정
    total = len(results)
    passed = sum(results)
    print(f"\n=== 결과: {passed}/{total} PASS ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8199")
    args = parser.parse_args()
    BASE = args.base
    sys.exit(run())

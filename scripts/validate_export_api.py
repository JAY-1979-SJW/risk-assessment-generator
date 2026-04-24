"""
Export API 검증 스크립트.

TestClient로 최소 FastAPI 앱을 구성해 엔드포인트를 검증.
DB 연결 없이 동작 (form_registry + builder만 사용).

검증 항목:
  1. GET /api/forms/types — 3종 포함
  2. POST /api/forms/export — education_log, file 모드
  3. POST /api/forms/export — excavation_workplan, base64 모드
  4. POST /api/forms/export — risk_assessment, file 모드
  5. POST /api/forms/export — risk_assessment, base64 모드
  6. POST /api/forms/export — 미지원 form_type → 400 UNSUPPORTED_FORM_TYPE
  7. POST /api/forms/export — required_field 누락 → 400 MISSING_REQUIRED_FIELDS
  8. POST /api/forms/export — repeat 한도 초과 → 400 REPEAT_LIMIT_EXCEEDED
  9. POST /api/forms/export — 스칼라 필드 타입 오류 → 422 INVALID_FIELD_TYPE
 10. POST /api/forms/export — options.filename override 동작

실행:
  python scripts/validate_export_api.py

의존성:
  httpx>=0.27.0  (pip install httpx)
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))

try:
    from starlette.testclient import TestClient
except ImportError:
    print("ERROR: httpx 패키지가 필요합니다.")
    print("       pip install httpx  후 재실행하세요.")
    sys.exit(1)

from fastapi import FastAPI
from routers.form_export import router

# ---------------------------------------------------------------------------
# 최소 테스트 앱 (DB 연결 없음)
# ---------------------------------------------------------------------------
test_app = FastAPI(title="form-export-test")
test_app.include_router(router, prefix="/api")
client = TestClient(test_app, raise_server_exceptions=False)

# ---------------------------------------------------------------------------
# 샘플 form_data
# ---------------------------------------------------------------------------
_EDU_FULL = {
    "site_name": "테스트 사업장",
    "education_type": "정기교육",
    "education_date": "2026-04-24 09:00~11:00",
    "education_location": "본사 교육실",
    "education_duration_hours": "2",
    "education_target_job": "전 직원",
    "instructor_name": "홍길동",
    "instructor_qualification": "산업안전지도사",
    "confirmer_name": "이담당",
    "confirmer_role": "안전보건관리책임자",
    "attendees": [
        {"attendee_name": "김철수", "attendee_job_type": "용접공"},
        {"attendee_name": "이영희", "attendee_job_type": "생산직"},
    ],
}

_EXC_FULL = {
    "site_name": "테스트 현장",
    "excavation_method": "개착식 굴착, 심도 5m",
    "earth_retaining": "H-Pile + 토류판",
    "excavation_machine": "백호우 0.8m³",
    "soil_disposal": "현장 외 반출",
    "water_disposal": "웰포인트 공법",
    "work_method": "단계별 굴착",
    "emergency_measure": "즉시 작업중단 및 대피",
    "guide_worker_required": "필요 (굴착기 진입 시 1명 배치)",
    "access_control": "작업구역 울타리 설치, 안전표지판 부착",
    "emergency_contact": "현장소장 010-0000-0000 / 119",
    "safety_steps": [
        {"task_step": "지하매설물 확인", "hazard": "파손", "safety_measure": "시험굴착"},
        {"task_step": "굴착기 진입", "hazard": "전도", "safety_measure": "유도자 배치"},
    ],
}

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_EXPECTED_TYPES = {"education_log", "excavation_workplan", "risk_assessment"}

_RISK_FULL = {
    "company_name": "테스트 주식회사",
    "industry": "건설업",
    "site_name": "테스트 현장",
    "representative": "홍대표",
    "assessment_type": "최초평가",
    "assessment_date": "2026-04-24",
    "work_type": "굴착공사",
    "rows": [
        {
            "no": "1",
            "process": "굴착",
            "sub_work": "지반 굴착",
            "hazard_category_major": "기계적",
            "hazard_category_minor": "전도",
            "hazard": "굴착기 전도",
            "legal_basis": "기준 규칙 제82조",
            "current_measures": "안전대 착용",
            "risk_scale": "3×3",
            "probability": "2",
            "severity": "3",
            "risk_level": "6",
            "control_measures": "유도자 배치, 작업반경 내 출입 금지",
            "residual_risk_level": "3",
            "target_date": "2026-05-01",
            "completion_date": None,
            "responsible_person": "김안전",
        },
    ],
}


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _check(condition: bool, name: str, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition


# ---------------------------------------------------------------------------
# 검증 함수
# ---------------------------------------------------------------------------

def test_get_types() -> list[bool]:
    results: list[bool] = []
    print("\n=== GET /api/forms/types ===")

    r = client.get("/api/forms/types")
    results.append(_check(r.status_code == 200, "HTTP 200"))

    body = r.json()
    forms = body.get("forms", [])
    types_set = {f["form_type"] for f in forms}

    results.append(_check(len(forms) == len(_EXPECTED_TYPES),
                          f"forms {len(_EXPECTED_TYPES)}종 반환", str(len(forms))))
    results.append(_check(types_set == _EXPECTED_TYPES,
                          f"form_type 목록 == {sorted(_EXPECTED_TYPES)}",
                          str(sorted(types_set))))
    results.append(_check(all("builder" not in f for f in forms),
                          "builder 참조 미노출"))
    results.append(_check(all("required_fields" in f for f in forms),
                          "required_fields 포함"))

    return results


def test_export_education_log_file() -> list[bool]:
    results: list[bool] = []
    print("\n=== POST /api/forms/export — education_log (file) ===")

    r = client.post("/api/forms/export", json={
        "form_type": "education_log",
        "form_data": _EDU_FULL,
        "options": {"return_type": "file"},
    })
    results.append(_check(r.status_code == 200, "HTTP 200"))
    results.append(_check(r.headers.get("content-type", "").startswith(_XLSX_MIME),
                          "Content-Type: xlsx",
                          r.headers.get("content-type", "")))
    disp_edu = r.headers.get("content-disposition", "")
    results.append(_check("content-disposition" in r.headers,
                          "Content-Disposition 헤더 존재", disp_edu))
    results.append(_check("education_log_" in disp_edu,
                          "파일명에 form_type 포함", disp_edu))
    results.append(_check(len(r.content) > 5000, "xlsx bytes 크기 > 5000",
                          f"{len(r.content):,} bytes"))

    return results


def test_export_excavation_workplan_base64() -> list[bool]:
    results: list[bool] = []
    print("\n=== POST /api/forms/export — excavation_workplan (base64) ===")

    r = client.post("/api/forms/export", json={
        "form_type": "excavation_workplan",
        "form_data": _EXC_FULL,
        "options": {"return_type": "base64"},
    })
    results.append(_check(r.status_code == 200, "HTTP 200"))

    body = r.json()
    results.append(_check(body.get("success") is True, "success == true"))
    results.append(_check(body.get("form_type") == "excavation_workplan",
                          "form_type 반환"))
    results.append(_check("file_base64" in body, "file_base64 포함"))
    results.append(_check(isinstance(body.get("size"), int) and body["size"] > 0,
                          "size > 0", str(body.get("size"))))

    # base64 디코딩 가능 여부
    if "file_base64" in body:
        try:
            decoded = base64.b64decode(body["file_base64"])
            results.append(_check(len(decoded) > 5000,
                                  "base64 디코딩 후 bytes 크기 > 5000",
                                  f"{len(decoded):,} bytes"))
        except Exception as e:
            results.append(_check(False, "base64 디코딩 가능", str(e)))

    return results


def test_export_risk_assessment_file() -> list[bool]:
    results: list[bool] = []
    print("\n=== POST /api/forms/export — risk_assessment (file) ===")

    r = client.post("/api/forms/export", json={
        "form_type": "risk_assessment",
        "form_data": _RISK_FULL,
        "options": {"return_type": "file"},
    })
    results.append(_check(r.status_code == 200, "HTTP 200", str(r.status_code)))
    results.append(_check(r.headers.get("content-type", "").startswith(_XLSX_MIME),
                          "Content-Type: xlsx",
                          r.headers.get("content-type", "")))
    disp = r.headers.get("content-disposition", "")
    results.append(_check("content-disposition" in r.headers,
                          "Content-Disposition 헤더 존재", disp))
    results.append(_check("risk_assessment_" in disp,
                          "파일명에 form_type 포함", disp))
    results.append(_check(len(r.content) > 5000, "xlsx bytes 크기 > 5000",
                          f"{len(r.content):,} bytes"))

    return results


def test_export_risk_assessment_base64() -> list[bool]:
    results: list[bool] = []
    print("\n=== POST /api/forms/export — risk_assessment (base64) ===")

    r = client.post("/api/forms/export", json={
        "form_type": "risk_assessment",
        "form_data": _RISK_FULL,
        "options": {"return_type": "base64"},
    })
    results.append(_check(r.status_code == 200, "HTTP 200", str(r.status_code)))

    body = r.json()
    results.append(_check(body.get("success") is True, "success == true"))
    results.append(_check(body.get("form_type") == "risk_assessment",
                          "form_type 반환"))
    results.append(_check(body.get("display_name") == "위험성평가표",
                          "display_name == '위험성평가표'",
                          repr(body.get("display_name"))))
    results.append(_check("file_base64" in body, "file_base64 포함"))
    results.append(_check(isinstance(body.get("size"), int) and body["size"] > 0,
                          "size > 0", str(body.get("size"))))

    if "file_base64" in body:
        try:
            import base64 as _b64
            decoded = _b64.b64decode(body["file_base64"])
            results.append(_check(len(decoded) > 5000,
                                  "base64 디코딩 후 bytes 크기 > 5000",
                                  f"{len(decoded):,} bytes"))
        except Exception as e:
            results.append(_check(False, "base64 디코딩 가능", str(e)))

    return results


def test_unsupported_form_type() -> list[bool]:
    results: list[bool] = []
    print("\n=== POST /api/forms/export — 미지원 form_type ===")

    for bad_type in ["vehicle_workplan", "", "EDUCATION_LOG"]:
        r = client.post("/api/forms/export", json={
            "form_type": bad_type,
            "form_data": {},
        })
        body = r.json()
        results.append(_check(r.status_code == 400,
                              f"form_type='{bad_type}' → HTTP 400",
                              str(r.status_code)))
        results.append(_check(body.get("error_code") == "UNSUPPORTED_FORM_TYPE",
                              f"  error_code == UNSUPPORTED_FORM_TYPE",
                              body.get("error_code", "")))

    return results


def test_missing_required_fields() -> list[bool]:
    results: list[bool] = []
    print("\n=== POST /api/forms/export — required_field 누락 ===")

    # education_log — education_type 누락
    r = client.post("/api/forms/export", json={
        "form_type": "education_log",
        "form_data": {k: v for k, v in _EDU_FULL.items() if k != "education_type"},
    })
    body = r.json()
    results.append(_check(r.status_code == 400, "HTTP 400"))
    results.append(_check(body.get("error_code") == "MISSING_REQUIRED_FIELDS",
                          "error_code == MISSING_REQUIRED_FIELDS",
                          body.get("error_code", "")))
    results.append(_check("education_type" in body.get("details", {}).get("missing_fields", []),
                          "details.missing_fields에 'education_type' 포함"))

    # excavation_workplan — 전체 required 누락
    r2 = client.post("/api/forms/export", json={
        "form_type": "excavation_workplan",
        "form_data": {"site_name": "테스트"},   # required 없음
    })
    body2 = r2.json()
    results.append(_check(r2.status_code == 400, "excavation_workplan 전체누락 → HTTP 400"))
    results.append(_check(body2.get("error_code") == "MISSING_REQUIRED_FIELDS",
                          "error_code == MISSING_REQUIRED_FIELDS"))

    return results


def test_repeat_limit_exceeded() -> list[bool]:
    results: list[bool] = []
    print("\n=== POST /api/forms/export — repeat 한도 초과 ===")

    # education_log attendees > 30
    over_attendees = [{"attendee_name": f"수강자{i}", "attendee_job_type": "직종"} for i in range(35)]
    r = client.post("/api/forms/export", json={
        "form_type": "education_log",
        "form_data": {**_EDU_FULL, "attendees": over_attendees},
    })
    body = r.json()
    results.append(_check(r.status_code == 400, "attendees 35개 → HTTP 400",
                          str(r.status_code)))
    results.append(_check(body.get("error_code") == "REPEAT_LIMIT_EXCEEDED",
                          "error_code == REPEAT_LIMIT_EXCEEDED",
                          body.get("error_code", "")))
    results.append(_check(body.get("details", {}).get("limit") == 30,
                          "details.limit == 30"))

    # excavation_workplan safety_steps > 10
    over_steps = [{"task_step": f"단계{i}", "hazard": "위험", "safety_measure": "조치"} for i in range(12)]
    r2 = client.post("/api/forms/export", json={
        "form_type": "excavation_workplan",
        "form_data": {**_EXC_FULL, "safety_steps": over_steps},
    })
    body2 = r2.json()
    results.append(_check(r2.status_code == 400, "safety_steps 12개 → HTTP 400"))
    results.append(_check(body2.get("error_code") == "REPEAT_LIMIT_EXCEEDED",
                          "error_code == REPEAT_LIMIT_EXCEEDED"))
    results.append(_check(body2.get("details", {}).get("limit") == 10,
                          "details.limit == 10"))

    return results


def test_invalid_field_type() -> list[bool]:
    results: list[bool] = []
    print("\n=== POST /api/forms/export — 스칼라 필드 타입 오류 ===")

    # integer 값 전달
    r = client.post("/api/forms/export", json={
        "form_type": "education_log",
        "form_data": {**_EDU_FULL, "site_name": 12345},   # int는 불허
    })
    body = r.json()
    results.append(_check(r.status_code == 422, "int 값 → HTTP 422",
                          str(r.status_code)))
    results.append(_check(body.get("error_code") == "INVALID_FIELD_TYPE",
                          "error_code == INVALID_FIELD_TYPE",
                          body.get("error_code", "")))

    return results


def test_filename_override() -> list[bool]:
    results: list[bool] = []
    print("\n=== POST /api/forms/export — options.filename override ===")

    r = client.post("/api/forms/export", json={
        "form_type": "excavation_workplan",
        "form_data": _EXC_FULL,
        "options": {"return_type": "file", "filename": "내_작업계획서"},
    })
    disp = r.headers.get("content-disposition", "")
    results.append(_check(r.status_code == 200, "HTTP 200", str(r.status_code)))
    # RFC 5987 인코딩: 한글은 %EC 등 percent-encoding으로 표시됨
    results.append(_check(
        "%EB%82%B4_%EC%9E%91%EC%97%85%EA%B3%84%ED%9A%8D%EC%84%9C.xlsx" in disp
        or "내_작업계획서.xlsx" in disp,
        "Content-Disposition에 커스텀 파일명 포함 (RFC5987 인코딩)", disp,
    ))

    return results


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main() -> int:
    print("Export API 검증 시작")
    print("=" * 50)

    all_results: list[bool] = []
    all_results += test_get_types()
    all_results += test_export_education_log_file()
    all_results += test_export_excavation_workplan_base64()
    all_results += test_export_risk_assessment_file()
    all_results += test_export_risk_assessment_base64()
    all_results += test_unsupported_form_type()
    all_results += test_missing_required_fields()
    all_results += test_repeat_limit_exceeded()
    all_results += test_invalid_field_type()
    all_results += test_filename_override()

    total  = len(all_results)
    passed = sum(all_results)
    failed = total - passed

    print("\n" + "=" * 50)
    print(f"결과: {passed}/{total} PASS, {failed} FAIL")
    if failed == 0:
        print("최종 판정: PASS")
        return 0
    else:
        print("최종 판정: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())

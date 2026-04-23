"""
POST /api/v1/risk-assessment/build
작업유형 기반 위험성평가 매핑 결과 조회.
"""
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

# engine/ 위치 탐색: 컨테이너(/app/engine 볼륨 마운트)와 로컬(프로젝트 루트) 양쪽 지원
def _find_engine_root() -> Path:
    for candidate in [
        Path(__file__).parent.parent,          # 컨테이너: /app
        Path(__file__).parent.parent.parent,   # 로컬: project root
    ]:
        if (candidate / "engine" / "kras_connector" / "mapper.py").exists():
            return candidate
    return Path(__file__).parent.parent.parent  # fallback

_ROOT = _find_engine_root()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engine.kras_connector.mapper import build_risk_assessment  # noqa: E402
from schemas.risk_assessment_build import RiskAssessmentBuildResponse  # noqa: E402

router = APIRouter(prefix="/v1/risk-assessment", tags=["risk-assessment-build"])

_SUPPORTED_WORK_TYPES = [
    "고소작업",
    "굴착작업",
    "양중작업",
    "이동식비계 작업",
    "고소작업대 작업",
    "밀폐공간 작업",
    "화기작업",
    "전기작업",
    "절단/천공 작업",
    "중장비 작업",
]


def _err(code: str, message: str, details: Optional[dict] = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


@router.post(
    "/build",
    response_model=RiskAssessmentBuildResponse,
    responses={
        400: {"description": "work_type 누락 또는 빈값"},
        404: {"description": "등록되지 않은 작업유형"},
        500: {"description": "내부 서버 오류"},
    },
)
def build(body: Optional[Any] = Body(default=None)):
    """작업유형 기반 위험성평가 매핑 결과를 반환한다."""
    # ── 1. body / work_type 존재 여부 검증 ────────────────────────────────────
    if body is None or not isinstance(body, dict) or "work_type" not in body:
        return JSONResponse(
            status_code=400,
            content=_err("MISSING_WORK_TYPE", "work_type 필드가 필요합니다."),
        )

    work_type_raw = body.get("work_type")

    if work_type_raw is None:
        return JSONResponse(
            status_code=400,
            content=_err("MISSING_WORK_TYPE", "work_type 필드가 필요합니다."),
        )

    if not isinstance(work_type_raw, str) or work_type_raw.strip() == "":
        return JSONResponse(
            status_code=400,
            content=_err(
                "EMPTY_WORK_TYPE",
                "work_type 값이 비어 있습니다.",
                {"work_type": work_type_raw if isinstance(work_type_raw, str) else ""},
            ),
        )

    work_type = work_type_raw  # 완전 일치 정책 — strip/normalize 하지 않음

    # ── 2. 매퍼 호출 ─────────────────────────────────────────────────────────
    try:
        result = build_risk_assessment(work_type)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception(
            "build_risk_assessment 오류: work_type=%r", work_type
        )
        return JSONResponse(
            status_code=500,
            content=_err("INTERNAL_ERROR", "내부 오류가 발생했습니다. 잠시 후 다시 시도하세요."),
        )

    # ── 3. 결과 없음 → 미등록 작업유형 ───────────────────────────────────────
    if not result.get("hazards"):
        return JSONResponse(
            status_code=404,
            content=_err(
                "UNKNOWN_WORK_TYPE",
                "등록되지 않은 작업유형입니다.",
                {
                    "work_type": work_type,
                    "supported_work_types": _SUPPORTED_WORK_TYPES,
                },
            ),
        )

    # ── 4. 정상 반환 ──────────────────────────────────────────────────────────
    return result

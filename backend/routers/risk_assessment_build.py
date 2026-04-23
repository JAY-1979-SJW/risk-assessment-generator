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
from engine.kras_connector.enrichment import (  # noqa: E402
    InvalidInputOption,
    apply_rules,
    context_is_empty,
    normalize_input_context,
)
from schemas.risk_assessment_build import ApiError, RiskAssessmentBuildResponse  # noqa: E402

router = APIRouter(prefix="/v1/risk-assessment", tags=["risk-assessment"])

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
    operation_id="buildRiskAssessment",
    response_model=RiskAssessmentBuildResponse,
    response_model_exclude_none=True,
    responses={
        400: {
            "model": ApiError,
            "description": "work_type 누락/빈값 또는 equipment/location/conditions 허용값 위반",
        },
        404: {"model": ApiError, "description": "등록되지 않은 작업유형"},
        500: {"model": ApiError, "description": "내부 서버 오류"},
    },
)
def build(body: Optional[Any] = Body(default=None)):
    """작업유형 기반 위험성평가 매핑 결과를 반환한다. v2: equipment/location/conditions 선택형 보강."""
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

    # ── 2. v2 입력 확장 정규화/검증 ───────────────────────────────────────────
    try:
        input_ctx = normalize_input_context(body)
    except InvalidInputOption as exc:
        return JSONResponse(
            status_code=400,
            content=_err(
                "INVALID_INPUT_OPTION",
                "입력 옵션이 허용되지 않은 값입니다.",
                {
                    "field": exc.field,
                    "value": exc.value,
                    "allowed_values": exc.allowed,
                },
            ),
        )

    # ── 3. 매퍼 호출 ─────────────────────────────────────────────────────────
    try:
        base_result = build_risk_assessment(work_type)
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "build_risk_assessment 오류: work_type=%r", work_type
        )
        return JSONResponse(
            status_code=500,
            content=_err("INTERNAL_ERROR", "내부 오류가 발생했습니다. 잠시 후 다시 시도하세요."),
        )

    # ── 4. 결과 없음 → 미등록 작업유형 ───────────────────────────────────────
    if not base_result.get("hazards"):
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

    # ── 5. 하위호환: 컨텍스트 미제공 시 v1 응답 그대로 반환 ───────────────────
    if context_is_empty(input_ctx):
        return base_result

    # ── 6. enrichment 적용 → input_context 부가 ───────────────────────────────
    try:
        enriched = apply_rules(base_result, input_ctx)
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "enrichment 오류: work_type=%r ctx=%r", work_type, input_ctx
        )
        return JSONResponse(
            status_code=500,
            content=_err("INTERNAL_ERROR", "내부 오류가 발생했습니다. 잠시 후 다시 시도하세요."),
        )

    enriched["input_context"] = input_ctx
    return enriched

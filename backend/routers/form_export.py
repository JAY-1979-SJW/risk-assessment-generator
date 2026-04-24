"""
Form Export Router — GET /api/forms/types, POST /api/forms/export

계약: docs/design/export_api_contract.md
Registry: engine/output/form_registry.py

인증: v1 내부용으로 생략 (확장 지점 주석 표시).
     인증이 필요할 때: dependencies=[Security(_require_internal_key)] 추가.
보안: form_data 원문 로그 기록 금지. xlsx 파일 서버 저장 금지.
"""
from __future__ import annotations

import base64
import logging
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# 프로젝트 루트 sys.path 추가 (backend/routers/ → backend/ → 프로젝트 루트)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from engine.output.form_registry import (
    UnsupportedFormTypeError,
    build_form_excel,
    get_form_spec,
    list_supported_forms,
)

# ---------------------------------------------------------------------------
# 상수 / 로거
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/forms", tags=["forms-export"])

_KST       = timezone(timedelta(hours=9))
_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_logger    = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic 모델
# ---------------------------------------------------------------------------

class ExportOptions(BaseModel):
    return_type: str = "file"       # "file" | "base64"
    filename: Optional[str] = None


class ExportRequest(BaseModel):
    form_type: str
    form_data: Dict[str, Any]
    options: Optional[ExportOptions] = None


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _error_response(status: int, code: str, message: str,
                    details: Optional[dict] = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={
        "success": False,
        "error_code": code,
        "message": message,
        "details": details or {},
    })


def _sanitize_filename(name: str) -> str:
    """경로 구분자 제거, .xlsx 보장, 255자 제한."""
    name = name.replace("\\", "").replace("/", "")
    name = re.sub(r"\.{2,}", ".", name)          # .. 연속 제거
    if not name.lower().endswith(".xlsx"):
        name += ".xlsx"
    if len(name) > 255:
        name = name[:251] + ".xlsx"
    return name


def _build_filename(form_type: str, custom: Optional[str]) -> str:
    if custom and custom.strip():
        return _sanitize_filename(custom.strip())
    now = datetime.now(_KST)
    return f"{form_type}_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"


def _validate(form_type: str, form_data: dict,
              opts: ExportOptions) -> Optional[JSONResponse]:
    """
    검증 5단계 — 실패 시 JSONResponse 반환, 통과 시 None.

    순서:
    1. form_type 존재
    2. required_fields 누락/null
    3. repeat_field 길이 제한
    4. 개별 스칼라 필드 타입
    5. options.return_type 값
    """
    # 1. form_type
    try:
        spec = get_form_spec(form_type)
    except UnsupportedFormTypeError:
        return _error_response(400, "UNSUPPORTED_FORM_TYPE",
                               "지원하지 않는 서식 유형입니다.", {
                                   "requested": form_type,
                                   "supported": [f["form_type"] for f in list_supported_forms()],
                               })

    # 2. required_fields (null은 누락으로 처리, 빈 문자열은 허용)
    missing = [f for f in spec["required_fields"] if form_data.get(f) is None]
    if missing:
        return _error_response(400, "MISSING_REQUIRED_FIELDS",
                               "필수 입력 항목이 누락되었습니다.",
                               {"missing_fields": missing})

    # 3. repeat_field 길이 제한 + extra_list_fields 타입 확인
    rf            = spec.get("repeat_field")
    max_rows      = spec.get("max_repeat_rows")
    extra_lists   = set(spec.get("extra_list_fields") or [])
    list_fields   = ({rf} if rf else set()) | extra_lists  # 타입 체크 제외 대상 전체

    if rf and max_rows and rf in form_data and form_data[rf] is not None:
        rows = form_data[rf]
        if not isinstance(rows, list):
            return _error_response(422, "INVALID_FIELD_TYPE",
                                   "필드 타입이 올바르지 않습니다.", {
                                       "field": rf,
                                       "expected": "array",
                                       "received": type(rows).__name__,
                                   })
        if len(rows) > max_rows:
            return _error_response(400, "REPEAT_LIMIT_EXCEEDED",
                                   "반복 행 수가 허용 한도를 초과했습니다.", {
                                       "field": rf,
                                       "limit": max_rows,
                                       "received": len(rows),
                                   })
        for idx, item in enumerate(rows):
            if not isinstance(item, dict):
                return _error_response(422, "INVALID_FIELD_TYPE",
                                       "필드 타입이 올바르지 않습니다.", {
                                           "field": f"{rf}[{idx}]",
                                           "expected": "object",
                                           "received": type(item).__name__,
                                       })

    # extra_list_fields — list 타입만 허용 (max_rows 제한 없음, 항목은 dict만)
    for elf in extra_lists:
        if elf not in form_data or form_data[elf] is None:
            continue
        val = form_data[elf]
        if not isinstance(val, list):
            return _error_response(422, "INVALID_FIELD_TYPE",
                                   "필드 타입이 올바르지 않습니다.", {
                                       "field": elf,
                                       "expected": "array",
                                       "received": type(val).__name__,
                                   })
        for idx, item in enumerate(val):
            if not isinstance(item, dict):
                return _error_response(422, "INVALID_FIELD_TYPE",
                                       "필드 타입이 올바르지 않습니다.", {
                                           "field": f"{elf}[{idx}]",
                                           "expected": "object",
                                           "received": type(item).__name__,
                                       })

    # 4. 스칼라 필드 타입 (list_fields 전체 제외, string|null만 허용)
    for key, val in form_data.items():
        if key in list_fields:
            continue
        if val is not None and not isinstance(val, str):
            return _error_response(422, "INVALID_FIELD_TYPE",
                                   "필드 타입이 올바르지 않습니다.", {
                                       "field": key,
                                       "expected": "string or null",
                                       "received": type(val).__name__,
                                   })

    # 5. options.return_type
    if opts.return_type not in ("file", "base64"):
        return _error_response(422, "INVALID_FIELD_TYPE",
                               "필드 타입이 올바르지 않습니다.", {
                                   "field": "options.return_type",
                                   "expected": "'file' or 'base64'",
                                   "received": repr(opts.return_type),
                               })

    return None  # 통과


# ---------------------------------------------------------------------------
# 엔드포인트
# ---------------------------------------------------------------------------

@router.get("/types")
def get_form_types():
    """
    지원 form_type 목록 반환.

    form_registry.list_supported_forms() 출력과 1:1 매핑.
    builder 함수 참조 미노출.

    # v1 인증 확장 지점:
    # dependencies=[Security(_require_internal_key)]
    """
    return {"forms": list_supported_forms()}


@router.post("/export")
def export_form(req: ExportRequest):
    """
    form_type + form_data → xlsx bytes 반환.

    options.return_type:
    - "file"   (기본): xlsx binary stream, Content-Disposition: attachment
    - "base64": JSON body에 base64 인코딩 문자열 포함

    보안:
    - form_data 원문 로그 기록 금지
    - xlsx 서버 저장 금지 (bytes로만 반환)

    # v1 인증 확장 지점:
    # dependencies=[Security(_require_internal_key)]
    """
    opts = req.options or ExportOptions()

    # 검증
    err = _validate(req.form_type, req.form_data, opts)
    if err is not None:
        return err

    # xlsx 생성
    try:
        xlsx_bytes = build_form_excel(req.form_type, req.form_data)
    except Exception as exc:
        # form_data 원문 미기록
        _logger.error("builder_error form_type=%s exc=%s", req.form_type, type(exc).__name__, exc_info=True)
        return _error_response(500, "BUILDER_ERROR",
                               "서식 파일 생성 중 내부 오류가 발생했습니다.", {
                                   "form_type": req.form_type,
                                   "hint": "서버 로그를 확인하세요.",
                               })

    # 파일명
    filename = _build_filename(req.form_type, opts.filename)

    # 접근 로그 (form_data 원문 미기록)
    _logger.info("form_export form_type=%s filename=%s size=%d",
                 req.form_type, filename, len(xlsx_bytes))

    # base64 응답
    if opts.return_type == "base64":
        spec = get_form_spec(req.form_type)
        return {
            "success": True,
            "form_type": req.form_type,
            "display_name": spec["display_name"],
            "filename": filename,
            "file_base64": base64.b64encode(xlsx_bytes).decode(),
            "size": len(xlsx_bytes),
            "generated_at": datetime.now(_KST).isoformat(),
        }

    # file 응답 (기본)
    # RFC 5987 인코딩으로 한글 파일명 지원 (기존 export.py 패턴 동일)
    encoded_name = quote(filename, safe="")
    return Response(
        content=xlsx_bytes,
        media_type=_XLSX_MIME,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
            "Content-Length": str(len(xlsx_bytes)),
        },
    )

"""
위험성평가 추천 API

로컬 standalone 실행:
  uvicorn app.api.risk_assessment:app --reload --port 8600

서버 통합: backend/routers/risk_assessment.py 로 등록
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (scripts.search 임포트용)
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from scripts.search.risk_assessment_formatter import format_assessment

# ── 스키마 ──────────────────────────────────────────────────────────────────

class AssessmentRequest(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query는 빈값일 수 없습니다")
        return v


# ── standalone FastAPI 앱 (로컬 테스트용) ────────────────────────────────────

app = FastAPI(title="위험성평가 추천 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.post("/risk-assessment")
async def create_risk_assessment(body: AssessmentRequest) -> dict:
    """
    작업 유형 쿼리로 위험성평가 요약 JSON을 반환합니다.

    - **query**: 작업 유형 또는 위험 키워드 (예: "비계 작업", "밀폐공간 질식")
    """
    try:
        result = format_assessment(body.query)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"인덱스 파일 없음: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 오류: {e}")
    return result


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# ── APIRouter (backend/routers/risk_assessment.py 에서 재사용) ────────────────

from fastapi import APIRouter

router = APIRouter(prefix="/risk-assessment", tags=["risk-assessment"])


@router.post("")
async def risk_assessment_endpoint(body: AssessmentRequest) -> dict:
    try:
        result = format_assessment(body.query)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"인덱스 파일 없음: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 오류: {e}")
    return result

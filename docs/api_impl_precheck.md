# API 구현 사전 점검 보고서

## 1. FastAPI 앱 구조

- 진입점: `backend/main.py`
- `app = FastAPI(title="KRAS API", version="2.0.0")` (line 64)
- 실행 경로: `backend/` 디렉토리에서 uvicorn 실행

## 2. 라우터 등록 방식

```python
# backend/main.py (lines 71-81)
app.include_router(router, prefix="/api")
```

- 모든 라우터는 `prefix="/api"` 로 등록
- 라우터 자체 prefix 가 그 뒤에 붙음
- 예: `router = APIRouter(prefix="/v1/risk-assessment")` → 최종 경로 `/api/v1/risk-assessment/...`

## 3. Request/Response 스키마 위치

- 전용 파일: `backend/schemas/` 디렉토리
- 예: `backend/schemas/risk_assessment_draft.py`
- 일부 라우터는 파일 내 인라인 정의 (소규모)
- 신규 스키마: `backend/schemas/risk_assessment_build.py` 생성

## 4. mapper.py import 경로

- 파일: `engine/kras_connector/mapper.py` (프로젝트 루트 기준)
- `backend/routers/` 에서 import 방법:
  ```python
  _ROOT = Path(__file__).parent.parent.parent  # project root
  sys.path.insert(0, str(_ROOT))
  from engine.kras_connector.mapper import build_risk_assessment
  ```
- 참고: `backend/routers/risk_assessment.py` 동일 패턴 사용

## 5. 예외 처리 공통 방식

- 정상 에러: `raise HTTPException(status_code, detail=...)`
- 커스텀 응답: `return JSONResponse(status_code=N, content={...})`
- 계약상 응답 포맷 `{"error": {"code": ..., "message": ..., "details": ...}}` → `JSONResponse` 직접 반환
- 전역 미들웨어(`log_requests`)가 uncaught exception 을 500으로 처리

## 6. 구현 방침

| 항목 | 결정 |
|------|------|
| 라우터 파일 | `backend/routers/risk_assessment_build.py` (신규) |
| 스키마 파일 | `backend/schemas/risk_assessment_build.py` (신규) |
| main.py 등록 | `prefix="/api"` 로 추가 |
| 에러 응답 | `JSONResponse` 직접 반환 (계약 포맷 일치) |
| work_type 검증 | 엔드포인트 내부에서 수동 검증 (422 → 400 변환) |
| DB write | 없음 (read-only, mapper 위임) |

"""
위험성평가 추천 라우터 — backend/main.py 에 등록
app/api/risk_assessment.py 의 router를 재노출
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.api.risk_assessment import router  # noqa: F401

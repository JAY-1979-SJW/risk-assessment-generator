# -*- coding: utf-8 -*-
"""
OpenAI API 기반 위험성평가 자동생성 엔진

입력: 공정명, 업종/공종 키워드
처리: KOSHA DB → raw_text 수집 → OpenAI JSON 추출
출력: KRAS 표준 위험성평가 항목 리스트
"""

import os
import json
import textwrap
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / '.env')

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
MAX_CONTEXT_CHARS = 12000  # 토큰 절약: 약 3k tokens

RISK_CATEGORIES = ["기계적 요인", "전기적 요인", "화학(물질)적 요인",
                   "작업환경 요인", "작업특성 요인", "기타"]

SYSTEM_PROMPT = textwrap.dedent("""
당신은 산업안전보건 전문가입니다.
제공된 안전보건 자료(raw_text)를 분석하여 위험성평가 항목을 JSON으로 추출합니다.

반드시 다음 JSON 배열 형식으로만 응답하세요. 설명문 없이 JSON만 출력:
[
  {
    "세부작업명": "작업 설명 (20자 이내)",
    "위험분류": "기계적 요인|전기적 요인|화학(물질)적 요인|작업환경 요인|작업특성 요인|기타 중 하나",
    "위험세부분류": "협착|추락|감전|폭발|분진|소음|화재|절단|충돌|기타 중 하나",
    "위험상황": "구체적인 위험 발생 상황과 예상 결과 (50자 이내)",
    "관련근거": "산업안전보건법 또는 안전보건규칙 조항 (없으면 빈 문자열)",
    "현재조치": "현재 시행 중인 안전보건조치 (없으면 빈 문자열)",
    "가능성": 1,
    "중대성": 2,
    "감소대책": "추가 위험 감소 대책 (50자 이내)"
  }
]

가능성/중대성 기준:
- 3(상): 일상적·자주 발생
- 2(중): 가끔 발생 가능
- 1(하): 드물게 발생
위험성 = 가능성 × 중대성 (6이상=높음, 3~4=보통, 1~2=낮음)

최대 15개 항목 추출. 실제 자료에 근거한 내용만 작성.
""").strip()


def _build_user_prompt(process_name: str, trade_type: str, raw_texts: list[str]) -> str:
    combined = "\n\n---\n\n".join(raw_texts)
    if len(combined) > MAX_CONTEXT_CHARS:
        combined = combined[:MAX_CONTEXT_CHARS] + "\n...(이하 생략)"

    return (
        f"공정명: {process_name}\n"
        f"작업 유형: {trade_type}\n\n"
        f"=== KOSHA 안전보건 자료 ===\n{combined}"
    )


def generate_risk_items(
    process_name: str,
    trade_type: str,
    raw_texts: list[str],
    work_type: str = "",
) -> list[dict]:
    """
    OpenAI API 호출 → KRAS 위험성평가 항목 리스트 반환.
    raw_texts: DB에서 가져온 관련 청크 텍스트 목록
    """
    if not raw_texts:
        return []

    user_msg = _build_user_prompt(
        process_name or trade_type,
        f"{trade_type} {work_type}".strip(),
        raw_texts,
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)

    # JSON object로 감싸진 경우 배열 꺼내기
    if isinstance(parsed, dict):
        for v in parsed.values():
            if isinstance(v, list):
                parsed = v
                break

    return _normalize_items(parsed, process_name or trade_type)


def _normalize_items(items: list, process_name: str) -> list[dict]:
    """OpenAI 응답을 KRAS DataManager 형식으로 정규화"""
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            prob = int(item.get("가능성", 2))
            sev = int(item.get("중대성", 2))
        except (ValueError, TypeError):
            prob, sev = 2, 2

        prob = max(1, min(3, prob))
        sev = max(1, min(3, sev))

        risk_score = prob * sev
        if risk_score >= 6:
            risk_level = "높음"
        elif risk_score >= 3:
            risk_level = "보통"
        else:
            risk_level = "낮음"

        cat = item.get("위험분류", "기타")
        if cat not in RISK_CATEGORIES:
            cat = "기타"

        result.append({
            "공정명": process_name,
            "세부작업명": item.get("세부작업명", ""),
            "위험분류": cat,
            "위험세부분류": item.get("위험세부분류", ""),
            "위험상황": item.get("위험상황", ""),
            "관련근거": item.get("관련근거", ""),
            "현재조치": item.get("현재조치", ""),
            "가능성": prob,
            "중대성": sev,
            "위험성": risk_score,
            "위험등급": risk_level,
            "감소대책": item.get("감소대책", ""),
        })

    return result

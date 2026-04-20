"""
Text-based hazard classifier (deterministic keyword matching).
Corrects generic hazard_type tags ("위험", "유해") by reading chunk text directly.
No external dependencies.
"""

import re
from typing import Dict, List, Optional

# Tags that carry no information about specific hazard type
GENERIC_HAZARD_TAGS = frozenset([
    '위험', '유해', '위험요인', '위험성평가', '재해사례', '안전', '사고',
    '위험물질', '위험기계', '유해위험',
])

# Hazard keyword map — checked in listed priority order (most specific first).
# Each hazard type has primary and secondary keywords.
# Structure: hazard_label -> (primary_kw, secondary_kw)
#   - primary: single occurrence is enough to assign
#   - secondary: used for reinforcement only
_HAZARD_RULES: List[tuple] = [
    # (label, primary_keywords, secondary_keywords)
    ('질식', ['질식', '산소결핍', '산소 결핍', '산소농도', '황화수소', 'H2S', '이산화탄소', '일산화탄소',
              '밀폐공간 작업', '밀폐된', '유해가스 농도', '산소부족'],
             ['밀폐공간', '환기', '송기마스크', '공기호흡기']),
    ('감전', ['감전', '활선', '활선작업', '전기사고', 'LOTO', '잠금장치', '전원 차단', '전원차단',
              '누전', '아크', '아크플래시', '절연 파괴', '절연파괴', '고압전기'],
             ['전기', '절연', '누전차단기']),
    ('폭발', ['폭발', '가스 누출', '가스누출', 'LPG 누출', 'LPG누출', '가연성 가스', '가연성가스',
              '압력 파열', '압력파열', '화약', '폭발위험'],
             ['LPG', '가스관', '압력']),
    ('화재', ['화재', '화재 발생', '인화성', '불꽃 비산', '불꽃비산', '불티', '점화원',
              '가연물', '화기 사용', '화기사용'],
             ['소화기', '화기', '방화']),
    ('추락', ['추락', '떨어짐', '떨어지', '고소 추락', '고소추락', '추락 사고', '추락위험',
              '개구부 추락', '비계 추락'],
             ['안전난간', '추락방지', '안전대', '작업발판', '고소', '비계', '사다리', '지붕']),
    ('낙하', ['낙하물', '물체 낙하', '낙하 위험', '중량물 낙하', '자재 낙하'],
             ['낙하', '비산']),
    ('충돌', ['충돌', '부딪힘', '충격', '충돌 위험'],
             ['크레인', '지게차', '차량']),
    ('붕괴', ['붕괴', '전도', '도괴', '지반 붕괴', '지반붕괴', '흙막이 붕괴', '동바리 붕괴',
              '구조물 붕괴'],
             ['동바리', '거푸집', '흙막이', '굴착', '사면']),
    ('협착', ['협착', '끼임', '압착', '말림', '회전체 협착'],
             ['회전체', '컨베이어', '프레스']),
    ('절단', ['절단 위험', '베임', '회전날', '절삭 위험', '날에 접촉', '날 접촉'],
             ['절단', '그라인더', '커터', '톱']),
    ('중독', ['중독', '화학물질 중독', '가스 중독', '흡입 중독', '피부 노출', '호흡기 노출', 'MSDS'],
             ['유해화학물질', '화학물질', '흡입']),
    ('분진', ['분진', '용접흄', '용접 흄', '석면', '실리카', '미세먼지'],
             ['먼지', '흄']),
    ('소음', ['소음 노출', '청력 손실', '소음성 난청'],
             ['소음', '진동']),
]


def classify_hazard_from_text(text: str) -> List[str]:
    """
    Classify hazard types by scanning text for specific keywords.
    Returns list of matched hazard labels (most specific first, no duplicates).
    Tag order preserved for consistency.
    """
    if not text:
        return []

    found = []
    for label, primary_kw, secondary_kw in _HAZARD_RULES:
        # Primary keyword hit → immediate match
        for kw in primary_kw:
            if kw in text:
                if label not in found:
                    found.append(label)
                break

    # If no primary hit, check secondary (needs at least 2 secondary hits for an ambiguous label)
    if not found:
        for label, primary_kw, secondary_kw in _HAZARD_RULES:
            if label in found:
                continue
            hits = sum(1 for kw in secondary_kw if kw in text)
            if hits >= 2:
                found.append(label)

    return found


def filter_generic_hazards(hazards: List[str]) -> List[str]:
    """Remove generic meaningless hazard tags from a list."""
    return [h for h in hazards if h not in GENERIC_HAZARD_TAGS]


def classify_chunk_hazard(chunk: dict) -> Optional[str]:
    """
    Determine best hazard label for a single chunk.
    Priority: specific hazard_type tag > text classifier result.
    Returns None if no useful hazard can be determined.
    """
    tag = chunk.get('hazard_type') or ''
    if tag and tag not in GENERIC_HAZARD_TAGS:
        return tag

    text = (chunk.get('normalized_text') or chunk.get('raw_text') or '')
    classified = classify_hazard_from_text(text)
    return classified[0] if classified else None

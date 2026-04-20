"""
Result assembler: takes top-k scored chunks and produces structured output fields.
All dedup/priority logic is deterministic.

v1.1: generic tag filter, text-based hazard classifier, phrase extraction
v1.2: improved action phrase extraction (sliding window, length cap),
      hazard-keyed action reinforcement, less-aggressive action dedup
"""

import re
from typing import Any, Dict, List, Literal, Optional

from .retrieval import normalize_text
from .hazard_classifier import (
    classify_hazard_from_text,
    filter_generic_hazards,
    GENERIC_HAZARD_TAGS,
)

# ── Action phrase extraction constants ─────────────────────────────────────

_ACTION_VERBS = (
    '착용', '설치', '차단', '확인', '점검', '제거', '금지', '비치',
    '배치', '측정', '실시', '교육', '통제', '사용', '방지',
    '준수', '수행', '관리', '감시', '유지', '고정', '체결',
    '검토', '확보', '수립', '지정', '부착', '격리', '차폐',
)

_MIN_PHRASE_LEN = 4
_MAX_PHRASE_LEN = 50   # v1.2: cap phrase length to prevent noisy long sentences
_WIN_BEFORE = 22       # v1.2: sliding window — chars of context before verb

# Single-word generic control_measure values that carry no information
_GENERIC_ACTIONS = frozenset([
    '예방', '대책', '안전조치', '착용', '설치', '확인', '점검', '실시',
    '준수', '사용', '차단', '금지', '관리', '교육', '조치', '실행',
])

# ── v1.2: Hazard-keyed action reinforcement keywords ───────────────────────
#
# For each hazard type, keywords that should appear in recommended_actions
# when the hazard is detected. The engine scans matched chunks for these
# keywords and, if found, prepends them — no content generation.
_HAZARD_ACTION_KEYWORDS: Dict[str, List[str]] = {
    '추락': [
        '안전난간', '안전대 착용', '작업발판', '추락방지망',
        '개구부 덮개', '추락 방지', '안전대', '비계 안전',
    ],
    '감전': [
        '전원 차단', '절연장갑', '누전차단기', 'LOTO', '이중 절연',
        '활선 금지', '접지', '절연', '전원차단',
    ],
    '질식': [
        '가스농도 측정', '환기 실시', '송기마스크', '공기호흡기',
        '감시인 배치', '산소농도', '환기',
    ],
    '화재': [
        '소화기 비치', '소화기', '화기 통제', '화기 금지',
        '가연물 제거', '방화포', '불티 방지', '잔불 확인',
    ],
    '폭발': [
        '가스농도 측정', '가스 탐지', '가스 차단', '환기', '방폭',
        '점화원 제거', '가스 농도',
    ],
    '낙하': [
        '낙하물 방지망', '신호수 배치', '작업 반경', '출입 통제',
        '낙하 방지', '신호수',
    ],
    '충돌': [
        '신호수 배치', '신호수', '작업 반경 통제', '출입 통제',
        '경보 장치', '반경 통제',
    ],
    '붕괴': [
        '동바리 점검', '거푸집 점검', '흙막이 설치', '해체 순서',
        '해체 계획', '흙막이', '동바리',
    ],
    '협착': [
        '방호 덮개', '잠금장치', 'LOTO', '비상 정지', '방호장치',
    ],
    '절단': [
        '방호 덮개', '보호대 착용', '방호장치', '덮개 설치',
    ],
    '중독': [
        'MSDS 확인', '방독마스크 착용', '환기 실시', '보호구 착용',
        '긴급 샤워', 'MSDS',
    ],
}


def _split_field(value: Optional[str]) -> List[str]:
    """Split comma/semicolon-delimited field into list, strip each item."""
    if not value:
        return []
    parts = []
    for part in value.replace(';', ',').replace('·', ',').split(','):
        p = part.strip()
        if p:
            parts.append(p)
    return parts


def _dedup_ordered(items: List[str]) -> List[str]:
    """Remove duplicates preserving order; case-insensitive; substring suppression."""
    seen_norm = []
    result = []
    for item in items:
        norm = normalize_text(item).lower()
        dominated = any(
            norm == s or norm in s or s in norm
            for s in seen_norm
        )
        if not dominated:
            seen_norm.append(norm)
            result.append(item)
    return result


def _dedup_actions(items: List[str]) -> List[str]:
    """
    v1.2: Less aggressive dedup specifically for action phrases.

    Unlike _dedup_ordered, short keywords (< 10 chars normalized) are NOT
    suppressed by longer phrases that happen to contain them. This prevents
    hazard-reinforced short keywords (e.g. '소화기', '환기') from being
    swallowed by long extracted phrases.
    """
    seen_norm = []
    result = []
    for item in items:
        norm = normalize_text(item).lower()
        skip = False
        for s in seen_norm:
            if norm == s:
                skip = True
                break
            # Only suppress if the NEW item (>= 10 chars) is a substring of existing
            if len(norm) >= 10 and norm in s:
                skip = True
                break
        if not skip:
            seen_norm.append(norm)
            result.append(item)
    return result


def _extract_action_phrases(text: str) -> List[str]:
    """
    v1.2: Sliding-window action phrase extractor.

    Changes from v1.1:
    - Sentence-level splitting (.\\n!?) before soft clause splitting
    - Sliding window: WIN_BEFORE chars of context captured before each verb
    - Hard cap at MAX_PHRASE_LEN (50 chars) — prevents full-sentence noise
    - At most one phrase per sentence (first matching verb wins)
    """
    if not text:
        return []

    phrases = []
    for sent in re.split(r'[.。\n!?]', text):
        sent = sent.strip()
        if len(sent) < _MIN_PHRASE_LEN + 3:
            continue

        for verb in _ACTION_VERBS:
            idx = sent.rfind(verb)
            if idx <= _MIN_PHRASE_LEN:
                continue

            # Sliding window: up to WIN_BEFORE chars before the verb
            win_start = max(0, idx - _WIN_BEFORE)
            window = sent[win_start: idx + len(verb)]

            # Trim leading soft-boundary noise within window
            m = list(re.finditer(r'[,·•\-\*\|\s]{2,}', window))
            if m:
                window = window[m[-1].end():]

            # Strip leading numbers/bullets
            window = re.sub(r'^[\d\.\)\s]+', '', window).strip()

            if len(window) >= _MIN_PHRASE_LEN:
                phrase = window[:_MAX_PHRASE_LEN].strip()
                if phrase:
                    phrases.append(phrase)
                    break  # one phrase per sentence

    return phrases


def _hazard_keyed_actions(
    chunks: List[Dict[str, Any]],
    hazards: List[str],
) -> List[str]:
    """
    v1.2: Scan matched chunks for hazard-specific action keywords.

    Returns only keywords actually present in chunk texts (no hallucination).
    Ordered by hazard priority then keyword list order.
    """
    if not hazards:
        return []

    all_text = ' '.join(
        (c.get('normalized_text') or c.get('raw_text') or '')
        for c in chunks
    )

    found: List[str] = []
    for hazard in hazards[:4]:
        for kw in _HAZARD_ACTION_KEYWORDS.get(hazard, []):
            if kw in all_text and kw not in found:
                found.append(kw)

    return found


def _is_generic_action(text: str) -> bool:
    stripped = text.strip()
    return stripped in _GENERIC_ACTIONS or len(stripped) <= 2


# ── Hazard assembly ─────────────────────────────────────────────────────────

def _hazard_frequency_specific(chunks: List[Dict[str, Any]]) -> List[str]:
    freq: Dict[str, int] = {}
    for c in chunks:
        ht = (c.get('hazard_type') or '').strip()
        if ht and ht not in GENERIC_HAZARD_TAGS:
            freq[ht] = freq.get(ht, 0) + 1
    return [k for k, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)]


def assemble_hazards(chunks: List[Dict[str, Any]]) -> List[str]:
    """
    primary_hazards: text-classifier results (primary) + specific tags (secondary).
    v1.2: unchanged — hazard accuracy 100%, no regression allowed.
    """
    specific_tags = _hazard_frequency_specific(chunks)

    classifier_freq: Dict[str, int] = {}
    for c in chunks:
        text = (c.get('normalized_text') or c.get('raw_text') or '')
        for label in classify_hazard_from_text(text):
            classifier_freq[label] = classifier_freq.get(label, 0) + 1

    classifier_ordered = [
        k for k, _ in sorted(classifier_freq.items(), key=lambda x: x[1], reverse=True)
    ]

    combined = classifier_ordered + [t for t in specific_tags if t not in classifier_ordered]
    return _dedup_ordered(combined)[:5]


# ── Action assembly ─────────────────────────────────────────────────────────

def assemble_actions(
    chunks: List[Dict[str, Any]],
    hazards: Optional[List[str]] = None,
) -> List[str]:
    """
    recommended_actions: phrase-based extraction with hazard reinforcement.

    v1.2 priority order:
    1. Hazard-keyed reinforcement keywords (from chunk texts, prepended)
    2. Multi-word control_measure items from tagged chunks (>= 5 chars, not generic)
    3. Sliding-window phrases from tagged chunk texts
    4. Same from untagged chunks
    5. Single-word fallback items (filtered)

    Args:
        chunks:  matched KOSHA chunks
        hazards: detected hazard labels; enables v1.2 reinforcement
    """
    reinforced = _hazard_keyed_actions(chunks, hazards or [])

    def _process_chunk(c: dict) -> tuple[List[str], List[str]]:
        good, fallback = [], []
        for part in _split_field(c.get('control_measure')):
            if len(part) >= 5 and not _is_generic_action(part):
                good.append(part)
            elif not _is_generic_action(part):
                fallback.append(part)

        text = c.get('normalized_text') or c.get('raw_text') or ''
        for phrase in _extract_action_phrases(text):
            if not _is_generic_action(phrase):
                good.append(phrase)

        return good, fallback

    tagged_good, tagged_fb = [], []
    untagged_good, untagged_fb = [], []

    for c in chunks:
        good, fb = _process_chunk(c)
        has_tags = bool(c.get('work_type') or c.get('hazard_type'))
        if has_tags:
            tagged_good.extend(good)
            tagged_fb.extend(fb)
        else:
            untagged_good.extend(good)
            untagged_fb.extend(fb)

    combined = reinforced + tagged_good + untagged_good + tagged_fb + untagged_fb
    return _dedup_actions(combined)[:8]


# ── PPE assembly (unchanged) ────────────────────────────────────────────────

def assemble_ppe(chunks: List[Dict[str, Any]]) -> List[str]:
    all_ppe = []
    for c in chunks:
        all_ppe.extend(_split_field(c.get('ppe')))
    return _dedup_ordered(all_ppe)[:6]


# ── Legal assembly (unchanged) ──────────────────────────────────────────────

def assemble_legal(chunks: List[Dict[str, Any]]) -> List[str]:
    all_refs = []
    for c in chunks:
        parts = _split_field(c.get('law_ref'))
        all_refs.extend(parts)
    return _dedup_ordered(all_refs)[:5]


# ── Confidence (unchanged) ──────────────────────────────────────────────────

def calculate_confidence(
    chunks: List[Dict[str, Any]],
    scores: List[float],
) -> Literal['low', 'medium', 'high']:
    if not chunks or not scores:
        return 'low'

    top_scores = scores[:3]
    avg_top = sum(top_scores) / len(top_scores)

    tagged = sum(1 for c in chunks if c.get('work_type') or c.get('hazard_type'))
    tag_ratio = tagged / len(chunks) if chunks else 0.0

    has_control = any(c.get('control_measure') for c in chunks)

    if avg_top >= 5.0 and tag_ratio >= 0.6 and has_control:
        return 'high'
    if avg_top < 1.5 or tag_ratio < 0.25:
        return 'low'
    return 'medium'


# ── Warnings ────────────────────────────────────────────────────────────────

def build_warnings(
    chunks: List[Dict[str, Any]],
    legal: List[str],
    confidence: str,
) -> List[str]:
    warnings = []

    if not chunks:
        warnings.append('검색 결과 없음: 입력 텍스트와 매칭되는 KOSHA 청크가 없습니다.')
        return warnings

    if not legal:
        warnings.append('법령 근거 없음: law_ref가 있는 청크가 검색되지 않았습니다.')

    tagless = [c for c in chunks if not c.get('work_type') and not c.get('hazard_type')]
    if len(tagless) > len(chunks) * 0.5:
        warnings.append(
            f'태그 미비: 상위 결과 {len(tagless)}/{len(chunks)}건이 분류 태그 없는 청크입니다. '
            'confidence가 낮아집니다.'
        )

    wt_values = [c.get('work_type') or '' for c in chunks if c.get('work_type')]
    if wt_values:
        dominant = max(set(wt_values), key=wt_values.count)
        ratio = wt_values.count(dominant) / len(wt_values)
        if ratio > 0.7 and dominant in ('설치', '기타', '작업'):
            warnings.append(
                f"work_type 편향: '{dominant}' 유형이 {ratio:.0%}로 과다 비중입니다. "
                '결과를 참고용으로만 활용하세요.'
            )

    if confidence == 'low':
        warnings.append('검색 품질 낮음: 쿼리와 강하게 매칭되는 청크가 부족합니다.')

    return warnings


# ── Reasoning notes ──────────────────────────────────────────────────────────

def build_reasoning_notes(
    inp_summary: str,
    chunks: List[Dict[str, Any]],
    scores: List[float],
    hazards: List[str],
    confidence: str,
) -> List[str]:
    notes = [f'쿼리 요약: {inp_summary}']

    if chunks:
        top_score = scores[0] if scores else 0
        notes.append(f'상위 청크 BM25+보너스 점수: {top_score:.2f}')

        tagged = sum(1 for c in chunks if c.get('work_type') or c.get('hazard_type'))
        notes.append(f'태그 보유 청크 비율: {tagged}/{len(chunks)}')

    if hazards:
        notes.append(f'감지된 위험 유형: {", ".join(hazards)}')

    notes.append(f'confidence 판정: {confidence}')
    return notes

"""
BM25 retrieval engine — pure Python, no external dependencies.
Indexes normalized_text + structured fields; applies field bonus weights.
"""

import re
import math
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

# Korean/common stopwords (do not contribute to scoring)
_STOPWORDS = frozenset([
    '및', '또는', '의', '을', '를', '이', '가', '은', '는', '에', '에서', '으로', '로',
    '와', '과', '도', '만', '에게', '으로부터', '하여', '하고', '하는', '한', '할', '함',
    '등', '것', '수', '때', '후', '전', '중', '이후', '이전', '위해', '위한', '따라',
    '경우', '때문', '통해', '대해', '관련', '해당', '위', '아래', '내', '외',
    '있다', '없다', '된다', '한다', '이다', '다', '고', '며', '면', '서', '시',
    '않다', '않는', '없는', '있는', '되는', '해야', '해서', '하면', '하지',
    '그리고', '그러나', '하지만', '따라서', '또한', '즉', '단', '항상',
])

# Minimum text length to avoid noise chunks (characters)
NOISE_THRESHOLD = 50

# BM25 hyperparameters
BM25_K1 = 1.5
BM25_B = 0.75

# Field bonus weights added on top of BM25 score
FIELD_BONUS = {
    'work_type_match': 2.0,
    'hazard_type_match': 2.5,
    'ppe_present': 0.5,
    'law_ref_present': 1.0,
    'control_measure_present': 0.5,
    'no_tags_penalty': -1.0,
    'noise_multiplier': 0.2,  # applied as multiplier, not addition
}


def normalize_text(text: str) -> str:
    if not text:
        return ''
    text = re.sub(r'[^\w\s가-힣a-zA-Z0-9]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def tokenize(text: str) -> List[str]:
    """Word tokens + Korean character bigrams for subword coverage."""
    normalized = normalize_text(text)
    words = [w for w in normalized.split() if len(w) >= 2 and w not in _STOPWORDS]
    bigrams = []
    for word in words:
        if len(word) >= 2:
            for i in range(len(word) - 1):
                bg = word[i:i + 2]
                # skip pure-digit bigrams
                if not bg.isdigit():
                    bigrams.append(bg)
    return words + bigrams


def _chunk_doc_text(chunk: Dict[str, Any]) -> str:
    """Combine all searchable fields into one document string."""
    parts = [
        chunk.get('normalized_text') or chunk.get('raw_text') or '',
        chunk.get('work_type') or '',
        chunk.get('hazard_type') or '',
        chunk.get('control_measure') or '',
        chunk.get('ppe') or '',
        chunk.get('law_ref') or '',
    ]
    kw = chunk.get('keywords')
    if isinstance(kw, list):
        parts.extend(str(k) for k in kw)
    elif isinstance(kw, str):
        parts.append(kw)
    return ' '.join(p for p in parts if p)


class BM25Index:
    """In-memory BM25 index over a list of KOSHA chunk dicts."""

    def __init__(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            raise ValueError('청크 데이터가 비어 있습니다.')
        self.chunks = chunks
        self.n = len(chunks)
        self._tf: List[Counter] = []
        self._dl: List[int] = []
        self._df: Dict[str, int] = defaultdict(int)
        self._avgdl: float = 0.0
        self._build()

    def _build(self):
        total = 0
        for chunk in self.chunks:
            tokens = tokenize(_chunk_doc_text(chunk))
            tf = Counter(tokens)
            self._tf.append(tf)
            dl = len(tokens)
            self._dl.append(dl)
            total += dl
            for term in tf:
                self._df[term] += 1
        self._avgdl = total / self.n if self.n else 1.0

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        return math.log((self.n - df + 0.5) / (df + 0.5) + 1.0)

    def _bm25_score(self, query_tokens: List[str], doc_idx: int) -> float:
        tf = self._tf[doc_idx]
        dl = self._dl[doc_idx]
        score = 0.0
        for term in set(query_tokens):
            if term not in self._df:
                continue
            tf_val = tf.get(term, 0)
            idf = self._idf(term)
            denom = tf_val + BM25_K1 * (1 - BM25_B + BM25_B * dl / self._avgdl)
            if denom > 0:
                score += idf * tf_val * (BM25_K1 + 1) / denom
        return score

    def _field_bonus(self, query_lower: str, doc_idx: int) -> float:
        chunk = self.chunks[doc_idx]
        bonus = 0.0

        wt = normalize_text(chunk.get('work_type') or '').lower()
        ht = normalize_text(chunk.get('hazard_type') or '').lower()

        if wt and wt in query_lower:
            bonus += FIELD_BONUS['work_type_match']
        if ht and ht in query_lower:
            bonus += FIELD_BONUS['hazard_type_match']
        if chunk.get('ppe'):
            bonus += FIELD_BONUS['ppe_present']
        if chunk.get('law_ref'):
            bonus += FIELD_BONUS['law_ref_present']
        if chunk.get('control_measure'):
            bonus += FIELD_BONUS['control_measure_present']
        if not wt and not ht:
            bonus += FIELD_BONUS['no_tags_penalty']

        return bonus

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Returns list of (chunk_index, score) sorted descending by score.
        Applies noise penalty to short chunks.
        Only returns results with score > 0.
        """
        q_tokens = tokenize(query)
        q_lower = normalize_text(query).lower()

        results = []
        for i in range(self.n):
            base = self._bm25_score(q_tokens, i)
            bonus = self._field_bonus(q_lower, i)
            total = base + bonus

            # Noise penalty: chunks shorter than threshold
            text = self.chunks[i].get('normalized_text') or self.chunks[i].get('raw_text') or ''
            if len(text) < NOISE_THRESHOLD:
                total *= FIELD_BONUS['noise_multiplier']

            # Require at least some text token match (base > 0).
            # Field bonuses alone (ppe/law_ref presence) are not sufficient.
            if base > 0:
                results.append((i, total))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

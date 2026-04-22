"""문장 정제 샘플 v2 생성기 (2026-04-23)

v1 대비 변경점
  - 주어 사전 확장 + 4단계 상속(P1 direct / P2 split_group / P3 prev_same_title / P4 kosha default)
  - duplicate 탐지(Q10) 초안 구현: 같은 doc_id 내 action+object alias 그룹 기반
  - split 규칙 확대: 동사 쌍 화이트리스트 + 지급·착용 주체 재할당
  - object 복원 보강: alias 사전 + split_group 상속

입력
  - data/risk_db/master/sentence_labeling_sample_v2.csv
  - data/risk_db/master/controls_master_draft_v2.csv
  - data/risk_db/master/sentence_normalization_sample_v1.csv  (비교용)

출력
  - data/risk_db/master/sentence_normalization_sample_v2.csv
  - data/risk_db/master/sentence_normalization_diff_v1_v2.csv

원칙: 원문 보존 / 임의 확정 금지 / duplicate 자동 삭제 금지 / DB 반영 없음.
"""
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/risk_db/master/sentence_labeling_sample_v2.csv"
CTRL_SRC = ROOT / "data/risk_db/master/controls_master_draft_v2.csv"
V1_NORM = ROOT / "data/risk_db/master/sentence_normalization_sample_v1.csv"
OUT_NORM = ROOT / "data/risk_db/master/sentence_normalization_sample_v2.csv"
OUT_DIFF = ROOT / "data/risk_db/master/sentence_normalization_diff_v1_v2.csv"

# ---------- 사전 ----------

# (키워드, subject_code) — 길이 긴 패턴 우선
SUBJECT_LEXICON: List[Tuple[str, str]] = [
    # 복수 결합(길이 긴 것 우선 매칭)
    ("사업주 또는 경영책임자등", "employer"),
    ("법인 또는 기관의 경영책임자등", "employer"),
    ("원수급인 또는 하수급인", "contractor"),
    ("관할청", "authority"),
    ("관계 행정기관의 장", "authority"),
    ("지방자치단체의 장", "authority"),
    # 법령 주체
    ("경영책임자등", "employer"),
    ("원수급인", "contractor"),
    ("하수급인", "contractor"),
    ("도급인", "contractor"),
    ("수급인", "contractor"),
    ("사업주", "employer"),
    ("현장소장", "supervisor"),
    ("관리감독자", "supervisor"),
    ("작업지휘자", "supervisor"),
    ("안전관리자", "safety_manager"),
    ("보건관리자", "safety_manager"),
    ("근로자", "worker"),
    ("작업자", "worker"),
    ("운전자", "worker"),
    ("점검자", "worker"),
    ("사용부서", "worker"),
    # 행정/사법/기관
    ("고용노동부장관", "authority"),
    ("국토교통부장관", "authority"),
    ("법무부장관", "authority"),
    ("소방본부장", "authority"),
    ("소방서장", "authority"),
    ("건설근로자공제회", "authority"),
    ("공제회", "authority"),
    ("공제조합", "authority"),
    ("공단", "authority"),
    ("협회", "authority"),
    ("사업주단체", "authority"),
    ("정부", "authority"),
    ("법원", "judicial"),
    ("검사", "judicial"),
    ("피고인", "judicial"),
    ("변호인", "judicial"),
    ("이사회", "board"),
    ("이사장", "board"),
    # 회사·조직
    ("회사", "workplace"),
    ("사업장", "workplace"),
    ("작업장", "workplace"),
    # 관리자 일반
    ("관리자", "supervisor"),
]

# object alias 그룹: 대표 코드 -> 변형 리스트
OBJECT_ALIAS_GROUPS = {
    "안전모": ["안전모", "헬멧"],
    "안전대": ["안전대", "안전벨트", "안전그네"],
    "안전화": ["안전화", "작업화"],
    "보안경": ["보안경", "고글", "보호안경"],
    "보호구": ["보호구", "개인보호구", "PPE"],
    "방진마스크": ["방진마스크"],
    "방독마스크": ["방독마스크"],
    "호흡보호구": ["호흡보호구", "송기마스크"],
    "귀마개": ["귀마개", "귀덮개"],
    "보호복": ["보호복", "내화학복", "내열복"],
    "안전난간": ["안전난간", "안전난간대", "난간"],
    "작업발판": ["작업발판", "발판"],
    "개구부 덮개": ["개구부 덮개", "덮개"],
    "안전방망": ["안전방망", "추락방호망"],
    "국소배기장치": ["국소배기장치", "LEV", "국소배기", "후드"],
    "방호장치": ["방호장치", "가드", "안전덮개", "인터록", "과부하방지장치"],
    "비계": ["비계", "이동식비계", "시스템비계"],
    "크레인": ["크레인", "이동식 크레인", "타워크레인"],
    "호이스트": ["호이스트"],
    "승강기": ["승강기"],
    "리프트": ["리프트"],
    "고소작업대": ["고소작업대"],
    "사다리": ["사다리"],
    "분전반": ["분전반"],
    "누전차단기": ["누전차단기", "ELCB"],
    "전동공구": ["전동공구"],
    "용접기": ["용접기"],
    "작업계획서": ["작업계획서", "작업계획", "작업순서서"],
    "MSDS": ["MSDS", "물질안전보건자료", "안전보건자료"],
    "경고표지": ["경고표지", "경고표시"],
    "관리대장": ["관리대장"],
    "점검표": ["점검표", "체크리스트"],
    "작업허가서": ["작업허가서", "허가서", "PTW"],
    "기록부": ["기록부"],
    "특별안전보건교육": ["특별안전보건교육", "특별교육", "안전보건교육", "안전교육"],
    "TBM": ["TBM"],
    "감시인": ["감시인", "감시자"],
    "신호수": ["신호수"],
    "유도자": ["유도자", "유도원"],
}

# object 검색 사전: (변형, 대표 code)
OBJECT_LEXICON: List[Tuple[str, str]] = []
for canonical, aliases in OBJECT_ALIAS_GROUPS.items():
    for a in sorted(aliases, key=len, reverse=True):
        OBJECT_LEXICON.append((a, canonical))

ACTION_MAP = [
    (r"설치", "install"),
    (r"점검", "inspect"),
    (r"검사", "inspect"),
    (r"측정", "measure"),
    (r"착용", "wear"),
    (r"지급", "provide"),
    (r"비치", "provide"),
    (r"게시", "post"),
    (r"작성", "prepare"),
    (r"준비", "prepare"),
    (r"기록", "record"),
    (r"보고", "report"),
    (r"신고", "report"),
    (r"교육", "train"),
    (r"훈련", "train"),
    (r"환기", "ventilate"),
    (r"청소", "clean"),
    (r"제거", "clean"),
    (r"보관", "store"),
    (r"저장", "store"),
    (r"격리", "isolate"),
    (r"차단", "isolate"),
    (r"폐쇄", "isolate"),
    (r"출입\s*(금지|통제|제한)", "prohibit_access"),
    (r"감시", "monitor"),
    (r"유지", "maintain"),
    (r"정비", "maintain"),
]

CONDITION_TRIGGERS = [
    (r"\d+\s*[mM미터]\s*이상", "height_work"),
    (r"\d+\s*[tT톤]\s*이상", "quantity_threshold"),
    (r"\d+\s*명\s*이상", "legal_scope"),
    (r"밀폐공간|산소결핍", "confined_space"),
    (r"양중|인양|들어올리는", "lifting_operation"),
    (r"충전전로|활선|전기", "electrical_work"),
    (r"용접|용단|화기작업", "hot_work"),
    (r"강풍|폭염|우천|한랭", "weather_environment"),
    (r"혼재작업|동시작업|복수\s*사업주", "simultaneous_work"),
    (r"매일|매월|매주|6개월마다|연\s*1회|정기적", "periodic_schedule"),
    (r"작업\s*시작\s*전|작업\s*종료\s*후|작업\s*전|작업\s*후", "before_after_work"),
    (r"재해\s*발생\s*시|사고\s*발생\s*시|화재\s*발생\s*시", "incident_emergency"),
    (r"관리대상|특별관리|유해[·・]?위험물질", "hazardous_substance"),
]

HAZARD_LEXICON = [
    ("추락", "추락"), ("낙하", "비래낙하"), ("비래", "비래낙하"),
    ("감전", "감전"), ("질식", "질식"), ("끼임", "끼임"),
    ("협착", "끼임"), ("절단", "절단"), ("화재", "화재"),
    ("폭발", "폭발"), ("화상", "화상"), ("분진", "분진"),
    ("소음", "소음진동"), ("진동", "소음진동"),
]

EQUIPMENT_LEXICON = [
    ("안전난간", "EQ_HANDRAIL"),
    ("작업발판", "EQ_WORK_PLATFORM"),
    ("이동식비계", "EQ_MOVSCAFF"),
    ("비계", "EQ_SCAFF"),
    ("이동식 크레인", "EQ_CRANE_MOB"),
    ("크레인", "EQ_CRANE_MOB"),
    ("호이스트", "EQ_HOIST"),
    ("고소작업대", "EQ_AWP"),
    ("사다리", "EQ_LADDER_MOV"),
    ("국소배기장치", "EQ_LEV"),
    ("방호장치", "EQ_GUARD"),
    ("분전반", "EQ_DIST_PANEL"),
    ("누전차단기", "EQ_ELCB"),
    ("용접기", "EQ_WELDER_ARC"),
]

VAGUE_REMOVE = [
    "적절한", "적절히", "적절하게",
    "충분한", "충분히",
    "안전하게", "확실히", "철저히",
]
VAGUE_FLAG_PHRASES = [
    "필요한 조치", "필요한 경우",
    "이상이 없도록",
    "노력하여야",
    "조치한다", "관리한다",
]

NOISE_SOLO_LEXICON = [
    "참고하세요", "자세한 내용", "일반정보",
    "본 물질은", "물리화학적", "증상", "질병",
    "중요하다", "바람직하다",
    "교육미디어", "OPL 참고",
    "다음과 같다",
]
MSDS_FORMULAIC_MARKS = [
    "본 물질은", "물리화학적", "증상이 나타",
    "MSDS 를 참고", "MSDS를 참고",
]

OBLIG_SIGNALS = [
    "하여야 한다", "해야 한다", "갖추어야",
    "금지", "해서는 아니", "해서는 안",
    "지급", "착용", "설치", "점검", "측정",
    "교육", "게시", "비치", "허가", "대피",
    "감시", "작성", "신고", "보고",
]

NOISE_RECOVERY_COMBOS = [
    (["보호구", "안전모", "안전대", "보안경", "방진마스크", "방독마스크", "귀마개"], ["착용", "지급"], "wear", "rule_core"),
    (["환기"], ["실시", "가동", "확인"], "ventilate", "rule_core"),
    (["저장", "보관"], ["분리", "격리"], "store", "rule_core"),
    (["점검"], ["매일", "매월", "주기", "6개월", "연 1회", "정기"], "inspect", "rule_core"),
    (["측정"], ["값", "기준", "주기"], "measure", "rule_core"),
    (["대피"], ["경로", "집결지"], "isolate", "rule_core"),
    (["허가"], ["작업", "진입", "발급"], "prepare", "rule_core"),
    (["감시인", "감시자"], ["배치", "지정"], "monitor", "rule_core"),
    (["유도자", "유도원"], ["배치", "지정"], "monitor", "rule_core"),
    (["출입"], ["금지", "통제", "제한"], "prohibit_access", "rule_core"),
    (["작업지휘자"], ["지정", "배치"], "monitor", "rule_core"),
]

EVIDENCE_PATTERNS = [
    r"제\s*\d+\s*조(에 따라|에 의하여|의 규정에 따라)",
    r"별표\s*\d+",
    r"같은\s*법\s*제\s*\d+\s*조",
    r"이\s*규칙\s*제\s*\d+\s*조",
    r"(고시|훈령)\s*제\s*\d+\s*호",
]

# ---------- 함수들 ----------

def load_controls() -> List[Dict]:
    rows = []
    with CTRL_SRC.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def build_control_index(controls: List[Dict]) -> List[Tuple[str, List[str]]]:
    idx = []
    for c in controls:
        kws = [k.strip() for k in (c.get("typical_keywords") or "").split("|") if k.strip()]
        if kws:
            idx.append((c["control_code"], kws))
    return idx


def header_strip(text: str) -> Tuple[str, Optional[str]]:
    evidence = None
    text = re.sub(r"<\s*(개정|신설|시행)\s*[^>]+>", "", text).strip()
    m = re.match(r"^\s*제\s*\d+\s*조(의?\s*\d+)?\s*(\([^)]+\))?", text)
    if m:
        evidence = m.group(0).strip()
        text = text[m.end():].strip()
    text = re.sub(r"^[①-⑳㉑-㉟]+\s*", "", text).strip()
    text = re.sub(r"^\d+\)\s*", "", text).strip()
    text = re.sub(r"^[가-하]\.\s*", "", text).strip()
    return text, evidence


def is_incomplete(text: str) -> bool:
    t = text.strip()
    if len(t) < 4:
        return True
    words = t.split()
    if len(words) <= 3 and not re.search(r"(한다|이다)$", t):
        return True
    if re.fullmatch(r"[가-하]\.|\d+\.|[①-⑳]+", t):
        return True
    return False


def is_evidence_only(text: str) -> bool:
    has_ref = any(re.search(p, text) for p in EVIDENCE_PATTERNS)
    if not has_ref:
        return False
    action_verbs = ["설치", "점검", "측정", "착용", "지급", "교육", "작성", "게시", "비치",
                     "신고", "보고", "허가", "대피"]
    if any(v in text for v in action_verbs):
        return False
    return True


def extract_evidence(text: str) -> Optional[str]:
    for p in EVIDENCE_PATTERNS:
        m = re.search(p, text)
        if m:
            return m.group(0)
    return None


def has_obligation_signal(text: str) -> bool:
    return any(sig in text for sig in OBLIG_SIGNALS)


def has_numeric_threshold(text: str) -> bool:
    return bool(re.search(r"\d+\s*(m|미터|톤|t|kg|%|ppm|dB|명|건)", text))


def detect_noise(text: str, v2_sentence_type: str = "") -> Tuple[bool, bool]:
    is_msds = any(m in text for m in MSDS_FORMULAIC_MARKS)
    if (v2_sentence_type or "").strip().lower() == "descriptive_noise":
        return True, is_msds
    if has_obligation_signal(text):
        return False, False
    if has_numeric_threshold(text):
        return False, False
    solo_hit = any(w in text for w in NOISE_SOLO_LEXICON)
    if solo_hit or is_msds:
        return True, is_msds
    return False, False


def noise_recover(text: str) -> Optional[Tuple[str, str]]:
    for anchors, combos, action, role in NOISE_RECOVERY_COMBOS:
        if any(a in text for a in anchors) and any(c in text for c in combos):
            return action, role
    return None


# -------- split v2 --------

SPLIT_VERB_PAIRS = [
    # 의미 연결이 자연스러운 동사쌍 (화이트리스트)
    ("설치", "점검"),
    ("비치", "게시"),
    ("작성", "게시"),
    ("작성", "비치"),
    ("지급", "착용"),  # 주체 재할당 별도
    ("점검", "측정"),
    ("설치", "비치"),
]

# (설치, 운영) 등은 split 금지
SPLIT_FORBIDDEN_PAIRS = {("설치", "운영"), ("관리", "감독"), ("유지", "정비")}


def split_complex_sentence(text: str) -> Tuple[List[str], List[str], str]:
    """복합 문장 split. 반환: (pieces, subject_override_list, split_confidence)

    subject_override_list: 각 piece 에 대응하는 subject override (None 이면 상속 시도).
    """
    t_stripped = text.strip()

    # 0) "A하고 있는지" 상태 확인 표현은 분해 금지
    if re.search(r"(설치|점검|측정|착용|지급|비치|게시|작성|기록|교육)하고\s+(있는지|있는|있을|있었)", t_stripped):
        return [text], [None], "high"

    # 1) 지급·착용 패턴 (주체 재할당)
    m = re.match(r"^(.*?보호구(?:[^,。.!?]*))\s*(를|을)\s*지급하(고|여)\s+(.+?)착용(?:하게\s*)?(하여야\s*한다|해야\s*한다|한다)\.?$", t_stripped)
    if m:
        obj = m.group(1).strip()
        tail = m.group(5).strip()
        piece_1 = f"사업주는 {obj}를 지급하여야 한다."
        piece_2 = f"근로자는 {obj}를 착용{tail}."
        return [piece_1, piece_2], ["employer", "worker"], "medium"

    # 2) "A하고 B한다" 범용 분해 (v1 유연성 유지 + FORBIDDEN 패턴만 제외)
    #    첫 동사는 주요 행위 동사, 두번째 동사는 열린 종결.
    pat_general = re.compile(
        r"^(.*?)(설치|점검|측정|착용|지급|비치|게시|작성|기록|교육|보관|배치|지정)하(고|여)\s+(.+?(하여야 한다|해야 한다|한다|하여야 하며|하여야 함))\.?$"
    )
    m = pat_general.match(t_stripped)
    if m:
        prefix = m.group(1).strip()
        v1 = m.group(2)
        right_whole = m.group(4).strip()
        # 두번째 동사 어근 추출(앞쪽 8자 이내)
        second_verb_m = re.match(r"^(.*?)(설치|점검|측정|착용|지급|비치|게시|작성|기록|교육|보관|배치|지정|운영|관리|감독|유지|정비)", right_whole)
        v2_verb = second_verb_m.group(2) if second_verb_m else ""
        pair = (v1, v2_verb)
        if pair in SPLIT_FORBIDDEN_PAIRS:
            # 의미 결합이 큰 경우 split 하지 않음
            pass
        else:
            p1 = f"{prefix}{v1}하여야 한다.".strip()
            # 두번째 piece 는 right_whole 을 그대로 사용하되, prefix 의 주어 부분만 상속
            # 주어 명사구를 prefix 앞쪽에서 추출해 right_whole 앞에 붙임
            subj_prefix_m = re.match(r"^(.{0,40}?[은는이가에게]\s)", prefix)
            subj_prefix = subj_prefix_m.group(1) if subj_prefix_m else ""
            p2 = (subj_prefix + right_whole).strip()
            if not p2.endswith("."):
                p2 += "."
            return [p1, p2], [None, None], "medium"

    # 3) "A·B·C 를 …한다" 열거
    enum_m = re.match(r"^(.*?)([가-힣\s]+?[·・、])([가-힣\s]+?[·・、])([가-힣\s]+?)(을|를)\s*(.+?(하여야 한다|한다)\.?)$", t_stripped)
    if enum_m:
        prefix = enum_m.group(1).strip()
        a = enum_m.group(2).strip(" ·・、")
        b = enum_m.group(3).strip(" ·・、")
        c = enum_m.group(4).strip()
        particle = enum_m.group(5)
        tail = enum_m.group(6).strip()
        items = [a, b, c]
        parts = []
        for it in items:
            if prefix:
                parts.append(f"{prefix} {it}{particle} {tail}".strip())
            else:
                parts.append(f"{it}{particle} {tail}".strip())
        return parts, [None] * len(parts), "high"

    # 4) "A 및 B 를 … 한다"
    m2 = re.match(r"^([가-힣]+)\s*및\s*([가-힣]+)(을|를)\s*(.+?(하여야 한다|한다)\.?)$", t_stripped)
    if m2:
        a = m2.group(1).strip()
        b = m2.group(2).strip()
        particle = m2.group(3)
        tail = m2.group(4).strip()
        parts = [f"{a}{particle} {tail}".strip(),
                 f"{b}{particle} {tail}".strip()]
        return parts, [None, None], "high"

    # 5) 조건/규칙 분리 "~인 경우 …하여야 한다"
    cond_m = re.match(r"^(.+?(인 경우|할 때|인 때에는|시에는|인 때|의 경우))\s+(.+?(하여야 한다|한다|해야 한다|금지한다)\.?)$", t_stripped)
    if cond_m:
        cond = cond_m.group(1).strip()
        rule = cond_m.group(3).strip()
        return [cond + " (조건)", rule], [None, None], "low"

    return [text], [None], "high"


def vague_normalize(text: str) -> Tuple[str, List[str], bool]:
    types: List[str] = []
    ambiguity = False
    out = text
    for word in VAGUE_REMOVE:
        if word in out:
            out = re.sub(rf"\s*{word}\s*", " ", out)
            out = re.sub(r"\s+", " ", out).strip()
            types.append("vague_remove")
    for phrase in VAGUE_FLAG_PHRASES:
        if phrase in out:
            ambiguity = True
            types.append("vague_flag")
            break
    seen = set()
    out_types = []
    for t in types:
        if t not in seen:
            seen.add(t)
            out_types.append(t)
    return out, out_types, ambiguity


# -------- 주어/객체 추론 (v2) --------

def infer_subject_direct(text: str) -> Optional[str]:
    """문장 내 주어 direct 탐지. 길이 긴 패턴 우선."""
    for kw, code in SUBJECT_LEXICON:
        # 조사 결합
        if re.search(rf"{re.escape(kw)}\s*(은|는|이|가|에게|에서|으로부터|과|와)", text):
            return code
    # 단독 주어(조사 없는 경우) — 문두에만
    for kw, code in SUBJECT_LEXICON:
        if text.strip().startswith(kw):
            return code
    return None


def infer_object_direct(text: str) -> Optional[str]:
    for alias, canonical in OBJECT_LEXICON:
        if alias in text:
            return canonical
    return None


def infer_action(text: str) -> Optional[str]:
    for pat, code in ACTION_MAP:
        if re.search(pat, text):
            return code
    return None


def infer_condition(text: str) -> Optional[str]:
    for pat, code in CONDITION_TRIGGERS:
        if re.search(pat, text):
            return code
    return None


def infer_hazard(text: str) -> Optional[str]:
    for kw, code in HAZARD_LEXICON:
        if kw in text:
            return code
    return None


def infer_equipment(text: str) -> Optional[str]:
    for kw, code in EQUIPMENT_LEXICON:
        if kw in text:
            return code
    return None


def infer_control(text: str, ctrl_idx: List[Tuple[str, List[str]]]) -> Optional[str]:
    for code, kws in ctrl_idx:
        if any(k in text for k in kws):
            return code
    return None


def detect_context_required(text: str) -> bool:
    markers = ["이 경우", "그 밖에", "같은 조", "해당 ", "위 항", "앞 각"]
    return any(m in text for m in markers)


# -------- duplicate 탐지 (v2) --------

def normalize_for_compare(text: str) -> str:
    t = re.sub(r"\s+", "", text)
    t = re.sub(r"[·・、,，。.!?()\[\]'\"\"\"]+", "", t)
    return t


def tokenize_for_jaccard(text: str) -> set:
    """어절 기반 토큰."""
    t = re.sub(r"[·・、,，。.!?()\[\]]", " ", text)
    return set(x for x in t.split() if x)


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------- 메인 파이프라인 ----------

def build_row_v2(**kw) -> Dict:
    return {
        "normalized_sentence_id": f"{kw['sid']}-{kw['order']:02d}",
        "source_sentence_id": kw["sid"],
        "source_type": kw["src"],
        "document_id": kw["doc_id"],
        "document_title": kw["title"],
        "raw_sentence_text": kw["raw"],
        "normalized_sentence_text": kw["norm"],
        "normalization_status": kw["status"],
        "split_group_id": kw["sid"],
        "split_order": kw["order"],
        "was_split": int(kw["was_split"]),
        "split_confidence": kw.get("split_confidence", ""),
        "normalization_type": kw["norm_types"],
        "sentence_role": kw["role"],
        "obligation_level_candidate": kw["obligation"] or "",
        "subject_candidate": kw["subject"] or "",
        "subject_candidate_direct": kw.get("subject_direct", "") or "",
        "subject_candidate_inherited": kw.get("subject_inherited", "") or "",
        "subject_candidate_confidence": kw.get("subject_conf", "") or "",
        "inherited_subject_from": kw.get("subject_from", "") or "",
        "object_candidate": kw["obj"] or "",
        "object_candidate_direct": kw.get("obj_direct", "") or "",
        "object_candidate_inherited": kw.get("obj_inherited", "") or "",
        "object_candidate_confidence": kw.get("obj_conf", "") or "",
        "action_candidate": kw["action"] or "",
        "condition_candidate": kw["cond"] or "",
        "hazard_candidate": kw["hazard"] or "",
        "equipment_candidate": kw["equipment"] or "",
        "control_candidate": kw["control"] or "",
        "evidence_candidate": kw["evidence"] or "",
        "noise_flag": int(bool(kw["noise"])),
        "noise_recovery_candidate": int(bool(kw["noise_recover"])),
        "ambiguity_flag": int(bool(kw["ambiguity"])),
        "context_required_flag": int(bool(kw["context_req"])),
        "duplicate_flag": 0,
        "duplicate_type": "",
        "canonical_candidate": 1,
        "duplicate_of": "",
        "duplicate_group_id": "",
        "quality_issue_codes": kw["q_codes"],
        "confidence": kw["conf"],
        "normalization_note": kw["note"],
        "reviewer_note": "",
    }


def process(rows: List[Dict], controls: List[Dict]) -> Tuple[List[Dict], Dict]:
    ctrl_idx = build_control_index(controls)
    normalized_rows: List[Dict] = []
    metrics = Counter()
    q_counter = Counter()
    role_counter = Counter()

    # pass 1: 각 행 처리 (direct 복원 + split)
    for r in rows:
        sid = r["sample_id"]
        raw = r["sentence_text"]
        doc_id = r.get("document_id", "")
        src = r.get("source_type", "")
        title = r.get("document_title", "")

        metrics["total_samples"] += 1

        stripped, evidence_from_header = header_strip(raw)
        types_applied: List[str] = []
        if evidence_from_header or stripped != raw.strip():
            types_applied.append("header_strip")

        # incomplete
        if is_incomplete(stripped):
            metrics["incomplete"] += 1
            q_counter["Q11"] += 1
            role_counter["metadata"] += 1
            normalized_rows.append(build_row_v2(
                sid=sid, order=1, raw=raw, norm=stripped or raw,
                role="metadata", status="auto",
                was_split=False, split_confidence="high",
                norm_types=",".join(types_applied + ["no_change"]),
                subject=None, subject_direct=None, subject_inherited=None, subject_conf="unresolved", subject_from="",
                obj=None, obj_direct=None, obj_inherited=None, obj_conf="unresolved",
                action=None, cond=None,
                hazard=None, equipment=None, control=None,
                evidence=evidence_from_header,
                noise=True, noise_recover=False, ambiguity=False,
                context_req=False, q_codes="Q11", conf="low",
                note="incomplete",
                src=src, doc_id=doc_id, title=title,
                obligation=None,
            ))
            continue

        # evidence only
        if is_evidence_only(stripped):
            ev = extract_evidence(stripped) or evidence_from_header
            q_counter["Q08"] += 1
            role_counter["evidence"] += 1
            metrics["evidence_only"] += 1
            normalized_rows.append(build_row_v2(
                sid=sid, order=1, raw=raw, norm=stripped,
                role="evidence", status="auto",
                was_split=False, split_confidence="high",
                norm_types=",".join(types_applied + ["evidence_isolate"]),
                subject=None, subject_direct=None, subject_inherited=None, subject_conf="unresolved", subject_from="",
                obj=None, obj_direct=None, obj_inherited=None, obj_conf="unresolved",
                action=None, cond=None,
                hazard=None, equipment=None, control=None,
                evidence=ev,
                noise=False, noise_recover=False, ambiguity=False,
                context_req=detect_context_required(stripped),
                q_codes="Q08", conf="medium",
                note="evidence_only",
                src=src, doc_id=doc_id, title=title,
                obligation="informative",
            ))
            continue

        noise_flag, is_msds = detect_noise(stripped, r.get("sentence_type_candidate", ""))
        noise_recover_result = None
        if noise_flag:
            noise_recover_result = noise_recover(stripped)

        pieces, subject_overrides, split_conf = split_complex_sentence(stripped)
        was_split = len(pieces) > 1
        if was_split:
            metrics["split_applied"] += 1
            types_applied.append("split_action")

        order = 0
        for idx, piece in enumerate(pieces):
            order += 1
            piece_types = list(types_applied)
            normalized_piece, vague_types, amb_flag = vague_normalize(piece)
            piece_types.extend(vague_types)

            # 주어 direct
            subj_direct = subject_overrides[idx] if subject_overrides[idx] else infer_subject_direct(normalized_piece)
            subj_inherited = None
            subj_from = ""
            subj_conf = "unresolved"
            if subj_direct:
                subj_conf = "direct_high"
            # 추후 pass 2에서 inheritance 처리

            # 객체 direct
            obj_direct = infer_object_direct(normalized_piece)
            obj_inherited = None
            obj_conf = "unresolved"
            if obj_direct:
                obj_conf = "direct"
                piece_types.append("object_infer")

            subject = subj_direct
            obj = obj_direct

            action = infer_action(normalized_piece)
            cond = infer_condition(normalized_piece)
            hazard = infer_hazard(normalized_piece)
            equipment = infer_equipment(normalized_piece)
            ctrl = infer_control(normalized_piece, ctrl_idx)

            piece_noise = noise_flag
            piece_noise_recover_cand = False
            role = "rule_core"
            q_codes: List[str] = []

            if noise_flag and "(조건)" not in normalized_piece:
                if noise_recover_result:
                    piece_noise_recover_cand = True
                    role = noise_recover_result[1]
                    if not action:
                        action = noise_recover_result[0]
                    piece_types.append("noise_recover")
                    q_codes.append("Q05")
                    if is_msds:
                        q_codes.append("Q09")
                else:
                    role = "explanation"
                    piece_types.append("noise_mark")
                    q_codes.append("Q05")
                    if is_msds:
                        q_codes.append("Q09")

            if "(조건)" in normalized_piece:
                role = "condition"
                normalized_piece = normalized_piece.replace(" (조건)", "").strip()
                q_codes.append("Q06")
            elif not noise_flag:
                sent_type = r.get("sentence_type_candidate", "")
                if sent_type == "scope_exclusion":
                    role = "exception"
                elif sent_type == "definition":
                    role = "explanation"
                elif sent_type == "legal_reference":
                    role = "evidence"
                elif sent_type == "descriptive_noise":
                    role = "explanation"
                elif sent_type == "condition_trigger":
                    role = "condition"
                else:
                    if has_obligation_signal(normalized_piece):
                        role = "rule_core"
                    elif hazard and not action:
                        role = "hazard_statement"
                    else:
                        role = "rule_core"

            if was_split:
                q_codes.append("Q01")
            if amb_flag:
                q_codes.append("Q04")
            # Q02/Q03 는 pass 2 에서 재계산 (상속 후)
            if hazard and (action or ctrl) and "위험" in normalized_piece:
                q_codes.append("Q07")
            ctx_req = detect_context_required(normalized_piece)
            if ctx_req:
                q_codes.append("Q12")

            if piece_noise_recover_cand or amb_flag or ctx_req:
                conf = "low"
            elif role == "metadata" or role == "evidence":
                conf = "medium"
            elif subject and obj and not amb_flag and role == "rule_core":
                conf = "high"
            else:
                conf = "medium"

            if role == "exception":
                obligation = "exception"
            elif role == "rule_core":
                if "금지" in normalized_piece or "해서는 아니" in normalized_piece:
                    obligation = "prohibited"
                elif "하여야 한다" in normalized_piece or "해야 한다" in normalized_piece:
                    obligation = "mandatory"
                else:
                    obligation = "informative"
            elif role == "explanation":
                obligation = "informative"
            else:
                obligation = None

            seen = set()
            pt_out = []
            for t in piece_types:
                if t not in seen:
                    seen.add(t)
                    pt_out.append(t)
            if not pt_out:
                pt_out = ["no_change"]

            seen = set()
            q_out = []
            for q in q_codes:
                if q not in seen:
                    seen.add(q)
                    q_out.append(q)

            if "vague_remove" in pt_out:
                metrics["vague_remove"] += 1
            if "vague_flag" in pt_out:
                metrics["vague_flag"] += 1
            if "noise_mark" in pt_out:
                metrics["noise_marked"] += 1
            if "noise_recover" in pt_out:
                metrics["noise_recovered"] += 1
            if ctrl:
                metrics["control_candidate"] += 1

            ev = extract_evidence(stripped) or evidence_from_header
            normalized_rows.append(build_row_v2(
                sid=sid, order=order, raw=raw, norm=normalized_piece,
                role=role, status="auto" if conf != "low" else "auto_flagged",
                was_split=was_split, split_confidence=split_conf,
                norm_types=",".join(pt_out),
                subject=subject, subject_direct=subj_direct, subject_inherited=subj_inherited, subject_conf=subj_conf,
                subject_from=subj_from,
                obj=obj, obj_direct=obj_direct, obj_inherited=obj_inherited, obj_conf=obj_conf,
                action=action, cond=cond,
                hazard=hazard, equipment=equipment, control=ctrl,
                evidence=ev,
                noise=piece_noise and not piece_noise_recover_cand,
                noise_recover=piece_noise_recover_cand,
                ambiguity=amb_flag,
                context_req=ctx_req,
                q_codes=",".join(q_out),
                conf=conf,
                note="",
                src=src, doc_id=doc_id, title=title,
                obligation=obligation,
            ))

    # ---- pass 2: 주어 상속 ----
    # index: split_group 별 order=1 direct 주어 / prev_same_title 체인
    group_order1_subject: Dict[str, Optional[str]] = {}
    for nr in normalized_rows:
        if nr["split_order"] == 1 and nr["subject_candidate_direct"]:
            group_order1_subject[nr["split_group_id"]] = nr["subject_candidate_direct"]

    prev_subject_by_title: Dict[Tuple[str, str], Tuple[str, str]] = {}
    #   key: (document_id, document_title) -> (subject_code, prev_normalized_sentence_id)

    for nr in normalized_rows:
        doc_id = str(nr["document_id"])
        title = nr["document_title"]
        key = (doc_id, title)

        if nr["subject_candidate_direct"]:
            # direct 존재 시 prev 갱신
            prev_subject_by_title[key] = (nr["subject_candidate_direct"], nr["normalized_sentence_id"])
            continue

        # 상속 금지 조건
        if nr["sentence_role"] in {"metadata", "evidence", "exception"}:
            continue

        # P2: split_group 의 order=1
        group_id = nr["split_group_id"]
        if group_id in group_order1_subject and nr["split_order"] != 1:
            subj = group_order1_subject[group_id]
            nr["subject_candidate_inherited"] = subj
            nr["subject_candidate"] = subj
            nr["subject_candidate_confidence"] = "inherited_split"
            nr["inherited_subject_from"] = f"split_group:order=1"
            nr["normalization_type"] = _add_type(nr["normalization_type"], "subject_inherit_split")
            metrics["subject_inherited_split"] += 1
            continue

        # P3: 같은 document_title 의 직전 direct 주어
        if key in prev_subject_by_title:
            subj_code, src_id = prev_subject_by_title[key]
            # 직전 문장이 설명/정의/메타이면 상속 금지 (해당 sentence_role 을 prev_subject_by_title 에 저장하지 않기 때문에 이미 필터링됨)
            nr["subject_candidate_inherited"] = subj_code
            nr["subject_candidate"] = subj_code
            nr["subject_candidate_confidence"] = "inherited_prev"
            nr["inherited_subject_from"] = f"prev:{src_id}"
            nr["normalization_type"] = _add_type(nr["normalization_type"], "subject_inherit_prev")
            metrics["subject_inherited_prev"] += 1
            continue

        # P4: kosha default (rule_core 만, noise/explanation 제외)
        if nr["source_type"] == "kosha" and nr["sentence_role"] in {"rule_core", "control_statement"}:
            nr["subject_candidate_inherited"] = "worker"
            nr["subject_candidate"] = "worker"
            nr["subject_candidate_confidence"] = "default_kosha_worker"
            nr["inherited_subject_from"] = "default:kosha_worker"
            nr["normalization_type"] = _add_type(nr["normalization_type"], "subject_default_kosha")
            metrics["subject_default_kosha"] += 1
            continue

        # 실패
        # (필드 기본값이 unresolved)

    # ---- pass 2b: object 상속 (split_group order=1 기반) ----
    group_order1_object: Dict[str, Optional[str]] = {}
    for nr in normalized_rows:
        if nr["split_order"] == 1 and nr["object_candidate_direct"]:
            group_order1_object[nr["split_group_id"]] = nr["object_candidate_direct"]

    for nr in normalized_rows:
        if nr["object_candidate_direct"]:
            continue
        if nr["sentence_role"] in {"metadata", "evidence"}:
            continue
        group_id = nr["split_group_id"]
        if group_id in group_order1_object and nr["split_order"] != 1:
            obj = group_order1_object[group_id]
            nr["object_candidate_inherited"] = obj
            nr["object_candidate"] = obj
            nr["object_candidate_confidence"] = "inherited_split"
            nr["normalization_type"] = _add_type(nr["normalization_type"], "object_inherit_split")
            metrics["object_inherited_split"] += 1

    # ---- pass 3: duplicate 탐지 ----
    # 같은 doc_id 내에서 action + object(대표 alias) + role + obligation 동일 그룹핑
    dup_groups: Dict[Tuple, List[int]] = defaultdict(list)
    for idx, nr in enumerate(normalized_rows):
        if nr["sentence_role"] not in {"rule_core", "control_statement"}:
            continue
        # action_candidate 와 object_candidate 모두 있어야 중복 그룹화.
        # action 없이 object 만 같으면 설명문의 단순 반복일 가능성이 커 over-grouping 위험.
        if not nr["action_candidate"] or not nr["object_candidate"]:
            continue
        key = (
            str(nr["document_id"]),
            nr["action_candidate"],
            nr["object_candidate"],
            nr["obligation_level_candidate"],
        )
        dup_groups[key].append(idx)

    group_counter = 0
    for key, idx_list in dup_groups.items():
        if len(idx_list) < 2:
            continue
        # 세부 분류: exact / near / same_control_variant / same_rule_different_surface
        # 버킷 내 페어링을 한번에 처리
        texts = [normalized_rows[i]["normalized_sentence_text"] for i in idx_list]
        controls = [normalized_rows[i]["control_candidate"] for i in idx_list]
        norms = [normalize_for_compare(t) for t in texts]

        # canonical 선정
        # 우선 direct + !ambiguity + !noise + 최단 길이
        best_idx = idx_list[0]
        best_score = None
        for i in idx_list:
            nr = normalized_rows[i]
            score = (
                0 if nr["subject_candidate_confidence"] == "direct_high" else 1,
                int(nr["ambiguity_flag"]),
                int(nr["noise_flag"]),
                len(nr["normalized_sentence_text"]),
                nr["normalized_sentence_id"],
            )
            if best_score is None or score < best_score:
                best_score = score
                best_idx = i
        canonical_id = normalized_rows[best_idx]["normalized_sentence_id"]

        group_counter += 1
        dg_id = f"DG{group_counter:04d}"

        for i in idx_list:
            nr = normalized_rows[i]
            # duplicate 유형 판정 (canonical 과의 관계)
            if i == best_idx:
                dup_type = ""
                nr["canonical_candidate"] = 1
                nr["duplicate_flag"] = 1
                nr["duplicate_of"] = ""
                nr["duplicate_group_id"] = dg_id
                # Q10 추가
                if "Q10" not in (nr["quality_issue_codes"] or ""):
                    qc = [q for q in nr["quality_issue_codes"].split(",") if q]
                    qc.append("Q10")
                    nr["quality_issue_codes"] = ",".join(qc)
                continue

            c_norm = normalize_for_compare(normalized_rows[best_idx]["normalized_sentence_text"])
            i_norm = norms[idx_list.index(i)]
            if c_norm == i_norm:
                dup_type = "exact_duplicate"
            else:
                a = tokenize_for_jaccard(normalized_rows[best_idx]["normalized_sentence_text"])
                b = tokenize_for_jaccard(nr["normalized_sentence_text"])
                j = jaccard(a, b)
                same_ctrl = (normalized_rows[best_idx]["control_candidate"] ==
                             nr["control_candidate"] and nr["control_candidate"])
                if j >= 0.8:
                    dup_type = "near_duplicate"
                elif same_ctrl:
                    dup_type = "same_control_variant"
                else:
                    dup_type = "same_rule_different_surface"

            nr["duplicate_flag"] = 1
            nr["duplicate_type"] = dup_type
            nr["canonical_candidate"] = 0
            nr["duplicate_of"] = canonical_id
            nr["duplicate_group_id"] = dg_id
            qc = [q for q in nr["quality_issue_codes"].split(",") if q]
            if "Q10" not in qc:
                qc.append("Q10")
                nr["quality_issue_codes"] = ",".join(qc)
            metrics[f"dup_{dup_type}"] += 1

        metrics["dup_groups"] += 1

    # ---- pass 4: Q02/Q03 재계산 (최종 subject/object 기준) ----
    # role_counter/q_counter 는 pass 1 의 조기 분기(incomplete/evidence)에서 일부 누적되었으므로
    # 재집계는 여기서 **리셋 후** 일괄 수행한다.
    role_counter.clear()
    q_counter.clear()
    metrics["rule_core"] = 0
    metrics["subject_direct"] = 0
    metrics["object_direct"] = 0

    for nr in normalized_rows:
        qc = [q for q in nr["quality_issue_codes"].split(",") if q and q != "Q02" and q != "Q03"]
        if not nr["subject_candidate"]:
            qc.append("Q02")
        if not nr["object_candidate"] and nr["action_candidate"] in {"install", "inspect", "wear", "provide", "prepare", "monitor", "train"}:
            qc.append("Q03")
        # dedupe
        seen = set()
        out = []
        for q in qc:
            if q not in seen:
                seen.add(q)
                out.append(q)
        nr["quality_issue_codes"] = ",".join(out)

        # 집계
        role_counter[nr["sentence_role"]] += 1
        for q in out:
            q_counter[q] += 1
        if nr["sentence_role"] == "rule_core":
            metrics["rule_core"] += 1
        if nr["subject_candidate_direct"]:
            metrics["subject_direct"] += 1
        if nr["object_candidate_direct"]:
            metrics["object_direct"] += 1

    return normalized_rows, metrics | Counter({"q_" + k: v for k, v in q_counter.items()}) | Counter({"role_" + k: v for k, v in role_counter.items()})


def _add_type(types_csv: str, new_type: str) -> str:
    parts = [t for t in types_csv.split(",") if t]
    if new_type not in parts:
        parts.append(new_type)
    return ",".join(parts) if parts else new_type


FIELDS_V2 = [
    "normalized_sentence_id", "source_sentence_id", "source_type",
    "document_id", "document_title",
    "raw_sentence_text", "normalized_sentence_text",
    "normalization_status", "split_group_id", "split_order",
    "was_split", "split_confidence", "normalization_type",
    "sentence_role", "obligation_level_candidate",
    "subject_candidate", "subject_candidate_direct",
    "subject_candidate_inherited", "subject_candidate_confidence",
    "inherited_subject_from",
    "object_candidate", "object_candidate_direct",
    "object_candidate_inherited", "object_candidate_confidence",
    "action_candidate", "condition_candidate",
    "hazard_candidate", "equipment_candidate",
    "control_candidate", "evidence_candidate",
    "noise_flag", "noise_recovery_candidate",
    "ambiguity_flag", "context_required_flag",
    "duplicate_flag", "duplicate_type",
    "canonical_candidate", "duplicate_of", "duplicate_group_id",
    "quality_issue_codes", "confidence",
    "normalization_note", "reviewer_note",
]


DIFF_FIELDS = [
    "sample_id",
    "raw_sentence_text",
    "normalized_sentence_text_v1",
    "normalized_sentence_text_v2",
    "subject_candidate_v1",
    "subject_candidate_v2",
    "subject_candidate_confidence_v2",
    "object_candidate_v1",
    "object_candidate_v2",
    "duplicate_flag_v2",
    "duplicate_type_v2",
    "was_split_v1",
    "was_split_v2",
    "control_candidate_v1",
    "control_candidate_v2",
    "changed_fields",
    "reviewer_note",
]


def load_v1() -> Dict[str, List[Dict]]:
    by_source: Dict[str, List[Dict]] = defaultdict(list)
    if not V1_NORM.exists():
        return by_source
    with V1_NORM.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            by_source[r["source_sentence_id"]].append(r)
    return by_source


def main() -> None:
    rows = []
    with SRC.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    controls = load_controls()

    norm_rows, metrics = process(rows, controls)

    with OUT_NORM.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS_V2)
        w.writeheader()
        for r in norm_rows:
            # 일부 필드가 row 에 없으면 빈 문자열
            for k in FIELDS_V2:
                r.setdefault(k, "")
            w.writerow(r)

    # diff 생성
    v1_by_src = load_v1()
    # v2 도 source_sentence_id 기준 첫 piece 로 대표
    v2_by_src: Dict[str, List[Dict]] = defaultdict(list)
    for r in norm_rows:
        v2_by_src[r["source_sentence_id"]].append(r)

    with OUT_DIFF.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=DIFF_FIELDS)
        w.writeheader()
        for sid in sorted(v2_by_src.keys()):
            v2_pieces = v2_by_src[sid]
            v1_pieces = v1_by_src.get(sid, [])
            v1_head = v1_pieces[0] if v1_pieces else {}
            v2_head = v2_pieces[0]
            # join pieces
            v2_norm_text = " ||| ".join(p["normalized_sentence_text"] for p in v2_pieces)
            v1_norm_text = " ||| ".join(p["normalized_sentence_text"] for p in v1_pieces)
            changed = []
            # subject
            v1_subj = v1_head.get("subject_candidate", "")
            v2_subj = v2_head.get("subject_candidate", "")
            if v1_subj != v2_subj:
                changed.append("subject")
            v1_obj = v1_head.get("object_candidate", "")
            v2_obj = v2_head.get("object_candidate", "")
            if v1_obj != v2_obj:
                changed.append("object")
            v1_split = v1_head.get("was_split", "")
            v2_split = str(v2_head.get("was_split", ""))
            if v1_split != v2_split:
                changed.append("split")
            v1_ctrl = v1_head.get("control_candidate", "")
            v2_ctrl = v2_head.get("control_candidate", "")
            if v1_ctrl != v2_ctrl:
                changed.append("control")
            dup_flag = any(p["duplicate_flag"] for p in v2_pieces)
            dup_types = ",".join(sorted({p["duplicate_type"] for p in v2_pieces if p["duplicate_type"]}))
            if dup_flag:
                changed.append("duplicate")

            w.writerow({
                "sample_id": sid,
                "raw_sentence_text": v2_head["raw_sentence_text"],
                "normalized_sentence_text_v1": v1_norm_text,
                "normalized_sentence_text_v2": v2_norm_text,
                "subject_candidate_v1": v1_subj,
                "subject_candidate_v2": v2_subj,
                "subject_candidate_confidence_v2": v2_head.get("subject_candidate_confidence", ""),
                "object_candidate_v1": v1_obj,
                "object_candidate_v2": v2_obj,
                "duplicate_flag_v2": int(dup_flag),
                "duplicate_type_v2": dup_types,
                "was_split_v1": v1_split,
                "was_split_v2": v2_split,
                "control_candidate_v1": v1_ctrl,
                "control_candidate_v2": v2_ctrl,
                "changed_fields": ",".join(changed),
                "reviewer_note": "",
            })

    # stdout summary
    print("=== 문장 정제 v2 샘플 생성 결과 ===")
    print(f"- 입력 샘플 수: {metrics.get('total_samples', 0)}")
    print(f"- 정제 문장 수 (split 포함): {len(norm_rows)}")
    print(f"- split 적용 원문 수: {metrics.get('split_applied', 0)}")
    print(f"- vague_remove 적용: {metrics.get('vague_remove', 0)}")
    print(f"- vague_flag(ambiguity) 적용: {metrics.get('vague_flag', 0)}")
    print(f"- 주어 direct: {metrics.get('subject_direct', 0)}")
    print(f"- 주어 inherited(split_group): {metrics.get('subject_inherited_split', 0)}")
    print(f"- 주어 inherited(prev_same_title): {metrics.get('subject_inherited_prev', 0)}")
    print(f"- 주어 default(kosha worker): {metrics.get('subject_default_kosha', 0)}")
    print(f"- 대상 direct: {metrics.get('object_direct', 0)}")
    print(f"- 대상 inherited(split_group): {metrics.get('object_inherited_split', 0)}")
    print(f"- noise 표시: {metrics.get('noise_marked', 0)}")
    print(f"- noise 복구 후보: {metrics.get('noise_recovered', 0)}")
    print(f"- incomplete(metadata): {metrics.get('incomplete', 0)}")
    print(f"- evidence_only: {metrics.get('evidence_only', 0)}")
    print(f"- control_candidate 부여: {metrics.get('control_candidate', 0)}")
    print(f"- rule_core 역할: {metrics.get('rule_core', 0)}")
    print(f"- duplicate 그룹: {metrics.get('dup_groups', 0)}")
    for k in ["exact_duplicate", "near_duplicate", "same_control_variant", "same_rule_different_surface"]:
        print(f"    dup_{k}: {metrics.get('dup_' + k, 0)}")
    print("- sentence_role 분포:")
    for k in ["rule_core", "condition", "evidence", "explanation",
              "hazard_statement", "control_statement", "exception",
              "metadata", "unresolved"]:
        print(f"    {k}: {metrics.get('role_' + k, 0)}")
    print("- 품질 이슈 코드 분포:")
    for q in ["Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07",
              "Q08", "Q09", "Q10", "Q11", "Q12"]:
        print(f"    {q}: {metrics.get('q_' + q, 0)}")
    print(f"OUT : {OUT_NORM}")
    print(f"DIFF: {OUT_DIFF}")


if __name__ == "__main__":
    main()

"""문장 정제 샘플 생성기 (v0.1)

입력
  - data/risk_db/master/sentence_labeling_sample_v2.csv (800 샘플)
  - data/risk_db/master/controls_master_draft_v2.csv (control 사전용)

파이프라인(sentence_normalization_rules.md § 1)
  header_strip → incomplete_check → evidence_check →
  noise_check → split_decide → vague_normalize →
  subject_infer → object_infer → role_assign → flag_set → confidence_set

출력
  - data/risk_db/master/sentence_normalization_sample_v1.csv
  - data/risk_db/master/sentence_normalization_diff_sample.csv
  - 표준출력: 품질 지표 요약

원칙
  - 원문 보존 (raw_sentence_text 유지).
  - subject/object 는 candidate 만, 자동 확정 금지.
  - noise 는 복구 후보만 플래그, 자동 삭제 금지.
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
OUT_NORM = ROOT / "data/risk_db/master/sentence_normalization_sample_v1.csv"
OUT_DIFF = ROOT / "data/risk_db/master/sentence_normalization_diff_sample.csv"

# ---------- 사전 ----------

SUBJECT_LEXICON = [
    ("원수급인", "contractor"),
    ("하수급인", "contractor"),
    ("도급인", "contractor"),
    ("수급인", "contractor"),
    ("사업주", "employer"),
    ("관리감독자", "supervisor"),
    ("작업지휘자", "supervisor"),
    ("안전관리자", "safety_manager"),
    ("보건관리자", "safety_manager"),
    ("근로자", "worker"),
    ("작업자", "worker"),
    ("고용노동부장관", "authority"),
    ("사업장", "workplace"),
    ("작업장", "workplace"),
]

OBJECT_LEXICON = [
    # 장비/설비
    "안전난간", "작업발판", "국소배기장치", "환기장치", "방호장치",
    "과부하방지장치", "안전방망", "추락방호망", "비계", "크레인",
    "호이스트", "승강기", "리프트", "고소작업대", "사다리",
    "분전반", "누전차단기", "전동공구", "용접기", "용단기",
    # 보호구
    "안전모", "안전대", "보안경", "안전화", "방진마스크",
    "방독마스크", "호흡보호구", "내화학장갑", "귀마개", "귀덮개",
    "보호복", "보호구",
    # 문서
    "작업계획서", "MSDS", "물질안전보건자료", "경고표지", "관리대장",
    "점검표", "작업허가서", "허가서", "기록부",
    # 행위 노무
    "특별안전보건교육", "안전보건교육", "안전교육", "TBM",
]

ACTION_MAP = [
    # (동사 어근 regex, action_code, object_hint_keywords)
    (r"설치", "install", []),
    (r"점검", "inspect", []),
    (r"검사", "inspect", []),
    (r"측정", "measure", []),
    (r"착용", "wear", ["보호구", "안전모", "안전대", "보안경", "방진마스크", "방독마스크", "안전화", "귀마개"]),
    (r"지급", "provide", ["보호구", "안전모", "안전대"]),
    (r"비치", "provide", []),
    (r"게시", "post", ["경고표지", "표지", "MSDS"]),
    (r"작성", "prepare", ["작업계획서", "서류", "MSDS"]),
    (r"준비", "prepare", []),
    (r"기록", "record", []),
    (r"보고", "report", []),
    (r"신고", "report", []),
    (r"교육", "train", []),
    (r"훈련", "train", []),
    (r"환기", "ventilate", []),
    (r"청소", "clean", []),
    (r"제거", "clean", []),
    (r"보관", "store", []),
    (r"저장", "store", []),
    (r"격리", "isolate", []),
    (r"차단", "isolate", []),
    (r"폐쇄", "isolate", []),
    (r"출입\s*(금지|통제|제한)", "prohibit_access", []),
    (r"감시", "monitor", []),
    (r"유지", "maintain", []),
    (r"정비", "maintain", []),
]

# 조건 trigger 사전
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
    ("비계", "EQ_SCAFF"),
    ("이동식비계", "EQ_MOVSCAFF"),
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

# 추상 표현
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

# noise 판정
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

# noise 복구 신호 (키워드 조합)
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

# evidence 패턴
EVIDENCE_PATTERNS = [
    r"제\s*\d+\s*조(에 따라|에 의하여|의 규정에 따라)",
    r"별표\s*\d+",
    r"같은\s*법\s*제\s*\d+\s*조",
    r"이\s*규칙\s*제\s*\d+\s*조",
    r"(고시|훈령)\s*제\s*\d+\s*호",
]

# control master index
def load_controls() -> List[Dict]:
    rows = []
    with CTRL_SRC.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


# ---------- 정제 파이프라인 ----------

def header_strip(text: str) -> Tuple[str, Optional[str]]:
    """조문 번호/장절 헤더 제거. 반환: (정제문, evidence 토큰 or None)."""
    evidence = None
    # <개정 …> / <신설 …>
    text = re.sub(r"<\s*(개정|신설|시행)\s*[^>]+>", "", text).strip()
    # 제X조(제목)
    m = re.match(r"^\s*제\s*\d+\s*조(의?\s*\d+)?\s*(\([^)]+\))?", text)
    if m:
        evidence = m.group(0).strip()
        text = text[m.end():].strip()
    # 문두 ①②③ 연속
    text = re.sub(r"^[①-⑳㉑-㉟]+\s*", "", text).strip()
    # 문두 숫자)
    text = re.sub(r"^\d+\)\s*", "", text).strip()
    # 문두 가. / 나. / 3. 단독이 아니면 제거
    text = re.sub(r"^[가-하]\.\s*", "", text).strip()
    return text, evidence


def is_incomplete(text: str) -> bool:
    t = text.strip()
    if len(t) < 4:
        return True
    words = t.split()
    if len(words) <= 3 and not re.search(r"(한다|이다)$", t):
        return True
    # 순수 항 번호만
    if re.fullmatch(r"[가-하]\.|\d+\.|[①-⑳]+", t):
        return True
    return False


def is_evidence_only(text: str) -> bool:
    has_ref = any(re.search(p, text) for p in EVIDENCE_PATTERNS)
    if not has_ref:
        return False
    # 실체 의무 동사 결합 검사
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
    """(noise_flag, is_msds_formulaic)

    판정 우선순위:
      1) v2 에서 이미 descriptive_noise 로 라벨된 문장은 1차 noise 로 채택.
      2) 그 외 자체 detect 규칙(NOISE_SOLO_LEXICON / MSDS 상투).
    """
    is_msds = any(m in text for m in MSDS_FORMULAIC_MARKS)
    # v2 label 우선
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
    """noise 복구 후보. 반환: (action_code, sentence_role) or None."""
    for anchors, combos, action, role in NOISE_RECOVERY_COMBOS:
        if any(a in text for a in anchors) and any(c in text for c in combos):
            return action, role
    return None


def split_complex_sentence(text: str) -> List[str]:
    """복합 문장 split.

    지원 패턴:
      - "A하고 B하여야 한다" → [A하여야 한다, B하여야 한다]
      - "A·B·C 를 …" → [A 를 …, B 를 …, C 를 …]
      - "A 및 B/A 또는 B" → [A, B] (단, 동사 결합 필요)
    """
    # 단순 "하고" 분리
    parts: List[str] = []

    # 1) "~하고 ~하여야 한다" / "~하여 ~한다" 분리
    #    단, "~하고 있는지", "~하고 있는" 등 상태 확인/진행 표현은 분해하지 않는다.
    t_stripped = text.strip()
    if re.search(r"(설치|점검|측정|착용|지급|비치|게시|작성|기록|교육)하고\s+(있는지|있는|있을|있었)", t_stripped):
        return [text]
    m = re.match(r"^(.*?)(설치|점검|측정|착용|지급|비치|게시|작성|기록|교육)하고\s+(.+?(하여야 한다|한다|하여야 하며|하여야 함)\.?)$", t_stripped)
    if m:
        left_obj = m.group(1).strip()
        v1 = m.group(2)
        right = m.group(3).strip()
        first = f"{left_obj}{v1}하여야 한다." if not left_obj.endswith(('을', '를')) and left_obj else f"{left_obj} {v1}하여야 한다."
        if left_obj:
            first = f"{left_obj} {v1}하여야 한다."
        else:
            first = f"{v1}하여야 한다."
        parts = [first.strip(), right.strip()]
        return parts

    # 2) 열거 "A·B·C를 ~한다"
    enum_m = re.match(r"^(.*?)([가-힣\s]+?[·・、])([가-힣\s]+?[·・、])([가-힣\s]+?)(을|를)\s*(.+?(하여야 한다|한다)\.?)$", text.strip())
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
        return parts

    # 3) "A 및 B" 만 split (또는 은 주어 or-관계 오분해 위험이 커 제외)
    #    게다가 prefix 가 있으면 split 하지 않음(문장 앞쪽에 다른 명사가 있으면 의미 손실)
    m2 = re.match(r"^([가-힣]+)\s*및\s*([가-힣]+)(을|를)\s*(.+?(하여야 한다|한다)\.?)$", text.strip())
    if m2:
        a = m2.group(1).strip()
        b = m2.group(2).strip()
        particle = m2.group(3)
        tail = m2.group(4).strip()
        parts = [f"{a}{particle} {tail}".strip(),
                 f"{b}{particle} {tail}".strip()]
        return parts

    # 4) 조건/규칙 분리 "~인 경우 …하여야 한다"
    cond_m = re.match(r"^(.+?(인 경우|할 때|인 때에는|시에는|인 때|의 경우))\s+(.+?(하여야 한다|한다|해야 한다|금지한다)\.?)$", text.strip())
    if cond_m:
        cond = cond_m.group(1).strip()
        rule = cond_m.group(3).strip()
        return [cond + " (조건)", rule]

    return [text]


def vague_normalize(text: str) -> Tuple[str, List[str], bool]:
    """추상 표현 정규화. 반환: (정제문, 적용 타입 리스트, ambiguity_flag)."""
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
    # 동일 type 중복 제거
    seen = set()
    out_types = []
    for t in types:
        if t not in seen:
            seen.add(t)
            out_types.append(t)
    return out, out_types, ambiguity


def infer_subject(text: str, inherited: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """주어 후보 복원. (subject_code, normalization_type_or_None)."""
    for kw, code in SUBJECT_LEXICON:
        # 문장 선두 + 조사 매칭 가산
        if re.search(rf"{kw}(은|는|이|가|에게|에서)", text):
            return code, None
    # 문장 내부 주어 명사가 있지만 선두 조사 결합이 아닐 때는 약하게 reject
    if inherited:
        return inherited, "subject_infer"
    return None, None


def infer_object(text: str) -> Optional[str]:
    for obj in OBJECT_LEXICON:
        if obj in text:
            return obj
    return None


def infer_action(text: str) -> Optional[str]:
    for pat, code, _ in ACTION_MAP:
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


# control 후보 매핑: controls_master_draft_v2 의 typical_keywords 로 단순 contains 매칭
def build_control_index(controls: List[Dict]) -> List[Tuple[str, List[str]]]:
    idx = []
    for c in controls:
        kws = [k.strip() for k in (c.get("typical_keywords") or "").split("|") if k.strip()]
        if kws:
            idx.append((c["control_code"], kws))
    return idx


def infer_control(text: str, ctrl_idx: List[Tuple[str, List[str]]]) -> Optional[str]:
    for code, kws in ctrl_idx:
        if any(k in text for k in kws):
            return code
    return None


def detect_context_required(text: str) -> bool:
    markers = ["이 경우", "그 밖에", "같은 조", "해당 ", "위 항", "앞 각"]
    return any(m in text for m in markers)


# ---------- 메인 ----------

def process(rows: List[Dict], controls: List[Dict]) -> Tuple[List[Dict], List[Dict], Dict]:
    ctrl_idx = build_control_index(controls)
    normalized_rows: List[Dict] = []
    diff_rows: List[Dict] = []

    # subject 상속을 위해 direct 선행 문장의 confirmed subject 추적
    last_subject_by_doc: Dict[str, str] = {}

    metrics = Counter()
    q_counter = Counter()
    role_counter = Counter()

    for r in rows:
        sid = r["sample_id"]
        raw = r["sentence_text"]
        doc_id = r.get("document_id", "")
        src = r.get("source_type", "")
        title = r.get("document_title", "")

        metrics["total_samples"] += 1

        # 1) header_strip
        stripped, evidence_from_header = header_strip(raw)
        types_applied: List[str] = []
        if evidence_from_header or stripped != raw.strip():
            types_applied.append("header_strip")

        # 2) incomplete 조기 분기
        if is_incomplete(stripped):
            metrics["incomplete"] += 1
            q_counter["Q11"] += 1
            role_counter["metadata"] += 1
            normalized_rows.append(build_row(
                sid=sid, order=1, raw=raw, norm=stripped or raw,
                role="metadata", status="auto",
                was_split=False, norm_types=",".join(types_applied + ["no_change"]),
                subject=None, obj=None, action=None, cond=None,
                hazard=None, equipment=None, control=None,
                evidence=evidence_from_header,
                noise=True, noise_recover=False, ambiguity=False,
                context_req=False, q_codes="Q11", conf="low",
                note="incomplete",
                src=src, doc_id=doc_id, title=title,
                obligation=None,
            ))
            continue

        # 3) evidence only
        if is_evidence_only(stripped):
            ev = extract_evidence(stripped) or evidence_from_header
            q_counter["Q08"] += 1
            role_counter["evidence"] += 1
            metrics["evidence_only"] += 1
            normalized_rows.append(build_row(
                sid=sid, order=1, raw=raw, norm=stripped,
                role="evidence", status="auto",
                was_split=False, norm_types=",".join(types_applied + ["evidence_isolate"]),
                subject=None, obj=None, action=None, cond=None,
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

        # 4) noise_check (v2 라벨 존중)
        noise_flag, is_msds = detect_noise(stripped, r.get("sentence_type_candidate", ""))
        noise_recover_result = None
        if noise_flag:
            noise_recover_result = noise_recover(stripped)

        # 5) split
        pieces = split_complex_sentence(stripped)
        was_split = len(pieces) > 1
        if was_split:
            metrics["split_applied"] += 1
            types_applied.append("split_action")

        # 6) vague normalize (각 piece 별로 수행)
        # 7~10) subject/object/role/flags
        prev_subject = last_subject_by_doc.get(str(doc_id))
        order = 0
        for piece in pieces:
            order += 1
            piece_types = list(types_applied)
            normalized_piece, vague_types, amb_flag = vague_normalize(piece)
            piece_types.extend(vague_types)

            # 주어 추론
            subj, subj_type_applied = infer_subject(normalized_piece, inherited=prev_subject)
            if subj and subj_type_applied:
                piece_types.append(subj_type_applied)
            # direct 문두 주어 발견 시 last_subject 갱신
            if subj and not subj_type_applied:
                last_subject_by_doc[str(doc_id)] = subj
            # 대상
            obj = infer_object(normalized_piece)
            if obj:
                piece_types.append("object_infer")
            # 액션/조건/위험/장비/컨트롤
            action = infer_action(normalized_piece)
            cond = infer_condition(normalized_piece)
            hazard = infer_hazard(normalized_piece)
            equipment = infer_equipment(normalized_piece)
            ctrl = infer_control(normalized_piece, ctrl_idx)

            # noise / noise_recover 반영
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

            # 역할 재조정
            if "(조건)" in normalized_piece:
                role = "condition"
                normalized_piece = normalized_piece.replace(" (조건)", "").strip()
                q_codes.append("Q06")
            elif not noise_flag:
                # scope_exclusion 등 원래 sentence_type 반영
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

            # Q 코드 집계
            if was_split:
                q_codes.append("Q01")
            if amb_flag:
                q_codes.append("Q04")
            if not subj:
                q_codes.append("Q02")
            if not obj and action in ("install", "inspect", "wear", "provide", "prepare"):
                q_codes.append("Q03")
            # mixed_control_hazard
            if hazard and (action or ctrl) and "위험" in normalized_piece:
                q_codes.append("Q07")
            # context_required
            ctx_req = detect_context_required(normalized_piece)
            if ctx_req:
                q_codes.append("Q12")

            # confidence 산정
            if piece_noise_recover_cand or amb_flag or ctx_req:
                conf = "low"
            elif role == "metadata" or role == "evidence":
                conf = "medium"
            elif subj and obj and not amb_flag and role == "rule_core":
                conf = "high"
            else:
                conf = "medium"

            # obligation_level_candidate
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

            # normalize piece_types dedup
            seen = set()
            pt_out = []
            for t in piece_types:
                if t not in seen:
                    seen.add(t)
                    pt_out.append(t)
            if not pt_out:
                pt_out = ["no_change"]

            # Q dedup
            seen = set()
            q_out = []
            for q in q_codes:
                if q not in seen:
                    seen.add(q)
                    q_out.append(q)

            # metrics
            if "vague_remove" in pt_out:
                metrics["vague_remove"] += 1
            if "vague_flag" in pt_out:
                metrics["vague_flag"] += 1
            if "subject_infer" in pt_out:
                metrics["subject_inferred"] += 1
            if "object_infer" in pt_out:
                metrics["object_inferred"] += 1
            if "noise_mark" in pt_out:
                metrics["noise_marked"] += 1
            if "noise_recover" in pt_out:
                metrics["noise_recovered"] += 1
            if role == "rule_core":
                metrics["rule_core"] += 1
            if ctrl:
                metrics["control_candidate"] += 1
            role_counter[role] += 1
            for q in q_out:
                q_counter[q] += 1

            ev = extract_evidence(stripped) or evidence_from_header
            normalized_rows.append(build_row(
                sid=sid, order=order, raw=raw, norm=normalized_piece,
                role=role, status="auto" if conf != "low" else "auto_flagged",
                was_split=was_split, norm_types=",".join(pt_out),
                subject=subj, obj=obj, action=action, cond=cond,
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

        # diff row (원문 1건당 1행 요약)
        diff_rows.append({
            "sample_id": sid,
            "raw_sentence_text": raw,
            "normalized_pieces": " ||| ".join(pieces),
            "was_split": int(was_split),
            "split_count": len(pieces),
            "noise_flag": int(noise_flag),
            "noise_recover_candidate": int(bool(noise_recover_result)),
        })

    return normalized_rows, diff_rows, metrics | Counter({"q_" + k: v for k, v in q_counter.items()}) | Counter({"role_" + k: v for k, v in role_counter.items()})


def build_row(**kw) -> Dict:
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
        "normalization_type": kw["norm_types"],
        "sentence_role": kw["role"],
        "obligation_level_candidate": kw["obligation"] or "",
        "subject_candidate": kw["subject"] or "",
        "object_candidate": kw["obj"] or "",
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
        "quality_issue_codes": kw["q_codes"],
        "confidence": kw["conf"],
        "normalization_note": kw["note"],
        "reviewer_note": "",
    }


FIELDS = [
    "normalized_sentence_id", "source_sentence_id", "source_type",
    "document_id", "document_title",
    "raw_sentence_text", "normalized_sentence_text",
    "normalization_status", "split_group_id", "split_order",
    "was_split", "normalization_type",
    "sentence_role", "obligation_level_candidate",
    "subject_candidate", "object_candidate", "action_candidate",
    "condition_candidate", "hazard_candidate", "equipment_candidate",
    "control_candidate", "evidence_candidate",
    "noise_flag", "noise_recovery_candidate",
    "ambiguity_flag", "context_required_flag",
    "quality_issue_codes", "confidence",
    "normalization_note", "reviewer_note",
]

DIFF_FIELDS = [
    "sample_id", "raw_sentence_text", "normalized_pieces",
    "was_split", "split_count",
    "noise_flag", "noise_recover_candidate",
]


def main() -> None:
    rows = []
    with SRC.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    controls = load_controls()

    norm_rows, diff_rows, metrics = process(rows, controls)

    with OUT_NORM.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in norm_rows:
            w.writerow(r)

    with OUT_DIFF.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=DIFF_FIELDS)
        w.writeheader()
        for r in diff_rows:
            w.writerow(r)

    # 품질 지표 stdout
    print("=== 문장 정제 샘플 생성 결과 ===")
    print(f"- 입력 샘플 수: {metrics.get('total_samples', 0)}")
    print(f"- 정제 문장 수 (split 포함): {len(norm_rows)}")
    print(f"- split 적용 원문 수: {metrics.get('split_applied', 0)}")
    print(f"- vague_remove 적용: {metrics.get('vague_remove', 0)}")
    print(f"- vague_flag(ambiguity) 적용: {metrics.get('vague_flag', 0)}")
    print(f"- 주어 복원(후보): {metrics.get('subject_inferred', 0)}")
    print(f"- 대상 복원(후보): {metrics.get('object_inferred', 0)}")
    print(f"- noise 표시: {metrics.get('noise_marked', 0)}")
    print(f"- noise 복구 후보: {metrics.get('noise_recovered', 0)}")
    print(f"- incomplete(metadata): {metrics.get('incomplete', 0)}")
    print(f"- evidence_only: {metrics.get('evidence_only', 0)}")
    print(f"- control_candidate 부여: {metrics.get('control_candidate', 0)}")
    print(f"- rule_core 역할: {metrics.get('rule_core', 0)}")
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

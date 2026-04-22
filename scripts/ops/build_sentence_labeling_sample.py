"""
문장 라벨링 샘플 CSV 생성기.

- source 별 balanced sample 추출 (law/admrul/licbyl/kosha/expc)
- 문장 분리·dedupe·길이 필터
- 규칙 기반 candidate(1순위) + noise split (primary ~85% / noise ~15%)
- CSV 출력 컬럼: docs/design/sentence_classification_schema.md 기준

기본 출력: $DATA_DIR/risk_db/schema/sentence_labeling_sample.csv
  DATA_DIR 미설정 시 /app/data

read-mostly (documents 만 SELECT, DB write 없음).
재실행 가능 (CSV 덮어쓰기). 라벨링 결과는 reviewer 가 별도 파일로 저장.
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import sys
from pathlib import Path

import psycopg2

OUT_PATH = Path(os.getenv("DATA_DIR", "/app/data")) / "risk_db" / "schema" / "sentence_labeling_sample.csv"
TARGET_TOTAL = 400  # 300~500 범위
MIN_LEN = 15
MAX_LEN = 400
SCHEMA_VERSION = "v0.1"

# 소스별 목표 분포 (합 1.0)
QUOTA = {
    "law":    120,   # 실체 조문 중심
    "admrul": 60,
    "licbyl": 40,
    "kosha":  120,
    "expc":   60,
}


# ---------------------------------------------------------------------------
# 문장 분리 + 정규화
# ---------------------------------------------------------------------------

_SENT_SPLIT = re.compile(r"(?<=[.。!?])\s+|(?<=다\.)\s+|\n+")
_WS = re.compile(r"\s+")
_LEADING = re.compile(r"^[①-⑳⓵-⓾0-9]+\)?\.?\s*")


def sentences(text: str) -> list[str]:
    if not text:
        return []
    t = text.replace("\x00", " ")
    parts = _SENT_SPLIT.split(t)
    out: list[str] = []
    for p in parts:
        p = _WS.sub(" ", p).strip()
        p = _LEADING.sub("", p)
        if MIN_LEN <= len(p) <= MAX_LEN:
            out.append(p)
    return out


def norm_key(s: str) -> str:
    return hashlib.md5(_WS.sub("", s)[:80].encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# 규칙 기반 candidate
# ---------------------------------------------------------------------------

# sentence_type 1순위 매칭 순서 (앞이 우선)
STYPE_RULES: list[tuple[str, list[str]]] = [
    ("prohibition", ["해서는 아니", "해서는 안", "하여서는 아니", "하여서는 안",
                      "금지한다", "출입하지 아니하도록", "사용하여서는", "아니 된다",
                      "하지 못한다", "아니된다"]),
    ("definition",  ["이란", "라 함은", "을(를) 말한다", "을 말한다", "라 한다"]),
    ("scope_exclusion", ["제외한다", "적용하지 아니한다", "다만,", "이 경우에는 제외"]),
    ("education_rule", ["특별교육", "안전보건교육", "안전교육", "교육을 실시", "교육하여야"]),
    ("inspection_rule", ["점검하여야", "측정하여야", "검사하여야", "확인하여야",
                           "매일 점검", "매월 점검", "매년", "6개월마다",
                           "주기적으로", "정기적으로 점검", "점검을 실시",
                           "작업환경측정", "자체점검"]),
    ("document_rule", ["비치하여야", "게시하여야", "작성하여야", "보존하여야", "기록하여야",
                       "보고하여야", "신고하여야", "MSDS", "물질안전보건자료", "경고표지"]),
    ("ppe_rule", ["안전모", "안전대", "안전화", "보호구를 지급", "보호구를 착용",
                   "호흡보호구", "방진마스크", "내화학장갑", "보호복", "보안경"]),
    ("emergency_rule", ["비상조치", "비상대응", "대피하여야", "응급조치", "피난"]),
    ("equipment_rule", ["설치하여야", "갖추어야", "방호장치", "안전난간", "비계",
                        "국소배기장치", "환기장치", "크레인", "고소작업대", "승강기", "리프트"]),
    ("legal_reference", ["별표", "고시 제", "같은 법 제", "이 규칙에 따른"]),
    ("requirement", ["하여야 한다", "해야 한다", "지급하여야", "실시하여야", "마련하여야"]),
    ("condition_trigger", ["인 경우에는", "인 경우", "할 때에는", "할 때", "이상인 경우", "이하인 경우"]),
    ("caution", ["주의하여야", "유의하여야", "유의사항"]),
    ("procedure", ["작업 순서", "다음 순서", "작업방법은"]),
]

OBLIGATION_MAP = {
    "prohibition": "prohibited",
    "requirement": "mandatory",
    "ppe_rule": "mandatory",
    "inspection_rule": "mandatory",
    "education_rule": "mandatory",
    "document_rule": "mandatory",
    "emergency_rule": "mandatory",
    "equipment_rule": "mandatory",
    "caution": "cautionary",
    "scope_exclusion": "exception",
    "definition": "informative",
    "descriptive_noise": "informative",
    "legal_reference": "informative",
    "condition_trigger": "informative",
    "procedure": "informative",
}

ACTION_PATTERNS = [
    ("install",         ["설치"]),
    ("inspect",         ["점검", "검사"]),
    ("measure",         ["측정"]),
    ("wear",            ["착용"]),
    ("provide",         ["지급", "비치"]),
    ("train",           ["교육", "훈련"]),
    ("post",            ["게시"]),
    ("prepare",         ["작성", "준비"]),
    ("record",          ["기록"]),
    ("report",          ["보고", "신고"]),
    ("isolate",         ["격리", "차단", "폐쇄"]),
    ("ventilate",       ["환기"]),
    ("clean",           ["청소", "제거"]),
    ("store",           ["보관", "저장"]),
    ("prohibit_access", ["출입금지", "출입을 금지"]),
    ("monitor",         ["감시", "모니터링"]),
    ("maintain",        ["유지", "정비"]),
]

SUBJECT_PATTERNS = [
    ("employer",       ["사업주"]),
    ("safety_manager", ["안전관리자", "보건관리자"]),
    ("supervisor",     ["관리감독자", "작업지휘자"]),
    ("worker",         ["근로자"]),
    ("contractor",     ["도급인", "수급인"]),
    ("document",       ["MSDS", "경고표지", "관리대장"]),
    ("workplace",      ["사업장", "작업장"]),
    ("chemical",       ["유해물질", "관리대상 유해", "위험물"]),
]

CONDITION_PATTERNS = [
    ("quantity_threshold",  [r"\d+\s*(명|톤|미터|m|%)\s*이상", r"\d+\s*(명|톤|미터|m|%)\s*이하"]),
    ("height_work",         ["높이 2m", "추락 우려", "고소"]),
    ("lifting_operation",   ["양중", "인양", "들어올리는"]),
    ("electrical_work",     ["충전전로", "활선", "전기작업"]),
    ("hot_work",            ["용접", "용단", "화기작업"]),
    ("confined_space",      ["밀폐공간", "산소결핍"]),
    ("hazardous_substance", ["유해·위험물질", "특별관리물질", "관리대상 유해물질", "화학물질"]),
    ("weather_environment", ["강풍", "폭염", "한랭", "우천"]),
    ("simultaneous_work",   ["혼재작업", "동시작업"]),
    ("periodic_schedule",   ["매일", "매월", "매주", "6개월마다", "연 1회", "분기별"]),
    ("before_after_work",   ["작업 시작 전", "작업 종료 후"]),
    ("incident_emergency",  ["재해 발생", "사고 발생"]),
    ("legal_scope",         ["상시근로자 수"]),
]

NOISE_TOKENS = [
    "참고하세요", "참고하시기", "자세한 내용은", "별지 참고",
    "물리화학적 특성", "일반정보", "교육미디어",
]


def pick_stype(text: str) -> str:
    for code, kws in STYPE_RULES:
        if any(k in text for k in kws):
            return code
    if any(k in text for k in NOISE_TOKENS):
        return "descriptive_noise"
    return ""


def pick_action(text: str) -> str:
    for code, kws in ACTION_PATTERNS:
        if any(k in text for k in kws):
            return code
    return ""


def pick_subject(text: str) -> str:
    for code, kws in SUBJECT_PATTERNS:
        if any(k in text for k in kws):
            return code
    return ""


def pick_condition(text: str) -> str:
    for code, pats in CONDITION_PATTERNS:
        for p in pats:
            if p.startswith(r"\d") or any(ch in p for ch in ("\\", "[", "(")):
                if re.search(p, text):
                    return code
            elif p in text:
                return code
    return ""


def pick_evidence(source_type: str) -> str:
    return {"law":"law","admrul":"admrul","licbyl":"licbyl","expc":"expc",
            "kosha":"kosha","kosha_form":"kosha","moel_form":"internal_rule"}.get(source_type,"unknown")


def confidence_of(stype: str, text: str) -> str:
    # prohibition/requirement 에 명확한 키워드 hit 면 high
    if stype == "prohibition" and ("해서는 아니" in text or "해서는 안" in text):
        return "high"
    if stype == "requirement" and ("하여야 한다" in text or "해야 한다" in text):
        return "high"
    if stype == "ppe_rule" and ("착용" in text or "지급" in text):
        return "high"
    if stype == "descriptive_noise":
        return "low"
    if stype == "":
        return "low"
    return "medium"


def noise_flag_of(stype: str, text: str) -> str:
    if stype == "descriptive_noise":
        return "1"
    if stype == "" and any(n in text for n in NOISE_TOKENS):
        return "1"
    return "0"


# ---------------------------------------------------------------------------
# 샘플링
# ---------------------------------------------------------------------------

conn = psycopg2.connect(os.environ["DATABASE_URL"])

samples: list[dict] = []
seen_keys: set[str] = set()


def fetch_source(source_type: str, limit_docs: int) -> list[tuple[int, str, str, str]]:
    with conn.cursor() as cur:
        if source_type == "kosha":
            cur.execute("""
                SELECT id, source_type, title, COALESCE(body_text,'')
                  FROM documents
                 WHERE source_type=%s AND status='active'
                   AND COALESCE(body_text,'') <> ''
                 ORDER BY id
                 LIMIT %s
            """, (source_type, limit_docs))
        else:
            cur.execute("""
                SELECT id, source_type, title, COALESCE(body_text,'')
                  FROM documents
                 WHERE source_type=%s
                   AND COALESCE(body_text,'') <> ''
                 ORDER BY id
                 LIMIT %s
            """, (source_type, limit_docs))
        return cur.fetchall()


def _make_sample(doc_id: int, st: str, title: str, s: str, stype: str) -> dict:
    obligation = OBLIGATION_MAP.get(stype, "")
    return {
        "sample_id": "",
        "schema_version": SCHEMA_VERSION,
        "source_type": st,
        "document_id": str(doc_id),
        "document_title": (title or "")[:200],
        "sentence_text": s,
        "sentence_type_candidate": stype,
        "obligation_level_candidate": obligation,
        "subject_type_candidate": pick_subject(s),
        "action_type_candidate": pick_action(s),
        "condition_type_candidate": pick_condition(s),
        "evidence_type_candidate": pick_evidence(st),
        "work_type_candidate": "",
        "hazard_candidate": "",
        "equipment_candidate": "",
        "confidence": confidence_of(stype, s),
        "noise_flag": noise_flag_of(stype, s),
        "reviewer_note": "",
    }


# 소스별 두 풀 분리 — rule-hit 우선, noise 는 quota 의 일부(~15%)만
NOISE_RATIO = 0.15

for source_type, target_n in QUOTA.items():
    docs = fetch_source(source_type, limit_docs=200)  # 더 많이 뽑아 선별
    primary: list[dict] = []
    noise: list[dict] = []
    for doc_id, st, title, body in docs:
        text = (body or "")[:6000]
        sents = sentences(text)
        for s in sents:
            key = norm_key(s)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            stype = pick_stype(s)
            if stype:
                primary.append(_make_sample(doc_id, st, title, s, stype))
            else:
                noise.append(_make_sample(doc_id, st, title, s, "descriptive_noise"))
            # 한 doc 당 너무 많이 뽑지 않도록 loose cap
            if len(primary) + len(noise) >= target_n * 6:
                break
        if len(primary) + len(noise) >= target_n * 6:
            break

    n_noise = max(1, int(target_n * NOISE_RATIO))
    n_primary = target_n - n_noise
    pick = primary[:n_primary] + noise[:n_noise]
    # 부족하면 나머지로 채움
    if len(pick) < target_n:
        leftover = primary[n_primary:] + noise[n_noise:]
        pick += leftover[: target_n - len(pick)]
    samples.extend(pick[:target_n])

conn.close()

# sample_id 부여 (최종)
for i, r in enumerate(samples, 1):
    r["sample_id"] = f"S{i:04d}"

# 총량이 TARGET_TOTAL 이상이면 잘라냄
samples = samples[:TARGET_TOTAL + 100]


# ---------------------------------------------------------------------------
# CSV 저장
# ---------------------------------------------------------------------------

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
fieldnames = [
    "sample_id", "schema_version",
    "source_type", "document_id", "document_title", "sentence_text",
    "sentence_type_candidate", "obligation_level_candidate",
    "subject_type_candidate", "action_type_candidate",
    "condition_type_candidate", "evidence_type_candidate",
    "work_type_candidate", "hazard_candidate", "equipment_candidate",
    "confidence", "noise_flag", "reviewer_note",
]
with open(OUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in samples:
        w.writerow(r)


# ---------------------------------------------------------------------------
# 보고용 집계
# ---------------------------------------------------------------------------

from collections import Counter
c_src = Counter(r["source_type"] for r in samples)
c_type = Counter(r["sentence_type_candidate"] for r in samples)
c_oblig = Counter(r["obligation_level_candidate"] for r in samples)
c_act = Counter(r["action_type_candidate"] or "(none)" for r in samples)
c_cond = Counter(r["condition_type_candidate"] or "(none)" for r in samples)
c_conf = Counter(r["confidence"] for r in samples)
noise_n = sum(1 for r in samples if r["noise_flag"] == "1")

print(f"[OUT] {OUT_PATH}  total={len(samples)}")
print(f"[BY_SOURCE]      {dict(c_src)}")
print(f"[BY_STYPE_top8]  {dict(c_type.most_common(8))}")
print(f"[BY_OBLIG]       {dict(c_oblig)}")
print(f"[BY_ACTION_top5] {dict(c_act.most_common(5))}")
print(f"[BY_COND_top5]   {dict(c_cond.most_common(5))}")
print(f"[CONFIDENCE]     {dict(c_conf)}")
print(f"[NOISE]          flagged={noise_n}")

"""controls master v2 기반으로 샘플 확장(400→800+) + 매핑 일괄 수행.

입력
  - data/risk_db/master/controls_master_draft_v2.csv (v2 master)
  - data/risk_db/schema/sentence_labeling_sample.csv (기존 400 샘플)
  - data/normalized/kosha/*.json (보조 확대 소스)

출력
  - data/risk_db/master/sentence_labeling_sample_v2.csv (확장된 입력 샘플)
  - data/risk_db/master/sentence_control_mapping_sample_v2.csv (확장된 매핑 결과)

원칙
  - 기존 400 샘플은 그대로 유지(id, sentence_type_candidate 보존).
  - 추가 샘플은 kosha normalized body_text 에서 추출.
    · 중복 최소화(exact sentence dedup)
    · 길이 15~160 chars
    · zero-hit category(supervision/permit/administrative/traffic) 키워드 우선 선별
  - descriptive_noise 과다 유입 방지 위해 기본 필터 적용.
"""
from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER_V2 = ROOT / "data/risk_db/master/controls_master_draft_v2.csv"
IN_SAMPLE = ROOT / "data/risk_db/schema/sentence_labeling_sample.csv"
KOSHA_DIR = ROOT / "data/normalized/kosha"

OUT_INPUT = ROOT / "data/risk_db/master/sentence_labeling_sample_v2.csv"
OUT_MAP = ROOT / "data/risk_db/master/sentence_control_mapping_sample_v2.csv"

# zero-hit 카테고리: 적극 확대
ZERO_HIT_KEYWORDS = {
    "supervision": [
        "감시인", "감시자", "관리감독자", "작업지휘자", "작업 지휘자",
        "신호수", "유도자", "유도원", "화재감시인", "화기감시",
        "신호체계", "수신호", "입회", "standby",
    ],
    "permit": [
        "작업허가", "작업 허가", "허가서", "밀폐공간 작업허가",
        "화기작업 허가", "화기 허가", "고소작업 허가", "굴착작업 허가",
        "PTW", "permit to work",
    ],
    "administrative": [
        "출입금지", "출입통제", "출입 제한", "관계자 외",
        "작업구역 분리", "혼재작업", "안전보건협의체",
        "라바콘", "안전선", "바리케이드", "경계 표시",
        "야간작업", "폭염", "한파", "휴식시간",
    ],
    "traffic": [
        "차량 동선", "보행자 동선", "주행로", "보행로",
        "제한속도", "서행", "유도자", "후진경보", "후방감지",
        "차량계", "중장비 유도",
    ],
}

# v2 master 에서 규칙을 자동 생성
def load_master() -> list[dict]:
    with MASTER_V2.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_rules(master: list[dict]) -> list[tuple[str, str, list[str]]]:
    """master → [(category, code, keywords)] list.
    구체 keyword 많은 control 을 앞쪽에 배치해 과잉 매칭 방지.
    """
    rules = []
    for row in master:
        kws_raw = row.get("typical_keywords", "")
        kws = [k.strip() for k in kws_raw.split("|") if k.strip()]
        if not kws:
            continue
        rules.append((row["control_category"], row["control_code"], kws))
    # 정렬: keyword 개수 많고 길이 긴 control 이 앞으로 (더 구체적) — 일반 키워드는 뒤로
    rules.sort(key=lambda r: (-sum(len(k) for k in r[2]) / max(len(r[2]), 1)))
    return rules


ELIGIBLE_STYPE = {
    "requirement", "equipment_rule", "ppe_rule", "inspection_rule",
    "education_rule", "document_rule", "emergency_rule", "procedure",
    "condition_trigger", "prohibition",
}

# context_required/negative 규칙 — single 단어 기반 false positive 억제
SINGLE_TOKEN_BLOCK = {
    # 단독 단어는 contextless 이므로 무조건 hit 시키지 않음 (1글자/2글자 단어)
    "관리", "조치", "확인", "준수", "주의", "실시", "부착", "설치",
}


def match_control(text: str, rules: list[tuple[str, str, list[str]]]) -> tuple[str, str, str]:
    """return (category, code, confidence)."""
    for cat, code, kws in rules:
        hits_meaningful = []
        for kw in kws:
            if kw in text:
                # 2글자 이하 단일 단어는 blocked 목록이면 skip
                if kw in SINGLE_TOKEN_BLOCK and len(kw) <= 2:
                    continue
                hits_meaningful.append(kw)
        if not hits_meaningful:
            continue
        # 최소 1개 키워드 hit: 다중 hit 또는 4글자 이상 키워드 hit 이면 high, 아니면 medium
        has_specific = any(len(k) >= 4 for k in hits_meaningful)
        conf = "high" if len(hits_meaningful) >= 2 or has_specific else "medium"
        return (cat, code, conf)
    return ("", "", "low")


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?·])\s+|(?<=다\.)\s+|(?<=한다)\s+|(?<=\n)")


def _split_sentences(text: str) -> list[str]:
    # 1차: 줄바꿈 단위
    parts = [p.strip() for p in text.split("\n") if p.strip()]
    out = []
    for p in parts:
        # 2차: 마침표 단위
        sub = re.split(r"(?<=[다\.])\s+", p)
        for s in sub:
            s = s.strip()
            if 15 <= len(s) <= 160:
                out.append(s)
    return out


KOSHA_NOISE_PATTERNS = [
    r"^www\.kosha", r"OPL", r"교육미디어", r"\d{4}-\d+", r"^그림\s*\d",
    r"^\<", r"^\d+\.\s*$",
]


def _is_noise(s: str) -> bool:
    for pat in KOSHA_NOISE_PATTERNS:
        if re.search(pat, s):
            return True
    # 조사/어미 비어있는 단어 나열
    if s.count(" ") < 1 and len(s) < 30:
        return True
    return False


def classify_sentence_type(s: str) -> str:
    """kosha 문장에 대한 간이 sentence_type 추정."""
    if any(k in s for k in ["작업허가", "허가서"]):
        return "document_rule"
    if any(k in s for k in ["점검", "측정", "검사", "확인"]) and any(p in s for p in ["매일", "주기", "전", "후", "정기"]):
        return "inspection_rule"
    if any(k in s for k in ["보호구", "안전모", "안전대", "방진마스크", "안전화"]):
        return "ppe_rule"
    if any(k in s for k in ["교육", "특별교육", "TBM", "주지"]):
        return "education_rule"
    if any(k in s for k in ["비상", "대피", "응급", "구조"]):
        return "emergency_rule"
    if any(k in s for k in ["해서는 안", "금지", "하지 아니"]):
        return "prohibition"
    if any(k in s for k in ["설치", "부착", "갖추", "설비"]):
        return "equipment_rule"
    if any(k in s for k in ["해야 한다", "하여야 한다", "유지한다", "준수"]):
        return "requirement"
    if any(k in s for k in ["경우", "때", "이상"]):
        return "condition_trigger"
    return "descriptive_noise"


def extract_kosha_sentences(target: int = 400, zero_hit_quota: int = 160) -> list[dict]:
    """kosha normalized body_text → 문장 단위 추출.
    zero-hit quota 만큼은 zero-hit keyword 를 포함한 문장을 우선 선별.
    """
    all_files = sorted(KOSHA_DIR.glob("*.json"))
    random.seed(42)
    # 안정적 순회를 위해 충분한 파일 수를 사전 셔플
    random.shuffle(all_files)

    zero_hit_words: list[tuple[str, list[str]]] = []
    for cat, kws in ZERO_HIT_KEYWORDS.items():
        zero_hit_words.append((cat, kws))

    seen: set[str] = set()
    zero_hit_bucket: list[dict] = []
    general_bucket: list[dict] = []

    for fp in all_files:
        if len(zero_hit_bucket) >= zero_hit_quota and len(general_bucket) >= (target - zero_hit_quota):
            break
        try:
            with fp.open("r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        body = d.get("body_text", "") or ""
        if not body:
            continue
        doc_id = d.get("source_id") or fp.stem
        title = d.get("title", "")
        for s in _split_sentences(body):
            if _is_noise(s) or s in seen:
                continue
            # zero-hit 카테고리 매칭이면 zero_hit_bucket
            zh_cat = None
            for cat, kws in zero_hit_words:
                if any(k in s for k in kws):
                    zh_cat = cat
                    break
            rec = {
                "source_type": "kosha",
                "document_id": doc_id,
                "document_title": title,
                "sentence_text": s,
                "zero_hit_category": zh_cat or "",
            }
            if zh_cat and len(zero_hit_bucket) < zero_hit_quota:
                seen.add(s)
                zero_hit_bucket.append(rec)
            elif not zh_cat and len(general_bucket) < (target - zero_hit_quota):
                seen.add(s)
                general_bucket.append(rec)
    return zero_hit_bucket + general_bucket


def write_expanded_input(existing: list[dict], extras: list[dict]) -> None:
    fields = [
        "sample_id", "schema_version", "source_type", "document_id",
        "document_title", "sentence_text", "sentence_type_candidate",
        "obligation_level_candidate", "subject_type_candidate",
        "action_type_candidate", "condition_type_candidate",
        "evidence_type_candidate", "work_type_candidate",
        "hazard_candidate", "equipment_candidate",
        "confidence", "noise_flag", "reviewer_note",
    ]
    OUT_INPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT_INPUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in existing:
            w.writerow({k: row.get(k, "") for k in fields})
        next_id = max(int(r["sample_id"][1:]) for r in existing) + 1
        for extra in extras:
            sid = f"S{next_id:04d}"
            next_id += 1
            stype = classify_sentence_type(extra["sentence_text"])
            obl = "mandatory" if "하여야" in extra["sentence_text"] or "해야 한다" in extra["sentence_text"] else "informative"
            if stype == "prohibition":
                obl = "prohibited"
            w.writerow({
                "sample_id": sid,
                "schema_version": "v0.2",
                "source_type": extra["source_type"],
                "document_id": extra["document_id"],
                "document_title": extra["document_title"],
                "sentence_text": extra["sentence_text"],
                "sentence_type_candidate": stype,
                "obligation_level_candidate": obl,
                "subject_type_candidate": "",
                "action_type_candidate": "",
                "condition_type_candidate": "",
                "evidence_type_candidate": extra["source_type"],
                "work_type_candidate": "",
                "hazard_candidate": "",
                "equipment_candidate": "",
                "confidence": "medium",
                "noise_flag": "1" if stype == "descriptive_noise" else "0",
                "reviewer_note": f"v2_extra|zh={extra.get('zero_hit_category','')}",
            })


def write_mapping(rules: list[tuple[str, str, list[str]]], master_index: dict[str, dict]) -> dict:
    fields = [
        "sample_id", "sentence_text", "source_type", "sentence_type",
        "obligation_level", "action_type", "condition_type",
        "hazard_candidate", "equipment_candidate", "work_type_candidate",
        "control_category_candidate", "control_type_candidate",
        "control_name_candidate", "legal_required_possible",
        "confidence", "review_note",
    ]
    stats = {"total": 0, "hit": 0, "by_cat": Counter(), "by_code": Counter(), "by_conf": Counter()}
    with OUT_INPUT.open("r", encoding="utf-8-sig") as rf, \
            OUT_MAP.open("w", encoding="utf-8-sig", newline="") as wf:
        rdr = csv.DictReader(rf)
        wtr = csv.DictWriter(wf, fieldnames=fields)
        wtr.writeheader()
        for row in rdr:
            stats["total"] += 1
            stype = row.get("sentence_type_candidate", "")
            text = row.get("sentence_text", "")
            cat = code = ""
            conf = "low"
            if stype in ELIGIBLE_STYPE:
                cat, code, conf = match_control(text, rules)
            name = master_index.get(code, {}).get("control_name_ko", "") if code else ""
            legal = master_index.get(code, {}).get("legal_required_possible", "") if code else ""
            if code:
                stats["hit"] += 1
                stats["by_cat"][cat] += 1
                stats["by_code"][code] += 1
                stats["by_conf"][conf] += 1
            wtr.writerow({
                "sample_id": row["sample_id"],
                "sentence_text": text,
                "source_type": row.get("source_type", ""),
                "sentence_type": stype,
                "obligation_level": row.get("obligation_level_candidate", ""),
                "action_type": row.get("action_type_candidate", ""),
                "condition_type": row.get("condition_type_candidate", ""),
                "hazard_candidate": row.get("hazard_candidate", ""),
                "equipment_candidate": row.get("equipment_candidate", ""),
                "work_type_candidate": row.get("work_type_candidate", ""),
                "control_category_candidate": cat,
                "control_type_candidate": code,
                "control_name_candidate": name,
                "legal_required_possible": legal,
                "confidence": conf,
                "review_note": row.get("reviewer_note", ""),
            })
    return stats


def main() -> None:
    master = load_master()
    master_index = {r["control_code"]: r for r in master}
    rules = build_rules(master)
    print(f"[master_v2] controls={len(master)}, rules={len(rules)}")

    # 기존 400 샘플
    with IN_SAMPLE.open("r", encoding="utf-8-sig") as f:
        existing = list(csv.DictReader(f))
    print(f"[existing_samples] {len(existing)}")

    # kosha 추가 추출
    extras = extract_kosha_sentences(target=400, zero_hit_quota=160)
    zh_count = sum(1 for x in extras if x["zero_hit_category"])
    print(f"[extras] total={len(extras)} zero_hit_hits={zh_count}")

    write_expanded_input(existing, extras)
    stats = write_mapping(rules, master_index)
    print(f"[OUT_INPUT] {OUT_INPUT}  total={stats['total']}")
    print(f"[OUT_MAP]   {OUT_MAP}  hit={stats['hit']} ({stats['hit']/stats['total']*100:.1f}%)")
    print(f"[by_cat]    {dict(stats['by_cat'].most_common())}")
    print(f"[by_conf]   {dict(stats['by_conf'])}")
    # zero-hit category 해소
    zero_hit_cats = {"supervision_control", "permit_control", "administrative_control", "traffic_control"}
    resolved = zero_hit_cats & set(stats["by_cat"].keys())
    print(f"[zero_hit_resolved] {resolved}")
    print(f"[top_codes] {stats['by_code'].most_common(10)}")


if __name__ == "__main__":
    main()

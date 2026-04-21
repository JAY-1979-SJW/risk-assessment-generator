"""
law raw staging 정규화 스크립트
입력:  data/risk_db/law_raw/{laws_index,admin_rules_index,licbyl_index,expc_index}.json
출력:  data/risk_db/law_normalized/safety_laws_normalized.json
       data/risk_db/law_normalized/safety_laws_rejects.json

원본 raw 파일은 읽기 전용 — 수정 금지.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
RAW_DIR = ROOT / "data/risk_db/law_raw"
OUT_DIR = ROOT / "data/risk_db/law_normalized"

RAW_FILES = [
    ("laws_index.json",        "law",    "statutes"),
    ("admin_rules_index.json", "admrul", "admin_rules"),
    ("licbyl_index.json",      "licbyl", "licbyl"),
    ("expc_index.json",        "expc",   "expc"),
]

LAW_GO_KR = "https://www.law.go.kr"

# ─── 필드 보강: law_id, title_normalized, keywords, status ───────────────────

# source_target → spec source_type 매핑
_SOURCE_TYPE_MAP = {
    "law":    "law",
    "admrul": "admrul",
    "licbyl": "licbyl",
    "expc":   "expc",
}

# 제목 정규화: 「」, [], () 제거 후 공백 압축
import re as _re

def _normalize_title(title: str) -> str:
    s = title
    s = _re.sub(r'[「」『』]', '', s)
    s = _re.sub(r'\[.*?\]', '', s)
    s = _re.sub(r'\(.*?\)', '', s)
    return _re.sub(r'\s+', ' ', s).strip()


# 법령명에서 키워드 추출 (형태소 분석 없이 단순 명사 분리)
_KW_STOPWORDS = frozenset(["관한", "규칙", "법률", "시행령", "시행규칙", "기준", "지침",
                            "고시", "예규", "훈령", "의", "에", "을", "를", "이", "가",
                            "및", "등", "에서", "에게", "으로", "와", "과", "한", "하는",
                            "수", "것", "에서의", "해석례", "에서는", "그", "이를"])

def _extract_keywords(title: str) -> list[str]:
    normalized = _normalize_title(title)
    tokens = _re.split(r'[\s·,·/·「」\-]+', normalized)
    kws = []
    for tok in tokens:
        tok = tok.strip()
        if len(tok) >= 2 and tok not in _KW_STOPWORDS:
            kws.append(tok)
    return list(dict.fromkeys(kws))[:8]  # 최대 8개, 순서 보존 중복 제거


def _enrich(norm: dict) -> dict:
    """기존 norm dict에 spec 필수 신규 필드를 추가해 반환."""
    category = norm.get("category", "")
    raw_id   = str(norm.get("raw_id", ""))
    title    = norm.get("title_ko", "")
    src_tgt  = norm.get("raw_target", norm.get("source_target", ""))

    return {
        **norm,
        # spec 필수 필드
        "law_id":           f"{category}:{raw_id}",
        "source_type":      _SOURCE_TYPE_MAP.get(src_tgt, src_tgt),
        "source_key":       f"{_SOURCE_TYPE_MAP.get(src_tgt, src_tgt)}:{raw_id}",
        "title":            title,
        "title_normalized": _normalize_title(title),
        "keywords":         _extract_keywords(title),
        "status":           "active",
    }


# ─── 날짜/링크 정규화 ────────────────────────────────────────────────────────

def norm_date(raw: str) -> tuple[str, bool]:
    """(정규화된 날짜, 성공 여부). 값이 없으면 ('', True)."""
    if not raw or not raw.strip():
        return "", True
    s = raw.strip()
    # YYYYMMDD
    if re.match(r'^\d{8}$', s):
        return f"{s[:4]}-{s[4:6]}-{s[6:]}", True
    # YYYY.MM.DD
    m = re.match(r'^(\d{4})\.(\d{2})\.(\d{2})$', s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}", True
    # YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
        return s, True
    return "", False


def norm_link(raw: str) -> str:
    if not raw or not raw.strip():
        return ""
    s = raw.strip()
    if s.startswith("http"):
        return s
    if s.startswith("/"):
        return f"{LAW_GO_KR}{s}"
    return s


# ─── source별 매핑 ───────────────────────────────────────────────────────────

def _base(file_meta: dict) -> dict:
    return {
        "source_type":   "data.go.kr",
        "source_api":    file_meta.get("endpoint", ""),
        "source_target": file_meta.get("target", ""),
        "source_file":   file_meta["_filename"],
        "query":         "",
        "collected_at":  file_meta.get("fetched_at", ""),
        "raw_target":    file_meta.get("target", ""),
    }


def map_statute(item: dict, file_meta: dict) -> tuple[dict, list[str]]:
    date_val, date_ok_p = norm_date(item.get("공포일자", ""))
    enf_val,  _         = norm_date(item.get("시행일자", ""))
    warns = [] if date_ok_p else [f"invalid_date:공포일자={item.get('공포일자')}"]
    return {
        **_base(file_meta),
        "category":          "statute",
        "raw_id":            item.get("법령일련번호", ""),
        "title_ko":          item.get("법령명한글", ""),
        "title_short":       item.get("법령약칭명", ""),
        "document_type":     item.get("법령구분명", ""),
        "law_type":          item.get("법령구분명", ""),
        "ministry_name":     item.get("소관부처명", ""),
        "authority":         item.get("소관부처명", ""),
        "promulgation_date": date_val,
        "enforcement_date":  enf_val,
        "revision_type":     item.get("제개정구분명", ""),
        "status_text":       item.get("현행연혁코드", ""),
        "reference_no":      item.get("공포번호", ""),
        "detail_link":       norm_link(item.get("법령상세링크", "")),
        "file_link":         "",
        "pdf_link":          "",
        "related_law_id":    "",
        "related_law_name":  "",
        "raw_payload":       item,
    }, warns


def map_admin_rule(item: dict, file_meta: dict) -> tuple[dict, list[str]]:
    date_val, date_ok = norm_date(item.get("발령일자", ""))
    enf_val,  _       = norm_date(item.get("시행일자", ""))
    warns = [] if date_ok else [f"invalid_date:발령일자={item.get('발령일자')}"]
    return {
        **_base(file_meta),
        "category":          "admin_rule",
        "raw_id":            item.get("행정규칙일련번호", ""),
        "title_ko":          item.get("행정규칙명", ""),
        "title_short":       "",
        "document_type":     item.get("행정규칙종류", ""),
        "law_type":          item.get("행정규칙종류", ""),
        "ministry_name":     item.get("소관부처명", ""),
        "authority":         item.get("소관부처명", ""),
        "promulgation_date": date_val,
        "enforcement_date":  enf_val,
        "revision_type":     item.get("제개정구분명", ""),
        "status_text":       item.get("현행연혁구분", ""),
        "reference_no":      item.get("발령번호", ""),
        "detail_link":       norm_link(item.get("행정규칙상세링크", "")),
        "file_link":         "",
        "pdf_link":          "",
        "related_law_id":    "",
        "related_law_name":  "",
        "raw_payload":       item,
    }, warns


def map_licbyl(item: dict, file_meta: dict) -> tuple[dict, list[str]]:
    date_val, date_ok = norm_date(item.get("공포일자", ""))
    warns = [] if date_ok else [f"invalid_date:공포일자={item.get('공포일자')}"]
    return {
        **_base(file_meta),
        "category":          "licbyl",
        "raw_id":            item.get("별표일련번호", ""),
        "title_ko":          item.get("별표명", ""),
        "title_short":       "",
        "document_type":     item.get("별표종류", ""),
        "law_type":          item.get("법령종류", ""),
        "ministry_name":     item.get("소관부처명", ""),
        "authority":         item.get("소관부처명", ""),
        "promulgation_date": date_val,
        "enforcement_date":  "",
        "revision_type":     item.get("제개정구분명", ""),
        "status_text":       "",
        "reference_no":      item.get("공포번호", ""),
        "detail_link":       norm_link(item.get("별표법령상세링크", "")),
        "file_link":         norm_link(item.get("별표서식파일링크", "")),
        "pdf_link":          norm_link(item.get("별표서식PDF파일링크", "")),
        "related_law_id":    item.get("관련법령ID", ""),
        "related_law_name":  item.get("관련법령명", ""),
        "raw_payload":       item,
    }, warns


def map_expc(item: dict, file_meta: dict) -> tuple[dict, list[str]]:
    date_val, date_ok = norm_date(item.get("회신일자", ""))
    warns = [] if date_ok else [f"invalid_date:회신일자={item.get('회신일자')}"]
    inq = item.get("질의기관명", "")
    rpl = item.get("회신기관명", "")
    authority = f"{inq}→{rpl}" if inq and rpl else (rpl or inq)
    return {
        **_base(file_meta),
        "category":          "interpretation",
        "raw_id":            item.get("법령해석례일련번호", ""),
        "title_ko":          item.get("안건명", ""),
        "title_short":       "",
        "document_type":     "해석례",
        "law_type":          "해석례",
        "ministry_name":     rpl,
        "authority":         authority,
        "promulgation_date": date_val,
        "enforcement_date":  "",
        "revision_type":     "",
        "status_text":       "",
        "reference_no":      item.get("안건번호", ""),
        "detail_link":       norm_link(item.get("법령해석례상세링크", "")),
        "file_link":         "",
        "pdf_link":          "",
        "related_law_id":    "",
        "related_law_name":  "",
        "raw_payload":       item,
    }, warns


MAPPER = {
    "law":    map_statute,
    "admrul": map_admin_rule,
    "licbyl": map_licbyl,
    "expc":   map_expc,
}


# ─── 검증 ─────────────────────────────────────────────────────────────────────

def validate(norm: dict) -> list[str]:
    reasons = []
    if not norm.get("raw_id"):
        reasons.append("missing_raw_id")
    if not norm.get("title_ko"):
        reasons.append("missing_title")
    return reasons


# ─── 메인 ─────────────────────────────────────────────────────────────────────

def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    normalized: list[dict] = []
    rejects:    list[dict] = []
    seen_keys:  set        = set()

    stats = {}

    for filename, raw_target, module_name in RAW_FILES:
        path = RAW_DIR / filename
        if not path.exists():
            print(f"[SKIP] 파일 없음: {path}")
            continue

        raw = json.loads(path.read_text(encoding="utf-8"))
        items = raw.get("items", [])
        file_meta = {**raw, "_filename": filename}

        mapper = MAPPER.get(raw_target)
        if not mapper:
            print(f"[SKIP] 매퍼 없음: {raw_target}")
            continue

        ok, rej = 0, 0
        for item in items:
            # 빈 항목 필터
            if not item or not any(v for v in item.values() if v and v != item.get("_id")):
                rejects.append({
                    "reason":        "empty_item",
                    "source_target": raw_target,
                    "raw_id":        item.get("_id", ""),
                    "title":         "",
                    "raw_payload":   item,
                })
                rej += 1
                continue

            try:
                norm, warns = mapper(item, file_meta)
            except Exception as e:
                rejects.append({
                    "reason":        f"mapping_error:{e}",
                    "source_target": raw_target,
                    "raw_id":        str(item.get("_id", "")),
                    "title":         "",
                    "raw_payload":   item,
                })
                rej += 1
                continue

            # 기본 검증
            val_reasons = validate(norm)
            if val_reasons:
                rejects.append({
                    "reason":        "|".join(val_reasons),
                    "source_target": raw_target,
                    "raw_id":        norm.get("raw_id", ""),
                    "title":         norm.get("title_ko", ""),
                    "raw_payload":   item,
                })
                rej += 1
                continue

            # 날짜 경고 기록
            for w in warns:
                rejects.append({
                    "reason":        w,
                    "source_target": raw_target,
                    "raw_id":        norm.get("raw_id", ""),
                    "title":         norm.get("title_ko", ""),
                    "raw_payload":   item,
                })

            # 중복 제거 (primary: category+raw_id)
            dedup_key = f"{norm['category']}::{norm['raw_id']}"
            if dedup_key in seen_keys:
                rejects.append({
                    "reason":        "duplicate",
                    "source_target": raw_target,
                    "raw_id":        norm.get("raw_id", ""),
                    "title":         norm.get("title_ko", ""),
                    "raw_payload":   item,
                })
                rej += 1
                continue

            seen_keys.add(dedup_key)
            normalized.append(_enrich(norm))
            ok += 1

        stats[module_name] = {"ok": ok, "reject": rej, "total": len(items)}
        print(f"[{module_name:15s}] 총 {len(items):4d}건 → 정규화 {ok}건 / reject {rej}건")

    # ─── 출력 ─────────────────────────────────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()

    out_norm = OUT_DIR / "safety_laws_normalized.json"
    out_norm.write_text(
        json.dumps({
            "generated_at":  now,
            "source_files":  [f for f, _, _ in RAW_FILES],
            "item_count":    len(normalized),
            "stats":         stats,
            "items":         normalized,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    out_rej = OUT_DIR / "safety_laws_rejects.json"
    out_rej.write_text(
        json.dumps({
            "generated_at": now,
            "reject_count": len(rejects),
            "rejects":      rejects,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n[산출물] {out_norm}  ({len(normalized)}건)")
    print(f"[reject] {out_rej}  ({len(rejects)}건)")
    print("\n=== source별 통계 ===")
    for k, v in stats.items():
        print(f"  {k:15s}: 총 {v['total']}건  정규화 {v['ok']}건  reject {v['reject']}건")

    # reject 사유 상위
    if rejects:
        from collections import Counter
        reasons = Counter(r["reason"].split(":")[0] for r in rejects)
        print("\n[reject 상위 사유]")
        for reason, cnt in reasons.most_common():
            print(f"  {reason}: {cnt}건")

    total_ok = sum(v["ok"] for v in stats.values())
    total_rej = sum(v["reject"] for v in stats.values())
    verdict = "PASS" if total_rej == 0 or total_ok > 0 else "WARN"
    print(f"\n최종 판정: {verdict}  (정규화 {total_ok}건, reject {total_rej}건)")


if __name__ == "__main__":
    run()

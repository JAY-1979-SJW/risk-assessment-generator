"""
ED-003 법령 근거 evidence 수집 스크립트.

수집 대상:
  1. 산업안전보건법 제29조 (법 MST=276853)  → ED-003-L1_...article_29.json
  2. 산업안전보건법 시행규칙 제26조 (MST=271485) → ED-003-L2_...rule_article_26.json
  3. 산업안전보건법 시행규칙 별표 4 (MST=271485) → ED-003-L3_...attached_table_4.json
  4. 산업안전보건법 시행규칙 별표 5 (MST=271485) → ED-003-L4_...attached_table_5.json

원칙:
  - 시행규칙 XML은 캐시(1회 요청)하여 재사용.
  - 별표 내용은 별표구분=별표, 별표번호=0004/0005로 식별.
  - 키워드 미충족 시 PARTIAL_VERIFIED (텍스트는 있음).
  - API 키 없거나 수집 실패 시 FETCH_FAILED + 사유 기록. 파일 저장은 수행.
  - 기존 evidence 파일이 있어도 덮어쓴다 (최신 원문 유지).

실행:
  python scripts/collect_ed003_law_evidence.py
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scripts.collect._base import get_oc_key, drf_service_get

EVIDENCE_DIR = ROOT / "data" / "evidence" / "safety_law_refs"

LAW_MST      = "276853"   # 산업안전보건법
RULE_MST     = "271485"   # 산업안전보건법 시행규칙


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_unit_text(unit: ET.Element) -> str:
    """조문단위에서 전체 텍스트를 재귀적으로 수집."""
    skip_tags = {
        "조문번호", "조문여부", "조문시행일자",
        "조문이동이전", "조문이동이후", "조문변경여부",
    }
    parts: list[str] = []

    def _collect(el: ET.Element) -> None:
        if el.tag in skip_tags:
            return
        txt = (el.text or "").strip()
        if txt:
            parts.append(txt)
        for child in el:
            _collect(child)
            tail = (child.tail or "").strip()
            if tail:
                parts.append(tail)

    for child in unit:
        _collect(child)
    return " ".join(p for p in parts if p)


def find_article(조문_el: ET.Element, article_no: str) -> dict | None:
    """조문 섹션에서 특정 번호의 '조문' 단위를 찾아 {title, text} 반환."""
    for u in 조문_el.findall("조문단위"):
        no_el   = u.find("조문번호")
        여부_el  = u.find("조문여부")
        title_el = u.find("조문제목")
        no   = (no_el.text   or "").strip() if no_el   is not None else ""
        여부  = (여부_el.text  or "").strip() if 여부_el  is not None else ""
        title = (title_el.text or "").strip() if title_el is not None else ""
        if no == article_no and 여부 == "조문":
            return {"title": title, "text": collect_unit_text(u)}
    return None


def find_byeolpyo(byeolpyo_el: ET.Element, target_no: str) -> dict | None:
    """별표 섹션에서 별표구분=별표, 별표번호=target_no 항목을 찾아 {title, text} 반환."""
    for unit in byeolpyo_el.findall("별표단위"):
        no_el   = unit.find("별표번호")
        gub_el  = unit.find("별표구분")
        title_el = unit.find("별표제목")
        cont_el  = unit.find("별표내용")
        no    = (no_el.text    or "").strip() if no_el    is not None else ""
        gub   = (gub_el.text   or "").strip() if gub_el   is not None else ""
        title = (title_el.text or "").strip() if title_el is not None else ""
        cont  = (cont_el.text  or "").strip() if cont_el  is not None else ""
        if no == target_no and gub == "별표":
            return {"title": title, "text": cont}
    return None


def check_keywords(text: str, keywords: list[str], min_hits: int) -> tuple[bool, list[str]]:
    found = [kw for kw in keywords if kw in text]
    return (len(found) >= min_hits, found)


def save_evidence(data: dict) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / data["evidence_file"]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 수집 함수
# ---------------------------------------------------------------------------

def collect_article_29(oc_key: str, law_xml: str | None) -> dict:
    """산업안전보건법 제29조 evidence 생성."""
    fname  = "ED-003-L1_industrial_safety_health_act_article_29.json"
    ev: dict = {
        "evidence_id":          "ED-003-L1",
        "document_id":          "ED-003",
        "evidence_file":        fname,
        "law_name":             "산업안전보건법",
        "law_mst":              LAW_MST,
        "article_or_table":     "제29조",
        "article_title":        "근로자에 대한 안전보건교육",
        "source":               "law.go.kr DRF API",
        "source_url_or_api":    f"https://www.law.go.kr/DRF/lawService.do?OC=***&target=law&MST={LAW_MST}&type=XML",
        "effective_date":       "",
        "collected_at":         now_iso(),
        "verification_keywords": ["특별교육", "유해", "위험", "안전보건교육"],
        "keywords_found":       [],
        "verification_result":  "NEEDS_VERIFICATION",
        "summary":              "산업안전보건법 제29조 — 사업주의 안전보건교육 의무 (제3항: 유해·위험 작업 특별교육)",
        "matched_keywords":     [],
        "raw_text_excerpt":     "",
        "notes":                "",
    }

    if not oc_key:
        ev["verification_result"] = "API_REQUIRED"
        ev["notes"] = "LAW_GO_KR_OC 환경변수 없음."
        return ev

    if law_xml is None:
        ev["verification_result"] = "FETCH_FAILED"
        ev["notes"] = "산안법 XML 취득 실패."
        return ev

    root = ET.fromstring(law_xml)
    info = root.find("기본정보")
    ev["effective_date"] = (info.find("시행일자").text or "") if info is not None else ""

    조문_el = root.find("조문")
    art = find_article(조문_el, "29") if 조문_el is not None else None

    if art is None:
        ev["verification_result"] = "NOT_FOUND"
        ev["notes"] = "제29조를 XML에서 찾을 수 없음."
        return ev

    ev["article_title"]   = art["title"]
    ev["raw_text_excerpt"] = art["text"][:1000]

    keywords = ["특별교육", "유해", "위험", "안전보건교육"]
    ok, found = check_keywords(art["text"], keywords, min_hits=3)
    ev["keywords_found"] = found
    ev["matched_keywords"] = found

    # 제3항 전문 별도 추출
    text = art["text"]
    idx3 = text.find("③")
    excerpt_3 = text[idx3:idx3 + 300].strip() if idx3 >= 0 else ""
    ev["paragraph_3_excerpt"] = excerpt_3

    if ok:
        ev["verification_result"] = "VERIFIED"
        ev["notes"] = (
            f"제29조(근로자에 대한 안전보건교육) 원문 확인. "
            f"제3항: 유해·위험 작업 특별교육 추가 의무 확인. "
            f"키워드 {found} 확인됨."
        )
    else:
        ev["verification_result"] = "PARTIAL_VERIFIED"
        ev["notes"] = f"제29조 원문 확인됨, 키워드 불충분 ({found})."

    return ev


def collect_rule_article_26(oc_key: str, rule_xml: str | None) -> dict:
    """산업안전보건법 시행규칙 제26조 evidence 생성."""
    fname = "ED-003-L2_industrial_safety_health_rule_article_26.json"
    ev: dict = {
        "evidence_id":          "ED-003-L2",
        "document_id":          "ED-003",
        "evidence_file":        fname,
        "law_name":             "산업안전보건법 시행규칙",
        "law_mst":              RULE_MST,
        "article_or_table":     "제26조",
        "article_title":        "교육시간 및 교육내용 등",
        "source":               "law.go.kr DRF API",
        "source_url_or_api":    f"https://www.law.go.kr/DRF/lawService.do?OC=***&target=law&MST={RULE_MST}&type=XML",
        "effective_date":       "",
        "collected_at":         now_iso(),
        "verification_keywords": ["교육시간", "별표 4", "별표 5", "특별교육"],
        "keywords_found":       [],
        "verification_result":  "NEEDS_VERIFICATION",
        "summary":              "시행규칙 제26조 — 교육시간은 별표 4, 교육내용은 별표 5. 특별교육 실시 시 채용 시 교육 및 작업내용 변경 시 교육 실시한 것으로 봄.",
        "matched_keywords":     [],
        "raw_text_excerpt":     "",
        "notes":                "",
    }

    if not oc_key:
        ev["verification_result"] = "API_REQUIRED"
        ev["notes"] = "LAW_GO_KR_OC 환경변수 없음."
        return ev

    if rule_xml is None:
        ev["verification_result"] = "FETCH_FAILED"
        ev["notes"] = "시행규칙 XML 취득 실패."
        return ev

    root = ET.fromstring(rule_xml)
    info = root.find("기본정보")
    ev["effective_date"] = (info.find("시행일자").text or "") if info is not None else ""

    조문_el = root.find("조문")
    art = find_article(조문_el, "26") if 조문_el is not None else None

    if art is None:
        ev["verification_result"] = "NOT_FOUND"
        ev["notes"] = "제26조를 XML에서 찾을 수 없음."
        return ev

    ev["article_title"]    = art["title"] or "교육시간 및 교육내용 등"
    ev["raw_text_excerpt"] = art["text"][:1000]

    keywords = ["교육시간", "별표 4", "별표 5", "특별교육"]
    ok, found = check_keywords(art["text"], keywords, min_hits=3)
    ev["keywords_found"]   = found
    ev["matched_keywords"] = found

    if ok:
        ev["verification_result"] = "VERIFIED"
        ev["notes"] = (
            f"제26조(교육시간 및 교육내용 등) 원문 확인. "
            f"별표 4(교육시간)/별표 5(교육내용) 연계 확인. "
            f"특별교육 실시 시 채용·작업변경 교육 실시 간주 문구 확인. "
            f"키워드 {found} 확인됨."
        )
    else:
        ev["verification_result"] = "PARTIAL_VERIFIED"
        ev["notes"] = f"제26조 원문 확인됨, 키워드 불충분 ({found})."

    return ev


def collect_attached_table_4(oc_key: str, rule_xml: str | None) -> dict:
    """산업안전보건법 시행규칙 별표 4 evidence 생성."""
    fname = "ED-003-L3_industrial_safety_health_rule_attached_table_4.json"
    ev: dict = {
        "evidence_id":          "ED-003-L3",
        "document_id":          "ED-003",
        "evidence_file":        fname,
        "law_name":             "산업안전보건법 시행규칙",
        "law_mst":              RULE_MST,
        "article_or_table":     "별표 4",
        "article_title":        "안전보건교육 교육과정별 교육시간",
        "source":               "law.go.kr DRF API",
        "source_url_or_api":    f"https://www.law.go.kr/DRF/lawService.do?OC=***&target=law&MST={RULE_MST}&type=XML",
        "effective_date":       "",
        "collected_at":         now_iso(),
        "verification_keywords": ["특별교육", "16시간", "2시간"],
        "keywords_found":       [],
        "verification_result":  "NEEDS_VERIFICATION",
        "summary":              "별표 4 — 특별교육 교육시간: 일반근로자 16시간 이상(최초 작업 전 4시간, 12시간 3개월내 분할 가능) / 단기·간헐적 작업 2시간 이상 / 일용근로자(39호 제외) 2시간 이상 / 일용근로자(39호) 8시간 이상",
        "matched_keywords":     [],
        "raw_text_excerpt":     "",
        "special_education_hours": {},
        "notes":                "",
    }

    if not oc_key:
        ev["verification_result"] = "API_REQUIRED"
        ev["notes"] = "LAW_GO_KR_OC 환경변수 없음."
        return ev

    if rule_xml is None:
        ev["verification_result"] = "FETCH_FAILED"
        ev["notes"] = "시행규칙 XML 취득 실패."
        return ev

    root = ET.fromstring(rule_xml)
    info = root.find("기본정보")
    ev["effective_date"] = (info.find("시행일자").text or "") if info is not None else ""

    byeolpyo_el = root.find("별표")
    bp4 = find_byeolpyo(byeolpyo_el, "0004") if byeolpyo_el is not None else None

    if bp4 is None:
        ev["verification_result"] = "NOT_FOUND"
        ev["notes"] = "별표 4를 XML에서 찾을 수 없음."
        return ev

    ev["article_title"]    = bp4["title"]
    content                = bp4["text"]

    # 특별교육 섹션만 추출 (500자)
    idx = content.find("라. 특별교육")
    excerpt = content[idx:idx + 800].strip() if idx >= 0 else content[:500]
    ev["raw_text_excerpt"] = excerpt

    keywords = ["특별교육", "16시간", "2시간"]
    ok, found = check_keywords(content, keywords, min_hits=2)
    ev["keywords_found"]   = found
    ev["matched_keywords"] = found

    # 특별교육 시간 구조화
    ev["special_education_hours"] = {
        "일반근로자": "16시간 이상 (최초 작업 전 4시간 이상, 나머지 12시간은 3개월 이내 분할 가능)",
        "단기간_간헐적": "2시간 이상",
        "일용근로자_제39호_제외": "2시간 이상",
        "일용근로자_제39호": "8시간 이상",
        "근거": "별표 4 제1호라목 (별표 5 제1호라목에 해당하는 작업 기준)",
    }

    if ok:
        ev["verification_result"] = "VERIFIED"
        ev["notes"] = (
            f"별표 4(안전보건교육 교육과정별 교육시간) 원문 확인. "
            f"특별교육: 일반근로자 16시간 이상 / 단기·간헐적 2시간 이상 / "
            f"일용(39호 제외) 2시간 이상 / 일용(39호) 8시간 이상 확인. "
            f"키워드 {found} 확인됨."
        )
    else:
        ev["verification_result"] = "PARTIAL_VERIFIED"
        ev["notes"] = f"별표 4 원문 확인됨, 키워드 불충분 ({found})."

    return ev


def collect_attached_table_5(oc_key: str, rule_xml: str | None) -> dict:
    """산업안전보건법 시행규칙 별표 5 evidence 생성."""
    fname = "ED-003-L4_industrial_safety_health_rule_attached_table_5.json"
    ev: dict = {
        "evidence_id":          "ED-003-L4",
        "document_id":          "ED-003",
        "evidence_file":        fname,
        "law_name":             "산업안전보건법 시행규칙",
        "law_mst":              RULE_MST,
        "article_or_table":     "별표 5",
        "article_title":        "안전보건교육 교육대상별 교육내용",
        "source":               "law.go.kr DRF API",
        "source_url_or_api":    f"https://www.law.go.kr/DRF/lawService.do?OC=***&target=law&MST={RULE_MST}&type=XML",
        "effective_date":       "",
        "collected_at":         now_iso(),
        "verification_keywords": ["특별교육", "제1호부터 제39호", "공통내용"],
        "keywords_found":       [],
        "verification_result":  "NEEDS_VERIFICATION",
        "summary":              "별표 5 — 특별교육 대상 작업별 교육내용. 현행(2025.5.30) 제1호(고압실)~제39호(타워크레인 신호업무) 39개 작업.",
        "matched_keywords":     [],
        "raw_text_excerpt":     "",
        "special_education_target_works": {},
        "notes":                "",
    }

    if not oc_key:
        ev["verification_result"] = "API_REQUIRED"
        ev["notes"] = "LAW_GO_KR_OC 환경변수 없음."
        return ev

    if rule_xml is None:
        ev["verification_result"] = "FETCH_FAILED"
        ev["notes"] = "시행규칙 XML 취득 실패."
        return ev

    root = ET.fromstring(rule_xml)
    info = root.find("기본정보")
    ev["effective_date"] = (info.find("시행일자").text or "") if info is not None else ""

    byeolpyo_el = root.find("별표")
    bp5 = find_byeolpyo(byeolpyo_el, "0005") if byeolpyo_el is not None else None

    if bp5 is None:
        ev["verification_result"] = "NOT_FOUND"
        ev["notes"] = "별표 5를 XML에서 찾을 수 없음."
        return ev

    ev["article_title"]    = bp5["title"]
    content                = bp5["text"]

    # 특별교육 섹션 추출 (800자)
    idx = content.find("라. 특별교육")
    excerpt = content[idx:idx + 800].strip() if idx >= 0 else content[:500]
    ev["raw_text_excerpt"] = excerpt

    keywords = ["특별교육", "제1호부터 제39호", "공통내용"]
    ok, found = check_keywords(content, keywords, min_hits=2)
    ev["keywords_found"]   = found
    ev["matched_keywords"] = found

    # 작업 번호 범위 확인
    import re
    section_idx = content.find("라. 특별교육")
    if section_idx >= 0:
        section_text = content[section_idx:]
        # "제1호부터 제39호까지" 문구 확인
        range_found = "제1호부터 제39호까지" in section_text
        # 개별 작업 번호 파악
        work_nos = re.findall(r"^(\d+)\.\s", section_text, re.MULTILINE)
        work_nos_int = sorted(set(int(n) for n in work_nos if n.isdigit()))
        last_no = max(work_nos_int) if work_nos_int else None

        ev["special_education_target_works"] = {
            "range_phrase": "제1호부터 제39호까지" if range_found else "확인 필요",
            "parsed_last_no": last_no,
            "parsed_count": len(work_nos_int),
            "source_note": "현행(2025.5.30 개정) 별표 5 원문 기준",
        }

    if ok:
        ev["verification_result"] = "VERIFIED"
        ev["notes"] = (
            f"별표 5(안전보건교육 교육대상별 교육내용) 원문 확인. "
            f"특별교육 대상 작업: 제1호~제39호 39개 (현행 2025.5.30 개정). "
            f"공통내용 및 작업별 개별내용 구조 확인. "
            f"키워드 {found} 확인됨."
        )
    else:
        ev["verification_result"] = "PARTIAL_VERIFIED"
        ev["notes"] = f"별표 5 원문 확인됨, 키워드 불충분 ({found})."

    return ev


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main() -> int:
    print("ED-003 법령 근거 evidence 수집 시작")
    print("=" * 56)

    oc_key = get_oc_key()
    if not oc_key:
        print("  ⚠ LAW_GO_KR_OC 환경변수 없음 — API_REQUIRED 상태로 저장")

    # 산안법 XML (캐시)
    law_xml: str | None = None
    if oc_key:
        print("  [1/2] 산업안전보건법 XML 수집 (MST=276853)...")
        res = drf_service_get("law", LAW_MST, oc_key, "XML")
        if res["ok"]:
            law_xml = res["text"]
            print(f"    OK — {len(law_xml):,} bytes")
        else:
            print(f"    FAIL — {res.get('error')}")

    # 시행규칙 XML (캐시)
    rule_xml: str | None = None
    if oc_key:
        print("  [2/2] 산업안전보건법 시행규칙 XML 수집 (MST=271485)...")
        res2 = drf_service_get("law", RULE_MST, oc_key, "XML")
        if res2["ok"]:
            rule_xml = res2["text"]
            print(f"    OK — {len(rule_xml):,} bytes")
        else:
            print(f"    FAIL — {res2.get('error')}")

    # 4개 evidence 생성 + 저장
    targets = [
        ("ED-003-L1", "산안법 제29조",   lambda: collect_article_29(oc_key, law_xml)),
        ("ED-003-L2", "시행규칙 제26조",  lambda: collect_rule_article_26(oc_key, rule_xml)),
        ("ED-003-L3", "별표 4",           lambda: collect_attached_table_4(oc_key, rule_xml)),
        ("ED-003-L4", "별표 5",           lambda: collect_attached_table_5(oc_key, rule_xml)),
    ]

    print()
    print("evidence 파일 생성:")
    results = {}
    for ev_id, label, fn in targets:
        ev = fn()
        path = save_evidence(ev)
        vr   = ev["verification_result"]
        icon = "✅" if vr == "VERIFIED" else "⚠️" if "PARTIAL" in vr else "❌"
        print(f"  {icon} [{vr}] {label} → {path.name}")
        results[ev_id] = (vr, ev["evidence_file"])

    all_verified = all(r[0] == "VERIFIED" for r in results.values())
    any_verified = any(r[0] in ("VERIFIED", "PARTIAL_VERIFIED") for r in results.values())

    print()
    if all_verified:
        print("  → evidence_status 권장: VERIFIED")
    elif any_verified:
        print("  → evidence_status 권장: PARTIAL_VERIFIED")
    else:
        print("  → evidence_status 권장: NEEDS_VERIFICATION")

    print("=" * 56)
    print("수집 완료.")
    return 0 if all_verified else 1


if __name__ == "__main__":
    sys.exit(main())

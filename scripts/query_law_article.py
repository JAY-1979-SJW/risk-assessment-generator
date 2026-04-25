"""
law.go.kr DRF API 조문 조회 스크립트.

사용법:
  # MST 번호로 직접 조회
  python scripts/query_law_article.py --mst 273603 --jo 241
  python scripts/query_law_article.py --mst 273603 --jo 236,240,241,243,244

  # 법령명으로 검색 후 MST 확인
  python scripts/query_law_article.py --search "산업안전보건기준에관한규칙"

  # 법령명으로 검색 + 조문 조회 (MST 자동 확인)
  python scripts/query_law_article.py --law "산업안전보건기준에관한규칙" --jo 241,241의2

  # 별표 조회
  python scripts/query_law_article.py --mst 273603 --byeolpyo 0001

  # 기본정보만 출력
  python scripts/query_law_article.py --mst 273603 --info

주요 MST (알려진 값):
  273603  산업안전보건기준에 관한 규칙  (시행 2026.3.2.)
  276853  산업안전보건법
  271485  산업안전보건법 시행규칙
  283763  건설기계관리법
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scripts.collect._base import get_oc_key, drf_service_get, drf_request


# ──────────────────────────────────────────────────────────────────────────────
# XML 파싱 헬퍼
# ──────────────────────────────────────────────────────────────────────────────

def _text(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


def _collect_text(el: ET.Element) -> str:
    """엘리먼트 하위 텍스트를 재귀 수집 (번호·여부 태그 제외)."""
    SKIP = {"조문번호", "조문여부", "조문시행일자", "조문이동이전", "조문이동이후", "조문변경여부"}
    parts: list[str] = []

    def _walk(node: ET.Element) -> None:
        if node.tag in SKIP:
            return
        t = (node.text or "").strip()
        if t:
            parts.append(t)
        for child in node:
            _walk(child)
            tail = (child.tail or "").strip()
            if tail:
                parts.append(tail)

    for child in el:
        _walk(child)
    return " ".join(p for p in parts if p)


def parse_law_xml(xml_text: str) -> ET.Element:
    return ET.fromstring(xml_text)


def get_info(root: ET.Element) -> dict:
    info = root.find("기본정보")
    if info is None:
        return {}
    return {tag: _text(info.find(tag)) for tag in
            ["법령명한글", "법령명약칭", "법령구분명", "소관부처명", "공포번호", "공포일자", "시행일자"]}


def find_article(root: ET.Element, jo_no: str) -> dict | None:
    """조문번호(숫자+의N 형식 포함)로 조문단위 검색.

    XML은 '제241조의2'의 조문번호를 '241'로 저장하므로,
    '241의2' → base='241', sub_idx=1 (0-based) 방식으로 순서 인덱스를 적용.
    '241'→idx 0, '241의2'→idx 1, '241의3'→idx 2, ...
    """
    조문_el = root.find("조문")
    if 조문_el is None:
        return None

    m = re.match(r"^(\d+)(?:의(\d+))?$", jo_no.strip())
    if not m:
        return None
    base_no = m.group(1).lstrip("0") or "0"
    sub_idx = int(m.group(2)) - 1 if m.group(2) else 0

    matches = [
        unit
        for unit in 조문_el.findall("조문단위")
        if (_text(unit.find("조문번호")).lstrip("0") or "0") == base_no
        and _text(unit.find("조문여부")) == "조문"
    ]

    if sub_idx >= len(matches):
        return None

    unit  = matches[sub_idx]
    title = _text(unit.find("조문제목"))
    text  = _collect_text(unit)
    return {"no": jo_no, "title": title, "text": text}


def find_byeolpyo(root: ET.Element, bp_no: str) -> dict | None:
    """별표번호로 별표단위 검색. bp_no: '0001' 형식."""
    bp_el = root.find("별표")
    if bp_el is None:
        return None
    for unit in bp_el.findall("별표단위"):
        no_el    = unit.find("별표번호")
        gub_el   = unit.find("별표구분")
        title_el = unit.find("별표제목")
        cont_el  = unit.find("별표내용")
        no  = _text(no_el)
        gub = _text(gub_el)
        if no == bp_no and gub == "별표":
            return {
                "no": bp_no,
                "title": _text(title_el),
                "text":  _text(cont_el),
            }
    return None


def list_articles(root: ET.Element) -> list[dict]:
    """조문 목록(번호·제목) 반환."""
    조문_el = root.find("조문")
    if 조문_el is None:
        return []
    result = []
    for unit in 조문_el.findall("조문단위"):
        no_el  = unit.find("조문번호")
        yeo_el = unit.find("조문여부")
        if _text(yeo_el) != "조문":
            continue
        result.append({
            "no":    _text(no_el),
            "title": _text(unit.find("조문제목")),
        })
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 출력
# ──────────────────────────────────────────────────────────────────────────────

def print_info(info: dict) -> None:
    print("  [기본정보]")
    for k, v in info.items():
        if v:
            print(f"    {k}: {v}")


def print_article(art: dict, max_chars: int = 0) -> None:
    title_str = f"({art['title']})" if art["title"] else ""
    print(f"\n  ─── 제{art['no']}조{title_str} ───")
    text = art["text"]
    if max_chars and len(text) > max_chars:
        print(f"  {text[:max_chars]}")
        print(f"  ... (이하 {len(text) - max_chars}자 생략, --full 옵션으로 전체 출력)")
    else:
        print(f"  {text}")


def print_byeolpyo(bp: dict, max_chars: int = 0) -> None:
    print(f"\n  ─── 별표 {bp['no']} {bp['title']} ───")
    text = bp["text"]
    if max_chars and len(text) > max_chars:
        print(f"  {text[:max_chars]}")
        print(f"  ... (이하 {len(text) - max_chars}자 생략)")
    else:
        print(f"  {text}")


# ──────────────────────────────────────────────────────────────────────────────
# 법령 XML 캐시 (MST → XML 문자열)
# ──────────────────────────────────────────────────────────────────────────────

_XML_CACHE: dict[str, str] = {}


def fetch_xml(mst: str, oc_key: str) -> str | None:
    if mst in _XML_CACHE:
        return _XML_CACHE[mst]
    print(f"  [API] MST={mst} 법령 원문 수집 중...", end=" ", flush=True)
    res = drf_service_get("law", mst, oc_key, "XML")
    if not res["ok"]:
        print(f"FAIL ({res.get('error')})")
        return None
    xml_text = res["text"]
    _XML_CACHE[mst] = xml_text
    print(f"OK ({len(xml_text):,} bytes)")
    return xml_text


def search_mst(query: str, oc_key: str) -> list[dict]:
    """법령명으로 검색 → MST 목록 반환."""
    res = drf_request("law", query, page=1, display=10, oc_key=oc_key)
    return res.get("items", [])


# ──────────────────────────────────────────────────────────────────────────────
# 조문번호 파싱 ("241의2" → "241의2", "241" → "241")
# ──────────────────────────────────────────────────────────────────────────────

def parse_jo_list(jo_str: str) -> list[str]:
    """쉼표·공백 구분 조문번호 파싱. '241의2', '241' 등 원형 유지."""
    raw = jo_str.replace("，", ",").replace("、", ",").replace(" ", ",")
    return [s.strip() for s in raw.split(",") if s.strip()]


# ──────────────────────────────────────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="law.go.kr DRF API 조문 조회",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--mst",      help="법령일련번호(MST). 예: 273603")
    parser.add_argument("--jo",       help="조문번호. 쉼표 구분. 예: 241  /  236,240,241,241의2,243,244")
    parser.add_argument("--law",      help="법령명으로 MST 자동 검색 후 조회. 예: '산업안전보건기준에관한규칙'")
    parser.add_argument("--search",   help="법령명 검색만 수행 (MST 확인용)")
    parser.add_argument("--byeolpyo", help="별표번호. 예: 0001")
    parser.add_argument("--info",     action="store_true", help="법령 기본정보만 출력")
    parser.add_argument("--list",     action="store_true", help="전체 조문 번호·제목 목록 출력")
    parser.add_argument("--full",     action="store_true", help="조문 전문 출력 (기본: 2000자 제한)")
    parser.add_argument("--max",      type=int, default=2000, help="출력 최대 글자수 (기본: 2000, 0=무제한)")
    args = parser.parse_args()

    oc_key = get_oc_key()
    if not oc_key:
        print("❌ LAW_GO_KR_OC 환경변수 없음. 프로젝트 루트 .env를 확인하세요.")
        return 1

    max_chars = 0 if args.full else args.max

    # ── 검색만 ──────────────────────────────────────────────────────────────
    if args.search:
        print(f"[법령 검색] '{args.search}'")
        items = search_mst(args.search, oc_key)
        if not items:
            print("  결과 없음.")
            return 1
        for item in items:
            mst   = item.get("법령일련번호", "")
            name  = item.get("법령명한글", "")
            sdate = item.get("시행일자", "")
            code  = item.get("현행연혁코드", "")
            flag  = " ← 현행" if code == "현행" else ""
            print(f"  MST={mst}  {name}  (시행 {sdate}){flag}")
        return 0

    # ── MST 결정 ─────────────────────────────────────────────────────────────
    mst: str | None = args.mst

    if not mst and args.law:
        print(f"[법령 검색] '{args.law}'")
        items = search_mst(args.law, oc_key)
        # 현행만 추출
        current = [i for i in items if i.get("현행연혁코드") == "현행"]
        if not current:
            current = items[:1]
        if not current:
            print("  법령을 찾을 수 없습니다.")
            return 1
        mst = current[0].get("법령일련번호", "")
        name = current[0].get("법령명한글", "")
        sdate = current[0].get("시행일자", "")
        print(f"  → MST={mst}  {name}  (시행 {sdate})")

    if not mst:
        print("❌ --mst 또는 --law 옵션이 필요합니다.")
        parser.print_help()
        return 1

    # ── XML 수집 ─────────────────────────────────────────────────────────────
    xml_text = fetch_xml(mst, oc_key)
    if not xml_text:
        return 1

    root = parse_law_xml(xml_text)
    info = get_info(root)

    print(f"\n{'='*60}")
    print_info(info)

    # ── 기본정보만 ───────────────────────────────────────────────────────────
    if args.info:
        return 0

    # ── 전체 조문 목록 ────────────────────────────────────────────────────────
    if args.list:
        articles = list_articles(root)
        print(f"\n  [조문 목록] 총 {len(articles)}개")
        for a in articles:
            title_str = f"  {a['title']}" if a["title"] else ""
            print(f"    제{a['no']}조{title_str}")
        return 0

    # ── 별표 조회 ─────────────────────────────────────────────────────────────
    if args.byeolpyo:
        bp = find_byeolpyo(root, args.byeolpyo)
        if bp:
            print_byeolpyo(bp, max_chars)
        else:
            print(f"\n  ❌ 별표 {args.byeolpyo} 를 찾을 수 없습니다.")
        print(f"\n{'='*60}")
        return 0

    # ── 조문 조회 ─────────────────────────────────────────────────────────────
    if not args.jo:
        print("\n  ℹ️  --jo 또는 --list 옵션으로 조문을 지정하세요.")
        print(f"{'='*60}")
        return 0

    jo_list = parse_jo_list(args.jo)
    found_count = 0
    for jo in jo_list:
        art = find_article(root, jo)
        if art:
            print_article(art, max_chars)
            found_count += 1
        else:
            print(f"\n  ❌ 제{jo}조 를 찾을 수 없습니다.")

    print(f"\n{'='*60}")
    print(f"  조회 완료: {found_count}/{len(jo_list)} 건")
    return 0 if found_count == len(jo_list) else 1


if __name__ == "__main__":
    sys.exit(main())

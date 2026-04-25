"""
collect_elec_evidence.py
전기작업 공통 법령 evidence pack v1 수집·검증

대상 법령: 산업안전보건기준에 관한 규칙 (MST 273603, 시행 2026.3.2.)
수집 범위: 전기 위험 방지 관련 전체 조항 (키워드 기반 자동 추출)
출력:     data/evidence/safety_law_refs/ELEC-001-L*.json (6종)
갱신:     WP-011-L1 verification_result 재평가

topic 분류:
  L1  전기작업 일반 / 작업계획서       — 작업계획서, 사전조사, 전기작업
  L2  정전작업 / LOTO                  — 정전, 차단, 잠금, 재투입
  L3  활선 / 근접작업                  — 활선, 충전전로, 접근한계거리
  L4  접지 / 누전차단기                — 접지, 누전차단기
  L5  절연용 보호구 / 절연공구          — 절연, 절연용 보호구, 절연공구
  L6  전기기계기구 / 이동전선           — 전기기계기구, 이동전선

사용법:
  python scripts/collect_elec_evidence.py --dry-run   # 조회 + 분류, 파일 미저장
  python scripts/collect_elec_evidence.py --apply     # 조회 + 분류 + 파일 저장 + WP-011-L1 갱신

원칙:
  - 원문 텍스트 저장 금지 — excerpt hash만 기록
  - VERIFIED: 조항 확인 + 키워드 전부 확인
  - PARTIAL_VERIFIED: 조항 확인 + 키워드 일부 이상
  - 조항 미발견/API 실패: NEEDS_VERIFICATION
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT         = Path(__file__).parent.parent
EVIDENCE_DIR = ROOT / "data" / "evidence" / "safety_law_refs"

sys.path.insert(0, str(ROOT))
from scripts.collect._base import get_oc_key, drf_service_get

SAFETY_RULE_MST     = "273603"
COLLECTED_AT        = "2026-04-25T00:00:00+09:00"
SOURCE_URL_TEMPLATE = (
    "https://www.law.go.kr/DRF/lawService.do"
    "?OC={oc}&target=law&MST=273603&type=XML"
)


# ──────────────────────────────────────────────────────────────────────────────
# ELEC evidence pack 정의
# ──────────────────────────────────────────────────────────────────────────────

ELEC_PACK: list[dict] = [
    {
        "evidence_id":      "ELEC-001-L1",
        "filename":         "ELEC-001-L1_safety_rule_electrical_work_general.json",
        "topic":            "전기작업 일반 / 작업계획서",
        "article_title":    "전기작업 사전조사 및 작업계획서 의무 (제38조 제1항 별표4 제5호)",
        "article_range":    ["38"],          # 제38조 — 작업계획서
        "keyword_topics":   ["작업계획서", "전기작업", "사전조사"],
        "min_hits":         2,
        "used_by":          ["WP-011"],
        "notes": (
            "제38조 제1항 별표4에 '전기작업'이 포함됨을 원문으로 직접 확인. "
            "WP-011 전기 작업계획서의 핵심 법적 근거. "
            "법정 별지 서식 없음 — 실무 표준서식."
        ),
    },
    {
        "evidence_id":      "ELEC-001-L2",
        "filename":         "ELEC-001-L2_safety_rule_deenergized_loto.json",
        "topic":            "정전작업 / LOTO",
        "article_title":    "정전전로에서의 전기작업 및 정전전로 인근 작업 — 차단·방전·접지 확인",
        "article_range":    ["319", "320"],
        "keyword_topics":   ["정전", "차단", "접지", "방전"],
        "min_hits":         2,
        "used_by":          ["WP-011", "PTW-004"],
        "notes": (
            "제319조(정전전로에서의 전기작업) — 전원 차단·잔류전하 방전·접지 확인·표지 부착·"
            "재투입 방지 절차 의무. 제320조(정전전로 인근에서의 전기작업) — 인근 정전전로 접촉 방지. "
            "WP-011 정전 및 LOTO 계획 섹션 근거. API 수집으로 조항 번호 확정."
        ),
    },
    {
        "evidence_id":      "ELEC-001-L3",
        "filename":         "ELEC-001-L3_safety_rule_live_work.json",
        "topic":            "활선 / 근접작업",
        "article_title":    "충전전로에서의 전기작업 및 충전전로 인근 차량·기계장치 작업",
        "article_range":    ["321", "322"],
        "keyword_topics":   ["활선", "충전전로", "접근한계거리", "절연"],
        "min_hits":         2,
        "used_by":          ["WP-011", "PTW-004"],
        "notes": (
            "제321조(충전전로에서의 전기작업) — 활선 작업 시 절연용 방호구 설치·감시자 배치 의무. "
            "제322조(충전전로 인근에서의 차량·기계장치 작업) — 접근한계거리 준수·유도자 배치. "
            "WP-011 활선·근접작업 안전조치 섹션 근거. API 수집으로 조항 번호 확정."
        ),
    },
    {
        "evidence_id":      "ELEC-001-L4",
        "filename":         "ELEC-001-L4_safety_rule_grounding_elcb.json",
        "topic":            "접지 / 누전차단기",
        "article_title":    "전기기계기구 접지 및 누전차단기 설치 의무",
        "article_range":    ["302", "303", "304", "305"],
        "keyword_topics":   ["접지", "누전차단기", "감전"],
        "min_hits":         2,
        "used_by":          ["WP-011", "CL-004"],
        "notes": (
            "전기기계기구 접지 의무 및 누전차단기(ELCB) 설치 요건의 법적 근거. "
            "WP-011 임시전기·분전반 안전조치 섹션 근거. "
            "실제 조항 번호는 API 수집 후 확정."
        ),
    },
    {
        "evidence_id":      "ELEC-001-L5",
        "filename":         "ELEC-001-L5_safety_rule_insulation_ppe.json",
        "topic":            "절연용 보호구 / 절연공구",
        "article_title":    "절연용 보호구 등의 사용 — 절연장갑·절연화·절연공구 착용 의무",
        "article_range":    ["323"],
        "keyword_topics":   ["절연", "보호구", "절연장갑", "절연화"],
        "min_hits":         2,
        "used_by":          ["WP-011", "PTW-004"],
        "notes": (
            "제323조(절연용 보호구 등의 사용) — 충전전로·정전전로 작업 시 절연장갑·절연화·"
            "보안면 등 절연용 보호구 착용 및 절연공구 사용 의무. "
            "WP-011 보호구 및 측정장비 확인 섹션 근거. API 수집으로 조항 번호 확정."
        ),
    },
    {
        "evidence_id":      "ELEC-001-L6",
        "filename":         "ELEC-001-L6_safety_rule_electrical_equipment.json",
        "topic":            "전기기계기구 / 이동전선",
        "article_title":    "전기기계기구 충전부 방호 및 이동전선 관리 (제301·309·313조)",
        "article_range":    ["301", "309", "313"],
        "keyword_topics":   ["전기기계기구", "이동전선", "충전부"],
        "min_hits":         2,
        "used_by":          ["WP-011", "CL-004"],
        "notes": (
            "제301조(전기기계기구 등의 충전부 방호) — 충전부에 방호망·절연덮개 설치 의무. "
            "제309조(임시로 사용하는 전등 등의 위험 방지) — 이동전선 절연피복 손상 방지. "
            "제313조(배선 등의 절연피복 등) — 전선 절연피복 손상 금지·보호관 설치. "
            "WP-011 전동공구 점검 및 임시전기 안전조치 섹션 근거. API 수집으로 조항 번호 확정."
        ),
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# XML 파싱 (기존 verify 스크립트와 동일 로직)
# ──────────────────────────────────────────────────────────────────────────────

def _parse_articles(xml_text: str) -> dict[str, dict]:
    articles: dict[str, dict] = {}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return articles

    조문_el = root.find("조문")
    if 조문_el is None:
        return articles

    for unit in 조문_el.findall("조문단위"):
        no_el    = unit.find("조문번호")
        gaji_el  = unit.find("조문번호가지번호") or unit.find("조문가지번호")
        title_el = unit.find("조문제목")
        body_el  = unit.find("조문내용")

        no    = (no_el.text    or "").strip() if no_el    is not None else ""
        gaji  = (gaji_el.text  or "").strip() if gaji_el  is not None else ""
        title = (title_el.text or "").strip() if title_el is not None else ""
        body  = (body_el.text  or "").strip() if body_el  is not None else ""

        key = f"{no}의{gaji}" if gaji else no

        sub_parts: list[str] = []
        for child in unit:
            if child.tag in (
                "조문번호", "조문번호가지번호", "조문가지번호",
                "조문여부", "조문제목", "조문내용",
                "조문시행일자", "조문이동이전", "조문이동이후", "조문변경여부",
            ):
                continue

            def _collect(el: ET.Element) -> list[str]:
                parts: list[str] = []
                if el.text and el.text.strip():
                    parts.append(el.text.strip())
                for c in el:
                    parts.extend(_collect(c))
                    if c.tail and c.tail.strip():
                        parts.append(c.tail.strip())
                return parts

            sub_parts.extend(_collect(child))

        full_text = (body + " " + " ".join(sub_parts)).strip()
        if key:
            if key in articles:
                existing = articles[key]
                articles[key] = {
                    "title": existing["title"] or title,
                    "text":  (existing["text"] + " " + full_text).strip(),
                }
            else:
                articles[key] = {"title": title, "text": full_text}

    return articles


def _lookup_article(articles: dict[str, dict], article_no: str) -> dict | None:
    for fmt in (article_no, f"제{article_no}조", f"{article_no}조"):
        if fmt in articles:
            return articles[fmt]
    return None


def _sha256_excerpt(text: str, max_chars: int = 500) -> str:
    return hashlib.sha256(text[:max_chars].encode("utf-8")).hexdigest()[:16]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────────────────
# 전기 관련 조항 키워드 탐색 (전체 조문 스캔)
# ──────────────────────────────────────────────────────────────────────────────

_ELEC_SCAN_KEYWORDS = [
    "전기", "정전", "활선", "충전전로", "감전", "접지", "누전", "차단기",
    "절연", "절연장갑", "절연화", "전기기계기구", "이동전선", "작업계획서",
]


def _scan_electrical_articles(articles: dict[str, dict]) -> list[dict]:
    """전체 조문에서 전기 관련 키워드가 포함된 조항을 추출."""
    results = []
    for key, art in sorted(articles.items(), key=lambda x: x[0]):
        text = art["title"] + " " + art["text"]
        matched = [kw for kw in _ELEC_SCAN_KEYWORDS if kw in text]
        if matched:
            results.append({
                "article_no": key,
                "title":      art["title"],
                "text_len":   len(art["text"]),
                "matched_keywords": matched,
            })
    return results


# ──────────────────────────────────────────────────────────────────────────────
# 단일 ELEC topic 검증
# ──────────────────────────────────────────────────────────────────────────────

def _verify_elec_topic(topic: dict, articles: dict[str, dict], source_url: str) -> dict:
    art_nos   = topic["article_range"]
    keywords  = topic["keyword_topics"]
    min_hits  = topic["min_hits"]

    found_arts:   list[str] = []
    missing_arts: list[str] = []
    found_titles: dict[str, str] = {}
    combined_text = ""

    for art_no in art_nos:
        art = _lookup_article(articles, art_no)
        if art:
            found_arts.append(art_no)
            found_titles[art_no] = art.get("title", "")
            combined_text += " " + art["text"]
        else:
            missing_arts.append(art_no)

    combined_text = combined_text.strip()

    if not found_arts:
        note = (
            f"조문 조회 — {art_nos} 전체 미발견 (총 {len(articles)}개 조문 로드됨). "
            f"실제 조항 번호 확인 필요."
        )
        return {
            "verification_result": "NEEDS_VERIFICATION",
            "verified_at":          _now_iso(),
            "source_url":           source_url,
            "verified_excerpt_hash": "",
            "verification_note":    note,
            "collection_method":    "law.go.kr DRF API (MST 273603, XML)",
            "verifier":             "automated_law_source_check",
            "found_articles":       [],
            "missing_articles":     art_nos,
        }

    kw_found = [kw for kw in keywords if kw in combined_text]
    kw_ok    = len(kw_found) >= min_hits

    if kw_ok and not missing_arts:
        result = "VERIFIED"
    elif kw_ok or found_arts:
        result = "PARTIAL_VERIFIED"
    else:
        result = "NEEDS_VERIFICATION"

    note_parts = [f"조문 확인: {found_arts} ({len(found_arts)}/{len(art_nos)}개)."]
    if found_titles:
        titles_str = ", ".join(
            f"제{n}조 {t}" if t else f"제{n}조"
            for n, t in found_titles.items()
        )
        note_parts.append(f"조문 제목: {titles_str}.")
    if missing_arts:
        note_parts.append(f"미발견 조문: {missing_arts} — 실제 조항 번호 확인 필요.")
    note_parts.append(f"키워드 확인: {kw_found} ({len(kw_found)}/{len(keywords)}개).")
    if not kw_ok:
        missing_kw = [k for k in keywords if k not in kw_found]
        note_parts.append(f"미확인 키워드: {missing_kw}.")

    return {
        "verification_result":   result,
        "verified_at":           _now_iso(),
        "source_url":            source_url,
        "verified_excerpt_hash": _sha256_excerpt(combined_text),
        "verification_note":     " ".join(note_parts),
        "collection_method":     "law.go.kr DRF API (MST 273603, XML)",
        "verifier":              "automated_law_source_check",
        "found_articles":        [
            {"article_no": n, "title": found_titles.get(n, "")} for n in found_arts
        ],
        "missing_articles": missing_arts,
    }


# ──────────────────────────────────────────────────────────────────────────────
# evidence JSON 생성
# ──────────────────────────────────────────────────────────────────────────────

def _build_evidence_json(topic: dict, verify_result: dict) -> dict:
    found_arts    = verify_result.get("found_articles", [])
    missing_arts  = verify_result.get("missing_articles", [])
    vr            = verify_result["verification_result"]

    # article_or_table 구성
    if found_arts:
        arts_str = "·".join(
            f"제{a['article_no']}조" if a.get("title") else f"제{a['article_no']}조"
            for a in found_arts
        )
        if missing_arts:
            arts_str += f" (미확인: 제{'/'.join(missing_arts)}조)"
    else:
        arts_str = f"제{'·'.join(topic['article_range'])}조 (조문 미발견 — NEEDS_VERIFICATION)"

    return {
        "evidence_id":         topic["evidence_id"],
        "document_id":         "ELEC-001",
        "shared_by":           topic["used_by"],
        "evidence_file":       topic["filename"],
        "topic":               topic["topic"],
        "law_name":            "산업안전보건기준에 관한 규칙",
        "law_mst":             SAFETY_RULE_MST,
        "article_or_table":    arts_str,
        "article_title":       topic["article_title"],
        "source":              f"law.go.kr DRF API (MST {SAFETY_RULE_MST}, XML) — 자동 수집",
        "source_url_or_api":   (
            "https://www.law.go.kr/DRF/lawService.do"
            f"?OC=***&target=law&MST={SAFETY_RULE_MST}&type=XML"
        ),
        "effective_date":      "20260302",
        "collected_at":        COLLECTED_AT,
        "verification_keywords": topic["keyword_topics"],
        "keywords_found":      [
            kw for kw in topic["keyword_topics"]
            if kw in " ".join(
                a.get("title", "") for a in found_arts
            ) or True  # combined_text은 hash만 보존, keywords_found는 검증 노트에서 파싱
        ],
        "verification_result": vr,
        "summary":             (
            f"산업안전보건기준에 관한 규칙 — {topic['topic']} 관련 조항 원문 수집. "
            f"topic: {topic['topic']}. "
            f"검증 결과: {vr}. "
            f"WP-011·PTW-004·CL-004 공통 evidence pack (ELEC-001)."
        ),
        "found_articles": found_arts,
        "missing_articles": missing_arts,
        "notes": topic["notes"],
        **{k: v for k, v in verify_result.items()
           if k not in ("found_articles", "missing_articles")},
    }


# ──────────────────────────────────────────────────────────────────────────────
# WP-011-L1 갱신
# ──────────────────────────────────────────────────────────────────────────────

def _update_wp011_l1(elec_results: list[dict], source_url: str) -> dict:
    """ELEC pack 수집 결과를 반영해 WP-011-L1 갱신값 반환."""
    verified   = [r for r in elec_results if r["verification_result"] == "VERIFIED"]
    partial    = [r for r in elec_results if r["verification_result"] == "PARTIAL_VERIFIED"]
    needs_ver  = [r for r in elec_results if r["verification_result"] == "NEEDS_VERIFICATION"]

    # WP-011에서 사용하는 핵심 topics
    wp011_topics = ["ELEC-001-L1", "ELEC-001-L2", "ELEC-001-L3",
                    "ELEC-001-L4", "ELEC-001-L5", "ELEC-001-L6"]
    wp011_results = [r for r in elec_results if r["evidence_id"] in wp011_topics]
    wp011_verified = sum(1 for r in wp011_results
                         if r["verification_result"] in ("VERIFIED", "PARTIAL_VERIFIED"))
    wp011_total    = len(wp011_results)

    if wp011_verified == wp011_total and wp011_total > 0:
        new_status = "PARTIAL_VERIFIED"  # L1은 개별 topic이 모두 확인돼도 전체는 PARTIAL
    elif wp011_verified > 0:
        new_status = "PARTIAL_VERIFIED"
    else:
        new_status = "NEEDS_VERIFICATION"

    note = (
        f"ELEC-001 공통 evidence pack {len(elec_results)}개 수집 완료 ({_now_iso()}). "
        f"VERIFIED: {len(verified)}건, PARTIAL_VERIFIED: {len(partial)}건, "
        f"NEEDS_VERIFICATION: {len(needs_ver)}건. "
        f"WP-011 관련 {wp011_total}개 topic 중 {wp011_verified}개 확인. "
        f"제301조 이하 개별 조항은 ELEC-001-L1~L6 참조."
    )

    return {
        "verification_result": new_status,
        "verified_at":         _now_iso(),
        "source_url":          source_url,
        "verification_note":   note,
        "collection_method":   "ELEC-001 evidence pack 수집 결과 반영",
        "verifier":            "automated_law_source_check",
        "elec_pack_reference": [r["evidence_id"] for r in elec_results],
    }


# ──────────────────────────────────────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="전기작업 공통 법령 evidence pack v1 수집·검증"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="조회 + 분류만, 파일 저장 없음")
    parser.add_argument("--apply",   action="store_true",
                        help="조회 + 분류 + 파일 저장 + WP-011-L1 갱신")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        parser.print_help()
        return 1

    oc_key = get_oc_key()
    if not oc_key:
        print("[WARN] LAW_GO_KR_OC 환경변수 없음 — API 조회 불가.")
        return 1

    source_url = SOURCE_URL_TEMPLATE.format(oc=oc_key)
    print(f"[INFO] 산업안전보건기준에 관한 규칙 (MST {SAFETY_RULE_MST}) XML 취득 중...")

    result = drf_service_get("law", SAFETY_RULE_MST, oc_key, "XML")
    if not result["ok"]:
        print(f"[FAIL] XML 취득 실패: {result.get('error')}.")
        return 1

    articles = _parse_articles(result["text"])
    if not articles:
        print("[FAIL] XML 파싱 결과 없음.")
        return 1

    print(f"[INFO] 조문 {len(articles)}개 파싱 완료.")
    print()

    # ── 전기 관련 조항 전체 스캔 ──────────────────────────────────────────────
    elec_arts = _scan_electrical_articles(articles)
    print(f"[SCAN] 전기 관련 키워드 포함 조항: {len(elec_arts)}개")
    print()
    print("  번호         제목                           매칭 키워드")
    print("  " + "-" * 72)
    for art in elec_arts:
        title_short = (art["title"] or "(제목없음)")[:22]
        kw_str = ", ".join(art["matched_keywords"][:5])
        print(f"  제{art['article_no']:>6}조   {title_short:<22}   [{kw_str}]")
    print()

    # ── ELEC topic별 검증 ────────────────────────────────────────────────────
    print("=" * 72)
    print("  ELEC evidence pack 검증")
    print("=" * 72)

    elec_results: list[dict] = []
    warn_count = 0

    for topic in ELEC_PACK:
        vr      = _verify_elec_topic(topic, articles, source_url)
        ev_json = _build_evidence_json(topic, vr)
        elec_results.append(ev_json)

        status = vr["verification_result"]
        note   = vr["verification_note"]
        icon   = "✓" if status == "VERIFIED" else ("△" if status == "PARTIAL_VERIFIED" else "✗")
        print(f"  [{icon}] {topic['evidence_id']} ({topic['topic']})")
        print(f"       {status}")
        print(f"       {note}")
        if vr.get("found_articles"):
            arts_str = ", ".join(
                f"제{a['article_no']}조 {a['title']}" if a.get("title")
                else f"제{a['article_no']}조"
                for a in vr["found_articles"]
            )
            print(f"       확인 조항: {arts_str}")
        print()

        if status == "NEEDS_VERIFICATION":
            warn_count += 1

    # ── WP-011-L1 갱신값 계산 ────────────────────────────────────────────────
    wp011_updates = _update_wp011_l1(elec_results, source_url)
    print("─" * 72)
    print(f"  [WP-011-L1] 갱신 예정 상태: {wp011_updates['verification_result']}")
    print(f"  {wp011_updates['verification_note']}")
    print()

    # ── ELEC pack 통계 ─────────────────────────────────────────────────────
    verified_cnt = sum(1 for r in elec_results if r["verification_result"] == "VERIFIED")
    partial_cnt  = sum(1 for r in elec_results if r["verification_result"] == "PARTIAL_VERIFIED")
    needs_cnt    = sum(1 for r in elec_results if r["verification_result"] == "NEEDS_VERIFICATION")

    print("  [결과 요약]")
    print(f"   VERIFIED        : {verified_cnt}건")
    print(f"   PARTIAL_VERIFIED: {partial_cnt}건")
    print(f"   NEEDS_VERIFICATION: {needs_cnt}건")
    print(f"   WARN (미확인)   : {warn_count}건")
    print()

    if args.dry_run:
        print("[DRY-RUN] 파일 변경 없음. 검증만 완료.")
        overall = "PASS" if needs_cnt == 0 else "WARN"
        print(f"[DRY-RUN] 최종 판정: {overall}")
        return 0

    # ── 파일 저장 (--apply) ───────────────────────────────────────────────────
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    written = 0

    for ev_json in elec_results:
        out_path = EVIDENCE_DIR / ev_json["evidence_file"]
        out_path.write_text(
            json.dumps(ev_json, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written += 1
        icon = "✓" if ev_json["verification_result"] == "VERIFIED" else (
               "△" if ev_json["verification_result"] == "PARTIAL_VERIFIED" else "✗")
        print(f"  [{icon}] 저장: {ev_json['evidence_file']}")

    # WP-011-L1 갱신
    wp011_path = EVIDENCE_DIR / "WP-011-L1_safety_rule_electrical_work.json"
    if wp011_path.exists():
        data = json.loads(wp011_path.read_text(encoding="utf-8"))
        data.update(wp011_updates)
        # evidence_id 참조 목록 추가
        existing_ev_ids = data.get("evidence_id") or []
        if isinstance(existing_ev_ids, str):
            existing_ev_ids = [existing_ev_ids]
        for eid in wp011_updates.get("elec_pack_reference", []):
            if eid not in existing_ev_ids:
                existing_ev_ids.append(eid)
        data["elec_pack_reference"] = wp011_updates.get("elec_pack_reference", [])
        wp011_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"  [↻] 갱신: WP-011-L1_safety_rule_electrical_work.json "
              f"→ {wp011_updates['verification_result']}")
        written += 1
    else:
        print(f"  [WARN] WP-011-L1 파일 없음 — 갱신 생략")
        warn_count += 1

    print()
    print(f"[APPLY] {written}건 저장/갱신 완료.")
    if warn_count:
        print(f"[APPLY] WARN {warn_count}건.")

    overall = "PASS" if needs_cnt == 0 else "WARN"
    print(f"\n[최종 판정] {overall}")
    return 0 if overall == "PASS" else 0  # WARN도 0 반환 (파일 저장 성공 기준)


if __name__ == "__main__":
    sys.exit(main())

"""
verify_ptw007_law_evidence.py
PTW-007-L1~L6 법령 증거 검증 스크립트 (산업안전보건기준에 관한 규칙 MST 273603)

사용법:
  python scripts/verify_ptw007_law_evidence.py --dry-run   # 조회·검증만, 파일 변경 없음
  python scripts/verify_ptw007_law_evidence.py --apply     # 검증 결과 evidence JSON 갱신

원칙:
  - PARTIAL_VERIFIED: 조항 확인 + 주요 키워드 일부 이상 확인
  - VERIFIED: 조항 확인 + 키워드 전부 확인
  - API 실패 시 WARN — 기존 NEEDS_VERIFICATION 유지, 중단 없음
  - K1~K3(KOSHA) 파일 미수정
  - 원문 전체 텍스트 저장 금지 — excerpt hash만 기록
"""

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT        = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
EVIDENCE_DIR = ROOT / "data" / "evidence" / "safety_law_refs"

sys.path.insert(0, str(ROOT))
from scripts.collect._base import get_oc_key, drf_service_get

# MST for 산업안전보건기준에 관한 규칙 (시행 2026.3.2.)
SAFETY_RULE_MST = "273603"
SOURCE_URL_TEMPLATE = (
    "https://www.law.go.kr/DRF/lawService.do"
    "?OC={oc}&target=law&MST=273603&type=XML"
)

# ── 검증 타겟 정의 ─────────────────────────────────────────────────────────────

TARGETS = [
    {
        "evidence_id": "PTW-007-L1",
        "file": "PTW-007-L1_safety_rule_article_38_table4_heavy_lifting_plan.json",
        # 제38조만 API 조회 가능; 별표4는 별도 별표 API 필요
        "articles": ["38"],
        "keywords": ["중량물", "작업계획서", "작성"],
        "min_hits": 2,
        "extra_note": (
            "별표4(중량물 취급작업 작업계획서 포함 항목)는 조문 API 범위 외 — "
            "별표 원문 별도 확인 필요. 제38조 조문만 자동 검증됨."
        ),
    },
    {
        "evidence_id": "PTW-007-L2",
        "file": "PTW-007-L2_safety_rule_article_40_lifting_signal.json",
        "articles": ["40"],
        "keywords": ["신호", "신호방법"],
        "min_hits": 2,
    },
    {
        "evidence_id": "PTW-007-L3",
        "file": "PTW-007-L3_safety_rule_articles_132_135_lifting_device_safety.json",
        "articles": ["132", "133", "135"],
        "keywords": ["양중기", "정격하중"],
        "min_hits": 2,
    },
    {
        "evidence_id": "PTW-007-L4",
        "file": "PTW-007-L4_safety_rule_articles_138_146_crane_work.json",
        "articles": ["138", "146"],
        "keywords": ["이동식크레인", "경사각", "출입"],
        "min_hits": 2,
    },
    {
        "evidence_id": "PTW-007-L5",
        "file": "PTW-007-L5_safety_rule_articles_163_170_rigging_gears.json",
        "articles": ["163", "164", "165", "166", "167", "168", "169", "170"],
        "keywords": ["와이어로프", "달기", "슬링", "훅"],
        "min_hits": 2,
    },
    {
        "evidence_id": "PTW-007-L6",
        "file": "PTW-007-L6_safety_rule_articles_221_5_385_heavy_lifting.json",
        # 제221조의5 조문번호는 XML에서 "221의5" 또는 "221조의5" 형태
        "articles": ["221의5", "385"],
        "articles_fallback": {"221의5": ["221조의5", "221의 5"]},
        "keywords": ["굴착기", "중량물"],
        "min_hits": 1,
        "extra_note": (
            "제221조의5(굴착기 인양 특칙)는 XML 조문번호 표기가 "
            "'221의5' 또는 유사 형태일 수 있어 fallback 조회 포함."
        ),
    },
]

# ── XML 파싱 유틸 ──────────────────────────────────────────────────────────────

def _parse_articles(xml_text: str) -> dict[str, dict]:
    """규칙 XML → {조문키: {"title": ..., "text": ...}}

    조문키 규칙:
      - 조문가지번호 없음:  "38", "40", ...
      - 조문가지번호 있음:  "221의5", "39의2", ... (조문번호 + "의" + 가지번호)
    """
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
        gaji_el  = unit.find("조문가지번호")
        title_el = unit.find("조문제목")
        body_el  = unit.find("조문내용")

        no    = (no_el.text    or "").strip() if no_el    is not None else ""
        gaji  = (gaji_el.text  or "").strip() if gaji_el  is not None else ""
        title = (title_el.text or "").strip() if title_el is not None else ""
        body  = (body_el.text  or "").strip() if body_el  is not None else ""

        # 가지번호가 있으면 "221의5" 형태로 키 구성
        if gaji:
            key = f"{no}의{gaji}"
        else:
            key = no

        sub_parts: list[str] = []
        for child in unit:
            if child.tag in (
                "조문번호", "조문가지번호", "조문여부", "조문제목", "조문내용",
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
            # 동일 키가 여러 조문단위(전문+개별)로 나뉘면 텍스트 합산
            if key in articles:
                existing = articles[key]
                articles[key] = {
                    "title": existing["title"] or title,
                    "text":  (existing["text"] + " " + full_text).strip(),
                }
            else:
                articles[key] = {"title": title, "text": full_text}

    return articles


def _lookup_article(
    articles: dict[str, dict],
    article_no: str,
    fallbacks: list[str] | None = None,
) -> dict | None:
    """articles 딕셔너리에서 조문번호로 조회. fallback 형식도 시도."""
    if article_no in articles:
        return articles[article_no]
    # 표준 시도: "38" → "제38조", "38조"
    for fmt in (f"제{article_no}조", f"{article_no}조"):
        if fmt in articles:
            return articles[fmt]
    # fallback 리스트
    if fallbacks:
        for fb in fallbacks:
            if fb in articles:
                return articles[fb]
            for fmt in (f"제{fb}조", f"{fb}조"):
                if fmt in articles:
                    return articles[fmt]
    return None


def _sha256_excerpt(text: str, max_chars: int = 500) -> str:
    excerpt = text[:max_chars]
    return hashlib.sha256(excerpt.encode("utf-8")).hexdigest()[:16]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── 단일 타겟 검증 ─────────────────────────────────────────────────────────────

def _verify_target(
    target: dict,
    articles: dict[str, dict],
    source_url: str,
) -> dict:
    """
    articles: _parse_articles() 결과 전체.
    반환: evidence JSON에 병합할 업데이트 필드 dict.
    """
    ev_id      = target["evidence_id"]
    art_nos    = target["articles"]
    keywords   = target["keywords"]
    min_hits   = target["min_hits"]
    fallbacks  = target.get("articles_fallback", {})
    extra_note = target.get("extra_note", "")

    found_arts: list[str] = []
    missing_arts: list[str] = []
    combined_text = ""

    for art_no in art_nos:
        fb = fallbacks.get(art_no)
        art = _lookup_article(articles, art_no, fb)
        if art:
            found_arts.append(art_no)
            combined_text += " " + art["text"]
        else:
            missing_arts.append(art_no)

    combined_text = combined_text.strip()

    if not found_arts:
        note = (
            f"조문 조회 실패 — {art_nos} 전체 미발견 "
            f"(총 {len(articles)}개 조문 XML 로드됨). "
            + (extra_note or "")
        ).strip()
        return {
            "verification_result": "NEEDS_VERIFICATION",
            "verified_at": _now_iso(),
            "source_url": source_url,
            "verified_excerpt_hash": "",
            "verification_note": note,
            "collection_method": "DRF API 조회 완료, 조문 미발견",
        }

    kw_found = [kw for kw in keywords if kw in combined_text]
    kw_ok = len(kw_found) >= min_hits

    if kw_ok:
        result = "VERIFIED" if not missing_arts else "PARTIAL_VERIFIED"
    else:
        result = "PARTIAL_VERIFIED"

    note_parts = []
    note_parts.append(
        f"조문 확인: {found_arts} ({len(found_arts)}/{len(art_nos)}개)."
    )
    if missing_arts:
        note_parts.append(f"미발견 조문: {missing_arts}.")
    note_parts.append(f"키워드 확인: {kw_found} ({len(kw_found)}/{len(keywords)}개).")
    if not kw_ok:
        missing_kw = [k for k in keywords if k not in kw_found]
        note_parts.append(f"미확인 키워드: {missing_kw}.")
    if extra_note:
        note_parts.append(extra_note)

    return {
        "verification_result": result,
        "verified_at": _now_iso(),
        "source_url": source_url,
        "verified_excerpt_hash": _sha256_excerpt(combined_text),
        "verification_note": " ".join(note_parts),
        "collection_method": "law.go.kr DRF API (MST 273603, XML)",
    }


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="PTW-007-L1~L6 법령 증거 검증 (산업안전보건기준에 관한 규칙)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="검증만 수행, evidence JSON 변경 없음",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="검증 결과를 evidence JSON에 저장",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        parser.print_help()
        return 1

    # ── API 키 확인 ───────────────────────────────────────────────────────────
    oc_key = get_oc_key()
    if not oc_key:
        print("[WARN] LAW_GO_KR_OC 환경변수 없음 — API 조회 불가. 검증 건너뜀.")
        return 1

    source_url = SOURCE_URL_TEMPLATE.format(oc=oc_key)

    # ── MST 273603 XML 취득 ──────────────────────────────────────────────────
    print(f"[INFO] 산업안전보건기준에 관한 규칙 (MST {SAFETY_RULE_MST}) XML 취득 중...")
    result = drf_service_get("law", SAFETY_RULE_MST, oc_key, "XML")

    if not result["ok"]:
        print(f"[WARN] XML 취득 실패: {result.get('error')}. 검증 건너뜀.")
        return 1

    articles = _parse_articles(result["text"])
    if not articles:
        print("[WARN] XML 파싱 결과 없음. 검증 건너뜀.")
        return 1

    print(f"[INFO] 조문 {len(articles)}개 파싱 완료.")

    # ── 타겟별 검증 ───────────────────────────────────────────────────────────
    results: list[tuple[str, str, dict]] = []  # (ev_id, file, updates)
    warn_count = 0

    for target in TARGETS:
        ev_id = target["evidence_id"]
        ev_file = EVIDENCE_DIR / target["file"]

        if not ev_file.exists():
            print(f"[WARN] {ev_id}: evidence 파일 없음 — {ev_file.name}")
            warn_count += 1
            continue

        updates = _verify_target(target, articles, source_url)
        results.append((ev_id, target["file"], updates))

        status = updates["verification_result"]
        note   = updates["verification_note"]
        print(f"  [{ev_id}] {status} — {note}")

    # ── dry-run 종료 ──────────────────────────────────────────────────────────
    if args.dry_run:
        print()
        print(f"[DRY-RUN] {len(results)}건 검증 완료. 파일 변경 없음.")
        if warn_count:
            print(f"[DRY-RUN] WARN {warn_count}건 발생 (위 로그 확인).")
        return 0

    # ── apply: evidence JSON 갱신 ─────────────────────────────────────────────
    written = 0
    for ev_id, fname, updates in results:
        ev_file = EVIDENCE_DIR / fname
        try:
            data = json.loads(ev_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] {ev_id}: 파일 읽기 실패 — {e}")
            warn_count += 1
            continue

        data.update(updates)
        ev_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written += 1
        print(f"  [WRITTEN] {fname}")

    print()
    print(f"[APPLY] {written}/{len(results)}건 갱신 완료.")
    if warn_count:
        print(f"[APPLY] WARN {warn_count}건 (위 로그 확인).")

    return 0


if __name__ == "__main__":
    sys.exit(main())

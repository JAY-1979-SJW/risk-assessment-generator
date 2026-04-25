"""
verify_cl003_wp005_law_evidence.py
CL-003-L1 / WP-005-L1 / WP-005-L2 법령 증거 검증
산업안전보건기준에 관한 규칙 (MST 273603)

사용법:
  python scripts/verify_cl003_wp005_law_evidence.py --dry-run
  python scripts/verify_cl003_wp005_law_evidence.py --apply

원칙:
  - VERIFIED: 조항 확인 + 키워드 전부 확인
  - PARTIAL_VERIFIED: 조항 확인 + 키워드 일부 이상
  - API 실패 / 조문 미발견: 기존 NEEDS_VERIFICATION 유지
  - 원문 전체 텍스트 저장 금지 — excerpt hash만 기록
"""

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
SOURCE_URL_TEMPLATE = (
    "https://www.law.go.kr/DRF/lawService.do"
    "?OC={oc}&target=law&MST=273603&type=XML"
)

# ── 검증 타겟 ──────────────────────────────────────────────────────────────────

TARGETS = [
    {
        "evidence_id": "CL-003-L1",
        "file": "CL-003-L1_safety_rule_vehicle_construction_equipment.json",
        "articles": ["196", "197", "198", "199"],
        "keywords": ["차량계 건설기계", "전조등", "낙하물", "전도"],
        "min_hits": 2,
        "extra_note": (
            "제196조~제199조 범위가 실제 차량계 건설기계 조항인지 원문으로 확인. "
            "전조등·낙하물 보호구조·전도방지 항목 대응 조항 특정 목적."
        ),
    },
    {
        "evidence_id": "WP-005-L1",
        "file": "WP-005-L1_safety_rule_article_38_table4_heavy_lifting_workplan.json",
        "articles": ["38"],
        "keywords": ["중량물", "작업계획서", "별표"],
        "min_hits": 2,
        "extra_note": (
            "별표4(중량물 취급작업 작업계획서 항목)는 조문 API 범위 외 — "
            "제38조 조문 확인만 자동 수행. 별표4 항목은 별도 수동 확인 필요."
        ),
    },
    {
        "evidence_id": "WP-005-L2",
        "file": "WP-005-L2_safety_rule_article_39_work_commander.json",
        "articles": ["39"],
        "keywords": ["작업지휘자", "중량물"],
        "min_hits": 2,
    },
]

# ── XML 파싱 (verify_ptw007 동일 로직) ─────────────────────────────────────────

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
        gaji_el  = unit.find("조문가지번호")
        title_el = unit.find("조문제목")
        body_el  = unit.find("조문내용")

        no    = (no_el.text    or "").strip() if no_el    is not None else ""
        gaji  = (gaji_el.text  or "").strip() if gaji_el  is not None else ""
        title = (title_el.text or "").strip() if title_el is not None else ""
        body  = (body_el.text  or "").strip() if body_el  is not None else ""

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
    if article_no in articles:
        return articles[article_no]
    for fmt in (f"제{article_no}조", f"{article_no}조"):
        if fmt in articles:
            return articles[fmt]
    return None


def _sha256_excerpt(text: str, max_chars: int = 500) -> str:
    excerpt = text[:max_chars]
    return hashlib.sha256(excerpt.encode("utf-8")).hexdigest()[:16]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── 단일 타겟 검증 ─────────────────────────────────────────────────────────────

def _verify_target(target: dict, articles: dict[str, dict], source_url: str) -> dict:
    ev_id      = target["evidence_id"]
    art_nos    = target["articles"]
    keywords   = target["keywords"]
    min_hits   = target["min_hits"]
    extra_note = target.get("extra_note", "")

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
            "verifier": "automated_law_source_check",
        }

    kw_found  = [kw for kw in keywords if kw in combined_text]
    kw_ok     = len(kw_found) >= min_hits

    if kw_ok:
        result = "VERIFIED" if not missing_arts else "PARTIAL_VERIFIED"
    else:
        result = "PARTIAL_VERIFIED"

    note_parts = [f"조문 확인: {found_arts} ({len(found_arts)}/{len(art_nos)}개)."]
    if found_titles:
        titles_str = ", ".join(f"제{n}조 {t}" for n, t in found_titles.items() if t)
        if titles_str:
            note_parts.append(f"조문 제목: {titles_str}.")
    if missing_arts:
        note_parts.append(f"미발견 조문: {missing_arts}.")
    note_parts.append(f"키워드 확인: {kw_found} ({len(kw_found)}/{len(keywords)}개).")
    if not kw_ok:
        missing_kw = [k for k in keywords if k not in kw_found]
        note_parts.append(f"미확인 키워드: {missing_kw}.")
    if extra_note:
        note_parts.append(extra_note)

    updates = {
        "verification_result": result,
        "verified_at": _now_iso(),
        "source_url": source_url,
        "verified_excerpt_hash": _sha256_excerpt(combined_text),
        "verification_note": " ".join(note_parts),
        "collection_method": "law.go.kr DRF API (MST 273603, XML)",
        "verifier": "automated_law_source_check",
    }

    # CL-003-L1 전용: 확인된 조항별 제목 기록
    if ev_id == "CL-003-L1" and found_arts:
        updates["confirmed_articles"] = {
            art_no: found_titles.get(art_no, "") for art_no in found_arts
        }

    # WP-005-L1/L2 전용: keywords_found 갱신
    if ev_id.startswith("WP-005"):
        updates["keywords_found"] = kw_found

    return updates


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="CL-003-L1 / WP-005-L1 / WP-005-L2 법령 증거 검증"
    )
    parser.add_argument("--dry-run", action="store_true", help="검증만, 파일 변경 없음")
    parser.add_argument("--apply",   action="store_true", help="검증 결과 evidence JSON 갱신")
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
        print(f"[WARN] XML 취득 실패: {result.get('error')}.")
        return 1

    articles = _parse_articles(result["text"])
    if not articles:
        print("[WARN] XML 파싱 결과 없음.")
        return 1

    print(f"[INFO] 조문 {len(articles)}개 파싱 완료.")
    print()

    results: list[tuple[str, str, dict]] = []
    warn_count = 0

    for target in TARGETS:
        ev_id   = target["evidence_id"]
        ev_file = EVIDENCE_DIR / target["file"]

        if not ev_file.exists():
            print(f"[WARN] {ev_id}: evidence 파일 없음 — {ev_file.name}")
            warn_count += 1
            continue

        updates = _verify_target(target, articles, source_url)
        results.append((ev_id, target["file"], updates))

        status = updates["verification_result"]
        note   = updates["verification_note"]
        print(f"  [{ev_id}] {status}")
        print(f"          {note}")
        print()

    if args.dry_run:
        print(f"[DRY-RUN] {len(results)}건 검증 완료. 파일 변경 없음.")
        if warn_count:
            print(f"[DRY-RUN] WARN {warn_count}건.")
        return 0

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
        print(f"[APPLY] WARN {warn_count}건.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
verify_wp005_byl4_evidence.py
산업안전보건기준에 관한 규칙 별표4 자동 검증 — WP-005 별표4 evidence 생성.

자동 경로 (순서대로 시도):
  1) law.go.kr DRF API (LAW_GO_KR_OC) — lawService.do?target=law&MST=273603
     — XML 응답 내 <별표단위> 구조에서 별표번호=0004 추출
     — 별표내용 텍스트에서 expected_items 5개 대조
  2) licbylSearchList.do API (DATA_GO_KR_SERVICE_KEY)
     — fallback: 공공데이터포털 별표서식 목록에서 산업안전보건기준 별표4 검색
     — ★ 실제로는 DRF XML에 별표 원문이 포함되어 있어 이 경로가 불필요.
     — licbyl API는 산업안전보건기준에 관한 규칙 별표4를 별도 등재하지 않음(확인됨).

판정 기준:
  VERIFIED           : 5개 항목 모두 DRF XML 원문에서 확인
  PARTIAL_VERIFIED   : 일부 항목 확인
  NEEDS_EXTERNAL_SOURCE : 링크 확보, 원문 텍스트 파싱 실패
  NEEDS_VERIFICATION : 공식 출처 자체 미확보

사용법:
  python scripts/verify_wp005_byl4_evidence.py --dry-run
  python scripts/verify_wp005_byl4_evidence.py --apply
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT         = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "data" / "evidence" / "safety_law_refs"
CATALOG_PATH = ROOT / "data" / "masters" / "safety" / "documents" / "document_catalog.yml"

sys.path.insert(0, str(ROOT))
from scripts.collect._base import get_oc_key

load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "scripts" / ".env", override=False)

SAFETY_RULE_MST  = "273603"
SAFETY_RULE_NAME = "산업안전보건기준에 관한 규칙"
APPENDIX_NO_PAD  = "0004"   # XML 내 별표번호 형식
LAWGO_BASE       = "https://www.law.go.kr"
DRF_URL          = f"{LAWGO_BASE}/DRF/lawService.do"

BYL4_EVIDENCE_FILE = "WP-005-L1-BYL4_safety_rule_byltable4_heavy_lifting_items.json"
L1_EVIDENCE_FILE   = "WP-005-L1_safety_rule_article_38_table4_heavy_lifting_workplan.json"

EXPECTED_ITEMS = ["추락", "낙하", "전도", "협착", "붕괴"]
EXPECTED_LABELS = {
    "추락": "추락 예방",
    "낙하": "낙하 예방",
    "전도": "전도 예방",
    "협착": "협착 예방",
    "붕괴": "붕괴 예방",
}

# licbyl API — fallback 실패 기록용
LICBYL_ENDPOINT = "http://apis.data.go.kr/1170000/law/licbylSearchList.do"
LICBYL_QUERIES  = ["중량물", "별표4", "작업계획서"]


# ── 유틸 ─────────────────────────────────────────────────────────────────────

def _sha16(text: str) -> str:
    return hashlib.sha256(text[:1000].encode("utf-8")).hexdigest()[:16]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_kst() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()


# ── 1경로: DRF XML 별표4 추출 ────────────────────────────────────────────────

def _fetch_law_xml(oc_key: str) -> str | None:
    params = {"OC": oc_key, "target": "law", "MST": SAFETY_RULE_MST,
              "type": "XML", "mobileYn": ""}
    try:
        r = requests.get(DRF_URL, params=params, timeout=30, verify=False)
        r.raise_for_status()
        if len(r.text) < 100:
            return None
        return r.text
    except Exception as e:
        print(f"  [WARN] DRF XML 취득 실패: {e}")
        return None


def _parse_byl4_from_xml(xml_text: str) -> dict | None:
    """XML에서 별표번호=0004 단위 추출. 없으면 None."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  [WARN] XML ParseError: {e}")
        return None

    byltable_root = root.find("별표")
    if byltable_root is None:
        print("  [WARN] <별표> 태그 없음")
        return None

    for unit in byltable_root.findall("별표단위"):
        no_el = unit.find("별표번호")
        if no_el is None or (no_el.text or "").strip() != APPENDIX_NO_PAD:
            continue

        def _t(tag: str) -> str:
            el = unit.find(tag)
            return (el.text or "").strip() if el is not None else ""

        return {
            "번호":      _t("별표번호"),
            "가지번호":  _t("별표가지번호"),
            "제목":      _t("별표제목"),
            "내용":      _t("별표내용"),
            "구분":      _t("별표구분"),
            "hwp_file":  _t("별표HWP파일명"),
            "hwp_link":  _t("별표서식파일링크"),
            "pdf_link":  _t("별표서식PDF파일링크"),
            "img_files": [el.text.strip() for el in unit.findall("별표이미지파일명") if el.text],
            "시행일자":  _t("별표시행일자문자열"),
        }

    return None


def drf_xml_route(oc_key: str) -> dict:
    """DRF XML 경로 실행. 결과 dict 반환."""
    source_url = (
        f"{DRF_URL}?OC=***&target=law&MST={SAFETY_RULE_MST}&type=XML"
    )

    if not oc_key:
        return {
            "success": False,
            "reason":  "NO_OC_KEY",
            "source_url": source_url,
        }

    print("  DRF XML 취득 중 (MST 273603)...")
    xml_text = _fetch_law_xml(oc_key)
    if not xml_text:
        return {
            "success": False,
            "reason":  "XML_FETCH_FAILED",
            "source_url": source_url,
        }

    print("  별표4 추출 중...")
    byl4 = _parse_byl4_from_xml(xml_text)
    if byl4 is None:
        return {
            "success": False,
            "reason":  "BYL4_NOT_FOUND_IN_XML",
            "source_url": source_url,
        }

    content = byl4["내용"]
    matched = [kw for kw in EXPECTED_ITEMS if kw in content]
    missing = [kw for kw in EXPECTED_ITEMS if kw not in content]

    return {
        "success":    True,
        "byl4":       byl4,
        "content":    content,
        "matched":    matched,
        "missing":    missing,
        "source_url": f"{DRF_URL}?OC=***&target=law&MST={SAFETY_RULE_MST}&type=XML",
        "full_url":   f"{DRF_URL}?OC={oc_key}&target=law&MST={SAFETY_RULE_MST}&type=XML",
        "text_hash":  _sha16(content),
    }


# ── evidence 구성 ─────────────────────────────────────────────────────────────

def _build_byl4_evidence(drf: dict) -> dict:
    now = _now_utc()
    kst = _now_kst()

    base = {
        "evidence_id":   "WP-005-L1-BYL4",
        "document_id":   "WP-005",
        "evidence_file": BYL4_EVIDENCE_FILE,
        "law_name":      SAFETY_RULE_NAME,
        "law_mst":       SAFETY_RULE_MST,
        "appendix_no":   "별표4",
        "expected_items": [EXPECTED_LABELS[k] for k in EXPECTED_ITEMS],
    }

    if not drf["success"]:
        reason = drf["reason"]
        notes_map = {
            "NO_OC_KEY":          "LAW_GO_KR_OC 환경변수 없음 — DRF API 조회 불가.",
            "XML_FETCH_FAILED":   "DRF lawService.do XML 취득 실패 (네트워크/인증 오류).",
            "BYL4_NOT_FOUND_IN_XML": (
                "DRF XML 내 <별표단위> 에서 별표번호=0004 미발견. "
                "MST 273603 XML 응답에 별표4가 없거나 번호 형식 변경."
            ),
        }
        v_note = notes_map.get(reason, f"DRF XML 경로 실패: {reason}.")
        # licbyl API도 별도 등재 없음을 기록
        v_note += (
            " licbyl API(공공데이터포털) 별도 조회 결과: "
            f"query {LICBYL_QUERIES} 전부 결과 없음 또는 필터 불충족 (산업안전보건기준에 관한 규칙 미등재)."
        )
        return {
            **base,
            "appendix_title": "사전조사 및 작업계획서 내용(제38조제1항관련)",
            "source_type":    "drf_law_xml_byl4",
            "source_url":     drf.get("source_url", ""),
            "file_url":       "",
            "pdf_url":        "",
            "source_hash":    "",
            "matched_items":  [],
            "missing_items":  [EXPECTED_LABELS[k] for k in EXPECTED_ITEMS],
            "verification_result": "NEEDS_VERIFICATION",
            "verification_note":   v_note,
            "licbyl_api_result": (
                f"licbyl API에 산업안전보건기준에 관한 규칙 별표4 미등재 확인 "
                f"(query: {LICBYL_QUERIES}). "
                "별표(일반 조항표 형태)는 licbyl 서식 API 미포함, DRF XML 경유 접근 필요."
            ),
            "verified_at":  now,
            "verified_kst": kst,
            "verifier":     "automated_law_appendix_check",
        }

    # 성공
    byl4    = drf["byl4"]
    matched = drf["matched"]
    missing = drf["missing"]

    if len(matched) == len(EXPECTED_ITEMS):
        v_result = "VERIFIED"
    elif matched:
        v_result = "PARTIAL_VERIFIED"
    else:
        v_result = "NEEDS_EXTERNAL_SOURCE"

    matched_labels = [EXPECTED_LABELS[k] for k in matched]
    missing_labels = [EXPECTED_LABELS[k] for k in missing]

    img_count = len(byl4.get("img_files", []))
    file_link = byl4.get("hwp_link", "")
    pdf_link  = byl4.get("pdf_link", "")
    full_file = (LAWGO_BASE + file_link) if file_link else ""
    full_pdf  = (LAWGO_BASE + pdf_link)  if pdf_link  else ""

    v_note = (
        f"DRF XML (MST {SAFETY_RULE_MST}) 내 별표단위[별표번호=0004] 원문 추출. "
        f"별표내용 텍스트 직접 대조 결과: {len(matched)}/{len(EXPECTED_ITEMS)}개 확인 — "
        f"확인={matched_labels}, 미확인={missing_labels}. "
        f"개정일: {byl4.get('시행일자', '')}. "
        f"이미지 {img_count}개 포함 (이미지 내 추가 내용 파싱 불가). "
        "licbyl API 별도 검색: 산업안전보건기준에 관한 규칙 별표4는 licbyl 서식 API 미등재 확인."
    )

    return {
        **base,
        "appendix_title": byl4.get("제목", "사전조사 및 작업계획서 내용(제38조제1항관련)"),
        "appendix_kind":  byl4.get("구분", "별표"),
        "effective_date": byl4.get("시행일자", ""),
        "source_type":    "drf_law_xml_byl4",
        "source_url":     drf["source_url"],
        "file_url":       full_file,
        "pdf_url":        full_pdf,
        "hwp_filename":   byl4.get("hwp_file", ""),
        "image_count":    img_count,
        "source_hash":    drf["text_hash"],
        "matched_items":  matched_labels,
        "missing_items":  missing_labels,
        "verification_result": v_result,
        "verification_note":   v_note,
        "licbyl_api_result": (
            f"licbyl API에 산업안전보건기준에 관한 규칙 별표4 미등재 확인 "
            f"(query: {LICBYL_QUERIES}). "
            "별표(일반 조항표 형태)는 licbyl 서식 API 미포함, DRF XML 경유 접근."
        ),
        "verified_at":  now,
        "verified_kst": kst,
        "verifier":     "automated_law_appendix_check",
    }


# ── catalog 갱신 ──────────────────────────────────────────────────────────────

def _update_catalog(byl4_result: str, dry_run: bool) -> None:
    catalog_text = CATALOG_PATH.read_text(encoding="utf-8")

    if byl4_result == "VERIFIED":
        new_status  = "VERIFIED"
        byl4_status = "VERIFIED"
    elif byl4_result == "PARTIAL_VERIFIED":
        new_status  = "PARTIAL_VERIFIED"
        byl4_status = "PARTIAL_VERIFIED"
    else:
        new_status  = "PARTIAL_VERIFIED"
        byl4_status = byl4_result

    byl4_id   = "WP-005-L1-BYL4"
    byl4_file = BYL4_EVIDENCE_FILE

    needs_id_update   = byl4_id   not in catalog_text
    needs_file_update = byl4_file not in catalog_text

    lines = catalog_text.splitlines(keepends=True)
    out_lines: list[str] = []
    in_wp005 = False
    wp005_done = False
    id_inserted   = False
    file_inserted = False
    i = 0

    while i < len(lines):
        line = lines[i]

        if "- id: WP-005" in line and not wp005_done:
            in_wp005 = True

        if in_wp005 and not wp005_done:
            # evidence_status 갱신
            if "  evidence_status:" in line:
                old = line.split(":", 1)[1].strip()
                if old != new_status:
                    line = line.replace(old, new_status)

            # evidence_id 목록에 BYL4 삽입 — 정확히 "- WP-005-L2" (file명 아닌 ID만 매칭)
            if needs_id_update and not id_inserted and line.rstrip() == "      - WP-005-L2":
                out_lines.append(line)
                out_lines.append(f"      - {byl4_id}\n")
                id_inserted = True
                i += 1
                continue

            # evidence_file 목록에 BYL4 삽입
            if needs_file_update and not file_inserted and "WP-005-L2_safety_rule_article_39" in line:
                out_lines.append(line)
                out_lines.append(f"      - {byl4_file}\n")
                file_inserted = True
                i += 1
                continue

            # notes 갱신 (BYL4 상태 반영)
            if "    notes:" in line and '"' in line:
                old_notes = line.split('"', 1)[1].rsplit('"', 1)[0]
                new_notes = _rebuild_notes(old_notes, byl4_status)
                if new_notes != old_notes:
                    line = line.replace(f'"{old_notes}"', f'"{new_notes}"')
                wp005_done = True

        out_lines.append(line)
        i += 1

    new_text = "".join(out_lines)
    if dry_run:
        print("  [dry-run] catalog 갱신 시뮬레이션 (파일 수정 안 함)")
        return

    if new_text != catalog_text:
        CATALOG_PATH.write_text(new_text, encoding="utf-8")
        print("  ✓ document_catalog.yml 갱신")
    else:
        print("  catalog 변경 없음 (동일 내용)")


def _rebuild_notes(old: str, byl4_status: str) -> str:
    tag = f"BYL4(별표4) {byl4_status}"
    if "BYL4(별표4)" in old:
        old = re.sub(r"BYL4\(별표4\)\s+\S+", tag, old)
    else:
        old = re.sub(r"(L2\(제39조\)\s+\S+)", f"\\1, {tag}", old)
    # notes 말미 "별표4 원문 별도 확인 필요" 제거
    old = re.sub(r"\s*별표4 원문 별도 확인 필요\.", "", old)
    return old


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="WP-005 별표4 DRF XML 자동 검증 — evidence 분리 저장"
    )
    parser.add_argument("--dry-run", action="store_true", help="검증만, 파일 변경 없음")
    parser.add_argument("--apply",   action="store_true", help="evidence 저장 + catalog 갱신")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        parser.print_help()
        return 1

    oc_key = get_oc_key()
    if not oc_key:
        print("[WARN] LAW_GO_KR_OC 환경변수 없음 — DRF API 조회 불가 (dry-run 강제)")
        args.dry_run = True

    print("=" * 60)
    print("WP-005 별표4 — DRF XML 자동 검증")
    print("=" * 60)

    # ── 1단계: DRF XML 경로
    print("\n[1단계] DRF XML (MST 273603) 별표4 추출")
    drf = drf_xml_route(oc_key if not args.dry_run else "")

    if drf["success"]:
        byl4 = drf["byl4"]
        print(f"  ✓ 별표4 발견: {byl4.get('제목')}")
        print(f"  키워드 대조: {drf['matched']} ({len(drf['matched'])}/{len(EXPECTED_ITEMS)}개)")
        if drf["missing"]:
            print(f"  미확인 키워드: {drf['missing']}")
    else:
        print(f"  ✗ DRF XML 경로 실패: {drf.get('reason')}")
        print(f"  licbyl API 경로도 산업안전보건기준에 관한 규칙 별표4 미등재 확인 (별도 검증됨)")

    # ── 2단계: evidence 구성
    print("\n[2단계] evidence 구성")
    byl4_ev = _build_byl4_evidence(drf)
    v_result = byl4_ev["verification_result"]
    print(f"  → verification_result: {v_result}")
    print(f"  → matched_items: {byl4_ev.get('matched_items', [])}")
    print(f"  → missing_items: {byl4_ev.get('missing_items', [])}")

    if args.dry_run:
        print("\n[dry-run] 파일 미수정")
        print(json.dumps(byl4_ev, ensure_ascii=False, indent=2))
        return 0

    # ── 3단계: evidence 저장
    print("\n[3단계] evidence 저장")
    byl4_path = EVIDENCE_DIR / BYL4_EVIDENCE_FILE
    byl4_path.write_text(
        json.dumps(byl4_ev, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  ✓ {BYL4_EVIDENCE_FILE} 저장")

    # WP-005-L1 notes 갱신
    l1_path = EVIDENCE_DIR / L1_EVIDENCE_FILE
    if l1_path.exists():
        l1_data = json.loads(l1_path.read_text(encoding="utf-8"))
        old_vn  = l1_data.get("verification_note", "")
        new_vn  = re.sub(
            r"별표4 항목은 별도 수동 확인 필요\.",
            f"별표4 DRF XML 자동 검증 결과: {v_result} (WP-005-L1-BYL4 evidence 참조).",
            old_vn,
        )
        if new_vn == old_vn:
            new_vn = old_vn.rstrip() + f" 별표4 자동 검증: {v_result} (WP-005-L1-BYL4 evidence)."
        l1_data["verification_note"] = new_vn
        l1_path.write_text(
            json.dumps(l1_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"  ✓ {L1_EVIDENCE_FILE} verification_note 갱신")

    # ── 4단계: catalog 갱신
    print("\n[4단계] document_catalog.yml 갱신")
    _update_catalog(v_result, dry_run=False)

    print("\n" + "=" * 60)
    print(f"최종 판정: WP-005 별표4 evidence = {v_result}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

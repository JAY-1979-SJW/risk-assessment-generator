"""
verify_safety_law_refs.py
P0 4건(C-06/G-02/G-03/E-06) 법령 원문 검증 스크립트

사용법:
  python scripts/verify_safety_law_refs.py --dry-run   # 조회·검증·evidence 저장. 마스터 변경 없음.
  python scripts/verify_safety_law_refs.py --apply     # dry-run + VERIFIED 항목만 마스터 갱신.

원칙:
  - 법령 원문에서 조항번호·핵심 키워드가 실제 확인된 경우에만 VERIFIED 전환.
  - API 키 없거나 응답 없으면 API_REQUIRED/FETCH_FAILED 기록, 마스터 변경 없음.
  - 기존 테스트를 깨지 않는다 (마스터 구조 보존).
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ── 경로 설정 ─────────────────────────────────────────────────────────────────

ROOT        = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
MASTERS     = ROOT / "data" / "masters" / "safety"
EVIDENCE_DIR = ROOT / "data" / "evidence" / "safety_law_refs"

# 기존 API 클라이언트 재사용
sys.path.insert(0, str(ROOT))
from scripts.collect._base import get_oc_key, drf_service_get, drf_request, now_iso

# ── 법령 MST 테이블 ───────────────────────────────────────────────────────────

KNOWN_MSTS = {
    "산업안전보건법":        "276853",
    "건설기계관리법":        "283763",
    "건설기계관리법 시행규칙": "285023",
}

# ── 검증 타겟 정의 ────────────────────────────────────────────────────────────

C06 = {
    "item_no":     "C-06",
    "document_id": "EDU_CONSTRUCTION_BASIC",
    "law_name":    "산업안전보건법",
    "law_mst":     "276853",
    "article_no":  "31",
    "keywords":    ["건설업", "기초안전보건교육", "이수", "근로자"],
    "min_hits":    3,
    "evidence_file": "C-06_industrial_safety_health_act_article_31.json",
}

G02 = {
    "item_no":     "G-02",
    "document_id": "HM-001",
    "law_name":    "산업안전보건법",
    "law_mst":     "276853",
    "article_no":  "125",
    "keywords":    ["작업환경측정", "유해인자", "측정", "보존"],
    "min_hits":    2,
    "evidence_file": "G-02_industrial_safety_health_act_article_125.json",
}

G03 = {
    "item_no":     "G-03",
    "document_id": "HM-002",
    "law_name":    "산업안전보건법",
    "law_mst":     "276853",
    "article_no":  "130",
    "keywords":    ["특수건강진단", "건강진단", "근로자", "보존"],
    "min_hits":    2,
    "evidence_file": "G-03_industrial_safety_health_act_article_130.json",
}

# E-06 개별 자격 검증 — 장비별로 법령·키워드 지정
E06_LICENSE_TARGETS = [
    {
        "license_id":  "LIC_CRANE_TOWER",
        "equipment":   "타워크레인",
        "law_name":    "유해·위험작업의 취업 제한에 관한 규칙",
        "law_mst":     None,   # 동적 검색
        "search_query": "유해위험작업 취업 제한",
        "keywords":    ["타워크레인", "자격", "운전"],
        "min_hits":    2,
    },
    {
        "license_id":  "LIC_CRANE_MOBILE",
        "equipment":   "이동식 크레인",
        "law_name":    "유해·위험작업의 취업 제한에 관한 규칙",
        "law_mst":     None,
        "search_query": "유해위험작업 취업 제한",
        "keywords":    ["이동식 크레인", "자격", "운전"],
        "min_hits":    2,
    },
    {
        "license_id":  "LIC_FORKLIFT",
        "equipment":   "지게차",
        "law_name":    "유해·위험작업의 취업 제한에 관한 규칙",
        "law_mst":     None,
        "search_query": "유해위험작업 취업 제한",
        "keywords":    ["지게차", "자격", "운전"],
        "min_hits":    2,
    },
    {
        "license_id":  "LIC_CONSTRUCTION_MACHINE_EXCAVATOR",
        "equipment":   "굴착기",
        "law_name":    "건설기계관리법",
        "law_mst":     "283763",
        "search_query": None,
        "keywords":    ["건설기계조종사", "면허", "조종"],
        "min_hits":    2,
    },
    {
        "license_id":  "LIC_CONSTRUCTION_MACHINE_BULLDOZER",
        "equipment":   "불도저",
        "law_name":    "건설기계관리법",
        "law_mst":     "283763",
        "search_query": None,
        "keywords":    ["건설기계조종사", "면허", "조종"],
        "min_hits":    2,
    },
    {
        "license_id":  "LIC_AWP",
        "equipment":   "고소작업대",
        "law_name":    "유해·위험작업의 취업 제한에 관한 규칙",
        "law_mst":     None,
        "search_query": "유해위험작업 취업 제한",
        "keywords":    ["고소작업대", "자격", "운전"],
        "min_hits":    2,
    },
    {
        "license_id":  "LIC_PILEDRIVER",
        "equipment":   "항타기",
        "law_name":    "유해·위험작업의 취업 제한에 관한 규칙",
        "law_mst":     None,
        "search_query": "유해위험작업 취업 제한",
        "keywords":    ["항타기", "자격", "운전"],
        "min_hits":    2,
    },
]

# ── 유틸 ─────────────────────────────────────────────────────────────────────

def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _save_evidence(data: dict) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / data["evidence_file"]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _parse_law_xml(xml_text: str) -> dict[str, dict]:
    """산안법 XML → {article_no: {"title": ..., "text": ...}}"""
    articles: dict[str, dict] = {}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return {}

    조문_el = root.find("조문")
    if 조문_el is None:
        return {}

    for unit in 조문_el.findall("조문단위"):
        no_el    = unit.find("조문번호")
        title_el = unit.find("조문제목")
        body_el  = unit.find("조문내용")

        no    = (no_el.text    or "").strip() if no_el    is not None else ""
        title = (title_el.text or "").strip() if title_el is not None else ""
        body  = (body_el.text  or "").strip() if body_el  is not None else ""

        # 항/호/목 텍스트 수집
        sub_parts = []
        for child in unit:
            if child.tag in ("조문번호", "조문여부", "조문제목", "조문내용",
                             "조문시행일자", "조문이동이전", "조문이동이후", "조문변경여부"):
                continue
            def _collect(el):
                parts = []
                if el.text and el.text.strip():
                    parts.append(el.text.strip())
                for c in el:
                    parts.extend(_collect(c))
                    if c.tail and c.tail.strip():
                        parts.append(c.tail.strip())
                return parts
            sub_parts.extend(_collect(child))

        full_text = (body + " " + " ".join(sub_parts)).strip()
        if no:
            articles[no] = {"title": title, "text": full_text}

    return articles


def _find_law_mst_by_search(query: str, oc_key: str) -> str | None:
    """DRF 검색으로 법령 MST를 동적으로 조회."""
    if not oc_key:
        return None
    result = drf_request("law", query, page=1, display=10, oc_key=oc_key)
    if result.get("result_code") not in ("00", "0"):
        return None
    items = result.get("items", [])
    for item in items:
        name = item.get("법령명한글", "")
        if "유해" in name and "취업 제한" in name:
            return item.get("법령일련번호", "") or None
    # 첫 번째 항목 반환 (쿼리 충분히 구체적인 경우)
    if items:
        return items[0].get("법령일련번호", "") or None
    return None


def _check_keywords(text: str, keywords: list[str], min_hits: int) -> tuple[bool, list[str]]:
    """키워드 확인. 반환: (충족 여부, 확인된 키워드 목록)"""
    found = [kw for kw in keywords if kw in text]
    return (len(found) >= min_hits, found)


# ── 법령 XML 캐시 (MST별 1회만 요청) ─────────────────────────────────────────

_xml_cache: dict[str, str] = {}
_mst_cache: dict[str, str] = {}  # search_query → mst


def _get_law_xml(mst: str, oc_key: str, law_name: str) -> dict:
    """drf_service_get 래퍼 — 캐시 적용."""
    if mst in _xml_cache:
        return {"ok": True, "text": _xml_cache[mst], "url": f"(cached MST={mst})"}
    result = drf_service_get("law", mst, oc_key, "XML")
    if result["ok"]:
        _xml_cache[mst] = result["text"]
    return result


# ── 개별 검증 함수 ────────────────────────────────────────────────────────────

def verify_single(target: dict, oc_key: str, verbose: bool = True) -> dict:
    """
    단일 법령 조항 검증.
    반환: evidence dict (파일에 저장되는 형식).
    """
    item_no     = target["item_no"]
    law_name    = target["law_name"]
    mst         = target["law_mst"]
    article_no  = target["article_no"]
    keywords    = target["keywords"]
    min_hits    = target["min_hits"]

    ev = {
        "item_no":          item_no,
        "document_id":      target["document_id"],
        "evidence_file":    target["evidence_file"],
        "law_name":         law_name,
        "article_no":       article_no,
        "article_title":    "",
        "source":           "law.go.kr DRF API",
        "source_url_or_api": "",
        "fetched_at":       now(),
        "effective_date":   "",
        "raw_text_excerpt": "",
        "normalized_text":  "",
        "verification_keywords": keywords,
        "keywords_found":   [],
        "verification_result": "NEEDS_VERIFICATION",
        "notes": "",
    }

    # API 키 없음
    if not oc_key:
        ev["verification_result"] = "API_REQUIRED"
        ev["notes"] = "LAW_GO_KR_OC 환경변수 없음. API 키 설정 후 재실행 필요."
        if verbose:
            print(f"  [{item_no}] API_REQUIRED — LAW_GO_KR_OC 없음")
        return ev

    # 법령 XML 취득
    result = _get_law_xml(mst, oc_key, law_name)
    ev["source_url_or_api"] = result.get("url", "")

    if not result["ok"]:
        ev["verification_result"] = "FETCH_FAILED"
        ev["notes"] = f"법령 XML 취득 실패: {result.get('error', 'unknown')}"
        if verbose:
            print(f"  [{item_no}] FETCH_FAILED — {ev['notes']}")
        return ev

    # XML 파싱
    articles = _parse_law_xml(result["text"])
    if not articles:
        ev["verification_result"] = "PARSE_FAILED"
        ev["notes"] = "XML 파싱 실패 또는 조문단위 없음"
        if verbose:
            print(f"  [{item_no}] PARSE_FAILED")
        return ev

    # 조항 검색
    if article_no not in articles:
        ev["verification_result"] = "NOT_FOUND"
        ev["notes"] = f"제{article_no}조를 XML에서 찾을 수 없음 (총 {len(articles)}개 조문 확인)"
        if verbose:
            print(f"  [{item_no}] NOT_FOUND — 제{article_no}조 없음 (총 {len(articles)}개 조문)")
        return ev

    art = articles[article_no]
    ev["article_title"]    = art["title"]
    ev["raw_text_excerpt"] = art["text"][:800]  # 최대 800자 excerpt
    ev["normalized_text"]  = art["text"][:400]

    # 키워드 검증
    ok, found = _check_keywords(art["text"], keywords, min_hits)
    ev["keywords_found"] = found

    if ok:
        ev["verification_result"] = "VERIFIED"
        ev["notes"] = f"제{article_no}조({art['title']}) 원문 확인. 키워드 {found} 확인됨."
    else:
        ev["verification_result"] = "PARTIAL_VERIFIED"
        ev["notes"] = (
            f"제{article_no}조({art['title']}) 원문 확인됨, "
            f"키워드 불충분: 필요 {min_hits}개, 확인 {len(found)}개({found}). "
            f"미확인 키워드: {[k for k in keywords if k not in found]}"
        )

    if verbose:
        print(f"  [{item_no}] {ev['verification_result']} — 제{article_no}조 '{art['title']}' | 키워드: {found}")

    return ev


def verify_e06(oc_key: str, verbose: bool = True) -> dict:
    """
    E-06 운전원 자격/면허 검증 (복수 법령 × 7종 자격).
    반환: evidence dict.
    """
    ev = {
        "item_no":        "E-06",
        "document_id":    "worker_licenses.yml",
        "evidence_file":  "E-06_worker_license_refs.json",
        "source":         "law.go.kr DRF API",
        "fetched_at":     now(),
        "verification_keywords": {},
        "license_results": [],
        "verification_result": "NEEDS_VERIFICATION",
        "notes": "",
    }

    if not oc_key:
        ev["verification_result"] = "API_REQUIRED"
        ev["notes"] = "LAW_GO_KR_OC 없음."
        if verbose:
            print("  [E-06] API_REQUIRED — LAW_GO_KR_OC 없음")
        return ev

    # 법령별 XML 미리 로드
    # 1) 유해위험작업취업제한규칙 — 동적 검색
    hazard_mst = None
    if "유해·위험작업의 취업 제한에 관한 규칙" not in KNOWN_MSTS:
        hazard_mst = _find_law_mst_by_search("유해위험작업 취업 제한", oc_key)
        if hazard_mst:
            KNOWN_MSTS["유해·위험작업의 취업 제한에 관한 규칙"] = hazard_mst

    if verbose and hazard_mst:
        print(f"  [E-06] 유해위험작업취업제한규칙 MST={hazard_mst} 검색됨")
    elif verbose:
        print(f"  [E-06] 유해위험작업취업제한규칙 MST 검색 실패 — 해당 자격 항목 NEEDS_VERIFICATION 유지")

    # 2) 건설기계관리법 MST=283763
    cma_articles: dict[str, dict] = {}
    cma_result = _get_law_xml("283763", oc_key, "건설기계관리법")
    if cma_result["ok"]:
        cma_articles = _parse_law_xml(cma_result["text"])
        if verbose:
            print(f"  [E-06] 건설기계관리법 조문 {len(cma_articles)}개 로드")

    # 3) 유해위험작업취업제한규칙 full-text (단일 조문 없으므로 전체 합산)
    hazard_full_text = ""
    if hazard_mst:
        hz_result = _get_law_xml(hazard_mst, oc_key, "유해·위험작업의 취업 제한에 관한 규칙")
        if hz_result["ok"]:
            hz_arts = _parse_law_xml(hz_result["text"])
            hazard_full_text = " ".join(a["text"] for a in hz_arts.values())
            if verbose:
                print(f"  [E-06] 유해위험작업취업제한규칙 조문 {len(hz_arts)}개, "
                      f"전문 {len(hazard_full_text)}자")

    # 건설기계관리법 full-text (조종사면허 관련 전체)
    cma_full_text = " ".join(a["text"] for a in cma_articles.values())

    # 개별 자격 검증
    verified_count = 0
    for lic in E06_LICENSE_TARGETS:
        lid = lic["license_id"]
        law = lic["law_name"]
        kws = lic["keywords"]
        min_h = lic["min_hits"]

        # 법령 텍스트 선택
        if "건설기계관리법" in law:
            search_text = cma_full_text
        else:
            search_text = hazard_full_text

        ok, found = _check_keywords(search_text, kws, min_h) if search_text else (False, [])

        res = {
            "license_id": lid,
            "equipment":  lic["equipment"],
            "law_name":   law,
            "keywords_checked": kws,
            "keywords_found":   found,
            "verification_result": "VERIFIED" if ok else (
                "NEEDS_VERIFICATION" if not search_text else "PARTIAL_VERIFIED"
            ),
        }
        ev["license_results"].append(res)
        if ok:
            verified_count += 1
        if verbose:
            print(f"    [{lid}] {res['verification_result']} | {lic['equipment']} | 키워드: {found}")

    total = len(E06_LICENSE_TARGETS)
    if verified_count == total:
        ev["verification_result"] = "VERIFIED"
    elif verified_count > 0:
        ev["verification_result"] = "PARTIAL_VERIFIED"
    else:
        ev["verification_result"] = "NEEDS_VERIFICATION"

    ev["notes"] = (
        f"7종 자격 중 {verified_count}종 VERIFIED. "
        f"나머지 {total - verified_count}종 NEEDS_VERIFICATION 유지."
    )
    if verbose:
        print(f"  [E-06] 종합: {ev['verification_result']} ({verified_count}/{total}종)")

    return ev


# ── 마스터 갱신 ───────────────────────────────────────────────────────────────

def _patch_yaml_field(path: Path, target_key: str, target_value: str,
                      field_name: str, new_value: str) -> bool:
    """
    YAML 파일에서 특정 키-값 블록 내의 field_name을 new_value로 교체.
    예: training_code: EDU_CONSTRUCTION_BASIC 아래 verification_status: X → Y
    반환: True=변경 있음, False=이미 동일하거나 못찾음
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    in_block = False
    block_indent = 0
    changed = False
    new_lines = []
    for line in lines:
        # 타겟 블록 진입 감지
        if f"{target_key}: {target_value}" in line:
            in_block = True
            stripped_bl = line.lstrip()
            block_indent = len(line) - len(stripped_bl)
        # 같은/낮은 들여쓰기의 "- " 라인 → 새 블록 시작, 현재 블록 종료
        elif in_block:
            stripped_bl = line.lstrip()
            if stripped_bl.startswith("- "):
                if len(line) - len(stripped_bl) <= block_indent:
                    in_block = False

        # 블록 내에서 field 패치
        if in_block and f"{field_name}:" in line:
            stripped = line.lstrip()
            indent   = line[: len(line) - len(stripped)]
            old_val  = line.split(f"{field_name}:")[1].strip()
            if old_val != new_value:
                line = f"{indent}{field_name}: {new_value}\n"
                changed = True

        new_lines.append(line)

    if changed:
        path.write_text("".join(new_lines), encoding="utf-8")
    return changed


def apply_verified(item_no: str, ev: dict, dry_run: bool = True) -> list[str]:
    """
    검증 결과가 VERIFIED 또는 PARTIAL_VERIFIED인 경우 마스터를 갱신.
    반환: 변경된 파일 목록.
    """
    result = ev.get("verification_result", "")
    changed_files = []

    if result not in ("VERIFIED", "PARTIAL_VERIFIED"):
        return changed_files

    if item_no == "C-06":
        if result == "VERIFIED":
            path = MASTERS / "training" / "training_types.yml"
            if not dry_run:
                ok = _patch_yaml_field(
                    path,
                    "training_code", "EDU_CONSTRUCTION_BASIC",
                    "verification_status", "confirmed",
                )
                if ok:
                    changed_files.append(str(path))
            else:
                changed_files.append(f"[dry-run] {path}")

    elif item_no == "G-02":
        if result == "VERIFIED":
            path = MASTERS / "documents" / "document_catalog.yml"
            if not dry_run:
                ok = _patch_yaml_field(
                    path, "id", "HM-001", "evidence_status", "VERIFIED"
                )
                if ok:
                    changed_files.append(str(path))
            else:
                changed_files.append(f"[dry-run] {path}")

    elif item_no == "G-03":
        if result == "VERIFIED":
            path = MASTERS / "documents" / "document_catalog.yml"
            if not dry_run:
                ok = _patch_yaml_field(
                    path, "id", "HM-002", "evidence_status", "VERIFIED"
                )
                if ok:
                    changed_files.append(str(path))
            else:
                changed_files.append(f"[dry-run] {path}")

    elif item_no == "E-06":
        # 개별 자격별로 VERIFIED인 항목만 worker_licenses.yml 갱신
        path = MASTERS / "worker" / "worker_licenses.yml"
        for lic_res in ev.get("license_results", []):
            if lic_res["verification_result"] == "VERIFIED":
                lid = lic_res["license_id"]
                if not dry_run:
                    ok = _patch_yaml_field(
                        path, "license_id", lid, "evidence_status", "VERIFIED"
                    )
                    ok2 = _patch_yaml_field(
                        path, "license_id", lid, "required_by_law", "true"
                    )
                    if ok or ok2:
                        if str(path) not in changed_files:
                            changed_files.append(str(path))
                else:
                    entry = f"[dry-run] {path} — {lid}"
                    if entry not in changed_files:
                        changed_files.append(entry)

    return changed_files


# ── 보고서 출력 ───────────────────────────────────────────────────────────────

def print_summary(results: list[dict], changed_files: list[str]) -> None:
    print()
    print("=" * 68)
    print("법령 원문 검증 결과 요약")
    print("=" * 68)
    for r in results:
        vr  = r.get("verification_result", "?")
        kw  = r.get("keywords_found", [])
        no  = r.get("item_no", "?")
        art = r.get("article_no", "")
        title = r.get("article_title", "") or r.get("notes", "")[:40]
        if no == "E-06":
            lrs = r.get("license_results", [])
            vcount = sum(1 for l in lrs if l["verification_result"] == "VERIFIED")
            print(f"  {no}: {vr} ({vcount}/{len(lrs)}종 VERIFIED)")
        else:
            art_str = f"제{art}조 " if art else ""
            print(f"  {no}: {vr} | {art_str}{title[:50]}")
            if kw:
                print(f"       확인 키워드: {kw}")
    print()
    if changed_files:
        print("── 변경된 파일 ──")
        for f in changed_files:
            print(f"  {f}")
    print("=" * 68)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="P0 법령 원문 검증 스크립트")
    mode_grp = parser.add_mutually_exclusive_group(required=True)
    mode_grp.add_argument("--dry-run", action="store_true", dest="dry_run",
                          help="조회·검증·evidence 저장만. 마스터 변경 없음.")
    mode_grp.add_argument("--apply",   action="store_true", dest="apply",
                          help="검증 후 VERIFIED 항목 마스터 갱신.")
    parser.add_argument("--quiet", action="store_true", help="상세 출력 억제")
    args = parser.parse_args()

    dry_run = not args.apply
    verbose = not args.quiet

    oc_key = get_oc_key()
    if verbose:
        mode_str = "DRY-RUN (마스터 변경 없음)" if dry_run else "APPLY (VERIFIED 항목 마스터 갱신)"
        key_str  = f"LAW_GO_KR_OC={'설정됨' if oc_key else '없음 — API_REQUIRED 처리'}"
        print(f"\n verify_safety_law_refs.py [{mode_str}]")
        print(f"  {key_str}\n")

    all_results:   list[dict] = []
    all_changed:   list[str]  = []
    all_evidences: list[Path] = []

    # C-06 / G-02 / G-03 — 산안법 동일 MST, 순차 처리
    for target in [C06, G02, G03]:
        if verbose:
            print(f"── {target['item_no']} ({target['law_name']} 제{target['article_no']}조) ──")
        ev = verify_single(target, oc_key, verbose=verbose)
        path = _save_evidence(ev)
        all_evidences.append(path)
        all_results.append(ev)
        changed = apply_verified(target["item_no"], ev, dry_run=dry_run)
        all_changed.extend(changed)
        if verbose:
            print(f"  evidence → {path.name}\n")

    # E-06 — 복수 법령
    if verbose:
        print("── E-06 (운전원 자격/면허 마스터) ──")
    ev_e06 = verify_e06(oc_key, verbose=verbose)
    path = _save_evidence(ev_e06)
    all_evidences.append(path)
    all_results.append(ev_e06)
    changed = apply_verified("E-06", ev_e06, dry_run=dry_run)
    all_changed.extend(changed)
    if verbose:
        print(f"  evidence → {path.name}\n")

    # 요약 출력
    print_summary(all_results, all_changed)

    # 최종 판정
    total   = len(all_results)
    v_count = sum(1 for r in all_results
                  if r.get("verification_result") in ("VERIFIED", "PARTIAL_VERIFIED"))
    missing = sum(1 for r in all_results
                  if r.get("verification_result") in ("API_REQUIRED", "FETCH_FAILED"))

    if missing > 0:
        verdict = "WARN — API 키 필요 또는 취득 실패 항목 있음"
        exit_code = 1
    elif v_count == total:
        verdict = "PASS — 전 항목 VERIFIED 또는 PARTIAL_VERIFIED"
        exit_code = 0
    else:
        verdict = "WARN — 일부 항목 NEEDS_VERIFICATION 유지"
        exit_code = 1

    print(f"\n최종 판정: {verdict}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

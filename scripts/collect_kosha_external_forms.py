"""
KOSHA/외부 공공 다운로드 타깃 — 작업계획서·TBM·교육일지·회의록 보강 수집

모두 공개 URL이므로 로그인 불필요. User-Agent만 지정.

저장: data/raw/kosha_external/{카테고리}/{원본파일명}
categories:
  - work_plan        (작업계획서 본체)
  - hoisting         (양중·크레인)
  - confined_space   (밀폐공간)
  - welding          (용접·화기)
  - excavation       (굴착)
  - aerial_lift      (고소작업대)
  - tbm              (작업 전 안전회의)
  - education        (교육일지)
  - committee        (산업안전보건위원회)
  - general          (일반 안전작업허가 등)
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw" / "kosha_external"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "*/*",
}

# (category, url, doc_type, title, authority_grade, origin)
TARGETS: list[tuple[str, str, str, str, str, str]] = [
    # ── 작업계획서 — 조선·건설기계·중량물·전기 ────────────────────────────
    ("work_plan",
     "https://oshri.kosha.or.kr/kosha/data/shipbuilding_A.do?mode=download&articleNo=327835&attachNo=171689",
     "작업계획서",
     "작업계획서 및 안전교육일지 (조선업 본선용)", "B",
     "KOSHA 조선업 자료실 (articleNo=327835)"),
    ("hoisting",
     "https://oshri.kosha.or.kr/extappKosha/kosha/guidance/fileDownload.do?sfhlhTchnlgyManualNo=C-102-2023&fileOrdrNo=2",
     "작업계획서",
     "건설현장 중량물 취급 작업계획서 (이동식 크레인) 작성지침 C-102-2023", "B",
     "KOSHA Guide C-102-2023"),
    ("work_plan",
     "https://oshri.kosha.or.kr/extappKosha/kosha/guidance/fileDownload.do?sfhlhTchnlgyManualNo=E-154-2016&fileOrdrNo=3",
     "작업계획서",
     "전기작업계획서 작성에 관한 기술지침 E-154-2016", "B",
     "KOSHA Guide E-154-2016"),

    # ── 굴착작업 ────────────────────────────────────────────────────────
    ("excavation",
     "https://oshri.kosha.or.kr/extappKosha/kosha/guidance/fileDownload.do?sfhlhTchnlgyManualNo=C-39-2023&fileOrdrNo=2",
     "작업계획서",
     "굴착공사 안전작업 지침 C-39-2023", "B",
     "KOSHA Guide C-39-2023"),

    # ── 고소작업대 ────────────────────────────────────────────────────
    ("aerial_lift",
     "https://oshri.kosha.or.kr/kosha/data/construction.do?mode=download&articleNo=453778&attachNo=260018",
     "작업계획서",
     "차량형 고소작업대 안전작업 자료 (재해 사례 및 작업계획서)", "B",
     "KOSHA 건설안전 자료실 (articleNo=453778)"),
    ("aerial_lift",
     "https://oshri.kosha.or.kr/ebook/fcatalog/download.jsp?kd=feb&sdir=572&cimg=&fn=204+%EC%95%88%EC%A0%84%EA%B4%80%EB%A6%AC%EA%B3%84%ED%9A%8D+%EB%B0%8F+%EC%9C%84%ED%97%98%EC%84%B1%ED%8F%89%EA%B0%80_%EC%8B%9C%EC%A0%80%ED%98%95+%EA%B3%A0%EC%86%8C%EC%9E%91%EC%97%85%EB%8C%80+%EC%82%AC%EC%9A%A9.pdf",
     "작업계획서",
     "안전관리계획 및 위험성평가 — 시저형 고소작업대 사용", "B",
     "KOSHA e-book 572 (204)"),

    # ── 밀폐공간 ────────────────────────────────────────────────────────
    ("confined_space",
     "https://oshri.kosha.or.kr/extappKosha/kosha/guidance/fileDownload.do?sfhlhTchnlgyManualNo=H-80-2021&fileOrdrNo=13",
     "작업계획서",
     "밀폐공간 작업 프로그램 수립 및 시행 기술지침 H-80-2021", "B",
     "KOSHA Guide H-80-2021"),
    ("confined_space",
     "https://oshri.kosha.or.kr/extappKosha/kosha/guidance/fileDownload.do?sfhlhTchnlgyManualNo=X-68-2015&fileOrdrNo=3",
     "작업계획서",
     "밀폐공간 위험관리 기술지침 X-68-2015", "B",
     "KOSHA Guide X-68-2015"),
    ("confined_space",
     "https://oshri.kosha.or.kr/kosha/data/musculoskeletalPreventionData_A.do?mode=download&articleNo=296344&attachNo=166843",
     "안전작업매뉴얼",
     "밀폐공간 안전작업 매뉴얼", "B",
     "KOSHA 자료실 (articleNo=296344)"),

    # ── 용접·화기·작업허가 ─────────────────────────────────────────────
    ("welding",
     "https://oshri.kosha.or.kr/extappKosha/kosha/guidance/fileDownload.do?sfhlhTchnlgyManualNo=P-94-2021&fileOrdrNo=2",
     "작업계획서",
     "안전작업허가지침 (용접·화기 포함) P-94-2021", "B",
     "KOSHA Guide P-94-2021"),

    # ── TBM / 작업전 안전회의 ─────────────────────────────────────────
    ("tbm",
     "https://oshri.kosha.or.kr/extappKosha/kosha/guidance/fileDownload.do?sfhlhTchnlgyManualNo=Z-5-2022&fileOrdrNo=2",
     "TBM",
     "작업허가 및 작업전 안전회의에 관한 지침 Z-5-2022", "B",
     "KOSHA Guide Z-5-2022"),
    ("tbm",
     "https://kosha.or.kr/ebook/fcatalog/download.jsp?kd=feb&sdir=544&cimg=&fn=TBM+%EC%8B%A4%ED%96%89+%EC%8B%9C%EB%82%98%EB%A6%AC%EC%98%A4+%EB%B0%8F+%ED%9A%8C%EC%9D%98%EB%A1%9D+%EC%96%91%EC%8B%9D.pdf",
     "TBM",
     "TBM 실행 시나리오 및 회의록 양식", "B",
     "KOSHA e-book 544"),

    # ── 교육일지 ────────────────────────────────────────────────────
    ("education",
     "https://www.moel.go.kr/local/uijeongbu/common/downloadFile.do?file_seq=21171285442&bbs_seq=1332895608140&bbs_id=LOCAL1",
     "교육일지",
     "안전보건교육일지 (양식) — MOEL 의정부지청", "B",
     "MOEL 의정부지청 자료실 (bbs_seq=1332895608140)"),

    # ── 산업안전보건위원회 회의록 (법정 별표 양식) ────────────────────────
    ("committee",
     "https://www.law.go.kr/LSW/flDownload.do?flSeq=138431615&flNm=%5B%EB%B3%84%ED%91%9C+2%EC%9D%982%5D+%EC%82%B0%EC%97%85%EC%95%88%EC%A0%84%EB%B3%B4%EA%B1%B4%EC%9C%84%EC%9B%90%ED%9A%8C+%ED%9A%8C%EC%9D%98%EB%A1%9D+%EC%96%91%EC%8B%9D&bylClsCd=200201",
     "회의록",
     "[별표 2의2] 산업안전보건위원회 회의록 양식 (법정 별표)", "A",
     "법령정보센터 flDownload (flSeq=138431615)"),

    # ── 안전작업절차 / 기타 일반 ────────────────────────────────────
    ("general",
     "https://oshri.kosha.or.kr/extappKosha/kosha/guidance/fileDownload.do?sfhlhTchnlgyManualNo=Z-47-2022&fileOrdrNo=2",
     "작업계획서",
     "안전작업절차에 관한 지침 Z-47-2022", "B",
     "KOSHA Guide Z-47-2022"),
]


def extract_filename(resp: requests.Response, url: str) -> str:
    cd = resp.headers.get("Content-Disposition", "")
    # filename*=UTF-8''... 우선
    m = re.search(r"filename\*\s*=\s*(?:UTF-8|utf-8)'[^']*'([^;]+)", cd)
    if m:
        try:
            return unquote(m.group(1).strip()).strip('"')
        except Exception:
            pass
    # filename=...
    m = re.search(r'filename\s*=\s*"?([^";]+)"?', cd)
    if m:
        name = m.group(1).strip()
        try:
            # ISO-8859-1로 온 경우 디코딩
            return name.encode("iso-8859-1").decode("utf-8")
        except Exception:
            return name
    # URL에서 추출
    tail = url.rsplit("/", 1)[-1].split("?", 1)[0]
    try:
        tail = unquote(tail)
    except Exception:
        pass
    if not tail or len(tail) < 3:
        return "download.bin"
    return tail


def download(url: str, dst_dir: Path) -> tuple[Path | None, str]:
    dst_dir.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, verify=False, allow_redirects=True)
    except Exception as e:  # noqa: BLE001
        return None, f"GET 실패: {e}"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    # html page?
    ctype = r.headers.get("Content-Type", "")
    if "text/html" in ctype and len(r.content) < 10000:
        return None, f"HTML 응답 — 실제 파일 아님 ({len(r.content)}B)"
    filename = extract_filename(r, url)
    # URL 인코딩 해제
    try:
        filename = unquote(filename)
    except Exception:
        pass
    # Windows 예약문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # 확장자와 stem 분리 후 stem을 150자로 제한
    stem, dot, ext = filename.rpartition(".")
    if dot and len(stem) > 150:
        filename = stem[:150] + "." + ext
    else:
        filename = filename[:200]
    if not filename.lower().endswith((".hwp", ".hwpx", ".pdf", ".docx", ".xlsx", ".xls", ".zip")):
        # URL 패턴에서 filename이 불완전 — 확장자 추측
        if "hwp" in ctype.lower() or "hangul" in ctype.lower():
            filename += ".hwp"
        elif "pdf" in ctype.lower():
            filename += ".pdf"
        else:
            # 내용 시그니처 체크
            sig = r.content[:4]
            if sig == b"%PDF":
                filename += ".pdf"
            elif sig[:2] == b"PK":  # zip/docx/hwpx/xlsx
                filename += ".zip"
    dst = dst_dir / filename
    if dst.exists() and dst.stat().st_size == len(r.content):
        return dst, f"skip (existing same size, {dst.stat().st_size:,}B)"
    dst.write_bytes(r.content)
    return dst, f"saved {len(r.content):,}B"


def main() -> int:
    manifest = []
    n_ok = 0
    n_fail = 0
    for category, url, doc_type, title, authority, origin in TARGETS:
        dst_dir = OUT_DIR / category
        print(f"\n[{category}] {title}")
        print(f"  URL: {url}")
        saved, msg = download(url, dst_dir)
        print(f"  → {msg}")
        if saved:
            n_ok += 1
            manifest.append({
                "category": category,
                "doc_type": doc_type,
                "title": title,
                "authority": authority,
                "origin": origin,
                "url": url,
                "local": str(saved.relative_to(ROOT)).replace("\\", "/"),
                "size": saved.stat().st_size,
                "msg": msg,
            })
        else:
            n_fail += 1
            manifest.append({
                "category": category,
                "doc_type": doc_type,
                "title": title,
                "authority": authority,
                "origin": origin,
                "url": url,
                "local": None,
                "size": 0,
                "msg": msg,
            })
        time.sleep(0.5)

    import json as _json
    mpath = OUT_DIR / "download_manifest.json"
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(_json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== 완료 ok={n_ok} fail={n_fail} manifest={mpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

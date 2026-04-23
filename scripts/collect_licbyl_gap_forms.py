"""
licbyl 격차 서식 수집 — Step 3 확장

기존 licbyl 수집은 "산업안전보건", "위험성평가", "안전보건관리" 키워드만 사용.
본 스크립트는 아래 키워드로 확장 검색하여 누락 법정 서식을 추가 다운로드한다:

- 산업재해      → 별지 제30호서식 산업재해조사표
- 산업재해조사   → 산업재해조사표 + 신청서류
- 교육          → 안전보건교육 관련 별지
- 회의록        → 산업안전보건위원회 회의록 등
- 안전점검      → 안전점검 관련 서식
- 유해위험방지   → 유해위험방지계획서 관련 (보강)
- 작업계획서    → 작업계획서 법정 서식 (존재 시)
- 도급          → 유해·위험작업 도급승인 신청서 (별지 31·33호)

저장:
- raw: data/raw/law_api/licbyl/files/{별표일련번호}/{원본파일명}
- index: data/raw/law_api/licbyl/licbyl_gap_index.json

Step 3의 collect_forms_to_repository.py 재실행으로 자동 카탈로그화 가능.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote, unquote
from xml.etree import ElementTree as ET

import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

SERVICE_KEY = os.getenv("DATA_GO_KR_SERVICE_KEY", "")
ENDPOINT = "http://apis.data.go.kr/1170000/law/licbylSearchList.do"
LAWGO_BASE = "https://www.law.go.kr"
TARGET = "licbyl"
OUT_DIR = ROOT / "data" / "raw" / "law_api" / "licbyl"
FILES_DIR = OUT_DIR / "files"
INDEX_PATH = OUT_DIR / "licbyl_gap_index.json"

QUERIES = [
    "산업재해",
    "산업재해조사",
    "교육",
    "회의록",
    "안전점검",
    "유해위험방지",
    "작업계획",
    "도급",
]


def gw_search(query: str, page_no: int = 1, num_of_rows: int = 100) -> dict:
    if not SERVICE_KEY:
        return {"result_code": "no_key", "items": [], "total": 0}
    q = quote(query, safe="")
    url = (
        f"{ENDPOINT}?serviceKey={SERVICE_KEY}&target={TARGET}&query={q}"
        f"&numOfRows={num_of_rows}&pageNo={page_no}"
    )
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    total = int((root.findtext("totalCnt") or "0"))
    items = []
    for elem in root.findall(TARGET):
        items.append({c.tag: (c.text or "").strip() for c in elem})
    return {"result_code": (root.findtext("resultCode") or "00"), "items": items, "total": total}


def is_target_item(item: dict) -> bool:
    """관련 법령이 산업안전보건 계열이거나, 제목이 타깃 키워드를 포함하는지."""
    law = (item.get("관련법령명") or "")
    title = (item.get("별표명") or "")
    if any(k in law for k in (
        "산업안전보건법", "산업안전보건기준에 관한 규칙",
        "중대재해", "안전보건공단법",
    )):
        return True
    if any(k in title for k in (
        "산업재해조사표", "교육", "회의록", "TBM", "작업계획서",
        "안전점검", "유해위험", "도급", "위험성평가",
    )):
        return True
    return False


def extract_id(item: dict) -> str:
    return item.get("별표일련번호") or item.get("_id") or ""


def download_one(url: str, dst_dir: Path, log_prefix: str = "") -> Path | None:
    """Content-Disposition에서 파일명 추출하여 저장. 이미 동일 size면 skip."""
    if not url:
        return None
    full_url = url if url.startswith("http") else LAWGO_BASE + url
    try:
        r = requests.get(full_url, timeout=30, verify=False, allow_redirects=True)
        r.raise_for_status()
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ {log_prefix} GET 실패: {e}")
        return None

    cd = r.headers.get("Content-Disposition", "")
    filename = None
    m = re.search(r'filename\s*\*?=(?:UTF-\d[\'"]*)?["\']?([^"\';]+)["\']?', cd)
    if m:
        try:
            filename = unquote(m.group(1)).strip()
        except Exception:
            filename = m.group(1).strip()
    if not filename:
        # URL에서 추출
        tail = full_url.rsplit("/", 1)[-1]
        try:
            filename = unquote(tail.split("?", 1)[0])
        except Exception:
            filename = tail.split("?", 1)[0]
        if not filename or len(filename) < 3:
            filename = "download.bin"

    # Windows 예약문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)[:200]
    dst = dst_dir / filename
    if dst.exists() and dst.stat().st_size == len(r.content):
        print(f"  = {log_prefix} skip (existing same size): {filename}")
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(r.content)
    print(f"  ✓ {log_prefix} saved {dst.stat().st_size:,}B → {filename}")
    return dst


def main() -> int:
    if not SERVICE_KEY:
        print("ERROR: DATA_GO_KR_SERVICE_KEY 미설정", file=sys.stderr)
        return 2

    seen_ids: set[str] = set()
    # 기존 수집본 ID 기억 (중복 다운로드 방지)
    for d in FILES_DIR.iterdir() if FILES_DIR.exists() else []:
        if d.is_dir():
            seen_ids.add(d.name)
    print(f"기존 licbyl ID {len(seen_ids)}개 확인")

    new_items: list[dict] = []
    downloaded: list[dict] = []
    per_query_stats: dict[str, dict] = {}

    for q in QUERIES:
        print(f"\n=== query: {q} ===")
        page = 1
        q_hits = 0
        q_downloaded = 0
        while True:
            r = gw_search(q, page_no=page)
            if r["result_code"] != "00":
                print(f"  API error: {r['result_code']}")
                break
            items = r.get("items", [])
            if not items:
                break
            for it in items:
                if not is_target_item(it):
                    continue
                q_hits += 1
                sid = extract_id(it)
                if not sid:
                    continue
                if sid in seen_ids:
                    continue
                seen_ids.add(sid)
                new_items.append(it)
                dst_dir = FILES_DIR / sid
                ok = False
                for url_field in ("별표서식파일링크", "별표서식PDF파일링크"):
                    u = it.get(url_field, "")
                    if u:
                        saved = download_one(u, dst_dir, log_prefix=f"[{sid}]")
                        if saved:
                            ok = True
                            q_downloaded += 1
                            downloaded.append({
                                "id": sid,
                                "query": q,
                                "title": it.get("별표명", ""),
                                "law": it.get("관련법령명", ""),
                                "kind": it.get("별표종류", ""),
                                "local": str(saved.relative_to(ROOT)).replace("\\", "/"),
                                "source_url": (u if u.startswith("http") else LAWGO_BASE + u),
                            })
                if not ok:
                    print(f"  - {sid}: 파일 링크 없음")
                time.sleep(0.3)
            # pagination
            if len(items) < 100:
                break
            page += 1
            time.sleep(0.5)
        per_query_stats[q] = {"hits": q_hits, "downloaded": q_downloaded}

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(
        json.dumps({
            "queries": QUERIES,
            "per_query": per_query_stats,
            "new_items": new_items,
            "downloaded": downloaded,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n=== 완료 ===")
    print(f"신규 item: {len(new_items)}")
    print(f"다운로드: {len(downloaded)}")
    print(f"index: {INDEX_PATH}")
    for q, s in per_query_stats.items():
        print(f"  {q}: hits={s['hits']} dl={s['downloaded']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

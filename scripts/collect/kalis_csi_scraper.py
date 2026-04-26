"""
kalis_csi_scraper.py — CSI 건설공사 안전관리 종합정보망 사고사례 수집
출처: https://www.csi.go.kr/acd/acdCaseList.do
수집 항목: 사고번호, 공사명, 지역, 발생일시, 조회수, 공종, 사고원인, 사망·부상자수
출력: data/raw/kosha_external/csi_accident_cases.jsonl
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scripts.collect._base import get_logger

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "raw" / "kosha_external"
OUT_FILE = OUT_DIR / "csi_accident_cases.jsonl"
META_FILE = OUT_DIR / "csi_accident_cases_meta.json"

BASE_URL = "https://www.csi.go.kr"
LIST_URL = f"{BASE_URL}/acd/acdCaseList.do"
VIEW_URL = f"{BASE_URL}/acd/acdCaseView.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
PAGE_SIZE = 20
DELAY = 1.0  # 서버 부하 방지
TIMEOUT = 60  # csi.go.kr 응답 느림


def fetch_list_page(session: requests.Session, page: int) -> list[dict]:
    """목록 1페이지 수집 → case_no + 기본 메타 반환"""
    resp = session.post(
        LIST_URL,
        data={"pageIndex": page, "recordCountPerPage": PAGE_SIZE},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("tbody tr")
    items = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        # goDetail('case_no') 패턴에서 case_no 추출
        link = row.find("a", href=lambda h: h and "goDetail" in h)
        if not link:
            continue
        href = link.get("href", "")
        case_no = href.strip("javascript:goDetail('").rstrip("');").strip("'")
        items.append({
            "case_no": case_no,
            "accident_no": cells[0].get_text(strip=True),
            "project_name": cells[1].get_text(strip=True),
            "region": cells[2].get_text(separator=" ", strip=True),
            "occurred_at": cells[3].get_text(strip=True),
            "view_count": cells[4].get_text(strip=True) if len(cells) > 4 else "",
        })
    return items


def fetch_detail(session: requests.Session, case_no: str) -> dict:
    """상세 페이지 수집 → 공종, 사고원인, 사망/부상자 정보 추가"""
    resp = session.post(
        VIEW_URL,
        data={"case_no": case_no},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    detail: dict[str, str] = {}
    # td-head → 다음 td-body 패턴으로 파싱
    rows = soup.select("tr")
    for row in rows:
        heads = row.find_all("td", class_="td-head")
        for head in heads:
            key = head.get_text(strip=True)
            nxt = head.find_next_sibling("td")
            val = nxt.get_text(separator=" ", strip=True) if nxt else ""
            detail[key] = val
    return detail


def get_total_pages(session: requests.Session) -> int:
    resp = session.post(
        LIST_URL,
        data={"pageIndex": 1, "recordCountPerPage": PAGE_SIZE},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # "( 1 / 3,669 페이지) / 총 36,681개" 형태의 텍스트 파싱
    import re
    text = soup.get_text()
    m = re.search(r"총\s*([\d,]+)개", text)
    if m:
        total = int(m.group(1).replace(",", ""))
        return (total + PAGE_SIZE - 1) // PAGE_SIZE
    return 1


def run(max_pages: int | None = None, detail: bool = False) -> int:
    log = get_logger("kalis_csi_scraper")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    log.info("CSI 사고사례 수집 시작")
    total_pages = get_total_pages(session)
    if max_pages:
        total_pages = min(total_pages, max_pages)
    log.info(f"총 페이지: {total_pages}")

    success = fail = 0
    with OUT_FILE.open("w", encoding="utf-8") as fout:
        for page in range(1, total_pages + 1):
            try:
                items = fetch_list_page(session, page)
                for item in items:
                    if detail:
                        try:
                            extra = fetch_detail(session, item["case_no"])
                            item.update(extra)
                            time.sleep(DELAY)
                        except Exception as e:
                            log.warning(f"상세 실패 case_no={item['case_no']}: {e}")
                    fout.write(json.dumps(item, ensure_ascii=False) + "\n")
                    success += 1
                log.info(f"  page {page}/{total_pages}: {len(items)}건")
                time.sleep(DELAY)
            except Exception as e:
                log.error(f"page {page} 실패: {e}")
                fail += 1

    meta = {
        "source": "CSI 건설공사 안전관리 종합정보망",
        "url": LIST_URL,
        "collected_records": success,
        "failed_pages": fail,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "detail_collected": detail,
    }
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"완료: {success}건 수집, {fail}페이지 실패 → {OUT_FILE}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    detail_flag = "--detail" in sys.argv
    max_p = None
    for a in sys.argv[1:]:
        if a.startswith("--max-pages="):
            max_p = int(a.split("=")[1])
    sys.exit(run(max_pages=max_p, detail=detail_flag))

"""
kalis_csi_scraper.py — CSI 건설공사 안전관리 종합정보망 사고사례 수집
출처: https://www.csi.go.kr/acd/acdCaseList.do
수집 항목: 사고번호, 공사명, 지역, 발생일시, 조회수
출력: data/raw/kosha_external/csi_accident_cases.jsonl
실패목록: data/raw/kosha_external/csi_failed_pages.json  (재실행용)

사용법:
  python -m scripts.collect.kalis_csi_scraper                      # 전체 수집
  python -m scripts.collect.kalis_csi_scraper --retry-failed        # 실패 페이지만 재실행
  python -m scripts.collect.kalis_csi_scraper --max-pages=10        # 테스트
"""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

import requests
from bs4 import BeautifulSoup

from scripts.collect._base import get_logger

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "raw" / "kosha_external"
OUT_FILE        = OUT_DIR / "csi_accident_cases.jsonl"
META_FILE       = OUT_DIR / "csi_accident_cases_meta.json"
FAILED_FILE     = OUT_DIR / "csi_failed_pages.json"

BASE_URL = "https://www.csi.go.kr"
LIST_URL = f"{BASE_URL}/acd/acdCaseList.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
PAGE_SIZE = 20
TIMEOUT = 90
WORKERS = 1  # csi.go.kr 동시 요청 차단 — 순차 수집만 가능
RETRY = 3    # 페이지당 최대 재시도 횟수
RETRY_DELAY = 5.0  # 재시도 간 대기 초
PAGE_DELAY = 1.5   # 페이지 간 대기 초


def _new_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def fetch_list_page(page: int) -> tuple[int, list[dict]]:
    """목록 1페이지 → (page, items) — 실패 시 RETRY회 재시도"""
    last_err: Exception | None = None
    for attempt in range(1, RETRY + 1):
        try:
            session = _new_session()
            resp = session.post(
                LIST_URL,
                data={"pageIndex": page, "recordCountPerPage": PAGE_SIZE},
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
            return page, items
        except Exception as e:
            last_err = e
            if attempt < RETRY:
                time.sleep(RETRY_DELAY * attempt)
    raise last_err  # type: ignore[misc]


def get_total_pages() -> tuple[int, int]:
    """(total_count, total_pages)"""
    session = _new_session()
    resp = session.post(
        LIST_URL,
        data={"pageIndex": 1, "recordCountPerPage": PAGE_SIZE},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text()
    m = re.search(r"총\s*([\d,]+)개", text)
    if m:
        total = int(m.group(1).replace(",", ""))
        return total, (total + PAGE_SIZE - 1) // PAGE_SIZE
    return 0, 1


def run(
    max_pages: int | None = None,
    workers: int = WORKERS,
    retry_failed: bool = False,
) -> int:
    log = get_logger("kalis_csi_scraper")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── 재실행 모드: 실패 목록 파일에서 페이지 번호 로드 ──────────────────────
    if retry_failed:
        if not FAILED_FILE.exists():
            log.error(f"실패 목록 없음: {FAILED_FILE}")
            return 1
        failed_meta = json.loads(FAILED_FILE.read_text(encoding="utf-8"))
        pages = failed_meta.get("failed_page_numbers", [])
        total_count = failed_meta.get("total_count", 0)
        total_pages = len(pages)
        log.info(f"[재실행] 실패 페이지 {total_pages}개 재수집 시작: {pages[:10]}{'...' if len(pages) > 10 else ''}")
        # 기존 성공 데이터 유지, 재수집 결과를 append 방식으로 병합
        append_mode = True
    else:
        log.info("CSI 사고사례 수집 시작")
        total_count, total_pages = get_total_pages()
        if max_pages:
            total_pages = min(total_pages, max_pages)
        pages = list(range(1, total_pages + 1))
        log.info(f"총 {total_count}건 / {total_pages}페이지 / 워커 {workers}개")
        append_mode = False

    results: dict[int, list[dict]] = {}
    failed_pages: list[int] = []
    success = fail = 0
    lock = Lock()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_list_page, pg): pg for pg in pages}
        done_count = 0
        for future in as_completed(futures):
            pg = futures[future]
            try:
                page_no, items = future.result()
                with lock:
                    results[page_no] = items
                    success += len(items)
                    done_count += 1
                    if done_count % 10 == 0 or done_count == total_pages:
                        log.info(f"  진행: {done_count}/{total_pages}페이지 완료 ({success}건)")
            except Exception as e:
                log.error(f"page {pg} 실패: {e}")
                with lock:
                    failed_pages.append(pg)
                    fail += 1
            if workers == 1:
                time.sleep(PAGE_DELAY)

    # ── 결과 저장 ──────────────────────────────────────────────────────────────
    if append_mode:
        # 재실행: 기존 파일에 성공 페이지 결과 추가
        with OUT_FILE.open("a", encoding="utf-8") as fout:
            for pg in sorted(results):
                for item in results[pg]:
                    fout.write(json.dumps(item, ensure_ascii=False) + "\n")
        log.info(f"재실행 완료: {success}건 추가, {fail}페이지 재실패")
    else:
        # 신규: 페이지 순서대로 전체 저장
        with OUT_FILE.open("w", encoding="utf-8") as fout:
            for pg in sorted(results):
                for item in results[pg]:
                    fout.write(json.dumps(item, ensure_ascii=False) + "\n")

    # ── 실패 페이지 목록 저장 ──────────────────────────────────────────────────
    if failed_pages:
        failed_pages.sort()
        prev_failed = []
        if retry_failed and FAILED_FILE.exists():
            prev = json.loads(FAILED_FILE.read_text(encoding="utf-8"))
            prev_failed = prev.get("failed_page_numbers", [])
            # 이번에도 실패한 것만 남김
            remaining = [p for p in prev_failed if p in failed_pages]
        else:
            remaining = failed_pages

        failed_data = {
            "total_count": total_count,
            "failed_page_count": len(remaining),
            "failed_page_numbers": remaining,
            "last_run_at": datetime.now(timezone.utc).isoformat(),
            "note": "python -m scripts.collect.kalis_csi_scraper --retry-failed 로 재실행",
        }
        FAILED_FILE.write_text(json.dumps(failed_data, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info(f"실패 목록 저장: {len(remaining)}페이지 → {FAILED_FILE.name}")
    else:
        # 전부 성공 시 실패 파일 제거
        if FAILED_FILE.exists():
            FAILED_FILE.unlink()
            log.info("실패 목록 없음 — 이전 실패 파일 삭제")

    meta = {
        "source": "CSI 건설공사 안전관리 종합정보망",
        "url": LIST_URL,
        "total_count": total_count,
        "collected_records": success,
        "failed_pages": fail,
        "failed_page_file": str(FAILED_FILE.name) if failed_pages else None,
        "workers": workers,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"완료: {success}건 수집, {fail}페이지 실패 → {OUT_FILE}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    max_p = None
    w = WORKERS
    retry = False
    for a in sys.argv[1:]:
        if a.startswith("--max-pages="):
            max_p = int(a.split("=")[1])
        if a.startswith("--workers="):
            w = int(a.split("=")[1])
        if a == "--retry-failed":
            retry = True
    sys.exit(run(max_pages=max_p, workers=w, retry_failed=retry))

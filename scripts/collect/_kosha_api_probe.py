"""
KOSHA 포털 SPA 내부 API 엔드포인트를 탐색.
목적:
    /archive/resources/tech-support/search/all 등 신규 아카이브의 실제 XHR API URL 과
    응답 구조를 캡처하여, 추후 requests 기반 수집기가 호출할 수 있도록 기록.
출력:
    data/raw/kosha_forms/api_probe_<category>.json
실행은 로컬(개발) 1회성. 서버 배포 대상 아님.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "raw" / "kosha_forms"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    ("tech_support_all", "https://portal.kosha.or.kr/archive/resources/tech-support/search/all?page=1&rowsPerPage=20"),
    ("tech_support_industry", "https://portal.kosha.or.kr/archive/resources/tech-support/search/industry"),
    ("master_arch", "https://portal.kosha.or.kr/archive/cent-archive/master-arch"),
    ("safe_health_arch", "https://portal.kosha.or.kr/archive/safe-arch"),
    ("safe_health_form", "https://portal.kosha.or.kr/archive/safe-arch/form-arch"),
    ("safe_data_room", "https://portal.kosha.or.kr/archive/resources/safe-data-room"),
    ("case_arch", "https://portal.kosha.or.kr/archive/case-arch"),
    ("revision_notice", "https://portal.kosha.or.kr/archive/resources/tech-support/revision/RevisionNoticePage"),
]


def capture_xhr(url: str, wait_ms: int = 7000) -> dict:
    xhr_calls: list[dict] = []
    api_jsons: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def on_request(req):
            try:
                if "/api/" in req.url or "ajax" in req.url.lower():
                    entry = {
                        "method": req.method, "url": req.url,
                        "resource_type": req.resource_type,
                        "post_data": None,
                        "headers": {},
                    }
                    try:
                        entry["post_data"] = req.post_data
                    except Exception:
                        pass
                    try:
                        hdrs = req.headers
                        # 민감하지 않은 헤더만 기록
                        entry["headers"] = {k: v for k, v in hdrs.items()
                                            if k.lower() in ("content-type", "accept",
                                                             "x-requested-with", "referer",
                                                             "origin")}
                    except Exception:
                        pass
                    xhr_calls.append(entry)
            except Exception:
                pass

        def on_response(res):
            try:
                u = res.url
                if "/api/" in u and "application/json" in (res.headers.get("content-type") or ""):
                    body = res.text()
                    api_jsons.append({
                        "url": u, "status": res.status,
                        "body": body[:3500]
                    })
            except Exception:
                pass

        page.on("request", on_request)
        page.on("response", on_response)

        try:
            page.goto(url, timeout=30000, wait_until="networkidle")
        except Exception as e:
            pass
        page.wait_for_timeout(wait_ms)

        # 가능한 경우 페이지 내부 'body' 주요 링크 카운트
        try:
            link_count = page.eval_on_selector_all("a[href]", "els => els.length")
            text_preview = page.inner_text("body")[:800]
        except Exception:
            link_count = -1
            text_preview = ""

        browser.close()

    return {
        "url": url,
        "xhr_calls": xhr_calls,
        "api_jsons": api_jsons,
        "link_count": link_count,
        "text_preview": text_preview,
    }


def main() -> int:
    for label, url in TARGETS:
        print(f"\n==== {label} ====\n  {url}")
        try:
            out = capture_xhr(url)
        except Exception as e:
            print(f"  [FAIL] {e!r}")
            continue
        out_path = OUT_DIR / f"api_probe_{label}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"  xhr_calls: {len(out['xhr_calls'])}  api_jsons: {len(out['api_jsons'])}  links: {out['link_count']}")
        for c in out["xhr_calls"][:10]:
            print(f"   - {c['method']} {c['url']}")
        print(f"  → {out_path}")
        time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

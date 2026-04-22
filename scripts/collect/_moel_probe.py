"""MOEL 정책자료실 HTML 구조 탐색 (1회성 디버그 도구)."""
import urllib3
urllib3.disable_warnings()
import re
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}


def probe_detail(bbs_seq: str = "20260401032") -> None:
    r = requests.get(
        "https://www.moel.go.kr/policy/policydata/view.do",
        params={"bbs_seq": bbs_seq},
        headers=HEADERS, verify=False, timeout=20,
    )
    print("detail status:", r.status_code, "size:", len(r.text))
    html = r.text

    # file_seq 주변 context
    for m in list(re.finditer(r"file_seq=\d+", html))[:3]:
        pos = m.start()
        print("--- context ---")
        print(html[max(0, pos - 200):pos + 300])

    # 첨부 링크 후보
    hrefs = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', html)
    hits = [(h, t) for h, t in hrefs if "file_seq" in h or ".hwp" in h or ".pdf" in h or ".xlsx" in h]
    print(f"\n첨부 link 후보: {len(hits)}")
    for h, t in hits[:6]:
        print(f"  href={h[:150]} text={t.strip()[:60]}")

    # fn* 함수 호출
    fns = re.findall(r'onclick="(fn\w+\([^)]*\))"', html)
    print(f"\nonclick 함수: {len(fns)}")
    for f in fns[:10]:
        print(f"  {f}")


def probe_list() -> None:
    r = requests.get(
        "https://www.moel.go.kr/policy/policydata/list.do",
        params={"bbsCd": "OMP_BBS_2", "pageIndex": 1, "_": 1},
        headers=HEADERS, verify=False, timeout=20,
    )
    print("\nlist status:", r.status_code, "size:", len(r.text))
    html = r.text
    # 전체 페이지 수
    for pat in (r"총\s*<em[^>]*>([\d,]+)</em>\s*건",
                r"totalCount[^\d]+(\d+)",
                r"pageIndex\s*=\s*(\d+)\s*/\s*(\d+)"):
        m = re.search(pat, html)
        if m:
            print(f"  found: {pat!r} -> {m.groups()}")

    # 페이지네이션 링크
    pgs = re.findall(r"pageIndex=(\d+)", html)
    print("  pageIndex 후보:", sorted(set(pgs))[:10], "...")


if __name__ == "__main__":
    probe_detail()
    probe_list()

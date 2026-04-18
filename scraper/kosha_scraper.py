"""
KOSHA 포털 업종별 안전보건 자료 전체 수집기
URL 패턴: /archive/cent-archive/indust-arch/indust-page{N}/indust-page{N}-list{M}?page=P&rowsPerPage=100
업종: 1=제조업 2=건설업 3=서비스업 4=조선업 5=기타산업
자료유형: 1=OPS 2=동영상 3=외국어교재 4=외국어교안 5=기타
"""
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

load_dotenv(Path(__file__).parent / ".env")

ID = os.getenv("KOSHA_ID")
PW = os.getenv("KOSHA_PW")
BASE = "https://portal.kosha.or.kr"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INDUSTRIES = {1: "제조업", 2: "건설업", 3: "서비스업", 4: "조선업", 5: "기타산업"}
LIST_TYPES = {1: "OPS", 2: "동영상", 3: "외국어교재", 4: "외국어교안", 5: "기타"}


def login(page):
    safe_goto(page, f"{BASE}/")
    page.click("a:has-text('로그인')")
    page.wait_for_timeout(2000)
    # popup이 렌더링될 때까지 최대 5초 대기
    for _ in range(10):
        exists = page.evaluate("!!document.querySelector('.popup')")
        if exists:
            break
        page.wait_for_timeout(500)
    page.evaluate("const p=document.querySelector('.popup'); if(p) p.style.display='block'")
    page.wait_for_timeout(500)
    page.eval_on_selector(
        ".inputGroup input[type=text]",
        f"el=>{{el.value='{ID}';el.dispatchEvent(new Event('input',{{bubbles:true}}))}}"
    )
    page.eval_on_selector(
        ".password input[type=password]",
        f"el=>{{el.value='{PW}';el.dispatchEvent(new Event('input',{{bubbles:true}}))}}"
    )
    page.wait_for_timeout(300)
    page.eval_on_selector(
        "section.login",
        "el=>{const btn=el.querySelector('button[type=button]');if(btn)btn.click()}"
    )
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    ok = page.locator("button:has-text('로그아웃')").count() > 0
    print(f"[login] {'성공' if ok else '실패'}")
    return ok


ITEM_JS = """els => els.map(e => {
    const titleEl = e.querySelector('p.tit, .tit, strong, p');
    const links = [...e.querySelectorAll('a[href]')];
    const dateEl = e.querySelector('.date, time, [class*=date]');
    const dlEl = e.querySelector('a.download, a[class*=down]');
    const title = titleEl ? titleEl.innerText.trim() : e.innerText.trim().replace(/\\s+/g,' ').substring(0,120);
    return {
        title: title,
        href: links.length > 0 ? links[0].href : '',
        download: dlEl ? dlEl.href : '',
        date: dateEl ? dateEl.innerText.trim() : ''
    };
}).filter(i => i.title.length > 3)"""


def safe_goto(page, url, retries=3):
    for attempt in range(retries):
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
            return True
        except PlaywrightTimeout:
            if attempt < retries - 1:
                print(f"    [retry {attempt+1}] timeout, 5초 후 재시도...")
                time.sleep(5)
            else:
                raise
    return False


def get_items(page):
    return page.eval_on_selector_all("ul.thumbList > li", ITEM_JS)


def get_total_count(page):
    """페이지 텍스트에서 총 건수 추출 (예: '823건')"""
    try:
        txt = page.inner_text("body")
        for line in txt.split("\n"):
            line = line.strip()
            if line.endswith("건") and line[:-1].replace(",", "").isdigit():
                return int(line[:-1].replace(",", ""))
    except Exception:
        pass
    return 0



def click_page_btn(page, page_num):
    """특정 페이지 번호 버튼 클릭. 성공 시 True"""
    try:
        btn = page.locator(
            f".pageLinks a:has-text('{page_num}'), .pagination a:has-text('{page_num}')"
        ).first
        if btn.count() > 0:
            btn.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(800)
            return True
    except Exception:
        pass
    return False


def go_to_page(page, page_num):
    """페이지 번호로 이동 — 그룹 전환 포함"""
    # 1차: 현재 그룹에 목표 버튼이 있으면 바로 클릭
    if click_page_btn(page, page_num):
        return True

    # 2차: 다음 그룹으로 이동 후 목표 버튼 재시도 (최대 3그룹)
    for _ in range(3):
        try:
            nxt = page.locator(
                ".pagination a:has-text('다음'), .pageLinks a:has-text('다음')"
            ).first
            if nxt.count() == 0:
                break
            nxt.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(800)
            if click_page_btn(page, page_num):
                return True
        except Exception:
            break

    return False


def collect_industry_list(page, industry_num, list_num):
    """업종+자료유형 전체 수집 — JS 페이지 클릭 방식"""
    industry = INDUSTRIES[industry_num]
    list_type = LIST_TYPES[list_num]
    base_url = (
        f"{BASE}/archive/cent-archive/indust-arch"
        f"/indust-page{industry_num}/indust-page{industry_num}-list{list_num}"
        f"?page=1&rowsPerPage=12"
    )

    print(f"  [{industry}-{list_type}] 수집 중...")
    safe_goto(page, base_url)
    page.wait_for_timeout(1500)

    total = get_total_count(page)
    total_pages = max(1, (total + 11) // 12)
    print(f"    총 {total}건 / {total_pages}페이지")

    all_items = []
    empty_streak = 0

    for page_num in range(1, total_pages + 1):
        if page_num > 1:
            navigated = go_to_page(page, page_num)
            if not navigated:
                print(f"    [warn] 페이지 {page_num} 이동 실패, 종료")
                break

        items = get_items(page)

        if not items:
            empty_streak += 1
            print(f"    [warn] 페이지 {page_num} 빈 결과 ({empty_streak}/3)")
            if empty_streak >= 3:
                break
            page.wait_for_timeout(1500)
            continue

        empty_streak = 0
        all_items.extend(items)
        print(f"    페이지 {page_num}/{total_pages}: {len(items)}개 | 누적 {len(all_items)}개")
        time.sleep(0.3)

    return {"industry": industry, "type": list_type, "total": total, "count": len(all_items), "items": all_items}


def save(data, filename):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size_kb = path.stat().st_size // 1024
    print(f"  [save] {filename} ({size_kb}KB)")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        )

        print("=== 로그인 ===")
        if not login(page):
            print("로그인 실패")
            return

        all_data = {}

        for ind_num, ind_name in INDUSTRIES.items():
            print(f"\n=== {ind_name} 수집 ===")
            ind_data = {}

            for list_num, list_name in LIST_TYPES.items():
                result = collect_industry_list(page, ind_num, list_num)
                ind_data[list_name] = result
                save(result, f"{ind_name}_{list_name}.json")
                time.sleep(0.5)

            all_data[ind_name] = ind_data
            total = sum(v["count"] for v in ind_data.values())
            print(f"  → {ind_name} 합계: {total}개")

        save(all_data, "kosha_all_data.json")

        grand_total = sum(
            v2["count"]
            for v1 in all_data.values()
            for v2 in v1.values()
        )
        print(f"\n=== 완료 | 전체 {grand_total}개 ===")
        browser.close()


if __name__ == "__main__":
    main()

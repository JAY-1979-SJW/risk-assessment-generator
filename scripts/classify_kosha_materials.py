"""
classify_kosha_materials.py — KOSHA 자료 세부 분류기 v1.0

parse_status='success' 인 kosha_material_files(2,047건)를 대상으로
제목·키워드·본문 앞부분을 분석해 kosha_material_classifications에 upsert.

Usage:
    python scripts/classify_kosha_materials.py --dry-run
    python scripts/classify_kosha_materials.py --apply
    python scripts/classify_kosha_materials.py --report
    python scripts/classify_kosha_materials.py --apply --limit 100
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CLASSIFIER_VERSION = "v1.0"

# ── DB ────────────────────────────────────────────────────────────────────────

def get_conn():
    url = (
        os.getenv("COMMON_DATA_URL")
        or os.getenv("KRAS_DB_URL")
        or os.getenv("DATABASE_URL")
    )
    if not url:
        # .env 자동 로드 시도
        env_file = ROOT / "scraper" / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("COMMON_DATA_URL="):
                    url = line.split("=", 1)[1].strip()
                    break
    if not url:
        sys.exit("[ERROR] COMMON_DATA_URL 환경변수 또는 scraper/.env 가 필요합니다.")
    return psycopg2.connect(url, connect_timeout=10)


# ── KOSHA Guide 번호 패턴 ─────────────────────────────────────────────────────

GUIDE_PATTERNS = [
    # KOSHA GUIDE H-1-2024
    re.compile(r"KOSHA\s*[-]?\s*GUIDE\s*([A-Z])\s*[-]\s*(\d{1,4})\s*[-]\s*(\d{4})", re.IGNORECASE),
    # KOSHA Guide H-1-2024 (space variant)
    re.compile(r"KOSHA\s+Guide\s+([A-Z])[- ](\d{1,4})[- ](\d{4})", re.IGNORECASE),
    # 안전보건기술지침 H-1-2024
    re.compile(r"안전보건기술지침\s*([A-Z])[- ]?(\d{1,4})[- ](\d{4})"),
    # 단순 코드: H-1-2024
    re.compile(r"\b([A-Z])-(\d{1,4})-(\d{4})\b"),
]

GUIDE_GROUP_NAMES = {
    "H": "산업보건",
    "G": "일반안전",
    "C": "건설안전",
    "M": "기계안전",
    "E": "전기안전",
    "P": "화공안전",
    "W": "작업환경",
    "F": "화재폭발",
    "S": "선박조선",
    "O": "사무서비스",
}


def extract_guide_code(text: str, title: str) -> tuple[Optional[str], Optional[str], float]:
    """Returns (code, group, confidence)."""
    combined = (title or "") + "\n" + (text or "")[:3000]
    for pat in GUIDE_PATTERNS:
        m = pat.search(combined)
        if m:
            grp = m.group(1).upper()
            num = m.group(2)
            year = m.group(3)
            code = f"{grp}-{num}-{year}"
            conf = 0.97 if "KOSHA" in combined[:500].upper() else 0.88
            return code, grp, conf
    return None, None, 0.0


# ── 업종 분류 ─────────────────────────────────────────────────────────────────

INDUSTRY_MAP = {
    "construction":  ["건설", "토목", "공사", "시공"],
    "manufacturing": ["제조", "생산", "공장", "가공"],
    "shipbuilding":  ["조선", "선박", "해양플랜트"],
    "service":       ["서비스", "유통", "판매", "음식"],
    "chemical":      ["화학", "석유", "정유", "가스"],
    "mining":        ["광업", "채굴", "광산"],
}

CATEGORY_INDUSTRY_MAP = {
    "건설업": "construction",
    "제조업": "manufacturing",
    "조선업": "shipbuilding",
    "서비스업": "service",
    "기타산업": "other",
}


def classify_industry(category: str, title: str, text: str) -> str:
    cat_base = (category or "").split("_")[0]
    if cat_base in CATEGORY_INDUSTRY_MAP:
        return CATEGORY_INDUSTRY_MAP[cat_base]
    combined = (title or "") + " " + (text or "")[:500]
    for ind, kws in INDUSTRY_MAP.items():
        if any(kw in combined for kw in kws):
            return ind
    return "other"


# ── 문서유형 분류 ─────────────────────────────────────────────────────────────

DOC_TYPE_RULES = [
    ("checklist",  ["체크리스트", "점검표", "확인표", "check list"]),
    ("casebook",   ["재해사례", "사고사례", "중대재해", "사망사고"]),
    ("education",  ["교육", "교안", "OPS", "강의", "훈련"]),
    ("manual",     ["매뉴얼", "지침서", "업무절차", "작업절차"]),
    ("guide",      ["기술지침", "KOSHA GUIDE", "안전지침", "가이드"]),
    ("regulation", ["법령", "고시", "기준", "규정", "규칙"]),
    ("form",       ["서식", "양식", "신청서", "보고서"]),
    ("poster",     ["포스터", "안내", "홍보", "OPL"]),
]


def classify_doc_type(title: str, category: str, text: str) -> str:
    combined = (title or "") + " " + (category or "") + " " + (text or "")[:500]
    for dtype, kws in DOC_TYPE_RULES:
        if any(kw.lower() in combined.lower() for kw in kws):
            return dtype
    return "unknown"


# ── 안전 도메인 분류 ──────────────────────────────────────────────────────────

DOMAIN_RULES = [
    ("fall",           ["추락", "떨어짐", "개구부", "안전난간", "비계", "작업발판", "고소"]),
    ("collapse",       ["붕괴", "토사", "흙막이", "굴착", "동바리", "가설"]),
    ("electric",       ["감전", "전기", "활선", "누전", "접지", "충전부"]),
    ("fire_explosion", ["화재", "폭발", "인화", "가연", "연소", "용접", "절단"]),
    ("confined_space", ["밀폐공간", "산소결핍", "황화수소", "질식"]),
    ("chemical",       ["화학물질", "유기용제", "MSDS", "흄", "분진", "독성"]),
    ("heavy_equipment",["지게차", "굴착기", "크레인", "고소작업대", "차량계"]),
    ("lifting",        ["양중", "인양", "달기", "슬링", "와이어", "훅"]),
    ("health",         ["직업병", "근골격계", "진폐", "소음", "진동", "온열"]),
    ("ppe",            ["보호구", "안전모", "안전대", "방진마스크", "안전화"]),
    ("emergency",      ["응급처치", "비상대응", "대피", "구조", "소화"]),
    ("inspection",     ["점검", "검사", "자체검사", "안전검사"]),
    ("falling_object", ["낙하", "비래", "투하", "자재낙하"]),
    ("entrapment",     ["끼임", "협착", "말림", "롤러"]),
]


def classify_domain(title: str, text: str) -> Optional[str]:
    combined = (title or "") + " " + (text or "")[:2000]
    hits: dict[str, int] = {}
    for domain, kws in DOMAIN_RULES:
        cnt = sum(combined.count(kw) for kw in kws)
        if cnt:
            hits[domain] = cnt
    if not hits:
        return None
    return max(hits, key=lambda d: hits[d])


# ── 태그 사전 ─────────────────────────────────────────────────────────────────

HAZARD_DICT = {
    "추락":    ["추락", "떨어짐", "개구부", "안전난간", "비계", "작업발판"],
    "낙하":    ["낙하", "비래", "투하", "자재낙하"],
    "붕괴":    ["붕괴", "토사", "흙막이", "굴착면", "동바리"],
    "협착":    ["끼임", "협착", "말림", "롤러"],
    "감전":    ["감전", "전기", "활선", "누전", "접지"],
    "화재폭발":["화재", "폭발", "용접", "절단", "인화성", "가연성"],
    "질식":    ["밀폐공간", "산소결핍", "황화수소"],
    "중독":    ["유기용제", "화학물질", "MSDS", "흄", "분진"],
    "소음진동":["소음", "진동"],
    "온열질환":["폭염", "온열", "열사병"],
}

WORK_TYPE_DICT = {
    "굴착":         ["굴착", "터파기", "굴삭"],
    "비계":         ["비계", "가설발판", "작업발판"],
    "거푸집동바리":  ["거푸집", "동바리", "갱폼"],
    "양중":         ["양중", "인양", "달기기구", "크레인작업"],
    "용접절단":     ["용접", "절단", "가스절단", "아크용접"],
    "전기":         ["전기작업", "배선", "활선작업"],
    "밀폐공간":     ["밀폐공간", "맨홀", "탱크내부"],
    "화학물질취급": ["화학물질", "유해물질취급", "MSDS"],
    "해체":         ["해체", "철거", "분해"],
    "터널":         ["터널", "갱도", "NATM"],
    "교량":         ["교량", "다리", "교각"],
    "고소작업":     ["고소작업", "지붕작업", "고층"],
}

EQUIPMENT_DICT = {
    "지게차":     ["지게차", "포크리프트"],
    "굴착기":     ["굴착기", "굴삭기", "백호"],
    "불도저":     ["불도저", "도저"],
    "이동식크레인":["이동식크레인", "트럭크레인", "이동크레인"],
    "타워크레인":  ["타워크레인"],
    "고소작업대":  ["고소작업대", "스카이", "버킷"],
    "항타기":     ["항타기", "말뚝"],
    "리프트":     ["리프트", "건설용리프트"],
    "곤돌라":     ["곤돌라"],
    "압축기":     ["압축기", "에어컴프레서"],
    "발전기":     ["발전기"],
    "용접기":     ["용접기", "용접장비"],
}


def extract_tags(title: str, text: str, tag_dict: dict) -> list[str]:
    combined = (title or "") + " " + (text or "")[:3000]
    return [tag for tag, kws in tag_dict.items() if any(kw in combined for kw in kws)]


# ── 전체 분류 ─────────────────────────────────────────────────────────────────

def classify_one(row: dict) -> dict:
    title   = row.get("title") or ""
    keyword = row.get("keyword") or ""
    category = row.get("category") or ""
    text    = row.get("raw_text") or ""

    search_text = f"{title} {keyword} {text}"

    guide_code, guide_group, guide_conf = extract_guide_code(text, title)
    guide_group_name = GUIDE_GROUP_NAMES.get(guide_group, "UNKNOWN") if guide_group else "UNKNOWN"

    industry = classify_industry(category, title, text)
    doc_type = classify_doc_type(title, category, text)
    domain   = classify_domain(title, search_text)

    hazard_tags    = extract_tags(title, search_text, HAZARD_DICT)
    work_type_tags = extract_tags(title, search_text, WORK_TYPE_DICT)
    equipment_tags = extract_tags(title, search_text, EQUIPMENT_DICT)

    rule_hits: dict = {}
    confidence = guide_conf

    if guide_code:
        rule_hits["guide_regex"] = guide_code
        confidence = max(confidence, 0.90)
    if hazard_tags:
        rule_hits["hazard_kw"] = hazard_tags
        confidence = max(confidence, 0.70)
    if work_type_tags:
        rule_hits["work_kw"] = work_type_tags
        confidence = max(confidence, 0.65)
    if equipment_tags:
        rule_hits["equip_kw"] = equipment_tags
        confidence = max(confidence, 0.65)
    if domain:
        rule_hits["domain_kw"] = domain
        confidence = max(confidence, 0.60)

    if not guide_code and not hazard_tags and not work_type_tags and not equipment_tags:
        confidence = 0.30

    return {
        "material_id":          row["material_id"],
        "file_id":              row["file_id"],
        "source_type":          "KOSHA",
        "primary_industry":     industry,
        "kosha_guide_code":     guide_code,
        "kosha_guide_group":    guide_group,
        "kosha_guide_group_name": guide_group_name,
        "safety_domain":        domain,
        "document_type":        doc_type,
        "hazard_tags":          json.dumps(hazard_tags, ensure_ascii=False),
        "work_type_tags":       json.dumps(work_type_tags, ensure_ascii=False),
        "equipment_tags":       json.dumps(equipment_tags, ensure_ascii=False),
        "confidence":           round(confidence, 4),
        "rule_hits":            json.dumps(rule_hits, ensure_ascii=False),
        "classifier_version":   CLASSIFIER_VERSION,
    }


# ── DB 작업 ───────────────────────────────────────────────────────────────────

FETCH_SQL = """
SELECT
    f.id          AS file_id,
    f.material_id,
    f.raw_text,
    m.title,
    m.keyword,
    m.category
FROM kosha_material_files f
JOIN kosha_materials m ON f.material_id = m.id
WHERE f.parse_status = 'success'
ORDER BY f.id
"""

UPSERT_SQL = """
INSERT INTO kosha_material_classifications
    (material_id, file_id, source_type, primary_industry,
     kosha_guide_code, kosha_guide_group, kosha_guide_group_name,
     safety_domain, document_type,
     hazard_tags, work_type_tags, equipment_tags,
     confidence, rule_hits, classified_at, classifier_version)
VALUES
    (%(material_id)s, %(file_id)s, %(source_type)s, %(primary_industry)s,
     %(kosha_guide_code)s, %(kosha_guide_group)s, %(kosha_guide_group_name)s,
     %(safety_domain)s, %(document_type)s,
     %(hazard_tags)s::jsonb, %(work_type_tags)s::jsonb, %(equipment_tags)s::jsonb,
     %(confidence)s, %(rule_hits)s::jsonb, NOW(), %(classifier_version)s)
ON CONFLICT (file_id) DO UPDATE SET
    source_type          = EXCLUDED.source_type,
    primary_industry     = EXCLUDED.primary_industry,
    kosha_guide_code     = EXCLUDED.kosha_guide_code,
    kosha_guide_group    = EXCLUDED.kosha_guide_group,
    kosha_guide_group_name = EXCLUDED.kosha_guide_group_name,
    safety_domain        = EXCLUDED.safety_domain,
    document_type        = EXCLUDED.document_type,
    hazard_tags          = EXCLUDED.hazard_tags,
    work_type_tags       = EXCLUDED.work_type_tags,
    equipment_tags       = EXCLUDED.equipment_tags,
    confidence           = EXCLUDED.confidence,
    rule_hits            = EXCLUDED.rule_hits,
    classified_at        = NOW(),
    classifier_version   = EXCLUDED.classifier_version
"""


def run_dry(rows: list[dict]) -> None:
    print(f"\n[DRY-RUN] 대상 {len(rows)}건 샘플 10건 미리보기:\n")
    for row in rows[:10]:
        result = classify_one(row)
        print(
            f"  file_id={result['file_id']}  "
            f"guide={result['kosha_guide_code'] or 'NONE':15s}  "
            f"domain={result['safety_domain'] or '-':18s}  "
            f"doc={result['document_type']:10s}  "
            f"conf={result['confidence']:.2f}  "
            f"hazard={result['hazard_tags']}"
        )
    print(f"\n→ 실제 적용 시: --apply 옵션 사용")


def run_apply(rows: list[dict], limit: Optional[int] = None) -> dict:
    target = rows[:limit] if limit else rows
    total = len(target)
    ok = err = 0
    guide_found = 0
    unknown = 0

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            for row in target:
                result = classify_one(row)
                if result["kosha_guide_code"]:
                    guide_found += 1
                if (not result["kosha_guide_code"]
                        and not json.loads(result["hazard_tags"])
                        and not json.loads(result["work_type_tags"])):
                    unknown += 1
                try:
                    cur.execute(UPSERT_SQL, result)
                    ok += 1
                except Exception as e:
                    err += 1
                    print(f"  [ERR] file_id={result['file_id']}: {e}")
                    conn.rollback()
                    continue
            conn.commit()
    finally:
        conn.close()

    print(f"\n[APPLY 완료]")
    print(f"  대상: {total:,}건")
    print(f"  성공: {ok:,}건  실패: {err:,}건")
    print(f"  KOSHA Guide 번호 추출: {guide_found:,}건")
    print(f"  완전 UNKNOWN(태그 없음): {unknown:,}건")
    return {"total": total, "ok": ok, "err": err, "guide_found": guide_found, "unknown": unknown}


def run_report(output_path: str = "docs/reports/kosha_classification_report.md") -> None:
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

            cur.execute("SELECT COUNT(*) AS cnt FROM kosha_material_classifications")
            total_classified = cur.fetchone()["cnt"]

            cur.execute("""
                SELECT COUNT(*) AS cnt FROM kosha_material_classifications
                WHERE kosha_guide_code IS NULL
                  AND hazard_tags = '[]'::jsonb
                  AND work_type_tags = '[]'::jsonb
            """)
            unknown_cnt = cur.fetchone()["cnt"]

            cur.execute("""
                SELECT COUNT(*) AS cnt FROM kosha_material_classifications
                WHERE kosha_guide_code IS NOT NULL
            """)
            guide_cnt = cur.fetchone()["cnt"]

            cur.execute("""
                SELECT
                  CASE
                    WHEN confidence >= 0.90 THEN '0.90+'
                    WHEN confidence >= 0.70 THEN '0.70-0.89'
                    WHEN confidence >= 0.50 THEN '0.50-0.69'
                    ELSE '<0.50'
                  END AS band,
                  COUNT(*) AS cnt
                FROM kosha_material_classifications
                GROUP BY band ORDER BY band DESC
            """)
            conf_rows = cur.fetchall()

            cur.execute("""
                SELECT primary_industry, COUNT(*) AS cnt
                FROM kosha_material_classifications
                GROUP BY primary_industry ORDER BY cnt DESC
            """)
            industry_rows = cur.fetchall()

            cur.execute("""
                SELECT COALESCE(kosha_guide_group, 'UNKNOWN') AS grp,
                       MAX(kosha_guide_group_name) AS grp_name,
                       COUNT(*) AS cnt
                FROM kosha_material_classifications
                GROUP BY grp ORDER BY cnt DESC
            """)
            group_rows = cur.fetchall()

            cur.execute("""
                SELECT jsonb_array_elements_text(hazard_tags) AS tag, COUNT(*) AS cnt
                FROM kosha_material_classifications
                WHERE hazard_tags != '[]'::jsonb
                GROUP BY tag ORDER BY cnt DESC LIMIT 20
            """)
            hazard_rows = cur.fetchall()

            cur.execute("""
                SELECT jsonb_array_elements_text(work_type_tags) AS tag, COUNT(*) AS cnt
                FROM kosha_material_classifications
                WHERE work_type_tags != '[]'::jsonb
                GROUP BY tag ORDER BY cnt DESC LIMIT 20
            """)
            work_rows = cur.fetchall()

            cur.execute("""
                SELECT jsonb_array_elements_text(equipment_tags) AS tag, COUNT(*) AS cnt
                FROM kosha_material_classifications
                WHERE equipment_tags != '[]'::jsonb
                GROUP BY tag ORDER BY cnt DESC LIMIT 20
            """)
            equip_rows = cur.fetchall()

            cur.execute("""
                SELECT COUNT(*) AS cnt FROM kosha_material_classifications
                WHERE primary_industry = 'construction'
            """)
            construction_cnt = cur.fetchone()["cnt"]

            cur.execute("""
                SELECT COUNT(*) AS cnt FROM kosha_material_classifications
                WHERE primary_industry = 'construction'
                  AND hazard_tags != '[]'::jsonb
            """)
            construction_hazard_cnt = cur.fetchone()["cnt"]

    finally:
        conn.close()

    kst_now = datetime.now().strftime("%Y-%m-%d %H:%M KST")
    lines = [
        f"# KOSHA 자료 세부 분류 품질 리포트",
        f"",
        f"생성일시: {kst_now}  |  분류기버전: {CLASSIFIER_VERSION}",
        f"",
        f"## 요약",
        f"",
        f"| 항목 | 건수 |",
        f"|------|------|",
        f"| 분류 대상 (parse_status=success) | 2,047 |",
        f"| 분류 완료 | {total_classified:,} |",
        f"| KOSHA Guide 번호 추출 | {guide_cnt:,} |",
        f"| 완전 UNKNOWN (태그 없음) | {unknown_cnt:,} |",
        f"| 건설업 관련 | {construction_cnt:,} |",
        f"| 건설업 중 위험요인 태그 있음 | {construction_hazard_cnt:,} |",
        f"",
        f"## Confidence 구간별",
        f"",
        f"| 구간 | 건수 |",
        f"|------|------|",
    ]
    for r in conf_rows:
        lines.append(f"| {r['band']} | {r['cnt']:,} |")

    lines += [
        f"",
        f"## 업종별 분류",
        f"",
        f"| 업종 | 건수 |",
        f"|------|------|",
    ]
    for r in industry_rows:
        lines.append(f"| {r['primary_industry'] or '-'} | {r['cnt']:,} |")

    lines += [
        f"",
        f"## KOSHA Guide 그룹별",
        f"",
        f"| 그룹 | 그룹명 | 건수 |",
        f"|------|--------|------|",
    ]
    for r in group_rows:
        lines.append(f"| {r['grp']} | {r['grp_name'] or '-'} | {r['cnt']:,} |")

    lines += [
        f"",
        f"## 위험요인 태그 TOP 20",
        f"",
        f"| 태그 | 건수 |",
        f"|------|------|",
    ]
    for r in hazard_rows:
        lines.append(f"| {r['tag']} | {r['cnt']:,} |")

    lines += [
        f"",
        f"## 작업유형 태그 TOP 20",
        f"",
        f"| 태그 | 건수 |",
        f"|------|------|",
    ]
    for r in work_rows:
        lines.append(f"| {r['tag']} | {r['cnt']:,} |")

    lines += [
        f"",
        f"## 장비 태그 TOP 20",
        f"",
        f"| 태그 | 건수 |",
        f"|------|------|",
    ]
    for r in equip_rows:
        lines.append(f"| {r['tag']} | {r['cnt']:,} |")

    lines += [
        f"",
        f"## Backlog",
        f"",
        f"| 유형 | 건수 | 비고 |",
        f"|------|------|------|",
        f"| image_pdf | 2,434 | OCR 후보, 이번 단계 제외 |",
        f"| failed_unzip | 111 | zip 압축 해제 실패 |",
        f"| hwp pending | 9 | HWP 파서 미처리 |",
        f"| text_pdf failed | 64 | PDF 텍스트 추출 실패 |",
        f"",
        f"## 다음 단계",
        f"",
        f"- [ ] `kosha_context_index` 생성 — 위험성평가 엔진 연결용 검색 인덱스",
        f"- [ ] image_pdf 2,434건 OCR 처리",
        f"- [ ] confidence < 0.50 구간 재검토",
    ]

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[REPORT] {out} 생성 완료")
    print(f"  분류 완료: {total_classified:,}건  |  UNKNOWN: {unknown_cnt:,}건  |  Guide 추출: {guide_cnt:,}건")


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="KOSHA 자료 세부 분류기")
    ap.add_argument("--dry-run", action="store_true", help="샘플 10건 미리보기만")
    ap.add_argument("--apply",   action="store_true", help="전체 분류 후 DB upsert")
    ap.add_argument("--report",  action="store_true", help="분류 결과 리포트 생성")
    ap.add_argument("--limit",   type=int, default=None, help="처리 건수 제한")
    ap.add_argument("--output",  default="docs/reports/kosha_classification_report.md")
    args = ap.parse_args()

    if not (args.dry_run or args.apply or args.report):
        ap.print_help()
        sys.exit(0)

    if args.dry_run or args.apply:
        print("[DB] 대상 자료 로드 중...")
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(FETCH_SQL)
                rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
        print(f"  → {len(rows):,}건 로드")

    if args.dry_run:
        run_dry(rows)

    if args.apply:
        run_apply(rows, limit=args.limit)

    if args.report:
        run_report(output_path=args.output)


if __name__ == "__main__":
    main()

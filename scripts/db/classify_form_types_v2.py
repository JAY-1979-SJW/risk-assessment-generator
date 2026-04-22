"""
서식 form_type 분류기 v2 — other_form 세분화 버전.

기존 classify_form_types.py 의 규칙을 확장하여 other_form 비율을 줄인다.

확장 분류 (우선순위 순, 첫 매칭 승리):
    risk_assessment       : 위험성평가 관련
    tbm                   : TBM / 작업전 안전회의 등
    contract_form         : 계약·협정·약정
    application_form      : 신청·신고·등록
    notification_form     : 통보·공고·고시·알림
    education_material    : 교육자료·교안·교재·과정
    education_log         : 교육일지·이수증·교육기록
    safety_checklist      : 자율점검표·자가점검·셀프체크
    inspection_checklist  : 점검표·체크리스트 (자율 제외)
    report_form           : 보고서·결과서·통계
    safety_plan           : 안전보건계획·비상대응계획·비상조치계획
    work_plan             : 작업계획서·시공계획·실시계획
    technical_standard    : 기술지침·기술지원규정·기술표준·기준
    guideline             : 작업지침·안전지침·가이드라인·안내서·해설서·매뉴얼·길잡이·지침
    inspection_form       : 점검·감독·진단·조사 (체크리스트가 아닌 점검서)
    plan_form             : 계획서 (잔여)
    other_form            : 그 외

대상
    source_type IN ('kosha_form', 'moel_form', 'licbyl')

저장
    documents.metadata->>'form_type' 에 분류코드 저장 (UPDATE)

dry-run / limit 지원.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
except (NameError, IndexError):
    PROJECT_ROOT = Path.cwd()


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    for env in (PROJECT_ROOT / ".env", PROJECT_ROOT / "infra" / ".env"):
        if env.exists():
            load_dotenv(env, override=False)


def get_db_connection():
    import psycopg2  # type: ignore
    _load_dotenv()
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    port = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"
    database = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    if not (host and database and user):
        raise RuntimeError("DB 접속 정보 누락")
    return psycopg2.connect(
        host=host, port=int(port), dbname=database, user=user, password=password or ""
    )


FORM_SOURCES = ("kosha_form", "moel_form", "licbyl")


# ---------------------------------------------------------------------------
# 규칙 (우선순위 순, 첫 매칭 승리)
# ---------------------------------------------------------------------------

RULES: list[tuple[str, list[str]]] = [
    # --- 가장 특정적인 것 먼저 ---
    ("risk_assessment",
        ["위험성평가", "위험성 평가", "RA(", "유해·위험요인", "유해위험요인"]),
    ("tbm",
        ["TBM", "Tool Box", "작업 전 안전", "작업전 안전", "일일안전", "조회"]),
    ("contract_form",
        ["계약서", "업무계약", "협정서", "협정", "약정서", "약정"]),
    ("application_form",
        ["신청서", "신고서", "등록신청", "변경신청", "지정신청",
         "허가신청", "승인신청", "인가신청", " 신청", " 신고"]),
    # education: material 먼저 (더 구체적), log 는 그 다음
    ("education_material",
        ["교육자료", "교안", "교재", "교육과정", "훈련교재",
         "학습자료", "교육용", "교육 자료"]),
    ("education_log",
        ["교육일지", "교육이수증", "교육 이수", "교육기록",
         "교육수료", "교육실적", "이수증"]),
    # checklist 계열: safety(자율) 우선, 그 다음 inspection
    ("safety_checklist",
        ["자율점검표", "자율 점검표", "자율안전점검표",
         "자가점검표", "자가 점검", "self-check", "셀프체크",
         "자율진단표", "자율점검"]),
    ("inspection_checklist",
        ["점검표", "점검 체크리스트", "안전점검표", "체크리스트",
         "점검목록", "점검 리스트"]),
    ("report_form",
        ["보고서", "발생현황", "결과서", "결과보고", "조사결과",
         "확인결과", "평가결과서", "평가 결과", "통계", "재해현황",
         "사고조사", "재해분석"]),
    # 기술지침/지원규정/표준 — safety_plan/guideline 보다 먼저
    # ("비상조치계획 기술지원규정" → form 자체는 technical_standard)
    ("technical_standard",
        ["기술지침", "기술 지침", "기술지원규정",
         "기술표준", "설치기준", "성능기준",
         "기술규정", "표준작업"]),
    ("safety_plan",
        ["안전보건계획", "안전보건 계획", "안전보건관리계획",
         "비상대응계획", "비상조치계획", "재난대응",
         "안전보건관리계획서"]),
    ("work_plan",
        ["작업계획서", "작업계획", "시공계획서", "시공계획",
         "실시계획서", "실시계획", "공사계획"]),
    # 지침·가이드 (technical_standard 로 잡히지 않은 것)
    ("guideline",
        ["작업지침", "작업 지침", "안전지침", "안전보건작업지침",
         "가이드라인", "가이드 ", " 가이드",
         "안내서", "해설서", "해설집",
         "매뉴얼", "길잡이",
         "지침서", "지침"]),
    # notification — 콘텐츠 타입 매칭 뒤로 이동
    ("notification_form",
        ["통보서", " 통보", "공고", "고시", "알림", "공시", "공포", "공지"]),
    # 잔여 inspection / plan
    ("inspection_form",
        ["점검", "감독", "진단서", "안전진단", "조사서"]),
    ("plan_form",
        ["계획서", " 계획"]),
]

DEFAULT_FORM_TYPE = "other_form"


def classify(title: str, body: str = "") -> str:
    hay = f" {title} "  # 공백 padding → " 신청" 같은 경계 매칭 허용
    for code, keywords in RULES:
        for kw in keywords:
            if kw in hay:
                return code
    # 2차 — body 앞 400자에서 확인 (title 이 애매한 경우)
    body_head = (body or "")[:400]
    hay2 = f" {title} {body_head} "
    for code, keywords in RULES:
        for kw in keywords:
            if kw in hay2:
                return code
    return DEFAULT_FORM_TYPE


def run(conn, dry_run: bool, limit: int) -> dict:
    stats: dict[str, int] = {"scanned": 0, "updated": 0, "changed": 0}
    distribution: dict[str, int] = {}
    before_dist: dict[str, int] = {}
    transitions: dict[tuple[str, str], int] = {}

    with conn.cursor() as rcur, conn.cursor() as wcur:
        q = f"""
            SELECT id, title, body_text, metadata->>'form_type' AS prev_ft
              FROM documents
             WHERE source_type IN ({','.join(['%s'] * len(FORM_SOURCES))})
             ORDER BY id
        """
        params: list = list(FORM_SOURCES)
        if limit > 0:
            q += " LIMIT %s"
            params.append(limit)
        rcur.execute(q, params)
        for doc_id, title, body, prev_ft in rcur.fetchall():
            stats["scanned"] += 1
            prev = prev_ft or "NULL"
            before_dist[prev] = before_dist.get(prev, 0) + 1

            ft = classify(title or "", body or "")
            distribution[ft] = distribution.get(ft, 0) + 1

            if ft != prev:
                stats["changed"] += 1
                transitions[(prev, ft)] = transitions.get((prev, ft), 0) + 1

            wcur.execute(
                """
                UPDATE documents
                   SET metadata   = COALESCE(metadata, '{}'::jsonb)
                                    || jsonb_build_object('form_type', %s::text),
                       updated_at = now()
                 WHERE id = %s
                """,
                (ft, doc_id),
            )
            if wcur.rowcount > 0:
                stats["updated"] += wcur.rowcount

    if dry_run:
        conn.rollback()
    else:
        conn.commit()

    stats["distribution"] = distribution
    stats["before_distribution"] = before_dist
    stats["transitions"] = transitions
    return stats


def _print_top_transitions(transitions: dict[tuple[str, str], int], top: int = 15) -> None:
    items = sorted(transitions.items(), key=lambda kv: -kv[1])[:top]
    print(f"[top {top} transitions]")
    for (src, dst), cnt in items:
        print(f"  {src:<22} -> {dst:<22}: {cnt:,}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"[FAIL] DB 접속 실패: {exc!r}", file=sys.stderr)
        return 3
    try:
        stats = run(conn, args.dry_run, args.limit)
    finally:
        conn.close()

    print("[RESULT]")
    print(f"  scanned : {stats['scanned']:,}")
    print(f"  updated : {stats['updated']:,}")
    print(f"  changed : {stats['changed']:,}")

    print("[before]")
    for ft in sorted(stats["before_distribution"], key=lambda k: -stats["before_distribution"][k]):
        print(f"  {ft:<22}: {stats['before_distribution'][ft]:,}")
    print("[after]")
    for ft in sorted(stats["distribution"], key=lambda k: -stats["distribution"][k]):
        print(f"  {ft:<22}: {stats['distribution'][ft]:,}")
    _print_top_transitions(stats["transitions"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

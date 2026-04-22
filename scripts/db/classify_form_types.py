"""
서식 form_type 분류기.

대상
    source_type IN ('kosha_form', 'moel_form', 'licbyl')

저장
    documents.metadata->>'form_type' 에 분류코드 저장
    (documents.metadata 는 JSONB 컬럼, 사전에 추가되어 있어야 함)

분류 (우선순위 순)
    risk_assessment   : 위험성평가 관련
    tbm               : TBM / 작업 전 안전회의 등
    checklist         : 체크리스트 / 점검표 / 자율점검
    education_log     : 교육일지/이수/기록
    inspection_form   : 점검·감독·진단·조사 '결과서'가 아닌 것 제외
    application_form  : 신청·신고·등록
    report_form       : 보고·발생현황·결과서·통계
    contract_form     : 계약·협정·약정
    plan_form         : 계획·대책·매뉴얼·길잡이
    other_form        : 그 외 (기술지침/해설집 등 가이드류)

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
    # risk_assessment
    ("risk_assessment", ["위험성평가", "위험성 평가", "RA(", "유해·위험요인"]),
    # tbm
    ("tbm", ["TBM", "Tool Box", "작업 전 안전", "작업전 안전", "일일안전", "조회"]),
    # checklist
    ("checklist", ["체크리스트", "점검표", "자율점검", "자가점검", "self-check", "셀프체크"]),
    # education_log
    ("education_log", ["교육일지", "교육이수", "교육 이수", "교육기록", "교육수료", "교육실적"]),
    # application_form (신청/신고)  — inspection·report 보다 우선
    ("application_form", ["신청서", "신청", "신고서", "신고", "등록신청", "변경신청", "지정신청"]),
    # contract_form
    ("contract_form", ["계약서", "업무계약", "협정서", "협정", "약정서", "약정"]),
    # plan_form
    ("plan_form", ["계획서", "비상대응계획", "재난대응", "안전보건관리계획", "안전보건계획",
                    "매뉴얼", "길잡이", "실시계획"]),
    # report_form
    ("report_form", ["보고서", "발생현황", "결과서", "결과보고", "조사결과", "확인결과",
                      "평가결과서", "평가 결과", "통계", "재해현황", "사고조사"]),
    # inspection_form
    ("inspection_form", ["점검", "감독", "진단서", "진단 ", "조사서", "안전진단"]),
    # education_log 부가 (training_plan 류는 plan)
]

DEFAULT_FORM_TYPE = "other_form"


def classify(title: str, body: str = "") -> str:
    # title 위주 (너무 긴 body 는 소음)
    hay = f"{title}  "  # title 로만 우선 판정
    for code, keywords in RULES:
        for kw in keywords:
            if kw in hay:
                return code
    # 2차 — body 앞 400자에서 확인 (title 이 애매한 경우 많음)
    body_head = (body or "")[:400]
    hay2 = title + "  " + body_head
    for code, keywords in RULES:
        for kw in keywords:
            if kw in hay2:
                return code
    return DEFAULT_FORM_TYPE


def run(conn, dry_run: bool, limit: int) -> dict:
    stats: dict[str, int] = {"scanned": 0, "updated": 0}
    distribution: dict[str, int] = {}
    with conn.cursor() as rcur, conn.cursor() as wcur:
        q = f"""
            SELECT id, title, body_text
              FROM documents
             WHERE source_type IN ({','.join(['%s'] * len(FORM_SOURCES))})
             ORDER BY id
        """
        params: list = list(FORM_SOURCES)
        if limit > 0:
            q += " LIMIT %s"
            params.append(limit)
        rcur.execute(q, params)
        for doc_id, title, body in rcur.fetchall():
            stats["scanned"] += 1
            ft = classify(title or "", body or "")
            distribution[ft] = distribution.get(ft, 0) + 1
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
    return stats


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
    print("[distribution]")
    for ft in sorted(stats["distribution"], key=lambda k: -stats["distribution"][k]):
        print(f"  {ft:<18}: {stats['distribution'][ft]:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

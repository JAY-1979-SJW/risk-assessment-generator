"""
고용노동부 법령해석(moelCgmExpc) 전체 수집 → SQLite 저장
  - 대상: law.go.kr DRF  target=moelCgmExpc  query=*  (전체 ~9,500건)
  - 저장: data/law_db/moel_expc.db  (SQLite)
  - 재개: 이미 수집된 법령해석일련번호 skip
  - 환경변수: LAW_GO_KR_OC (law.go.kr 개발계정 OC 키)
"""
import sqlite3
import time
from pathlib import Path

from ._base import get_logger, get_oc_key, drf_request, now_iso, ROOT

log = get_logger("moel_expc_full")

DB_PATH   = ROOT / "data" / "law_db" / "moel_expc.db"
TARGET    = "moelCgmExpc"
QUERY     = "*"
DISPLAY   = 100   # 페이지당 최대 100건
DELAY     = 0.8   # 요청 간격(초)


# ─── DB 초기화 ────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS moel_expc (
    serial_no       TEXT PRIMARY KEY,   -- 법령해석일련번호
    case_name       TEXT,               -- 안건명
    case_no         TEXT,               -- 안건번호
    interpret_org   TEXT,               -- 해석기관명
    interpret_code  TEXT,               -- 해석기관코드
    inquire_org     TEXT,               -- 질의기관명
    inquire_code    TEXT,               -- 질의기관코드
    interpreted_at  TEXT,               -- 해석일자 (YYYYMMDD)
    detail_url      TEXT,               -- 법령해석상세링크
    data_std_dt     TEXT,               -- 데이터기준일시
    collected_at    TEXT                -- 수집일시 (UTC ISO)
);
CREATE INDEX IF NOT EXISTS idx_interpreted_at ON moel_expc (interpreted_at);
CREATE INDEX IF NOT EXISTS idx_interpret_org  ON moel_expc (interpret_org);
"""


def _init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    conn.commit()


def _load_existing_serials(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT serial_no FROM moel_expc").fetchall()
    return {r[0] for r in rows}


def _insert_batch(conn: sqlite3.Connection, rows: list[dict]) -> int:
    sql = """
        INSERT OR IGNORE INTO moel_expc
            (serial_no, case_name, case_no, interpret_org, interpret_code,
             inquire_org, inquire_code, interpreted_at, detail_url,
             data_std_dt, collected_at)
        VALUES
            (:serial_no, :case_name, :case_no, :interpret_org, :interpret_code,
             :inquire_org, :inquire_code, :interpreted_at, :detail_url,
             :data_std_dt, :collected_at)
    """
    now = now_iso()
    params = [
        {
            "serial_no":     r.get("법령해석일련번호", ""),
            "case_name":     r.get("안건명", ""),
            "case_no":       r.get("안건번호", ""),
            "interpret_org": r.get("해석기관명", ""),
            "interpret_code":r.get("해석기관코드", ""),
            "inquire_org":   r.get("질의기관명", ""),
            "inquire_code":  r.get("질의기관코드", ""),
            "interpreted_at":r.get("해석일자", ""),
            "detail_url":    r.get("법령해석상세링크", ""),
            "data_std_dt":   r.get("데이터기준일시", ""),
            "collected_at":  now,
        }
        for r in rows
        if r.get("법령해석일련번호")   # serial 없는 행 제외
    ]
    if not params:
        return 0
    conn.executemany(sql, params)
    conn.commit()
    return len(params)


# ─── 수집 ─────────────────────────────────────────────────────────────────────

def run() -> bool:
    oc_key = get_oc_key()
    if not oc_key:
        log.error("LAW_GO_KR_OC 환경변수가 설정되지 않았습니다. .env에 추가 후 재실행하세요.")
        return False

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    _init_db(conn)

    existing = _load_existing_serials(conn)
    log.info(f"=== 고용노동부 법령해석 전체 수집 시작 (기수집: {len(existing)}건) ===")

    total_saved = 0
    total_skip  = 0
    page        = 1

    while True:
        result = drf_request(TARGET, QUERY, page=page, display=DISPLAY, oc_key=oc_key)
        code = result.get("result_code", "00")

        if code in ("01", "02", "09", "99"):
            log.error(f"API 오류 [{code}]: {result.get('result_msg')} — 중단")
            conn.close()
            return False

        if code == "03" or not result.get("items"):
            log.info(f"p{page}: 데이터 없음 — 수집 완료")
            break

        items      = result["items"]
        total_cnt  = result.get("total_count", 0)

        # 이미 수집된 건 필터
        new_items = [i for i in items if i.get("법령해석일련번호") not in existing]
        skip_cnt  = len(items) - len(new_items)
        total_skip += skip_cnt

        saved = _insert_batch(conn, new_items)
        total_saved += saved
        existing.update(i.get("법령해석일련번호", "") for i in new_items)

        log.info(
            f"p{page}: +{saved}건 저장 / {skip_cnt}건 skip "
            f"/ 누적 {len(existing)}/{total_cnt}건"
        )

        if len(existing) >= total_cnt:
            log.info("전체 수집 완료")
            break

        page += 1
        time.sleep(DELAY)

    conn.close()
    log.info(f"=== 완료: 신규 {total_saved}건 저장 / {total_skip}건 skip — {DB_PATH} ===")
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)

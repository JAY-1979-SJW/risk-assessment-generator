# -*- coding: utf-8 -*-
"""
KOSHA DB 연결 모듈
SSH 터널(포트 5435)이 열려 있어야 함:
  ssh -i ~/.ssh/haehan-ai.pem -L 5435:localhost:5432 ubuntu@1.201.177.67 -N -f
"""

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / '.env')

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', '5435'))
DB_NAME = os.getenv('DB_NAME', 'common_data')
DB_USER = os.getenv('DB_USER', 'common_admin')
DB_PASS = os.getenv('DB_PASS', '')


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS,
        connect_timeout=5
    )


def fetch_chunks_for_work(trade_type: str, work_type: str = None, limit: int = 30) -> list[dict]:
    """
    업종+공종 키워드로 관련 KOSHA 청크 조회.
    반환: [{"raw_text": ..., "trade_type": ..., "work_type": ..., "hazard_type": ...}]
    """
    params = [f"%{trade_type}%", f"%{trade_type}%"]
    work_filter = ""
    if work_type:
        work_filter = "AND (kct.work_type ILIKE %s OR kmc.work_type ILIKE %s)"
        params += [f"%{work_type}%", f"%{work_type}%"]
    params.append(limit)

    sql = f"""
        SELECT kmc.raw_text,
               kct.trade_type,
               kct.work_type,
               kct.hazard_type,
               kct.law_ref,
               kct.confidence
        FROM kosha_material_chunks kmc
        JOIN kosha_chunk_tags kct ON kct.chunk_id = kmc.id
        WHERE (kct.trade_type ILIKE %s OR kmc.work_type ILIKE %s)
          {work_filter}
          AND kmc.raw_text IS NOT NULL
          AND LENGTH(kmc.raw_text) > 100
        ORDER BY kct.confidence DESC NULLS LAST,
                 kmc.id DESC
        LIMIT %s
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

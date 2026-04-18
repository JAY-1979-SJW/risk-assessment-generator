import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="KRAS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")


def _db_stats():
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM kosha_materials")
        materials = cur.fetchone()[0]
        cur.execute("SELECT parse_status, COUNT(*) FROM kosha_material_files GROUP BY parse_status")
        files = dict(cur.fetchall())
        cur.execute("SELECT COUNT(*) FROM kosha_material_chunks")
        chunks = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM kosha_chunk_tags")
        tags = cur.fetchone()[0]
        return {"materials": materials, "files": files, "chunks": chunks, "tags": tags}
    finally:
        conn.close()


@app.get("/health")
def health():
    result = {"status": "ok", "api": "up"}
    if not DATABASE_URL:
        result["db"] = "not_configured"
        return result
    try:
        result["db"] = "connected"
        result["kosha"] = _db_stats()
    except Exception as e:
        result["status"] = "degraded"
        result["db"] = "error"
        result["db_error"] = str(e)
    return result

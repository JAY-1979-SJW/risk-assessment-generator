from fastapi import FastAPI

app = FastAPI(title="KRAS API")

@app.get("/health")
def health():
    return {"status": "ok"}

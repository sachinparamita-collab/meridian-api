from fastapi import FastAPI

app = FastAPI(
    title="Meridian API",
    description="Meridian - DMC Operating System for India travel",
    version="0.1.0"
)

@app.get("/v1/health")
def health():
    return {"status": "ok", "service": "meridian-api", "version": "0.1.0"}

@app.post("/v1/recommend")
def recommend(payload: dict):
    return {"status": "ok", "message": "recommend endpoint stub", "input": payload}

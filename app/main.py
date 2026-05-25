import os
import sys
import traceback
import sqlite3
import json
from datetime import date, datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Engine path setup ────────────────────────────────────────────────────────
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "engine"))
sys.path.insert(0, ENGINE_DIR)

DB_PATH         = os.path.join(ENGINE_DIR, "master_v2.db")
PORTFOLIO_PATH  = os.path.join(ENGINE_DIR, "hotel_portfolio.csv")
ACTIVITY_PATH   = os.path.join(ENGINE_DIR, "activity_details.csv")
FNB_PATH        = os.path.join(ENGINE_DIR, "fnb_details.csv")
AGENCY_PATH     = os.path.join(ENGINE_DIR, "agency_crm.xlsx")
CITY_RULES_PATH = os.path.join(ENGINE_DIR, "city_rules.csv")

# ── JSON serialiser — handles date, tuple ────────────────────────────────────
def serialise(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"Not serialisable: {type(obj)}")

# ── Load engine at startup ───────────────────────────────────────────────────
ENGINE_LOADED = False
ENGINE_ERROR  = ""

try:
    import recommendation_engine as engine
    ENGINE_LOADED = True
    print("✓ Recommendation engine loaded")
except Exception as e:
    ENGINE_ERROR = str(e)
    print(f"✗ Engine failed to load: {e}")

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="Meridian API", version="0.1.0")


class RecommendRequest(BaseModel):
    email_text: str
    source_market: str | None = None


@app.get("/v1/health")
def health():
    return {
        "status": "ok",
        "engine_loaded": ENGINE_LOADED,
        "engine_error": ENGINE_ERROR if not ENGINE_LOADED else None
    }


@app.get("/v1/debug")
def debug():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        counts = {}
        for t in tables:
            counts[t] = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        conn.close()
        return {
            "db_path": DB_PATH,
            "file_size_mb": round(os.path.getsize(DB_PATH) / 1024 / 1024, 1),
            "tables": counts
        }
    except Exception as e:
        return {"db_path": DB_PATH, "error": str(e)}


@app.post("/v1/recommend")
def recommend(request: RecommendRequest):
    if not ENGINE_LOADED:
        raise HTTPException(
            status_code=503,
            detail=f"Engine not available: {ENGINE_ERROR}"
        )
    try:
        result = engine.recommend(
            email_text      = request.email_text,
            db_path         = DB_PATH,
            portfolio_path  = PORTFOLIO_PATH,
            activity_path   = ACTIVITY_PATH,
            fnb_path        = FNB_PATH,
            agency_path     = AGENCY_PATH,
            city_rules_path = CITY_RULES_PATH,
            source_market   = request.source_market,
        )
        # Serialise via json to handle date + tuple types, then return as response
        clean = json.loads(json.dumps(result, default=serialise))
        return JSONResponse(content=clean)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
import os
import sys
import traceback
from fastapi import FastAPI, HTTPException
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
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
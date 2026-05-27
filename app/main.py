import os
import sys
import traceback
import sqlite3
import json
import time
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import psycopg2
import psycopg2.extras

# ── Engine path setup ────────────────────────────────────────────────────────
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "engine"))
sys.path.insert(0, ENGINE_DIR)

DB_PATH         = os.environ.get("DB_PATH", os.path.join(ENGINE_DIR, "master_v2.db"))
PORTFOLIO_PATH  = os.path.join(ENGINE_DIR, "hotel_portfolio.csv")
ACTIVITY_PATH   = os.path.join(ENGINE_DIR, "activity_details.csv")
FNB_PATH        = os.path.join(ENGINE_DIR, "fnb_details.csv")
AGENCY_PATH     = os.path.join(ENGINE_DIR, "agency_crm.xlsx")
CITY_RULES_PATH = os.path.join(ENGINE_DIR, "city_rules.csv")

DATABASE_URL = os.getenv("DATABASE_URL", "")
# Railway supplies postgres:// — psycopg2 requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ── JSON serialiser ───────────────────────────────────────────────────────────
def serialise(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"Not serialisable: {type(obj)}")

# ── Load engine at startup ────────────────────────────────────────────────────
ENGINE_LOADED = False
ENGINE_ERROR  = ""

try:
    import recommendation_engine as engine
    ENGINE_LOADED = True
    print("✓ Recommendation engine loaded")
except Exception as e:
    ENGINE_ERROR = str(e)
    print(f"✗ Engine failed to load: {e}")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Meridian API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# ── DB helpers ────────────────────────────────────────────────────────────────
def get_pg():
    return psycopg2.connect(DATABASE_URL)

def verify_api_key(api_key: str):
    """Returns user row if valid, raises 401 if not."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required. Pass X-API-Key header.")
    try:
        conn = get_pg()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM users WHERE api_key = %s AND active = TRUE", (api_key,))
        user = cur.fetchone()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {e}")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key.")
    return user

def log_usage(user_id: int, endpoint: str, request_preview: str, response_ms: int):
    try:
        conn = get_pg()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usage_logs (user_id, endpoint, request_preview, response_ms) VALUES (%s, %s, %s, %s)",
            (user_id, endpoint, request_preview[:200], response_ms)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠ Usage log failed: {e}")

# ── Models ────────────────────────────────────────────────────────────────────
class RecommendRequest(BaseModel):
    email_text: str
    source_market: str | None = None

# ── Endpoints ─────────────────────────────────────────────────────────────────
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
def recommend(request: RecommendRequest, api_key: str = Security(api_key_header)):
    user = verify_api_key(api_key)
    if not ENGINE_LOADED:
        raise HTTPException(status_code=503, detail=f"Engine not available: {ENGINE_ERROR}")
    t_start = time.time()
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
        response_ms = int((time.time() - t_start) * 1000)
        log_usage(user["id"], "/v1/recommend", request.email_text, response_ms)
        clean = json.loads(json.dumps(result, default=serialise))
        return JSONResponse(content=clean)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
# cache-bust 202605252036



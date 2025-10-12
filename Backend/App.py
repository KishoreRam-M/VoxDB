from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import httpx

# Gemini API Key
GEMINI_API_KEY = "AIzaSyD9lwGeVMOusHmvEizWDEC-Gcd4W7Ro7iY"

# FastAPI instance
app = FastAPI()

# CORS Config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# Dynamic MySQL Engine
# ------------------------
def Vox_Engine(conn: dict):
    """
    Create a dynamic MySQL SQLAlchemy engine from connection info.
    """
    try:
        db_url = (
            f"mysql+pymysql://{conn['user']}:{conn['password']}"
            f"@{conn['host']}:{conn['port']}/{conn['database']}"
        )
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        raise ValueError(f"Invalid connection: {e}")

# ------------------------
# Gemini AI API Call
# ------------------------
async def gemini_request(prompt: str):
    """
    Call Gemini AI to process prompt and return text response.
    """
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}

    payload = {
        "model": "gemini-2.5-pro",
        "prompt": prompt,
        "max_tokens": 1000
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.gemini.ai/v1/complete",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result.get("text", "").strip()

# ------------------------
# AI-powered SQL Query Endpoint
# ------------------------
@app.post("/query")
async def query_vox(request: Request):
    """
    Receives a prompt and database connection info.
    Generates table names using Gemini AI.
    """
    body = await request.json()
    prompt = body.get("prompt", "")
    connection_info = body.get("connection", {})

    if not prompt:
        return {"error": "Prompt is missing"}

    if not connection_info:
        return {"error": "MySQL Database Connection is missing"}

    try:
        # Create dynamic engine
        engine = Vox_Engine(connection_info)
    except Exception as e:
        return {"error": f"Engine creation failed: {str(e)}"}

    try:
        # Extract table names using AI
        table_prompt = f"Extract table names from this prompt (comma separated, no explanation): {prompt}"
        table_str = await gemini_request(table_prompt)
        tables = [t.strip() for t in table_str.split(",") if t.strip()]
    except Exception as e:
        return {"error": f"Table extraction failed: {str(e)}"}

    return {
        "message": "Engine created and tables extracted successfully",
        "tables": tables
    }

"""
=========================================================
💡 VoxDB: AI-Powered Conversational Database Engine
=========================================================
This FastAPI service allows users to interact with a MySQL
database using natural language. It leverages Google's
Gemini AI to:
    1️⃣ Interpret human language prompts.
    2️⃣ Extract table names dynamically.
    3️⃣ Generate SQL queries automatically.
    4️⃣ Execute SQL commands and return structured results.

Author : Kishore Ram M
Project: VoxDB - Talk to Your Database
=========================================================
"""

# ---------------------------------------------------------
# ✅ Import Required Libraries
# ---------------------------------------------------------
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import httpx

# ---------------------------------------------------------
# 🔑 Gemini API Configuration
# ---------------------------------------------------------

# ---------------------------------------------------------
# 🚀 Initialize FastAPI Application
# ---------------------------------------------------------
app = FastAPI(title="VoxDB - AI Database Assistant")

# ---------------------------------------------------------
# 🌍 CORS Configuration (Allow Frontend Access)
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# 🧠 Dynamic MySQL Engine Builder
# ---------------------------------------------------------
def Vox_Engine(conn: dict):
    """
    Dynamically builds a MySQL SQLAlchemy engine
    from provided connection parameters.
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

# ---------------------------------------------------------
# 🤖 Gemini AI Request Function
# ---------------------------------------------------------
async def gemini_request(prompt: str):
    """
    Sends a natural language prompt to Gemini AI
    and returns a generated text (SQL, table names, etc.)
    """
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }

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

# ---------------------------------------------------------
# 🧩 AI-Powered SQL Query Endpoint
# ---------------------------------------------------------
@app.post("/query")
async def query_vox(request: Request):
    """
    Main endpoint to:
        - Accept user prompt & DB credentials.
        - Generate SQL dynamically via Gemini.
        - Execute SQL and return results.

    Example Input JSON:
    {
        "prompt": "Show all students from CSE department",
        "connection": {
            "user": "root",
            "password": "1234",
            "host": "localhost",
            "port": 3306,
            "database": "college"
        }
    }
    """
    # -----------------------------------------------------
    # Step 1: Parse Input
    # -----------------------------------------------------
    body = await request.json()
    prompt = body.get("prompt", "")
    connection_info = body.get("connection", {})

    if not prompt:
        return {"error": "Prompt is missing."}
    if not connection_info:
        return {"error": "MySQL Database Connection info is missing."}

    # -----------------------------------------------------
    # Step 2: Create SQLAlchemy Engine
    # -----------------------------------------------------
    try:
        engine = Vox_Engine(connection_info)
    except Exception as e:
        return {"error": f"Engine creation failed: {str(e)}"}

    # -----------------------------------------------------
    # Step 3: Extract Table Names Using AI
    # -----------------------------------------------------
    try:
        table_prompt = (
            f"Extract table names from this prompt "
            f"(comma separated, no explanation): {prompt}"
        )
        table_str = await gemini_request(table_prompt)
        tables = [t.strip() for t in table_str.split(",") if t.strip()]
    except Exception as e:
        return {"error": f"Table extraction failed: {str(e)}"}

    # -----------------------------------------------------
    # Step 4: Fetch Table Schemas from Database
    # -----------------------------------------------------
    schema_parts = []
    try:
        with engine.begin() as conn:
            for table in tables:
                try:
                    rows = conn.execute(text(f"DESCRIBE {table}")).fetchall()
                    columns = [f"{row[0]} {row[1]}" for row in rows]
                    schema_parts.append(f"{table}({', '.join(columns)})")
                except SQLAlchemyError:
                    # Ignore missing or inaccessible tables
                    continue
    except Exception as e:
        return {"error": f"Schema extraction failed: {str(e)}"}

    schema = "\n".join(schema_parts)

    # -----------------------------------------------------
    # Step 5: Generate SQL Query via Gemini
    # -----------------------------------------------------
    try:
        sql_prompt = f"""
        You are a MySQL expert. Using this schema:
        {schema}
        Generate a valid SQL query for: {prompt}
        Return only SQL.
        """

        sql = await gemini_request(sql_prompt)

        # -------------------------------------------------
        # Step 6: Execute SQL on the Database
        # -------------------------------------------------
        with engine.begin() as conn:
            result = conn.execute(text(sql))

            if sql.lower().startswith("select"):
                # Convert rows to dictionary for JSON response
                rows = [dict(row._mapping) for row in result]
                return {
                    "sql": sql,
                    "data": rows,
                    "message": "Query executed successfully."
                }
            else:
                # For INSERT, UPDATE, DELETE, etc.
                return {
                    "sql": sql,
                    "message": f"{result.rowcount} rows affected."
                }

    except Exception as e:
        return {"error": f"Server error: {e}"}

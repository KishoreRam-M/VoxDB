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
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import httpx
from datetime import datetime
import subprocess

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
    allow_origins=["http://localhost:5173"],  # Frontend URL
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

    :param conn: Dictionary containing 'user', 'password', 'host', 'port', 'database'
    :return: SQLAlchemy Engine object
    :raises: ValueError if connection info is invalid
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
    and returns a generated text (SQL, table names, tasks, etc.)

    :param prompt: The user or system prompt to process
    :return: AI-generated text response
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
    # ------------------------
    # Step 1: Parse Input
    # ------------------------
    body = await request.json()
    prompt = body.get("prompt", "")
    connection_info = body.get("connection", {})

    if not prompt:
        return {"error": "Prompt is missing."}
    if not connection_info:
        return {"error": "MySQL Database Connection info is missing."}

    # ------------------------
    # Step 2: Create SQLAlchemy Engine
    # ------------------------
    try:
        engine = Vox_Engine(connection_info)
    except Exception as e:
        return {"error": f"Engine creation failed: {str(e)}"}

    # ------------------------
    # Step 3: Extract Table Names Using AI
    # ------------------------
    try:
        table_prompt = (
            f"Extract table names from this prompt "
            f"(comma separated, no explanation): {prompt}"
        )
        table_str = await gemini_request(table_prompt)
        tables = [t.strip() for t in table_str.split(",") if t.strip()]
    except Exception as e:
        return {"error": f"Table extraction failed: {str(e)}"}

    # ------------------------
    # Step 4: Fetch Table Schemas
    # ------------------------
    schema_parts = []
    try:
        with engine.begin() as conn:
            for table in tables:
                try:
                    rows = conn.execute(text(f"DESCRIBE {table}")).fetchall()
                    columns = [f"{row[0]} {row[1]}" for row in rows]
                    schema_parts.append(f"{table}({', '.join(columns)})")
                except SQLAlchemyError:
                    continue
    except Exception as e:
        return {"error": f"Schema extraction failed: {str(e)}"}

    schema = "\n".join(schema_parts)

    # ------------------------
    # Step 5: Generate SQL Query via AI
    # ------------------------
    try:
        sql_prompt = f"""
        You are a MySQL expert. Using this schema:
        {schema}
        Generate a valid SQL query for: {prompt}
        Return only SQL.
        """
        sql = await gemini_request(sql_prompt)

        # ------------------------
        # Step 6: Execute SQL on the Database
        # ------------------------
        with engine.begin() as conn:
            result = conn.execute(text(sql))
            if sql.lower().startswith("select"):
                rows = [dict(row._mapping) for row in result]
                return {
                    "sql": sql,
                    "data": rows,
                    "message": "Query executed successfully."
                }
            else:
                return {
                    "sql": sql,
                    "message": f"{result.rowcount} rows affected."
                }

    except Exception as e:
        return {"error": f"Server error: {e}"}


# ---------------------------------------------------------
# 📝 AI Task & Comment System
# ---------------------------------------------------------
@app.post("/task")
async def create_task(request: Request):
    """
    Creates a task and comment using AI interpretation.

    Input JSON Example:
    {
        "prompt": "Add a new column 'role' to the users table",
        "connection": { ... MySQL connection info ... }
    }
    """
    body = await request.json()
    task_prompt = body.get("prompt", "")
    connection_info = body.get("connection", {})

    if not task_prompt:
        return {"error": "Prompt is missing."}
    if not connection_info:
        return {"error": "MySQL Database Connection info is missing."}

    try:
        engine = Vox_Engine(connection_info)

        # AI-generated task and comment
        task_text = await gemini_request(
            f"Extract task description and comment clearly from this: {task_prompt}"
        )

        with engine.begin() as conn:
            # Create tasks table if it doesn't exist
            conn.execute(text("""
                              CREATE TABLE IF NOT EXISTS tasks
                              (
                                  id
                                  INT
                                  AUTO_INCREMENT
                                  PRIMARY
                                  KEY,
                                  description
                                  TEXT,
                                  comment
                                  TEXT,
                                  status
                                  VARCHAR
                              (
                                  20
                              ) DEFAULT 'pending',
                                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                  )
                              """))

            # Insert new task
            conn.execute(
                text("INSERT INTO tasks (description, comment) VALUES (:desc, :comm)"),
                {"desc": task_text, "comm": task_text}
            )

        return {"message": "Task created successfully", "task": task_text}

    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------
# 💾 Database Backup Endpoint
# ---------------------------------------------------------
@app.post("/backup")
async def backup_db(request: Request):
    """
    Backup MySQL database (requires mysqldump installed).

    Input JSON Example:
    {
        "connection": { ... MySQL connection info ... }
    }
    """
    body = await request.json()
    conn_info = body.get("connection", {})

    try:
        backup_file = f"{conn_info['database']}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
        cmd = [
            "mysqldump",
            "-h", conn_info['host'],
            "-P", str(conn_info['port']),
            "-u", conn_info['user'],
            f"-p{conn_info['password']}",
            conn_info['database']
        ]
        with open(backup_file, "w") as f:
            subprocess.run(cmd, stdout=f, check=True)

        return {"message": "Backup completed", "file": backup_file}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------
# 🎙️ Voice Command Endpoint
# ---------------------------------------------------------
@app.post("/voice")
async def voxVoice(file: UploadFile = File(...)):
    """
    Receive voice file, convert to text, and process via Gemini AI.

    :param file: Audio file (WAV/MP3)
    :return: JSON containing recognized text and AI response
    """
    import speech_recognition as sr

    re = sr.Recognizer()
    audio_data = sr.AudioFile(file.file)
    with audio_data as source:
        audio = re.record(source)

    text = re.recognize_google(audio)
    response = await gemini_request(f"Process this command: {text}")

    return {"voice_text": text, "response": response}


# ---------------------------------------------------------
# 🧩 Interactive Student-Friendly Task Guidance
# ---------------------------------------------------------
@app.post("/interactive-task")
async def interactive_task(request: Request):
    """
    Guides students step by step to perform tasks with detailed explanations.

    Features:
        1️⃣ Explains the task clearly (what, why, how it works).
        2️⃣ Provides behind-the-scenes explanation of SQL/AI operations.
        3️⃣ Asks simple interactive questions to engage the student.

    Input JSON Example:
    {
        "prompt": "Show all students from CSE department",
        "connection": { ... MySQL connection info ... }
    }
    """
    body = await request.json()
    prompt = body.get("prompt", "")
    connection_info = body.get("connection", {})

    if not prompt:
        return {"error": "Prompt is missing."}
    if not connection_info:
        return {"error": "MySQL Database Connection info is missing."}

    try:
        # Step 1: Create dynamic engine
        engine = Vox_Engine(connection_info)
    except Exception as e:
        return {"error": f"Engine creation failed: {str(e)}"}

    try:
        # Step 2: Explain task using AI
        explanation_prompt = f"""
        Explain step by step how to perform this task for a student:
        {prompt}
        Include:
        - What the task is
        - Why it's done
        - How it works behind the scenes (SQL/AI)
        - A simple question to ask the student
        """
        explanation = await gemini_request(explanation_prompt)
    except Exception as e:
        return {"error": f"Task explanation failed: {str(e)}"}

    try:
        # Step 3: Extract table names using AI (behind the scenes)
        table_prompt = f"Extract table names (comma separated) from: {prompt}"
        table_str = await gemini_request(table_prompt)
        tables = [t.strip() for t in table_str.split(",") if t.strip()]

        # Step 4: Fetch table schemas
        schema_parts = []
        with engine.begin() as conn:
            for table in tables:
                try:
                    rows = conn.execute(text(f"DESCRIBE {table}")).fetchall()
                    columns = [f"{row[0]} {row[1]}" for row in rows]
                    schema_parts.append(f"{table}({', '.join(columns)})")
                except SQLAlchemyError:
                    continue
        schema = "\n".join(schema_parts)

    except Exception as e:
        return {"error": f"Schema extraction failed: {str(e)}"}

    try:
        # Step 5: Generate SQL query using AI
        sql_prompt = f"""
        You are a MySQL expert. Using this schema:
        {schema}
        Generate a valid SQL query for: {prompt}
        Return only SQL.
        """
        sql = await gemini_request(sql_prompt)

        # Step 6: Execute SQL and return results
        with engine.begin() as conn:
            result = conn.execute(text(sql))
            if sql.lower().startswith("select"):
                rows = [dict(row._mapping) for row in result]
            else:
                rows = f"{result.rowcount} rows affected."

    except Exception as e:
        return {"error": f"SQL execution failed: {str(e)}"}

    return {
        "message": "Interactive task completed",
        "task_explanation": explanation,
        "tables": tables,
        "schema": schema,
        "sql": sql,
        "result": rows
    }


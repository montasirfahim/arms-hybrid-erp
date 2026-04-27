import os
import json
import logging
from typing import List, Dict, Optional
import urllib.parse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import MySQLdb
import MySQLdb.cursors
from groq import Groq
from dotenv import load_dotenv

# Load environment variables for local development
load_dotenv()

# Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_service")

app = FastAPI(title="ARMS AI Service", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Groq Configuration ---
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")
    return Groq(api_key=api_key)

# --- Database Helper ---
def get_db_connection():
    """
    Connects to MySQL using either DATABASE_URL (Render/Production) 
    or individual DB environment variables (Local).
    """
    db_url = os.getenv('DATABASE_URL')
    
    try:
        if db_url:
            # Parse DATABASE_URL: mysql://user:password@host:port/dbname
            url = urllib.parse.urlparse(db_url)
            conn = MySQLdb.connect(
                host=url.hostname,
                user=url.username,
                passwd=url.password,
                db=url.path[1:], # Remove leading slash
                port=url.port or 3306,
                cursorclass=MySQLdb.cursors.DictCursor,
                ssl={"ssl_mode": "REQUIRED"} if url.hostname and ("render.com" in url.hostname or "aivencloud.com" in url.hostname) else None
            )
        else:
            # Fallback to individual variables
            conn = MySQLdb.connect(
                host=os.getenv('DB_HOST', '127.0.0.1'),
                user=os.getenv('DB_USER'),
                passwd=os.getenv('DB_PASSWORD'),
                db=os.getenv('DB_NAME'),
                port=int(os.getenv('DB_PORT', '3306')),
                cursorclass=MySQLdb.cursors.DictCursor
            )
        return conn
    except Exception as e:
        logger.error(f"Database Connection Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

def execute_read_only_query(sql_query: str):
    query_stripped = sql_query.strip().upper()
    forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE"]
    
    if not query_stripped.startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed."}
    
    for word in forbidden_keywords:
        if f" {word} " in f" {query_stripped} ":
            return {"error": f"Keyword '{word}' is forbidden."}

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        return results if results else "No records found."
    except Exception as e:
        logger.error(f"SQL Execution Error: {str(e)}")
        return {"error": str(e)}
    finally:
        if conn:
            conn.close()

# --- Pydantic Models ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.1
    max_tokens: int = 1024

# --- AI Context ---
SCHEMA_CONTEXT = """
### Database Schema for ARMS ERP:
1. accounts_user: id (int, PK), name, email, role ('CHAIRMAN', 'FACULTY', 'OFFICER', 'STUDENT'), designation, is_verified (boolean)
2. accounts_batch: id (int, PK), session (varchar 7, e.g. '2025-26'), name (e.g. 'Masters in ICT')
3. accounts_student: student_id (varchar 7, PK, e.g. 'IT22001'), name, email, batch_id (FK to accounts_batch), group ('M.Sc', 'M.Engg', 'Both')
4. accounts_semester: id (int, PK), name ('1st Semester', '2nd Semester', '3rd Semester'), batch_id (FK to accounts_batch), committee_chairman_id (FK to accounts_user), result_status (boolean)
5. accounts_course: id (int, PK), course_code (e.g. 'ICT5101'), title, credit_hour, type ('Theory'), target_student ('M.Sc', 'M.Engg', 'Both'), batch_id (FK to accounts_batch), semester_id (FK to accounts_semester), course_teacher_id (FK to accounts_user), marks_input_status (boolean)
6. accounts_registeredstudent: id (int, PK), batch_id (FK to accounts_batch), semester_id (FK to accounts_semester), student_id (FK to accounts_student), status (boolean)
7. results_courseresult: id (int, PK), student_id (FK to accounts_student), course_id (FK to accounts_course), semester_id (FK to accounts_semester), ct_marks, attendance_marks, theory_internal, theory_external, theory_third_examiner, third_examiner_needed (boolean), final_theory_marks, gpa (float, 0.0-4.0), letter (e.g. 'A+')

### CRITICAL OPERATIONAL RULES:
1. **NO TECHNICAL TALK:** Never mention SQL, queries, tables, or database IDs to the user. 
2. **SILENT EXECUTION:** If you need data, use the `execute_read_only_query` tool. Do not describe the query you are about to run.
3. **NATURAL LANGUAGE ONLY:** Your response must be 100% natural language. 
4. **VAGUE REQUESTS:** If the user doesn't provide enough info, ask: "Which session or batch should I look into?"
5. **NO HALLUCINATIONS:** If the tool returns no data, say you couldn't find anything in the records.
"""

TOOLS = [

    {
        "type": "function",
        "function": {
            "name": "execute_read_only_query",
            "description": "Execute a MySQL SELECT query to fetch ERP data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {"type": "string", "description": "MySQL SELECT query."}
                },
                "required": ["sql_query"]
            }
        }
    }
]

# @app.get("/")
# def health_check():
#     return {"status": "healthy", "service": "ARMS-AI"}

@app.post("/chat")
async def ai_chat(request: ChatRequest):
    try:
        client = get_groq_client()
        messages = [{"role": "system", "content": f"You are the ARMS ERP Assistant. {SCHEMA_CONTEXT}"}]
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        response = client.chat.completions.create(
            model=request.model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        response_message = response.choices[0].message
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "execute_read_only_query":
                    args = json.loads(tool_call.function.arguments)
                    result = execute_read_only_query(args.get("sql_query"))
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "execute_read_only_query",
                        "content": json.dumps(result, default=str),
                    })

            second_response = client.chat.completions.create(model=request.model, messages=messages)
            return {"role": "assistant", "content": second_response.choices[0].message.content}

        return {"role": "assistant", "content": response_message.content}
    except Exception as e:
        logger.error(f"Chat Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

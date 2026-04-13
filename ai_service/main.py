from dotenv import load_dotenv
import os
import sys

# Get the absolute path to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Load root .env for DB and Django settings
root_env = os.path.join(BASE_DIR, ".env")
if os.path.exists(root_env):
    load_dotenv(root_env)

# 2. Load local .env for AI specific settings (Groq Key)
local_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(local_env):
    load_dotenv(local_env, override=True)

import django
import json
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

# Setup Django Environment
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj_arms.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from django.db import connection

# Initialize FastAPI app
app = FastAPI(title="ARMS AI SQL Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "llama-3.3-70b-versatile"
    temperature: Optional[float] = 0.1 # Lower temperature for better SQL accuracy
    max_tokens: Optional[int] = 1024

# --- SQL Execution Tool ---

def execute_read_only_query(sql_query: str):
    """
    Executes a raw SQL SELECT query against the database.
    Only SELECT statements are allowed for security.
    """
    # Security: Basic check to ensure it's a SELECT query
    query_stripped = sql_query.strip().upper()
    
    # Block non-SELECT queries and dangerous keywords
    forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE"]
    
    if not query_stripped.startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed for security reasons."}
    
    for word in forbidden_keywords:
        if f" {word} " in f" {query_stripped} ":
            return {"error": f"Keyword '{word}' is forbidden."}

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results if results else "No records found."
    except Exception as e:
        return {"error": str(e)}

# Tools definition for Groq
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_read_only_query",
            "description": "Execute a MySQL SELECT query to fetch data from the ERP database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string", 
                        "description": "A valid MySQL SELECT query. Example: 'SELECT * FROM accounts_student WHERE batch_id = 1'"
                    }
                },
                "required": ["sql_query"]
            }
        }
    }
]

SCHEMA_CONTEXT = """
### Database Schema for ARMS ERP:
1. accounts_batch: id (int, PK), session (varchar 7, e.g. '2025-26'), name (varchar 255)
2. accounts_student: student_id (varchar 7, PK, e.g. 'IT22001'), name, email, batch_id (FK to accounts_batch), group ('M.Sc', 'M.Engg', 'Both')
3. accounts_semester: id, name ('1st Semester', '2nd Semester', '3rd Semester'), batch_id (FK to accounts_batch), result_status (boolean)
4. accounts_course: id, course_code (e.g. 'ICT5101'), title, credit_hour, type ('Theory', 'Thesis', 'Project'), target_student ('M.Sc', 'M.Engg', 'Both'), batch_id (FK to accounts_batch), semester_id (FK to accounts_semester)
5. results_courseresult: id, student_id (FK to accounts_student), course_id (FK to accounts_course), semester_id (FK to accounts_semester), ct_marks, attendance_marks, theory_internal, theory_external, theory_third_examiner, gpa (float, 0.0-4.0)

### CRITICAL OPERATIONAL RULES:
1. **NO TECHNICAL TALK:** Never mention SQL, queries, tables, or database IDs to the user. 
2. **SILENT EXECUTION:** If you need data, use the `execute_read_only_query` tool. Do not describe the query you are about to run.
3. **NATURAL LANGUAGE ONLY:** Your response must be 100% natural language. 
   - Good: "There is 1 semester registered for the 2025-26 session."
   - Bad: "Running SELECT count... found 1."
4. **VAGUE REQUESTS:** If the user doesn't provide enough info (e.g., "show students"), do not guess. Ask: "Which session or batch should I look into?"
5. **NO HALLUCINATIONS:** If the tool returns no data, say you couldn't find anything in the records.
"""

@app.get("/")
async def root():
    return {"status": "Online", "service": "ARMS AI SQL Analytics Engine"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Use a very specific system message to enforce the rules
        messages = [
            {"role": "system", "content": f"You are the ARMS ERP Assistant. {SCHEMA_CONTEXT}"}
        ]
        
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        # 1. First call to decide on SQL
        response = client.chat.completions.create(
            model=request.model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        response_message = response.choices[0].message
        print(f"\n--- RAW AI RESPONSE (1st Call) ---\n{response_message.content}\n")
        
        tool_calls = response_message.tool_calls
        if tool_calls:
            print(f"--- TOOL CALLS ---\n{tool_calls}\n")

        # 2. If SQL generation was requested
        if tool_calls:
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments) 
                
                if function_name == "execute_read_only_query":
                    sql = function_args.get("sql_query")
                    print(f"--- EXECUTING SQL ---\n{sql}\n")
                    result = execute_read_only_query(sql)
                else:
                    result = {"error": "Function not found"}

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(result, default=str),
                })

            # 3. Final summary call
            second_response = client.chat.completions.create(
                model=request.model,
                messages=messages
            )
            print(f"--- FINAL AI SUMMARY ---\n{second_response.choices[0].message.content}\n")
            return {
                "role": "assistant",
                "content": second_response.choices[0].message.content
            }

        return {
            "role": "assistant",
            "content": response_message.content
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

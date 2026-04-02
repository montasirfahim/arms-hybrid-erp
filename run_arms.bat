@echo off
echo [1/2] Starting ARMS Django Core on Port 8000...
start cmd /k "venv\Scripts\activate && python manage.py runserver 8000"

echo [2/2] Starting ARMS AI Brain on Port 8001...
start cmd /k "venv\Scripts\activate && cd ai_service && uvicorn main:app --reload --port 8001"

echo ---------------------------------------------------
echo Systems are launching!
echo Admin Panel: http://127.0.0.1:8000/admin
echo AI Docs: http://127.0.0.1:8001/docs
echo ---------------------------------------------------
pause
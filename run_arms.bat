@echo off
echo Starting ARMS Hybrid ERP System...

:: Start FastAPI AI Service in a new window
echo Starting FastAPI AI Microservice...
start "ARMS-AI-Service" cmd /k "venv\Scripts\activate && uvicorn ai_service.main:app --host 127.0.0.1 --port 8001 --reload"

:: Start Django Server in the current window
echo Starting Django ERP Backend...
call venv\Scripts\activate
python -m pip install requests --quiet
python manage.py runserver

pause

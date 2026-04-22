#!/usr/bin/env bash

echo "Starting ARMS AI Service..."
# Start FastAPI in the background
python3 -m uvicorn ai_service.main:app --host 127.0.0.1 --port 8001 &

# Wait a few seconds for FastAPI to bind the port
sleep 5

echo "Starting Django Server..."
# Start Django Gunicorn
gunicorn proj_arms.wsgi:application --bind 0.0.0.0:$PORT

#!/usr/bin/env bash

# Start FastAPI in the background on port 8001
# We use 127.0.0.1 so it's only accessible internally
python -m uvicorn ai_service.main:app --host 127.0.0.1 --port 8001 &

# Start Django Gunicorn on the port Render provides
gunicorn proj_arms.wsgi:application --bind 0.0.0.0:$PORT

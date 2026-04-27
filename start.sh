#!/usr/bin/env bash

echo "Starting Django Server..."
# Start Django Gunicorn
# Using 0.0.0.0:$PORT so it works on Render
gunicorn proj_arms.wsgi:application --bind 0.0.0.0:$PORT

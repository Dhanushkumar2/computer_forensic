#!/bin/bash
cd "$(dirname "$0")/backend"
# Activate virtual environment (parent directory is the venv)
source ../../bin/activate 2>/dev/null || echo "Warning: Could not activate venv"
echo "Starting Django backend on http://localhost:8000"
python manage.py runserver 8000

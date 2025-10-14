#!/usr/bin/env bash
export FLASK_APP=app.py
export FLASK_ENV=production

# Run Gunicorn in production using the $PORT Render provides
exec gunicorn app:app --bind 0.0.0.0:$PORT

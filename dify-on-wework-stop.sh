#!/bin/bash

# 停止 Uvicorn
pkill -f "uvicorn main:app --host 0.0.0.0 --port 80"

# 停止 Celery
pkill -f "celery -A tasks worker"

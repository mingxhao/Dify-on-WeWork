#!/bin/bash

# 激活虚拟环境（使用动态路径）
source "$PWD/venv/bin/activate"

# 启动 Uvicorn
nohup uvicorn main:app --host 0.0.0.0 --port 80 >> /var/log/dify_on_wework_main.log 2>> /var/log/dify_on_wework_main_error.log &

# 启动 Celery
nohup celery -A tasks worker --loglevel=info >> /var/log/dify_on_wework_celery.log 2>> /var/log/dify_on_wework_celery_error.log &

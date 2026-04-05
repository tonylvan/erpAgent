@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d D:\erpAgent\backend
python -m uvicorn app.main:app --reload --port 8005

@echo off
cd /d D:\erpAgent\backend
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
python test_agent_api.py

@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d D:\erpAgent
python scripts\init_financial_risk_data.py

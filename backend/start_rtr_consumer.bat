@echo off
chcp 65001 >nul
cd /d D:\erpAgent\backend
echo ============================================
echo RTR Consumer Starting...
echo ============================================
python rtr_minimal.py
pause

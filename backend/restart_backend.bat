@echo off
chcp 65001 >nul
echo ========================================
echo GSD Backend Restart Script
echo ========================================
echo.

echo [1/4] Stopping all uvicorn processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
timeout /t 2 /nobreak >nul

echo [2/4] Cleaning cache...
cd /d "D:\erpAgent\backend"
if exist "app\__pycache__" rmdir /s /q "app\__pycache__"
if exist "__pycache__" rmdir /s /q "__pycache__"

echo [3/4] Starting backend server...
start "GSD Backend" cmd /k "cd /d D:\erpAgent\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005"

echo [4/4] Waiting for server to start...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo [SUCCESS] Backend restarted!
echo ========================================
echo.
echo Server URL: http://localhost:8005
echo API Docs: http://localhost:8005/docs
echo.

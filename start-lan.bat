@echo off
chcp 65001 >nul
echo ========================================
echo  GSD Platform - 局域网启动脚本
echo ========================================
echo.

REM 获取本机 IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do set LOCAL_IP=%%a
set LOCAL_IP=%LOCAL_IP: =%

echo [信息] 本机 IP: %LOCAL_IP%
echo.

REM 启动后端
echo [1/2] 启动后端 API...
start "GSD Backend" cmd /k "cd /d D:\erpAgent\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload"
timeout /t 3 /nobreak >nul

REM 启动前端
echo [2/2] 启动前端...
start "GSD Frontend" cmd /k "cd /d D:\erpAgent\frontend && npm run dev -- --host 0.0.0.0"

echo.
echo ========================================
echo  启动完成！
echo ========================================
echo.
echo 访问地址:
echo - 本机：http://localhost:5182
echo - 局域网：http://%LOCAL_IP%:5182
echo - API 文档：http://%LOCAL_IP%:8005/docs
echo.
echo 按任意键退出...
pause >nul

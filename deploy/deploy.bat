@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo ========================================
echo GSD 企业智能决策和预警中心 - 本地部署
echo ========================================
echo.

echo [1/4] 初始化 Neo4j 测试数据...
cd /d D:\erpAgent
python scripts\init_financial_risk_data.py
if errorlevel 1 (
    echo ❌ Neo4j 数据初始化失败
    pause
    exit /b 1
)
echo ✅ Neo4j 数据初始化完成
echo.

echo [2/4] 启动后端服务...
start "GSD Backend" cmd /k "cd /d D:\erpAgent\backend && uvicorn app.main:app --reload --port 8005"
echo ✅ 后端服务已启动 (http://localhost:8005)
echo ✅ Swagger UI: http://localhost:8005/docs
timeout /t 3 >nul
echo.

echo [3/4] 启动前端服务...
start "GSD Frontend" cmd /k "cd /d D:\erpAgent\frontend && npm run dev"
echo ✅ 前端服务已启动 (http://localhost:5177)
timeout /t 3 >nul
echo.

echo [4/4] 打开浏览器...
start http://localhost:5177
echo.

echo ========================================
echo ✅ 部署完成！
echo ========================================
echo.
echo 访问地址:
echo - 前端：http://localhost:5177
echo - 后端 API: http://localhost:8005
echo - Swagger UI: http://localhost:8005/docs
echo.
echo 按任意键退出...
pause >nul

@echo off
chcp 65001 >nul
echo ============================================================
echo Windows Redis 一键安装脚本
echo ============================================================
echo.

REM 检查是否已安装 Redis
redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis 已安装并运行中
    redis-cli --version
    goto :test_connection
)

echo [INFO] 未检测到 Redis，开始安装...
echo.

REM 检查 Docker
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker 已安装
    echo.
    echo 正在使用 Docker 安装 Redis...
    docker run -d --name redis -p 6379:6379 --restart always redis:latest
    if %errorlevel% equ 0 (
        echo [OK] Redis 容器启动成功
        goto :wait_redis
    ) else (
        echo [ERROR] Docker 容器启动失败
        goto :manual_install
    )
)

:manual_install
echo.
echo [WARN] Docker 未安装
echo.
echo 请选择安装方式:
echo 1. 下载 Windows 移植版（推荐新手）
echo 2. 使用 WSL2 安装（推荐开发者）
echo.
set /p choice="请输入选项 (1-2): "

if "%choice%"=="1" (
    echo.
    echo 正在下载 Redis for Windows...
    echo 下载地址：https://github.com/microsoftarchive/redis/releases
    echo 请手动下载 Redis-x64-3.0.504.msi 并安装
    echo.
    start https://github.com/microsoftarchive/redis/releases/download/Win-3.0.504/Redis-x64-3.0.504.msi
    echo [INFO] 已在浏览器中打开下载页面
    echo.
    set /p installed="安装完成后按回车继续检测... "
    goto :check_again
)

if "%choice%"=="2" (
    echo.
    echo 正在安装 WSL2...
    wsl --install
    echo [INFO] WSL2 安装完成后，请重启电脑并运行:
    echo   wsl -e bash -c "sudo apt update ^&^& sudo apt install redis-server -y"
    goto :end
)

:wait_redis
echo.
echo 等待 Redis 启动...
timeout /t 5 /nobreak >nul

:check_again
redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis 安装成功
    goto :test_connection
) else (
    echo [ERROR] 仍未检测到 Redis
    goto :end
)

:test_connection
echo.
echo ============================================================
echo 测试 Redis 连接
echo ============================================================
redis-cli ping
if %errorlevel% equ 0 (
    echo.
    echo [OK] Redis 连接成功
    echo.
    echo 正在更新环境变量...
    
    REM 更新 .env 文件
    echo.>> D:\erpAgent\backend\.env
    echo # Redis 配置>> D:\erpAgent\backend\.env
    echo REDIS_HOST=localhost>> D:\erpAgent\backend\.env
    echo REDIS_PORT=6379>> D:\erpAgent\backend\.env
    echo REDIS_PASSWORD=>> D:\erpAgent\backend\.env
    echo REDIS_DB=0>> D:\erpAgent\backend\.env
    echo CACHE_EXPIRE=3600>> D:\erpAgent\backend\.env
    
    echo [OK] 环境变量已更新
    echo.
    echo ============================================================
    echo 安装完成！
    echo ============================================================
    echo.
    echo 下一步:
    echo 1. 重启后端服务
    echo 2. 访问缓存统计 API: http://localhost:8005/api/v1/smart-query-v25/cache-stats
    echo.
) else (
    echo [ERROR] Redis 连接失败，请检查服务状态
)

:end
echo.
echo 按任意键退出...
pause >nul

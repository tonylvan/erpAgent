@echo off
REM ========================================
REM Ollama Embedding Model 常驻脚本
REM ========================================
REM 此脚本用于保持 Ollama embedding 模型常驻内存
REM 避免首次调用时的冷启动延迟
REM ========================================

echo ========================================
echo  Ollama Embedding Model 常驻脚本
echo ========================================
echo.

REM 检查 Ollama 服务是否运行
echo [1/3] 检查 Ollama 服务状态...
ollama ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama 服务未运行，正在启动...
    start "" "ollama app"
    timeout /t 5 /nobreak >nul
) else (
    echo [OK] Ollama 服务正在运行
)

echo.
echo [2/3] 预加载 embedding 模型...
REM 使用一个小查询来保持模型活跃
ollama run modelscope.cn/nomic-ai/nomic-embed-text-v1.5-GGUF:latest "warmup" >nul 2>&1
echo [OK] 模型已预加载

echo.
echo [3/3] 验证模型状态...
ollama ps
echo.

echo ========================================
echo  完成！Embedding 模型已常驻内存
echo ========================================
echo.
echo 模型信息:
echo - 名称：modelscope.cn/nomic-ai/nomic-embed-text-v1.5-GGUF:latest
echo - 大小：约 274 MB
echo - 端口：11434
echo.
echo 提示：
echo - 模型将在 18 分钟后自动卸载（Ollama 默认行为）
echo - 可以定期调用此脚本来保持模型常驻
echo - OpenClaw 已配置使用此本地模型
echo.
pause

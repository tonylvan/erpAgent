# GSD 企业智能决策和预警中心 - 本地部署脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GSD 企业智能决策和预警中心 - 本地部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 初始化 Neo4j 数据
Write-Host "[1/4] 初始化 Neo4j 测试数据..." -ForegroundColor Yellow
Set-Location D:\erpAgent
try {
    python scripts\init_financial_risk_data.py
    Write-Host "✅ Neo4j 数据初始化完成" -ForegroundColor Green
} catch {
    Write-Host "❌ Neo4j 数据初始化失败：$_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 2: 启动后端服务
Write-Host "[2/4] 启动后端服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\erpAgent\backend; uvicorn app.main:app --reload --port 8005"
Write-Host "✅ 后端服务已启动 (http://localhost:8005)" -ForegroundColor Green
Write-Host "✅ Swagger UI: http://localhost:8005/docs" -ForegroundColor Green
Start-Sleep -Seconds 3
Write-Host ""

# 步骤 3: 启动前端服务
Write-Host "[3/4] 启动前端服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\erpAgent\frontend; npm run dev"
Write-Host "✅ 前端服务已启动 (http://localhost:5177)" -ForegroundColor Green
Start-Sleep -Seconds 3
Write-Host ""

# 步骤 4: 打开浏览器
Write-Host "[4/4] 打开浏览器..." -ForegroundColor Yellow
Start-Process "http://localhost:5177"
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址:" -ForegroundColor White
Write-Host "  - 前端：http://localhost:5177" -ForegroundColor Cyan
Write-Host "  - 后端 API: http://localhost:8005" -ForegroundColor Cyan
Write-Host "  - Swagger UI: http://localhost:8005/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow

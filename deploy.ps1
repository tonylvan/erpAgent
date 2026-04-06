# GSD 工单中心 v3.0 部署脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GSD 工单中心 v3.0 部署检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查后端服务
Write-Host "[1/5] 检查后端服务 (端口 8005)..." -ForegroundColor Yellow
$backend = netstat -ano | findstr ":8005.*LISTENING"
if ($backend) {
    Write-Host "  ✅ 后端服务运行中" -ForegroundColor Green
} else {
    Write-Host "  ❌ 后端服务未运行" -ForegroundColor Red
    Write-Host "  启动命令：cd D:\erpAgent\backend; uvicorn app.main:app --reload --port 8005" -ForegroundColor Gray
}

# 检查前端服务
Write-Host ""
Write-Host "[2/5] 检查前端服务 (端口 5180)..." -ForegroundColor Yellow
$frontend = netstat -ano | findstr ":5180.*LISTENING"
if ($frontend) {
    Write-Host "  ✅ 前端服务运行中" -ForegroundColor Green
} else {
    Write-Host "  ❌ 前端服务未运行" -ForegroundColor Red
    Write-Host "  启动命令：cd D:\erpAgent\frontend; npm run dev" -ForegroundColor Gray
}

# 检查数据库连接
Write-Host ""
Write-Host "[3/5] 检查 PostgreSQL 数据库 (端口 5432)..." -ForegroundColor Yellow
$database = netstat -ano | findstr ":5432.*LISTENING"
if ($database) {
    Write-Host "  ✅ 数据库服务运行中" -ForegroundColor Green
} else {
    Write-Host "  ❌ 数据库服务未运行" -ForegroundColor Red
    Write-Host "  请启动 PostgreSQL 服务" -ForegroundColor Gray
}

# 检查数据库表
Write-Host ""
Write-Host "[4/5] 检查数据库表结构..." -ForegroundColor Yellow
$checkTables = @"
SELECT COUNT(*) as table_count FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('tickets', 'ticket_comments', 'ticket_notifications', 'ticket_workflow_logs');
"@
# 注意：这里需要 psql 命令，简化检查
Write-Host "  ⚠️  跳过详细检查 (需要 psql 连接)" -ForegroundColor Yellow
Write-Host "  手动检查：psql -U postgres -d erpagent -c `"$checkTables`"" -ForegroundColor Gray

# 访问 URL
Write-Host ""
Write-Host "[5/5] 服务访问地址:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  🌐 前端页面：" -NoNewline
Write-Host "http://localhost:5180" -ForegroundColor Cyan
Write-Host "  📝 工单列表：" -NoNewline
Write-Host "http://localhost:5180/tickets" -ForegroundColor Cyan
Write-Host "  📋 工单详情：" -NoNewline
Write-Host "http://localhost:5180/tickets/1" -ForegroundColor Cyan
Write-Host "  📖 API 文档：" -NoNewline
Write-Host "http://localhost:8005/docs" -ForegroundColor Cyan
Write-Host "  🧪 运行测试：" -NoNewline
Write-Host "cd D:\erpAgent\backend; pytest tests/ -v" -ForegroundColor Cyan
Write-Host ""

# 测试状态
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  快速测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. 访问 API 文档测试后端" -ForegroundColor Gray
Write-Host "  2. 访问工单列表测试前端" -ForegroundColor Gray
Write-Host "  3. 创建测试工单验证完整流程" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  部署检查完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

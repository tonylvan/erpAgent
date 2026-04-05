# GSD 智能问数自动化测试指南

本文档详细说明如何运行各类测试并生成报告。

## 📋 测试框架总览

| 测试类型 | 工具 | 用例数 | 位置 |
|---------|------|--------|------|
| 后端单元测试 | pytest | 27 | `backend/tests/test_smart_query_full.py` |
| 前端组件测试 | vitest | 13 | `frontend/tests/unit/SmartQuery.test.js` |
| E2E 端到端测试 | playwright | 11 | `frontend/tests/e2e/smart-query.spec.js` |
| 全链路集成测试 | pytest+aiohttp | 15 | `backend/tests/test_full_workflow.py` |
| 性能测试 | locust | 5 场景 | `backend/tests/performance/locustfile.py` |
| **总计** | - | **71** | - |

## 🚀 快速开始

### 1. 后端单元测试

```bash
cd D:\erpAgent\backend

# 运行所有测试
pytest tests/test_smart_query_full.py -v

# 运行并生成覆盖率报告
pytest tests/test_smart_query_full.py -v --cov=app --cov-report=html --cov-report=term-missing

# 运行特定测试类
pytest tests/test_smart_query_full.py::TestKeywordMatching -v
pytest tests/test_smart_query_full.py::TestAPIEndpoints -v
pytest tests/test_smart_query_full.py::TestPerformance -v
```

### 2. 前端组件测试

```bash
cd D:\erpAgent\frontend

# 运行单元测试
npm run test:unit

# 运行并生成覆盖率报告
npm run test:unit:coverage

# 监视模式（开发时使用）
npx vitest
```

### 3. E2E 端到端测试

```bash
cd D:\erpAgent\frontend

# 安装 Playwright 浏览器
npx playwright install chromium

# 运行 E2E 测试（无头模式）
npm run test:e2e

# 运行 E2E 测试（有头模式，可视化）
npm run test:e2e:headed

# 使用 UI 模式
npm run test:e2e:ui
```

### 4. 全链路集成测试

```bash
cd D:\erpAgent\backend

# 确保后端服务运行
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

# 运行集成测试
pytest tests/test_full_workflow.py -v --asyncio-mode=auto

# 运行特定测试类
pytest tests/test_full_workflow.py::TestFullWorkflow -v
pytest tests/test_full_workflow.py::TestFrontendIntegration -v
```

### 5. 性能测试

```bash
cd D:\erpAgent\backend

# 确保后端服务运行
uvicorn app.main:app --host 0.0.0.0 --port 8005

# 方式 1：Web UI 模式（推荐）
locust -f tests/performance/locustfile.py --host=http://localhost:8005
# 浏览器访问：http://localhost:8089

# 方式 2：无头模式（CI/CD 使用）
locust -f tests/performance/locustfile.py --host=http://localhost:8005 --headless -u 100 -r 10 --run-time 60s

# 方式 3：压力测试
locust -f tests/performance/locustfile.py --host=http://localhost:8005 --headless -u 200 -r 20 --run-time 120s
```

## 📊 验收标准

### 性能指标

| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| P99 响应时间 | < 500ms | `test_response_time_p99` |
| 平均响应时间 | < 200ms | `test_response_time_p50` |
| QPS | > 50 | `test_qps_throughput` |
| 错误率 | < 1% | `test_error_rate_under_load` |
| 测试覆盖率 | > 70% | `--cov` 参数 |

### 功能指标

- ✅ 所有关键词匹配测试通过
- ✅ 所有 API 端点测试通过
- ✅ 所有缓存测试通过
- ✅ 所有数据结构测试通过
- ✅ 所有边界条件测试通过
- ✅ 所有集成测试通过

## 📁 测试报告

### 生成 HTML 报告

```bash
# 后端测试报告
pytest tests/test_smart_query_full.py -v --cov=app --cov-report=html
# 打开：backend/htmlcov/index.html

# 前端测试报告
npm run test:unit:coverage
# 打开：frontend/coverage/index.html

# Playwright 报告
npm run test:e2e
# 打开：frontend/playwright-report/index.html
```

### 生成 JUnit XML 报告（CI/CD 使用）

```bash
# 后端
pytest tests/test_smart_query_full.py -v --junitxml=report.xml

# 前端
npx vitest run --reporter=junit
```

## 🔧 故障排查

### 常见问题

**1. 端口被占用**
```bash
# 检查端口
netstat -ano | findstr :8005

# 终止进程
taskkill /F /PID <PID>
```

**2. 依赖缺失**
```bash
# 后端
cd D:\erpAgent\backend
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx pytest-cov locust aiohttp

# 前端
cd D:\erpAgent\frontend
npm install
```

**3. Playwright 浏览器未安装**
```bash
cd D:\erpAgent\frontend
npx playwright install --with-deps chromium
```

**4. 测试超时**
```bash
# 增加超时时间
pytest tests/test_full_workflow.py -v --timeout=60
```

## 📝 测试清单

运行测试前检查：

- [ ] 后端服务运行在 8005 端口
- [ ] 前端服务运行在 5176 端口
- [ ] 数据库连接正常
- [ ] Neo4j 连接正常
- [ ] 所有依赖已安装
- [ ] 环境变量已配置

## 🎯 最佳实践

1. **本地开发**：先运行单元测试，再运行集成测试
2. **提交前**：运行所有测试确保通过率 100%
3. **性能测试**：在独立环境运行，避免影响开发
4. **覆盖率**：新增代码必须包含对应测试
5. **CI/CD**：所有测试自动运行，失败阻止部署

## 📈 持续改进

- 定期审查测试用例
- 更新测试以覆盖新功能
- 优化慢测试
- 维护测试数据

---

**最后更新**: 2026-04-05  
**维护者**: CodeMaster

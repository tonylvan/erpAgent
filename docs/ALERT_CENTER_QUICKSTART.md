# 🚀 预警中心模块 - 快速启动指南

## 📋 5 分钟快速体验

### 步骤 1: 初始化测试数据 (1 分钟)

```bash
cd D:\erpAgent
python scripts/init_financial_risk_data.py
```

**预期输出**:
```
✅ 创建公司和现金流：某某科技有限公司，现金流：¥500,000
✅ 创建财务比率：流动比率 0.8, ROE 3%...
✅ 创建部门预算：市场部，偏差 30%
✅ 创建客户应收账款：6 笔逾期
✅ 创建供应商应付账款：3 笔 7 天内到期
```

---

### 步骤 2: 启动后端服务 (1 分钟)

```bash
# 终端 1
cd D:\erpAgent\backend
uvicorn app.main:app --reload --port 8005
```

**验证**: 访问 http://localhost:8005/docs 查看 API 文档

---

### 步骤 3: 启动前端服务 (1 分钟)

```bash
# 终端 2
cd D:\erpAgent\frontend
npm run dev
```

**验证**: 访问 http://localhost:5177

---

### 步骤 4: 查看预警看板 (1 分钟)

1. 打开浏览器：http://localhost:5177
2. 导航到 "预警中心" 或访问 `/alert-center`
3. 查看预警列表和财务风险专项

**预期看到**:
- 🔴 高危预警：现金流风险
- 🟠 警告预警：应收账款逾期、预算偏差
- 💰 财务健康度评分：65 分 (需关注)

---

### 步骤 5: 测试 API (1 分钟)

```bash
# 获取所有预警
curl http://localhost:8005/api/v1/alerts

# 获取财务风险专项
curl http://localhost:8005/api/v1/alerts/financial

# 获取预警统计
curl http://localhost:8005/api/v1/alerts/stats
```

---

## 🧪 运行测试

### 单元测试

```bash
cd D:\erpAgent\backend
pytest tests/test_alert_rules.py -v
```

**预期**: 20 个测试用例 100% 通过

### 查看覆盖率

```bash
pytest tests/test_alert_rules.py --cov=app.services.alert_rules --cov-report=html
open htmlcov/index.html
```

**预期**: 100% 代码覆盖率

---

## 📊 功能演示

### 1. 查看预警列表

**路径**: 预警中心 → 预警列表

**功能**:
- 按 severity 排序 (RED > ORANGE > YELLOW)
- 按级别筛选 (全部/高危/警告/提示)
- 按类型筛选 (全部/业务/财务)

---

### 2. 查看财务风险专项

**路径**: 预警中心 → 财务风险专项

**展示**:
- 财务健康度评分 (0-100 分)
- 关键指标：流动比率、负债权益比、ROE、现金流
- 风险 indicator 列表

---

### 3. 确认预警

**操作**: 点击预警卡片上的 "确认接收" 按钮

**效果**: 预警状态变更为 "已确认"

---

### 4. 分配负责人

**操作**: 点击 "分配负责人" → 填写姓名和时限 → 确认

**效果**: 创建工单并通知负责人

---

## 🔍 常见问题

### Q1: 测试数据如何初始化？

**A**: 运行初始化脚本:
```bash
python scripts/init_financial_risk_data.py
```

---

### Q2: 如何添加新的预警规则？

**A**: 在 `app/services/alert_rules.py` 中添加新方法:

```python
def check_new_rule(self) -> List[Dict[str, Any]]:
    """新预警规则"""
    query = """
    MATCH (n:Node)
    WHERE n.condition = true
    RETURN 'NEW_ALERT' as alert_type, 'RED' as severity
    """
    with self.driver.session() as session:
        result = session.run(query)
        return [dict(record) for record in result]
```

然后在 `run_all_alerts()` 中调用。

---

### Q3: 如何修改预警阈值？

**A**: 阈值在 Cypher 查询中硬编码，建议改为参数化:

```python
def check_cashflow_risk(self, threshold: float = 1000000) -> List[Dict]:
    query = """
    MATCH (c:Company)-[:HAS_CASHFLOW]->(cf:CashFlow)
    WHERE cf.balance < $threshold
    RETURN ...
    """
    with self.driver.session() as session:
        result = session.run(query, threshold=threshold)
        return [dict(record) for result in result]
```

---

### Q4: 如何集成通知推送？

**A**: 在 `assign_alert()` 中添加通知逻辑:

```python
async def assign_alert(...):
    # 创建工单
    task = create_task(...)
    
    # 发送通知
    if notify_type == 'wechat':
        send_wechat_notification(...)
    elif notify_type == 'email':
        send_email_notification(...)
    
    return {"success": True, ...}
```

---

### Q5: 如何查看 API 文档？

**A**: 启动后端后访问:
- Swagger UI: http://localhost:8005/docs
- ReDoc: http://localhost:8005/redoc

---

## 📁 文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| 预警规则引擎 | `backend/app/services/alert_rules.py` | 11 个预警规则 |
| 预警 API | `backend/app/api/v1/alerts.py` | 6 个 API 端点 |
| 预警看板 | `frontend/src/views/AlertCenter.vue` | 前端组件 |
| 测试代码 | `backend/tests/test_alert_rules.py` | 20 个测试用例 |
| 测试数据脚本 | `scripts/init_financial_risk_data.py` | Neo4j 数据初始化 |
| 测试报告 | `docs/ALERT_CENTER_TEST_REPORT.md` | 详细测试报告 |
| 完成总结 | `docs/ALERT_CENTER_COMPLETION_SUMMARY.md` | 开发总结 |
| 验收报告 | `docs/ALERT_CENTER_FINAL_ACCEPTANCE.md` | 最终验收 |

---

## 🎯 下一步

### 1. 探索预警规则

阅读 `app/services/alert_rules.py` 了解 11 个预警规则的 Cypher 实现。

### 2. 自定义阈值

根据实际业务需求调整预警阈值。

### 3. 集成工单系统

实现预警→工单的自动转换。

### 4. 添加通知推送

集成企业微信/钉钉/邮件通知。

### 5. 部署到生产环境

参考 `docs/deployment.md` 进行生产部署。

---

## 📞 技术支持

- **API 文档**: http://localhost:8005/docs
- **测试报告**: `docs/ALERT_CENTER_TEST_REPORT.md`
- **问题反馈**: 查看项目 README.md

---

**🎉 祝使用愉快！** 🚀

<qqimg>https://picsum.photos/800/600?random=quick-start-guide</qqimg>

# Agent 风险检测系统使用文档

## 概述

Agent 风险检测系统是基于 Neo4j 图数据库的智能风险识别引擎，包含 3 个专业化 Agent，分别负责业务风险、财务风险和用户操作问题的检测与预警。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 应用层                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           app/api/v1/agents.py (API 路由)            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Agent 层                                 │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────┐│
│  │ BusinessRisk     │ │ FinancialRisk    │ │ UserOperation││
│  │ Agent            │ │ Agent            │ │ Agent        ││
│  │ (业务风险)        │ │ (财务风险)        │ │ (用户操作)    ││
│  └──────────────────┘ └──────────────────┘ └──────────────┘│
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   服务层 (复用现有资产)                       │
│  ┌──────────────────┐ ┌──────────────────┐                 │
│  │ AlertRuleEngine  │ │ FinancialAnalysis│                 │
│  │ (alert_rules.py) │ │ (financial_      │                 │
│  │                  │ │  analysis.py)    │                 │
│  └──────────────────┘ └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Neo4j 图数据库                          │
└─────────────────────────────────────────────────────────────┘
```

## Agent 详情

### 1. BusinessRiskAgent (业务风险 Agent)

**文件**: `app/agents/business_risk_agent.py`

**职责**: 封装现有业务预警规则，提供统一的风险检测接口

**检测规则** (6 条):
| 规则名称 | 方法 | 严重程度 | 描述 |
|---------|------|---------|------|
| 库存预警 | `check_inventory_low()` | MEDIUM | 库存低于安全线 |
| 库存为零 | `check_inventory_zero()` | CRITICAL | 库存为 0 且有未完成订单 |
| 付款逾期 | `check_payment_overdue()` | HIGH | 发票付款逾期 |
| 客户流失 | `check_customer_churn()` | HIGH | 客户 90 天未下单 |
| 供应商交货逾期 | `check_delivery_delay()` | MEDIUM | 采购订单交货逾期 |
| 销售订单异常 | `check_sales_anomaly()` | MEDIUM | 订单金额异常波动 |

**使用示例**:
```python
from app.agents.business_risk_agent import BusinessRiskAgent
from app.core.database import get_neo4j_driver

driver = get_neo4j_driver()
agent = BusinessRiskAgent(driver)

# 执行分析
findings = agent.analyze()

# 获取摘要
summary = agent.get_summary()
```

**输出格式**:
```json
{
  "risk_id": "business_risk_inventory_low_P001_0",
  "risk_type": "INVENTORY_LOW",
  "severity": "MEDIUM",
  "entity_id": "P001",
  "entity_name": "测试产品",
  "description": "库存低于安全线，建议补货",
  "recommendation": "立即安排补货",
  "data": {
    "current_stock": 10,
    "safety_threshold": 50
  },
  "detected_at": "2024-01-15T10:30:00",
  "agent": "business_risk",
  "agent_version": "1.0.0"
}
```

---

### 2. FinancialRiskAgent (财务风险 Agent)

**文件**: `app/agents/financial_risk_agent.py`

**职责**: 封装财务风险规则，集成财务分析引擎

**检测规则** (5 条):
| 规则名称 | 方法 | 严重程度 | 描述 |
|---------|------|---------|------|
| 现金流风险 | `check_cashflow_risk()` | CRITICAL | 现金流低于安全线 |
| 应收账款逾期 | `check_ar_overdue()` | HIGH | 客户应收账款逾期 |
| 应付账款风险 | `check_ap_risk()` | MEDIUM | 7 天内到期应付 |
| 财务比率异常 | `check_financial_ratio_abnormal()` | HIGH | 流动比率/负债权益比/ROE 异常 |
| 预算偏差 | `check_budget_variance()` | MEDIUM | 部门预算偏差超过 20% |

**特色功能**:
- **财务健康度评分**: `analyze_health_score(company_id)` - 计算公司财务健康度 (0-100 分)
- **风险传播分析**: `analyze_risk_propagation(risk_id, risk_type)` - 分析风险传播路径和影响范围

**使用示例**:
```python
from app.agents.financial_risk_agent import FinancialRiskAgent

driver = get_neo4j_driver()
agent = FinancialRiskAgent(driver)

# 执行风险检测
findings = agent.analyze()

# 计算财务健康度评分
health_score = agent.analyze_health_score("company_123")

# 分析风险传播
propagation = agent.analyze_risk_propagation("risk_456", "CASHFLOW")
```

**健康度评分维度**:
- 流动性 (权重 30%): 流动比率、速动比率
- 杠杆 (权重 25%): 负债权益比
- 盈利能力 (权重 25%): ROE
- 现金流 (权重 20%): 现金余额、消耗率

**健康等级**:
- HEALTHY: ≥80 分
- NEEDS_ATTENTION: 60-79 分
- AT_RISK: 40-59 分
- CRITICAL: <40 分

---

### 3. UserOperationAgent (用户操作问题 Agent)

**文件**: `app/agents/user_operation_agent.py`

**职责**: 检测用户操作异常、数据质量问题、流程阻塞和系统使用异常

**检测规则** (9 条):

#### 操作异常 (3 条)
| 规则名称 | 方法 | 严重程度 | 描述 |
|---------|------|---------|------|
| 频繁修改 | `_check_frequent_modifications()` | HIGH | 1 小时内修改同一实体≥10 次 |
| 非工作时间操作 | `_check_off_hours_operation()` | MEDIUM | 22:00-6:00 或周末的敏感操作 |
| 未授权访问 | `_check_unauthorized_access()` | CRITICAL | 尝试访问无权资源≥3 次 |

#### 数据质量 (2 条)
| 规则名称 | 方法 | 严重程度 | 描述 |
|---------|------|---------|------|
| 必填字段缺失 | `_check_missing_fields()` | MEDIUM | 关键实体缺少必填字段 |
| 重复条目 | `_check_duplicate_entries()` | MEDIUM | 基于关键字段的重复记录 |

#### 流程阻塞 (2 条)
| 规则名称 | 方法 | 严重程度 | 描述 |
|---------|------|---------|------|
| 审批超时 | `_check_approval_timeout()` | HIGH | 审批请求>48 小时未处理 |
| 工单逾期 | `_check_ticket_overdue()` | HIGH/CRITICAL | 工单>3 天未解决 |

#### 系统使用 (2 条)
| 规则名称 | 方法 | 严重程度 | 描述 |
|---------|------|---------|------|
| 低功能采用率 | `_check_low_feature_adoption()` | LOW | 功能使用率<30% |
| 高错误率 | `_check_high_error_rate()` | HIGH | API 错误率>10% |

**配置参数**:
```python
agent.config = {
    "frequent_modifications": {"threshold_count": 10, "window_hours": 1},
    "off_hours": {"start_hour": 22, "end_hour": 6, "weekends": True},
    "approval_timeout": {"timeout_hours": 48},
    "ticket_overdue": {"overdue_days": 3},
    "feature_adoption": {"min_usage_rate": 0.3},
    "error_rate": {"max_error_rate": 0.1, "window_hours": 24}
}
```

**使用示例**:
```python
from app.agents.user_operation_agent import UserOperationAgent

driver = get_neo4j_driver()
agent = UserOperationAgent(driver)

# 执行分析
findings = agent.analyze()

# 获取摘要
summary = agent.get_summary()
```

---

## API 接口

**路由**: `app/api/v1/agents.py`

### 1. 业务风险检测
```http
GET /api/v1/agents/business-risk
```

**响应**:
```json
{
  "success": true,
  "agent": "business_risk",
  "findings": [...],
  "summary": {...},
  "timestamp": "2024-01-15T10:30:00"
}
```

### 2. 财务风险检测
```http
GET /api/v1/agents/financial-risk
```

### 3. 财务健康度评分
```http
GET /api/v1/agents/financial-risk/health-score/{company_id}
```

### 4. 风险传播分析
```http
GET /api/v1/agents/financial-risk/propagation/{risk_id}/{risk_type}
```

### 5. 用户操作检测
```http
GET /api/v1/agents/user-operation
```

### 6. 全量风险检测
```http
GET /api/v1/agents/all
```

**响应**:
```json
{
  "success": true,
  "total": 123,
  "by_agent": {
    "business_risk": {"count": 45, "summary": {...}},
    "financial_risk": {"count": 38, "summary": {...}},
    "user_operation": {"count": 40, "summary": {...}}
  },
  "by_severity": {
    "CRITICAL": 10,
    "HIGH": 25,
    "MEDIUM": 50,
    "LOW": 38
  },
  "findings": [...],
  "timestamp": "2024-01-15T10:30:00"
}
```

### 7. 风险摘要统计
```http
GET /api/v1/agents/summary
```

---

## 严重程度说明

| 级别 | 说明 | 响应要求 |
|-----|------|---------|
| CRITICAL | 危急 | 立即处理，可能影响核心业务 |
| HIGH | 高危 | 24 小时内处理，可能影响重要业务 |
| MEDIUM | 中等 | 72 小时内处理，需要关注 |
| LOW | 低危 | 定期审查，优化改进 |

---

## 测试

### 运行测试
```bash
cd D:\erpAgent\backend

# 运行所有 Agent 测试
pytest tests/test_business_risk_agent.py -v
pytest tests/test_financial_risk_agent.py -v
pytest tests/test_user_operation_agent.py -v

# 运行单个测试
pytest tests/test_business_risk_agent.py::TestBusinessRiskAgentAnalyze::test_analyze_returns_list -v
```

### 测试覆盖
- ✅ Agent 初始化测试
- ✅ 各检测规则测试
- ✅ 输出格式验证
- ✅ 错误处理测试
- ✅ 摘要统计测试
- ✅ 配置参数测试

---

## 最佳实践

### 1. 定期执行检测
建议配置定时任务，每小时执行一次全量风险检测：
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(check_all_risks, 'interval', hours=1)
scheduler.start()
```

### 2. 风险分级处理
```python
findings = agent.analyze()

# 优先处理 CRITICAL 和 HIGH 级别
critical_findings = [f for f in findings if f["severity"] == "CRITICAL"]
high_findings = [f for f in findings if f["severity"] == "HIGH"]

# 发送告警
for finding in critical_findings:
    send_alert(finding, channel="critical")
```

### 3. 风险趋势分析
```python
# 保存历史检测结果
def save_risk_history(findings):
    with open("risk_history.json", "a") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": len(findings),
            "by_severity": {...}
        }, f)
        f.write("\n")
```

### 4. 集成告警系统
```python
# 企业微信告警
def send_wechat_alert(finding):
    if finding["severity"] in ["CRITICAL", "HIGH"]:
        requests.post(
            WEBHOOK_URL,
            json={
                "msgtype": "markdown",
                "markdown": {
                    "content": f"## {finding['risk_type']}\n\n{finding['description']}"
                }
            }
        )
```

---

## 故障排查

### 常见问题

#### 1. Neo4j 连接失败
**错误**: `Neo4j connection error`

**解决**:
```bash
# 检查 Neo4j 服务状态
neo4j status

# 检查连接配置
cat .env | grep NEO4J
```

#### 2. 检测结果为空
**可能原因**:
- Neo4j 数据库无数据
- Cypher 查询条件过严
- 节点标签不匹配

**解决**:
```cypher
// 检查数据是否存在
MATCH (n) RETURN labels(n), count(n)
```

#### 3. 性能问题
**优化建议**:
- 为常用查询字段创建索引
- 限制返回结果数量 (LIMIT)
- 使用异步执行

---

## 扩展开发

### 添加新检测规则

1. 在对应 Agent 中添加检测方法:
```python
def _check_new_rule(self) -> List[Dict[str, Any]]:
    findings = []
    cypher = """
    MATCH (n:NodeType)
    WHERE n.condition = true
    RETURN n.id, n.name
    """
    
    with self.driver.session() as session:
        result = session.run(cypher)
        for record in result:
            findings.append({
                "risk_id": f"{self.agent_name}_new_rule_{record['n.id']}",
                "risk_type": "NEW_RULE",
                "severity": "MEDIUM",
                ...
            })
    
    return findings
```

2. 在 `analyze()` 方法中调用:
```python
def analyze(self) -> List[Dict[str, Any]]:
    findings = []
    findings.extend(self._check_new_rule())
    # ... 其他规则
    return findings
```

3. 添加单元测试

---

## 版本历史

| 版本 | 日期 | 变更 |
|-----|------|------|
| 1.0.0 | 2024-01-15 | 初始版本，3 个 Agent 全部实现 |

---

## 联系支持

如有问题或建议，请联系:
- 开发者：GSD 团队
- 文档：`D:\erpAgent\docs\AGENT_RISK_DETECTION.md`

# 业务风险检测 Agent (Business Risk Agent)

## 概述

业务风险检测 Agent 是 ERP Agent 系统的核心组件，用于实时检测 ERP 业务流程中的异常情况，提供风险告警和决策建议。

### 核心能力

- **4 大类风险检测**：库存、采购、销售、付款
- **15 条检测规则**：覆盖主要业务风险场景
- **实时告警**：支持严重程度分级（CRITICAL/HIGH/MEDIUM/LOW）
- **智能建议**：为每个风险提供可操作的建议
- **图谱分析**：利用 Neo4j 进行供应商关系链分析

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    BusinessRiskAgent                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  库存异常检测 │  │  采购异常检测 │  │  销售异常检测 │      │
│  │  (4 条规则)   │  │  (4 条规则)   │  │  (4 条规则)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  付款异常检测 │  │  Neo4j 图谱分析│                        │
│  │  (3 条规则)   │  │  (供应商风险) │                        │
│  └──────────────┘  └──────────────┘                        │
├─────────────────────────────────────────────────────────────┤
│           PostgreSQL              │         Neo4j           │
│  (采购/销售/库存/付款表)          │   (供应商关系链)        │
└─────────────────────────────────────────────────────────────┘
```

## 检测规则详解

### 1. 库存异常 (Inventory Risks)

#### 1.1 库存低于安全库存 (`inventory_low`)

**检测规则**：
```python
current_stock < safety_stock
```

**严重程度**：
- `CRITICAL`: current_stock < safety_stock * 0.5
- `HIGH`: current_stock < safety_stock * 0.8
- `MEDIUM`: 其他

**SQL 查询**：
```sql
SELECT p.id, p.name, i.current_stock, i.safety_stock
FROM products p
JOIN inventory i ON p.id = i.product_id
WHERE i.current_stock < i.safety_stock
```

**示例告警**：
```json
{
  "risk_type": "inventory_low",
  "severity": "CRITICAL",
  "description": "iPhone 15 Pro 库存不足",
  "data": {
    "product_id": 123,
    "product_name": "iPhone 15 Pro",
    "current_stock": 30,
    "safety_stock": 100,
    "shortage": 70
  },
  "recommendation": "立即补货 70 件，联系供应商",
  "impact": "可能影响销售订单交付"
}
```

#### 1.2 库存周转率过低 (`inventory_turnover_low`)

**检测规则**：
```python
turnover_rate = cost_of_goods_sold / average_inventory
turnover_rate < industry_benchmark * 0.5  # 行业基准 50%
```

**阈值**：
- `HIGH`: 周转率 < 行业基准 * 0.25
- `MEDIUM`: 周转率 < 行业基准 * 0.5

#### 1.3 滞销商品 (`inventory_slow_moving`)

**检测规则**：
```python
90 天无销售记录 AND 库存金额 > 0
```

**阈值**：
- `CRITICAL`: 库存价值 > ¥50,000
- `HIGH`: 库存价值 > ¥10,000
- `MEDIUM`: 库存价值 > ¥1,000

#### 1.4 库存积压 (`inventory_overstock`)

**检测规则**：
```python
current_stock > safety_stock * 3
```

**严重程度**：
- `HIGH`: current_stock > safety_stock * 5
- `MEDIUM`: current_stock > safety_stock * 3

---

### 2. 采购异常 (Purchase Risks)

#### 2.1 供应商交货延迟 (`purchase_delivery_delay`)

**检测规则**：
```python
expected_delivery_date < today AND status = 'PENDING'
```

**严重程度**：
- `CRITICAL`: 延迟天数 > 14
- `HIGH`: 延迟天数 > 7
- `MEDIUM`: 延迟天数 <= 7

#### 2.2 采购价格波动 (`purchase_price_fluctuation`)

**检测规则**：
```python
fluctuation = |(current_price - historical_avg) / historical_avg| * 100
fluctuation > 20%
```

**严重程度**：
- `HIGH`: 波动 > 50%
- `MEDIUM`: 波动 > 30%
- `LOW`: 波动 > 20%

#### 2.3 单一供应商依赖 (`purchase_single_supplier`)

**检测规则**：
```python
supplier_purchase / total_purchase > 80%
```

**严重程度**：
- `CRITICAL`: 占比 > 90%
- `HIGH`: 占比 > 80%

#### 2.4 采购订单异常取消 (`purchase_order_cancel`)

**检测规则**：
```python
cancelled_orders / total_orders > 15%
```

**严重程度**：
- `HIGH`: 取消率 > 30%
- `MEDIUM`: 取消率 > 15%

---

### 3. 销售异常 (Sales Risks)

#### 3.1 客户订单取消率过高 (`sales_order_cancel`)

**检测规则**：
```python
cancelled_orders / total_orders > 15%
```

#### 3.2 销售退货率过高 (`sales_return_high`)

**检测规则**：
```python
return_amount / sales_amount > 10%
```

**严重程度**：
- `CRITICAL`: 退货率 > 30%
- `HIGH`: 退货率 > 20%
- `MEDIUM`: 退货率 > 10%

#### 3.3 销售额异常下降 (`sales_decline`)

**检测规则**：
```python
(this_month_sales - last_month_sales) / last_month_sales < -50%
```

**严重程度**：
- `CRITICAL`: 下降 > 80%
- `HIGH`: 下降 > 60%
- `MEDIUM`: 下降 > 50%

#### 3.4 大客户流失风险 (`sales_customer_lost`)

**检测规则**：
```python
Top 10 客户 AND 30 天无订单
```

**严重程度**：
- `CRITICAL`: 90 天销售额 > ¥500,000
- `HIGH`: 90 天销售额 > ¥100,000
- `MEDIUM`: 其他

---

### 4. 付款异常 (Payment Risks)

#### 4.1 重复付款检测 (`payment_duplicate`)

**检测规则**：
```python
相同金额 + 相同供应商 + 7 天内多笔付款
```

**严重程度**：
- `CRITICAL`: 付款次数 > 3
- `HIGH`: 付款次数 > 2
- `MEDIUM`: 付款次数 = 2

#### 4.2 付款金额与发票不符 (`payment_invoice_mismatch`)

**检测规则**：
```python
|payment_amount - invoice_amount| / invoice_amount > 5%
```

#### 4.3 异常大额付款 (`payment_abnormal_large`)

**检测规则**：
```python
payment_amount > average_payment * 10
```

**严重程度**：
- `CRITICAL`: > 平均值 * 50
- `HIGH`: > 平均值 * 20
- `MEDIUM`: > 平均值 * 10

---

## 使用方法

### 1. 基础使用

```python
from app.agents.business_risk_agent import BusinessRiskAgent

# 创建 Agent 实例
agent = BusinessRiskAgent()

# 检测所有风险
alerts = agent.detect_all_risks()

# 处理告警
for alert in alerts:
    print(f"[{alert.severity}] {alert.risk_type}: {alert.description}")
    print(f"建议：{alert.recommendation}")
    print(f"影响：{alert.impact}")

# 关闭连接
agent.close()
```

### 2. 分类检测

```python
# 只检测库存风险
inventory_alerts = agent.detect_inventory_risks()

# 只检测采购风险
purchase_alerts = agent.detect_purchase_risks()

# 只检测销售风险
sales_alerts = agent.detect_sales_risks()

# 只检测付款风险
payment_alerts = agent.detect_payment_risks()
```

### 3. 获取汇总报告

```python
summary = agent.get_risk_summary()

print(f"总风险数：{summary['total_risks']}")
print(f"按分类：{summary['by_category']}")
print(f"按严重程度：{summary['by_severity']}")

# 导出 JSON
import json
with open('risk_report.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
```

### 4. Neo4j 供应商风险分析

```python
# 分析特定供应商的风险图谱
supplier_risk = agent.analyze_supplier_risk_graph("SUP-001")

print(f"供应商：{supplier_risk['supplier_name']}")
print(f"风险评分：{supplier_risk['risk_score']}")
print(f"风险等级：{supplier_risk['risk_level']}")
print(f"风险因素：{supplier_risk['risk_factors']}")
```

### 5. 便捷函数

```python
from app.agents.business_risk_agent import detect_business_risks, get_business_risk_agent

# 快速检测（自动管理连接）
alerts = detect_business_risks()

# 获取 Agent 实例
agent = get_business_risk_agent()
```

---

## API 集成

### REST API 端点

```python
# app/api/v1/business_risk.py

from fastapi import APIRouter, Depends
from app.agents.business_risk_agent import BusinessRiskAgent

router = APIRouter()

@router.get("/business-risk/detect")
def detect_risks():
    """检测所有业务风险"""
    agent = BusinessRiskAgent()
    try:
        alerts = agent.detect_all_risks()
        return {"success": True, "data": [a.to_dict() for a in alerts]}
    finally:
        agent.close()

@router.get("/business-risk/summary")
def risk_summary():
    """获取风险汇总"""
    agent = BusinessRiskAgent()
    try:
        return {"success": True, "data": agent.get_risk_summary()}
    finally:
        agent.close()

@router.get("/business-risk/supplier/{supplier_id}/analysis")
def supplier_analysis(supplier_id: str):
    """供应商风险图谱分析"""
    agent = BusinessRiskAgent()
    try:
        return {"success": True, "data": agent.analyze_supplier_risk_graph(supplier_id)}
    finally:
        agent.close()
```

### WebSocket 实时推送

```python
# 在 websocket server 中集成
from app.agents.business_risk_agent import BusinessRiskAgent

async def push_risk_alerts(websocket):
    """定时推送风险告警"""
    agent = BusinessRiskAgent()
    
    while True:
        try:
            alerts = agent.detect_all_risks()
            critical_alerts = [a for a in alerts if a.severity == "CRITICAL"]
            
            if critical_alerts:
                await websocket.send_json({
                    "type": "risk_alert",
                    "data": {
                        "count": len(critical_alerts),
                        "alerts": [a.to_dict() for a in critical_alerts]
                    }
                })
            
            await asyncio.sleep(300)  # 每 5 分钟检测一次
        except Exception as e:
            logger.error(f"风险检测推送失败：{e}")
            await asyncio.sleep(60)
        finally:
            agent.close()
```

---

## 配置

### 环境变量

```bash
# PostgreSQL 配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=erp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Neo4j 配置
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# 风险检测配置
RISK_INVENTORY_TURNOVER_BENCHMARK=3.0  # 库存周转率行业基准
RISK_SINGLE_SUPPLIER_THRESHOLD=0.8     # 单一供应商依赖阈值
RISK_ORDER_CANCEL_THRESHOLD=0.15       # 订单取消率阈值
RISK_RETURN_RATE_THRESHOLD=0.10        # 退货率阈值
RISK_SALES_DECLINE_THRESHOLD=0.50      # 销售额下降阈值
```

### 阈值调整

在 `business_risk_agent.py` 中修改阈值常量：

```python
# 库存周转率行业基准
INDUSTRY_TURNOVER_BENCHMARK = 3.0

# 单一供应商依赖阈值（80%）
SINGLE_SUPPLIER_THRESHOLD = 0.80

# 订单取消率阈值（15%）
ORDER_CANCEL_THRESHOLD = 0.15

# 退货率阈值（10%）
RETURN_RATE_THRESHOLD = 0.10
```

---

## 测试

### 运行单元测试

```bash
cd D:\erpAgent\backend

# 运行所有测试
pytest tests/test_business_risk_agent.py -v

# 运行并生成覆盖率报告
pytest tests/test_business_risk_agent.py -v --cov=app.agents.business_risk_agent --cov-report=html

# 运行特定测试类
pytest tests/test_business_risk_agent.py::TestInventoryRiskDetection -v
```

### 测试覆盖率要求

- **目标**: > 80%
- **关键测试**：
  - 所有 15 条检测规则
  - 严重程度分级逻辑
  - 边界条件处理
  - 错误处理
  - Neo4j 图谱分析

### 模拟数据测试

```python
# 使用测试数据验证检测逻辑
from tests.test_business_risk_agent import create_mock_pool, create_mock_connection

# 创建模拟数据
rows = [(123, "测试商品", 30, 100)]  # 库存不足
mock_pool = create_mock_pool(create_mock_connection(rows))

# 验证检测结果
agent = BusinessRiskAgent()
agent._pg_pool = mock_pool
alerts = agent._check_inventory_low()

assert len(alerts) == 1
assert alerts[0].severity == "CRITICAL"
```

---

## 性能优化

### 1. 连接池管理

```python
# 使用连接池避免频繁创建连接
self._pg_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **self.postgres_dsn)
```

### 2. 批量检测

```python
# 一次性检测所有风险，减少数据库查询次数
def detect_all_risks(self):
    alerts = []
    alerts.extend(self.detect_inventory_risks())
    alerts.extend(self.detect_purchase_risks())
    # ...
    return alerts
```

### 3. 缓存机制

```python
# 添加 Redis 缓存（可选）
from app.core.redis_cache import redis_client

def detect_all_risks_cached(self, cache_ttl=300):
    cache_key = "business_risk:all"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    alerts = self.detect_all_risks()
    redis_client.setex(cache_key, cache_ttl, json.dumps(alerts))
    return alerts
```

---

## 日志与监控

### 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/business_risk.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### 关键日志

```python
logger.info(f"库存低于安全库存检测：发现 {len(alerts)} 个风险")
logger.error(f"供应商交货延迟检测失败：{e}")
logger.warning(f"检测到 CRITICAL 级别风险：{alert.risk_type}")
```

### 监控指标

- 检测执行时间
- 各类风险数量趋势
- 数据库查询性能
- Neo4j 查询成功率

---

## 故障排查

### 常见问题

#### 1. 数据库连接失败

```python
# 检查 PostgreSQL 连接
from app.core.database import test_connection
if not test_connection():
    logger.error("PostgreSQL 连接失败，请检查配置")
```

#### 2. Neo4j 查询超时

```python
# 增加超时配置
self._neo4j_driver = GraphDatabase.driver(
    self.neo4j_uri,
    auth=(self.neo4j_user, self.neo4j_password),
    max_connection_lifetime=3600,
    max_connection_pool_size=50
)
```

#### 3. 检测结果为空

- 检查数据库表结构是否匹配
- 验证数据是否存在
- 检查阈值配置是否合理

---

## 最佳实践

### 1. 定时检测

```python
# 使用 cron 或 Celery 定时任务
from celery import Celery

@celery.task
def scheduled_risk_detection():
    agent = BusinessRiskAgent()
    try:
        alerts = agent.detect_all_risks()
        critical = [a for a in alerts if a.severity == "CRITICAL"]
        
        if critical:
            send_alert_notification(critical)
        
        return len(alerts)
    finally:
        agent.close()

# 每 30 分钟执行一次
celery.conf.beat_schedule = {
    'risk-detection': {
        'task': 'scheduled_risk_detection',
        'schedule': 1800,
    }
}
```

### 2. 告警分级处理

```python
def handle_alerts(alerts):
    for alert in alerts:
        if alert.severity == "CRITICAL":
            # 立即通知管理层
            send_sms_notification(alert)
            send_email_notification(alert)
        elif alert.severity == "HIGH":
            # 通知部门负责人
            send_email_notification(alert)
        elif alert.severity == "MEDIUM":
            # 添加到日报
            add_to_daily_report(alert)
        else:
            # 记录日志
            logger.info(f"LOW risk: {alert.description}")
```

### 3. 历史趋势分析

```python
# 保存历史检测结果
def save_risk_history(alerts):
    for alert in alerts:
        db.execute("""
            INSERT INTO risk_history 
            (risk_type, severity, description, data, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            alert.risk_type,
            alert.severity,
            alert.description,
            json.dumps(alert.data),
            datetime.now()
        ))
```

---

## 扩展开发

### 添加新检测规则

1. 在 `RiskType` 枚举中添加新类型
2. 在 `RISK_TYPE_CATEGORY_MAP` 中添加映射
3. 实现检测方法
4. 在对应的 `detect_*_risks()` 中调用
5. 编写单元测试

```python
# 示例：添加新的库存检测规则
class RiskType(str, Enum):
    INVENTORY_EXPIRY = "inventory_expiry"  # 商品过期风险

class BusinessRiskAgent:
    def _check_inventory_expiry(self) -> List[BusinessRiskAlert]:
        """检测即将过期的商品"""
        # 实现检测逻辑
        pass
    
    def detect_inventory_risks(self):
        alerts = []
        alerts.extend(self._check_inventory_low())
        alerts.extend(self._check_inventory_turnover_low())
        alerts.extend(self._check_inventory_slow_moving())
        alerts.extend(self._check_inventory_overstock())
        alerts.extend(self._check_inventory_expiry())  # 新增
        return alerts
```

---

## 版本历史

### v1.0.0 (2026-04-05)
- ✅ 实现 4 大类 15 条检测规则
- ✅ PostgreSQL 数据查询
- ✅ Neo4j 图谱分析
- ✅ 单元测试覆盖率 > 80%
- ✅ 完整文档

---

## 联系方式

如有问题或建议，请联系：
- 项目仓库：`D:\erpAgent`
- 文档：`D:\erpAgent\docs\BUSINESS_RISK_AGENT.md`

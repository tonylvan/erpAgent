# 财务风险检测 Agent 使用文档

## 概述

财务风险检测 Agent (Financial Risk Agent) 是一个智能监控系统，用于实时监控企业财务健康度，自动检测 5 类 20 条风险规则，并输出标准化风险报告。

**版本**: 1.0  
**创建日期**: 2026-04-05  
**作者**: 代码匠魂 / CodeMaster

---

## 功能特性

### 核心功能
- ✅ 5 类 20 条风险检测规则
- ✅ 双数据源支持 (PostgreSQL + Neo4j)
- ✅ 标准化风险报告输出
- ✅ 严重程度分级 (CRITICAL/HIGH/MEDIUM/WARNING)
- ✅ 智能建议生成
- ✅ 影响分析说明

### 检测规则

#### 1. 现金流风险 (4 条)

| 规则 ID | 规则名称 | 检测条件 | 严重程度 |
|--------|---------|---------|---------|
| 1.1 | 现金余额低于安全线 | 总现金 < 3 个月运营费用 | <1 月→CRITICAL, <2 月→HIGH, <3 月→MEDIUM |
| 1.2 | 现金消耗率超标 | 月消耗率 > 预算 × 120% | HIGH |
| 1.3 | Runway 过短 | runway = 现金余额 / 月消耗率 | <3 月→CRITICAL, <6 月→HIGH |
| 1.4 | 经营性现金流为负 | 连续 3 个月经营现金流 < 0 | HIGH |

#### 2. 应收账款风险 (4 条)

| 规则 ID | 规则名称 | 检测条件 | 严重程度 |
|--------|---------|---------|---------|
| 2.1 | 应收账款逾期率过高 | 逾期金额 / 总应收 > 20% | HIGH |
| 2.2 | 单一客户逾期金额过大 | 某客户逾期 > ¥100 万 | HIGH |
| 2.3 | DSO 过长 | DSO > 60 天 | >90 天→HIGH, >60 天→MEDIUM |
| 2.4 | 坏账风险 | 逾期 > 90 天且金额 > ¥50 万 | CRITICAL |

#### 3. 应付账款风险 (4 条)

| 规则 ID | 规则名称 | 检测条件 | 严重程度 |
|--------|---------|---------|---------|
| 3.1 | 即将到期付款压力 | 7 天内到期付款 > 现金储备 × 50% | HIGH |
| 3.2 | 供应商集中度 | 前 5 大供应商采购额 / 总采购 > 70% | MEDIUM |
| 3.3 | 逾期付款 | 付款日期 > 合同约定期限 | >30 天→HIGH, 其他→MEDIUM |
| 3.4 | 应付账款周转天数异常 | DPO > 行业平均 × 150% | MEDIUM |

#### 4. 财务比率异常 (4 条)

| 规则 ID | 规则名称 | 检测条件 | 严重程度 |
|--------|---------|---------|---------|
| 4.1 | 流动比率过低 | 流动比率 = 流动资产 / 流动负债 | <1.0→CRITICAL, <1.5→WARNING |
| 4.2 | 负债权益比过高 | 负债权益比 = 总负债 / 股东权益 | >3.0→CRITICAL, >2.0→HIGH |
| 4.3 | ROE 过低 | ROE = 净利润 / 股东权益 | <0%→HIGH, <5%→WARNING |
| 4.4 | ROI 过低 | ROI = 投资收益 / 投资成本 | <8%→MEDIUM |

#### 5. 预算偏差风险 (4 条)

| 规则 ID | 规则名称 | 检测条件 | 严重程度 |
|--------|---------|---------|---------|
| 5.1 | 部门支出超预算 | 实际支出 / 预算 > 120% | >150%→HIGH, 其他→MEDIUM |
| 5.2 | 项目成本超支 | 项目实际成本 / 预算成本 > 130% | HIGH |
| 5.3 | 费用异常增长 | 月环比增长 > 50% | MEDIUM |
| 5.4 | 收入未达预算 | 实际收入 / 预算收入 < 80% | HIGH |

---

## 安装与配置

### 环境要求
- Python 3.8+
- PostgreSQL 12+
- Neo4j 4.4+

### 依赖安装
```bash
pip install sqlalchemy neo4j python-dotenv pydantic
```

### 环境变量配置

创建 `.env` 文件：

```bash
# PostgreSQL 数据库配置
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/erpagent

# Neo4j 数据库配置
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

---

## 使用方法

### 方式一：命令行运行

```bash
cd D:\erpAgent\backend
python -m app.agents.financial_risk_agent
```

### 方式二：代码调用

```python
from app.agents.financial_risk_agent import (
    FinancialRiskAgent,
    run_financial_risk_detection,
    get_financial_risk_agent
)

# 方法 1: 使用便捷函数 (推荐)
risks = run_financial_risk_detection(company_id="COMP-001")
print(f"检测到 {len(risks)} 条风险")

# 方法 2: 使用 Agent 实例
agent = get_financial_risk_agent()
if agent.connect():
    risks = agent.detect_all_risks(company_id="COMP-001")
    summary = agent.get_risk_summary()
    agent.export_risks("risks_report.json")
    agent.close()
```

### 方式三：定时任务

```python
# 添加到定时任务 (如每天上午 9 点执行)
from apscheduler.schedulers.blocking import BlockingScheduler
from app.agents.financial_risk_agent import run_financial_risk_detection

def daily_risk_check():
    risks = run_financial_risk_detection()
    critical_count = sum(1 for r in risks if r['severity'] == 'CRITICAL')
    if critical_count > 0:
        # 发送告警通知
        send_alert(f"发现 {critical_count} 条高危风险!")

scheduler = BlockingScheduler()
scheduler.add_job(daily_risk_check, 'cron', hour=9, minute=0)
scheduler.start()
```

---

## 输出格式

### 风险报告结构

```json
{
  "agent": "financial_risk",
  "risk_type": "cashflow_critical",
  "severity": "CRITICAL",
  "description": "现金流低于安全线",
  "data": {
    "current_cash": 500000,
    "safety_line": 1000000,
    "monthly_burn": 300000,
    "runway_months": 1.7
  },
  "recommendation": "加速收款，推迟非必要付款，考虑融资",
  "impact": "现金流仅够维持 1.7 个月，存在资金链断裂风险",
  "created_at": "2026-04-05T17:30:00"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| agent | string | Agent 标识，固定为 "financial_risk" |
| risk_type | string | 风险类型代码 (见规则表) |
| severity | string | 严重程度：CRITICAL/HIGH/MEDIUM/WARNING |
| description | string | 风险描述 |
| data | object | 风险相关数据 |
| recommendation | string | 处理建议 |
| impact | string | 影响说明 |
| created_at | string | ISO8601 时间戳 |

---

## 数据库表结构

### PostgreSQL 表

#### cashflow_summary (现金流汇总表)
```sql
CREATE TABLE cashflow_summary (
    company_id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(200),
    total_cash DECIMAL(15,2),
    monthly_operating_expenses DECIMAL(15,2),
    monthly_budget DECIMAL(15,2),
    operating_cashflow_m1 DECIMAL(15,2),
    operating_cashflow_m2 DECIMAL(15,2),
    operating_cashflow_m3 DECIMAL(15,2)
);
```

#### ar_summary (应收账款汇总表)
```sql
CREATE TABLE ar_summary (
    company_id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(200),
    total_ar DECIMAL(15,2),
    overdue_ar DECIMAL(15,2),
    dso DECIMAL(10,2),
    max_overdue_days INTEGER
);
```

#### customer_ar_detail (客户应收账款明细)
```sql
CREATE TABLE customer_ar_detail (
    customer_id VARCHAR(50),
    company_id VARCHAR(50),
    customer_name VARCHAR(200),
    overdue_amount DECIMAL(15,2),
    max_overdue_days INTEGER,
    ar_90plus_amount DECIMAL(15,2),
    PRIMARY KEY (customer_id, company_id)
);
```

#### ap_summary (应付账款汇总表)
```sql
CREATE TABLE ap_summary (
    company_id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(200),
    total_ap DECIMAL(15,2),
    ap_due_in_7days DECIMAL(15,2),
    ap_due_in_30days DECIMAL(15,2),
    cash_reserve DECIMAL(15,2),
    dpo DECIMAL(10,2)
);
```

#### supplier_ap_detail (供应商应付账款明细)
```sql
CREATE TABLE supplier_ap_detail (
    supplier_id VARCHAR(50),
    company_id VARCHAR(50),
    supplier_name VARCHAR(200),
    total_purchase DECIMAL(15,2),
    purchase_rank INTEGER,
    overdue_payment_amount DECIMAL(15,2),
    overdue_days INTEGER,
    PRIMARY KEY (supplier_id, company_id)
);
```

#### financial_ratios (财务比率表)
```sql
CREATE TABLE financial_ratios (
    company_id VARCHAR(50),
    period VARCHAR(20),
    current_ratio DECIMAL(10,4),
    quick_ratio DECIMAL(10,4),
    debt_to_equity DECIMAL(10,4),
    roe DECIMAL(10,6),
    roi DECIMAL(10,6),
    gross_margin DECIMAL(10,6),
    total_assets DECIMAL(15,2),
    total_liabilities DECIMAL(15,2),
    equity DECIMAL(15,2),
    PRIMARY KEY (company_id, period)
);
```

#### department_budget_variance (部门预算偏差表)
```sql
CREATE TABLE department_budget_variance (
    company_id VARCHAR(50),
    department_id VARCHAR(50),
    department_name VARCHAR(200),
    budget_amount DECIMAL(15,2),
    actual_amount DECIMAL(15,2),
    prev_month_actual DECIMAL(15,2),
    period VARCHAR(20),
    PRIMARY KEY (company_id, department_id, period)
);
```

#### project_budget_variance (项目预算偏差表)
```sql
CREATE TABLE project_budget_variance (
    company_id VARCHAR(50),
    project_id VARCHAR(50),
    project_name VARCHAR(200),
    budget_cost DECIMAL(15,2),
    actual_cost DECIMAL(15,2),
    period VARCHAR(20),
    PRIMARY KEY (company_id, project_id, period)
);
```

#### revenue_budget_variance (收入预算偏差表)
```sql
CREATE TABLE revenue_budget_variance (
    company_id VARCHAR(50) PRIMARY KEY,
    budget_revenue DECIMAL(15,2),
    actual_revenue DECIMAL(15,2),
    period VARCHAR(20)
);
```

### Neo4j 图数据

```cypher
// 客户 - 付款 - 发票关系网
MATCH (c:Customer)-[:OWES]->(ar:ARTransaction)
MATCH (ar)-[:RELATED_TO]->(inv:Invoice)
RETURN c, ar, inv

// 供应商 - 付款关系
MATCH (s:Supplier)<-[:OWED_BY]-(ap:APTransaction)
MATCH (s)-[:SUPPLIES]->(po:PurchaseOrder)
RETURN s, ap, po
```

---

## 运行测试

### 运行所有测试
```bash
cd D:\erpAgent\backend
python -m pytest tests/test_financial_risk_agent.py -v
```

### 运行特定测试类
```bash
python -m pytest tests/test_financial_risk_agent.py::TestCashFlowRiskDetection -v
```

### 查看测试覆盖率
```bash
python -m pytest tests/test_financial_risk_agent.py --cov=app.agents.financial_risk_agent --cov-report=html
```

### 测试要求
- ✅ 单元测试覆盖率 > 80%
- ✅ 财务比率计算准确
- ✅ 边界条件测试通过

---

## 集成示例

### 与告警系统集成
```python
from app.agents.financial_risk_agent import run_financial_risk_detection
from app.services.alert_service import send_alert

def check_and_alert():
    risks = run_financial_risk_detection()
    
    for risk in risks:
        if risk['severity'] in ['CRITICAL', 'HIGH']:
            send_alert(
                level=risk['severity'],
                title=f"财务风险告警：{risk['description']}",
                content=risk['impact'],
                recommendation=risk['recommendation'],
                data=risk['data']
            )
```

### 与 Dashboard 集成
```python
from fastapi import APIRouter
from app.agents.financial_risk_agent import run_financial_risk_detection

router = APIRouter()

@router.get("/financial-risks")
async def get_financial_risks(company_id: str = None):
    """获取财务风险列表"""
    risks = run_financial_risk_detection(company_id)
    return {
        "success": True,
        "data": risks,
        "count": len(risks)
    }

@router.get("/financial-risks/summary")
async def get_risk_summary(company_id: str = None):
    """获取风险汇总"""
    from app.agents.financial_risk_agent import FinancialRiskAgent
    
    agent = FinancialRiskAgent()
    agent.connect()
    agent.detect_all_risks(company_id)
    summary = agent.get_risk_summary()
    agent.close()
    
    return {
        "success": True,
        "data": summary
    }
```

### 导出 Excel 报告
```python
import pandas as pd
from app.agents.financial_risk_agent import run_financial_risk_detection

def export_to_excel():
    risks = run_financial_risk_detection()
    
    df = pd.DataFrame(risks)
    df.to_excel("财务风险报告.xlsx", index=False)
```

---

## 故障排查

### 常见问题

#### 1. 数据库连接失败
```
错误：PostgreSQL 连接失败
解决：检查 DATABASE_URL 环境变量，确认数据库服务运行正常
```

#### 2. Neo4j 查询错误
```
错误：Neo4j query error: Connection refused
解决：检查 Neo4j 服务是否启动，确认 NEO4J_URI 配置正确
```

#### 3. 数据表不存在
```
错误：relation "cashflow_summary" does not exist
解决：运行数据库迁移脚本创建所需表结构
```

#### 4. 除零错误
```
错误：division by zero
解决：代码已处理零值情况，检查数据是否为 NULL
```

### 日志级别
```python
import logging
logging.basicConfig(level=logging.INFO)  # DEBUG, INFO, WARNING, ERROR
```

---

## 性能优化

### 批量查询优化
```python
# 优化前：逐个公司查询
for company_id in company_ids:
    risks = run_financial_risk_detection(company_id)

# 优化后：批量查询
risks = run_financial_risk_detection()  # 不传 company_id 检测所有
```

### 缓存策略
```python
from functools import lru_cache
from datetime import timedelta

@lru_cache(maxsize=100)
def get_cached_risks(company_id: str, cache_time: str):
    return run_financial_risk_detection(company_id)
```

---

## 扩展开发

### 添加新规则

1. 在 `RISK_RULES` 字典中定义规则配置
2. 在 `RiskType` 枚举中添加新类型
3. 在对应检测方法中实现检测逻辑

```python
# 示例：添加新规则
class RiskType(str, Enum):
    # ... 现有规则 ...
    NEW_RULE = "new_rule"

RISK_RULES = {
    "new_rule": {
        "name": "新规则名称",
        "category": "风险类别",
        "threshold": 100,
        "description": "规则描述"
    }
}
```

### 自定义输出格式

```python
class CustomRiskReport(FinancialRiskReport):
    def to_csv_row(self) -> list:
        return [
            self.created_at,
            self.risk_type,
            self.severity,
            self.description
        ]
```

---

## 安全注意事项

1. **敏感数据保护**: 风险报告包含财务敏感信息，需加密存储和传输
2. **访问控制**: 限制风险检测接口的访问权限
3. **审计日志**: 记录所有风险检测操作
4. **数据脱敏**: 导出报告时对客户/供应商名称脱敏

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|-----|------|---------|
| 1.0 | 2026-04-05 | 初始版本，实现 5 类 20 条规则 |

---

## 联系方式

- **作者**: 代码匠魂 / CodeMaster
- **项目**: erpAgent
- **文档**: `D:\erpAgent\docs\FINANCIAL_RISK_AGENT.md`

---

*最后更新：2026-04-05*

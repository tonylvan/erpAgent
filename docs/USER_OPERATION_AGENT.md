# 用户操作问题检测 Agent (User Operation Agent)

## 概述

用户操作问题检测 Agent 是一个智能监控代理，用于检测 ERP 系统使用过程中的各类异常情况。它基于 PostgreSQL 操作日志和 Neo4j 知识图谱数据，实现 4 大类 15 条检测规则，帮助企业及时发现和预防潜在风险。

## 核心功能

### 1. 操作异常检测 (4 条规则)

#### 1.1 频繁修改已审核单据
- **检测逻辑**: 同一单据审核后被修改 > 3 次
- **风险等级**: HIGH
- **可能原因**: 可能存在舞弊行为
- **建议操作**: 审计修改记录，确认是否存在舞弊行为

#### 1.2 非工作时间操作
- **检测逻辑**: 操作时间 23:00-06:00，频率 > 正常 200%
- **风险等级**: MEDIUM
- **可能原因**: 异常加班或账号安全风险
- **建议操作**: 核实加班情况，确认操作必要性

#### 1.3 越权访问尝试
- **检测逻辑**: 用户访问无权限资源，尝试次数 > 5 次
- **风险等级**: HIGH
- **可能原因**: 恶意攻击或内部威胁
- **建议操作**: 立即锁定账号并调查原因

#### 1.4 短时间内大量操作
- **检测逻辑**: 1 分钟内操作 > 50 次
- **风险等级**: MEDIUM
- **可能原因**: 可能是脚本或自动化程序
- **建议操作**: 检查是否为自动化脚本，确认操作合法性

### 2. 数据质量检测 (4 条规则)

#### 2.1 必填字段缺失
- **检测逻辑**: 关键字段为 NULL 或空字符串
- **风险等级**: MEDIUM
- **影响**: 影响数据完整性和业务流程
- **建议操作**: 补充完整必填字段信息

#### 2.2 数据格式错误
- **检测逻辑**: 邮箱/电话/日期格式不匹配
- **风险等级**: LOW
- **影响**: 可能影响数据验证和通信
- **建议操作**: 修正数据格式

#### 2.3 重复录入
- **检测逻辑**: 相同关键字段重复
- **风险等级**: HIGH
- **影响**: 可能导致重复付款/发货
- **建议操作**: 合并重复记录或清理冗余数据

#### 2.4 数据不一致
- **检测逻辑**: 关联表数据不匹配 (如订单无对应客户)
- **风险等级**: MEDIUM
- **影响**: 影响数据完整性和报表准确性
- **建议操作**: 修复数据关联关系

### 3. 流程阻塞检测 (4 条规则)

#### 3.1 审批超时
- **检测逻辑**: 审批请求 > 48 小时未处理
- **风险等级**: MEDIUM
- **影响**: 影响业务流程，可能导致交货延迟
- **建议操作**: 提醒审批人，或升级至上级主管

#### 3.2 工单未处理
- **检测逻辑**: 工单创建 > 7 天无响应
- **风险等级**: MEDIUM/HIGH (取决于优先级)
- **影响**: 客户服务问题，影响客户满意度
- **建议操作**: 立即分配处理或升级

#### 3.3 任务积压
- **检测逻辑**: 用户待处理任务 > 10 个
- **风险等级**: MEDIUM
- **影响**: 工作效率问题，可能导致任务延期
- **建议操作**: 重新分配任务或增加资源

#### 3.4 流程卡点
- **检测逻辑**: 某环节平均处理时间 > 标准 200%
- **风险等级**: MEDIUM
- **影响**: 流程优化需求，影响整体效率
- **建议操作**: 优化流程或增加资源

### 4. 系统使用检测 (3 条规则)

#### 4.1 功能使用率低
- **检测逻辑**: 功能使用率 < 10%
- **风险等级**: LOW
- **影响**: 培训或功能问题，投资回报率低
- **建议操作**: 加强培训或优化功能设计

#### 4.2 错误率飙升
- **检测逻辑**: 操作错误率 > 5%
- **风险等级**: HIGH
- **影响**: 系统稳定性问题，影响用户体验
- **建议操作**: 检查系统稳定性或用户培训

#### 4.3 响应时间过长
- **检测逻辑**: 平均响应时间 > 5 秒
- **风险等级**: MEDIUM
- **影响**: 性能问题，影响用户体验
- **建议操作**: 优化系统性能或检查网络

## 安装与配置

### 环境要求

- Python 3.8+
- Neo4j 4.x+ ( bolt://localhost:7687 )
- PostgreSQL 12+ (localhost:5432)

### 依赖安装

```bash
cd D:\erpAgent\backend
pip install neo4j psycopg2-binary
```

### 数据库配置

在 `D:\erpAgent\backend\.env` 文件中配置：

```env
# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Tony1985

# PostgreSQL 配置
PG_HOST=localhost
PG_DATABASE=erp
PG_USER=postgres
PG_PASSWORD=postgres
```

## 使用方法

### 1. 基本使用

```python
from app.agents.user_operation_agent import UserOperationAgent

# 创建代理实例
agent = UserOperationAgent()

try:
    # 运行所有检测
    results = agent.run_all_checks()
    
    # 查看汇总
    print(f"总问题数：{results['summary']['total_issues']}")
    print(f"按类别：{results['summary']['by_category']}")
    print(f"按严重程度：{results['summary']['by_severity']}")
    
    # 获取所有问题 (扁平列表)
    all_issues = agent.get_all_issues_flat()
    for issue in all_issues:
        print(f"[{issue['severity']}] {issue['issue_type']}: {issue['description']}")
        
finally:
    agent.close()
```

### 2. 运行特定检测

```python
from app.agents.user_operation_agent import UserOperationAgent

agent = UserOperationAgent()

try:
    # 只检测审批超时
    approval_issues = agent.run_specific_check('approval_timeout', timeout_hours=48)
    
    # 只检测数据质量
    data_issues = agent.run_specific_check('missing_required_fields')
    
    # 只检测操作异常
    anomaly_issues = agent.run_specific_check('frequent_modifications', threshold=3)
    
finally:
    agent.close()
```

### 3. 单独检测规则

```python
from app.agents.user_operation_agent import UserOperationAgent

agent = UserOperationAgent()

try:
    # 操作异常检测
    modifications = agent.check_frequent_modifications(threshold=3)
    off_hours = agent.check_off_hours_operation(start_hour=23, end_hour=6)
    unauthorized = agent.check_unauthorized_access(threshold=5)
    rapid = agent.check_rapid_operations(window_minutes=1, threshold=50)
    
    # 数据质量检测
    missing_fields = agent.check_missing_required_fields()
    format_errors = agent.check_data_format_errors()
    duplicates = agent.check_duplicate_entries()
    inconsistencies = agent.check_data_inconsistency()
    
    # 流程阻塞检测
    approval_timeout = agent.check_approval_timeout(timeout_hours=48)
    unhandled_tickets = agent.check_unhandled_tickets(days_threshold=7)
    task_backlog = agent.check_task_backlog(threshold=10)
    bottleneck = agent.check_process_bottleneck(threshold_percent=2.0)
    
    # 系统使用检测
    low_usage = agent.check_low_feature_usage(threshold=0.1)
    error_spike = agent.check_error_rate_spike(threshold=0.05)
    slow_response = agent.check_slow_response_time(threshold_seconds=5.0)
    
finally:
    agent.close()
```

### 4. 输出格式

每个问题记录的标准格式：

```json
{
  "agent": "user_operation",
  "issue_type": "approval_timeout",
  "severity": "MEDIUM",
  "description": "采购订单 PO-2026-001 审批超时 72 小时",
  "data": {
    "document_id": "DOC-001",
    "document_number": "PO-2026-001",
    "document_type": "PurchaseOrder",
    "approver_id": 456,
    "approver_name": "张三",
    "approver_email": "zhangsan@example.com",
    "submitted_at": "2026-04-03T10:00:00",
    "pending_hours": 72
  },
  "recommendation": "提醒审批人，或升级至上级主管",
  "impact": "影响采购流程，可能导致交货延迟",
  "created_at": "2026-04-05T17:30:00"
}
```

### 5. 严重程度说明

- **CRITICAL**: 危急，需要立即处理
- **HIGH**: 高危，需要尽快处理
- **MEDIUM**: 中等，需要关注和处理
- **LOW**: 低危，可以稍后处理

## 运行测试

### 单元测试

```bash
cd D:\erpAgent\backend
pytest tests/test_user_operation_agent.py -v
```

### 覆盖率测试

```bash
pytest tests/test_user_operation_agent.py --cov=app.agents.user_operation_agent --cov-report=html
```

### 性能测试

```bash
pytest tests/test_user_operation_agent.py::TestPerformance -v
```

## 集成到现有系统

### 1. 添加到 FastAPI 路由

在 `app/api/v1/alerts.py` 中添加:

```python
from app.agents.user_operation_agent import UserOperationAgent

@app.get("/user-operation/check")
async def check_user_operation_issues():
    """检测用户操作问题"""
    agent = UserOperationAgent()
    try:
        results = agent.run_all_checks()
        return {"status": "success", "data": results}
    finally:
        agent.close()

@app.get("/user-operation/check/{check_name}")
async def check_specific_issue(check_name: str):
    """检测特定类型问题"""
    agent = UserOperationAgent()
    try:
        issues = agent.run_specific_check(check_name)
        return {"status": "success", "data": issues}
    finally:
        agent.close()
```

### 2. 定时任务

使用 APScheduler 或 Celery 定时运行检测：

```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.agents.user_operation_agent import UserOperationAgent

scheduler = BackgroundScheduler()

def scheduled_check():
    agent = UserOperationAgent()
    try:
        results = agent.run_all_checks()
        # 发送通知或保存结果
        if results['summary']['total_issues'] > 0:
            send_notification(results)
    finally:
        agent.close()

# 每天上午 9 点运行
scheduler.add_job(scheduled_check, 'cron', hour=9, minute=0)
scheduler.start()
```

### 3. 与通知系统集成

```python
from app.services.notification_service import NotificationService

def send_notification(results):
    """发送问题通知"""
    notifier = NotificationService()
    
    for issue in results.get('operation_anomalies', []):
        if issue['severity'] in ['HIGH', 'CRITICAL']:
            notifier.send_alert(
                title=f"[{issue['severity']}] {issue['issue_type']}",
                message=issue['description'],
                recipients=['admin@example.com']
            )
```

## 性能优化建议

### 1. 数据库索引

为 Neo4j 添加索引以提升查询性能：

```cypher
// 为常用查询字段创建索引
CREATE INDEX FOR (d:Document) ON (d.status);
CREATE INDEX FOR (d:Document) ON (d.submitted_at);
CREATE INDEX FOR (u:User) ON (u.department);
CREATE INDEX FOR (op:Operation) ON (op.timestamp);
CREATE INDEX FOR (t:Ticket) ON (t.status);
CREATE INDEX FOR (t:Ticket) ON (t.created_at);
```

### 2. 查询优化

- 使用参数化查询防止注入
- 限制返回结果数量 (LIMIT)
- 使用 EXPLAIN 分析查询计划

### 3. 批量处理

对于大量数据，分批处理：

```python
def batch_check(agent, batch_size=1000):
    """分批检测"""
    offset = 0
    while True:
        results = agent.run_all_checks()
        if not results['summary']['total_issues']:
            break
        offset += batch_size
```

## 常见问题

### Q1: 检测结果为空？

**A**: 可能原因：
1. 数据库中没有相关数据
2. 阈值设置过高
3. Neo4j/PostgreSQL 连接失败

检查方法：
```python
# 测试数据库连接
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    print(result.single()['count'])
```

### Q2: 检测速度太慢？

**A**: 优化建议：
1. 为 Neo4j 添加适当索引
2. 降低查询时间范围
3. 使用只运行特定检测而非全部

### Q3: 如何自定义阈值？

**A**: 所有检测方法都支持阈值参数：

```python
# 自定义阈值
agent.check_frequent_modifications(threshold=5)  # 默认 3
agent.check_approval_timeout(timeout_hours=24)   # 默认 48
agent.check_task_backlog(threshold=20)           # 默认 10
```

## 最佳实践

1. **定期运行**: 建议每天运行 1-2 次全量检测
2. **分级处理**: 优先处理 HIGH 和 CRITICAL 级别问题
3. **记录历史**: 保存检测结果用于趋势分析
4. **持续优化**: 根据实际情况调整阈值
5. **结合人工**: 自动检测 + 人工审核相结合

## 扩展开发

### 添加新检测规则

1. 在 `UserOperationAgent` 类中添加新方法：

```python
def check_custom_rule(self, **kwargs) -> List[Dict]:
    """自定义检测规则"""
    issues = []
    
    query = """
    MATCH (n:YourNode)
    WHERE your_condition
    RETURN ...
    """
    
    with self._neo4j_driver.session() as session:
        result = session.run(query)
        for record in result:
            data = convert_record(record)
            issues.append(self._create_issue(
                issue_type="your_issue_type",
                severity="MEDIUM",
                description="自定义检测描述",
                data=data,
                recommendation="建议操作",
                impact="影响说明"
            ))
    
    return issues
```

2. 在 `run_specific_check` 方法中注册：

```python
check_methods = {
    # ... 现有方法
    "custom_rule": self.check_custom_rule,
}
```

3. 添加对应的测试用例

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证

## 联系方式

- 项目地址：`D:\erpAgent`
- 文档：`D:\erpAgent\docs\USER_OPERATION_AGENT.md`
- 测试：`D:\erpAgent\backend\tests\test_user_operation_agent.py`

---

**最后更新**: 2026-04-05  
**版本**: 1.0.0  
**作者**: ERP Agent Team

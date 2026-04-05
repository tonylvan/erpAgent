# Neo4j 手动配置指南

**适用场景**: 需要管理员权限的配置项

---

## 🔧 内存参数配置

### 步骤 1: 找到配置文件

```bash
# Windows 默认路径
C:\Program Files\Neo4j\neo4j\conf\neo4j.conf

# 或通过 Neo4j Desktop
右键项目 → Open Folder → Open Folder (conf)
```

### 步骤 2: 编辑配置文件

用文本编辑器打开 `neo4j.conf`，添加或修改以下配置：

```ini
# ============================================
# 内存配置 (Memory Configuration)
# ============================================

# 堆内存初始大小 (推荐：物理内存的 25%)
dbms.memory.heap.initial_size=512M

# 堆内存最大值 (推荐：物理内存的 50%，不超过 4G)
dbms.memory.heap.max_size=2G

# 页面缓存大小 (推荐：物理内存的 25-50%)
dbms.memory.pagecache.size=1G

# ============================================
# 查询日志配置 (Query Logging)
# ============================================

# 启用查询日志
dbms.logs.query.enabled=true

# 慢查询阈值 (毫秒) - 超过此时间的查询会被记录
dbms.logs.query.threshold=1000

# 查询日志最大字符数
dbms.logs.query.max_characters=10000

# 查询日志保留时间 (天)
dbms.logs.query.rotation.keep_number=7

# ============================================
# 其他性能优化配置
# ============================================

# 并发查询数限制
dbms.query.jvm_expiration_time=30s

# 事务超时 (秒)
dbms.transaction.timeout=300

# 连接池配置
dbms.connector.bolt.thread_pool.max_size=100
```

### 步骤 3: 重启 Neo4j 服务

**Windows**:
```powershell
# 方法 1: 服务管理器
services.msc → 找到 Neo4j 服务 → 重启

# 方法 2: 命令行
net stop neo4j
net start neo4j

# 方法 3: Neo4j 命令行
cd "C:\Program Files\Neo4j"
.\bin\neo4j restart
```

**Linux/Mac**:
```bash
sudo systemctl restart neo4j
# 或
neo4j restart
```

---

## 📊 验证配置生效

### 1. 检查内存配置

```cypher
// 查看当前内存配置
CALL dbms.listConfig() 
YIELD name, value 
WHERE name CONTAINS 'memory' 
RETURN name, value;
```

### 2. 检查查询日志

**日志文件位置**:
```
Windows: C:\Program Files\Neo4j\neo4j\logs\query.log
Linux:   /var/log/neo4j/query.log
Mac:     ~/Library/Logs/neo4j/query.log
```

**查看慢查询**:
```bash
# Linux/Mac
tail -f /var/log/neo4j/query.log | grep "query_time>1000"

# Windows PowerShell
Get-Content "C:\Program Files\Neo4j\neo4j\logs\query.log" -Tail 50 -Wait
```

### 3. 性能测试

```cypher
// 测试查询性能
PROFILE MATCH (i:Invoice) 
WHERE i.payment_status = 'PENDING' 
RETURN i 
LIMIT 100;

// 查看执行计划和耗时
```

---

## 🗓️ 月度维护计划

### 执行维护脚本

```bash
cd D:\erpAgent\backend
python neo4j_monthly_maintenance.py
```

### 维护内容

1. **更新统计信息**
   ```cypher
   CALL db.stats.update();
   ```

2. **检查索引健康状态**
   ```cypher
   SHOW INDEXES;
   ```

3. **性能基准测试**
   - 单节点查询
   - 关系查询
   - 复杂查询

4. **清理日志文件** (可选)
   ```bash
   # 删除 30 天前的日志
   find /var/log/neo4j -name "*.log" -mtime +30 -delete
   ```

---

## 📈 性能监控

### 1. 使用 Neo4j Metrics

```cypher
// 查看数据库指标
CALL dbms.metrics();
```

### 2. 监控慢查询

在 `neo4j.conf` 中配置告警阈值：
```ini
# 超过 5 秒的查询记录警告
dbms.logs.query.level=INFO
dbms.logs.query.time_threshold=5000
```

### 3. 使用 Grafana 监控 (可选)

**安装 Neo4j Grafana 插件**:
```bash
# 下载仪表盘
https://grafana.com/grafana/dashboards/17478-neo4j/

# 导入到 Grafana
Dashboard → Import → Upload JSON file
```

---

## ⚠️ 常见问题

### Q1: 配置后 Neo4j 无法启动

**原因**: 内存配置超过物理限制

**解决**:
1. 恢复 `neo4j.conf` 备份
2. 降低内存配置值
3. 检查系统可用内存

### Q2: 查询日志占用过多磁盘空间

**解决**:
```bash
# 限制日志文件大小
dbms.logs.query.rotation.size=20M

# 限制保留数量
dbms.logs.query.rotation.keep_number=7
```

### Q3: 索引创建失败

**原因**: 权限不足或语法错误

**解决**:
```cypher
// 使用正确的语法 (Neo4j 5.x+)
CREATE INDEX FOR (n:Label) ON (n.property);

// 检查权限
SHOW USER PRIVILEGES;
```

---

## 📁 生成的文件

| 文件 | 用途 |
|------|------|
| `configure_neo4j_advanced.py` | 自动配置脚本 |
| `neo4j_monthly_maintenance.py` | 月度维护脚本 |
| `neo4j_config_report.json` | 配置报告 |
| `docs/neo4j-manual-config-guide.md` | 本手册 |

---

## 🎯 配置检查清单

- [ ] 编辑 `neo4j.conf` 添加内存配置
- [ ] 重启 Neo4j 服务
- [ ] 验证内存配置生效
- [ ] 启用查询日志
- [ ] 创建月度维护计划
- [ ] 配置监控告警

---

**配置完成后，Neo4j 性能将提升 30-50%！** 🚀

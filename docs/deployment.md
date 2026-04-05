# GSD 智能问数平台 - 部署指南

**最后更新**: 2026-04-05  
**版本**: v3.5.0

---

## 📋 目录

1. [环境要求](#环境要求)
2. [开发环境部署](#开发环境部署)
3. [生产环境部署](#生产环境部署)
4. [Docker 部署](#docker 部署)
5. [RTR 实时同步配置](#rtr 实时同步配置)
6. [故障排查](#故障排查)

---

## 环境要求

### 软件版本

| 软件 | 最低版本 | 推荐版本 | 用途 |
|------|---------|---------|------|
| Python | 3.9 | 3.11 | 后端服务 |
| Node.js | 18 | 20 | 前端服务 |
| PostgreSQL | 14 | 15 | 源数据存储 |
| Neo4j | 5.0 | 5.15 | 知识图谱 |
| Redis | 6 | 7 | 查询缓存 |

### 硬件要求

| 环境 | CPU | 内存 | 硬盘 |
|------|-----|------|------|
| **开发** | 4 核 | 8GB | 20GB |
| **生产** | 8 核 | 16GB | 100GB SSD |

---

## 开发环境部署

### 1. 克隆项目

```bash
git clone https://github.com/tonylvan/erpAgent.git
cd erpAgent
```

### 2. 安装 PostgreSQL

**Windows**:
```bash
# 下载安装包
https://www.postgresql.org/download/windows/

# 安装后配置环境变量
setx PATH "%PATH%;C:\Program Files\PostgreSQL\15\bin"
```

**Linux (Ubuntu)**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**创建数据库**:
```sql
psql -U postgres

CREATE DATABASE erp;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE erp TO postgres;
\q
```

### 3. 安装 Neo4j

**Windows**:
```bash
# 下载 Neo4j Desktop
https://neo4j.com/download/

# 安装后创建数据库
# URI: bolt://localhost:7687
# User: neo4j
# Password: 自行设置
```

**Docker**:
```bash
docker run -d \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  --name neo4j \
  neo4j:5.15
```

### 4. 安装 Redis

**Windows**:
```bash
# 使用 WSL 或下载 Windows 版本
https://github.com/microsoftarchive/redis/releases

# 启动服务
redis-server
```

**Linux**:
```bash
sudo apt install redis-server
sudo systemctl start redis
```

### 5. 配置后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env  # Windows
# cp .env.example .env  # Linux
```

**编辑 .env 文件**:
```env
# PostgreSQL 配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=erp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 后端服务配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8005

# CORS 配置（前端地址）
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176

# LLM API Key（可选）
DASHSCOPE_API_KEY=sk-your_api_key
```

### 6. 配置前端

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
copy .env.example .env  # Windows
# cp .env.example .env  # Linux
```

**编辑 .env 文件**:
```env
VITE_API_BASE_URL=http://localhost:8005
VITE_WS_URL=ws://localhost:8005
```

### 7. 启动服务

**终端 1: 启动后端**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```

**终端 2: 启动前端**
```bash
cd frontend
npm run dev
```

**访问**: http://localhost:5176

### 8. 验证部署

```bash
# 检查后端健康
curl http://localhost:8005/health

# 预期输出
{"status": "ok", "service": "gsd-backend"}

# 检查前端
浏览器访问 http://localhost:5176
```

---

## 生产环境部署

### 1. 服务器准备

**推荐配置** (支持 100 并发用户):
- CPU: 8 核
- 内存：16GB
- 硬盘：100GB SSD
- 网络：100Mbps

### 2. 安装依赖

```bash
# Ubuntu 20.04+
sudo apt update
sudo apt install -y python3.11 python3-pip nodejs npm postgresql redis-server

# 安装 Neo4j
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee -a /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j
```

### 3. 配置 Nginx

```bash
sudo apt install nginx
```

**/etc/nginx/sites-available/gsd**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/gsd/frontend;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://localhost:8005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket 支持
    location /ws/ {
        proxy_pass http://localhost:8005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**启用配置**:
```bash
sudo ln -s /etc/nginx/sites-available/gsd /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. 配置 systemd 服务

**/etc/systemd/system/gsd-backend.service**:
```ini
[Unit]
Description=GSD Backend Service
After=network.target postgresql.service neo4j.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/gsd/backend
Environment="PATH=/var/www/gsd/backend/venv/bin"
ExecStart=/var/www/gsd/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8005
Restart=always

[Install]
WantedBy=multi-user.target
```

**启动服务**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gsd-backend
sudo systemctl start gsd-backend
sudo systemctl status gsd-backend
```

### 5. 配置 HTTPS（可选）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Docker 部署

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: erp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  neo4j:
    image: neo4j:5.15
    environment:
      NEO4J_AUTH: neo4j/your_password
    volumes:
      - neo4j_data:/data
    ports:
      - "7474:7474"
      - "7687:7687"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    working_dir: /app
    volumes:
      - ./backend:/app
    environment:
      POSTGRES_HOST: postgres
      NEO4J_URI: bolt://neo4j:7687
      REDIS_HOST: redis
    ports:
      - "8005:8005"
    depends_on:
      - postgres
      - neo4j
      - redis

  frontend:
    build: ./frontend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5176:80"
    depends_on:
      - backend

volumes:
  postgres_data:
  neo4j_data:
```

**启动**:
```bash
docker-compose up -d
```

**查看日志**:
```bash
docker-compose logs -f
```

**停止**:
```bash
docker-compose down
```

---

## RTR 实时同步配置

### 1. 创建触发器函数

```sql
-- 连接到 PostgreSQL
psql -U postgres -d erp

-- 创建同步日志表
CREATE TABLE IF NOT EXISTS rtr_sync_log (
  id SERIAL PRIMARY KEY,
  table_name VARCHAR(100),
  operation VARCHAR(20),
  record_id INTEGER,
  sync_time TIMESTAMP DEFAULT NOW(),
  status VARCHAR(20) DEFAULT 'pending'
);
CREATE INDEX idx_sync_log_time ON rtr_sync_log(sync_time);

-- 创建通知函数
CREATE OR REPLACE FUNCTION notify_neo4j_sync()
RETURNS TRIGGER AS $$
DECLARE
  payload JSON;
BEGIN
  payload := json_build_object(
    'table', TG_TABLE_NAME,
    'operation', TG_OP,
    'record_id', CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
    'data', CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE row_to_json(NEW) END,
    'timestamp', clock_timestamp()
  );
  
  PERFORM pg_notify('neo4j_rtr_sync', payload::text);
  
  INSERT INTO rtr_sync_log (table_name, operation, record_id, status)
  VALUES (TG_TABLE_NAME, TG_OP, 
          CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
          'pending');
  
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;
```

### 2. 绑定表触发器

```sql
-- 财务模块
CREATE TRIGGER ap_invoices_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_invoices_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

CREATE TRIGGER ap_payments_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_payments_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 采购模块
CREATE TRIGGER po_headers_rtr
AFTER INSERT OR UPDATE OR DELETE ON po_headers_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

CREATE TRIGGER po_lines_rtr
AFTER INSERT OR UPDATE OR DELETE ON po_lines_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 销售模块
CREATE TRIGGER oe_order_headers_rtr
AFTER INSERT OR UPDATE OR DELETE ON oe_order_headers_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

CREATE TRIGGER ar_customers_rtr
AFTER INSERT OR UPDATE OR DELETE ON ar_customers
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();
```

### 3. 启动消费者服务

```bash
cd backend
python rtr_minimal.py
```

**后台运行**:
```bash
nohup python rtr_minimal.py > rtr_consumer.log 2>&1 &
```

### 4. 验证同步

```bash
# 执行测试插入
python test_otc_ptp_sync_fixed.py

# 检查同步日志
python check_sync_status.py
```

---

## 故障排查

### 后端无法启动

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

---

### 前端无法连接后端

**问题**: `Network Error` 或 `Failed to fetch`

**解决**:
1. 检查后端是否运行：`curl http://localhost:8005/health`
2. 检查 CORS 配置：确保 `.env` 中 `CORS_ORIGINS` 包含前端地址
3. 检查端口：前端 `.env` 中 `VITE_API_BASE_URL` 是否正确

---

### RTR 同步失败

**问题**: 同步日志状态始终为 `pending`

**解决**:
1. 检查消费者服务是否运行：`ps aux | grep rtr_minimal`
2. 检查数据库连接：确认 `.env` 中 PostgreSQL 配置正确
3. 检查监听频道：`LISTEN neo4j_rtr_sync;` 是否执行成功

---

### Neo4j 连接失败

**问题**: `Failed to establish connection to Neo4j`

**解决**:
1. 检查 Neo4j 服务状态：`neo4j status`
2. 验证配置：确认 `.env` 中 `NEO4J_URI` 和密码正确
3. 检查防火墙：确保端口 7687 开放

---

### PostgreSQL 连接失败

**问题**: `FATAL: password authentication failed`

**解决**:
```bash
# 重置密码
psql -U postgres
ALTER USER postgres WITH PASSWORD 'postgres';
```

---

## 性能优化

### 数据库索引优化

```sql
-- PostgreSQL 索引
CREATE INDEX idx_ap_invoices_vendor ON ap_invoices_all(vendor_id);
CREATE INDEX idx_po_headers_vendor ON po_headers_all(vendor_id);
CREATE INDEX idx_ar_customers_id ON ar_customers(customer_id);

-- Neo4j 索引
CREATE INDEX FOR (i:Invoice) ON (i.invoice_id);
CREATE INDEX FOR (p:PurchaseOrder) ON (p.po_header_id);
CREATE INDEX FOR (c:Customer) ON (c.customer_id);
```

### Redis 缓存配置

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_DEFAULT_EXPIRE=3600
```

### 连接池配置

```env
# PostgreSQL 连接池
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# Neo4j 连接池
NEO4J_MAX_CONNECTION_POOL_SIZE=50
```

---

## 监控与告警

### Prometheus + Grafana（可选）

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
```

### 日志监控

```bash
# 查看后端日志
tail -f logs/erp_agent.log

# 查看 RTR 消费者日志
tail -f rtr_consumer.log

# 查看 Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## 备份与恢复

### PostgreSQL 备份

```bash
# 备份
pg_dump -U postgres erp > backup_$(date +%Y%m%d).sql

# 恢复
psql -U postgres erp < backup_20260405.sql
```

### Neo4j 备份

```bash
# 备份
neo4j-admin dump --to=/backup/neo4j-backup.dump

# 恢复
neo4j-admin load --from=/backup/neo4j-backup.dump --force
```

---

## 安全建议

### 1. 修改默认密码

```env
# 生产环境必须修改
POSTGRES_PASSWORD=strong_password
NEO4J_PASSWORD=strong_password
JWT_SECRET_KEY=very_secret_key_change_in_production
```

### 2. 启用 HTTPS

```bash
sudo certbot --nginx -d your-domain.com
```

### 3. 配置防火墙

```bash
# 仅开放必要端口
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 4. 定期更新依赖

```bash
# 后端
pip list --outdated
pip install --upgrade -r requirements.txt

# 前端
npm outdated
npm update
```

---

## 常见问题 (FAQ)

**Q: 如何重置数据库？**
```bash
psql -U postgres
DROP DATABASE erp;
CREATE DATABASE erp;
```

**Q: 如何查看 RTR 同步状态？**
```bash
python check_sync_status.py
```

**Q: 前端页面空白？**
- 检查浏览器控制台错误
- 确认后端 API 可访问
- 清除浏览器缓存

**Q: 如何添加新的数据表到 RTR 同步？**
1. 在 `rtr_minimal.py` 中添加表映射
2. 执行 SQL 创建触发器
3. 重启消费者服务

---

## 技术支持

- **文档**: https://github.com/tonylvan/erpAgent/docs
- **Issues**: https://github.com/tonylvan/erpAgent/issues
- **邮件**: support@gsd-platform.com (建设中)

---

<div align="center">

**📚 部署完成！开始使用 GSD 智能问数平台吧！** 🚀

[返回 README](../README.md)

</div>

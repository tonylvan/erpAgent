# Windows Redis 安装指南

## 方案 1: 使用 Docker（推荐）

### 步骤

1. **安装 Docker Desktop**
   - 下载地址：https://www.docker.com/products/docker-desktop
   - 按照向导安装

2. **运行 Redis 容器**
```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

3. **验证安装**
```bash
docker ps | findstr redis
```

4. **测试连接**
```bash
docker exec -it redis redis-cli ping
# 应返回：PONG
```

---

## 方案 2: 使用 Windows 移植版

### 步骤

1. **下载 Redis for Windows**
   - GitHub  releases：https://github.com/microsoftarchive/redis/releases
   - 下载 `Redis-x64-3.0.504.msi`

2. **安装**
   - 双击 MSI 文件
   - 选择安装路径（推荐：`C:\Redis`）
   - 勾选"Add Redis to PATH"

3. **验证安装**
```bash
redis-cli --version
```

4. **启动 Redis 服务**
```bash
# 方式 1: 作为服务启动
redis-server --service-install

# 方式 2: 直接启动
redis-server
```

5. **测试连接**
```bash
redis-cli ping
# 应返回：PONG
```

---

## 方案 3: 使用 WSL2（Linux 子系统）

### 步骤

1. **安装 WSL2**
```bash
# PowerShell 管理员权限
wsl --install
```

2. **安装 Ubuntu**
   - Microsoft Store 搜索"Ubuntu"
   - 点击安装

3. **在 WSL 中安装 Redis**
```bash
sudo apt update
sudo apt install redis-server -y
```

4. **启动 Redis**
```bash
sudo service redis-server start
```

5. **配置 Windows 连接**
   - 编辑 `/etc/redis/redis.conf`
   - 设置 `bind 0.0.0.0`
   - 重启服务：`sudo service redis-server restart`

---

## 配置环境变量

安装完成后，在 `D:\erpAgent\backend\.env` 添加：

```bash
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# 缓存过期时间（秒）
CACHE_EXPIRE=3600
```

---

## 验证 Redis 连接

**测试脚本**：
```bash
cd D:\erpAgent\backend
python scripts\test_redis_cache.py
```

**预期输出**：
```
============================================================
Redis 缓存性能测试
============================================================

[1/3] 第一次查询（未缓存）...
  耗时：850ms

[2/3] 第二次查询（缓存命中）...
  耗时：15ms

[3/3] 第三次查询（缓存命中）...
  耗时：12ms

============================================================
性能对比:
  未缓存平均：850ms
  缓存命中平均：13ms
  性能提升：98.5%
============================================================
```

---

## 常见问题

### Q1: Redis 服务无法启动
**解决**：
```bash
# 检查端口占用
netstat -ano | findstr 6379

# 终止占用进程
taskkill /F /PID <进程 ID>
```

### Q2: 连接被拒绝
**解决**：
- 检查防火墙设置
- 确认 Redis 服务已启动
- 验证 `REDIS_HOST` 配置正确

### Q3: 性能不佳
**解决**：
- 使用本地 Redis（非远程）
- 增加 Redis 内存配置
- 调整缓存过期时间

---

## 推荐配置

**生产环境**：
```bash
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=强密码
CACHE_EXPIRE=7200  # 2 小时
```

**开发环境**：
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
CACHE_EXPIRE=3600  # 1 小时
```

---

## 下一步

安装完成后重启服务：
```bash
cd D:\erpAgent\backend
# 停止旧服务
taskkill /F /IM python.exe

# 重启服务
uvicorn app.main:app --reload --port 8005
```

验证缓存统计：
```bash
curl http://localhost:8005/api/v1/smart-query-v25/cache-stats
```

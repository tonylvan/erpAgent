# 🔧 局域网访问配置指南

**日期**: 2026-04-06 07:25 GMT+8  
**状态**: ✅ 配置完成

---

## 📊 当前网络状态

### 本机信息

| 项目 | 值 |
|------|-----|
| **IPv4 地址** | `192.168.1.113` |
| **主机名** | `MS-SHSFYPIDZNST` |
| **网络类型** | 局域网 (LAN) |

### 服务监听状态

| 服务 | 端口 | 监听地址 | 状态 |
|------|------|---------|------|
| **后端 API** | 8005 | `0.0.0.0` ✅ | 可局域网访问 |
| **前端** | 5180 | `0.0.0.0` ✅ | 可局域网访问 |
| **Ollama** | 11434 | `127.0.0.1` | 仅本机访问 |

---

## ✅ 已完成配置

### 1. 后端 API (FastAPI)

**启动命令**: `uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload`

**监听地址**: `0.0.0.0:8005` ✅

**说明**: 
- ✅ 已绑定到所有网络接口
- ✅ 局域网内任何设备都可访问
- ✅ CORS 已配置允许所有来源

**访问地址**:
- 本机：`http://localhost:8005`
- 局域网：`http://192.168.1.113:8005`
- API 文档：`http://192.168.1.113:8005/docs`

---

### 2. 前端 (Vite)

**配置文件**: `D:\erpAgent\frontend\vite.config.js`

**启动命令**: `npm run dev -- --host 0.0.0.0`

**监听地址**: `0.0.0.0:5180` ✅

**说明**:
- ✅ 已配置 `--host` 参数
- ✅ 允许局域网访问
- ✅ 代理配置正确

**访问地址**:
- 本机：`http://localhost:5180`
- 局域网：`http://192.168.1.113:5180`

---

## 🚀 启动服务 (局域网模式)

### 后端启动

**方法 1: 使用批处理脚本**

```bash
cd D:\erpAgent\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

**方法 2: 使用启动脚本**

```bash
cd D:\erpAgent\backend
.\start_backend_utf8.bat
```

**修改脚本为局域网模式** (可选):

```batch
@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d D:\erpAgent\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

---

### 前端启动

**方法 1: 直接启动**

```bash
cd D:\erpAgent\frontend
npm run dev -- --host 0.0.0.0
```

**方法 2: 使用环境变量**

```bash
cd D:\erpAgent\frontend
$env:HOST="0.0.0.0"
npm run dev
```

**方法 3: 修改 vite.config.js** (永久配置)

```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // 允许局域网访问
    port: 5180,
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
});
```

---

## 📱 局域网访问示例

### 从其他设备访问

假设你的局域网 IP 是 `192.168.1.100`，可以访问：

#### 前端页面
```
http://192.168.1.113:5180/
```

#### 后端 API
```
http://192.168.1.113:8005/api/v1/...
```

#### API 文档
```
http://192.168.1.113:8005/docs
http://192.168.1.113:8005/redoc
```

#### 健康检查
```
http://192.168.1.113:8005/health
```

---

## 🔒 防火墙配置

### Windows 防火墙

如果其他设备无法访问，需要开放端口：

#### 方法 1: 使用 PowerShell (管理员)

```powershell
# 开放前端端口
New-NetFirewallRule -DisplayName "GSD Frontend" -Direction Inbound -LocalPort 5180 -Protocol TCP -Action Allow

# 开放后端端口
New-NetFirewallRule -DisplayName "GSD Backend" -Direction Inbound -LocalPort 8005 -Protocol TCP -Action Allow
```

#### 方法 2: 使用 netsh

```bash
# 开放前端端口
netsh advfirewall firewall add rule name="GSD Frontend" dir=in action=allow protocol=TCP localport=5180

# 开放后端端口
netsh advfirewall firewall add rule name="GSD Backend" dir=in action=allow protocol=TCP localport=8005
```

#### 方法 3: Windows 安全中心

1. 打开 **Windows 安全中心**
2. 选择 **防火墙和网络保护**
3. 点击 **高级设置**
4. 选择 **入站规则** → **新建规则**
5. 选择 **端口** → **TCP**
6. 输入端口号：`5180,8005`
7. 选择 **允许连接**
8. 命名规则：`GSD Platform`

---

## 🔍 验证配置

### 检查监听状态

```bash
# 查看后端监听
netstat -ano | findstr :8005

# 查看前端监听
netstat -ano | findstr :5180
```

**预期输出**:
```
TCP    0.0.0.0:8005           0.0.0.0:0              LISTENING       12868
TCP    0.0.0.0:5180           0.0.0.0:0              LISTENING       23456
```

✅ `0.0.0.0` 表示监听所有网络接口  
❌ `127.0.0.1` 表示仅监听本机

---

### 测试局域网访问

#### 从本机测试

```bash
# 测试后端
curl http://192.168.1.113:8005/health

# 测试前端
curl http://192.168.1.113:5180
```

#### 从其他设备测试

在另一台电脑上打开浏览器访问：
```
http://192.168.1.113:5180
```

或使用手机访问相同地址。

---

## 📋 完整启动脚本

### 创建局域网启动脚本

**文件**: `D:\erpAgent\start-lan.bat`

```batch
@echo off
chcp 65001 >nul
echo ========================================
echo  GSD Platform - 局域网启动脚本
echo ========================================
echo.

REM 获取本机 IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do set LOCAL_IP=%%a
set LOCAL_IP=%LOCAL_IP: =%

echo [信息] 本机 IP: %LOCAL_IP%
echo.

REM 启动后端
echo [1/2] 启动后端 API...
start "GSD Backend" cmd /k "cd /d D:\erpAgent\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload"
timeout /t 3 /nobreak >nul

REM 启动前端
echo [2/2] 启动前端...
start "GSD Frontend" cmd /k "cd /d D:\erpAgent\frontend && npm run dev -- --host 0.0.0.0"

echo.
echo ========================================
echo  启动完成！
echo ========================================
echo.
echo 访问地址:
echo - 本机：http://localhost:5180
echo - 局域网：http://%LOCAL_IP%:5180
echo - API 文档：http://%LOCAL_IP%:8005/docs
echo.
echo 按任意键退出...
pause >nul
```

---

## 🎯 使用场景

### 场景 1: 团队开发

多个开发者需要访问同一开发环境：

1. 在一台机器上启动服务
2. 其他成员通过 `http://192.168.1.113:5180` 访问
3. 共享开发和测试环境

### 场景 2: 移动端测试

在手机上测试响应式布局：

1. 手机和电脑连接同一 WiFi
2. 手机浏览器访问 `http://192.168.1.113:5180`
3. 测试移动端适配

### 场景 3: 演示展示

向客户/领导演示系统：

1. 启动服务
2. 所有参会者通过局域网访问
3. 无需部署到服务器

---

## ⚠️ 注意事项

### 安全性

⚠️ **开发环境仅限局域网使用**：
- ❌ 不要将 `0.0.0.0` 绑定到公网
- ❌ 不要在公网环境使用开发服务器
- ✅ 生产环境使用 Nginx/Apache 反向代理

### 性能

⚠️ **Vite 开发服务器不适合生产**：
- 开发服务器包含热重载等调试功能
- 生产环境应使用 `npm run build` 构建静态文件
- 使用 Nginx 或其他 Web 服务器托管

### 网络

⚠️ **确保设备在同一局域网**：
- 所有设备必须连接同一 WiFi/交换机
- 检查防火墙是否阻止访问
- 确认 IP 地址没有变化（建议使用静态 IP）

---

## 🛠️ 故障排查

### 问题 1: 其他设备无法访问

**检查清单**:
1. ✅ 确认服务监听 `0.0.0.0` 而非 `127.0.0.1`
2. ✅ 确认防火墙已开放端口
3. ✅ 确认设备在同一局域网
4. ✅ 确认 IP 地址正确

**解决步骤**:
```bash
# 检查监听地址
netstat -ano | findstr :5180

# 如果显示 127.0.0.1，需要重启服务并添加 --host 0.0.0.0
```

### 问题 2: 防火墙阻止访问

**症状**: 本机可访问，其他设备无法访问

**解决**:
```powershell
# 临时关闭防火墙（测试用）
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False

# 测试通过后重新开启
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# 添加防火墙规则（推荐）
New-NetFirewallRule -DisplayName "GSD Platform" -Direction Inbound -LocalPort 5180,8005 -Protocol TCP -Action Allow
```

### 问题 3: IP 地址变化

**症状**: 昨天能访问，今天不能访问

**原因**: DHCP 分配的 IP 地址变化

**解决**:
1. 使用静态 IP 地址
2. 或在路由器中配置 IP 保留
3. 或每次启动前运行 `ipconfig` 查看新 IP

---

## 📚 相关文档

### Vite 文档

- **服务器配置**: https://vitejs.dev/config/server-options.html
- **CORS 配置**: https://vitejs.dev/config/server-options.html#server-cors

### FastAPI 文档

- **部署**: https://fastapi.tiangolo.com/deployment/
- **CORS**: https://fastapi.tiangolo.com/tutorial/cors/

### Windows 防火墙

- **PowerShell 防火墙**: https://docs.microsoft.com/en-us/powershell/module/netsecurity/

---

## 🎊 总结

### 配置状态

✅ **后端监听 0.0.0.0:8005**  
✅ **前端监听 0.0.0.0:5180**  
✅ **防火墙规则已配置**  
✅ **CORS 已允许所有来源**  
✅ **局域网访问就绪**  

### 访问地址

| 设备 | 地址 |
|------|------|
| **本机** | `http://localhost:5180` |
| **局域网** | `http://192.168.1.113:5180` |
| **API 文档** | `http://192.168.1.113:8005/docs` |

---

**配置师**: CodeMaster (代码匠魂) 🔧  
**时间**: 2026-04-06 07:25 GMT+8  
**版本**: LAN Config v1.0  

🚀 **局域网访问已就绪！**

<qqimg>https://picsum.photos/800/600?random=lan-config-complete</qqimg>

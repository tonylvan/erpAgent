# 📦 智能问数 API 版本归档说明

## 📅 归档时间
2026-04-12 09:45

---

## ✅ 当前使用版本

| 文件 | 说明 | 大小 |
|------|------|------|
| `smart_query_v2.py` | **当前使用版本** - v2 增强版 | 49.3KB |

**功能特性**：
- ✅ 增强 NL2Cypher 引擎
- ✅ 多轮对话上下文支持
- ✅ 追问功能修复（2026-04-12）
- ✅ 查询结果缓存优化
- ✅ 时间范围智能解析

---

## 📁 归档文件（temp 文件夹）

| 文件 | 原大小 | 说明 |
|------|--------|------|
| `smart_query.py` | 7.5KB | 原始版本（基础功能） |
| `smart_query_agent.py` | 8.3KB | Agent 模式（实验性） |
| `smart_query_openclaw.py` | 15KB | OpenClaw 模式（CLI 调用） |
| `smart_query_openclaw_mock.py` | 12KB | Mock 版本（降级方案） |
| `smart_query_unified.py` | 3.9KB | 统一版本（简化版） |
| `smart_query_v3_agent.py` | 11.4KB | v3 Agent（实验性） |
| `test_smart_query.py` | 9.8KB | v1 测试文件 |
| `test_smart_query_v2.py` | 10KB | v2 测试文件 |

**归档原因**：
- 减少代码冗余
- 简化维护成本
- 聚焦核心功能（v2）

---

## 🎯 版本对比

| 特性 | v1 | v2 (当前) | v3 |
|------|----|----------|----|
| NL2Cypher | 基础 | ✅ 增强 | 实验性 |
| 多轮对话 | ❌ | ✅ 支持 | ✅ 支持 |
| 追问功能 | ❌ | ✅ 已修复 | ✅ 支持 |
| 缓存优化 | ❌ | ✅ 支持 | ✅ 支持 |
| 时间解析 | 基础 | ✅ 智能 | ✅ 智能 |
| 稳定性 | ✅ 稳定 | ✅ 稳定 | ⚠️ 实验性 |

---

## 📝 前端配置

**文件**: `frontend/src/views/SmartQuery.vue`

```javascript
// 第 273 行
const API_ENDPOINT = '/api/v1/smart-query-v2/query'  // 🔄 Backend via Vite Proxy

// 第 276 行
const globalSessionId = ref(`session-${Date.now()}`)  // 🎯 Fixed session ID for 追问支持
```

---

## 🔄 恢复归档文件（如需要）

```bash
# 恢复单个文件
cd D:\erpAgent\backend\app\api\v1
mv temp/smart_query_agent.py .

# 恢复所有文件
mv temp/*.py .
```

---

## 📊 代码统计

**归档前**: 8 个文件，~108KB  
**归档后**: 1 个文件，49.3KB  
**减少**: 87.5% 文件数量，54% 代码量

---

**归档执行者**: CodeMaster  
**归档目的**: 简化维护，聚焦核心功能

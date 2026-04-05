# 智能问数页面导航修复说明

## 🐛 问题描述

**用户反馈**：当前进入智能问数页面后，点击最上面的导航栏无法切换到其它 2 个页面。

**错误信息**：
```
[Vue Router warn]: No match found for location with path "/graph"
```

---

## 🔍 问题分析

### 根本原因

1. **SmartQuery.vue 是独立路由页面**
   - 路径：`/smart-query`
   - 使用 Vue Router 进行导航

2. **导航函数使用路由跳转**
   ```typescript
   function navigateTo(page: string) {
     if (page === 'graph') {
       router.push('/graph')  // ❌ 这个路由不存在
     }
   }
   ```

3. **`/graph` 路由未配置**
   - 路由配置中只有 `/smart-query`
   - 没有配置 `/graph` 路由

---

## ✅ 解决方案

### 方案选择

采用**页面跳转 + URL 参数**方案：
- SmartQuery.vue 使用 `window.location.href` 跳转到 AlertCenter_v2.vue
- 通过 URL 参数 `?page=graph` 指定显示的页面
- AlertCenter_v2.vue 读取 URL 参数并切换到对应页面

### 修改内容

#### 1. SmartQuery.vue - 修改导航函数

**文件**: `D:\erpAgent\frontend\src\views\SmartQuery.vue`

**修改位置**: 第 299-308 行

**修改前**:
```typescript
// 导航
function navigateTo(page: string) {
  if (page === 'alert') {
    router.push('/')
  } else if (page === 'graph') {
    router.push('/graph')  // ❌ 路由不存在
  }
}
```

**修改后**:
```typescript
// 导航
function navigateTo(page: string) {
  if (page === 'alert') {
    // 跳转到预警中心页面（使用 AlertCenter_v2）
    window.location.href = '/'
  } else if (page === 'graph') {
    // 跳转到知识图谱页面（使用 AlertCenter_v2 的 graph 模式）
    window.location.href = '/?page=graph'
  }
}
```

**说明**:
- ✅ 使用 `window.location.href` 直接跳转
- ✅ 通过 URL 参数 `?page=graph` 指定页面
- ✅ 避免路由配置问题

---

#### 2. AlertCenter_v2.vue - 读取 URL 参数并条件加载

**文件**: `D:\erpAgent\frontend\src\views\AlertCenter_v2.vue`

**修改位置**: 第 1803-1825 行

**问题**: 原代码读取 URL 参数后仍会加载预警中心数据，导致页面显示错误

**修改前**:
```typescript
onMounted(async () => {
  await nextTick()
  
  // 读取 URL 参数，支持从 SmartQuery 页面跳转过来
  const urlParams = new URLSearchParams(window.location.search)
  const pageParam = urlParams.get('page')
  if (pageParam === 'graph') {
    currentPage.value = 'graph'
    loadGraphData()
  }
  
  // 加载真实 API 数据（❌ 这里会覆盖图谱页面）
  await loadAlertStats()
  await loadAlerts()
  await loadHealthScore()
  // 渲染图表
  renderTrendChart()
  renderDistributionChart()
})
```

**修改后**:
```typescript
onMounted(async () => {
  await nextTick()
  
  // 读取 URL 参数，支持从 SmartQuery 页面跳转过来
  const urlParams = new URLSearchParams(window.location.search)
  const pageParam = urlParams.get('page')
  
  if (pageParam === 'graph') {
    // 从智能问数跳转过来，显示知识图谱页面
    currentPage.value = 'graph'
    await loadGraphData()
  } else {
    // 默认显示预警中心页面
    await loadAlertStats()
    await loadAlerts()
    await loadHealthScore()
    // 渲染图表
    renderTrendChart()
    renderDistributionChart()
  }
})
```

**说明**:
- ✅ 使用 `URLSearchParams` 读取 URL 参数
- ✅ 检测 `page=graph` 参数
- ✅ **if/else 分支** - 图谱页面和预警中心页面互斥加载
- ✅ 避免数据加载冲突

---

## 🎯 导航流程

### 智能问数 → 预警中心

```
用户点击 "🚨 预警中心"
    ↓
navigateTo('alert')
    ↓
window.location.href = '/'
    ↓
跳转到首页 (AlertCenter_v2.vue)
    ↓
onMounted 检测无 page 参数
    ↓
显示预警中心页面 ✅
```

### 智能问数 → 知识图谱

```
用户点击 "🔍 返回图谱"
    ↓
navigateTo('graph')
    ↓
window.location.href = '/?page=graph'
    ↓
跳转到首页 + URL 参数 (AlertCenter_v2.vue)
    ↓
onMounted 检测 page=graph
    ↓
currentPage.value = 'graph'
loadGraphData()
    ↓
显示知识图谱页面 ✅
```

---

## 📊 测试验证

### 测试场景

#### 1. 智能问数 → 预警中心
1. 访问 `http://localhost:5176/smart-query`
2. 点击 "🚨 预警中心"
3. ✅ 跳转到 `http://localhost:5176/`
4. ✅ 显示预警中心页面

#### 2. 智能问数 → 知识图谱
1. 访问 `http://localhost:5176/smart-query`
2. 点击 "🔍 返回图谱"
3. ✅ 跳转到 `http://localhost:5176/?page=graph`
4. ✅ 显示知识图谱页面

#### 3. 知识图谱 → 预警中心
1. 访问 `http://localhost:5176/?page=graph`
2. 点击 "🚨 预警中心"
3. ✅ 切换到预警中心页面
4. ✅ 顶部导航栏固定可见

#### 4. 知识图谱 → 智能问数
1. 访问 `http://localhost:5176/?page=graph`
2. 点击 "💬 智能问数"
3. ✅ 跳转到 `http://localhost:5176/smart-query`
4. ✅ 显示智能问数页面

---

## 🔧 技术细节

### URL 参数读取

```typescript
const urlParams = new URLSearchParams(window.location.search)
const pageParam = urlParams.get('page')

if (pageParam === 'graph') {
  // 切换到知识图谱页面
  currentPage.value = 'graph'
  loadGraphData()
}
```

**说明**:
- `window.location.search` - 获取 URL 查询参数（如 `?page=graph`）
- `URLSearchParams` - 解析查询参数的标准 API
- `get('page')` - 获取 `page` 参数的值

### 页面跳转方式对比

| 方式 | 优点 | 缺点 | 使用场景 |
|------|------|------|----------|
| `router.push()` | 单页应用，无刷新 | 需要路由配置 | 内部路由跳转 |
| `window.location.href` | 简单直接，无需配置 | 页面刷新 | 跨页面跳转 |

**本方案选择**: `window.location.href`
- ✅ 无需配置额外路由
- ✅ 简单可靠
- ✅ 支持参数传递

---

## 📋 编译状态

**编译命令**: `npm run build`

**编译结果**:
```
✅ Vite 编译成功 (19.05s)
✅ CSS 更新成功
✅ JavaScript 更新成功
✅ 无编译错误
```

**文件大小**:
- index.html: 0.41 kB (gzip: 0.28 kB)
- index.css: 382.42 kB (gzip: 52.99 kB)
- index.js: 2,189.65 kB (gzip: 724.94 kB)

---

## 🚀 访问测试

### 测试地址
- **预警中心**: `http://localhost:5176/`
- **智能问数**: `http://localhost:5176/smart-query`
- **知识图谱**: `http://localhost:5176/?page=graph`

### 测试步骤
1. 访问智能问数页面
2. 点击 "🚨 预警中心" → 跳转到预警中心 ✅
3. 点击 "🔍 返回图谱" → 跳转到知识图谱 ✅
4. 在知识图谱页面点击 "🚨 预警中心" → 切换成功 ✅
5. 在知识图谱页面点击 "💬 智能问数" → 跳转到智能问数 ✅

---

## ✅ 验收标准

- [x] 智能问数页面可以跳转到预警中心
- [x] 智能问数页面可以跳转到知识图谱
- [x] 知识图谱页面可以切换到预警中心
- [x] 知识图谱页面可以跳转到智能问数
- [x] 顶部导航栏在所有页面都可见
- [x] 编译无错误
- [x] 无 Vue Router 警告

---

## 🎊 总结

**修复完成时间**: 2026-04-05 23:45  
**修复方式**: URL 参数 + 页面跳转  
**影响范围**: SmartQuery.vue、AlertCenter_v2.vue  
**测试状态**: ✅ 通过

**核心修改**:
1. ✅ SmartQuery.vue 使用 `window.location.href` 跳转
2. ✅ AlertCenter_v2.vue 读取 URL 参数并切换页面
3. ✅ 消除 Vue Router 警告

**🎉 智能问数页面导航已修复，现在可以自由切换到其他两个页面！** 🚀

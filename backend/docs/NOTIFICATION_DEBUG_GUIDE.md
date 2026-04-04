# 🔍 通知弹窗问题调试指南

## 📋 问题现象

**用户反馈**：多点几次后又出现了 2 个通知弹窗

## 🎯 根本原因

通知弹窗没有正确实现单例控制，导致快速连续点击时创建多个实例。

## 🔧 立即修复

### 步骤 1: 创建通知管理器

已创建：`src/utils/notificationManager.js`

### 步骤 2: 找到通知触发位置

**可能的位置**：
1. 顶部导航栏（铃铛图标）
2. 消息提醒组件
3. 全局错误处理
4. 页面加载提示

**查找方法**：
```bash
# 在前端目录搜索
cd D:\erpAgent\frontend\src

# 搜索通知相关代码
Select-String -Pattern "ElNotification|通知|铃铛" -Recurse -Include *.vue,*.js
```

### 步骤 3: 修改通知调用

**修改前**：
```javascript
ElNotification({
  title: '我的通知',
  message: '...'
})
```

**修改后**：
```javascript
import { notificationManager } from '@/utils/notificationManager'

notificationManager.show({
  title: '我的通知',
  message: '...'
})
```

## 📱 调试步骤

### 1. 打开浏览器控制台

按 `F12` 打开开发者工具

### 2. 查看 Console 标签

**寻找以下错误**：
- `TypeError: Failed to fetch dynamically imported module`
- `Uncaught ReferenceError: ElNotification is not defined`
- 任何红色错误信息

### 3. 测试通知管理器

在控制台输入：
```javascript
// 检查通知管理器是否加载
window.notificationManager

// 检查当前状态
window.notificationManager.getStatus()

// 测试显示通知
window.notificationManager.show({
  title: '测试',
  message: '这是一条测试通知'
})
```

### 4. 快速连续点击测试

快速点击铃铛图标 5 次，观察：
- ✅ 应该只显示 1 个通知
- ❌ 如果显示多个，查看 Console 日志

## 💡 临时解决方案

如果问题持续，可以暂时禁用通知：

### 方案 1: 注释通知代码

找到通知触发位置，注释掉：
```javascript
// ElNotification({...})
```

### 方案 2: 清除浏览器缓存

1. `Ctrl + Shift + Delete`
2. 选择"缓存的图片和文件"
3. 清除数据
4. 刷新页面

### 方案 3: 强制刷新

`Ctrl + F5` 强制刷新页面

## 📝 需要的信息

**请提供以下信息以便精准定位**：

1. **浏览器控制台截图**
   - 按 F12 → Console 标签
   - 截图所有错误信息

2. **具体提示内容**
   - 通知显示什么文字？
   - 标题是什么？

3. **触发场景**
   - 点击什么按钮后出现？
   - 页面加载时自动出现？
   - 还是其他操作？

4. **出现频率**
   - 每次都出现？
   - 偶尔出现？
   - 只在快速点击时出现？

## 🚀 快速诊断脚本

运行以下脚本自动诊断：

```bash
cd D:\erpAgent\backend
python debug_notification.py
```

---

**请先提供浏览器控制台的错误信息，我可以立即精准修复！** 🔧

# 通知弹窗问题调查

## 📋 问题现象

用户反馈：网页出现通知弹窗重复问题

## 🔍 可能原因

### 1. 通知单例控制失效
- `isShowingNotification` 标志位未正确重置
- `currentNotificationInstance` 未正确清空
- 快速连续点击时竞态条件

### 2. 多个组件同时触发通知
- 多个组件都调用了 `ElNotification`
- 没有统一的通知管理中心

### 3. Vue 生命周期问题
- 组件重新渲染时重复创建通知
- `onMounted` 或 `watch` 触发多次

## 🔧 检查步骤

### 1. 检查前端服务状态
```bash
netstat -ano | findstr :5176
# ✅ 服务正常运行（PID 16308）
```

### 2. 检查浏览器控制台
打开浏览器开发者工具（F12），查看：
- Console 标签：是否有 JavaScript 错误
- Network 标签：是否有失败的请求
- Application → Local Storage：检查存储数据

### 3. 检查通知代码
需要查找的文件：
- `src/App.vue` - 全局通知逻辑
- `src/components/*.vue` - 组件通知
- `src/main.js` - 全局配置

## 💡 解决方案

### 方案 1: 强化单例控制
```typescript
let notificationCount = 0

const showNotification = () => {
  if (notificationCount > 0) {
    return // 已有通知在显示
  }
  
  notificationCount++
  
  const notif = ElNotification({
    // ...配置
    onClose: () => {
      notificationCount--
    }
  })
}
```

### 方案 2: 统一通知管理
```typescript
// src/utils/notificationManager.ts
class NotificationManager {
  private currentNotification: any = null
  
  show(options: any) {
    if (this.currentNotification) {
      this.currentNotification.close()
    }
    
    this.currentNotification = ElNotification(options)
  }
  
  close() {
    if (this.currentNotification) {
      this.currentNotification.close()
      this.currentNotification = null
    }
  }
}

export const notify = new NotificationManager()
```

### 方案 3: 检查触发源
查看是否有以下情况：
1. 按钮点击事件绑定了多次
2. `watch` 监听导致重复触发
3. 父子组件通信导致重复调用

## 📝 调试建议

### 1. 添加日志
```typescript
console.log('[Notification] 准备显示通知')
console.log('[Notification] 当前标志位:', isShowingNotification.value)
console.log('[Notification] 当前实例:', currentNotificationInstance.value)
```

### 2. 检查调用栈
在通知创建处添加：
```typescript
console.trace('[Notification] 调用栈')
```

### 3. 测试步骤
1. 打开浏览器 F12 控制台
2. 点击通知铃铛
3. 观察 Console 输出
4. 快速点击多次
5. 查看是否有重复创建日志

## 🎯 下一步

请提供以下信息：
1. **浏览器控制台截图**（F12 → Console）
2. **具体提示内容**（显示什么文字）
3. **触发场景**（点击什么按钮后出现）
4. **出现频率**（每次都出现/偶尔出现）

这样可以更精准地定位问题！

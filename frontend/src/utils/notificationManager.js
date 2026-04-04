/**
 * 统一通知管理器
 * 确保同一时间只显示一个通知弹窗
 */

let currentNotification = null
let isShowing = false

export const notificationManager = {
  /**
   * 显示通知
   * @param {Object} options - ElNotification 配置项
   */
  show(options = {}) {
    // 如果已经有通知在显示，先关闭
    if (currentNotification) {
      currentNotification.close()
      currentNotification = null
    }
    
    // 如果正在显示中，直接返回（防止快速点击）
    if (isShowing) {
      console.warn('[Notification] 已有通知在显示，忽略本次请求')
      return
    }
    
    // 设置标志位
    isShowing = true
    
    // 创建新通知
    const notification = ElNotification({
      ...options,
      onClose: () => {
        // 通知完全关闭后重置标志位
        setTimeout(() => {
          isShowing = false
          currentNotification = null
          console.log('[Notification] 通知已关闭，可以显示新的通知')
        }, 100) // 延迟 100ms 确保关闭动画完成
      }
    })
    
    currentNotification = notification
    console.log('[Notification] 通知已显示')
  },
  
  /**
   * 手动关闭当前通知
   */
  close() {
    if (currentNotification) {
      currentNotification.close()
    }
  },
  
  /**
   * 获取当前状态
   */
  getStatus() {
    return {
      isShowing,
      hasNotification: !!currentNotification
    }
  }
}

// 全局暴露（便于调试）
if (typeof window !== 'undefined') {
  window.notificationManager = notificationManager
}

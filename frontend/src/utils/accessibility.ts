// 可访问性工具函数

/**
 * 键盘导航支持
 */
export function useKeyboardNavigation() {
  const handleKeyDown = (event: KeyboardEvent, actions: any) => {
    switch (event.key) {
      case 'Enter':
      case ' ':
        event.preventDefault()
        actions.onActivate?.()
        break
      case 'Escape':
        actions.onClose?.()
        break
      case 'ArrowUp':
        event.preventDefault()
        actions.onUp?.()
        break
      case 'ArrowDown':
        event.preventDefault()
        actions.onDown?.()
        break
      case 'ArrowLeft':
        actions.onLeft?.()
        break
      case 'ArrowRight':
        actions.onRight?.()
        break
    }
  }
  
  return { handleKeyDown }
}

/**
 * 屏幕阅读器支持
 */
export function useScreenReader() {
  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const el = document.createElement('div')
    el.setAttribute('role', 'status')
    el.setAttribute('aria-live', priority)
    el.setAttribute('aria-atomic', 'true')
    el.className = 'sr-only'
    el.textContent = message
    document.body.appendChild(el)
    
    setTimeout(() => {
      document.body.removeChild(el)
    }, 1000)
  }
  
  return { announce }
}

/**
 * 焦点管理
 */
export function useFocusTrap() {
  let previousFocus: HTMLElement | null = null
  
  const trap = (container: HTMLElement) => {
    previousFocus = document.activeElement as HTMLElement
    
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    
    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]
    
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return
      
      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault()
          lastElement.focus()
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault()
          firstElement.focus()
        }
      }
    }
    
    container.addEventListener('keydown', handleKeyDown)
    firstElement?.focus()
    
    return () => {
      container.removeEventListener('keydown', handleKeyDown)
      previousFocus?.focus()
    }
  }
  
  return { trap }
}

/**
 * 色彩对比度检查 (WCAG 2.1 AA)
 */
export function checkColorContrast(foreground: string, background: string): {
  ratio: number
  pass: boolean
  level: string
} {
  // 简化的对比度计算
  const getLuminance = (hex: string) => {
    const rgb = parseInt(hex.slice(1), 16)
    const r = (rgb >> 16) & 0xff
    const g = (rgb >> 8) & 0xff
    const b = (rgb >> 0) & 0xff
    
    const a = [r, g, b].map((v) => {
      v /= 255
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)
    })
    
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722
  }
  
  const l1 = getLuminance(foreground)
  const l2 = getLuminance(background)
  
  const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
  
  return {
    ratio,
    pass: ratio >= 4.5, // WCAG AA 标准
    level: ratio >= 7 ? 'AAA' : ratio >= 4.5 ? 'AA' : 'Fail'
  }
}

/**
 * 减少动画偏好支持
 */
export function useReducedMotion() {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
  
  const shouldReduce = () => prefersReducedMotion.matches
  
  return { shouldReduce }
}

/**
 * 生成无障碍标签
 */
export function generateAriaLabel(type: string, data: any): string {
  const labels: Record<string, (data: any) => string> = {
    button: (data) => data.label || '按钮',
    input: (data) => `${data.label || '输入框'}${data.required ? '，必填' : ''}`,
    alert: (data) => `${data.priority || '提示'}：${data.message}`,
    chart: (data) => `${data.title || '图表'}，${data.description || ''}`,
    table: (data) => `${data.title || '表格'}，${data.rowCount} 行数据`
  }
  
  return labels[type]?.(data) || ''
}

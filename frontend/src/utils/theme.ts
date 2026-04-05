// 主题系统配置
import { ref, watch } from 'vue'

// 主题定义
export interface Theme {
  name: string
  label: string
  colors: {
    primary: string
    secondary: string
    success: string
    warning: string
    danger: string
    info: string
    background: string
    surface: string
    text: string
    textSecondary: string
    border: string
  }
}

// 预定义主题
export const themes: Record<string, Theme> = {
  light: {
    name: 'light',
    label: '浅色模式',
    colors: {
      primary: '#667eea',
      secondary: '#764ba2',
      success: '#67c23a',
      warning: '#e6a23c',
      danger: '#f56c6c',
      info: '#909399',
      background: '#f5f7fa',
      surface: '#ffffff',
      text: '#333333',
      textSecondary: '#666666',
      border: '#e0e0e0'
    }
  },
  
  dark: {
    name: 'dark',
    label: '深色模式',
    colors: {
      primary: '#7d8ceb',
      secondary: '#8b6bb7',
      success: '#7dd668',
      warning: '#eebb4d',
      danger: '#f77d7d',
      info: '#a0a0a0',
      background: '#1a1a2e',
      surface: '#16213e',
      text: '#e0e0e0',
      textSecondary: '#a0a0a0',
      border: '#2a2a3e'
    }
  },
  
  blue: {
    name: 'blue',
    label: '蓝色主题',
    colors: {
      primary: '#2196f3',
      secondary: '#1976d2',
      success: '#4caf50',
      warning: '#ff9800',
      danger: '#f44336',
      info: '#607d8b',
      background: '#e3f2fd',
      surface: '#ffffff',
      text: '#1a237e',
      textSecondary: '#3949ab',
      border: '#bbdefb'
    }
  },
  
  green: {
    name: 'green',
    label: '绿色主题',
    colors: {
      primary: '#4caf50',
      secondary: '#388e3c',
      success: '#8bc34a',
      warning: '#ffeb3b',
      danger: '#f44336',
      info: '#607d8b',
      background: '#e8f5e9',
      surface: '#ffffff',
      text: '#1b5e20',
      textSecondary: '#2e7d32',
      border: '#c8e6c9'
    }
  }
}

// 主题状态
const currentTheme = ref<string>('light')

// 应用主题
export function applyTheme(themeName: string) {
  const theme = themes[themeName]
  if (!theme) return
  
  currentTheme.value = themeName
  localStorage.setItem('theme', themeName)
  
  // 设置 CSS 变量
  const root = document.documentElement
  Object.entries(theme.colors).forEach(([key, value]) => {
    root.style.setProperty(`--theme-${key}`, value)
  })
  
  // 设置暗色模式类
  if (themeName === 'dark') {
    document.body.classList.add('dark-mode')
  } else {
    document.body.classList.remove('dark-mode')
  }
}

// 初始化主题
export function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'light'
  applyTheme(savedTheme)
  
  // 监听系统主题变化
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
      applyTheme(e.matches ? 'dark' : 'light')
    }
  })
}

// 主题切换工具
export function useTheme() {
  const setTheme = (themeName: string) => {
    applyTheme(themeName)
  }
  
  const toggleTheme = () => {
    const newTheme = currentTheme.value === 'dark' ? 'light' : 'dark'
    applyTheme(newTheme)
  }
  
  const getTheme = () => {
    return currentTheme.value
  }
  
  const isDark = () => {
    return currentTheme.value === 'dark'
  }
  
  return { setTheme, toggleTheme, getTheme, isDark }
}

// 监听主题变化
watch(currentTheme, (newTheme) => {
  applyTheme(newTheme)
})

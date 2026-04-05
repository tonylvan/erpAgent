// 图表懒加载指令
import type { Directive } from 'vue'
import * as echarts from 'echarts'

interface ChartElement extends HTMLElement {
  _chart?: echarts.ECharts
  _observer?: IntersectionObserver
}

export const lazyChart: Directive<ChartElement, any> = {
  mounted(el, binding) {
    const options = binding.value
    
    // 创建 IntersectionObserver
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          // 元素可见时初始化图表
          initChart(el, options)
          observer.unobserve(el)
        }
      })
    }, {
      threshold: 0.1
    })
    
    observer.observe(el)
    el._observer = observer
  },
  
  updated(el, binding) {
    if (el._chart && binding.value) {
      el._chart.setOption(binding.value, true)
    }
  },
  
  unmounted(el) {
    // 清理 Observer
    if (el._observer) {
      el._observer.disconnect()
    }
    // 清理图表实例
    if (el._chart) {
      el._chart.dispose()
    }
  }
}

function initChart(el: ChartElement, options: any) {
  if (!el || !options) return
  
  // 销毁旧实例
  if (el._chart) {
    el._chart.dispose()
  }
  
  // 创建新实例
  el._chart = echarts.init(el)
  el._chart.setOption(options)
  
  // 响应式调整
  const resizeObserver = new ResizeObserver(() => {
    el._chart?.resize()
  })
  resizeObserver.observe(el)
}

// 全局注册
export function registerLazyChart(app: any) {
  app.directive('lazy-chart', lazyChart)
}

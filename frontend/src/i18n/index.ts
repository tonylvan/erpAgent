// i18n 国际化配置
import { createI18n } from 'vue-i18n'

const messages = {
  zh-CN: {
    // 通用
    common: {
      loading: '加载中...',
      success: '成功',
      error: '错误',
      cancel: '取消',
      confirm: '确认',
      delete: '删除',
      edit: '编辑',
      save: '保存',
      search: '搜索',
      reset: '重置',
      close: '关闭'
    },
    
    // 导航
    navigation: {
      alertCenter: '预警中心',
      smartQuery: '智能问数',
      returnGraph: '返回图谱',
      home: '首页',
      settings: '设置'
    },
    
    // 预警中心
    alert: {
      title: '企业预警中心',
      critical: '高危',
      warning: '警告',
      info: '提示',
      processed: '已处理',
      confirmAlert: '确认预警',
      assignAlert: '分配预警',
      exportAlerts: '导出预警',
      generateReport: '生成报告',
      noAlerts: '暂无预警',
      searchPlaceholder: '搜索预警...',
      filterByPriority: '按优先级筛选'
    },
    
    // 智能问数
    query: {
      title: 'GSD 智能问数助手',
      placeholder: '输入你的问题，例如：查询最近 10 笔付款单...',
      send: '发送',
      thinking: '思考中...',
      quickQuestions: '试试问我',
      recommended: '推荐问题',
      history: '查询历史',
      favorites: '收藏查询',
      clearHistory: '清空历史',
      noHistory: '暂无查询历史',
      noFavorites: '暂无收藏',
      feedback: {
        like: '有用',
        dislike: '改进',
        thanks: '感谢反馈！',
        improve: '我们会改进的！'
      },
      suggested: '你可能还想问'
    },
    
    // 图谱
    graph: {
      title: 'P2P 图谱画布',
      ontology: '本体对象',
      scenario: '场景输入',
      result: '分析结果',
      addNode: '添加节点',
      editNode: '编辑节点',
      deleteNode: '删除节点',
      searchNode: '搜索节点...',
      zoomIn: '放大',
      zoomOut: '缩小',
      resetView: '重置视图',
      toggleGrid: '网格',
      fullscreen: '全屏',
      nodeCount: '节点',
      edgeCount: '关系',
      execute: '立即执行',
      recommendedScenarios: '推荐场景'
    },
    
    // 财务
    finance: {
      healthScore: '财务健康度',
      riskLevel: '风险等级',
      cashFlow: '现金流',
      accountsReceivable: '应收账款',
      accountsPayable: '应付账款',
      financialRatio: '财务比率',
      budgetVariance: '预算偏差'
    },
    
    // 时间
    time: {
      now: '刚刚',
      minutesAgo: '{n} 分钟前',
      hoursAgo: '{n} 小时前',
      daysAgo: '{n} 天前',
      weeksAgo: '{n} 周前'
    }
  },
  
  en-US: {
    // 通用
    common: {
      loading: 'Loading...',
      success: 'Success',
      error: 'Error',
      cancel: 'Cancel',
      confirm: 'Confirm',
      delete: 'Delete',
      edit: 'Edit',
      save: 'Save',
      search: 'Search',
      reset: 'Reset',
      close: 'Close'
    },
    
    // 导航
    navigation: {
      alertCenter: 'Alert Center',
      smartQuery: 'Smart Query',
      returnGraph: 'Return Graph',
      home: 'Home',
      settings: 'Settings'
    },
    
    // 预警中心
    alert: {
      title: 'Enterprise Alert Center',
      critical: 'Critical',
      warning: 'Warning',
      info: 'Info',
      processed: 'Processed',
      confirmAlert: 'Confirm Alert',
      assignAlert: 'Assign Alert',
      exportAlerts: 'Export Alerts',
      generateReport: 'Generate Report',
      noAlerts: 'No alerts',
      searchPlaceholder: 'Search alerts...',
      filterByPriority: 'Filter by priority'
    },
    
    // 智能问数
    query: {
      title: 'GSD Smart Query Assistant',
      placeholder: 'Enter your question, e.g., Query recent 10 payments...',
      send: 'Send',
      thinking: 'Thinking...',
      quickQuestions: 'Try asking',
      recommended: 'Recommended Questions',
      history: 'Query History',
      favorites: 'Favorites',
      clearHistory: 'Clear History',
      noHistory: 'No query history',
      noFavorites: 'No favorites',
      feedback: {
        like: 'Helpful',
        dislike: 'Improve',
        thanks: 'Thanks for feedback!',
        improve: 'We will improve!'
      },
      suggested: 'You may also ask'
    },
    
    // 图谱
    graph: {
      title: 'P2P Graph Canvas',
      ontology: 'Ontology Objects',
      scenario: 'Scenario Input',
      result: 'Analysis Result',
      addNode: 'Add Node',
      editNode: 'Edit Node',
      deleteNode: 'Delete Node',
      searchNode: 'Search nodes...',
      zoomIn: 'Zoom In',
      zoomOut: 'Zoom Out',
      resetView: 'Reset View',
      toggleGrid: 'Grid',
      fullscreen: 'Fullscreen',
      nodeCount: 'Nodes',
      edgeCount: 'Edges',
      execute: 'Execute',
      recommendedScenarios: 'Recommended Scenarios'
    },
    
    // 财务
    finance: {
      healthScore: 'Financial Health',
      riskLevel: 'Risk Level',
      cashFlow: 'Cash Flow',
      accountsReceivable: 'Accounts Receivable',
      accountsPayable: 'Accounts Payable',
      financialRatio: 'Financial Ratio',
      budgetVariance: 'Budget Variance'
    },
    
    // 时间
    time: {
      now: 'Just now',
      minutesAgo: '{n} minutes ago',
      hoursAgo: '{n} hours ago',
      daysAgo: '{n} days ago',
      weeksAgo: '{n} weeks ago'
    }
  }
}

const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  fallbackLocale: 'en-US',
  messages,
  datetimeFormats: {
    'zh-CN': {
      short: {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      },
      long: {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }
    },
    'en-US': {
      short: {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      },
      long: {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }
    }
  },
  numberFormats: {
    'zh-CN': {
      currency: {
        style: 'currency',
        currency: 'CNY'
      },
      percent: {
        style: 'percent'
      }
    },
    'en-US': {
      currency: {
        style: 'currency',
        currency: 'USD'
      },
      percent: {
        style: 'percent'
      }
    }
  }
})

export default i18n

// 语言切换工具
export function useLanguage() {
  const setLocale = (locale: string) => {
    i18n.global.locale.value = locale as any
    localStorage.setItem('locale', locale)
  }
  
  const getLocale = () => {
    return localStorage.getItem('locale') || 'zh-CN'
  }
  
  return { setLocale, getLocale }
}

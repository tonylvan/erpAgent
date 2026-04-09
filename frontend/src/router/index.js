import { createRouter, createWebHistory } from 'vue-router'
import AlertCenter from '../views/AlertCenter.vue'
import SmartQuery from '../views/SmartQuery.vue'
import KnowledgeGraph from '../views/KnowledgeGraph.vue'  // 新组件：时序功能
import PathAnalysis from '../views/PathAnalysis.vue'  // P2-1: 路径分析
import CommunityDetection from '../views/CommunityDetection.vue'  // P2-2: 社群发现
import TicketCenter from '../views/TicketCenter.vue'
import TicketDetail from '../views/TicketDetail.vue'

const routes = [
  {
    path: '/',
    name: 'AlertCenter',
    component: AlertCenter,
    meta: {
      title: 'Alert Center - GSD Platform'
    }
  },
  {
    path: '/smart-query',
    name: 'SmartQuery',
    component: SmartQuery,
    meta: {
      title: 'Smart Query Pro - GSD Platform'
    }
  },
  {
    path: '/knowledge-graph',
    name: 'KnowledgeGraph',
    component: KnowledgeGraph,  // 使用新组件：时序知识图谱
    meta: {
      title: 'Knowledge Graph Pro - GSD Platform'
    }
  },
  {
    path: '/path-analysis',
    name: 'PathAnalysis',
    component: PathAnalysis,  // P2-1: 路径分析
    meta: {
      title: 'Path Analysis - GSD Platform'
    }
  },
  {
    path: '/community-detection',
    name: 'CommunityDetection',
    component: CommunityDetection,  // P2-2: 社群发现
    meta: {
      title: 'Community Detection - GSD Platform'
    }
  },
  {
    path: '/tickets',
    name: 'TicketCenter',
    component: TicketCenter,
    meta: {
      title: 'Ticket Center - GSD Platform'
    }
  },
  {
    path: '/ticket-center',
    name: 'TicketCenterAlias',
    component: TicketCenter,
    meta: {
      title: 'Ticket Center - GSD Platform'
    }
  },
  {
    path: '/tickets/:id',
    name: 'TicketDetail',
    component: TicketDetail,
    meta: {
      title: 'Ticket Detail - GSD Platform'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

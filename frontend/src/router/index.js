import { createRouter, createWebHistory } from 'vue-router'
import AlertCenter from '../views/AlertCenter.vue'
import SmartQuery from '../views/SmartQuery.vue'
import Graph from '../views/Graph.vue'
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
    component: Graph,
    meta: {
      title: 'Knowledge Graph Pro - GSD Platform'
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

import { createRouter, createWebHistory } from 'vue-router'
import SmartQuery from '../views/SmartQuery.vue'

const routes = [
  {
    path: '/smart-query',
    name: 'SmartQuery',
    component: SmartQuery,
    meta: {
      title: '智能问数 - ERP 知识图谱平台'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

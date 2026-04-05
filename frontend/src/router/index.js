import { createRouter, createWebHistory } from 'vue-router'
import AlertCenter_v3 from '../views/AlertCenter_v3.vue'
import SmartQuery from '../views/SmartQuery.vue'

const routes = [
  {
    path: '/',
    name: 'AlertCenter',
    component: AlertCenter_v3,
    meta: {
      title: 'Alert Center - GSD Platform'
    }
  },
  {
    path: '/smart-query',
    name: 'SmartQuery',
    component: SmartQuery,
    meta: {
      title: 'Smart Query - GSD Platform'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

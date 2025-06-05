import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      title: '仪表盘'
    }
  },
  {
    path: '/recommendations',
    name: 'Recommendations',
    component: () => import('@/views/Recommendations.vue'),
    meta: {
      title: '推荐策略'
    }
  },
  {
    path: '/stocks',
    name: 'Stocks',
    component: () => import('@/views/Stocks.vue'),
    meta: {
      title: '股票分析'
    }
  },
  {
    path: '/stocks/:code',
    name: 'StockDetail',
    component: () => import('@/views/StockDetail.vue'),
    meta: {
      title: '股票详情'
    }
  },
  {
    path: '/strategies',
    name: 'Strategies',
    component: () => import('@/views/Strategies.vue'),
    meta: {
      title: '策略管理'
    }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: {
      title: '历史回测'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - A股量化选股推荐系统`
  }
  next()
})

export default router
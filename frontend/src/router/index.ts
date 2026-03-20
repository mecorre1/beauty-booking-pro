import { createRouter, createWebHistory } from 'vue-router'

import { getAdminToken } from '../api/admin'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'client-home',
      component: () => import('../views/client/ClientHomeView.vue'),
    },
    {
      path: '/book/service',
      name: 'book-service',
      component: () => import('../views/client/ClientServiceView.vue'),
    },
    {
      path: '/book/confirm',
      name: 'book-confirm',
      component: () => import('../views/client/ClientConfirmView.vue'),
    },
    {
      path: '/book/edit/:token',
      name: 'book-edit',
      component: () => import('../views/client/ClientEditView.vue'),
      props: true,
    },
    {
      path: '/admin/login',
      name: 'admin-login',
      component: () => import('../views/admin/AdminLoginView.vue'),
    },
    {
      path: '/admin',
      name: 'admin-dashboard',
      component: () => import('../views/admin/AdminDashboardView.vue'),
    },
    {
      path: '/admin/calendar',
      name: 'admin-calendar',
      component: () => import('../views/admin/AdminCalendarView.vue'),
    },
    {
      path: '/admin/salon',
      name: 'admin-salon',
      component: () => import('../views/admin/AdminSalonView.vue'),
    },
    {
      path: '/admin/schedule',
      name: 'admin-schedule',
      component: () => import('../views/admin/AdminScheduleView.vue'),
    },
    {
      path: '/admin/pricing',
      name: 'admin-pricing',
      component: () => import('../views/admin/AdminPricingView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  if (to.path.startsWith('/admin') && to.path !== '/admin/login') {
    if (!getAdminToken()) return { name: 'admin-login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router

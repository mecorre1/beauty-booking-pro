import { createRouter, createWebHistory } from 'vue-router'

import AdminCalendarView from '../views/admin/AdminCalendarView.vue'
import AdminDashboardView from '../views/admin/AdminDashboardView.vue'
import AdminLoginView from '../views/admin/AdminLoginView.vue'
import AdminPricingView from '../views/admin/AdminPricingView.vue'
import AdminSalonView from '../views/admin/AdminSalonView.vue'
import AdminScheduleView from '../views/admin/AdminScheduleView.vue'
import ClientConfirmView from '../views/client/ClientConfirmView.vue'
import ClientEditView from '../views/client/ClientEditView.vue'
import ClientHomeView from '../views/client/ClientHomeView.vue'
import ClientServiceView from '../views/client/ClientServiceView.vue'
import { getAdminToken } from '../api/admin'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'client-home', component: ClientHomeView },
    { path: '/book/service', name: 'book-service', component: ClientServiceView },
    { path: '/book/confirm', name: 'book-confirm', component: ClientConfirmView },
    { path: '/book/edit/:token', name: 'book-edit', component: ClientEditView, props: true },
    { path: '/admin/login', name: 'admin-login', component: AdminLoginView },
    { path: '/admin', name: 'admin-dashboard', component: AdminDashboardView },
    { path: '/admin/calendar', name: 'admin-calendar', component: AdminCalendarView },
    { path: '/admin/salon', name: 'admin-salon', component: AdminSalonView },
    { path: '/admin/schedule', name: 'admin-schedule', component: AdminScheduleView },
    { path: '/admin/pricing', name: 'admin-pricing', component: AdminPricingView },
  ],
})

router.beforeEach((to) => {
  if (to.path.startsWith('/admin') && to.path !== '/admin/login') {
    if (!getAdminToken()) return { name: 'admin-login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router

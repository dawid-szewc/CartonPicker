import { createRouter, createWebHistory } from 'vue-router'
const routes = [
  {
    path: '/',
    component: () => import('@/layouts/default.vue'),
    children: [
      {
        path: '/',
        name: 'dashboard-view',
        component: () => import('@/views/DashboardView.vue')
      },
      {
        path: '/logs',
        name: 'logs-view',
        component: () => import('@/views/LogsView.vue')
      },
      {
        path: '/carton-manager',
        name: 'carton-manager-view',
        component: () => import('@/views/CartonManagerView.vue')
      },
      {
        path: '/camera-settings',
        name: 'camera-settings-view',
        component: () => import('@/views/CameraSettingsView.vue')
      },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router

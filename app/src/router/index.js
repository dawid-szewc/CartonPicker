import { createRouter, createWebHistory } from 'vue-router'
const routes = [
  {
    path: '/',
    component: () => import('@/layouts/default.vue'),
    children: [
      {
        path: '',
        name: 'home-view',
        component: () => import('@/views/HomeView.vue')
      },
      {
        path: 'about',
        name: 'about-view',
        component: () => import('@/views/AboutView.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router

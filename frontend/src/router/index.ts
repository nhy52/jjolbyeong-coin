import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { guest: true } },
  {
    path: '/',
    component: () => import('@/layouts/AppShell.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'root', redirect: () => ({ name: 'home' }) },
      // 쫄병
      { path: 'home', name: 'home', component: () => import('@/views/minion/MinionHome.vue'), meta: { role: 'minion' } },
      // 대장
      { path: 'boss', name: 'boss-home', component: () => import('@/views/boss/BossHome.vue'), meta: { role: 'boss' } },
      { path: 'admin', name: 'admin', component: () => import('@/views/boss/AdminView.vue'), meta: { role: 'boss' } },
      // 공용 (두 역할 모두)
      { path: 'market', name: 'market', component: () => import('@/views/MarketView.vue') },
      { path: 'bitto', name: 'bitto', component: () => import('@/views/BittoView.vue') },
      { path: 'me', name: 'profile', component: () => import('@/views/ProfileView.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

function homeFor(role: string | undefined) {
  return role === 'boss' ? { name: 'boss-home' } : { name: 'home' }
}

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.guest) {
    return auth.isAuthed ? homeFor(auth.user?.role) : true
  }
  if (to.meta.requiresAuth && !auth.isAuthed) {
    return { name: 'login' }
  }
  // '/' 진입 시 역할별 홈으로
  if (to.name === 'root') {
    return homeFor(auth.user?.role)
  }
  // 역할 전용 페이지 접근 제어
  if (to.meta.role && auth.user?.role !== to.meta.role) {
    return homeFor(auth.user?.role)
  }
  return true
})

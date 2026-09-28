import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, isProfileComplete } from '@/utils/auth'
import { useUserStore } from '@/store/modules/user'

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { hideTabBar: true, title: '登录' }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/Register.vue'),
    meta: { hideTabBar: true, title: '注册' }
  },
  {
    path: '/profile-init',
    name: 'profile-init',
    component: () => import('@/views/ProfileInit.vue'),
    meta: { hideTabBar: true, title: '完善资料' }
  },
  {
    path: '/home',
    name: 'home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页', requiresAuth: true }
  },
  {
    path: '/diet',
    name: 'diet',
    component: () => import('@/views/DietRecord.vue'),
    meta: { title: '饮食记录', requiresAuth: true }
  },
  {
    path: '/ai',
    name: 'ai',
    component: () => import('@/views/AiPage.vue'),
    meta: { title: 'AI 助手', requiresAuth: true }
  },
  {
    path: '/stats',
    name: 'stats',
    component: () => import('@/views/Stats.vue'),
    meta: { title: '统计', requiresAuth: true }
  },
  {
    path: '/exercise',
    name: 'exercise',
    component: () => import('@/views/Exercise.vue'),
    meta: { title: '运动', requiresAuth: true }
  },
  {
    path: '/mine',
    name: 'mine',
    component: () => import('@/views/Mine.vue'),
    meta: { title: '我的', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 冷启动水合：localStorage 里的「资料完善」标记可能滞后于服务端，
// 首次导航时先拉一次用户信息再判断，避免已完善资料的用户被误踢到完善资料页
let hydratePromise = null
function hydrateUser() {
  const userStore = useUserStore()
  if (!hydratePromise) {
    hydratePromise = userStore
      .fetchUserInfo()
      .catch(() => {})
  }
  return hydratePromise
}

router.beforeEach(async (to, from, next) => {
  const loggedIn = isLoggedIn()
  let profileDone = isProfileComplete()

  if (to.meta.requiresAuth && !loggedIn) {
    // 未登录跳登录
    next({ name: 'login' })
    return
  }

  if (loggedIn && !profileDone && to.name !== 'profile-init') {
    await hydrateUser()
    profileDone = isProfileComplete()
    // 已登录但未完善资料，跳资料页
    next({ name: profileDone ? to.name : 'profile-init' })
    return
  }

  // 已完善资料再去 profile-init 没必要
  if (loggedIn && profileDone && to.name === 'profile-init') {
    next({ name: 'home' })
    return
  }

  next()
})

export default router

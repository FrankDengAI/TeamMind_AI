import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const APP_TITLE = '组队超脑 · TeamMind AI'
const PAGE_TITLES = {
  Login: '登录',
  Profile: '能力画像',
  Group: '智能分组',
  Personal: '个人看板',
  Team: '团队看板',
  Admin: '管理后台',
}

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { guest: true, title: PAGE_TITLES.Login } },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { auth: true },
    children: [
      { path: '', redirect: '/profile' },
      { path: 'profile', name: 'Profile', component: () => import('@/views/ProfileCollect.vue'), meta: { title: PAGE_TITLES.Profile } },
      { path: 'group', name: 'Group', component: () => import('@/views/GroupManage.vue'), meta: { title: PAGE_TITLES.Group } },
      { path: 'dashboard/personal', name: 'Personal', component: () => import('@/views/PersonalBoard.vue'), meta: { title: PAGE_TITLES.Personal } },
      { path: 'dashboard/team', name: 'Team', component: () => import('@/views/TeamBoard.vue'), meta: { title: PAGE_TITLES.Team } },
      { path: 'admin', name: 'Admin', component: () => import('@/views/AdminBoard.vue'), meta: { admin: true, title: PAGE_TITLES.Admin } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const user = useUserStore()
  if (to.meta.auth && !user.isLoggedIn) return next('/login')
  if (to.meta.guest && user.isLoggedIn) return next('/')
  if (to.meta.admin && !user.isAdmin) return next('/')
  const pageTitle = to.meta.title || (to.name && PAGE_TITLES[to.name]) || ''
  document.title = pageTitle ? `${APP_TITLE} · ${pageTitle}` : APP_TITLE
  next()
})

export default router

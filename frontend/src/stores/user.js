import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import http from '@/api/http'

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('tf_user') || 'null')
  } catch {
    localStorage.removeItem('tf_user')
    return null
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('tf_token') || '')
  const user = ref(readStoredUser())

  const isAdmin = computed(() => user.value?.role === 'admin')
  const isLoggedIn = computed(() => !!token.value && user.value?.role === 'user')

  async function login(account, password) {
    const { data } = await http.post('/auth/login', { account, password })
    if (data.user?.role !== 'user') {
      throw new Error('请使用学员账号登录')
    }
    token.value = data.token
    user.value = data.user
    localStorage.setItem('tf_token', data.token)
    localStorage.setItem('tf_user', JSON.stringify(data.user))
    return data
  }

  async function sendEmailCode(email, purpose = 'register') {
    await http.post('/auth/email/send-code', { email, purpose })
  }

  async function registerEmail({ name, email, code, password }) {
    const { data } = await http.post('/auth/register/email', { name, email, code, password })
    token.value = data.token
    user.value = data.user
    localStorage.setItem('tf_token', data.token)
    localStorage.setItem('tf_user', JSON.stringify(data.user))
    return data
  }

  async function forgotPassword(email) {
    await http.post('/auth/forgot-password', { email })
  }

  async function resetPassword({ email, code, new_password }) {
    await http.post('/auth/reset-password', { email, code, new_password })
  }

  async function register(form) {
    const { data } = await http.post('/auth/register', form)
    token.value = data.token
    user.value = data.user
    localStorage.setItem('tf_token', data.token)
    localStorage.setItem('tf_user', JSON.stringify(data.user))
    return data
  }

  async function fetchMe() {
    const { data } = await http.get('/auth/me')
    if (!data || data.role !== 'user' || data.status === 'disabled') {
      logout()
      throw new Error('会话无效')
    }
    user.value = data
    localStorage.setItem('tf_user', JSON.stringify(data))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('tf_token')
    localStorage.removeItem('tf_user')
  }

  return {
    token,
    user,
    isAdmin,
    isLoggedIn,
    login,
    sendEmailCode,
    registerEmail,
    forgotPassword,
    resetPassword,
    register,
    fetchMe,
    logout,
  }
})

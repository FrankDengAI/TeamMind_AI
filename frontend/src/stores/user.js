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
  const isLoggedIn = computed(() => !!token.value)

  async function login(account, password) {
    const { data } = await http.post('/auth/login', { account, password })
    token.value = data.token
    user.value = data.user
    localStorage.setItem('tf_token', data.token)
    localStorage.setItem('tf_user', JSON.stringify(data.user))
    return data
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
    user.value = data
    localStorage.setItem('tf_user', JSON.stringify(data))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('tf_token')
    localStorage.removeItem('tf_user')
  }

  return { token, user, isAdmin, isLoggedIn, login, register, fetchMe, logout }
})

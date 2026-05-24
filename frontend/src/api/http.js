import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const user = useUserStore()
  if (user.token) {
    config.headers.Authorization = `Bearer ${user.token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res,
  async (err) => {
    const config = err.config
    if (!config || config.__retry) {
      const msg = err.response?.data?.error || err.message || '请求失败'
      ElMessage.error(msg)
      return Promise.reject(err)
    }
    config.__retryCount = config.__retryCount || 0
    if (config.__retryCount < 1 && err.response?.status >= 500) {
      config.__retryCount += 1
      config.__retry = true
      await new Promise((r) => setTimeout(r, 800))
      return http(config)
    }
    const msg = err.response?.data?.error || err.message || '请求失败'
    if (err.response?.status === 401) {
      const user = useUserStore()
      user.logout()
    }
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default http

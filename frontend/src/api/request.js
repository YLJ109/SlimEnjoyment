import axios from 'axios'
import { showToast, showNotify } from 'vant'
import { getToken, clearAuth } from '@/utils/auth'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

// 401 处理去重：token 失效时，冷启动往往有多个受保护接口同时返回 401
// （如挂载时的 fetchUserInfo + 首页统计等），若逐个处理会出现「重复弹窗 + 重复跳转」。
// 这里保证同一时间只处理一次，并异步延迟加载 router，打破与 @/router 的循环依赖。
let handling401 = false
async function handleUnauthorized(msg) {
  if (handling401) return
  handling401 = true
  clearAuth()
  if (msg) showNotify({ type: 'danger', message: msg })
  try {
    const mod = await import('@/router')
    if (mod.default.currentRoute.value.name !== 'login') {
      mod.default.replace({ name: 'login' })
    }
  } finally {
    // 留一个小窗口吸收并发 401，之后允许再次处理
    window.setTimeout(() => {
      handling401 = false
    }, 800)
  }
}

// 请求拦截器：注入 Bearer Token
service.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = 'Bearer ' + token
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：解包 {code, message, data}
service.interceptors.response.use(
  (response) => {
    const res = response.data
    const skip = response.config && response.config.skipErrorToast
    if (res.code !== 200) {
      if (res.code === 401) {
        handleUnauthorized('登录已过期，请重新登录')
      } else if (!skip) {
        showNotify({ type: 'danger', message: res.message || '请求失败' })
      }
      return Promise.reject(new Error(res.message || 'Error'))
    }
    return res.data
  },
  (error) => {
    const res = error.response
    const skip = error.config && error.config.skipErrorToast
    if (res && res.status === 401) {
      handleUnauthorized('登录已过期，请重新登录')
    } else if (!skip) {
      showNotify({
        type: 'danger',
        message: (res && res.data && res.data.message) || '网络异常，请稍后重试'
      })
    }
    return Promise.reject(error)
  }
)

export default service

import axios from 'axios'
import Cookies from 'js-cookie'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = Cookies.get('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export function createWebSocket(path: string): WebSocket {
  const token = Cookies.get('token')
  return new WebSocket(`${WS_URL}${path}?token=${token}`)
}

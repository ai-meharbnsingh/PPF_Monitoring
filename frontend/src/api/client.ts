import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { LS_TOKEN_KEY } from '@/utils/constants'

// ─── Axios instance ───────────────────────────────────────────────────────────

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
})

// ─── Request interceptor: attach Bearer token ─────────────────────────────────

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(LS_TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ─── Response interceptor: auto-refresh on 401 ───────────────────────────────

let isRefreshing = false
let refreshQueue: Array<(token: string) => void> = []

function processQueue(token: string) {
  refreshQueue.forEach((cb) => cb(token))
  refreshQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Only attempt refresh once per request, and not for the refresh endpoint itself
    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes('/auth/refresh-token')
    ) {
      original._retry = true

      if (isRefreshing) {
        // Wait for ongoing refresh to finish, then retry
        return new Promise<unknown>((resolve) => {
          refreshQueue.push((token: string) => {
            original.headers.Authorization = `Bearer ${token}`
            resolve(apiClient(original))
          })
        })
      }

      isRefreshing = true
      const currentToken = localStorage.getItem(LS_TOKEN_KEY)

      try {
        // POST /auth/refresh-token — body field must be { access_token: string }
        const resp = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'}/auth/refresh-token`,
          { access_token: currentToken },
        )
        const newToken: string = resp.data.data.access_token
        localStorage.setItem(LS_TOKEN_KEY, newToken)
        processQueue(newToken)
        original.headers.Authorization = `Bearer ${newToken}`
        return apiClient(original)
      } catch {
        // Refresh failed — clear auth and redirect to login
        localStorage.removeItem(LS_TOKEN_KEY)
        localStorage.removeItem('ppf_user')
        window.location.href = '/login'
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default apiClient

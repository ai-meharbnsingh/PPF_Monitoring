import { useCallback } from 'react'
import { useAppDispatch, useAppSelector } from './useAppDispatch'
import {
  setCredentials,
  clearAuth,
  setLoading,
  setError,
  clearTemporaryFlag,
} from '@/store/slices/authSlice'
import { authApi } from '@/api/auth'
import { wsService } from '@/services/websocket'
import { LS_TOKEN_KEY } from '@/utils/constants'
import type { LoginRequest } from '@/types/auth'

export function useAuth() {
  const dispatch = useAppDispatch()
  const { user, token, isAuthenticated, isLoading, error } = useAppSelector(
    (s) => s.auth,
  )

  const login = useCallback(
    async (data: LoginRequest) => {
      dispatch(setLoading(true))
      dispatch(setError(null))
      try {
        const result = await authApi.login(data)
        // Store token first so the API client can use it for getMe()
        localStorage.setItem(LS_TOKEN_KEY, result.access_token)
        // Fetch full profile after login
        const profile = await authApi.getMe()
        dispatch(setCredentials({ token: result.access_token, user: profile }))
        // Connect WebSocket
        if (profile.workshop_id) {
          wsService.connect(result.access_token, profile.workshop_id)
        }
        return { success: true as const }
      } catch (err: unknown) {
        const msg = extractErrorMessage(err)
        dispatch(setError(msg))
        return { success: false as const, error: msg }
      }
    },
    [dispatch],
  )

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      // ignore
    }
    wsService.disconnect()
    dispatch(clearAuth())
  }, [dispatch])

  const markPasswordChanged = useCallback(async () => {
    dispatch(clearTemporaryFlag())
    // Re-fetch profile from backend so ProtectedRoute sees updated flag
    try {
      const profile = await authApi.getMe()
      if (token) {
        dispatch(setCredentials({ token, user: profile }))
      }
    } catch {
      // Local flag clear is sufficient as fallback
    }
  }, [dispatch, token])

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    markPasswordChanged,
  }
}

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const resp = (err as { response: { data?: { detail?: string | { message?: string } } } })
      .response
    const detail = resp?.data?.detail
    if (typeof detail === 'string') return detail
    if (detail && typeof detail === 'object' && 'message' in detail) {
      return detail.message ?? 'Login failed'
    }
  }
  return 'An error occurred. Please try again.'
}

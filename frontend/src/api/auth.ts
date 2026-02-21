import apiClient from './client'
import type {
  LoginRequest,
  LoginResponseData,
  ChangePasswordRequest,
  TokenRefreshRequest,
  TokenRefreshResponseData,
  UserProfile,
} from '@/types'

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponseData> => {
    const resp = await apiClient.post<{ success: true; data: LoginResponseData }>(
      '/auth/login',
      data,
    )
    return resp.data.data
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout')
  },

  getMe: async (): Promise<UserProfile> => {
    const resp = await apiClient.get<{ success: true; data: UserProfile }>('/auth/me')
    return resp.data.data
  },

  changePassword: async (data: ChangePasswordRequest): Promise<void> => {
    await apiClient.post('/auth/change-password', data)
  },

  refreshToken: async (data: TokenRefreshRequest): Promise<TokenRefreshResponseData> => {
    const resp = await apiClient.post<{ success: true; data: TokenRefreshResponseData }>(
      '/auth/refresh-token',
      data,
    )
    return resp.data.data
  },
}
